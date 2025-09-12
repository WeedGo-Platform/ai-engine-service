import React, { useState } from 'react';

interface Template {
  id: string;
  name: string;
  description: string;
  icon?: string;
}

interface TemplateSwitcherProps {
  currentTemplate: string;
  templates?: Template[];
  onTemplateChange?: (templateId: string) => void;
}

const TemplateSwitcher: React.FC<TemplateSwitcherProps> = ({
  currentTemplate,
  templates = [],
  onTemplateChange,
}) => {
  const [isOpen, setIsOpen] = useState(false);

  const defaultTemplates: Template[] = [
    { id: 'rasta-vibes', name: 'Rasta Vibes', description: 'Irie vibes with Rastafarian colors', icon: '🦁' },
    { id: 'pot-palace', name: 'Pot Palace', description: 'Classic cannabis theme', icon: '🏰' },
    { id: 'modern-minimal', name: 'Modern Minimal', description: 'Clean and minimalist', icon: '⚪' },
    { id: 'dark-tech', name: 'Dark Tech', description: 'Futuristic dark theme', icon: '🌑' },
  ];

  const availableTemplates = templates.length > 0 ? templates : defaultTemplates;
  const current = availableTemplates.find(t => t.id === currentTemplate);

  return (
    <div className="relative">
      {/* Trigger Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center space-x-2 px-4 py-2 rounded-lg transition-all hover:scale-105"
        style={{
          background: 'linear-gradient(135deg, rgba(252, 211, 77, 0.2) 0%, rgba(252, 211, 77, 0.1) 100%)',
          border: '2px solid rgba(252, 211, 77, 0.5)',
        }}
      >
        <span className="text-xl">{current?.icon || '🎨'}</span>
        <span 
          className="font-medium"
          style={{ color: '#FCD34D', fontFamily: 'Ubuntu, sans-serif' }}
        >
          {current?.name || 'Select Theme'}
        </span>
        <svg 
          className="w-4 h-4 transition-transform"
          fill="currentColor" 
          viewBox="0 0 24 24"
          style={{
            color: '#FCD34D',
            transform: isOpen ? 'rotate(180deg)' : 'rotate(0deg)',
          }}
        >
          <path d="M7 10l5 5 5-5z" />
        </svg>
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div 
          className="absolute top-full mt-2 right-0 w-72 rounded-xl overflow-hidden z-50 smooth-fade-in"
          style={{
            background: 'rgba(26, 26, 26, 0.98)',
            border: '3px solid transparent',
            backgroundImage: 'linear-gradient(rgba(26, 26, 26, 0.98), rgba(26, 26, 26, 0.98)), linear-gradient(90deg, #DC2626, #FCD34D, #16A34A)',
            backgroundOrigin: 'border-box',
            backgroundClip: 'padding-box, border-box',
            boxShadow: '0 10px 40px rgba(0, 0, 0, 0.5), 0 0 40px rgba(252, 211, 77, 0.2)',
            backdropFilter: 'blur(10px)',
          }}
        >
          {/* Header */}
          <div 
            className="px-4 py-3"
            style={{
              background: 'rgba(0, 0, 0, 0.5)',
              borderBottom: '1px solid rgba(252, 211, 77, 0.2)',
            }}
          >
            <h3 
              className="font-bold"
              style={{
                color: '#FCD34D',
                fontFamily: 'Bebas Neue, sans-serif',
                letterSpacing: '1px',
              }}
            >
              Choose Your Vibe
            </h3>
          </div>

          {/* Templates List */}
          <div className="max-h-64 overflow-y-auto">
            {availableTemplates.map((template) => (
              <button
                key={template.id}
                onClick={() => {
                  onTemplateChange?.(template.id);
                  setIsOpen(false);
                }}
                className="w-full px-4 py-3 flex items-start space-x-3 transition-all"
                style={{
                  background: currentTemplate === template.id 
                    ? 'rgba(252, 211, 77, 0.2)' 
                    : 'transparent',
                  borderBottom: '1px solid rgba(252, 211, 77, 0.1)',
                }}
                onMouseEnter={(e) => {
                  if (currentTemplate !== template.id) {
                    e.currentTarget.style.background = 'rgba(252, 211, 77, 0.1)';
                  }
                }}
                onMouseLeave={(e) => {
                  if (currentTemplate !== template.id) {
                    e.currentTarget.style.background = 'transparent';
                  }
                }}
              >
                <span className="text-2xl flex-shrink-0">{template.icon}</span>
                <div className="text-left">
                  <p 
                    className="font-semibold"
                    style={{ 
                      color: currentTemplate === template.id ? '#FCD34D' : '#F3E7C3',
                      fontFamily: 'Ubuntu, sans-serif',
                    }}
                  >
                    {template.name}
                  </p>
                  <p 
                    className="text-xs opacity-70"
                    style={{ color: '#F3E7C3' }}
                  >
                    {template.description}
                  </p>
                </div>
                {currentTemplate === template.id && (
                  <span 
                    className="ml-auto text-lg"
                    style={{ color: '#16A34A' }}
                  >
                    ✓
                  </span>
                )}
              </button>
            ))}
          </div>

          {/* Footer */}
          <div 
            className="px-4 py-2 text-center"
            style={{
              background: 'rgba(0, 0, 0, 0.5)',
              borderTop: '1px solid rgba(252, 211, 77, 0.2)',
            }}
          >
            <p 
              className="text-xs opacity-60"
              style={{ color: '#FCD34D' }}
            >
              Express yourself with style
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default TemplateSwitcher;