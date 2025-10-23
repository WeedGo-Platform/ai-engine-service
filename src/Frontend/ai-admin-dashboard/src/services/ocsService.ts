import axios from './api';

// Types
export interface OCSCredentials {
  client_id: string;
  client_secret: string;
}

export interface StoreOCSConfig {
  ocs_key?: string;
  license_number?: string;
  oauth_client_id?: string;
  oauth_client_secret?: string;
  oauth_token_url?: string;
  oauth_scope?: string;
}

export interface OCSStatus {
  credentials_configured: boolean;
  token_valid: boolean;
  token_expires_at?: string;
  enabled_stores: number;
  last_position_sync?: string;
  last_event?: string;
  stats: {
    positions_7d: number;
    events_7d: number;
    failed_events_7d: number;
    failed_positions_7d: number;
  };
}

export interface OCSPositionHistory {
  id: string;
  store_id: string;
  snapshot_date: string;
  total_items: number;
  total_quantity: number;
  status: 'success' | 'failed' | 'pending';
  submitted_at?: string;
  ocs_response?: any;
  error_message?: string;
}

export interface OCSEventHistory {
  id: string;
  store_id: string;
  transaction_type: string;
  transaction_id: string;
  status: 'success' | 'failed' | 'pending';
  retry_count: number;
  submitted_at?: string;
  ocs_response?: any;
  error_message?: string;
}

export interface OCSAuditLog {
  id: string;
  tenant_id: string;
  store_id?: string;
  action: string;
  user_id?: string;
  details?: any;
  created_at: string;
}

export interface ManualPositionSubmit {
  store_id: string;
  snapshot_date?: string;
}

export interface RetryEventsRequest {
  event_ids?: string[];
  store_id?: string;
  failed_before?: string;
}

/**
 * OCS Service - API client for Ontario Cannabis Store integration
 */
class OCSService {
  /**
   * Store OAuth credentials (Super Admin only)
   * Validates credentials before storing
   */
  async storeCredentials(tenantId: string, credentials: OCSCredentials): Promise<void> {
    await axios.post(`/api/ocs/credentials`, {
      tenant_id: tenantId,
      ...credentials,
    });
  }

  /**
   * Update store OCS configuration
   * Sets OCS hash key and CRSA license number
   */
  async updateStoreConfig(storeId: string, config: StoreOCSConfig): Promise<void> {
    await axios.put(`/api/ocs/stores/${storeId}/config`, config);
  }

  /**
   * Get position submission history for a store
   */
  async getPositionHistory(
    storeId: string,
    limit: number = 30
  ): Promise<OCSPositionHistory[]> {
    const response = await axios.get(`/api/ocs/position/history/${storeId}`, {
      params: { limit },
    });
    return response.data;
  }

  /**
   * Manually trigger position submission for a store
   */
  async submitPosition(data: ManualPositionSubmit): Promise<void> {
    await axios.post(`/api/ocs/position/submit`, data);
  }

  /**
   * Get event submission history for a store
   */
  async getEventHistory(
    storeId: string,
    limit: number = 100
  ): Promise<OCSEventHistory[]> {
    const response = await axios.get(`/api/ocs/events/history/${storeId}`, {
      params: { limit },
    });
    return response.data;
  }

  /**
   * Retry failed events (Super Admin only)
   */
  async retryEvents(data: RetryEventsRequest): Promise<{ retried: number }> {
    const response = await axios.post(`/api/ocs/events/retry`, data);
    return response.data;
  }

  /**
   * Get audit logs (Super Admin only)
   */
  async getAuditLogs(
    tenantId?: string,
    storeId?: string,
    limit: number = 50
  ): Promise<OCSAuditLog[]> {
    const response = await axios.get(`/api/ocs/audit`, {
      params: { tenant_id: tenantId, store_id: storeId, limit },
    });
    return response.data;
  }

  /**
   * Get OCS status dashboard for a tenant
   */
  async getStatus(tenantId: string): Promise<OCSStatus> {
    const response = await axios.get(`/api/ocs/status/${tenantId}`);
    return response.data;
  }
}

export default new OCSService();
