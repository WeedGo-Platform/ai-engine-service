import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';
import { useTranslation } from 'react-i18next';
import {
  ShoppingCart, Clock, CheckCircle, XCircle, Package, Truck,
  CreditCard, Eye, Filter, Search, Calendar, Download, MessageSquare,
  User, AlertCircle, MapPin, Phone, Mail, Cannabis, Timer,
  DollarSign, TrendingUp, Users, BarChart3, Send, Camera,
  FileText, RefreshCw, Ban
} from 'lucide-react';
import { formatCurrency } from '../utils/currency';

interface Order {
  id: string;
  order_number: string;
  customer_id: string;
  customer?: Customer;
  status: 'pending' | 'confirmed' | 'preparing' | 'ready' | 'out_for_delivery' | 'delivered' | 'cancelled' | 'refunded';
  order_type: 'delivery' | 'pickup' | 'in_store';
  items: OrderItem[];
  subtotal: number;
  tax_amount: number;
  delivery_fee: number;
  discount_amount: number;
  total_amount: number;
  payment_method: 'cash' | 'credit' | 'debit' | 'e-transfer';
  payment_status: 'pending' | 'paid' | 'refunded';
  delivery_address?: string;
  delivery_time?: string;
  pickup_time?: string;
  special_instructions?: string;
  driver_id?: string;
  driver?: Driver;
  dried_flower_equivalent: number;
  age_verified: boolean;
  id_checked: boolean;
  signature_url?: string;
  delivery_photo_url?: string;
  created_at: string;
  updated_at: string;
  completed_at?: string;
  cancelled_reason?: string;
  refund_reason?: string;
}

interface OrderItem {
  id: string;
  product_id: string;
  product?: Product;
  quantity: number;
  unit_price: number;
  total_price: number;
  thc_content: number;
  cbd_content: number;
  dried_flower_equivalent: number;
}

interface Customer {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  birth_date: string;
  customer_type: 'recreational' | 'medical';
  loyalty_points?: number;
  total_orders?: number;
  verified: boolean;
}

interface Product {
  id: string;
  name: string;
  brand: string;
  category: string;
  sku: string;
}

interface Driver {
  id: string;
  name: string;
  phone: string;
  vehicle: string;
  license_plate: string;
  current_location?: { lat: number; lng: number };
  status: 'available' | 'busy' | 'offline';
}

const OrdersEnhanced: React.FC = () => {
  const { t } = useTranslation(['orders', 'common', 'errors']);
  const queryClient = useQueryClient();
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const [selectedType, setSelectedType] = useState<string>('all');
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [dateRange, setDateRange] = useState({ start: '', end: '' });
  const [showFilters, setShowFilters] = useState(false);
  const [showDriverAssignment, setShowDriverAssignment] = useState(false);
  const [selectedDriverId, setSelectedDriverId] = useState('');
  const [messageToCustomer, setMessageToCustomer] = useState('');
  const [showMessageModal, setShowMessageModal] = useState(false);

  // Fetch orders with filters
  const { data: orders, isLoading, error, refetch } = useQuery({
    queryKey: ['orders', selectedStatus, selectedType, searchTerm, dateRange],
    queryFn: async () => {
      const params: any = {};
      if (selectedStatus !== 'all') params.status = selectedStatus;
      if (selectedType !== 'all') params.order_type = selectedType;
      if (searchTerm) params.search = searchTerm;
      if (dateRange.start) params.start_date = dateRange.start;
      if (dateRange.end) params.end_date = dateRange.end;
      
      const response = await api.orders.getAll(params);
      return response.data;
    },
    refetchInterval: 30000, // Auto-refresh every 30 seconds
  });

  // Fetch available drivers
  const { data: drivers } = useQuery({
    queryKey: ['drivers'],
    queryFn: async () => {
      const response = await api.drivers.getAvailable();
      return response.data;
    },
  });

  // Update order status
  const updateMutation = useMutation({
    mutationFn: (data: { id: string; updates: Partial<Order> }) =>
      api.orders.update(data.id, data.updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['orders'] });
    },
  });

  // Assign driver
  const assignDriverMutation = useMutation({
    mutationFn: (data: { orderId: string; driverId: string }) =>
      api.orders.assignDriver(data.orderId, data.driverId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['orders'] });
      setShowDriverAssignment(false);
    },
  });

  // Send message to customer
  const sendMessageMutation = useMutation({
    mutationFn: (data: { orderId: string; message: string }) =>
      api.orders.sendMessage(data.orderId, data.message),
    onSuccess: () => {
      setShowMessageModal(false);
      setMessageToCustomer('');
    },
  });

  // Calculate metrics
  const calculateMetrics = () => {
    if (!orders?.data) return { pending: 0, preparing: 0, ready: 0, revenue: 0, avgTime: 0 };
    
    const data = orders.data;
    const today = new Date().toDateString();
    
    return {
      pending: data.filter((o: Order) => o.status === 'pending').length,
      preparing: data.filter((o: Order) => ['confirmed', 'preparing'].includes(o.status)).length,
      ready: data.filter((o: Order) => o.status === 'ready').length,
      revenue: data
        .filter((o: Order) => new Date(o.created_at).toDateString() === today && o.payment_status === 'paid')
        .reduce((sum: number, o: Order) => sum + o.total_amount, 0),
      avgTime: calculateAverageProcessingTime(data),
    };
  };

  const calculateAverageProcessingTime = (orders: Order[]) => {
    const completedOrders = orders.filter(o => o.completed_at);
    if (completedOrders.length === 0) return 0;
    
    const totalTime = completedOrders.reduce((sum, order) => {
      const created = new Date(order.created_at).getTime();
      const completed = new Date(order.completed_at!).getTime();
      return sum + (completed - created);
    }, 0);
    
    return Math.round(totalTime / completedOrders.length / 60000); // Return in minutes
  };

  const getStatusIcon = (status: string) => {
    const icons: { [key: string]: JSX.Element } = {
      pending: <Clock className="h-5 w-5 text-yellow-500" />,
      confirmed: <CheckCircle className="h-5 w-5 text-accent-500" />,
      preparing: <Package className="h-5 w-5 text-indigo-500" />,
      ready: <Timer className="h-5 w-5 text-primary-500" />,
      out_for_delivery: <Truck className="h-5 w-5 text-purple-500" />,
      delivered: <CheckCircle className="h-5 w-5 text-primary-600" />,
      cancelled: <XCircle className="h-5 w-5 text-red-500" />,
      refunded: <RefreshCw className="h-5 w-5 text-orange-500" />,
    };
    return icons[status] || <ShoppingCart className="h-5 w-5 text-gray-500" />;
  };

  const getStatusColor = (status: string) => {
    const colors: { [key: string]: string } = {
      pending: 'bg-warning-100 text-warning-800',
      confirmed: 'bg-blue-100 text-blue-800',
      preparing: 'bg-indigo-100 text-indigo-800',
      ready: 'bg-primary-100 text-primary-800',
      out_for_delivery: 'bg-purple-100 text-purple-800',
      delivered: 'bg-green-200 text-primary-900',
      cancelled: 'bg-danger-100 text-danger-800',
      refunded: 'bg-orange-100 text-orange-800',
    };
    return colors[status] || 'bg-gray-50 text-gray-800';
  };

  const handleStatusUpdate = (orderId: string, newStatus: string) => {
    updateMutation.mutate({
      id: orderId,
      updates: { status: newStatus as Order['status'] },
    });
  };

  const handleVerifyAge = (orderId: string) => {
    updateMutation.mutate({
      id: orderId,
      updates: { age_verified: true, id_checked: true },
    });
  };

  const handleCancelOrder = (order: Order) => {
    const reason = prompt(t('orders:prompts.cancelReason'));
    if (reason) {
      updateMutation.mutate({
        id: order.id,
        updates: {
          status: 'cancelled',
          cancelled_reason: reason,
        },
      });
    }
  };

  const handleRefund = (order: Order) => {
    const reason = prompt(t('orders:prompts.refundReason'));
    if (reason) {
      updateMutation.mutate({
        id: order.id,
        updates: {
          status: 'refunded',
          payment_status: 'refunded',
          refund_reason: reason,
        },
      });
    }
  };

  const exportOrders = () => {
    const csv = orders?.data?.map((order: Order) => ({
      'Order Number': order.order_number,
      'Customer': `${order.customer?.first_name} ${order.customer?.last_name}`,
      'Status': order.status,
      'Type': order.order_type,
      'Total': order.total_amount,
      'Date': new Date(order.created_at).toLocaleString(),
    }));

    // Convert to CSV and download
    console.log('Exporting orders:', csv);
    alert(t('orders:messages.exportMessage'));
  };

  const metrics = calculateMetrics();

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
        {t('orders:messages.loadingError')} {(error as Error).message}
      </div>
    );
  }

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 sm:gap-0">
        <h1 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white">{t('orders:titles.management')}</h1>
        <div className="flex gap-2 w-full sm:w-auto">
          <button
            onClick={() => refetch()}
            className="p-2 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 active:scale-95 transition-all touch-manipulation"
            title={t('orders:actions.refresh')}
            aria-label="Refresh orders"
          >
            <RefreshCw className="h-4 h-4 sm:h-5 sm:w-5 dark:text-gray-300" />
          </button>
          <button
            onClick={exportOrders}
            className="flex-1 sm:flex-none px-4 py-2 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 flex items-center justify-center gap-2 active:scale-95 transition-all touch-manipulation"
          >
            <Download className="h-4 h-4 sm:h-5 sm:w-5 dark:text-gray-300" />
            <span className="text-sm dark:text-gray-200">{t('orders:actions.export')}</span>
          </button>
        </div>
      </div>

      {/* Metrics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 sm:gap-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 sm:p-6 border border-gray-200 dark:border-gray-700 transition-colors">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-gray-600 dark:text-gray-400">{t('orders:metrics.pending')}</p>
              <p className="text-xl sm:text-2xl font-bold text-warning-600 dark:text-warning-400">{metrics.pending}</p>
            </div>
            <Clock className="w-6 h-6 sm:h-8 sm:w-8 text-warning-600 dark:text-warning-400 opacity-20" />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 sm:p-6 border border-gray-200 dark:border-gray-700 transition-colors">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-gray-600 dark:text-gray-400">{t('orders:metrics.preparing')}</p>
              <p className="text-xl sm:text-2xl font-bold text-accent-600 dark:text-accent-400">{metrics.preparing}</p>
            </div>
            <Package className="w-6 h-6 sm:h-8 sm:w-8 text-accent-600 dark:text-accent-400 opacity-20" />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 sm:p-6 border border-gray-200 dark:border-gray-700 transition-colors">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-gray-600 dark:text-gray-400">{t('orders:metrics.ready')}</p>
              <p className="text-xl sm:text-2xl font-bold text-primary-600 dark:text-primary-400">{metrics.ready}</p>
            </div>
            <CheckCircle className="w-6 h-6 sm:h-8 sm:w-8 text-primary-600 dark:text-primary-400 opacity-20" />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 sm:p-6 border border-gray-200 dark:border-gray-700 transition-colors">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-gray-600 dark:text-gray-400">{t('orders:metrics.todayRevenue')}</p>
              <p className="text-base sm:text-xl font-bold text-primary-600 dark:text-primary-400">{formatCurrency(metrics.revenue || 0)}</p>
            </div>
            <DollarSign className="w-6 h-6 sm:h-8 sm:w-8 text-primary-600 dark:text-primary-400 opacity-20" />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 sm:p-6 border border-gray-200 dark:border-gray-700 transition-colors">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-gray-600 dark:text-gray-400">{t('orders:metrics.avgProcessTime')}</p>
              <p className="text-base sm:text-xl font-bold text-gray-700 dark:text-gray-200">{metrics.avgTime} {t('orders:messages.min')}</p>
            </div>
            <Timer className="w-6 h-6 sm:h-8 sm:w-8 text-gray-600 dark:text-gray-400 opacity-20" />
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white dark:bg-gray-800 rounded-lg p-4 sm:p-6 border border-gray-200 dark:border-gray-700 transition-colors">
        <div className="flex flex-col sm:flex-row sm:flex-wrap gap-3 sm:gap-6 sm:items-center">
          {/* Search */}
          <div className="flex-1 min-w-full sm:min-w-[200px] relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 dark:text-gray-500 h-4 h-4 sm:h-5 sm:w-5" />
            <input
              type="text"
              placeholder={t('orders:messages.searchPlaceholder')}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 text-sm border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white transition-colors"
            />
          </div>

          {/* Status Filter */}
          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="w-full sm:w-auto px-4 py-2 text-sm border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white transition-colors"
          >
            <option value="all">{t('orders:status.all')}</option>
            <option value="pending">{t('orders:status.pending')}</option>
            <option value="confirmed">{t('orders:status.confirmed')}</option>
            <option value="preparing">{t('orders:status.preparing')}</option>
            <option value="ready">{t('orders:status.ready')}</option>
            <option value="out_for_delivery">{t('orders:status.outForDelivery')}</option>
            <option value="delivered">{t('orders:status.delivered')}</option>
            <option value="cancelled">{t('orders:status.cancelled')}</option>
            <option value="refunded">{t('orders:status.refunded')}</option>
          </select>

          {/* Type Filter */}
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="w-full sm:w-auto px-4 py-2 text-sm border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white transition-colors"
          >
            <option value="all">{t('orders:orderTypes.all')}</option>
            <option value="delivery">{t('orders:orderTypes.delivery')}</option>
            <option value="pickup">{t('orders:orderTypes.pickup')}</option>
            <option value="in_store">{t('orders:orderTypes.inStore')}</option>
          </select>

          {/* Date Range */}
          <div className="flex items-center gap-2 w-full sm:w-auto">
            <input
              type="date"
              value={dateRange.start}
              onChange={(e) => setDateRange({ ...dateRange, start: e.target.value })}
              className="flex-1 sm:flex-none px-4 py-2 text-sm border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white transition-colors"
            />
            <span className="text-sm text-gray-500 dark:text-gray-400">{t('orders:messages.to')}</span>
            <input
              type="date"
              value={dateRange.end}
              onChange={(e) => setDateRange({ ...dateRange, end: e.target.value })}
              className="flex-1 sm:flex-none px-4 py-2 text-sm border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white transition-colors"
            />
          </div>

          <button
            onClick={() => setShowFilters(!showFilters)}
            className="p-2 bg-gray-50 dark:bg-gray-700 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600 active:scale-95 transition-all touch-manipulation"
            aria-label="Toggle filters"
          >
            <Filter className="h-4 h-4 sm:h-5 sm:w-5 dark:text-gray-300" />
          </button>
        </div>
      </div>

      {/* Orders Table */}
      <div className="bg-white dark:bg-gray-800 rounded-lg overflow-hidden border border-gray-200 dark:border-gray-700 transition-colors">
        <div className="overflow-x-auto">
          <div className="inline-block min-w-full align-middle">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-700">
                <tr>
                  <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    {t('orders:fields.orderNumber')}
                  </th>
                  <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    {t('orders:fields.customer')}
                  </th>
                  <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    {t('orders:fields.status')}
                  </th>
                  <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    {t('orders:fields.type')}
                  </th>
                  <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    {t('orders:fields.items')}
                  </th>
                  <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    {t('orders:fields.cannabis')}
                  </th>
                  <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    {t('orders:fields.total')}
                  </th>
                  <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    {t('orders:fields.verification')}
                  </th>
                  <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    {t('orders:fields.time')}
                  </th>
                  <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    {t('orders:fields.actions')}
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
              {orders?.data?.map((order: Order) => (
                <tr key={order.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      {getStatusIcon(order.status)}
                      <div className="ml-2">
                        <span className="text-sm font-medium text-gray-900">
                          {order.order_number}
                        </span>
                        {order.payment_status === 'pending' && (
                          <span className="ml-2 text-xs text-warning-600">Payment Pending</span>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm">
                      <div className="font-medium text-gray-900">
                        {order.customer?.first_name} {order.customer?.last_name}
                      </div>
                      <div className="text-gray-500">{order.customer?.phone}</div>
                      {order.customer?.customer_type === 'medical' && (
                        <span className="inline-flex px-2 py-1 text-xs rounded-full bg-purple-100 text-purple-800">
                          Medical
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusColor(order.status)}`}>
                      {order.status.replace('_', ' ')}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center text-sm">
                      {order.order_type === 'delivery' ? (
                        <>
                          <Truck className="h-4 w-4 mr-1" />
                          {order.driver && (
                            <span className="text-xs text-gray-500 ml-1">({order.driver.name})</span>
                          )}
                        </>
                      ) : order.order_type === 'pickup' ? (
                        <Package className="h-4 w-4 mr-1" />
                      ) : (
                        <ShoppingCart className="h-4 w-4 mr-1" />
                      )}
                      <span className="capitalize">{order.order_type}</span>
                    </div>
                    {order.delivery_time && (
                      <div className="text-xs text-gray-500">{order.delivery_time}</div>
                    )}
                    {order.pickup_time && (
                      <div className="text-xs text-gray-500">{order.pickup_time}</div>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {order.items?.length || 0} items
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center text-sm">
                      <Cannabis className="h-4 w-4 mr-1 text-primary-600" />
                      <span className={order.dried_flower_equivalent > 30 ? 'text-danger-600 font-bold' : ''}>
                        {order.dried_flower_equivalent?.toFixed(1) || 0}g
                      </span>
                      {order.dried_flower_equivalent > 30 && (
                        <AlertCircle className="h-4 w-4 ml-1 text-danger-600" />
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">
                                          <span className="text-sm font-medium text-gray-900 dark:text-white">
                      {formatCurrency(order.total_amount || 0)}
                    </span>
                    </div>
                    <div className="text-xs text-gray-500">{order.payment_method}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center gap-2">
                      {order.age_verified ? (
                        <CheckCircle className="h-4 w-4 text-primary-500" />
                      ) : (
                        <AlertCircle className="h-4 w-4 text-yellow-500" />
                      )}
                      {order.id_checked ? (
                        <span className="text-xs text-primary-600">ID ✓</span>
                      ) : (
                        <span className="text-xs text-gray-400">No ID</span>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(order.created_at).toLocaleTimeString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => setSelectedOrder(order)}
                        className="text-indigo-600 hover:text-indigo-900"
                        title="View Details"
                      >
                        <Eye className="h-4 w-4" />
                      </button>

                      {/* Status Actions */}
                      {order.status === 'pending' && (
                        <>
                          <button
                            onClick={() => handleStatusUpdate(order.id, 'confirmed')}
                            className="text-accent-600 hover:text-blue-900"
                            title="Confirm Order"
                          >
                            <CheckCircle className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => handleCancelOrder(order)}
                            className="text-danger-600 hover:text-red-900"
                            title="Cancel Order"
                          >
                            <Ban className="h-4 w-4" />
                          </button>
                        </>
                      )}
                      
                      {order.status === 'confirmed' && (
                        <button
                          onClick={() => handleStatusUpdate(order.id, 'preparing')}
                          className="text-indigo-600 hover:text-indigo-900"
                          title="Start Preparing"
                        >
                          <Package className="h-4 w-4" />
                        </button>
                      )}
                      
                      {order.status === 'preparing' && (
                        <button
                          onClick={() => handleStatusUpdate(order.id, 'ready')}
                          className="text-primary-600 hover:text-primary-900"
                          title="Mark Ready"
                        >
                          <CheckCircle className="h-4 w-4" />
                        </button>
                      )}
                      
                      {order.status === 'ready' && order.order_type === 'delivery' && (
                        <button
                          onClick={() => {
                            setSelectedOrder(order);
                            setShowDriverAssignment(true);
                          }}
                          className="text-purple-600 hover:text-purple-900"
                          title="Assign Driver"
                        >
                          <Truck className="h-4 w-4" />
                        </button>
                      )}
                      
                      {order.status === 'ready' && order.order_type === 'pickup' && (
                        <button
                          onClick={() => handleStatusUpdate(order.id, 'delivered')}
                          className="text-primary-600 hover:text-primary-900"
                          title="Mark Picked Up"
                        >
                          <CheckCircle className="h-4 w-4" />
                        </button>
                      )}
                      
                      {order.status === 'out_for_delivery' && (
                        <button
                          onClick={() => handleStatusUpdate(order.id, 'delivered')}
                          className="text-primary-600 hover:text-primary-900"
                          title="Mark Delivered"
                        >
                          <CheckCircle className="h-4 w-4" />
                        </button>
                      )}

                      {/* Age Verification */}
                      {!order.age_verified && (
                        <button
                          onClick={() => handleVerifyAge(order.id)}
                          className="text-warning-600 hover:text-yellow-900"
                          title="Verify Age & ID"
                        >
                          <User className="h-4 w-4" />
                        </button>
                      )}

                      {/* Message Customer */}
                      <button
                        onClick={() => {
                          setSelectedOrder(order);
                          setShowMessageModal(true);
                        }}
                        className="text-gray-600 hover:text-gray-900"
                        title="Message Customer"
                      >
                        <MessageSquare className="h-4 w-4" />
                      </button>

                      {/* Refund */}
                      {order.status === 'delivered' && order.payment_status === 'paid' && (
                        <button
                          onClick={() => handleRefund(order)}
                          className="text-orange-600 hover:text-orange-900"
                          title="Process Refund"
                        >
                          <RefreshCw className="h-4 w-4" />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
            </table>
          </div>
        </div>

        {(!orders?.data || orders.data.length === 0) && (
          <div className="text-center py-12">
            <ShoppingCart className="mx-auto h-12 w-12 text-gray-400 dark:text-gray-500" />
            <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">{t('orders:messages.noOrders')}</h3>
            <p className="mt-1 text-sm text-gray-500">
              {t('orders:messages.ordersWillAppear')}
            </p>
          </div>
        )}
      </div>

      {/* Order Details Modal */}
      {selectedOrder && !showDriverAssignment && !showMessageModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-6 z-50">
          <div className="bg-white rounded-lg max-w-5xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-center mb-6">
                <div>
                  <h2 className="text-xl font-bold">Order {selectedOrder.order_number}</h2>
                  <p className="text-sm text-gray-500">{new Date(selectedOrder.created_at).toLocaleString()}</p>
                </div>
                <button
                  onClick={() => setSelectedOrder(null)}
                  className="text-gray-500 hover:text-gray-700"
                >
                  <XCircle className="h-6 w-6" />
                </button>
              </div>

              <div className="grid grid-cols-3 gap-6 mb-6">
                {/* Customer Info */}
                <div className="bg-gray-50 p-6 rounded-lg">
                  <h3 className="font-semibold mb-3 flex items-center gap-2">
                    <User className="h-5 w-5" />
                    Customer Information
                  </h3>
                  <div className="space-y-2 text-sm">
                    <p>
                      <span className="font-medium">{selectedOrder.customer?.first_name} {selectedOrder.customer?.last_name}</span>
                      {selectedOrder.customer?.customer_type === 'medical' && (
                        <span className="ml-2 px-2 py-1 text-xs bg-purple-100 text-purple-800 rounded">Medical</span>
                      )}
                    </p>
                    <p className="flex items-center gap-2">
                      <Phone className="h-4 w-4" />
                      {selectedOrder.customer?.phone}
                    </p>
                    <p className="flex items-center gap-2">
                      <Mail className="h-4 w-4" />
                      {selectedOrder.customer?.email}
                    </p>
                    <p className="flex items-center gap-2">
                      <Calendar className="h-4 w-4" />
                      DOB: {selectedOrder.customer?.birth_date}
                    </p>
                    {selectedOrder.customer?.loyalty_points && (
                      <p>Loyalty Points: {selectedOrder.customer.loyalty_points}</p>
                    )}
                  </div>
                </div>

                {/* Order Info */}
                <div className="bg-gray-50 p-6 rounded-lg">
                  <h3 className="font-semibold mb-3 flex items-center gap-2">
                    <Package className="h-5 w-5" />
                    Order Information
                  </h3>
                  <div className="space-y-2 text-sm">
                    <p>
                      Status: <span className={`px-2 py-1 rounded ${getStatusColor(selectedOrder.status)}`}>
                        {selectedOrder.status}
                      </span>
                    </p>
                    <p>Type: <span className="capitalize">{selectedOrder.order_type}</span></p>
                    <p>Payment: {selectedOrder.payment_method} ({selectedOrder.payment_status})</p>
                    <p className="flex items-center gap-2">
                      <Cannabis className="h-4 w-4" />
                      Dried Flower Eq: 
                      <span className={selectedOrder.dried_flower_equivalent > 30 ? 'text-danger-600 font-bold' : ''}>
                        {selectedOrder.dried_flower_equivalent}g
                      </span>
                    </p>
                    <div className="flex items-center gap-2">
                      {selectedOrder.age_verified ? (
                        <>
                          <CheckCircle className="h-4 w-4 text-primary-500" />
                          <span className="text-primary-600">Age Verified</span>
                        </>
                      ) : (
                        <>
                          <AlertCircle className="h-4 w-4 text-yellow-500" />
                          <span className="text-warning-600">Age Not Verified</span>
                        </>
                      )}
                    </div>
                  </div>
                </div>

                {/* Delivery/Pickup Info */}
                <div className="bg-gray-50 p-6 rounded-lg">
                  <h3 className="font-semibold mb-3 flex items-center gap-2">
                    {selectedOrder.order_type === 'delivery' ? (
                      <Truck className="h-5 w-5" />
                    ) : (
                      <MapPin className="h-5 w-5" />
                    )}
                    {selectedOrder.order_type === 'delivery' ? 'Delivery' : 'Pickup'} Information
                  </h3>
                  <div className="space-y-2 text-sm">
                    {selectedOrder.delivery_address && (
                      <p className="flex items-start gap-2">
                        <MapPin className="h-4 w-4 mt-0.5" />
                        <span>{selectedOrder.delivery_address}</span>
                      </p>
                    )}
                    {selectedOrder.delivery_time && (
                      <p>Delivery Time: {selectedOrder.delivery_time}</p>
                    )}
                    {selectedOrder.pickup_time && (
                      <p>Pickup Time: {selectedOrder.pickup_time}</p>
                    )}
                    {selectedOrder.driver && (
                      <div className="mt-2 pt-2 border-t">
                        <p className="font-medium">Driver: {selectedOrder.driver.name}</p>
                        <p>Vehicle: {selectedOrder.driver.vehicle}</p>
                        <p>Phone: {selectedOrder.driver.phone}</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Special Instructions */}
              {selectedOrder.special_instructions && (
                <div className="mb-6 p-6 bg-warning-50 border border-yellow-200 rounded-lg">
                  <h3 className="font-semibold mb-2 text-warning-800">Special Instructions</h3>
                  <p className="text-sm text-yellow-700">{selectedOrder.special_instructions}</p>
                </div>
              )}

              {/* Order Items */}
              <div className="mb-6">
                <h3 className="font-semibold mb-3">Order Items</h3>
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Product</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Brand</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Category</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">THC/CBD</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Qty</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Price</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Total</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {selectedOrder.items?.map((item) => (
                      <tr key={item.id}>
                        <td className="px-4 py-2 text-sm">{item.product?.name || 'Unknown'}</td>
                        <td className="px-4 py-2 text-sm">{item.product?.brand}</td>
                        <td className="px-4 py-2 text-sm">{item.product?.category}</td>
                        <td className="px-4 py-2 text-sm">
                          {item.thc_content}% / {item.cbd_content}%
                        </td>
                        <td className="px-4 py-2 text-sm">{item.quantity}</td>
                        <td className="px-4 py-2 text-sm">{formatCurrency(item.unit_price || 0)}</td>
                        <td className="px-4 py-2 text-sm font-medium">{formatCurrency(item.total_price || 0)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Order Summary */}
              <div className="border-t pt-4">
                <div className="flex justify-end">
                  <div className="w-64">
                    <div className="flex justify-between py-1">
                      <span className="text-sm text-gray-600">Subtotal:</span>
                      <span className="text-sm">{formatCurrency(selectedOrder.subtotal || 0)}</span>
                    </div>
                    <div className="flex justify-between py-1">
                      <span className="text-sm text-gray-600">Tax (13% HST):</span>
                      <span className="text-sm">{formatCurrency(selectedOrder.tax_amount || 0)}</span>
                    </div>
                    {selectedOrder.delivery_fee > 0 && (
                      <div className="flex justify-between py-1">
                        <span className="text-sm text-gray-600">Delivery:</span>
                        <span className="text-sm">${(selectedOrder.delivery_fee || 0).toFixed(2)}</span>
                      </div>
                    )}
                    {selectedOrder.discount_amount > 0 && (
                      <div className="flex justify-between py-1">
                        <span className="text-sm text-gray-600">Discount:</span>
                        <span className="text-sm text-danger-600">-${(selectedOrder.discount_amount || 0).toFixed(2)}</span>
                      </div>
                    )}
                    <div className="flex justify-between py-2 border-t font-bold">
                      <span>Total:</span>
                      <span>${(selectedOrder.total_amount || 0).toFixed(2)}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Delivery Proof */}
              {(selectedOrder.signature_url || selectedOrder.delivery_photo_url) && (
                <div className="mt-6 pt-6 border-t">
                  <h3 className="font-semibold mb-3">Delivery Confirmation</h3>
                  <div className="grid grid-cols-2 gap-6">
                    {selectedOrder.signature_url && (
                      <div>
                        <p className="text-sm text-gray-600 mb-2">Customer Signature</p>
                        <img src={selectedOrder.signature_url} alt="Signature" className="border rounded" />
                      </div>
                    )}
                    {selectedOrder.delivery_photo_url && (
                      <div>
                        <p className="text-sm text-gray-600 mb-2">Delivery Photo</p>
                        <img src={selectedOrder.delivery_photo_url} alt="Delivery" className="border rounded" />
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Driver Assignment Modal */}
      {showDriverAssignment && selectedOrder && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-6 z-50">
          <div className="bg-white rounded-lg max-w-md w-full">
            <div className="p-6">
              <h3 className="text-lg font-semibold mb-4">Assign Driver</h3>
              <p className="text-sm text-gray-600 mb-4">
                Assign a driver for order {selectedOrder.order_number}
              </p>
              
              <select
                value={selectedDriverId}
                onChange={(e) => setSelectedDriverId(e.target.value)}
                className="w-full px-4 py-2 border rounded-lg mb-4"
              >
                <option value="">Select a driver...</option>
                {drivers?.map((driver: Driver) => (
                  <option key={driver.id} value={driver.id}>
                    {driver.name} - {driver.vehicle} ({driver.status})
                  </option>
                ))}
              </select>

              <div className="flex justify-end gap-2">
                <button
                  onClick={() => {
                    setShowDriverAssignment(false);
                    setSelectedDriverId('');
                  }}
                  className="px-4 py-2 text-gray-600 hover:text-gray-800"
                >
                  Cancel
                </button>
                <button
                  onClick={() => {
                    if (selectedDriverId) {
                      assignDriverMutation.mutate({
                        orderId: selectedOrder.id,
                        driverId: selectedDriverId,
                      });
                      handleStatusUpdate(selectedOrder.id, 'out_for_delivery');
                    }
                  }}
                  disabled={!selectedDriverId}
                  className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-gray-300"
                >
                  Assign & Dispatch
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Message Customer Modal */}
      {showMessageModal && selectedOrder && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-6 z-50">
          <div className="bg-white rounded-lg max-w-md w-full">
            <div className="p-6">
              <h3 className="text-lg font-semibold mb-4">Message Customer</h3>
              <p className="text-sm text-gray-600 mb-4">
                Send a message to {selectedOrder.customer?.first_name} {selectedOrder.customer?.last_name}
              </p>
              
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Quick Templates
                </label>
                <select
                  onChange={(e) => setMessageToCustomer(e.target.value)}
                  className="w-full px-4 py-2 border rounded-lg mb-2"
                >
                  <option value="">Select a template...</option>
                  <option value="Your order is confirmed and being prepared.">Order Confirmed</option>
                  <option value="Your order is ready for pickup!">Ready for Pickup</option>
                  <option value="Your order is out for delivery.">Out for Delivery</option>
                  <option value="There's a delay with your order. We apologize for the inconvenience.">Delay Notice</option>
                </select>
              </div>

              <textarea
                value={messageToCustomer}
                onChange={(e) => setMessageToCustomer(e.target.value)}
                placeholder="Type your message..."
                className="w-full px-4 py-2 border rounded-lg h-32 mb-4"
              />

              <div className="flex justify-end gap-2">
                <button
                  onClick={() => {
                    setShowMessageModal(false);
                    setMessageToCustomer('');
                  }}
                  className="px-4 py-2 text-gray-600 hover:text-gray-800"
                >
                  Cancel
                </button>
                <button
                  onClick={() => {
                    if (messageToCustomer) {
                      sendMessageMutation.mutate({
                        orderId: selectedOrder.id,
                        message: messageToCustomer,
                      });
                    }
                  }}
                  disabled={!messageToCustomer}
                  className="px-4 py-2 bg-accent-600 text-white rounded-lg hover:bg-accent-700 disabled:bg-gray-300 flex items-center gap-2"
                >
                  <Send className="h-4 w-4" />
                  Send Message
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default OrdersEnhanced;