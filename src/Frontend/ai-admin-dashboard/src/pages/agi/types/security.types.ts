/**
 * Security Type Definitions
 * Covers all security-related data structures from the AGI API
 */

export enum ThreatLevel {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical'
}

export enum SecurityEventType {
  SQL_INJECTION = 'sql_injection',
  XSS_ATTEMPT = 'xss_attempt',
  RATE_LIMIT = 'rate_limit',
  AUTH_FAILURE = 'auth_failure',
  SUSPICIOUS_IP = 'suspicious_ip',
  PII_DETECTED = 'pii_detected',
  CONTENT_FILTERED = 'content_filtered',
  ACCESS_DENIED = 'access_denied'
}

export interface ISecurityStatus {
  contentFiltering: 'active' | 'inactive' | 'error';
  rateLimiting: 'active' | 'inactive' | 'error';
  accessControl: string;
  totalEvents: number;
  threatsBlocked: number;
  lastThreat?: {
    type: string;
    timestamp: string;
    severity?: ThreatLevel;
  };
  activeRules: {
    content_filter: number;
    rate_limits: number;
    access_rules?: number;
  };
}

export interface ISecurityEvent {
  id: string;
  timestamp: string;
  event_type: SecurityEventType | string;
  severity: ThreatLevel;
  description: string;
  source_ip?: string;
  user_id?: string;
  blocked: boolean;
  details?: Record<string, any>;
  remediation?: string;
}

export interface ISecurityRule {
  id: string;
  name: string;
  type: 'content_filter' | 'rate_limit' | 'access_control';
  enabled: boolean;
  value: any;
  description?: string;
  created_at?: string;
  updated_at?: string;
  conditions?: Array<{
    field: string;
    operator: string;
    value: any;
  }>;
}

export interface IThreatAnalysis {
  threat_types: Array<{
    type: string;
    count: number;
    percentage?: number;
  }>;
  time_range: {
    start: string;
    end: string;
  };
  total_threats: number;
  blocked_threats: number;
  trending?: 'increasing' | 'stable' | 'decreasing';
}

export interface IContentFilter {
  pii_detection: boolean;
  profanity_filter: boolean;
  sql_injection: boolean;
  email_masking: boolean;
  phone_masking: boolean;
  credit_card_mask: boolean;
  custom_patterns?: string[];
}

export interface IRateLimit {
  rule: string;
  limit: number;
  window: number; // in seconds
  current: number;
  remaining?: number;
  reset_at?: string;
}

export interface IRateLimitUpdate {
  rule: string;
  limit: number;
  window?: number;
}

export interface IAuditLog {
  id: string;
  timestamp: string;
  event_type: string;
  user_id?: string;
  severity: 'info' | 'warning' | 'error' | 'critical';
  message: string;
  details?: Record<string, any>;
  ip_address?: string;
  user_agent?: string;
  session_id?: string;
  request_id?: string;
}

export interface IAuditLogQuery {
  start_time?: string;
  end_time?: string;
  event_type?: string;
  user_id?: string;
  severity?: string;
  limit?: number;
  offset?: number;
}

// Authentication types
export interface IApiKey {
  id: string;
  key_id: string;
  name: string;
  created_at: string;
  last_used?: string;
  permissions?: string[];
  is_active: boolean;
}

export interface ILoginRequest {
  username: string;
  password: string;
}

export interface ILoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface IUser {
  id: string;
  username: string;
  roles: string[];
  permissions: string[];
  is_active: boolean;
  created_at?: string;
  last_login?: string;
}