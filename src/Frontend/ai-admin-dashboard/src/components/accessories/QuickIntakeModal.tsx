import React, { useState } from 'react';
import { getApiEndpoint } from '../../config/app.config';
import {
  X, Plus, Package, DollarSign, Hash,
  Upload, Check, AlertCircle
} from 'lucide-react';
import axios from 'axios';

interface QuickIntakeModalProps {
  isOpen: boolean;
  onClose: () => void;
  onComplete: () => void;
  storeId: string;
  categories: Array<{ id: number; name: string; icon: string }>;
  initialData?: any;
}

const QuickIntakeModal: React.FC<QuickIntakeModalProps> = ({
  isOpen,
  onClose,
  onComplete,
  storeId,
  categories,
  initialData
}) => {
  const [formData, setFormData] = useState({
    name: initialData?.name || '',
    brand: initialData?.brand || '',
    sku: initialData?.sku || '',
    barcode: initialData?.barcode || '',
    category_id: initialData?.category_id || '',
    description: initialData?.description || '',
    quantity: 1,
    cost_price: initialData?.cost_price || '',
    retail_price: initialData?.retail_price || '',
    location: '',
    image_url: initialData?.image_url || ''
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [imagePreview, setImagePreview] = useState(initialData?.image_url || '');

  // Handle form field changes
  const handleChange = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  // Handle image upload
  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      // In production, upload to storage service
      // For now, create local preview
      const reader = new FileReader();
      reader.onloadend = () => {
        const base64 = reader.result as string;
        setImagePreview(base64);
        handleChange('image_url', base64);
      };
      reader.readAsDataURL(file);
    }
  };

  // Validate form
  const validateForm = () => {
    if (!formData.name) {
      setError('Product name is required');
      return false;
    }
    if (!formData.sku) {
      // Auto-generate SKU if not provided
      const timestamp = Date.now();
      handleChange('sku', `ACC-${timestamp}`);
    }
    if (!formData.cost_price || !formData.retail_price) {
      setError('Cost and retail prices are required');
      return false;
    }
    if (formData.quantity < 1) {
      setError('Quantity must be at least 1');
      return false;
    }
    return true;
  };

  // Handle form submission
  const handleSubmit = async () => {
    if (!validateForm()) return;

    setLoading(true);
    setError('');

    try {
      // First, add to catalog if needed
      const catalogResponse = await axios.post(
        getApiEndpoint('/accessories/catalog'),
        {
          barcode: formData.barcode || null,
          sku: formData.sku || `ACC-${Date.now()}`,
          name: formData.name,
          brand: formData.brand || null,
          category_id: formData.category_id || null,
          description: formData.description || null,
          image_url: formData.image_url || null,
          msrp: parseFloat(formData.retail_price)
        }
      );

      const accessoryId = catalogResponse.data.id;

      // Then add to inventory
      await axios.post(
        getApiEndpoint('/accessories/inventory/intake'),
        {
          store_id: storeId,
          barcode: formData.barcode,
          name: formData.name,
          brand: formData.brand,
          category_id: formData.category_id,
          quantity: formData.quantity,
          cost_price: parseFloat(formData.cost_price),
          retail_price: parseFloat(formData.retail_price),
          location: formData.location,
          image_url: formData.image_url,
          description: formData.description,
          auto_create_catalog: false // Already created above
        }
      );

      onComplete();
    } catch (error: any) {
      console.error('Intake error:', error);
      setError(error.response?.data?.detail || 'Failed to add item to inventory');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  const margin = formData.cost_price && formData.retail_price
    ? ((parseFloat(formData.retail_price) - parseFloat(formData.cost_price)) / parseFloat(formData.retail_price) * 100).toFixed(1)
    : 0;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black dark:bg-black bg-opacity-50 dark:bg-opacity-70 transition-colors duration-200">
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 w-full max-w-3xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-4">
            <Plus className="w-6 h-6 text-primary-600 dark:text-primary-500" />
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Quick Add Accessory</h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg text-gray-900 dark:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Error Message */}
          {error && (
            <div className="flex items-center gap-2 p-4 bg-danger-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 rounded-lg transition-colors">
              <AlertCircle className="w-5 h-5" />
              <span>{error}</span>
            </div>
          )}

          {/* Image Upload */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Product Image
            </label>
            <div className="flex items-center gap-6">
              {imagePreview ? (
                <img
                  src={imagePreview}
                  alt="Product"
                  className="w-24 h-24 object-cover rounded-lg border"
                />
              ) : (
                <div className="w-24 h-24 bg-gray-50 dark:bg-gray-700 rounded-lg border-2 border-dashed border-gray-200 dark:border-gray-600 flex items-center justify-center transition-colors">
                  <Package className="w-8 h-8 text-gray-400" />
                </div>
              )}
              <div className="flex-1">
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleImageUpload}
                  className="hidden"
                  id="image-upload"
                />
                <label
                  htmlFor="image-upload"
                  className="inline-flex items-center gap-2 px-4 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white hover:bg-gray-50 dark:hover:bg-gray-600 cursor-pointer transition-colors"
                >
                  <Upload className="w-4 h-4" />
                  Upload Image
                </label>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Or paste image URL below
                </p>
              </div>
            </div>
            <input
              type="text"
              value={formData.image_url}
              onChange={(e) => {
                handleChange('image_url', e.target.value);
                setImagePreview(e.target.value);
              }}
              placeholder="https://example.com/image.jpg"
              className="mt-2 w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 text-sm transition-colors"
            />
          </div>

          {/* Product Details */}
          <div className="grid grid-cols-2 gap-6">
            <div className="col-span-2">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Product Name *
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => handleChange('name', e.target.value)}
                placeholder="e.g., RAW Classic Rolling Papers"
                className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 transition-colors"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Brand
              </label>
              <input
                type="text"
                value={formData.brand}
                onChange={(e) => handleChange('brand', e.target.value)}
                placeholder="e.g., RAW"
                className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 transition-colors"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Category
              </label>
              <select
                value={formData.category_id}
                onChange={(e) => handleChange('category_id', e.target.value ? Number(e.target.value) : null)}
                className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 transition-colors"
              >
                <option value="">Select Category</option>
                {categories.map(cat => (
                  <option key={cat.id} value={cat.id}>
                    {cat.icon} {cat.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                SKU
              </label>
              <div className="relative">
                <Hash className="absolute left-3 top-2.5 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  value={formData.sku}
                  onChange={(e) => handleChange('sku', e.target.value)}
                  placeholder="Auto-generated"
                  className="w-full pl-9 pr-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 transition-colors"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Barcode
              </label>
              <input
                type="text"
                value={formData.barcode}
                onChange={(e) => handleChange('barcode', e.target.value)}
                placeholder="Optional"
                className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 transition-colors"
              />
            </div>

            <div className="col-span-2">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Description
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => handleChange('description', e.target.value)}
                rows={2}
                placeholder="Optional product description..."
                className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 transition-colors"
              />
            </div>
          </div>

          {/* Inventory Details */}
          <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
            <h3 className="font-medium mb-3 text-gray-900 dark:text-white">Inventory Details</h3>
            <div className="grid grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Quantity *
                </label>
                <input
                  type="number"
                  value={formData.quantity}
                  onChange={(e) => handleChange('quantity', parseInt(e.target.value) || 0)}
                  min="1"
                  className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 transition-colors"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Location
                </label>
                <input
                  type="text"
                  value={formData.location}
                  onChange={(e) => handleChange('location', e.target.value)}
                  placeholder="e.g., Shelf A1"
                  className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 transition-colors"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Cost Price *
                </label>
                <div className="relative">
                  <DollarSign className="absolute left-3 top-2.5 w-4 h-4 text-gray-400" />
                  <input
                    type="number"
                    value={formData.cost_price}
                    onChange={(e) => handleChange('cost_price', e.target.value)}
                    step="0.01"
                    placeholder="0.00"
                    className="w-full pl-9 pr-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 transition-colors"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Retail Price *
                </label>
                <div className="relative">
                  <DollarSign className="absolute left-3 top-2.5 w-4 h-4 text-gray-400" />
                  <input
                    type="number"
                    value={formData.retail_price}
                    onChange={(e) => handleChange('retail_price', e.target.value)}
                    step="0.01"
                    placeholder="0.00"
                    className="w-full pl-9 pr-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 transition-colors"
                  />
                </div>
              </div>
            </div>

            {/* Margin Calculation */}
            {formData.cost_price && formData.retail_price && (
              <div className="mt-4 p-4 bg-primary-50 dark:bg-primary-900/30 rounded-lg transition-colors">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600 dark:text-gray-300">Profit Margin:</span>
                  <span className="font-medium text-primary-700 dark:text-primary-400">{margin}%</span>
                </div>
                <div className="flex items-center justify-between text-sm mt-1">
                  <span className="text-gray-600 dark:text-gray-300">Total Inventory Value:</span>
                  <span className="font-medium text-gray-900 dark:text-white">
                    ${(formData.quantity * parseFloat(formData.retail_price)).toFixed(2)}
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-4 p-6 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700 transition-colors">
          <button
            onClick={onClose}
            className="px-4 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-600 text-gray-900 dark:text-white hover:bg-gray-50 dark:hover:bg-gray-500 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={loading || !formData.name || !formData.cost_price || !formData.retail_price}
            className="px-4 py-2 bg-primary-600 dark:bg-primary-500 text-white rounded-lg hover:bg-primary-700 dark:hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 transition-colors"
          >
            {loading ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Adding...
              </>
            ) : (
              <>
                <Check className="w-4 h-4" />
                Add to Inventory
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default QuickIntakeModal;