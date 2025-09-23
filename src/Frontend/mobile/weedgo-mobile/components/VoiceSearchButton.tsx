import React, { useState, useEffect } from 'react';
import {
  TouchableOpacity,
  View,
  Text,
  StyleSheet,
  Animated,
  Modal,
  ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Colors } from '@/constants/Colors';
import { voiceService } from '@/services/voice';

interface VoiceSearchButtonProps {
  onSearchComplete: (query: string) => void;
  onError?: (error: string) => void;
  size?: number;
  color?: string;
}

export const VoiceSearchButton: React.FC<VoiceSearchButtonProps> = ({
  onSearchComplete,
  onError,
  size = 24,
  color = Colors.light.primary,
}) => {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const pulseAnim = useState(new Animated.Value(1))[0];

  useEffect(() => {
    if (isRecording) {
      // Create pulsing animation when recording
      Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, {
            toValue: 1.2,
            duration: 500,
            useNativeDriver: true,
          }),
          Animated.timing(pulseAnim, {
            toValue: 1,
            duration: 500,
            useNativeDriver: true,
          }),
        ])
      ).start();
    } else {
      pulseAnim.setValue(1);
    }
  }, [isRecording, pulseAnim]);

  const handlePress = async () => {
    if (isRecording) {
      // Stop recording
      await stopRecording();
    } else {
      // Start recording
      await startRecording();
    }
  };

  const startRecording = async () => {
    try {
      // Request permissions first if needed
      const hasPermission = await voiceService.requestPermissions();
      if (!hasPermission) {
        onError?.('Microphone permission is required for voice search');
        return;
      }

      setShowModal(true);
      setIsRecording(true);

      // Provide haptic feedback
      await voiceService.provideHapticFeedback('light');

      // Start recording
      const started = await voiceService.startRecording();
      if (!started) {
        setIsRecording(false);
        setShowModal(false);
        onError?.('Failed to start voice recording');
        return;
      }

      // Auto-stop after 10 seconds
      setTimeout(async () => {
        if (voiceService.getIsRecording()) {
          await stopRecording();
        }
      }, 10000);
    } catch (error) {
      console.error('Failed to start recording:', error);
      setIsRecording(false);
      setShowModal(false);
      onError?.('Failed to start voice search');
    }
  };

  const stopRecording = async () => {
    try {
      setIsRecording(false);
      setIsProcessing(true);

      // Provide haptic feedback
      await voiceService.provideHapticFeedback('medium');

      // Stop recording and get audio file
      const result = await voiceService.stopRecording();

      if (result.success && result.uri) {
        // Transcribe audio
        const transcript = await voiceService.transcribeAudio(result.uri);

        if (transcript) {
          onSearchComplete(transcript);
          // Speak confirmation
          await voiceService.speak(`Searching for ${transcript}`);
        } else {
          onError?.('Could not understand. Please try again.');
        }
      } else {
        onError?.(result.error || 'Recording failed');
      }
    } catch (error) {
      console.error('Failed to stop recording:', error);
      onError?.('Failed to process voice search');
    } finally {
      setIsProcessing(false);
      setShowModal(false);
    }
  };

  const handleCancel = async () => {
    await voiceService.cancelRecording();
    setIsRecording(false);
    setIsProcessing(false);
    setShowModal(false);
  };

  return (
    <>
      <TouchableOpacity onPress={handlePress} style={styles.button}>
        <Ionicons name="mic-outline" size={size} color={color} />
      </TouchableOpacity>

      <Modal
        visible={showModal}
        transparent
        animationType="fade"
        onRequestClose={handleCancel}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            {isRecording ? (
              <>
                <Animated.View
                  style={[
                    styles.microphoneContainer,
                    {
                      transform: [{ scale: pulseAnim }],
                    },
                  ]}
                >
                  <View style={styles.recordingIndicator}>
                    <Ionicons name="mic" size={48} color="white" />
                  </View>
                </Animated.View>
                <Text style={styles.modalTitle}>Listening...</Text>
                <Text style={styles.modalSubtitle}>Tap to stop</Text>
                <TouchableOpacity
                  style={styles.stopButton}
                  onPress={stopRecording}
                >
                  <Ionicons name="stop-circle" size={64} color={Colors.light.error} />
                </TouchableOpacity>
              </>
            ) : isProcessing ? (
              <>
                <ActivityIndicator size="large" color={Colors.light.primary} />
                <Text style={styles.modalTitle}>Processing...</Text>
                <Text style={styles.modalSubtitle}>Converting speech to text</Text>
              </>
            ) : null}

            {!isProcessing && (
              <TouchableOpacity
                style={styles.cancelButton}
                onPress={handleCancel}
              >
                <Text style={styles.cancelText}>Cancel</Text>
              </TouchableOpacity>
            )}
          </View>
        </View>
      </Modal>
    </>
  );
};

const styles = StyleSheet.create({
  button: {
    padding: 8,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.8)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalContent: {
    backgroundColor: Colors.light.card,
    borderRadius: 20,
    padding: 32,
    alignItems: 'center',
    minWidth: 280,
  },
  microphoneContainer: {
    marginBottom: 24,
  },
  recordingIndicator: {
    width: 120,
    height: 120,
    borderRadius: 60,
    backgroundColor: Colors.light.primary,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: Colors.light.primary,
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.3,
    shadowRadius: 10,
    elevation: 5,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: Colors.light.text,
    marginBottom: 8,
  },
  modalSubtitle: {
    fontSize: 14,
    color: Colors.light.gray,
    marginBottom: 24,
  },
  stopButton: {
    marginTop: 16,
  },
  cancelButton: {
    marginTop: 16,
    paddingHorizontal: 24,
    paddingVertical: 12,
  },
  cancelText: {
    fontSize: 16,
    color: Colors.light.gray,
  },
});