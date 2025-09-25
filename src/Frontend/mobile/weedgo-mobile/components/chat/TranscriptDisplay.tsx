import React, { useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Animated,
  Dimensions,
} from 'react-native';
import { BlurView } from 'expo-blur';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';

interface TranscriptDisplayProps {
  transcript: string;
  isRecording: boolean;
  isProcessing?: boolean;
  error?: string | null;
}

const { width } = Dimensions.get('window');

export function TranscriptDisplay({
  transcript,
  isRecording,
  isProcessing = false,
  error,
}: TranscriptDisplayProps) {
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(30)).current;
  const pulseAnim = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    if (isRecording || transcript || isProcessing || error) {
      Animated.parallel([
        Animated.timing(fadeAnim, {
          toValue: 1,
          duration: 300,
          useNativeDriver: true,
        }),
        Animated.spring(slideAnim, {
          toValue: 0,
          friction: 8,
          tension: 40,
          useNativeDriver: true,
        }),
      ]).start();

      if (isRecording) {
        Animated.loop(
          Animated.sequence([
            Animated.timing(pulseAnim, {
              toValue: 1.05,
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
      }
    } else {
      Animated.parallel([
        Animated.timing(fadeAnim, {
          toValue: 0,
          duration: 200,
          useNativeDriver: true,
        }),
        Animated.timing(slideAnim, {
          toValue: 30,
          duration: 200,
          useNativeDriver: true,
        }),
      ]).start();

      pulseAnim.stopAnimation();
      pulseAnim.setValue(1);
    }
  }, [isRecording, transcript, isProcessing, error]);

  if (!isRecording && !transcript && !isProcessing && !error) {
    return null;
  }

  return (
    <Animated.View
      style={[
        styles.container,
        {
          opacity: fadeAnim,
          transform: [
            { translateY: slideAnim },
            { scale: pulseAnim },
          ],
        },
      ]}
    >
      <BlurView intensity={95} tint="dark" style={styles.blurContainer}>
        <LinearGradient
          colors={['rgba(30, 30, 30, 0.9)', 'rgba(20, 20, 20, 0.95)']}
          style={styles.gradient}
          start={{ x: 0, y: 0 }}
          end={{ x: 0, y: 1 }}
        >
          {/* Header */}
          <View style={styles.header}>
            <View style={styles.headerLeft}>
              {isRecording && (
                <>
                  <Animated.View style={styles.recordingDot} />
                  <Text style={styles.statusText}>Listening...</Text>
                </>
              )}
              {isProcessing && !isRecording && (
                <>
                  <View style={styles.processingIndicator}>
                    <Ionicons name="sync" size={16} color="#4A90E2" />
                  </View>
                  <Text style={styles.statusText}>Processing...</Text>
                </>
              )}
              {!isRecording && !isProcessing && transcript && (
                <>
                  <Ionicons name="checkmark-circle" size={16} color="#4CAF50" />
                  <Text style={styles.statusText}>Transcribed</Text>
                </>
              )}
              {error && (
                <>
                  <Ionicons name="alert-circle" size={16} color="#FF6B6B" />
                  <Text style={[styles.statusText, styles.errorText]}>Error</Text>
                </>
              )}
            </View>

            {/* Sound wave visualization */}
            {isRecording && (
              <View style={styles.soundWaves}>
                {[...Array(5)].map((_, i) => (
                  <Animated.View
                    key={i}
                    style={[
                      styles.soundBar,
                      {
                        transform: [
                          {
                            scaleY: pulseAnim.interpolate({
                              inputRange: [1, 1.05],
                              outputRange: [0.3 + Math.random() * 0.7, 0.5 + Math.random() * 0.5],
                            }),
                          },
                        ],
                      },
                    ]}
                  />
                ))}
              </View>
            )}
          </View>

          {/* Transcript content */}
          <View style={styles.content}>
            {error ? (
              <Text style={styles.errorMessage}>{error}</Text>
            ) : transcript ? (
              <Text style={styles.transcript}>{transcript}</Text>
            ) : isRecording ? (
              <View style={styles.listeningContainer}>
                <Text style={styles.listeningText}>Speak clearly into the microphone...</Text>
                <View style={styles.tips}>
                  <Text style={styles.tipText}>• Speak naturally and clearly</Text>
                  <Text style={styles.tipText}>• Avoid background noise</Text>
                  <Text style={styles.tipText}>• Tap stop when finished</Text>
                </View>
              </View>
            ) : isProcessing ? (
              <Text style={styles.processingText}>Converting speech to text...</Text>
            ) : null}
          </View>

          {/* Footer with confidence indicator */}
          {transcript && !isRecording && !isProcessing && (
            <View style={styles.footer}>
              <View style={styles.confidenceBar}>
                <View style={[styles.confidenceFill, { width: '85%' }]} />
              </View>
              <Text style={styles.confidenceText}>High confidence</Text>
            </View>
          )}
        </LinearGradient>
      </BlurView>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    bottom: 100,
    left: 16,
    right: 16,
    maxWidth: width - 32,
    borderRadius: 16,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 4,
    },
    shadowOpacity: 0.3,
    shadowRadius: 12,
    elevation: 8,
  },
  blurContainer: {
    borderRadius: 16,
    overflow: 'hidden',
  },
  gradient: {
    padding: 16,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  recordingDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#FF4757',
    shadowColor: '#FF4757',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.8,
    shadowRadius: 4,
  },
  processingIndicator: {
    animation: 'spin 1s linear infinite',
  },
  statusText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '600',
  },
  errorText: {
    color: '#FF6B6B',
  },
  soundWaves: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 2,
  },
  soundBar: {
    width: 3,
    height: 16,
    backgroundColor: '#4A90E2',
    borderRadius: 1.5,
  },
  content: {
    minHeight: 60,
    justifyContent: 'center',
  },
  transcript: {
    color: '#FFFFFF',
    fontSize: 16,
    lineHeight: 24,
    fontWeight: '500',
  },
  listeningContainer: {
    gap: 12,
  },
  listeningText: {
    color: 'rgba(255, 255, 255, 0.9)',
    fontSize: 15,
    textAlign: 'center',
  },
  tips: {
    gap: 4,
  },
  tipText: {
    color: 'rgba(255, 255, 255, 0.6)',
    fontSize: 12,
    paddingLeft: 8,
  },
  processingText: {
    color: 'rgba(255, 255, 255, 0.8)',
    fontSize: 14,
    textAlign: 'center',
    fontStyle: 'italic',
  },
  errorMessage: {
    color: '#FF6B6B',
    fontSize: 14,
    textAlign: 'center',
  },
  footer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: 'rgba(255, 255, 255, 0.1)',
  },
  confidenceBar: {
    flex: 1,
    height: 4,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 2,
    overflow: 'hidden',
  },
  confidenceFill: {
    height: '100%',
    backgroundColor: '#4CAF50',
    borderRadius: 2,
  },
  confidenceText: {
    color: 'rgba(255, 255, 255, 0.6)',
    fontSize: 11,
  },
});