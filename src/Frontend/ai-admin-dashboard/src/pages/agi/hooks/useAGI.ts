/**
 * Custom React Hooks for AGI Functionality
 * Provides reusable hooks for common AGI operations
 * Following DRY principle and React best practices
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { agiApi, AGIApiError } from '../services/agiApi';
import { wsService, WSMessageType } from '../services/websocket';
import {
  IAgent, IAgentDetails, IAgentStats, IAgentTask,
  ISystemStats, IActivity, ISecurityStatus, ISecurityEvent,
  ILearningMetrics, IPattern, IFeedback, IRateLimit,
  IAuditLog, IAuditLogQuery, IChatRequest, IChatResponse
} from '../types';

/**
 * Generic hook state interface
 */
interface IUseAsyncState<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
}

/**
 * Generic hook for async data fetching
 */
export function useAsyncData<T>(
  fetchFn: () => Promise<T>,
  dependencies: any[] = []
): IUseAsyncState<T> & { refetch: () => Promise<void> } {
  const [state, setState] = useState<IUseAsyncState<T>>({
    data: null,
    loading: true,
    error: null
  });

  const refetch = useCallback(async () => {
    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      const data = await fetchFn();
      setState({ data, loading: false, error: null });
    } catch (error) {
      setState({ data: null, loading: false, error: error as Error });
    }
  }, [fetchFn]);

  useEffect(() => {
    refetch();
  }, dependencies);

  return { ...state, refetch };
}

/**
 * Hook for agent management
 */
export function useAgents() {
  const { data: agents, loading, error, refetch } = useAsyncData(
    () => agiApi.getAgents(),
    []
  );

  // Subscribe to real-time agent updates
  useEffect(() => {
    const unsubscribe = wsService.subscribe(
      WSMessageType.AGENT_STATUS_CHANGED,
      () => refetch()
    );

    return unsubscribe;
  }, [refetch]);

  return { agents: agents || [], loading, error, refetch };
}

/**
 * Hook for individual agent details with real-time updates
 */
export function useAgentDetails(agentId: string) {
  const [details, setDetails] = useState<IAgentDetails | null>(null);
  const [stats, setStats] = useState<IAgentStats | null>(null);
  const [tasks, setTasks] = useState<IAgentTask[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchAgentData = useCallback(async () => {
    if (!agentId) return;

    setLoading(true);
    setError(null);

    try {
      const [detailsData, statsData, tasksData] = await Promise.all([
        agiApi.getAgentDetails(agentId),
        agiApi.getAgentStats(agentId),
        agiApi.getAgentTasks(agentId, 10)
      ]);

      setDetails(detailsData);
      setStats(statsData);
      setTasks(tasksData);
    } catch (err) {
      setError(err as Error);
    } finally {
      setLoading(false);
    }
  }, [agentId]);

  useEffect(() => {
    fetchAgentData();
  }, [fetchAgentData]);

  // Subscribe to real-time updates
  useEffect(() => {
    const unsubscribeStatus = wsService.subscribe(
      WSMessageType.AGENT_STATUS_CHANGED,
      (agent: IAgent) => {
        if (agent.id === agentId) {
          fetchAgentData();
        }
      }
    );

    const unsubscribeTask = wsService.subscribe(
      WSMessageType.AGENT_TASK_UPDATED,
      (task: IAgentTask) => {
        if (task.agent_id === agentId) {
          setTasks(prev => {
            const index = prev.findIndex(t => t.id === task.id);
            if (index >= 0) {
              const updated = [...prev];
              updated[index] = task;
              return updated;
            }
            return [task, ...prev].slice(0, 10);
          });
        }
      }
    );

    const unsubscribeMetrics = wsService.subscribe(
      WSMessageType.AGENT_METRICS_UPDATED,
      (metrics: IAgentStats) => {
        if (metrics.agent_id === agentId) {
          setStats(metrics);
        }
      }
    );

    return () => {
      unsubscribeStatus();
      unsubscribeTask();
      unsubscribeMetrics();
    };
  }, [agentId, fetchAgentData]);

  return { details, stats, tasks, loading, error, refetch: fetchAgentData };
}

/**
 * Hook for system statistics with real-time updates
 */
export function useSystemStats(refreshInterval: number = 30000) {
  const [stats, setStats] = useState<ISystemStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchStats = useCallback(async () => {
    try {
      const data = await agiApi.getSystemStats();
      setStats(data);
      setError(null);
    } catch (err) {
      setError(err as Error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, refreshInterval);
    return () => clearInterval(interval);
  }, [fetchStats, refreshInterval]);

  // Subscribe to real-time updates
  useEffect(() => {
    const unsubscribe = wsService.subscribe(
      WSMessageType.SYSTEM_STATS_UPDATED,
      (newStats: ISystemStats) => setStats(newStats)
    );

    return unsubscribe;
  }, []);

  return { stats, loading, error, refetch: fetchStats };
}

/**
 * Hook for activities with real-time updates
 */
export function useActivities(limit: number = 100) {
  const [activities, setActivities] = useState<IActivity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchActivities = useCallback(async () => {
    setLoading(true);
    try {
      const data = await agiApi.getActivities(limit);
      setActivities(data);
      setError(null);
    } catch (err) {
      setError(err as Error);
    } finally {
      setLoading(false);
    }
  }, [limit]);

  useEffect(() => {
    fetchActivities();
  }, [fetchActivities]);

  // Subscribe to real-time activity updates
  useEffect(() => {
    const unsubscribe = wsService.subscribe(
      WSMessageType.ACTIVITY_CREATED,
      (activity: IActivity) => {
        setActivities(prev => [activity, ...prev].slice(0, limit));
      }
    );

    return unsubscribe;
  }, [limit]);

  return { activities, loading, error, refetch: fetchActivities };
}

/**
 * Hook for security monitoring
 */
export function useSecurity() {
  const [status, setStatus] = useState<ISecurityStatus | null>(null);
  const [events, setEvents] = useState<ISecurityEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchSecurityData = useCallback(async () => {
    setLoading(true);
    try {
      const [statusData, eventsData] = await Promise.all([
        agiApi.getSecurityStatus(),
        agiApi.getSecurityEvents(50)
      ]);

      setStatus(statusData);
      setEvents(eventsData);
      setError(null);
    } catch (err) {
      setError(err as Error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSecurityData();
  }, [fetchSecurityData]);

  // Subscribe to real-time security updates
  useEffect(() => {
    const unsubscribeStatus = wsService.subscribe(
      WSMessageType.SECURITY_STATUS_CHANGED,
      (newStatus: ISecurityStatus) => setStatus(newStatus)
    );

    const unsubscribeEvent = wsService.subscribe(
      WSMessageType.SECURITY_EVENT_TRIGGERED,
      (event: ISecurityEvent) => {
        setEvents(prev => [event, ...prev].slice(0, 50));
      }
    );

    return () => {
      unsubscribeStatus();
      unsubscribeEvent();
    };
  }, []);

  return { status, events, loading, error, refetch: fetchSecurityData };
}

/**
 * Hook for learning metrics
 */
export function useLearning() {
  const [metrics, setMetrics] = useState<ILearningMetrics | null>(null);
  const [patterns, setPatterns] = useState<IPattern[]>([]);
  const [feedback, setFeedback] = useState<IFeedback[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchLearningData = useCallback(async () => {
    setLoading(true);
    try {
      const [metricsData, patternsData, feedbackData] = await Promise.all([
        agiApi.getLearningMetrics(),
        agiApi.getPatterns(50),
        agiApi.getFeedback(50)
      ]);

      setMetrics(metricsData);
      setPatterns(patternsData);
      setFeedback(feedbackData);
      setError(null);
    } catch (err) {
      setError(err as Error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchLearningData();
  }, [fetchLearningData]);

  // Subscribe to real-time learning updates
  useEffect(() => {
    const unsubscribeMetrics = wsService.subscribe(
      WSMessageType.LEARNING_METRICS_UPDATED,
      (newMetrics: ILearningMetrics) => setMetrics(newMetrics)
    );

    const unsubscribePattern = wsService.subscribe(
      WSMessageType.PATTERN_DETECTED,
      (pattern: IPattern) => {
        setPatterns(prev => [pattern, ...prev].slice(0, 50));
      }
    );

    const unsubscribeFeedback = wsService.subscribe(
      WSMessageType.FEEDBACK_RECEIVED,
      (fb: IFeedback) => {
        setFeedback(prev => [fb, ...prev].slice(0, 50));
      }
    );

    return () => {
      unsubscribeMetrics();
      unsubscribePattern();
      unsubscribeFeedback();
    };
  }, []);

  return { metrics, patterns, feedback, loading, error, refetch: fetchLearningData };
}

/**
 * Hook for chat functionality with streaming support
 */
export function useChat(sessionId?: string) {
  const [messages, setMessages] = useState<IChatResponse[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState('');
  const [error, setError] = useState<Error | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const sendMessage = useCallback(async (
    message: string,
    options: Partial<IChatRequest> = {}
  ) => {
    setError(null);
    setIsStreaming(true);
    setStreamingContent('');

    try {
      if (options.stream) {
        // Handle streaming response
        const generator = agiApi.streamChat({
          message,
          session_id: sessionId,
          ...options
        });

        let fullContent = '';
        for await (const chunk of generator) {
          fullContent += chunk;
          setStreamingContent(fullContent);
        }

        // Add complete message to history
        const response: IChatResponse = {
          response: fullContent,
          session_id: sessionId || 'default',
          model_used: options.model_id || 'default',
          processing_time: 0,
          tokens_used: { prompt: 0, completion: 0 }
        };

        setMessages(prev => [...prev, response]);
        setStreamingContent('');
      } else {
        // Handle regular response
        const response = await agiApi.sendChatMessage({
          message,
          session_id: sessionId,
          ...options
        });

        setMessages(prev => [...prev, response]);
      }
    } catch (err) {
      setError(err as Error);
    } finally {
      setIsStreaming(false);
    }
  }, [sessionId]);

  const stopStreaming = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsStreaming(false);
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setStreamingContent('');
    setError(null);
  }, []);

  return {
    messages,
    isStreaming,
    streamingContent,
    error,
    sendMessage,
    stopStreaming,
    clearMessages
  };
}

/**
 * Hook for audit logs
 */
export function useAuditLogs(query?: IAuditLogQuery) {
  const [logs, setLogs] = useState<IAuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchLogs = useCallback(async () => {
    setLoading(true);
    try {
      const data = await agiApi.getAuditLogs(query);
      setLogs(data);
      setError(null);
    } catch (err) {
      setError(err as Error);
    } finally {
      setLoading(false);
    }
  }, [query]);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  return { logs, loading, error, refetch: fetchLogs };
}

/**
 * Hook for rate limits
 */
export function useRateLimits() {
  const [limits, setLimits] = useState<IRateLimit[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchLimits = useCallback(async () => {
    setLoading(true);
    try {
      const data = await agiApi.getRateLimits();
      setLimits(data);
      setError(null);
    } catch (err) {
      setError(err as Error);
    } finally {
      setLoading(false);
    }
  }, []);

  const updateLimit = useCallback(async (
    rule: string,
    limit: number,
    window?: number
  ) => {
    try {
      await agiApi.updateRateLimit(rule, { rule, limit, window });
      await fetchLimits();
    } catch (err) {
      throw err;
    }
  }, [fetchLimits]);

  useEffect(() => {
    fetchLimits();
  }, [fetchLimits]);

  // Subscribe to rate limit exceeded events
  useEffect(() => {
    const unsubscribe = wsService.subscribe(
      WSMessageType.RATE_LIMIT_EXCEEDED,
      () => fetchLimits()
    );

    return unsubscribe;
  }, [fetchLimits]);

  return { limits, loading, error, updateLimit, refetch: fetchLimits };
}

/**
 * Hook for WebSocket connection status
 */
export function useWebSocketStatus() {
  const [isConnected, setIsConnected] = useState(wsService.isConnected());
  const [stats, setStats] = useState(wsService.getStats());

  useEffect(() => {
    const handleStateChange = () => {
      setIsConnected(wsService.isConnected());
      setStats(wsService.getStats());
    };

    wsService.on('stateChange', handleStateChange);
    wsService.on('connected', handleStateChange);
    wsService.on('disconnected', handleStateChange);

    return () => {
      wsService.off('stateChange', handleStateChange);
      wsService.off('connected', handleStateChange);
      wsService.off('disconnected', handleStateChange);
    };
  }, []);

  return { isConnected, stats };
}