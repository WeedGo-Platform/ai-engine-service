# Payment System Implementation Plan
## AI Admin Dashboard - Production Readiness Roadmap

**Status:** 87.5% Complete → 100% Production-Ready
**Timeline:** 8-14 weeks (4-7 sprints)
**Last Updated:** 2025-01-19
**Based On:** Comprehensive code analysis of commit e1c917a

---

## Executive Summary

This plan addresses the critical gaps identified in the payment system analysis to achieve production readiness. The implementation follows a **risk-first approach**, tackling blocking issues before feature enhancements.

**Key Objectives:**
1. ✅ Resolve frontend-backend API version mismatch
2. ✅ Implement proper state management
3. ✅ Remove mock data and complete integrations
4. ✅ Add production-grade error handling
5. ✅ Implement comprehensive testing
6. ✅ Complete advanced features

---

## Priority Classification

- 🔴 **P0 - BLOCKER**: Must complete before any production deployment
- 🟠 **P1 - CRITICAL**: Required for production, can be deployed without
- 🟡 **P2 - HIGH**: Important for good UX, not blocking
- 🟢 **P3 - MEDIUM**: Nice to have, improves system
- 🔵 **P4 - LOW**: Future enhancements

---

# Phase 1: Critical Blockers (Sprint 1-2) 🔴

**Duration:** 2-4 weeks
**Goal:** Resolve all production blockers
**Success Criteria:** System can process real payments end-to-end

## 1.1 API Version Migration 🔴 P0

**Problem:** Frontend calls V1 APIs while backend has migrated to V2
**Impact:** Payment features completely non-functional
**Effort:** 3-5 days

### Tasks:

#### Task 1.1.1: Backend - Complete V2 Provider Endpoints
**File:** `src/Backend/api/v2/payments/payment_provider_endpoints.py` (NEW)

```python
"""
Payment Provider Management V2 Endpoints
Manages payment providers at tenant and store levels
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from uuid import UUID

from ..dependencies import get_current_user
from .schemas import (
    ProviderConfigRequest,
    ProviderConfigResponse,
    ProviderListResponse,
    ProviderHealthResponse
)

router = APIRouter(
    prefix="/v2/payment-providers",
    tags=["💳 Payment Providers V2"],
)


@router.get(
    "/tenants/{tenant_id}/providers",
    response_model=ProviderListResponse,
    summary="List Tenant Payment Providers"
)
async def list_tenant_providers(
    tenant_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """
    Get all payment providers configured for a tenant.

    Returns both tenant-level and store-level provider configurations.
    """
    # Implementation here
    pass


@router.get(
    "/tenants/{tenant_id}/providers/{provider_id}",
    response_model=ProviderConfigResponse,
    summary="Get Provider Configuration"
)
async def get_provider(
    tenant_id: UUID,
    provider_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """Get specific provider configuration details"""
    pass


@router.post(
    "/tenants/{tenant_id}/providers",
    response_model=ProviderConfigResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Payment Provider"
)
async def create_provider(
    tenant_id: UUID,
    request: ProviderConfigRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Add a new payment provider to tenant.

    Validates credentials and tests connection before saving.
    """
    pass


@router.put(
    "/tenants/{tenant_id}/providers/{provider_id}",
    response_model=ProviderConfigResponse,
    summary="Update Provider Configuration"
)
async def update_provider(
    tenant_id: UUID,
    provider_id: UUID,
    request: ProviderConfigRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update provider credentials or settings"""
    pass


@router.delete(
    "/tenants/{tenant_id}/providers/{provider_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Payment Provider"
)
async def delete_provider(
    tenant_id: UUID,
    provider_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """Remove payment provider from tenant"""
    pass


@router.get(
    "/tenants/{tenant_id}/providers/{provider_id}/health",
    response_model=ProviderHealthResponse,
    summary="Check Provider Health"
)
async def check_provider_health(
    tenant_id: UUID,
    provider_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """
    Test provider connection and return health status.

    Performs actual API call to provider to verify credentials.
    """
    pass


@router.post(
    "/tenants/{tenant_id}/providers/{provider_id}/test",
    summary="Test Provider Connection"
)
async def test_provider_connection(
    tenant_id: UUID,
    provider_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """Test provider credentials with a zero-amount authorization"""
    pass


# Clover OAuth Endpoints
@router.get(
    "/tenants/{tenant_id}/clover/oauth/authorize",
    summary="Initiate Clover OAuth Flow"
)
async def initiate_clover_oauth(
    tenant_id: UUID,
    redirect_uri: str,
    current_user: dict = Depends(get_current_user)
):
    """Generate Clover OAuth authorization URL"""
    pass


@router.post(
    "/tenants/{tenant_id}/clover/oauth/callback",
    summary="Handle Clover OAuth Callback"
)
async def handle_clover_oauth_callback(
    tenant_id: UUID,
    code: str,
    merchant_id: str,
    state: str,
    current_user: dict = Depends(get_current_user)
):
    """Process OAuth callback and save access token"""
    pass
```

**Acceptance Criteria:**
- [ ] All endpoints return proper HTTP status codes
- [ ] Endpoints validate tenant ownership
- [ ] Provider credentials encrypted before storage
- [ ] Health checks work for Clover, Moneris, Interac
- [ ] OAuth flow completes successfully for Clover
- [ ] Comprehensive error responses

#### Task 1.1.2: Frontend - Update paymentService.ts
**File:** `src/Frontend/ai-admin-dashboard/src/services/paymentService.ts`

```typescript
// Update all methods to use V2 endpoints

class PaymentService {
  private readonly API_VERSION = 'v2';
  private readonly BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5024';

  // Provider Management - Updated to V2
  async getProviders(tenantId: string): Promise<PaymentProviderConfig[]> {
    const response = await axios.get(
      `${this.BASE_URL}/api/${this.API_VERSION}/payment-providers/tenants/${tenantId}/providers`,
      { headers: this.getAuthHeaders() }
    );
    return response.data.providers; // Adjust based on V2 response structure
  }

  async getProvider(tenantId: string, providerId: string): Promise<PaymentProviderConfig> {
    const response = await axios.get(
      `${this.BASE_URL}/api/${this.API_VERSION}/payment-providers/tenants/${tenantId}/providers/${providerId}`,
      { headers: this.getAuthHeaders() }
    );
    return response.data;
  }

  async createProvider(tenantId: string, config: Partial<PaymentProviderConfig>): Promise<PaymentProviderConfig> {
    const response = await axios.post(
      `${this.BASE_URL}/api/${this.API_VERSION}/payment-providers/tenants/${tenantId}/providers`,
      config,
      { headers: this.getAuthHeaders() }
    );
    return response.data;
  }

  // Update all other methods similarly...
  // Transactions: /api/v2/payments/transactions
  // Refunds: /api/v2/payments/{id}/refund
  // Stats: /api/v2/payments/stats
}
```

**Acceptance Criteria:**
- [ ] All service methods use V2 endpoints
- [ ] Response types match V2 schemas
- [ ] Error responses properly typed
- [ ] No V1 endpoint references remain

#### Task 1.1.3: Update API Response Schemas
**File:** `src/Frontend/ai-admin-dashboard/src/types/payment.ts` (NEW)

```typescript
/**
 * Payment domain types aligned with V2 backend schemas
 */

export enum ProviderType {
  CLOVER = 'clover',
  MONERIS = 'moneris',
  INTERAC = 'interac',
}

export enum PaymentStatus {
  PENDING = 'pending',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed',
  VOIDED = 'voided',
  REFUNDED = 'refunded',
}

export interface Money {
  amount: number;
  currency: 'CAD' | 'USD';
}

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
  created_at: string;
  completed_at: string | null;
}

export interface ProviderConfigResponse {
  id: string;
  tenant_id: string;
  store_id: string;
  provider_type: ProviderType;
  merchant_id: string;
  environment: 'sandbox' | 'production';
  is_active: boolean;
  health_status?: 'healthy' | 'degraded' | 'unavailable';
  last_health_check?: string;
  created_at: string;
  updated_at: string;
}

export interface ProviderListResponse {
  providers: ProviderConfigResponse[];
  total: number;
}

export interface CreatePaymentRequest {
  amount: number;
  currency: 'CAD' | 'USD';
  payment_method_id: string;
  provider_type: ProviderType;
  order_id?: string;
  idempotency_key?: string;
  metadata?: Record<string, any>;
}

export interface CreateRefundRequest {
  amount: number;
  currency: 'CAD' | 'USD';
  reason: string;
  notes?: string;
}

export interface TransactionListResponse {
  transactions: PaymentTransactionDTO[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

export interface PaymentStatsResponse {
  total_transactions: number;
  successful_transactions: number;
  failed_transactions: number;
  total_amount: number;
  total_fees: number;
  total_refunds: number;
  success_rate: number;
  avg_transaction_time: number;
}
```

**Acceptance Criteria:**
- [ ] Types match backend Pydantic schemas exactly
- [ ] All enums aligned with backend
- [ ] Proper null handling
- [ ] JSDoc comments for complex types

---

## 1.2 Remove Mock Data 🔴 P0

**Problem:** TenantPaymentSettings uses hardcoded mock data
**Impact:** Settings page non-functional with real data
**Effort:** 1-2 days

### Tasks:

#### Task 1.2.1: Replace Mock Data with API Calls
**File:** `src/Frontend/ai-admin-dashboard/src/pages/TenantPaymentSettings.tsx`

**Changes:**
```typescript
// BEFORE (lines 122-161) - REMOVE THIS:
const mockProviders: PaymentProvider[] = [
  {
    id: '1',
    type: 'clover',
    // ... mock data
  }
];

// AFTER - Use real API:
const loadPaymentProviders = async () => {
  try {
    setLoading(true);
    setError(null);

    const response = await paymentService.getProviders(tenantId!);
    setProviders(response);

  } catch (err: any) {
    setError(t('payments:settings.notifications.providersLoadFailed'));
    console.error('Failed to load payment providers:', err);
  } finally {
    setLoading(false);
  }
};

const loadPaymentStats = async () => {
  try {
    const stats = await paymentService.getPaymentStats(tenantId!, {
      start: format(subDays(new Date(), 30), 'yyyy-MM-dd'),
      end: format(new Date(), 'yyyy-MM-dd')
    });
    setStats(stats);
  } catch (err) {
    console.error('Failed to load payment stats:', err);
  }
};
```

**Acceptance Criteria:**
- [ ] All mock data removed
- [ ] Real API integration works
- [ ] Loading states properly handled
- [ ] Error states display user-friendly messages
- [ ] Empty states handled (no providers configured)

---

## 1.3 Implement State Management 🔴 P0

**Problem:** No centralized payment state, duplicate API calls
**Impact:** Poor performance, inconsistent UI state
**Effort:** 3-4 days

### Tasks:

#### Task 1.3.1: Create Payment Context
**File:** `src/Frontend/ai-admin-dashboard/src/contexts/PaymentContext.tsx` (NEW)

```typescript
import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import paymentService from '../services/paymentService';
import { useAuth } from './AuthContext';
import { useTenant } from './TenantContext';

interface PaymentProvider {
  id: string;
  type: string;
  name: string;
  status: 'active' | 'inactive' | 'pending' | 'error';
  environment: 'sandbox' | 'production';
  health_status?: 'healthy' | 'degraded' | 'unavailable';
  // ... other fields
}

interface PaymentTransaction {
  id: string;
  transaction_reference: string;
  amount: number;
  currency: string;
  status: string;
  // ... other fields
}

interface PaymentMetrics {
  total_transactions: number;
  successful_transactions: number;
  failed_transactions: number;
  total_amount: number;
  total_fees: number;
  total_refunds: number;
  success_rate: number;
  avg_transaction_time: number;
}

interface TransactionFilters {
  startDate?: Date;
  endDate?: Date;
  status?: string;
  provider?: string;
  searchTerm?: string;
}

interface PaymentContextType {
  // State
  providers: PaymentProvider[];
  transactions: PaymentTransaction[];
  metrics: PaymentMetrics | null;
  filters: TransactionFilters;

  // Loading states
  providersLoading: boolean;
  transactionsLoading: boolean;
  metricsLoading: boolean;

  // Error states
  providersError: Error | null;
  transactionsError: Error | null;
  metricsError: Error | null;

  // Actions
  setFilters: (filters: Partial<TransactionFilters>) => void;
  refreshProviders: () => Promise<void>;
  refreshTransactions: () => Promise<void>;
  refreshMetrics: () => Promise<void>;
  refreshAll: () => Promise<void>;

  // Provider actions
  addProvider: (config: any) => Promise<PaymentProvider>;
  updateProvider: (id: string, config: any) => Promise<PaymentProvider>;
  deleteProvider: (id: string) => Promise<void>;
  testProviderConnection: (id: string) => Promise<boolean>;

  // Transaction actions
  processRefund: (transactionId: string, amount?: number, reason?: string) => Promise<void>;
  getTransactionDetails: (transactionId: string) => Promise<PaymentTransaction>;
}

const PaymentContext = createContext<PaymentContextType | undefined>(undefined);

export const PaymentProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { currentUser } = useAuth();
  const { currentTenant } = useTenant();

  // State
  const [providers, setProviders] = useState<PaymentProvider[]>([]);
  const [transactions, setTransactions] = useState<PaymentTransaction[]>([]);
  const [metrics, setMetrics] = useState<PaymentMetrics | null>(null);
  const [filters, setFilters] = useState<TransactionFilters>({
    startDate: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000), // Last 30 days
    endDate: new Date(),
  });

  // Loading states
  const [providersLoading, setProvidersLoading] = useState(false);
  const [transactionsLoading, setTransactionsLoading] = useState(false);
  const [metricsLoading, setMetricsLoading] = useState(false);

  // Error states
  const [providersError, setProvidersError] = useState<Error | null>(null);
  const [transactionsError, setTransactionsError] = useState<Error | null>(null);
  const [metricsError, setMetricsError] = useState<Error | null>(null);

  // Refresh functions
  const refreshProviders = useCallback(async () => {
    if (!currentTenant?.id) return;

    try {
      setProvidersLoading(true);
      setProvidersError(null);

      const data = await paymentService.getProviders(currentTenant.id);
      setProviders(data);

    } catch (error: any) {
      setProvidersError(error);
      console.error('Failed to load providers:', error);
    } finally {
      setProvidersLoading(false);
    }
  }, [currentTenant?.id]);

  const refreshTransactions = useCallback(async () => {
    if (!currentTenant?.id) return;

    try {
      setTransactionsLoading(true);
      setTransactionsError(null);

      const params = {
        start_date: filters.startDate?.toISOString().split('T')[0],
        end_date: filters.endDate?.toISOString().split('T')[0],
        status: filters.status,
        provider: filters.provider,
      };

      const data = await paymentService.getTransactions(currentTenant.id, params);
      setTransactions(data.transactions || []);

    } catch (error: any) {
      setTransactionsError(error);
      console.error('Failed to load transactions:', error);
    } finally {
      setTransactionsLoading(false);
    }
  }, [currentTenant?.id, filters]);

  const refreshMetrics = useCallback(async () => {
    if (!currentTenant?.id) return;

    try {
      setMetricsLoading(true);
      setMetricsError(null);

      const data = await paymentService.getPaymentStats(currentTenant.id, {
        start: filters.startDate?.toISOString().split('T')[0] || '',
        end: filters.endDate?.toISOString().split('T')[0] || '',
      });

      setMetrics(data);

    } catch (error: any) {
      setMetricsError(error);
      console.error('Failed to load metrics:', error);
    } finally {
      setMetricsLoading(false);
    }
  }, [currentTenant?.id, filters.startDate, filters.endDate]);

  const refreshAll = useCallback(async () => {
    await Promise.all([
      refreshProviders(),
      refreshTransactions(),
      refreshMetrics(),
    ]);
  }, [refreshProviders, refreshTransactions, refreshMetrics]);

  // Provider actions
  const addProvider = useCallback(async (config: any): Promise<PaymentProvider> => {
    if (!currentTenant?.id) throw new Error('No tenant selected');

    const newProvider = await paymentService.createProvider(currentTenant.id, config);
    setProviders(prev => [...prev, newProvider]);
    return newProvider;
  }, [currentTenant?.id]);

  const updateProvider = useCallback(async (id: string, config: any): Promise<PaymentProvider> => {
    if (!currentTenant?.id) throw new Error('No tenant selected');

    const updatedProvider = await paymentService.updateProvider(currentTenant.id, id, config);
    setProviders(prev => prev.map(p => p.id === id ? updatedProvider : p));
    return updatedProvider;
  }, [currentTenant?.id]);

  const deleteProvider = useCallback(async (id: string): Promise<void> => {
    if (!currentTenant?.id) throw new Error('No tenant selected');

    await paymentService.deleteProvider(currentTenant.id, id);
    setProviders(prev => prev.filter(p => p.id !== id));
  }, [currentTenant?.id]);

  const testProviderConnection = useCallback(async (id: string): Promise<boolean> => {
    if (!currentTenant?.id) throw new Error('No tenant selected');

    return await paymentService.testConnection(currentTenant.id, id);
  }, [currentTenant?.id]);

  // Transaction actions
  const processRefund = useCallback(async (
    transactionId: string,
    amount?: number,
    reason?: string
  ): Promise<void> => {
    if (!currentTenant?.id) throw new Error('No tenant selected');

    await paymentService.refundTransaction(currentTenant.id, transactionId, amount, reason);
    await refreshTransactions();
    await refreshMetrics();
  }, [currentTenant?.id, refreshTransactions, refreshMetrics]);

  const getTransactionDetails = useCallback(async (transactionId: string): Promise<PaymentTransaction> => {
    if (!currentTenant?.id) throw new Error('No tenant selected');

    return await paymentService.getTransaction(currentTenant.id, transactionId);
  }, [currentTenant?.id]);

  // Auto-refresh on tenant change or filter change
  useEffect(() => {
    if (currentTenant?.id) {
      refreshAll();
    }
  }, [currentTenant?.id, filters, refreshAll]);

  const value: PaymentContextType = {
    // State
    providers,
    transactions,
    metrics,
    filters,

    // Loading states
    providersLoading,
    transactionsLoading,
    metricsLoading,

    // Error states
    providersError,
    transactionsError,
    metricsError,

    // Actions
    setFilters: (newFilters) => setFilters(prev => ({ ...prev, ...newFilters })),
    refreshProviders,
    refreshTransactions,
    refreshMetrics,
    refreshAll,

    // Provider actions
    addProvider,
    updateProvider,
    deleteProvider,
    testProviderConnection,

    // Transaction actions
    processRefund,
    getTransactionDetails,
  };

  return (
    <PaymentContext.Provider value={value}>
      {children}
    </PaymentContext.Provider>
  );
};

export const usePayment = (): PaymentContextType => {
  const context = useContext(PaymentContext);
  if (!context) {
    throw new Error('usePayment must be used within a PaymentProvider');
  }
  return context;
};
```

**Acceptance Criteria:**
- [ ] Context provides all payment state
- [ ] Automatic refresh on tenant/filter changes
- [ ] Proper error handling
- [ ] Loading states for all operations
- [ ] Optimistic updates for mutations
- [ ] No unnecessary re-renders

#### Task 1.3.2: Integrate Context into App
**File:** `src/Frontend/ai-admin-dashboard/src/App.tsx`

```typescript
import { PaymentProvider } from './contexts/PaymentContext';

// Wrap routes with PaymentProvider
<AuthProvider>
  <TenantProvider>
    <StoreProvider>
      <PaymentProvider>  {/* Add this */}
        <RouterProvider router={router} />
      </PaymentProvider>
    </StoreProvider>
  </TenantProvider>
</AuthProvider>
```

#### Task 1.3.3: Refactor Components to Use Context
**Files:**
- `src/Frontend/ai-admin-dashboard/src/pages/Payments.tsx`
- `src/Frontend/ai-admin-dashboard/src/pages/TenantPaymentSettings.tsx`

```typescript
// BEFORE:
const [transactions, setTransactions] = useState<Transaction[]>([]);
const [providers, setProviders] = useState<PaymentProvider[]>([]);

useEffect(() => {
  fetchTransactions();
  fetchProviders();
}, []);

// AFTER:
import { usePayment } from '../contexts/PaymentContext';

const {
  transactions,
  providers,
  metrics,
  transactionsLoading,
  providersLoading,
  refreshTransactions,
  refreshProviders,
  setFilters,
} = usePayment();

// State automatically managed by context
// No need for local state or useEffect
```

**Acceptance Criteria:**
- [ ] No duplicate state in components
- [ ] No direct API calls from components
- [ ] All components use context hooks
- [ ] Performance optimized (no unnecessary renders)

---

## 1.4 Error Handling & Boundaries 🔴 P0

**Problem:** No error boundaries, poor error UX
**Impact:** App crashes on payment errors
**Effort:** 2-3 days

### Tasks:

#### Task 1.4.1: Create Payment Error Boundary
**File:** `src/Frontend/ai-admin-dashboard/src/components/PaymentErrorBoundary.tsx` (NEW)

```typescript
import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

export class PaymentErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return {
      hasError: true,
      error,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log error to monitoring service
    console.error('Payment Error Boundary caught error:', error, errorInfo);

    // Call optional error handler
    this.props.onError?.(error, errorInfo);

    this.setState({
      errorInfo,
    });
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <Card className="max-w-2xl mx-auto mt-8">
          <CardHeader>
            <div className="flex items-center gap-3">
              <AlertTriangle className="w-6 h-6 text-destructive" />
              <div>
                <CardTitle>Payment System Error</CardTitle>
                <CardDescription>
                  Something went wrong with the payment system
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-4">
              <p className="font-mono text-sm text-destructive">
                {this.state.error?.message || 'Unknown error occurred'}
              </p>
            </div>

            {process.env.NODE_ENV === 'development' && this.state.errorInfo && (
              <details className="bg-muted rounded-lg p-4">
                <summary className="cursor-pointer font-medium mb-2">
                  Error Details (Development Only)
                </summary>
                <pre className="text-xs overflow-auto">
                  {this.state.errorInfo.componentStack}
                </pre>
              </details>
            )}

            <div className="flex gap-3">
              <Button onClick={this.handleReset} variant="default">
                <RefreshCw className="w-4 h-4 mr-2" />
                Try Again
              </Button>
              <Button
                onClick={() => window.location.reload()}
                variant="outline"
              >
                Reload Page
              </Button>
            </div>

            <p className="text-sm text-muted-foreground">
              If this problem persists, please contact support with the error details above.
            </p>
          </CardContent>
        </Card>
      );
    }

    return this.props.children;
  }
}
```

**Acceptance Criteria:**
- [ ] Catches all payment component errors
- [ ] Shows user-friendly error UI
- [ ] Allows error recovery without page reload
- [ ] Logs errors for monitoring
- [ ] Shows stack trace in development only

#### Task 1.4.2: Add Service Layer Error Handling
**File:** `src/Frontend/ai-admin-dashboard/src/services/paymentService.ts`

```typescript
// Add retry logic and better error handling

import axios, { AxiosError } from 'axios';

class PaymentServiceError extends Error {
  constructor(
    message: string,
    public code: string,
    public status?: number,
    public details?: any
  ) {
    super(message);
    this.name = 'PaymentServiceError';
  }
}

class PaymentService {
  private async retryableRequest<T>(
    fn: () => Promise<T>,
    maxRetries: number = 3,
    retryDelay: number = 1000
  ): Promise<T> {
    let lastError: Error;

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        return await fn();
      } catch (error: any) {
        lastError = error;

        // Don't retry on client errors (4xx)
        if (error.response?.status >= 400 && error.response?.status < 500) {
          throw this.handleError(error);
        }

        // Don't retry on last attempt
        if (attempt === maxRetries) {
          throw this.handleError(error);
        }

        // Exponential backoff
        const delay = retryDelay * Math.pow(2, attempt);
        await new Promise(resolve => setTimeout(resolve, delay));

        console.log(`Retry attempt ${attempt + 1}/${maxRetries} after ${delay}ms`);
      }
    }

    throw this.handleError(lastError!);
  }

  private handleError(error: any): PaymentServiceError {
    if (axios.isAxiosError(error)) {
      const axiosError = error as AxiosError<any>;

      if (axiosError.response) {
        // Server responded with error
        const data = axiosError.response.data;
        return new PaymentServiceError(
          data.error || data.detail || 'Payment service error',
          data.error_code || 'PAYMENT_ERROR',
          axiosError.response.status,
          data.details
        );
      } else if (axiosError.request) {
        // Request made but no response
        return new PaymentServiceError(
          'No response from payment service',
          'NETWORK_ERROR'
        );
      }
    }

    // Unknown error
    return new PaymentServiceError(
      error.message || 'Unknown payment error',
      'UNKNOWN_ERROR'
    );
  }

  // Update all methods to use retryableRequest
  async getProviders(tenantId: string): Promise<PaymentProviderConfig[]> {
    return this.retryableRequest(async () => {
      const response = await axios.get(
        `${this.BASE_URL}/api/v2/payment-providers/tenants/${tenantId}/providers`,
        { headers: this.getAuthHeaders() }
      );
      return response.data.providers;
    });
  }

  // ... other methods
}
```

**Acceptance Criteria:**
- [ ] Automatic retry for transient errors
- [ ] Exponential backoff on retries
- [ ] Proper error classification
- [ ] Detailed error information
- [ ] No retry on 4xx errors

#### Task 1.4.3: Wrap Payment Routes with Error Boundary
**File:** `src/Frontend/ai-admin-dashboard/src/App.tsx`

```typescript
import { PaymentErrorBoundary } from './components/PaymentErrorBoundary';

// Wrap payment routes
{
  path: 'tenants/:tenantCode/payment-settings',
  element: (
    <PaymentErrorBoundary>
      <TenantPaymentSettings />
    </PaymentErrorBoundary>
  )
},
{
  path: 'payments',
  element: (
    <PaymentErrorBoundary>
      <Payments />
    </PaymentErrorBoundary>
  )
}
```

---

## 1.5 Idempotency Key Generation 🔴 P0

**Problem:** Potential duplicate payments on double-click
**Impact:** Financial loss, customer complaints
**Effort:** 1 day

### Tasks:

#### Task 1.5.1: Create Idempotency Utilities
**File:** `src/Frontend/ai-admin-dashboard/src/utils/idempotency.ts` (NEW)

```typescript
/**
 * Idempotency key generation and management
 * Prevents duplicate payment processing
 */

import { v4 as uuidv4 } from 'uuid';

const IDEMPOTENCY_KEY_PREFIX = 'payment';
const IDEMPOTENCY_STORAGE_KEY = 'payment_idempotency_keys';
const KEY_TTL_MS = 24 * 60 * 60 * 1000; // 24 hours

interface StoredKey {
  key: string;
  timestamp: number;
  context: string;
}

export class IdempotencyManager {
  /**
   * Generate a unique idempotency key for a payment operation
   */
  static generateKey(context: string = 'default'): string {
    const timestamp = Date.now();
    const uuid = uuidv4();
    const key = `${IDEMPOTENCY_KEY_PREFIX}-${context}-${timestamp}-${uuid}`;

    // Store key
    this.storeKey(key, context);

    return key;
  }

  /**
   * Store idempotency key with metadata
   */
  private static storeKey(key: string, context: string): void {
    try {
      const stored = this.getStoredKeys();
      stored.push({
        key,
        context,
        timestamp: Date.now(),
      });

      // Clean old keys
      const cleaned = stored.filter(
        item => Date.now() - item.timestamp < KEY_TTL_MS
      );

      localStorage.setItem(IDEMPOTENCY_STORAGE_KEY, JSON.stringify(cleaned));
    } catch (error) {
      console.error('Failed to store idempotency key:', error);
    }
  }

  /**
   * Get all stored idempotency keys
   */
  private static getStoredKeys(): StoredKey[] {
    try {
      const stored = localStorage.getItem(IDEMPOTENCY_STORAGE_KEY);
      return stored ? JSON.parse(stored) : [];
    } catch {
      return [];
    }
  }

  /**
   * Check if a key has been used recently
   */
  static hasRecentKey(context: string, withinMs: number = 60000): boolean {
    const keys = this.getStoredKeys();
    const cutoff = Date.now() - withinMs;

    return keys.some(
      item => item.context === context && item.timestamp > cutoff
    );
  }

  /**
   * Clear old idempotency keys
   */
  static cleanup(): void {
    const keys = this.getStoredKeys();
    const cleaned = keys.filter(
      item => Date.now() - item.timestamp < KEY_TTL_MS
    );

    localStorage.setItem(IDEMPOTENCY_STORAGE_KEY, JSON.stringify(cleaned));
  }
}

// Auto cleanup on load
if (typeof window !== 'undefined') {
  IdempotencyManager.cleanup();
}
```

**Acceptance Criteria:**
- [ ] Unique keys generated for each operation
- [ ] Keys stored with context
- [ ] Automatic cleanup of old keys
- [ ] Prevention of duplicate operations
- [ ] Works across page reloads

#### Task 1.5.2: Integrate into Payment Service
**File:** `src/Frontend/ai-admin-dashboard/src/services/paymentService.ts`

```typescript
import { IdempotencyManager } from '../utils/idempotency';

class PaymentService {
  async processPayment(
    tenantId: string,
    request: CreatePaymentRequest
  ): Promise<PaymentTransactionDTO> {
    // Generate idempotency key if not provided
    const idempotencyKey = request.idempotency_key ||
      IdempotencyManager.generateKey(`payment-${request.order_id || 'manual'}`);

    // Check for recent duplicate
    if (IdempotencyManager.hasRecentKey(`payment-${request.order_id || 'manual'}`, 5000)) {
      throw new Error('Duplicate payment attempt detected. Please wait a few seconds.');
    }

    const response = await this.retryableRequest(async () => {
      return await axios.post(
        `${this.BASE_URL}/api/v2/payments/process`,
        { ...request, idempotency_key: idempotencyKey },
        { headers: this.getAuthHeaders() }
      );
    });

    return response.data;
  }

  async processRefund(
    tenantId: string,
    transactionId: string,
    request: CreateRefundRequest
  ): Promise<void> {
    // Generate idempotency key for refund
    const idempotencyKey = IdempotencyManager.generateKey(`refund-${transactionId}`);

    await this.retryableRequest(async () => {
      return await axios.post(
        `${this.BASE_URL}/api/v2/payments/${transactionId}/refund`,
        { ...request, idempotency_key: idempotencyKey },
        { headers: this.getAuthHeaders() }
      );
    });
  }
}
```

**Acceptance Criteria:**
- [ ] All payment operations use idempotency keys
- [ ] Keys auto-generated if not provided
- [ ] Duplicate detection within 5 seconds
- [ ] User-friendly duplicate error messages

---

# Phase 2: Critical Features (Sprint 3-4) 🟠

**Duration:** 4-6 weeks
**Goal:** Complete production-critical features
**Success Criteria:** System ready for production deployment

## 2.1 Complete Provider Management UI 🟠 P1

**Problem:** Cannot add/edit/delete providers from UI
**Impact:** Manual database updates required
**Effort:** 4-5 days

### Tasks:

#### Task 2.1.1: Provider Creation Flow
**File:** `src/Frontend/ai-admin-dashboard/src/components/AddProviderModal.tsx` (NEW)

```typescript
import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from './ui/dialog';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Shield, Loader2 } from 'lucide-react';
import { usePayment } from '../contexts/PaymentContext';
import { toast } from './ui/use-toast';

interface AddProviderModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const AddProviderModal: React.FC<AddProviderModalProps> = ({
  isOpen,
  onClose,
}) => {
  const { t } = useTranslation(['payments', 'common']);
  const { addProvider } = usePayment();

  const [formData, setFormData] = useState({
    provider_type: 'clover' as 'clover' | 'moneris' | 'interac',
    merchant_id: '',
    api_key: '',
    environment: 'sandbox' as 'sandbox' | 'production',
    is_active: true,
  });

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [testingConnection, setTestingConnection] = useState(false);
  const [connectionTestResult, setConnectionTestResult] = useState<{
    success: boolean;
    message: string;
  } | null>(null);

  const handleTestConnection = async () => {
    setTestingConnection(true);
    setConnectionTestResult(null);

    try {
      // Call test endpoint
      const response = await fetch('/api/v2/payment-providers/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });

      const result = await response.json();

      setConnectionTestResult({
        success: response.ok,
        message: result.message || (response.ok ? 'Connection successful!' : 'Connection failed'),
      });
    } catch (error: any) {
      setConnectionTestResult({
        success: false,
        message: error.message || 'Connection test failed',
      });
    } finally {
      setTestingConnection(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    setIsSubmitting(true);

    try {
      await addProvider(formData);

      toast({
        title: t('common:messages.success'),
        description: t('payments:settings.notifications.providerAdded'),
      });

      onClose();

      // Reset form
      setFormData({
        provider_type: 'clover',
        merchant_id: '',
        api_key: '',
        environment: 'sandbox',
        is_active: true,
      });

    } catch (error: any) {
      toast({
        title: t('payments:messages.error.title'),
        description: error.message || t('payments:settings.notifications.providerAddFailed'),
        variant: 'destructive',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>{t('payments:settings.addProvider')}</DialogTitle>
          <DialogDescription>
            {t('payments:settings.addProviderDescription')}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Provider Type */}
          <div>
            <Label htmlFor="provider_type">
              {t('payments:settings.providerType')}
            </Label>
            <Select
              value={formData.provider_type}
              onValueChange={(value: any) =>
                setFormData({ ...formData, provider_type: value })
              }
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="clover">🍀 Clover</SelectItem>
                <SelectItem value="moneris">💳 Moneris</SelectItem>
                <SelectItem value="interac">🏦 Interac</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Environment */}
          <div>
            <Label htmlFor="environment">
              {t('payments:settings.environment')}
            </Label>
            <Select
              value={formData.environment}
              onValueChange={(value: any) =>
                setFormData({ ...formData, environment: value })
              }
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="sandbox">
                  {t('payments:settings.sandbox')}
                </SelectItem>
                <SelectItem value="production">
                  {t('payments:settings.production')}
                </SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Merchant ID */}
          <div>
            <Label htmlFor="merchant_id">
              {t('payments:settings.merchantId')}
              <span className="text-destructive ml-1">*</span>
            </Label>
            <Input
              id="merchant_id"
              type="text"
              value={formData.merchant_id}
              onChange={(e) =>
                setFormData({ ...formData, merchant_id: e.target.value })
              }
              placeholder={t('payments:settings.merchantIdPlaceholder')}
              required
            />
          </div>

          {/* API Key */}
          <div>
            <Label htmlFor="api_key">
              {t('payments:settings.apiKey')}
              <span className="text-destructive ml-1">*</span>
            </Label>
            <Input
              id="api_key"
              type="password"
              value={formData.api_key}
              onChange={(e) =>
                setFormData({ ...formData, api_key: e.target.value })
              }
              placeholder={t('payments:settings.apiKeyPlaceholder')}
              required
            />
          </div>

          {/* Security Notice */}
          <div className="bg-warning-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
            <div className="flex gap-2">
              <Shield className="w-5 h-5 text-warning-600 dark:text-yellow-400 flex-shrink-0 mt-0.5" />
              <div className="text-sm text-yellow-700 dark:text-yellow-300">
                <strong>{t('payments:settings.securityNotice')}</strong>{' '}
                {t('payments:settings.credentialsWillBeEncrypted')}
              </div>
            </div>
          </div>

          {/* Test Connection Button */}
          <Button
            type="button"
            variant="outline"
            onClick={handleTestConnection}
            disabled={!formData.merchant_id || !formData.api_key || testingConnection}
          >
            {testingConnection ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                {t('payments:settings.testing')}
              </>
            ) : (
              t('payments:settings.testConnection')
            )}
          </Button>

          {/* Connection Test Result */}
          {connectionTestResult && (
            <div
              className={`p-4 rounded-lg ${
                connectionTestResult.success
                  ? 'bg-green-50 border border-green-200 text-green-800'
                  : 'bg-red-50 border border-red-200 text-red-800'
              }`}
            >
              {connectionTestResult.message}
            </div>
          )}

          <DialogFooter>
            <Button type="button" variant="outline" onClick={onClose}>
              {t('common:actions.cancel')}
            </Button>
            <Button
              type="submit"
              disabled={isSubmitting || !formData.merchant_id || !formData.api_key}
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  {t('common:actions.adding')}
                </>
              ) : (
                t('common:actions.add')
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};
```

**Acceptance Criteria:**
- [ ] Provider type selection
- [ ] Environment selection
- [ ] Credential input with validation
- [ ] Connection test before saving
- [ ] Proper error handling
- [ ] Success feedback

[Continuing in next response due to length...]

**Remaining sections to include:**
- Task 2.1.2: Provider Edit/Delete
- Task 2.1.3: Provider Health Monitoring
- Section 2.2: Webhook Implementation
- Section 2.3: Transaction Export
- Phase 3: Testing (Sprint 5)
- Phase 4: Advanced Features (Sprint 6-7)
- Appendices (API Reference, Testing Checklist, Deployment Checklist)

Would you like me to continue with the complete plan?
