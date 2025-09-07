// API Response Types
export interface ApiResponse<T> {
  data?: T;
  error?: string;
  message?: string;
  status: number;
}

// Product Types
export interface Product {
  id: string;
  name: string;
  category: 'flower' | 'edibles' | 'concentrates' | 'vapes' | 'accessories';
  strain_type: 'indica' | 'sativa' | 'hybrid' | 'cbd';
  thc_content: number;
  cbd_content: number;
  price: number;
  description: string;
  effects: string[];
  terpenes: string[];
  image_url?: string;
  brand: string;
  sku: string;
  created_at: string;
  updated_at: string;
}

// Inventory Types
export interface InventoryItem {
  id: string;
  product_id: string;
  product?: Product;
  quantity_on_hand: number;
  quantity_reserved: number;
  quantity_available: number;
  reorder_point: number;
  reorder_quantity: number;
  unit_cost: number;
  location: string;
  batch_number: string;
  expiry_date?: string;
  last_restocked: string;
  status: 'in_stock' | 'low_stock' | 'out_of_stock' | 'discontinued';
}

// Purchase Order Types
export interface PurchaseOrder {
  id: string;
  order_number: string;
  supplier_id: string;
  supplier?: Supplier;
  status: 'draft' | 'pending' | 'approved' | 'ordered' | 'shipped' | 'received' | 'cancelled';
  order_date: string;
  expected_delivery: string;
  actual_delivery?: string;
  items: PurchaseOrderItem[];
  subtotal: number;
  tax_amount: number;
  shipping_cost: number;
  total_amount: number;
  notes?: string;
  created_by: string;
  approved_by?: string;
  received_by?: string;
  created_at: string;
  updated_at: string;
}

export interface PurchaseOrderItem {
  id: string;
  product_id: string;
  product?: Product;
  quantity_ordered: number;
  quantity_received?: number;
  unit_cost: number;
  total_cost: number;
  batch_number?: string;
  expiry_date?: string;
}

// Supplier Types
export interface Supplier {
  id: string;
  name: string;
  contact_name: string;
  email: string;
  phone: string;
  address: string;
  city: string;
  province: string;
  postal_code: string;
  license_number: string;
  payment_terms: string;
  rating: number;
  status: 'active' | 'inactive' | 'suspended';
  created_at: string;
  updated_at: string;
}

// Customer Types
export interface Customer {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  date_of_birth: string;
  address?: string;
  city?: string;
  province?: string;
  postal_code?: string;
  customer_type: 'recreational' | 'medical';
  medical_license?: string;
  medical_expiry?: string;
  preferences: {
    preferred_strains: string[];
    consumption_methods: string[];
    desired_effects: string[];
    avoid_effects: string[];
  };
  loyalty_points: number;
  total_spent: number;
  order_count: number;
  last_order_date?: string;
  status: 'active' | 'inactive' | 'banned';
  created_at: string;
  updated_at: string;
}

// Order Types
export interface Order {
  id: string;
  order_number: string;
  customer_id: string;
  customer?: Customer;
  status: 'pending' | 'confirmed' | 'processing' | 'ready' | 'delivered' | 'cancelled';
  order_type: 'pickup' | 'delivery';
  items: OrderItem[];
  subtotal: number;
  tax_amount: number;
  delivery_fee: number;
  discount_amount: number;
  total_amount: number;
  payment_method: 'cash' | 'debit' | 'credit' | 'e-transfer';
  payment_status: 'pending' | 'paid' | 'refunded';
  delivery_address?: string;
  delivery_time?: string;
  special_instructions?: string;
  created_at: string;
  updated_at: string;
}

export interface OrderItem {
  id: string;
  product_id: string;
  product?: Product;
  quantity: number;
  unit_price: number;
  discount_amount: number;
  total_price: number;
}

// Cart Types
export interface Cart {
  id: string;
  session_id: string;
  customer_id?: string;
  items: CartItem[];
  subtotal: number;
  tax_amount: number;
  delivery_fee: number;
  discount_amount: number;
  total_amount: number;
  expires_at: string;
  created_at: string;
  updated_at: string;
}

export interface CartItem {
  id: string;
  product_id: string;
  product?: Product;
  quantity: number;
  unit_price: number;
  total_price: number;
}

// Analytics Types
export interface DashboardStats {
  revenue: {
    today: number;
    week: number;
    month: number;
    year: number;
    trend: number;
  };
  orders: {
    today: number;
    week: number;
    month: number;
    pending: number;
    processing: number;
  };
  inventory: {
    total_value: number;
    low_stock_items: number;
    out_of_stock_items: number;
    expiring_soon: number;
  };
  customers: {
    total: number;
    new_this_month: number;
    active: number;
    top_spenders: Customer[];
  };
}

export interface ProductAnalytics {
  product_id: string;
  product?: Product;
  units_sold: number;
  revenue: number;
  average_rating: number;
  reorder_rate: number;
  profit_margin: number;
}

// User & Auth Types
export interface User {
  id: string;
  email: string;
  name: string;
  role: 'admin' | 'manager' | 'staff';
  permissions: string[];
  avatar?: string;
  created_at: string;
  last_login: string;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  loading: boolean;
}

// Filter & Pagination Types
export interface PaginationParams {
  page: number;
  limit: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export interface FilterParams {
  search?: string;
  category?: string;
  status?: string;
  date_from?: string;
  date_to?: string;
  min_price?: number;
  max_price?: number;
  [key: string]: any;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}