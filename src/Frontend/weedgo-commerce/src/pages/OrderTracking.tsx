import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  TruckIcon,
  CheckCircleIcon,
  ClockIcon,
  MapPinIcon,
  PhoneIcon,
  ExclamationCircleIcon,
  ArrowLeftIcon
} from '@heroicons/react/24/outline';
import { ordersApi, Order } from '@api/orders';
import toast from 'react-hot-toast';

interface OrderStepProps {
  title: string;
  description: string;
  time?: string;
  isCompleted: boolean;
  isCurrent: boolean;
  icon: React.ReactNode;
}

const OrderStep: React.FC<OrderStepProps> = ({
  title,
  description,
  time,
  isCompleted,
  isCurrent,
  icon
}) => (
  <div className="flex gap-4">
    <div className="flex flex-col items-center">
      <div
        className={`w-10 h-10 rounded-full flex items-center justify-center ${
          isCompleted
            ? 'bg-green-100 text-green-600'
            : isCurrent
            ? 'bg-blue-100 text-blue-600 animate-pulse'
            : 'bg-gray-100 text-gray-400'
        }`}
      >
        {icon}
      </div>
      <div className="flex-1 w-0.5 bg-gray-200 mt-2"></div>
    </div>
    <div className="flex-1 pb-8">
      <h3 className={`font-semibold ${isCompleted || isCurrent ? 'text-gray-900' : 'text-gray-500'}`}>
        {title}
      </h3>
      <p className="text-sm text-gray-600 mt-1">{description}</p>
      {time && <p className="text-xs text-gray-500 mt-1">{time}</p>}
    </div>
  </div>
);

const OrderTracking: React.FC = () => {
  const { orderNumber } = useParams<{ orderNumber: string }>();
  const navigate = useNavigate();
  const [order, setOrder] = useState<Order | null>(null);
  const [loading, setLoading] = useState(true);
  const [trackingNumber, setTrackingNumber] = useState('');
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    if (orderNumber) {
      loadOrder(orderNumber);
      // Auto-refresh every 30 seconds
      const interval = setInterval(() => {
        loadOrder(orderNumber, true);
      }, 30000);
      return () => clearInterval(interval);
    }
  }, [orderNumber]);

  const loadOrder = async (number: string, isRefresh = false) => {
    if (isRefresh) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }

    try {
      const orderData = await ordersApi.trackOrder(number);
      setOrder(orderData);
    } catch (error) {
      console.error('Failed to load order:', error);
      if (!isRefresh) {
        toast.error('Order not found');
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleTrackOrder = async (e: React.FormEvent) => {
    e.preventDefault();
    if (trackingNumber.trim()) {
      navigate(`/track/${trackingNumber.trim()}`);
      loadOrder(trackingNumber.trim());
    }
  };

  const getOrderSteps = (status: string) => {
    const steps = [
      {
        title: 'Order Placed',
        description: 'Your order has been received',
        icon: <CheckCircleIcon className="w-5 h-5" />,
        completed: true,
        statuses: ['pending', 'confirmed', 'preparing', 'ready', 'out_for_delivery', 'delivered']
      },
      {
        title: 'Order Confirmed',
        description: 'Your order has been confirmed and payment processed',
        icon: <CheckCircleIcon className="w-5 h-5" />,
        completed: false,
        statuses: ['confirmed', 'preparing', 'ready', 'out_for_delivery', 'delivered']
      },
      {
        title: 'Preparing',
        description: 'Your order is being prepared',
        icon: <ClockIcon className="w-5 h-5" />,
        completed: false,
        statuses: ['preparing', 'ready', 'out_for_delivery', 'delivered']
      },
      {
        title: 'Ready for Delivery',
        description: 'Your order is ready and waiting for pickup',
        icon: <CheckCircleIcon className="w-5 h-5" />,
        completed: false,
        statuses: ['ready', 'out_for_delivery', 'delivered']
      },
      {
        title: 'Out for Delivery',
        description: 'Your order is on the way',
        icon: <TruckIcon className="w-5 h-5" />,
        completed: false,
        statuses: ['out_for_delivery', 'delivered']
      },
      {
        title: 'Delivered',
        description: 'Your order has been delivered',
        icon: <CheckCircleIcon className="w-5 h-5" />,
        completed: false,
        statuses: ['delivered']
      }
    ];

    return steps.map(step => ({
      ...step,
      completed: step.statuses.includes(status),
      current: step.statuses[0] === status
    }));
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'delivered':
        return 'bg-green-100 text-green-800';
      case 'out_for_delivery':
        return 'bg-blue-100 text-blue-800';
      case 'ready':
      case 'preparing':
        return 'bg-yellow-100 text-yellow-800';
      case 'confirmed':
        return 'bg-primary-100 text-primary-800';
      case 'cancelled':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatDate = (date: string) => {
    return new Date(date).toLocaleString('en-CA', {
      weekday: 'short',
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="container-max py-8">
        <div className="max-w-4xl mx-auto">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-1/3 mb-4"></div>
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="h-6 bg-gray-200 rounded w-1/4 mb-4"></div>
              <div className="space-y-4">
                <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                <div className="h-4 bg-gray-200 rounded w-1/2"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!order && !loading) {
    return (
      <div className="container-max py-8">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-3xl font-bold text-gray-900 mb-8">Track Your Order</h1>

          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
            <form onSubmit={handleTrackOrder} className="max-w-md mx-auto">
              <label htmlFor="tracking" className="block text-sm font-medium text-gray-700 mb-2">
                Enter Order Number
              </label>
              <div className="flex gap-2">
                <input
                  id="tracking"
                  type="text"
                  value={trackingNumber}
                  onChange={(e) => setTrackingNumber(e.target.value)}
                  placeholder="e.g. ORD-123456"
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                  required
                />
                <button
                  type="submit"
                  className="btn-primary"
                >
                  Track
                </button>
              </div>
              <p className="text-sm text-gray-500 mt-2">
                You can find your order number in your confirmation email
              </p>
            </form>
          </div>
        </div>
      </div>
    );
  }

  if (!order) return null;

  const steps = getOrderSteps(order.status);
  const currentStepIndex = steps.findIndex(s => s.current);

  return (
    <div className="container-max py-8">
      <div className="max-w-4xl mx-auto">
        <button
          onClick={() => navigate('/orders')}
          className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-4"
        >
          <ArrowLeftIcon className="w-4 h-4" />
          Back to Orders
        </button>

        <div className="flex items-center justify-between mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Order Tracking</h1>
          {refreshing && (
            <span className="text-sm text-gray-500">Refreshing...</span>
          )}
        </div>

        {/* Order Summary */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-xl font-semibold">Order #{order.order_number}</h2>
              <p className="text-sm text-gray-600">
                Placed on {formatDate(order.created_at)}
              </p>
            </div>
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(order.status)}`}>
              {order.status.replace(/_/g, ' ').toUpperCase()}
            </span>
          </div>

          {order.status === 'cancelled' ? (
            <div className="bg-red-50 border-l-4 border-red-400 p-4">
              <div className="flex">
                <ExclamationCircleIcon className="h-5 w-5 text-red-400" />
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-red-800">Order Cancelled</h3>
                  <p className="text-sm text-red-700 mt-1">
                    This order has been cancelled. If you have any questions, please contact support.
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <>
              {/* Estimated Delivery */}
              {order.estimated_delivery && (
                <div className="bg-green-50 border-l-4 border-green-400 p-4 mb-4">
                  <div className="flex">
                    <TruckIcon className="h-5 w-5 text-green-400" />
                    <div className="ml-3">
                      <h3 className="text-sm font-medium text-green-800">
                        Estimated Delivery
                      </h3>
                      <p className="text-sm text-green-700 mt-1">
                        {formatDate(order.estimated_delivery)}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Tracking Timeline */}
              <div className="mt-8">
                <h3 className="font-semibold text-gray-900 mb-4">Delivery Progress</h3>
                <div className="relative">
                  {steps.map((step, index) => (
                    <OrderStep
                      key={index}
                      title={step.title}
                      description={step.description}
                      time={step.completed && order.updated_at ? formatDate(order.updated_at) : undefined}
                      isCompleted={step.completed}
                      isCurrent={index === currentStepIndex}
                      icon={step.icon}
                    />
                  ))}
                </div>
              </div>

              {/* Driver Info */}
              {order.driver_name && order.status === 'out_for_delivery' && (
                <div className="mt-6 p-4 bg-blue-50 rounded-lg">
                  <h3 className="font-semibold text-gray-900 mb-2">Delivery Driver</h3>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium">{order.driver_name}</p>
                      {order.driver_phone && (
                        <p className="text-sm text-gray-600 flex items-center gap-1 mt-1">
                          <PhoneIcon className="w-4 h-4" />
                          {order.driver_phone}
                        </p>
                      )}
                    </div>
                    {order.tracking_number && (
                      <div className="text-right">
                        <p className="text-xs text-gray-500">Tracking #</p>
                        <p className="text-sm font-mono">{order.tracking_number}</p>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </>
          )}

          {/* Delivery Address */}
          <div className="mt-6 pt-6 border-t">
            <h3 className="font-semibold text-gray-900 mb-2">
              {order.delivery_info.type === 'delivery' ? 'Delivery Address' : 'Pickup Location'}
            </h3>
            <div className="flex items-start gap-2">
              <MapPinIcon className="w-5 h-5 text-gray-400 mt-0.5" />
              <div className="text-sm text-gray-600">
                {order.delivery_info.address && (
                  <>
                    <p>{order.delivery_info.address}</p>
                    <p>
                      {order.delivery_info.city}, {order.delivery_info.province} {order.delivery_info.postal_code}
                    </p>
                  </>
                )}
                {order.delivery_info.delivery_instructions && (
                  <p className="mt-2 italic">
                    Instructions: {order.delivery_info.delivery_instructions}
                  </p>
                )}
              </div>
            </div>
          </div>

          {/* Order Items */}
          <div className="mt-6 pt-6 border-t">
            <h3 className="font-semibold text-gray-900 mb-4">Order Items</h3>
            <div className="space-y-3">
              {order.items.map((item, index) => (
                <div key={index} className="flex items-center gap-4">
                  {item.image_url && (
                    <img
                      src={item.image_url}
                      alt={item.name}
                      className="w-12 h-12 object-cover rounded"
                    />
                  )}
                  <div className="flex-1">
                    <p className="font-medium">{item.name}</p>
                    <p className="text-sm text-gray-600">
                      Qty: {item.quantity} × ${item.price.toFixed(2)}
                    </p>
                  </div>
                  <p className="font-medium">${item.subtotal.toFixed(2)}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Order Total */}
          <div className="mt-6 pt-6 border-t">
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span>Subtotal</span>
                <span>${order.subtotal.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span>Tax</span>
                <span>${order.tax.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span>Delivery</span>
                <span>${order.delivery_fee.toFixed(2)}</span>
              </div>
              <div className="flex justify-between font-semibold text-base pt-2 border-t">
                <span>Total</span>
                <span>${order.total.toFixed(2)}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Help Section */}
        <div className="bg-gray-50 rounded-lg p-6">
          <h3 className="font-semibold text-gray-900 mb-2">Need Help?</h3>
          <p className="text-sm text-gray-600 mb-4">
            If you have any questions about your order, please don't hesitate to contact us.
          </p>
          <div className="flex gap-4">
            <button className="btn-secondary">Contact Support</button>
            <button
              onClick={() => loadOrder(order.order_number, true)}
              className="btn-secondary"
            >
              Refresh Status
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OrderTracking;