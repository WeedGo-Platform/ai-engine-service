/**
 * WebRTC-based Voice Transcription Hook
 * Provides ultra-low latency streaming with automatic failover
 */
import { useState, useRef, useCallback, useEffect } from 'react';
import { Platform } from 'react-native';

interface WebRTCConfig {
  iceServers: RTCIceServer[];
  apiUrl: string;
  enableDataChannel: boolean;
  enableAudioTrack: boolean;
}

interface WebRTCState {
  isConnected: boolean;
  connectionState: RTCPeerConnectionState;
  iceConnectionState: RTCIceConnectionState;
  signalingState: RTCSignalingState;
  error: string | null;
}

const DEFAULT_CONFIG: WebRTCConfig = {
  iceServers: [
    { urls: 'stun:stun.l.google.com:19302' },
    { urls: 'stun:stun1.l.google.com:19302' }
  ],
  apiUrl: 'http://10.0.0.169:5024/api/voice/rtc',
  enableDataChannel: true,
  enableAudioTrack: true,
};

export const useWebRTCTranscription = (config: Partial<WebRTCConfig> = {}) => {
  const mergedConfig = { ...DEFAULT_CONFIG, ...config };

  const [state, setState] = useState<WebRTCState>({
    isConnected: false,
    connectionState: 'new',
    iceConnectionState: 'new',
    signalingState: 'stable',
    error: null,
  });

  const peerConnectionRef = useRef<RTCPeerConnection | null>(null);
  const dataChannelRef = useRef<RTCDataChannel | null>(null);
  const localStreamRef = useRef<MediaStream | null>(null);

  /**
   * Initialize WebRTC connection
   */
  const initializeWebRTC = useCallback(async () => {
    try {
      console.log('[WebRTC] Initializing connection...');

      // Create peer connection
      const pc = new RTCPeerConnection({
        iceServers: mergedConfig.iceServers,
      });

      // Set up event handlers
      pc.oniceconnectionstatechange = () => {
        console.log(`[WebRTC] ICE state: ${pc.iceConnectionState}`);
        setState(prev => ({
          ...prev,
          iceConnectionState: pc.iceConnectionState,
          isConnected: pc.iceConnectionState === 'connected',
        }));
      };

      pc.onconnectionstatechange = () => {
        console.log(`[WebRTC] Connection state: ${pc.connectionState}`);
        setState(prev => ({
          ...prev,
          connectionState: pc.connectionState,
        }));
      };

      pc.onsignalingstatechange = () => {
        console.log(`[WebRTC] Signaling state: ${pc.signalingState}`);
        setState(prev => ({
          ...prev,
          signalingState: pc.signalingState,
        }));
      };

      // Create data channel for audio chunks
      if (mergedConfig.enableDataChannel) {
        const dataChannel = pc.createDataChannel('audio-stream', {
          ordered: true,
          maxRetransmits: 3,
        });

        dataChannel.onopen = () => {
          console.log('[WebRTC] Data channel opened');
        };

        dataChannel.onmessage = (event) => {
          // Handle transcription results
          try {
            const message = JSON.parse(event.data);
            handleTranscriptionMessage(message);
          } catch (error) {
            console.error('[WebRTC] Failed to parse message:', error);
          }
        };

        dataChannel.onerror = (error) => {
          console.error('[WebRTC] Data channel error:', error);
          setState(prev => ({ ...prev, error: 'Data channel error' }));
        };

        dataChannelRef.current = dataChannel;
      }

      // Add audio track if enabled
      if (mergedConfig.enableAudioTrack) {
        try {
          const stream = await navigator.mediaDevices.getUserMedia({
            audio: {
              echoCancellation: true,
              noiseSuppression: true,
              autoGainControl: true,
              sampleRate: 16000,
            },
          });

          stream.getTracks().forEach(track => {
            pc.addTrack(track, stream);
          });

          localStreamRef.current = stream;
        } catch (error) {
          console.error('[WebRTC] Failed to get user media:', error);
        }
      }

      peerConnectionRef.current = pc;

      // Create and send offer
      const offer = await pc.createOffer();
      await pc.setLocalDescription(offer);

      // Send offer to signaling server
      const response = await fetch(`${mergedConfig.apiUrl}/offer`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          offer: offer,
          config: {
            enableDataChannel: mergedConfig.enableDataChannel,
            enableAudioTrack: mergedConfig.enableAudioTrack,
          },
        }),
      });

      if (response.ok) {
        const { answer } = await response.json();
        await pc.setRemoteDescription(answer);
        console.log('[WebRTC] Connection established');
      } else {
        throw new Error('Failed to get answer from server');
      }

      return true;
    } catch (error) {
      console.error('[WebRTC] Initialization failed:', error);
      setState(prev => ({ ...prev, error: String(error) }));
      return false;
    }
  }, [mergedConfig]);

  /**
   * Send audio chunk via DataChannel
   */
  const sendAudioChunk = useCallback((audioData: ArrayBuffer) => {
    if (dataChannelRef.current && dataChannelRef.current.readyState === 'open') {
      try {
        // Send as binary data for efficiency
        dataChannelRef.current.send(audioData);
        return true;
      } catch (error) {
        console.error('[WebRTC] Failed to send audio chunk:', error);
        return false;
      }
    }
    return false;
  }, []);

  /**
   * Handle incoming transcription messages
   */
  const handleTranscriptionMessage = useCallback((message: any) => {
    switch (message.type) {
      case 'partial':
        console.log('[WebRTC] Partial transcript:', message.text);
        break;
      case 'final':
        console.log('[WebRTC] Final transcript:', message.text);
        break;
      case 'error':
        console.error('[WebRTC] Server error:', message.error);
        break;
      default:
        console.log('[WebRTC] Unknown message type:', message.type);
    }
  }, []);

  /**
   * Close WebRTC connection
   */
  const closeConnection = useCallback(() => {
    console.log('[WebRTC] Closing connection...');

    if (dataChannelRef.current) {
      dataChannelRef.current.close();
      dataChannelRef.current = null;
    }

    if (localStreamRef.current) {
      localStreamRef.current.getTracks().forEach(track => track.stop());
      localStreamRef.current = null;
    }

    if (peerConnectionRef.current) {
      peerConnectionRef.current.close();
      peerConnectionRef.current = null;
    }

    setState({
      isConnected: false,
      connectionState: 'closed',
      iceConnectionState: 'closed',
      signalingState: 'closed',
      error: null,
    });
  }, []);

  /**
   * Check connection quality
   */
  const getConnectionQuality = useCallback(async (): Promise<'excellent' | 'good' | 'poor'> => {
    if (!peerConnectionRef.current) return 'poor';

    try {
      const stats = await peerConnectionRef.current.getStats();
      let totalRtt = 0;
      let count = 0;

      stats.forEach((report) => {
        if (report.type === 'candidate-pair' && report.state === 'succeeded') {
          if (report.currentRoundTripTime) {
            totalRtt += report.currentRoundTripTime * 1000; // Convert to ms
            count++;
          }
        }
      });

      if (count > 0) {
        const avgRtt = totalRtt / count;
        if (avgRtt < 50) return 'excellent';
        if (avgRtt < 150) return 'good';
      }
    } catch (error) {
      console.error('[WebRTC] Failed to get stats:', error);
    }

    return 'poor';
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      closeConnection();
    };
  }, [closeConnection]);

  return {
    // State
    isConnected: state.isConnected,
    connectionState: state.connectionState,
    iceConnectionState: state.iceConnectionState,
    error: state.error,

    // Actions
    initialize: initializeWebRTC,
    sendAudioChunk,
    closeConnection,
    getConnectionQuality,
  };
};