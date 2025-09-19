import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';
import { 
  TrendingUp, TrendingDown, DollarSign, ShoppingCart, 
  Users, Package, AlertTriangle, Activity, 
  Clock, CheckCircle, Truck, Calendar,
  Building2, Store
} from 'lucide-react';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { useAuth } from '../contexts/AuthContext';
import { useStoreContext } from '../contexts/StoreContext';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const Dashboard: React.FC = () => {
  const { user, isSuperAdmin, isTenantAdmin } = useAuth();
  const { currentStore, stores, inventoryStats } = useStoreContext();

  // Fetch store-specific or system-wide stats based on role
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['dashboard-stats', currentStore?.id, user?.user_id],
    queryFn: async () => {
      const headers: any = { 'Content-Type': 'application/json' };
      if (currentStore) {
        headers['X-Store-ID'] = currentStore.id;
      }

      const response = await fetch(`http://localhost:5024/api/analytics/dashboard`, {
        headers
      });

      if (!response.ok) {
        // Fallback data if endpoint doesn't exist
        return {
          revenue: { total: 0, trend: 0 },
          orders: { total: 0, trend: 0 },
          customers: { total: 0, trend: 0 },
          inventory: { total: 0, low_stock: 0 }
        };
      }

      return response.json();
    },
  });

  const { data: orders } = useQuery({
    queryKey: ['recent-orders', currentStore?.id],
    queryFn: async () => {
      if (!currentStore) return { orders: [] };
      
      const response = await fetch(`http://localhost:5024/api/orders?limit=10`, {
        headers: {
          'Content-Type': 'application/json',
          'X-Store-ID': currentStore.id
        }
      });

      if (!response.ok) {
        return { orders: [] };
      }

      return response.json();
    },
    enabled: !!currentStore
  });

  const { data: inventory } = useQuery({
    queryKey: ['inventory-alerts', currentStore?.id],
    queryFn: async () => {
      if (!currentStore) return { items: [] };

      const response = await fetch(`http://localhost:5024/api/store-inventory/low-stock`, {
        headers: {
          'Content-Type': 'application/json',
          'X-Store-ID': currentStore.id
        }
      });

      if (!response.ok) {
        return { items: [] };
      }

      return response.json();
    },
    enabled: !!currentStore
  });

  if (statsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  // Use actual revenue chart data from API
  const revenueChartData = stats?.revenue?.chart_data || [];
  const revenueData = {
    labels: revenueChartData.slice(-7).map((d: any) => {
      const date = new Date(d.date);
      return date.toLocaleDateString('en-US', { weekday: 'short' });
    }),
    datasets: [
      {
        label: 'Revenue',
        data: revenueChartData.slice(-7).map((d: any) => d.revenue || 0),
        borderColor: 'rgb(34, 197, 94)',
        backgroundColor: 'rgba(34, 197, 94, 0.1)',
        tension: 0.4,
        fill: true,
      },
    ],
  };

  // Use actual sales by category data from API
  const salesByCategory = stats?.sales_by_category || {};
  const hasCategories = Object.keys(salesByCategory).length > 0;
  const categoryData = {
    labels: hasCategories ? Object.keys(salesByCategory) : ['No Data'],
    datasets: [
      {
        data: hasCategories ? Object.values(salesByCategory) : [100],
        backgroundColor: hasCategories ? [
          'rgba(34, 197, 94, 0.8)',
          'rgba(168, 85, 247, 0.8)',
          'rgba(251, 146, 60, 0.8)',
          'rgba(59, 130, 246, 0.8)',
          'rgba(239, 68, 68, 0.8)',
        ] : ['rgba(200, 200, 200, 0.3)'],
      },
    ],
  };

  // Use actual order status data from API (or recent orders)
  const recentOrders = stats?.orders?.recent || [];
  const orderStatusCounts = recentOrders.reduce((acc: any, order: any) => {
    const status = order.status || 'pending';
    acc[status] = (acc[status] || 0) + 1;
    return acc;
  }, {});
  
  const orderStatusData = {
    labels: Object.keys(orderStatusCounts),
    datasets: [
      {
        label: 'Orders',
        data: Object.values(orderStatusCounts),
        backgroundColor: 'rgba(59, 130, 246, 0.8)',
      },
    ],
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            {currentStore ? `${currentStore.name} Dashboard` : 'System Dashboard'}
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            {isSuperAdmin() ? 'System-wide overview' : 
             isTenantAdmin() ? 'Tenant overview' : 
             'Store performance metrics'}
          </p>
        </div>
        <div className="flex items-center gap-6">
          {isSuperAdmin() && (
            <div className="bg-purple-50 px-4 py-2 rounded-lg">
              <div className="flex items-center gap-2">
                <Building2 className="h-5 w-5 text-purple-600" />
                <span className="text-sm font-medium text-purple-900">
                  {stores.length} Active Stores
                </span>
              </div>
            </div>
          )}
          <div className="text-right">
            <p className="text-sm text-gray-500">Today</p>
            <p className="text-lg font-semibold">{new Date().toLocaleDateString()}</p>
          </div>
        </div>
      </div>

      {/* No Store Selected Warning */}
      {!currentStore && !isSuperAdmin() && (
        <div className="bg-warning-50 border border-yellow-200 rounded-lg p-6">
          <div className="flex items-center">
            <AlertTriangle className="h-5 w-5 text-warning-600 mr-2" />
            <p className="text-sm text-warning-800">
              Please select a store from the dropdown above to view detailed metrics.
            </p>
          </div>
        </div>
      )}

      {/* Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg  p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Revenue</p>
              <p className="text-2xl font-bold text-gray-900">
                ${stats?.revenue?.total?.toLocaleString() || '0'}
              </p>
              <div className="flex items-center mt-2">
                {(stats?.revenue?.trend || 0) > 0 ? (
                  <>
                    <TrendingUp className="h-4 w-4 text-primary-500 mr-1" />
                    <span className="text-sm text-primary-600">
                      +{stats?.revenue?.trend || 0}%
                    </span>
                  </>
                ) : (
                  <>
                    <TrendingDown className="h-4 w-4 text-red-500 mr-1" />
                    <span className="text-sm text-danger-600">
                      {stats?.revenue?.trend || 0}%
                    </span>
                  </>
                )}
                <span className="text-sm text-gray-500 ml-2">vs last week</span>
              </div>
            </div>
            <DollarSign className="h-8 w-8 text-primary-600" />
          </div>
        </div>

        <div className="bg-white rounded-lg  p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Orders</p>
              <p className="text-2xl font-bold text-gray-900">
                {stats?.orders?.total || 0}
              </p>
              <div className="flex items-center mt-2">
                {(stats?.orders?.trend || 0) > 0 ? (
                  <>
                    <TrendingUp className="h-4 w-4 text-primary-500 mr-1" />
                    <span className="text-sm text-primary-600">
                      +{stats?.orders?.trend || 0}%
                    </span>
                  </>
                ) : (
                  <>
                    <TrendingDown className="h-4 w-4 text-red-500 mr-1" />
                    <span className="text-sm text-danger-600">
                      {stats?.orders?.trend || 0}%
                    </span>
                  </>
                )}
                <span className="text-sm text-gray-500 ml-2">vs last week</span>
              </div>
            </div>
            <ShoppingCart className="h-8 w-8 text-accent-600" />
          </div>
        </div>

        <div className="bg-white rounded-lg  p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Active Customers</p>
              <p className="text-2xl font-bold text-gray-900">
                {stats?.customers?.total || 0}
              </p>
              <div className="flex items-center mt-2">
                <span className="text-sm text-gray-500">
                  {stats?.customers?.new || 0} new this week
                </span>
              </div>
            </div>
            <Users className="h-8 w-8 text-purple-600" />
          </div>
        </div>

        <div className="bg-white rounded-lg  p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Inventory Items</p>
              <p className="text-2xl font-bold text-gray-900">
                {inventoryStats?.total_skus || stats?.inventory?.total || 0}
              </p>
              <div className="flex items-center mt-2">
                <AlertTriangle className="h-4 w-4 text-yellow-500 mr-1" />
                <span className="text-sm text-warning-600">
                  {inventoryStats?.low_stock_items || stats?.inventory?.low_stock || 0} low stock
                </span>
              </div>
            </div>
            <Package className="h-8 w-8 text-orange-600" />
          </div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg  p-6">
          <h3 className="text-lg font-semibold mb-4">Revenue Trend</h3>
          <div style={{ height: '300px', position: 'relative' }}>
            <Line 
              data={revenueData} 
              options={{ 
                responsive: true, 
                maintainAspectRatio: false,
                scales: {
                  y: {
                    beginAtZero: true,
                    min: 0
                  }
                }
              }} 
            />
          </div>
        </div>

        <div className="bg-white rounded-lg  p-6">
          <h3 className="text-lg font-semibold mb-4">Sales by Category</h3>
          <div style={{ height: '300px', position: 'relative' }}>
            <Doughnut 
              data={categoryData} 
              options={{ 
                responsive: true, 
                maintainAspectRatio: false,
                plugins: {
                  legend: {
                    position: 'bottom'
                  }
                }
              }} 
            />
          </div>
        </div>
      </div>

      {/* Additional Charts for Admin Users */}
      {(isSuperAdmin() || isTenantAdmin()) && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white rounded-lg  p-6">
            <h3 className="text-lg font-semibold mb-4">Order Status Distribution</h3>
            <div style={{ height: '300px', position: 'relative' }}>
              <Bar 
                data={orderStatusData} 
                options={{ 
                  responsive: true, 
                  maintainAspectRatio: false,
                  scales: {
                    y: {
                      beginAtZero: true,
                      min: 0
                    }
                  }
                }} 
              />
            </div>
          </div>

          <div className="bg-white rounded-lg  p-6">
            <h3 className="text-lg font-semibold mb-4">Store Performance</h3>
            <div className="space-y-4">
              {stores.slice(0, 5).map((store) => (
                <div key={store.id} className="flex items-center justify-between">
                  <div className="flex items-center">
                    <Store className="h-5 w-5 text-gray-400 mr-2" />
                    <span className="text-sm font-medium">{store.name}</span>
                  </div>
                  <div className="flex items-center gap-6">
                    <span className="text-sm text-gray-500">
                      ${store.revenue?.toLocaleString() || '0'}
                    </span>
                    <div className="w-24 bg-gray-100 rounded-full h-2">
                      <div 
                        className="bg-primary-600 h-2 rounded-full" 
                        style={{ width: `${store.performance || 0}%` }}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Recent Activity Tables */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg ">
          <div className="px-6 py-4 border-b">
            <h3 className="text-lg font-semibold">Recent Orders</h3>
          </div>
          <div className="p-6">
            {(stats?.orders?.recent?.length > 0 || orders?.orders?.length > 0) ? (
              <div className="space-y-3">
                {(stats?.orders?.recent || orders?.orders || []).slice(0, 5).map((order: any, index: number) => (
                  <div key={order.id || index} className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium">#{order.id || order.order_number}</p>
                      <p className="text-xs text-gray-500">{order.customer || order.customer_name}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium">${order.total}</p>
                      <span className={`text-xs px-2 py-1 rounded-full ${
                        order.status === 'completed' ? 'bg-primary-100 text-primary-800' :
                        order.status === 'processing' ? 'bg-blue-100 text-blue-800' :
                        order.status === 'shipped' ? 'bg-purple-100 text-purple-800' :
                        'bg-warning-100 text-warning-800'
                      }`}>
                        {order.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-500">No recent orders</p>
            )}
          </div>
        </div>

        <div className="bg-white rounded-lg ">
          <div className="px-6 py-4 border-b">
            <h3 className="text-lg font-semibold">Low Stock Alerts</h3>
          </div>
          <div className="p-6">
            {inventory?.items?.length > 0 ? (
              <div className="space-y-3">
                {inventory.items.slice(0, 5).map((item: any) => (
                  <div key={item.id} className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium">{item.name}</p>
                      <p className="text-xs text-gray-500">SKU: {item.sku}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium text-danger-600">
                        {item.quantity} left
                      </p>
                      <p className="text-xs text-gray-500">
                        Reorder: {item.reorder_point}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-500">No low stock items</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;