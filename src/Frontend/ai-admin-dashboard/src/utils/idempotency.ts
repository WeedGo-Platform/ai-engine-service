/**
 * Idempotency Utilities
 *
 * Provides idempotency key generation and duplicate request prevention
 * for payment operations. Ensures payments are processed exactly once,
 * even if the request is retried.
 *
 * Principles:
 * - Payment Safety: Prevents duplicate charges
 * - Retry Safety: Same key can be used for retries
 * - Time-bound: Keys expire after configurable duration
 * - UUID-based: Globally unique identifiers
 *
 * Standards:
 * - Stripe idempotency: https://stripe.com/docs/api/idempotent_requests
 * - RFC 4122: UUID specification
 *
 * @example
 * const key = generateIdempotencyKey('payment', userId, amount);
 * await processPayment({ amount, idempotency_key: key });
 */

// ============================================================================
// UUID Generation
// ============================================================================

/**
 * Generate a UUID v4 (random)
 *
 * Uses crypto.randomUUID() if available (modern browsers),
 * falls back to manual implementation for older browsers.
 *
 * @returns UUID v4 string (e.g., "550e8400-e29b-41d4-a716-446655440000")
 */
export function generateUUID(): string {
  // Use native crypto.randomUUID if available (modern browsers)
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }

  // Fallback implementation for older browsers
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

// ============================================================================
// Idempotency Key Generation
// ============================================================================

/**
 * Idempotency key configuration
 */
export interface IdempotencyKeyConfig {
  /** Operation type (e.g., 'payment', 'refund', 'provider_create') */
  operation: string;
  /** User/tenant identifier */
  userId?: string;
  /** Additional context (e.g., amount, provider ID) */
  context?: Record<string, any>;
  /** Custom prefix for the key */
  prefix?: string;
  /** Include timestamp in key (default: false) */
  includeTimestamp?: boolean;
}

/**
 * Generate idempotency key for payment operations
 *
 * Creates a unique key that can be used to prevent duplicate operations.
 * Same parameters will generate the same key, allowing safe retries.
 *
 * Format: prefix_operation_hash_uuid
 *
 * @param config - Idempotency key configuration
 * @returns Idempotency key string
 *
 * @example
 * // Simple usage
 * const key = generateIdempotencyKey({
 *   operation: 'payment',
 *   userId: 'user-123'
 * });
 * // Returns: "idem_payment_abc123_550e8400..."
 *
 * @example
 * // With context
 * const key = generateIdempotencyKey({
 *   operation: 'payment',
 *   userId: 'user-123',
 *   context: { amount: 99.99, currency: 'CAD' }
 * });
 */
export function generateIdempotencyKey(config: IdempotencyKeyConfig): string {
  const {
    operation,
    userId,
    context = {},
    prefix = 'idem',
    includeTimestamp = false,
  } = config;

  // Generate unique identifier
  const uuid = generateUUID();

  // Create context hash for deterministic keys
  const contextStr = JSON.stringify({
    operation,
    userId,
    ...context,
    ...(includeTimestamp ? { timestamp: Date.now() } : {}),
  });

  const hash = simpleHash(contextStr);

  // Format: prefix_operation_hash_uuid
  return `${prefix}_${operation}_${hash}_${uuid}`;
}

/**
 * Generate simple hash from string
 *
 * Simple, fast hash function for creating short identifiers.
 * NOT cryptographically secure - only for deduplication.
 *
 * @param str - String to hash
 * @returns Hash string (8 characters)
 */
function simpleHash(str: string): string {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = (hash << 5) - hash + char;
    hash = hash & hash; // Convert to 32-bit integer
  }
  return Math.abs(hash).toString(36).substring(0, 8);
}

// ============================================================================
// Idempotency Key Storage & Tracking
// ============================================================================

/**
 * Idempotency key metadata
 */
interface IdempotencyKeyMetadata {
  key: string;
  operation: string;
  createdAt: number;
  expiresAt: number;
  status: 'pending' | 'completed' | 'failed';
  result?: any;
  error?: any;
}

/**
 * Idempotency key storage manager
 *
 * Tracks idempotency keys in memory (sessionStorage) to prevent
 * duplicate operations within the same browser session.
 */
export class IdempotencyKeyManager {
  private storage: Storage;
  private storageKey = 'payment_idempotency_keys';
  private defaultTTL = 24 * 60 * 60 * 1000; // 24 hours

  constructor(storage: Storage = sessionStorage) {
    this.storage = storage;
  }

  /**
   * Store idempotency key with metadata
   *
   * @param key - Idempotency key
   * @param metadata - Key metadata
   */
  store(key: string, metadata: Partial<IdempotencyKeyMetadata>): void {
    const keys = this.getAllKeys();
    const now = Date.now();

    keys[key] = {
      key,
      operation: metadata.operation || 'unknown',
      createdAt: now,
      expiresAt: metadata.expiresAt || now + this.defaultTTL,
      status: metadata.status || 'pending',
      result: metadata.result,
      error: metadata.error,
    };

    this.saveKeys(keys);
  }

  /**
   * Get idempotency key metadata
   *
   * @param key - Idempotency key
   * @returns Key metadata or null if not found
   */
  get(key: string): IdempotencyKeyMetadata | null {
    const keys = this.getAllKeys();
    const metadata = keys[key];

    if (!metadata) {
      return null;
    }

    // Check if expired
    if (Date.now() > metadata.expiresAt) {
      this.delete(key);
      return null;
    }

    return metadata;
  }

  /**
   * Check if operation with this key is in progress
   *
   * @param key - Idempotency key
   * @returns True if operation is pending
   */
  isPending(key: string): boolean {
    const metadata = this.get(key);
    return metadata?.status === 'pending';
  }

  /**
   * Check if operation with this key is completed
   *
   * @param key - Idempotency key
   * @returns True if operation is completed
   */
  isCompleted(key: string): boolean {
    const metadata = this.get(key);
    return metadata?.status === 'completed';
  }

  /**
   * Mark operation as completed
   *
   * @param key - Idempotency key
   * @param result - Operation result
   */
  markCompleted(key: string, result?: any): void {
    const metadata = this.get(key);
    if (metadata) {
      this.store(key, {
        ...metadata,
        status: 'completed',
        result,
      });
    }
  }

  /**
   * Mark operation as failed
   *
   * @param key - Idempotency key
   * @param error - Error information
   */
  markFailed(key: string, error?: any): void {
    const metadata = this.get(key);
    if (metadata) {
      this.store(key, {
        ...metadata,
        status: 'failed',
        error,
      });
    }
  }

  /**
   * Delete idempotency key
   *
   * @param key - Idempotency key
   */
  delete(key: string): void {
    const keys = this.getAllKeys();
    delete keys[key];
    this.saveKeys(keys);
  }

  /**
   * Clean up expired keys
   *
   * Removes all keys that have expired.
   *
   * @returns Number of keys removed
   */
  cleanup(): number {
    const keys = this.getAllKeys();
    const now = Date.now();
    let removed = 0;

    Object.keys(keys).forEach((key) => {
      if (keys[key].expiresAt < now) {
        delete keys[key];
        removed++;
      }
    });

    this.saveKeys(keys);
    return removed;
  }

  /**
   * Clear all keys (for testing or logout)
   */
  clear(): void {
    this.storage.removeItem(this.storageKey);
  }

  /**
   * Get all stored keys
   */
  private getAllKeys(): Record<string, IdempotencyKeyMetadata> {
    const data = this.storage.getItem(this.storageKey);
    if (!data) {
      return {};
    }

    try {
      return JSON.parse(data);
    } catch {
      return {};
    }
  }

  /**
   * Save all keys to storage
   */
  private saveKeys(keys: Record<string, IdempotencyKeyMetadata>): void {
    this.storage.setItem(this.storageKey, JSON.stringify(keys));
  }
}

// ============================================================================
// Default Manager Instance
// ============================================================================

/**
 * Default idempotency key manager instance
 *
 * Uses sessionStorage by default (clears on browser close).
 * For persistent tracking across sessions, create a new manager with localStorage.
 */
export const idempotencyManager = new IdempotencyKeyManager();

// ============================================================================
// High-Level Helpers
// ============================================================================

/**
 * Create payment idempotency key
 *
 * Convenience function for generating payment-specific idempotency keys.
 *
 * @param userId - User/tenant identifier
 * @param amount - Payment amount
 * @param currency - Currency code
 * @param additionalContext - Additional context
 * @returns Idempotency key
 *
 * @example
 * const key = createPaymentIdempotencyKey('user-123', 99.99, 'CAD', {
 *   orderId: 'order-456'
 * });
 */
export function createPaymentIdempotencyKey(
  userId: string,
  amount: number,
  currency: string,
  additionalContext?: Record<string, any>
): string {
  return generateIdempotencyKey({
    operation: 'payment',
    userId,
    context: {
      amount,
      currency,
      ...additionalContext,
    },
  });
}

/**
 * Create refund idempotency key
 *
 * @param userId - User/tenant identifier
 * @param transactionId - Original transaction ID
 * @param amount - Refund amount
 * @returns Idempotency key
 */
export function createRefundIdempotencyKey(
  userId: string,
  transactionId: string,
  amount: number
): string {
  return generateIdempotencyKey({
    operation: 'refund',
    userId,
    context: {
      transactionId,
      amount,
    },
  });
}

/**
 * Create provider operation idempotency key
 *
 * @param userId - User/tenant identifier
 * @param operation - Operation type (create, update, delete)
 * @param providerId - Provider ID (for updates/deletes)
 * @returns Idempotency key
 */
export function createProviderIdempotencyKey(
  userId: string,
  operation: 'create' | 'update' | 'delete',
  providerId?: string
): string {
  return generateIdempotencyKey({
    operation: `provider_${operation}`,
    userId,
    context: providerId ? { providerId } : {},
  });
}

// ============================================================================
// Idempotent Request Wrapper
// ============================================================================

/**
 * Execute idempotent operation
 *
 * Wraps an async operation with idempotency protection.
 * If operation is already in progress or completed, returns cached result.
 *
 * @param key - Idempotency key
 * @param operation - Async operation to execute
 * @returns Operation result
 *
 * @example
 * const result = await withIdempotency(
 *   idempotencyKey,
 *   () => processPayment({ amount: 99.99 })
 * );
 */
export async function withIdempotency<T>(
  key: string,
  operation: () => Promise<T>
): Promise<T> {
  // Check if operation is already completed
  const metadata = idempotencyManager.get(key);
  if (metadata?.status === 'completed') {
    console.log(`[Idempotency] Using cached result for key: ${key}`);
    return metadata.result;
  }

  // Check if operation is in progress
  if (metadata?.status === 'pending') {
    throw new Error(
      'Operation already in progress. Please wait for the current operation to complete.'
    );
  }

  // Mark as pending
  idempotencyManager.store(key, {
    operation: key.split('_')[1] || 'unknown',
    status: 'pending',
  });

  try {
    // Execute operation
    const result = await operation();

    // Mark as completed
    idempotencyManager.markCompleted(key, result);

    return result;
  } catch (error) {
    // Mark as failed
    idempotencyManager.markFailed(key, error);
    throw error;
  }
}

// ============================================================================
// Auto-cleanup
// ============================================================================

/**
 * Initialize auto-cleanup
 *
 * Automatically cleans up expired idempotency keys every hour.
 */
export function initIdempotencyCleanup(intervalMs: number = 60 * 60 * 1000): void {
  setInterval(() => {
    const removed = idempotencyManager.cleanup();
    if (removed > 0) {
      console.log(`[Idempotency] Cleaned up ${removed} expired keys`);
    }
  }, intervalMs);
}

// Start auto-cleanup on module load
if (typeof window !== 'undefined') {
  initIdempotencyCleanup();
}
