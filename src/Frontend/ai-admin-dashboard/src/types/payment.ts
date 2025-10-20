/**
 * Payment Domain Types
 *
 * TypeScript definitions for payment-related entities.
 * These types EXACTLY match the backend Pydantic schemas in:
 * src/Backend/api/v2/payments/schemas.py
 *
 * Principles:
 * - DRY: Single source of truth for types
 * - Type Safety: Strict typing with no `any`
 * - Documentation: JSDoc comments for clarity
 */

// ============================================================================
// Enums
// ============================================================================

/**
 * Supported payment provider types
 * Must match backend ProviderType enum
 */
export enum ProviderType {
  CLOVER = 'clover',
  MONERIS = 'moneris',
  INTERAC = 'interac',
}

/**
 * Payment transaction statuses
 * Must match backend PaymentStatusEnum
 */
export enum PaymentStatus {
  PENDING = 'pending',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed',
  VOIDED = 'voided',
  REFUNDED = 'refunded',
}

/**
 * Provider environment types
 * Must match backend EnvironmentType enum
 */
export enum EnvironmentType {
  SANDBOX = 'sandbox',
  PRODUCTION = 'production',
}

/**
 * Provider health check statuses
 * Must match backend ProviderHealthStatus enum
 */
export enum ProviderHealthStatus {
  HEALTHY = 'healthy',
  DEGRADED = 'degraded',
  UNAVAILABLE = 'unavailable',
  UNKNOWN = 'unknown',
}

// ============================================================================
// Payment Transaction Types
// ============================================================================

/**
 * Request to create a payment transaction
 * Matches backend CreatePaymentRequest schema
 */
export interface CreatePaymentRequest {
  amount: number;
  currency: 'CAD' | 'USD';
  payment_method_id: string;
  provider_type: ProviderType;
  order_id?: string | null;
  idempotency_key?: string | null;
  metadata?: Record<string, unknown>;
}

/**
 * Payment transaction response
 * Matches backend PaymentResponse schema
 */
export interface PaymentTransactionDTO {
  id: string;
  transaction_reference: string;
  store_id: string;
  amount: number;
  currency: string;
  status: PaymentStatus;
  provider_transaction_id: string | null;
  error_code: string | null;
  error_message: string | null;
  created_at: string; // ISO 8601 datetime
  completed_at: string | null; // ISO 8601 datetime
}

/**
 * Paginated list of transactions
 * Matches backend TransactionListResponse schema
 */
export interface TransactionListResponse {
  transactions: PaymentTransactionDTO[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

// ============================================================================
// Refund Types
// ============================================================================

/**
 * Request to create a refund
 * Matches backend CreateRefundRequest schema
 */
export interface CreateRefundRequest {
  amount: number;
  currency: 'CAD' | 'USD';
  reason: string;
  notes?: string | null;
}

/**
 * Refund response
 * Matches backend RefundResponse schema
 */
export interface RefundResponse {
  id: string;
  refund_reference: string;
  transaction_id: string;
  amount: number;
  currency: string;
  status: string;
  reason: string;
  created_at: string; // ISO 8601 datetime
  completed_at: string | null; // ISO 8601 datetime
}

// ============================================================================
// Provider Configuration Types
// ============================================================================

/**
 * Request to create a payment provider
 * Matches backend CreateProviderRequest schema
 */
export interface CreateProviderRequest {
  provider_type: ProviderType;
  merchant_id: string;
  api_key: string;
  api_secret?: string | null;
  environment?: EnvironmentType;
  is_active?: boolean;
  webhook_secret?: string | null;
  metadata?: Record<string, unknown>;
}

/**
 * Request to update a payment provider
 * All fields optional for partial updates
 * Matches backend UpdateProviderRequest schema
 */
export interface UpdateProviderRequest {
  merchant_id?: string | null;
  api_key?: string | null;
  api_secret?: string | null;
  environment?: EnvironmentType | null;
  is_active?: boolean | null;
  webhook_secret?: string | null;
  metadata?: Record<string, unknown> | null;
}

/**
 * Payment provider configuration response
 * Matches backend ProviderResponse schema
 *
 * SECURITY: Never contains actual credentials, only metadata about them
 */
export interface ProviderResponse {
  id: string;
  tenant_id: string;
  store_id: string | null;
  provider_type: ProviderType;
  merchant_id: string;
  environment: EnvironmentType;
  is_active: boolean;
  health_status: ProviderHealthStatus | null;
  last_health_check: string | null; // ISO 8601 datetime
  has_credentials: boolean; // Never exposes actual credentials
  has_webhook_secret: boolean;
  metadata: Record<string, unknown>;
  created_at: string; // ISO 8601 datetime
  updated_at: string; // ISO 8601 datetime
}

/**
 * Paginated list of payment providers
 * Matches backend ProviderListResponse schema
 */
export interface ProviderListResponse {
  providers: ProviderResponse[];
  total: number;
  limit: number;
  offset: number;
}

/**
 * Health check response for a payment provider
 * Matches backend ProviderHealthCheckResponse schema
 */
export interface ProviderHealthCheckResponse {
  provider_id: string;
  provider_type: ProviderType;
  status: ProviderHealthStatus;
  response_time_ms: number | null;
  error_message: string | null;
  last_successful_transaction: string | null; // ISO 8601 datetime
  checked_at: string; // ISO 8601 datetime
}

// ============================================================================
// Clover OAuth Types
// ============================================================================

/**
 * Response for Clover OAuth initiation
 * Matches backend CloverOAuthInitiateResponse schema
 */
export interface CloverOAuthInitiateResponse {
  authorization_url: string;
  state: string;
}

/**
 * Request from Clover OAuth callback
 * Matches backend CloverOAuthCallbackRequest schema
 */
export interface CloverOAuthCallbackRequest {
  code: string;
  merchant_id: string;
  state: string;
}

// ============================================================================
// Error Response Types
// ============================================================================

/**
 * Standard error response
 * Matches backend ErrorResponse schema
 */
export interface ErrorResponse {
  error: string;
  error_code: string;
  details?: Record<string, unknown> | null;
}

// ============================================================================
// Query/Filter Types (Frontend-Specific)
// ============================================================================

/**
 * Filters for querying transactions
 * Used in API calls, not directly from backend
 */
export interface TransactionFilters {
  order_id?: string;
  status?: PaymentStatus;
  provider_type?: ProviderType;
  start_date?: string; // ISO 8601 date
  end_date?: string; // ISO 8601 date
  search?: string; // Search transaction reference, customer, etc.
  limit?: number;
  offset?: number;
}

/**
 * Filters for querying providers
 * Used in API calls, not directly from backend
 */
export interface ProviderFilters {
  provider_type?: ProviderType;
  environment?: EnvironmentType;
  is_active?: boolean;
  limit?: number;
  offset?: number;
}

// ============================================================================
// Type Guards (for runtime type checking)
// ============================================================================

/**
 * Check if a value is a valid ProviderType
 */
export function isProviderType(value: unknown): value is ProviderType {
  return (
    typeof value === 'string' &&
    Object.values(ProviderType).includes(value as ProviderType)
  );
}

/**
 * Check if a value is a valid PaymentStatus
 */
export function isPaymentStatus(value: unknown): value is PaymentStatus {
  return (
    typeof value === 'string' &&
    Object.values(PaymentStatus).includes(value as PaymentStatus)
  );
}

/**
 * Check if a value is a valid EnvironmentType
 */
export function isEnvironmentType(value: unknown): value is EnvironmentType {
  return (
    typeof value === 'string' &&
    Object.values(EnvironmentType).includes(value as EnvironmentType)
  );
}

/**
 * Check if a response is an error response
 */
export function isErrorResponse(response: unknown): response is ErrorResponse {
  return (
    typeof response === 'object' &&
    response !== null &&
    'error' in response &&
    'error_code' in response
  );
}

// ============================================================================
// Utility Types
// ============================================================================

/**
 * Provider display information for UI
 * Not from backend - frontend convenience type
 */
export interface ProviderDisplayInfo {
  id: ProviderType;
  name: string;
  icon: string;
  description: string;
  features: string[];
  docsUrl: string;
}

/**
 * Provider credentials form data
 * Used for forms, not sent directly to API (validated and transformed first)
 */
export interface ProviderCredentialsForm {
  provider_type: ProviderType;
  merchant_id: string;
  api_key: string;
  api_secret: string;
  environment: EnvironmentType;
  webhook_secret: string;
}

/**
 * Payment statistics/metrics
 * Frontend aggregation type
 */
export interface PaymentMetrics {
  total_transactions: number;
  successful_transactions: number;
  failed_transactions: number;
  total_amount: number;
  total_fees: number;
  total_refunds: number;
  success_rate: number;
  avg_transaction_time: number;
}

// ============================================================================
// Constants
// ============================================================================

/**
 * Provider display information
 * Used for UI rendering
 */
export const PROVIDER_INFO: Record<ProviderType, ProviderDisplayInfo> = {
  [ProviderType.CLOVER]: {
    id: ProviderType.CLOVER,
    name: 'Clover',
    icon: '🍀',
    description: 'Clover payment processing for Canadian merchants',
    features: ['Credit/Debit Cards', 'Tap to Pay', 'Recurring Payments', 'Refunds'],
    docsUrl: 'https://docs.clover.com/',
  },
  [ProviderType.MONERIS]: {
    id: ProviderType.MONERIS,
    name: 'Moneris',
    icon: '💳',
    description: 'Leading Canadian payment processor',
    features: ['Credit/Debit Cards', 'Interac Online', 'Pre-authorization'],
    docsUrl: 'https://developer.moneris.com/',
  },
  [ProviderType.INTERAC]: {
    id: ProviderType.INTERAC,
    name: 'Interac',
    icon: '🏦',
    description: 'Interac e-Transfer and online payments',
    features: ['Interac e-Transfer', 'Real-time payments', 'Bank-level security'],
    docsUrl: 'https://developer.interac.ca/',
  },
};

/**
 * Supported currencies
 */
export const SUPPORTED_CURRENCIES = ['CAD', 'USD'] as const;
export type SupportedCurrency = typeof SUPPORTED_CURRENCIES[number];

/**
 * Default pagination values
 */
export const DEFAULT_PAGE_SIZE = 50;
export const MAX_PAGE_SIZE = 100;
