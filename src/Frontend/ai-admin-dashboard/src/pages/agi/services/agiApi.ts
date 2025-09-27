/**
 * AGI API Service Layer
 * Implements all 26 AGI endpoints with proper error handling, retry logic, and type safety
 * Following DRY, KISS, and SOLID principles
 */

import axios, { AxiosInstance, AxiosError, AxiosRequestConfig } from 'axios';
import {
  IAgent, IAgentDetails, IAgentStats, IAgentAction, IAgentActionResponse,
  ISystemStats, IActivity, IAgentTask,
  ISecurityStatus, ISecurityEvent, ISecurityRule, IRateLimit, IRateLimitUpdate,
  IAuditLog, IAuditLogQuery, IApiKey, ILoginRequest, ILoginResponse, IUser,
  ILearningMetrics, IPattern, IFeedback,
  IChatRequest, IChatResponse, ISystemAction, ISystemActionResponse,
  ILogExportOptions, IHealthStatus, IApiResponse, IPaginatedResponse
} from '../types/api.types';

// API Configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5024';
const API_TIMEOUT = 30000; // 30 seconds
const MAX_RETRIES = 3;
const RETRY_DELAY = 1000; // 1 second

/**
 * Custom error class for API errors
 */
export class AGIApiError extends Error {
  constructor(
    message: string,
    public code?: string,
    public status?: number,
    public details?: any
  ) {
    super(message);
    this.name = 'AGIApiError';
  }
}

/**
 * Exponential backoff for retry logic
 */
const getRetryDelay = (attempt: number): number => {
  return Math.min(RETRY_DELAY * Math.pow(2, attempt), 10000);
};

/**
 * AGI API Service Class
 * Single responsibility: Handle all AGI API communications
 */
export class AGIApiService {
  private api: AxiosInstance;
  private authToken?: string;

  constructor() {
    this.api = this.createApiInstance();
    this.setupInterceptors();
  }

  /**
   * Create axios instance with base configuration
   */
  private createApiInstance(): AxiosInstance {
    return axios.create({
      baseURL: `${API_BASE_URL}/api/agi`,
      timeout: API_TIMEOUT,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  /**
   * Setup request and response interceptors
   */
  private setupInterceptors(): void {
    // Request interceptor
    this.api.interceptors.request.use(
      (config) => {
        if (this.authToken) {
          config.headers.Authorization = `Bearer ${this.authToken}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor with retry logic
    this.api.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const config = error.config as AxiosRequestConfig & { _retry?: number };

        if (!config || !error.response) {
          return Promise.reject(this.handleError(error));
        }

        // Retry logic for 5xx errors
        if (error.response.status >= 500 && (!config._retry || config._retry < MAX_RETRIES)) {
          config._retry = (config._retry || 0) + 1;
          const delay = getRetryDelay(config._retry);

          await new Promise(resolve => setTimeout(resolve, delay));
          return this.api(config);
        }

        // Handle 401 - attempt token refresh
        if (error.response.status === 401 && !config.url?.includes('/auth/')) {
          try {
            await this.refreshToken();
            return this.api(config);
          } catch (refreshError) {
            // Refresh failed, reject with original error
          }
        }

        return Promise.reject(this.handleError(error));
      }
    );
  }

  /**
   * Handle API errors consistently
   */
  private handleError(error: AxiosError): AGIApiError {
    if (error.response) {
      const { status, data } = error.response;
      const message = (data as any)?.detail || (data as any)?.message || 'API request failed';
      return new AGIApiError(message, (data as any)?.code, status, data);
    } else if (error.request) {
      return new AGIApiError('No response from server', 'NETWORK_ERROR');
    } else {
      return new AGIApiError(error.message || 'Request setup failed', 'REQUEST_ERROR');
    }
  }

  /**
   * Set authentication token
   */
  public setAuthToken(token: string): void {
    this.authToken = token;
    localStorage.setItem('agi_auth_token', token);
  }

  /**
   * Clear authentication token
   */
  public clearAuthToken(): void {
    this.authToken = undefined;
    localStorage.removeItem('agi_auth_token');
    localStorage.removeItem('agi_refresh_token');
  }

  // ===========================================
  // AUTHENTICATION ENDPOINTS (6)
  // ===========================================

  async login(credentials: ILoginRequest): Promise<ILoginResponse> {
    const response = await this.api.post<ILoginResponse>('/auth/login', credentials);
    this.setAuthToken(response.data.access_token);
    localStorage.setItem('agi_refresh_token', response.data.refresh_token);
    return response.data;
  }

  async logout(): Promise<void> {
    await this.api.post('/auth/logout');
    this.clearAuthToken();
  }

  async getCurrentUser(): Promise<IUser> {
    const response = await this.api.get<IUser>('/auth/me');
    return response.data;
  }

  async refreshToken(): Promise<ILoginResponse> {
    const refreshToken = localStorage.getItem('agi_refresh_token');
    if (!refreshToken) {
      throw new AGIApiError('No refresh token available', 'NO_REFRESH_TOKEN');
    }

    const response = await this.api.post<ILoginResponse>('/auth/refresh', {
      refresh_token: refreshToken
    });

    this.setAuthToken(response.data.access_token);
    localStorage.setItem('agi_refresh_token', response.data.refresh_token);
    return response.data;
  }

  async createApiKey(name: string, permissions?: string[]): Promise<IApiKey> {
    const response = await this.api.post<IApiKey>('/auth/api-keys', { name, permissions });
    return response.data;
  }

  async revokeApiKey(keyId: string): Promise<void> {
    await this.api.delete(`/auth/api-keys/${keyId}`);
  }

  // ===========================================
  // AGENT MANAGEMENT ENDPOINTS (5)
  // ===========================================

  async getAgents(): Promise<IAgent[]> {
    const response = await this.api.get<IAgent[]>('/agents');
    return response.data;
  }

  async getAgentDetails(agentId: string): Promise<IAgentDetails> {
    const response = await this.api.get<IAgentDetails>(`/agents/${agentId}`);
    return response.data;
  }

  async executeAgentAction(agentId: string, action: IAgentAction): Promise<IAgentActionResponse> {
    const response = await this.api.post<IAgentActionResponse>(
      `/agents/${agentId}/actions`,
      action
    );
    return response.data;
  }

  async getAgentStats(agentId: string): Promise<IAgentStats> {
    const response = await this.api.get<IAgentStats>(`/agents/${agentId}/stats`);
    return response.data;
  }

  async getAgentTasks(agentId: string, limit?: number): Promise<IAgentTask[]> {
    const response = await this.api.get<IAgentTask[]>(`/agents/${agentId}/tasks`, {
      params: { limit }
    });
    return response.data;
  }

  // ===========================================
  // STATISTICS & MONITORING ENDPOINTS (2)
  // ===========================================

  async getSystemStats(): Promise<ISystemStats> {
    const response = await this.api.get<ISystemStats>('/stats');
    return response.data;
  }

  async getActivities(limit: number = 100): Promise<IActivity[]> {
    const response = await this.api.get<IActivity[]>('/activities', {
      params: { limit }
    });
    return response.data;
  }

  // ===========================================
  // SECURITY ENDPOINTS (3)
  // ===========================================

  async getSecurityStatus(): Promise<ISecurityStatus> {
    const response = await this.api.get<ISecurityStatus>('/security/status');
    return response.data;
  }

  async getSecurityEvents(limit: number = 50): Promise<ISecurityEvent[]> {
    const response = await this.api.get<ISecurityEvent[]>('/security/events', {
      params: { limit }
    });
    return response.data;
  }

  async updateSecurityRule(rule: string, value: any): Promise<IApiResponse<ISecurityRule>> {
    const response = await this.api.put<IApiResponse<ISecurityRule>>(
      `/security/rules/${rule}`,
      { value }
    );
    return response.data;
  }

  // ===========================================
  // LEARNING ENDPOINTS (3)
  // ===========================================

  async getLearningMetrics(): Promise<ILearningMetrics> {
    const response = await this.api.get<ILearningMetrics>('/learning/metrics');
    return response.data;
  }

  async getPatterns(limit: number = 50): Promise<IPattern[]> {
    const response = await this.api.get<IPattern[]>('/learning/patterns', {
      params: { limit }
    });
    return response.data;
  }

  async getFeedback(limit: number = 50): Promise<IFeedback[]> {
    const response = await this.api.get<IFeedback[]>('/learning/feedback', {
      params: { limit }
    });
    return response.data;
  }

  // ===========================================
  // AUDIT & LOGGING ENDPOINTS (2)
  // ===========================================

  async getAuditLogs(query?: IAuditLogQuery): Promise<IAuditLog[]> {
    const response = await this.api.get<IAuditLog[]>('/audit-logs', {
      params: query
    });
    return response.data;
  }

  async exportLogs(options: ILogExportOptions): Promise<Blob> {
    const response = await this.api.get('/system/export-logs', {
      params: options,
      responseType: 'blob'
    });
    return response.data;
  }

  // ===========================================
  // RATE LIMITING ENDPOINTS (2)
  // ===========================================

  async getRateLimits(): Promise<IRateLimit[]> {
    const response = await this.api.get<IRateLimit[]>('/rate-limits');
    return response.data;
  }

  async updateRateLimit(rule: string, update: IRateLimitUpdate): Promise<IApiResponse<IRateLimit>> {
    const response = await this.api.put<IApiResponse<IRateLimit>>(
      `/rate-limits/${rule}`,
      update
    );
    return response.data;
  }

  // ===========================================
  // SYSTEM CONTROL ENDPOINTS (3)
  // ===========================================

  async restartAgents(): Promise<ISystemActionResponse> {
    const response = await this.api.post<ISystemActionResponse>('/system/restart-agents');
    return response.data;
  }

  async clearCache(): Promise<ISystemActionResponse> {
    const response = await this.api.post<ISystemActionResponse>('/system/clear-cache');
    return response.data;
  }

  async performSystemAction(action: ISystemAction): Promise<ISystemActionResponse> {
    const endpoint = `/system/${action.action.replace('_', '-')}`;
    const response = await this.api.post<ISystemActionResponse>(endpoint, action.parameters);
    return response.data;
  }

  // ===========================================
  // CHAT INTERFACE ENDPOINTS (2)
  // ===========================================

  async sendChatMessage(request: IChatRequest): Promise<IChatResponse> {
    const response = await this.api.post<IChatResponse>('/chat', request);
    return response.data;
  }

  async checkHealth(): Promise<IHealthStatus> {
    const response = await this.api.get<IHealthStatus>('/health');
    return response.data;
  }

  // ===========================================
  // STREAMING SUPPORT
  // ===========================================

  async* streamChat(request: IChatRequest): AsyncGenerator<string, void, unknown> {
    const response = await fetch(`${API_BASE_URL}/api/agi/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': this.authToken ? `Bearer ${this.authToken}` : '',
      },
      body: JSON.stringify({ ...request, stream: true }),
    });

    if (!response.ok) {
      throw new AGIApiError('Stream request failed', 'STREAM_ERROR', response.status);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new AGIApiError('No response body', 'STREAM_ERROR');
    }

    const decoder = new TextDecoder();

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') return;

            try {
              const parsed = JSON.parse(data);
              if (parsed.type === 'content' && parsed.content) {
                yield parsed.content;
              }
            } catch (e) {
              console.error('Failed to parse SSE data:', e);
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  }
}

// Export singleton instance
export const agiApi = new AGIApiService();

// Export for testing
export default AGIApiService;