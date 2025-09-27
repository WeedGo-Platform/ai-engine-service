import { useState, useRef, useCallback } from 'react';
import { Audio } from 'expo-av';
import { Alert } from 'react-native';
import * as FileSystem from 'expo-file-system/legacy';
import * as Haptics from 'expo-haptics';

const API_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:5024';

interface UseEnhancedTranscriptionOptions {
  onTranscription?: (text: string) => void;
  onPartialTranscript?: (text: string) => void; // Real-time partial transcript
  onError?: (error: any) => void;
  onStatusChange?: (status: TranscriptionStatus) => void;
  maxDuration?: number; // Maximum recording duration in milliseconds
  autoStop?: boolean; // Auto stop after silence detection
  silenceThreshold?: number; // Milliseconds of silence before auto-send (default 2000)
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
  const [partialTranscript, setPartialTranscript] = useState('');
  const [status, setStatus] = useState<TranscriptionStatus>('idle');
  const [error, setError] = useState<string | null>(null);
  const [recordingDuration, setRecordingDuration] = useState(0);
  const [audioLevel, setAudioLevel] = useState(0);

  const recording = useRef<Audio.Recording>();
  const durationInterval = useRef<NodeJS.Timeout>();
  const silenceTimeout = useRef<NodeJS.Timeout>();
  const lastSoundTime = useRef<number>(Date.now());
  const transcriptAccumulator = useRef<string>('');
  const silenceThreshold = options.silenceThreshold || 2000;

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
      // Use WAV format for better compatibility with speech recognition
      const recordingOptions = {
        ...Audio.RecordingOptionsPresets.HIGH_QUALITY,
        ios: {
          extension: '.wav',
          outputFormat: Audio.IOSOutputFormat.LINEARPCM, // WAV format
          audioQuality: Audio.IOSAudioQuality.MAX,
          sampleRate: 16000, // 16kHz is standard for speech recognition
          numberOfChannels: 1, // Mono for speech
          bitRate: 128000,
          linearPCMBitDepth: 16,
          linearPCMIsBigEndian: false,
          linearPCMIsFloat: false,
        },
        android: {
          extension: '.wav',
          outputFormat: Audio.AndroidOutputFormat.DEFAULT,
          audioEncoder: Audio.AndroidAudioEncoder.DEFAULT,
          sampleRate: 16000, // 16kHz for speech recognition
          numberOfChannels: 1, // Mono
          bitRate: 128000,
        },
        web: {
          mimeType: 'audio/wav',
          bitsPerSecond: 128000,
        },
      };

      console.log('Recording options:', recordingOptions);

      const { recording: rec, status: recordingStatus } = await Audio.Recording.createAsync(
        recordingOptions,
        (status) => {
          // Update audio levels for visualization and silence detection
          if (status.isRecording && status.metering) {
            const normalizedLevel = Math.min(1, Math.max(0, (status.metering + 160) / 160));
            setAudioLevel(normalizedLevel);

            // Log audio levels periodically for debugging
            if (Math.random() < 0.1) { // Log ~10% of the time
              console.log('Recording audio level:', normalizedLevel, 'Raw metering:', status.metering);
            }

            // Detect voice activity
            if (normalizedLevel > 0.1) {
              lastSoundTime.current = Date.now();

              // Clear silence timeout if voice detected
              if (silenceTimeout.current) {
                clearTimeout(silenceTimeout.current);
                silenceTimeout.current = undefined;
              }
            } else {
              // Check for silence and auto-send if threshold reached
              const silenceDuration = Date.now() - lastSoundTime.current;

              if (silenceDuration > silenceThreshold && transcriptAccumulator.current && !silenceTimeout.current) {
                // Set timeout to send accumulated transcript
                silenceTimeout.current = setTimeout(async () => {
                  if (transcriptAccumulator.current && recording.current) {
                    // Send accumulated transcript
                    const textToSend = transcriptAccumulator.current;
                    options.onTranscription?.(textToSend);

                    // Clear accumulator for next segment
                    transcriptAccumulator.current = '';
                    setPartialTranscript('');

                    // Continue recording
                    console.log('Silence detected, sent transcript and continuing...');
                  }
                  silenceTimeout.current = undefined;
                }, 500); // Small delay to ensure silence is real
              }
            }
          }
        },
        100 // Update interval in ms
      );

      recording.current = rec;
      setIsRecording(true);
      setTranscript('');
      setPartialTranscript('');
      transcriptAccumulator.current = '';
      lastSoundTime.current = Date.now();
      setRecordingDuration(0);
      updateStatus('recording');

      // No mock real-time transcription - wait for actual API implementation

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

      // Auto-stop is now handled in the audio status callback with silence detection

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

      // Get duration
      const duration = recordingDuration / 1000; // Convert to seconds

      console.log('Reading audio from URI:', uri);

      // Read file as base64
      let base64Audio;
      try {
        base64Audio = await FileSystem.readAsStringAsync(uri, {
          encoding: FileSystem.EncodingType.Base64,
        });
        console.log('Audio file read successfully, size:', base64Audio.length);
      } catch (readError) {
        console.error('Error reading audio file:', readError);
        throw new Error('Failed to read audio file');
      }

      // Validate base64 audio
      if (!base64Audio || base64Audio.length === 0) {
        throw new Error('Audio file is empty');
      }

      // Verify recording has actual audio data
      console.log('Audio URI exists:', !!uri);
      console.log('Base64 audio size:', base64Audio.length);
      console.log('Recording duration:', duration, 'seconds');
      console.log('Audio level during recording:', audioLevel);

      // Check if audio file has reasonable size (at least 10KB for 1 second of audio)
      const expectedMinSize = duration * 10000; // ~10KB per second minimum
      if (base64Audio.length < expectedMinSize) {
        console.warn('Audio file seems too small for duration:', base64Audio.length, 'bytes for', duration, 'seconds');
      }

      // Create FormData for React Native
      // In React Native, we can append the base64 directly with proper metadata
      const formData = new FormData();

      // React Native FormData handles file uploads differently
      // We need to provide an object with uri, type, and name
      formData.append('audio', {
        uri: uri,
        type: 'audio/wav',
        name: 'recording.wav'
      } as any);

      formData.append('language', options.language || 'en');
      formData.append('mode', 'auto_vad'); // Use auto_vad mode for voice activity detection

      console.log('Sending transcription request to API via FormData with auto_vad mode');

      const response = await fetch(`${API_URL}/api/voice/transcribe`, {
        method: 'POST',
        body: formData,
        // Don't set Content-Type header - let browser set it with boundary for multipart/form-data
      });

      if (!response.ok) {
        const errorData = await response.text();
        console.error('Transcription API error:', errorData);
        throw new Error(`Transcription failed: ${errorData}`);
      }

      const data = await response.json();
      console.log('Transcription response:', data);

      // Extract result from response structure
      const result = data.result || data;

      // Log full result for debugging
      console.log('Full API result:', JSON.stringify(result, null, 2));

      // Check if speech was detected (only in auto_vad mode)
      if (result.vad_result && !result.vad_result.has_speech) {
        console.warn('No speech detected by VAD. Confidence:', result.vad_result.confidence);
        console.warn('VAD segments:', result.vad_result.segments);
        console.warn('Recording duration:', duration, 'seconds');
        console.warn('Audio size:', base64Audio.length, 'bytes');
        console.warn('Session ID:', result.session_id);
        console.warn('Processing time:', result.processing_time_ms, 'ms');

        // Don't throw error immediately - check if there's still transcription
        if (!result.transcription && !result.text) {
          throw new Error('No speech detected in recording. Please speak clearly and try again.');
        }
      }

      // Extract transcription text from nested structure
      let text = '';
      if (result.transcription && typeof result.transcription === 'object') {
        text = result.transcription.text || '';
      } else if (typeof result.transcription === 'string') {
        text = result.transcription;
      } else {
        text = result.text || result.transcript || '';
      }

      // Check if we got any text
      if (!text && result.has_speech !== false) {
        // If speech was detected but no transcription, it's an error
        console.warn('No transcription text found, but speech might be present');
        throw new Error('Transcription failed - no text returned');
      }

      if (text) {
        const transcriptionResult: TranscriptionResult = {
          text,
          confidence: result.confidence || 0.85,
          language: result.language || options.language,
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
        return transcriptionResult;
      } else {
        throw new Error('No transcription text received');
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
    setPartialTranscript('');
    transcriptAccumulator.current = '';
    setError(null);
    setRecordingDuration(0);
    setAudioLevel(0);
    updateStatus('idle');
  };

  return {
    // State
    isRecording,
    transcript,
    partialTranscript, // Real-time partial transcript
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