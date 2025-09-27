/**
 * Overview Tab Component
 * Displays 4-panel grid: System Health, Active Agents, Performance Metrics, Quick Actions
 */

import React, { useEffect, useState } from 'react';
import {
  Heart, Activity, TrendingUp, Zap, Users, Clock,
  CheckCircle, AlertTriangle, Shield, Brain, RefreshCw, Power
} from 'lucide-react';
import { Agent, SystemStats, SecurityData, LearningMetrics, Activity as ActivityItem } from '../../types';
import PerformanceChart from '../charts/PerformanceChart';
import ActivityTimeline from '../charts/ActivityTimeline';
import { agiApi } from '../../services/api';

interface OverviewTabProps {
  agents: Agent[];
  systemStats: SystemStats | null;
  securityData: SecurityData | null;
  learningMetrics: LearningMetrics | null;
  activities: ActivityItem[];
  onAgentAction: (agentId: string, action: string) => void;
}

const OverviewTab: React.FC<OverviewTabProps> = ({
  agents,
  systemStats,
  securityData,
  learningMetrics,
  activities,
  onAgentAction
}) => {
  const activeAgents = agents.filter(a => a.status === 'active').length;
  const totalTasks = agents.reduce((sum, a) => sum + a.tasks, 0);
  const avgSuccessRate = agents.reduce((sum, a) => sum + a.successRate, 0) / agents.length || 0;

  const [performanceData, setPerformanceData] = useState<any[]>([]);
  const [activityData, setActivityData] = useState<any[]>([]);

  useEffect(() => {
    loadChartData();
    const interval = setInterval(loadChartData, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadChartData = async () => {
    try {
      const metrics = await agiApi.getMetrics();
      const performance = metrics.slice(-20).map((m: any, idx: number) => ({
        time: new Date(Date.now() - (20 - idx) * 60000).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
        successRate: m.success_rate,
        responseTime: m.response_time,
        throughput: m.throughput
      }));
      setPerformanceData(performance);

      const activity = metrics.slice(-10).map((m: any, idx: number) => ({
        time: new Date(Date.now() - (10 - idx) * 60000).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
        activeAgents: m.active_agents,
        tasksProcessed: m.tasks_processed
      }));
      setActivityData(activity);
    } catch (error) {
      console.error('Failed to load chart data:', error);
    }
  };

  return (
    <div className="p-6 space-y-6 overflow-y-auto h-full">
      {/* 4-Panel Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Panel 1: System Health */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center">
              <Heart className="h-5 w-5 text-green-500 mr-2" />
              System Health
            </h3>
            <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-medium rounded-full">
              Healthy
            </span>
          </div>

          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Uptime</span>
              <span className="text-sm font-semibold text-gray-900">
                {systemStats?.uptime ? `${systemStats.uptime.toFixed(1)}%` : '--'}
              </span>
            </div>

            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Response Time</span>
              <span className="text-sm font-semibold text-gray-900">
                {systemStats?.averageResponseTime ? `${systemStats.averageResponseTime}ms` : '--'}
              </span>
            </div>

            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Success Rate</span>
              <span className="text-sm font-semibold text-gray-900">
                {systemStats?.successRate ? `${systemStats.successRate.toFixed(1)}%` : '--'}
              </span>
            </div>

            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Peak Load</span>
              <span className="text-sm font-semibold text-gray-900">
                {systemStats?.peakLoad ? `${systemStats.peakLoad}%` : '--'}
              </span>
            </div>

            <div className="mt-4 pt-4 border-t border-gray-200">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Security Status</span>
                <span className="flex items-center">
                  <Shield className={`h-4 w-4 mr-1 ${
                    securityData?.contentFiltering === 'active' ? 'text-green-500' : 'text-yellow-500'
                  }`} />
                  <span className="text-sm font-semibold">
                    {securityData?.threatsBlocked || 0} threats blocked
                  </span>
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Panel 2: Active Agents */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center">
              <Activity className="h-5 w-5 text-blue-500 mr-2" />
              Active Agents
            </h3>
            <span className="text-sm text-gray-500">{activeAgents} / {agents.length}</span>
          </div>

          <div className="space-y-3">
            {agents.slice(0, 5).map((agent) => (
              <div key={agent.id} className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className={`w-2 h-2 rounded-full mr-2 ${
                    agent.status === 'active' ? 'bg-green-500' :
                    agent.status === 'idle' ? 'bg-yellow-500' : 'bg-gray-500'
                  }`} />
                  <div>
                    <span className="text-sm font-medium text-gray-900">{agent.name}</span>
                    <span className="text-xs text-gray-500 ml-2">{agent.model}</span>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-xs text-gray-500">{agent.currentLoad}%</span>
                  <div className="w-20 bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${
                        agent.currentLoad > 80 ? 'bg-red-500' :
                        agent.currentLoad > 50 ? 'bg-yellow-500' : 'bg-green-500'
                      }`}
                      style={{ width: `${agent.currentLoad}%` }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-4 pt-4 border-t border-gray-200">
            <div className="grid grid-cols-3 gap-2 text-center">
              <div>
                <span className="block text-2xl font-bold text-gray-900">{totalTasks}</span>
                <span className="text-xs text-gray-500">Total Tasks</span>
              </div>
              <div>
                <span className="block text-2xl font-bold text-gray-900">
                  {avgSuccessRate.toFixed(1)}%
                </span>
                <span className="text-xs text-gray-500">Avg Success</span>
              </div>
              <div>
                <span className="block text-2xl font-bold text-gray-900">{activeAgents}</span>
                <span className="text-xs text-gray-500">Active</span>
              </div>
            </div>
          </div>
        </div>

        {/* Panel 3: Performance Metrics */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center">
              <TrendingUp className="h-5 w-5 text-purple-500 mr-2" />
              Performance Metrics
            </h3>
            <button onClick={loadChartData} className="text-gray-400 hover:text-gray-600">
              <RefreshCw className="h-4 w-4" />
            </button>
          </div>

          <div className="space-y-4">
            <div>
              <div className="flex justify-between mb-1">
                <span className="text-sm text-gray-600">Total Requests</span>
                <span className="text-sm font-semibold text-gray-900">
                  {systemStats?.totalRequests?.toLocaleString() || '0'}
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div className="bg-purple-500 h-2 rounded-full" style={{ width: '75%' }} />
              </div>
            </div>

            <div>
              <div className="flex justify-between mb-1">
                <span className="text-sm text-gray-600">Active Users</span>
                <span className="text-sm font-semibold text-gray-900">
                  {systemStats?.activeUsers || 0}
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div className="bg-blue-500 h-2 rounded-full" style={{ width: '60%' }} />
              </div>
            </div>

            <div>
              <div className="flex justify-between mb-1">
                <span className="text-sm text-gray-600">Learning Progress</span>
                <span className="text-sm font-semibold text-gray-900">
                  {learningMetrics?.patternCount || 0} patterns
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div className="bg-green-500 h-2 rounded-full"
                     style={{ width: `${learningMetrics?.learningRate ? learningMetrics.learningRate * 100 : 0}%` }} />
              </div>
            </div>

            <div className="mt-4 pt-4 border-t border-gray-200">
              <div className="grid grid-cols-2 gap-4 text-center">
                <div>
                  <span className="block text-xl font-bold text-gray-900">
                    {learningMetrics?.feedbackPositive || 0}%
                  </span>
                  <span className="text-xs text-gray-500">Positive Feedback</span>
                </div>
                <div>
                  <span className="block text-xl font-bold text-gray-900">
                    {learningMetrics?.adaptationsToday || 0}
                  </span>
                  <span className="text-xs text-gray-500">Adaptations Today</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Panel 4: Quick Actions */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center">
              <Zap className="h-5 w-5 text-yellow-500 mr-2" />
              Quick Actions
            </h3>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <button
              onClick={() => agents.forEach(a => onAgentAction(a.id, 'restart'))}
              className="flex flex-col items-center justify-center p-4 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <RefreshCw className="h-6 w-6 text-blue-600 mb-2" />
              <span className="text-sm font-medium text-gray-900">Restart All</span>
            </button>

            <button
              className="flex flex-col items-center justify-center p-4 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <Shield className="h-6 w-6 text-green-600 mb-2" />
              <span className="text-sm font-medium text-gray-900">Security Scan</span>
            </button>

            <button
              className="flex flex-col items-center justify-center p-4 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <Brain className="h-6 w-6 text-purple-600 mb-2" />
              <span className="text-sm font-medium text-gray-900">Train Models</span>
            </button>

            <button
              className="flex flex-col items-center justify-center p-4 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <Power className="h-6 w-6 text-red-600 mb-2" />
              <span className="text-sm font-medium text-gray-900">Emergency Stop</span>
            </button>
          </div>

          <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
            <div className="flex items-start">
              <AlertTriangle className="h-5 w-5 text-yellow-600 mr-2 flex-shrink-0" />
              <div>
                <h4 className="text-sm font-medium text-yellow-900">System Notice</h4>
                <p className="text-xs text-yellow-700 mt-1">
                  All systems operational. Next maintenance window in 48 hours.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Performance Chart */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Performance Trends</h3>
        <PerformanceChart data={performanceData} />
      </div>

      {/* Activity Timeline Chart */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Activity Timeline</h3>
        <ActivityTimeline data={activityData} />
      </div>

      {/* Activity Stream */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <Clock className="h-5 w-5 text-gray-500 mr-2" />
          Recent Activity
        </h3>

        <div className="space-y-2 max-h-40 overflow-y-auto">
          {activities.map((activity) => (
            <div key={activity.id} className="flex items-center text-sm">
              <span className="text-gray-400 w-20">{activity.timestamp}</span>
              <span className={`px-2 py-1 rounded text-xs font-medium mr-2 ${
                activity.type === 'MODEL' ? 'bg-purple-100 text-purple-700' :
                activity.type === 'AGENT' ? 'bg-blue-100 text-blue-700' :
                activity.type === 'SECURITY' ? 'bg-red-100 text-red-700' :
                activity.type === 'AUTH' ? 'bg-green-100 text-green-700' :
                'bg-gray-100 text-gray-700'
              }`}>
                {activity.type}
              </span>
              <span className="text-gray-700">{activity.message}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default OverviewTab;