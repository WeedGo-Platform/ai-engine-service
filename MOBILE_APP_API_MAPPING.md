# Mobile App Screen to API Endpoint Mapping

## Complete Screen & API Integration Map

### 1. **Authentication Screens**

#### `/app/(auth)/register.tsx` - Registration Screen
**API Endpoint:** `POST /api/v1/auth/customer/register`
**Request:**
```json
{
  "phone": "+1234567890",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "date_of_birth": "1990-01-01"
}
```
**Response:** Returns user object with verification_required flag

**API Endpoint:** `POST /api/v1/auth/otp/send`
**Request:**
```json
{
  "identifier": "+1234567890",
  "purpose": "registration"
}
```

#### `/app/(auth)/otp-verify.tsx` - OTP Verification
**API Endpoint:** `POST /api/v1/auth/otp/verify`
**Request:**
```json
{
  "identifier": "+1234567890",
  "code": "123456"
}
```
**Response:** Returns authentication token and user details

#### `/app/(auth)/login.tsx` - Login Screen
**API Endpoint:** `POST /api/v1/auth/customer/login`
**Request:**
```json
{
  "identifier": "phone_or_email",
  "password": "optional_password"
}
```
**Response:** Returns token or triggers OTP flow

### 2. **Main Product Browsing**

#### `/app/(tabs)/index.tsx` - Home/Products Screen
**API Endpoint:** `GET /api/products/search`
**Query Parameters:**
- `q`: Search query (empty for all products)
- `limit`: Number of results (20)
- `offset`: Pagination offset
- `category`: Filter by category
- `brand`: Filter by brand
- `strain_type`: indica/sativa/hybrid/cbd
- `thc_min`/`thc_max`: THC range
- `cbd_min`/`cbd_max`: CBD range
- `price_min`/`price_max`: Price range
- `store_id`: Current store ID

**Response:**
```json
{
  "results": [
    {
      "id": "sku_variant",
      "name": "Product Name",
      "brand": "Brand Name",
      "description": "Short description",
      "category": "Flower",
      "subCategory": "Pre-Roll",
      "price": 25.99,
      "image": "https://cdn.url/image.jpg",
      "images": ["url1", "url2"],
      "thcContent": {"min": 18, "max": 22, "display": "18-22%"},
      "cbdContent": {"min": 0, "max": 1, "display": "0-1%"},
      "inStock": true,
      "quantity": 50,
      "rating": 4.5,
      "reviewCount": 123
    }
  ],
  "total": 500,
  "page": 0,
  "limit": 20
}
```

**Additional Endpoints:**
- `GET /api/products/featured` - Featured products
- `GET /api/products/bestsellers` - Best selling products
- `GET /api/products/new-arrivals` - New products
- `GET /api/products/trending` - Trending products

### 3. **Product Details**

#### `/app/product/[id].tsx` - Product Detail Screen
**API Endpoint:** `GET /api/products/details/{product_id}`
**Response:** Full product details with all fields

**API Endpoint:** `GET /api/products/{product_id}/related`
**Response:** Array of related products

**API Endpoint:** `GET /api/v1/reviews/products/{sku}/reviews`
**Response:** Product reviews and ratings

**API Endpoint:** `GET /api/v1/reviews/products/{sku}/ratings`
**Response:** Rating distribution

### 4. **Shopping Cart**

#### `/app/(tabs)/cart.tsx` - Cart Screen
**API Endpoint:** `GET /api/cart`
**Response:**
```json
{
  "items": [
    {
      "id": "cart_item_id",
      "product_id": "sku",
      "product": {/* product details */},
      "quantity": 2,
      "price": 25.99,
      "subtotal": 51.98
    }
  ],
  "subtotal": 103.96,
  "tax": 13.51,
  "delivery_fee": 5.00,
  "discount": 0,
  "total": 122.47
}
```

**API Endpoint:** `POST /api/cart/items`
**Request:**
```json
{
  "product_id": "sku",
  "quantity": 2
}
```

**API Endpoint:** `PUT /api/cart/items/{item_id}`
**Request:**
```json
{
  "quantity": 3
}
```

**API Endpoint:** `DELETE /api/cart/items/{item_id}`

**API Endpoint:** `POST /api/cart/validate`
**Purpose:** Validate cart before checkout

### 5. **Checkout**

#### `/app/checkout/index.tsx` - Checkout Screen
**API Endpoint:** `GET /api/stores/nearest`
**Query:** `lat`, `lng`, `radius`
**Response:** Available stores for delivery/pickup

**API Endpoint:** `POST /api/cart/delivery-address`
**Request:**
```json
{
  "address": {
    "street": "123 Main St",
    "city": "Toronto",
    "province": "ON",
    "postal_code": "M1M 1M1"
  }
}
```

**API Endpoint:** `GET /api/stores/{store_id}/delivery-availability`
**Query:** `address`
**Response:** Delivery availability and fees

**API Endpoint:** `POST /api/orders/create`
**Request:**
```json
{
  "cart_id": "cart_uuid",
  "delivery_method": "delivery|pickup",
  "delivery_address": {/* address object */},
  "payment_method": "card|cash",
  "payment_token": "clover_token",
  "notes": "Special instructions"
}
```
**Response:** Order confirmation with order number

### 6. **Order Confirmation**

#### `/app/checkout/confirmation.tsx` - Order Confirmation
**API Endpoint:** `GET /api/orders/{order_id}`
**Response:** Complete order details with tracking info

### 7. **User Profile**

#### `/app/(tabs)/profile.tsx` - Profile Screen
**API Endpoint:** `GET /api/v1/auth/customer/me`
**Response:** User profile details

**API Endpoint:** `GET /api/v1/auth/customer/addresses`
**Response:** Saved addresses

**API Endpoint:** `POST /api/v1/auth/customer/addresses`
**Request:** New address object

**API Endpoint:** `GET /api/customers/{customer_id}/orders`
**Response:** Order history

**API Endpoint:** `GET /api/wishlist`
**Response:** Wishlist items

### 8. **Search**

#### `/app/(tabs)/search.tsx` - Search Screen
**API Endpoint:** `GET /api/search/products`
**Query:**
- `q`: Search query
- `filters`: JSON stringified filters
**Response:** Search results with facets

### 9. **AI Chat**

#### `/app/(tabs)/chat.tsx` - Chat Screen
**WebSocket Endpoint:** `ws://localhost:5024/chat/session`
**Initial Connection:** Creates chat session

**API Endpoint:** `POST /chat/message`
**Request:**
```json
{
  "session_id": "session_uuid",
  "message": "User message",
  "context": {
    "current_screen": "products",
    "cart_items": []
  }
}
```
**Response:** AI response with product recommendations

**API Endpoint:** `GET /chat/history/{user_id}`
**Response:** Chat history

### 10. **Store Selection**

**Component:** `StoreSelector.tsx`
**API Endpoint:** `GET /api/stores/tenant/active`
**Response:** List of active stores for tenant

**API Endpoint:** `POST /api/stores/{store_id}/select`
**Purpose:** Set current store for session

### 11. **Payment Processing**

**API Endpoint:** `POST /api/payment/create-card-token`
**Request:** Card details
**Response:** Secure token for payment

**API Endpoint:** `POST /api/v1/client/payments/charge`
**Request:**
```json
{
  "amount": 122.47,
  "currency": "CAD",
  "token": "payment_token",
  "order_id": "order_uuid"
}
```
**Response:** Payment confirmation

## Data Flow Summary

1. **App Launch:**
   - Load tenant configuration
   - Get active stores
   - Initialize selected store

2. **Product Browsing:**
   - Fetch products from `/api/products/search`
   - Use actual images from API response
   - Display real prices, THC/CBD content
   - Show actual stock levels

3. **Cart Management:**
   - Persist cart on server via `/api/cart`
   - Validate inventory before checkout
   - Calculate taxes based on location

4. **Checkout Process:**
   - Verify delivery availability
   - Process payment through Clover
   - Create order record
   - Send confirmation

5. **Real-time Features:**
   - WebSocket for chat
   - Push notifications for orders
   - Live inventory updates

## Important Notes

- **NO MOCK DATA:** All data comes from API
- **Images:** Use `image` and `images` fields from product API responses
- **Prices:** Use actual prices from API including taxes
- **Inventory:** Check real-time stock levels
- **Store Context:** Always send store_id with requests
- **Authentication:** Include bearer token in all authenticated requests
- **Error Handling:** Display API error messages to user