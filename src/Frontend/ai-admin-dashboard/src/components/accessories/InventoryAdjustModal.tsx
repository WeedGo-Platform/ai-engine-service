import React, { useState } from 'react';
import {
  X, Plus, Minus, Edit2, AlertTriangle,
  Package, TrendingDown, RefreshCw
} from 'lucide-react';

interface InventoryAdjustModalProps {
  isOpen: boolean;
  onClose: () => void;
  accessory: any;
  onAdjust: (adjustment: any) => void;
}

const InventoryAdjustModal: React.FC<InventoryAdjustModalProps> = ({
  isOpen,
  onClose,
  accessory,
  onAdjust
}) => {
  const [adjustmentType, setAdjustmentType] = useState<'add' | 'remove' | 'set' | 'damage' | 'loss'>('add');
  const [quantity, setQuantity] = useState(1);
  const [reason, setReason] = useState('');
  const [notes, setNotes] = useState('');

  const handleSubmit = () => {
    if (quantity <= 0 && adjustmentType !== 'set') {
      return;
    }

    onAdjust({
      accessory_id: accessory.accessory_id,
      adjustment_type: adjustmentType,
      quantity,
      reason,
      notes
    });

    // Reset form
    setQuantity(1);
    setReason('');
    setNotes('');
  };

  if (!isOpen) return null;

  const getNewQuantity = () => {
    switch (adjustmentType) {
      case 'add':
        return accessory.quantity + quantity;
      case 'remove':
      case 'damage':
      case 'loss':
        return Math.max(0, accessory.quantity - quantity);
      case 'set':
        return quantity;
      default:
        return accessory.quantity;
    }
  };

  const adjustmentOptions = [
    { value: 'add', label: 'Add Stock', icon: Plus, color: 'text-primary-600' },
    { value: 'remove', label: 'Remove Stock', icon: Minus, color: 'text-accent-600' },
    { value: 'set', label: 'Set Count', icon: Edit2, color: 'text-purple-600' },
    { value: 'damage', label: 'Damaged', icon: AlertTriangle, color: 'text-orange-600' },
    { value: 'loss', label: 'Loss/Theft', icon: TrendingDown, color: 'text-danger-600' }
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black dark:bg-black bg-opacity-50 dark:bg-opacity-70 p-0 sm:p-4 transition-colors duration-200">
      <div className="bg-white dark:bg-gray-800 h-full sm:h-auto sm:rounded-lg border-0 sm:border border-gray-200 dark:border-gray-700 w-full sm:max-w-lg max-h-full sm:max-h-[90vh] overflow-y-auto flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 sm:p-6 border-b border-gray-200 dark:border-gray-700 flex-shrink-0 sticky top-0 bg-white dark:bg-gray-800 z-10">
          <div className="flex items-center gap-3 sm:gap-4">
            <Package className="w-5 h-5 sm:w-6 sm:h-6 text-accent-600 dark:text-accent-500" />
            <h2 className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-white">Adjust Inventory</h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 -mr-2 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg text-gray-900 dark:text-white transition-colors"
            aria-label="Close inventory adjust modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-4 sm:p-6 space-y-4 flex-1 overflow-y-auto">
          {/* Product Info */}
          <div className="p-3 sm:p-4 bg-gray-50 dark:bg-gray-700 rounded-lg transition-colors">
            <div className="flex items-center gap-3 sm:gap-4">
              {accessory.image_url ? (
                <img
                  src={accessory.image_url}
                  alt={accessory.name}
                  className="w-12 h-12 sm:w-14 sm:h-14 rounded object-cover flex-shrink-0"
                />
              ) : (
                <div className="w-12 h-12 sm:w-14 sm:h-14 bg-gray-100 dark:bg-gray-600 rounded flex items-center justify-center transition-colors flex-shrink-0">
                  <Package className="w-6 h-6 sm:w-7 sm:h-7 text-gray-400" />
                </div>
              )}
              <div className="flex-1 min-w-0">
                <p className="font-medium text-sm sm:text-base text-gray-900 dark:text-white truncate">{accessory.name}</p>
                <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400">SKU: {accessory.sku}</p>
              </div>
              <div className="text-right flex-shrink-0">
                <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400">Current Stock</p>
                <p className="text-lg sm:text-xl font-bold text-gray-900 dark:text-white">{accessory.quantity}</p>
              </div>
            </div>
          </div>

          {/* Adjustment Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Adjustment Type
            </label>
            <div className="grid grid-cols-2 gap-2 sm:gap-3">
              {adjustmentOptions.map(option => {
                const Icon = option.icon;
                return (
                  <button
                    key={option.value}
                    onClick={() => setAdjustmentType(option.value as any)}
                    className={`flex items-center justify-center sm:justify-start gap-2 p-2.5 sm:p-2 border rounded-lg transition-all active:scale-95 touch-manipulation ${
                      adjustmentType === option.value
                        ? 'border-blue-500 dark:border-blue-400 bg-blue-50 dark:bg-blue-900/30'
                        : 'border-gray-200 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700'
                    }`}
                  >
                    <Icon className={`w-4 h-4 flex-shrink-0 ${option.color}`} />
                    <span className="text-xs sm:text-sm text-gray-900 dark:text-white">{option.label}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Quantity */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              {adjustmentType === 'set' ? 'New Quantity' : 'Adjustment Quantity'}
            </label>
            <input
              type="number"
              value={quantity}
              onChange={(e) => setQuantity(parseInt(e.target.value) || 0)}
              min={adjustmentType === 'set' ? 0 : 1}
              className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 transition-colors"
            />
          </div>

          {/* Reason */}
          {['damage', 'loss'].includes(adjustmentType) && (
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Reason
              </label>
              <select
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 transition-colors"
              >
                <option value="">Select reason...</option>
                {adjustmentType === 'damage' && (
                  <>
                    <option value="shipping_damage">Shipping Damage</option>
                    <option value="customer_return">Customer Return</option>
                    <option value="expired">Expired</option>
                    <option value="other">Other</option>
                  </>
                )}
                {adjustmentType === 'loss' && (
                  <>
                    <option value="theft">Theft</option>
                    <option value="missing">Missing</option>
                    <option value="inventory_error">Inventory Error</option>
                    <option value="other">Other</option>
                  </>
                )}
              </select>
            </div>
          )}

          {/* Notes */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Notes (Optional)
            </label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={2}
              placeholder="Add any additional details..."
              className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 transition-colors"
            />
          </div>

          {/* Preview */}
          <div className="p-3 sm:p-4 bg-blue-50 dark:bg-blue-900/30 rounded-lg transition-colors">
            <div className="flex items-center justify-between">
              <span className="text-xs sm:text-sm text-gray-600 dark:text-gray-300">New Quantity:</span>
              <div className="flex items-center gap-2">
                <span className="text-base sm:text-lg text-gray-500 dark:text-gray-400">{accessory.quantity}</span>
                <RefreshCw className="w-3 h-3 sm:w-4 sm:h-4 text-gray-400" />
                <span className={`text-base sm:text-lg font-bold ${
                  getNewQuantity() < accessory.min_stock ? 'text-danger-600 dark:text-red-400' : 'text-primary-600 dark:text-primary-400'
                }`}>
                  {getNewQuantity()}
                </span>
              </div>
            </div>
            {getNewQuantity() < accessory.min_stock && (
              <p className="text-xs text-danger-600 dark:text-red-400 mt-2">
                Warning: This will put the item below minimum stock level ({accessory.min_stock})
              </p>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="flex flex-col-reverse sm:flex-row items-stretch sm:items-center justify-end gap-2 sm:gap-4 p-4 sm:p-6 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700 transition-colors flex-shrink-0 sticky bottom-0">
          <button
            onClick={onClose}
            className="w-full sm:w-auto px-4 py-2.5 sm:py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-600 text-gray-900 dark:text-white hover:bg-gray-50 dark:hover:bg-gray-500 transition-colors font-medium active:scale-95 touch-manipulation"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={quantity <= 0 && adjustmentType !== 'set'}
            className="w-full sm:w-auto px-4 py-2.5 sm:py-2 bg-accent-600 dark:bg-accent-500 text-white rounded-lg hover:bg-accent-700 dark:hover:bg-accent-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-semibold active:scale-95 touch-manipulation"
          >
            Apply Adjustment
          </button>
        </div>
      </div>
    </div>
  );
};

export default InventoryAdjustModal;