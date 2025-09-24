import { useState, useRef, useEffect } from 'react';
import { Audio } from 'expo-av';
import AsyncStorage from '@react-native-async-storage/async-storage';

const API_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:5024';
const TTS_ENABLED_KEY = '@tts_enabled';

interface UseTextToSpeechOptions {
  autoPlay?: boolean;
  onStart?: () => void;
  onComplete?: () => void;
  onError?: (error: any) => void;
}

export function useTextToSpeech(options: UseTextToSpeechOptions = {}) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isTTSEnabled, setIsTTSEnabled] = useState(true);
  const soundRef = useRef<Audio.Sound>();
  const currentTextRef = useRef<string>('');

  useEffect(() => {
    // Load TTS preference
    loadTTSPreference();

    // Configure audio mode
    configureAudioMode();

    return () => {
      // Cleanup on unmount
      if (soundRef.current) {
        soundRef.current.unloadAsync().catch(() => {});
      }
    };
  }, []);

  const loadTTSPreference = async () => {
    try {
      const enabled = await AsyncStorage.getItem(TTS_ENABLED_KEY);
      setIsTTSEnabled(enabled !== 'false'); // Default to true
    } catch (error) {
      console.error('Error loading TTS preference:', error);
    }
  };

  const configureAudioMode = async () => {
    try {
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: false,
        playsInSilentModeIOS: true,
        shouldDuckAndroid: true,
        playThroughEarpieceAndroid: false,
        staysActiveInBackground: false,
      });
    } catch (error) {
      console.error('Error configuring audio mode:', error);
    }
  };

  const toggleTTS = async () => {
    const newState = !isTTSEnabled;
    setIsTTSEnabled(newState);

    try {
      await AsyncStorage.setItem(TTS_ENABLED_KEY, newState.toString());
    } catch (error) {
      console.error('Error saving TTS preference:', error);
    }

    // Stop current playback if disabling
    if (!newState && isPlaying) {
      await stopSpeaking();
    }

    return newState;
  };

  const speakText = async (text: string, force: boolean = false) => {
    // Don't speak if TTS is disabled (unless forced)
    if (!isTTSEnabled && !force) {
      console.log('TTS is disabled, skipping speech');
      return;
    }

    // Stop any current playback
    if (soundRef.current) {
      await soundRef.current.unloadAsync();
      soundRef.current = undefined;
    }

    currentTextRef.current = text;
    setIsLoading(true);

    try {
      // Call TTS API
      const response = await fetch(`${API_URL}/api/voice/synthesize`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: text,
          voice: 'en-US-Standard-C', // Female voice
          speed: 1.0,
          pitch: 1.0,
        }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('TTS API error:', response.status, errorText);

        // Fallback: Try alternate endpoint or skip TTS
        console.warn('TTS not available, skipping voice readback');
        return;
      }

      // For React Native, we need to get the audio URL directly
      const contentType = response.headers.get('content-type');
      let audioUri: string;

      if (contentType?.includes('application/json')) {
        // API returns JSON with audio URL
        const data = await response.json();
        audioUri = data.audio_url || data.url || data.audio;

        if (!audioUri) {
          console.warn('No audio URL in response, skipping TTS');
          return;
        }
      } else {
        // API returns audio directly - construct URL
        // For now, skip TTS if direct audio is returned
        console.warn('Direct audio response not supported yet');
        return;
      }

      // Create and play sound
      const { sound } = await Audio.Sound.createAsync(
        { uri: audioUri },
        { shouldPlay: true },
        onPlaybackStatusUpdate
      );

      soundRef.current = sound;
      setIsPlaying(true);
      options.onStart?.();

    } catch (error) {
      console.error('Failed to speak text:', error);
      options.onError?.(error);
      setIsPlaying(false);
    } finally {
      setIsLoading(false);
    }
  };

  const onPlaybackStatusUpdate = (status: any) => {
    if (status.didJustFinish) {
      setIsPlaying(false);
      options.onComplete?.();

      // Cleanup
      if (soundRef.current) {
        soundRef.current.unloadAsync().catch(() => {});
        soundRef.current = undefined;
      }
    }
  };

  const stopSpeaking = async () => {
    if (soundRef.current) {
      try {
        await soundRef.current.stopAsync();
        await soundRef.current.unloadAsync();
        soundRef.current = undefined;
        setIsPlaying(false);
      } catch (error) {
        console.error('Error stopping speech:', error);
      }
    }
  };

  const pauseSpeaking = async () => {
    if (soundRef.current && isPlaying) {
      try {
        await soundRef.current.pauseAsync();
        setIsPlaying(false);
      } catch (error) {
        console.error('Error pausing speech:', error);
      }
    }
  };

  const resumeSpeaking = async () => {
    if (soundRef.current && !isPlaying) {
      try {
        await soundRef.current.playAsync();
        setIsPlaying(true);
      } catch (error) {
        console.error('Error resuming speech:', error);
      }
    }
  };

  return {
    isPlaying,
    isLoading,
    isTTSEnabled,
    toggleTTS,
    speakText,
    stopSpeaking,
    pauseSpeaking,
    resumeSpeaking,
  };
}