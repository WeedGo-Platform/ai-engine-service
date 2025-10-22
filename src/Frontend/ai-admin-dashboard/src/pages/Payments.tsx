import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import {
  CreditCard,
  DollarSign,
  TrendingUp,
  TrendingDown,
  RefreshCw,
  Download,
  AlertCircle,
import { formatCurrency } from '../utils/currency';
  CheckCircle,
  XCircle,
  Clock,
  Search,
  Eye,
  Undo,
  Settings,
} from 'lucide-react';
import { format } from 'date-fns';
import { paymentService } from '../services/paymentServiceV2';
import type {
  PaymentTransactionDTO,
  TransactionFilters,
  CreateRefundRequest,
} from '../types/payment';
import { ApiError, NetworkError, AuthenticationError } from '../utils/api-error-handler';
import { useStoreContext } from '../contexts/StoreContext';
import toast from 'react-hot-toast';

interface Transaction {
  id: string;
  transaction_reference: string;
  provider_transaction_id: string;
  type: string;
  status: string;
  amount: number;
  currency: string;
  provider_name: string;
  customer_name: string;
  order_id: string;
  created_at: string;
  completed_at: string;
  error_message?: string;
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

const PaymentsPage: React.FC = () => {
  const { t } = useTranslation(['payments', 'common']);
  const { currentStore } = useStoreContext();
  const navigate = useNavigate();

  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [metrics, setMetrics] = useState<PaymentMetrics | null>(null);
  const [selectedTransaction, setSelectedTransaction] = useState<Transaction | null>(null);
  const [dateRange, setDateRange] = useState({
    from: new Date(new Date().setDate(new Date().getDate() - 30)),
    to: new Date()
  });
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [refundAmount, setRefundAmount] = useState('');
  const [refundReason, setRefundReason] = useState('');
  const [isRefundDialogOpen, setIsRefundDialogOpen] = useState(false);
  const [isDetailDialogOpen, setIsDetailDialogOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  // Currency input handler - treats input like a cash register (last 2 digits are cents)
  const handleCurrencyInput = (value: string, setter: (val: string) => void) => {
    // Remove all non-numeric characters
    const numericValue = value.replace(/\D/g, '');
    
    // Handle empty input
    if (numericValue === '') {
      setter('');
      return;
    }
    
    // Convert to cents and then to dollar format
    const cents = parseInt(numericValue, 10);
    const dollars = (cents / 100).toFixed(2);
    setter(dollars);
  };

  // Only use tenant_id if it's actually available (not from incomplete store data)
  const tenantId = currentStore?.tenant_id;

  useEffect(() => {
    // Only fetch if we have a complete store object with tenant_id
    if (currentStore?.id && currentStore?.tenant_id) {
      fetchTransactions();
      fetchMetrics();
    } else if (currentStore?.id && !currentStore?.tenant_id) {
      // Store is selected but data is incomplete - wait for full load
      console.log('Waiting for complete store data (tenant_id missing)...');
      setIsLoading(true);
    }
  }, [dateRange, statusFilter, currentStore?.id, currentStore?.tenant_id]);

  const fetchTransactions = async () => {
    // Guard: Don't fetch without valid tenant_id
    if (!currentStore?.id || !tenantId) {
      console.warn('Cannot fetch transactions: missing tenant_id');
      return;
    }

    try {
      setIsLoading(true);

      const filters: TransactionFilters = {
        start_date: format(dateRange.from, 'yyyy-MM-dd'),
        end_date: format(dateRange.to, 'yyyy-MM-dd'),
        status: statusFilter !== 'all' ? statusFilter : undefined,
        limit: 100,
        offset: 0,
      };

      const response = await paymentService.getTransactions(tenantId, filters);
      setTransactions(response.transactions as any);
    } catch (error) {
      if (error instanceof ApiError) {
        toast.error(error.getUserMessage());
      } else {
        toast.error(t('common:messages.error'));
      }
    } finally {
      setIsLoading(false);
    }
  };

  const fetchMetrics = async () => {
    // Guard: Don't fetch without valid tenant_id
    if (!currentStore?.id || !tenantId) {
      console.warn('Cannot fetch metrics: missing tenant_id');
      return;
    }

    try {
      const metricsData = await paymentService.getPaymentStats(tenantId, {
        start: format(dateRange.from, 'yyyy-MM-dd'),
        end: format(dateRange.to, 'yyyy-MM-dd'),
      });

      setMetrics({
        total_transactions: metricsData.total_transactions,
        successful_transactions: metricsData.successful_transactions,
        failed_transactions: metricsData.failed_transactions,
        total_amount: metricsData.total_volume,
        total_fees: metricsData.total_fees || 0,
        total_refunds: metricsData.total_refunds || 0,
        success_rate: metricsData.success_rate,
        avg_transaction_time: metricsData.average_transaction_time || 0,
      });
    } catch (error) {
      console.error('Error fetching metrics:', error);
      setMetrics(null);
    }
  };

  const processRefund = async () => {
    if (!selectedTransaction || !refundAmount || !tenantId) {
      if (!tenantId) {
        toast.error('Store information not available. Please try again.');
      }
      return;
    }

    try {
      const refundRequest: CreateRefundRequest = {
        amount: parseFloat(refundAmount),
        currency: selectedTransaction.currency,
        reason: refundReason || 'Customer requested refund',
        tenant_id: tenantId,
      };

      await paymentService.refundTransaction(
        selectedTransaction.id,
        refundRequest
      );

      toast.success(t('common:messages.success'));
      setIsRefundDialogOpen(false);
      setRefundAmount('');
      setRefundReason('');

      await Promise.all([
        fetchTransactions(),
        fetchMetrics(),
      ]);
    } catch (error) {
      if (error instanceof ApiError) {
        toast.error(error.getUserMessage());
      } else {
        toast.error(t('common:messages.error'));
      }
    }
  };

  const getStatusBadge = (status: string) => {
    const statusConfig: Record<string, { color: string; icon: any }> = {
      completed: { color: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300', icon: CheckCircle },
      pending: { color: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300', icon: Clock },
      processing: { color: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300', icon: RefreshCw },
      failed: { color: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300', icon: XCircle },
      refunded: { color: 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-300', icon: Undo },
    };

    const config = statusConfig[status] || statusConfig.pending;
    const Icon = config.icon;

    return (
      <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium ${config.color}`}>
        <Icon className="h-3 w-3" />
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    );
  };

  const filteredTransactions = transactions.filter(transaction => {
    const matchesSearch = searchTerm === '' ||
      transaction.transaction_reference.toLowerCase().includes(searchTerm.toLowerCase()) ||
      transaction.customer_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      transaction.order_id?.toLowerCase().includes(searchTerm.toLowerCase());

    return matchesSearch;
  });

  if (!currentStore) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-gray-500 dark:text-gray-400">Please select a store to view payments</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Payments</h1>
        <div className="flex gap-2">
          <button
            onClick={() => fetchTransactions()}
            className="inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm text-sm font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </button>
          <button className="inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm text-sm font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700">
            <Download className="h-4 w-4 mr-2" />
            Export
          </button>
        </div>
      </div>

      {/* Metrics Cards */}
      {metrics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <DollarSign className="h-6 w-6 text-gray-400" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">
                      Total Revenue
                    </dt>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">
                      {formatCurrency(metrics.total_amount)}
                    </p>
                    <dd className="text-xs text-gray-500 dark:text-gray-400">
                      {metrics.total_transactions} transactions
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <TrendingUp className="h-6 w-6 text-gray-400" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">
                      Success Rate
                    </dt>
                    <dd className="text-2xl font-semibold text-gray-900 dark:text-white">
                      {metrics.success_rate.toFixed(1)}%
                    </dd>
                    <dd className="text-xs text-gray-500 dark:text-gray-400">
                      {metrics.successful_transactions} successful
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <TrendingDown className="h-6 w-6 text-gray-400" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">
                      Total Refunds
                    </dt>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">
                      {formatCurrency(metrics.total_refunds)}
                    </p>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <AlertCircle className="h-6 w-6 text-gray-400" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">
                      Processing Fees
                    </dt>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">
                      {formatCurrency(metrics.total_fees)}
                    </p>
                    <dd className="text-xs text-gray-500 dark:text-gray-400">
                      {((metrics.total_fees / metrics.total_amount) * 100).toFixed(2)}% of revenue
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Transactions Table */}
      <div className="bg-white dark:bg-gray-800 shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900 dark:text-white mb-4">
            Transaction History
          </h3>

          {/* Filters */}
          <div className="flex flex-col lg:flex-row gap-4 mb-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search transactions..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                />
              </div>
            </div>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="block w-full lg:w-48 rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
            >
              <option value="all">All Status</option>
              <option value="completed">Completed</option>
              <option value="pending">Pending</option>
              <option value="failed">Failed</option>
              <option value="refunded">Refunded</option>
            </select>
          </div>

          {/* Table */}
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-900">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Reference
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Customer
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Amount
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                {isLoading ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-4 text-center text-sm text-gray-500 dark:text-gray-400">
                      Loading...
                    </td>
                  </tr>
                ) : filteredTransactions.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-12">
                      <div className="text-center">
                        <CreditCard className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                          No Transactions Yet
                        </h3>
                        <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                          {transactions.length === 0
                            ? "Configure your payment providers to start processing transactions"
                            : "No transactions match your current filters"}
                        </p>
                        {transactions.length === 0 && currentStore?.store_code && (
                          <button
                            onClick={() => navigate(`/dashboard/stores/${currentStore.store_code}/settings`)}
                            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                          >
                            <Settings className="w-4 h-4" />
                            Configure Payment Providers
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ) : (
                  filteredTransactions.map((transaction) => (
                    <tr key={transaction.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                        {transaction.transaction_reference}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                        {transaction.customer_name || 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                        {formatCurrency(transaction.amount)} {transaction.currency}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        {getStatusBadge(transaction.status)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                        {format(new Date(transaction.created_at), 'MMM dd, yyyy HH:mm')}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <div className="flex gap-2">
                          <button
                            onClick={() => {
                              setSelectedTransaction(transaction);
                              setIsDetailDialogOpen(true);
                            }}
                            className="text-primary-600 hover:text-primary-900 dark:text-primary-400 dark:hover:text-primary-300"
                          >
                            <Eye className="h-4 w-4" />
                          </button>
                          {transaction.status === 'completed' && (
                            <button
                              onClick={() => {
                                setSelectedTransaction(transaction);
                                setIsRefundDialogOpen(true);
                              }}
                              className="text-yellow-600 hover:text-yellow-900 dark:text-yellow-400 dark:hover:text-yellow-300"
                            >
                              <Undo className="h-4 w-4" />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Refund Dialog */}
      {isRefundDialogOpen && selectedTransaction && (
        <div className="fixed z-10 inset-0 overflow-y-auto">
          <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={() => setIsRefundDialogOpen(false)}></div>
            <div className="inline-block align-bottom bg-white dark:bg-gray-800 rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
              <div className="bg-white dark:bg-gray-800 px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                <h3 className="text-lg leading-6 font-medium text-gray-900 dark:text-white mb-4">
                  Process Refund
                </h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                      Original Amount
                    </label>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">
                      {formatCurrency(selectedTransaction.amount)} {selectedTransaction.currency}
                    </p>
                  </div>
                  <div>
                    <label htmlFor="refund-amount" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                      Refund Amount
                    </label>
                    <input
                      id="refund-amount"
                      type="text"
                      max={selectedTransaction.amount}
                      value={refundAmount}
                      onChange={(e) => handleCurrencyInput(e.target.value, setRefundAmount)}
                      placeholder="Enter refund amount"
                      className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                    />
                  </div>
                  <div>
                    <label htmlFor="refund-reason" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                      Reason
                    </label>
                    <input
                      id="refund-reason"
                      type="text"
                      value={refundReason}
                      onChange={(e) => setRefundReason(e.target.value)}
                      placeholder="Enter refund reason"
                      className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                    />
                  </div>
                </div>
              </div>
              <div className="bg-gray-50 dark:bg-gray-900 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                <button
                  onClick={processRefund}
                  className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-primary-600 text-base font-medium text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:ml-3 sm:w-auto sm:text-sm"
                >
                  Process Refund
                </button>
                <button
                  onClick={() => setIsRefundDialogOpen(false)}
                  className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 dark:border-gray-600 shadow-sm px-4 py-2 bg-white dark:bg-gray-800 text-base font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PaymentsPage;
