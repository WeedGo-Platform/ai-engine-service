import React, { useState, useEffect, useCallback } from 'react';
import {
  Package, Scan, Plus, Search, Filter, AlertTriangle,
  Download, Upload, Edit2, Trash2, Eye, BarChart3,
  DollarSign, TrendingUp, ShoppingCart, Camera,
  RefreshCw, Check, X, Loader2, Info, Box, Tag
} from 'lucide-react';
import axios from 'axios';
import BarcodeIntakeModal from '../components/accessories/BarcodeIntakeModal';
import { getApiEndpoint } from '../config/app.config';
import QuickIntakeModal from '../components/accessories/QuickIntakeModal';
import InventoryAdjustModal from '../components/accessories/InventoryAdjustModal';
import OCRScanModal from '../components/accessories/OCRScanModal';
import CategoryManagementModal from '../components/accessories/CategoryManagementModal';
import { useStoreContext } from '../contexts/StoreContext';
import { formatCurrency } from '../utils/currency';

interface Accessory {
  id: number;
  accessory_id: number;
  name: string;
  brand: string;
  sku: string;
  barcode: string;
  category: string;
  quantity: number;
  available: number;
  reserved: number;
  cost_price: number;
  retail_price: number;
  sale_price?: number;
  min_stock: number;
  status: string;
  location?: string;
  image_url?: string;
}

interface Category {
  id: number;
  name: string;
  slug: string;
  icon: string;
}

const Accessories: React.FC = () => {
  const { currentStore } = useStoreContext();
  const [accessories, setAccessories] = useState<Accessory[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState<number | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [showLowStockOnly, setShowLowStockOnly] = useState(false);
  const [selectedAccessory, setSelectedAccessory] = useState<Accessory | null>(null);

  // Modals
  const [showBarcodeIntake, setShowBarcodeIntake] = useState(false);
  const [showOCRScan, setShowOCRScan] = useState(false);
  const [showQuickIntake, setShowQuickIntake] = useState(false);
  const [showAdjustModal, setShowAdjustModal] = useState(false);
  const [showCategoryManagement, setShowCategoryManagement] = useState(false);

  // Stats
  const [inventoryStats, setInventoryStats] = useState({
    total_items: 0,
    total_units: 0,
    total_value: 0,
    low_stock_count: 0
  });

  const storeId = currentStore?.id;

  // Fetch accessories inventory
  const fetchAccessories = useCallback(async () => {
    // Don't fetch if no store is selected
    if (!storeId) {
      setLoading(false);
      setAccessories([]);
      return;
    }

    try {
      setLoading(true);
      const params: any = { store_id: storeId };

      if (selectedCategory) {
        params.category_id = selectedCategory;
      }
      if (showLowStockOnly) {
        params.low_stock_only = true;
      }

      const response = await axios.get(
        getApiEndpoint(`/accessories/inventory/${storeId}`),
        { params }
      );

      setAccessories(response.data.inventory || []);

      // Calculate stats
      const stats = {
        total_items: response.data.inventory.length,
        total_units: response.data.inventory.reduce((sum: number, item: Accessory) => sum + item.quantity, 0),
        total_value: response.data.inventory.reduce((sum: number, item: Accessory) =>
          sum + (item.quantity * item.retail_price), 0),
        low_stock_count: response.data.inventory.filter((item: Accessory) =>
          item.quantity <= item.min_stock).length
      };
      setInventoryStats(stats);

    } catch (error) {
      console.error('Error fetching accessories:', error);
    } finally {
      setLoading(false);
    }
  }, [storeId, selectedCategory, showLowStockOnly]);

  // Fetch categories
  const fetchCategories = async () => {
    try {
      const response = await axios.get(getApiEndpoint(`/accessories/categories`));
      setCategories(response.data);
    } catch (error) {
      console.error('Error fetching categories:', error);
    }
  };

  useEffect(() => {
    fetchCategories();
    fetchAccessories();
  }, [fetchAccessories]);

  // Filter accessories by search
  const filteredAccessories = accessories.filter(item =>
    item.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    item.sku.toLowerCase().includes(searchTerm.toLowerCase()) ||
    item.barcode?.includes(searchTerm) ||
    item.brand?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Handle barcode scan complete
  const handleBarcodeScanned = (data: any) => {
    setShowBarcodeIntake(false);
    if (data.requires_manual_entry) {
      setShowQuickIntake(true);
    } else {
      fetchAccessories();
    }
  };

  // Handle OCR scan complete
  const handleOCRScanned = (extractedData: any) => {
    setShowOCRScan(false);
    // Pre-populate QuickIntake modal with OCR-extracted data
    // For now, just refresh inventory
    fetchAccessories();
  };

  // Handle inventory adjustment
  const handleAdjustInventory = async (adjustment: any) => {
    try {
      await axios.post(getApiEndpoint(`/accessories/inventory/adjust`), {
        ...adjustment,
        store_id: storeId
      });
      fetchAccessories();
      setShowAdjustModal(false);
    } catch (error) {
      console.error('Error adjusting inventory:', error);
    }
  };

  // Export inventory
  const exportInventory = () => {
    const csv = [
      ['SKU', 'Name', 'Brand', 'Category', 'Quantity', 'Cost', 'Retail', 'Value'].join(','),
      ...filteredAccessories.map(item => [
        item.sku,
        `"${item.name}"`,
        item.brand || '',
        item.category || '',
        item.quantity,
        item.cost_price,
        item.retail_price,
        item.quantity * item.retail_price
      ].join(','))
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `accessories_inventory_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
  };

  // Show message if no store is selected
  if (!currentStore) {
    return (
      <div className="h-full flex items-center justify-center bg-gray-50 dark:bg-gray-900 p-4">
        <div className="text-center max-w-md">
          <div className="mb-3 sm:mb-4">
            <div className="inline-flex items-center justify-center w-12 h-12 sm:w-16 sm:h-16 bg-primary-100 dark:bg-primary-900/30 rounded-full">
              <Package className="w-6 h-6 sm:w-8 sm:h-8 text-primary-600 dark:text-primary-400" />
            </div>
          </div>
          <h3 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-white mb-2">No Store Selected</h3>
          <p className="text-sm text-gray-500 dark:text-gray-400">Please select a store to manage accessories inventory</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 sm:gap-0">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white">Accessories & Paraphernalia</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Manage non-cannabis inventory for {currentStore.name}</p>
        </div>
        <div className="flex flex-col sm:flex-row gap-2 sm:gap-4 w-full sm:w-auto">
          <button
            onClick={() => setShowCategoryManagement(true)}
            className="w-full sm:w-auto px-4 py-2.5 sm:py-2 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-600 flex items-center justify-center gap-2 text-gray-900 dark:text-white active:scale-95 transition-all touch-manipulation"
          >
            <Tag className="w-4 h-4" />
            <span className="text-sm">Categories</span>
          </button>
          <button
            onClick={exportInventory}
            className="w-full sm:w-auto px-4 py-2.5 sm:py-2 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-600 flex items-center justify-center gap-2 text-gray-900 dark:text-white active:scale-95 transition-all touch-manipulation"
          >
            <Download className="w-4 h-4" />
            <span className="text-sm">Export</span>
          </button>
          <button
            onClick={() => setShowBarcodeIntake(true)}
            className="w-full sm:w-auto px-4 py-2.5 sm:py-2 bg-accent-600 dark:bg-accent-700 text-white rounded-lg hover:bg-accent-700 dark:hover:bg-accent-600 flex items-center justify-center gap-2 active:scale-95 transition-all touch-manipulation"
          >
            <Scan className="w-4 h-4" />
            <span className="text-sm">Scan Barcode</span>
          </button>
          <button
            onClick={() => setShowOCRScan(true)}
            className="w-full sm:w-auto px-4 py-2.5 sm:py-2 bg-indigo-600 dark:bg-indigo-700 text-white rounded-lg hover:bg-indigo-700 dark:hover:bg-indigo-600 flex items-center justify-center gap-2 active:scale-95 transition-all touch-manipulation"
          >
            <Camera className="w-4 h-4" />
            <span className="text-sm">OCR Scan</span>
          </button>
          <button
            onClick={() => setShowQuickIntake(true)}
            className="w-full sm:w-auto px-4 py-2.5 sm:py-2 bg-primary-600 dark:bg-primary-700 text-white rounded-lg hover:bg-primary-700 dark:hover:bg-primary-600 flex items-center justify-center gap-2 active:scale-95 transition-all touch-manipulation"
          >
            <Plus className="w-4 h-4" />
            <span className="text-sm">Quick Add</span>
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-6">
        <div className="bg-white dark:bg-gray-800 p-4 sm:p-6 rounded-lg border border-gray-200 dark:border-gray-700 transition-colors">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400">Total Items</p>
              <p className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white">{inventoryStats.total_items}</p>
            </div>
            <Package className="w-6 h-6 sm:w-8 sm:h-8 text-accent-500 dark:text-accent-400" />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 p-4 sm:p-6 rounded-lg border border-gray-200 dark:border-gray-700 transition-colors">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400">Total Units</p>
              <p className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white">{inventoryStats.total_units.toLocaleString()}</p>
            </div>
            <Box className="w-6 h-6 sm:w-8 sm:h-8 text-primary-500 dark:text-primary-400" />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 p-4 sm:p-6 rounded-lg border border-gray-200 dark:border-gray-700 transition-colors">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400">Inventory Value</p>
              <p className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white">{formatCurrency(inventoryStats.total_value)}</p>
            </div>
            <DollarSign className="w-6 h-6 sm:w-8 sm:h-8 text-primary-600 dark:text-primary-400" />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 p-4 sm:p-6 rounded-lg border border-gray-200 dark:border-gray-700 transition-colors">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400">Low Stock</p>
              <p className="text-xl sm:text-2xl font-bold text-danger-600 dark:text-red-400">{inventoryStats.low_stock_count}</p>
            </div>
            <AlertTriangle className="w-6 h-6 sm:w-8 sm:h-8 text-red-500 dark:text-red-400" />
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white dark:bg-gray-800 p-4 sm:p-6 rounded-lg border border-gray-200 dark:border-gray-700 transition-colors">
        <div className="flex flex-col sm:flex-row sm:flex-wrap gap-3 sm:gap-6 sm:items-center">
          {/* Search */}
          <div className="flex-1 min-w-full sm:min-w-[200px]">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400 dark:text-gray-500" />
              <input
                type="text"
                placeholder="Search by name, SKU, barcode..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 text-sm border border-gray-200 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-primary-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 transition-colors"
              />
            </div>
          </div>

          {/* Category Filter */}
          <div className="flex gap-2">
            <select
              value={selectedCategory || ''}
              onChange={(e) => setSelectedCategory(e.target.value ? Number(e.target.value) : null)}
              className="w-full sm:w-auto px-4 py-2 text-sm border border-gray-200 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-primary-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white transition-colors"
            >
              <option value="">All Categories</option>
              {categories.map(cat => (
                <option key={cat.id} value={cat.id}>
                  {cat.icon} {cat.name}
                </option>
              ))}
            </select>
            <button
              onClick={() => setShowCategoryManagement(true)}
              className="p-2 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg transition-colors border border-gray-200 dark:border-gray-600"
              title="Manage Categories"
            >
              <Tag className="w-4 h-4" />
            </button>
          </div>

          {/* Low Stock Toggle */}
          <label className="flex items-center gap-2 cursor-pointer touch-manipulation">
            <input
              type="checkbox"
              checked={showLowStockOnly}
              onChange={(e) => setShowLowStockOnly(e.target.checked)}
              className="rounded text-accent-600 dark:text-accent-400"
            />
            <span className="text-sm text-gray-900 dark:text-white">Low Stock Only</span>
          </label>

          {/* Refresh */}
          <button
            onClick={fetchAccessories}
            className="p-2 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg active:scale-95 transition-all touch-manipulation"
            aria-label="Refresh inventory data"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Inventory Table */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden transition-colors">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <Loader2 className="w-8 h-8 animate-spin text-accent-600 dark:text-accent-400" />
          </div>
        ) : filteredAccessories.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-gray-500 dark:text-gray-400">
            <Package className="w-12 h-12 mb-4" />
            <p className="text-base sm:text-lg">No accessories found</p>
            <p className="text-xs sm:text-sm">Try adjusting your filters or add new items</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <div className="inline-block min-w-full align-middle">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead className="bg-gray-50 dark:bg-gray-700">
                  <tr>
                    <th className="px-3 sm:px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Product</th>
                    <th className="px-3 sm:px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">SKU/Barcode</th>
                    <th className="px-3 sm:px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Category</th>
                    <th className="px-3 sm:px-4 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Stock</th>
                    <th className="px-3 sm:px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Cost</th>
                    <th className="px-3 sm:px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Retail</th>
                    <th className="px-3 sm:px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Value</th>
                    <th className="px-3 sm:px-4 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Location</th>
                    <th className="px-3 sm:px-4 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 dark:divide-gray-700 bg-white dark:bg-gray-800">
                  {filteredAccessories.map((item) => (
                    <tr key={item.id} className="hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                      <td className="px-3 sm:px-4 py-3">
                        <div className="flex items-center gap-2 sm:gap-4">
                          {item.image_url ? (
                            <img
                              src={item.image_url}
                              alt={item.name}
                              className="w-8 h-8 sm:w-10 sm:h-10 rounded object-cover flex-shrink-0"
                            />
                          ) : (
                            <div className="w-8 h-8 sm:w-10 sm:h-10 bg-gray-100 dark:bg-gray-700 rounded flex items-center justify-center flex-shrink-0">
                              <Package className="w-4 h-4 sm:w-5 sm:h-5 text-gray-400 dark:text-gray-500" />
                            </div>
                          )}
                          <div className="min-w-0">
                            <p className="font-medium text-xs sm:text-sm text-gray-900 dark:text-white truncate">{item.name}</p>
                            {item.brand && (
                              <p className="text-xs text-gray-500 dark:text-gray-400 truncate">{item.brand}</p>
                            )}
                          </div>
                        </div>
                      </td>
                      <td className="px-3 sm:px-4 py-3">
                        <p className="text-xs sm:text-sm font-mono text-gray-900 dark:text-white">{item.sku}</p>
                        {item.barcode && (
                          <p className="text-xs text-gray-500 dark:text-gray-400">{item.barcode}</p>
                        )}
                      </td>
                      <td className="px-3 sm:px-4 py-3">
                        <span className="text-xs sm:text-sm text-gray-900 dark:text-white">{item.category || 'Uncategorized'}</span>
                      </td>
                      <td className="px-3 sm:px-4 py-3">
                        <div className="text-center">
                          <p className={`text-xs sm:text-sm font-medium ${
                            item.quantity <= item.min_stock ? 'text-danger-600 dark:text-red-400' : 'text-gray-900 dark:text-white'
                          }`}>
                            {item.quantity}
                          </p>
                          {item.quantity <= item.min_stock && (
                            <p className="text-xs text-red-500 dark:text-red-400">Low Stock</p>
                          )}
                          {item.reserved > 0 && (
                            <p className="text-xs text-gray-500 dark:text-gray-400">{item.reserved} reserved</p>
                          )}
                        </div>
                      </td>
                      <td className="px-3 sm:px-4 py-3 text-right">
                        <p className="text-xs sm:text-sm text-gray-900 dark:text-white">{formatCurrency(item.cost_price)}</p>
                      </td>
                      <td className="px-3 sm:px-4 py-3 text-right">
                        <p className="text-xs sm:text-sm font-medium text-gray-900 dark:text-white">{formatCurrency(item.retail_price)}</p>
                        {item.sale_price && (
                          <p className="text-xs text-primary-600 dark:text-primary-400">{formatCurrency(item.sale_price)}</p>
                        )}
                      </td>
                      <td className="px-3 sm:px-4 py-3 text-right">
                        <p className="text-xs sm:text-sm font-medium text-gray-900 dark:text-white">
                          {formatCurrency(item.quantity * item.retail_price)}
                        </p>
                      </td>
                      <td className="px-3 sm:px-4 py-3 text-center">
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                          {item.location || '-'}
                        </span>
                      </td>
                      <td className="px-3 sm:px-4 py-3">
                        <div className="flex items-center justify-center gap-1">
                          <button
                            onClick={() => {
                              setSelectedAccessory(item);
                              setShowAdjustModal(true);
                            }}
                            className="p-1.5 sm:p-1 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700 rounded active:scale-95 transition-all touch-manipulation"
                            title="Adjust Stock"
                          >
                            <Edit2 className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => setSelectedAccessory(item)}
                            className="p-1.5 sm:p-1 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700 rounded active:scale-95 transition-all touch-manipulation"
                            title="View Details"
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* Modals */}
      {showBarcodeIntake && (
        <BarcodeIntakeModal
          isOpen={showBarcodeIntake}
          onClose={() => setShowBarcodeIntake(false)}
          onComplete={handleBarcodeScanned}
          storeId={storeId}
          categories={categories}
        />
      )}

      {showOCRScan && (
        <OCRScanModal
          isOpen={showOCRScan}
          onClose={() => setShowOCRScan(false)}
          onComplete={handleOCRScanned}
          storeId={storeId}
          categories={categories}
        />
      )}

      {showQuickIntake && (
        <QuickIntakeModal
          isOpen={showQuickIntake}
          onClose={() => setShowQuickIntake(false)}
          onComplete={() => {
            setShowQuickIntake(false);
            fetchAccessories();
          }}
          storeId={storeId}
          categories={categories}
        />
      )}

      {showAdjustModal && selectedAccessory && (
        <InventoryAdjustModal
          isOpen={showAdjustModal}
          onClose={() => {
            setShowAdjustModal(false);
            setSelectedAccessory(null);
          }}
          accessory={selectedAccessory}
          onAdjust={handleAdjustInventory}
        />
      )}

      {showCategoryManagement && (
        <CategoryManagementModal
          isOpen={showCategoryManagement}
          onClose={() => setShowCategoryManagement(false)}
          onCategoriesUpdated={() => {
            fetchCategories();
            fetchAccessories();
          }}
        />
      )}
    </div>
  );
};

export default Accessories;