import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

// Import translation files
import commonEN from './locales/en/common.json';
import commonES from './locales/es/common.json';
import commonFR from './locales/fr/common.json';
import commonZH from './locales/zh/common.json';
import commonAR from './locales/ar/common.json';
import commonDE from './locales/de/common.json';
import commonJA from './locales/ja/common.json';

import authEN from './locales/en/auth.json';
import authES from './locales/es/auth.json';
import authFR from './locales/fr/auth.json';
import authZH from './locales/zh/auth.json';
import authAR from './locales/ar/auth.json';
import authDE from './locales/de/auth.json';
import authJA from './locales/ja/auth.json';

import dashboardEN from './locales/en/dashboard.json';
import dashboardES from './locales/es/dashboard.json';
import dashboardFR from './locales/fr/dashboard.json';
import dashboardZH from './locales/zh/dashboard.json';
import dashboardAR from './locales/ar/dashboard.json';
import dashboardDE from './locales/de/dashboard.json';
import dashboardJA from './locales/ja/dashboard.json';

import landingEN from './locales/en/landing.json';
import landingES from './locales/es/landing.json';
import landingFR from './locales/fr/landing.json';
import landingZH from './locales/zh/landing.json';
import landingAR from './locales/ar/landing.json';
import landingDE from './locales/de/landing.json';
import landingJA from './locales/ja/landing.json';

// Supported languages configuration
export const SUPPORTED_LANGUAGES = [
  { code: 'en', name: 'English', flag: '🇺🇸', nativeName: 'English' },
  { code: 'es', name: 'Spanish', flag: '🇪🇸', nativeName: 'Español' },
  { code: 'fr', name: 'French', flag: '🇫🇷', nativeName: 'Français' },
  { code: 'zh', name: 'Chinese', flag: '🇨🇳', nativeName: '中文' },
  { code: 'ar', name: 'Arabic', flag: '🇸🇦', nativeName: 'العربية' },
  { code: 'de', name: 'German', flag: '🇩🇪', nativeName: 'Deutsch' },
  { code: 'ja', name: 'Japanese', flag: '🇯🇵', nativeName: '日本語' },
] as const;

export type SupportedLanguage = typeof SUPPORTED_LANGUAGES[number]['code'];

// Language resources
const resources = {
  en: {
    common: commonEN,
    auth: authEN,
    dashboard: dashboardEN,
    landing: landingEN,
  },
  es: {
    common: commonES,
    auth: authES,
    dashboard: dashboardES,
    landing: landingES,
  },
  fr: {
    common: commonFR,
    auth: authFR,
    dashboard: dashboardFR,
    landing: landingFR,
  },
  zh: {
    common: commonZH,
    auth: authZH,
    dashboard: dashboardZH,
    landing: landingZH,
  },
  ar: {
    common: commonAR,
    auth: authAR,
    dashboard: dashboardAR,
    landing: landingAR,
  },
  de: {
    common: commonDE,
    auth: authDE,
    dashboard: dashboardDE,
    landing: landingDE,
  },
  ja: {
    common: commonJA,
    auth: authJA,
    dashboard: dashboardJA,
    landing: landingJA,
  },
};

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
    ns: ['common', 'auth', 'dashboard', 'landing'],
    
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

export default i18n;
