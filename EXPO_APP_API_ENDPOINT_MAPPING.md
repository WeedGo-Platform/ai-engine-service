# Complete API Endpoint Mapping for Mobile Application Features

## Authentication & User Management

### Registration Flow
```typescript
// STEP 1: Check if phone exists (determine new vs existing user)
POST /api/v1/auth/customer/check-phone
Request: { phone: string }
Response: { exists: boolean, requiresOtp: boolean }

// STEP 2A: Register new user
POST /api/v1/auth/customer/register
Request: {
  phone: string,
  email?: string,
  first_name?: string,
  last_name?: string,
  date_of_birth?: string
}
Response: {
  success: boolean,
  message: string,
  otp_sent: boolean
}

// STEP 2B: Login existing user
POST /api/v1/auth/customer/login
Request: { phone: string }
Response: {
  success: boolean,
  otp_sent: boolean,
  session_id: string
}

// STEP 3: Verify OTP
POST /api/v1/auth/otp/verify
Request: {
  phone: string,
  otp_code: string,
  session_id: string
}
Response: {
  access_token: string,
  refresh_token: string,
  user: {
    id: string,
    phone: string,
    email: string,
    profile_id: string
  }
}

// Token refresh
POST /api/v1/auth/refresh
Headers: { Authorization: "Bearer <refresh_token>" }
Response: {
  access_token: string,
  refresh_token: string
}

// Logout
POST /api/v1/auth/logout
Headers: { Authorization: "Bearer <access_token>" }
Response: { success: boolean }
```

### Profile Management
```typescript
// Get user profile
GET /api/profile
Headers: { Authorization: "Bearer <token>" }
Response: {
  id: string,
  phone: string,
  email: string,
  first_name: string,
  last_name: string,
  date_of_birth: string,
  preferences: object,
  medical_info: object
}

// Update profile
PUT /api/profile/update
Headers: { Authorization: "Bearer <token>" }
Request: {
  email?: string,
  first_name?: string,
  last_name?: string,
  preferences?: object
}
Response: { success: boolean, profile: Profile }

// Manage addresses
GET /api/profile/addresses
Headers: { Authorization: "Bearer <token>" }
Response: Address[]

POST /api/profile/addresses
Headers: { Authorization: "Bearer <token>" }
Request: {
  type: 'delivery' | 'billing',
  street: string,
  city: string,
  province: string,
  postal_code: string,
  is_default: boolean
}
Response: { success: boolean, address_id: string }

PUT /api/profile/addresses/{address_id}
DELETE /api/profile/addresses/{address_id}
```

## Store & Tenant Context

### Store Selection
```typescript
// Get available stores for tenant
GET /api/stores
Headers: { X-Tenant-ID: "<tenant_id>" }
Response: Store[]

// Get specific store details
GET /api/stores/{store_id}
Response: {
  id: string,
  name: string,
  store_code: string,
  address: string,
  phone: string,
  hours: object,
  delivery_zones: Zone[],
  pickup_available: boolean,
  delivery_available: boolean
}

// Get store hours
GET /api/stores/{store_id}/hours
Response: {
  monday: { open: string, close: string },
  tuesday: { open: string, close: string },
  // ... etc
  holidays: Holiday[]
}

// Check store availability
GET /api/stores/{store_id}/availability
Query: { date?: string, time?: string }
Response: {
  is_open: boolean,
  next_open_time: string,
  delivery_available: boolean,
  pickup_available: boolean
}
```

## Product Catalog & Inventory

### Product Browsing
```typescript
// Search products with filters
GET /api/products/search
Query: {
  q?: string,              // search query
  category?: string,
  subcategory?: string,
  brand?: string,
  strain_type?: string,    // indica, sativa, hybrid
  thc_min?: number,
  thc_max?: number,
  cbd_min?: number,
  cbd_max?: number,
  price_min?: number,
  price_max?: number,
  size?: string,
  in_stock?: boolean,
  sort?: 'price_asc' | 'price_desc' | 'name' | 'thc' | 'cbd' | 'rating',
  limit?: number,
  offset?: number
}
Response: {
  products: Product[],
  total: number,
  facets: {
    categories: CategoryCount[],
    brands: BrandCount[],
    price_ranges: PriceRange[]
  }
}

// Get product categories
GET /api/products/categories
Response: {
  categories: [{
    id: string,
    name: string,
    slug: string,
    image_url: string,
    subcategories: Subcategory[]
  }]
}

// Get single product details
GET /api/products/{product_id}/details
Response: {
  id: string,
  sku: string,
  name: string,
  brand: string,
  category: string,
  subcategory: string,
  description: string,
  image_url: string,
  images: string[],
  thc_content: number,
  cbd_content: number,
  strain_type: string,
  terpenes: Terpene[],
  effects: string[],
  price: number,
  size: string,
  unit_of_measure: string,
  rating: number,
  rating_count: number,
  in_stock: boolean,
  quantity_available: number
}

// Get store-specific inventory
GET /api/store-inventory/{store_id}/products
Query: {
  category?: string,
  subcategory?: string,
  brand?: string,
  strain_type?: string,
  size?: string,
  quick_filter?: 'trending' | 'new' | 'staff-picks',
  search?: string,
  limit?: number,
  offset?: number
}
Response: {
  products: [{
    ...Product,
    quantity_available: number,
    quantity_reserved: number,
    retail_price: number,
    batch_details: BatchInfo[]
  }],
  total: number
}

// Check product availability at store
GET /api/inventory/store/{store_id}/status/{sku}
Response: {
  sku: string,
  quantity_available: number,
  quantity_reserved: number,
  retail_price: number,
  is_available: boolean,
  reorder_point: number
}

// Get trending products
GET /api/products/trending
Query: { store_id?: string, limit?: number }
Response: Product[]

// Get product recommendations
GET /api/products/recommendations
Query: {
  product_id?: string,
  user_id?: string,
  limit?: number
}
Headers: { Authorization: "Bearer <token>" }
Response: Product[]
```

## Shopping Cart

### Cart Management
```typescript
// Create or get cart session
POST /api/cart/session
Headers: { Authorization?: "Bearer <token>" }
Request: {
  store_id: string,
  user_id?: string
}
Response: {
  session_id: string,
  items: CartItem[],
  subtotal: number,
  tax_amount: number,
  total_amount: number
}

// Get cart
GET /api/cart/session/{session_id}
Response: {
  session_id: string,
  items: CartItem[],
  subtotal: number,
  tax_amount: number,
  discount_amount: number,
  delivery_fee: number,
  total_amount: number,
  applied_promotions: Promotion[]
}

// Add item to cart
POST /api/cart/add
Request: {
  session_id: string,
  sku: string,
  quantity: number,
  retail_price: number
}
Response: {
  success: boolean,
  cart: Cart,
  message?: string
}

// Update cart item quantity
PUT /api/cart/update
Request: {
  session_id: string,
  sku: string,
  quantity: number
}
Response: {
  success: boolean,
  cart: Cart
}

// Remove item from cart
DELETE /api/cart/remove
Request: {
  session_id: string,
  sku: string
}
Response: {
  success: boolean,
  cart: Cart
}

// Clear cart
DELETE /api/cart/clear/{session_id}
Response: { success: boolean }

// Apply promotion code
POST /api/promotions/apply
Request: {
  session_id: string,
  promotion_code: string
}
Response: {
  success: boolean,
  discount_amount: number,
  cart: Cart
}

// Calculate delivery fee
POST /api/delivery/calculate-fee
Request: {
  session_id: string,
  delivery_address: Address,
  store_id: string
}
Response: {
  delivery_fee: number,
  estimated_time: string,
  available: boolean
}
```

## Checkout & Orders

### Checkout Process
```typescript
// Validate cart for checkout
POST /api/cart/validate
Request: {
  session_id: string,
  delivery_type: 'delivery' | 'pickup'
}
Response: {
  valid: boolean,
  issues: string[],
  minimum_order_amount?: number
}

// Create order from cart
POST /api/orders/create
Headers: { Authorization: "Bearer <token>" }
Request: {
  cart_session_id: string,
  user_id?: string,
  payment_method: 'cash' | 'card' | 'debit',
  delivery_type: 'delivery' | 'pickup',
  delivery_address?: Address,
  pickup_time?: string,
  special_instructions?: string,
  tip_amount?: number
}
Response: {
  success: boolean,
  order_id: string,
  order_number: string,
  total_amount: number,
  payment_required: boolean,
  estimated_time: string
}

// Get order details
GET /api/orders/{order_id}
Headers: { Authorization: "Bearer <token>" }
Response: {
  id: string,
  order_number: string,
  status: OrderStatus,
  items: OrderItem[],
  subtotal: number,
  tax_amount: number,
  delivery_fee: number,
  tip_amount: number,
  total_amount: number,
  payment_status: string,
  delivery_status: string,
  estimated_delivery: string,
  delivery_address: Address,
  created_at: string,
  updated_at: string
}

// Get order history
GET /api/orders/history
Headers: { Authorization: "Bearer <token>" }
Query: {
  limit?: number,
  offset?: number,
  status?: string
}
Response: {
  orders: Order[],
  total: number
}

// Track order status
GET /api/orders/{order_id}/status
Response: {
  order_id: string,
  status: string,
  status_history: StatusUpdate[],
  estimated_time: string,
  delivery_person?: {
    name: string,
    phone: string
  }
}

// Cancel order
POST /api/orders/{order_id}/cancel
Headers: { Authorization: "Bearer <token>" }
Request: { reason: string }
Response: {
  success: boolean,
  refund_amount?: number
}

// Reorder
POST /api/orders/{order_id}/reorder
Headers: { Authorization: "Bearer <token>" }
Response: {
  success: boolean,
  cart_session_id: string,
  unavailable_items: string[]
}
```

## Payment Processing

### Payment Methods
```typescript
// Get saved payment methods
GET /api/payment/methods
Headers: { Authorization: "Bearer <token>" }
Response: PaymentMethod[]

// Add payment method
POST /api/payment/methods
Headers: { Authorization: "Bearer <token>" }
Request: {
  type: 'card' | 'bank',
  token: string,      // From Clover tokenization
  last_four: string,
  brand?: string,
  is_default: boolean
}
Response: {
  success: boolean,
  payment_method_id: string
}

// Delete payment method
DELETE /api/payment/methods/{method_id}
Headers: { Authorization: "Bearer <token>" }

// Process payment
POST /api/payment/process
Headers: { Authorization: "Bearer <token>" }
Request: {
  order_id: string,
  payment_method_id?: string,
  amount: number,
  tip?: number,
  payment_token?: string,  // For one-time payments
  store_id: string
}
Response: {
  success: boolean,
  transaction_id: string,
  status: 'approved' | 'declined' | 'pending',
  receipt_url?: string
}

// Process Clover payment
POST /api/payment/clover/process
Headers: { Authorization: "Bearer <token>" }
Request: {
  order_id: string,
  encrypted_card_data: string,  // From Clover SDK
  amount: number,
  device_id?: string
}
Response: {
  success: boolean,
  transaction_id: string,
  approval_code: string,
  receipt: Receipt
}

// Get payment status
GET /api/payment/status/{transaction_id}
Response: {
  transaction_id: string,
  status: string,
  amount: number,
  processed_at: string
}

// Request refund
POST /api/payment/refund
Headers: { Authorization: "Bearer <token>" }
Request: {
  transaction_id: string,
  amount: number,
  reason: string
}
Response: {
  success: boolean,
  refund_id: string,
  status: string
}
```

## AI Chat & Voice

### WebSocket Chat
```typescript
// WebSocket connection
WS: ws://[API_URL]/chat/ws
Connection: {
  query: { session_id: string }
}

// Send message
SEND: {
  type: 'message',
  content: string,
  isVoice?: boolean,
  context?: {
    store_id: string,
    user_id?: string,
    location?: Coordinates
  }
}

// Receive message
RECEIVE: {
  type: 'response' | 'product' | 'typing' | 'error',
  content?: string,
  products?: Product[],
  suggestions?: string[],
  action?: {
    type: 'add_to_cart' | 'show_product' | 'navigate',
    data: any
  }
}

// Voice transcription
POST /api/voice/transcribe
Headers: {
  Authorization: "Bearer <token>",
  Content-Type: "multipart/form-data"
}
Request: FormData with audio file
Response: {
  text: string,
  confidence: number,
  language: string
}

// Text-to-speech
POST /api/voice/synthesize
Request: {
  text: string,
  voice?: 'male' | 'female',
  speed?: number
}
Response: Audio stream

// Get chat history
GET /api/chat/history
Headers: { Authorization: "Bearer <token>" }
Query: {
  session_id?: string,
  limit?: number
}
Response: ChatMessage[]

// Save chat context
POST /api/chat/context
Headers: { Authorization: "Bearer <token>" }
Request: {
  session_id: string,
  context: object
}
Response: { success: boolean }
```

## Delivery & Tracking

### Delivery Management
```typescript
// Get delivery zones
GET /api/delivery/zones
Query: { store_id: string }
Response: {
  zones: [{
    id: string,
    name: string,
    polygon: Coordinates[],
    fee: number,
    minimum_order: number,
    estimated_time: string
  }]
}

// Check delivery availability
POST /api/delivery/check
Request: {
  store_id: string,
  address: Address
}
Response: {
  available: boolean,
  fee: number,
  estimated_time: string,
  zone_id: string
}

// Track delivery
GET /api/delivery/track/{order_id}
Response: {
  order_id: string,
  status: 'preparing' | 'ready' | 'dispatched' | 'delivered',
  driver?: {
    name: string,
    phone: string,
    photo_url: string,
    location?: {
      lat: number,
      lng: number,
      updated_at: string
    }
  },
  estimated_arrival: string,
  tracking_url?: string
}

// Rate delivery
POST /api/delivery/rate
Headers: { Authorization: "Bearer <token>" }
Request: {
  order_id: string,
  rating: number,
  comment?: string,
  driver_rating?: number
}
Response: { success: boolean }
```

## Reviews & Ratings

### Product Reviews
```typescript
// Get product reviews
GET /api/products/{product_id}/reviews
Query: {
  limit?: number,
  offset?: number,
  sort?: 'recent' | 'helpful' | 'rating'
}
Response: {
  reviews: Review[],
  total: number,
  average_rating: number
}

// Submit review
POST /api/reviews/create
Headers: { Authorization: "Bearer <token>" }
Request: {
  product_id: string,
  order_id: string,
  rating: number,
  title: string,
  comment: string,
  effects?: string[],
  would_recommend: boolean
}
Response: {
  success: boolean,
  review_id: string
}

// Vote on review helpfulness
POST /api/reviews/{review_id}/vote
Headers: { Authorization: "Bearer <token>" }
Request: { helpful: boolean }
Response: { success: boolean }
```

## Wishlist & Favorites

### Wishlist Management
```typescript
// Get wishlist
GET /api/wishlist
Headers: { Authorization: "Bearer <token>" }
Response: WishlistItem[]

// Add to wishlist
POST /api/wishlist/add
Headers: { Authorization: "Bearer <token>" }
Request: { product_id: string }
Response: { success: boolean }

// Remove from wishlist
DELETE /api/wishlist/remove/{product_id}
Headers: { Authorization: "Bearer <token>" }
Response: { success: boolean }

// Move wishlist to cart
POST /api/wishlist/to-cart
Headers: { Authorization: "Bearer <token>" }
Request: {
  product_ids: string[],
  session_id: string
}
Response: {
  success: boolean,
  added: string[],
  failed: string[]
}
```

## Promotions & Rewards

### Promotions
```typescript
// Get available promotions
GET /api/promotions/available
Query: {
  store_id: string,
  user_id?: string
}
Response: Promotion[]

// Validate promotion code
POST /api/promotions/validate
Request: {
  code: string,
  cart_session_id: string
}
Response: {
  valid: boolean,
  discount_type: 'percentage' | 'fixed',
  discount_value: number,
  message?: string
}

// Get user rewards
GET /api/rewards/balance
Headers: { Authorization: "Bearer <token>" }
Response: {
  points: number,
  tier: string,
  next_tier_points: number,
  available_rewards: Reward[]
}
```

## Analytics & Tracking

### Event Tracking
```typescript
// Track user event
POST /api/analytics/track
Request: {
  event: string,
  properties: object,
  user_id?: string,
  session_id: string,
  timestamp: string
}
Response: { success: boolean }

// Track product view
POST /api/analytics/product-view
Request: {
  product_id: string,
  user_id?: string,
  source: string
}

// Track search
POST /api/analytics/search
Request: {
  query: string,
  results_count: number,
  clicked_position?: number
}
```

## Push Notifications

### Notification Management
```typescript
// Register device token
POST /api/notifications/register
Headers: { Authorization: "Bearer <token>" }
Request: {
  token: string,
  platform: 'ios' | 'android',
  device_id: string
}
Response: { success: boolean }

// Update notification preferences
PUT /api/notifications/preferences
Headers: { Authorization: "Bearer <token>" }
Request: {
  order_updates: boolean,
  promotions: boolean,
  new_products: boolean,
  delivery_updates: boolean
}
Response: { success: boolean }

// Get notifications
GET /api/notifications
Headers: { Authorization: "Bearer <token>" }
Query: {
  unread_only?: boolean,
  limit?: number
}
Response: Notification[]

// Mark as read
PUT /api/notifications/{notification_id}/read
Headers: { Authorization: "Bearer <token>" }
```

## Store-Specific Features

### In-Store Pickup
```typescript
// Get pickup time slots
GET /api/stores/{store_id}/pickup-slots
Query: { date: string }
Response: {
  slots: [{
    time: string,
    available: boolean,
    capacity: number
  }]
}

// Reserve pickup slot
POST /api/pickup/reserve
Request: {
  order_id: string,
  slot_time: string
}
Response: {
  success: boolean,
  reservation_id: string,
  qr_code: string
}
```

### Kiosk Mode
```typescript
// Initialize kiosk session
POST /api/kiosk/session
Request: {
  store_id: string,
  kiosk_id: string
}
Response: {
  session_id: string,
  config: KioskConfig
}

// Process kiosk order
POST /api/kiosk/order
Request: {
  session_id: string,
  items: CartItem[],
  customer_age_verified: boolean
}
Response: {
  order_number: string,
  pickup_code: string,
  estimated_time: string
}
```

## Admin Features (Store Staff)

### POS Integration
```typescript
// Search customers for POS
GET /api/pos/customers/search
Query: {
  phone?: string,
  email?: string,
  name?: string
}
Headers: { Authorization: "Bearer <staff_token>" }
Response: Customer[]

// Create POS transaction
POST /api/pos/transaction
Headers: { Authorization: "Bearer <staff_token>" }
Request: {
  customer_id?: string,
  items: CartItem[],
  payment_method: string,
  cash_received?: number,
  terminal_id: string
}
Response: {
  transaction_id: string,
  receipt: Receipt,
  change_due?: number
}

// Get daily sales report
GET /api/pos/reports/daily
Headers: { Authorization: "Bearer <staff_token>" }
Query: {
  date: string,
  store_id: string
}
Response: DailySalesReport
```

## System Health & Configuration

### App Configuration
```typescript
// Get app config for tenant
GET /api/config/app
Headers: {
  X-Tenant-ID: "<tenant_id>",
  X-App-Version: "<version>"
}
Response: {
  minimum_app_version: string,
  force_update: boolean,
  features: {
    voice_enabled: boolean,
    delivery_enabled: boolean,
    loyalty_enabled: boolean,
    kiosk_enabled: boolean
  },
  payment_providers: string[],
  theme: ThemeConfig
}

// Get system status
GET /api/health
Response: {
  status: 'healthy' | 'degraded',
  services: {
    database: boolean,
    redis: boolean,
    payment: boolean,
    chat: boolean
  }
}
```

## Error Responses

### Standard Error Format
```typescript
// All endpoints return errors in this format
ERROR Response: {
  error: {
    code: string,           // e.g., "INVALID_TOKEN", "OUT_OF_STOCK"
    message: string,        // User-friendly message
    details?: object,       // Additional error details
    request_id: string      // For support reference
  },
  status: number           // HTTP status code
}

// Common Error Codes
- AUTH_REQUIRED: 401
- INVALID_TOKEN: 401
- FORBIDDEN: 403
- NOT_FOUND: 404
- VALIDATION_ERROR: 400
- OUT_OF_STOCK: 409
- PAYMENT_DECLINED: 402
- RATE_LIMITED: 429
- SERVER_ERROR: 500
```

## Request Headers

### Required Headers for All Authenticated Requests
```typescript
{
  "Authorization": "Bearer <access_token>",
  "X-Tenant-ID": "<tenant_id>",         // From environment
  "X-Store-ID": "<store_id>",           // Selected store
  "X-App-Version": "<version>",         // App version
  "X-Device-ID": "<device_id>",         // Unique device ID
  "X-Platform": "ios" | "android",      // Platform
  "Accept-Language": "en-CA",           // User language
  "Content-Type": "application/json"    // For POST/PUT requests
}
```

## WebSocket Events

### Chat WebSocket Events
```typescript
// Client -> Server Events
- "message": Send user message
- "typing": User is typing
- "product_inquiry": Ask about specific product
- "add_to_cart": Add product via chat
- "voice_input": Send voice data

// Server -> Client Events
- "response": AI response
- "typing": AI is typing
- "product_card": Product recommendation
- "action": Suggested action
- "error": Error message
- "connection": Connection status

// Connection Management
- "ping": Keep-alive
- "pong": Keep-alive response
- "reconnect": Reconnection needed
```

## Rate Limits

### API Rate Limiting
```typescript
// Per endpoint category (requests per minute)
- Authentication: 10 requests
- Product Browse: 60 requests
- Cart Operations: 30 requests
- Order Creation: 5 requests
- Payment Processing: 10 requests
- Chat Messages: 30 requests
- General API: 100 requests

// Rate limit headers in response
{
  "X-RateLimit-Limit": "100",
  "X-RateLimit-Remaining": "95",
  "X-RateLimit-Reset": "1640995200"
}
```

## Implementation Priority

### Phase 1: Core Shopping (Must Have)
1. Authentication endpoints
2. Product browsing/search
3. Cart management
4. Basic checkout
5. Order creation

### Phase 2: Enhanced Experience
1. AI Chat WebSocket
2. Voice endpoints
3. Delivery tracking
4. Payment processing
5. User profile

### Phase 3: Advanced Features
1. Wishlist
2. Reviews
3. Promotions
4. Push notifications
5. Analytics

### Phase 4: Store Features
1. In-store pickup
2. Kiosk mode
3. POS integration
4. Loyalty rewards
5. Admin functions

This comprehensive endpoint mapping ensures that every feature in the mobile application is backed by a real API endpoint, with no mock data or placeholder functionality.