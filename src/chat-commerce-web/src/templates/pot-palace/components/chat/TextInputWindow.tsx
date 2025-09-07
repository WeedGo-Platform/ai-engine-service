import React from 'react';
import type { TextInputWindowProps } from '../../../../core/contracts/template.contracts';

const TextInputWindow: React.FC<TextInputWindowProps> = ({
  value,
  onChange,
  onKeyPress,
  placeholder = "Type your question here... (Cmd+K to focus)",
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
      placeholder={disabled ? "Load a model to start chatting" : placeholder}
      disabled={disabled}
      className="flex-1 px-5 py-3 bg-purple-900/50 border border-purple-600/30 rounded-xl text-purple-100 placeholder-purple-500 focus:outline-none focus:ring-2 focus:ring-pink-500/50 focus:border-transparent transition-all"
    />
  );
};

export default TextInputWindow;