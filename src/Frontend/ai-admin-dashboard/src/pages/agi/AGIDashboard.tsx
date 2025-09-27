/**
 * AGI Dashboard - Main Component
 * Implements the exact tabbed interface from the original design
 */

import React, { useState, useEffect } from 'react';
import { Brain, Shield, TrendingUp, Settings, Activity, AlertTriangle } from 'lucide-react';
import { agiApi } from './services/api';
import {
  Agent,
  SystemStats,
  SecurityData,
  LearningMetrics,
  Activity as ActivityItem,
  WebSocketMessage
} from './types';

// Import tab components
import OverviewTab from './components/tabs/OverviewTab';
import AgentsTab from './components/tabs/AgentsTab';
import SecurityTab from './components/tabs/SecurityTab';
import LearningTab from './components/tabs/LearningTab';
import SystemTab from './components/tabs/SystemTab';

type TabType = 'overview' | 'agents' | 'security' | 'learning' | 'system';

const AGIDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [agents, setAgents] = useState<Agent[]>([]);
  const [systemStats, setSystemStats] = useState<SystemStats | null>(null);
  const [securityData, setSecurityData] = useState<SecurityData | null>(null);
  const [learningMetrics, setLearningMetrics] = useState<LearningMetrics | null>(null);
  const [activities, setActivities] = useState<ActivityItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch initial data
  useEffect(() => {
    fetchDashboardData();

    // Setup WebSocket connection for real-time updates
    const handleWebSocketMessage = (msg: WebSocketMessage) => {
      switch (msg.type) {
        case 'agent_update':
          if (msg.agentId && msg.update) {
            setAgents(prev => prev.map(agent =>
              agent.id === msg.agentId ? { ...agent, ...msg.update } : agent
            ));
          }
          break;
        case 'stats_update':
          if (msg.stats) {
            setSystemStats(msg.stats);
          }
          break;
        case 'security_update':
          // Refresh security data
          fetchSecurityData();
          break;
      }
    };

    agiApi.connectWebSocket(handleWebSocketMessage);

    // Refresh data every 30 seconds
    const interval = setInterval(fetchDashboardData, 30000);

    return () => {
      clearInterval(interval);
      agiApi.disconnectWebSocket(handleWebSocketMessage);
    };
  }, []);

  const fetchDashboardData = async () => {
    setLoading(true);
    setError(null);

    try {
      const [
        agentsData,
        statsData,
        securityStatus,
        learningData,
        activitiesData
      ] = await Promise.all([
        agiApi.getAgents(),
        agiApi.getSystemStats(),
        agiApi.getSecurityStatus(),
        agiApi.getLearningMetrics(),
        agiApi.getActivities(20)
      ]);

      setAgents(agentsData);
      setSystemStats(statsData);
      setSecurityData(securityStatus);
      setLearningMetrics(learningData);
      setActivities(activitiesData);
    } catch (err) {
      setError('Failed to load dashboard data. Please ensure the AGI service is running on port 5024.');
      console.error('Dashboard data fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchSecurityData = async () => {
    try {
      const data = await agiApi.getSecurityStatus();
      setSecurityData(data);
    } catch (err) {
      console.error('Failed to fetch security data:', err);
    }
  };

  const handleAgentAction = async (agentId: string, action: string) => {
    try {
      await agiApi.executeAgentAction(agentId, action);
      // Refresh agent data
      const updatedAgents = await agiApi.getAgents();
      setAgents(updatedAgents);
    } catch (err) {
      console.error('Failed to execute agent action:', err);
    }
  };

  const tabs = [
    { id: 'overview' as TabType, label: 'Overview', icon: Brain },
    { id: 'agents' as TabType, label: 'Agents', icon: Activity },
    { id: 'security' as TabType, label: 'Security', icon: Shield },
    { id: 'learning' as TabType, label: 'Learning', icon: TrendingUp },
    { id: 'system' as TabType, label: 'System', icon: Settings },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md">
          <div className="flex items-center">
            <AlertTriangle className="h-5 w-5 text-red-600 mr-2" />
            <h3 className="text-red-900 font-semibold">Connection Error</h3>
          </div>
          <p className="text-red-700 mt-2">{error}</p>
          <button
            onClick={fetchDashboardData}
            className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <Brain className="h-8 w-8 text-primary-600 mr-3" />
              <h1 className="text-2xl font-bold text-gray-900">AGI Dashboard</h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-500">
                Last updated: {new Date().toLocaleTimeString()}
              </span>
              <button
                onClick={fetchDashboardData}
                className="px-3 py-1 text-sm bg-primary-600 text-white rounded-lg hover:bg-primary-700"
              >
                Refresh
              </button>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="px-6">
          <nav className="flex space-x-8 border-b border-gray-200 -mb-px">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`
                    group inline-flex items-center py-4 px-1 border-b-2 font-medium text-sm
                    ${activeTab === tab.id
                      ? 'border-primary-500 text-primary-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }
                  `}
                >
                  <Icon className={`
                    mr-2 h-5 w-5
                    ${activeTab === tab.id ? 'text-primary-500' : 'text-gray-400 group-hover:text-gray-500'}
                  `} />
                  {tab.label}
                </button>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-hidden">
        {activeTab === 'overview' && (
          <OverviewTab
            agents={agents}
            systemStats={systemStats}
            securityData={securityData}
            learningMetrics={learningMetrics}
            activities={activities}
            onAgentAction={handleAgentAction}
          />
        )}
        {activeTab === 'agents' && (
          <AgentsTab
            agents={agents}
            onAgentAction={handleAgentAction}
          />
        )}
        {activeTab === 'security' && (
          <SecurityTab
            securityData={securityData}
            onRefresh={fetchSecurityData}
          />
        )}
        {activeTab === 'learning' && (
          <LearningTab
            metrics={learningMetrics}
          />
        )}
        {activeTab === 'system' && (
          <SystemTab
            onRefresh={fetchDashboardData}
          />
        )}
      </div>
    </div>
  );
};

export default AGIDashboard;