# Comprehensive React + Vite E-Commerce Web Application Build Specification

## Project Overview
Build a production-ready, multi-template e-commerce web application using React + Vite for the Canadian cannabis retail market, with Ontario as the flagship province. The application must be fully integrated with existing API endpoints, support multiple languages, and prioritize chat-first user experience with voice capabilities.

## Core Requirements

### 1. Technical Foundation
```
Framework: React 18+ with TypeScript
Build Tool: Vite (latest version)
State Management: Redux Toolkit / Zustand
Routing: React Router v6
API Client: Axios with interceptors
Authentication: JWT with refresh token rotation
Styling: Tailwind CSS + CSS Modules
UI Components: Radix UI / Headless UI for accessibility
Deployment: Vercel/Netlify with CDN
PWA: Vite PWA Plugin for offline support
```

### 2. Project Structure
```
weedgo-commerce/
├── src/
│   ├── api/              # API client and endpoints
│   ├── assets/           # Static assets
│   ├── components/       # Reusable components
│   │   ├── common/       # Shared components
│   │   ├── templates/    # Template-specific components
│   │   └── ui/           # UI primitives
│   ├── contexts/         # React contexts
│   ├── features/         # Feature modules
│   │   ├── auth/
│   │   ├── cart/
│   │   ├── chat/
│   │   ├── checkout/
│   │   ├── products/
│   │   └── delivery/
│   ├── hooks/            # Custom React hooks
│   ├── layouts/          # Layout components
│   ├── locales/          # i18n translations
│   ├── pages/            # Route pages
│   ├── services/         # Business logic services
│   ├── store/            # Redux store
│   ├── styles/           # Global styles
│   ├── templates/        # Template definitions
│   ├── types/            # TypeScript types
│   └── utils/            # Utility functions
├── public/               # Public assets
├── .env.example          # Environment variables template
├── index.html            # Entry HTML
├── vite.config.ts        # Vite configuration
├── tsconfig.json         # TypeScript configuration
├── tailwind.config.js    # Tailwind configuration
└── package.json
```

### 3. Environment Configuration
```typescript
// .env
VITE_TENANT_ID=your_tenant_id
VITE_API_BASE_URL=http://localhost:5024
VITE_WS_BASE_URL=ws://localhost:5024
VITE_STORE_ID=store_uuid
VITE_TEMPLATE=modern
VITE_DEFAULT_LOCALE=en
VITE_STRIPE_PUBLISHABLE_KEY=pk_test_xxx
VITE_CLOVER_APP_ID=xxx
VITE_CDN_URL=https://cdn.weedgo.ca
```

```typescript
// vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { VitePWA } from 'vite-plugin-pwa';
import path from 'path';

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.ico', 'robots.txt', 'apple-touch-icon.png'],
      manifest: {
        name: 'WeedGo Commerce',
        short_name: 'WeedGo',
        theme_color: '#2E7D32',
        background_color: '#ffffff',
        display: 'standalone',
        scope: '/',
        start_url: '/',
      }
    })
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@components': path.resolve(__dirname, './src/components'),
      '@features': path.resolve(__dirname, './src/features'),
      '@templates': path.resolve(__dirname, './src/templates'),
    }
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: process.env.VITE_API_BASE_URL,
        changeOrigin: true,
      }
    }
  }
});
```

## API Endpoints Integration

### Authentication & User Management
```typescript
POST   /api/auth/register
POST   /api/auth/login
POST   /api/auth/refresh
POST   /api/auth/logout
GET    /api/auth/me
PUT    /api/auth/profile
POST   /api/auth/verify-email
POST   /api/auth/reset-password
POST   /api/auth/change-password
```

### Product Catalog & Search
```typescript
GET    /api/kiosk/products/browse?store_id={id}&category={cat}&limit={n}&offset={n}
GET    /api/kiosk/products/{sku}
GET    /api/kiosk/categories
GET    /api/kiosk/brands
POST   /api/chat/search
GET    /api/inventory/products/search?q={query}&category={cat}&brand={brand}
GET    /api/store-inventory/list?search={q}&category={c}&low_stock={bool}
```

### Shopping Cart & Orders
```typescript
POST   /api/orders/create
GET    /api/orders/list
GET    /api/orders/{order_id}
PUT    /api/orders/{order_id}/status
POST   /api/orders/{order_id}/cancel
GET    /api/orders/{order_id}/track
POST   /api/cart/add
PUT    /api/cart/update
DELETE /api/cart/remove
GET    /api/cart
POST   /api/cart/clear
```

### Store Management
```typescript
GET    /api/stores/list
GET    /api/stores/{store_id}
GET    /api/stores/{store_id}/hours
GET    /api/stores/{store_id}/inventory
GET    /api/stores/nearest?lat={lat}&lng={lng}
GET    /api/store-settings/{store_id}
```

### Payment Processing
```typescript
POST   /api/payments/process
POST   /api/payments/clover/initialize
POST   /api/payments/clover/capture
GET    /api/payments/methods
POST   /api/payments/tokenize
GET    /api/payments/{payment_id}/status
```

### Chat & AI Assistant
```typescript
POST   /api/chat/message
GET    /api/chat/history
POST   /api/chat/voice/transcribe
POST   /api/chat/voice/synthesize
WS     /ws/chat/stream
POST   /api/chat/context
GET    /api/chat/suggestions
```

### Delivery & Tracking
```typescript
POST   /api/delivery/calculate
POST   /api/delivery/schedule
GET    /api/delivery/track/{tracking_id}
GET    /api/delivery/zones
PUT    /api/delivery/{delivery_id}/update
```

## Template System Architecture

### Base Template Interface
```typescript
// src/templates/types.ts
export interface ITemplate {
  name: string;
  theme: ITheme;
  layout: ILayout;
  components: IComponentMap;
  animations: IAnimationConfig;
  typography: ITypography;
}

export interface ITheme {
  colors: {
    primary: string;
    secondary: string;
    accent: string;
    background: string;
    surface: string;
    text: string;
    error: string;
    success: string;
    warning: string;
  };
  spacing: Record<string, string>;
  borderRadius: Record<string, string>;
  shadows: Record<string, string>;
}

export interface IComponentMap {
  ProductCard: React.FC<IProductCardProps>;
  CartItem: React.FC<ICartItemProps>;
  ChatBubble: React.FC<IChatBubbleProps>;
  Button: React.FC<IButtonProps>;
  Input: React.FC<IInputProps>;
  Modal: React.FC<IModalProps>;
}
```

### Template Provider
```typescript
// src/templates/TemplateProvider.tsx
import React, { createContext, useContext, useMemo } from 'react';
import { PotPalaceTemplate } from './pot-palace';
import { ModernTemplate } from './modern';
import { HeadlessTemplate } from './headless';

const TemplateContext = createContext<ITemplate | null>(null);

export const TemplateProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const templateName = import.meta.env.VITE_TEMPLATE || 'modern';

  const template = useMemo(() => {
    switch (templateName) {
      case 'pot-palace':
        return PotPalaceTemplate;
      case 'headless':
        return HeadlessTemplate;
      default:
        return ModernTemplate;
    }
  }, [templateName]);

  return (
    <TemplateContext.Provider value={template}>
      <div className={`template-${template.name}`}>
        {children}
      </div>
    </TemplateContext.Provider>
  );
};

export const useTemplate = () => {
  const context = useContext(TemplateContext);
  if (!context) throw new Error('useTemplate must be used within TemplateProvider');
  return context;
};
```

### Template Implementations

#### 1. Pot Palace Template
```typescript
// src/templates/pot-palace/index.ts
export const PotPalaceTemplate: ITemplate = {
  name: 'pot-palace',
  theme: {
    colors: {
      primary: '#2E7D32',      // Deep Green
      secondary: '#FDD835',     // Golden Yellow
      accent: '#8B4513',        // Saddle Brown
      background: '#FFF8E1',    // Cream
      surface: '#FFFFFF',
      text: '#212121',
      error: '#D32F2F',
      success: '#388E3C',
      warning: '#F57C00'
    }
  },
  components: {
    ProductCard: PotPalaceProductCard,
    Button: PotPalaceButton,
    // Playful animations, rounded corners, cannabis leaf decorations
  }
};
```

#### 2. Modern Template
```typescript
// src/templates/modern/index.ts
export const ModernTemplate: ITemplate = {
  name: 'modern',
  theme: {
    colors: {
      primary: '#1A237E',      // Indigo
      secondary: '#00BCD4',     // Cyan
      accent: '#FF4081',        // Pink Accent
      background: '#FAFAFA',
      surface: '#FFFFFF',
      text: '#263238',
      error: '#F44336',
      success: '#4CAF50',
      warning: '#FF9800'
    }
  },
  components: {
    ProductCard: ModernProductCard,
    Button: ModernButton,
    // Clean lines, minimal design, subtle animations
  }
};
```

#### 3. Headless Template
```typescript
// src/templates/headless/index.ts
export const HeadlessTemplate: ITemplate = {
  name: 'headless',
  theme: {
    // CSS variables for complete customization
    cssVariables: true
  },
  components: {
    // Unstyled components with semantic HTML
    ProductCard: HeadlessProductCard,
    Button: HeadlessButton,
  }
};
```

## Core Features Implementation

### 1. API Client Setup
```typescript
// src/api/client.ts
import axios from 'axios';
import { toast } from 'react-hot-toast';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  }
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    const storeId = localStorage.getItem('store_id') || import.meta.env.VITE_STORE_ID;
    if (storeId) {
      config.headers['X-Store-ID'] = storeId;
    }

    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Try to refresh token
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const { data } = await axios.post(`${import.meta.env.VITE_API_BASE_URL}/api/auth/refresh`, {
            refresh: refreshToken
          });

          localStorage.setItem('access_token', data.access);
          localStorage.setItem('refresh_token', data.refresh);

          // Retry original request
          error.config.headers.Authorization = `Bearer ${data.access}`;
          return apiClient(error.config);
        } catch (refreshError) {
          // Redirect to login
          window.location.href = '/login';
        }
      }
    }

    // Show error message
    const message = error.response?.data?.detail || 'An error occurred';
    toast.error(message);

    return Promise.reject(error);
  }
);

export default apiClient;
```

### 2. Chat-First Design Implementation
```typescript
// src/features/chat/ChatWidget.tsx
import React, { useState, useEffect, useRef } from 'react';
import { useChat } from '@/hooks/useChat';
import { useVoice } from '@/hooks/useVoice';
import { ChatBubble } from './ChatBubble';
import { VoiceButton } from './VoiceButton';
import { motion, AnimatePresence } from 'framer-motion';

export const ChatWidget: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState('');
  const { messages, sendMessage, isTyping } = useChat();
  const { isListening, startListening, stopListening, transcript } = useVoice();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Update input with voice transcript
  useEffect(() => {
    if (transcript) {
      setInput(transcript);
    }
  }, [transcript]);

  const handleSend = () => {
    if (input.trim()) {
      sendMessage(input);
      setInput('');
    }
  };

  return (
    <>
      {/* Floating Chat Button */}
      <motion.button
        className="fixed bottom-6 right-6 w-16 h-16 bg-primary-500 rounded-full shadow-lg flex items-center justify-center z-50"
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        onClick={() => setIsOpen(!isOpen)}
      >
        <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
        </svg>
      </motion.button>

      {/* Chat Window */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 100 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 100 }}
            className="fixed bottom-24 right-6 w-96 h-[600px] bg-white rounded-2xl shadow-2xl z-50 flex flex-col"
          >
            {/* Header */}
            <div className="bg-primary-500 text-white p-4 rounded-t-2xl flex justify-between items-center">
              <h3 className="text-lg font-semibold">WeedGo Assistant</h3>
              <button onClick={() => setIsOpen(false)}>
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.map((msg, idx) => (
                <ChatBubble key={idx} message={msg} />
              ))}
              {isTyping && (
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100" />
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200" />
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="p-4 border-t">
              <div className="flex items-center space-x-2">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                  placeholder="Type a message..."
                  className="flex-1 px-4 py-2 border rounded-full focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
                <VoiceButton
                  isListening={isListening}
                  onStart={startListening}
                  onStop={stopListening}
                />
                <button
                  onClick={handleSend}
                  className="p-2 bg-primary-500 text-white rounded-full hover:bg-primary-600"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                  </svg>
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};
```

### 3. Voice Integration Hook
```typescript
// src/hooks/useVoice.ts
import { useState, useEffect, useRef } from 'react';

export const useVoice = () => {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [isSupported, setIsSupported] = useState(false);
  const recognition = useRef<SpeechRecognition | null>(null);

  useEffect(() => {
    // Check browser support
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      setIsSupported(true);
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognition.current = new SpeechRecognition();

      recognition.current.continuous = true;
      recognition.current.interimResults = true;
      recognition.current.lang = localStorage.getItem('locale') || 'en-US';

      recognition.current.onresult = (event) => {
        const last = event.results.length - 1;
        const text = event.results[last][0].transcript;
        setTranscript(text);
      };

      recognition.current.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        setIsListening(false);
      };

      recognition.current.onend = () => {
        setIsListening(false);
      };
    }

    return () => {
      if (recognition.current) {
        recognition.current.stop();
      }
    };
  }, []);

  const startListening = () => {
    if (recognition.current && !isListening) {
      recognition.current.start();
      setIsListening(true);
      setTranscript('');
    }
  };

  const stopListening = () => {
    if (recognition.current && isListening) {
      recognition.current.stop();
      setIsListening(false);
    }
  };

  const speak = (text: string) => {
    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = localStorage.getItem('locale') || 'en-US';
      utterance.rate = 1.0;
      utterance.pitch = 1.0;
      speechSynthesis.speak(utterance);
    }
  };

  return {
    isListening,
    transcript,
    isSupported,
    startListening,
    stopListening,
    speak
  };
};
```

### 4. Multi-lingual Support
```typescript
// src/i18n/config.ts
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

// Import translations
import enTranslations from './locales/en.json';
import frTranslations from './locales/fr.json';
import esTranslations from './locales/es.json';
import ptTranslations from './locales/pt.json';
import zhTranslations from './locales/zh.json';
import arTranslations from './locales/ar.json';

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      en: { translation: enTranslations },
      fr: { translation: frTranslations },
      es: { translation: esTranslations },
      pt: { translation: ptTranslations },
      zh: { translation: zhTranslations },
      ar: { translation: arTranslations }
    },
    fallbackLng: 'en',
    debug: import.meta.env.DEV,
    interpolation: {
      escapeValue: false
    },
    detection: {
      order: ['localStorage', 'navigator', 'htmlTag'],
      caches: ['localStorage']
    }
  });

export default i18n;
```

### 5. Payment Integration - Clover
```typescript
// src/services/payment/clover.ts
import { loadScript } from '@/utils/loadScript';

export class CloverPaymentService {
  private cloverInstance: any;
  private merchantId: string;
  private publicKey: string;

  constructor() {
    this.merchantId = import.meta.env.VITE_CLOVER_MERCHANT_ID;
    this.publicKey = import.meta.env.VITE_CLOVER_PUBLIC_KEY;
  }

  async initialize() {
    // Load Clover SDK
    await loadScript('https://checkout.sandbox.dev.clover.com/sdk.js');

    this.cloverInstance = new window.Clover(this.publicKey);

    const elements = this.cloverInstance.elements();
    return elements;
  }

  async createCardElement(elements: any) {
    const cardNumber = elements.create('CARD_NUMBER');
    const cardDate = elements.create('CARD_DATE');
    const cardCvv = elements.create('CARD_CVV');
    const cardZip = elements.create('CARD_ZIP');

    return {
      cardNumber,
      cardDate,
      cardCvv,
      cardZip
    };
  }

  async tokenizeCard(cardElement: any) {
    try {
      const result = await this.cloverInstance.createToken();
      return result.token;
    } catch (error) {
      console.error('Tokenization error:', error);
      throw error;
    }
  }

  async processPayment(token: string, amount: number, orderId: string) {
    const response = await apiClient.post('/api/payments/clover/process', {
      token,
      amount: Math.round(amount * 100), // Convert to cents
      orderId,
      merchantId: this.merchantId
    });

    return response.data;
  }
}
```

### 6. Real-time Order Tracking
```typescript
// src/features/delivery/TrackingMap.tsx
import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Polyline } from 'react-leaflet';
import { useWebSocket } from '@/hooks/useWebSocket';

interface TrackingData {
  orderId: string;
  status: string;
  driver: {
    name: string;
    phone: string;
    location: {
      lat: number;
      lng: number;
    };
  };
  estimatedTime: number;
  route: Array<[number, number]>;
}

export const TrackingMap: React.FC<{ orderId: string }> = ({ orderId }) => {
  const [trackingData, setTrackingData] = useState<TrackingData | null>(null);
  const { sendMessage, lastMessage } = useWebSocket(
    `${import.meta.env.VITE_WS_BASE_URL}/tracking/${orderId}`
  );

  useEffect(() => {
    if (lastMessage) {
      const data = JSON.parse(lastMessage.data);
      setTrackingData(data);

      // Show notification
      if ('Notification' in window && Notification.permission === 'granted') {
        new Notification('Delivery Update', {
          body: `Your order is ${data.status}`,
          icon: '/logo.png'
        });
      }
    }
  }, [lastMessage]);

  if (!trackingData) {
    return <div>Loading tracking information...</div>;
  }

  return (
    <div className="relative h-[500px]">
      <MapContainer
        center={[trackingData.driver.location.lat, trackingData.driver.location.lng]}
        zoom={13}
        className="h-full w-full"
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        />

        <Marker position={[trackingData.driver.location.lat, trackingData.driver.location.lng]}>
          {/* Driver icon */}
        </Marker>

        {trackingData.route && (
          <Polyline positions={trackingData.route} color="blue" />
        )}
      </MapContainer>

      {/* Status Card */}
      <div className="absolute bottom-4 left-4 right-4 bg-white rounded-lg shadow-lg p-4">
        <div className="flex justify-between items-center">
          <div>
            <h3 className="font-semibold">{trackingData.status}</h3>
            <p className="text-sm text-gray-600">
              Driver: {trackingData.driver.name}
            </p>
            <p className="text-sm text-gray-600">
              ETA: {trackingData.estimatedTime} minutes
            </p>
          </div>
          <a
            href={`tel:${trackingData.driver.phone}`}
            className="px-4 py-2 bg-primary-500 text-white rounded-lg"
          >
            Call Driver
          </a>
        </div>
      </div>
    </div>
  );
};
```

## Redux Store Configuration

```typescript
// src/store/index.ts
import { configureStore } from '@reduxjs/toolkit';
import { setupListeners } from '@reduxjs/toolkit/query';
import authSlice from '@/features/auth/authSlice';
import cartSlice from '@/features/cart/cartSlice';
import productsSlice from '@/features/products/productsSlice';
import chatSlice from '@/features/chat/chatSlice';
import deliverySlice from '@/features/delivery/deliverySlice';
import { api } from '@/services/api';

export const store = configureStore({
  reducer: {
    auth: authSlice,
    cart: cartSlice,
    products: productsSlice,
    chat: chatSlice,
    delivery: deliverySlice,
    [api.reducerPath]: api.reducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['chat/messageReceived'],
      },
    }).concat(api.middleware),
});

setupListeners(store.dispatch);

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
```

## Performance Optimizations

### 1. Code Splitting & Lazy Loading
```typescript
// src/App.tsx
import React, { Suspense, lazy } from 'react';
import { Routes, Route } from 'react-router-dom';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

// Lazy load pages
const Home = lazy(() => import('@/pages/Home'));
const Products = lazy(() => import('@/pages/Products'));
const ProductDetail = lazy(() => import('@/pages/ProductDetail'));
const Cart = lazy(() => import('@/pages/Cart'));
const Checkout = lazy(() => import('@/pages/Checkout'));
const Profile = lazy(() => import('@/pages/Profile'));
const OrderTracking = lazy(() => import('@/pages/OrderTracking'));

export const App: React.FC = () => {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/products" element={<Products />} />
        <Route path="/products/:sku" element={<ProductDetail />} />
        <Route path="/cart" element={<Cart />} />
        <Route path="/checkout" element={<Checkout />} />
        <Route path="/profile" element={<Profile />} />
        <Route path="/track/:orderId" element={<OrderTracking />} />
      </Routes>
    </Suspense>
  );
};
```

### 2. Image Optimization
```typescript
// src/components/ui/OptimizedImage.tsx
import React, { useState } from 'react';
import { LazyLoadImage } from 'react-lazy-load-image-component';
import 'react-lazy-load-image-component/src/effects/blur.css';

interface OptimizedImageProps {
  src: string;
  alt: string;
  className?: string;
  width?: number;
  height?: number;
}

export const OptimizedImage: React.FC<OptimizedImageProps> = ({
  src,
  alt,
  className,
  width,
  height
}) => {
  const [error, setError] = useState(false);

  // Generate CDN URL with optimization parameters
  const optimizedSrc = `${import.meta.env.VITE_CDN_URL}/optimize?url=${encodeURIComponent(src)}&w=${width || 'auto'}&q=80&format=webp`;

  if (error) {
    return (
      <div className={`bg-gray-200 flex items-center justify-center ${className}`}>
        <span className="text-gray-400">Image not available</span>
      </div>
    );
  }

  return (
    <LazyLoadImage
      src={optimizedSrc}
      alt={alt}
      effect="blur"
      className={className}
      onError={() => setError(true)}
      width={width}
      height={height}
    />
  );
};
```

### 3. Service Worker & PWA
```typescript
// src/service-worker.ts
import { precacheAndRoute } from 'workbox-precaching';
import { registerRoute } from 'workbox-routing';
import { StaleWhileRevalidate, CacheFirst } from 'workbox-strategies';
import { CacheableResponsePlugin } from 'workbox-cacheable-response';
import { ExpirationPlugin } from 'workbox-expiration';

// Precache all static assets
precacheAndRoute(self.__WB_MANIFEST);

// Cache API responses
registerRoute(
  ({ url }) => url.pathname.startsWith('/api/products'),
  new StaleWhileRevalidate({
    cacheName: 'api-cache',
    plugins: [
      new CacheableResponsePlugin({
        statuses: [0, 200],
      }),
      new ExpirationPlugin({
        maxEntries: 100,
        maxAgeSeconds: 60 * 60 * 24, // 1 day
      }),
    ],
  })
);

// Cache images
registerRoute(
  ({ request }) => request.destination === 'image',
  new CacheFirst({
    cacheName: 'images',
    plugins: [
      new ExpirationPlugin({
        maxEntries: 60,
        maxAgeSeconds: 30 * 24 * 60 * 60, // 30 days
      }),
    ],
  })
);
```

## Security Implementation

### 1. Authentication Guard
```typescript
// src/components/auth/ProtectedRoute.tsx
import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requireVerified?: boolean;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requireVerified = false
}) => {
  const { isAuthenticated, user, isLoading } = useAuth();

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (requireVerified && !user?.emailVerified) {
    return <Navigate to="/verify-email" replace />;
  }

  // Age verification for cannabis
  if (!user?.ageVerified) {
    return <Navigate to="/age-verification" replace />;
  }

  return <>{children}</>;
};
```

### 2. Input Validation
```typescript
// src/utils/validation.ts
import { z } from 'zod';

export const schemas = {
  email: z.string().email('Invalid email address'),
  phone: z.string().regex(/^\+?[1-9]\d{1,14}$/, 'Invalid phone number'),
  canadianPostalCode: z.string().regex(
    /^[A-Za-z]\d[A-Za-z][ -]?\d[A-Za-z]\d$/,
    'Invalid Canadian postal code'
  ),
  age: z.number().min(19, 'Must be 19 or older to purchase cannabis in Ontario'),
  password: z.string()
    .min(8, 'Password must be at least 8 characters')
    .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
    .regex(/[a-z]/, 'Password must contain at least one lowercase letter')
    .regex(/[0-9]/, 'Password must contain at least one number'),
};

export const validateForm = <T>(schema: z.ZodSchema<T>, data: unknown): T => {
  return schema.parse(data);
};
```

## Testing Strategy

### Unit Tests
```typescript
// src/__tests__/components/ProductCard.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { Provider } from 'react-redux';
import { store } from '@/store';
import { ProductCard } from '@/components/ProductCard';

describe('ProductCard', () => {
  const mockProduct = {
    id: '1',
    sku: 'TEST-SKU',
    name: 'Test Product',
    price: 29.99,
    thc_content: 20,
    cbd_content: 0.5,
    image_url: 'https://example.com/image.jpg'
  };

  it('renders product information correctly', () => {
    render(
      <Provider store={store}>
        <ProductCard product={mockProduct} />
      </Provider>
    );

    expect(screen.getByText('Test Product')).toBeInTheDocument();
    expect(screen.getByText('$29.99')).toBeInTheDocument();
    expect(screen.getByText('THC: 20%')).toBeInTheDocument();
  });

  it('adds product to cart when button clicked', () => {
    const { getByRole } = render(
      <Provider store={store}>
        <ProductCard product={mockProduct} />
      </Provider>
    );

    const addButton = getByRole('button', { name: /add to cart/i });
    fireEvent.click(addButton);

    // Check if product was added to store
    const state = store.getState();
    expect(state.cart.items).toHaveLength(1);
  });
});
```

### E2E Tests with Playwright
```typescript
// e2e/checkout.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Checkout Flow', () => {
  test('completes purchase successfully', async ({ page }) => {
    // Navigate to store
    await page.goto('http://localhost:3000');

    // Search for product
    await page.fill('[data-testid="search-input"]', 'Blue Dream');
    await page.press('[data-testid="search-input"]', 'Enter');

    // Add to cart
    await page.click('[data-testid="product-card"]:first-child [data-testid="add-to-cart"]');

    // Go to cart
    await page.click('[data-testid="cart-button"]');

    // Proceed to checkout
    await page.click('[data-testid="checkout-button"]');

    // Fill delivery information
    await page.fill('[name="address"]', '123 Main St');
    await page.fill('[name="city"]', 'Toronto');
    await page.fill('[name="postalCode"]', 'M5V 3A8');

    // Select payment method
    await page.click('[data-testid="payment-clover"]');

    // Complete payment
    await page.click('[data-testid="place-order"]');

    // Verify success
    await expect(page.locator('[data-testid="order-confirmation"]')).toBeVisible();
  });
});
```

## Deployment Configuration

### 1. Docker Setup
```dockerfile
# Dockerfile
FROM node:18-alpine as builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### 2. CI/CD with GitHub Actions
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: 18
          cache: 'npm'

      - run: npm ci
      - run: npm run test
      - run: npm run test:e2e

  build-and-deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build Docker image
        run: docker build -t weedgo-commerce:${{ github.sha }} .

      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v20
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          vercel-args: '--prod'
```

## Implementation Phases

### Phase 1: Foundation (Days 1-5)
- [ ] Initialize Vite + React + TypeScript project
- [ ] Setup Tailwind CSS and component library
- [ ] Configure environment variables
- [ ] Implement authentication flow
- [ ] Setup Redux Toolkit store
- [ ] Create API client with interceptors
- [ ] Setup i18n for multi-language support

### Phase 2: Core Features (Days 6-10)
- [ ] Implement template system architecture
- [ ] Create base components for all templates
- [ ] Build product browsing and search
- [ ] Implement shopping cart functionality
- [ ] Create user profile management
- [ ] Add store selection and hours display

### Phase 3: Chat & Voice (Days 11-15)
- [ ] Implement chat interface
- [ ] Add WebSocket connection for real-time chat
- [ ] Integrate Web Speech API for voice
- [ ] Create chat context and AI responses
- [ ] Add product recommendations in chat
- [ ] Implement voice commands

### Phase 4: Checkout & Payment (Days 16-20)
- [ ] Build checkout flow
- [ ] Integrate Clover payment SDK
- [ ] Add address validation
- [ ] Implement delivery scheduling
- [ ] Create order confirmation
- [ ] Add email/SMS notifications

### Phase 5: Templates & Polish (Days 21-25)
- [ ] Complete Pot Palace template
- [ ] Complete Modern template
- [ ] Complete Headless template
- [ ] Add animations and transitions
- [ ] Implement dark mode support
- [ ] Optimize performance

### Phase 6: Testing & Deployment (Days 26-30)
- [ ] Write unit tests (>80% coverage)
- [ ] Create E2E test suite
- [ ] Performance optimization
- [ ] Security audit
- [ ] Setup CI/CD pipeline
- [ ] Deploy to production

## Performance Metrics
- First Contentful Paint: < 1.5s
- Time to Interactive: < 3s
- Lighthouse Score: > 90
- Bundle Size: < 200KB (initial)
- API Response Time: < 200ms
- WebSocket Latency: < 100ms

## Success Criteria
- All API endpoints fully integrated
- No mock data used
- Voice commands work in all supported languages
- Payment processing functional
- Real-time order tracking working
- PWA installable on mobile devices
- Accessibility WCAG 2.1 AA compliant
- All three templates fully functional

This specification provides a complete roadmap for building a production-ready React + Vite e-commerce web application for the Canadian cannabis market.