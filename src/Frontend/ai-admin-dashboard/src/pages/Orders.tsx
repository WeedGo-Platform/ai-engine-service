import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';
import { Order, Customer, Product } from '../types';
import { ShoppingCart, Clock, CheckCircle, XCircle, Package, Truck, CreditCard, Eye } from 'lucide-react';
import { usePersistentState } from '../hooks/usePersistentState';
import { useStoreContext } from '../contexts/StoreContext';

const Orders: React.FC = () => {
  const { currentStore } = useStoreContext();
  const queryClient = useQueryClient();
  const [selectedStatus, setSelectedStatus] = usePersistentState<string>('orders_status_filter', 'all');
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);

  const { data: orders, isLoading, error } = useQuery({
    queryKey: ['orders', selectedStatus, currentStore?.id],
    queryFn: async () => {
      // Don't fetch if no store is selected
      if (!currentStore?.id) {
        return { data: [] };
      }
      const params: any = { store_id: currentStore.id };
      if (selectedStatus !== 'all') params.status = selectedStatus;
      const response = await api.orders.getAll(params);
      return response.data;
    },
    enabled: !!currentStore?.id,
  });

  const updateMutation = useMutation({
    mutationFn: async (data: { id: string; payment_status?: string; delivery_status?: string; notes?: string }) => {
      const response = await api.orders.updateStatus(data.id, {
        payment_status: data.payment_status,
        delivery_status: data.delivery_status,
        notes: data.notes
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['orders'] });
    },
  });

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending':
        return <Clock className="h-5 w-5 text-yellow-500" />;
      case 'confirmed':
        return <CheckCircle className="h-5 w-5 text-accent-500" />;
      case 'processing':
        return <Package className="h-5 w-5 text-indigo-500" />;
      case 'ready':
        return <CheckCircle className="h-5 w-5 text-primary-500" />;
      case 'out_for_delivery':
        return <Truck className="h-5 w-5 text-accent-500" />;
      case 'delivered':
        return <Truck className="h-5 w-5 text-primary-600" />;
      case 'cancelled':
        return <XCircle className="h-5 w-5 text-red-500" />;
      default:
        return <ShoppingCart className="h-5 w-5 text-gray-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending':
        return 'bg-warning-100 dark:bg-warning-900/30 text-warning-800 dark:text-warning-300';
      case 'confirmed':
        return 'bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300';
      case 'processing':
        return 'bg-indigo-100 dark:bg-indigo-900/30 text-indigo-800 dark:text-indigo-300';
      case 'ready':
        return 'bg-primary-100 dark:bg-primary-900/30 text-primary-800 dark:text-primary-300';
      case 'out_for_delivery':
        return 'bg-accent-100 dark:bg-accent-900/30 text-accent-800 dark:text-accent-300';
      case 'delivered':
        return 'bg-green-200 dark:bg-green-900/30 text-primary-900 dark:text-green-300';
      case 'cancelled':
        return 'bg-danger-100 dark:bg-red-900/30 text-danger-800 dark:text-red-300';
      default:
        return 'bg-gray-50 dark:bg-gray-700 text-gray-800 dark:text-gray-300';
    }
  };

  const getPaymentIcon = (method: string) => {
    switch (method) {
      case 'credit':
      case 'debit':
        return <CreditCard className="h-4 w-4 text-gray-500" />;
      default:
        return null;
    }
  };

  const handleStatusUpdate = (orderId: string, newStatus: string, statusType: 'payment' | 'delivery' = 'delivery') => {
    const updateData: any = { id: orderId };
    if (statusType === 'payment') {
      updateData.payment_status = newStatus;
    } else {
      updateData.delivery_status = newStatus;
    }
    updateMutation.mutate(updateData);
  };

  // Show "No Store Selected" UI if no store is selected
  if (!currentStore) {
    return (
      <div className="h-full flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="text-center">
          <div className="mb-4">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-accent-100 dark:bg-accent-900/30 rounded-full">
              <ShoppingCart className="w-8 h-8 text-accent-600 dark:text-accent-400" />
            </div>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">No Store Selected</h3>
          <p className="text-gray-500 dark:text-gray-400">Please select a store to manage orders</p>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 dark:border-primary-400"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-danger-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 px-4 py-3 rounded">
        Error loading orders: {(error as Error).message}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Order Management</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Managing orders for {currentStore.name}</p>
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg p-6">
        <div className="flex gap-6 mb-6">
          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="px-4 py-2 border border-gray-200 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 dark:focus:ring-primary-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          >
            <option value="all">All Orders</option>
            <option value="pending">Pending</option>
            <option value="confirmed">Confirmed</option>
            <option value="preparing">Preparing</option>
            <option value="ready">Ready</option>
            <option value="out_for_delivery">Out for Delivery</option>
            <option value="delivered">Delivered</option>
            <option value="cancelled">Cancelled</option>
          </select>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead className="bg-gray-50 dark:bg-gray-700">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Order
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Customer
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Items
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Total
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Payment
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Created
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
              {orders?.data?.map((order: Order) => (
                <tr key={order.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      {getStatusIcon(order.status)}
                      <span className="ml-2 text-sm font-medium text-gray-900 dark:text-white">
                        {order.order_number}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900 dark:text-white">
                      {order.customer?.first_name} {order.customer?.last_name}
                    </div>
                    <div className="text-sm text-gray-500 dark:text-gray-400">
                      {order.customer?.email}
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
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="text-sm text-gray-900 dark:text-white capitalize">
                      {order.order_type === 'pickup' ? (
                        <Package className="inline h-4 w-4 mr-1" />
                      ) : (
                        <Truck className="inline h-4 w-4 mr-1" />
                      )}
                      {order.order_type}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                    {order.items?.length || 0} items
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                    ${order.total_amount?.toFixed(2) || '0.00'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center text-sm text-gray-900 dark:text-white">
                      {getPaymentIcon(order.payment_method)}
                      <span className="ml-1 capitalize">{order.payment_method}</span>
                    </div>
                    <span className={`text-xs ${order.payment_status === 'paid' ? 'text-primary-600 dark:text-primary-400' : 'text-warning-600 dark:text-warning-400'}`}>
                      {order.payment_status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                    {new Date(order.created_at).toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button
                      onClick={() => setSelectedOrder(order)}
                      className="text-indigo-600 dark:text-indigo-400 hover:text-indigo-900 dark:hover:text-indigo-300 mr-3"
                    >
                      <Eye className="h-4 w-4" />
                    </button>
                    {order.status === 'pending' && (
                      <button
                        onClick={() => handleStatusUpdate(order.id, 'confirmed')}
                        className="text-accent-600 dark:text-accent-400 hover:text-blue-900 dark:hover:text-accent-300 mr-2"
                      >
                        Confirm
                      </button>
                    )}
                    {order.status === 'confirmed' && (
                      <button
                        onClick={() => handleStatusUpdate(order.id, 'preparing')}
                        className="text-indigo-600 dark:text-indigo-400 hover:text-indigo-900 dark:hover:text-indigo-300 mr-2"
                      >
                        Prepare
                      </button>
                    )}
                    {(order.status === 'preparing' || order.status === 'processing') && (
                      <button
                        onClick={() => handleStatusUpdate(order.id, 'ready')}
                        className="text-primary-600 dark:text-primary-400 hover:text-primary-900 dark:hover:text-primary-300 mr-2"
                      >
                        Ready
                      </button>
                    )}
                    {order.status === 'ready' && (
                      <>
                        <button
                          onClick={() => handleStatusUpdate(order.id, 'out_for_delivery')}
                          className="text-accent-600 dark:text-accent-400 hover:text-accent-900 dark:hover:text-accent-300 mr-2"
                        >
                          Out for Delivery
                        </button>
                        <button
                          onClick={() => handleStatusUpdate(order.id, 'delivered')}
                          className="text-primary-600 dark:text-primary-400 hover:text-primary-900 dark:hover:text-primary-300"
                        >
                          Mark Delivered
                        </button>
                      </>
                    )}
                    {order.status === 'out_for_delivery' && (
                      <button
                        onClick={() => handleStatusUpdate(order.id, 'delivered')}
                        className="text-primary-600 dark:text-primary-400 hover:text-primary-900 dark:hover:text-primary-300"
                      >
                        Delivered
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
            <ShoppingCart className="mx-auto h-12 w-12 text-gray-400 dark:text-gray-600" />
            <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">No orders found</h3>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              Orders will appear here when customers place them.
            </p>
          </div>
        )}
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Pending</p>
              <p className="text-2xl font-bold text-warning-600 dark:text-warning-400">
                {orders?.data?.filter((o: Order) => o.status === 'pending').length || 0}
              </p>
            </div>
            <Clock className="h-8 w-8 text-warning-600 dark:text-warning-400" />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Processing</p>
              <p className="text-2xl font-bold text-accent-600 dark:text-accent-400">
                {orders?.data?.filter((o: Order) =>
                  ['confirmed', 'processing'].includes(o.status)
                ).length || 0}
              </p>
            </div>
            <Package className="h-8 w-8 text-accent-600 dark:text-accent-400" />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Today's Revenue</p>
              <p className="text-2xl font-bold text-primary-600 dark:text-primary-400">
                ${orders?.data?.filter((o: Order) => {
                  const orderDate = new Date(o.created_at);
                  const today = new Date();
                  return orderDate.toDateString() === today.toDateString() &&
                         o.payment_status === 'paid';
                }).reduce((sum: number, o: Order) => sum + o.total_amount, 0).toFixed(2) || '0.00'}
              </p>
            </div>
            <CreditCard className="h-8 w-8 text-primary-600 dark:text-primary-400" />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Completed Today</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {orders?.data?.filter((o: Order) => {
                  const orderDate = new Date(o.created_at);
                  const today = new Date();
                  return orderDate.toDateString() === today.toDateString() &&
                         o.status === 'delivered';
                }).length || 0}
              </p>
            </div>
            <CheckCircle className="h-8 w-8 text-gray-600 dark:text-gray-400" />
          </div>
        </div>
      </div>

      {/* Order Details Modal */}
      {selectedOrder && (
        <div className="fixed inset-0 bg-black bg-opacity-50 dark:bg-opacity-70 flex items-center justify-center p-6 z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-bold text-gray-900 dark:text-white">Order Details: {selectedOrder.order_number}</h2>
                <button
                  onClick={() => setSelectedOrder(null)}
                  className="text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
                >
                  <XCircle className="h-6 w-6" />
                </button>
              </div>

              <div className="grid grid-cols-2 gap-6 mb-6">
                <div>
                  <h3 className="font-semibold mb-2 text-gray-900 dark:text-white">Customer Information</h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {selectedOrder.customer?.first_name} {selectedOrder.customer?.last_name}<br />
                    {selectedOrder.customer?.email}<br />
                    {selectedOrder.customer?.phone}<br />
                    Type: {selectedOrder.customer?.customer_type}
                  </p>
                </div>
                <div>
                  <h3 className="font-semibold mb-2 text-gray-900 dark:text-white">Order Information</h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Status: <span className={`px-2 py-1 rounded ${getStatusColor(selectedOrder.status)}`}>
                      {selectedOrder.status}
                    </span><br />
                    Type: {selectedOrder.order_type}<br />
                    Payment: {selectedOrder.payment_method} ({selectedOrder.payment_status})<br />
                    Created: {new Date(selectedOrder.created_at).toLocaleString()}
                  </p>
                </div>
              </div>

              {selectedOrder.delivery_address && (
                <div className="mb-6">
                  <h3 className="font-semibold mb-2 text-gray-900 dark:text-white">Delivery Information</h3>
                  <div className="text-sm text-gray-600 dark:text-gray-400">
                    {typeof selectedOrder.delivery_address === 'object' ? (
                      <>
                        <p>{selectedOrder.delivery_address.street}</p>
                        {selectedOrder.delivery_address.apartment && (
                          <p>{selectedOrder.delivery_address.apartment}</p>
                        )}
                        <p>
                          {selectedOrder.delivery_address.city}, {selectedOrder.delivery_address.province} {selectedOrder.delivery_address.postal_code}
                        </p>
                        {selectedOrder.delivery_address.instructions && (
                          <p className="mt-2 italic">Instructions: {selectedOrder.delivery_address.instructions}</p>
                        )}
                      </>
                    ) : (
                      <p>{selectedOrder.delivery_address}</p>
                    )}
                    {selectedOrder.delivery_time && (
                      <p className="mt-2">Delivery Time: {selectedOrder.delivery_time}</p>
                    )}
                  </div>
                </div>
              )}

              <div className="mb-6">
                <h3 className="font-semibold mb-2 text-gray-900 dark:text-white">Order Items</h3>
                <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                  <thead className="bg-gray-50 dark:bg-gray-700">
                    <tr>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Product</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Quantity</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Unit Price</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Total</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                    {selectedOrder.items?.map((item) => (
                      <tr key={item.id}>
                        <td className="px-4 py-2 text-sm text-gray-900 dark:text-white">{item.product?.name || 'Unknown'}</td>
                        <td className="px-4 py-2 text-sm text-gray-900 dark:text-white">{item.quantity}</td>
                        <td className="px-4 py-2 text-sm text-gray-900 dark:text-white">${(item.unit_price || 0).toFixed(2)}</td>
                        <td className="px-4 py-2 text-sm text-gray-900 dark:text-white">${(item.total_price || 0).toFixed(2)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
                <div className="flex justify-end space-y-1">
                  <div className="text-right">
                    <p className="text-sm text-gray-600 dark:text-gray-400">Subtotal: ${(selectedOrder.subtotal || 0).toFixed(2)}</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">Tax (13% HST): ${(selectedOrder.tax_amount || 0).toFixed(2)}</p>
                    {selectedOrder.delivery_fee > 0 && (
                      <p className="text-sm text-gray-600 dark:text-gray-400">Delivery: ${(selectedOrder.delivery_fee || 0).toFixed(2)}</p>
                    )}
                    {selectedOrder.discount_amount > 0 && (
                      <p className="text-sm text-gray-600 dark:text-gray-400">Discount: -${(selectedOrder.discount_amount || 0).toFixed(2)}</p>
                    )}
                    <p className="text-lg font-bold text-gray-900 dark:text-white">Total: ${(selectedOrder.total_amount || 0).toFixed(2)}</p>
                  </div>
                </div>
              </div>

              {selectedOrder.special_instructions && (
                <div className="mt-4 p-4 bg-warning-50 dark:bg-warning-900/30 rounded border border-warning-200 dark:border-warning-800">
                  <p className="text-sm font-semibold text-gray-900 dark:text-white">Special Instructions:</p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">{selectedOrder.special_instructions}</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Orders;