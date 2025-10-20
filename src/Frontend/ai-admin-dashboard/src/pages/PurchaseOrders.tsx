import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';
import { getApiEndpoint } from '../config/app.config';
import { PurchaseOrder, Supplier, Product } from '../types';
import { FileText, Plus, Eye, Clock, CheckCircle, XCircle, TruckIcon, FileSpreadsheet, Package, Info } from 'lucide-react';
import ASNImportModal from '../components/ASNImportModal';
import CreatePurchaseOrderModal from '../components/CreatePurchaseOrderModal';
import { useStoreContext } from '../contexts/StoreContext';
import { useAuth } from '../contexts/AuthContext';
import toast from 'react-hot-toast';

const PurchaseOrders: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { currentStore } = useStoreContext();
  const { user } = useAuth();
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showASNImportModal, setShowASNImportModal] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState<PurchaseOrder | null>(null);
  const [selectedItem, setSelectedItem] = useState<any | null>(null);

  const { data: orders, isLoading, error } = useQuery({
    queryKey: ['purchase-orders', selectedStatus, currentStore?.id],
    queryFn: async () => {
      if (!currentStore?.id) return { purchase_orders: [] };

      const params: any = { store_id: currentStore.id };
      if (selectedStatus !== 'all') params.status = selectedStatus;

      const response = await fetch(getApiEndpoint(`/inventory/purchase-orders`), {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'X-Store-ID': currentStore.id,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch purchase orders');
      }

      return response.json();
    },
    enabled: !!currentStore?.id,
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
          'X-Store-ID': currentStore?.id || '',
        },
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to fetch order details');
      }

      const orderDetails = await response.json();

      // Parse charges if it's a JSON string (from JSONB column)
      if (orderDetails.charges && typeof orderDetails.charges === 'string') {
        try {
          orderDetails.charges = JSON.parse(orderDetails.charges);
        } catch (e) {
          console.warn('Failed to parse charges:', e);
          orderDetails.charges = [];
        }
      }

      // Ensure charges is always an array
      if (!Array.isArray(orderDetails.charges)) {
        orderDetails.charges = [];
      }

      setSelectedOrder(orderDetails);
    } catch (error) {
      toast.error(`Error fetching order details: ${(error as Error).message}`);
    }
  };

  const handleStatusUpdate = async (orderId: string, newStatus: string) => {
    // NOTE: This is for simple status updates (e.g., cancel)
    // For receiving, use handleReceivePurchaseOrder instead
    try {
      const response = await fetch(getApiEndpoint(`/inventory/purchase-orders/${orderId}/status?status=${newStatus}`), {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'X-Store-ID': currentStore.id,
        },
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to update status');
      }

      const data = await response.json();
      toast.success(data.message);

      // Refresh the purchase orders list
      queryClient.invalidateQueries({ queryKey: ['purchase-orders'] });
    } catch (error) {
      toast.error(`Error updating status: ${(error as Error).message}`);
    }
  };

  const handleReceivePurchaseOrder = async (orderId: string) => {
    try {
      // Fetch PO items first
      const poResponse = await fetch(getApiEndpoint(`/inventory/purchase-orders/${orderId}`), {
        headers: {
          'X-Store-ID': currentStore.id ,
        },
      });

      if (!poResponse.ok) {
        throw new Error('Failed to fetch purchase order details');
      }

      const poData = await poResponse.json();

      // Prepare items for receive endpoint - use batch_lot from ASN import
      const items = poData.items.map((item: any) => ({
        sku: item.sku,
        quantity_received: item.quantity_ordered,
        unit_cost: item.unit_cost,
        batch_lot: item.batch_lot,
        case_gtin: item.case_gtin,
        packaged_on_date: item.packaged_on_date,
        gtin_barcode: item.gtin_barcode,
        each_gtin: item.each_gtin,
        vendor: item.vendor, 
          item_name: item.item_name,
        brand: item.brand,
      }));

      // Call V1 receive endpoint
      const response = await fetch(getApiEndpoint(`/inventory/purchase-orders/${orderId}/receive`), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Store-ID': currentStore.id,
          'X-User-ID': user.user_id,
        },
        body: JSON.stringify({ items }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to receive purchase order');
      }

      const data = await response.json();
      toast.success(data.message || 'Purchase order received successfully');

      // Refresh the purchase orders list
      queryClient.invalidateQueries({ queryKey: ['purchase-orders'] });
    } catch (error) {
      toast.error(`Error receiving purchase order: ${(error as Error).message}`);
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

  // Show "No Store Selected" UI if no store is selected
  if (!currentStore) {
    return (
      <div className="h-full flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="mb-4">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-primary-100 rounded-full">
              <FileText className="w-8 h-8 text-primary-600" />
            </div>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No Store Selected</h3>
          <p className="text-gray-500">Please select a store to manage purchase orders</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Purchase Orders</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Managing purchase orders for {currentStore.name}</p>
        </div>
        <div className="flex gap-4">
          <button
            onClick={() => setShowASNImportModal(true)}
            className="bg-accent-600 dark:bg-accent-700 text-white px-4 py-2 rounded-lg hover:bg-accent-700 dark:hover:bg-accent-600 flex items-center gap-2"
          >
            <FileSpreadsheet className="h-5 w-5" />
            Import ASN
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="bg-primary-600 dark:bg-primary-700 text-white px-4 py-2 rounded-lg hover:bg-primary-700 dark:hover:bg-primary-600 flex items-center gap-2"
          >
            <Plus className="h-5 w-5" />
            Create Order
          </button>
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg p-6">
        <div className="flex gap-6 mb-6">
          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="px-4 py-2 border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white rounded-lg focus:ring-2 focus:ring-primary-500"
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
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead className="bg-gray-50 dark:bg-gray-900">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Order Number
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Supplier
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Order Date
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Expected Delivery
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Items
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Total Amount
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
              {orders?.purchase_orders?.map((order: any) => (
                <tr key={order.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      {getStatusIcon(order.status)}
                      <span className="ml-2 text-sm font-medium text-gray-900 dark:text-white">
                        {order.po_number}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900 dark:text-white">
                      {order.supplier_name || 'Unknown Supplier'}
                    </div>
                    <div className="text-sm text-gray-500 dark:text-gray-400">
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
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-200">
                    {new Date(order.order_date).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-200">
                    {order.expected_date ? new Date(order.expected_date).toLocaleDateString() : 'Not set'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-200">
                    {order.item_count || 0} items
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                    ${order.total_amount?.toFixed(2) || '0.00'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button
                      onClick={() => handleViewOrder(order)}
                      className="text-indigo-600 dark:text-indigo-400 hover:text-indigo-900 dark:hover:text-indigo-300 mr-3"
                    >
                      <Eye className="h-4 w-4" />
                    </button>
                    {order.status === 'pending' && (
                      <button
                        onClick={() => handleReceivePurchaseOrder(order.id)}
                        className="text-primary-600 dark:text-primary-400 hover:text-primary-900 dark:hover:text-primary-300 mr-3"
                        title="Receive items (creates batches & updates inventory)"
                      >
                        Receive Items
                      </button>
                    )}
                    {order.status === 'pending' && (
                      <button
                        onClick={() => handleStatusUpdate(order.id, 'cancelled')}
                        className="text-danger-600 dark:text-danger-400 hover:text-red-900 dark:hover:text-red-500"
                      >
                        Cancel
                      </button>
                    )}
                    {order.status === 'partial' && (
                      <button
                        onClick={() => handleReceivePurchaseOrder(order.id)}
                        className="text-primary-600 dark:text-primary-400 hover:text-primary-900 dark:hover:text-primary-300"
                        title="Receive remaining items"
                      >
                        Receive Remaining
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {(!orders?.purchase_orders || orders.purchase_orders.length === 0) && (
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
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Pending Orders</p>
              <p className="text-2xl font-bold text-warning-600 dark:text-warning-400">
                {orders?.stats?.pending_orders || 0}
              </p>
            </div>
            <Clock className="h-8 w-8 text-warning-600 dark:text-warning-400" />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">In Transit</p>
              <p className="text-2xl font-bold text-accent-600 dark:text-accent-400">
                {orders?.stats?.in_transit || 0}
              </p>
            </div>
            <TruckIcon className="h-8 w-8 text-accent-600 dark:text-accent-400" />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">This Month</p>
              <p className="text-2xl font-bold text-primary-600 dark:text-primary-400">
                {orders?.stats?.this_month || 0}
              </p>
            </div>
            <CheckCircle className="h-8 w-8 text-primary-600 dark:text-primary-400" />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Total Value</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                ${orders?.stats?.total_value?.toFixed(2) || '0.00'}
              </p>
            </div>
            <FileText className="h-8 w-8 text-gray-600 dark:text-gray-400" />
          </div>
        </div>
      </div>

      {/* Order Details Modal */}
      {selectedOrder && (
        <div className="fixed inset-0 bg-black bg-opacity-50 dark:bg-opacity-70 flex items-center justify-center p-6 z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg max-w-6xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              {/* Header */}
              <div className="flex justify-between items-start mb-6">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-3">
                    <FileText className="h-7 w-7 text-primary-600 dark:text-primary-400" />
                    {selectedOrder.po_number || selectedOrder.order_number}
                  </h2>
                  <div className="mt-2 flex items-center gap-3">
                    <span className={`px-3 py-1 rounded-full text-sm font-semibold ${getStatusColor(selectedOrder.status)}`}>
                      {selectedOrder.status}
                    </span>
                    {selectedOrder.paid && (
                      <span className="px-3 py-1 rounded-full text-sm font-semibold bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                        Paid in Full
                      </span>
                    )}
                  </div>
                </div>
                <button
                  onClick={() => setSelectedOrder(null)}
                  className="text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
                >
                  <XCircle className="h-6 w-6" />
                </button>
              </div>

              {/* Information Grid */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                {/* Supplier Information */}
                <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 border border-blue-200 dark:border-blue-800">
                  <h3 className="font-semibold text-blue-900 dark:text-blue-200 mb-3 flex items-center gap-2">
                    <Package className="h-5 w-5" />
                    Supplier Information
                  </h3>
                  <div className="space-y-2 text-sm">
                    <p className="text-blue-800 dark:text-blue-300 font-medium">{selectedOrder.supplier_name || 'Unknown Supplier'}</p>
                    {selectedOrder.supplier?.contact_person && (
                      <p className="text-blue-700 dark:text-blue-400">{selectedOrder.supplier.contact_person}</p>
                    )}
                  </div>
                </div>

                {/* Order Information */}
                <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-4 border border-purple-200 dark:border-purple-800">
                  <h3 className="font-semibold text-purple-900 dark:text-purple-200 mb-3 flex items-center gap-2">
                    <Clock className="h-5 w-5" />
                    Order Timeline
                  </h3>
                  <div className="space-y-2 text-sm">
                    <div>
                      <span className="text-purple-700 dark:text-purple-400 font-medium">Ordered:</span>
                      <span className="text-purple-800 dark:text-purple-300 ml-2">
                        {selectedOrder.order_date ? new Date(selectedOrder.order_date).toLocaleDateString() : 'N/A'}
                      </span>
                    </div>
                    <div>
                      <span className="text-purple-700 dark:text-purple-400 font-medium">Expected:</span>
                      <span className="text-purple-800 dark:text-purple-300 ml-2">
                        {selectedOrder.expected_date ? new Date(selectedOrder.expected_date).toLocaleDateString() : 'N/A'}
                      </span>
                    </div>
                    {selectedOrder.received_date && (
                      <div>
                        <span className="text-purple-700 dark:text-purple-400 font-medium">Received:</span>
                        <span className="text-purple-800 dark:text-purple-300 ml-2">
                          {new Date(selectedOrder.received_date).toLocaleDateString()}
                        </span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Shipping Information */}
                <div className="bg-amber-50 dark:bg-amber-900/20 rounded-lg p-4 border border-amber-200 dark:border-amber-800">
                  <h3 className="font-semibold text-amber-900 dark:text-amber-200 mb-3 flex items-center gap-2">
                    <TruckIcon className="h-5 w-5" />
                    Shipping Details
                  </h3>
                  <div className="space-y-2 text-sm">
                    {selectedOrder.shipment_id ? (
                      <div>
                        <span className="text-amber-700 dark:text-amber-400 font-medium">Shipment ID:</span>
                        <span className="text-amber-800 dark:text-amber-300 ml-2">{selectedOrder.shipment_id}</span>
                      </div>
                    ) : (
                      <p className="text-amber-600 dark:text-amber-400 italic">No shipment info</p>
                    )}
                    {selectedOrder.container_id && (
                      <div>
                        <span className="text-amber-700 dark:text-amber-400 font-medium">Container ID:</span>
                        <span className="text-amber-800 dark:text-amber-300 ml-2">{selectedOrder.container_id}</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Order Items Table */}
              <div className="mb-6">
                <h3 className="font-semibold text-gray-900 dark:text-white mb-3 text-lg">Order Items</h3>
                <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
                  <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                    <thead className="bg-gray-50 dark:bg-gray-900">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">SKU</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Item Name</th>
                        <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Quantity</th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Unit Cost</th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Total</th>
                        <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                      {selectedOrder.items && selectedOrder.items.length > 0 ? (
                        selectedOrder.items.map((item) => (
                          <tr key={item.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                            <td className="px-4 py-3 text-sm font-mono text-gray-900 dark:text-gray-200">{item.sku || 'Unknown'}</td>
                            <td className="px-4 py-3 text-sm text-gray-900 dark:text-gray-200">
                              {item.item_name}
                            </td>
                            <td className="px-4 py-3 text-sm text-center text-gray-900 dark:text-gray-200">{item.quantity_ordered || 0}</td>
                            <td className="px-4 py-3 text-sm text-right text-gray-900 dark:text-gray-200">${(item.unit_cost || 0).toFixed(2)}</td>
                            <td className="px-4 py-3 text-sm text-right font-medium text-gray-900 dark:text-gray-200">${(item.total_cost || 0).toFixed(2)}</td>
                            <td className="px-4 py-3 text-sm text-center">
                              <button
                                onClick={() => setSelectedItem(item)}
                                className="text-accent-600 dark:text-accent-400 hover:text-accent-800 dark:hover:text-accent-300"
                                title="View Details"
                              >
                                <Info className="h-4 w-4 inline" />
                              </button>
                            </td>
                          </tr>
                        ))
                      ) : (
                        <tr>
                          <td colSpan={6} className="px-4 py-8 text-sm text-gray-500 dark:text-gray-400 text-center">
                            No items in this order
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Financial Summary */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Charges Breakdown */}
                {selectedOrder.charges && selectedOrder.charges.length > 0 && (
                  <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-4 border border-yellow-200 dark:border-yellow-800">
                    <h3 className="font-semibold text-yellow-900 dark:text-yellow-200 mb-3">Additional Charges</h3>
                    <div className="space-y-2">
                      {selectedOrder.charges.map((charge: any, index: number) => (
                        <div key={index} className="flex justify-between items-center text-sm">
                          <div className="flex items-center gap-2">
                            <span className="text-yellow-800 dark:text-yellow-300">{charge.description}</span>
                            {charge.taxable && (
                              <span className="text-xs px-2 py-0.5 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded">
                                Taxable
                              </span>
                            )}
                          </div>
                          <span className={`font-medium ${charge.amount >= 0 ? 'text-yellow-700 dark:text-yellow-400' : 'text-green-700 dark:text-green-400'}`}>
                            {charge.amount >= 0 ? '+' : ''}${charge.amount.toFixed(2)}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Total Breakdown */}
                <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
                  <h3 className="font-semibold text-gray-900 dark:text-white mb-3">Order Summary</h3>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600 dark:text-gray-400">Subtotal (Items):</span>
                      <span className="font-medium text-gray-900 dark:text-white">${(selectedOrder.subtotal || 0).toFixed(2)}</span>
                    </div>
                    {selectedOrder.charges && selectedOrder.charges.length > 0 && (
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600 dark:text-gray-400">Additional Charges:</span>
                        <span className="font-medium text-gray-900 dark:text-white">
                          ${selectedOrder.charges.reduce((sum: number, c: any) => sum + (c.amount || 0), 0).toFixed(2)}
                        </span>
                      </div>
                    )}
                    {selectedOrder.tax_amount > 0 && (
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600 dark:text-gray-400">Tax:</span>
                        <span className="font-medium text-blue-700 dark:text-blue-400">+${(selectedOrder.tax_amount || 0).toFixed(2)}</span>
                      </div>
                    )}
                    <div className="border-t border-gray-300 dark:border-gray-600 pt-2 mt-2">
                      <div className="flex justify-between">
                        <span className="text-lg font-bold text-gray-900 dark:text-white">Total Amount:</span>
                        <span className="text-lg font-bold text-primary-600 dark:text-primary-400">${(selectedOrder.total_amount || 0).toFixed(2)}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Notes Section */}
              {selectedOrder.notes && (
                <div className="mt-6 bg-gray-50 dark:bg-gray-900 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
                  <h3 className="font-semibold text-gray-900 dark:text-white mb-2">Notes</h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">{selectedOrder.notes}</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Item Details Modal */}
      {selectedItem && (
        <div className="fixed inset-0 bg-black bg-opacity-50 dark:bg-opacity-70 flex items-center justify-center p-6 z-[60]">
          <div className="bg-white dark:bg-gray-800 rounded-lg max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
                  <Package className="h-6 w-6 text-primary-600 dark:text-primary-400" />
                  Item Details
                </h2>
                <button
                  onClick={() => setSelectedItem(null)}
                  className="text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
                >
                  <XCircle className="h-6 w-6" />
                </button>
              </div>

              <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-6">
                <table className="min-w-full">
                  <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                    <tr>
                      <td className="py-2.5 px-4 font-medium text-gray-600 dark:text-gray-400 w-1/3">SKU:</td>
                      <td className="py-2.5 px-4 text-gray-900 dark:text-gray-200">{selectedItem.sku || 'N/A'}</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 px-4 font-medium text-gray-600 dark:text-gray-400">Item Name:</td>
                      <td className="py-2.5 px-4 text-gray-900 dark:text-gray-200">
                        {selectedItem.item_name || 'N/A'}
                      </td>
                    </tr>
                    <tr>
                      <td className="py-2.5 px-4 font-medium text-gray-600 dark:text-gray-400">Vendor:</td>
                      <td className="py-2.5 px-4 text-gray-900 dark:text-gray-200">{selectedItem.vendor || 'N/A'}</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 px-4 font-medium text-gray-600 dark:text-gray-400">Brand:</td>
                      <td className="py-2.5 px-4 text-gray-900 dark:text-gray-200">{selectedItem.brand || 'N/A'}</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 px-4 font-medium text-gray-600 dark:text-gray-400">Quantity Ordered:</td>
                      <td className="py-2.5 px-4 text-gray-900 dark:text-gray-200">{selectedItem.quantity_ordered || 0}</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 px-4 font-medium text-gray-600 dark:text-gray-400">Quantity Received:</td>
                      <td className="py-2.5 px-4 text-gray-900 dark:text-gray-200">{selectedItem.quantity_received || 0}</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 px-4 font-medium text-gray-600 dark:text-gray-400">Shipped Quantity:</td>
                      <td className="py-2.5 px-4 text-gray-900 dark:text-gray-200">{selectedItem.shipped_qty || 'N/A'}</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 px-4 font-medium text-gray-600 dark:text-gray-400">UOM:</td>
                      <td className="py-2.5 px-4 text-gray-900 dark:text-gray-200">{selectedItem.uom || 'N/A'}</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 px-4 font-medium text-gray-600 dark:text-gray-400">UOM Conversion:</td>
                      <td className="py-2.5 px-4 text-gray-900 dark:text-gray-200">{selectedItem.uom_conversion || 'N/A'}</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 px-4 font-medium text-gray-600 dark:text-gray-400">UOM Conversion Qty:</td>
                      <td className="py-2.5 px-4 text-gray-900 dark:text-gray-200">{selectedItem.uom_conversion_qty || 'N/A'}</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 px-4 font-medium text-gray-600 dark:text-gray-400">Unit Cost:</td>
                      <td className="py-2.5 px-4 text-gray-900 dark:text-gray-200">${(selectedItem.unit_cost || 0).toFixed(2)}</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 px-4 font-medium text-gray-600 dark:text-gray-400">Total Cost:</td>
                      <td className="py-2.5 px-4 text-gray-700 dark:text-gray-300 font-medium text-sm">
                        ${(selectedItem.total_cost || 0).toFixed(2)}
                      </td>
                    </tr>
                    <tr>
                      <td className="py-2.5 px-4 font-medium text-gray-600 dark:text-gray-400">Batch/Lot:</td>
                      <td className="py-2.5 px-4 text-gray-900 dark:text-gray-200">{selectedItem.batch_lot || 'N/A'}</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 px-4 font-medium text-gray-600 dark:text-gray-400">Packaged On Date:</td>
                      <td className="py-2.5 px-4 text-gray-900 dark:text-gray-200">
                        {selectedItem.packaged_on_date ? new Date(selectedItem.packaged_on_date).toLocaleDateString() : 'N/A'}
                      </td>
                    </tr>
                    <tr>
                      <td className="py-2.5 px-4 font-medium text-gray-600 dark:text-gray-400">Case GTIN:</td>
                      <td className="py-2.5 px-4 text-gray-900 dark:text-gray-200">{selectedItem.case_gtin || 'Not provided'}</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 px-4 font-medium text-gray-600 dark:text-gray-400">GTIN Barcode:</td>
                      <td className="py-2.5 px-4 text-gray-900 dark:text-gray-200">{selectedItem.gtin_barcode || 'Not provided'}</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 px-4 font-medium text-gray-600 dark:text-gray-400">Each GTIN:</td>
                      <td className="py-2.5 px-4 text-gray-900 dark:text-gray-200">{selectedItem.each_gtin || 'Not provided'}</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <div className="mt-6 flex justify-end">
                <button
                  onClick={() => setSelectedItem(null)}
                  className="px-4 py-2 bg-gray-600 dark:bg-gray-700 text-white rounded-lg hover:bg-gray-700 dark:hover:bg-gray-600"
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
    </div>
  );
};

export default PurchaseOrders;