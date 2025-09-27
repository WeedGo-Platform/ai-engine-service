/**
 * Agent Type Definitions
 * Covers all agent-related data structures from the AGI API
 */

export enum AgentState {
  IDLE = 'idle',
  EXECUTING = 'executing',
  WAITING = 'waiting',
  ERROR = 'error',
  STOPPED = 'stopped'
}

export enum AgentType {
  COORDINATOR = 'coordinator',
  RESEARCH = 'research',
  ANALYST = 'analyst',
  EXECUTOR = 'executor',
  VALIDATOR = 'validator'
}

export enum TaskStatus {
  PENDING = 'pending',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled'
}

export interface IAgentCapability {
  name: string;
  description: string;
  enabled: boolean;
}

export interface IAgent {
  id: string;
  name: string;
  type: AgentType;
  model: string;
  status: 'active' | 'idle' | 'error';
  state?: AgentState;
  tasks: number;
  successRate: number;
  currentLoad: number;
  capabilities?: string[];
  lastActivity?: string;
  created_at?: string;
  updated_at?: string;
}

export interface IAgentDetails extends IAgent {
  description?: string;
  version?: string;
  memory_usage?: number;
  cpu_usage?: number;
  token_usage?: {
    current: number;
    limit: number;
  };
  error_rate?: number;
  response_time?: number;
  recent_tasks?: IAgentTask[];
  configuration?: Record<string, any>;
}

export interface IAgentTask {
  id: string;
  agent_id: string;
  description: string;
  status: TaskStatus;
  priority?: number;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  duration?: number;
  result?: any;
  error?: string;
  metadata?: Record<string, any>;
}

export interface IAgentStats {
  agent_id: string;
  total_tasks: number;
  completed_tasks: number;
  failed_tasks: number;
  average_execution_time: number;
  success_rate: number;
  hourly_stats?: Array<{
    hour: string;
    tasks: number;
    success_rate: number;
  }>;
  performance_metrics?: {
    response_time: number[];
    memory_usage: number[];
    cpu_usage: number[];
    timestamps: string[];
  };
}

export interface IAgentAction {
  action: 'restart' | 'pause' | 'resume' | 'configure' | 'clear_queue';
  agent_id?: string;
  parameters?: Record<string, any>;
}

export interface IAgentActionResponse {
  success: boolean;
  action: string;
  agent_id?: string;
  message?: string;
  timestamp?: string;
}

export interface ISystemStats {
  totalRequests: number;
  successRate: number;
  averageResponseTime: number;
  activeUsers: number;
  peakLoad: number;
  uptime: number;
  timestamp?: string;
}

export interface IActivity {
  id: string;
  timestamp: string;
  type: 'MODEL' | 'TOOL' | 'AGENT' | 'AUTH' | 'SECURITY' | 'METRICS' | 'WARNING' | 'ERROR';
  message: string;
  severity?: 'info' | 'warning' | 'error' | 'critical';
  user_id?: string;
  agent_id?: string;
  metadata?: Record<string, any>;
}

// WebSocket message types
export interface IWebSocketMessage {
  type: 'agent_update' | 'stats_update' | 'activity' | 'security_alert' | 'system_action';
  payload: any;
  timestamp: string;
}

export interface IAgentUpdateMessage {
  type: 'agent_update';
  agentId: string;
  update: Partial<IAgent>;
}

export interface IStatsUpdateMessage {
  type: 'stats_update';
  stats: ISystemStats;
}

export interface IActivityMessage {
  type: 'activity';
  activity: IActivity;
}