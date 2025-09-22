import React, { useState, useEffect, useRef } from 'react';
import { ShoppingCart, Monitor, Menu, Maximize, Minimize, Tv } from 'lucide-react';
import POS from './POS';
import { KioskProvider, useKiosk } from '../contexts/KioskContext';
import WelcomeScreen from '../components/kiosk/WelcomeScreen';
import ProductBrowsing from '../components/kiosk/ProductBrowsing';
import Cart from '../components/kiosk/Cart';
import Checkout from '../components/kiosk/Checkout';
import OrderConfirmation from '../components/kiosk/OrderConfirmation';
import StoreSelectionModal from '../components/StoreSelectionModal';
import MenuDisplay from '../components/menuDisplay/MenuDisplay';
import { useStoreContext } from '../contexts/StoreContext';
import { useAuth } from '../contexts/AuthContext';

// Kiosk component that manages the flow
function KioskApp({ currentStore }: { currentStore: { id: string; name: string } | null }) {
  const { currentScreen, setCurrentScreen } = useKiosk();
  const [completedOrderId, setCompletedOrderId] = useState<string | null>(null);

  console.log('KioskApp rendering, currentScreen:', currentScreen, 'currentStore:', currentStore);

  const handleWelcomeContinue = () => {
    setCurrentScreen('browse');
  };

  const handleViewCart = () => {
    setCurrentScreen('cart');
  };

  const handleCheckout = () => {
    setCurrentScreen('checkout');
  };

  const handleOrderComplete = (orderId: string) => {
    setCompletedOrderId(orderId);
    setCurrentScreen('confirmation');
  };

  const handleNewSession = () => {
    setCompletedOrderId(null);
    setCurrentScreen('welcome');
  };

  // Don't render if no store is selected
  if (!currentStore) {
    return (
      <div className="h-full flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <p className="text-gray-500">Please select a store to continue</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full bg-gray-50">
      {currentScreen === 'welcome' && (
        <WelcomeScreen
          onContinue={handleWelcomeContinue}
          currentStore={currentStore}
        />
      )}
      {currentScreen === 'browse' && (
        <ProductBrowsing
          onCartClick={handleViewCart}
          currentStore={currentStore}
        />
      )}
      {currentScreen === 'cart' && (
        <Cart
          onBack={() => setCurrentScreen('browse')}
          onCheckout={handleCheckout}
          currentStore={currentStore}
        />
      )}
      {currentScreen === 'checkout' && (
        <Checkout
          onBack={() => setCurrentScreen('cart')}
          onComplete={handleOrderComplete}
          currentStore={currentStore}
        />
      )}
      {currentScreen === 'confirmation' && completedOrderId && (
        <OrderConfirmation
          onNewOrder={handleNewSession}
          onReturnHome={handleNewSession}
          orderId={completedOrderId}
          currentStore={currentStore}
        />
      )}
    </div>
  );
}

export default function Apps() {
  const [activeTab, setActiveTab] = useState<'pos' | 'kiosk' | 'menu-display'>('pos');
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [isKioskFullscreen, setIsKioskFullscreen] = useState(false);
  const [showStoreSelectionModal, setShowStoreSelectionModal] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const posContainerRef = useRef<HTMLDivElement>(null);
  const kioskContainerRef = useRef<HTMLDivElement>(null);

  const { currentStore, selectStore } = useStoreContext();
  const { user, isSuperAdmin, isTenantAdminOnly, isStoreManager } = useAuth();

  // Check if store selection is needed when switching to kiosk or menu-display tab
  useEffect(() => {
    if ((activeTab === 'kiosk' || activeTab === 'menu-display') && !currentStore) {
      // Show store selection modal if no store is selected
      setShowStoreSelectionModal(true);
    }
  }, [activeTab, currentStore]);

  const handleStoreSelect = async (tenantId: string, storeId: string, storeName: string, tenantName?: string) => {
    try {
      // Update the store context with the selected store
      await selectStore(storeId, storeName);
      setShowStoreSelectionModal(false);
    } catch (error) {
      console.error('Failed to select store:', error);
      setShowStoreSelectionModal(false);
    }
  };

  // Handle POS fullscreen toggle using browser's fullscreen API
  const handlePOSFullscreenToggle = async () => {
    if (!document.fullscreenElement) {
      try {
        // Use the POS container for fullscreen
        if (posContainerRef.current) {
          await posContainerRef.current.requestFullscreen();
          setIsFullscreen(true);
        }
      } catch (err) {
        console.error('Error entering fullscreen:', err);
      }
    } else {
      try {
        await document.exitFullscreen();
        setIsFullscreen(false);
      } catch (err) {
        console.error('Error exiting fullscreen:', err);
      }
    }
  };

  // Handle Kiosk fullscreen toggle
  const handleKioskFullscreenToggle = async () => {
    if (!document.fullscreenElement) {
      try {
        if (kioskContainerRef.current) {
          await kioskContainerRef.current.requestFullscreen();
          setIsKioskFullscreen(true);
        }
      } catch (err) {
        console.error('Error entering fullscreen:', err);
      }
    } else {
      try {
        await document.exitFullscreen();
        setIsKioskFullscreen(false);
      } catch (err) {
        console.error('Error exiting fullscreen:', err);
      }
    }
  };

  // Listen for fullscreen changes
  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
      setIsKioskFullscreen(!!document.fullscreenElement);
    };

    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => {
      document.removeEventListener('fullscreenchange', handleFullscreenChange);
    };
  }, []);

  return (
    <div ref={containerRef} className="h-full flex flex-col bg-gray-50">
      {/* Compact Header */}
      <div className="bg-white border-b">
        <div className="px-4 sm:px-6 py-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <h1 className="text-lg sm:text-xl font-bold">Apps</h1>

              {/* Tabs - more compact */}
              <div className="flex gap-1 sm:gap-2">
                <button
                  onClick={() => setActiveTab('pos')}
                  className={`px-3 py-1.5 rounded-lg text-sm font-medium flex items-center gap-1.5 transition-colors ${
                    activeTab === 'pos'
                      ? 'bg-accent-500 text-white'
                      : 'text-gray-600 hover:bg-gray-50'
                  }`}
                >
                  <ShoppingCart className="w-3.5 h-3.5" />
                  <span className="hidden sm:inline">Point of Sale</span>
                  <span className="sm:hidden">POS</span>
                </button>
                <button
                  onClick={() => setActiveTab('kiosk')}
                  className={`px-3 py-1.5 rounded-lg text-sm font-medium flex items-center gap-1.5 transition-colors ${
                    activeTab === 'kiosk'
                      ? 'bg-accent-500 text-white'
                      : 'text-gray-600 hover:bg-gray-50'
                  }`}
                >
                  <Monitor className="w-3.5 h-3.5" />
                  <span className="hidden sm:inline">Self-Service Kiosk</span>
                  <span className="sm:hidden">Kiosk</span>
                </button>
                <button
                  onClick={() => setActiveTab('menu-display')}
                  className={`px-3 py-1.5 rounded-lg text-sm font-medium flex items-center gap-1.5 transition-colors ${
                    activeTab === 'menu-display'
                      ? 'bg-accent-500 text-white'
                      : 'text-gray-600 hover:bg-gray-50'
                  }`}
                >
                  <Menu className="w-3.5 h-3.5" />
                  <span className="hidden sm:inline">Menu Display</span>
                  <span className="sm:hidden">Menu</span>
                </button>
              </div>
            </div>

            {/* Fullscreen toggle for Kiosk */}
            {activeTab === 'kiosk' && (
              <button
                onClick={handleKioskFullscreenToggle}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                title={isKioskFullscreen ? 'Exit Fullscreen' : 'Enter Fullscreen'}
              >
                {isKioskFullscreen ? (
                  <Minimize className="w-5 h-5 text-gray-600" />
                ) : (
                  <Maximize className="w-5 h-5 text-gray-600" />
                )}
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        {activeTab === 'pos' && (
          <div ref={posContainerRef} className="h-full">
            <POS
              hideHeader={true}
              isFullscreen={isFullscreen}
              onFullscreenToggle={handlePOSFullscreenToggle}
            />
          </div>
        )}

        {activeTab === 'kiosk' && (
          <div ref={kioskContainerRef} className="h-full">
            {console.log('Rendering kiosk tab with store:', currentStore)}
            <KioskProvider>
              <KioskApp currentStore={currentStore} />
            </KioskProvider>
          </div>
        )}

        {activeTab === 'menu-display' && (
          <div className="h-full">
            <MenuDisplay />
          </div>
        )}
      </div>

      {/* Store Selection Modal */}
      {showStoreSelectionModal && (
        <StoreSelectionModal
          isOpen={showStoreSelectionModal}
          onSelect={handleStoreSelect}
          onClose={() => setShowStoreSelectionModal(false)}
        />
      )}
    </div>
  );
}