import React from 'react';
import { ICartItemProps } from '../../types';
import { clsx } from 'clsx';
import { PotPalaceButton } from './Button';

export const PotPalaceCartItem: React.FC<ICartItemProps> = ({
  item,
  onUpdateQuantity,
  onRemove,
  variant = 'default',
  className
}) => {
  return (
    <div className={clsx(
      'flex items-center gap-4 p-4',
      'bg-white rounded-2xl border-3 border-green-200',
      'hover:shadow-lg transition-all duration-300',
      className
    )}>
      <img
        src={item.product.image_url}
        alt={item.product.name}
        className="w-20 h-20 object-cover rounded-xl"
      />

      <div className="flex-1">
        <h3 className="font-bold text-gray-800">{item.product.name}</h3>
        <p className="text-sm text-gray-600">
          THC: {item.product.thc_content}% | CBD: {item.product.cbd_content}%
        </p>
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={() => onUpdateQuantity(item.id, Math.max(0, item.quantity - 1))}
          className="w-8 h-8 rounded-full bg-yellow-400 text-gray-800 font-bold hover:bg-yellow-500"
        >
          -
        </button>
        <span className="font-bold px-3">{item.quantity}</span>
        <button
          onClick={() => onUpdateQuantity(item.id, item.quantity + 1)}
          className="w-8 h-8 rounded-full bg-green-500 text-white font-bold hover:bg-green-600"
        >
          +
        </button>
      </div>

      <div className="text-right">
        <p className="font-bold text-green-600">${(item.price * item.quantity).toFixed(2)}</p>
        <button
          onClick={() => onRemove(item.id)}
          className="text-red-500 hover:text-red-700 text-sm"
        >
          Remove
        </button>
      </div>
    </div>
  );
};
