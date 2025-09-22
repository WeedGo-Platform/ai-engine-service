import React, { useState, useEffect } from 'react';
import {
  Search, Filter, Calendar, DollarSign, CreditCard,
  RefreshCw, Eye, Receipt, X, Check, AlertCircle,
  ArrowUpDown, FileText, Loader2
} from 'lucide-react';
import { useStoreContext } from '../../contexts/StoreContext';
import posService from '../../services/posService';

interface Transaction {
  id: string;
  receipt_number: string;
  customer_id?: string;
  customer_name?: string;
  customer_email?: string;
  items: any[];
  subtotal: number;
  tax: number;
  total: number;
  refunded_amount?: number;
  payment_method: 'cash' | 'card' | 'debit' | 'split';
  status: 'completed' | 'parked' | 'cancelled' | 'refunded' | 'partial_refund';
  timestamp: string;
  cashier_id?: string;
  cashier_name?: string;
  store_id: string;
}

interface RefundModalProps {
  transaction: Transaction;
  onClose: () => void;
  onRefund: (transactionId: string, amount: number, reason: string, items?: any[]) => Promise<void>;
}

const RefundModal: React.FC<RefundModalProps> = ({ transaction, onClose, onRefund }) => {
  const [refundType, setRefundType] = useState<'full' | 'partial' | 'items'>('full');
  const [refundAmount, setRefundAmount] = useState(transaction.total - ((transaction.refunded_amount ?? 0) || 0));
  const [selectedItems, setSelectedItems] = useState<any[]>([]);
  const [refundReason, setRefundReason] = useState('');
  const [processing, setProcessing] = useState(false);

  const maxRefundable = transaction.total - ((transaction.refunded_amount ?? 0) || 0);

  const handleRefund = async () => {
    if (!refundReason.trim()) {
      alert('Please provide a reason for the refund');
      return;
    }

    if (refundType === 'partial' && (refundAmount <= 0 || refundAmount > maxRefundable)) {
      alert(`Refund amount must be between $0.01 and $${maxRefundable.toFixed(2)}`);
      return;
    }

    if (refundType === 'items' && selectedItems.length === 0) {
      alert('Please select items to refund');
      return;
    }

    setProcessing(true);
    try {
      const amount = refundType === 'full' ? maxRefundable :
                     refundType === 'partial' ? refundAmount :
                     selectedItems.reduce((sum, item) => sum + (item.price * item.quantity), 0);

      await onRefund(
        transaction.id,
        amount,
        refundReason,
        refundType === 'items' ? selectedItems : undefined
      );
      onClose();
    } catch (error) {
      console.error('Refund failed:', error);
      alert('Failed to process refund. Please try again.');
    } finally {
      setProcessing(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-lg border border-gray-200 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold">Process Refund</h2>
            <button onClick={onClose} className="p-1 hover:bg-gray-50 rounded">
              <X className="w-5 h-5" />
            </button>
          </div>
          <div className="mt-2 text-sm text-gray-600">
            Transaction: {transaction.receipt_number} |
            Total: ${transaction.total.toFixed(2)} |
            {(transaction.refunded_amount ?? 0) ? ` Previously refunded: $${(transaction.refunded_amount ?? 0).toFixed(2)}` : ''}
          </div>
        </div>

        <div className="p-6">
          {/* Refund Type Selection */}
          <div className="mb-6">
            <label className="block text-sm font-medium mb-3">Refund Type</label>
            <div className="grid grid-cols-3 gap-4">
              <button
                onClick={() => setRefundType('full')}
                className={`p-4 rounded-lg border-2 transition-colors ${
                  refundType === 'full'
                    ? 'border-blue-500 bg-blue-50 text-accent-700'
                    : 'border-gray-200 hover:border-gray-200'
                }`}
              >
                <Check className="w-5 h-5 mx-auto mb-1" />
                <span className="text-sm">Full Refund</span>
                <p className="text-xs text-gray-500 mt-1">${maxRefundable.toFixed(2)}</p>
              </button>

              <button
                onClick={() => setRefundType('partial')}
                className={`p-4 rounded-lg border-2 transition-colors ${
                  refundType === 'partial'
                    ? 'border-blue-500 bg-blue-50 text-accent-700'
                    : 'border-gray-200 hover:border-gray-200'
                }`}
              >
                <DollarSign className="w-5 h-5 mx-auto mb-1" />
                <span className="text-sm">Partial Refund</span>
                <p className="text-xs text-gray-500 mt-1">Custom amount</p>
              </button>

              <button
                onClick={() => setRefundType('items')}
                className={`p-4 rounded-lg border-2 transition-colors ${
                  refundType === 'items'
                    ? 'border-blue-500 bg-blue-50 text-accent-700'
                    : 'border-gray-200 hover:border-gray-200'
                }`}
              >
                <FileText className="w-5 h-5 mx-auto mb-1" />
                <span className="text-sm">Item Refund</span>
                <p className="text-xs text-gray-500 mt-1">Select items</p>
              </button>
            </div>
          </div>

          {/* Partial Refund Amount */}
          {refundType === 'partial' && (
            <div className="mb-6">
              <label className="block text-sm font-medium mb-2">Refund Amount</label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500">$</span>
                <input
                  type="number"
                  step="0.01"
                  min="0.01"
                  max={maxRefundable}
                  value={refundAmount}
                  onChange={(e) => setRefundAmount(parseFloat(e.target.value) || 0)}
                  className="w-full pl-8 pr-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <p className="text-xs text-gray-500 mt-1">
                Maximum refundable: ${maxRefundable.toFixed(2)}
              </p>
            </div>
          )}

          {/* Item Selection for Item Refund */}
          {refundType === 'items' && (
            <div className="mb-6">
              <label className="block text-sm font-medium mb-2">Select Items to Refund</label>
              <div className="border rounded-lg max-h-48 overflow-y-auto">
                {transaction.items.map((item, index) => (
                  <label
                    key={index}
                    className="flex items-center p-4 hover:bg-gray-50 cursor-pointer border-b last:border-b-0"
                  >
                    <input
                      type="checkbox"
                      checked={selectedItems.some(si => si.id === item.product?.id)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedItems([...selectedItems, item]);
                        } else {
                          setSelectedItems(selectedItems.filter(si => si.id !== item.product?.id));
                        }
                      }}
                      className="mr-3"
                    />
                    <div className="flex-1">
                      <p className="font-medium text-sm">{item.product?.name}</p>
                      <p className="text-xs text-gray-500">
                        Qty: {item.quantity} × ${item.product?.price?.toFixed(2)}
                      </p>
                    </div>
                    <span className="font-medium">
                      ${((item.product?.price || 0) * item.quantity).toFixed(2)}
                    </span>
                  </label>
                ))}
              </div>
              {selectedItems.length > 0 && (
                <p className="text-sm text-accent-600 mt-2">
                  Total to refund: ${selectedItems.reduce((sum, item) =>
                    sum + ((item.product?.price || 0) * item.quantity), 0
                  ).toFixed(2)}
                </p>
              )}
            </div>
          )}

          {/* Refund Reason */}
          <div className="mb-6">
            <label className="block text-sm font-medium mb-2">
              Reason for Refund <span className="text-red-500">*</span>
            </label>
            <textarea
              value={refundReason}
              onChange={(e) => setRefundReason(e.target.value)}
              placeholder="Enter reason for refund..."
              className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
              rows={3}
              required
            />
          </div>

          {/* Warning */}
          <div className="mb-6 p-4 bg-warning-50 border border-yellow-200 rounded-lg flex items-start gap-2">
            <AlertCircle className="w-5 h-5 text-warning-600 mt-0.5" />
            <div className="text-sm text-warning-800">
              <p className="font-medium">Important:</p>
              <p>Refunds cannot be reversed. Please verify the refund details before proceeding.</p>
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-4">
            <button
              onClick={onClose}
              className="px-4 py-2 border rounded-lg hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              onClick={handleRefund}
              disabled={processing || !refundReason.trim()}
              className="px-4 py-2 bg-danger-500 text-white rounded-lg hover:bg-danger-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {processing ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  <RefreshCw className="w-4 h-4" />
                  Process Refund
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default function TransactionHistory() {
  const { currentStore } = useStoreContext();
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [filteredTransactions, setFilteredTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [dateRange, setDateRange] = useState({
    start: new Date(new Date().setHours(0, 0, 0, 0)).toISOString().split('T')[0],
    end: new Date().toISOString().split('T')[0]
  });
  const [filters, setFilters] = useState({
    status: 'all',
    paymentMethod: 'all',
    minAmount: '',
    maxAmount: ''
  });
  const [sortBy, setSortBy] = useState<'date' | 'amount' | 'customer'>('date');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [selectedTransaction, setSelectedTransaction] = useState<Transaction | null>(null);
  const [showRefundModal, setShowRefundModal] = useState(false);
  const [showFilters, setShowFilters] = useState(false);

  // Fetch transactions
  const fetchTransactions = async () => {
    if (!currentStore?.id) return;

    setLoading(true);
    try {
      const history = await posService.getTransactionHistory(
        currentStore.id,
        dateRange.start,
        dateRange.end
      );
      setTransactions(history);
      applyFilters(history);
    } catch (error) {
      console.error('Failed to fetch transactions:', error);
    } finally {
      setLoading(false);
    }
  };

  // Apply filters and search
  const applyFilters = (txns: Transaction[] = transactions) => {
    let filtered = [...txns];

    // Filter by store (important!)
    if (currentStore?.id) {
      filtered = filtered.filter(t => t.store_id === currentStore.id);
    }

    // Search filter
    if (searchTerm) {
      const search = searchTerm.toLowerCase();
      filtered = filtered.filter(t =>
        t.receipt_number?.toLowerCase().includes(search) ||
        t.customer_name?.toLowerCase().includes(search) ||
        t.customer_email?.toLowerCase().includes(search) ||
        t.id.toLowerCase().includes(search)
      );
    }

    // Status filter
    if (filters.status !== 'all') {
      filtered = filtered.filter(t => t.status === filters.status);
    }

    // Payment method filter
    if (filters.paymentMethod !== 'all') {
      filtered = filtered.filter(t => t.payment_method === filters.paymentMethod);
    }

    // Amount filters
    if (filters.minAmount) {
      filtered = filtered.filter(t => t.total >= parseFloat(filters.minAmount));
    }
    if (filters.maxAmount) {
      filtered = filtered.filter(t => t.total <= parseFloat(filters.maxAmount));
    }

    // Sort
    filtered.sort((a, b) => {
      let comparison = 0;
      switch (sortBy) {
        case 'date':
          comparison = new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime();
          break;
        case 'amount':
          comparison = a.total - b.total;
          break;
        case 'customer':
          comparison = (a.customer_name || '').localeCompare(b.customer_name || '');
          break;
      }
      return sortOrder === 'asc' ? comparison : -comparison;
    });

    setFilteredTransactions(filtered);
  };

  // Process refund
  const processRefund = async (transactionId: string, amount: number, reason: string, items?: any[]) => {
    try {
      await posService.processRefund(transactionId, {
        amount,
        reason,
        items,
        processed_by: 'current_user' // TODO: Get from auth context
      });

      // Refresh transactions
      await fetchTransactions();
      setShowRefundModal(false);
      setSelectedTransaction(null);
      alert('Refund processed successfully');
    } catch (error) {
      console.error('Failed to process refund:', error);
      throw error;
    }
  };

  // Effects
  useEffect(() => {
    if (currentStore?.id) {
      fetchTransactions();
    }
  }, [currentStore, dateRange]);

  useEffect(() => {
    applyFilters();
  }, [searchTerm, filters, sortBy, sortOrder]);

  const getStatusBadge = (status: string) => {
    const styles = {
      completed: 'bg-primary-100 text-primary-700',
      parked: 'bg-warning-100 text-yellow-700',
      cancelled: 'bg-gray-50 text-gray-700',
      refunded: 'bg-danger-100 text-red-700',
      partial_refund: 'bg-orange-100 text-orange-700'
    };
    return styles[status] || 'bg-gray-50 text-gray-700';
  };

  const getPaymentMethodIcon = (method: string) => {
    switch (method) {
      case 'cash':
        return <DollarSign className="w-4 h-4" />;
      case 'card':
      case 'debit':
        return <CreditCard className="w-4 h-4" />;
      default:
        return <DollarSign className="w-4 h-4" />;
    }
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header with Search and Filters */}
      <div className="bg-white p-6 border-b">
        <div className="flex flex-col lg:flex-row gap-6">
          {/* Search */}
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input
              type="text"
              placeholder="Search by receipt #, customer name, email..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border rounded-lg"
            />
          </div>

          {/* Date Range */}
          <div className="flex items-center gap-2">
            <Calendar className="w-5 h-5 text-gray-400" />
            <input
              type="date"
              value={dateRange.start}
              onChange={(e) => setDateRange({ ...dateRange, start: e.target.value })}
              className="px-3 py-2 border rounded-lg"
            />
            <span className="text-gray-500">to</span>
            <input
              type="date"
              value={dateRange.end}
              onChange={(e) => setDateRange({ ...dateRange, end: e.target.value })}
              className="px-3 py-2 border rounded-lg"
            />
          </div>

          {/* Filter Toggle */}
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`px-4 py-2 border rounded-lg flex items-center gap-2 ${
              showFilters ? 'bg-blue-50 border-blue-300 text-accent-700' : 'hover:bg-gray-50'
            }`}
          >
            <Filter className="w-4 h-4" />
            Filters
            {(filters.status !== 'all' || filters.paymentMethod !== 'all' ||
              filters.minAmount || filters.maxAmount) && (
              <span className="px-1.5 py-0.5 bg-accent-600 text-white text-xs rounded-full">
                {[filters.status !== 'all', filters.paymentMethod !== 'all',
                  !!filters.minAmount, !!filters.maxAmount].filter(Boolean).length}
              </span>
            )}
          </button>

          {/* Refresh */}
          <button
            onClick={fetchTransactions}
            className="px-4 py-2 border rounded-lg hover:bg-gray-50"
            disabled={loading}
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>

        {/* Filter Panel */}
        {showFilters && (
          <div className="mt-4 p-6 bg-gray-50 rounded-lg grid grid-cols-1 md:grid-cols-4 gap-6">
            <div>
              <label className="block text-sm font-medium mb-1">Status</label>
              <select
                value={filters.status}
                onChange={(e) => setFilters({ ...filters, status: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
              >
                <option value="all">All Statuses</option>
                <option value="completed">Completed</option>
                <option value="refunded">Refunded</option>
                <option value="partial_refund">Partial Refund</option>
                <option value="cancelled">Cancelled</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Payment Method</label>
              <select
                value={filters.paymentMethod}
                onChange={(e) => setFilters({ ...filters, paymentMethod: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
              >
                <option value="all">All Methods</option>
                <option value="cash">Cash</option>
                <option value="card">Card</option>
                <option value="debit">Debit</option>
                <option value="split">Split Payment</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Min Amount</label>
              <input
                type="number"
                placeholder="0.00"
                value={filters.minAmount}
                onChange={(e) => setFilters({ ...filters, minAmount: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Max Amount</label>
              <input
                type="number"
                placeholder="999.99"
                value={filters.maxAmount}
                onChange={(e) => setFilters({ ...filters, maxAmount: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
              />
            </div>
          </div>
        )}
      </div>

      {/* Summary Stats */}
      <div className="bg-white px-4 py-3 border-b">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">
            Showing {filteredTransactions.length} of {transactions.length} transactions
          </span>
          <div className="flex items-center gap-6">
            <span className="text-gray-600">
              Total: ${filteredTransactions.reduce((sum, t) => sum + t.total, 0).toFixed(2)}
            </span>
            <span className="text-gray-600">
              Refunded: ${filteredTransactions.reduce((sum, t) => sum + (t.refunded_amount || 0), 0).toFixed(2)}
            </span>
          </div>
        </div>
      </div>

      {/* Transactions Table */}
      <div className="flex-1 overflow-auto">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
          </div>
        ) : filteredTransactions.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <Receipt className="w-12 h-12 mx-auto mb-3 text-gray-300" />
            <p>No transactions found</p>
            <p className="text-sm mt-1">Try adjusting your filters or date range</p>
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-gray-50 sticky top-0">
              <tr>
                <th className="px-4 py-3 text-left">
                  <button
                    onClick={() => {
                      setSortBy('date');
                      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
                    }}
                    className="flex items-center gap-1 font-medium text-sm text-gray-700 hover:text-gray-900"
                  >
                    Date/Time
                    <ArrowUpDown className="w-3 h-3" />
                  </button>
                </th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Receipt #</th>
                <th className="px-4 py-3 text-left">
                  <button
                    onClick={() => {
                      setSortBy('customer');
                      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
                    }}
                    className="flex items-center gap-1 font-medium text-sm text-gray-700 hover:text-gray-900"
                  >
                    Customer
                    <ArrowUpDown className="w-3 h-3" />
                  </button>
                </th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Items</th>
                <th className="px-4 py-3 text-left">
                  <button
                    onClick={() => {
                      setSortBy('amount');
                      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
                    }}
                    className="flex items-center gap-1 font-medium text-sm text-gray-700 hover:text-gray-900"
                  >
                    Amount
                    <ArrowUpDown className="w-3 h-3" />
                  </button>
                </th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Payment</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Status</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {filteredTransactions.map((transaction) => (
                <tr key={transaction.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <div className="text-sm">
                      <p className="font-medium">
                        {new Date(transaction.timestamp).toLocaleDateString()}
                      </p>
                      <p className="text-gray-500 text-xs">
                        {new Date(transaction.timestamp).toLocaleTimeString()}
                      </p>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm font-mono">
                    {transaction.receipt_number || `#${transaction.id.slice(-6)}`}
                  </td>
                  <td className="px-4 py-3">
                    <div className="text-sm">
                      <p className="font-medium">
                        {transaction.customer_name || 'Guest'}
                      </p>
                      {transaction.customer_email && (
                        <p className="text-gray-500 text-xs">{transaction.customer_email}</p>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm">
                    {transaction.items?.length || 0}
                  </td>
                  <td className="px-4 py-3">
                    <div className="text-sm">
                      <p className="font-medium">${transaction.total.toFixed(2)}</p>
                      {(transaction.refunded_amount ?? 0) > 0 && (
                        <p className="text-danger-600 text-xs">
                          -${(transaction.refunded_amount ?? 0).toFixed(2)}
                        </p>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-1 text-sm">
                      {getPaymentMethodIcon(transaction.payment_method)}
                      <span className="capitalize">{transaction.payment_method}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusBadge(transaction.status)}`}>
                      {transaction.status.replace('_', ' ')}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => setSelectedTransaction(transaction)}
                        className="p-1 hover:bg-gray-50 rounded"
                        title="View Details"
                      >
                        <Eye className="w-4 h-4 text-gray-600" />
                      </button>
                      <button
                        onClick={() => posService.printReceipt(transaction.id)}
                        className="p-1 hover:bg-gray-50 rounded"
                        title="Print Receipt"
                      >
                        <Receipt className="w-4 h-4 text-gray-600" />
                      </button>
                      {transaction.status === 'completed' &&
                       transaction.total > ((transaction.refunded_amount ?? 0) || 0) && (
                        <button
                          onClick={() => {
                            setSelectedTransaction(transaction);
                            setShowRefundModal(true);
                          }}
                          className="p-1 hover:bg-gray-50 rounded"
                          title="Refund"
                        >
                          <RefreshCw className="w-4 h-4 text-danger-600" />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Refund Modal */}
      {showRefundModal && selectedTransaction && (
        <RefundModal
          transaction={selectedTransaction}
          onClose={() => {
            setShowRefundModal(false);
            setSelectedTransaction(null);
          }}
          onRefund={processRefund}
        />
      )}

      {/* Transaction Details Modal */}
      {selectedTransaction && !showRefundModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="bg-white rounded-lg border border-gray-200 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-bold">Transaction Details</h2>
                <button
                  onClick={() => setSelectedTransaction(null)}
                  className="p-1 hover:bg-gray-50 rounded"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>
            <div className="p-6">
              <div className="grid grid-cols-2 gap-6 mb-6">
                <div>
                  <p className="text-sm text-gray-600">Receipt Number</p>
                  <p className="font-medium">{selectedTransaction.receipt_number}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Date & Time</p>
                  <p className="font-medium">
                    {new Date(selectedTransaction.timestamp).toLocaleString()}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Customer</p>
                  <p className="font-medium">
                    {selectedTransaction.customer_name || 'Guest'}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Cashier</p>
                  <p className="font-medium">
                    {selectedTransaction.cashier_name || selectedTransaction.cashier_id}
                  </p>
                </div>
              </div>

              <div className="border-t pt-4">
                <h3 className="font-medium mb-3">Items</h3>
                <div className="space-y-2">
                  {selectedTransaction.items?.map((item, index) => (
                    <div key={index} className="flex justify-between text-sm">
                      <span>{item.product?.name} × {item.quantity}</span>
                      <span>${((item.product?.price || 0) * item.quantity).toFixed(2)}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="border-t mt-4 pt-4 space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Subtotal</span>
                  <span>${selectedTransaction.subtotal.toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Tax</span>
                  <span>${selectedTransaction.tax.toFixed(2)}</span>
                </div>
                <div className="flex justify-between font-medium">
                  <span>Total</span>
                  <span>${selectedTransaction.total.toFixed(2)}</span>
                </div>
                {selectedTransaction.refunded_amount > 0 && (
                  <div className="flex justify-between text-sm text-danger-600">
                    <span>Refunded</span>
                    <span>-${selectedTransaction.refunded_amount.toFixed(2)}</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}