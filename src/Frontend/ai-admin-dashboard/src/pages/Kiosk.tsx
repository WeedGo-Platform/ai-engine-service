import React, { useState, useEffect, useCallback } from 'react';
import { useStoreContext } from '../contexts/StoreContext';
import { KioskProvider } from '../contexts/KioskContext';
import WelcomeScreen from '../components/kiosk/WelcomeScreen';
import ProductBrowsing from '../components/kiosk/ProductBrowsing';
import Cart from '../components/kiosk/Cart';
import Checkout from '../components/kiosk/Checkout';
import OrderConfirmation from '../components/kiosk/OrderConfirmation';
import { useKioskSession } from '../hooks/useKioskSession';

// Define the kiosk flow states
export type KioskFlow =
  | 'welcome'
  | 'browsing'
  | 'cart'
  | 'checkout'
  | 'confirmation';

interface KioskProps {
  isFullscreen?: boolean;
  onFullscreenToggle?: () => void;
}

export default function Kiosk({ isFullscreen, onFullscreenToggle }: KioskProps) {
  const { currentStore } = useStoreContext();
  const [currentFlow, setCurrentFlow] = useState<KioskFlow>('welcome');
  const [orderId, setOrderId] = useState<string | null>(null);
  const { session, initializeSession, clearSession } = useKioskSession();

  // Handle flow navigation
  const navigateToFlow = useCallback((flow: KioskFlow) => {
    setCurrentFlow(flow);
  }, []);

  // Handle order completion
  const handleOrderComplete = useCallback((newOrderId: string) => {
    setOrderId(newOrderId);
    setCurrentFlow('confirmation');
  }, []);

  // Handle starting a new order
  const handleNewOrder = useCallback(() => {
    setOrderId(null);
    setCurrentFlow('browsing');
  }, []);

  // Reset to welcome after timeout
  useEffect(() => {
    let timeoutId: NodeJS.Timeout;

    if (currentFlow === 'confirmation') {
      // After 30 seconds on confirmation, reset to welcome
      timeoutId = setTimeout(() => {
        clearSession();
        setCurrentFlow('welcome');
        setOrderId(null);
      }, 30000);
    }

    return () => {
      if (timeoutId) clearTimeout(timeoutId);
    };
  }, [currentFlow, clearSession]);

  // Validate store is selected
  if (!currentStore) {
    return (
      <div className="h-full flex items-center justify-center bg-gray-100">
        <div className="text-center">
          <h2 className="text-2xl font-semibold text-gray-700 mb-4">
            No Store Selected
          </h2>
          <p className="text-gray-600">
            Please select a store to activate the kiosk
          </p>
        </div>
      </div>
    );
  }

  return (
    <KioskProvider>
      <div className="h-full bg-gray-50 overflow-hidden">
        {/* Main content based on current flow */}
        <div className="h-full">
          {currentFlow === 'welcome' && (
            <WelcomeScreen
              onContinue={() => navigateToFlow('browsing')}
              currentStore={currentStore}
            />
          )}

          {currentFlow === 'browsing' && (
            <ProductBrowsing
              onCartClick={() => navigateToFlow('cart')}
              currentStore={currentStore}
            />
          )}

          {currentFlow === 'cart' && (
            <Cart
              onBack={() => navigateToFlow('browsing')}
              onCheckout={() => navigateToFlow('checkout')}
              currentStore={currentStore}
            />
          )}

          {currentFlow === 'checkout' && (
            <Checkout
              onBack={() => navigateToFlow('cart')}
              onComplete={handleOrderComplete}
              currentStore={currentStore}
            />
          )}

          {currentFlow === 'confirmation' && orderId && (
            <OrderConfirmation
              orderId={orderId}
              onNewOrder={handleNewOrder}
              currentStore={currentStore}
            />
          )}
        </div>

        {/* Fullscreen toggle button - always visible in corner */}
        {onFullscreenToggle && (
          <button
            onClick={onFullscreenToggle}
            className="fixed bottom-4 right-4 p-3 bg-white rounded-full shadow-lg hover:shadow-xl transition-shadow z-50"
            title={isFullscreen ? 'Exit fullscreen' : 'Enter fullscreen'}
          >
            {isFullscreen ? (
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 9V4.5M9 9H4.5M9 9L3.75 3.75M9 15v4.5M9 15H4.5M9 15l-5.25 5.25M15 9h4.5M15 9V4.5M15 9l5.25-5.25M15 15h4.5M15 15v4.5m0-4.5l5.25 5.25" />
              </svg>
            ) : (
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
              </svg>
            )}
          </button>
        )}
      </div>
    </KioskProvider>
  );
}