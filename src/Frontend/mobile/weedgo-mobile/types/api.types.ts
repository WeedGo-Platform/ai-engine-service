// API Response Types

// Authentication Types
export interface CheckPhoneRequest {
  phone: string;
}

export interface CheckPhoneResponse {
  exists: boolean;
  requiresOtp: boolean;
}

export interface RegisterRequest {
  phone: string;
  email?: string;
  first_name?: string;
  last_name?: string;
  password?: string;
  date_of_birth?: string;
  accept_terms?: boolean;
  accept_privacy?: boolean;
  accept_marketing?: boolean;
  referral_code?: string;
  enable_voice_auth?: boolean;
}

export interface RegisterResponse {
  message: string;
  access_token: string;
  token_type: string;
  user: User;
}

export interface LoginRequest {
  phone: string;
}

export interface LoginResponse {
  message: string;
  access_token?: string;
  refresh_token?: string;
  access?: string;  // Alternative field name used by backend
  refresh?: string; // Alternative field name used by backend
  token_type?: string;
  user: User;
}

export interface VerifyOTPRequest {
  phone: string;
  otp_code: string;
  session_id: string;
}

export interface VerifyOTPResponse {
  access_token: string;
  refresh_token: string;
  user: User;
}

export interface RefreshTokenResponse {
  access_token: string;
  refresh_token: string;
}

// User Types
export interface User {
  id: string;
  phone: string;
  email?: string;
  profile_id?: string;
  first_name?: string;
  last_name?: string;
  // Additional properties for component compatibility
  firstName?: string;
  lastName?: string;
  profileId?: string;
  profile_image?: string;
}

export interface Profile {
  id: string;
  phone: string;
  email?: string;
  first_name?: string;
  last_name?: string;
  date_of_birth?: string;
  profile_image?: string;
  email_verified?: boolean;
  phone_verified?: boolean;
  age_verified?: boolean;
  age_verified_at?: string;
  verification_method?: string;
  preferences?: Record<string, any>;
  addresses?: Address[];
  created_at?: string;
  updated_at?: string;
}

export interface Address {
  id: string;
  type: 'delivery' | 'billing';
  street: string;
  city: string;
  province: string;
  postal_code: string;
  is_default: boolean;
}

// Store Types
export interface StoreAddress {
  street: string;
  city: string;
  province: string;
  postal_code: string;
  country: string;
}

export interface Store {
  id: string;
  name: string;
  store_code: string;
  address: StoreAddress;
  city?: string;
  phone: string;
  hours: StoreHours;
  latitude?: number;
  longitude?: number;
  distance?: number;
  rating?: number;
  reviewCount?: number;
  delivery_zones: DeliveryZone[];
  pickup_available: boolean;
  delivery_available: boolean;
  image_url?: string;
}

export interface StoreHours {
  monday?: DayHours;
  tuesday?: DayHours;
  wednesday?: DayHours;
  thursday?: DayHours;
  friday?: DayHours;
  saturday?: DayHours;
  sunday?: DayHours;
  holidays?: Holiday[];
}

export interface DayHours {
  open: string;
  close: string;
  is_closed?: boolean;
}

export interface Holiday {
  date: string;
  name: string;
  is_closed: boolean;
}

export interface DeliveryZone {
  id: string;
  name: string;
  postal_codes: string[];
  fee: number;
  minimum_order: number;
  estimated_time: string;
}

// Product Types - matches actual API response
export interface Product {
  id: string;
  sku: string;
  slug?: string;
  name: string;
  brand: string;
  description: string;
  longDescription?: string;
  category: string;
  subCategory?: string;
  sub_category?: string;  // API field name with underscore
  subSubCategory?: string;
  strainType?: string;
  plantType?: string;
  strain?: string | null;
  images?: string[];
  image?: string;
  sizes?: Array<{
    id: string;
    name: string;
    price: number | null;
    inStock: boolean;
  }>;
  size?: string;
  price?: number | null;
  basePrice?: number;
  compareAtPrice?: number | null;
  onSale?: boolean;
  thcContent?: {
    min: number;
    max: number;
    display: string;
  };
  cbdContent?: {
    min: number;
    max: number;
    display: string;
  };
  inStock?: boolean;
  stockStatus?: string;
  quantity?: number | null;
  rating?: number;
  reviewCount?: number;
  effects?: string[];
  featured?: boolean;
  bestseller?: boolean;
  newArrival?: boolean;
  tags?: string[];
  terpenes?: Terpene[] | null;
  ocsItemNumber?: number;
  ocsVariantNumber?: string;
  gtin?: string;

  // Legacy compatibility fields
  image_url?: string;
  thc_content?: number;
  cbd_content?: number;
  strain_type?: string;
  in_stock?: boolean;
  rating_count?: number;
  quantity_available?: number;
  unit_of_measure?: string;
}

export interface Terpene {
  name: string;
  percentage: number;
  effects: string[];
}

export interface ProductSearchParams {
  q?: string;
  search?: string;
  store_id?: string;
  category?: string;
  subcategory?: string;
  brand?: string;
  strain_type?: string;
  thc_min?: number;
  thc_max?: number;
  cbd_min?: number;
  cbd_max?: number;
  price_min?: number;
  price_max?: number;
  size?: string;
  in_stock?: boolean;
  sort?: 'price_asc' | 'price_desc' | 'name' | 'thc' | 'cbd' | 'rating';
  limit?: number;
  offset?: number;
}

export interface ProductSearchResponse {
  offset?: number;
  results?: Product[];  // Some endpoints return 'results'
  products?: Product[];  // /api/search/products returns 'products'
  total?: number;
  page?: number;
  limit?: number;
  facets?: {
    categories: CategoryCount[];
    brands: BrandCount[];
    price_ranges: PriceRange[];
  };
}

export interface Category {
  id: string;
  name: string;
  slug: string;
  image_url?: string;
  subcategories?: Subcategory[];
}

export interface Subcategory {
  id: string;
  name: string;
  slug: string;
  image_url?: string;
}

export interface CategoryCount {
  category: string;
  count: number;
}

export interface BrandCount {
  brand: string;
  count: number;
}

export interface PriceRange {
  min: number;
  max: number;
  count: number;
}

// Cart Types
export interface Cart {
  session_id: string;
  items: CartItem[];
  subtotal: number;
  tax: number;
  delivery_fee?: number;
  discount?: number;
  total: number;
  promo_code?: string;
}

export interface CartItem {
  id: string;
  product_id: string;
  product: Product;
  quantity: number;
  price: number;
  subtotal: number;
}

export interface AddToCartRequest {
  product_id: string;
  quantity: number;
  size?: string;
}

export interface UpdateCartItemRequest {
  quantity: number;
}

export interface ApplyPromoRequest {
  promo_code: string;
}

// Order Types
export interface Order {
  id: string;
  order_number: string;
  status: OrderStatus;
  created_at: string;
  updated_at: string;
  customer: {
    name: string;
    phone: string;
    email?: string;
  };
  delivery_type: 'delivery' | 'pickup';
  delivery_address?: Address;
  store: Store;
  items: OrderItem[];
  subtotal: number;
  tax: number;
  delivery_fee?: number;
  discount?: number;
  total: number;
  payment_method: string;
  payment_status: PaymentStatus;
  estimated_time?: string;
  tracking?: TrackingInfo;
}

export interface OrderItem {
  id: string;
  product: Product;
  quantity: number;
  price: number;
  subtotal: number;
}

export type OrderStatus =
  | 'pending'
  | 'confirmed'
  | 'preparing'
  | 'ready'
  | 'out_for_delivery'
  | 'delivered'
  | 'cancelled';

export type PaymentStatus =
  | 'pending'
  | 'processing'
  | 'completed'
  | 'failed'
  | 'refunded';

export interface TrackingInfo {
  driver_name?: string;
  driver_phone?: string;
  vehicle_info?: string;
  current_location?: {
    lat: number;
    lng: number;
  };
  estimated_arrival?: string;
}

export interface CreateOrderRequest {
  delivery_type: 'delivery' | 'pickup';
  delivery_address_id?: string;
  delivery_instructions?: string;
  pickup_time?: string;
  payment_method: string;
  tip_amount?: number;
}

// Chat Types
export interface ChatMessage {
  id: string;
  type: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  metadata?: {
    products?: Product[];
    order?: Order;
    action?: ChatAction;
  };
}

export interface ChatAction {
  type: 'add_to_cart' | 'view_product' | 'track_order' | 'apply_promo';
  payload: any;
}

// WebSocket Events
export interface WSMessage {
  type: string;
  data: any;
}

// API Error Response
export interface ApiError {
  error: string;
  message: string;
  statusCode: number;
  details?: any;
}