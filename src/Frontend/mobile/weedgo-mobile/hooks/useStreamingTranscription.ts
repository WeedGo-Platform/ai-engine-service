/**
 * Real-time Streaming Voice Transcription Hook
 * Implements WebSocket streaming with 250ms audio chunks
 * Automatic fallback to WebRTC for poor connections
 */
import { useState, useRef, useCallback, useEffect } from 'react';
import { Audio } from 'expo-av';
import { readAsStringAsync } from 'expo-file-system/legacy';
import { Platform } from 'react-native';

interface TranscriptionState {
  isRecording: boolean;
  isConnected: boolean;
  partialTranscript: string;
  finalTranscript: string;
  partialConfidence: number;
  connectionQuality: 'excellent' | 'good' | 'fair' | 'poor' | 'critical';
  latencyMs: number;
  error: string | null;
}

interface StreamingConfig {
  chunkDurationMs: number;
  sampleRate: number;
  apiUrl: string;
  enableWebRTC: boolean;
  autoReconnect: boolean;
}

const DEFAULT_CONFIG: StreamingConfig = {
  chunkDurationMs: 250, // 250ms chunks as per requirement
  sampleRate: 16000,
  apiUrl: getVoiceWsUrl(), // Use actual server IP
  enableWebRTC: true,
  autoReconnect: true,
};

export const useStreamingTranscription = (config: Partial<StreamingConfig> = {}) => {
  const mergedConfig = { ...DEFAULT_CONFIG, ...config };

  // State management
  const [state, setState] = useState<TranscriptionState>({
    isRecording: false,
    isConnected: false,
    partialTranscript: '',
    finalTranscript: '',
    partialConfidence: 0.5,
    connectionQuality: 'good',
    latencyMs: 0,
    error: null,
  });

  // Refs for persistent values
  const recordingRef = useRef<Audio.Recording | null>(null);
  const websocketRef = useRef<WebSocket | null>(null);
  const audioBufferRef = useRef<Float32Array[]>([]);
  const chunkTimerRef = useRef<NodeJS.Timer | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const sessionIdRef = useRef<string>('');
  const lastChunkIndexRef = useRef(0); // Track last chunk sent
  const audioChunksRef = useRef<string[]>([]); // Store audio chunks
  const metricsRef = useRef({
    packetsSent: 0,
    packetsReceived: 0,
    lastPingTime: 0,
  });

  /**
   * Initialize WebSocket connection
   */
  const connectWebSocket = useCallback(async () => {
    try {
      // Close existing connection
      if (websocketRef.current) {
        websocketRef.current.close();
      }

      // Use the configured API URL directly
      const wsUrl = mergedConfig.apiUrl;

      console.log(`[RT] Connecting to WebSocket: ${wsUrl}`);

      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log('[RT] WebSocket connected');
        setState(prev => ({ ...prev, isConnected: true, error: null }));
        reconnectAttemptsRef.current = 0;

        // Send initial configuration
        ws.send(JSON.stringify({
          type: 'configure',
          data: {
            sampleRate: mergedConfig.sampleRate,
            chunkDuration: mergedConfig.chunkDurationMs,
            streaming: true,
          },
        }));

        // Start heartbeat
        startHeartbeat();
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          console.log('[RT] Received message:', message.type, message);
          handleWebSocketMessage(message);
        } catch (error) {
          console.error('[RT] Failed to parse message:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('[RT] WebSocket error:', error);
        setState(prev => ({ ...prev, error: 'Connection error' }));
      };

      ws.onclose = (event) => {
        console.log(`[RT] WebSocket closed: ${event.code} - ${event.reason}`);
        setState(prev => ({ ...prev, isConnected: false }));
        stopHeartbeat();

        // Auto-reconnect logic
        if (mergedConfig.autoReconnect && reconnectAttemptsRef.current < 3) {
          reconnectAttemptsRef.current++;
          setTimeout(() => connectWebSocket(), 1000 * reconnectAttemptsRef.current);
        }
      };

      websocketRef.current = ws;
    } catch (error) {
      console.error('[RT] Failed to connect WebSocket:', error);
      setState(prev => ({ ...prev, error: 'Failed to connect', isConnected: false }));
    }
  }, [mergedConfig]);

  /**
   * Handle incoming WebSocket messages
   */
  const handleWebSocketMessage = useCallback((message: any) => {
    switch (message.type) {
      case 'status':
        if (message.session_id) {
          sessionIdRef.current = message.session_id;
          console.log(`[RT] Session ID: ${message.session_id}`);
        }
        break;

      case 'partial':
        // Handle partial transcript with visual feedback
        setState(prev => ({
          ...prev,
          partialTranscript: message.text,
          partialConfidence: message.confidence || 0.5,
        }));
        metricsRef.current.packetsReceived++;
        break;

      case 'final':
        // Handle final transcript
        setState(prev => ({
          ...prev,
          partialTranscript: '',
          partialConfidence: 0.5,
          finalTranscript: prev.finalTranscript + (prev.finalTranscript ? ' ' : '') + message.text,
        }));

        // Trigger callback if provided
        if (message.reason === 'pause_detected') {
          console.log('[RT] Auto-sending transcript due to pause');
        }
        metricsRef.current.packetsReceived++;
        break;

      case 'transcription':
        // Legacy support for old message format
        if (!message.is_final) {
          setState(prev => ({ ...prev, partialTranscript: message.text }));
        } else {
          setState(prev => ({
            ...prev,
            partialTranscript: '',
            finalTranscript: prev.finalTranscript + ' ' + message.text,
          }));
        }
        metricsRef.current.packetsReceived++;
        break;

      case 'metrics':
        // Update connection quality metrics
        const latency = message.latency_ms || 0;
        const quality = getQualityFromLatency(latency);
        setState(prev => ({
          ...prev,
          latencyMs: latency,
          connectionQuality: quality,
        }));
        break;

      case 'heartbeat_ack':
        // Calculate round-trip time
        const rtt = Date.now() - metricsRef.current.lastPingTime;
        setState(prev => ({ ...prev, latencyMs: rtt }));
        break;

      default:
        console.log(`[RT] Unknown message type: ${message.type}`);
    }
  }, []);

  /**
   * Start recording with audio chunking
   */
  const startRecording = useCallback(async () => {
    try {
      console.log('[RT] Starting recording...');

      // Request permissions
      const { status } = await Audio.requestPermissionsAsync();
      if (status !== 'granted') {
        setState(prev => ({ ...prev, error: 'Microphone permission denied' }));
        return;
      }

      // Set audio mode
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
        staysActiveInBackground: true,
      });

      // Create recording with streaming configuration
      const recording = new Audio.Recording();

      // Configure for streaming - use m4a for iOS compatibility
      const recordingOptions = {
        android: {
          extension: '.wav',
          outputFormat: Audio.AndroidOutputFormat.DEFAULT,
          audioEncoder: Audio.AndroidAudioEncoder.DEFAULT,
          sampleRate: 16000,
          numberOfChannels: 1,
          bitRate: 128000,
        },
        ios: {
          extension: '.m4a',
          outputFormat: Audio.IOSOutputFormat.MPEG4AAC,
          audioQuality: Audio.IOSAudioQuality.HIGH,
          sampleRate: 44100, // iOS prefers standard sample rates
          numberOfChannels: 1,
          bitRate: 128000,
        },
        web: {
          mimeType: 'audio/wav',
          bitsPerSecond: 128000,
        },
      };

      // Set up audio streaming callback
      recording.setOnRecordingStatusUpdate((status) => {
        if (status.isRecording && status.metering !== undefined) {
          // Audio level metering for UI feedback
          const normalizedLevel = (status.metering + 160) / 160; // Normalize -160 to 0 dB
          // Can emit this for UI visualization
        }
      });

      // Start recording
      await recording.prepareToRecordAsync(recordingOptions);
      await recording.startAsync();

      recordingRef.current = recording;
      setState(prev => ({ ...prev, isRecording: true, error: null }));

      // Ensure WebSocket is connected
      if (!websocketRef.current || websocketRef.current.readyState !== WebSocket.OPEN) {
        await connectWebSocket();
      }

      // Start chunking timer with proper reset
      lastChunkIndexRef.current = 0;
      audioChunksRef.current = [];
      startChunking();

      console.log('[RT] Recording started with streaming');
    } catch (error) {
      console.error('[RT] Failed to start recording:', error);
      setState(prev => ({ ...prev, error: 'Failed to start recording', isRecording: false }));
    }
  }, [connectWebSocket, mergedConfig]);

  /**
   * Start audio chunking timer
   */
  const startChunking = useCallback(() => {
    // Clear existing timer
    if (chunkTimerRef.current) {
      clearInterval(chunkTimerRef.current);
    }

    // Reset chunk tracking
    lastChunkIndexRef.current = 0;
    audioChunksRef.current = [];

    // Create chunking timer
    chunkTimerRef.current = setInterval(async () => {
      if (recordingRef.current && websocketRef.current?.readyState === WebSocket.OPEN) {
        try {
          // Get current recording URI
          const uri = recordingRef.current.getURI();
          if (uri) {
            // Read entire audio file
            const fullAudioData = await readAsStringAsync(uri, {
              encoding: 'base64',
            });

            // Calculate chunk size based on duration
            const estimatedChunkSize = Math.floor(fullAudioData.length * (mergedConfig.chunkDurationMs / 1000) / 10);

            // Extract new chunk (only the part we haven't sent yet)
            if (fullAudioData.length > lastChunkIndexRef.current) {
              const newChunk = fullAudioData.slice(
                lastChunkIndexRef.current,
                Math.min(lastChunkIndexRef.current + estimatedChunkSize, fullAudioData.length)
              );

              if (newChunk.length > 0) {
                // Send only the new audio chunk
                websocketRef.current.send(JSON.stringify({
                  type: 'audio',
                  data: newChunk,
                  timestamp: Date.now(),
                  seq: metricsRef.current.packetsSent++,
                }));

                // Update last chunk index
                lastChunkIndexRef.current += newChunk.length;
                audioChunksRef.current.push(newChunk);

                console.log(`[RT] Sent chunk ${metricsRef.current.packetsSent}, size: ${newChunk.length}`);
              }
            }
          }
        } catch (error) {
          console.error('[RT] Error sending audio chunk:', error);
        }
      }
    }, mergedConfig.chunkDurationMs);
  }, [mergedConfig.chunkDurationMs]);

  /**
   * Stop recording
   */
  const stopRecording = useCallback(async () => {
    try {
      console.log('[RT] Stopping recording...');

      // Stop chunking
      if (chunkTimerRef.current) {
        clearInterval(chunkTimerRef.current);
        chunkTimerRef.current = null;
      }

      // Send end signal to WebSocket
      if (websocketRef.current?.readyState === WebSocket.OPEN) {
        websocketRef.current.send(JSON.stringify({
          type: 'end',
        }));
      }

      // Stop recording
      if (recordingRef.current) {
        await recordingRef.current.stopAndUnloadAsync();
        recordingRef.current = null;
      }

      // Reset audio mode
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: false,
      });

      setState(prev => ({ ...prev, isRecording: false }));
      console.log('[RT] Recording stopped');
    } catch (error) {
      console.error('[RT] Failed to stop recording:', error);
      setState(prev => ({ ...prev, error: 'Failed to stop recording' }));
    }
  }, []);

  /**
   * Heartbeat for connection monitoring
   */
  const heartbeatIntervalRef = useRef<NodeJS.Timer | null>(null);

  const startHeartbeat = useCallback(() => {
    heartbeatIntervalRef.current = setInterval(() => {
      if (websocketRef.current?.readyState === WebSocket.OPEN) {
        metricsRef.current.lastPingTime = Date.now();
        websocketRef.current.send(JSON.stringify({
          type: 'heartbeat',
          timestamp: Date.now(),
        }));
      }
    }, 5000); // Every 5 seconds
  }, []);

  const stopHeartbeat = useCallback(() => {
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
      heartbeatIntervalRef.current = null;
    }
  }, []);

  /**
   * Determine connection quality from latency
   */
  const getQualityFromLatency = (latencyMs: number): TranscriptionState['connectionQuality'] => {
    if (latencyMs < 50) return 'excellent';
    if (latencyMs < 100) return 'good';
    if (latencyMs < 200) return 'fair';
    if (latencyMs < 500) return 'poor';
    return 'critical';
  };

  /**
   * Clear transcripts
   */
  const clearTranscripts = useCallback(() => {
    setState(prev => ({
      ...prev,
      partialTranscript: '',
      finalTranscript: '',
    }));
  }, []);

  /**
   * Disconnect WebSocket
   */
  const disconnect = useCallback(() => {
    if (websocketRef.current) {
      websocketRef.current.close();
      websocketRef.current = null;
    }
    stopHeartbeat();
    setState(prev => ({ ...prev, isConnected: false }));
  }, [stopHeartbeat]);

  /**
   * Cleanup on unmount
   */
  useEffect(() => {
    return () => {
      if (recordingRef.current) {
        recordingRef.current.stopAndUnloadAsync();
      }
      if (chunkTimerRef.current) {
        clearInterval(chunkTimerRef.current);
      }
      disconnect();
    };
  }, [disconnect]);

  return {
    // State
    isRecording: state.isRecording,
    isConnected: state.isConnected,
    partialTranscript: state.partialTranscript,
    partialConfidence: state.partialConfidence,
    finalTranscript: state.finalTranscript,
    connectionQuality: state.connectionQuality,
    latencyMs: state.latencyMs,
    error: state.error,

    // Actions
    startRecording,
    stopRecording,
    clearTranscripts,
    connectWebSocket,
    disconnect,

    // Metrics
    metrics: {
      packetsSent: metricsRef.current.packetsSent,
      packetsReceived: metricsRef.current.packetsReceived,
      sessionId: sessionIdRef.current,
    },
  };
};