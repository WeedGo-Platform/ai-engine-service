import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';
import { getApiEndpoint } from '../config/app.config';
import { PurchaseOrder, Supplier, Product } from '../types';
import { FileText, Plus, Eye, Clock, CheckCircle, XCircle, TruckIcon, FileSpreadsheet, Package, Info } from 'lucide-react';
import ASNImportModal from '../components/ASNImportModal';
import CreatePurchaseOrderModal from '../components/CreatePurchaseOrderModal';
import StoreSelectionModal from '../components/StoreSelectionModal';
import { useStoreContext } from '../contexts/StoreContext';
import { useAuth } from '../contexts/AuthContext';

const PurchaseOrders: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { currentStore, selectStore, stores } = useStoreContext();
  const { user, isSuperAdmin, isTenantAdminOnly, isStoreManager } = useAuth();
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showASNImportModal, setShowASNImportModal] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState<PurchaseOrder | null>(null);
  const [selectedItem, setSelectedItem] = useState<any | null>(null);
  const [showStoreSelectionModal, setShowStoreSelectionModal] = useState(false);
  const [selectedStoreForOrders, setSelectedStoreForOrders] = useState<{id: string, name: string} | null>(null);


  // Determine if we need to show store selection modal
  useEffect(() => {
    if (isSuperAdmin() || isTenantAdminOnly()) {
      // For admins, check if we have a current store selected
      if (currentStore) {
        setSelectedStoreForOrders({ id: currentStore.id, name: currentStore.name });
      } else if (!selectedStoreForOrders) {
        // Only show modal if no store is selected
        setShowStoreSelectionModal(true);
      }
    } else if (isStoreManager()) {
      // For store managers, use the current store from context (which should be auto-selected)
      if (currentStore) {
        setSelectedStoreForOrders({ id: currentStore.id, name: currentStore.name });
      } else if (user?.stores && user.stores.length > 0) {
        // Fallback to user's first store if context hasn't loaded yet
        const userStore = user.stores[0];
        setSelectedStoreForOrders({ id: userStore.id, name: userStore.name });
      }
    }
  }, [currentStore, user, isSuperAdmin, isTenantAdminOnly, isStoreManager]);

  const handleStoreSelect = async (tenantId: string, storeId: string, storeName: string, tenantName?: string) => {
    try {
      // Update the store context with the selected store
      await selectStore(storeId, storeName);
      setSelectedStoreForOrders({ id: storeId, name: storeName });
      setShowStoreSelectionModal(false);
    } catch (error) {
      console.error('Failed to select store:', error);
      // Still set the local state even if context update fails
      setSelectedStoreForOrders({ id: storeId, name: storeName });
      setShowStoreSelectionModal(false);
    }
  };

  const { data: orders, isLoading, error } = useQuery({
    queryKey: ['purchase-orders', selectedStatus, selectedStoreForOrders?.id],
    queryFn: async () => {
      if (!selectedStoreForOrders) return { purchase_orders: [] };

      const params: any = { store_id: selectedStoreForOrders.id };
      if (selectedStatus !== 'all') params.status = selectedStatus;

      const response = await fetch(getApiEndpoint(`/inventory/purchase-orders`), {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'X-Store-ID': selectedStoreForOrders.id,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch purchase orders');
      }

      return response.json();
    },
    enabled: !!selectedStoreForOrders,
  });

  const { data: suppliers } = useQuery({
    queryKey: ['suppliers'],
    queryFn: async () => {
      const response = await api.suppliers.getAll();
      return response.data;
    },
  });

  // Products are not needed for this page
  const products = null;

  const createMutation = useMutation({
    mutationFn: (order: Partial<PurchaseOrder>) => api.purchaseOrders.create(order),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['purchase-orders'] });
      setShowCreateModal(false);
    },
  });

  const updateMutation = useMutation({
    mutationFn: (data: { id: string; order: Partial<PurchaseOrder> }) =>
      api.purchaseOrders.update(data.id, data.order),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['purchase-orders'] });
    },
  });

  const getProductNameBySku = (sku: string): string => {
    // Parse SKU to generate a product name
    if (!sku) return 'Unknown Product';
    
    // Example SKU patterns:
    // 102779_10X0.5G___ -> 10x 0.5g Pre-Rolls
    // 103719_2X1G___ -> 2x 1g Pre-Rolls
    // 101557_28G___ -> 28g Flower
    
    const parts = sku.split('_');
    if (parts.length < 2) return sku;
    
    const productCode = parts[0];
    const sizeInfo = parts[1];
    
    // Parse size information
    if (sizeInfo.includes('X')) {
      const [quantity, size] = sizeInfo.split('X');
      if (size.includes('G')) {
        const grams = size.replace('G', '');
        return `${quantity}x ${grams}g Pre-Rolls - ${productCode}`;
      }
    } else if (sizeInfo.includes('G')) {
      const grams = sizeInfo.replace('G', '');
      return `${grams}g Flower - ${productCode}`;
    }
    
    return `Product ${productCode}`;
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'draft':
        return <FileText className="h-5 w-5 text-gray-500" />;
      case 'pending':
        return <Clock className="h-5 w-5 text-yellow-500" />;
      case 'approved':
        return <CheckCircle className="h-5 w-5 text-primary-500" />;
      case 'ordered':
        return <TruckIcon className="h-5 w-5 text-accent-500" />;
      case 'received':
        return <CheckCircle className="h-5 w-5 text-primary-600" />;
      case 'cancelled':
        return <XCircle className="h-5 w-5 text-red-500" />;
      default:
        return <FileText className="h-5 w-5 text-gray-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'draft':
        return 'bg-gray-50 text-gray-800';
      case 'pending':
        return 'bg-warning-100 text-warning-800';
      case 'approved':
        return 'bg-primary-100 text-primary-800';
      case 'ordered':
        return 'bg-blue-100 text-blue-800';
      case 'shipped':
        return 'bg-indigo-100 text-indigo-800';
      case 'received':
        return 'bg-green-200 text-primary-900';
      case 'cancelled':
        return 'bg-danger-100 text-danger-800';
      default:
        return 'bg-gray-50 text-gray-800';
    }
  };

  const handleViewOrder = async (order: any) => {
    try {
      const response = await fetch(getApiEndpoint(`/inventory/purchase-orders/${order.id}`), {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'X-Store-ID': selectedStoreForOrders?.id || '',
        },
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to fetch order details');
      }
      
      const orderDetails = await response.json();
      setSelectedOrder(orderDetails);
    } catch (error) {
      alert(`Error fetching order details: ${(error as Error).message}`);
    }
  };

  const handleStatusUpdate = async (orderId: string, newStatus: string) => {
    try {
      const response = await fetch(getApiEndpoint(`/inventory/purchase-orders/${orderId}/status?status=${newStatus}`), {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'X-Store-ID': selectedStoreForOrders?.id || '',
        },
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to update status');
      }
      
      const data = await response.json();
      alert(data.message);
      
      // Refresh the purchase orders list
      queryClient.invalidateQueries({ queryKey: ['purchase-orders'] });
    } catch (error) {
      alert(`Error updating status: ${(error as Error).message}`);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-danger-50 border border-red-200 text-red-700 px-4 py-3 rounded">
        Error loading purchase orders: {(error as Error).message}
      </div>
    );
  }

  // Show loading state while determining store
  if (!selectedStoreForOrders && !showStoreSelectionModal) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Purchase Orders</h1>
        <div className="flex gap-4">
          <button
            onClick={() => setShowASNImportModal(true)}
            className="bg-accent-600 text-white px-4 py-2 rounded-lg hover:bg-accent-700 flex items-center gap-2"
          >
            <FileSpreadsheet className="h-5 w-5" />
            Import ASN
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 flex items-center gap-2"
          >
            <Plus className="h-5 w-5" />
            Create Order
          </button>
        </div>
      </div>

      <div className="bg-white rounded-lg  p-6">
        <div className="flex gap-6 mb-6">
          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-500"
          >
            <option value="all">All Status</option>
            <option value="draft">Draft</option>
            <option value="pending">Pending</option>
            <option value="approved">Approved</option>
            <option value="ordered">Ordered</option>
            <option value="shipped">Shipped</option>
            <option value="received">Received</option>
            <option value="cancelled">Cancelled</option>
          </select>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Order Number
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Supplier
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Order Date
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Expected Delivery
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Items
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Total Amount
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {orders?.purchase_orders?.map((order: any) => (
                <tr key={order.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      {getStatusIcon(order.status)}
                      <span className="ml-2 text-sm font-medium text-gray-900">
                        {order.po_number}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">
                      {order.supplier_name || 'Unknown Supplier'}
                    </div>
                    <div className="text-sm text-gray-500">
                      {order.supplier?.contact_person || ''}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusColor(
                        order.status
                      )}`}
                    >
                      {order.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {new Date(order.order_date).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {order.expected_date ? new Date(order.expected_date).toLocaleDateString() : 'Not set'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {order.item_count || 0} items
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    ${order.total_amount?.toFixed(2) || '0.00'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button
                      onClick={() => handleViewOrder(order)}
                      className="text-indigo-600 hover:text-indigo-900 mr-3"
                    >
                      <Eye className="h-4 w-4" />
                    </button>
                    {order.status === 'pending' && (
                      <button
                        onClick={() => handleStatusUpdate(order.id, 'received')}
                        className="text-primary-600 hover:text-primary-900 mr-3"
                      >
                        Mark as Received
                      </button>
                    )}
                    {order.status === 'pending' && (
                      <button
                        onClick={() => handleStatusUpdate(order.id, 'cancelled')}
                        className="text-danger-600 hover:text-red-900"
                      >
                        Cancel
                      </button>
                    )}
                    {order.status === 'partial' && (
                      <button
                        onClick={() => handleStatusUpdate(order.id, 'received')}
                        className="text-primary-600 hover:text-primary-900"
                      >
                        Mark Fully Received
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {(!orders?.data || orders.data.length === 0) && (
          <div className="text-center py-12">
            <FileText className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No purchase orders</h3>
            <p className="mt-1 text-sm text-gray-500">
              Get started by creating a new purchase order.
            </p>
          </div>
        )}
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg  p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Pending Orders</p>
              <p className="text-2xl font-bold text-warning-600">
                {orders?.data?.filter((o: PurchaseOrder) => o.status === 'pending').length || 0}
              </p>
            </div>
            <Clock className="h-8 w-8 text-warning-600" />
          </div>
        </div>

        <div className="bg-white rounded-lg  p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">In Transit</p>
              <p className="text-2xl font-bold text-accent-600">
                {orders?.data?.filter((o: PurchaseOrder) => o.status === 'shipped').length || 0}
              </p>
            </div>
            <TruckIcon className="h-8 w-8 text-accent-600" />
          </div>
        </div>

        <div className="bg-white rounded-lg  p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">This Month</p>
              <p className="text-2xl font-bold text-primary-600">
                {orders?.data?.filter((o: PurchaseOrder) => {
                  const orderDate = new Date(o.order_date);
                  const now = new Date();
                  return orderDate.getMonth() === now.getMonth() && 
                         orderDate.getFullYear() === now.getFullYear();
                }).length || 0}
              </p>
            </div>
            <CheckCircle className="h-8 w-8 text-primary-600" />
          </div>
        </div>

        <div className="bg-white rounded-lg  p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Value</p>
              <p className="text-2xl font-bold text-gray-900">
                ${orders?.data?.reduce((sum: number, o: PurchaseOrder) => 
                  sum + (o.total_amount || 0), 0
                ).toFixed(2) || '0.00'}
              </p>
            </div>
            <FileText className="h-8 w-8 text-gray-600" />
          </div>
        </div>
      </div>

      {/* Order Details Modal */}
      {selectedOrder && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-6 z-50">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-bold">Order Details: {selectedOrder.order_number}</h2>
                <button
                  onClick={() => setSelectedOrder(null)}
                  className="text-gray-500 hover:text-gray-700"
                >
                  <XCircle className="h-6 w-6" />
                </button>
              </div>

              <div className="grid grid-cols-2 gap-6 mb-6">
                <div>
                  <h3 className="font-semibold mb-2">Supplier Information</h3>
                  <p className="text-sm text-gray-600">
                    {selectedOrder.supplier?.name}<br />
                    {selectedOrder.supplier?.contact_name}<br />
                    {selectedOrder.supplier?.email}<br />
                    {selectedOrder.supplier?.phone}
                  </p>
                </div>
                <div>
                  <h3 className="font-semibold mb-2">Order Information</h3>
                  <p className="text-sm text-gray-600">
                    Status: <span className={`px-2 py-1 rounded ${getStatusColor(selectedOrder.status)}`}>
                      {selectedOrder.status}
                    </span><br />
                    Order Date: {new Date(selectedOrder.order_date).toLocaleDateString()}<br />
                    Expected: {new Date(selectedOrder.expected_delivery).toLocaleDateString()}<br />
                    {selectedOrder.actual_delivery && 
                      `Received: ${new Date(selectedOrder.actual_delivery).toLocaleDateString()}`}<br />
                    {selectedOrder.shipment_id && `Shipment ID: ${selectedOrder.shipment_id}`}<br />
                    {selectedOrder.container_id && `Container ID: ${selectedOrder.container_id}`}<br />
                    {selectedOrder.vendor && `Vendor: ${selectedOrder.vendor}`}
                  </p>
                </div>
              </div>

              <div className="mb-6">
                <h3 className="font-semibold mb-2">Order Items</h3>
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Product</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Product Name</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Quantity</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Unit Cost</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Total</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {selectedOrder.items && selectedOrder.items.length > 0 ? (
                      selectedOrder.items.map((item) => (
                        <tr key={item.id}>
                          <td className="px-4 py-2 text-sm">{item.sku || 'Unknown'}</td>
                          <td className="px-4 py-2 text-sm">
                            {item.product_name || getProductNameBySku(item.sku)}
                          </td>
                          <td className="px-4 py-2 text-sm">{item.quantity_ordered || 0}</td>
                          <td className="px-4 py-2 text-sm">${(item.unit_cost || 0).toFixed(2)}</td>
                          <td className="px-4 py-2 text-sm">${(item.total_cost || 0).toFixed(2)}</td>
                          <td className="px-4 py-2 text-sm">
                            <button
                              onClick={() => setSelectedItem(item)}
                              className="text-accent-600 hover:text-blue-800"
                              title="View Details"
                            >
                              <Info className="h-4 w-4" />
                            </button>
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={6} className="px-4 py-4 text-sm text-gray-500 text-center">
                          No items in this order
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>

              <div className="border-t pt-4">
                <div className="flex justify-end space-y-1">
                  <div className="text-right">
                    <p className="text-lg font-bold">Total Amount: ${(selectedOrder.total_amount || 0).toFixed(2)}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Item Details Modal */}
      {selectedItem && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-6 z-[60]">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-bold flex items-center gap-2">
                  <Package className="h-6 w-6 text-primary-600" />
                  Item Details
                </h2>
                <button
                  onClick={() => setSelectedItem(null)}
                  className="text-gray-500 hover:text-gray-700"
                >
                  <XCircle className="h-6 w-6" />
                </button>
              </div>

              <div className="bg-gray-50 rounded-lg p-6">
                <table className="min-w-full">
                  <tbody className="divide-y divide-gray-200">
                    <tr>
                      <td className="py-2.5 px-4 font-medium text-gray-600 w-1/3">SKU:</td>
                      <td className="py-2.5 px-4 text-gray-900">{selectedItem.sku || 'N/A'}</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 px-4 font-medium text-gray-600">Product Name:</td>
                      <td className="py-2.5 px-4 text-gray-900">
                        {selectedItem.product_name || getProductNameBySku(selectedItem.sku)}
                      </td>
                    </tr>
                    <tr>
                      <td className="py-2.5 px-4 font-medium text-gray-600">Vendor:</td>
                      <td className="py-2.5 px-4 text-gray-900">{selectedItem.vendor || 'N/A'}</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 px-4 font-medium text-gray-600">Brand:</td>
                      <td className="py-2.5 px-4 text-gray-900">{selectedItem.brand || 'N/A'}</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 px-4 font-medium text-gray-600">Quantity Ordered:</td>
                      <td className="py-2.5 px-4 text-gray-900">{selectedItem.quantity_ordered || 0}</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 px-4 font-medium text-gray-600">Quantity Received:</td>
                      <td className="py-2.5 px-4 text-gray-900">{selectedItem.quantity_received || 0}</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 px-4 font-medium text-gray-600">Shipped Quantity:</td>
                      <td className="py-2.5 px-4 text-gray-900">{selectedItem.shipped_qty || 'N/A'}</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 px-4 font-medium text-gray-600">UOM:</td>
                      <td className="py-2.5 px-4 text-gray-900">{selectedItem.uom || 'N/A'}</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 px-4 font-medium text-gray-600">UOM Conversion:</td>
                      <td className="py-2.5 px-4 text-gray-900">{selectedItem.uom_conversion || 'N/A'}</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 px-4 font-medium text-gray-600">UOM Conversion Qty:</td>
                      <td className="py-2.5 px-4 text-gray-900">{selectedItem.uom_conversion_qty || 'N/A'}</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 px-4 font-medium text-gray-600">Unit Cost:</td>
                      <td className="py-2.5 px-4 text-gray-900">${(selectedItem.unit_cost || 0).toFixed(2)}</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 px-4 font-medium text-gray-600">Total Cost:</td>
                      <td className="py-2.5 px-4 text-gray-700 font-medium text-sm">
                        ${(selectedItem.total_cost || 0).toFixed(2)}
                      </td>
                    </tr>
                    <tr>
                      <td className="py-2.5 px-4 font-medium text-gray-600">Batch/Lot:</td>
                      <td className="py-2.5 px-4 text-gray-900">{selectedItem.batch_lot || 'N/A'}</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 px-4 font-medium text-gray-600">Packaged On Date:</td>
                      <td className="py-2.5 px-4 text-gray-900">
                        {selectedItem.packaged_on_date ? new Date(selectedItem.packaged_on_date).toLocaleDateString() : 'N/A'}
                      </td>
                    </tr>
                    <tr>
                      <td className="py-2.5 px-4 font-medium text-gray-600">Case GTIN:</td>
                      <td className="py-2.5 px-4 text-gray-900">{selectedItem.case_gtin || 'Not provided'}</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 px-4 font-medium text-gray-600">GTIN Barcode:</td>
                      <td className="py-2.5 px-4 text-gray-900">{selectedItem.gtin_barcode || 'Not provided'}</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 px-4 font-medium text-gray-600">Each GTIN:</td>
                      <td className="py-2.5 px-4 text-gray-900">{selectedItem.each_gtin || 'Not provided'}</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <div className="mt-6 flex justify-end">
                <button
                  onClick={() => setSelectedItem(null)}
                  className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ASN Import Modal */}
      <ASNImportModal
        isOpen={showASNImportModal}
        onClose={() => setShowASNImportModal(false)}
        suppliers={suppliers?.suppliers || []}
      />
      
      {/* Create Purchase Order Modal */}
      <CreatePurchaseOrderModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        suppliers={suppliers?.suppliers || []}
        products={products?.products || []}
      />

      <StoreSelectionModal
        isOpen={showStoreSelectionModal}
        onSelect={handleStoreSelect}
        onClose={() => {
          // Close modal and navigate to dashboard
          setShowStoreSelectionModal(false);
          navigate('/dashboard');
        }}
      />
    </div>
  );
};

export default PurchaseOrders;