import React from 'react';
import type { TextInputWindowProps } from '../../../../core/contracts/template.contracts';

const TextInputWindow: React.FC<TextInputWindowProps> = ({
  value,
  onChange,
  onKeyPress,
  placeholder = "Enter command... [Cmd+K]",
  disabled = false,
  inputRef
}) => {
  return (
    <input
      ref={inputRef}
      type="text"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      onKeyPress={onKeyPress}
      placeholder={disabled ? "SYSTEM::OFFLINE" : placeholder}
      disabled={disabled}
      className="flex-1 px-4 py-3 bg-black/80 border border-cyan-500/30 rounded-lg text-cyan-300 placeholder-cyan-500/50 font-mono focus:outline-none focus:border-cyan-400 focus:shadow-[0_0_15px_rgba(6,182,212,0.3)] transition-all"
    />
  );
};

export default TextInputWindow;