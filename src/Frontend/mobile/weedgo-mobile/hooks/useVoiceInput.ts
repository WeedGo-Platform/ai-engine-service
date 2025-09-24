import { useState, useRef, useEffect } from 'react';
import { Audio } from 'expo-av';
import { Alert } from 'react-native';

const API_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:5024';

interface UseVoiceInputOptions {
  onTranscription?: (text: string) => void;
  onError?: (error: any) => void;
}

export function useVoiceInput(options: UseVoiceInputOptions = {}) {
  const [isRecording, setIsRecording] = useState(false);
  const [permissionStatus, setPermissionStatus] = useState<string>();
  const [isTranscribing, setIsTranscribing] = useState(false);
  const recording = useRef<Audio.Recording>();

  useEffect(() => {
    // Check permissions on mount
    checkPermissions();

    return () => {
      // Cleanup recording if component unmounts while recording
      if (recording.current) {
        recording.current.stopAndUnloadAsync().catch(() => {});
      }
    };
  }, []);

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

  const startRecording = async () => {
    try {
      // Check and request permissions if needed
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

      // Configure audio mode for iOS
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
        shouldDuckAndroid: true,
        playThroughEarpieceAndroid: false,
      });

      // Start recording with custom options for better compatibility
      const recordingOptions = {
        android: {
          extension: '.m4a',
          outputFormat: Audio.AndroidOutputFormat.MPEG_4,
          audioEncoder: Audio.AndroidAudioEncoder.AAC,
          sampleRate: 44100,
          numberOfChannels: 2,
          bitRate: 128000,
        },
        ios: {
          extension: '.m4a',
          outputFormat: Audio.IOSOutputFormat.MPEG4AAC,
          audioQuality: Audio.IOSAudioQuality.HIGH,
          sampleRate: 44100,
          numberOfChannels: 2,
          bitRate: 128000,
          linearPCMBitDepth: 16,
          linearPCMIsBigEndian: false,
          linearPCMIsFloat: false,
        },
        web: {
          mimeType: 'audio/webm',
          bitsPerSecond: 128000,
        },
      };

      const { recording: newRecording } = await Audio.Recording.createAsync(
        recordingOptions
      );

      recording.current = newRecording;
      setIsRecording(true);

      // Set a maximum recording duration of 30 seconds
      setTimeout(async () => {
        if (recording.current) {
          console.log('Auto-stopping recording after 30 seconds');
          await stopRecording();
        }
      }, 30000);

    } catch (error) {
      console.error('Failed to start recording', error);
      options.onError?.(error);
      Alert.alert('Recording Error', 'Failed to start recording. Please try again.');
    }
  };

  const stopRecording = async () => {
    if (!recording.current) {
      setIsRecording(false);
      return;
    }

    try {
      setIsRecording(false);
      setIsTranscribing(true);

      // Stop the recording
      await recording.current.stopAndUnloadAsync();
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: false,
      });

      // Get the recording URI
      const uri = recording.current.getURI();
      recording.current = undefined;

      if (!uri) {
        throw new Error('No recording URI available');
      }

      // Transcribe the audio
      await transcribeAudio(uri);

    } catch (error) {
      console.error('Failed to stop recording', error);
      options.onError?.(error);
      Alert.alert('Recording Error', 'Failed to process recording. Please try again.');
    } finally {
      setIsTranscribing(false);
    }
  };

  const transcribeAudio = async (uri: string) => {
    try {
      console.log('Starting transcription for URI:', uri);
      console.log('API URL:', `${API_URL}/api/voice/transcribe`);

      // Create form data with the audio file
      const formData = new FormData();

      // For React Native/Expo, we need to format the file object properly
      const audioFile = {
        uri,
        type: 'audio/m4a', // iOS typically records in m4a format
        name: 'recording.m4a',
      } as any;

      formData.append('audio', audioFile);

      // Send to transcription API
      const response = await fetch(`${API_URL}/api/voice/transcribe`, {
        method: 'POST',
        body: formData,
        headers: {
          'Accept': 'application/json',
          // Don't set Content-Type, let fetch set it with boundary
        },
      });

      if (!response.ok) {
        const errorData = await response.text();
        console.error('Transcription API error:', response.status, errorData);
        throw new Error(`Transcription failed: ${response.status} - ${errorData}`);
      }

      const data = await response.json();
      console.log('Transcription response:', JSON.stringify(data, null, 2));

      // Handle different response formats
      let transcribedText = null;

      // Check various possible response formats
      if (data.result && typeof data.result === 'object') {
        transcribedText = data.result.transcription || data.result.text;
      }

      if (!transcribedText) {
        transcribedText = data.text || data.transcription || data.transcript || data.result;
      }

      // Also check for nested transcription object
      if (!transcribedText && data.data) {
        transcribedText = data.data.transcription || data.data.text || data.data.transcript;
      }

      if (transcribedText && transcribedText.trim()) {
        console.log('Transcribed text:', transcribedText);
        options.onTranscription?.(transcribedText);
      } else if (data.result?.has_speech === false || data.has_speech === false) {
        // No speech detected in the audio
        console.log('No speech detected in audio');
        throw new Error('No speech detected. Please try speaking clearly.');
      } else {
        console.warn('Unable to extract transcription from response:', data);
        throw new Error('Unable to process audio. Please try again.');
      }

    } catch (error: any) {
      console.error('Transcription error details:', error);
      options.onError?.(error);

      // Provide more specific error messages
      let errorMessage = 'Failed to transcribe audio. ';

      if (error.message.includes('No speech detected')) {
        errorMessage = 'No speech detected. Please speak clearly and try again.';
      } else if (error.message.includes('Network')) {
        errorMessage = 'Network error. Please check your connection.';
      } else if (error.message.includes('422')) {
        errorMessage = 'Invalid audio format. Please try again.';
      } else {
        errorMessage += error.message || 'Please try again.';
      }

      Alert.alert('Transcription Error', errorMessage);
    }
  };

  const cancelRecording = async () => {
    if (recording.current && isRecording) {
      try {
        await recording.current.stopAndUnloadAsync();
        await Audio.setAudioModeAsync({
          allowsRecordingIOS: false,
        });
        recording.current = undefined;
        setIsRecording(false);
      } catch (error) {
        console.error('Failed to cancel recording', error);
      }
    }
  };

  return {
    isRecording,
    isTranscribing,
    startRecording,
    stopRecording,
    cancelRecording,
    permissionStatus,
  };
}