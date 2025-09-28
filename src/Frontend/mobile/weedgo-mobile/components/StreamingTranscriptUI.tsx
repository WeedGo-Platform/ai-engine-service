/**
 * Real-time Transcript UI with Animations
 * Provides visual feedback for streaming voice transcription
 */
import React, { useEffect, useRef, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Animated,
  TouchableOpacity,
  ScrollView,
  Dimensions,
  ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { BlurView } from 'expo-blur';

interface StreamingTranscriptUIProps {
  isRecording: boolean;
  isConnected: boolean;
  partialTranscript: string;
  finalTranscript: string;
  partialConfidence?: number; // 0-1 confidence level for partial transcript
  connectionQuality: 'excellent' | 'good' | 'fair' | 'poor' | 'critical';
  latencyMs: number;
  error: string | null;
  onStartRecording: () => void;
  onStopRecording: () => void;
  onClearTranscripts?: () => void;
  onSendTranscript?: (text: string) => void; // Callback when transcript should be sent
  audioLevel?: number; // 0-1 normalized audio level
  compact?: boolean; // Compact mode for non-blocking display
  showAlways?: boolean; // Keep UI visible even when not recording
}

const { width: SCREEN_WIDTH } = Dimensions.get('window');

export const StreamingTranscriptUI: React.FC<StreamingTranscriptUIProps> = ({
  isRecording,
  isConnected,
  partialTranscript,
  finalTranscript,
  partialConfidence = 0.5,
  connectionQuality,
  latencyMs,
  error,
  onStartRecording,
  onStopRecording,
  onClearTranscripts,
  onSendTranscript,
  audioLevel = 0,
  compact = false,
  showAlways = false,
}) => {
  // Animation values
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const waveAnim = useRef(new Animated.Value(0)).current;
  const partialOpacity = useRef(new Animated.Value(0)).current;
  const [waveformBars] = useState(
    Array(20).fill(0).map(() => new Animated.Value(0.2))
  );

  // Scroll view ref for auto-scroll
  const scrollViewRef = useRef<ScrollView>(null);

  // Pulse animation for recording button
  useEffect(() => {
    if (isRecording) {
      Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, {
            toValue: 1.2,
            duration: 1000,
            useNativeDriver: true,
          }),
          Animated.timing(pulseAnim, {
            toValue: 1,
            duration: 1000,
            useNativeDriver: true,
          }),
        ])
      ).start();
    } else {
      pulseAnim.setValue(1);
    }
  }, [isRecording, pulseAnim]);

  // Partial transcript fade-in animation
  useEffect(() => {
    if (partialTranscript) {
      Animated.sequence([
        Animated.timing(partialOpacity, {
          toValue: 1,
          duration: 200,
          useNativeDriver: true,
        }),
      ]).start();
    } else {
      Animated.timing(partialOpacity, {
        toValue: 0,
        duration: 200,
        useNativeDriver: true,
      }).start();
    }
  }, [partialTranscript, partialOpacity]);

  // Waveform animation based on audio level
  useEffect(() => {
    if (isRecording && audioLevel > 0) {
      waveformBars.forEach((bar, index) => {
        Animated.timing(bar, {
          toValue: Math.random() * audioLevel + 0.2,
          duration: 100 + Math.random() * 100,
          useNativeDriver: true,
        }).start();
      });
    } else {
      waveformBars.forEach((bar) => {
        Animated.timing(bar, {
          toValue: 0.2,
          duration: 300,
          useNativeDriver: true,
        }).start();
      });
    }
  }, [audioLevel, isRecording, waveformBars]);

  // Auto-scroll to bottom when new text appears
  useEffect(() => {
    scrollViewRef.current?.scrollToEnd({ animated: true });
  }, [finalTranscript, partialTranscript]);

  // Get connection quality color
  const getQualityColor = () => {
    switch (connectionQuality) {
      case 'excellent': return '#4CAF50';
      case 'good': return '#8BC34A';
      case 'fair': return '#FFC107';
      case 'poor': return '#FF9800';
      case 'critical': return '#F44336';
      default: return '#9E9E9E';
    }
  };

  // Get connection quality icon
  const getQualityIcon = () => {
    switch (connectionQuality) {
      case 'excellent':
      case 'good':
        return 'wifi';
      case 'fair':
        return 'cellular';
      case 'poor':
      case 'critical':
        return 'warning';
      default:
        return 'cloud-offline';
    }
  };

  // Compact mode styles (enhanced for better visibility)
  if (compact) {
    // Only show when recording or showAlways is true
    if (!isRecording && !showAlways && !finalTranscript && !partialTranscript) {
      return null;
    }

    return (
      <View style={compactStyles.container}>
        {/* Status Header with Recording Indicator */}
        <View style={compactStyles.header}>
          <View style={compactStyles.statusRow}>
            {isRecording && (
              <>
                <Animated.View
                  style={[
                    compactStyles.recordingDot,
                    {
                      opacity: pulseAnim.interpolate({
                        inputRange: [1, 1.2],
                        outputRange: [1, 0.3],
                      }),
                    },
                  ]}
                />
                <Text style={compactStyles.statusText}>Recording...</Text>
              </>
            )}
            {!isRecording && finalTranscript && (
              <Text style={compactStyles.statusText}>Transcript Ready</Text>
            )}
            {latencyMs > 0 && isRecording && (
              <Text style={compactStyles.latencyText}>({latencyMs}ms)</Text>
            )}
          </View>

          {/* Action Buttons */}
          <View style={compactStyles.actionButtons}>
            {/* Clear button when there's text */}
            {(finalTranscript || partialTranscript) && onClearTranscripts && !isRecording && (
              <TouchableOpacity onPress={onClearTranscripts} style={compactStyles.clearButton}>
                <Ionicons name="close-circle" size={20} color="#999" />
              </TouchableOpacity>
            )}

            {/* Stop button when recording */}
            {isRecording && (
              <TouchableOpacity onPress={onStopRecording} style={compactStyles.stopButton}>
                <Ionicons name="stop-circle" size={28} color="#FF5252" />
              </TouchableOpacity>
            )}
          </View>
        </View>

        {/* Enhanced Transcript Display */}
        <ScrollView
          ref={scrollViewRef}
          style={compactStyles.transcriptContainer}
          contentContainerStyle={compactStyles.transcriptContent}
          showsVerticalScrollIndicator={true}
        >
          {/* Show listening indicator when no text */}
          {isRecording && !finalTranscript && !partialTranscript && (
            <View style={compactStyles.listeningIndicator}>
              <ActivityIndicator size="small" color="#2196F3" />
              <Text style={compactStyles.listeningText}>Listening...</Text>
            </View>
          )}

          {/* Display transcript */}
          {(finalTranscript || partialTranscript) && (
            <Text style={compactStyles.transcript}>
              {finalTranscript}
              {partialTranscript && (
                <>
                  {finalTranscript && ' '}
                  <Text style={[
                    compactStyles.partialText,
                    {
                      opacity: 0.5 + (partialConfidence * 0.5),
                      color: isRecording ? '#2196F3' : '#666',
                    }
                  ]}>
                    {partialTranscript}
                  </Text>
                  {isRecording && (
                    <Text style={compactStyles.cursor}>|</Text>
                  )}
                </>
              )}
            </Text>
          )}
        </ScrollView>

        {/* Error Display */}
        {error && (
          <View style={compactStyles.errorContainer}>
            <Ionicons name="alert-circle-outline" size={14} color="#F44336" />
            <Text style={compactStyles.errorText}>{error}</Text>
          </View>
        )}

        {/* Real-time indicators */}
        {isRecording && (
          <View style={compactStyles.indicators}>
            <View style={[compactStyles.qualityDot, { backgroundColor: getQualityColor() }]} />
            <Text style={compactStyles.qualityText}>{connectionQuality}</Text>
          </View>
        )}
      </View>
    );
  }

  // Full mode (original implementation)
  return (
    <View style={styles.container}>
      {/* Connection Status Bar */}
      <View style={styles.statusBar}>
        <View style={styles.connectionStatus}>
          <Ionicons
            name={getQualityIcon() as any}
            size={16}
            color={getQualityColor()}
          />
          <Text style={[styles.statusText, { color: getQualityColor() }]}>
            {connectionQuality.toUpperCase()}
          </Text>
          {latencyMs > 0 && (
            <Text style={styles.latencyText}>{latencyMs}ms</Text>
          )}
        </View>
        {isConnected && (
          <View style={styles.connectedIndicator}>
            <View style={[styles.dot, { backgroundColor: '#4CAF50' }]} />
            <Text style={styles.connectedText}>Connected</Text>
          </View>
        )}
      </View>

      {/* Waveform Visualization */}
      {isRecording && (
        <View style={styles.waveformContainer}>
          {waveformBars.map((bar, index) => (
            <Animated.View
              key={index}
              style={[
                styles.waveformBar,
                {
                  transform: [{ scaleY: bar }],
                  backgroundColor: `hsl(${200 + index * 5}, 70%, 50%)`,
                },
              ]}
            />
          ))}
        </View>
      )}

      {/* Transcript Display */}
      <ScrollView
        ref={scrollViewRef}
        style={styles.transcriptContainer}
        contentContainerStyle={styles.transcriptContent}
        showsVerticalScrollIndicator={false}
      >
        {/* Final Transcript */}
        {finalTranscript && (
          <Text style={styles.finalTranscript}>
            {finalTranscript}
          </Text>
        )}

        {/* Partial Transcript with Confidence-based Opacity */}
        {partialTranscript && (
          <Animated.View style={{ opacity: partialOpacity }}>
            <Text
              style={[
                styles.partialTranscript,
                {
                  opacity: 0.4 + (partialConfidence * 0.6), // Soft (0.4) to solid (1.0) based on confidence
                  fontWeight: partialConfidence > 0.8 ? '500' : 'normal',
                }
              ]}
            >
              {partialTranscript}
              <Text style={[styles.cursor, { opacity: 1.0 }]}>|</Text>
            </Text>
          </Animated.View>
        )}

        {/* Listening Indicator */}
        {isRecording && !partialTranscript && !finalTranscript && (
          <View style={styles.listeningContainer}>
            <ActivityIndicator size="small" color="#666" />
            <Text style={styles.listeningText}>Listening...</Text>
          </View>
        )}

        {/* Placeholder when not recording */}
        {!isRecording && !finalTranscript && (
          <Text style={styles.placeholder}>
            Tap the microphone to start speaking
          </Text>
        )}
      </ScrollView>

      {/* Error Display */}
      {error && (
        <View style={styles.errorContainer}>
          <Ionicons name="alert-circle" size={16} color="#F44336" />
          <Text style={styles.errorText}>{error}</Text>
        </View>
      )}

      {/* Control Buttons */}
      <View style={styles.controlsContainer}>
        {/* Clear Button */}
        {finalTranscript && onClearTranscripts && (
          <TouchableOpacity
            style={styles.clearButton}
            onPress={onClearTranscripts}
          >
            <Ionicons name="trash-outline" size={24} color="#666" />
          </TouchableOpacity>
        )}

        {/* Record Button with Pulse Animation */}
        <TouchableOpacity
          style={styles.recordButtonContainer}
          onPress={isRecording ? onStopRecording : onStartRecording}
          activeOpacity={0.8}
        >
          <Animated.View
            style={[
              styles.recordButtonOuter,
              {
                transform: [{ scale: pulseAnim }],
              },
            ]}
          >
            <LinearGradient
              colors={isRecording ? ['#FF5252', '#FF1744'] : ['#2196F3', '#1976D2']}
              style={styles.recordButtonGradient}
            >
              <Ionicons
                name={isRecording ? 'stop' : 'mic'}
                size={32}
                color="white"
              />
            </LinearGradient>
          </Animated.View>

          {/* Recording Ring Animation */}
          {isRecording && (
            <Animated.View
              style={[
                styles.recordingRing,
                {
                  transform: [{ scale: pulseAnim }],
                  opacity: pulseAnim.interpolate({
                    inputRange: [1, 1.2],
                    outputRange: [0.5, 0],
                  }),
                },
              ]}
            />
          )}
        </TouchableOpacity>

        {/* Spacer for alignment */}
        <View style={{ width: 44 }} />
      </View>

      {/* Debug info removed for production */}
    </View>
  );
};

const compactStyles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 12,
    backgroundColor: 'rgba(255, 255, 255, 0.98)',
    borderRadius: 12,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
    paddingBottom: 8,
    borderBottomWidth: 0.5,
    borderBottomColor: '#e0e0e0',
  },
  statusRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  recordingDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#FF5252',
  },
  dot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  statusText: {
    fontSize: 13,
    color: '#666',
    fontWeight: '600',
  },
  latencyText: {
    fontSize: 11,
    color: '#999',
  },
  actionButtons: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  clearButton: {
    padding: 4,
  },
  stopButton: {
    padding: 4,
  },
  transcriptContainer: {
    flex: 1,
    maxHeight: 240, // Increased 3x from 80
    minHeight: 100,
    backgroundColor: '#fafafa',
    borderRadius: 8,
    padding: 2,
  },
  transcriptContent: {
    padding: 10,
    minHeight: 80,
  },
  transcript: {
    fontSize: 15,
    lineHeight: 22,
    color: '#333',
    letterSpacing: 0.2,
  },
  partialText: {
    fontStyle: 'normal',
    fontWeight: '500',
  },
  cursor: {
    color: '#2196F3',
    fontWeight: 'bold',
    fontSize: 16,
    marginLeft: 2,
  },
  listeningIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 20,
  },
  listeningText: {
    fontSize: 13,
    color: '#666',
  },
  errorContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginTop: 8,
    padding: 8,
    backgroundColor: '#FFEBEE',
    borderRadius: 6,
  },
  errorText: {
    fontSize: 11,
    color: '#F44336',
    flex: 1,
  },
  indicators: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginTop: 8,
  },
  qualityDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  qualityText: {
    fontSize: 10,
    color: '#999',
    textTransform: 'uppercase',
  },
});

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  statusBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 8,
    backgroundColor: 'white',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  connectionStatus: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  statusText: {
    fontSize: 12,
    fontWeight: '600',
  },
  latencyText: {
    fontSize: 11,
    color: '#666',
    marginLeft: 4,
  },
  connectedIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  connectedText: {
    fontSize: 12,
    color: '#666',
  },
  waveformContainer: {
    height: 60,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 20,
    gap: 3,
    backgroundColor: 'white',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  waveformBar: {
    width: 3,
    height: 40,
    borderRadius: 2,
    backgroundColor: '#2196F3',
  },
  transcriptContainer: {
    flex: 1,
    backgroundColor: 'white',
  },
  transcriptContent: {
    padding: 20,
    minHeight: '100%',
  },
  finalTranscript: {
    fontSize: 16,
    lineHeight: 24,
    color: '#333',
    marginBottom: 12,
  },
  partialTranscript: {
    fontSize: 16,
    lineHeight: 24,
    color: '#555',
    fontStyle: 'normal', // Remove italic for cleaner look with opacity
  },
  cursor: {
    color: '#2196F3',
    fontWeight: 'bold',
    fontSize: 18,
  },
  listeningContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    marginTop: 40,
  },
  listeningText: {
    fontSize: 14,
    color: '#666',
  },
  placeholder: {
    fontSize: 16,
    color: '#999',
    textAlign: 'center',
    marginTop: 40,
  },
  errorContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#FFEBEE',
    paddingHorizontal: 16,
    paddingVertical: 12,
    marginHorizontal: 16,
    marginBottom: 8,
    borderRadius: 8,
  },
  errorText: {
    color: '#F44336',
    fontSize: 13,
    flex: 1,
  },
  controlsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 20,
    backgroundColor: 'white',
    borderTopWidth: 1,
    borderTopColor: '#e0e0e0',
  },
  clearButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#f5f5f5',
    justifyContent: 'center',
    alignItems: 'center',
  },
  recordButtonContainer: {
    position: 'relative',
    alignItems: 'center',
    justifyContent: 'center',
  },
  recordButtonOuter: {
    width: 72,
    height: 72,
    borderRadius: 36,
    overflow: 'hidden',
    elevation: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
  },
  recordButtonGradient: {
    width: '100%',
    height: '100%',
    justifyContent: 'center',
    alignItems: 'center',
  },
  recordingRing: {
    position: 'absolute',
    width: 72,
    height: 72,
    borderRadius: 36,
    borderWidth: 2,
    borderColor: '#FF5252',
  },
  debugInfo: {
    position: 'absolute',
    bottom: 100,
    left: 0,
    right: 0,
    backgroundColor: 'rgba(0,0,0,0.7)',
    padding: 8,
  },
  debugText: {
    color: 'white',
    fontSize: 10,
    textAlign: 'center',
  },
});