import React, { useState, useEffect, useCallback } from 'react';
import {
  Package, Scan, Plus, Search, Filter, AlertTriangle,
  Download, Upload, Edit2, Trash2, Eye, BarChart3,
  DollarSign, TrendingUp, ShoppingCart, Camera,
  RefreshCw, Check, X, Loader2, Info, Box
} from 'lucide-react';
import axios from 'axios';
import BarcodeIntakeModal from '../components/accessories/BarcodeIntakeModal';
import { getApiEndpoint } from '../config/app.config';
import QuickIntakeModal from '../components/accessories/QuickIntakeModal';
import InventoryAdjustModal from '../components/accessories/InventoryAdjustModal';
import { useStoreContext } from '../contexts/StoreContext';

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
  const [showQuickIntake, setShowQuickIntake] = useState(false);
  const [showAdjustModal, setShowAdjustModal] = useState(false);

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
      <div className="h-full flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="text-center">
          <div className="mb-4">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-primary-100 dark:bg-primary-900/30 rounded-full">
              <Package className="w-8 h-8 text-primary-600 dark:text-primary-400" />
            </div>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">No Store Selected</h3>
          <p className="text-gray-500 dark:text-gray-400">Please select a store to manage accessories inventory</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Accessories & Paraphernalia</h1>
          <p className="text-gray-500 dark:text-gray-400">Manage non-cannabis inventory for {currentStore.name}</p>
        </div>
        <div className="flex gap-4">
          <button
            onClick={exportInventory}
            className="px-4 py-2 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-600 flex items-center gap-2 text-gray-900 dark:text-white"
          >
            <Download className="w-4 h-4" />
            Export
          </button>
          <button
            onClick={() => setShowBarcodeIntake(true)}
            className="px-4 py-2 bg-accent-600 dark:bg-accent-700 text-white rounded-lg hover:bg-accent-700 dark:hover:bg-accent-600 flex items-center gap-2"
          >
            <Scan className="w-4 h-4" />
            Scan Barcode
          </button>
          <button
            onClick={() => setShowQuickIntake(true)}
            className="px-4 py-2 bg-primary-600 dark:bg-primary-700 text-white rounded-lg hover:bg-primary-700 dark:hover:bg-primary-600 flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            Quick Add
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg border border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Total Items</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">{inventoryStats.total_items}</p>
            </div>
            <Package className="w-8 h-8 text-accent-500 dark:text-accent-400" />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg border border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Total Units</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">{inventoryStats.total_units.toLocaleString()}</p>
            </div>
            <Box className="w-8 h-8 text-primary-500 dark:text-primary-400" />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg border border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Inventory Value</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">${inventoryStats.total_value.toFixed(2)}</p>
            </div>
            <DollarSign className="w-8 h-8 text-primary-600 dark:text-primary-400" />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg border border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Low Stock</p>
              <p className="text-2xl font-bold text-danger-600 dark:text-red-400">{inventoryStats.low_stock_count}</p>
            </div>
            <AlertTriangle className="w-8 h-8 text-red-500 dark:text-red-400" />
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white dark:bg-gray-800 p-6 rounded-lg border border-gray-200 dark:border-gray-700">
        <div className="flex flex-wrap gap-6 items-center">
          {/* Search */}
          <div className="flex-1 min-w-[300px]">
            <div className="relative">
              <Search className="absolute left-3 top-4 w-4 h-4 text-gray-400 dark:text-gray-500" />
              <input
                type="text"
                placeholder="Search by name, SKU, barcode..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-200 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-primary-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500"
              />
            </div>
          </div>

          {/* Category Filter */}
          <select
            value={selectedCategory || ''}
            onChange={(e) => setSelectedCategory(e.target.value ? Number(e.target.value) : null)}
            className="px-4 py-2 border border-gray-200 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-primary-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          >
            <option value="">All Categories</option>
            {categories.map(cat => (
              <option key={cat.id} value={cat.id}>
                {cat.icon} {cat.name}
              </option>
            ))}
          </select>

          {/* Low Stock Toggle */}
          <label className="flex items-center gap-2 cursor-pointer">
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
            className="p-2 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Inventory Table */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <Loader2 className="w-8 h-8 animate-spin text-accent-600 dark:text-accent-400" />
          </div>
        ) : filteredAccessories.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-gray-500 dark:text-gray-400">
            <Package className="w-12 h-12 mb-4" />
            <p className="text-lg">No accessories found</p>
            <p className="text-sm">Try adjusting your filters or add new items</p>
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-700">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Product</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">SKU/Barcode</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Category</th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Stock</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Cost</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Retail</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Value</th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Location</th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {filteredAccessories.map((item) => (
                <tr key={item.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-4">
                      {item.image_url ? (
                        <img
                          src={item.image_url}
                          alt={item.name}
                          className="w-10 h-10 rounded object-cover"
                        />
                      ) : (
                        <div className="w-10 h-10 bg-gray-100 dark:bg-gray-700 rounded flex items-center justify-center">
                          <Package className="w-5 h-5 text-gray-400 dark:text-gray-500" />
                        </div>
                      )}
                      <div>
                        <p className="font-medium text-sm text-gray-900 dark:text-white">{item.name}</p>
                        {item.brand && (
                          <p className="text-xs text-gray-500 dark:text-gray-400">{item.brand}</p>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <p className="text-sm font-mono text-gray-900 dark:text-white">{item.sku}</p>
                    {item.barcode && (
                      <p className="text-xs text-gray-500 dark:text-gray-400">{item.barcode}</p>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-sm text-gray-900 dark:text-white">{item.category || 'Uncategorized'}</span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="text-center">
                      <p className={`text-sm font-medium ${
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
                  <td className="px-4 py-3 text-right">
                    <p className="text-sm text-gray-900 dark:text-white">${item.cost_price.toFixed(2)}</p>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <p className="text-sm font-medium text-gray-900 dark:text-white">${item.retail_price.toFixed(2)}</p>
                    {item.sale_price && (
                      <p className="text-xs text-primary-600 dark:text-primary-400">${item.sale_price.toFixed(2)}</p>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <p className="text-sm font-medium text-gray-900 dark:text-white">
                      ${(item.quantity * item.retail_price).toFixed(2)}
                    </p>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      {item.location || '-'}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-center gap-1">
                      <button
                        onClick={() => {
                          setSelectedAccessory(item);
                          setShowAdjustModal(true);
                        }}
                        className="p-1 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700 rounded"
                        title="Adjust Stock"
                      >
                        <Edit2 className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => setSelectedAccessory(item)}
                        className="p-1 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700 rounded"
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
        )}
      </div>

      {/* Modals */}
      {showBarcodeIntake && (
        <BarcodeIntakeModal
          isOpen={showBarcodeIntake}
          onClose={() => setShowBarcodeIntake(false)}
          onComplete={handleBarcodeScanned}
          storeId={storeId}
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
    </div>
  );
};

export default Accessories;