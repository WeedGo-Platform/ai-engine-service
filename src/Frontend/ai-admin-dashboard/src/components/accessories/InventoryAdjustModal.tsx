import React, { useState } from 'react';
import {
  X, Plus, Minus, Edit2, AlertTriangle,
  Package, TrendingUp, TrendingDown, RefreshCw
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
    { value: 'add', label: 'Add Stock', icon: Plus, color: 'text-green-600' },
    { value: 'remove', label: 'Remove Stock', icon: Minus, color: 'text-blue-600' },
    { value: 'set', label: 'Set Count', icon: Edit2, color: 'text-purple-600' },
    { value: 'damage', label: 'Damaged', icon: AlertTriangle, color: 'text-orange-600' },
    { value: 'loss', label: 'Loss/Theft', icon: TrendingDown, color: 'text-red-600' }
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-lg">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center gap-3">
            <Package className="w-6 h-6 text-blue-600" />
            <h2 className="text-xl font-semibold">Adjust Inventory</h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          {/* Product Info */}
          <div className="p-3 bg-gray-50 rounded-lg">
            <div className="flex items-center gap-3">
              {accessory.image_url ? (
                <img
                  src={accessory.image_url}
                  alt={accessory.name}
                  className="w-12 h-12 rounded object-cover"
                />
              ) : (
                <div className="w-12 h-12 bg-gray-200 rounded flex items-center justify-center">
                  <Package className="w-6 h-6 text-gray-400" />
                </div>
              )}
              <div className="flex-1">
                <p className="font-medium">{accessory.name}</p>
                <p className="text-sm text-gray-500">SKU: {accessory.sku}</p>
              </div>
              <div className="text-right">
                <p className="text-sm text-gray-500">Current Stock</p>
                <p className="text-xl font-bold">{accessory.quantity}</p>
              </div>
            </div>
          </div>

          {/* Adjustment Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Adjustment Type
            </label>
            <div className="grid grid-cols-2 gap-2">
              {adjustmentOptions.map(option => {
                const Icon = option.icon;
                return (
                  <button
                    key={option.value}
                    onClick={() => setAdjustmentType(option.value as any)}
                    className={`flex items-center gap-2 p-2 border rounded-lg ${
                      adjustmentType === option.value
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    <Icon className={`w-4 h-4 ${option.color}`} />
                    <span className="text-sm">{option.label}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Quantity */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {adjustmentType === 'set' ? 'New Quantity' : 'Adjustment Quantity'}
            </label>
            <input
              type="number"
              value={quantity}
              onChange={(e) => setQuantity(parseInt(e.target.value) || 0)}
              min={adjustmentType === 'set' ? 0 : 1}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Reason */}
          {['damage', 'loss'].includes(adjustmentType) && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Reason
              </label>
              <select
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
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
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Notes (Optional)
            </label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={2}
              placeholder="Add any additional details..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Preview */}
          <div className="p-3 bg-blue-50 rounded-lg">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">New Quantity:</span>
              <div className="flex items-center gap-2">
                <span className="text-lg text-gray-500">{accessory.quantity}</span>
                <RefreshCw className="w-4 h-4 text-gray-400" />
                <span className={`text-lg font-bold ${
                  getNewQuantity() < accessory.min_stock ? 'text-red-600' : 'text-green-600'
                }`}>
                  {getNewQuantity()}
                </span>
              </div>
            </div>
            {getNewQuantity() < accessory.min_stock && (
              <p className="text-xs text-red-600 mt-1">
                Warning: This will put the item below minimum stock level ({accessory.min_stock})
              </p>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-3 p-6 border-t bg-gray-50">
          <button
            onClick={onClose}
            className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={quantity <= 0 && adjustmentType !== 'set'}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Apply Adjustment
          </button>
        </div>
      </div>
    </div>
  );
};

export default InventoryAdjustModal;