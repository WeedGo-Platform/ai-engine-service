import { useState, useEffect } from 'react';
import {
  X, CreditCard, DollarSign, Smartphone, Calculator,
  CheckCircle, AlertCircle, Printer, Mail
} from 'lucide-react';

interface PaymentModalProps {
  isOpen: boolean;
  onClose: () => void;
  total: number;
  onComplete: (payment: PaymentDetails) => void;
}

interface PaymentDetails {
  method: 'cash' | 'card' | 'debit' | 'split';
  cashAmount?: number;
  cardAmount?: number;
  changeGiven?: number;
  cardLastFour?: string;
  authorizationCode?: string;
  printReceipt: boolean;
  emailReceipt?: string;
}

const CASH_DENOMINATIONS = [
  { value: 100, label: '$100' },
  { value: 50, label: '$50' },
  { value: 20, label: '$20' },
  { value: 10, label: '$10' },
  { value: 5, label: '$5' },
];

const QUICK_AMOUNTS = [20, 40, 60, 80, 100, 200];

export default function PaymentModal({ isOpen, onClose, total, onComplete }: PaymentModalProps) {
  const [paymentMethod, setPaymentMethod] = useState<'cash' | 'card' | 'debit' | 'split'>('cash');
  const [cashAmount, setCashAmount] = useState<string>('');
  const [cardAmount, setCardAmount] = useState<string>('');
  const [change, setChange] = useState<number>(0);
  const [processing, setProcessing] = useState(false);
  const [printReceipt, setPrintReceipt] = useState(true);
  const [emailReceipt, setEmailReceipt] = useState('');
  const [showEmailInput, setShowEmailInput] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (paymentMethod === 'cash' && cashAmount) {
      const cash = parseFloat(cashAmount);
      if (!isNaN(cash)) {
        setChange(Math.max(0, cash - total));
      }
    } else if (paymentMethod === 'split' && cashAmount && cardAmount) {
      const cash = parseFloat(cashAmount) || 0;
      const card = parseFloat(cardAmount) || 0;
      setChange(Math.max(0, (cash + card) - total));
    } else {
      setChange(0);
    }
  }, [cashAmount, cardAmount, total, paymentMethod]);

  const handleQuickCash = (amount: number) => {
    setCashAmount(amount.toString());
  };

  const handleCashDenomination = (value: number) => {
    const current = parseFloat(cashAmount) || 0;
    setCashAmount((current + value).toString());
  };

  const calculateChange = () => {
    const cash = parseFloat(cashAmount) || 0;
    return Math.max(0, cash - total);
  };

  const processPayment = async () => {
    setProcessing(true);
    setError(null);

    try {
      // Validate payment amount
      if (paymentMethod === 'cash') {
        const cash = parseFloat(cashAmount);
        if (isNaN(cash) || cash < total) {
          throw new Error('Insufficient cash amount');
        }
      } else if (paymentMethod === 'split') {
        const cash = parseFloat(cashAmount) || 0;
        const card = parseFloat(cardAmount) || 0;
        if (cash + card < total) {
          throw new Error('Insufficient payment amount');
        }
      }

      // Simulate payment processing
      await new Promise(resolve => setTimeout(resolve, 1500));

      const payment: PaymentDetails = {
        method: paymentMethod,
        printReceipt,
        emailReceipt: showEmailInput ? emailReceipt : undefined
      };

      if (paymentMethod === 'cash') {
        payment.cashAmount = parseFloat(cashAmount);
        payment.changeGiven = change;
      } else if (paymentMethod === 'card' || paymentMethod === 'debit') {
        payment.cardAmount = total;
        payment.cardLastFour = '****';
        payment.authorizationCode = Math.random().toString(36).substring(7).toUpperCase();
      } else if (paymentMethod === 'split') {
        payment.cashAmount = parseFloat(cashAmount);
        payment.cardAmount = parseFloat(cardAmount);
        payment.changeGiven = change;
        payment.cardLastFour = '****';
        payment.authorizationCode = Math.random().toString(36).substring(7).toUpperCase();
      }

      onComplete(payment);
      onClose();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setProcessing(false);
    }
  };

  const canProcess = () => {
    if (paymentMethod === 'cash') {
      const cash = parseFloat(cashAmount);
      return !isNaN(cash) && cash >= total;
    } else if (paymentMethod === 'split') {
      const cash = parseFloat(cashAmount) || 0;
      const card = parseFloat(cardAmount) || 0;
      return cash + card >= total;
    }
    return true; // Card and debit can always process
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black dark:bg-black bg-opacity-50 dark:bg-opacity-70 flex items-center justify-center z-50 transition-colors duration-200">
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 w-full max-w-3xl">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Process Payment</h2>
          <button
            onClick={onClose}
            className="text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {/* Total Amount */}
          <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-6 mb-6 transition-colors duration-200">
            <div className="text-center">
              <p className="text-sm text-gray-600 dark:text-gray-300 mb-1">Total Amount Due</p>
              <p className="text-4xl font-bold text-gray-900 dark:text-white">${total.toFixed(2)}</p>
            </div>
          </div>

          {/* Payment Method Selection */}
          <div className="mb-6">
            <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">Payment Method</p>
            <div className="grid grid-cols-4 gap-4">
              <button
                onClick={() => setPaymentMethod('cash')}
                className={`p-4 rounded-lg border-2 transition-colors ${
                  paymentMethod === 'cash'
                    ? 'border-primary-500 dark:border-primary-400 bg-primary-50 dark:bg-primary-900/30'
                    : 'border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500'
                }`}
              >
                <DollarSign className="w-6 h-6 mx-auto mb-1" />
                <p className="text-sm font-medium text-gray-900 dark:text-white">Cash</p>
              </button>
              <button
                onClick={() => setPaymentMethod('card')}
                className={`p-4 rounded-lg border-2 transition-colors ${
                  paymentMethod === 'card'
                    ? 'border-primary-500 dark:border-primary-400 bg-primary-50 dark:bg-primary-900/30'
                    : 'border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500'
                }`}
              >
                <CreditCard className="w-6 h-6 mx-auto mb-1" />
                <p className="text-sm font-medium text-gray-900 dark:text-white">Credit</p>
              </button>
              <button
                onClick={() => setPaymentMethod('debit')}
                className={`p-4 rounded-lg border-2 transition-colors ${
                  paymentMethod === 'debit'
                    ? 'border-primary-500 dark:border-primary-400 bg-primary-50 dark:bg-primary-900/30'
                    : 'border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500'
                }`}
              >
                <Smartphone className="w-6 h-6 mx-auto mb-1" />
                <p className="text-sm font-medium text-gray-900 dark:text-white">Debit</p>
              </button>
              <button
                onClick={() => setPaymentMethod('split')}
                className={`p-4 rounded-lg border-2 transition-colors ${
                  paymentMethod === 'split'
                    ? 'border-primary-500 dark:border-primary-400 bg-primary-50 dark:bg-primary-900/30'
                    : 'border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500'
                }`}
              >
                <Calculator className="w-6 h-6 mx-auto mb-1" />
                <p className="text-sm font-medium text-gray-900 dark:text-white">Split</p>
              </button>
            </div>
          </div>

          {/* Cash Payment */}
          {paymentMethod === 'cash' && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Cash Received
                </label>
                <input
                  type="number"
                  value={cashAmount}
                  onChange={(e) => setCashAmount(e.target.value)}
                  className="w-full px-4 py-3 text-2xl font-bold border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 dark:focus:ring-primary-400 transition-colors"
                  placeholder="0.00"
                  step="0.01"
                />
              </div>

              {/* Quick Cash Buttons */}
              <div>
                <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Quick Amount</p>
                <div className="grid grid-cols-6 gap-2">
                  {QUICK_AMOUNTS.map(amount => (
                    <button
                      key={amount}
                      onClick={() => handleQuickCash(amount)}
                      className="px-3 py-2 bg-gray-50 dark:bg-gray-600 hover:bg-gray-100 dark:hover:bg-gray-500 rounded text-sm font-medium text-gray-900 dark:text-white transition-colors"
                    >
                      ${amount}
                    </button>
                  ))}
                </div>
              </div>

              {/* Cash Denominations */}
              <div>
                <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Add Bills</p>
                <div className="flex gap-2">
                  {CASH_DENOMINATIONS.map(denom => (
                    <button
                      key={denom.value}
                      onClick={() => handleCashDenomination(denom.value)}
                      className="flex-1 px-3 py-2 bg-primary-100 dark:bg-primary-900/30 hover:bg-green-200 dark:hover:bg-primary-800/40 rounded text-sm font-medium text-gray-900 dark:text-white transition-colors"
                    >
                      {denom.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Change Display */}
              {change > 0 && (
                <div className="bg-warning-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-700 rounded-lg p-6 transition-colors">
                  <div className="flex items-center justify-between">
                    <span className="text-lg font-medium text-gray-900 dark:text-white">Change Due:</span>
                    <span className="text-2xl font-bold text-yellow-700 dark:text-yellow-400">
                      ${change.toFixed(2)}
                    </span>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Card/Debit Payment */}
          {(paymentMethod === 'card' || paymentMethod === 'debit') && (
            <div className="text-center py-8">
              <CreditCard className="w-16 h-16 mx-auto mb-4 text-gray-400 dark:text-gray-500" />
              <p className="text-lg font-medium mb-2 text-gray-900 dark:text-white">Insert or Tap Card</p>
              <p className="text-sm text-gray-600 dark:text-gray-300">
                Waiting for {paymentMethod === 'card' ? 'credit' : 'debit'} card...
              </p>
              <p className="text-2xl font-bold mt-4">${total.toFixed(2)}</p>
            </div>
          )}

          {/* Split Payment */}
          {paymentMethod === 'split' && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Cash Amount
                  </label>
                  <input
                    type="number"
                    value={cashAmount}
                    onChange={(e) => setCashAmount(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white transition-colors"
                    placeholder="0.00"
                    step="0.01"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Card Amount
                  </label>
                  <input
                    type="number"
                    value={cardAmount}
                    onChange={(e) => setCardAmount(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white transition-colors"
                    placeholder="0.00"
                    step="0.01"
                  />
                </div>
              </div>
              
              <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 transition-colors">
                <div className="flex justify-between text-sm text-gray-900 dark:text-white">
                  <span>Cash:</span>
                  <span>${parseFloat(cashAmount) || 0}</span>
                </div>
                <div className="flex justify-between text-sm text-gray-900 dark:text-white">
                  <span>Card:</span>
                  <span>${parseFloat(cardAmount) || 0}</span>
                </div>
                <div className="flex justify-between font-bold pt-2 border-t border-gray-200 dark:border-gray-600 mt-2 text-gray-900 dark:text-white">
                  <span>Total:</span>
                  <span>${((parseFloat(cashAmount) || 0) + (parseFloat(cardAmount) || 0)).toFixed(2)}</span>
                </div>
                {change > 0 && (
                  <div className="flex justify-between text-sm text-warning-600 dark:text-yellow-400 mt-2">
                    <span>Change:</span>
                    <span>${change.toFixed(2)}</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Receipt Options */}
          <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
            <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">Receipt Options</p>
            <div className="space-y-2">
              <label className="flex items-center gap-2 text-gray-900 dark:text-white">
                <input
                  type="checkbox"
                  checked={printReceipt}
                  onChange={(e) => setPrintReceipt(e.target.checked)}
                  className="rounded"
                />
                <Printer className="w-4 h-4" />
                <span className="text-sm">Print Receipt</span>
              </label>
              <label className="flex items-center gap-2 text-gray-900 dark:text-white">
                <input
                  type="checkbox"
                  checked={showEmailInput}
                  onChange={(e) => setShowEmailInput(e.target.checked)}
                  className="rounded"
                />
                <Mail className="w-4 h-4" />
                <span className="text-sm">Email Receipt</span>
              </label>
              {showEmailInput && (
                <input
                  type="email"
                  value={emailReceipt}
                  onChange={(e) => setEmailReceipt(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm transition-colors"
                  placeholder="customer@email.com"
                />
              )}
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mt-4 p-4 bg-danger-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-center gap-2 transition-colors">
              <AlertCircle className="w-5 h-5 text-red-500 dark:text-red-400" />
              <span className="text-sm text-red-700 dark:text-red-400">{error}</span>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700 transition-colors">
          <button
            onClick={onClose}
            className="px-6 py-2 text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={processPayment}
            disabled={processing || !canProcess()}
            className="px-6 py-3 bg-primary-500 dark:bg-primary-600 text-white rounded-lg hover:bg-primary-600 dark:hover:bg-primary-700 disabled:bg-gray-300 dark:disabled:bg-gray-600 disabled:cursor-not-allowed flex items-center gap-2 transition-colors"
          >
            {processing ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white" />
                Processing...
              </>
            ) : (
              <>
                <CheckCircle className="w-5 h-5" />
                Complete Payment
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}