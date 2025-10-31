import { appConfig } from '../config/app.config';
import axios from 'axios';

// Use centralized API configuration
const API_BASE_URL = appConfig.api.baseUrl;

export interface PaymentProviderConfig {
  id: string;
  tenantId: string;
  type: 'clover' | 'moneris' | 'stripe' | 'square' | 'interac';
  name: string;
  status: 'active' | 'inactive' | 'pending' | 'error';
  environment: 'sandbox' | 'production';
  merchantId?: string;
  storeId?: string;
  locationId?: string;
  isActive: boolean;
  isPrimary: boolean;
  healthStatus?: 'healthy' | 'degraded' | 'unavailable';
  lastHealthCheck?: string;
  capabilities?: {
    refunds: boolean;
    partialRefunds: boolean;
    recurring: boolean;
    tokenization: boolean;
    threeDSecure: boolean;
  };
  fees?: {
    platformPercentage: number;
    platformFixed: number;
  };
  limits?: {
    dailyLimit?: number;
    transactionLimit?: number;
  };
}

export interface CloverCredentials {
  apiKey: string;
  secret: string;
  merchantId: string;
  accessToken?: string;
  environment: 'sandbox' | 'production';
}

export interface PaymentStats {
  totalTransactions: number;
  totalVolume: number;
  successRate: number;
  averageTransaction: number;
  todayVolume: number;
  pendingSettlement: number;
  platformFees: number;
  netRevenue: number;
  last30Days: {
    date: string;
    volume: number;
    transactions: number;
  }[];
}

export interface PaymentTransaction {
  id: string;
  reference: string;
  type: 'charge' | 'refund' | 'void';
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'refunded';
  amount: number;
  currency: string;
  provider: string;
  orderId?: string;
  customerId?: string;
  description?: string;
  metadata?: Record<string, any>;
  createdAt: string;
  completedAt?: string;
  refundedAmount?: number;
  error?: {
    code: string;
    message: string;
  };
}

export interface WebhookConfig {
  url: string;
  secret?: string;
  events: string[];
  isActive: boolean;
  lastReceived?: string;
  failureCount: number;
}

class PaymentService {
  private getAuthHeaders() {
    const token = localStorage.getItem('authToken');
    return {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    };
  }

  // Provider Management
  async getProviders(tenantId: string): Promise<PaymentProviderConfig[]> {
    const response = await axios.get(
      `${API_BASE_URL}/api/v1/payment-providers/tenants/${tenantId}/providers`,
      { headers: this.getAuthHeaders() }
    );
    return response.data;
  }

  async getProvider(tenantId: string, providerId: string): Promise<PaymentProviderConfig> {
    const response = await axios.get(
      `${API_BASE_URL}/api/v1/payment-providers/tenants/${tenantId}/providers/${providerId}`,
      { headers: this.getAuthHeaders() }
    );
    return response.data;
  }

  async createProvider(tenantId: string, config: Partial<PaymentProviderConfig>): Promise<PaymentProviderConfig> {
    const response = await axios.post(
      `${API_BASE_URL}/api/v1/payment-providers/tenants/${tenantId}/providers`,
      config,
      { headers: this.getAuthHeaders() }
    );
    return response.data;
  }

  async updateProvider(
    tenantId: string, 
    providerId: string, 
    config: Partial<PaymentProviderConfig>
  ): Promise<PaymentProviderConfig> {
    const response = await axios.put(
      `${API_BASE_URL}/api/v1/payment-providers/tenants/${tenantId}/providers/${providerId}`,
      config,
      { headers: this.getAuthHeaders() }
    );
    return response.data;
  }

  async deleteProvider(tenantId: string, providerId: string): Promise<void> {
    await axios.delete(
      `${API_BASE_URL}/api/v1/payment-providers/tenants/${tenantId}/providers/${providerId}`,
      { headers: this.getAuthHeaders() }
    );
  }

  // Clover Specific
  async configureCloverCredentials(tenantId: string, credentials: CloverCredentials): Promise<any> {
    const response = await axios.post(
      `${API_BASE_URL}/api/v1/payment-providers/tenants/${tenantId}/clover/credentials`,
      credentials,
      { headers: this.getAuthHeaders() }
    );
    return response.data;
  }

  async getCloverStatus(tenantId: string): Promise<any> {
    const response = await axios.get(
      `${API_BASE_URL}/api/v1/payment-providers/tenants/${tenantId}/clover/status`,
      { headers: this.getAuthHeaders() }
    );
    return response.data;
  }

  async initiateCloverOAuth(tenantId: string, redirectUri: string): Promise<{ authorizationUrl: string; state: string }> {
    const response = await axios.get(
      `${API_BASE_URL}/api/v1/payment-providers/tenants/${tenantId}/clover/oauth/authorize`,
      {
        params: { redirect_uri: redirectUri },
        headers: this.getAuthHeaders()
      }
    );
    return response.data;
  }

  async handleCloverOAuthCallback(
    tenantId: string,
    code: string,
    merchantId: string,
    state: string
  ): Promise<any> {
    const response = await axios.post(
      `${API_BASE_URL}/api/v1/payment-providers/tenants/${tenantId}/clover/oauth/callback`,
      { code, merchant_id: merchantId, state },
      { headers: this.getAuthHeaders() }
    );
    return response.data;
  }

  // Health Checks
  async checkProviderHealth(tenantId: string, providerType?: string): Promise<any[]> {
    const url = providerType
      ? `${API_BASE_URL}/api/v1/payment-providers/tenants/${tenantId}/${providerType}/health-check`
      : `${API_BASE_URL}/api/v1/payment-providers/tenants/${tenantId}/health`;
    
    const response = await axios.get(url, { headers: this.getAuthHeaders() });
    return response.data;
  }

  async testConnection(tenantId: string, providerId: string): Promise<boolean> {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/api/v1/payment-providers/tenants/${tenantId}/providers/${providerId}/test`,
        {},
        { headers: this.getAuthHeaders() }
      );
      return response.data.success;
    } catch {
      return false;
    }
  }

  // Payment Stats & Analytics
  async getPaymentStats(tenantId: string, dateRange?: { start: string; end: string }): Promise<PaymentStats> {
    const params = dateRange ? { start_date: dateRange.start, end_date: dateRange.end } : {};
    const response = await axios.get(
      `${API_BASE_URL}/api/v1/payment-providers/tenants/${tenantId}/analytics`,
      {
        params,
        headers: this.getAuthHeaders()
      }
    );
    return response.data;
  }

  async getTransactions(
    tenantId: string,
    params?: {
      page?: number;
      perPage?: number;
      status?: string;
      providerId?: string;
      orderId?: string;
      fromDate?: string;
      toDate?: string;
    }
  ): Promise<{ transactions: PaymentTransaction[]; total: number; hasMore: boolean }> {
    const response = await axios.get(
      `${API_BASE_URL}/api/v1/payments/transactions`,
      {
        params: { ...params, tenant_id: tenantId },
        headers: this.getAuthHeaders()
      }
    );
    return response.data;
  }

  async getTransaction(tenantId: string, transactionId: string): Promise<PaymentTransaction> {
    const response = await axios.get(
      `${API_BASE_URL}/api/v1/payments/transactions/${transactionId}`,
      {
        headers: {
          ...this.getAuthHeaders(),
          'X-Tenant-Id': tenantId
        }
      }
    );
    return response.data;
  }

  // Fee Management
  async updateFees(
    tenantId: string,
    providerId: string,
    fees: { platformPercentage: number; platformFixed: number }
  ): Promise<void> {
    await axios.put(
      `${API_BASE_URL}/api/v1/payment-providers/tenants/${tenantId}/providers/${providerId}/fees`,
      fees,
      { headers: this.getAuthHeaders() }
    );
  }

  async updateLimits(
    tenantId: string,
    providerId: string,
    limits: { dailyLimit?: number; transactionLimit?: number }
  ): Promise<void> {
    await axios.put(
      `${API_BASE_URL}/api/v1/payment-providers/tenants/${tenantId}/providers/${providerId}/limits`,
      limits,
      { headers: this.getAuthHeaders() }
    );
  }

  // Webhook Management
  async getWebhookConfig(tenantId: string, providerId: string): Promise<WebhookConfig> {
    const response = await axios.get(
      `${API_BASE_URL}/api/v1/payment-providers/tenants/${tenantId}/providers/${providerId}/webhook`,
      { headers: this.getAuthHeaders() }
    );
    return response.data;
  }

  async updateWebhookConfig(
    tenantId: string,
    providerId: string,
    config: Partial<WebhookConfig>
  ): Promise<WebhookConfig> {
    const response = await axios.put(
      `${API_BASE_URL}/api/v1/payment-providers/tenants/${tenantId}/providers/${providerId}/webhook`,
      config,
      { headers: this.getAuthHeaders() }
    );
    return response.data;
  }

  async registerWebhook(
    tenantId: string,
    providerId: string,
    events: string[]
  ): Promise<{ webhookId: string; url: string }> {
    const response = await axios.post(
      `${API_BASE_URL}/api/v1/payment-providers/tenants/${tenantId}/providers/${providerId}/webhook/register`,
      { events },
      { headers: this.getAuthHeaders() }
    );
    return response.data;
  }

  // Settlement & Reconciliation
  async getSettlements(
    tenantId: string,
    params?: {
      providerId?: string;
      fromDate?: string;
      toDate?: string;
      status?: string;
    }
  ): Promise<any[]> {
    const response = await axios.get(
      `${API_BASE_URL}/api/v1/payment-providers/tenants/${tenantId}/settlements`,
      {
        params,
        headers: this.getAuthHeaders()
      }
    );
    return response.data;
  }

  async reconcileSettlement(tenantId: string, settlementId: string): Promise<any> {
    const response = await axios.post(
      `${API_BASE_URL}/api/v1/payment-providers/tenants/${tenantId}/settlements/${settlementId}/reconcile`,
      {},
      { headers: this.getAuthHeaders() }
    );
    return response.data;
  }

  // Export & Reports
  async exportTransactions(
    tenantId: string,
    format: 'csv' | 'pdf' | 'excel',
    params?: {
      fromDate?: string;
      toDate?: string;
      providerId?: string;
    }
  ): Promise<Blob> {
    const response = await axios.get(
      `${API_BASE_URL}/api/v1/payment-providers/tenants/${tenantId}/export`,
      {
        params: { ...params, format },
        headers: this.getAuthHeaders(),
        responseType: 'blob'
      }
    );
    return response.data;
  }

  async generateReport(
    tenantId: string,
    reportType: 'summary' | 'detailed' | 'reconciliation',
    dateRange: { start: string; end: string }
  ): Promise<any> {
    const response = await axios.post(
      `${API_BASE_URL}/api/v1/payment-providers/tenants/${tenantId}/reports`,
      {
        type: reportType,
        start_date: dateRange.start,
        end_date: dateRange.end
      },
      { headers: this.getAuthHeaders() }
    );
    return response.data;
  }

  // Store-level Payment Terminal Management
  async getStorePaymentTerminals(storeId: string): Promise<any> {
    const response = await axios.get(
      `${API_BASE_URL}/api/stores/${storeId}/payment-terminals`,
      { headers: this.getAuthHeaders() }
    );
    return response.data;
  }

  async updateStorePaymentTerminals(storeId: string, terminals: any): Promise<any> {
    const response = await axios.put(
      `${API_BASE_URL}/api/stores/${storeId}/payment-terminals`,
      terminals,
      { headers: this.getAuthHeaders() }
    );
    return response.data;
  }

  // Store Device Management
  async getStoreDevices(storeId: string): Promise<any> {
    const response = await axios.get(
      `${API_BASE_URL}/api/stores/${storeId}/devices`,
      { headers: this.getAuthHeaders() }
    );
    return response.data;
  }

  async updateStoreDevices(storeId: string, devices: any): Promise<any> {
    const response = await axios.put(
      `${API_BASE_URL}/api/stores/${storeId}/devices`,
      devices,
      { headers: this.getAuthHeaders() }
    );
    return response.data;
  }
}

export default new PaymentService();