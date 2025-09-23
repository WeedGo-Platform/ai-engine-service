// Core type definitions for WeedGo Commerce

export interface User {
  id: string;
  email: string;
  name: string;
  role: UserRole;
  avatar?: string;
  createdAt: Date;
  updatedAt: Date;
}

export enum UserRole {
  Customer = 'customer',
  Admin = 'admin',
  Staff = 'staff',
  Manager = 'manager'
}

export interface Store {
  id: string;
  name: string;
  code: string;
  address?: string;
  city?: string;
  province?: string;
  postalCode?: string;
  phone?: string;
  email?: string;
  delivery_available: boolean;
  pickup_available: boolean;
  hours?: StoreHours;
  settings?: StoreSettings;
}

export interface StoreHours {
  monday: DayHours;
  tuesday: DayHours;
  wednesday: DayHours;
  thursday: DayHours;
  friday: DayHours;
  saturday: DayHours;
  sunday: DayHours;
}

export interface DayHours {
  open: string;
  close: string;
  closed: boolean;
}

export interface StoreSettings {
  theme?: ThemeConfig;
  features?: FeatureFlags;
  payment?: PaymentSettings;
}

export interface ThemeConfig {
  primaryColor: string;
  secondaryColor: string;
  fontFamily: string;
  darkMode: boolean;
}

export interface FeatureFlags {
  delivery: boolean;
  pickup: boolean;
  onlineOrdering: boolean;
  loyaltyProgram: boolean;
  ageVerification: boolean;
}

export interface PaymentSettings {
  acceptCash: boolean;
  acceptCard: boolean;
  acceptDebit: boolean;
  acceptCrypto: boolean;
}

export interface Product {
  id: string;
  name: string;
  description: string;
  category: ProductCategory;
  price: number;
  image: string;
  images?: string[];
  thc?: number;
  cbd?: number;
  strain?: string;
  weight?: number;
  unit?: string;
  inStock: boolean;
  quantity: number;
  featured?: boolean;
  rating?: number;
  reviews?: number;
}

export enum ProductCategory {
  Flower = 'flower',
  Edibles = 'edibles',
  Concentrates = 'concentrates',
  Vapes = 'vapes',
  Accessories = 'accessories',
  Topicals = 'topicals',
  Seeds = 'seeds',
  PreRolls = 'prerolls'
}

export interface CartItem {
  id: string;
  product: Product;
  quantity: number;
  addedAt: Date;
}

export interface Order {
  id: string;
  userId: string;
  storeId: string;
  items: OrderItem[];
  status: OrderStatus;
  total: number;
  subtotal: number;
  tax: number;
  delivery?: DeliveryInfo;
  payment: PaymentInfo;
  createdAt: Date;
  updatedAt: Date;
}

export interface OrderItem {
  productId: string;
  name: string;
  price: number;
  quantity: number;
  total: number;
}

export enum OrderStatus {
  Pending = 'pending',
  Confirmed = 'confirmed',
  Processing = 'processing',
  Ready = 'ready',
  Delivered = 'delivered',
  Cancelled = 'cancelled'
}

export interface DeliveryInfo {
  method: 'delivery' | 'pickup';
  address?: string;
  scheduledTime?: Date;
  notes?: string;
}

export interface PaymentInfo {
  method: PaymentMethod;
  status: PaymentStatus;
  transactionId?: string;
}

export enum PaymentMethod {
  Cash = 'cash',
  Card = 'card',
  Debit = 'debit',
  Crypto = 'crypto'
}

export enum PaymentStatus {
  Pending = 'pending',
  Completed = 'completed',
  Failed = 'failed',
  Refunded = 'refunded'
}

export interface ApiResponse<T> {
  data?: T;
  error?: string;
  message?: string;
  status: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  hasMore: boolean;
}

export interface Language {
  code: string;
  label: string;
  flag: string;
  rtl?: boolean;
}

export interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  message: string;
  timestamp: Date;
  read: boolean;
}

export enum NotificationType {
  Info = 'info',
  Success = 'success',
  Warning = 'warning',
  Error = 'error'
}