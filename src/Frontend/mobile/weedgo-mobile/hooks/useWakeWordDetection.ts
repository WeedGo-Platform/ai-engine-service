import { useState, useEffect, useRef, useCallback } from 'react';
import { Audio } from 'expo-av';
import { Platform } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

interface WakeWordConfig {
  enabled: boolean;
  sensitivity: number;
  threshold: number;
  models: string[];
  continuousListening: boolean;
  privacyMode: boolean;
}

interface WakeWordDetection {
  detected: boolean;
  wakeWord: string | null;
  confidence: number;
  timestamp: number;
}

interface WakeWordState {
  isListening: boolean;
  isConnected: boolean;
  lastDetection: WakeWordDetection | null;
  sessionId: string | null;
  state: 'idle' | 'listening_wake_word' | 'listening_command' | 'processing' | 'error';
  error: string | null;
}

interface UseWakeWordDetectionReturn {
  // State
  isListening: boolean;
  isConnected: boolean;
  lastDetection: WakeWordDetection | null;
  state: WakeWordState['state'];
  error: string | null;

  // Actions
  startListening: () => Promise<void>;
  stopListening: () => Promise<void>;
  toggleListening: () => Promise<void>;
  updateConfig: (config: Partial<WakeWordConfig>) => Promise<void>;
  resetDetection: () => void;

  // Config
  config: WakeWordConfig;
}

const DEFAULT_CONFIG: WakeWordConfig = {
  enabled: true,
  sensitivity: 0.6,
  threshold: 0.7,
  models: ['hey_weedgo', 'weedgo'],
  continuousListening: true,
  privacyMode: false,
};

const WS_RECONNECT_DELAY = 3000; // 3 seconds
const AUDIO_CHUNK_SIZE = 4096; // 4KB chunks
const AUDIO_SEND_INTERVAL = 100; // Send audio every 100ms

export function useWakeWordDetection(): UseWakeWordDetectionReturn {
  const [state, setState] = useState<WakeWordState>({
    isListening: false,
    isConnected: false,
    lastDetection: null,
    sessionId: null,
    state: 'idle',
    error: null,
  });

  const [config, setConfig] = useState<WakeWordConfig>(DEFAULT_CONFIG);

  // Refs for WebSocket and Audio
  const wsRef = useRef<WebSocket | null>(null);
  const recordingRef = useRef<Audio.Recording | null>(null);
  const audioBufferRef = useRef<Int16Array>(new Int16Array(0));
  const sendIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const isProcessingRef = useRef(false);

  // Load config from storage
  useEffect(() => {
    loadConfig();
  }, []);

  // Auto-connect if enabled
  useEffect(() => {
    if (config.enabled && config.continuousListening && !state.isConnected) {
      connectWebSocket();
    }

    return () => {
      disconnect();
    };
  }, [config.enabled, config.continuousListening]);

  const loadConfig = async () => {
    try {
      const storedConfig = await AsyncStorage.getItem('wake_word_config');
      if (storedConfig) {
        setConfig({ ...DEFAULT_CONFIG, ...JSON.parse(storedConfig) });
      }
    } catch (error) {
      console.error('Failed to load wake word config:', error);
    }
  };

  const saveConfig = async (newConfig: WakeWordConfig) => {
    try {
      await AsyncStorage.setItem('wake_word_config', JSON.stringify(newConfig));
    } catch (error) {
      console.error('Failed to save wake word config:', error);
    }
  };

  const connectWebSocket = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      const apiUrl = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:5025';
      const wsUrl = apiUrl.replace('http', 'ws');
      const ws = new WebSocket(`${wsUrl}/api/voice/ws/listen`);

      ws.onopen = () => {
        console.log('Wake word WebSocket connected');
        setState(prev => ({ ...prev, isConnected: true, error: null }));

        // Clear reconnect timeout
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
          reconnectTimeoutRef.current = null;
        }
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          handleWebSocketMessage(message);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setState(prev => ({ ...prev, error: 'Connection error' }));
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setState(prev => ({
          ...prev,
          isConnected: false,
          isListening: false,
          sessionId: null
        }));

        // Attempt reconnect if continuous listening is enabled
        if (config.continuousListening && !reconnectTimeoutRef.current) {
          reconnectTimeoutRef.current = setTimeout(() => {
            connectWebSocket();
          }, WS_RECONNECT_DELAY);
        }
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
      setState(prev => ({ ...prev, error: 'Failed to connect' }));
    }
  }, [config.continuousListening]);

  const disconnect = () => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (sendIntervalRef.current) {
      clearInterval(sendIntervalRef.current);
      sendIntervalRef.current = null;
    }

    stopRecording();
  };

  const handleWebSocketMessage = (message: any) => {
    const { type, data } = message;

    switch (type) {
      case 'status':
        if (data.session_id) {
          setState(prev => ({ ...prev, sessionId: data.session_id }));
        }
        if (data.state) {
          setState(prev => ({ ...prev, state: data.state }));
        }
        break;

      case 'wake_word_detected':
        const detection: WakeWordDetection = {
          detected: true,
          wakeWord: data.wake_word,
          confidence: data.confidence,
          timestamp: data.timestamp,
        };
        setState(prev => ({
          ...prev,
          lastDetection: detection,
          state: 'listening_command'
        }));

        // Haptic feedback on wake word detection
        if (Platform.OS !== 'web') {
          try {
            const Haptics = require('expo-haptics');
            Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
          } catch {}
        }
        break;

      case 'transcription':
        if (data.is_command) {
          // Command received after wake word
          console.log('Command received:', data.text);
          // Reset to listening for wake word
          setState(prev => ({ ...prev, state: 'listening_wake_word' }));
        }
        break;

      case 'vad_state':
        // Voice activity detection state
        console.log('VAD state:', data);
        break;

      case 'error':
        console.error('Wake word error:', data.error);
        setState(prev => ({ ...prev, error: data.error }));
        break;
    }
  };

  const startListening = async () => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      await connectWebSocket();
      // Wait for connection
      await new Promise(resolve => setTimeout(resolve, 500));
    }

    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket not connected');
    }

    try {
      // Request microphone permission
      const { status } = await Audio.requestPermissionsAsync();
      if (status !== 'granted') {
        throw new Error('Microphone permission not granted');
      }

      // Configure audio
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
        staysActiveInBackground: true,
        shouldDuckAndroid: true,
        playThroughEarpieceAndroid: false,
      });

      // Send start listening message
      wsRef.current.send(JSON.stringify({
        type: 'start_listening',
        data: {
          config: {
            threshold: config.threshold,
            sensitivity: config.sensitivity,
            models: config.models.join(','),
          }
        }
      }));

      // Start recording
      await startRecording();

      setState(prev => ({
        ...prev,
        isListening: true,
        state: 'listening_wake_word',
        error: null
      }));

    } catch (error) {
      console.error('Failed to start listening:', error);
      setState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Failed to start listening'
      }));
      throw error;
    }
  };

  const stopListening = async () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'stop_listening',
        data: {}
      }));
    }

    await stopRecording();

    setState(prev => ({
      ...prev,
      isListening: false,
      state: 'idle'
    }));
  };

  const toggleListening = async () => {
    if (state.isListening) {
      await stopListening();
    } else {
      await startListening();
    }
  };

  const startRecording = async () => {
    try {
      // Create recording with specific settings for wake word detection
      const recording = new Audio.Recording();
      await recording.prepareToRecordAsync({
        android: {
          extension: '.wav',
          outputFormat: Audio.AndroidOutputFormat.DEFAULT,
          audioEncoder: Audio.AndroidAudioEncoder.DEFAULT,
          sampleRate: 16000,
          numberOfChannels: 1,
          bitRate: 128000,
        },
        ios: {
          extension: '.wav',
          audioQuality: Audio.IOSAudioQuality.HIGH,
          sampleRate: 16000,
          numberOfChannels: 1,
          bitRate: 128000,
          linearPCMBitDepth: 16,
          linearPCMIsBigEndian: false,
          linearPCMIsFloat: false,
        },
        web: {
          mimeType: 'audio/wav',
          sampleRate: 16000,
          numberOfChannels: 1,
        }
      });

      await recording.startAsync();
      recordingRef.current = recording;

      // Start sending audio chunks
      startAudioStreaming();

    } catch (error) {
      console.error('Failed to start recording:', error);
      throw error;
    }
  };

  const stopRecording = async () => {
    if (sendIntervalRef.current) {
      clearInterval(sendIntervalRef.current);
      sendIntervalRef.current = null;
    }

    if (recordingRef.current) {
      try {
        await recordingRef.current.stopAndUnloadAsync();
        recordingRef.current = null;
      } catch (error) {
        console.error('Failed to stop recording:', error);
      }
    }
  };

  const startAudioStreaming = () => {
    // Send audio chunks periodically
    sendIntervalRef.current = setInterval(async () => {
      if (!recordingRef.current || !wsRef.current ||
          wsRef.current.readyState !== WebSocket.OPEN ||
          isProcessingRef.current) {
        return;
      }

      try {
        isProcessingRef.current = true;

        // Get audio status
        const status = await recordingRef.current.getStatusAsync();
        if (!status.isRecording) {
          return;
        }

        // For React Native, we need to get the audio URI and read it
        // This is a simplified version - in production you'd want to use
        // a more efficient streaming method
        const uri = recordingRef.current.getURI();
        if (uri) {
          // Convert audio to base64 and send
          // Note: This is simplified - you'd want to stream chunks properly
          const audioChunk = new Uint8Array(AUDIO_CHUNK_SIZE);
          // Fill with audio data (placeholder)

          const audioBase64 = btoa(String.fromCharCode(...audioChunk));

          wsRef.current.send(JSON.stringify({
            type: 'audio_data',
            data: { audio: audioBase64 }
          }));
        }
      } catch (error) {
        console.error('Failed to send audio chunk:', error);
      } finally {
        isProcessingRef.current = false;
      }
    }, AUDIO_SEND_INTERVAL);
  };

  const updateConfig = async (updates: Partial<WakeWordConfig>) => {
    const newConfig = { ...config, ...updates };
    setConfig(newConfig);
    await saveConfig(newConfig);

    // Send config update if connected
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'configure',
        data: {
          threshold: newConfig.threshold,
          sensitivity: newConfig.sensitivity,
          models: newConfig.models.join(','),
        }
      }));
    }

    // Handle privacy mode
    if ('privacyMode' in updates) {
      if (updates.privacyMode && state.isListening) {
        await stopListening();
      }
    }
  };

  const resetDetection = () => {
    setState(prev => ({ ...prev, lastDetection: null }));
  };

  return {
    // State
    isListening: state.isListening,
    isConnected: state.isConnected,
    lastDetection: state.lastDetection,
    state: state.state,
    error: state.error,

    // Actions
    startListening,
    stopListening,
    toggleListening,
    updateConfig,
    resetDetection,

    // Config
    config,
  };
}