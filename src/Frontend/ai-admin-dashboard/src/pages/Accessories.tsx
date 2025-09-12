import React, { useState, useEffect, useCallback } from 'react';
import {
  Package, Scan, Plus, Search, Filter, AlertTriangle,
  Download, Upload, Edit2, Trash2, Eye, BarChart3,
  DollarSign, TrendingUp, ShoppingCart, Camera,
  RefreshCw, Check, X, Loader2, Info, Box
} from 'lucide-react';
import axios from 'axios';
import BarcodeIntakeModal from '../components/accessories/BarcodeIntakeModal';
import QuickIntakeModal from '../components/accessories/QuickIntakeModal';
import InventoryAdjustModal from '../components/accessories/InventoryAdjustModal';

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

  const storeId = 'store_001'; // TODO: Get from context

  // Fetch accessories inventory
  const fetchAccessories = useCallback(async () => {
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
        `http://localhost:5024/api/accessories/inventory/${storeId}`,
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
      const response = await axios.get('http://localhost:5024/api/accessories/categories');
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
      await axios.post('http://localhost:5024/api/accessories/inventory/adjust', {
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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Accessories & Paraphernalia</h1>
          <p className="text-gray-500">Manage non-cannabis inventory</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={exportInventory}
            className="px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center gap-2"
          >
            <Download className="w-4 h-4" />
            Export
          </button>
          <button
            onClick={() => setShowBarcodeIntake(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
          >
            <Scan className="w-4 h-4" />
            Scan Barcode
          </button>
          <button
            onClick={() => setShowQuickIntake(true)}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            Quick Add
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Total Items</p>
              <p className="text-2xl font-bold">{inventoryStats.total_items}</p>
            </div>
            <Package className="w-8 h-8 text-blue-500" />
          </div>
        </div>
        
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Total Units</p>
              <p className="text-2xl font-bold">{inventoryStats.total_units.toLocaleString()}</p>
            </div>
            <Box className="w-8 h-8 text-green-500" />
          </div>
        </div>
        
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Inventory Value</p>
              <p className="text-2xl font-bold">${inventoryStats.total_value.toFixed(2)}</p>
            </div>
            <DollarSign className="w-8 h-8 text-green-600" />
          </div>
        </div>
        
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Low Stock</p>
              <p className="text-2xl font-bold text-red-600">{inventoryStats.low_stock_count}</p>
            </div>
            <AlertTriangle className="w-8 h-8 text-red-500" />
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow">
        <div className="flex flex-wrap gap-4 items-center">
          {/* Search */}
          <div className="flex-1 min-w-[300px]">
            <div className="relative">
              <Search className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search by name, SKU, barcode..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          {/* Category Filter */}
          <select
            value={selectedCategory || ''}
            onChange={(e) => setSelectedCategory(e.target.value ? Number(e.target.value) : null)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
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
              className="rounded text-blue-600"
            />
            <span className="text-sm">Low Stock Only</span>
          </label>

          {/* Refresh */}
          <button
            onClick={fetchAccessories}
            className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Inventory Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
          </div>
        ) : filteredAccessories.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-gray-500">
            <Package className="w-12 h-12 mb-4" />
            <p className="text-lg">No accessories found</p>
            <p className="text-sm">Try adjusting your filters or add new items</p>
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Product</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">SKU/Barcode</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Category</th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Stock</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Cost</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Retail</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Value</th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Location</th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {filteredAccessories.map((item) => (
                <tr key={item.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-3">
                      {item.image_url ? (
                        <img
                          src={item.image_url}
                          alt={item.name}
                          className="w-10 h-10 rounded object-cover"
                        />
                      ) : (
                        <div className="w-10 h-10 bg-gray-200 rounded flex items-center justify-center">
                          <Package className="w-5 h-5 text-gray-400" />
                        </div>
                      )}
                      <div>
                        <p className="font-medium text-sm">{item.name}</p>
                        {item.brand && (
                          <p className="text-xs text-gray-500">{item.brand}</p>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <p className="text-sm font-mono">{item.sku}</p>
                    {item.barcode && (
                      <p className="text-xs text-gray-500">{item.barcode}</p>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-sm">{item.category || 'Uncategorized'}</span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="text-center">
                      <p className={`text-sm font-medium ${
                        item.quantity <= item.min_stock ? 'text-red-600' : 'text-gray-900'
                      }`}>
                        {item.quantity}
                      </p>
                      {item.quantity <= item.min_stock && (
                        <p className="text-xs text-red-500">Low Stock</p>
                      )}
                      {item.reserved > 0 && (
                        <p className="text-xs text-gray-500">{item.reserved} reserved</p>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <p className="text-sm">${item.cost_price.toFixed(2)}</p>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <p className="text-sm font-medium">${item.retail_price.toFixed(2)}</p>
                    {item.sale_price && (
                      <p className="text-xs text-green-600">${item.sale_price.toFixed(2)}</p>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <p className="text-sm font-medium">
                      ${(item.quantity * item.retail_price).toFixed(2)}
                    </p>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className="text-xs text-gray-500">
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
                        className="p-1 text-gray-600 hover:bg-gray-100 rounded"
                        title="Adjust Stock"
                      >
                        <Edit2 className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => setSelectedAccessory(item)}
                        className="p-1 text-gray-600 hover:bg-gray-100 rounded"
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