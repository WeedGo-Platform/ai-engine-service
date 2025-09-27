/**
 * API Type Definitions
 * General API response types and chat interface structures
 */

// Base API response wrapper
export interface IApiResponse<T> {
  success: boolean;
  data?: T;
  error?: IApiError;
  timestamp?: string;
  request_id?: string;
}

export interface IApiError {
  code: string;
  message: string;
  details?: any;
  timestamp?: string;
}

export interface IPaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
  hasMore: boolean;
}

// Chat Interface Types
export interface IChatSession {
  id: string;
  user_id?: string;
  model_id: string;
  status: 'active' | 'paused' | 'closed';
  created_at: string;
  last_activity?: string;
  message_count?: number;
  token_count?: {
    prompt: number;
    completion: number;
    total: number;
  };
  metadata?: Record<string, any>;
}

export interface IChatMessage {
  id?: string;
  session_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  model?: string;
  tokens_used?: {
    prompt: number;
    completion: number;
  };
  metadata?: Record<string, any>;
}

export interface IChatRequest {
  message: string;
  session_id?: string;
  context?: Record<string, any>;
  model_id?: string;
  stream?: boolean;
  temperature?: number;
  max_tokens?: number;
  system_prompt?: string;
}

export interface IChatResponse {
  response: string;
  session_id: string;
  model_used: string;
  processing_time: number;
  tokens_used: {
    prompt: number;
    completion: number;
  };
  context?: Record<string, any>;
}

// Streaming response types
export interface IStreamChunk {
  type: 'start' | 'content' | 'end' | 'error';
  content?: string;
  session_id?: string;
  tokens_used?: {
    prompt: number;
    completion: number;
  };
  error?: string;
}

// System Control Types
export interface ISystemAction {
  action: 'restart_agents' | 'clear_cache' | 'export_logs';
  parameters?: Record<string, any>;
}

export interface ISystemActionResponse {
  success: boolean;
  action: string;
  result?: any;
  message?: string;
  timestamp?: string;
}

export interface ILogExportOptions {
  format: 'json' | 'csv';
  start_date?: string;
  end_date?: string;
  event_types?: string[];
  limit?: number;
}

export interface ICacheStatus {
  size: number;
  entries: number;
  hit_rate: number;
  miss_rate: number;
  last_cleared?: string;
}

// Health check type
export interface IHealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  service: string;
  version?: string;
  uptime?: number;
  checks?: Array<{
    name: string;
    status: 'ok' | 'warning' | 'error';
    message?: string;
  }>;
}

// Export all types
export * from './agent.types';
export * from './security.types';
export * from './learning.types';