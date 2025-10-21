import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { api } from '../services/api';
import { getApiEndpoint } from '../config/app.config';
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
  const { t } = useTranslation(['dashboard', 'common']);
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

      const response = await fetch(getApiEndpoint('/analytics/dashboard'), {
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
      
      const response = await fetch(getApiEndpoint('/orders?limit=10'), {
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

      const response = await fetch(getApiEndpoint('/store-inventory/low-stock'), {
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
        label: t('dashboard:charts.revenueLabel'),
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
    labels: hasCategories ? Object.keys(salesByCategory) : [t('common:messages.noData')],
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
    <div className="space-y-4 sm:space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 sm:gap-0">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white">
            {currentStore ? `${currentStore.name} ${t('dashboard:title')}` : t('dashboard:systemDashboard')}
          </h1>
          <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400 mt-1">
            {isSuperAdmin() ? t('dashboard:systemOverview') :
             isTenantAdmin() ? t('dashboard:tenantOverview') :
             t('dashboard:storeMetrics')}
          </p>
        </div>
        <div className="flex items-center gap-3 sm:gap-6 w-full sm:w-auto">
          {isSuperAdmin() && (
            <div className="bg-purple-50 dark:bg-purple-900/20 px-3 sm:px-4 py-2 rounded-lg">
              <div className="flex items-center gap-2">
                <Building2 className="h-4 w-4 sm:h-5 sm:w-5 text-purple-600 dark:text-purple-400" />
                <span className="text-xs sm:text-sm font-medium text-purple-900 dark:text-purple-300">
                  {stores.length} {t('dashboard:activeStores')}
                </span>
              </div>
            </div>
          )}
          <div className="text-left sm:text-right flex-1 sm:flex-none">
            <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400">{t('common:common.today')}</p>
            <p className="text-sm sm:text-lg font-semibold text-gray-900 dark:text-white">{new Date().toLocaleDateString()}</p>
          </div>
        </div>
      </div>

      {/* No Store Selected Warning */}
      {!currentStore && !isSuperAdmin() && (
        <div className="bg-warning-50 dark:bg-warning-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-6">
          <div className="flex items-center">
            <AlertTriangle className="h-5 w-5 text-warning-600 dark:text-warning-400 mr-2" />
            <p className="text-sm text-warning-800 dark:text-warning-300">
              {t('dashboard:selectStoreMessage')}
            </p>
          </div>
        </div>
      )}

      {/* Metrics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 lg:gap-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 sm:p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs sm:text-sm font-medium text-gray-600 dark:text-gray-400">{t('dashboard:totalRevenue')}</p>
              <p className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white">
                ${stats?.revenue?.total?.toLocaleString() || '0'}
              </p>
              <div className="flex items-center mt-2">
                {(stats?.revenue?.trend || 0) > 0 ? (
                  <>
                    <TrendingUp className="h-3 w-3 sm:h-4 sm:w-4 text-primary-500 dark:text-primary-400 mr-1" />
                    <span className="text-xs sm:text-sm text-primary-600 dark:text-primary-400">
                      +{stats?.revenue?.trend || 0}%
                    </span>
                  </>
                ) : (
                  <>
                    <TrendingDown className="h-3 w-3 sm:h-4 sm:w-4 text-red-500 mr-1" />
                    <span className="text-xs sm:text-sm text-danger-600 dark:text-danger-400">
                      {stats?.revenue?.trend || 0}%
                    </span>
                  </>
                )}
                <span className="text-xs sm:text-sm text-gray-500 dark:text-gray-400 ml-2">{t('dashboard:vsLastWeek')}</span>
              </div>
            </div>
            <DollarSign className="h-6 w-6 sm:h-8 sm:w-8 text-primary-600 dark:text-primary-400" />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 sm:p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs sm:text-sm font-medium text-gray-600 dark:text-gray-400">{t('dashboard:totalOrders')}</p>
              <p className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white">
                {stats?.orders?.total || 0}
              </p>
              <div className="flex items-center mt-2">
                {(stats?.orders?.trend || 0) > 0 ? (
                  <>
                    <TrendingUp className="h-3 w-3 sm:h-4 sm:w-4 text-primary-500 dark:text-primary-400 mr-1" />
                    <span className="text-xs sm:text-sm text-primary-600 dark:text-primary-400">
                      +{stats?.orders?.trend || 0}%
                    </span>
                  </>
                ) : (
                  <>
                    <TrendingDown className="h-3 w-3 sm:h-4 sm:w-4 text-red-500 mr-1" />
                    <span className="text-xs sm:text-sm text-danger-600 dark:text-danger-400">
                      {stats?.orders?.trend || 0}%
                    </span>
                  </>
                )}
                <span className="text-xs sm:text-sm text-gray-500 dark:text-gray-400 ml-2">{t('dashboard:vsLastWeek')}</span>
              </div>
            </div>
            <ShoppingCart className="h-6 w-6 sm:h-8 sm:w-8 text-accent-600" />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 sm:p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs sm:text-sm font-medium text-gray-600 dark:text-gray-400">{t('dashboard:activeCustomers')}</p>
              <p className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white">
                {stats?.customers?.total || 0}
              </p>
              <div className="flex items-center mt-2">
                <span className="text-xs sm:text-sm text-gray-500 dark:text-gray-400">
                  {stats?.customers?.new || 0} {t('dashboard:newThisWeek')}
                </span>
              </div>
            </div>
            <Users className="h-6 w-6 sm:h-8 sm:w-8 text-purple-600 dark:text-purple-400" />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 sm:p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs sm:text-sm font-medium text-gray-600 dark:text-gray-400">{t('dashboard:inventoryItems')}</p>
              <p className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white">
                {inventoryStats?.total_skus || stats?.inventory?.total || 0}
              </p>
              <div className="flex items-center mt-2">
                <AlertTriangle className="h-3 w-3 sm:h-4 sm:w-4 text-yellow-500 mr-1" />
                <span className="text-xs sm:text-sm text-warning-600 dark:text-warning-400">
                  {inventoryStats?.low_stock_items || stats?.inventory?.low_stock || 0} {t('dashboard:lowStockCount')}
                </span>
              </div>
            </div>
            <Package className="h-6 w-6 sm:h-8 sm:w-8 text-orange-600 dark:text-orange-400" />
          </div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 sm:p-6">
          <h3 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-white mb-3 sm:mb-4">{t('dashboard:revenueTrend')}</h3>
          <div style={{ height: '250px', position: 'relative' }} className="sm:h-[300px]">
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
                },
                plugins: {
                  legend: {
                    labels: {
                      font: {
                        size: window.innerWidth < 640 ? 10 : 12
                      }
                    }
                  }
                }
              }}
            />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 sm:p-6">
          <h3 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-white mb-3 sm:mb-4">{t('dashboard:salesByCategory')}</h3>
          <div style={{ height: '250px', position: 'relative' }} className="sm:h-[300px]">
            <Doughnut
              data={categoryData}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: {
                    position: 'bottom',
                    labels: {
                      font: {
                        size: window.innerWidth < 640 ? 10 : 12
                      },
                      padding: window.innerWidth < 640 ? 10 : 15
                    }
                  }
                }
              }}
            />
          </div>
        </div>
      </div>

      {/* Additional Charts for Admin Users */}
      {(isSuperAdmin() || isTenantAdmin()) && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 sm:p-6">
            <h3 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-white mb-3 sm:mb-4">{t('dashboard:orderStatusDistribution')}</h3>
            <div style={{ height: '250px', position: 'relative' }} className="sm:h-[300px]">
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
                  },
                  plugins: {
                    legend: {
                      labels: {
                        font: {
                          size: window.innerWidth < 640 ? 10 : 12
                        }
                      }
                    }
                  }
                }}
              />
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 sm:p-6">
            <h3 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-white mb-3 sm:mb-4">{t('dashboard:storePerformance')}</h3>
            <div className="space-y-3 sm:space-y-4">
              {stores.slice(0, 5).map((store) => (
                <div key={store.id} className="flex items-center justify-between gap-2">
                  <div className="flex items-center flex-1 min-w-0">
                    <Store className="h-4 w-4 sm:h-5 sm:w-5 text-gray-400 dark:text-gray-500 mr-2 flex-shrink-0" />
                    <span className="text-xs sm:text-sm font-medium text-gray-900 dark:text-white truncate">{store.name}</span>
                  </div>
                  <div className="flex items-center gap-3 sm:gap-6 flex-shrink-0">
                    <span className="text-xs sm:text-sm text-gray-500 dark:text-gray-400">
                      ${store.revenue?.toLocaleString() || '0'}
                    </span>
                    <div className="w-16 sm:w-24 bg-gray-100 dark:bg-gray-700 rounded-full h-2">
                      <div
                        className="bg-primary-600 dark:bg-primary-500 h-2 rounded-full"
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
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
          <div className="px-4 sm:px-6 py-3 sm:py-4 border-b border-gray-200 dark:border-gray-700">
            <h3 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-white">{t('dashboard:recentOrders')}</h3>
          </div>
          <div className="p-4 sm:p-6">
            {(stats?.orders?.recent?.length > 0 || orders?.orders?.length > 0) ? (
              <div className="space-y-3">
                {(stats?.orders?.recent || orders?.orders || []).slice(0, 5).map((order: any, index: number) => (
                  <div key={order.id || index} className="flex items-center justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <p className="text-xs sm:text-sm font-medium text-gray-900 dark:text-white truncate">
                        #{order.id || order.order_number}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400 truncate">{order.customer || order.customer_name}</p>
                    </div>
                    <div className="text-right flex-shrink-0">
                      <p className="text-xs sm:text-sm font-medium text-gray-900 dark:text-white whitespace-nowrap">${order.total}</p>
                      <span className={`inline-block text-xs px-2 py-0.5 sm:py-1 rounded-full whitespace-nowrap ${
                        order.status === 'completed' ? 'bg-primary-100 text-primary-800 dark:bg-primary-900/20 dark:text-primary-300' :
                        order.status === 'processing' ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-300' :
                        order.status === 'shipped' ? 'bg-purple-100 text-purple-800 dark:bg-purple-900/20 dark:text-purple-300' :
                        'bg-warning-100 text-warning-800 dark:bg-warning-900/20 dark:text-warning-300'
                      }`}>
                        {t(`dashboard:orderStatuses.${order.status}`, { defaultValue: order.status })}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400">{t('dashboard:noRecentOrders')}</p>
            )}
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
          <div className="px-4 sm:px-6 py-3 sm:py-4 border-b border-gray-200 dark:border-gray-700">
            <h3 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-white">{t('dashboard:lowStockAlerts')}</h3>
          </div>
          <div className="p-4 sm:p-6">
            {inventory?.items?.length > 0 ? (
              <div className="space-y-3">
                {inventory.items.slice(0, 5).map((item: any) => (
                  <div key={item.id} className="flex items-center justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <p className="text-xs sm:text-sm font-medium text-gray-900 dark:text-white truncate">{item.name}</p>
                      <p className="text-xs text-gray-500 dark:text-gray-400 truncate">SKU: {item.sku}</p>
                    </div>
                    <div className="text-right flex-shrink-0">
                      <p className="text-xs sm:text-sm font-medium text-danger-600 dark:text-danger-400 whitespace-nowrap">
                        {item.quantity} {t('dashboard:left')}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400 whitespace-nowrap">
                        {t('dashboard:reorder')}: {item.reorder_point}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400">{t('dashboard:noLowStockItems')}</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;