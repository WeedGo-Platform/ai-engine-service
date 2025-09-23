import React, { useState, useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { RootState } from '@store/index';
import { clearCart } from '@features/cart/cartSlice';
import { ordersApi, CreateOrderRequest } from '@api/orders';
import toast from 'react-hot-toast';
import {
  MapPinIcon,
  TruckIcon,
  CreditCardIcon,
  ClockIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline';

const Checkout: React.FC = () => {
  const navigate = useNavigate();
  const dispatch = useDispatch();

  const { items } = useSelector((state: RootState) => state.cart);
  const { selectedStore } = useSelector((state: RootState) => state.store || {});
  const { user, isAuthenticated } = useSelector((state: RootState) => state.auth);

  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState(1); // 1: Delivery, 2: Payment, 3: Review
  const [deliveryType, setDeliveryType] = useState<'delivery' | 'pickup'>('delivery');

  // Delivery Information
  const [deliveryInfo, setDeliveryInfo] = useState({
    address: '',
    city: '',
    province: 'Ontario',
    postal_code: '',
    unit: '',
    instructions: '',
    scheduled_time: ''
  });

  // Customer Information
  const [customerInfo, setCustomerInfo] = useState({
    name: '',
    email: '',
    phone: ''
  });

  // Payment Information
  const [paymentInfo, setPaymentInfo] = useState({
    cardNumber: '',
    expiryDate: '',
    cvv: '',
    cardName: ''
  });

  const TAX_RATE = 0.13;
  const DELIVERY_FEE = 5.99;
  const FREE_DELIVERY_THRESHOLD = 50;

  const subtotal = items.reduce((sum, item) => sum + (item.price * item.quantity), 0);
  const tax = subtotal * TAX_RATE;
  const deliveryFee = deliveryType === 'pickup' ? 0 : (subtotal >= FREE_DELIVERY_THRESHOLD ? 0 : DELIVERY_FEE);
  const total = subtotal + tax + deliveryFee;

  useEffect(() => {
    // Pre-fill customer info if user is logged in
    if (user) {
      setCustomerInfo({
        name: `${user.first_name || ''} ${user.last_name || ''}`.trim(),
        email: user.email || '',
        phone: user.phone || ''
      });
    }

    // Redirect if cart is empty
    if (items.length === 0) {
      navigate('/cart');
    }

    // Check if user is authenticated
    if (!isAuthenticated) {
      navigate('/login?redirect=/checkout');
    }
  }, [user, items, isAuthenticated, navigate]);

  const validateDeliveryInfo = (): boolean => {
    if (deliveryType === 'delivery') {
      if (!deliveryInfo.address || !deliveryInfo.city || !deliveryInfo.postal_code) {
        toast.error('Please fill in all delivery fields');
        return false;
      }

      // Validate Canadian postal code
      const postalCodeRegex = /^[A-Z]\d[A-Z]\s?\d[A-Z]\d$/i;
      if (!postalCodeRegex.test(deliveryInfo.postal_code)) {
        toast.error('Please enter a valid Canadian postal code');
        return false;
      }
    }

    if (!customerInfo.name || !customerInfo.email || !customerInfo.phone) {
      toast.error('Please fill in all customer information');
      return false;
    }

    // Validate email
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(customerInfo.email)) {
      toast.error('Please enter a valid email address');
      return false;
    }

    // Validate phone (Canadian format)
    const phoneRegex = /^\d{10}$/;
    const cleanPhone = customerInfo.phone.replace(/\D/g, '');
    if (!phoneRegex.test(cleanPhone)) {
      toast.error('Please enter a valid 10-digit phone number');
      return false;
    }

    return true;
  };

  const validatePaymentInfo = (): boolean => {
    if (!paymentInfo.cardNumber || !paymentInfo.expiryDate || !paymentInfo.cvv || !paymentInfo.cardName) {
      toast.error('Please fill in all payment fields');
      return false;
    }

    // Enhanced card number validation
    const cleanCardNumber = paymentInfo.cardNumber.replace(/\s/g, '');
    if (!/^\d{13,19}$/.test(cleanCardNumber)) {
      toast.error('Please enter a valid card number');
      return false;
    }

    // Luhn algorithm validation
    if (!validateLuhn(cleanCardNumber)) {
      toast.error('Please enter a valid card number');
      return false;
    }

    // Expiry date validation (MM/YY)
    const expiryRegex = /^(0[1-9]|1[0-2])\/\d{2}$/;
    if (!expiryRegex.test(paymentInfo.expiryDate)) {
      toast.error('Please enter expiry date in MM/YY format');
      return false;
    }

    // Check if card is expired
    const [month, year] = paymentInfo.expiryDate.split('/');
    const expiry = new Date(2000 + parseInt(year), parseInt(month) - 1);
    const now = new Date();
    if (expiry < now) {
      toast.error('Card has expired');
      return false;
    }

    // CVV validation (3 or 4 digits)
    if (!/^\d{3,4}$/.test(paymentInfo.cvv)) {
      toast.error('Please enter a valid CVV (3 or 4 digits)');
      return false;
    }

    // Cardholder name validation
    if (paymentInfo.cardName.trim().length < 2) {
      toast.error('Please enter a valid cardholder name');
      return false;
    }

    return true;
  };

  // Luhn algorithm for credit card validation
  const validateLuhn = (cardNumber: string): boolean => {
    let sum = 0;
    let isEven = false;

    for (let i = cardNumber.length - 1; i >= 0; i--) {
      let digit = parseInt(cardNumber[i]);

      if (isEven) {
        digit *= 2;
        if (digit > 9) {
          digit -= 9;
        }
      }

      sum += digit;
      isEven = !isEven;
    }

    return sum % 10 === 0;
  };

  const handleNextStep = () => {
    if (step === 1) {
      if (validateDeliveryInfo()) {
        setStep(2);
      }
    } else if (step === 2) {
      if (validatePaymentInfo()) {
        setStep(3);
      }
    }
  };

  const handlePreviousStep = () => {
    setStep(step - 1);
  };

  const handlePlaceOrder = async () => {
    if (!selectedStore) {
      toast.error('Please select a store');
      return;
    }

    setLoading(true);

    try {
      // Prepare order request
      const orderRequest: CreateOrderRequest = {
        store_id: selectedStore.id,
        items: items.map(item => ({
          product_id: item.id,
          quantity: item.quantity
        })),
        delivery_info: {
          type: deliveryType,
          ...(deliveryType === 'delivery' && {
            address: deliveryInfo.address,
            city: deliveryInfo.city,
            province: deliveryInfo.province,
            postal_code: deliveryInfo.postal_code,
            delivery_instructions: deliveryInfo.instructions
          }),
          scheduled_time: deliveryInfo.scheduled_time || undefined
        },
        customer_info: customerInfo,
        payment_method: 'credit_card'
      };

      // Create order
      const order = await ordersApi.create(orderRequest);

      // Clear cart after successful order
      dispatch(clearCart());

      // Success! Navigate to order confirmation
      toast.success('Order placed successfully!');
      navigate(`/order-confirmation/${order.order_number}`);

    } catch (error: any) {
      console.error('Order creation failed:', error);
      toast.error(error.response?.data?.detail || 'Failed to place order. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const formatCardNumber = (value: string) => {
    const v = value.replace(/\s+/g, '').replace(/[^0-9]/gi, '');
    const matches = v.match(/\d{4,16}/g);
    const match = (matches && matches[0]) || '';
    const parts = [];

    for (let i = 0, len = match.length; i < len; i += 4) {
      parts.push(match.substring(i, i + 4));
    }

    return parts.length ? parts.join(' ') : value;
  };

  return (
    <div className="container-max py-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Checkout</h1>

      {/* Progress Steps */}
      <div className="flex items-center justify-center mb-8">
        {[1, 2, 3].map((i) => (
          <React.Fragment key={i}>
            <div className="flex items-center">
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center ${
                  step >= i
                    ? 'bg-green-600 text-white'
                    : 'bg-gray-200 text-gray-500'
                }`}
              >
                {step > i ? <CheckCircleIcon className="w-6 h-6" /> : i}
              </div>
              <span className={`ml-2 ${step >= i ? 'text-gray-900' : 'text-gray-500'}`}>
                {i === 1 ? 'Delivery' : i === 2 ? 'Payment' : 'Review'}
              </span>
            </div>
            {i < 3 && (
              <div
                className={`w-24 h-1 mx-4 ${
                  step > i ? 'bg-green-600' : 'bg-gray-200'
                }`}
              />
            )}
          </React.Fragment>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Content */}
        <div className="lg:col-span-2">
          {/* Step 1: Delivery Information */}
          {step === 1 && (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-6">Delivery Information</h2>

              {/* Delivery Type Selection */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  How would you like to receive your order?
                </label>
                <div className="grid grid-cols-2 gap-4">
                  <button
                    onClick={() => setDeliveryType('delivery')}
                    className={`p-4 border rounded-lg flex flex-col items-center ${
                      deliveryType === 'delivery'
                        ? 'border-green-600 bg-green-50'
                        : 'border-gray-300'
                    }`}
                  >
                    <TruckIcon className="w-8 h-8 mb-2 text-green-600" />
                    <span className="font-medium">Delivery</span>
                    <span className="text-sm text-gray-500">
                      {subtotal >= FREE_DELIVERY_THRESHOLD ? 'Free' : `$${DELIVERY_FEE}`}
                    </span>
                  </button>
                  <button
                    onClick={() => setDeliveryType('pickup')}
                    className={`p-4 border rounded-lg flex flex-col items-center ${
                      deliveryType === 'pickup'
                        ? 'border-green-600 bg-green-50'
                        : 'border-gray-300'
                    }`}
                  >
                    <MapPinIcon className="w-8 h-8 mb-2 text-green-600" />
                    <span className="font-medium">Pickup</span>
                    <span className="text-sm text-gray-500">Free</span>
                  </button>
                </div>
              </div>

              {/* Delivery Address */}
              {deliveryType === 'delivery' && (
                <div className="space-y-4 mb-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="md:col-span-2">
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Street Address *
                      </label>
                      <input
                        type="text"
                        value={deliveryInfo.address}
                        onChange={(e) => setDeliveryInfo({...deliveryInfo, address: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                        placeholder="123 Main Street"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Unit/Apt (optional)
                      </label>
                      <input
                        type="text"
                        value={deliveryInfo.unit}
                        onChange={(e) => setDeliveryInfo({...deliveryInfo, unit: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                        placeholder="Apt 4B"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        City *
                      </label>
                      <input
                        type="text"
                        value={deliveryInfo.city}
                        onChange={(e) => setDeliveryInfo({...deliveryInfo, city: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                        placeholder="Toronto"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Province *
                      </label>
                      <select
                        value={deliveryInfo.province}
                        onChange={(e) => setDeliveryInfo({...deliveryInfo, province: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                      >
                        <option value="Ontario">Ontario</option>
                        <option value="Quebec">Quebec</option>
                        <option value="British Columbia">British Columbia</option>
                        <option value="Alberta">Alberta</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Postal Code *
                      </label>
                      <input
                        type="text"
                        value={deliveryInfo.postal_code}
                        onChange={(e) => setDeliveryInfo({...deliveryInfo, postal_code: e.target.value.toUpperCase()})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                        placeholder="M5H 2N2"
                        maxLength={7}
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Delivery Instructions (optional)
                    </label>
                    <textarea
                      value={deliveryInfo.instructions}
                      onChange={(e) => setDeliveryInfo({...deliveryInfo, instructions: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                      rows={3}
                      placeholder="Ring doorbell, leave at door, etc."
                    />
                  </div>
                </div>
              )}

              {/* Customer Information */}
              <div className="space-y-4">
                <h3 className="font-medium text-gray-900 mb-3">Contact Information</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Full Name *
                    </label>
                    <input
                      type="text"
                      value={customerInfo.name}
                      onChange={(e) => setCustomerInfo({...customerInfo, name: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                      placeholder="John Doe"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Email *
                    </label>
                    <input
                      type="email"
                      value={customerInfo.email}
                      onChange={(e) => setCustomerInfo({...customerInfo, email: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                      placeholder="john@example.com"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Phone Number *
                    </label>
                    <input
                      type="tel"
                      value={customerInfo.phone}
                      onChange={(e) => setCustomerInfo({...customerInfo, phone: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                      placeholder="(416) 555-0123"
                    />
                  </div>
                </div>
              </div>

              <button
                onClick={handleNextStep}
                className="w-full mt-6 bg-green-600 text-white py-3 rounded-lg font-semibold hover:bg-green-700 transition-colors"
              >
                Continue to Payment
              </button>
            </div>
          )}

          {/* Step 2: Payment Information */}
          {step === 2 && (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-6">Payment Information</h2>


              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Card Number *
                  </label>
                  <input
                    type="text"
                    value={paymentInfo.cardNumber}
                    onChange={(e) => setPaymentInfo({...paymentInfo, cardNumber: formatCardNumber(e.target.value)})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                    placeholder="4242 4242 4242 4242"
                    maxLength={19}
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Expiry Date *
                    </label>
                    <input
                      type="text"
                      value={paymentInfo.expiryDate}
                      onChange={(e) => {
                        let value = e.target.value.replace(/\D/g, '');
                        if (value.length >= 2) {
                          value = value.slice(0, 2) + '/' + value.slice(2, 4);
                        }
                        setPaymentInfo({...paymentInfo, expiryDate: value});
                      }}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                      placeholder="MM/YY"
                      maxLength={5}
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      CVV *
                    </label>
                    <input
                      type="text"
                      value={paymentInfo.cvv}
                      onChange={(e) => setPaymentInfo({...paymentInfo, cvv: e.target.value.replace(/\D/g, '')})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                      placeholder="123"
                      maxLength={3}
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Cardholder Name *
                  </label>
                  <input
                    type="text"
                    value={paymentInfo.cardName}
                    onChange={(e) => setPaymentInfo({...paymentInfo, cardName: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                    placeholder="John Doe"
                  />
                </div>
              </div>

              <div className="flex gap-4 mt-6">
                <button
                  onClick={handlePreviousStep}
                  className="flex-1 px-6 py-3 border border-gray-300 rounded-lg font-semibold hover:bg-gray-50 transition-colors"
                >
                  Back
                </button>
                <button
                  onClick={handleNextStep}
                  className="flex-1 bg-green-600 text-white py-3 rounded-lg font-semibold hover:bg-green-700 transition-colors"
                >
                  Review Order
                </button>
              </div>
            </div>
          )}

          {/* Step 3: Review Order */}
          {step === 3 && (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-6">Review Your Order</h2>

              {/* Order Items */}
              <div className="mb-6">
                <h3 className="font-medium text-gray-900 mb-3">Order Items</h3>
                {items.map((item) => (
                  <div key={item.id} className="flex justify-between py-2 border-b">
                    <div>
                      <span className="font-medium">{item.name}</span>
                      <span className="text-gray-500 text-sm ml-2">x{item.quantity}</span>
                    </div>
                    <span className="font-medium">${(item.price * item.quantity).toFixed(2)}</span>
                  </div>
                ))}
              </div>

              {/* Delivery Summary */}
              <div className="mb-6">
                <h3 className="font-medium text-gray-900 mb-3">
                  {deliveryType === 'delivery' ? 'Delivery Details' : 'Pickup Details'}
                </h3>
                {deliveryType === 'delivery' ? (
                  <div className="text-sm text-gray-600">
                    <p>{deliveryInfo.address} {deliveryInfo.unit}</p>
                    <p>{deliveryInfo.city}, {deliveryInfo.province} {deliveryInfo.postal_code}</p>
                    {deliveryInfo.instructions && (
                      <p className="mt-2 italic">Instructions: {deliveryInfo.instructions}</p>
                    )}
                  </div>
                ) : (
                  <div className="text-sm text-gray-600">
                    <p className="font-medium">{selectedStore?.name}</p>
                    <p>{selectedStore?.address}</p>
                  </div>
                )}
              </div>

              {/* Contact Summary */}
              <div className="mb-6">
                <h3 className="font-medium text-gray-900 mb-3">Contact Information</h3>
                <div className="text-sm text-gray-600">
                  <p>{customerInfo.name}</p>
                  <p>{customerInfo.email}</p>
                  <p>{customerInfo.phone}</p>
                </div>
              </div>

              {/* Payment Summary */}
              <div className="mb-6">
                <h3 className="font-medium text-gray-900 mb-3">Payment Method</h3>
                <div className="flex items-center text-sm text-gray-600">
                  <CreditCardIcon className="w-5 h-5 mr-2" />
                  <span>Card ending in {paymentInfo.cardNumber.slice(-4)}</span>
                </div>
              </div>

              <div className="flex gap-4">
                <button
                  onClick={handlePreviousStep}
                  className="flex-1 px-6 py-3 border border-gray-300 rounded-lg font-semibold hover:bg-gray-50 transition-colors"
                  disabled={loading}
                >
                  Back
                </button>
                <button
                  onClick={handlePlaceOrder}
                  disabled={loading}
                  className="flex-1 bg-green-600 text-white py-3 rounded-lg font-semibold hover:bg-green-700 transition-colors disabled:bg-gray-400"
                >
                  {loading ? 'Processing...' : `Place Order - $${total.toFixed(2)}`}
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Order Summary Sidebar */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 sticky top-4">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Order Summary</h2>

            {/* Items Count */}
            <div className="text-sm text-gray-600 mb-4">
              {items.length} item{items.length !== 1 ? 's' : ''}
            </div>

            {/* Price Breakdown */}
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Subtotal</span>
                <span className="font-medium">${subtotal.toFixed(2)}</span>
              </div>

              <div className="flex justify-between">
                <span className="text-gray-600">Tax (HST)</span>
                <span className="font-medium">${tax.toFixed(2)}</span>
              </div>

              <div className="flex justify-between">
                <span className="text-gray-600">
                  {deliveryType === 'delivery' ? 'Delivery' : 'Pickup'}
                </span>
                <span className="font-medium">
                  {deliveryFee === 0 ? (
                    <span className="text-green-600">FREE</span>
                  ) : (
                    `$${deliveryFee.toFixed(2)}`
                  )}
                </span>
              </div>

              <div className="border-t pt-2 mt-4">
                <div className="flex justify-between text-lg font-semibold">
                  <span>Total</span>
                  <span>${total.toFixed(2)}</span>
                </div>
              </div>
            </div>

            {/* Security Badge */}
            <div className="mt-6 p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center text-xs text-gray-600">
                <svg
                  className="w-4 h-4 mr-2 text-green-600"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z"
                    clipRule="evenodd"
                  />
                </svg>
                Secure SSL Encrypted Payment
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Checkout;