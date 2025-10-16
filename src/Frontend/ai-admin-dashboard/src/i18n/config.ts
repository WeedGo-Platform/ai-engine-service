import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import { applyTextDirection } from '../utils/rtl';

// Supported languages configuration
export const SUPPORTED_LANGUAGES = [
  { code: 'en', name: 'English', flag: '🇺🇸', nativeName: 'English' },
  { code: 'es', name: 'Spanish', flag: '🇪🇸', nativeName: 'Español' },
  { code: 'fr', name: 'French', flag: '🇫🇷', nativeName: 'Français' },
  { code: 'zh', name: 'Mandarin', flag: '🇨🇳', nativeName: '中文' },
  { code: 'yue', name: 'Cantonese', flag: '🇭🇰', nativeName: '廣東話' },
  { code: 'pa', name: 'Punjabi', flag: '🇮🇳', nativeName: 'ਪੰਜਾਬੀ' },
  { code: 'ar', name: 'Arabic', flag: '🇸🇦', nativeName: 'العربية' },
  { code: 'tl', name: 'Tagalog', flag: '🇵🇭', nativeName: 'Tagalog' },
  { code: 'de', name: 'German', flag: '🇩🇪', nativeName: 'Deutsch' },
  { code: 'it', name: 'Italian', flag: '🇮🇹', nativeName: 'Italiano' },
  { code: 'pt', name: 'Portuguese', flag: '🇵🇹', nativeName: 'Português' },
  { code: 'pl', name: 'Polish', flag: '🇵🇱', nativeName: 'Polski' },
  { code: 'ru', name: 'Russian', flag: '🇷🇺', nativeName: 'Русский' },
  { code: 'vi', name: 'Vietnamese', flag: '🇻🇳', nativeName: 'Tiếng Việt' },
  { code: 'hi', name: 'Hindi', flag: '🇮🇳', nativeName: 'हिन्दी' },
  { code: 'uk', name: 'Ukrainian', flag: '🇺🇦', nativeName: 'Українська' },
  { code: 'fa', name: 'Persian', flag: '🇮🇷', nativeName: 'فارسی' },
  { code: 'ko', name: 'Korean', flag: '🇰🇷', nativeName: '한국어' },
  { code: 'ta', name: 'Tamil', flag: '🇮🇳', nativeName: 'தமிழ்' },
  { code: 'ur', name: 'Urdu', flag: '🇵🇰', nativeName: 'اردو' },
  { code: 'gu', name: 'Gujarati', flag: '🇮🇳', nativeName: 'ગુજરાતી' },
  { code: 'ro', name: 'Romanian', flag: '🇷🇴', nativeName: 'Română' },
  { code: 'nl', name: 'Dutch', flag: '🇳🇱', nativeName: 'Nederlands' },
  { code: 'cr', name: 'Cree', flag: '🇨🇦', nativeName: 'ᓀᐦᐃᔭᐍᐏᐣ' },
  { code: 'iu', name: 'Inuktitut', flag: '🇨🇦', nativeName: 'ᐃᓄᒃᑎᑐᑦ' },
  { code: 'bn', name: 'Bengali', flag: '🇧🇩', nativeName: 'বাংলা' },
  { code: 'he', name: 'Hebrew', flag: '🇮🇱', nativeName: 'עברית' },
  { code: 'so', name: 'Somali', flag: '🇸🇴', nativeName: 'Soomaali' },
  { code: 'ja', name: 'Japanese', flag: '🇯🇵', nativeName: '日本語' },
] as const;

export type SupportedLanguage = typeof SUPPORTED_LANGUAGES[number]['code'];

// All available namespaces
const namespaces = ['common', 'auth', 'dashboard', 'landing', 'forms', 'errors', 'modals', 'tenants', 'stores', 'inventory', 'orders', 'pos', 'payments', 'settings', 'communications', 'database', 'promotions', 'catalog', 'apps', 'tools', 'signup'];

// Dynamically load resources for all languages and namespaces
const loadResources = () => {
  const resources: Record<string, Record<string, any>> = {};

  SUPPORTED_LANGUAGES.forEach(({ code }) => {
    resources[code] = {};
    namespaces.forEach(ns => {
      try {
        // @ts-ignore - Dynamic imports
        resources[code][ns] = require(`./locales/${code}/${ns}.json`);
      } catch (error) {
        console.warn(`Failed to load namespace "${ns}" for language "${code}"`);
      }
    });
  });

  return resources;
};

// Language resources
export const resources = loadResources();

i18n
  // Detect user language
  .use(LanguageDetector)
  // Pass the i18n instance to react-i18next
  .use(initReactI18next)
  // Initialize i18next
  .init({
    resources,
    fallbackLng: 'en',
    defaultNS: 'common',
    ns: namespaces,

    // Language detection options
    detection: {
      order: ['localStorage', 'navigator', 'htmlTag'],
      caches: ['localStorage'],
      lookupLocalStorage: 'i18nextLng',
    },

    interpolation: {
      escapeValue: false, // React already escapes values
    },

    // React specific options
    react: {
      useSuspense: false, // We'll handle loading states manually
    },

    // Debug mode (disable in production)
    debug: import.meta.env.DEV,
  });

// Apply RTL direction on language change
i18n.on('languageChanged', (lng) => {
  applyTextDirection(lng);
});

// Initialize RTL on startup
applyTextDirection(i18n.language);

export default i18n;
