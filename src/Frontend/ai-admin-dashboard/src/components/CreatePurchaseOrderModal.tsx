import React, { useState, useEffect } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { X, Plus, Trash2, Package, DollarSign } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useStoreContext } from '../contexts/StoreContext';
import { getApiEndpoint } from '../config/app.config';
import StoreSelector from './StoreSelector';
import toast from 'react-hot-toast';

interface POItem {
  sku: string;
  product_name?: string;
  quantity: number;
  unit_cost: number;
  received_quantity?: number;
  retail_price?: number;
  batch_lot?: string;
  case_gtin?: string;
  packaged_on_date?: string;
  gtin_barcode?: string;
  each_gtin?: string;
}

interface CreatePurchaseOrderModalProps {
  isOpen: boolean;
  onClose: () => void;
  suppliers: any[];
  products?: any[];
}

const CreatePurchaseOrderModal: React.FC<CreatePurchaseOrderModalProps> = ({
  isOpen,
  onClose,
  suppliers
}) => {
  const { t } = useTranslation(['common']);
  const queryClient = useQueryClient();
  const { currentStore } = useStoreContext();

  // Form state
  const [supplierId, setSupplierId] = useState('');
  const [expectedDate, setExpectedDate] = useState('');
  const [notes, setNotes] = useState('');
  const [items, setItems] = useState<POItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  
  // Auto-select provincial supplier based on store's province
  useEffect(() => {
    const fetchProvincialSupplier = async () => {
      if (isOpen && currentStore) {
        // Check if store has province_territory_id
        if (currentStore.province_territory_id) {
          try {
            // Fetch the provincial supplier for the store's province/territory ID
            const response = await fetch(getApiEndpoint(`/suppliers/by-province-territory-id/${currentStore.province_territory_id}`), {
              method: 'GET',
              headers: {
                'Content-Type': 'application/json',
              },
            });

            if (response.ok) {
              const provincialSupplier = await response.json();
              setSupplierId(provincialSupplier.id);
              console.log(`Auto-selected provincial supplier by territory ID:`, provincialSupplier.name);
              return; // Exit if we found the supplier
            }
          } catch (error) {
            console.error('Error fetching provincial supplier by territory ID:', error);
          }
        }

        // Fallback to province_code if province_territory_id is not available
        if (currentStore.province_code) {
          try {
            const response = await fetch(getApiEndpoint(`/suppliers/by-province/${currentStore.province_code}`), {
              method: 'GET',
              headers: {
                'Content-Type': 'application/json',
              },
            });

            if (response.ok) {
              const provincialSupplier = await response.json();
              setSupplierId(provincialSupplier.id);
              console.log(`Auto-selected provincial supplier by province code:`, provincialSupplier.name);
              return;
            }
          } catch (error) {
            console.error('Error fetching provincial supplier by province code:', error);
          }
        }

        // Fallback to finding supplier in the suppliers list
        if (suppliers?.length > 0) {
          // First try to match by provinces_territories_id
          if (currentStore.province_territory_id) {
            const provincialSupplier = suppliers.find((s: any) =>
              s.provinces_territories_id === currentStore.province_territory_id
            );
            if (provincialSupplier) {
              setSupplierId(provincialSupplier.id);
              console.log('Found provincial supplier in list by territory ID:', provincialSupplier.name);
              return;
            }
          }

          // Then try to match by province_code
          if (currentStore.province_code) {
            const provincialSupplier = suppliers.find((s: any) =>
              s.province_code === currentStore.province_code
            );
            if (provincialSupplier) {
              setSupplierId(provincialSupplier.id);
              console.log('Found provincial supplier in list by province code:', provincialSupplier.name);
              return;
            }
          }

          // Default to first supplier if no match found
          setSupplierId(suppliers[0].id);
          console.log('Using default supplier:', suppliers[0].name);
        }
      } else if (isOpen && suppliers?.length > 0 && !currentStore) {
        // If no store selected, use first supplier
        setSupplierId(suppliers[0].id);
        console.log('No store selected, using first supplier');
      }
    };

    if (isOpen) {
      fetchProvincialSupplier();

      // Set today's date as default
      const today = new Date().toISOString().split('T')[0];
      setExpectedDate(today);

      // Add one empty item by default
      if (items.length === 0) {
        setItems([{
          sku: '',
          quantity: 1,
          unit_cost: 0,
          received_quantity: 0,
          retail_price: 0
        }]);
      }
    }
  }, [isOpen, currentStore, suppliers]);
  
  const addItem = () => {
    setItems([...items, {
      sku: '',
      quantity: 1,
      unit_cost: 0,
      received_quantity: 0,
      retail_price: 0
    }]);
  };
  
  const removeItem = (index: number) => {
    setItems(items.filter((_, i) => i !== index));
  };
  
  const updateItem = (index: number, field: keyof POItem, value: any) => {
    const updatedItems = [...items];
    updatedItems[index] = {
      ...updatedItems[index],
      [field]: value
    };
    setItems(updatedItems);
  };
  
  const createPOMutation = useMutation({
    mutationFn: async () => {
      // Prepare items with all fields including received_quantity and retail_price
      const poItems = items.map(item => ({
        sku: item.sku,
        quantity: item.quantity,
        unit_cost: item.unit_cost,
        batch_lot: item.batch_lot,
        case_gtin: item.case_gtin,
        packaged_on_date: item.packaged_on_date,
        gtin_barcode: item.gtin_barcode,
        each_gtin: item.each_gtin,
        // Store received_quantity and retail_price in notes or custom fields
        // These will be used when marking as received
        quantity_received: item.received_quantity,
        retail_price: item.retail_price
      }));
      
      const purchaseOrder = {
        supplier_id: supplierId,
        store_id: currentStore?.id,  // Include store_id from context
        items: poItems,
        expected_date: expectedDate || null,
        notes: notes,
        // Include received quantities and retail prices in metadata
        metadata: {
          items_metadata: items.map(item => ({
            sku: item.sku,
            received_quantity: item.received_quantity,
            retail_price: item.retail_price
          }))
        }
      };
      
      const response = await fetch(getApiEndpoint('/inventory/purchase-orders'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Store-ID': currentStore?.id || '',  // Ensure store ID is in header
        },
        body: JSON.stringify(purchaseOrder),
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to create purchase order');
      }
      
      return response.json();
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['purchase-orders'] });
      toast.success(`Purchase Order created successfully!`);
      handleClose();
    },
    onError: (error: Error) => {
      setError(error.message);
    },
  });
  
  const handleSubmit = () => {
    // Validate
    if (!currentStore) {
      setError(t('common:errors.validation.selectStore'));
      return;
    }

    if (!supplierId) {
      setError(t('common:errors.validation.selectSupplier'));
      return;
    }

    if (items.length === 0) {
      setError(t('common:errors.validation.addAtLeastOneItem'));
      return;
    }

    const invalidItems = items.filter(item => !item.sku || item.quantity <= 0 || item.unit_cost <= 0);
    if (invalidItems.length > 0) {
      setError(t('common:errors.validation.fillRequiredFields'));
      return;
    }

    setError(null);
    createPOMutation.mutate();
  };
  
  const handleClose = () => {
    setSupplierId('');
    setExpectedDate('');
    setNotes('');
    setItems([]);
    setError(null);
    onClose();
  };
  
  const calculateTotal = () => {
    return items.reduce((sum, item) => sum + (item.quantity * item.unit_cost), 0);
  };
  
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-6 z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg max-w-6xl w-full max-h-[90vh] overflow-hidden">
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-xl font-bold flex items-center gap-2 text-gray-900 dark:text-white">
            <Package className="h-6 w-6 text-primary-600 dark:text-primary-400" />
            Create Purchase Order
          </h2>
          <button onClick={handleClose} className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300">
            <X className="h-6 w-6" />
          </button>
        </div>
        
        <div className="p-6 overflow-y-auto" style={{ maxHeight: 'calc(90vh - 200px)' }}>
          {error && (
            <div className="mb-4 p-6 bg-danger-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
              <span className="text-red-700 dark:text-red-400">{error}</span>
            </div>
          )}

          {/* Store Selector */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Store *
            </label>
            <StoreSelector className="w-full" showStats={false} />
            {!currentStore && (
              <p className="mt-1 text-sm text-danger-600 dark:text-danger-400">Please select a store</p>
            )}
          </div>
          
          <div className="grid grid-cols-3 gap-6 mb-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Supplier *
              </label>
              <select
                value={supplierId}
                onChange={(e) => setSupplierId(e.target.value)}
                className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value="">Select Supplier</option>
                {suppliers?.map((supplier: any) => (
                  <option key={supplier.id} value={supplier.id}>
                    {supplier.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Expected Date *
              </label>
              <input
                type="date"
                value={expectedDate}
                onChange={(e) => setExpectedDate(e.target.value)}
                className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Notes
              </label>
              <input
                type="text"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white dark:placeholder-gray-400"
                placeholder="Optional notes..."
              />
            </div>
          </div>
          
          <div className="mb-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white">Order Items</h3>
              <button
                onClick={addItem}
                className="bg-primary-600 dark:bg-primary-700 text-white px-4 py-2 rounded-lg hover:bg-primary-700 dark:hover:bg-primary-600 flex items-center gap-2"
              >
                <Plus className="h-4 w-4" />
                Add Item
              </button>
            </div>

            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead className="bg-gray-50 dark:bg-gray-700">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">SKU</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Batch Lot</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Order Qty</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Received Qty</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Unit Cost</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Retail Price</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Total</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Actions</th>
                  </tr>
                </thead>
                <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                  {items.map((item, index) => (
                    <tr key={index}>
                      <td className="px-4 py-3">
                        <input
                          type="text"
                          value={item.sku}
                          onChange={(e) => updateItem(index, 'sku', e.target.value)}
                          className="w-full px-2 py-1 border border-gray-200 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white dark:placeholder-gray-400"
                          placeholder="Enter SKU"
                        />
                      </td>
                      <td className="px-4 py-3">
                        <input
                          type="text"
                          value={item.batch_lot || ''}
                          onChange={(e) => updateItem(index, 'batch_lot', e.target.value)}
                          className="w-full px-2 py-1 border border-gray-200 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white dark:placeholder-gray-400"
                          placeholder="Optional"
                        />
                      </td>
                      <td className="px-4 py-3">
                        <input
                          type="number"
                          value={item.quantity}
                          onChange={(e) => updateItem(index, 'quantity', parseInt(e.target.value) || 0)}
                          className="w-20 px-2 py-1 border border-gray-200 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                          min="1"
                        />
                      </td>
                      <td className="px-4 py-3">
                        <input
                          type="number"
                          value={item.received_quantity || 0}
                          onChange={(e) => updateItem(index, 'received_quantity', parseInt(e.target.value) || 0)}
                          className="w-20 px-2 py-1 border border-gray-200 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                          min="0"
                        />
                      </td>
                      <td className="px-4 py-3">
                        <input
                          type="number"
                          value={item.unit_cost}
                          onChange={(e) => updateItem(index, 'unit_cost', parseFloat(e.target.value) || 0)}
                          className="w-24 px-2 py-1 border border-gray-200 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                          min="0"
                          step="0.01"
                        />
                      </td>
                      <td className="px-4 py-3">
                        <input
                          type="number"
                          value={item.retail_price || 0}
                          onChange={(e) => updateItem(index, 'retail_price', parseFloat(e.target.value) || 0)}
                          className="w-24 px-2 py-1 border border-gray-200 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                          min="0"
                          step="0.01"
                        />
                      </td>
                      <td className="px-4 py-3 font-medium text-gray-900 dark:text-white">
                        ${(item.quantity * item.unit_cost).toFixed(2)}
                      </td>
                      <td className="px-4 py-3">
                        <button
                          onClick={() => removeItem(index)}
                          className="text-danger-600 dark:text-danger-400 hover:text-danger-800 dark:hover:text-danger-300"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          
          <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-6">
            <div className="flex justify-between items-center">
              <div className="text-sm text-gray-600 dark:text-gray-300">
                <span>Total Items: {items.length}</span>
                <span className="ml-4">Total Quantity: {items.reduce((sum, item) => sum + item.quantity, 0)}</span>
              </div>
              <div className="flex items-center gap-2">
                <DollarSign className="h-5 w-5 text-gray-600 dark:text-gray-400" />
                <span className="text-xl font-bold text-gray-900 dark:text-white">Total: ${calculateTotal().toFixed(2)}</span>
              </div>
            </div>
          </div>
        </div>

        <div className="flex justify-between p-6 border-t border-gray-200 dark:border-gray-700">
          <button
            onClick={handleClose}
            className="px-4 py-2 border border-gray-200 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={createPOMutation.isPending}
            className="bg-primary-600 dark:bg-primary-700 text-white px-6 py-2 rounded-lg hover:bg-primary-700 dark:hover:bg-primary-600 disabled:opacity-50"
          >
            {createPOMutation.isPending ? 'Creating...' : 'Create Purchase Order'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default CreatePurchaseOrderModal;