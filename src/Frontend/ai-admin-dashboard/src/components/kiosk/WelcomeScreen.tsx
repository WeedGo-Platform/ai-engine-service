import React, { useState, useEffect } from 'react';
import { getApiUrl } from '../../config/app.config';
import { Globe, UserCircle, Scan, ChevronRight, Users } from 'lucide-react';
import { useKiosk } from '../../contexts/KioskContext';
import CustomerAuthModal from './CustomerAuthModal';
import QRLoginModal from './QRLoginModal';

interface WelcomeScreenProps {
  onContinue: () => void;
  currentStore: any;
}

const LANGUAGES = [
  { code: 'en', name: 'English', flag: '🇬🇧' },
  { code: 'fr', name: 'Français', flag: '🇫🇷' },
  { code: 'zh', name: '中文', flag: '🇨🇳' },
  { code: 'es', name: 'Español', flag: '🇪🇸' },
  { code: 'pt', name: 'Português', flag: '🇵🇹' },
  { code: 'hi', name: 'हिन्दी', flag: '🇮🇳' },
];

const translations: Record<string, any> = {
  en: {
    welcome: 'Welcome to',
    selectLanguage: 'Select Your Language',
    orContinue: 'OR',
    scanQR: 'Scan QR to Sign In',
    signIn: 'Sign In with Phone/Email',
    continueAsGuest: 'Continue as Guest',
    touchToStart: 'Touch to Start Shopping',
  },
  fr: {
    welcome: 'Bienvenue à',
    selectLanguage: 'Sélectionnez votre langue',
    orContinue: 'OU',
    scanQR: 'Scanner le QR pour se connecter',
    signIn: 'Se connecter avec téléphone/email',
    continueAsGuest: 'Continuer en tant qu\'invité',
    touchToStart: 'Touchez pour commencer vos achats',
  },
  zh: {
    welcome: '欢迎来到',
    selectLanguage: '选择您的语言',
    orContinue: '或',
    scanQR: '扫描二维码登录',
    signIn: '使用手机/邮箱登录',
    continueAsGuest: '以访客身份继续',
    touchToStart: '触摸开始购物',
  },
  // Add more translations as needed
};

export default function WelcomeScreen({ onContinue, currentStore }: WelcomeScreenProps) {
  const { language, setLanguage, initializeSession } = useKiosk();
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [showQRModal, setShowQRModal] = useState(false);
  const [selectedLanguage, setSelectedLanguage] = useState(language);

  const t = translations[selectedLanguage] || translations['en'];

  // Handle language selection
  const handleLanguageSelect = (langCode: string) => {
    setSelectedLanguage(langCode);
    setLanguage(langCode);
  };

  // Handle guest continuation
  const handleGuestContinue = () => {
    initializeSession(undefined, selectedLanguage);
    onContinue();
  };

  // Handle successful authentication
  const handleAuthSuccess = (customer: any) => {
    initializeSession(customer, customer.language || selectedLanguage);
    onContinue();
  };

  return (
    <div className="h-full flex flex-col items-center justify-center bg-gradient-to-br from-primary-50 to-accent-50 p-8">
      {/* Store Branding */}
      <div className="text-center mb-12">
        <h1 className="text-5xl font-bold text-gray-800 mb-2">
          {t.welcome}
        </h1>
        <h2 className="text-4xl font-semibold text-primary-600">
          {currentStore?.name || 'Select Store'}
        </h2>
      </div>

      {/* Language Selection */}
      <div className="w-full max-w-4xl mb-12">
        <h3 className="text-2xl font-medium text-center mb-6 flex items-center justify-center text-gray-700">
          <Globe className="mr-3 text-primary-600" size={24} />
          <span>{t.selectLanguage}</span>
        </h3>
        <div className="grid grid-cols-3 gap-4">
          {LANGUAGES.map((lang) => (
            <button
              key={lang.code}
              onClick={() => handleLanguageSelect(lang.code)}
              className={`p-6 rounded-xl border-2 transition-all ${
                selectedLanguage === lang.code
                  ? 'border-primary-500 bg-primary-50 shadow-md'
                  : 'border-gray-200 bg-white hover:border-primary-300 hover:shadow-sm'
              }`}
            >
              <div className="text-4xl mb-2">{lang.flag}</div>
              <div className="text-lg font-medium">{lang.name}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Divider */}
      <div className="w-full max-w-2xl flex items-center mb-8">
        <div className="flex-1 border-t border-gray-300"></div>
        <span className="px-4 text-gray-500 font-medium">{t.orContinue}</span>
        <div className="flex-1 border-t border-gray-300"></div>
      </div>

      {/* Action Buttons */}
      <div className="w-full max-w-2xl space-y-4">
        {/* QR Code Login */}
        <button
          onClick={() => setShowQRModal(true)}
          className="w-full p-6 bg-white rounded-xl shadow-lg hover:shadow-xl transition-all flex items-center justify-between group"
        >
          <div className="flex items-center">
            <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center mr-4">
              <Scan className="w-6 h-6 text-primary-600" />
            </div>
            <span className="text-xl font-medium text-gray-800">{t.scanQR}</span>
          </div>
          <ChevronRight className="w-5 h-5 text-gray-400 group-hover:text-primary-600 transition-colors" />
        </button>

        {/* Phone/Email Login */}
        <button
          onClick={() => setShowAuthModal(true)}
          className="w-full p-6 bg-white rounded-xl shadow-lg hover:shadow-xl transition-all flex items-center justify-between group"
        >
          <div className="flex items-center">
            <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center mr-4">
              <UserCircle className="w-6 h-6 text-primary-600" />
            </div>
            <span className="text-xl font-medium text-gray-800">{t.signIn}</span>
          </div>
          <ChevronRight className="w-5 h-5 text-gray-400 group-hover:text-primary-600 transition-colors" />
        </button>

        {/* Guest Continue */}
        <button
          onClick={handleGuestContinue}
          className="w-full p-6 bg-primary-600 hover:bg-primary-700 text-white rounded-xl shadow-lg hover:shadow-xl transition-all flex items-center justify-between group"
        >
          <div className="flex items-center">
            <div className="w-12 h-12 bg-white/20 rounded-lg flex items-center justify-center mr-4">
              <Users className="w-6 h-6 text-white" />
            </div>
            <div className="text-left">
              <span className="text-xl font-semibold block">{t.continueAsGuest}</span>
              <div className="text-sm opacity-90">{t.touchToStart}</div>
            </div>
          </div>
          <ChevronRight className="w-5 h-5 text-white/70 group-hover:text-white transition-colors" />
        </button>
      </div>

      {/* Modals */}
      {showAuthModal && (
        <CustomerAuthModal
          isOpen={showAuthModal}
          onClose={() => setShowAuthModal(false)}
          onSuccess={handleAuthSuccess}
          language={selectedLanguage}
        />
      )}

      {showQRModal && (
        <QRLoginModal
          isOpen={showQRModal}
          onClose={() => setShowQRModal(false)}
          onSuccess={handleAuthSuccess}
          language={selectedLanguage}
        />
      )}
    </div>
  );
}