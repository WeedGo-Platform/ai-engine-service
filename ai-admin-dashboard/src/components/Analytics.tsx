import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import apiService from '../services/api';
import { format } from 'date-fns';
import { 
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, 
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  AreaChart, Area
} from 'recharts';
import { 
  TrendingUp, Activity, MessageSquare, 
  Clock, Target, AlertCircle 
} from 'lucide-react';

const COLORS = ['#10b981', '#8b5cf6', '#f59e0b', '#ef4444', '#3b82f6', '#ec4899'];

interface AnalyticsData {
  daily_conversations: { date: string; count: number; satisfaction: number }[];
  intent_distribution: { intent: string; count: number; percentage: number }[];
  popular_products: { name: string; requests: number; conversions: number }[];
  response_times: { hour: number; avg_ms: number; p95_ms: number }[];
  customer_satisfaction: { rating: number; count: number }[];
  slang_usage: { term: string; frequency: number }[];
  conversion_funnel: { stage: string; users: number; rate: number }[];
  error_rates: { date: string; errors: number; total: number; rate: number }[];
}

// Removed mock data - will fetch from API

export default function Analytics() {
  const [dateRange] = useState({
    start: format(new Date(Date.now() - 7 * 24 * 60 * 60 * 1000), 'yyyy-MM-dd'),
    end: format(new Date(), 'yyyy-MM-dd')
  });

  const { data: analytics, isLoading, error } = useQuery({
    queryKey: ['analytics', dateRange],
    queryFn: () => apiService.getAnalytics(dateRange),
  });

  // Show loading state
  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="bg-white rounded-xl shadow-sm p-6">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-1/3 mb-4"></div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="h-64 bg-gray-200 rounded-lg"></div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Show error state
  if (error || !analytics) {
    return (
      <div className="bg-white rounded-xl shadow-sm p-6">
        <div className="text-center py-8 text-red-500">
          <p className="text-lg font-medium">Failed to load analytics</p>
          <p className="text-sm mt-2">Please check your connection and try again</p>
        </div>
      </div>
    );
  }

  // Provide default structure if data is missing
  const analyticsData: AnalyticsData = {
    daily_conversations: analytics.daily_conversations || [],
    intent_distribution: analytics.intent_distribution || [],
    popular_products: analytics.popular_products || [],
    response_times: analytics.response_times || [],
    customer_satisfaction: analytics.customer_satisfaction || [],
    slang_usage: analytics.slang_usage || [],
    conversion_funnel: analytics.conversion_funnel || [],
    error_rates: analytics.error_rates || []
  };

  const totalConversations = analyticsData.daily_conversations.length > 0 
    ? analyticsData.daily_conversations.reduce((sum, day) => sum + day.count, 0) 
    : 0;
  const avgSatisfaction = analyticsData.daily_conversations.length > 0
    ? (analyticsData.daily_conversations.reduce((sum, day) => sum + day.satisfaction, 0) / analyticsData.daily_conversations.length).toFixed(1)
    : '0.0';
  const conversionRate = ((analyticsData.conversion_funnel.find(s => s.stage === 'Purchase')?.rate || 0)).toFixed(1);
  const avgResponseTime = analyticsData.response_times.length > 0
    ? (analyticsData.response_times.reduce((sum, hour) => sum + hour.avg_ms, 0) / analyticsData.response_times.length).toFixed(0)
    : '0';

  return (
    <div className="space-y-6">
      {/* Header with Key Metrics */}
      <div className="bg-white rounded-xl shadow-sm p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Analytics & Reports</h2>
        
        <div className="grid grid-cols-4 gap-4">
          <div className="bg-gradient-to-r from-weed-green-50 to-weed-green-100 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <MessageSquare className="w-8 h-8 text-weed-green-600" />
              <span className="text-xs text-weed-green-600 flex items-center">
                <TrendingUp className="w-4 h-4 mr-1" />
                +12.5%
              </span>
            </div>
            <p className="text-2xl font-bold text-gray-900">{totalConversations.toLocaleString()}</p>
            <p className="text-sm text-gray-600 mt-1">Total Conversations</p>
          </div>

          <div className="bg-gradient-to-r from-purple-haze-50 to-purple-haze-100 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <Activity className="w-8 h-8 text-purple-haze-600" />
              <span className="text-xs text-purple-haze-600">{avgSatisfaction}/5.0</span>
            </div>
            <p className="text-2xl font-bold text-gray-900">{avgSatisfaction}</p>
            <p className="text-sm text-gray-600 mt-1">Avg Satisfaction</p>
          </div>

          <div className="bg-gradient-to-r from-blue-50 to-blue-100 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <Target className="w-8 h-8 text-blue-600" />
              <span className="text-xs text-blue-600 flex items-center">
                <TrendingUp className="w-4 h-4 mr-1" />
                +5.2%
              </span>
            </div>
            <p className="text-2xl font-bold text-gray-900">{conversionRate}%</p>
            <p className="text-sm text-gray-600 mt-1">Conversion Rate</p>
          </div>

          <div className="bg-gradient-to-r from-amber-50 to-amber-100 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <Clock className="w-8 h-8 text-amber-600" />
              <span className="text-xs text-amber-600">ms</span>
            </div>
            <p className="text-2xl font-bold text-gray-900">{avgResponseTime}</p>
            <p className="text-sm text-gray-600 mt-1">Avg Response Time</p>
          </div>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-2 gap-6">
        {/* Daily Conversations & Satisfaction */}
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Daily Activity</h3>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={analyticsData.daily_conversations}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" tick={{ fontSize: 12 }} />
              <YAxis yAxisId="left" tick={{ fontSize: 12 }} />
              <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 12 }} />
              <Tooltip />
              <Legend />
              <Area 
                yAxisId="left"
                type="monotone" 
                dataKey="count" 
                stroke="#10b981" 
                fill="#10b981" 
                fillOpacity={0.3}
                name="Conversations"
              />
              <Line 
                yAxisId="right"
                type="monotone" 
                dataKey="satisfaction" 
                stroke="#8b5cf6" 
                strokeWidth={2}
                name="Satisfaction"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Intent Distribution */}
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Intent Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={analyticsData.intent_distribution}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ intent, percentage }) => `${intent} (${percentage}%)`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="count"
              >
                {analyticsData.intent_distribution.map((_entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Popular Products */}
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Requested Products</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={analyticsData.popular_products} layout="horizontal">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" tick={{ fontSize: 12 }} />
              <YAxis dataKey="name" type="category" tick={{ fontSize: 12 }} width={100} />
              <Tooltip />
              <Legend />
              <Bar dataKey="requests" fill="#10b981" name="Requests" />
              <Bar dataKey="conversions" fill="#8b5cf6" name="Conversions" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Response Times */}
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Response Time by Hour</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={analyticsData.response_times}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="hour" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="avg_ms" stroke="#10b981" strokeWidth={2} name="Average (ms)" />
              <Line type="monotone" dataKey="p95_ms" stroke="#f59e0b" strokeWidth={2} name="95th Percentile (ms)" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Conversion Funnel */}
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Conversion Funnel</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={analyticsData.conversion_funnel}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="stage" tick={{ fontSize: 11 }} angle={-45} textAnchor="end" height={80} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="users" fill="#8b5cf6">
                {analyticsData.conversion_funnel.map((_entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Cannabis Slang Usage */}
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Cannabis Slang Detection</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={analyticsData.slang_usage}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="term" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="frequency" fill="#10b981" radius={[8, 8, 0, 0]}>
                {analyticsData.slang_usage.map((_entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Error Rate Monitoring */}
      <div className="bg-white rounded-xl shadow-sm p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Error Rate Monitoring</h3>
          <div className="flex items-center space-x-2 text-sm">
            <AlertCircle className="w-4 h-4 text-amber-500" />
            <span className="text-gray-600">Current: 1.7%</span>
          </div>
        </div>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={analyticsData.error_rates}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip />
            <Line type="monotone" dataKey="rate" stroke="#ef4444" strokeWidth={2} name="Error Rate %" />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}