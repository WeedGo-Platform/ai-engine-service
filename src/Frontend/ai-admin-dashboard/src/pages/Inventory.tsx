import React, { useState, useEffect } from 'react';
import {
  Package,
  Search,
  Filter,
  Plus,
  Edit,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  Calendar,
  DollarSign,
  TrendingUp,
  AlertCircle,
  CheckCircle,
  Barcode,
  Info,
  Box,
  Building2
} from 'lucide-react';
import { api } from '../services/api';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useStoreContext } from '../contexts/StoreContext';
import InventoryEditModal from '../components/InventoryEditModal';
import { getApiEndpoint } from '../config/app.config';

interface InventoryItem {
  id: string;
  name: string;
  product_name?: string;
  sku: string;
  category: string;
  quantity_available: number;
  quantity_on_hand?: number;
  quantity_reserved?: number;
  stock_status: string;
  price: number;
  retail_price?: number;
  unit_cost?: number;
  reorder_level?: number;
  reorder_point?: number;
  reorder_quantity?: number;
  is_available?: boolean;
  brand?: string;
  image_url?: string;
  // Batch tracking fields
  batch_lot?: string;
  lot_number?: string;
  packaged_on_date?: string;
  manufacture_date?: string;
  supplier_name?: string;
  supplier?: string;
  // GTIN fields
  case_gtin?: string;
  each_gtin?: string;
  gtin_barcode?: string;
  // Cannabis specific
  thc_percentage?: number;
  cbd_percentage?: number;
  thc_content?: number;
  cbd_content?: number;
  test_results?: string;
  lab_tested?: boolean;
  certificate_number?: string;
  coa?: string;
  notes?: string;
  // Batch details array
  batch_details?: Array<{
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
  }>;
  store_id?: string;
}

const Inventory: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterCategory, setFilterCategory] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingItem, setEditingItem] = useState<InventoryItem | null>(null);
  const [showEditModal, setShowEditModal] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const queryClient = useQueryClient();
  const { currentStore, inventoryStats } = useStoreContext();

  // Fetch inventory data for current store
  const { data: inventory, isLoading } = useQuery({
    queryKey: ['inventory', currentStore?.id, searchTerm, filterCategory, filterStatus],
    queryFn: async () => {
      if (!currentStore) return [];
      
      const params: any = {
        store_id: currentStore.id
      };
      if (searchTerm) params.search = searchTerm;
      if (filterCategory !== 'all') params.category = filterCategory;
      if (filterStatus !== 'all') {
        if (filterStatus === 'low_stock') params.low_stock = true;
        else if (filterStatus === 'out_of_stock') params.out_of_stock = true;
      }
      
      // Use the new store-inventory endpoint
      const response = await fetch(`${getApiEndpoint('/store-inventory/list')}?${new URLSearchParams(params)}`, {
        headers: {
          'Content-Type': 'application/json',
          'X-Store-ID': currentStore.id
        }
      });
      
      if (!response.ok) throw new Error('Failed to fetch inventory');
      const data = await response.json();
      return data.items || [];
    },
    enabled: !!currentStore
  });

  // Toggle expanded row
  const toggleRowExpanded = (itemId: string) => {
    setExpandedRows(prev => {
      const newSet = new Set(prev);
      if (newSet.has(itemId)) {
        newSet.delete(itemId);
      } else {
        newSet.add(itemId);
      }
      return newSet;
    });
  };

  // Get status color
  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'in_stock':
        return 'bg-primary-100 text-primary-800 dark:bg-green-900/20 dark:text-green-400';
      case 'low_stock':
        return 'bg-warning-100 text-warning-800 dark:bg-yellow-900/20 dark:text-yellow-400';
      case 'out_of_stock':
        return 'bg-danger-100 text-danger-800 dark:bg-red-900/20 dark:text-red-400';
      default:
        return 'bg-gray-50 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'in_stock':
        return <CheckCircle className="w-5 h-5 text-primary-500" />;
      case 'low_stock':
        return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
      case 'out_of_stock':
        return <AlertCircle className="w-5 h-5 text-red-500" />;
      default:
        return <Info className="w-5 h-5 text-gray-500" />;
    }
  };

  // Calculate stats
  const stats = {
    totalItems: inventory?.length || 0,
    inStock: inventory?.filter((item: any) =>
      item.quantity_available > 0 || item.stock_status?.toLowerCase() === 'in_stock'
    ).length || 0,
    lowStock: inventory?.filter((item: any) =>
      item.stock_status?.toLowerCase() === 'low_stock'
    ).length || 0,
    totalValue: inventory?.reduce((sum: number, item: any) =>
      sum + ((item.quantity_available || 0) * (item.unit_cost || item.retail_price || item.price || 0)), 0) || 0
  };

  // Filter inventory items
  const filteredItems = inventory?.filter((item: any) => {
    const matchesSearch = !searchTerm || 
      item.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.sku?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.batch_lot?.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesCategory = filterCategory === 'all' || item.category === filterCategory;
    const matchesStatus = filterStatus === 'all' || 
      (filterStatus === 'in_stock' && item.stock_status === 'in_stock') ||
      (filterStatus === 'low_stock' && item.stock_status === 'low_stock') ||
      (filterStatus === 'out_of_stock' && item.stock_status === 'out_of_stock');
    
    return matchesSearch && matchesCategory && matchesStatus;
  }) || [];

  useEffect(() => {
    if (success) {
      const timer = setTimeout(() => setSuccess(null), 3000);
      return () => clearTimeout(timer);
    }
  }, [success]);

  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => setError(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [error]);

  return (
    <div className="h-full flex flex-col space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center flex-shrink-0">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Inventory Management</h1>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-accent-600 text-white rounded-lg hover:bg-accent-700 transition-colors"
        >
          <Plus className="w-5 h-5" />
          Add Product
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 flex-shrink-0">
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg ">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Total Products</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {stats.totalItems}
              </p>
            </div>
            <Package className="w-8 h-8 text-accent-500" />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg ">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">In Stock</p>
              <p className="text-2xl font-bold text-primary-600">
                {stats.inStock}
              </p>
            </div>
            <CheckCircle className="w-8 h-8 text-primary-500" />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg ">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Low Stock</p>
              <p className="text-2xl font-bold text-warning-600">
                {stats.lowStock}
              </p>
            </div>
            <AlertTriangle className="w-8 h-8 text-yellow-500" />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg ">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Total Value</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                ${stats.totalValue.toLocaleString()}
              </p>
            </div>
            <DollarSign className="w-8 h-8 text-primary-500" />
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white dark:bg-gray-800 p-6 rounded-lg  flex-shrink-0">
        <div className="flex flex-wrap gap-6">
          <div className="flex-1 min-w-[200px]">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                placeholder="Search products, SKU, or batch/lot..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-200 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
              />
            </div>
          </div>

          <select
            value={filterCategory}
            onChange={(e) => setFilterCategory(e.target.value)}
            className="px-4 py-2 border border-gray-200 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
          >
            <option value="all">All Categories</option>
            <option value="flower">Flower</option>
            <option value="pre-rolls">Pre-Rolls</option>
            <option value="edibles">Edibles</option>
            <option value="concentrates">Concentrates</option>
            <option value="topicals">Topicals</option>
            <option value="accessories">Accessories</option>
          </select>

          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="px-4 py-2 border border-gray-200 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
          >
            <option value="all">All Status</option>
            <option value="in_stock">In Stock</option>
            <option value="low_stock">Low Stock</option>
            <option value="out_of_stock">Out of Stock</option>
          </select>
        </div>
      </div>

      {/* Success Alert */}
      {success && (
        <div className="bg-primary-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-6 flex items-center gap-2">
          <CheckCircle className="w-5 h-5 text-primary-600 dark:text-green-400" />
          <span className="text-primary-700 dark:text-green-300">{success}</span>
        </div>
      )}

      {/* Error Alert */}
      {error && (
        <div className="bg-danger-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6 flex items-center gap-2">
          <AlertCircle className="w-5 h-5 text-danger-600 dark:text-red-400" />
          <span className="text-red-700 dark:text-red-300">{error}</span>
        </div>
      )}

      {/* Inventory Table */}
      <div className="bg-white dark:bg-gray-800 rounded-lg  overflow-hidden flex-1 flex flex-col min-h-0">
        <div className="overflow-auto flex-1">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-700 border-b border-gray-200 dark:border-gray-600 sticky top-0 z-10">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Product
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  SKU
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Batch/Lot
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Available
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Price
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
              {isLoading ? (
                <tr>
                  <td colSpan={7} className="px-6 py-8 text-center text-gray-500 dark:text-gray-400">
                    Loading inventory...
                  </td>
                </tr>
              ) : filteredItems.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-8 text-center text-gray-500 dark:text-gray-400">
                    No inventory items found
                  </td>
                </tr>
              ) : (
                filteredItems.map((item: InventoryItem, index: number) => (
                  <React.Fragment key={`${item.id}-${item.batch_lot || index}`}>
                    <tr className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          {item.image_url ? (
                            <img
                              src={item.image_url}
                              alt={item.product_name || item.name}
                              className="h-10 w-10 rounded-lg object-cover mr-3"
                              onError={(e) => {
                                e.currentTarget.onerror = null;
                                e.currentTarget.src = '';
                                e.currentTarget.style.display = 'none';
                                e.currentTarget.parentElement?.insertAdjacentHTML('beforeend', '<div class="h-10 w-10 rounded-lg bg-gray-100 dark:bg-gray-700 flex items-center justify-center mr-3"><svg class="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/></svg></div>');
                              }}
                            />
                          ) : (
                            <Package className="h-5 w-5 text-gray-400 mr-3" />
                          )}
                          <div>
                            <div className="text-sm font-medium text-gray-900 dark:text-white">
                              {item.product_name || item.name}
                            </div>
                            <div className="text-sm text-gray-500 dark:text-gray-400">
                              {item.category}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900 dark:text-white font-mono">
                          {item.sku}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <button
                          onClick={() => item.batch_lot && toggleRowExpanded(item.id)}
                          className="flex items-center gap-1 text-sm text-accent-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
                          disabled={!item.batch_lot}
                        >
                          {item.batch_lot || 'N/A'}
                          {item.batch_lot && (
                            expandedRows.has(item.id) ? 
                              <ChevronUp className="h-4 w-4" /> : 
                              <ChevronDown className="h-4 w-4" />
                          )}
                        </button>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900 dark:text-white">
                          {item.quantity_available || 0}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900 dark:text-white">
                          ${(parseFloat(item.retail_price) || parseFloat(item.price) || 0).toFixed(2)}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center gap-2">
                          {getStatusIcon(item.stock_status)}
                          <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusColor(item.stock_status)}`}>
                            {item.stock_status?.replace('_', ' ')}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <button
                          onClick={() => {
                            setEditingItem(item);
                            setShowEditModal(true);
                          }}
                          className="text-indigo-600 hover:text-indigo-900 dark:text-indigo-400 dark:hover:text-indigo-300"
                        >
                          <Edit className="h-4 w-4" />
                        </button>
                      </td>
                    </tr>
                    {expandedRows.has(item.id) && item.batch_lot && (
                      <tr>
                        <td colSpan={7} className="px-6 py-4 bg-gray-50 dark:bg-gray-700/30">
                          {item.batch_details && item.batch_details.length > 0 ? (
                            <div className="space-y-4">
                              {item.batch_details.map((batch: any, batchIndex: number) => (
                                <div key={batchIndex} className="border-b border-gray-200 dark:border-gray-600 last:border-0 pb-4 last:pb-0">
                                  {item.batch_details.length > 1 && (
                                    <div className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
                                      Batch {batchIndex + 1} of {item.batch_details.length}
                                    </div>
                                  )}
                                  <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                                    <div>
                                      <div className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Batch/Lot Number</div>
                                      <div className="text-sm text-gray-900 dark:text-white font-mono">
                                        {batch.batch_lot}
                                      </div>
                                    </div>
                                    <div>
                                      <div className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Packaged On</div>
                                      <div className="text-sm text-gray-900 dark:text-white">
                                        {batch.packaged_on_date ?
                                          new Date(batch.packaged_on_date).toLocaleDateString() :
                                          'Not specified'}
                                      </div>
                                    </div>
                                    <div>
                                      <div className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Supplier</div>
                                      <div className="text-sm text-gray-900 dark:text-white">
                                        {batch.supplier_name || 'Unknown'}
                                      </div>
                                    </div>
                                    <div>
                                      <div className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Case GTIN</div>
                                      <div className="text-sm text-gray-900 dark:text-white font-mono">
                                        {batch.case_gtin || 'Not specified'}
                                      </div>
                                    </div>
                                    <div>
                                      <div className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Each GTIN</div>
                                      <div className="text-sm text-gray-900 dark:text-white font-mono">
                                        {batch.each_gtin || 'Not specified'}
                                      </div>
                                    </div>
                                    <div>
                                      <div className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">GTIN Barcode</div>
                                      <div className="text-sm text-gray-900 dark:text-white font-mono text-xs">
                                        {batch.gtin_barcode || 'Not specified'}
                                      </div>
                                    </div>
                                    <div>
                                      <div className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Vendor</div>
                                      <div className="text-sm text-gray-900 dark:text-white">
                                        {batch.vendor || 'Not specified'}
                                      </div>
                                    </div>
                                    <div>
                                      <div className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Brand</div>
                                      <div className="text-sm text-gray-900 dark:text-white">
                                        {batch.brand || item.brand || 'Not specified'}
                                      </div>
                                    </div>
                                    <div>
                                      <div className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Quantity Remaining</div>
                                      <div className="text-sm text-gray-900 dark:text-white">
                                        {batch.quantity_remaining || 0} units
                                      </div>
                                    </div>
                                    <div>
                                      <div className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Unit Cost</div>
                                      <div className="text-sm text-gray-900 dark:text-white">
                                        ${parseFloat(batch.unit_cost || 0).toFixed(2)}
                                      </div>
                                    </div>
                                    <div>
                                      <div className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">PO Number</div>
                                      <div className="text-sm text-gray-900 dark:text-white font-mono">
                                        {batch.po_number || 'N/A'}
                                      </div>
                                    </div>
                                    <div>
                                      <div className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">THC/CBD</div>
                                      <div className="text-sm text-gray-900 dark:text-white">
                                        THC: {item.thc_content || 0}% /
                                        CBD: {item.cbd_content || 0}%
                                      </div>
                                    </div>
                                  </div>
                                </div>
                              ))}
                            </div>
                          ) : (
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                              <div>
                                <div className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Batch/Lot Number</div>
                                <div className="text-sm text-gray-900 dark:text-white font-mono">
                                  {item.batch_lot}
                                </div>
                              </div>
                              <div>
                                <div className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">No batch details available</div>
                                <div className="text-sm text-gray-500 dark:text-gray-400">
                                  Batch tracking data not found
                                </div>
                              </div>
                            </div>
                          )}
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Edit Modal */}
      {showEditModal && editingItem && (
        <InventoryEditModal
          item={editingItem}
          isOpen={showEditModal}
          onClose={() => {
            setShowEditModal(false);
            setEditingItem(null);
          }}
          onSave={(updatedItem) => {
            queryClient.invalidateQueries({ queryKey: ['inventory'] });
            setSuccess('Inventory item updated successfully');
            setShowEditModal(false);
            setEditingItem(null);
          }}
          storeId={currentStore?.id}
        />
      )}
    </div>
  );
};

export default Inventory;