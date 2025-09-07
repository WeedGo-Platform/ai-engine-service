import React, { useState, useRef, useEffect } from 'react';
import { useTemplateContext } from '../../contexts/TemplateContext';

const TEMPLATE_INFO = {
  'pot-palace': {
    name: 'Pot Palace',
    description: 'Vibrant purple gradient theme',
    icon: '🎨',
    color: '#E91ED4'
  },
  'modern-minimal': {
    name: 'Modern Minimal',
    description: 'Clean and minimalist design',
    icon: '⚪',
    color: '#000000'
  },
  'dark-tech': {
    name: 'Dark Tech',
    description: 'Futuristic terminal theme',
    icon: '💻',
    color: '#00FF88'
  }
};

export function TemplateSwitcher() {
  const { currentTemplate, availableTemplates, switchTemplate } = useTemplateContext();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const currentTemplateInfo = TEMPLATE_INFO[currentTemplate as keyof typeof TEMPLATE_INFO];

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="p-2.5 rounded-full hover:bg-white/20 transition-all group flex items-center gap-2"
        title="Switch Template"
      >
        <span className="text-lg">{currentTemplateInfo?.icon || '🎨'}</span>
        <svg 
          className={`w-4 h-4 text-white transition-transform ${isOpen ? 'rotate-180' : ''}`} 
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-64 bg-white rounded-xl shadow-2xl overflow-hidden z-50">
          <div className="p-3 bg-gray-50 border-b">
            <h3 className="text-sm font-semibold text-gray-700">Choose Theme</h3>
          </div>
          
          <div className="p-2">
            {availableTemplates.map((template) => {
              const info = TEMPLATE_INFO[template as keyof typeof TEMPLATE_INFO];
              const isActive = template === currentTemplate;
              
              return (
                <button
                  key={template}
                  onClick={() => {
                    switchTemplate(template);
                    setIsOpen(false);
                  }}
                  className={`
                    w-full p-3 rounded-lg transition-all flex items-start gap-3
                    ${isActive 
                      ? 'bg-gradient-to-r from-purple-50 to-pink-50 border border-purple-200' 
                      : 'hover:bg-gray-50'
                    }
                  `}
                >
                  <div 
                    className="w-10 h-10 rounded-lg flex items-center justify-center text-lg"
                    style={{ 
                      backgroundColor: isActive ? info?.color + '20' : '#f3f4f6',
                      color: info?.color
                    }}
                  >
                    {info?.icon}
                  </div>
                  
                  <div className="flex-1 text-left">
                    <div className="font-medium text-gray-900 flex items-center gap-2">
                      {info?.name}
                      {isActive && (
                        <span className="text-xs bg-purple-500 text-white px-2 py-0.5 rounded-full">
                          Active
                        </span>
                      )}
                    </div>
                    <div className="text-xs text-gray-500 mt-0.5">
                      {info?.description}
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}