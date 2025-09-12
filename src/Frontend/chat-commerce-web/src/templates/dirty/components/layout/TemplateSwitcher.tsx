import React, { useState } from 'react';
import { TemplateSwitcherProps } from '../../../../core/contracts/template.contracts';

const TemplateSwitcher: React.FC<TemplateSwitcherProps> = ({ 
  currentTemplate, 
  availableTemplates, 
  onTemplateChange 
}) => {
  const [isOpen, setIsOpen] = useState(false);

  const getTemplateInfo = (template: string) => {
    switch (template) {
      case 'pot-palace':
        return { name: 'Pot Palace', icon: '🌿' };
      case 'modern-minimal':
        return { name: 'Modern Minimal', icon: '◆' };
      case 'dark-tech':
        return { name: 'Dark Tech', icon: '▲' };
      case 'rasta-vibes':
        return { name: 'Rasta Vibes', icon: '🌴' };
      case 'weedgo':
        return { name: 'WeedGo', icon: '🚀' };
      case 'vintage':
        return { name: 'Vintage', icon: '📜' };
      case 'dirty':
        return { name: 'Dirty', icon: '🌑' };
      case 'metal':
        return { name: 'Metal', icon: '⚡' };
      default:
        return { name: template, icon: '●' };
    }
  };

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-4 py-2.5 bg-[#282828] hover:bg-[#3C3C3C] border border-[#4A4A4A] text-[#D3D3D3] font-medium rounded-lg shadow-sm flex items-center justify-between transition-all duration-200"
      >
        <span className="flex items-center gap-2">
          <span className="text-[#A9A9A9]">{getTemplateInfo(currentTemplate).icon}</span>
          <span>{getTemplateInfo(currentTemplate).name}</span>
        </span>
        <svg
          className={`w-4 h-4 text-[#A9A9A9] transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <div className="absolute top-full mt-2 w-full bg-[#282828] rounded-lg shadow-lg border border-[#4A4A4A] overflow-hidden z-50">
          <div className="py-1">
            {availableTemplates.map((template) => {
              const info = getTemplateInfo(template);
              return (
                <button
                  key={template}
                  onClick={() => {
                    onTemplateChange(template);
                    setIsOpen(false);
                  }}
                  className={`w-full px-4 py-2.5 text-left transition-all duration-200 flex items-center gap-3 ${
                    template === currentTemplate
                      ? 'bg-[#5C4033] text-[#D3D3D3]'
                      : 'text-[#D3D3D3] hover:bg-[#3C3C3C]'
                  }`}
                >
                  <span className="text-[#A9A9A9]">{info.icon}</span>
                  <span className="font-medium">{info.name}</span>
                  {template === currentTemplate && (
                    <svg className="ml-auto w-4 h-4 text-[#8B7355]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  )}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

export default TemplateSwitcher;