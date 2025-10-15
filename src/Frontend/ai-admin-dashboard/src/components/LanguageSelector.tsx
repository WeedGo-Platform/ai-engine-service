import React, { useState, useRef, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Globe, Check } from 'lucide-react';
import { SUPPORTED_LANGUAGES, type SupportedLanguage } from '../i18n/config';

interface LanguageSelectorProps {
  className?: string;
}

const LanguageSelector: React.FC<LanguageSelectorProps> = ({ className = '' }) => {
  const { i18n } = useTranslation();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const currentLanguage = SUPPORTED_LANGUAGES.find(
    (lang) => lang.code === i18n.language
  ) || SUPPORTED_LANGUAGES[0];

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  const handleLanguageChange = async (languageCode: SupportedLanguage) => {
    await i18n.changeLanguage(languageCode);
    setIsOpen(false);
    
    // Store preference in localStorage
    localStorage.setItem('i18nextLng', languageCode);
    
    console.log(`[LanguageSelector] Language changed to: ${languageCode}`);
  };

  return (
    <div className={`relative ${className}`} ref={dropdownRef}>
      {/* Language Toggle Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 p-2 text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg transition-all"
        title="Change Language"
        aria-label="Select Language"
        aria-expanded={isOpen}
      >
        <Globe className="h-5 w-5" />
        <span className="text-lg" aria-hidden="true">
          {currentLanguage.flag}
        </span>
      </button>

      {/* Language Dropdown */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-56 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg z-50 overflow-hidden">
          <div className="py-1">
            {SUPPORTED_LANGUAGES.map((language) => {
              const isSelected = language.code === i18n.language;
              
              return (
                <button
                  key={language.code}
                  onClick={() => handleLanguageChange(language.code)}
                  className={`w-full flex items-center justify-between px-4 py-2.5 text-sm transition-colors ${
                    isSelected
                      ? 'bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-400'
                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
                  }`}
                  role="menuitem"
                >
                  <div className="flex items-center gap-3">
                    <span className="text-xl" aria-hidden="true">
                      {language.flag}
                    </span>
                    <div className="text-left">
                      <div className="font-medium">{language.nativeName}</div>
                      <div className="text-xs text-gray-500 dark:text-gray-400">
                        {language.name}
                      </div>
                    </div>
                  </div>
                  {isSelected && (
                    <Check className="h-4 w-4 text-primary-600 dark:text-primary-400" />
                  )}
                </button>
              );
            })}
          </div>

          {/* Footer with language info */}
          <div className="border-t border-gray-200 dark:border-gray-700 px-4 py-2 bg-gray-50 dark:bg-gray-750">
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Language: <span className="font-medium">{currentLanguage.nativeName}</span>
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default LanguageSelector;
