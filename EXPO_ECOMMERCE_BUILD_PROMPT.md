# Comprehensive Expo E-Commerce Web Application Build Specification

## Project Overview
Build a production-ready, multi-template e-commerce web application using Expo for the Canadian cannabis retail market, with Ontario as the flagship province. The application must be fully integrated with existing API endpoints, support multiple languages, and prioritize chat-first user experience with voice capabilities.

## Core Requirements

### 1. Technical Foundation
```
Framework: Expo (latest version)
Platform: Web-first with responsive design
State Management: Redux Toolkit or Zustand
API Client: Axios with interceptors
Authentication: JWT with refresh token rotation
Styling: Tailwind CSS or NativeWind
Build Tool: Expo EAS Build
Deployment: Vercel/Netlify with CDN
```

### 2. Environment Configuration
```javascript
// app.config.js
export default {
  expo: {
    name: process.env.APP_NAME || "WeedGo Commerce",
    slug: "weedgo-commerce",
    version: "1.0.0",
    web: {
      bundler: "metro",
      favicon: "./assets/favicon.png"
    },
    extra: {
      TENANT_ID: process.env.TENANT_ID,
      API_BASE_URL: process.env.API_BASE_URL || "http://localhost:5024",
      STORE_ID: process.env.STORE_ID,
      TEMPLATE: process.env.TEMPLATE || "modern",
      LOCALE: process.env.DEFAULT_LOCALE || "en",
      STRIPE_PUBLISHABLE_KEY: process.env.STRIPE_PUBLISHABLE_KEY,
      CLOVER_APP_ID: process.env.CLOVER_APP_ID
    }
  }
};
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

### User Addresses & Profiles
```typescript
GET    /api/profile/addresses
POST   /api/profile/addresses
PUT    /api/profile/addresses/{id}
DELETE /api/profile/addresses/{id}
GET    /api/profile/preferences
PUT    /api/profile/preferences
GET    /api/profile/orders
GET    /api/profile/favorites
POST   /api/profile/favorites
```

## Template System Architecture

### Base Template Interface
```typescript
interface ITemplate {
  name: string;
  theme: ITheme;
  layout: ILayout;
  components: IComponentMap;
  animations: IAnimationConfig;
  typography: ITypography;
}

interface ITheme {
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
  spacing: Record<string, number>;
  borderRadius: Record<string, number>;
  shadows: Record<string, string>;
}

interface ILayout {
  header: IHeaderConfig;
  navigation: INavigationConfig;
  footer: IFooterConfig;
  grid: IGridConfig;
  breakpoints: IBreakpoints;
}

interface IComponentMap {
  ProductCard: React.FC<IProductCardProps>;
  CartItem: React.FC<ICartItemProps>;
  ChatBubble: React.FC<IChatBubbleProps>;
  Button: React.FC<IButtonProps>;
  Input: React.FC<IInputProps>;
  Modal: React.FC<IModalProps>;
  // ... other components
}
```

### Template Implementations

#### 1. Pot Palace Template
```typescript
const PotPalaceTemplate: ITemplate = {
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
    },
    typography: {
      fontFamily: 'Quicksand',
      headerFont: 'Righteous',
      sizes: {
        xs: 12,
        sm: 14,
        md: 16,
        lg: 20,
        xl: 24,
        xxl: 32
      }
    }
  },
  components: {
    ProductCard: PotPalaceProductCard,
    // Playful, rounded corners, leaf icons, animated hover effects
  }
};
```

#### 2. Modern Template
```typescript
const ModernTemplate: ITemplate = {
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
    },
    typography: {
      fontFamily: 'Inter',
      headerFont: 'Poppins',
      minimalist: true
    }
  },
  components: {
    ProductCard: ModernProductCard,
    // Clean lines, card-based, material design inspired
  }
};
```

#### 3. Headless Template
```typescript
const HeadlessTemplate: ITemplate = {
  name: 'headless',
  theme: {
    // Fully customizable via CSS variables
    cssVariables: true,
    inherit: true
  },
  components: {
    // Unstyled base components with semantic HTML
    ProductCard: HeadlessProductCard,
  }
};
```

## Core Features Implementation

### 1. Chat-First Design
```typescript
interface IChatSystem {
  // Main chat interface always accessible
  position: 'bottom-right' | 'fullscreen' | 'sidebar';
  features: {
    voiceInput: boolean;
    voiceOutput: boolean;
    contextAware: boolean;
    productSearch: boolean;
    orderTracking: boolean;
    recommendations: boolean;
  };

  // Implementation
  useChatBot: () => {
    const [messages, setMessages] = useState<IMessage[]>([]);
    const [isListening, setIsListening] = useState(false);
    const recognition = useRef<SpeechRecognition>();
    const synthesis = useRef<SpeechSynthesis>();

    // Voice transcription using Web Speech API
    const startListening = () => {
      recognition.current = new webkitSpeechRecognition();
      recognition.current.continuous = true;
      recognition.current.interimResults = true;
      recognition.current.lang = i18n.language;

      recognition.current.onresult = (event) => {
        const transcript = Array.from(event.results)
          .map(result => result[0].transcript)
          .join('');

        sendMessage(transcript);
      };

      recognition.current.start();
    };

    // Text-to-speech response
    const speak = (text: string) => {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = i18n.language;
      synthesis.current?.speak(utterance);
    };

    return { messages, sendMessage, startListening, speak };
  };
}
```

### 2. Seamless Authentication
```typescript
interface IAuthFlow {
  methods: ['email', 'phone', 'social', 'biometric'];

  // Phone number auth with OTP
  phoneAuth: async (phoneNumber: string) => {
    await api.post('/api/auth/send-otp', { phone: phoneNumber });
    // Auto-advance to OTP input
  };

  // Biometric for returning users
  biometricAuth: async () => {
    const credential = await navigator.credentials.get({
      publicKey: challengeFromServer
    });
    return api.post('/api/auth/biometric', { credential });
  };

  // Social login
  socialAuth: async (provider: 'google' | 'apple' | 'facebook') => {
    // OAuth flow implementation
  };
}
```

### 3. Multi-lingual Support
```typescript
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

const resources = {
  en: {
    translation: await import('./locales/en.json'),
  },
  fr: {
    translation: await import('./locales/fr.json'),
  },
  es: {
    translation: await import('./locales/es.json'),
  },
  pt: {
    translation: await import('./locales/pt.json'),
  },
  zh: {
    translation: await import('./locales/zh.json'),
  },
  ar: {
    translation: await import('./locales/ar.json'),
  }
};

i18n.use(initReactI18next).init({
  resources,
  lng: detectUserLanguage(),
  interpolation: {
    escapeValue: false
  },
  react: {
    useSuspense: true
  }
});
```

### 4. Payment Integration - Clover Go
```typescript
interface ICloverPayment {
  initialize: async () => {
    const clover = await loadCloverSDK();
    const merchantInfo = await api.get('/api/payments/clover/merchant');

    return clover.init({
      appId: process.env.CLOVER_APP_ID,
      merchantId: merchantInfo.id,
      environment: process.env.NODE_ENV === 'production' ? 'prod' : 'sandbox'
    });
  };

  processPayment: async (amount: number, orderId: string) => {
    const paymentRequest = {
      amount: Math.round(amount * 100), // Convert to cents
      orderId,
      external_payment_id: generatePaymentId(),
      tender: {
        type: 'CREDIT_CARD'
      }
    };

    // Initialize Clover card reader if physical
    if (isPhysicalStore) {
      const reader = await clover.connectCardReader();
      const card = await reader.readCard();
      paymentRequest.cardDetails = card;
    } else {
      // Use Clover iframe for online payments
      const token = await clover.tokenizeCard(cardElement);
      paymentRequest.token = token;
    }

    return api.post('/api/payments/clover/process', paymentRequest);
  };
}
```

### 5. Delivery Tracking
```typescript
interface IDeliveryTracking {
  trackOrder: (orderId: string) => {
    const [status, setStatus] = useState<IDeliveryStatus>();
    const [location, setLocation] = useState<ILocation>();

    useEffect(() => {
      // WebSocket for real-time updates
      const ws = new WebSocket(`${WS_URL}/track/${orderId}`);

      ws.onmessage = (event) => {
        const update = JSON.parse(event.data);
        setStatus(update.status);
        setLocation(update.location);

        // Push notification
        if ('Notification' in window && Notification.permission === 'granted') {
          new Notification('Delivery Update', {
            body: `Your order is ${update.status}`,
            icon: '/logo.png'
          });
        }
      };

      return () => ws.close();
    }, [orderId]);

    return { status, location, estimatedTime };
  };
}
```

## Component Library Structure

### Product Components
```typescript
// src/components/templates/base/ProductCard.tsx
export interface IProductCardProps {
  product: IProduct;
  onAddToCart: (product: IProduct) => void;
  onQuickView: (product: IProduct) => void;
  template?: ITemplate;
}

export const BaseProductCard: React.FC<IProductCardProps> = ({
  product,
  onAddToCart,
  onQuickView,
  template
}) => {
  const { t } = useTranslation();
  const { speak } = useVoice();

  const handleAddToCart = () => {
    onAddToCart(product);
    speak(t('product.addedToCart', { name: product.name }));
  };

  return (
    <View style={template?.styles?.productCard}>
      <Image source={{ uri: product.image_url }} />
      <Text>{product.name}</Text>
      <Text>{product.thc_content}% THC | {product.cbd_content}% CBD</Text>
      <Text>${product.price}</Text>
      <Button onPress={handleAddToCart}>
        {t('product.addToCart')}
      </Button>
    </View>
  );
};
```

### Chat Components
```typescript
// src/components/chat/ChatInterface.tsx
export const ChatInterface: React.FC = () => {
  const { messages, sendMessage, isListening, startListening } = useChat();
  const [input, setInput] = useState('');

  return (
    <View style={styles.chatContainer}>
      <ScrollView style={styles.messageList}>
        {messages.map((msg, idx) => (
          <ChatMessage key={idx} message={msg} />
        ))}
      </ScrollView>

      <View style={styles.inputContainer}>
        <TextInput
          value={input}
          onChangeText={setInput}
          placeholder={t('chat.typeMessage')}
          onSubmitEditing={() => {
            sendMessage(input);
            setInput('');
          }}
        />

        <TouchableOpacity onPress={startListening}>
          <Icon name={isListening ? 'mic-off' : 'mic'} />
        </TouchableOpacity>
      </View>
    </View>
  );
};
```

## State Management

### Redux Store Structure
```typescript
// src/store/index.ts
export const store = configureStore({
  reducer: {
    auth: authSlice.reducer,
    products: productsSlice.reducer,
    cart: cartSlice.reducer,
    chat: chatSlice.reducer,
    delivery: deliverySlice.reducer,
    ui: uiSlice.reducer,
    preferences: preferencesSlice.reducer
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['chat/messageReceived'],
      },
    }).concat(
      apiMiddleware,
      websocketMiddleware,
      analyticsMiddleware
    )
});
```

### API Middleware
```typescript
// src/middleware/api.ts
const apiMiddleware: Middleware = (store) => (next) => async (action) => {
  if (!action.meta?.api) return next(action);

  const { endpoint, method, data, onSuccess, onError } = action.meta.api;

  try {
    store.dispatch({ type: `${action.type}_PENDING` });

    const response = await api.request({
      url: endpoint,
      method,
      data,
      headers: {
        'X-Store-ID': store.getState().preferences.storeId,
        'Accept-Language': store.getState().preferences.language
      }
    });

    store.dispatch({
      type: `${action.type}_SUCCESS`,
      payload: response.data
    });

    if (onSuccess) onSuccess(response.data);
  } catch (error) {
    store.dispatch({
      type: `${action.type}_FAILURE`,
      error: error.message
    });

    if (onError) onError(error);
  }
};
```

## Performance Optimization

### 1. Code Splitting
```typescript
// Lazy load routes
const Home = lazy(() => import('./screens/Home'));
const Products = lazy(() => import('./screens/Products'));
const Cart = lazy(() => import('./screens/Cart'));
const Checkout = lazy(() => import('./screens/Checkout'));
```

### 2. Image Optimization
```typescript
const OptimizedImage: React.FC<{ src: string; alt: string }> = ({ src, alt }) => {
  const [loaded, setLoaded] = useState(false);

  return (
    <View>
      {!loaded && <Skeleton />}
      <Image
        source={{
          uri: `${CDN_URL}/resize?url=${src}&w=${width}&q=75&format=webp`
        }}
        onLoad={() => setLoaded(true)}
        alt={alt}
      />
    </View>
  );
};
```

### 3. Request Caching
```typescript
const cacheAdapter = setupCache({
  maxAge: 15 * 60 * 1000, // 15 minutes
  exclude: {
    query: false,
    methods: ['post', 'put', 'delete']
  }
});

const api = axios.create({
  adapter: cacheAdapter.adapter
});
```

## Security Implementation

### 1. Authentication
```typescript
// Secure token storage
import * as SecureStore from 'expo-secure-store';

const TokenManager = {
  setTokens: async (access: string, refresh: string) => {
    await SecureStore.setItemAsync('access_token', access);
    await SecureStore.setItemAsync('refresh_token', refresh);
  },

  getAccessToken: async () => {
    return await SecureStore.getItemAsync('access_token');
  },

  refreshToken: async () => {
    const refresh = await SecureStore.getItemAsync('refresh_token');
    const response = await api.post('/api/auth/refresh', { refresh });
    await TokenManager.setTokens(response.data.access, response.data.refresh);
    return response.data.access;
  }
};
```

### 2. Input Validation
```typescript
import { z } from 'zod';

const schemas = {
  email: z.string().email(),
  phone: z.string().regex(/^\+?[1-9]\d{1,14}$/),
  postalCode: z.string().regex(/^[A-Za-z]\d[A-Za-z][ -]?\d[A-Za-z]\d$/),
  age: z.number().min(19, 'Must be 19 or older'), // Ontario legal age
};
```

## Testing Strategy

### Unit Tests
```typescript
// src/__tests__/components/ProductCard.test.tsx
describe('ProductCard', () => {
  it('displays product information correctly', () => {
    const product = mockProduct();
    const { getByText } = render(
      <ProductCard product={product} />
    );

    expect(getByText(product.name)).toBeTruthy();
    expect(getByText(`$${product.price}`)).toBeTruthy();
  });

  it('calls onAddToCart when button pressed', () => {
    const onAddToCart = jest.fn();
    const { getByText } = render(
      <ProductCard product={mockProduct()} onAddToCart={onAddToCart} />
    );

    fireEvent.press(getByText('Add to Cart'));
    expect(onAddToCart).toHaveBeenCalled();
  });
});
```

### E2E Tests
```typescript
// e2e/checkout.test.ts
describe('Checkout Flow', () => {
  it('completes purchase successfully', async () => {
    await device.launchApp();

    // Add product to cart
    await element(by.id('product-card-0')).tap();
    await element(by.text('Add to Cart')).tap();

    // Go to cart
    await element(by.id('cart-icon')).tap();

    // Proceed to checkout
    await element(by.text('Checkout')).tap();

    // Fill delivery info
    await element(by.id('address-input')).typeText('123 Main St');

    // Complete payment
    await element(by.id('pay-button')).tap();

    // Verify success
    await expect(element(by.text('Order Confirmed'))).toBeVisible();
  });
});
```

## Deployment Configuration

### 1. Environment Setup
```bash
# .env.production
EXPO_PUBLIC_API_URL=https://api.weedgo.ca
EXPO_PUBLIC_WS_URL=wss://ws.weedgo.ca
EXPO_PUBLIC_CDN_URL=https://cdn.weedgo.ca
EXPO_PUBLIC_TENANT_ID=${TENANT_ID}
EXPO_PUBLIC_STORE_ID=${STORE_ID}
EXPO_PUBLIC_TEMPLATE=${TEMPLATE}
EXPO_PUBLIC_STRIPE_KEY=${STRIPE_PUBLISHABLE_KEY}
EXPO_PUBLIC_CLOVER_APP_ID=${CLOVER_APP_ID}
```

### 2. Build Configuration
```json
// eas.json
{
  "cli": {
    "version": ">= 3.0.0"
  },
  "build": {
    "production": {
      "web": {
        "buildConfiguration": "production",
        "output": "dist",
        "bundler": "metro"
      },
      "env": {
        "EXPO_PUBLIC_ENV": "production"
      }
    }
  }
}
```

### 3. CI/CD Pipeline
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node
        uses: actions/setup-node@v3
        with:
          node-version: 18

      - name: Install dependencies
        run: npm ci

      - name: Run tests
        run: npm test

      - name: Build web
        run: npx expo export --platform web

      - name: Deploy to Vercel
        uses: vercel/action@v2
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
```

## Implementation Phases

### Phase 1: Foundation (Week 1-2)
- [ ] Setup Expo project with TypeScript
- [ ] Configure environment variables and multi-tenancy
- [ ] Implement authentication flow
- [ ] Setup Redux store and API client
- [ ] Create base template system
- [ ] Implement i18n support

### Phase 2: Core Features (Week 3-4)
- [ ] Product browsing and search
- [ ] Shopping cart functionality
- [ ] User profile management
- [ ] Store selection and hours
- [ ] Basic chat interface
- [ ] Responsive layouts for all templates

### Phase 3: Advanced Features (Week 5-6)
- [ ] Voice integration (transcription & synthesis)
- [ ] Real-time chat with WebSocket
- [ ] Clover payment integration
- [ ] Delivery tracking
- [ ] Push notifications
- [ ] Offline support with cache

### Phase 4: Template Completion (Week 7)
- [ ] Complete Pot Palace template
- [ ] Complete Modern template
- [ ] Complete Headless template
- [ ] Template switching mechanism
- [ ] Custom theming options
- [ ] Accessibility features (WCAG 2.1 AA)

### Phase 5: Optimization & Testing (Week 8)
- [ ] Performance optimization
- [ ] Security audit
- [ ] Unit test coverage >80%
- [ ] E2E test suite
- [ ] Load testing
- [ ] SEO optimization

### Phase 6: Deployment (Week 9)
- [ ] Production environment setup
- [ ] CI/CD pipeline
- [ ] Monitoring and analytics
- [ ] Documentation
- [ ] Launch preparation

## Quality Assurance Checklist

### Performance
- [ ] First Contentful Paint < 1.5s
- [ ] Time to Interactive < 3s
- [ ] Lighthouse score > 90
- [ ] Bundle size < 200KB (initial)

### Accessibility
- [ ] Screen reader compatible
- [ ] Keyboard navigation
- [ ] Color contrast WCAG AA
- [ ] Focus indicators
- [ ] Alt text for images

### Security
- [ ] HTTPS only
- [ ] XSS protection
- [ ] CSRF tokens
- [ ] Input sanitization
- [ ] Rate limiting

### User Experience
- [ ] Mobile responsive
- [ ] Offline functionality
- [ ] Error boundaries
- [ ] Loading states
- [ ] Empty states
- [ ] Success feedback

## Success Metrics
- Page load time < 2 seconds
- Checkout completion rate > 70%
- Chat engagement rate > 50%
- Voice command success rate > 85%
- Customer satisfaction score > 4.5/5
- Zero critical security vulnerabilities
- 99.9% uptime

## Notes for Implementation
1. Always use real API endpoints, no mock data
2. Implement proper error handling with user-friendly messages
3. Ensure all features degrade gracefully
4. Optimize for mobile-first experience
5. Follow React/Expo best practices
6. Implement comprehensive logging
7. Use TypeScript strictly
8. Document all components with JSDoc
9. Maintain consistent code style with ESLint/Prettier
10. Regular commits with meaningful messages

This specification should be followed systematically to build a production-ready, feature-complete e-commerce application for the Canadian cannabis market.