import React, { useState, useEffect } from 'react';
import { X, Package, AlertCircle, ChevronDown, ChevronUp } from 'lucide-react';
import { getApiEndpoint } from '../config/app.config';

interface BatchDetail {
  batch_lot: string;
  quantity_remaining: number;
  quantity_received: number;
  unit_cost: number;
  case_gtin?: string;
  each_gtin?: string;
  gtin_barcode?: string;
  packaged_on_date?: string;
  supplier_name?: string;
  vendor?: string;
  brand?: string;
  po_number?: string;
}

interface InventoryItem {
  id: string;
  sku: string;
  name?: string;
  product_name?: string;
  category?: string;
  quantity_available: number;
  quantity_on_hand?: number;
  retail_price?: number;
  unit_cost?: number;
  reorder_point?: number;
  reorder_quantity?: number;
  is_available?: boolean;
  batch_lot?: string;
  batch_details?: BatchDetail[];
  store_id?: string;
}

interface BatchEditData {
  batch_lot: string;
  original_quantity: number;
  new_quantity: number;
  adjustment: number;
  reason: string;
  unit_cost: number;
}

interface InventoryEditModalProps {
  item: InventoryItem | null;
  isOpen: boolean;
  onClose: () => void;
  onSave: (updatedItem: Partial<InventoryItem>) => void;
  storeId?: string;
}

const adjustmentReasons = [
  'Cycle Count',
  'Damaged',
  'Expired',
  'Lost',
  'Theft',
  'Return',
  'Quality Issue',
  'Other'
];

const InventoryEditModal: React.FC<InventoryEditModalProps> = ({
  item,
  isOpen,
  onClose,
  onSave,
  storeId
}) => {
  const [batchEdits, setBatchEdits] = useState<BatchEditData[]>([]);
  const [expandedBatches, setExpandedBatches] = useState<Set<string>>(new Set());
  const [retailPrice, setRetailPrice] = useState<number>(0);
  const [reorderPoint, setReorderPoint] = useState<number>(10);
  const [reorderQuantity, setReorderQuantity] = useState<number>(50);
  const [isAvailable, setIsAvailable] = useState<boolean>(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (item) {
      // Initialize batch edit data from batch_details
      if (item.batch_details && item.batch_details.length > 0) {
        const edits = item.batch_details.map(batch => ({
          batch_lot: batch.batch_lot,
          original_quantity: batch.quantity_remaining || 0,
          new_quantity: batch.quantity_remaining || 0,
          adjustment: 0,
          reason: 'Cycle Count',
          unit_cost: batch.unit_cost || item.unit_cost || 0
        }));
        setBatchEdits(edits);
      } else if (item.batch_lot) {
        // Fallback for single batch without details
        setBatchEdits([{
          batch_lot: item.batch_lot.split(',')[0].trim(),
          original_quantity: item.quantity_available || 0,
          new_quantity: item.quantity_available || 0,
          adjustment: 0,
          reason: 'Cycle Count',
          unit_cost: item.unit_cost || 0
        }]);
      }

      setRetailPrice(item.retail_price || 0);
      setReorderPoint(item.reorder_point || 10);
      setReorderQuantity(item.reorder_quantity || 50);
      setIsAvailable(item.is_available !== false);
    }
  }, [item]);

  if (!isOpen || !item) return null;

  const toggleBatchExpanded = (batchLot: string) => {
    const newExpanded = new Set(expandedBatches);
    if (newExpanded.has(batchLot)) {
      newExpanded.delete(batchLot);
    } else {
      newExpanded.add(batchLot);
    }
    setExpandedBatches(newExpanded);
  };

  const updateBatchQuantity = (batchLot: string, newQuantity: number) => {
    setBatchEdits(prev => prev.map(batch => {
      if (batch.batch_lot === batchLot) {
        const adjustment = newQuantity - batch.original_quantity;
        return { ...batch, new_quantity: newQuantity, adjustment };
      }
      return batch;
    }));
  };

  const updateBatchReason = (batchLot: string, reason: string) => {
    setBatchEdits(prev => prev.map(batch =>
      batch.batch_lot === batchLot ? { ...batch, reason } : batch
    ));
  };

  const getTotalQuantity = () => {
    return batchEdits.reduce((sum, batch) => sum + batch.new_quantity, 0);
  };

  const getTotalAdjustment = () => {
    return batchEdits.reduce((sum, batch) => sum + batch.adjustment, 0);
  };

  const getWeightedAverageCost = () => {
    const totalValue = batchEdits.reduce((sum, batch) =>
      sum + (batch.new_quantity * batch.unit_cost), 0
    );
    const totalQty = getTotalQuantity();
    return totalQty > 0 ? (totalValue / totalQty).toFixed(2) : '0.00';
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      // Prepare batch adjustments
      const batchAdjustments = batchEdits.filter(batch => batch.adjustment !== 0);

      const payload = {
        sku: item.sku,
        store_id: storeId || item.store_id,
        batch_adjustments: batchAdjustments.map(batch => ({
          batch_lot: batch.batch_lot,
          adjustment: batch.adjustment,
          new_quantity: batch.new_quantity,
          reason: batch.reason
        })),
        retail_price: retailPrice,
        reorder_point: reorderPoint,
        reorder_quantity: reorderQuantity,
        is_available: isAvailable,
        total_quantity: getTotalQuantity()
      };

      const response = await fetch(getApiEndpoint(`/store-inventory/batch-adjust`), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Store-ID': storeId || item.store_id || ''
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to update inventory');
      }

      onSave({
        quantity_available: getTotalQuantity(),
        quantity_on_hand: getTotalQuantity(),
        retail_price: retailPrice,
        reorder_point: reorderPoint,
        reorder_quantity: reorderQuantity,
        is_available: isAvailable
      });
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
        <div
          className="fixed inset-0 transition-opacity bg-gray-500 bg-opacity-75"
          onClick={onClose}
        ></div>

        <div className="inline-block w-full max-w-4xl my-8 overflow-hidden text-left align-middle transition-all transform bg-white shadow-xl rounded-lg">
          <div className="bg-white dark:bg-gray-800 px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                Edit Inventory Item - Batch Level
              </h3>
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-gray-500 focus:outline-none"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="px-6 py-4 max-h-[70vh] overflow-y-auto">
            {error && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md flex items-center gap-2">
                <AlertCircle className="w-5 h-5 text-red-600" />
                <p className="text-sm text-red-800">{error}</p>
              </div>
            )}

            {/* Product Info */}
            <div className="mb-6 p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                    Product
                  </label>
                  <div className="text-sm font-semibold text-gray-900 dark:text-white">
                    {item.product_name || item.name || item.sku}
                  </div>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                    SKU
                  </label>
                  <div className="text-sm font-mono text-gray-900 dark:text-white">
                    {item.sku}
                  </div>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                    Category
                  </label>
                  <div className="text-sm text-gray-900 dark:text-white">
                    {item.category || 'N/A'}
                  </div>
                </div>
              </div>
            </div>

            {/* Batch-Level Editing */}
            <div className="space-y-4 mb-6">
              <h4 className="text-md font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                <Package className="w-5 h-5" />
                Batch Inventory Adjustments
              </h4>

              {batchEdits.length === 0 ? (
                <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-md">
                  <p className="text-sm text-yellow-800">No batch information available</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {batchEdits.map((batch, index) => {
                    const batchDetail = item.batch_details?.find(b => b.batch_lot === batch.batch_lot);
                    const isExpanded = expandedBatches.has(batch.batch_lot);

                    return (
                      <div key={batch.batch_lot} className="border border-gray-200 dark:border-gray-600 rounded-lg overflow-hidden">
                        <div className="p-4 bg-gray-50 dark:bg-gray-700/30">
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="flex items-center gap-4 mb-3">
                                <div className="flex items-center gap-2">
                                  <span className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                                    Batch {index + 1}: {batch.batch_lot}
                                  </span>
                                  {batchDetail && (
                                    <button
                                      type="button"
                                      onClick={() => toggleBatchExpanded(batch.batch_lot)}
                                      className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
                                    >
                                      {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                                    </button>
                                  )}
                                </div>
                                {batch.adjustment !== 0 && (
                                  <span className={`px-2 py-1 text-xs rounded-full ${
                                    batch.adjustment > 0
                                      ? 'bg-green-100 text-green-800'
                                      : 'bg-red-100 text-red-800'
                                  }`}>
                                    {batch.adjustment > 0 ? '+' : ''}{batch.adjustment} units
                                  </span>
                                )}
                              </div>

                              {isExpanded && batchDetail && (
                                <div className="grid grid-cols-3 gap-3 mb-3 text-xs">
                                  <div>
                                    <span className="text-gray-500 dark:text-gray-400">Packaged:</span>
                                    <span className="ml-1 text-gray-700 dark:text-gray-300">
                                      {batchDetail.packaged_on_date ? new Date(batchDetail.packaged_on_date).toLocaleDateString() : 'N/A'}
                                    </span>
                                  </div>
                                  <div>
                                    <span className="text-gray-500 dark:text-gray-400">Supplier:</span>
                                    <span className="ml-1 text-gray-700 dark:text-gray-300">
                                      {batchDetail.supplier_name || 'Unknown'}
                                    </span>
                                  </div>
                                  <div>
                                    <span className="text-gray-500 dark:text-gray-400">PO:</span>
                                    <span className="ml-1 text-gray-700 dark:text-gray-300 font-mono">
                                      {batchDetail.po_number || 'N/A'}
                                    </span>
                                  </div>
                                </div>
                              )}

                              <div className="grid grid-cols-3 gap-4">
                                <div>
                                  <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
                                    Current Quantity
                                  </label>
                                  <div className="text-sm font-semibold text-gray-900 dark:text-white">
                                    {batch.original_quantity} units
                                  </div>
                                </div>

                                <div>
                                  <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
                                    New Quantity
                                  </label>
                                  <input
                                    type="number"
                                    value={batch.new_quantity}
                                    onChange={(e) => updateBatchQuantity(batch.batch_lot, parseInt(e.target.value) || 0)}
                                    className="w-full px-2 py-1 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                                    min="0"
                                  />
                                </div>

                                <div>
                                  <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
                                    Adjustment Reason
                                  </label>
                                  <select
                                    value={batch.reason}
                                    onChange={(e) => updateBatchReason(batch.batch_lot, e.target.value)}
                                    className="w-full px-2 py-1 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                                    disabled={batch.adjustment === 0}
                                  >
                                    {adjustmentReasons.map(reason => (
                                      <option key={reason} value={reason}>{reason}</option>
                                    ))}
                                  </select>
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}

              {/* Summary */}
              <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                <div className="grid grid-cols-4 gap-3 text-sm">
                  <div>
                    <span className="text-gray-600 dark:text-gray-400">Total Current:</span>
                    <span className="ml-2 font-semibold text-gray-900 dark:text-white">
                      {batchEdits.reduce((sum, b) => sum + b.original_quantity, 0)} units
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-600 dark:text-gray-400">Total New:</span>
                    <span className="ml-2 font-semibold text-gray-900 dark:text-white">
                      {getTotalQuantity()} units
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-600 dark:text-gray-400">Total Adjustment:</span>
                    <span className={`ml-2 font-semibold ${
                      getTotalAdjustment() > 0 ? 'text-green-600' : getTotalAdjustment() < 0 ? 'text-red-600' : 'text-gray-900 dark:text-white'
                    }`}>
                      {getTotalAdjustment() > 0 ? '+' : ''}{getTotalAdjustment()} units
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-600 dark:text-gray-400">Avg Cost:</span>
                    <span className="ml-2 font-semibold text-gray-900 dark:text-white">
                      ${getWeightedAverageCost()}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Other Settings */}
            <div className="space-y-4">
              <h4 className="text-md font-semibold text-gray-900 dark:text-white">
                Inventory Settings
              </h4>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Retail Price
                  </label>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">$</span>
                    <input
                      type="number"
                      step="0.01"
                      value={retailPrice}
                      onChange={(e) => setRetailPrice(parseFloat(e.target.value) || 0)}
                      className="w-full pl-7 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                      min="0"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Reorder Point
                  </label>
                  <input
                    type="number"
                    value={reorderPoint}
                    onChange={(e) => setReorderPoint(parseInt(e.target.value) || 0)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                    min="0"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Reorder Quantity
                  </label>
                  <input
                    type="number"
                    value={reorderQuantity}
                    onChange={(e) => setReorderQuantity(parseInt(e.target.value) || 0)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                    min="0"
                  />
                </div>
              </div>

              <div>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={isAvailable}
                    onChange={(e) => setIsAvailable(e.target.checked)}
                    className="mr-2 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Available for Sale
                  </span>
                </label>
              </div>
            </div>

            <div className="mt-6 flex justify-end space-x-3">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                disabled={loading}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                disabled={loading || getTotalAdjustment() === 0}
              >
                {loading ? 'Saving...' : `Apply ${Math.abs(getTotalAdjustment())} Unit Adjustment`}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default InventoryEditModal;