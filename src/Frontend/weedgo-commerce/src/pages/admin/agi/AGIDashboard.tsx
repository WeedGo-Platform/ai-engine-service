import React, { useState, useEffect } from 'react';
import {
  Activity, Users, CheckCircle, Shield, GitBranch,
  TrendingUp, Zap, RefreshCw, Download, Sliders,
  Database, Cpu, Search, BarChart2, PlayCircle,
  CheckSquare, Command, AlertTriangle
} from 'lucide-react';
import { useAGIEngine } from '../../../hooks/useAGIEngine';
import StatsCard from './components/StatsCard';
import AgentCard from './components/AgentCard';
import SecurityMonitor from './components/SecurityMonitor';
import LearningMetrics from './components/LearningMetrics';
import ActivityLog from './components/ActivityLog';
import QuickActions from './components/QuickActions';

interface DashboardStats {
  totalRequests: number;
  activeAgents: number;
  totalAgents: number;
  successRate: number;
  securityEvents: number;
  threatsBlocked: number;
}

const AGIDashboard: React.FC = () => {
  const { agents, stats, activities, security, learning, refreshData } = useAGIEngine();
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      setIsLoading(true);
      await refreshData();
      setIsLoading(false);
    };
    loadData();

    // Auto-refresh every 30 seconds
    const interval = setInterval(refreshData, 30000);
    return () => clearInterval(interval);
  }, []);

  const dashboardStats: DashboardStats = {
    totalRequests: stats?.totalRequests || 0,
    activeAgents: agents?.filter(a => a.status === 'active').length || 0,
    totalAgents: agents?.length || 0,
    successRate: stats?.successRate || 0,
    securityEvents: security?.totalEvents || 0,
    threatsBlocked: security?.threatsBlocked || 0,
  };

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100">
      {/* Header */}
      <div className="bg-gray-800 border-b border-gray-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-500 rounded-lg flex items-center justify-center">
              <Cpu className="w-6 h-6 text-white" />
            </div>
            <h1 className="text-2xl font-bold">AGI Engine Control Center</h1>
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${
              isLoading ? 'bg-yellow-500/20 text-yellow-400' : 'bg-green-500/20 text-green-400'
            }`}>
              {isLoading ? 'Loading...' : 'System Online'}
            </span>
          </div>
          <div className="flex items-center space-x-4">
            <button
              onClick={refreshData}
              className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
            >
              <RefreshCw className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Main Dashboard */}
      <div className="p-6">
        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
          <StatsCard
            title="Total Requests"
            value={dashboardStats.totalRequests.toLocaleString()}
            icon={<Activity className="w-6 h-6 text-blue-400" />}
            trend="+12%"
            trendUp={true}
            bgColor="bg-blue-500/20"
          />
          <StatsCard
            title="Active Agents"
            value={`${dashboardStats.activeAgents} / ${dashboardStats.totalAgents}`}
            icon={<Users className="w-6 h-6 text-purple-400" />}
            trend="Active"
            trendUp={true}
            bgColor="bg-purple-500/20"
          />
          <StatsCard
            title="Success Rate"
            value={`${dashboardStats.successRate}%`}
            icon={<CheckCircle className="w-6 h-6 text-green-400" />}
            trend={`${dashboardStats.successRate}%`}
            trendUp={dashboardStats.successRate > 95}
            bgColor="bg-green-500/20"
          />
          <StatsCard
            title="Security Events"
            value={dashboardStats.securityEvents.toString()}
            icon={<Shield className="w-6 h-6 text-red-400" />}
            trend={`${dashboardStats.threatsBlocked} Blocked`}
            trendUp={false}
            bgColor="bg-red-500/20"
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Agent Status Panel */}
          <div className="lg:col-span-2 bg-gray-800 rounded-xl border border-gray-700">
            <div className="p-6 border-b border-gray-700">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold flex items-center">
                  <GitBranch className="w-5 h-5 mr-2" />
                  Multi-Agent System Status
                </h2>
                <button className="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg text-sm font-medium transition-colors">
                  Deploy New Agent
                </button>
              </div>
            </div>

            <div className="p-6 space-y-4">
              {/* Agent Cards Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {agents?.map((agent) => (
                  <AgentCard
                    key={agent.id}
                    agent={agent}
                    isSelected={selectedAgent === agent.id}
                    onClick={() => setSelectedAgent(agent.id)}
                  />
                ))}
              </div>

              {/* Coordinator Status */}
              {agents?.find(a => a.type === 'coordinator') && (
                <div className="mt-4">
                  <div className="bg-gradient-to-r from-purple-500 to-pink-500 p-[2px] rounded-lg">
                    <div className="bg-gray-800 rounded-lg p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center">
                          <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-pink-500 rounded-lg flex items-center justify-center mr-4">
                            <Command className="w-6 h-6 text-white" />
                          </div>
                          <div>
                            <div className="font-semibold text-lg">Coordinator Agent</div>
                            <div className="text-sm text-gray-400">
                              Orchestrating {agents.filter(a => a.type !== 'coordinator').length} sub-agents
                            </div>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-2xl font-bold text-green-400">Active</div>
                          <div className="text-sm text-gray-400">12 delegations/hour</div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Right Side Panels */}
          <div className="space-y-6">
            <SecurityMonitor security={security} />
            <LearningMetrics learning={learning} />
          </div>
        </div>

        {/* Bottom Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
          <ActivityLog activities={activities} />
          <QuickActions onAction={(action) => console.log('Action:', action)} />
        </div>
      </div>
    </div>
  );
};

export default AGIDashboard;