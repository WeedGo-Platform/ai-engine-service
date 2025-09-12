import React, { useState } from 'react';
import { FiCreditCard, FiLock, FiInfo } from 'react-icons/fi';
import { CheckoutSession, CompleteCheckoutRequest } from '../../services/checkout';

interface PaymentMethodProps {
  session: CheckoutSession;
  onComplete: (data: CompleteCheckoutRequest) => void;
  onBack: () => void;
  loading: boolean;
  theme: any;
}

const PaymentMethod: React.FC<PaymentMethodProps> = ({ session, onComplete, onBack, loading, theme }) => {
  const [paymentMethod, setPaymentMethod] = useState<'card' | 'cash'>('card');
  const [cardDetails, setCardDetails] = useState({
    cardNumber: '',
    cardName: '',
    expiryMonth: '',
    expiryYear: '',
    cvv: ''
  });
  const [saveCard, setSaveCard] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [tipAmount, setTipAmount] = useState(session.tip_amount || 0);
  const [customTip, setCustomTip] = useState(false);

  const tipOptions = [
    { label: '10%', value: session.subtotal * 0.10 },
    { label: '15%', value: session.subtotal * 0.15 },
    { label: '20%', value: session.subtotal * 0.20 },
    { label: 'Custom', value: 0 }
  ];

  const validateCard = () => {
    const newErrors: Record<string, string> = {};
    
    if (paymentMethod === 'card') {
      if (!cardDetails.cardNumber) {
        newErrors.cardNumber = 'Card number is required';
      } else if (cardDetails.cardNumber.replace(/\s/g, '').length < 13) {
        newErrors.cardNumber = 'Invalid card number';
      }
      
      if (!cardDetails.cardName) {
        newErrors.cardName = 'Cardholder name is required';
      }
      
      if (!cardDetails.expiryMonth || !cardDetails.expiryYear) {
        newErrors.expiry = 'Expiry date is required';
      }
      
      if (!cardDetails.cvv) {
        newErrors.cvv = 'CVV is required';
      } else if (cardDetails.cvv.length < 3) {
        newErrors.cvv = 'Invalid CVV';
      }
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const formatCardNumber = (value: string) => {
    const v = value.replace(/\s+/g, '').replace(/[^0-9]/gi, '');
    const matches = v.match(/\d{4,16}/g);
    const match = (matches && matches[0]) || '';
    const parts = [];

    for (let i = 0, len = match.length; i < len; i += 4) {
      parts.push(match.substring(i, i + 4));
    }

    if (parts.length) {
      return parts.join(' ');
    } else {
      return value;
    }
  };

  const handleCardNumberChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const formatted = formatCardNumber(e.target.value);
    if (formatted.replace(/\s/g, '').length <= 16) {
      setCardDetails({ ...cardDetails, cardNumber: formatted });
    }
  };

  const handleSubmit = () => {
    if (!validateCard()) return;
    
    const data: CompleteCheckoutRequest = {
      payment_method: paymentMethod,
      ...(paymentMethod === 'card' && {
        card_token: 'tok_' + Date.now(), // In production, this would come from Clover/payment provider
        save_payment_method: saveCard
      })
    };
    
    onComplete(data);
  };

  const calculateTotal = () => {
    return session.subtotal - session.discount_amount + session.tax_amount + 
           session.delivery_fee + session.service_fee + tipAmount;
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Payment Form */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-lg shadow">
            <div className="p-6 border-b">
              <h2 className="text-lg font-semibold text-gray-900">Payment Method</h2>
            </div>
            
            <div className="p-6">
              {/* Payment Type Selection */}
              <div className="grid grid-cols-2 gap-4 mb-6">
                <button
                  onClick={() => setPaymentMethod('card')}
                  className={`p-4 border-2 rounded-lg flex items-center space-x-3 transition-colors ${
                    paymentMethod === 'card' 
                      ? `border-blue-500 ${theme.secondary}` 
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <FiCreditCard className="w-5 h-5" />
                  <span className="font-medium">Credit/Debit Card</span>
                </button>
                
                <button
                  onClick={() => setPaymentMethod('cash')}
                  disabled={session.fulfillment_type !== 'pickup'}
                  className={`p-4 border-2 rounded-lg flex items-center space-x-3 transition-colors ${
                    paymentMethod === 'cash' 
                      ? `border-blue-500 ${theme.secondary}` 
                      : 'border-gray-200 hover:border-gray-300'
                  } ${session.fulfillment_type !== 'pickup' ? 'opacity-50 cursor-not-allowed' : ''}`}
                >
                  <span className="font-medium">Cash on Pickup</span>
                </button>
              </div>
              
              {session.fulfillment_type !== 'pickup' && (
                <p className="text-sm text-gray-500 mb-6">
                  Cash payment is only available for pickup orders
                </p>
              )}

              {/* Card Details Form */}
              {paymentMethod === 'card' && (
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Card Number
                    </label>
                    <div className="relative">
                      <input
                        type="text"
                        value={cardDetails.cardNumber}
                        onChange={handleCardNumberChange}
                        placeholder="1234 5678 9012 3456"
                        className={`w-full px-3 py-2 pr-10 border rounded-md focus:ring-blue-500 focus:border-blue-500 ${
                          errors.cardNumber ? 'border-red-300' : 'border-gray-300'
                        }`}
                      />
                      <FiCreditCard className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                    </div>
                    {errors.cardNumber && (
                      <p className="mt-1 text-sm text-red-600">{errors.cardNumber}</p>
                    )}
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Cardholder Name
                    </label>
                    <input
                      type="text"
                      value={cardDetails.cardName}
                      onChange={(e) => setCardDetails({ ...cardDetails, cardName: e.target.value })}
                      placeholder="John Doe"
                      className={`w-full px-3 py-2 border rounded-md focus:ring-blue-500 focus:border-blue-500 ${
                        errors.cardName ? 'border-red-300' : 'border-gray-300'
                      }`}
                    />
                    {errors.cardName && (
                      <p className="mt-1 text-sm text-red-600">{errors.cardName}</p>
                    )}
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Expiry Date
                      </label>
                      <div className="flex space-x-2">
                        <input
                          type="text"
                          value={cardDetails.expiryMonth}
                          onChange={(e) => {
                            const value = e.target.value.replace(/\D/g, '');
                            if (value.length <= 2 && parseInt(value) <= 12) {
                              setCardDetails({ ...cardDetails, expiryMonth: value });
                            }
                          }}
                          placeholder="MM"
                          maxLength={2}
                          className={`w-20 px-3 py-2 border rounded-md focus:ring-blue-500 focus:border-blue-500 ${
                            errors.expiry ? 'border-red-300' : 'border-gray-300'
                          }`}
                        />
                        <span className="self-center">/</span>
                        <input
                          type="text"
                          value={cardDetails.expiryYear}
                          onChange={(e) => {
                            const value = e.target.value.replace(/\D/g, '');
                            if (value.length <= 2) {
                              setCardDetails({ ...cardDetails, expiryYear: value });
                            }
                          }}
                          placeholder="YY"
                          maxLength={2}
                          className={`w-20 px-3 py-2 border rounded-md focus:ring-blue-500 focus:border-blue-500 ${
                            errors.expiry ? 'border-red-300' : 'border-gray-300'
                          }`}
                        />
                      </div>
                      {errors.expiry && (
                        <p className="mt-1 text-sm text-red-600">{errors.expiry}</p>
                      )}
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        CVV
                      </label>
                      <div className="relative">
                        <input
                          type="text"
                          value={cardDetails.cvv}
                          onChange={(e) => {
                            const value = e.target.value.replace(/\D/g, '');
                            if (value.length <= 4) {
                              setCardDetails({ ...cardDetails, cvv: value });
                            }
                          }}
                          placeholder="123"
                          maxLength={4}
                          className={`w-full px-3 py-2 pr-10 border rounded-md focus:ring-blue-500 focus:border-blue-500 ${
                            errors.cvv ? 'border-red-300' : 'border-gray-300'
                          }`}
                        />
                        <FiInfo className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                      </div>
                      {errors.cvv && (
                        <p className="mt-1 text-sm text-red-600">{errors.cvv}</p>
                      )}
                    </div>
                  </div>
                  
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={saveCard}
                      onChange={(e) => setSaveCard(e.target.checked)}
                      className="mr-2 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <span className="text-sm text-gray-700">
                      Save this card for future purchases
                    </span>
                  </label>
                </div>
              )}

              {/* Tip Section */}
              {session.fulfillment_type === 'delivery' && (
                <div className="mt-6 pt-6 border-t">
                  <h3 className="text-base font-medium text-gray-900 mb-3">Add a tip for your driver</h3>
                  <div className="grid grid-cols-4 gap-2">
                    {tipOptions.map((option, index) => (
                      <button
                        key={index}
                        onClick={() => {
                          if (option.label === 'Custom') {
                            setCustomTip(true);
                            setTipAmount(0);
                          } else {
                            setCustomTip(false);
                            setTipAmount(option.value);
                          }
                        }}
                        className={`py-2 px-3 rounded-md border-2 transition-colors ${
                          (!customTip && Math.abs(tipAmount - option.value) < 0.01) || 
                          (customTip && option.label === 'Custom')
                            ? `border-blue-500 ${theme.secondary}`
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
                      >
                        {option.label}
                      </button>
                    ))}
                  </div>
                  
                  {customTip && (
                    <div className="mt-3">
                      <div className="relative">
                        <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500">$</span>
                        <input
                          type="number"
                          value={tipAmount}
                          onChange={(e) => setTipAmount(parseFloat(e.target.value) || 0)}
                          min="0"
                          step="0.01"
                          className="w-full pl-8 pr-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                        />
                      </div>
                    </div>
                  )}
                  
                  {tipAmount > 0 && (
                    <p className="mt-2 text-sm text-gray-600">
                      Tip amount: ${tipAmount.toFixed(2)}
                    </p>
                  )}
                </div>
              )}

              {/* Security Notice */}
              <div className="mt-6 p-4 bg-gray-50 rounded-lg flex items-start space-x-3">
                <FiLock className="w-5 h-5 text-gray-400 mt-0.5" />
                <div className="flex-1">
                  <p className="text-sm text-gray-600">
                    Your payment information is encrypted and secure. We never store your card details.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Order Summary */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg shadow sticky top-4">
            <div className="p-6 border-b">
              <h2 className="text-lg font-semibold text-gray-900">Order Summary</h2>
            </div>
            
            <div className="p-6 space-y-4">
              {/* Price Breakdown */}
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Subtotal</span>
                  <span className="font-medium">${session.subtotal.toFixed(2)}</span>
                </div>
                
                {session.discount_amount > 0 && (
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Discount</span>
                    <span className="font-medium text-green-600">-${session.discount_amount.toFixed(2)}</span>
                  </div>
                )}
                
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Tax</span>
                  <span className="font-medium">${session.tax_amount.toFixed(2)}</span>
                </div>
                
                {session.delivery_fee > 0 && (
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Delivery Fee</span>
                    <span className="font-medium">${session.delivery_fee.toFixed(2)}</span>
                  </div>
                )}
                
                {session.service_fee > 0 && (
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Service Fee</span>
                    <span className="font-medium">${session.service_fee.toFixed(2)}</span>
                  </div>
                )}
                
                {tipAmount > 0 && (
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Tip</span>
                    <span className="font-medium">${tipAmount.toFixed(2)}</span>
                  </div>
                )}
                
                <div className="flex justify-between text-lg font-semibold pt-2 border-t">
                  <span>Total</span>
                  <span>${calculateTotal().toFixed(2)}</span>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="space-y-3 pt-4">
                <button
                  onClick={handleSubmit}
                  disabled={loading}
                  className={`w-full py-3 text-white font-medium rounded-md transition-colors disabled:opacity-50 ${theme.primary}`}
                >
                  {loading ? (
                    <span className="flex items-center justify-center">
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                      Processing...
                    </span>
                  ) : (
                    `Place Order • $${calculateTotal().toFixed(2)}`
                  )}
                </button>
                
                <button
                  onClick={onBack}
                  disabled={loading}
                  className="w-full py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors disabled:opacity-50"
                >
                  Back to Delivery
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PaymentMethod;