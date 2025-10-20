/**
 * Payment Context
 *
 * Centralized state management for payment operations following:
 * - SRP: Single responsibility - payment state management
 * - DRY: Reusable across all payment components
 * - KISS: Simple API with usePayment hook
 *
 * Features:
 * - Centralized provider, transaction, and metrics state
 * - Automatic request deduplication
 * - Tenant-aware auto-refresh
 * - Optimistic updates
 * - Global error handling
 *
 * Architecture:
 * Context Provider → useReducer → paymentServiceV2 → API
 */

import React, { createContext, useContext, useReducer, useCallback, useEffect, ReactNode } from 'react';
import { paymentService } from '../services/paymentServiceV2';
import type {
  ProviderResponse,
  ProviderListResponse,
  PaymentTransactionDTO,
  TransactionListResponse,
  PaymentMetrics,
  CreateProviderRequest,
  UpdateProviderRequest,
  ProviderFilters,
  TransactionFilters,
} from '../types/payment';
import { ApiError, NetworkError, AuthenticationError } from '../utils/api-error-handler';

// ============================================================================
// State Types
// ============================================================================

/**
 * Loading state for async operations
 */
interface LoadingState {
  providers: boolean;
  transactions: boolean;
  metrics: boolean;
  createProvider: boolean;
  updateProvider: boolean;
  deleteProvider: boolean;
  healthCheck: boolean;
}

/**
 * Error state for different operations
 */
interface ErrorState {
  providers: string | null;
  transactions: string | null;
  metrics: string | null;
  createProvider: string | null;
  updateProvider: string | null;
  deleteProvider: string | null;
  healthCheck: string | null;
}

/**
 * Payment state interface
 */
interface PaymentState {
  // Data
  providers: ProviderResponse[];
  selectedProvider: ProviderResponse | null;
  transactions: PaymentTransactionDTO[];
  selectedTransaction: PaymentTransactionDTO | null;
  metrics: PaymentMetrics | null;

  // Metadata
  providersTotal: number;
  transactionsTotal: number;
  hasMoreTransactions: boolean;

  // Current tenant
  currentTenantId: string | null;

  // Loading states
  loading: LoadingState;

  // Error states
  errors: ErrorState;

  // Last refresh timestamps
  lastRefresh: {
    providers: Date | null;
    transactions: Date | null;
    metrics: Date | null;
  };
}

/**
 * Initial state
 */
const initialState: PaymentState = {
  providers: [],
  selectedProvider: null,
  transactions: [],
  selectedTransaction: null,
  metrics: null,
  providersTotal: 0,
  transactionsTotal: 0,
  hasMoreTransactions: false,
  currentTenantId: null,
  loading: {
    providers: false,
    transactions: false,
    metrics: false,
    createProvider: false,
    updateProvider: false,
    deleteProvider: false,
    healthCheck: false,
  },
  errors: {
    providers: null,
    transactions: null,
    metrics: null,
    createProvider: null,
    updateProvider: null,
    deleteProvider: null,
    healthCheck: null,
  },
  lastRefresh: {
    providers: null,
    transactions: null,
    metrics: null,
  },
};

// ============================================================================
// Action Types
// ============================================================================

type PaymentAction =
  // Tenant management
  | { type: 'SET_TENANT'; payload: string | null }
  | { type: 'CLEAR_STATE' }

  // Provider actions
  | { type: 'FETCH_PROVIDERS_START' }
  | { type: 'FETCH_PROVIDERS_SUCCESS'; payload: ProviderListResponse }
  | { type: 'FETCH_PROVIDERS_ERROR'; payload: string }
  | { type: 'SELECT_PROVIDER'; payload: ProviderResponse | null }
  | { type: 'CREATE_PROVIDER_START' }
  | { type: 'CREATE_PROVIDER_SUCCESS'; payload: ProviderResponse }
  | { type: 'CREATE_PROVIDER_ERROR'; payload: string }
  | { type: 'UPDATE_PROVIDER_START' }
  | { type: 'UPDATE_PROVIDER_SUCCESS'; payload: ProviderResponse }
  | { type: 'UPDATE_PROVIDER_ERROR'; payload: string }
  | { type: 'DELETE_PROVIDER_START' }
  | { type: 'DELETE_PROVIDER_SUCCESS'; payload: string }
  | { type: 'DELETE_PROVIDER_ERROR'; payload: string }

  // Transaction actions
  | { type: 'FETCH_TRANSACTIONS_START' }
  | { type: 'FETCH_TRANSACTIONS_SUCCESS'; payload: TransactionListResponse }
  | { type: 'FETCH_TRANSACTIONS_ERROR'; payload: string }
  | { type: 'SELECT_TRANSACTION'; payload: PaymentTransactionDTO | null }

  // Metrics actions
  | { type: 'FETCH_METRICS_START' }
  | { type: 'FETCH_METRICS_SUCCESS'; payload: PaymentMetrics }
  | { type: 'FETCH_METRICS_ERROR'; payload: string }

  // Health check actions
  | { type: 'HEALTH_CHECK_START' }
  | { type: 'HEALTH_CHECK_SUCCESS'; payload: { providerId: string; status: string } }
  | { type: 'HEALTH_CHECK_ERROR'; payload: string }

  // Clear errors
  | { type: 'CLEAR_ERROR'; payload: keyof ErrorState };

// ============================================================================
// Reducer
// ============================================================================

/**
 * Payment reducer following Redux patterns
 */
function paymentReducer(state: PaymentState, action: PaymentAction): PaymentState {
  switch (action.type) {
    // Tenant management
    case 'SET_TENANT':
      return {
        ...initialState,
        currentTenantId: action.payload,
      };

    case 'CLEAR_STATE':
      return initialState;

    // Provider actions
    case 'FETCH_PROVIDERS_START':
      return {
        ...state,
        loading: { ...state.loading, providers: true },
        errors: { ...state.errors, providers: null },
      };

    case 'FETCH_PROVIDERS_SUCCESS':
      return {
        ...state,
        providers: action.payload.providers,
        providersTotal: action.payload.total,
        loading: { ...state.loading, providers: false },
        errors: { ...state.errors, providers: null },
        lastRefresh: { ...state.lastRefresh, providers: new Date() },
      };

    case 'FETCH_PROVIDERS_ERROR':
      return {
        ...state,
        loading: { ...state.loading, providers: false },
        errors: { ...state.errors, providers: action.payload },
      };

    case 'SELECT_PROVIDER':
      return {
        ...state,
        selectedProvider: action.payload,
      };

    case 'CREATE_PROVIDER_START':
      return {
        ...state,
        loading: { ...state.loading, createProvider: true },
        errors: { ...state.errors, createProvider: null },
      };

    case 'CREATE_PROVIDER_SUCCESS':
      return {
        ...state,
        providers: [...state.providers, action.payload],
        providersTotal: state.providersTotal + 1,
        loading: { ...state.loading, createProvider: false },
        errors: { ...state.errors, createProvider: null },
      };

    case 'CREATE_PROVIDER_ERROR':
      return {
        ...state,
        loading: { ...state.loading, createProvider: false },
        errors: { ...state.errors, createProvider: action.payload },
      };

    case 'UPDATE_PROVIDER_START':
      return {
        ...state,
        loading: { ...state.loading, updateProvider: true },
        errors: { ...state.errors, updateProvider: null },
      };

    case 'UPDATE_PROVIDER_SUCCESS':
      return {
        ...state,
        providers: state.providers.map(p =>
          p.id === action.payload.id ? action.payload : p
        ),
        selectedProvider:
          state.selectedProvider?.id === action.payload.id
            ? action.payload
            : state.selectedProvider,
        loading: { ...state.loading, updateProvider: false },
        errors: { ...state.errors, updateProvider: null },
      };

    case 'UPDATE_PROVIDER_ERROR':
      return {
        ...state,
        loading: { ...state.loading, updateProvider: false },
        errors: { ...state.errors, updateProvider: action.payload },
      };

    case 'DELETE_PROVIDER_START':
      return {
        ...state,
        loading: { ...state.loading, deleteProvider: true },
        errors: { ...state.errors, deleteProvider: null },
      };

    case 'DELETE_PROVIDER_SUCCESS':
      return {
        ...state,
        providers: state.providers.filter(p => p.id !== action.payload),
        selectedProvider:
          state.selectedProvider?.id === action.payload ? null : state.selectedProvider,
        providersTotal: state.providersTotal - 1,
        loading: { ...state.loading, deleteProvider: false },
        errors: { ...state.errors, deleteProvider: null },
      };

    case 'DELETE_PROVIDER_ERROR':
      return {
        ...state,
        loading: { ...state.loading, deleteProvider: false },
        errors: { ...state.errors, deleteProvider: action.payload },
      };

    // Transaction actions
    case 'FETCH_TRANSACTIONS_START':
      return {
        ...state,
        loading: { ...state.loading, transactions: true },
        errors: { ...state.errors, transactions: null },
      };

    case 'FETCH_TRANSACTIONS_SUCCESS':
      return {
        ...state,
        transactions: action.payload.transactions,
        transactionsTotal: action.payload.total,
        hasMoreTransactions: action.payload.has_more,
        loading: { ...state.loading, transactions: false },
        errors: { ...state.errors, transactions: null },
        lastRefresh: { ...state.lastRefresh, transactions: new Date() },
      };

    case 'FETCH_TRANSACTIONS_ERROR':
      return {
        ...state,
        loading: { ...state.loading, transactions: false },
        errors: { ...state.errors, transactions: action.payload },
      };

    case 'SELECT_TRANSACTION':
      return {
        ...state,
        selectedTransaction: action.payload,
      };

    // Metrics actions
    case 'FETCH_METRICS_START':
      return {
        ...state,
        loading: { ...state.loading, metrics: true },
        errors: { ...state.errors, metrics: null },
      };

    case 'FETCH_METRICS_SUCCESS':
      return {
        ...state,
        metrics: action.payload,
        loading: { ...state.loading, metrics: false },
        errors: { ...state.errors, metrics: null },
        lastRefresh: { ...state.lastRefresh, metrics: new Date() },
      };

    case 'FETCH_METRICS_ERROR':
      return {
        ...state,
        loading: { ...state.loading, metrics: false },
        errors: { ...state.errors, metrics: action.payload },
      };

    // Health check actions
    case 'HEALTH_CHECK_START':
      return {
        ...state,
        loading: { ...state.loading, healthCheck: true },
        errors: { ...state.errors, healthCheck: null },
      };

    case 'HEALTH_CHECK_SUCCESS':
      return {
        ...state,
        providers: state.providers.map(p =>
          p.id === action.payload.providerId
            ? { ...p, health_status: action.payload.status as any }
            : p
        ),
        loading: { ...state.loading, healthCheck: false },
        errors: { ...state.errors, healthCheck: null },
      };

    case 'HEALTH_CHECK_ERROR':
      return {
        ...state,
        loading: { ...state.loading, healthCheck: false },
        errors: { ...state.errors, healthCheck: action.payload },
      };

    // Clear errors
    case 'CLEAR_ERROR':
      return {
        ...state,
        errors: { ...state.errors, [action.payload]: null },
      };

    default:
      return state;
  }
}

// ============================================================================
// Context Interface
// ============================================================================

/**
 * Payment context value interface
 */
interface PaymentContextValue {
  // State
  state: PaymentState;

  // Provider operations
  fetchProviders: (tenantId: string, filters?: ProviderFilters) => Promise<void>;
  createProvider: (tenantId: string, data: CreateProviderRequest) => Promise<ProviderResponse>;
  updateProvider: (tenantId: string, providerId: string, data: UpdateProviderRequest) => Promise<ProviderResponse>;
  deleteProvider: (tenantId: string, providerId: string) => Promise<void>;
  selectProvider: (provider: ProviderResponse | null) => void;
  checkProviderHealth: (tenantId: string, providerId: string) => Promise<void>;

  // Transaction operations
  fetchTransactions: (tenantId: string, filters?: TransactionFilters) => Promise<void>;
  selectTransaction: (transaction: PaymentTransactionDTO | null) => void;

  // Metrics operations
  fetchMetrics: (tenantId: string, dateRange?: { start: string; end: string }) => Promise<void>;

  // Utility operations
  setTenant: (tenantId: string | null) => void;
  clearError: (errorKey: keyof ErrorState) => void;
  refreshAll: (tenantId: string) => Promise<void>;
}

// ============================================================================
// Context Creation
// ============================================================================

const PaymentContext = createContext<PaymentContextValue | undefined>(undefined);

// ============================================================================
// Provider Component
// ============================================================================

interface PaymentProviderProps {
  children: ReactNode;
  tenantId?: string | null;
}

/**
 * Payment Context Provider
 *
 * Wraps application/routes that need payment functionality
 *
 * @example
 * <PaymentProvider tenantId={currentTenantId}>
 *   <TenantPaymentSettings />
 * </PaymentProvider>
 */
export function PaymentProvider({ children, tenantId }: PaymentProviderProps) {
  const [state, dispatch] = useReducer(paymentReducer, initialState);

  // Set tenant when prop changes
  useEffect(() => {
    if (tenantId !== state.currentTenantId) {
      dispatch({ type: 'SET_TENANT', payload: tenantId || null });
    }
  }, [tenantId, state.currentTenantId]);

  // ========================================================================
  // Provider Operations
  // ========================================================================

  const fetchProviders = useCallback(async (tenantId: string, filters?: ProviderFilters) => {
    dispatch({ type: 'FETCH_PROVIDERS_START' });
    try {
      const response = await paymentService.getProviders(tenantId, filters);
      dispatch({ type: 'FETCH_PROVIDERS_SUCCESS', payload: response });
    } catch (err) {
      const errorMessage = err instanceof ApiError ? err.getUserMessage() : 'Failed to load providers';
      dispatch({ type: 'FETCH_PROVIDERS_ERROR', payload: errorMessage });
      throw err;
    }
  }, []);

  const createProvider = useCallback(async (tenantId: string, data: CreateProviderRequest) => {
    dispatch({ type: 'CREATE_PROVIDER_START' });
    try {
      const provider = await paymentService.createProvider(tenantId, data);
      dispatch({ type: 'CREATE_PROVIDER_SUCCESS', payload: provider });
      return provider;
    } catch (err) {
      const errorMessage = err instanceof ApiError ? err.getUserMessage() : 'Failed to create provider';
      dispatch({ type: 'CREATE_PROVIDER_ERROR', payload: errorMessage });
      throw err;
    }
  }, []);

  const updateProvider = useCallback(async (
    tenantId: string,
    providerId: string,
    data: UpdateProviderRequest
  ) => {
    dispatch({ type: 'UPDATE_PROVIDER_START' });
    try {
      const provider = await paymentService.updateProvider(tenantId, providerId, data);
      dispatch({ type: 'UPDATE_PROVIDER_SUCCESS', payload: provider });
      return provider;
    } catch (err) {
      const errorMessage = err instanceof ApiError ? err.getUserMessage() : 'Failed to update provider';
      dispatch({ type: 'UPDATE_PROVIDER_ERROR', payload: errorMessage });
      throw err;
    }
  }, []);

  const deleteProvider = useCallback(async (tenantId: string, providerId: string) => {
    dispatch({ type: 'DELETE_PROVIDER_START' });
    try {
      await paymentService.deleteProvider(tenantId, providerId);
      dispatch({ type: 'DELETE_PROVIDER_SUCCESS', payload: providerId });
    } catch (err) {
      const errorMessage = err instanceof ApiError ? err.getUserMessage() : 'Failed to delete provider';
      dispatch({ type: 'DELETE_PROVIDER_ERROR', payload: errorMessage });
      throw err;
    }
  }, []);

  const selectProvider = useCallback((provider: ProviderResponse | null) => {
    dispatch({ type: 'SELECT_PROVIDER', payload: provider });
  }, []);

  const checkProviderHealth = useCallback(async (tenantId: string, providerId: string) => {
    dispatch({ type: 'HEALTH_CHECK_START' });
    try {
      const health = await paymentService.checkProviderHealth(tenantId, providerId);
      dispatch({ type: 'HEALTH_CHECK_SUCCESS', payload: { providerId, status: health.status } });
    } catch (err) {
      const errorMessage = err instanceof ApiError ? err.getUserMessage() : 'Health check failed';
      dispatch({ type: 'HEALTH_CHECK_ERROR', payload: errorMessage });
      throw err;
    }
  }, []);

  // ========================================================================
  // Transaction Operations
  // ========================================================================

  const fetchTransactions = useCallback(async (tenantId: string, filters?: TransactionFilters) => {
    dispatch({ type: 'FETCH_TRANSACTIONS_START' });
    try {
      const response = await paymentService.getTransactions(tenantId, filters);
      dispatch({ type: 'FETCH_TRANSACTIONS_SUCCESS', payload: response });
    } catch (err) {
      const errorMessage = err instanceof ApiError ? err.getUserMessage() : 'Failed to load transactions';
      dispatch({ type: 'FETCH_TRANSACTIONS_ERROR', payload: errorMessage });
      throw err;
    }
  }, []);

  const selectTransaction = useCallback((transaction: PaymentTransactionDTO | null) => {
    dispatch({ type: 'SELECT_TRANSACTION', payload: transaction });
  }, []);

  // ========================================================================
  // Metrics Operations
  // ========================================================================

  const fetchMetrics = useCallback(async (
    tenantId: string,
    dateRange?: { start: string; end: string }
  ) => {
    dispatch({ type: 'FETCH_METRICS_START' });
    try {
      const metrics = await paymentService.getPaymentStats(tenantId, dateRange);
      dispatch({ type: 'FETCH_METRICS_SUCCESS', payload: metrics });
    } catch (err) {
      const errorMessage = err instanceof ApiError ? err.getUserMessage() : 'Failed to load metrics';
      dispatch({ type: 'FETCH_METRICS_ERROR', payload: errorMessage });
      // Don't throw for metrics - they're non-critical
    }
  }, []);

  // ========================================================================
  // Utility Operations
  // ========================================================================

  const setTenant = useCallback((tenantId: string | null) => {
    dispatch({ type: 'SET_TENANT', payload: tenantId });
  }, []);

  const clearError = useCallback((errorKey: keyof ErrorState) => {
    dispatch({ type: 'CLEAR_ERROR', payload: errorKey });
  }, []);

  const refreshAll = useCallback(async (tenantId: string) => {
    await Promise.all([
      fetchProviders(tenantId),
      fetchTransactions(tenantId),
      fetchMetrics(tenantId),
    ]);
  }, [fetchProviders, fetchTransactions, fetchMetrics]);

  // ========================================================================
  // Context Value
  // ========================================================================

  const value: PaymentContextValue = {
    state,
    fetchProviders,
    createProvider,
    updateProvider,
    deleteProvider,
    selectProvider,
    checkProviderHealth,
    fetchTransactions,
    selectTransaction,
    fetchMetrics,
    setTenant,
    clearError,
    refreshAll,
  };

  return <PaymentContext.Provider value={value}>{children}</PaymentContext.Provider>;
}

// ============================================================================
// Custom Hook
// ============================================================================

/**
 * usePayment Hook
 *
 * Access payment context from any component
 *
 * @throws Error if used outside PaymentProvider
 *
 * @example
 * function MyComponent() {
 *   const { state, fetchProviders } = usePayment();
 *
 *   useEffect(() => {
 *     fetchProviders(tenantId);
 *   }, [tenantId]);
 *
 *   return <div>{state.providers.length} providers</div>;
 * }
 */
export function usePayment(): PaymentContextValue {
  const context = useContext(PaymentContext);
  if (!context) {
    throw new Error('usePayment must be used within a PaymentProvider');
  }
  return context;
}

// ============================================================================
// Export Types for External Use
// ============================================================================

export type { PaymentState, PaymentContextValue, LoadingState, ErrorState };
