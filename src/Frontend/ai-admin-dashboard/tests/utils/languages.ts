/**
 * Language Configuration for Multilingual Testing
 */

export interface LanguageConfig {
  code: string;
  name: string;
  nativeName: string;
  isRTL: boolean;
  script: string;
  testPhrase: string; // A phrase that should appear in the UI
}

export const LANGUAGES: LanguageConfig[] = [
  { code: 'en', name: 'English', nativeName: 'English', isRTL: false, script: 'Latin', testPhrase: 'Dashboard' },
  { code: 'ar', name: 'Arabic', nativeName: 'العربية', isRTL: true, script: 'Arabic', testPhrase: 'لوحة التحكم' },
  { code: 'bn', name: 'Bengali', nativeName: 'বাংলা', isRTL: false, script: 'Bengali', testPhrase: 'ড্যাশবোর্ড' },
  { code: 'cr', name: 'Cree', nativeName: 'ᓀᐦᐃᔭᐍᐏᐣ', isRTL: false, script: 'Cree Syllabics', testPhrase: 'ᒪᓯᓇᐦᐄᑲᐣ' },
  { code: 'de', name: 'German', nativeName: 'Deutsch', isRTL: false, script: 'Latin', testPhrase: 'Dashboard' },
  { code: 'es', name: 'Spanish', nativeName: 'Español', isRTL: false, script: 'Latin', testPhrase: 'Panel' },
  { code: 'fa', name: 'Persian', nativeName: 'فارسی', isRTL: true, script: 'Persian', testPhrase: 'داشبورد' },
  { code: 'fr', name: 'French', nativeName: 'Français', isRTL: false, script: 'Latin', testPhrase: 'Tableau de bord' },
  { code: 'gu', name: 'Gujarati', nativeName: 'ગુજરાતી', isRTL: false, script: 'Gujarati', testPhrase: 'ડેશબોર્ડ' },
  { code: 'he', name: 'Hebrew', nativeName: 'עברית', isRTL: true, script: 'Hebrew', testPhrase: 'לוח בקרה' },
  { code: 'hi', name: 'Hindi', nativeName: 'हिन्दी', isRTL: false, script: 'Devanagari', testPhrase: 'डैशबोर्ड' },
  { code: 'it', name: 'Italian', nativeName: 'Italiano', isRTL: false, script: 'Latin', testPhrase: 'Cruscotto' },
  { code: 'iu', name: 'Inuktitut', nativeName: 'ᐃᓄᒃᑎᑐᑦ', isRTL: false, script: 'Inuktitut Syllabics', testPhrase: 'ᐊᐅᓚᑦᑎᔨᒃᑯᑦ' },
  { code: 'ja', name: 'Japanese', nativeName: '日本語', isRTL: false, script: 'Japanese', testPhrase: 'ダッシュボード' },
  { code: 'ko', name: 'Korean', nativeName: '한국어', isRTL: false, script: 'Korean', testPhrase: '대시보드' },
  { code: 'nl', name: 'Dutch', nativeName: 'Nederlands', isRTL: false, script: 'Latin', testPhrase: 'Dashboard' },
  { code: 'pa', name: 'Punjabi', nativeName: 'ਪੰਜਾਬੀ', isRTL: false, script: 'Gurmukhi', testPhrase: 'ਡੈਸ਼ਬੋਰਡ' },
  { code: 'pl', name: 'Polish', nativeName: 'Polski', isRTL: false, script: 'Latin', testPhrase: 'Panel' },
  { code: 'pt', name: 'Portuguese', nativeName: 'Português', isRTL: false, script: 'Latin', testPhrase: 'Painel' },
  { code: 'ro', name: 'Romanian', nativeName: 'Română', isRTL: false, script: 'Latin', testPhrase: 'Tablou de bord' },
  { code: 'ru', name: 'Russian', nativeName: 'Русский', isRTL: false, script: 'Cyrillic', testPhrase: 'Панель управления' },
  { code: 'so', name: 'Somali', nativeName: 'Soomaali', isRTL: false, script: 'Latin', testPhrase: 'Dashboard' },
  { code: 'ta', name: 'Tamil', nativeName: 'தமிழ்', isRTL: false, script: 'Tamil', testPhrase: 'டாஷ்போர்டு' },
  { code: 'tl', name: 'Tagalog', nativeName: 'Tagalog', isRTL: false, script: 'Latin', testPhrase: 'Dashboard' },
  { code: 'uk', name: 'Ukrainian', nativeName: 'Українська', isRTL: false, script: 'Cyrillic', testPhrase: 'Панель керування' },
  { code: 'ur', name: 'Urdu', nativeName: 'اردو', isRTL: true, script: 'Urdu', testPhrase: 'ڈیش بورڈ' },
  { code: 'vi', name: 'Vietnamese', nativeName: 'Tiếng Việt', isRTL: false, script: 'Latin', testPhrase: 'Bảng điều khiển' },
  { code: 'yue', name: 'Cantonese', nativeName: '粵語', isRTL: false, script: 'Chinese', testPhrase: '儀表板' },
  { code: 'zh', name: 'Mandarin', nativeName: '中文', isRTL: false, script: 'Chinese', testPhrase: '仪表板' },
];

export const RTL_LANGUAGES = LANGUAGES.filter(lang => lang.isRTL);
export const LTR_LANGUAGES = LANGUAGES.filter(lang => !lang.isRTL);

export const getLanguageByCode = (code: string): LanguageConfig | undefined => {
  return LANGUAGES.find(lang => lang.code === code);
};

export const getLanguageGroups = () => {
  return {
    indigenous: LANGUAGES.filter(l => ['cr', 'iu'].includes(l.code)),
    asian: LANGUAGES.filter(l => ['bn', 'gu', 'hi', 'ja', 'ko', 'pa', 'ta', 'tl', 'vi', 'yue', 'zh'].includes(l.code)),
    middleEastern: LANGUAGES.filter(l => ['ar', 'fa', 'he', 'ur'].includes(l.code)),
    european: LANGUAGES.filter(l => ['de', 'es', 'fr', 'it', 'nl', 'pl', 'pt', 'ro', 'ru', 'uk', 'so'].includes(l.code)),
  };
};
