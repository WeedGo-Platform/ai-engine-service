import React, { useState, useEffect, useCallback } from 'react';
import {
  Activity,
  Brain,
  Shield,
  Zap,
  Users,
  Settings,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  TrendingUp,
  Clock,
  Database,
  Lock,
  Cpu,
  BarChart3,
  Play,
  Pause,
  RotateCcw
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import toast from 'react-hot-toast';

interface Agent {
  id: string;
  name: string;
  type: string;
  model: string;
  status: 'active' | 'idle' | 'error' | 'restarting';
  tasks: number;
  successRate: number;
  currentLoad: number;
}

interface SystemStats {
  totalRequests: number;
  successRate: number;
  averageResponseTime: number;
  activeUsers: number;
  peakLoad: number;
  uptime: number;
}

interface Activity {
  id: string;
  timestamp: string;
  type: string;
  message: string;
}

interface SecurityStatus {
  contentFiltering: string;
  rateLimiting: string;
  accessControl: string;
  totalEvents: number;
  threatsBlocked: number;
  lastThreat?: {
    type: string;
    timestamp: string;
  };
}

interface LearningMetrics {
  patternCount: number;
  feedbackPositive: number;
  adaptationsToday: number;
  learningRate: number;
  confidenceScore: number;
}

const AGIDashboard: React.FC = () => {
  const { token } = useAuth();
  const [agents, setAgents] = useState<Agent[]>([]);
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [activities, setActivities] = useState<Activity[]>([]);
  const [security, setSecurity] = useState<SecurityStatus | null>(null);
  const [learning, setLearning] = useState<LearningMetrics | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [wsConnection, setWsConnection] = useState<WebSocket | null>(null);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);

  const apiBaseUrl = 'http://localhost:5024/agi/api';
  const wsUrl = 'ws://localhost:5024/agi/ws';

  // Fetch agents data
  const fetchAgents = useCallback(async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/agents`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();
      setAgents(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Error fetching agents:', error);
      toast.error('Failed to fetch agents data');
      setAgents([]);
    }
  }, [token]);

  // Fetch system stats
  const fetchStats = useCallback(async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/stats`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  }, [token]);

  // Fetch activities
  const fetchActivities = useCallback(async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/activities?limit=20`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();
      setActivities(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Error fetching activities:', error);
      setActivities([]);
    }
  }, [token]);

  // Fetch security status
  const fetchSecurity = useCallback(async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/security/status`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();
      setSecurity(data);
    } catch (error) {
      console.error('Error fetching security status:', error);
    }
  }, [token]);

  // Fetch learning metrics
  const fetchLearning = useCallback(async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/learning/metrics`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();
      setLearning(data);
    } catch (error) {
      console.error('Error fetching learning metrics:', error);
    }
  }, [token]);

  // Initialize WebSocket connection
  useEffect(() => {
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('WebSocket connected');
      ws.send(JSON.stringify({ type: 'auth', token }));
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      switch(data.type) {
        case 'agent_update':
          setAgents(prev => prev.map(agent =>
            agent.id === data.agentId ? { ...agent, ...data.update } : agent
          ));
          break;
        case 'stats_update':
          setStats(data.stats);
          break;
        case 'activity':
          setActivities(prev => [data.activity, ...prev.slice(0, 19)]);
          break;
        case 'security_update':
          setSecurity(prev => ({ ...prev, ...data.update }));
          break;
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
    };

    setWsConnection(ws);

    return () => {
      ws.close();
    };
  }, [token, wsUrl]);

  // Initial data fetch
  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      await Promise.all([
        fetchAgents(),
        fetchStats(),
        fetchActivities(),
        fetchSecurity(),
        fetchLearning()
      ]);
      setIsLoading(false);
    };
    fetchData();
  }, [fetchAgents, fetchStats, fetchActivities, fetchSecurity, fetchLearning]);

  // Agent actions
  const handleAgentAction = async (agentId: string, action: string) => {
    try {
      const response = await fetch(`${apiBaseUrl}/agents/${agentId}/actions`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ action })
      });

      if (response.ok) {
        toast.success(`Agent ${action} initiated`);
        fetchAgents();
      } else {
        toast.error(`Failed to ${action} agent`);
      }
    } catch (error) {
      console.error('Error performing agent action:', error);
      toast.error('Action failed');
    }
  };

  // System actions
  const handleSystemAction = async (action: string) => {
    try {
      const response = await fetch(`${apiBaseUrl}/system/${action}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        toast.success(`System ${action} completed`);
      } else {
        toast.error(`Failed to ${action} system`);
      }
    } catch (error) {
      console.error('Error performing system action:', error);
      toast.error('Action failed');
    }
  };

  const getStatusColor = (status: string) => {
    switch(status) {
      case 'active': return 'bg-green-100 text-green-800';
      case 'idle': return 'bg-gray-100 text-gray-800';
      case 'error': return 'bg-red-100 text-red-800';
      case 'restarting': return 'bg-yellow-100 text-yellow-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getActivityIcon = (type: string) => {
    switch(type) {
      case 'MODEL': return <Brain className="h-4 w-4" />;
      case 'TOOL': return <Settings className="h-4 w-4" />;
      case 'AGENT': return <Users className="h-4 w-4" />;
      case 'AUTH': return <Lock className="h-4 w-4" />;
      case 'SECURITY': return <Shield className="h-4 w-4" />;
      default: return <Activity className="h-4 w-4" />;
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with System Actions */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">AGI Engine Dashboard</h1>
          <p className="text-gray-600">Monitor and manage your AI agents and system</p>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={() => handleSystemAction('restart-agents')}
            className="px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center space-x-2"
          >
            <RotateCcw className="h-4 w-4" />
            <span>Restart All Agents</span>
          </button>
          <button
            onClick={() => handleSystemAction('clear-cache')}
            className="px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center space-x-2"
          >
            <RefreshCw className="h-4 w-4" />
            <span>Clear Cache</span>
          </button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Requests</p>
              <p className="text-2xl font-bold text-gray-900">{stats?.totalRequests?.toLocaleString() || '0'}</p>
              <p className="text-xs text-gray-500 mt-1">Last 24 hours</p>
            </div>
            <Activity className="h-8 w-8 text-blue-500" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Success Rate</p>
              <p className="text-2xl font-bold text-gray-900">{stats?.successRate || 0}%</p>
              <p className="text-xs text-gray-500 mt-1">Overall performance</p>
            </div>
            <CheckCircle className="h-8 w-8 text-green-500" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Response Time</p>
              <p className="text-2xl font-bold text-gray-900">{stats?.averageResponseTime || 0}ms</p>
              <p className="text-xs text-gray-500 mt-1">Average</p>
            </div>
            <Clock className="h-8 w-8 text-purple-500" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">System Uptime</p>
              <p className="text-2xl font-bold text-gray-900">{stats?.uptime || 0}%</p>
              <p className="text-xs text-gray-500 mt-1">Last 30 days</p>
            </div>
            <TrendingUp className="h-8 w-8 text-indigo-500" />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Agents Panel */}
        <div className="lg:col-span-2 bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900 flex items-center">
              <Brain className="h-5 w-5 mr-2" />
              AI Agents
            </h2>
          </div>
          <div className="divide-y divide-gray-200">
            {agents && agents.length > 0 ? agents.map(agent => (
              <div key={agent.id} className="p-4 hover:bg-gray-50">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3">
                      <h3 className="text-sm font-medium text-gray-900">{agent.name}</h3>
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(agent.status)}`}>
                        {agent.status}
                      </span>
                    </div>
                    <div className="mt-1 grid grid-cols-3 gap-4 text-xs text-gray-500">
                      <div>Model: {agent.model}</div>
                      <div>Tasks: {agent.tasks}</div>
                      <div>Success: {agent.successRate}%</div>
                    </div>
                    <div className="mt-2">
                      <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
                        <span>Current Load</span>
                        <span>{agent.currentLoad}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${agent.currentLoad}%` }}
                        />
                      </div>
                    </div>
                  </div>
                  <div className="ml-4 flex space-x-2">
                    <button
                      onClick={() => handleAgentAction(agent.id, 'restart')}
                      className="p-2 text-gray-400 hover:text-gray-600"
                      title="Restart Agent"
                    >
                      <RotateCcw className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => setSelectedAgent(agent)}
                      className="p-2 text-gray-400 hover:text-gray-600"
                      title="View Details"
                    >
                      <Settings className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </div>
            )) : (
              <div className="p-8 text-center text-gray-500">
                No agents available
              </div>
            )}
          </div>
        </div>

        {/* Activity Feed */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900 flex items-center">
              <Activity className="h-5 w-5 mr-2" />
              Activity Feed
            </h2>
          </div>
          <div className="max-h-96 overflow-y-auto">
            {activities && activities.length > 0 ? activities.map(activity => (
              <div key={activity.id} className="p-4 border-b border-gray-100 hover:bg-gray-50">
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0">
                    {getActivityIcon(activity.type)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-900">{activity.message}</p>
                    <p className="text-xs text-gray-500 mt-1">{activity.timestamp}</p>
                  </div>
                </div>
              </div>
            )) : (
              <div className="p-8 text-center text-gray-500">
                No activities to display
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Bottom Panels */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Security Status */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900 flex items-center">
              <Shield className="h-5 w-5 mr-2" />
              Security Status
            </h2>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Content Filtering</span>
                <span className="px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded-full">
                  {security?.contentFiltering}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Rate Limiting</span>
                <span className="px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded-full">
                  {security?.rateLimiting}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Access Control</span>
                <span className="text-sm text-gray-900">{security?.accessControl}</span>
              </div>
              <div className="pt-4 border-t border-gray-200">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-xs text-gray-500">Security Events</p>
                    <p className="text-2xl font-bold text-gray-900">{security?.totalEvents}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Threats Blocked</p>
                    <p className="text-2xl font-bold text-red-600">{security?.threatsBlocked}</p>
                  </div>
                </div>
                {security?.lastThreat && (
                  <div className="mt-4 p-3 bg-red-50 rounded-lg">
                    <p className="text-xs text-red-600 font-medium">Last Threat</p>
                    <p className="text-sm text-red-800 mt-1">{security.lastThreat.type}</p>
                    <p className="text-xs text-red-500 mt-1">{security.lastThreat.timestamp}</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Learning Metrics */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900 flex items-center">
              <Zap className="h-5 w-5 mr-2" />
              Learning & Adaptation
            </h2>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm text-gray-600">Pattern Recognition</span>
                  <span className="text-sm font-medium text-gray-900">{learning?.patternCount} patterns</span>
                </div>
              </div>
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm text-gray-600">Positive Feedback</span>
                  <span className="text-sm font-medium text-gray-900">{learning?.feedbackPositive}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-green-600 h-2 rounded-full"
                    style={{ width: `${learning?.feedbackPositive}%` }}
                  />
                </div>
              </div>
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm text-gray-600">Learning Rate</span>
                  <span className="text-sm font-medium text-gray-900">{learning?.learningRate}</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full"
                    style={{ width: `${(learning?.learningRate || 0) * 100}%` }}
                  />
                </div>
              </div>
              <div className="pt-4 border-t border-gray-200">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-xs text-gray-500">Adaptations Today</p>
                    <p className="text-2xl font-bold text-gray-900">{learning?.adaptationsToday}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Confidence Score</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {((learning?.confidenceScore || 0) * 100).toFixed(1)}%
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Agent Detail Modal */}
      {selectedAgent && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="flex justify-between items-start mb-4">
              <h2 className="text-xl font-semibold text-gray-900">{selectedAgent.name}</h2>
              <button
                onClick={() => setSelectedAgent(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-500">Type</p>
                  <p className="text-base font-medium text-gray-900">{selectedAgent.type}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Model</p>
                  <p className="text-base font-medium text-gray-900">{selectedAgent.model}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Status</p>
                  <span className={`inline-block px-2 py-1 text-sm font-medium rounded-full ${getStatusColor(selectedAgent.status)}`}>
                    {selectedAgent.status}
                  </span>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Total Tasks</p>
                  <p className="text-base font-medium text-gray-900">{selectedAgent.tasks}</p>
                </div>
              </div>
              <div className="flex space-x-2">
                <button
                  onClick={() => {
                    handleAgentAction(selectedAgent.id, 'restart');
                    setSelectedAgent(null);
                  }}
                  className="flex-1 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
                >
                  Restart Agent
                </button>
                <button
                  onClick={() => setSelectedAgent(null)}
                  className="flex-1 px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AGIDashboard;