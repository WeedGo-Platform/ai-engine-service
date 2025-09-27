/**
 * Streaming Voice Screen
 * Complete integration of real-time voice transcription with UI
 */
import React from 'react';
import {
  SafeAreaView,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { useStreamingTranscription } from '../hooks/useStreamingTranscription';
import { StreamingTranscriptUI } from '../components/StreamingTranscriptUI';

export const StreamingVoiceScreen: React.FC = () => {
  // Use the streaming transcription hook
  const {
    isRecording,
    isConnected,
    partialTranscript,
    finalTranscript,
    connectionQuality,
    latencyMs,
    error,
    startRecording,
    stopRecording,
    clearTranscripts,
    connectWebSocket,
    disconnect,
    metrics,
  } = useStreamingTranscription({
    chunkDurationMs: 250, // 250ms chunks for real-time streaming
    apiUrl: __DEV__
      ? Platform.select({
          ios: 'ws://localhost:5024/api/voice/ws/stream',
          android: 'ws://10.0.2.2:5024/api/voice/ws/stream',
          default: 'ws://localhost:5024/api/voice/ws/stream',
        })
      : 'wss://your-production-server.com/api/voice/ws/stream',
    enableWebRTC: true,
    autoReconnect: true,
  });

  // Connect WebSocket on mount
  React.useEffect(() => {
    connectWebSocket();

    // Cleanup on unmount
    return () => {
      disconnect();
    };
  }, []);

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView
        style={styles.container}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        <StreamingTranscriptUI
          isRecording={isRecording}
          isConnected={isConnected}
          partialTranscript={partialTranscript}
          finalTranscript={finalTranscript}
          connectionQuality={connectionQuality}
          latencyMs={latencyMs}
          error={error}
          onStartRecording={startRecording}
          onStopRecording={stopRecording}
          onClearTranscripts={clearTranscripts}
          audioLevel={0} // TODO: Connect actual audio level from recording
        />
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
});