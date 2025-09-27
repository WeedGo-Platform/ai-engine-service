import { useState, useEffect, useCallback } from 'react';
import { Agent } from '../pages/admin/agi/components/AgentCard';
import { ActivityEntry } from '../pages/admin/agi/components/ActivityLog';
import agiService from '../services/agiService';

interface AGIStats {
  totalRequests: number;
  successRate: number;
  averageResponseTime: number;
}

interface SecurityData {
  contentFiltering: 'active' | 'inactive';
  rateLimiting: 'active' | 'inactive';
  accessControl: string;
  totalEvents: number;
  threatsBlocked: number;
  lastThreat?: {
    type: string;
    timestamp: string;
  };
}

interface LearningData {
  patternCount: number;
  feedbackPositive: number;
  adaptationsToday: number;
}

export const useAGIEngine = () => {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [stats, setStats] = useState<AGIStats | null>(null);
  const [activities, setActivities] = useState<ActivityEntry[]>([]);
  const [security, setSecurity] = useState<SecurityData | null>(null);
  const [learning, setLearning] = useState<LearningData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAgents = useCallback(async () => {
    try {
      const data = await agiService.getAgents();
      setAgents(data);
    } catch (err) {
      console.error('Failed to fetch agents:', err);
      setError('Failed to fetch agents');
    }
  }, []);

  const fetchStats = useCallback(async () => {
    try {
      const data = await agiService.getStats();
      setStats(data);
    } catch (err) {
      console.error('Failed to fetch stats:', err);
      setError('Failed to fetch stats');
    }
  }, []);

  const fetchActivities = useCallback(async () => {
    try {
      const data = await agiService.getActivities();
      setActivities(data);
    } catch (err) {
      console.error('Failed to fetch activities:', err);
      setError('Failed to fetch activities');
    }
  }, []);

  const fetchSecurity = useCallback(async () => {
    try {
      const data = await agiService.getSecurityStatus();
      setSecurity(data);
    } catch (err) {
      console.error('Failed to fetch security status:', err);
      setError('Failed to fetch security status');
    }
  }, []);

  const fetchLearning = useCallback(async () => {
    try {
      const data = await agiService.getLearningMetrics();
      setLearning(data);
    } catch (err) {
      console.error('Failed to fetch learning metrics:', err);
      setError('Failed to fetch learning metrics');
    }
  }, []);

  const refreshData = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    await Promise.all([
      fetchAgents(),
      fetchStats(),
      fetchActivities(),
      fetchSecurity(),
      fetchLearning()
    ]);

    setIsLoading(false);
  }, [fetchAgents, fetchStats, fetchActivities, fetchSecurity, fetchLearning]);

  const executeAgentAction = useCallback(async (agentId: string, action: string) => {
    try {
      await agiService.executeAgentAction(agentId, action);
      await fetchAgents(); // Refresh agents after action
    } catch (err) {
      console.error('Failed to execute agent action:', err);
      setError('Failed to execute agent action');
    }
  }, [fetchAgents]);

  const updateSecurityRule = useCallback(async (rule: string, value: any) => {
    try {
      await agiService.updateSecurityRule(rule, value);
      await fetchSecurity(); // Refresh security status
    } catch (err) {
      console.error('Failed to update security rule:', err);
      setError('Failed to update security rule');
    }
  }, [fetchSecurity]);

  useEffect(() => {
    // Initial data fetch
    refreshData();

    // Set up WebSocket connection for real-time updates
    const ws = agiService.connectWebSocket();

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      switch (data.type) {
        case 'agent_update':
          setAgents(prev => prev.map(agent =>
            agent.id === data.agentId ? { ...agent, ...data.update } : agent
          ));
          break;
        case 'new_activity':
          setActivities(prev => [data.activity, ...prev].slice(0, 100));
          break;
        case 'stats_update':
          setStats(data.stats);
          break;
        case 'security_alert':
          setSecurity(prev => prev ? { ...prev, ...data.security } : data.security);
          break;
        case 'learning_update':
          setLearning(data.learning);
          break;
      }
    };

    return () => {
      ws.close();
    };
  }, []);

  return {
    agents,
    stats,
    activities,
    security,
    learning,
    isLoading,
    error,
    refreshData,
    executeAgentAction,
    updateSecurityRule
  };
};