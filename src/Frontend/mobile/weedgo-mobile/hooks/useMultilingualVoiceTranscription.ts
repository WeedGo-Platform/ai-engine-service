/**
 * Multilingual Voice Transcription Hook for React Native
 * Implements intelligent language detection and switching
 * Supports mixed-language conversations
 */

import { useState, useRef, useCallback, useEffect } from 'react';
import Voice, {
  SpeechRecognizedEvent,
  SpeechResultsEvent,
  SpeechErrorEvent,
  SpeechEndEvent,
  SpeechStartEvent,
} from '@react-native-voice/voice';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Try to import expo-localization, fallback to default if not available
let Localization: any = null;
try {
  Localization = require('expo-localization');
} catch (error) {
  console.log('[Voice] expo-localization not available, using en-US as default');
}

interface MultilingualVoiceState {
  isRecording: boolean;
  isTranscribing: boolean;
  transcript: string;
  liveTranscript: string;
  error: string | null;
  isConnected: boolean;
  detectedLanguage: string | null;
  currentLanguage: string;
}

interface UseMultilingualVoiceOptions {
  onTranscriptComplete?: (text: string, language: string) => void;
  autoPauseMs?: number;
  autoStopMs?: number;
  preferredLanguages?: string[];
  autoDetect?: boolean;
}

// Common language codes and their variations
const LANGUAGE_FAMILIES = {
  english: ['en-US', 'en-GB', 'en-AU', 'en-CA', 'en-IN'],
  spanish: ['es-ES', 'es-MX', 'es-US', 'es-AR'],
  french: ['fr-FR', 'fr-CA', 'fr-BE', 'fr-CH'],
  chinese: ['zh-CN', 'zh-TW', 'zh-HK'],
  arabic: ['ar-SA', 'ar-AE', 'ar-EG'],
  portuguese: ['pt-BR', 'pt-PT'],
  german: ['de-DE', 'de-AT', 'de-CH'],
  hindi: ['hi-IN'],
  yoruba: ['yo-NG'], // Note: iOS may not support Yoruba natively
};

// Language detection patterns (simplified)
const LANGUAGE_PATTERNS = {
  'fr': /\b(je|tu|il|elle|nous|vous|ils|elles|est|sont|avoir|être|faire|avec|pour|dans|sur|sous|chez|mais|donc|alors)\b/i,
  'es': /\b(yo|tú|él|ella|nosotros|vosotros|ellos|estar|ser|hacer|tener|poder|para|pero|porque|cuando|donde)\b/i,
  'de': /\b(ich|du|er|sie|wir|ihr|Sie|ist|sind|haben|sein|werden|können|müssen|aber|oder|und|nicht)\b/i,
  'zh': /[\u4e00-\u9fa5]/,
  'ar': /[\u0600-\u06ff]/,
  'hi': /[\u0900-\u097F]/,
  'yo': /\b(ẹ|ọ|ṣ|ni|ti|ninu|lati|pẹlu|fun|sugbon|nitori|nigbati)\b/i,
};

export function useMultilingualVoiceTranscription(options: UseMultilingualVoiceOptions = {}) {
  const {
    onTranscriptComplete,
    autoPauseMs = 2000,
    autoStopMs = 2000,
    preferredLanguages = [],
    autoDetect = true
  } = options;

  // Get device language (fallback to en-US if localization not available)
  const deviceLanguage = Localization ?
    (Localization.getLocales()[0]?.languageTag || 'en-US') :
    'en-US';

  // State
  const [state, setState] = useState<MultilingualVoiceState>({
    isRecording: false,
    isTranscribing: false,
    transcript: '',
    liveTranscript: '',
    error: null,
    isConnected: true,
    detectedLanguage: null,
    currentLanguage: deviceLanguage
  });

  // Refs
  const pauseTimerRef = useRef<NodeJS.Timeout | null>(null);
  const silenceTimerRef = useRef<NodeJS.Timeout | null>(null);
  const accumulatedTextRef = useRef<string>('');
  const lastSentTextRef = useRef<string>('');
  const lastPartialRef = useRef<string>('');
  const currentRecognitionRef = useRef<any>(null);
  const failedLanguagesRef = useRef<Set<string>>(new Set());
  const confidenceScoresRef = useRef<Map<string, number>>(new Map());

  /**
   * Load user's language preference
   */
  useEffect(() => {
    loadLanguagePreference();
  }, []);

  const loadLanguagePreference = async () => {
    try {
      const saved = await AsyncStorage.getItem('userLanguagePreference');
      if (saved) {
        setState(prev => ({ ...prev, currentLanguage: saved }));
      }
    } catch (error) {
      console.log('[Voice] Could not load language preference');
    }
  };

  /**
   * Save language preference
   */
  const saveLanguagePreference = async (language: string) => {
    try {
      await AsyncStorage.setItem('userLanguagePreference', language);
      setState(prev => ({ ...prev, currentLanguage: language }));
    } catch (error) {
      console.log('[Voice] Could not save language preference');
    }
  };

  /**
   * Detect language from text using patterns
   */
  const detectLanguageFromText = (text: string): string | null => {
    if (!text) return null;

    const scores: { [key: string]: number } = {};

    // Check each language pattern
    for (const [lang, pattern] of Object.entries(LANGUAGE_PATTERNS)) {
      const matches = text.match(pattern);
      if (matches) {
        scores[lang] = matches.length;
      }
    }

    // Find the language with highest score
    let maxScore = 0;
    let detectedLang = null;

    for (const [lang, score] of Object.entries(scores)) {
      if (score > maxScore) {
        maxScore = score;
        detectedLang = lang;
      }
    }

    // Map to full language code
    if (detectedLang) {
      for (const [family, codes] of Object.entries(LANGUAGE_FAMILIES)) {
        if (family.startsWith(detectedLang) || codes.some(code => code.startsWith(detectedLang))) {
          return codes[0]; // Return primary variant
        }
      }
    }

    return null;
  };

  /**
   * Try recognition with different languages
   */
  const tryMultipleLanguages = async (languages: string[]): Promise<boolean> => {
    for (const lang of languages) {
      if (failedLanguagesRef.current.has(lang)) continue;

      try {
        console.log(`[Voice] Trying language: ${lang}`);
        await Voice.stop();
        await Voice.start(lang);

        // Wait briefly to see if we get results
        await new Promise(resolve => setTimeout(resolve, 500));

        if (accumulatedTextRef.current) {
          setState(prev => ({ ...prev, detectedLanguage: lang }));
          return true;
        }
      } catch (error) {
        console.log(`[Voice] Language ${lang} failed:`, error);
        failedLanguagesRef.current.add(lang);
      }
    }
    return false;
  };

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

  const onSpeechError = async (e: SpeechErrorEvent) => {
    console.error('[Voice] Error:', e.error);

    // If no speech detected and auto-detect is on, try other languages
    if (autoDetect && e.error?.code === '7' && preferredLanguages.length > 0) {
      const currentLangIndex = preferredLanguages.indexOf(state.currentLanguage);
      if (currentLangIndex < preferredLanguages.length - 1) {
        // Try next language
        const nextLang = preferredLanguages[currentLangIndex + 1];
        console.log(`[Voice] Switching to ${nextLang}`);
        await startRecording(nextLang);
        return;
      }
    }

    setState(prev => ({
      ...prev,
      error: e.error?.message || 'Speech recognition error',
      isRecording: false,
      isTranscribing: false
    }));
    clearTimers();
  };

  const onSpeechResults = (e: SpeechResultsEvent) => {
    if (!e.value || e.value.length === 0) return;

    const text = e.value[0];
    console.log('[Voice] Final results:', text);

    // Detect language if auto-detect is enabled
    if (autoDetect) {
      const detectedLang = detectLanguageFromText(text);
      if (detectedLang && detectedLang !== state.currentLanguage) {
        console.log(`[Voice] Language detected: ${detectedLang}`);
        setState(prev => ({ ...prev, detectedLanguage: detectedLang }));
      }
    }

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

      // Try to detect language from partial results
      if (autoDetect && partialText.length > 10) {
        const detectedLang = detectLanguageFromText(partialText);
        if (detectedLang && detectedLang !== state.currentLanguage) {
          console.log(`[Voice] Early language detection: ${detectedLang}`);
          // Could switch language here for better accuracy
        }
      }

      setState(prev => ({
        ...prev,
        liveTranscript: partialText,
        isTranscribing: true
      }));

      accumulatedTextRef.current = partialText;
      resetSilenceTimer();
    }
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
        onTranscriptComplete?.(remainingText, state.detectedLanguage || state.currentLanguage);
        lastSentTextRef.current = remainingText;
      }

      stopRecording();
    }, autoStopMs);
  }, [autoStopMs, onTranscriptComplete, state.currentLanguage, state.detectedLanguage]);

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
          onTranscriptComplete?.(textToSend, state.detectedLanguage || state.currentLanguage);
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
  }, [autoPauseMs, onTranscriptComplete, state.currentLanguage, state.detectedLanguage]);

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

  const startRecording = useCallback(async (language?: string): Promise<boolean> => {
    try {
      console.log('[Voice] Starting recording...');

      const langToUse = language || state.currentLanguage;

      accumulatedTextRef.current = '';
      lastSentTextRef.current = '';
      lastPartialRef.current = '';
      failedLanguagesRef.current.clear();
      clearTimers();

      setState(prev => ({
        ...prev,
        isRecording: true,
        error: null,
        transcript: '',
        liveTranscript: '',
        detectedLanguage: null,
        currentLanguage: langToUse
      }));

      await Voice.start(langToUse);
      resetSilenceTimer();

      console.log(`[Voice] Recording started with language: ${langToUse}`);
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
  }, [state.currentLanguage, resetSilenceTimer]);

  const stopRecording = useCallback(async () => {
    try {
      console.log('[Voice] Stopping recording...');

      clearTimers();

      const remainingText = accumulatedTextRef.current.trim();
      if (remainingText && remainingText !== lastSentTextRef.current) {
        console.log('[Voice] Sending final transcript:', remainingText);
        onTranscriptComplete?.(remainingText, state.detectedLanguage || state.currentLanguage);
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
  }, [onTranscriptComplete, state.currentLanguage, state.detectedLanguage]);

  const toggleRecording = useCallback(async () => {
    if (state.isRecording) {
      await stopRecording();
    } else {
      // Build language priority list
      const languages = [state.currentLanguage];
      if (preferredLanguages.length > 0) {
        languages.push(...preferredLanguages.filter(l => l !== state.currentLanguage));
      }
      await startRecording(languages[0]);
    }
  }, [state.isRecording, state.currentLanguage, preferredLanguages, startRecording, stopRecording]);

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

  const setLanguage = useCallback((language: string) => {
    saveLanguagePreference(language);
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
    setLanguage,
    connect,
    disconnect,
  };
}