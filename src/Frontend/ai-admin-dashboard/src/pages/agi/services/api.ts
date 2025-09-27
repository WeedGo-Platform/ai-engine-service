/**
 * AGI Dashboard API Service
 * Connects to real AGI endpoints on port 5024
 */

import {
  Agent,
  AgentStats,
  SystemStats,
  SecurityData,
  SecurityEvent,
  LearningMetrics,
  Pattern,
  Activity,
  RateLimit,
  AuditLog,
  SystemAction,
  WebSocketMessage
} from '../types';

const API_BASE = 'http://localhost:5024/api/agi';

class AGIApiService {
  private wsConnection: WebSocket | null = null;
  private wsCallbacks: Set<(msg: WebSocketMessage) => void> = new Set();

  // Agent Management Endpoints
  async getAgents(): Promise<Agent[]> {
    const response = await fetch(`${API_BASE}/agents`);
    if (!response.ok) throw new Error('Failed to fetch agents');
    return response.json();
  }

  async getAgent(agentId: string): Promise<Agent> {
    const response = await fetch(`${API_BASE}/agents/${agentId}`);
    if (!response.ok) throw new Error('Failed to fetch agent');
    return response.json();
  }

  async executeAgentAction(agentId: string, action: string): Promise<any> {
    const response = await fetch(`${API_BASE}/agents/${agentId}/actions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action })
    });
    if (!response.ok) throw new Error('Failed to execute action');
    return response.json();
  }

  async getAgentStats(agentId: string): Promise<AgentStats> {
    const response = await fetch(`${API_BASE}/agents/${agentId}/stats`);
    if (!response.ok) throw new Error('Failed to fetch agent stats');
    return response.json();
  }

  async updateAgent(agentId: string, updates: Partial<Agent>): Promise<Agent> {
    const response = await fetch(`${API_BASE}/agents/${agentId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updates)
    });
    if (!response.ok) throw new Error('Failed to update agent');
    return response.json();
  }

  async deleteAgent(agentId: string): Promise<void> {
    const response = await fetch(`${API_BASE}/agents/${agentId}`, {
      method: 'DELETE'
    });
    if (!response.ok) throw new Error('Failed to delete agent');
  }

  // System Statistics
  async getSystemStats(): Promise<SystemStats> {
    const response = await fetch(`${API_BASE}/stats`);
    if (!response.ok) throw new Error('Failed to fetch system stats');
    return response.json();
  }

  async getStatsHistory(period: string = '24h'): Promise<any> {
    const response = await fetch(`${API_BASE}/stats/history?period=${period}`);
    if (!response.ok) throw new Error('Failed to fetch stats history');
    return response.json();
  }

  async getMetrics(): Promise<any> {
    const response = await fetch(`${API_BASE}/metrics`);
    if (!response.ok) throw new Error('Failed to fetch metrics');
    return response.json();
  }

  // Security Endpoints
  async getSecurityStatus(): Promise<SecurityData> {
    const response = await fetch(`${API_BASE}/security/status`);
    if (!response.ok) throw new Error('Failed to fetch security status');
    return response.json();
  }

  async getSecurityEvents(limit: number = 50): Promise<SecurityEvent[]> {
    const response = await fetch(`${API_BASE}/security/events?limit=${limit}`);
    if (!response.ok) throw new Error('Failed to fetch security events');
    return response.json();
  }

  async updateSecurityRule(rule: string, value: any): Promise<any> {
    const response = await fetch(`${API_BASE}/security/rules/${rule}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ value })
    });
    if (!response.ok) throw new Error('Failed to update security rule');
    return response.json();
  }

  async getThreats(): Promise<any> {
    const response = await fetch(`${API_BASE}/security/threats`);
    if (!response.ok) throw new Error('Failed to fetch threats');
    return response.json();
  }

  // Learning Metrics
  async getLearningMetrics(): Promise<LearningMetrics> {
    const response = await fetch(`${API_BASE}/learning/metrics`);
    if (!response.ok) throw new Error('Failed to fetch learning metrics');
    return response.json();
  }

  async getPatterns(limit: number = 50): Promise<Pattern[]> {
    const response = await fetch(`${API_BASE}/learning/patterns?limit=${limit}`);
    if (!response.ok) throw new Error('Failed to fetch patterns');
    return response.json();
  }

  async getFeedback(limit: number = 50): Promise<any[]> {
    const response = await fetch(`${API_BASE}/learning/feedback?limit=${limit}`);
    if (!response.ok) throw new Error('Failed to fetch feedback');
    return response.json();
  }

  // Rate Limiting
  async getRateLimits(): Promise<RateLimit[]> {
    const response = await fetch(`${API_BASE}/rate-limits`);
    if (!response.ok) throw new Error('Failed to fetch rate limits');
    return response.json();
  }

  async updateRateLimit(rule: string, limit: number): Promise<any> {
    const response = await fetch(`${API_BASE}/rate-limits/${rule}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ limit })
    });
    if (!response.ok) throw new Error('Failed to update rate limit');
    return response.json();
  }

  // Activity & Audit
  async getActivities(limit: number = 100): Promise<Activity[]> {
    const response = await fetch(`${API_BASE}/activities?limit=${limit}`);
    if (!response.ok) throw new Error('Failed to fetch activities');
    return response.json();
  }

  async getAuditLogs(params?: {
    start_time?: string;
    end_time?: string;
    event_type?: string;
    user_id?: string;
    limit?: number;
  }): Promise<AuditLog[]> {
    const queryParams = new URLSearchParams();
    if (params?.start_time) queryParams.append('start_time', params.start_time);
    if (params?.end_time) queryParams.append('end_time', params.end_time);
    if (params?.event_type) queryParams.append('event_type', params.event_type);
    if (params?.user_id) queryParams.append('user_id', params.user_id);
    if (params?.limit) queryParams.append('limit', params.limit.toString());

    const response = await fetch(`${API_BASE}/audit-logs?${queryParams}`);
    if (!response.ok) throw new Error('Failed to fetch audit logs');
    return response.json();
  }

  async exportLogs(format: 'json' | 'csv' = 'json'): Promise<Blob> {
    const response = await fetch(`${API_BASE}/system/export-logs?format=${format}`);
    if (!response.ok) throw new Error('Failed to export logs');
    return response.blob();
  }

  // System Actions
  async restartAgents(): Promise<any> {
    const response = await fetch(`${API_BASE}/system/restart-agents`, {
      method: 'POST'
    });
    if (!response.ok) throw new Error('Failed to restart agents');
    return response.json();
  }

  async clearCache(): Promise<any> {
    const response = await fetch(`${API_BASE}/system/clear-cache`, {
      method: 'POST'
    });
    if (!response.ok) throw new Error('Failed to clear cache');
    return response.json();
  }

  async createBackup(): Promise<any> {
    const response = await fetch(`${API_BASE}/system/backup`, {
      method: 'POST'
    });
    if (!response.ok) throw new Error('Failed to create backup');
    return response.json();
  }

  async restoreBackup(backupId: string): Promise<any> {
    const response = await fetch(`${API_BASE}/system/restore`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ backup_id: backupId })
    });
    if (!response.ok) throw new Error('Failed to restore backup');
    return response.json();
  }

  // Health Check
  async checkHealth(): Promise<any> {
    const response = await fetch(`${API_BASE}/health`);
    if (!response.ok) throw new Error('Health check failed');
    return response.json();
  }

  // WebSocket Connection
  connectWebSocket(onMessage: (msg: WebSocketMessage) => void): void {
    if (this.wsConnection?.readyState === WebSocket.OPEN) {
      this.wsCallbacks.add(onMessage);
      return;
    }

    this.wsConnection = new WebSocket('ws://localhost:5024/api/agi/ws');
    this.wsCallbacks.add(onMessage);

    this.wsConnection.onopen = () => {
      console.log('AGI WebSocket connected');
      // Send ping to keep connection alive
      setInterval(() => {
        if (this.wsConnection?.readyState === WebSocket.OPEN) {
          this.wsConnection.send(JSON.stringify({ type: 'ping' }));
        }
      }, 30000);
    };

    this.wsConnection.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data) as WebSocketMessage;
        this.wsCallbacks.forEach(cb => cb(message));
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    this.wsConnection.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    this.wsConnection.onclose = () => {
      console.log('WebSocket disconnected');
      // Attempt to reconnect after 5 seconds
      setTimeout(() => {
        if (this.wsCallbacks.size > 0) {
          this.wsCallbacks.forEach(cb => this.connectWebSocket(cb));
        }
      }, 5000);
    };
  }

  disconnectWebSocket(onMessage?: (msg: WebSocketMessage) => void): void {
    if (onMessage) {
      this.wsCallbacks.delete(onMessage);
    }

    if (this.wsCallbacks.size === 0 && this.wsConnection) {
      this.wsConnection.close();
      this.wsConnection = null;
    }
  }
}

export const agiApi = new AGIApiService();