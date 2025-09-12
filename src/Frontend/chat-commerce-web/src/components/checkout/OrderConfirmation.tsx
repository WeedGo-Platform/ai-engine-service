import React from 'react';
import { FiCheckCircle, FiPackage, FiMail, FiHome, FiCalendar, FiUser, FiPhone, FiMapPin, FiTruck } from 'react-icons/fi';
import { CheckoutSession } from '../../services/checkout';

interface OrderConfirmationProps {
  orderId: string;
  session: CheckoutSession | null;
  onClose: () => void;
  theme: any;
}

const OrderConfirmation: React.FC<OrderConfirmationProps> = ({ orderId, session, onClose, theme }) => {
  const formatDateTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="max-w-3xl mx-auto">
      <div className="bg-white rounded-lg shadow">
        {/* Success Header */}
        <div className="p-8 text-center border-b">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mb-4">
            <FiCheckCircle className="w-8 h-8 text-green-600" />
          </div>
          
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Order Confirmed!</h1>
          <p className="text-gray-600">Thank you for your order. We've sent a confirmation to your email.</p>
          
          <div className="mt-6 p-4 bg-gray-50 rounded-lg inline-block">
            <p className="text-sm text-gray-600 mb-1">Order Number</p>
            <p className="text-lg font-mono font-semibold text-gray-900">
              {orderId.split('-')[0].toUpperCase()}
            </p>
          </div>
        </div>

        {/* Order Details */}
        {session && (
          <div className="p-6 space-y-6">
            {/* Delivery/Pickup Information */}
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-3 flex items-center">
                {session.fulfillment_type === 'delivery' ? (
                  <>
                    <FiTruck className="w-5 h-5 mr-2" />
                    Delivery Information
                  </>
                ) : (
                  <>
                    <FiMapPin className="w-5 h-5 mr-2" />
                    Pickup Information
                  </>
                )}
              </h2>
              
              <div className="bg-gray-50 rounded-lg p-4 space-y-2">
                {session.fulfillment_type === 'delivery' ? (
                  <>
                    <div className="flex items-start">
                      <FiHome className="w-4 h-4 text-gray-400 mt-0.5 mr-2" />
                      <div>
                        <p className="text-sm font-medium text-gray-900">Delivery Address</p>
                        {session.delivery_address && (
                          <p className="text-sm text-gray-600">
                            {session.delivery_address.street_address}
                            {session.delivery_address.unit_number && `, ${session.delivery_address.unit_number}`}<br />
                            {session.delivery_address.city}, {session.delivery_address.province_state} {session.delivery_address.postal_code}
                          </p>
                        )}
                      </div>
                    </div>
                    
                    {session.delivery_datetime && (
                      <div className="flex items-start">
                        <FiCalendar className="w-4 h-4 text-gray-400 mt-0.5 mr-2" />
                        <div>
                          <p className="text-sm font-medium text-gray-900">Estimated Delivery</p>
                          <p className="text-sm text-gray-600">{formatDateTime(session.delivery_datetime)}</p>
                        </div>
                      </div>
                    )}
                    
                    {session.delivery_instructions && (
                      <div className="flex items-start">
                        <FiPackage className="w-4 h-4 text-gray-400 mt-0.5 mr-2" />
                        <div>
                          <p className="text-sm font-medium text-gray-900">Delivery Instructions</p>
                          <p className="text-sm text-gray-600">{session.delivery_instructions}</p>
                        </div>
                      </div>
                    )}
                  </>
                ) : (
                  <>
                    <div className="flex items-start">
                      <FiMapPin className="w-4 h-4 text-gray-400 mt-0.5 mr-2" />
                      <div>
                        <p className="text-sm font-medium text-gray-900">Pickup Location</p>
                        <p className="text-sm text-gray-600">Store location details will be provided</p>
                      </div>
                    </div>
                    
                    {session.pickup_datetime && (
                      <div className="flex items-start">
                        <FiCalendar className="w-4 h-4 text-gray-400 mt-0.5 mr-2" />
                        <div>
                          <p className="text-sm font-medium text-gray-900">Pickup Time</p>
                          <p className="text-sm text-gray-600">{formatDateTime(session.pickup_datetime)}</p>
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>

            {/* Customer Information */}
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-3">Customer Information</h2>
              
              <div className="bg-gray-50 rounded-lg p-4 space-y-2">
                <div className="flex items-center">
                  <FiUser className="w-4 h-4 text-gray-400 mr-2" />
                  <span className="text-sm text-gray-600">
                    {session.customer_first_name} {session.customer_last_name}
                  </span>
                </div>
                
                <div className="flex items-center">
                  <FiMail className="w-4 h-4 text-gray-400 mr-2" />
                  <span className="text-sm text-gray-600">{session.customer_email}</span>
                </div>
                
                <div className="flex items-center">
                  <FiPhone className="w-4 h-4 text-gray-400 mr-2" />
                  <span className="text-sm text-gray-600">{session.customer_phone}</span>
                </div>
              </div>
            </div>

            {/* Order Summary */}
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-3">Order Summary</h2>
              
              <div className="bg-gray-50 rounded-lg p-4">
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
                  
                  {session.tip_amount > 0 && (
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Tip</span>
                      <span className="font-medium">${session.tip_amount.toFixed(2)}</span>
                    </div>
                  )}
                  
                  <div className="flex justify-between text-base font-semibold pt-2 border-t border-gray-200">
                    <span>Total Paid</span>
                    <span>${session.total_amount.toFixed(2)}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Next Steps */}
            <div className="border-t pt-6">
              <h3 className="text-base font-semibold text-gray-900 mb-3">What's Next?</h3>
              <ul className="space-y-2 text-sm text-gray-600">
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">✓</span>
                  You'll receive an order confirmation email shortly
                </li>
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">✓</span>
                  {session.fulfillment_type === 'delivery' 
                    ? "We'll notify you when your order is out for delivery"
                    : "We'll notify you when your order is ready for pickup"}
                </li>
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">✓</span>
                  You can track your order status in your account
                </li>
              </ul>
            </div>

            {/* Action Button */}
            <div className="flex justify-center pt-4">
              <button
                onClick={onClose}
                className={`px-8 py-3 text-white font-medium rounded-md transition-colors ${theme.primary}`}
              >
                Continue Shopping
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default OrderConfirmation;