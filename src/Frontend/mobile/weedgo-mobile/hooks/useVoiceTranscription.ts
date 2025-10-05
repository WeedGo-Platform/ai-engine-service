/**
 * Native Voice Transcription Hook for React Native
 * Uses @react-native-voice/voice for on-device speech recognition
 * Requires Expo Development Build (not Expo Go)
 */

import { useState, useRef, useCallback, useEffect } from 'react';
import Voice, {
  SpeechRecognizedEvent,
  SpeechResultsEvent,
  SpeechErrorEvent,
  SpeechEndEvent,
  SpeechStartEvent,
  SpeechVolumeChangedEvent,
} from '@react-native-voice/voice';

interface VoiceTranscriptionState {
  isRecording: boolean;
  isTranscribing: boolean;
  transcript: string;
  liveTranscript: string;
  error: string | null;
  isConnected: boolean;
}

interface UseVoiceTranscriptionOptions {
  onTranscriptComplete?: (text: string) => void;
  autoPauseMs?: number;
  autoStopMs?: number;
  language?: string;
}

export function useVoiceTranscription(options: UseVoiceTranscriptionOptions = {}) {
  const {
    onTranscriptComplete,
    autoPauseMs = 2000,
    autoStopMs = 2000,
    language = 'en-US'
  } = options;

  // State
  const [state, setState] = useState<VoiceTranscriptionState>({
    isRecording: false,
    isTranscribing: false,
    transcript: '',
    liveTranscript: '',
    error: null,
    isConnected: true
  });

  // Refs
  const pauseTimerRef = useRef<NodeJS.Timeout | null>(null);
  const silenceTimerRef = useRef<NodeJS.Timeout | null>(null);
  const accumulatedTextRef = useRef<string>('');
  const lastSentTextRef = useRef<string>('');
  const lastPartialRef = useRef<string>('');

  /**
   * Initialize Voice handlers
   */
  useEffect(() => {
    Voice.onSpeechStart = onSpeechStart;
    Voice.onSpeechRecognized = onSpeechRecognized;
    Voice.onSpeechEnd = onSpeechEnd;
    Voice.onSpeechError = onSpeechError;
    Voice.onSpeechResults = onSpeechResults;
    Voice.onSpeechPartialResults = onSpeechPartialResults;
    Voice.onSpeechVolumeChanged = onVolumeChanged;

    return () => {
      Voice.destroy().then(Voice.removeAllListeners);
    };
  }, []);

  const onSpeechStart = (e: SpeechStartEvent) => {
    console.log('[Voice] Speech started');
    setState(prev => ({
      ...prev,
      isTranscribing: true,
      error: null
    }));
  };

  const onSpeechRecognized = (e: SpeechRecognizedEvent) => {
    console.log('[Voice] Speech recognized');
    resetSilenceTimer();
  };

  const onSpeechEnd = (e: SpeechEndEvent) => {
    console.log('[Voice] Speech ended');
    setState(prev => ({
      ...prev,
      isTranscribing: false
    }));
  };

  const onSpeechError = (e: SpeechErrorEvent) => {
    const errorCode = e.error?.code;
    const errorMessage = e.error?.message || 'Speech recognition error';

    // Filter out benign errors that are expected behavior
    const isNoSpeechDetected = errorCode === '1110' || errorMessage.includes('No speech detected');
    const isCancelled = errorCode === '2' || errorMessage.includes('cancelled');

    if (isNoSpeechDetected || isCancelled) {
      // These are normal - user stopped speaking or cancelled
      console.log('[Voice] Info:', errorMessage);
      setState(prev => ({
        ...prev,
        isRecording: false,
        isTranscribing: false
      }));
    } else {
      // Actual errors worth reporting
      console.error('[Voice] Error:', e.error);
      setState(prev => ({
        ...prev,
        error: errorMessage,
        isRecording: false,
        isTranscribing: false
      }));
    }
    clearTimers();
  };

  const onSpeechResults = (e: SpeechResultsEvent) => {
    if (!e.value || e.value.length === 0) return;

    const text = e.value[0];
    console.log('[Voice] Final results:', text);

    accumulatedTextRef.current = text;
    setState(prev => ({
      ...prev,
      transcript: text,
      liveTranscript: '',
      isTranscribing: false
    }));

    setPauseTimer();
  };

  const onSpeechPartialResults = (e: SpeechResultsEvent) => {
    if (!e.value || e.value.length === 0) return;

    const partialText = e.value[0];
    if (partialText !== lastPartialRef.current) {
      console.log('[Voice] Partial results:', partialText);
      lastPartialRef.current = partialText;

      setState(prev => ({
        ...prev,
        liveTranscript: partialText,
        isTranscribing: true
      }));

      accumulatedTextRef.current = partialText;
      resetSilenceTimer();
    }
  };

  const onVolumeChanged = (e: SpeechVolumeChangedEvent) => {
    // Could be used for voice activity visualization
  };

  const resetSilenceTimer = useCallback(() => {
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current);
      silenceTimerRef.current = null;
    }

    silenceTimerRef.current = setTimeout(() => {
      console.log('[Voice] Auto-stopping due to silence');

      const remainingText = accumulatedTextRef.current.trim();
      if (remainingText && remainingText !== lastSentTextRef.current) {
        console.log('[Voice] Sending remaining transcript:', remainingText);
        onTranscriptComplete?.(remainingText);
        lastSentTextRef.current = remainingText;
      }

      stopRecording();
    }, autoStopMs);
  }, [autoStopMs, onTranscriptComplete]);

  const setPauseTimer = useCallback(() => {
    if (pauseTimerRef.current) {
      clearTimeout(pauseTimerRef.current);
      pauseTimerRef.current = null;
    }

    const textToCheck = accumulatedTextRef.current.trim();
    if (textToCheck && textToCheck !== lastSentTextRef.current) {
      pauseTimerRef.current = setTimeout(() => {
        const textToSend = accumulatedTextRef.current.trim();
        if (textToSend && textToSend !== lastSentTextRef.current) {
          console.log('[Voice] Sending transcript after pause:', textToSend);
          onTranscriptComplete?.(textToSend);
          lastSentTextRef.current = textToSend;

          accumulatedTextRef.current = '';
          setState(prev => ({
            ...prev,
            transcript: '',
            liveTranscript: ''
          }));

          stopRecording();
        }
      }, autoPauseMs);
    }
  }, [autoPauseMs, onTranscriptComplete]);

  const clearTimers = () => {
    if (pauseTimerRef.current) {
      clearTimeout(pauseTimerRef.current);
      pauseTimerRef.current = null;
    }
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current);
      silenceTimerRef.current = null;
    }
  };

  const startRecording = useCallback(async (): Promise<boolean> => {
    try {
      console.log('[Voice] Starting recording...');

      accumulatedTextRef.current = '';
      lastSentTextRef.current = '';
      lastPartialRef.current = '';
      clearTimers();

      setState(prev => ({
        ...prev,
        isRecording: true,
        error: null,
        transcript: '',
        liveTranscript: ''
      }));

      await Voice.start(language);
      resetSilenceTimer();

      console.log('[Voice] Recording started');
      return true;
    } catch (error) {
      console.error('[Voice] Failed to start recording:', error);
      setState(prev => ({
        ...prev,
        error: 'Failed to start recording',
        isRecording: false
      }));
      return false;
    }
  }, [language, resetSilenceTimer]);

  const stopRecording = useCallback(async () => {
    try {
      console.log('[Voice] Stopping recording...');

      clearTimers();

      const remainingText = accumulatedTextRef.current.trim();
      if (remainingText && remainingText !== lastSentTextRef.current) {
        console.log('[Voice] Sending final transcript:', remainingText);
        onTranscriptComplete?.(remainingText);
      }

      await Voice.stop();
      await Voice.destroy();

      setState(prev => ({
        ...prev,
        isRecording: false,
        isTranscribing: false,
        transcript: '',
        liveTranscript: ''
      }));

      accumulatedTextRef.current = '';
      lastSentTextRef.current = '';
      lastPartialRef.current = '';

      console.log('[Voice] Recording stopped');
    } catch (error) {
      console.error('[Voice] Failed to stop recording:', error);
      setState(prev => ({ ...prev, isRecording: false }));
    }
  }, [onTranscriptComplete]);

  const toggleRecording = useCallback(async () => {
    if (state.isRecording) {
      await stopRecording();
    } else {
      await startRecording();
    }
  }, [state.isRecording, startRecording, stopRecording]);

  const clearTranscript = useCallback(() => {
    setState(prev => ({
      ...prev,
      transcript: '',
      liveTranscript: ''
    }));
    accumulatedTextRef.current = '';
    lastSentTextRef.current = '';
    lastPartialRef.current = '';
  }, []);

  const connect = useCallback(async (): Promise<boolean> => {
    setState(prev => ({ ...prev, isConnected: true }));
    return true;
  }, []);

  const disconnect = useCallback(() => {
    if (state.isRecording) {
      stopRecording();
    }
  }, [state.isRecording, stopRecording]);

  useEffect(() => {
    return () => {
      clearTimers();
      Voice.destroy().then(Voice.removeAllListeners);
    };
  }, []);

  return {
    ...state,
    startRecording,
    stopRecording,
    toggleRecording,
    clearTranscript,
    connect,
    disconnect,
  };
}