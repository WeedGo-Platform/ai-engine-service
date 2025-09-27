import { getApiUrl } from '../../config/app.config';
import React, { useState } from 'react';
import { getApiUrl } from '../../config/app.config';
import { ChevronLeft, ShoppingBag, Loader2, AlertCircle, User, Mail, Phone } from 'lucide-react';
import { useKiosk } from '../../contexts/KioskContext';
import { useKioskSession } from '../../hooks/useKioskSession';

interface CheckoutProps {
  onBack: () => void;
  onComplete: (orderId: string) => void;
  currentStore: any;
}

export default function Checkout({ onBack, onComplete, currentStore }: CheckoutProps) {
  const {
    cart,
    cartTotal,
    customer,
    clearCart
  } = useKiosk();
  const { session } = useKioskSession();

  // Customer info form state - pre-fill if logged in
  const [customerName, setCustomerName] = useState(
    customer ? `${customer.firstName || ''} ${customer.lastName || ''}`.trim() : ''
  );
  const [customerEmail, setCustomerEmail] = useState(customer?.email || '');
  const [customerPhone, setCustomerPhone] = useState(customer?.phone || '');

  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState('');

  const taxRate = 0.13;
  const subtotal = cartTotal;
  const tax = subtotal * taxRate;
  const total = subtotal + tax;

  const handlePlaceOrder = async () => {
    setIsProcessing(true);
    setError('');

    // Debug logging
    console.log('Current store at order time:', currentStore);
    console.log('Store ID:', currentStore?.id);

    try {
      // Prepare customer info - follow POS pattern for anonymous orders
      const customerInfo = {
        customer_id: customer?.id || 'anonymous',
        customer_name: customerName || 'Walk-in Customer',
        customer_email: customerEmail || null,
        customer_phone: customerPhone || null
      };

      const requestBody = {
        session_id: session?.session_id,
        store_id: currentStore?.id,
        cart_items: cart.map(item => ({
          product_id: item.id.split('-')[0],  // Remove timestamp suffix from product ID
          name: item.name,
          price: item.price,
          quantity: item.quantity
        })),
        payment_method: 'pay_at_pickup',
        customer_info: customerInfo
      };

      console.log('Request body being sent:', requestBody);

      // Create order with pay at pickup
      const response = await fetch(getApiUrl('/api/kiosk/order/create'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
      });

      if (response.ok) {
        const data = await response.json();
        // No payment processing delay - seamless submission
        clearCart();
        onComplete(data.order_id);
      } else {
        throw new Error('Failed to create order');
      }
    } catch (err) {
      console.error('Checkout error:', err);
      setError('Failed to process order. Please try again.');
      setIsProcessing(false);
    }
  };

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm px-6 py-4">
        <div className="flex items-center gap-4">
          <button
            onClick={onBack}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            disabled={isProcessing}
          >
            <ChevronLeft className="w-6 h-6" />
          </button>
          <h1 className="text-2xl font-bold text-gray-800">Complete Your Order</h1>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-2xl mx-auto space-y-6">

          {/* Order Summary */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold mb-4">Order Summary</h3>

            {/* Items */}
            <div className="space-y-3 mb-4">
              {cart.map(item => (
                <div key={item.id} className="flex justify-between text-sm">
                  <div className="flex-1">
                    <span>{item.name}</span>
                    <span className="text-gray-500 ml-2">x{item.quantity}</span>
                  </div>
                  <span className="font-medium">
                    ${(item.price * item.quantity).toFixed(2)}
                  </span>
                </div>
              ))}
            </div>

            {/* Totals */}
            <div className="border-t pt-4 space-y-2">
              <div className="flex justify-between text-gray-600">
                <span>Subtotal</span>
                <span>${subtotal.toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-gray-600">
                <span>Tax (HST 13%)</span>
                <span>${tax.toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-xl font-bold pt-2 border-t">
                <span>Total</span>
                <span className="text-primary-600">${total.toFixed(2)}</span>
              </div>
            </div>
          </div>

          {/* Optional Customer Info */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold mb-2">Contact Information</h3>
            <p className="text-sm text-gray-500 mb-4">Optional - Help us notify you when your order is ready</p>

            <div className="space-y-4">
              {/* Name Field */}
              <div>
                <label className="flex items-center text-sm font-medium text-gray-700 mb-1">
                  <User className="w-4 h-4 mr-2" />
                  Name
                </label>
                <input
                  type="text"
                  value={customerName}
                  onChange={(e) => setCustomerName(e.target.value)}
                  placeholder="Enter your name (optional)"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-primary-500"
                  disabled={isProcessing}
                />
              </div>

              {/* Email Field */}
              <div>
                <label className="flex items-center text-sm font-medium text-gray-700 mb-1">
                  <Mail className="w-4 h-4 mr-2" />
                  Email
                </label>
                <input
                  type="email"
                  value={customerEmail}
                  onChange={(e) => setCustomerEmail(e.target.value)}
                  placeholder="Enter your email (optional)"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-primary-500"
                  disabled={isProcessing}
                />
              </div>

              {/* Phone Field */}
              <div>
                <label className="flex items-center text-sm font-medium text-gray-700 mb-1">
                  <Phone className="w-4 h-4 mr-2" />
                  Phone
                </label>
                <input
                  type="tel"
                  value={customerPhone}
                  onChange={(e) => setCustomerPhone(e.target.value)}
                  placeholder="Enter your phone number (optional)"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-primary-500"
                  disabled={isProcessing}
                />
              </div>
            </div>
          </div>

          {/* Pickup Info & Payment Notice */}
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <h4 className="font-semibold text-green-800 mb-2">
              <ShoppingBag className="inline w-5 h-5 mr-2" />
              Pay at Pickup
            </h4>
            <p className="text-sm text-green-700">
              Your order will be ready for immediate pickup. Payment will be collected at:
            </p>
            {currentStore && (
              <>
                <p className="text-sm font-medium text-green-800 mt-2">
                  {currentStore.name}
                </p>
                <p className="text-sm text-green-600">
                  {typeof currentStore.address === 'string'
                    ? `${currentStore.address}, ${currentStore.city}`
                    : currentStore.address?.street
                      ? `${currentStore.address.street}, ${currentStore.address.city}, ${currentStore.address.province}`
                      : `${currentStore.city || ''}`
                  }
                </p>
              </>
            )}
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <p className="text-red-800">{error}</p>
            </div>
          )}
        </div>
      </div>

      {/* Footer - Single Action Button */}
      <div className="bg-white border-t px-6 py-4">
        <div className="max-w-2xl mx-auto">
          <button
            onClick={handlePlaceOrder}
            disabled={isProcessing || cart.length === 0}
            className="w-full py-4 bg-primary-600 text-white rounded-lg font-semibold text-lg hover:bg-primary-700 transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {isProcessing ? (
              <>
                <Loader2 className="w-6 h-6 animate-spin" />
                Placing Order...
              </>
            ) : (
              <>
                <ShoppingBag className="w-6 h-6" />
                Place Order - Pay ${total.toFixed(2)} at Pickup
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}