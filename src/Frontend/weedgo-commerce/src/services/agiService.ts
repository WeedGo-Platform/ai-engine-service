import axios from 'axios';

// AGI components have been removed, using local type definitions
interface Agent {
  id: string;
  name: string;
  status: 'active' | 'idle' | 'processing' | 'error';
  description?: string;
  capabilities?: string[];
}

interface ActivityEntry {
  id: string;
  timestamp: Date;
  agent: string;
  action: string;
  status: 'success' | 'error' | 'pending';
  details?: string;
}

const AGI_API_BASE = process.env.REACT_APP_AGI_API_URL || 'http://localhost:5024/agi/api';
const WS_URL = process.env.REACT_APP_AGI_WS_URL || 'ws://localhost:5024/agi/ws';

class AGIService {
  private apiClient = axios.create({
    baseURL: AGI_API_BASE,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  private ws: WebSocket | null = null;

  constructor() {
    // Add request interceptor for authentication
    this.apiClient.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('agi_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Add response interceptor for error handling
    this.apiClient.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Handle unauthorized access
          localStorage.removeItem('agi_token');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  // Agent Management
  async getAgents(): Promise<Agent[]> {
    const response = await this.apiClient.get('/agents');
    return response.data;
  }

  async getAgent(id: string): Promise<Agent> {
    const response = await this.apiClient.get(`/agents/${id}`);
    return response.data;
  }

  async executeAgentAction(agentId: string, action: string): Promise<void> {
    await this.apiClient.post(`/agents/${agentId}/actions`, { action });
  }

  async deployAgent(config: any): Promise<Agent> {
    const response = await this.apiClient.post('/agents', config);
    return response.data;
  }

  // Statistics
  async getStats(): Promise<any> {
    const response = await this.apiClient.get('/stats');
    return response.data;
  }

  async getAgentStats(agentId: string): Promise<any> {
    const response = await this.apiClient.get(`/agents/${agentId}/stats`);
    return response.data;
  }

  // Activity Logs
  async getActivities(limit: number = 100): Promise<ActivityEntry[]> {
    const response = await this.apiClient.get('/activities', { params: { limit } });
    return response.data;
  }

  async getAuditLogs(filters?: any): Promise<any[]> {
    const response = await this.apiClient.get('/audit-logs', { params: filters });
    return response.data;
  }

  // Security
  async getSecurityStatus(): Promise<any> {
    const response = await this.apiClient.get('/security/status');
    return response.data;
  }

  async updateSecurityRule(rule: string, value: any): Promise<void> {
    await this.apiClient.put(`/security/rules/${rule}`, { value });
  }

  async getSecurityEvents(limit: number = 50): Promise<any[]> {
    const response = await this.apiClient.get('/security/events', { params: { limit } });
    return response.data;
  }

  // Learning Metrics
  async getLearningMetrics(): Promise<any> {
    const response = await this.apiClient.get('/learning/metrics');
    return response.data;
  }

  async getPatterns(): Promise<any[]> {
    const response = await this.apiClient.get('/learning/patterns');
    return response.data;
  }

  async getFeedback(): Promise<any[]> {
    const response = await this.apiClient.get('/learning/feedback');
    return response.data;
  }

  // Rate Limiting
  async getRateLimits(): Promise<any[]> {
    const response = await this.apiClient.get('/rate-limits');
    return response.data;
  }

  async updateRateLimit(rule: string, limit: number): Promise<void> {
    await this.apiClient.put(`/rate-limits/${rule}`, { limit });
  }

  // System Actions
  async restartAgents(): Promise<void> {
    await this.apiClient.post('/system/restart-agents');
  }

  async clearCache(): Promise<void> {
    await this.apiClient.post('/system/clear-cache');
  }

  async exportLogs(format: 'json' | 'csv' = 'json'): Promise<Blob> {
    const response = await this.apiClient.get('/system/export-logs', {
      params: { format },
      responseType: 'blob',
    });
    return response.data;
  }

  // WebSocket Connection
  connectWebSocket(): WebSocket {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      return this.ws;
    }

    this.ws = new WebSocket(WS_URL);

    this.ws.onopen = () => {
      console.log('Connected to AGI Engine WebSocket');

      // Send authentication
      const token = localStorage.getItem('agi_token');
      if (token) {
        this.ws?.send(JSON.stringify({ type: 'auth', token }));
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    this.ws.onclose = () => {
      console.log('WebSocket connection closed');
      // Attempt to reconnect after 5 seconds
      setTimeout(() => {
        this.connectWebSocket();
      }, 5000);
    };

    return this.ws;
  }

  disconnectWebSocket(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

// Export singleton instance
const agiService = new AGIService();
export default agiService;