import { useState, useRef } from 'react';
import { Audio } from 'expo-av';
import { Alert } from 'react-native';
import * as FileSystem from 'expo-file-system';

const API_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:5024';

interface UseSimpleTranscriptionOptions {
  onTranscription?: (text: string) => void;
  onError?: (error: any) => void;
}

export function useSimpleTranscription(options: UseSimpleTranscriptionOptions = {}) {
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState('');
  const recording = useRef<Audio.Recording>();

  const startRecording = async () => {
    try {
      // Request permissions
      const { status } = await Audio.requestPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Permission Required', 'Please grant microphone permission.');
        return;
      }

      // Configure audio
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
      });

      // Start recording
      const { recording: rec } = await Audio.Recording.createAsync(
        Audio.RecordingOptionsPresets.HIGH_QUALITY
      );

      recording.current = rec;
      setIsRecording(true);
      setTranscript('');

      console.log('Recording started');
    } catch (error) {
      console.error('Failed to start recording:', error);
      options.onError?.(error);
    }
  };

  const stopRecording = async () => {
    if (!recording.current) return;

    try {
      setIsRecording(false);

      // Stop recording
      await recording.current.stopAndUnloadAsync();
      const uri = recording.current.getURI();

      if (!uri) {
        throw new Error('No recording URI');
      }

      console.log('Recording stopped, URI:', uri);

      // Read file as base64
      const base64Audio = await FileSystem.readAsStringAsync(uri, {
        encoding: FileSystem.EncodingType.Base64,
      });

      // Send to backend
      const response = await fetch(`${API_URL}/api/voice/transcribe`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          audio: base64Audio,
          format: 'm4a'
        }),
      });

      if (response.ok) {
        const data = await response.json();
        const text = data.text || data.transcription || data.transcript || '';

        if (text) {
          setTranscript(text);
          options.onTranscription?.(text);
        }
      } else {
        console.error('Transcription failed:', response.status);
      }

      recording.current = undefined;

    } catch (error) {
      console.error('Error stopping recording:', error);
      options.onError?.(error);
    }
  };

  return {
    isRecording,
    transcript,
    startRecording,
    stopRecording,
  };
}