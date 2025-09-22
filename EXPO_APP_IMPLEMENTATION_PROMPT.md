# Comprehensive Implementation Prompt: Multi-Tenant Cannabis E-Commerce Mobile Application

## Project Overview
Build a production-ready, multi-tenant cannabis e-commerce mobile application using Expo (latest SDK 50+) that interfaces exclusively with the AI Engine Service API. The application must be template-based, supporting multiple brand identities while maintaining consistent functionality.

## Core Requirements & Constraints

### Technical Foundation
- **Framework**: Expo SDK 50+ with Expo Router v3
- **Language**: TypeScript (strict mode)
- **State Management**: Zustand with persistence
- **API Client**: Axios with interceptors for auth refresh
- **Styling**: NativeWind (Tailwind for React Native) with theme system
- **Forms**: React Hook Form with Zod validation
- **Chat**: Socket.io client for WebSocket
- **Voice**: Expo Speech & Expo AV for voice features
- **Payment**: Clover Go SDK integration
- **Navigation**: File-based routing with Expo Router

### API Integration Rules
1. **ONLY use documented endpoints** from the AI Engine Service
2. **No mock data** - all features must connect to real API
3. **Environment-based configuration** for tenant_id, API_URL
4. **Automatic token refresh** on 401 responses
5. **Offline queue** for failed requests with retry logic

## Architecture Implementation

### 1. Project Structure
```
/app
  /(auth)
    login.tsx
    register.tsx
    otp-verify.tsx
  /(tabs)
    index.tsx          # Home/Browse
    chat.tsx          # AI Assistant
    cart.tsx          # Shopping Cart
    profile.tsx       # User Profile
  /product/[id].tsx   # Product Detail
  /checkout/
    index.tsx         # Checkout Flow
    payment.tsx       # Payment Selection
    confirmation.tsx  # Order Confirmation
  /orders/[id].tsx    # Order Tracking
  _layout.tsx         # Root Layout

/components
  /templates
    /pot-palace
      Theme.ts
      Components/
    /modern
      Theme.ts
      Components/
    /headless
      Theme.ts
      Components/
  /common
    ProductCard.tsx
    ChatBubble.tsx
    VoiceInput.tsx

/services
  /api
    client.ts         # Axios setup
    auth.ts          # Auth endpoints
    products.ts      # Product endpoints
    cart.ts          # Cart management
    orders.ts        # Order processing
    chat.ts          # WebSocket chat

/stores
  authStore.ts       # Authentication state
  cartStore.ts       # Cart state
  chatStore.ts       # Chat history
  settingsStore.ts   # App settings

/hooks
  useAuth.ts
  useCart.ts
  useVoice.ts
  useChat.ts
  usePayment.ts

/utils
  storage.ts         # Secure storage
  voice.ts          # Voice utilities
  payment.ts        # Clover integration
```

### 2. Template System Implementation

#### Template Interface
```typescript
interface ThemeTemplate {
  id: string;
  name: string;
  colors: ColorScheme;
  typography: Typography;
  spacing: SpacingScale;
  components: ComponentOverrides;
  animations: AnimationConfig;
}

interface ComponentOverrides {
  ProductCard: React.FC<ProductCardProps>;
  CategoryTile: React.FC<CategoryTileProps>;
  ChatInterface: React.FC<ChatInterfaceProps>;
  NavigationBar: React.FC<NavigationProps>;
  // ... other components
}
```

#### Template Configurations

**Pot Palace Template**
- Cannabis-culture inspired design
- Vibrant greens, purples, golds
- Playful animations
- Rounded corners, organic shapes
- Cannabis leaf accents
- Friendly, casual tone in UI copy

**Modern Template**
- Clean, minimal medical aesthetic
- White, grey, accent colors
- Sharp lines, geometric shapes
- Professional typography
- Clinical but approachable
- Focus on product information

**Headless Template**
- Fully customizable base
- System default colors
- Standard components
- Configuration-driven styling
- White-label ready
- No predefined branding

### 3. Feature Implementation Specifications

#### A. Authentication Flow
```typescript
// Seamless registration/login flow
1. Phone number entry (single screen)
2. Auto-detect new vs returning user via API
3. OTP verification (auto-focus, auto-submit on 6 digits)
4. Biometric enrollment prompt (FaceID/TouchID)
5. Store tokens securely in Expo SecureStore
6. Implement silent refresh for expired tokens

API Endpoints:
- POST /api/v1/auth/customer/register
- POST /api/v1/auth/customer/login
- POST /api/v1/auth/otp/verify
- POST /api/v1/auth/refresh
```

#### B. Product Browse & Search
```typescript
// Optimized browsing experience
1. Lazy-loaded product grid with Flashlist
2. Category quick filters (horizontal scroll)
3. Smart search with debouncing
4. Price, THC/CBD filters
5. Add to cart without navigation
6. Quick view modal for product details

API Endpoints:
- GET /api/products/search
- GET /api/products/categories
- GET /api/inventory/store/{storeId}/products
- GET /api/products/{id}/details
```

#### C. AI Chat Assistant (First-Class Feature)
```typescript
// WebSocket-based real-time chat
1. Floating chat bubble on all screens
2. Full-screen chat interface
3. Voice input with Expo.Speech
4. Product recommendations inline
5. Order status queries
6. Dosage calculations
7. Persist chat history locally

Implementation:
- Connect to WebSocket: ws://[API_URL]/chat/ws
- Implement reconnection logic
- Stream responses with typing indicator
- Handle product cards in chat
- Quick actions for common queries
```

#### D. Voice Integration
```typescript
// Native voice features
1. Push-to-talk button in chat
2. Voice search from home screen
3. Voice-activated cart additions
4. Order status voice queries
5. Accessibility voice navigation

Implementation:
- Use Expo.Audio for recording
- Stream audio to /api/voice/transcribe
- Use Expo.Speech for TTS responses
- Implement wake word detection (optional)
- Handle permissions gracefully
```

#### E. Shopping Cart
```typescript
// Persistent cart management
1. Real-time inventory checking
2. Quantity adjustments with +/- buttons
3. Swipe to delete items
4. Promotion code application
5. Running total with taxes
6. Save for later functionality

API Endpoints:
- POST /api/cart/add
- PUT /api/cart/update
- DELETE /api/cart/remove
- GET /api/cart/session/{sessionId}
- POST /api/promotions/apply
```

#### F. Checkout Flow
```typescript
// Streamlined checkout (max 3 taps)
1. Single-page checkout preferred
2. Auto-fill from profile
3. Delivery/pickup toggle
4. Saved payment methods
5. Real-time delivery fee calculation
6. Age verification check

API Endpoints:
- POST /api/orders/create
- POST /api/payment/process
- GET /api/delivery/zones
- POST /api/delivery/calculate-fee
```

#### G. Payment Integration (Clover Go)
```typescript
// Secure payment processing
1. Clover Go SDK integration
2. Card reader pairing flow
3. Tap/chip/swipe support
4. Digital wallet integration
5. Split payment options
6. Receipt via email/SMS

Implementation:
- Initialize Clover SDK with merchant credentials
- Handle reader connection states
- Process payments via /api/payment/clover/process
- Store payment tokens securely
- Implement PCI compliance measures
```

#### H. Order Tracking
```typescript
// Real-time order updates
1. Live order status timeline
2. Delivery driver location (when applicable)
3. Push notifications for status changes
4. Estimated delivery/ready time
5. Contact driver/store options

API Endpoints:
- GET /api/orders/{orderId}/status
- GET /api/delivery/track/{orderId}
- WebSocket subscription for updates
```

#### I. User Profile
```typescript
// Comprehensive profile management
1. Quick edit for delivery addresses
2. Payment method management
3. Order history with reorder
4. Wishlist/favorites
5. Preferences (notifications, language)
6. Medical documentation upload

API Endpoints:
- GET /api/profile
- PUT /api/profile/update
- POST /api/profile/addresses
- GET /api/orders/history
- POST /api/wishlist/add
```

### 4. UX Optimization Requirements

#### Performance
- App launch to browse: <2 seconds
- Search results: <500ms
- Add to cart: Instant with optimistic UI
- Page transitions: <200ms
- Image loading: Progressive with blur placeholders

#### Interaction Patterns
- Single thumb reachability for key actions
- Bottom sheet for quick actions
- Haptic feedback for important actions
- Swipe gestures for navigation
- Pull-to-refresh on all lists
- Skeleton screens during loading

#### Accessibility
- VoiceOver/TalkBack support
- Minimum touch target: 44x44 pts
- Color contrast WCAG AA compliant
- Font scaling support
- Reduce motion options

### 5. State Management Pattern

```typescript
// Zustand store example
interface AuthStore {
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  isLoading: boolean;

  login: (phone: string) => Promise<void>;
  verifyOTP: (code: string) => Promise<void>;
  logout: () => void;
  refreshAuth: () => Promise<void>;
}

// Persist sensitive data securely
const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      // Implementation
    }),
    {
      name: 'auth-storage',
      storage: createSecureStorage(), // Expo SecureStore
    }
  )
);
```

### 6. API Client Configuration

```typescript
// Axios instance with interceptors
const apiClient = axios.create({
  baseURL: process.env.EXPO_PUBLIC_API_URL,
  timeout: 10000,
  headers: {
    'X-Tenant-ID': process.env.EXPO_PUBLIC_TENANT_ID,
    'X-Store-ID': process.env.EXPO_PUBLIC_STORE_ID,
  }
});

// Request interceptor for auth
apiClient.interceptors.request.use(
  async (config) => {
    const token = await SecureStore.getItemAsync('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  }
);

// Response interceptor for token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Implement token refresh logic
      await refreshToken();
      return apiClient.request(error.config);
    }
    return Promise.reject(error);
  }
);
```

### 7. WebSocket Chat Implementation

```typescript
class ChatService {
  private socket: Socket | null = null;
  private reconnectAttempts = 0;

  connect(sessionId: string) {
    this.socket = io(process.env.EXPO_PUBLIC_WS_URL, {
      path: '/chat/ws',
      query: { sessionId },
      transports: ['websocket'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 5,
    });

    this.setupListeners();
  }

  private setupListeners() {
    this.socket?.on('connect', this.onConnect);
    this.socket?.on('message', this.onMessage);
    this.socket?.on('error', this.onError);
    this.socket?.on('disconnect', this.onDisconnect);
  }

  sendMessage(message: string, voice?: boolean) {
    this.socket?.emit('message', {
      type: 'message',
      content: message,
      isVoice: voice,
      timestamp: Date.now(),
    });
  }
}
```

### 8. Testing Requirements

#### Unit Tests
- Component rendering tests with React Native Testing Library
- Store action tests
- API service tests with MSW
- Utility function tests
- 80% code coverage minimum

#### Integration Tests
- Auth flow end-to-end
- Cart to checkout flow
- Chat interaction flow
- Payment processing flow

#### E2E Tests (Detox)
- Critical user paths
- Template switching
- Offline/online transitions
- Payment scenarios

### 9. Deployment Configuration

#### Environment Variables
```bash
# .env.production
EXPO_PUBLIC_API_URL=https://api.weedgo.com
EXPO_PUBLIC_WS_URL=wss://api.weedgo.com
EXPO_PUBLIC_TENANT_ID=uuid-here
EXPO_PUBLIC_STORE_ID=uuid-here
EXPO_PUBLIC_CLOVER_APP_ID=xxx
EXPO_PUBLIC_SENTRY_DSN=xxx
```

#### Build Configuration
```json
// app.config.ts
export default {
  expo: {
    name: process.env.EXPO_PUBLIC_APP_NAME,
    slug: process.env.EXPO_PUBLIC_APP_SLUG,
    scheme: process.env.EXPO_PUBLIC_APP_SCHEME,
    version: "1.0.0",
    orientation: "portrait",
    icon: `./assets/icons/${process.env.EXPO_PUBLIC_TENANT_ID}/icon.png`,
    splash: {
      image: `./assets/splash/${process.env.EXPO_PUBLIC_TENANT_ID}/splash.png`,
    },
    ios: {
      bundleIdentifier: `com.weedgo.${process.env.EXPO_PUBLIC_TENANT_ID}`,
      supportsTablet: true,
      infoPlist: {
        NSMicrophoneUsageDescription: "For voice search and chat",
        NSLocationWhenInUseUsageDescription: "For delivery tracking",
      }
    },
    android: {
      package: `com.weedgo.${process.env.EXPO_PUBLIC_TENANT_ID}`,
      permissions: [
        "RECORD_AUDIO",
        "ACCESS_FINE_LOCATION",
        "VIBRATE"
      ]
    },
    plugins: [
      "expo-secure-store",
      "expo-av",
      "expo-speech",
      "@config-plugins/clover-go"
    ]
  }
};
```

### 10. Performance Monitoring

#### Analytics Integration
```typescript
// Track key metrics
- App launch time
- Screen load times
- API response times
- Cart abandonment rate
- Checkout completion rate
- Error rates by screen
- Voice feature usage
- Chat engagement metrics
```

#### Error Tracking (Sentry)
```typescript
Sentry.init({
  dsn: process.env.EXPO_PUBLIC_SENTRY_DSN,
  environment: process.env.NODE_ENV,
  integrations: [
    new Sentry.ReactNativeTracing({
      tracingOrigins: ['localhost', /^\//],
      routingInstrumentation: new Sentry.ReactNavigationInstrumentation(),
    }),
  ],
  tracesSampleRate: 0.2,
});
```

## Implementation Phases

### Phase 1: Foundation (Week 1-2)
1. Project setup with Expo SDK 50
2. Template system architecture
3. API client configuration
4. Authentication flow
5. Basic navigation structure

### Phase 2: Core Commerce (Week 3-4)
1. Product browsing and search
2. Shopping cart functionality
3. Basic checkout flow
4. Order history

### Phase 3: AI & Voice (Week 5-6)
1. WebSocket chat integration
2. Voice input/output
3. AI product recommendations
4. Chat history persistence

### Phase 4: Payments & Delivery (Week 7-8)
1. Clover Go integration
2. Payment method management
3. Delivery tracking
4. Push notifications

### Phase 5: Polish & Optimization (Week 9-10)
1. Performance optimization
2. Offline capabilities
3. Error handling refinement
4. Accessibility audit
5. Template refinement

### Phase 6: Testing & Deployment (Week 11-12)
1. Comprehensive testing
2. Beta testing with users
3. App store preparation
4. Production deployment

## Success Criteria

### Functional Requirements
- ✅ All API endpoints properly integrated
- ✅ Three templates fully functional
- ✅ Voice features working on iOS/Android
- ✅ Payment processing successful
- ✅ Real-time chat operational
- ✅ Offline mode handling

### Performance Metrics
- ✅ App size < 50MB
- ✅ Cold start < 2 seconds
- ✅ 60 FPS animations
- ✅ Memory usage < 200MB
- ✅ Battery drain < 5%/hour active use

### User Experience
- ✅ Checkout in 3 taps or less
- ✅ Search results in < 500ms
- ✅ Chat response < 1 second
- ✅ Zero crashes in production
- ✅ 4.5+ app store rating

## Critical Implementation Notes

1. **Security First**: Never store sensitive data in AsyncStorage. Use Expo SecureStore for tokens, credentials.

2. **API Efficiency**: Implement request debouncing, caching, and batch operations where possible.

3. **Template System**: Use composition over inheritance. Components should be swappable, not extended.

4. **Voice Privacy**: Always show visual indicator when microphone is active. Get explicit permission.

5. **Payment Compliance**: Follow PCI DSS standards. Never store card details locally.

6. **Accessibility**: Test with screen readers from day one. Don't retrofit accessibility.

7. **Error Handling**: Every API call needs error handling with user-friendly messages.

8. **State Management**: Keep stores small and focused. Don't put everything in one store.

9. **Performance**: Use React.memo, useMemo, and useCallback appropriately. Profile before optimizing.

10. **Testing**: Write tests as you code, not after. TDD for critical paths.

## Development Workflow

```bash
# Initial setup
npx create-expo-app weedgo-mobile --template expo-template-blank-typescript
cd weedgo-mobile
npx expo install expo-router expo-secure-store expo-av expo-speech
npm install axios socket.io-client zustand react-hook-form zod
npm install -D @types/react @types/react-native typescript

# Start development
npm run start

# Run on devices
npm run ios
npm run android

# Build for production
eas build --platform ios --profile production
eas build --platform android --profile production

# Submit to stores
eas submit --platform ios
eas submit --platform android
```

## Final Checklist Before Launch

- [ ] All endpoints integrated and tested
- [ ] Three templates fully styled and functional
- [ ] Voice features tested on real devices
- [ ] Payment flow tested with real transactions
- [ ] Delivery tracking validated
- [ ] Push notifications working
- [ ] Offline mode graceful degradation
- [ ] Accessibility audit passed
- [ ] Performance benchmarks met
- [ ] Security audit completed
- [ ] Privacy policy updated
- [ ] App store assets ready
- [ ] Beta testing feedback incorporated
- [ ] Crash-free rate > 99.9%
- [ ] Documentation complete

This comprehensive implementation guide ensures the development of a production-ready, first-class mobile application that fully leverages the AI Engine Service API while providing an exceptional user experience with minimal friction and maximum delight.