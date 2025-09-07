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
        return { name: 'POT_PALACE', code: '0x001' };
      case 'modern-minimal':
        return { name: 'MODERN_MIN', code: '0x002' };
      case 'dark-tech':
        return { name: 'DARK_TECH', code: '0x003' };
      default:
        return { name: template.toUpperCase(), code: '0x000' };
    }
  };

  return (
    <div className="relative font-mono">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-3 py-2 bg-black border border-cyan-400 text-cyan-400 hover:bg-cyan-400 hover:text-black transition-all duration-200 flex items-center justify-between text-xs"
      >
        <span className="flex items-center gap-2">
          <span className="text-green-400">&gt;</span>
          <span>[THEME::{getTemplateInfo(currentTemplate).name}]</span>
        </span>
        <span className="text-xs opacity-60">{isOpen ? '▲' : '▼'}</span>
      </button>

      {isOpen && (
        <div className="absolute top-full mt-1 w-full bg-black border border-cyan-400 shadow-lg shadow-cyan-400/20 overflow-hidden z-50">
          <div className="text-xs">
            <div className="px-3 py-2 border-b border-cyan-400/30 text-green-400">
              SELECT_TEMPLATE:
            </div>
            {availableTemplates.map((template) => {
              const info = getTemplateInfo(template);
              return (
                <button
                  key={template}
                  onClick={() => {
                    onTemplateChange(template);
                    setIsOpen(false);
                  }}
                  className={`w-full px-3 py-2 text-left transition-all duration-200 flex items-center justify-between hover:bg-cyan-400/10 ${
                    template === currentTemplate
                      ? 'bg-cyan-400/20 text-cyan-300'
                      : 'text-cyan-400'
                  }`}
                >
                  <span className="flex items-center gap-2">
                    <span className="opacity-60">{info.code}</span>
                    <span>{info.name}</span>
                  </span>
                  {template === currentTemplate && (
                    <span className="text-green-400">[ACTIVE]</span>
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