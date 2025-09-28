/**
 * Voice Transcript Overlay Component
 * Displays real-time transcription in a prominent, user-friendly overlay
 */
import React, { useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Animated,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  Dimensions,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { BlurView } from 'expo-blur';
import { AudioWaveform } from './chat/AudioWaveform';

interface VoiceTranscriptOverlayProps {
  isVisible: boolean;
  isRecording: boolean;
  transcript: string;
  isPartial: boolean;
  error: string | null;
  onStop: () => void;
  onDismiss?: () => void;
  isSpeaking?: boolean;
  noiseLevel?: number;
  detectedLanguage?: string | null;
  currentLanguage?: string;
}

const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get('window');

export const VoiceTranscriptOverlay: React.FC<VoiceTranscriptOverlayProps> = ({
  isVisible,
  isRecording,
  transcript,
  isPartial,
  error,
  onStop,
  onDismiss,
  isSpeaking = false,
  noiseLevel = 0,
  detectedLanguage = null,
  currentLanguage = 'en-US',
}) => {
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const scaleAnim = useRef(new Animated.Value(0.9)).current;
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const scrollViewRef = useRef<ScrollView>(null);

  // Fade in/out animation
  useEffect(() => {
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: isVisible ? 1 : 0,
        duration: 300,
        useNativeDriver: true,
      }),
      Animated.timing(scaleAnim, {
        toValue: isVisible ? 1 : 0.9,
        duration: 300,
        useNativeDriver: true,
      }),
    ]).start();
  }, [isVisible]);

  // Pulse animation for recording indicator
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
  }, [isRecording]);

  // Auto-scroll to bottom
  useEffect(() => {
    if (transcript) {
      scrollViewRef.current?.scrollToEnd({ animated: true });
    }
  }, [transcript]);

  if (!isVisible) return null;

  return (
    <Animated.View
      style={[
        styles.overlay,
        {
          opacity: fadeAnim,
          transform: [{ scale: scaleAnim }],
        },
      ]}
    >
      <BlurView intensity={95} tint="light" style={styles.container}>
        {/* Header */}
        <View style={styles.header}>
          <View style={styles.titleRow}>
            <Animated.View
              style={[
                styles.recordingIndicator,
                {
                  transform: [{ scale: pulseAnim }],
                },
              ]}
            />
            <View style={styles.titleContainer}>
              <Text style={styles.title}>
                {isSpeaking ? 'Speaking Detected' :
                 isRecording ? 'Listening...' : 'Processing...'}
              </Text>
              {detectedLanguage && detectedLanguage !== currentLanguage && (
                <Text style={styles.languageIndicator}>
                  Detected: {detectedLanguage.split('-')[0].toUpperCase()}
                </Text>
              )}
            </View>
          </View>

          <View style={styles.headerActions}>
            {/* Stop & Send Button */}
            <TouchableOpacity
              onPress={onStop}
              style={styles.stopButton}
              activeOpacity={0.7}
            >
              <View style={styles.stopButtonInner}>
                <Ionicons name="send" size={20} color="#FFF" />
                <Text style={styles.stopButtonText}>Stop & Send</Text>
              </View>
            </TouchableOpacity>

            {/* Dismiss Button */}
            {onDismiss && (
              <TouchableOpacity
                onPress={onDismiss}
                style={styles.dismissButton}
                activeOpacity={0.7}
              >
                <Ionicons name="close" size={24} color="#666" />
              </TouchableOpacity>
            )}
          </View>
        </View>

        {/* Transcript Area */}
        <ScrollView
          ref={scrollViewRef}
          style={styles.transcriptContainer}
          contentContainerStyle={styles.transcriptContent}
          showsVerticalScrollIndicator={false}
        >
          {transcript ? (
            <Text style={[
              styles.transcriptText,
              isPartial && styles.partialText,
            ]}>
              {transcript}
              {isPartial && isRecording && (
                <Text style={styles.cursor}>|</Text>
              )}
            </Text>
          ) : (
            <View style={styles.waitingContainer}>
              <ActivityIndicator size="large" color="#667eea" />
              <Text style={styles.waitingText}>
                Start speaking...
              </Text>
            </View>
          )}
        </ScrollView>

        {/* Error Message */}
        {error && (
          <View style={styles.errorContainer}>
            <Ionicons name="alert-circle" size={16} color="#FF5252" />
            <Text style={styles.errorText}>{error}</Text>
          </View>
        )}

        {/* Audio Waveform Visualizer */}
        {isRecording && (
          <AudioWaveform
            isRecording={isRecording}
            audioLevel={noiseLevel}
            isSpeaking={isSpeaking}
            style={styles.waveformContainer}
          />
        )}

        {/* Old Visual Waveform (hidden) */}
        {false && (
          <View style={styles.waveformContainer}>
            {[...Array(20)].map((_, i) => (
              <Animated.View
                key={i}
                style={[
                  styles.waveformBar,
                  {
                    height: isSpeaking ?
                      Math.random() * 30 + 20 :  // Higher bars when speaking
                      Math.random() * 10 + 5,     // Lower bars when silent
                    backgroundColor: isSpeaking ?
                      `hsl(${120}, 70%, 60%)` :   // Green when speaking
                      `hsl(${250 + i * 2}, 70%, 60%)`,  // Purple when listening
                  },
                ]}
              />
            ))}
          </View>
        )}

        {/* Instructions */}
        <View style={styles.footer}>
          <Text style={styles.instructions}>
            Speak clearly • Sentences will auto-send • 2 second pause to stop
          </Text>
          {currentLanguage && (
            <Text style={styles.languageInfo}>
              Language: {currentLanguage.split('-')[0].toUpperCase()}
            </Text>
          )}
        </View>
      </BlurView>
    </Animated.View>
  );
};

const styles = StyleSheet.create({
  overlay: {
    position: 'absolute',
    bottom: 100,
    left: 20,
    right: 20,
    maxHeight: SCREEN_HEIGHT * 0.4,
    zIndex: 1000,
    elevation: 10,
  },
  container: {
    borderRadius: 20,
    overflow: 'hidden',
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 12,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(0, 0, 0, 0.05)',
  },
  titleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    flex: 1,
  },
  titleContainer: {
    flex: 1,
  },
  languageIndicator: {
    fontSize: 12,
    color: '#667eea',
    marginTop: 2,
    fontWeight: '500',
  },
  recordingIndicator: {
    width: 12,
    height: 12,
    borderRadius: 6,
    backgroundColor: '#FF5252',
  },
  title: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },
  headerActions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  stopButton: {
    borderRadius: 20,
    overflow: 'hidden',
    backgroundColor: '#667eea',
  },
  stopButtonInner: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 10,
    gap: 6,
  },
  stopButtonText: {
    color: '#FFF',
    fontSize: 14,
    fontWeight: '600',
  },
  dismissButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: 'rgba(0, 0, 0, 0.05)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  transcriptContainer: {
    minHeight: 100,
    maxHeight: 200,
    paddingHorizontal: 16,
  },
  transcriptContent: {
    paddingVertical: 16,
  },
  transcriptText: {
    fontSize: 18,
    lineHeight: 26,
    color: '#222',
    letterSpacing: 0.3,
  },
  partialText: {
    color: '#666',
  },
  cursor: {
    color: '#667eea',
    fontWeight: 'bold',
    fontSize: 20,
  },
  waitingContainer: {
    alignItems: 'center',
    paddingVertical: 30,
    gap: 12,
  },
  waitingText: {
    fontSize: 14,
    color: '#999',
  },
  errorContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#FFEBEE',
    padding: 12,
    marginHorizontal: 16,
    marginBottom: 12,
    borderRadius: 8,
  },
  errorText: {
    flex: 1,
    fontSize: 13,
    color: '#FF5252',
  },
  waveformContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 2,
    paddingVertical: 12,
    paddingHorizontal: 16,
  },
  waveformBar: {
    width: 3,
    borderRadius: 2,
  },
  footer: {
    backgroundColor: 'rgba(0, 0, 0, 0.02)',
    paddingVertical: 8,
    paddingHorizontal: 16,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  instructions: {
    fontSize: 11,
    color: '#999',
    flex: 1,
  },
  languageInfo: {
    fontSize: 11,
    color: '#667eea',
    fontWeight: '500',
  },
});