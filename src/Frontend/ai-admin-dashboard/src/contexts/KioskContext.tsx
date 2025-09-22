import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';

// Define types for Kiosk context
interface Customer {
  id: string;
  email?: string;
  phone?: string;
  firstName?: string;
  lastName?: string;
  preferences?: CustomerPreferences;
  language?: string;
}

interface CustomerPreferences {
  effects?: string[];
  categories?: string[];
  thcRange?: { min: number; max: number };
  cbdRange?: { min: number; max: number };
}

interface CartItem {
  id: string;
  productId: string;
  name: string;
  price: number;
  quantity: number;
  image?: string;
  thc?: number;
  cbd?: number;
  category?: string;
  subcategory?: string;
  batchLot?: string;
}

interface KioskContextValue {
  // Language settings
  language: string;
  setLanguage: (lang: string) => void;

  // Customer management
  customer: Customer | null;
  setCustomer: (customer: Customer | null) => void;
  isGuest: boolean;
  setIsGuest: (isGuest: boolean) => void;

  // Cart management
  cart: CartItem[];
  addToCart: (item: CartItem) => void;
  updateCartItem: (productId: string, quantity: number) => void;
  removeFromCart: (productId: string) => void;
  clearCart: () => void;
  cartTotal: number;
  cartItemCount: number;

  // Session management
  sessionId: string | null;
  setSessionId: (id: string | null) => void;
  initializeSession: (customer: Customer | undefined, language: string) => void;

  // Recommendations
  recommendations: any[];
  setRecommendations: (items: any[]) => void;

  // UI state
  showChat: boolean;
  setShowChat: (show: boolean) => void;
  currentScreen: 'welcome' | 'browse' | 'cart' | 'checkout' | 'confirmation';
  setCurrentScreen: (screen: 'welcome' | 'browse' | 'cart' | 'checkout' | 'confirmation') => void;
}

interface KioskProviderProps {
  children: ReactNode;
}

// Create context
const KioskContext = createContext<KioskContextValue | undefined>(undefined);

// Custom hook to use Kiosk context
export const useKiosk = (): KioskContextValue => {
  const context = useContext(KioskContext);
  if (!context) {
    throw new Error('useKiosk must be used within a KioskProvider');
  }
  return context;
};

// Kiosk Provider component
export const KioskProvider: React.FC<KioskProviderProps> = ({ children }) => {
  // State management
  const [language, setLanguage] = useState<string>('en');
  const [customer, setCustomer] = useState<Customer | null>(null);
  const [isGuest, setIsGuest] = useState<boolean>(true);
  const [cart, setCart] = useState<CartItem[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [showChat, setShowChat] = useState<boolean>(false);
  const [currentScreen, setCurrentScreen] = useState<'welcome' | 'browse' | 'cart' | 'checkout' | 'confirmation'>('welcome');

  // Cart management functions
  const addToCart = useCallback((item: CartItem) => {
    setCart(prevCart => {
      const existingItem = prevCart.find(i => i.productId === item.productId);
      if (existingItem) {
        return prevCart.map(i =>
          i.productId === item.productId
            ? { ...i, quantity: i.quantity + item.quantity }
            : i
        );
      }
      return [...prevCart, item];
    });
  }, []);

  const updateCartItem = useCallback((productId: string, quantity: number) => {
    if (quantity <= 0) {
      removeFromCart(productId);
      return;
    }
    setCart(prevCart =>
      prevCart.map(item =>
        item.productId === productId
          ? { ...item, quantity }
          : item
      )
    );
  }, []);

  const removeFromCart = useCallback((productId: string) => {
    setCart(prevCart => prevCart.filter(item => item.productId !== productId));
  }, []);

  const clearCart = useCallback(() => {
    setCart([]);
  }, []);

  // Calculate cart totals
  const cartTotal = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
  const cartItemCount = cart.reduce((sum, item) => sum + item.quantity, 0);

  // Initialize session
  const initializeSession = useCallback((customer: Customer | undefined, language: string) => {
    const newSessionId = `kiosk-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    setSessionId(newSessionId);
    setCustomer(customer || null);
    setIsGuest(!customer);
    setLanguage(language);
    setCurrentScreen('browse');
  }, []);

  // Context value
  const contextValue: KioskContextValue = {
    language,
    setLanguage,
    customer,
    setCustomer,
    isGuest,
    setIsGuest,
    cart,
    addToCart,
    updateCartItem,
    removeFromCart,
    clearCart,
    cartTotal,
    cartItemCount,
    sessionId,
    setSessionId,
    initializeSession,
    recommendations,
    setRecommendations,
    showChat,
    setShowChat,
    currentScreen,
    setCurrentScreen,
  };

  return (
    <KioskContext.Provider value={contextValue}>
      {children}
    </KioskContext.Provider>
  );
};