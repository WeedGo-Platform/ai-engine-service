import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FiShoppingCart, FiTruck, FiCreditCard, FiCheck, FiChevronLeft, FiChevronRight } from 'react-icons/fi';
import { checkoutService, CheckoutSession, DeliveryAddress, CompleteCheckoutRequest } from '../../services/checkout';
import { cartService } from '../../services/cart';
import CartReview from './CartReview';
import DeliveryDetails from './DeliveryDetails';
import PaymentMethod from './PaymentMethod';
import OrderConfirmation from './OrderConfirmation';
import { useTemplateContext } from '../../contexts/TemplateContext';

export interface CheckoutProps {
  onClose: () => void;
  onComplete?: (orderId: string) => void;
}

type CheckoutStep = 'cart' | 'delivery' | 'payment' | 'confirmation';

const Checkout: React.FC<CheckoutProps> = ({ onClose, onComplete }) => {
  const { currentTemplate } = useTemplateContext();
  const [currentStep, setCurrentStep] = useState<CheckoutStep>('cart');
  const [session, setSession] = useState<CheckoutSession | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [orderId, setOrderId] = useState<string | null>(null);
  const [timeRemaining, setTimeRemaining] = useState<number>(30 * 60 * 1000); // 30 minutes

  // Step configuration
  const steps: { id: CheckoutStep; label: string; icon: React.ElementType }[] = [
    { id: 'cart', label: 'Review Cart', icon: FiShoppingCart },
    { id: 'delivery', label: 'Delivery Details', icon: FiTruck },
    { id: 'payment', label: 'Payment', icon: FiCreditCard },
    { id: 'confirmation', label: 'Confirmation', icon: FiCheck }
  ];

  const currentStepIndex = steps.findIndex(s => s.id === currentStep);

  // Initialize or resume checkout session
  useEffect(() => {
    initializeCheckout();
  }, []);

  // Update timer
  useEffect(() => {
    if (!session || session.status !== 'draft') return;

    const timer = setInterval(() => {
      const remaining = checkoutService.getTimeRemaining(session);
      setTimeRemaining(remaining);
      
      if (remaining <= 0) {
        handleSessionExpired();
      }
    }, 1000);

    return () => clearInterval(timer);
  }, [session]);

  const initializeCheckout = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Check for existing session
      let existingSession = await checkoutService.getSession();
      
      if (!existingSession || checkoutService.isSessionExpired(existingSession)) {
        // Create new session
        existingSession = await checkoutService.initiateCheckout();
      }
      
      setSession(existingSession);
    } catch (err: any) {
      setError('Failed to initialize checkout. Please try again.');
      console.error('Checkout initialization error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSessionExpired = () => {
    setError('Your checkout session has expired. Please start over.');
    setTimeout(() => {
      onClose();
    }, 3000);
  };

  const handleCartContinue = async () => {
    if (!session) return;
    setCurrentStep('delivery');
  };

  const handleDeliveryUpdate = async (deliveryData: {
    fulfillment_type: 'delivery' | 'pickup' | 'shipping';
    delivery_address?: DeliveryAddress;
    pickup_store_id?: string;
    pickup_datetime?: string;
    delivery_instructions?: string;
    customer_email: string;
    customer_phone: string;
    customer_first_name: string;
    customer_last_name: string;
  }) => {
    if (!session) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const updatedSession = await checkoutService.updateSession(session.session_id, deliveryData);
      
      // Calculate taxes and delivery fee if delivery address provided
      if (deliveryData.delivery_address && deliveryData.fulfillment_type === 'delivery') {
        const [taxes, deliveryFee] = await Promise.all([
          checkoutService.calculateTaxes(session.session_id),
          checkoutService.calculateDeliveryFee(session.session_id, deliveryData.delivery_address)
        ]);
        
        // Update session with calculated values
        const finalSession = await checkoutService.updateSession(session.session_id, {
          ...deliveryData,
          tip_amount: updatedSession.tip_amount || 0
        });
        
        setSession(finalSession);
      } else {
        setSession(updatedSession);
      }
      
      setCurrentStep('payment');
    } catch (err: any) {
      setError('Failed to update delivery details. Please try again.');
      console.error('Delivery update error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handlePaymentComplete = async (paymentData: CompleteCheckoutRequest) => {
    if (!session) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const result = await checkoutService.completeCheckout(session.session_id, paymentData);
      
      if (result.success && result.order_id) {
        setOrderId(result.order_id);
        setCurrentStep('confirmation');
        
        // Clear cart
        await cartService.clearCart();
        
        // Callback
        if (onComplete) {
          onComplete(result.order_id);
        }
      } else {
        setError(result.message || 'Payment failed. Please try again.');
      }
    } catch (err: any) {
      setError('Payment processing failed. Please try again.');
      console.error('Payment error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleApplyDiscount = async (couponCode: string) => {
    if (!session) return { success: false, message: 'No active session' };
    
    try {
      const result = await checkoutService.applyDiscount(session.session_id, { coupon_code: couponCode });
      
      if (result.success) {
        // Refresh session to get updated totals
        const updatedSession = await checkoutService.getSession(session.session_id);
        if (updatedSession) {
          setSession(updatedSession);
        }
        return { success: true, message: result.message };
      } else {
        return { success: false, message: result.message };
      }
    } catch (err: any) {
      return { success: false, message: 'Failed to apply discount' };
    }
  };

  const formatTime = (ms: number) => {
    const minutes = Math.floor(ms / 60000);
    const seconds = Math.floor((ms % 60000) / 1000);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  const getThemeColors = () => {
    switch (currentTemplate) {
      case 'pot-palace':
        return {
          primary: 'bg-purple-600 hover:bg-purple-700',
          secondary: 'bg-purple-100 text-purple-700',
          accent: 'text-purple-600'
        };
      case 'modern-minimal':
        return {
          primary: 'bg-blue-600 hover:bg-blue-700',
          secondary: 'bg-blue-100 text-blue-700',
          accent: 'text-blue-600'
        };
      case 'dark-tech':
        return {
          primary: 'bg-green-600 hover:bg-green-700',
          secondary: 'bg-green-100 text-green-700',
          accent: 'text-green-600'
        };
      default:
        return {
          primary: 'bg-gray-600 hover:bg-gray-700',
          secondary: 'bg-gray-100 text-gray-700',
          accent: 'text-gray-600'
        };
    }
  };

  const theme = getThemeColors();

  if (loading && !session) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between py-4">
            <h1 className="text-2xl font-bold text-gray-900">Checkout</h1>
            
            {/* Timer */}
            {session?.status === 'draft' && (
              <div className="flex items-center space-x-2 text-sm text-gray-600">
                <span>Session expires in:</span>
                <span className="font-mono font-semibold">{formatTime(timeRemaining)}</span>
              </div>
            )}
            
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Progress Steps */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <nav className="flex items-center justify-center">
            {steps.map((step, index) => {
              const Icon = step.icon;
              const isActive = step.id === currentStep;
              const isCompleted = index < currentStepIndex;
              
              return (
                <React.Fragment key={step.id}>
                  <div className={`flex items-center ${index > 0 ? 'ml-8' : ''}`}>
                    <div
                      className={`
                        flex items-center justify-center w-10 h-10 rounded-full
                        ${isActive ? theme.primary + ' text-white' : 
                          isCompleted ? 'bg-green-500 text-white' : 
                          'bg-gray-200 text-gray-400'}
                      `}
                    >
                      {isCompleted ? <FiCheck /> : <Icon />}
                    </div>
                    <span className={`ml-3 text-sm font-medium ${isActive ? theme.accent : 'text-gray-500'}`}>
                      {step.label}
                    </span>
                  </div>
                  
                  {index < steps.length - 1 && (
                    <div className={`mx-4 h-0.5 w-12 ${isCompleted ? 'bg-green-500' : 'bg-gray-200'}`} />
                  )}
                </React.Fragment>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-4">
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            {error}
          </div>
        </div>
      )}

      {/* Step Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <AnimatePresence mode="wait">
          <motion.div
            key={currentStep}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.3 }}
          >
            {currentStep === 'cart' && session && (
              <CartReview
                session={session}
                onContinue={handleCartContinue}
                onApplyDiscount={handleApplyDiscount}
                theme={theme}
              />
            )}
            
            {currentStep === 'delivery' && session && (
              <DeliveryDetails
                session={session}
                onContinue={handleDeliveryUpdate}
                onBack={() => setCurrentStep('cart')}
                theme={theme}
              />
            )}
            
            {currentStep === 'payment' && session && (
              <PaymentMethod
                session={session}
                onComplete={handlePaymentComplete}
                onBack={() => setCurrentStep('delivery')}
                loading={loading}
                theme={theme}
              />
            )}
            
            {currentStep === 'confirmation' && orderId && (
              <OrderConfirmation
                orderId={orderId}
                session={session}
                onClose={onClose}
                theme={theme}
              />
            )}
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
};

export default Checkout;