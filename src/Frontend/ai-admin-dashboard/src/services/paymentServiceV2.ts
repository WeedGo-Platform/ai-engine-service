/**
 * Payment Service V2
 *
 * Complete rewrite using V2 API endpoints with:
 * - Automatic retry logic
 * - Request deduplication
 * - Proper error handling
 * - Type safety
 * - AbortController support
 *
 * Principles:
 * - SRP: Each method has single responsibility
 * - DRY: No code duplication
 * - KISS: Simple, predictable API
 * - Type Safety: Full TypeScript coverage
 *
 * Architecture:
 * Service Layer → HTTP Client → API V2 Endpoints
 */

import { httpClient } from '../utils/http-client';
import {
  createPaymentIdempotencyKey,
  createRefundIdempotencyKey,
  createProviderIdempotencyKey,
  withIdempotency,
  generateIdempotencyKey,
} from '../utils/idempotency';
import type {
  // Provider types
  ProviderResponse,
  ProviderListResponse,
  CreateProviderRequest,
  UpdateProviderRequest,
  ProviderHealthCheckResponse,
  ProviderFilters,
  CloverOAuthInitiateResponse,
  CloverOAuthCallbackRequest,

  // Transaction types
  PaymentTransactionDTO,
  TransactionListResponse,
  CreatePaymentRequest,
  TransactionFilters,

  // Refund types
  CreateRefundRequest,
  RefundResponse,

  // Utility types
  PaymentMetrics,
} from '../types/payment';

// ============================================================================
// Payment Service Class
// ============================================================================

/**
 * Payment Service V2
 *
 * Handles all payment-related API operations following SRP
 */
class PaymentServiceV2 {
  private readonly API_VERSION = 'v2';

  // ==========================================================================
  // Provider Management
  // ==========================================================================

  /**
   * Get all payment providers for a tenant
   *
   * @param tenantId - Tenant UUID
   * @param filters - Optional filters
   * @returns List of providers with metadata
   *
   * @example
   * const providers = await paymentService.getProviders('tenant-123', {
   *   provider_type: ProviderType.CLOVER,
   *   is_active: true
   * });
   */
  async getProviders(
    tenantId: string,
    filters?: ProviderFilters
  ): Promise<ProviderListResponse> {
    return httpClient.get<ProviderListResponse>(
      `/api/${this.API_VERSION}/payment-providers/tenants/${tenantId}/providers`,
      { params: filters }
    );
  }

  /**
   * Get single payment provider by ID
   *
   * @param tenantId - Tenant UUID
   * @param providerId - Provider UUID
   * @returns Provider configuration
   *
   * @throws NotFoundError if provider doesn't exist
   *
   * @example
   * const provider = await paymentService.getProvider('tenant-123', 'provider-456');
   */
  async getProvider(
    tenantId: string,
    providerId: string
  ): Promise<ProviderResponse> {
    return httpClient.get<ProviderResponse>(
      `/api/${this.API_VERSION}/payment-providers/tenants/${tenantId}/providers/${providerId}`
    );
  }

  /**
   * Create new payment provider configuration
   *
   * @param tenantId - Tenant UUID
   * @param request - Provider configuration
   * @param idempotencyKey - Optional idempotency key (auto-generated if not provided)
   * @returns Created provider
   *
   * @throws ValidationError if credentials are invalid
   * @throws ConflictError if provider already exists
   *
   * @example
   * const provider = await paymentService.createProvider('tenant-123', {
   *   provider_type: ProviderType.CLOVER,
   *   merchant_id: 'MERCHANT123',
   *   api_key: 'api_key_here',
   *   environment: EnvironmentType.SANDBOX
   * });
   */
  async createProvider(
    tenantId: string,
    request: CreateProviderRequest,
    idempotencyKey?: string
  ): Promise<ProviderResponse> {
    // Generate idempotency key if not provided
    const key = idempotencyKey || createProviderIdempotencyKey(
      tenantId,
      'create'
    );

    // Wrap in idempotency protection
    return withIdempotency(key, () =>
      httpClient.post<ProviderResponse>(
        `/api/${this.API_VERSION}/payment-providers/tenants/${tenantId}/providers`,
        request,
        {
          skipRetry: true, // Don't retry creates to avoid duplicates
          headers: {
            'Idempotency-Key': key, // Send to backend
          },
        }
      )
    );
  }

  /**
   * Update existing payment provider configuration
   *
   * Partial update - only provided fields are updated
   *
   * @param tenantId - Tenant UUID
   * @param providerId - Provider UUID
   * @param request - Fields to update
   * @returns Updated provider
   *
   * @throws NotFoundError if provider doesn't exist
   * @throws ValidationError if update is invalid
   *
   * @example
   * const provider = await paymentService.updateProvider('tenant-123', 'provider-456', {
   *   is_active: false
   * });
   */
  async updateProvider(
    tenantId: string,
    providerId: string,
    request: UpdateProviderRequest
  ): Promise<ProviderResponse> {
    return httpClient.put<ProviderResponse>(
      `/api/${this.API_VERSION}/payment-providers/tenants/${tenantId}/providers/${providerId}`,
      request
    );
  }

  /**
   * Delete payment provider configuration
   *
   * Soft delete - provider is deactivated but data retained for audit
   *
   * @param tenantId - Tenant UUID
   * @param providerId - Provider UUID
   *
   * @throws NotFoundError if provider doesn't exist
   * @throws ConflictError if provider has pending transactions
   *
   * @example
   * await paymentService.deleteProvider('tenant-123', 'provider-456');
   */
  async deleteProvider(
    tenantId: string,
    providerId: string
  ): Promise<void> {
    await httpClient.delete(
      `/api/${this.API_VERSION}/payment-providers/tenants/${tenantId}/providers/${providerId}`
    );
  }

  // ==========================================================================
  // Provider Health & Testing
  // ==========================================================================

  /**
   * Check health of payment provider
   *
   * Makes actual API call to provider to verify credentials and connectivity
   *
   * @param tenantId - Tenant UUID
   * @param providerId - Provider UUID
   * @returns Health check results
   *
   * @example
   * const health = await paymentService.checkProviderHealth('tenant-123', 'provider-456');
   * if (health.status === ProviderHealthStatus.HEALTHY) {
   *   console.log('Provider is operational');
   * }
   */
  async checkProviderHealth(
    tenantId: string,
    providerId: string
  ): Promise<ProviderHealthCheckResponse> {
    return httpClient.get<ProviderHealthCheckResponse>(
      `/api/${this.API_VERSION}/payment-providers/tenants/${tenantId}/providers/${providerId}/health`,
      { skipDedup: true } // Don't deduplicate health checks
    );
  }

  /**
   * Test provider credentials without saving
   *
   * Useful for validating credentials during setup
   *
   * @param tenantId - Tenant UUID
   * @param request - Provider configuration to test
   * @returns Test results
   *
   * @throws ValidationError if credentials are invalid
   *
   * @example
   * const result = await paymentService.testProviderCredentials('tenant-123', {
   *   provider_type: ProviderType.CLOVER,
   *   merchant_id: 'TEST123',
   *   api_key: 'test_key'
   * });
   */
  async testProviderCredentials(
    tenantId: string,
    request: CreateProviderRequest
  ): Promise<ProviderHealthCheckResponse> {
    return httpClient.post<ProviderHealthCheckResponse>(
      `/api/${this.API_VERSION}/payment-providers/tenants/${tenantId}/providers/test`,
      request,
      { skipRetry: true } // Don't retry test requests
    );
  }

  // ==========================================================================
  // Clover OAuth Flow
  // ==========================================================================

  /**
   * Initiate Clover OAuth authorization flow
   *
   * Returns URL to redirect user to for authorization
   *
   * @param tenantId - Tenant UUID
   * @param redirectUri - Where Clover will redirect after authorization
   * @returns Authorization URL and state parameter
   *
   * @example
   * const { authorization_url, state } = await paymentService.initiateCloverOAuth(
   *   'tenant-123',
   *   'https://app.weedgo.ca/payment-settings/clover/callback'
   * );
   * localStorage.setItem('oauth_state', state);
   * window.location.href = authorization_url;
   */
  async initiateCloverOAuth(
    tenantId: string,
    redirectUri: string
  ): Promise<CloverOAuthInitiateResponse> {
    return httpClient.get<CloverOAuthInitiateResponse>(
      `/api/${this.API_VERSION}/payment-providers/tenants/${tenantId}/clover/oauth/authorize`,
      { params: { redirect_uri: redirectUri } }
    );
  }

  /**
   * Handle Clover OAuth callback
   *
   * Exchanges authorization code for access token and creates provider
   *
   * @param tenantId - Tenant UUID
   * @param callback - OAuth callback parameters
   * @returns Created provider configuration
   *
   * @throws ValidationError if state is invalid (CSRF check failed)
   *
   * @example
   * // In callback route handler
   * const params = new URLSearchParams(window.location.search);
   * const provider = await paymentService.handleCloverOAuthCallback('tenant-123', {
   *   code: params.get('code')!,
   *   merchant_id: params.get('merchant_id')!,
   *   state: params.get('state')!
   * });
   */
  async handleCloverOAuthCallback(
    tenantId: string,
    callback: CloverOAuthCallbackRequest
  ): Promise<ProviderResponse> {
    return httpClient.post<ProviderResponse>(
      `/api/${this.API_VERSION}/payment-providers/tenants/${tenantId}/clover/oauth/callback`,
      callback,
      { skipRetry: true } // Don't retry OAuth callback
    );
  }

  // ==========================================================================
  // Transaction Management
  // ==========================================================================

  /**
   * Get paginated list of payment transactions
   *
   * @param tenantId - Tenant UUID
   * @param filters - Filter criteria
   * @returns Paginated transaction list
   *
   * @example
   * const { transactions, total, has_more } = await paymentService.getTransactions('tenant-123', {
   *   status: PaymentStatus.COMPLETED,
   *   start_date: '2025-01-01',
   *   end_date: '2025-01-31',
   *   limit: 50,
   *   offset: 0
   * });
   */
  async getTransactions(
    tenantId: string,
    filters?: TransactionFilters
  ): Promise<TransactionListResponse> {
    return httpClient.get<TransactionListResponse>(
      `/api/${this.API_VERSION}/payments`,
      { params: { ...filters, tenant_id: tenantId } }
    );
  }

  /**
   * Get single payment transaction by ID
   *
   * @param transactionId - Transaction UUID
   * @returns Transaction details
   *
   * @throws NotFoundError if transaction doesn't exist
   *
   * @example
   * const transaction = await paymentService.getTransaction('txn-123');
   */
  async getTransaction(transactionId: string): Promise<PaymentTransactionDTO> {
    return httpClient.get<PaymentTransactionDTO>(
      `/api/${this.API_VERSION}/payments/${transactionId}`
    );
  }

  /**
   * Process new payment transaction
   *
   * @param request - Payment details
   * @param idempotencyKey - Optional idempotency key (auto-generated if not provided)
   * @returns Created transaction
   *
   * @throws ValidationError if payment details are invalid
   * @throws ServerError if payment processing fails
   *
   * @example
   * const transaction = await paymentService.processPayment({
   *   amount: 99.99,
   *   currency: 'CAD',
   *   payment_method_id: 'pm-123',
   *   provider_type: ProviderType.CLOVER,
   *   order_id: 'order-456',
   *   tenant_id: 'tenant-123'
   * });
   */
  async processPayment(
    request: CreatePaymentRequest,
    idempotencyKey?: string
  ): Promise<PaymentTransactionDTO> {
    // Generate idempotency key if not provided
    const key = idempotencyKey || createPaymentIdempotencyKey(
      request.tenant_id,
      request.amount,
      request.currency,
      { orderId: request.order_id }
    );

    // Wrap in idempotency protection
    return withIdempotency(key, () =>
      httpClient.post<PaymentTransactionDTO>(
        `/api/${this.API_VERSION}/payments/process`,
        { ...request, idempotency_key: key },
        {
          skipRetry: true, // Don't retry payments (use idempotency instead)
          headers: {
            'Idempotency-Key': key, // Send to backend
          },
        }
      )
    );
  }

  // ==========================================================================
  // Refund Management
  // ==========================================================================

  /**
   * Refund a payment transaction (full or partial)
   *
   * @param transactionId - Transaction UUID to refund
   * @param request - Refund details
   * @param idempotencyKey - Optional idempotency key (auto-generated if not provided)
   * @returns Refund transaction
   *
   * @throws NotFoundError if transaction doesn't exist
   * @throws ValidationError if refund amount exceeds transaction amount
   *
   * @example
   * // Full refund
   * const refund = await paymentService.refundTransaction('txn-123', {
   *   amount: 99.99,
   *   currency: 'CAD',
   *   reason: 'Customer requested refund',
   *   tenant_id: 'tenant-123'
   * });
   *
   * // Partial refund
   * const partialRefund = await paymentService.refundTransaction('txn-123', {
   *   amount: 50.00,
   *   currency: 'CAD',
   *   reason: 'Partial refund - product damaged',
   *   tenant_id: 'tenant-123'
   * });
   */
  async refundTransaction(
    transactionId: string,
    request: CreateRefundRequest,
    idempotencyKey?: string
  ): Promise<RefundResponse> {
    // Generate idempotency key if not provided
    const key = idempotencyKey || createRefundIdempotencyKey(
      request.tenant_id,
      transactionId,
      request.amount
    );

    // Wrap in idempotency protection
    return withIdempotency(key, () =>
      httpClient.post<RefundResponse>(
        `/api/${this.API_VERSION}/payments/${transactionId}/refund`,
        { ...request, idempotency_key: key },
        {
          skipRetry: true, // Don't retry refunds
          headers: {
            'Idempotency-Key': key, // Send to backend
          },
        }
      )
    );
  }

  // ==========================================================================
  // Analytics & Statistics
  // ==========================================================================

  /**
   * Get payment statistics and metrics
   *
   * @param tenantId - Tenant UUID
   * @param dateRange - Optional date range
   * @returns Payment metrics
   *
   * @example
   * const metrics = await paymentService.getPaymentStats('tenant-123', {
   *   start: '2025-01-01',
   *   end: '2025-01-31'
   * });
   * console.log(`Success rate: ${metrics.success_rate}%`);
   */
  async getPaymentStats(
    tenantId: string,
    dateRange?: { start: string; end: string }
  ): Promise<PaymentMetrics> {
    return httpClient.get<PaymentMetrics>(
      `/api/${this.API_VERSION}/payments/stats`,
      { params: { tenant_id: tenantId, ...dateRange } }
    );
  }

  // ==========================================================================
  // Utility Methods
  // ==========================================================================

  /**
   * Cancel all pending requests
   *
   * Useful when component unmounts or user navigates away
   *
   * @example
   * useEffect(() => {
   *   return () => {
   *     paymentService.cancelAllRequests();
   *   };
   * }, []);
   */
  cancelAllRequests(): void {
    httpClient.cancelAllRequests();
  }

  /**
   * Cancel specific request
   *
   * @param method - HTTP method
   * @param url - Request URL
   *
   * @example
   * paymentService.cancelRequest('GET', '/api/v2/payments/transactions');
   */
  cancelRequest(method: string, url: string): void {
    httpClient.cancelRequest(method, url);
  }

  /**
   * Clear request deduplication cache
   *
   * Forces next request to execute even if identical request is pending
   *
   * @example
   * paymentService.clearCache();
   */
  clearCache(): void {
    httpClient.clearCache();
  }
}

// ============================================================================
// Export Singleton Instance
// ============================================================================

/**
 * Default payment service instance
 *
 * Use this singleton for all payment operations
 */
export const paymentService = new PaymentServiceV2();

/**
 * Export class for testing or custom instances
 */
export { PaymentServiceV2 };

/**
 * Re-export types for convenience
 */
export type {
  ProviderResponse,
  ProviderListResponse,
  CreateProviderRequest,
  UpdateProviderRequest,
  ProviderHealthCheckResponse,
  ProviderFilters,
  PaymentTransactionDTO,
  TransactionListResponse,
  CreatePaymentRequest,
  TransactionFilters,
  CreateRefundRequest,
  RefundResponse,
  PaymentMetrics,
};
