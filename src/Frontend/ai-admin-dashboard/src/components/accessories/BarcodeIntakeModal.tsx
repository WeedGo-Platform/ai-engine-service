import React, { useState, useEffect, useRef, useMemo } from 'react';
import { getApiEndpoint } from '../../config/app.config';
import {
  X, Scan, Loader2, Check, AlertCircle,
  Search, Package, DollarSign
} from 'lucide-react';
import axios from 'axios';
import { getSubcategoriesForCategory, getCategorySlug } from '../../constants/subcategories';
import { formatCurrency, formatCurrencyInput, parseCurrencyInput } from '../../utils/currency';

interface BarcodeIntakeModalProps {
  isOpen: boolean;
  onClose: () => void;
  onComplete: (data: any) => void;
  storeId: string;
  categories: Array<{ id: number; name: string; slug: string; icon: string }>;
}

const BarcodeIntakeModal: React.FC<BarcodeIntakeModalProps> = ({
  isOpen,
  onClose,
  onComplete,
  storeId,
  categories
}) => {
  const [barcode, setBarcode] = useState('');
  const [scanning, setScanning] = useState(false);
  const [scanResult, setScanResult] = useState<any>(null);
  const [error, setError] = useState('');
  const [manualEntry, setManualEntry] = useState(false);
  
  // Intake form fields
  const [quantity, setQuantity] = useState(1);
  const [costPrice, setCostPrice] = useState('');
  const [retailPrice, setRetailPrice] = useState('');
  const [location, setLocation] = useState('');
  const [categoryId, setCategoryId] = useState('');
  const [subcategory, setSubcategory] = useState('');

  // Get available subcategories based on selected category
  const availableSubcategories = useMemo(() => {
    if (!categoryId) return [];
    const slug = getCategorySlug(categoryId, categories);
    return getSubcategoriesForCategory(slug);
  }, [categoryId, categories]);
  
  const barcodeInputRef = useRef<HTMLInputElement>(null);

  // Format currency input as user types (last 2 digits = cents)
  const handleCurrencyInput = (value: string, setter: (val: string) => void) => {
    // Remove all non-numeric characters
    const numericValue = value.replace(/\D/g, '');
    
    if (numericValue === '') {
      setter('');
      return;
    }
    
    // Convert to cents then to dollars
    const cents = parseInt(numericValue, 10);
    const dollars = (cents / 100).toFixed(2);
    setter(dollars);
  };

  useEffect(() => {
    if (isOpen && barcodeInputRef.current) {
      barcodeInputRef.current.focus();
    }
  }, [isOpen]);

  // Handle barcode scan
  const handleScan = async () => {
    if (!barcode) {
      setError('Please enter a barcode');
      return;
    }

    setScanning(true);
    setError('');
    setScanResult(null);

    try {
      const response = await axios.post(getApiEndpoint('/accessories/barcode/scan'), {
        barcode,
        store_id: storeId,
        scan_type: 'intake'
      });

      setScanResult(response.data);
      
      // Pre-fill prices if found
      if (response.data.data) {
        if (response.data.data.price) {
          setRetailPrice(response.data.data.price.toString());
        }
        if (response.data.data.msrp) {
          setCostPrice(formatCurrencyInput(response.data.data.msrp * 0.5)); // Assume 50% margin
        }
      }

      if (response.data.requires_manual_entry) {
        setManualEntry(true);
      }
    } catch (error) {
      console.error('Scan error:', error);
      setError('Failed to scan barcode. Please try again.');
    } finally {
      setScanning(false);
    }
  };

  // Handle intake submission
  const handleIntake = async () => {
    if (!scanResult || !costPrice || !retailPrice || quantity < 1) {
      setError('Please fill in all required fields');
      return;
    }

    try {
      const intakeData = {
        barcode,
        store_id: storeId,
        name: scanResult.data?.name || 'Unknown Product',
        brand: scanResult.data?.brand,
        category_id: categoryId || scanResult.data?.category_id,
        subcategory: subcategory || null,
        quantity,
        cost_price: parseFloat(costPrice),
        retail_price: parseFloat(retailPrice),
        image_url: scanResult.data?.image_url,
        description: scanResult.data?.description,
        location,
        auto_create_catalog: true
      };

      const response = await axios.post(
        getApiEndpoint('/accessories/inventory/intake'),
        intakeData
      );

      if (response.data.success) {
        onComplete(response.data);
        handleReset();
      }
    } catch (error) {
      console.error('Intake error:', error);
      setError('Failed to add item to inventory');
    }
  };

  // Reset form
  const handleReset = () => {
    setBarcode('');
    setScanResult(null);
    setQuantity(1);
    setCostPrice('');
    setRetailPrice('');
    setLocation('');
    setCategoryId('');
    setSubcategory('');
    setError('');
    setManualEntry(false);
  };

  // Handle enter key for quick scanning
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !scanning) {
      handleScan();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black dark:bg-black bg-opacity-50 dark:bg-opacity-70 p-0 sm:p-4 transition-colors duration-200">
      <div className="bg-white dark:bg-gray-800 h-full sm:h-auto sm:rounded-lg border-0 sm:border border-gray-200 dark:border-gray-700 w-full sm:max-w-2xl max-h-full sm:max-h-[90vh] overflow-y-auto flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 sm:p-6 border-b border-gray-200 dark:border-gray-700 flex-shrink-0 sticky top-0 bg-white dark:bg-gray-800 z-10">
          <div className="flex items-center gap-3 sm:gap-4">
            <Scan className="w-5 h-5 sm:w-6 sm:h-6 text-accent-600 dark:text-accent-500" />
            <h2 className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-white">Barcode Intake</h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 -mr-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg text-gray-900 dark:text-white transition-colors"
            aria-label="Close barcode intake"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-4 sm:p-6 space-y-4 sm:space-y-6 flex-1 overflow-y-auto">
          {/* Barcode Input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Scan or Enter Barcode
            </label>
            <div className="flex gap-2">
              <input
                ref={barcodeInputRef}
                type="text"
                value={barcode}
                onChange={(e) => setBarcode(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Scan barcode or enter manually..."
                className="flex-1 px-4 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 transition-colors"
                disabled={scanning}
              />
              <button
                onClick={handleScan}
                disabled={scanning || !barcode}
                className="px-4 py-2 bg-accent-600 dark:bg-accent-500 text-white rounded-lg hover:bg-accent-700 dark:hover:bg-accent-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 transition-colors"
              >
                {scanning ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Scanning...
                  </>
                ) : (
                  <>
                    <Search className="w-4 h-4" />
                    Lookup
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="flex items-center gap-2 p-4 bg-danger-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 rounded-lg transition-colors">
              <AlertCircle className="w-5 h-5" />
              <span>{error}</span>
            </div>
          )}

          {/* Scan Result */}
          {scanResult && (
            <div className="space-y-4 sm:space-y-6">
              {/* Product Info */}
              <div className="p-4 sm:p-6 bg-gray-50 dark:bg-gray-700 rounded-lg transition-colors">
                <div className="flex flex-col sm:flex-row items-start gap-4 sm:gap-6">
                  {scanResult.data?.image_url ? (
                    <img
                      src={scanResult.data.image_url}
                      alt={scanResult.data.name}
                      className="w-full sm:w-20 h-32 sm:h-20 object-cover rounded"
                    />
                  ) : (
                    <div className="w-full sm:w-20 h-32 sm:h-20 bg-gray-100 dark:bg-gray-600 rounded flex items-center justify-center transition-colors">
                      <Package className="w-12 h-12 sm:w-8 sm:h-8 text-gray-400" />
                    </div>
                  )}

                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold text-base sm:text-lg text-gray-900 dark:text-white">
                      {scanResult.data?.name || 'Unknown Product'}
                    </h3>
                    {scanResult.data?.brand && (
                      <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-300">Brand: {scanResult.data.brand}</p>
                    )}
                    {scanResult.data?.description && (
                      <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400 mt-1 line-clamp-2">{scanResult.data.description}</p>
                    )}

                    <div className="flex flex-wrap items-center gap-2 sm:gap-4 mt-2">
                      <span className={`text-xs px-2 py-1 rounded ${
                        scanResult.confidence > 0.7 ? 'bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-400' :
                        scanResult.confidence > 0.4 ? 'bg-warning-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400' :
                        'bg-danger-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'
                      }`}>
                        Confidence: {(scanResult.confidence * 100).toFixed(0)}%
                      </span>
                      <span className="text-xs px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-accent-700 dark:text-blue-400 rounded">
                        Source: {scanResult.source}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Intake Form */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Quantity *
                  </label>
                  <input
                    type="number"
                    value={quantity}
                    onChange={(e) => setQuantity(parseInt(e.target.value) || 0)}
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
                    value={location}
                    onChange={(e) => setLocation(e.target.value)}
                    placeholder="e.g., Shelf A1"
                    className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 transition-colors"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Category
                  </label>
                  <select
                    value={categoryId}
                    onChange={(e) => { setCategoryId(e.target.value); setSubcategory(''); }}
                    className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 transition-colors"
                  >
                    <option value="">Select category</option>
                    {categories.map(cat => (
                      <option key={cat.id} value={cat.id}>
                        {cat.icon} {cat.name}
                      </option>
                    ))}
                  </select>
                </div>

                {categoryId && availableSubcategories.length > 0 && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Subcategory
                    </label>
                    <select
                      value={subcategory}
                      onChange={(e) => setSubcategory(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 transition-colors"
                    >
                      <option value="">Select subcategory (optional)</option>
                      {availableSubcategories.map(subcat => (
                        <option key={subcat} value={subcat}>
                          {subcat}
                        </option>
                      ))}
                    </select>
                  </div>
                )}

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Cost Price *
                  </label>
                  <div className="relative">
                    <DollarSign className="absolute left-3 top-2.5 w-4 h-4 text-gray-400" />
                    <input
                      type="text"
                      value={costPrice}
                      onChange={(e) => handleCurrencyInput(e.target.value, setCostPrice)}
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
                      type="text"
                      value={retailPrice}
                      onChange={(e) => handleCurrencyInput(e.target.value, setRetailPrice)}
                      placeholder="0.00"
                      className="w-full pl-9 pr-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 transition-colors"
                    />
                  </div>
                </div>
              </div>

              {/* Margin Calculation */}
              {costPrice && retailPrice && (
                <div className="p-4 bg-primary-50 dark:bg-primary-900/30 rounded-lg transition-colors">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600 dark:text-gray-300">Margin:</span>
                    <span className="font-medium text-primary-700 dark:text-primary-400">
                      {formatCurrency(parseFloat(retailPrice) - parseFloat(costPrice))} 
                      ({((parseFloat(retailPrice) - parseFloat(costPrice)) / parseFloat(retailPrice) * 100).toFixed(1)}%)
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-sm mt-1">
                    <span className="text-gray-600 dark:text-gray-300">Total Value:</span>
                    <span className="font-medium text-gray-900 dark:text-white">
                      {formatCurrency(quantity * parseFloat(retailPrice))}
                    </span>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Manual Entry Notice */}
          {manualEntry && (
            <div className="p-4 bg-warning-50 dark:bg-yellow-900/30 text-warning-800 dark:text-yellow-400 rounded-lg transition-colors">
              <p className="text-sm">
                Product not found in database. It will be added to the catalog when you complete the intake.
              </p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex flex-col-reverse sm:flex-row justify-between items-stretch sm:items-center gap-2 sm:gap-0 p-4 sm:p-6 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700 transition-colors flex-shrink-0 sticky bottom-0">
          <button
            onClick={handleReset}
            className="w-full sm:w-auto px-4 py-2.5 sm:py-2 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg sm:hover:bg-transparent transition-colors font-medium active:scale-95 touch-manipulation"
          >
            Reset
          </button>


          <div className="flex flex-col sm:flex-row gap-2 sm:gap-4 w-full sm:w-auto">
            <button
              onClick={onClose}
              className="w-full sm:w-auto px-4 py-2.5 sm:py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-600 text-gray-900 dark:text-white hover:bg-gray-50 dark:hover:bg-gray-500 transition-colors font-medium active:scale-95 touch-manipulation"
            >
              Cancel
            </button>
            <button
              onClick={handleIntake}
              disabled={!scanResult || !costPrice || !retailPrice}
              className="w-full sm:w-auto px-4 py-2.5 sm:py-2 bg-primary-600 dark:bg-primary-500 text-white rounded-lg hover:bg-primary-700 dark:hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 transition-colors font-semibold active:scale-95 touch-manipulation"
            >
              <Check className="w-4 h-4" />
              Add to Inventory
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BarcodeIntakeModal;