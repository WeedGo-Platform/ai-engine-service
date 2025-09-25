import { useState, useRef, useCallback } from 'react';
import { Audio } from 'expo-av';
import { Alert } from 'react-native';
import * as FileSystem from 'expo-file-system';
import * as Haptics from 'expo-haptics';

const API_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:5024';

interface UseEnhancedTranscriptionOptions {
  onTranscription?: (text: string) => void;
  onError?: (error: any) => void;
  onStatusChange?: (status: TranscriptionStatus) => void;
  maxDuration?: number; // Maximum recording duration in milliseconds
  autoStop?: boolean; // Auto stop after silence detection
  language?: string; // Language code for better transcription
}

export type TranscriptionStatus =
  | 'idle'
  | 'requesting-permission'
  | 'recording'
  | 'processing'
  | 'transcribing'
  | 'completed'
  | 'error';

interface TranscriptionResult {
  text: string;
  confidence?: number;
  language?: string;
  duration?: number;
}

export function useEnhancedTranscription(options: UseEnhancedTranscriptionOptions = {}) {
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [status, setStatus] = useState<TranscriptionStatus>('idle');
  const [error, setError] = useState<string | null>(null);
  const [recordingDuration, setRecordingDuration] = useState(0);
  const [audioLevel, setAudioLevel] = useState(0);

  const recording = useRef<Audio.Recording>();
  const durationInterval = useRef<NodeJS.Timeout>();
  const silenceTimeout = useRef<NodeJS.Timeout>();

  const updateStatus = useCallback((newStatus: TranscriptionStatus) => {
    setStatus(newStatus);
    options.onStatusChange?.(newStatus);
  }, [options]);

  const startRecording = async () => {
    try {
      setError(null);
      updateStatus('requesting-permission');

      // Request permissions
      const { status } = await Audio.requestPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert(
          'Microphone Permission Required',
          'Please enable microphone access in your device settings to use voice recording.',
          [
            { text: 'Cancel', style: 'cancel' },
            { text: 'Open Settings', onPress: () => {
              // Open app settings
              // Note: This would need expo-linking in a real implementation
            }},
          ]
        );
        updateStatus('idle');
        return false;
      }

      // Configure audio for optimal recording
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
        staysActiveInBackground: false,
        shouldDuckAndroid: true,
        playThroughEarpieceAndroid: false,
      });

      // Create recording with high quality settings
      const recordingOptions = {
        ...Audio.RecordingOptionsPresets.HIGH_QUALITY,
        ios: {
          ...Audio.RecordingOptionsPresets.HIGH_QUALITY.ios,
          outputFormat: Audio.IOSOutputFormat.MPEG4AAC,
          audioQuality: Audio.IOSAudioQuality.MAX,
          sampleRate: 44100,
          numberOfChannels: 1,
          bitRate: 128000,
          linearPCMBitDepth: 16,
          linearPCMIsBigEndian: false,
          linearPCMIsFloat: false,
        },
        android: {
          ...Audio.RecordingOptionsPresets.HIGH_QUALITY.android,
          outputFormat: Audio.AndroidOutputFormat.AAC_ADTS,
          audioEncoder: Audio.AndroidAudioEncoder.AAC,
          sampleRate: 44100,
          numberOfChannels: 1,
          bitRate: 128000,
        },
      };

      const { recording: rec, status: recordingStatus } = await Audio.Recording.createAsync(
        recordingOptions,
        (status) => {
          // Update audio levels for visualization
          if (status.isRecording && status.metering) {
            const normalizedLevel = Math.min(1, Math.max(0, (status.metering + 160) / 160));
            setAudioLevel(normalizedLevel);
          }
        },
        100 // Update interval in ms
      );

      recording.current = rec;
      setIsRecording(true);
      setTranscript('');
      setRecordingDuration(0);
      updateStatus('recording');

      // Haptic feedback
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);

      // Start duration counter
      const startTime = Date.now();
      durationInterval.current = setInterval(() => {
        const duration = Date.now() - startTime;
        setRecordingDuration(duration);

        // Auto-stop if max duration reached
        if (options.maxDuration && duration >= options.maxDuration) {
          stopRecording();
        }
      }, 100);

      // Setup silence detection for auto-stop
      if (options.autoStop) {
        // This would need actual audio level monitoring
        // For now, just a placeholder timeout
        silenceTimeout.current = setTimeout(() => {
          if (recording.current) {
            stopRecording();
          }
        }, 30000); // 30 seconds max
      }

      console.log('Recording started successfully');
      return true;

    } catch (error) {
      console.error('Failed to start recording:', error);
      setError('Failed to start recording. Please try again.');
      updateStatus('error');
      options.onError?.(error);

      // Haptic feedback for error
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
      return false;
    }
  };

  const stopRecording = async (): Promise<TranscriptionResult | null> => {
    if (!recording.current) return null;

    try {
      updateStatus('processing');

      // Clear timers
      if (durationInterval.current) {
        clearInterval(durationInterval.current);
      }
      if (silenceTimeout.current) {
        clearTimeout(silenceTimeout.current);
      }

      // Stop recording
      await recording.current.stopAndUnloadAsync();
      const uri = recording.current.getURI();

      // Reset audio mode
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: false,
        playsInSilentModeIOS: true,
      });

      setIsRecording(false);

      if (!uri) {
        throw new Error('No recording URI available');
      }

      console.log('Recording stopped, processing audio...');
      updateStatus('transcribing');

      // Get file info
      const fileInfo = await FileSystem.getInfoAsync(uri);
      const duration = recordingDuration / 1000; // Convert to seconds

      // Read file as base64
      const base64Audio = await FileSystem.readAsStringAsync(uri, {
        encoding: FileSystem.EncodingType.Base64,
      });

      // Send to backend with enhanced metadata
      const response = await fetch(`${API_URL}/api/voice/transcribe`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          audio: base64Audio,
          format: 'm4a',
          language: options.language || 'en',
          duration: duration,
          fileSize: fileInfo.size,
        }),
      });

      if (!response.ok) {
        const errorData = await response.text();
        throw new Error(`Transcription failed: ${errorData}`);
      }

      const data = await response.json();
      const text = data.text || data.transcription || data.transcript || '';
      const confidence = data.confidence || data.confidence_score || 0.85;

      if (text) {
        const result: TranscriptionResult = {
          text,
          confidence,
          language: data.language || options.language,
          duration,
        };

        setTranscript(text);
        updateStatus('completed');
        options.onTranscription?.(text);

        // Success haptic
        await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);

        // Clean up the recording file
        try {
          await FileSystem.deleteAsync(uri, { idempotent: true });
        } catch (cleanupError) {
          console.warn('Failed to cleanup recording file:', cleanupError);
        }

        recording.current = undefined;
        return result;
      } else {
        throw new Error('No transcription received');
      }

    } catch (error: any) {
      console.error('Error stopping/processing recording:', error);
      const errorMessage = error.message || 'Failed to process recording';
      setError(errorMessage);
      updateStatus('error');
      options.onError?.(error);

      // Error haptic
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);

      recording.current = undefined;
      setIsRecording(false);
      return null;
    }
  };

  const cancelRecording = async () => {
    if (!recording.current) return;

    try {
      // Clear timers
      if (durationInterval.current) {
        clearInterval(durationInterval.current);
      }
      if (silenceTimeout.current) {
        clearTimeout(silenceTimeout.current);
      }

      // Stop and unload without processing
      await recording.current.stopAndUnloadAsync();
      const uri = recording.current.getURI();

      // Clean up the file
      if (uri) {
        await FileSystem.deleteAsync(uri, { idempotent: true });
      }

      recording.current = undefined;
      setIsRecording(false);
      setTranscript('');
      setRecordingDuration(0);
      updateStatus('idle');

      // Haptic feedback
      await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);

    } catch (error) {
      console.error('Error canceling recording:', error);
    }
  };

  const resetTranscription = () => {
    setTranscript('');
    setError(null);
    setRecordingDuration(0);
    setAudioLevel(0);
    updateStatus('idle');
  };

  return {
    // State
    isRecording,
    transcript,
    status,
    error,
    recordingDuration,
    audioLevel,

    // Actions
    startRecording,
    stopRecording,
    cancelRecording,
    resetTranscription,
  };
}