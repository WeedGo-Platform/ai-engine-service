/**
 * RTL (Right-to-Left) language detection and management utilities
 *
 * Handles text direction for languages like Arabic, Hebrew, Persian, and Urdu
 */

// List of RTL language codes
export const RTL_LANGUAGES = ['ar', 'he', 'fa', 'ur'] as const;

export type RTLLanguage = typeof RTL_LANGUAGES[number];

/**
 * Check if a language code is RTL
 * @param languageCode - ISO 639-1 language code (e.g., 'ar', 'en')
 * @returns true if language is RTL, false otherwise
 */
export const isRTL = (languageCode: string): boolean => {
  return RTL_LANGUAGES.includes(languageCode as RTLLanguage);
};

/**
 * Get text direction for a language
 * @param languageCode - ISO 639-1 language code
 * @returns 'rtl' or 'ltr'
 */
export const getTextDirection = (languageCode: string): 'rtl' | 'ltr' => {
  return isRTL(languageCode) ? 'rtl' : 'ltr';
};

/**
 * Apply text direction to document root element
 * @param languageCode - ISO 639-1 language code
 */
export const applyTextDirection = (languageCode: string): void => {
  const direction = getTextDirection(languageCode);
  document.documentElement.dir = direction;
  document.documentElement.lang = languageCode;

  // Store direction in localStorage for persistence
  localStorage.setItem('textDirection', direction);

  // Add direction class to body for CSS targeting
  document.body.classList.remove('rtl', 'ltr');
  document.body.classList.add(direction);
};

/**
 * Get stored text direction from localStorage
 * @returns stored direction or 'ltr' as default
 */
export const getStoredTextDirection = (): 'rtl' | 'ltr' => {
  const stored = localStorage.getItem('textDirection');
  return stored === 'rtl' ? 'rtl' : 'ltr';
};

/**
 * Initialize RTL support on app startup
 * @param currentLanguage - Current active language code
 */
export const initializeRTL = (currentLanguage: string): void => {
  applyTextDirection(currentLanguage);
};

/**
 * Hook for React components to get RTL status
 * @param languageCode - Current language code
 * @returns object with RTL information
 */
export const useRTLInfo = (languageCode: string) => {
  const isRTLLanguage = isRTL(languageCode);
  const direction = getTextDirection(languageCode);

  return {
    isRTL: isRTLLanguage,
    direction,
    textAlign: isRTLLanguage ? 'right' : 'left',
    flexDirection: isRTLLanguage ? 'row-reverse' : 'row',
  };
};
