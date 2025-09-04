import { useQuery } from '@tanstack/react-query';
import { 
  TrendingUp, 
  TrendingDown, 
  Brain, 
  MessageSquare, 
  Activity,
  Users,
  Zap,
  BarChart3,
  ArrowUpRight,
  ArrowDownRight
} from 'lucide-react';
import apiService from '../services/api';

export default function Dashboard() {
  // Fetch dashboard stats
  const { data: stats, isLoading: statsLoading, error: statsError } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: () => apiService.getDashboardStats(),
    refetchInterval: 5000, // Refresh every 5 seconds
  });
  
  // Fetch recent activity
  const { data: recentActivity } = useQuery({
    queryKey: ['recent-activity'],
    queryFn: async () => {
      const data = await apiService.getRecentActivity();
      console.log('Dashboard received recent activity:', data);
      return data;
    },
    refetchInterval: 10000, // Refresh every 10 seconds
  });
  
  // Fetch system health
  const { data: systemHealth } = useQuery({
    queryKey: ['system-health'],
    queryFn: () => apiService.getAllServicesHealth(),
    refetchInterval: 15000, // Refresh every 15 seconds
  });

  const metrics = [
    {
      title: 'AI Accuracy',
      value: stats?.accuracy ? `${(stats.accuracy * 100).toFixed(1)}%` : '0.0%',
      change: stats?.accuracy_trend || 0,
      icon: Brain,
      color: 'primary',
      description: 'Model performance'
    },
    {
      title: 'Examples Trained',
      value: stats?.total_examples || 0,
      subtitle: stats?.examples_today ? `+${stats.examples_today} today` : null,
      icon: Zap,
      color: 'purple',
      description: 'Training data size'
    },
    {
      title: 'Unique Patterns',
      value: stats?.unique_patterns || 0,
      subtitle: 'Cannabis terms mapped',
      icon: BarChart3,
      color: 'teal',
      description: 'Knowledge base'
    },
    {
      title: 'Queries Today',
      value: stats?.queries_today || 0,
      subtitle: stats?.peak_time ? `Peak: ${stats.peak_time}` : null,
      icon: MessageSquare,
      color: 'amber',
      description: 'User interactions'
    }
  ];

  const quickActions = [
    { label: 'Train AI', icon: '🧠', color: 'from-primary-400 to-primary-600' },
    { label: 'Test Query', icon: '💬', color: 'from-purple-400 to-purple-600' },
    { label: 'View Reports', icon: '📊', color: 'from-teal-400 to-teal-600' },
    { label: 'Deploy Model', icon: '🚀', color: 'from-amber-400 to-amber-600' }
  ];

  const getColorClasses = (color: string) => {
    const colors: Record<string, { bg: string; text: string; icon: string }> = {
      primary: { 
        bg: 'bg-green-50', 
        text: 'text-green-600', 
        icon: 'text-green-500' 
      },
      purple: { 
        bg: 'bg-purple-50', 
        text: 'text-purple-600', 
        icon: 'text-purple-500' 
      },
      teal: { 
        bg: 'bg-teal-50', 
        text: 'text-teal-600', 
        icon: 'text-teal-500' 
      },
      amber: { 
        bg: 'bg-amber-50', 
        text: 'text-amber-600', 
        icon: 'text-amber-500' 
      }
    };
    return colors[color] || colors.primary;
  };

  return (
    <div className="space-y-8 animate-in">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold text-zinc-900">Dashboard</h2>
          <p className="text-zinc-500 mt-1">Monitor your AI budtender performance and analytics</p>
        </div>
        <div className="flex items-center gap-3">
          <button className="btn-secondary">
            <Activity className="w-4 h-4 mr-2" />
            View Live Activity
          </button>
          <button className="btn-primary">
            <Brain className="w-4 h-4 mr-2" />
            Train Model
          </button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="dashboard-grid">
        {metrics.map((metric, index) => {
          const colorClasses = getColorClasses(metric.color);
          const Icon = metric.icon;
          
          return (
            <div 
              key={index} 
              className="card p-6 hover:shadow-lg transition-all duration-300 animate-slide-up"
              style={{ animationDelay: `${index * 50}ms` }}
            >
              <div className="flex items-start justify-between mb-4">
                <div className={`p-3 rounded-xl ${colorClasses.bg}`}>
                  <Icon className={`w-5 h-5 ${colorClasses.icon}`} />
                </div>
                {metric.change !== undefined && metric.change !== 0 && (
                  <div className={`flex items-center gap-1 text-sm font-medium ${
                    metric.change > 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {metric.change > 0 ? (
                      <>
                        <ArrowUpRight className="w-4 h-4" />
                        {Math.abs(metric.change).toFixed(1)}%
                      </>
                    ) : (
                      <>
                        <ArrowDownRight className="w-4 h-4" />
                        {Math.abs(metric.change).toFixed(1)}%
                      </>
                    )}
                  </div>
                )}
              </div>
              
              <div>
                <p className="text-sm font-medium text-zinc-500 mb-1">{metric.title}</p>
                {statsLoading ? (
                  <div className="skeleton h-8 w-24 mb-2"></div>
                ) : statsError ? (
                  <p className="text-2xl font-bold text-red-500">Error</p>
                ) : (
                  <p className={`text-3xl font-bold ${colorClasses.text}`}>
                    {metric.value}
                  </p>
                )}
                {metric.subtitle && (
                  <p className="text-xs text-zinc-400 mt-2">{metric.subtitle}</p>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Quick Actions */}
      <div className="card p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-zinc-900">Quick Actions</h3>
          <span className="text-sm text-zinc-400">Frequently used tools</span>
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {quickActions.map((action, index) => (
            <button
              key={index}
              className="group relative overflow-hidden rounded-xl p-6 text-white transition-all duration-300 hover:scale-105 hover:shadow-xl"
              style={{ animationDelay: `${index * 100}ms` }}
            >
              <div className={`absolute inset-0 bg-gradient-to-br ${action.color}`}></div>
              <div className="relative z-10">
                <span className="text-3xl mb-3 block">{action.icon}</span>
                <span className="text-sm font-semibold">{action.label}</span>
              </div>
              <div className="absolute inset-0 bg-white opacity-0 group-hover:opacity-10 transition-opacity duration-300"></div>
            </button>
          ))}
        </div>
      </div>

      {/* Recent Activity & Stats */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Activity */}
        <div className="card p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-zinc-900">Recent Activity</h3>
            <button className="text-sm text-primary-600 hover:text-primary-700 font-medium">
              View all
            </button>
          </div>
          
          <div className="space-y-4">
            {(recentActivity && Array.isArray(recentActivity) && recentActivity.length > 0) ? (
              recentActivity.map((item, index) => (
                <div key={index} className="flex items-center gap-4 p-3 rounded-lg hover:bg-zinc-50 transition-colors">
                  <div className={`w-2 h-2 rounded-full ${
                    item.type === 'success' ? 'bg-green-500' :
                    item.type === 'info' ? 'bg-blue-500' :
                    item.type === 'warning' ? 'bg-amber-500' :
                    'bg-zinc-400'
                  }`}></div>
                  <div className="flex-1">
                    <p className="text-sm text-zinc-700">{item.action}</p>
                    <p className="text-xs text-zinc-400 mt-0.5">{item.time}</p>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-4 text-zinc-500">
                <p>No recent activity</p>
              </div>
            )}
          </div>
        </div>

        {/* System Health */}
        <div className="card p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-zinc-900">System Health</h3>
            <span className="badge-success">All Systems Operational</span>
          </div>
          
          <div className="space-y-4">
            {systemHealth?.services && systemHealth.services.length > 0 ? (
              systemHealth.services.map((service: any, index) => {
              const status = service.status === 'healthy' || service.status === 'running' ? 'online' : 
                            service.status === 'degraded' ? 'warning' : 'offline';
              const latency = service.health?.latency || service.response_time || 0;
              const uptime = service.uptime || `${(100 - (service.error_rate || 0)).toFixed(1)}%`;
              
              return (
                <div key={index} className="flex items-center justify-between p-3 rounded-lg hover:bg-zinc-50 transition-colors">
                  <div className="flex items-center gap-3">
                    <div className={`status-${status === 'warning' ? 'warning' : status === 'offline' ? 'offline' : 'online'}`}></div>
                    <div>
                      <p className="text-sm font-medium text-zinc-700">{service.name}</p>
                      <p className="text-xs text-zinc-400">Latency: {latency}ms</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-zinc-600">{uptime}</p>
                    <p className="text-xs text-zinc-400">Uptime</p>
                  </div>
                </div>
              );
            })
            ) : (
              <div className="text-center py-4 text-zinc-500">
                <p>No system health data available</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}