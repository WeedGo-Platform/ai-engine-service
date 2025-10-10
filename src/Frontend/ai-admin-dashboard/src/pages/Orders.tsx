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
        return 'bg-warning-100 text-warning-800';
      case 'confirmed':
        return 'bg-blue-100 text-blue-800';
      case 'processing':
        return 'bg-indigo-100 text-indigo-800';
      case 'ready':
        return 'bg-primary-100 text-primary-800';
      case 'out_for_delivery':
        return 'bg-accent-100 text-accent-800';
      case 'delivered':
        return 'bg-green-200 text-primary-900';
      case 'cancelled':
        return 'bg-danger-100 text-danger-800';
      default:
        return 'bg-gray-50 text-gray-800';
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
      <div className="h-full flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="mb-4">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-accent-100 rounded-full">
              <ShoppingCart className="w-8 h-8 text-accent-600" />
            </div>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No Store Selected</h3>
          <p className="text-gray-500">Please select a store to manage orders</p>
        </div>
      </div>
    );
  }

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
        Error loading orders: {(error as Error).message}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Order Management</h1>
          <p className="text-sm text-gray-500 mt-1">Managing orders for {currentStore.name}</p>
        </div>
      </div>

      <div className="bg-white rounded-lg  p-6">
        <div className="flex gap-6 mb-6">
          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-500"
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
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Order
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Customer
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Items
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Total
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Payment
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Created
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {orders?.data?.map((order: Order) => (
                <tr key={order.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      {getStatusIcon(order.status)}
                      <span className="ml-2 text-sm font-medium text-gray-900">
                        {order.order_number}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">
                      {order.customer?.first_name} {order.customer?.last_name}
                    </div>
                    <div className="text-sm text-gray-500">
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
                    <span className="text-sm text-gray-900 capitalize">
                      {order.order_type === 'pickup' ? (
                        <Package className="inline h-4 w-4 mr-1" />
                      ) : (
                        <Truck className="inline h-4 w-4 mr-1" />
                      )}
                      {order.order_type}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {order.items?.length || 0} items
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    ${order.total_amount?.toFixed(2) || '0.00'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center text-sm text-gray-900">
                      {getPaymentIcon(order.payment_method)}
                      <span className="ml-1 capitalize">{order.payment_method}</span>
                    </div>
                    <span className={`text-xs ${order.payment_status === 'paid' ? 'text-primary-600' : 'text-warning-600'}`}>
                      {order.payment_status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {new Date(order.created_at).toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button
                      onClick={() => setSelectedOrder(order)}
                      className="text-indigo-600 hover:text-indigo-900 mr-3"
                    >
                      <Eye className="h-4 w-4" />
                    </button>
                    {order.status === 'pending' && (
                      <button
                        onClick={() => handleStatusUpdate(order.id, 'confirmed')}
                        className="text-accent-600 hover:text-blue-900 mr-2"
                      >
                        Confirm
                      </button>
                    )}
                    {order.status === 'confirmed' && (
                      <button
                        onClick={() => handleStatusUpdate(order.id, 'preparing')}
                        className="text-indigo-600 hover:text-indigo-900 mr-2"
                      >
                        Prepare
                      </button>
                    )}
                    {(order.status === 'preparing' || order.status === 'processing') && (
                      <button
                        onClick={() => handleStatusUpdate(order.id, 'ready')}
                        className="text-primary-600 hover:text-primary-900 mr-2"
                      >
                        Ready
                      </button>
                    )}
                    {order.status === 'ready' && (
                      <>
                        <button
                          onClick={() => handleStatusUpdate(order.id, 'out_for_delivery')}
                          className="text-accent-600 hover:text-accent-900 mr-2"
                        >
                          Out for Delivery
                        </button>
                        <button
                          onClick={() => handleStatusUpdate(order.id, 'delivered')}
                          className="text-primary-600 hover:text-primary-900"
                        >
                          Mark Delivered
                        </button>
                      </>
                    )}
                    {order.status === 'out_for_delivery' && (
                      <button
                        onClick={() => handleStatusUpdate(order.id, 'delivered')}
                        className="text-primary-600 hover:text-primary-900"
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
            <ShoppingCart className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No orders found</h3>
            <p className="mt-1 text-sm text-gray-500">
              Orders will appear here when customers place them.
            </p>
          </div>
        )}
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg  p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Pending</p>
              <p className="text-2xl font-bold text-warning-600">
                {orders?.data?.filter((o: Order) => o.status === 'pending').length || 0}
              </p>
            </div>
            <Clock className="h-8 w-8 text-warning-600" />
          </div>
        </div>

        <div className="bg-white rounded-lg  p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Processing</p>
              <p className="text-2xl font-bold text-accent-600">
                {orders?.data?.filter((o: Order) => 
                  ['confirmed', 'processing'].includes(o.status)
                ).length || 0}
              </p>
            </div>
            <Package className="h-8 w-8 text-accent-600" />
          </div>
        </div>

        <div className="bg-white rounded-lg  p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Today's Revenue</p>
              <p className="text-2xl font-bold text-primary-600">
                ${orders?.data?.filter((o: Order) => {
                  const orderDate = new Date(o.created_at);
                  const today = new Date();
                  return orderDate.toDateString() === today.toDateString() && 
                         o.payment_status === 'paid';
                }).reduce((sum: number, o: Order) => sum + o.total_amount, 0).toFixed(2) || '0.00'}
              </p>
            </div>
            <CreditCard className="h-8 w-8 text-primary-600" />
          </div>
        </div>

        <div className="bg-white rounded-lg  p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Completed Today</p>
              <p className="text-2xl font-bold text-gray-900">
                {orders?.data?.filter((o: Order) => {
                  const orderDate = new Date(o.created_at);
                  const today = new Date();
                  return orderDate.toDateString() === today.toDateString() && 
                         o.status === 'delivered';
                }).length || 0}
              </p>
            </div>
            <CheckCircle className="h-8 w-8 text-gray-600" />
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
                  <h3 className="font-semibold mb-2">Customer Information</h3>
                  <p className="text-sm text-gray-600">
                    {selectedOrder.customer?.first_name} {selectedOrder.customer?.last_name}<br />
                    {selectedOrder.customer?.email}<br />
                    {selectedOrder.customer?.phone}<br />
                    Type: {selectedOrder.customer?.customer_type}
                  </p>
                </div>
                <div>
                  <h3 className="font-semibold mb-2">Order Information</h3>
                  <p className="text-sm text-gray-600">
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
                  <h3 className="font-semibold mb-2">Delivery Information</h3>
                  <div className="text-sm text-gray-600">
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
                <h3 className="font-semibold mb-2">Order Items</h3>
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Product</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Quantity</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Unit Price</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Total</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {selectedOrder.items?.map((item) => (
                      <tr key={item.id}>
                        <td className="px-4 py-2 text-sm">{item.product?.name || 'Unknown'}</td>
                        <td className="px-4 py-2 text-sm">{item.quantity}</td>
                        <td className="px-4 py-2 text-sm">${(item.unit_price || 0).toFixed(2)}</td>
                        <td className="px-4 py-2 text-sm">${(item.total_price || 0).toFixed(2)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="border-t pt-4">
                <div className="flex justify-end space-y-1">
                  <div className="text-right">
                    <p className="text-sm text-gray-600">Subtotal: ${(selectedOrder.subtotal || 0).toFixed(2)}</p>
                    <p className="text-sm text-gray-600">Tax (13% HST): ${(selectedOrder.tax_amount || 0).toFixed(2)}</p>
                    {selectedOrder.delivery_fee > 0 && (
                      <p className="text-sm text-gray-600">Delivery: ${(selectedOrder.delivery_fee || 0).toFixed(2)}</p>
                    )}
                    {selectedOrder.discount_amount > 0 && (
                      <p className="text-sm text-gray-600">Discount: -${(selectedOrder.discount_amount || 0).toFixed(2)}</p>
                    )}
                    <p className="text-lg font-bold">Total: ${(selectedOrder.total_amount || 0).toFixed(2)}</p>
                  </div>
                </div>
              </div>

              {selectedOrder.special_instructions && (
                <div className="mt-4 p-4 bg-warning-50 rounded">
                  <p className="text-sm font-semibold">Special Instructions:</p>
                  <p className="text-sm text-gray-600">{selectedOrder.special_instructions}</p>
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