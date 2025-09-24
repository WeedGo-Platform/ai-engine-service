import { useState, useRef, useEffect, useCallback } from 'react';
import { Audio } from 'expo-av';
import { Alert } from 'react-native';

const API_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:5024';
const SILENCE_THRESHOLD = 3000; // 3 seconds of silence
const CHUNK_DURATION = 1000; // Send audio chunks every 1 second
const MIN_DECIBELS = -45; // Minimum sound level to detect speech

interface UseRealtimeTranscriptionOptions {
  onTranscriptUpdate?: (text: string) => void;
  onTranscriptComplete?: (text: string) => void;
  onError?: (error: any) => void;
  onSpeechDetected?: () => void;
  onSilenceDetected?: () => void;
}

export function useRealtimeTranscription(options: UseRealtimeTranscriptionOptions = {}) {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentTranscript, setCurrentTranscript] = useState('');
  const [permissionStatus, setPermissionStatus] = useState<string>();

  const recording = useRef<Audio.Recording>();
  const silenceTimer = useRef<NodeJS.Timeout>();
  const chunkTimer = useRef<NodeJS.Timeout>();
  const audioChunks = useRef<string[]>([]);
  const lastSoundTime = useRef<number>(Date.now());
  const transcriptBuffer = useRef<string>('');
  const isListening = useRef<boolean>(false);

  useEffect(() => {
    checkPermissions();
    return () => {
      cleanup();
    };
  }, []);

  const cleanup = () => {
    if (recording.current) {
      recording.current.stopAndUnloadAsync().catch(() => {});
    }
    if (silenceTimer.current) {
      clearTimeout(silenceTimer.current);
    }
    if (chunkTimer.current) {
      clearInterval(chunkTimer.current);
    }
  };

  const checkPermissions = async () => {
    try {
      const { status } = await Audio.getPermissionsAsync();
      setPermissionStatus(status);
    } catch (error) {
      console.error('Failed to check audio permissions', error);
    }
  };

  const requestPermissions = async () => {
    try {
      const { status } = await Audio.requestPermissionsAsync();
      setPermissionStatus(status);
      return status === 'granted';
    } catch (error) {
      console.error('Failed to request audio permissions', error);
      return false;
    }
  };

  const detectSilence = useCallback(() => {
    const now = Date.now();
    const silenceDuration = now - lastSoundTime.current;

    if (silenceDuration >= SILENCE_THRESHOLD && transcriptBuffer.current.trim()) {
      console.log('Silence detected for 3 seconds, sending transcript');
      options.onSilenceDetected?.();

      // Send the complete transcript
      const finalTranscript = transcriptBuffer.current.trim();
      options.onTranscriptComplete?.(finalTranscript);

      // Reset for next sentence
      transcriptBuffer.current = '';
      setCurrentTranscript('');
    }
  }, [options]);

  const processAudioChunk = async (uri: string) => {
    if (!isListening.current) return;

    try {
      const formData = new FormData();
      const audioFile = {
        uri,
        type: 'audio/m4a',
        name: `chunk_${Date.now()}.m4a`,
      } as any;

      formData.append('audio', audioFile);
      formData.append('stream', 'true');
      formData.append('partial', 'true');

      const response = await fetch(`${API_URL}/api/voice/transcribe-stream`, {
        method: 'POST',
        body: formData,
        headers: {
          'Accept': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();

        if (data.transcript || data.text || data.partial_transcript) {
          const newText = data.transcript || data.text || data.partial_transcript;

          // Detect if there's actual speech
          if (newText.trim()) {
            lastSoundTime.current = Date.now();
            options.onSpeechDetected?.();

            // Update transcript buffer
            transcriptBuffer.current += ' ' + newText;
            const displayText = transcriptBuffer.current.trim();

            setCurrentTranscript(displayText);
            options.onTranscriptUpdate?.(displayText);
          }
        }

        // Check for silence
        detectSilence();
      }
    } catch (error) {
      console.error('Error processing audio chunk:', error);
    }
  };

  const startRealtimeRecording = async () => {
    try {
      // Check permissions
      if (permissionStatus !== 'granted') {
        const granted = await requestPermissions();
        if (!granted) {
          Alert.alert(
            'Permission Required',
            'Please grant microphone permission to use voice input.',
            [{ text: 'OK' }]
          );
          return;
        }
      }

      // Configure audio mode
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
        shouldDuckAndroid: true,
        playThroughEarpieceAndroid: false,
        staysActiveInBackground: true,
      });

      // Recording options optimized for streaming
      const recordingOptions = {
        android: {
          extension: '.m4a',
          outputFormat: Audio.AndroidOutputFormat.MPEG_4,
          audioEncoder: Audio.AndroidAudioEncoder.AAC,
          sampleRate: 16000, // Lower sample rate for faster processing
          numberOfChannels: 1, // Mono for smaller file size
          bitRate: 64000, // Lower bitrate for streaming
        },
        ios: {
          extension: '.m4a',
          outputFormat: Audio.IOSOutputFormat.MPEG4AAC,
          audioQuality: Audio.IOSAudioQuality.MEDIUM,
          sampleRate: 16000,
          numberOfChannels: 1,
          bitRate: 64000,
          linearPCMBitDepth: 16,
          linearPCMIsBigEndian: false,
          linearPCMIsFloat: false,
        },
        web: {
          mimeType: 'audio/webm',
          bitsPerSecond: 64000,
        },
      };

      // Create recording with metering enabled for volume detection
      const { recording: newRecording, status } = await Audio.Recording.createAsync(
        recordingOptions,
        (status) => onRecordingStatusUpdate(status),
        100 // Update every 100ms
      );

      recording.current = newRecording;
      isListening.current = true;
      setIsRecording(true);
      lastSoundTime.current = Date.now();
      transcriptBuffer.current = '';
      setCurrentTranscript('');

      console.log('Started realtime recording');

      // Start chunk processing timer
      chunkTimer.current = setInterval(async () => {
        if (recording.current && isListening.current) {
          try {
            // Get current recording URI and process it
            const uri = recording.current.getURI();
            if (uri) {
              await processAudioChunk(uri);
            }
          } catch (error) {
            console.error('Error processing chunk:', error);
          }
        }
      }, CHUNK_DURATION);

      // Start silence detection timer
      silenceTimer.current = setInterval(() => {
        detectSilence();
      }, 500); // Check every 500ms

    } catch (error) {
      console.error('Failed to start recording', error);
      options.onError?.(error);
      Alert.alert('Recording Error', 'Failed to start recording. Please try again.');
    }
  };

  const onRecordingStatusUpdate = (status: Audio.RecordingStatus) => {
    if (status.isRecording && status.metering !== undefined) {
      // Check if sound level indicates speech
      if (status.metering > MIN_DECIBELS) {
        lastSoundTime.current = Date.now();
        options.onSpeechDetected?.();
      }
    }
  };

  const stopRealtimeRecording = async () => {
    if (!recording.current) {
      return;
    }

    try {
      isListening.current = false;
      setIsRecording(false);

      // Clear timers
      if (chunkTimer.current) {
        clearInterval(chunkTimer.current);
      }
      if (silenceTimer.current) {
        clearInterval(silenceTimer.current);
      }

      // Stop recording
      await recording.current.stopAndUnloadAsync();
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: false,
      });

      // Process final recording if there's a transcript
      if (transcriptBuffer.current.trim()) {
        const finalTranscript = transcriptBuffer.current.trim();
        options.onTranscriptComplete?.(finalTranscript);
      }

      recording.current = undefined;
      transcriptBuffer.current = '';
      setCurrentTranscript('');

      console.log('Stopped realtime recording');

    } catch (error) {
      console.error('Failed to stop recording', error);
      options.onError?.(error);
    }
  };

  const cancelRecording = async () => {
    if (recording.current && isRecording) {
      try {
        isListening.current = false;

        if (chunkTimer.current) {
          clearInterval(chunkTimer.current);
        }
        if (silenceTimer.current) {
          clearInterval(silenceTimer.current);
        }

        await recording.current.stopAndUnloadAsync();
        await Audio.setAudioModeAsync({
          allowsRecordingIOS: false,
        });

        recording.current = undefined;
        transcriptBuffer.current = '';
        setCurrentTranscript('');
        setIsRecording(false);
      } catch (error) {
        console.error('Failed to cancel recording', error);
      }
    }
  };

  const clearTranscript = () => {
    transcriptBuffer.current = '';
    setCurrentTranscript('');
  };

  return {
    isRecording,
    isProcessing,
    currentTranscript,
    startRecording: startRealtimeRecording,
    stopRecording: stopRealtimeRecording,
    cancelRecording,
    clearTranscript,
    permissionStatus,
  };
}