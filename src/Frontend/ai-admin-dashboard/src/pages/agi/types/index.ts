/**
 * AGI Dashboard Type Definitions
 * Matching the exact API structure from backend
 */

export type AgentStatus = 'active' | 'idle' | 'restarting' | 'error' | 'stopped';
export type SecurityStatus = 'active' | 'warning' | 'critical';
export type ActivityType = 'MODEL' | 'TOOL' | 'AGENT' | 'AUTH' | 'SECURITY' | 'SYSTEM';

export interface Agent {
  id: string;
  name: string;
  type: string;
  model: string;
  status: AgentStatus;
  tasks: number;
  successRate: number;
  currentLoad: number;
  capabilities?: string[];
  recent_tasks?: {
    id: string;
    description: string;
    status: string;
  }[];
}

export interface AgentStats {
  agent_id: string;
  total_tasks: number;
  completed_tasks: number;
  failed_tasks: number;
  average_execution_time: number;
  hourly_stats: {
    hour: string;
    tasks: number;
    success_rate: number;
  }[];
}

export interface SystemStats {
  totalRequests: number;
  successRate: number;
  averageResponseTime: number;
  activeUsers: number;
  peakLoad: number;
  uptime: number;
}

export interface SecurityData {
  contentFiltering: SecurityStatus;
  rateLimiting: SecurityStatus;
  accessControl: string;
  totalEvents: number;
  threatsBlocked: number;
  lastThreat: {
    type: string;
    timestamp: string;
  };
  activeRules: {
    content_filter: number;
    rate_limits: number;
  };
}

export interface SecurityEvent {
  id: string;
  timestamp: string;
  type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  user_id?: string;
  ip_address?: string;
}

export interface LearningMetrics {
  patternCount: number;
  feedbackPositive: number;
  adaptationsToday: number;
  learningRate: number;
  confidenceScore: number;
}

export interface Pattern {
  id: string;
  type: string;
  frequency: number;
  confidence: number;
  last_seen: string;
}

export interface Activity {
  id: string;
  timestamp: string;
  type: ActivityType;
  message: string;
}

export interface RateLimit {
  rule: string;
  limit: number;
  window: number;
  current: number;
}

export interface AuditLog {
  id: string;
  timestamp: string;
  user_id: string;
  event_type: string;
  details: any;
  ip_address?: string;
}

export interface SystemAction {
  action: 'restart_agents' | 'clear_cache' | 'backup' | 'restore';
  status?: 'in_progress' | 'completed' | 'failed';
  timestamp?: string;
}

export interface WebSocketMessage {
  type: 'agent_update' | 'stats_update' | 'security_update' | 'system_action' | 'ping' | 'pong' | 'auth' | 'auth_success';
  agentId?: string;
  update?: any;
  stats?: SystemStats;
  rule?: string;
  value?: any;
  action?: string;
  status?: string;
}