import React from 'react';
import { motion } from 'framer-motion';

export interface QuickAction {
  id: string;
  label: string;
  value: string;
  type: 'product' | 'effect' | 'category' | 'price' | 'confirm' | 'info' | 'navigate';
  icon?: string;
  metadata?: any;
}

interface QuickActionButtonProps {
  action: QuickAction;
  onClick: (action: QuickAction) => void;
  disabled?: boolean;
}

const typeStyles = {
  product: 'bg-weed-green-500 hover:bg-weed-green-600 text-white',
  effect: 'bg-purple-500 hover:bg-purple-600 text-white',
  category: 'bg-blue-500 hover:bg-blue-600 text-white',
  price: 'bg-yellow-500 hover:bg-yellow-600 text-white',
  confirm: 'bg-green-500 hover:bg-green-600 text-white',
  info: 'bg-gray-500 hover:bg-gray-600 text-white',
  navigate: 'bg-indigo-500 hover:bg-indigo-600 text-white'
};

const typeIcons = {
  product: '🌿',
  effect: '✨',
  category: '📦',
  price: '💰',
  confirm: '✅',
  info: 'ℹ️',
  navigate: '➡️'
};

export default function QuickActionButton({ action, onClick, disabled = false }: QuickActionButtonProps) {
  return (
    <motion.button
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      onClick={() => onClick(action)}
      disabled={disabled}
      className={`
        px-4 py-2 rounded-full font-medium text-sm
        transition-all duration-200 shadow-sm
        disabled:opacity-50 disabled:cursor-not-allowed
        flex items-center gap-2
        ${typeStyles[action.type]}
      `}
    >
      <span className="text-base">{action.icon || typeIcons[action.type]}</span>
      <span>{action.label}</span>
    </motion.button>
  );
}

export function QuickActionGroup({ 
  actions, 
  onActionClick,
  title 
}: { 
  actions: QuickAction[]; 
  onActionClick: (action: QuickAction) => void;
  title?: string;
}) {
  if (!actions || actions.length === 0) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="mt-3 p-3 bg-gray-50 rounded-lg"
    >
      {title && (
        <p className="text-xs text-gray-600 mb-2 font-medium">{title}</p>
      )}
      <div className="flex flex-wrap gap-2">
        {actions.map((action) => (
          <QuickActionButton
            key={action.id}
            action={action}
            onClick={onActionClick}
          />
        ))}
      </div>
    </motion.div>
  );
}