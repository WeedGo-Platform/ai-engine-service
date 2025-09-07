import React from 'react';
import type { TextInputWindowProps } from '../../../../core/contracts/template.contracts';

const TextInputWindow: React.FC<TextInputWindowProps> = ({
  value,
  onChange,
  onKeyPress,
  placeholder = "Type your message...",
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
      placeholder={disabled ? "System offline" : placeholder}
      disabled={disabled}
      className="flex-1 px-5 py-3.5 bg-white border border-gray-200 rounded-xl text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-300 focus:border-transparent transition-all shadow-sm"
    />
  );
};

export default TextInputWindow;