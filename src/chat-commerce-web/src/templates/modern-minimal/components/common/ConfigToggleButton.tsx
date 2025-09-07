import React from 'react';

interface ConfigToggleButtonProps {
  isPanelOpen: boolean;
  onClick: () => void;
}

const ConfigToggleButton: React.FC<ConfigToggleButtonProps> = ({ isPanelOpen, onClick }) => {
  if (isPanelOpen) return null;

  return (
    <button
      onClick={onClick}
      className="fixed left-4 top-[92px] z-30 p-3 bg-white hover:bg-slate-100 border border-slate-300 rounded-xl transition-all group shadow-lg"
    >
      <svg className="w-5 h-5 text-[#E91ED4] group-hover:text-[#FF006E]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16" />
      </svg>
    </button>
  );
};

export default ConfigToggleButton;