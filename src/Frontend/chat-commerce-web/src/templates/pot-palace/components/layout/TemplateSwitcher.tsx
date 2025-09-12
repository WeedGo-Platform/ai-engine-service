import React, { useState } from 'react';
import { TemplateSwitcherProps } from '../../../../core/contracts/template.contracts';

const TemplateSwitcher: React.FC<TemplateSwitcherProps> = ({ 
  currentTemplate, 
  availableTemplates, 
  onTemplateChange 
}) => {
  const [isOpen, setIsOpen] = useState(false);

  const getTemplateDisplayName = (template: string) => {
    switch (template) {
      case 'pot-palace':
        return '🌿 Pot Palace';
      case 'modern-minimal':
        return '⚡ Modern Minimal';
      case 'dark-tech':
        return '💻 Dark Tech';
      default:
        return template;
    }
  };

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-4 py-3 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-semibold rounded-xl shadow-lg flex items-center justify-between transition-all duration-200 transform hover:scale-105"
      >
        <span className="flex items-center gap-2">
          <span className="text-yellow-300">✨</span>
          {getTemplateDisplayName(currentTemplate)}
        </span>
        <svg
          className={`w-4 h-4 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <div className="absolute top-full mt-2 w-full bg-gradient-to-br from-purple-900/95 via-purple-800/95 to-pink-900/95 backdrop-blur-xl rounded-xl shadow-2xl border border-purple-400/30 overflow-hidden z-50">
          <div className="p-2">
            {availableTemplates.map((template) => (
              <button
                key={template}
                onClick={() => {
                  onTemplateChange(template);
                  setIsOpen(false);
                }}
                className={`w-full px-4 py-3 rounded-lg text-left transition-all duration-200 flex items-center gap-3 ${
                  template === currentTemplate
                    ? 'bg-gradient-to-r from-yellow-400/20 to-purple-400/20 text-yellow-300'
                    : 'text-purple-100 hover:bg-purple-700/30 hover:text-white'
                }`}
              >
                <span className="text-lg">{getTemplateDisplayName(template).split(' ')[0]}</span>
                <span className="font-medium">{getTemplateDisplayName(template).slice(2)}</span>
                {template === currentTemplate && (
                  <span className="ml-auto text-yellow-400">✓</span>
                )}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default TemplateSwitcher;