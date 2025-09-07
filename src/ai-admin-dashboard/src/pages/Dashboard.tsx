import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';
import { 
  TrendingUp, TrendingDown, DollarSign, ShoppingCart, 
  Users, Package, AlertTriangle, Activity, 
  Clock, CheckCircle, Truck, Calendar
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
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: async () => {
      const response = await api.analytics.getDashboardStats();
      return response.data;
    },
  });

  const { data: orders } = useQuery({
    queryKey: ['recent-orders'],
    queryFn: async () => {
      const response = await api.orders.getAll({ limit: 10 });
      return response.data;
    },
  });

  const { data: inventory } = useQuery({
    queryKey: ['inventory-alerts'],
    queryFn: async () => {
      const response = await api.inventory.getAll({ status: 'low_stock' });
      return response.data;
    },
  });

  const { data: topProducts } = useQuery({
    queryKey: ['top-products'],
    queryFn: async () => {
      // Placeholder for top products since endpoint doesn't exist yet
      return { data: [] };
    },
  });

  if (statsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600"></div>
      </div>
    );
  }

  const revenueData = {
    labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
    datasets: [
      {
        label: 'Revenue',
        data: [1200, 1900, 1500, 2200, 2800, 3200, 2900],
        borderColor: 'rgb(34, 197, 94)',
        backgroundColor: 'rgba(34, 197, 94, 0.1)',
        tension: 0.4,
        fill: true,
      },
    ],
  };

  const categoryData = {
    labels: ['Flower', 'Edibles', 'Concentrates', 'Vapes', 'Accessories'],
    datasets: [
      {
        data: [45, 20, 15, 15, 5],
        backgroundColor: [
          'rgba(34, 197, 94, 0.8)',
          'rgba(168, 85, 247, 0.8)',
          'rgba(251, 146, 60, 0.8)',
          'rgba(59, 130, 246, 0.8)',
          'rgba(107, 114, 128, 0.8)',
        ],
      },
    ],
  };

  const orderStatusData = {
    labels: ['Pending', 'Processing', 'Ready', 'Delivered'],
    datasets: [
      {
        label: 'Orders',
        data: [
          orders?.data?.filter((o: any) => o.status === 'pending').length || 0,
          orders?.data?.filter((o: any) => ['confirmed', 'processing'].includes(o.status)).length || 0,
          orders?.data?.filter((o: any) => o.status === 'ready').length || 0,
          orders?.data?.filter((o: any) => o.status === 'delivered').length || 0,
        ],
        backgroundColor: [
          'rgba(250, 204, 21, 0.8)',
          'rgba(59, 130, 246, 0.8)',
          'rgba(34, 197, 94, 0.8)',
          'rgba(16, 185, 129, 0.8)',
        ],
      },
    ],
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard Overview</h1>
          <p className="text-sm text-gray-600">Welcome to Pot Palace Admin</p>
        </div>
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <Calendar className="h-4 w-4" />
          {new Date().toLocaleDateString('en-US', { 
            weekday: 'long', 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric' 
          })}
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Today's Revenue</p>
              <p className="text-2xl font-bold text-gray-900">
                ${stats?.revenue?.today?.toFixed(2) || '0.00'}
              </p>
              <p className="text-xs text-green-600 flex items-center mt-1">
                <TrendingUp className="h-3 w-3 mr-1" />
                {stats?.revenue?.trend || 0}% from yesterday
              </p>
            </div>
            <div className="p-3 bg-green-100 rounded-lg">
              <DollarSign className="h-6 w-6 text-green-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Orders</p>
              <p className="text-2xl font-bold text-gray-900">
                {stats?.orders?.today || 0}
              </p>
              <p className="text-xs text-gray-600">
                {stats?.orders?.pending || 0} pending
              </p>
            </div>
            <div className="p-3 bg-blue-100 rounded-lg">
              <ShoppingCart className="h-6 w-6 text-blue-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Active Customers</p>
              <p className="text-2xl font-bold text-gray-900">
                {stats?.customers?.active || 0}
              </p>
              <p className="text-xs text-gray-600">
                +{stats?.customers?.new_this_month || 0} this month
              </p>
            </div>
            <div className="p-3 bg-purple-100 rounded-lg">
              <Users className="h-6 w-6 text-purple-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Low Stock Items</p>
              <p className="text-2xl font-bold text-yellow-600">
                {stats?.inventory?.low_stock_items || 0}
              </p>
              <p className="text-xs text-red-600">
                {stats?.inventory?.out_of_stock_items || 0} out of stock
              </p>
            </div>
            <div className="p-3 bg-yellow-100 rounded-lg">
              <AlertTriangle className="h-6 w-6 text-yellow-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white rounded-lg shadow-sm p-6">
          <h2 className="text-lg font-semibold mb-4">Revenue Trend</h2>
          <Line 
            data={revenueData} 
            options={{
              responsive: true,
              plugins: {
                legend: {
                  display: false,
                },
              },
              scales: {
                y: {
                  beginAtZero: true,
                  ticks: {
                    callback: function(value) {
                      return '$' + value;
                    }
                  }
                }
              }
            }}
          />
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6">
          <h2 className="text-lg font-semibold mb-4">Sales by Category</h2>
          <Doughnut 
            data={categoryData}
            options={{
              responsive: true,
              plugins: {
                legend: {
                  position: 'bottom',
                },
              },
            }}
          />
        </div>
      </div>

      {/* Tables Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Orders */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold">Recent Orders</h2>
            <a href="/orders" className="text-sm text-green-600 hover:text-green-700">
              View all →
            </a>
          </div>
          <div className="space-y-3">
            {orders?.data?.slice(0, 5).map((order: any) => (
              <div key={order.id} className="flex items-center justify-between p-3 hover:bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  {order.status === 'pending' && <Clock className="h-5 w-5 text-yellow-500" />}
                  {order.status === 'processing' && <Package className="h-5 w-5 text-blue-500" />}
                  {order.status === 'ready' && <CheckCircle className="h-5 w-5 text-green-500" />}
                  {order.status === 'delivered' && <Truck className="h-5 w-5 text-green-600" />}
                  <div>
                    <p className="text-sm font-medium">{order.order_number}</p>
                    <p className="text-xs text-gray-500">
                      {order.customer?.first_name} {order.customer?.last_name}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium">${order.total_amount?.toFixed(2)}</p>
                  <p className="text-xs text-gray-500">{order.items?.length || 0} items</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Low Stock Alerts */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold">Low Stock Alerts</h2>
            <a href="/inventory" className="text-sm text-green-600 hover:text-green-700">
              View all →
            </a>
          </div>
          <div className="space-y-3">
            {inventory?.data?.slice(0, 5).map((item: any) => (
              <div key={item.id} className="flex items-center justify-between p-3 hover:bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <AlertTriangle className="h-5 w-5 text-yellow-500" />
                  <div>
                    <p className="text-sm font-medium">{item.product?.name}</p>
                    <p className="text-xs text-gray-500">{item.product?.sku}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium text-yellow-600">
                    {item.quantity_on_hand} left
                  </p>
                  <p className="text-xs text-gray-500">
                    Reorder: {item.reorder_point}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Order Status Distribution */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-lg font-semibold mb-4">Order Status Distribution</h2>
        <Bar 
          data={orderStatusData}
          options={{
            responsive: true,
            plugins: {
              legend: {
                display: false,
              },
            },
            scales: {
              y: {
                beginAtZero: true,
                ticks: {
                  stepSize: 1,
                }
              }
            }
          }}
        />
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-lg font-semibold mb-4">Quick Actions</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <button className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 text-center">
            <Package className="h-8 w-8 mx-auto mb-2 text-green-600" />
            <span className="text-sm">Add Product</span>
          </button>
          <button className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 text-center">
            <Users className="h-8 w-8 mx-auto mb-2 text-blue-600" />
            <span className="text-sm">New Customer</span>
          </button>
          <button className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 text-center">
            <ShoppingCart className="h-8 w-8 mx-auto mb-2 text-purple-600" />
            <span className="text-sm">Create Order</span>
          </button>
          <button className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 text-center">
            <Activity className="h-8 w-8 mx-auto mb-2 text-orange-600" />
            <span className="text-sm">View Reports</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;