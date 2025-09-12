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
      default:
        return { name: template, icon: '●' };
    }
  };

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-4 py-2.5 bg-white hover:bg-slate-50 border border-slate-300 text-slate-700 font-medium rounded-lg shadow-sm flex items-center justify-between transition-all duration-200"
      >
        <span className="flex items-center gap-2">
          <span className="text-slate-500">{getTemplateInfo(currentTemplate).icon}</span>
          <span>{getTemplateInfo(currentTemplate).name}</span>
        </span>
        <svg
          className={`w-4 h-4 text-slate-500 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <div className="absolute top-full mt-2 w-full bg-white rounded-lg shadow-lg border border-slate-200 overflow-hidden z-50">
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
                      ? 'bg-slate-100 text-slate-900'
                      : 'text-slate-700 hover:bg-slate-50'
                  }`}
                >
                  <span className="text-slate-500">{info.icon}</span>
                  <span className="font-medium">{info.name}</span>
                  {template === currentTemplate && (
                    <svg className="ml-auto w-4 h-4 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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