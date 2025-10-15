import { useState, useCallback } from 'react';
import { useTranslation } from 'react-i18next';

const API_URL = import.meta.env.VITE_TRANSLATION_API_URL || 'http://localhost:5024/api/translate';

interface TranslationRequest {
  text: string;
  targetLanguage: string;
  sourceLanguage?: string;
  context?: string;
  namespace?: string;
  useCache?: boolean;
}

interface TranslationResponse {
  success: boolean;
  original: string;
  translated: string;
  target_language: string;
  cache_hit?: boolean;
  source?: string;
  error?: string;
}

interface UseBackendTranslationReturn {
  translateText: (request: TranslationRequest) => Promise<string>;
  isTranslating: boolean;
  error: string | null;
  clearError: () => void;
}

/**
 * Hook for dynamic backend translations
 * Use this for translating user-generated content or dynamic text
 * For static UI text, use the i18next translations instead
 */
export const useBackendTranslation = (): UseBackendTranslationReturn => {
  const { i18n } = useTranslation();
  const [isTranslating, setIsTranslating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const translateText = useCallback(
    async (request: TranslationRequest): Promise<string> => {
      setIsTranslating(true);
      setError(null);

      try {
        // Use current i18n language if target not specified
        const targetLang = request.targetLanguage || i18n.language;

        // Skip translation if already in target language
        if (targetLang === (request.sourceLanguage || 'en')) {
          setIsTranslating(false);
          return request.text;
        }

        const response = await fetch(API_URL, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            text: request.text,
            target_language: targetLang,
            source_language: request.sourceLanguage || 'en',
            context: request.context,
            namespace: request.namespace,
            use_cache: request.useCache !== false, // Default to true
          }),
        });

        if (!response.ok) {
          throw new Error(`Translation API error: ${response.status}`);
        }

        const result: TranslationResponse = await response.json();

        if (result.success && result.translated) {
          console.log(
            `[useBackendTranslation] Translated to ${targetLang} (cache_hit: ${result.cache_hit})`
          );
          return result.translated;
        } else {
          throw new Error(result.error || 'Translation failed');
        }
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Translation error';
        console.error('[useBackendTranslation] Error:', errorMessage);
        setError(errorMessage);
        // Return original text on error
        return request.text;
      } finally {
        setIsTranslating(false);
      }
    },
    [i18n.language]
  );

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    translateText,
    isTranslating,
    error,
    clearError,
  };
};

/**
 * Hook for translating dynamic greeting messages
 * Pre-configured for sales chat widget greeting translations
 */
export const useGreetingTranslation = () => {
  const { i18n } = useTranslation();
  const { translateText, isTranslating, error } = useBackendTranslation();

  const translateGreeting = useCallback(
    async (greetingText: string): Promise<string> => {
      // Skip if English
      if (i18n.language === 'en') {
        return greetingText;
      }

      return translateText({
        text: greetingText,
        targetLanguage: i18n.language,
        sourceLanguage: 'en',
        context: 'sales_chat_greeting',
        namespace: 'sales_widget',
        useCache: true,
      });
    },
    [i18n.language, translateText]
  );

  return {
    translateGreeting,
    isTranslating,
    error,
  };
};

export default useBackendTranslation;
