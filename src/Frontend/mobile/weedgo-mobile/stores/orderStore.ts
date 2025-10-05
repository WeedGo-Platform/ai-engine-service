import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { ordersService as orderService } from '@/services/api/orders';
import { useCartStore } from './cartStore';
import Toast from 'react-native-toast-message';

export interface DeliveryAddress {
  id: string;
  street: string;
  unit?: string;
  city: string;
  province: string;
  postal_code: string;
  instructions?: string;
  latitude?: number;
  longitude?: number;
}

export interface PaymentMethod {
  id: string;
  type: 'card' | 'cash' | 'etransfer';
  last4?: string;
  card_brand?: string;
  is_default: boolean;
}

export interface Order {
  id: string;
  order_number: string;
  user_id: string;
  store_id: string;
  status: 'pending' | 'confirmed' | 'preparing' | 'ready' | 'out_for_delivery' | 'delivered' | 'cancelled';
  items: OrderItem[];
  subtotal: number;
  tax: number;
  delivery_fee: number;
  tip_amount: number;
  discount: number;
  total: number;
  delivery_type: 'delivery' | 'pickup';
  delivery_address?: DeliveryAddress;
  pickup_time?: string;
  payment_method: PaymentMethod;
  special_instructions?: string;
  estimated_time?: string;
  driver?: {
    id: string;
    name: string;
    phone: string;
    photo?: string;
  };
  created_at: string;
  updated_at: string;
}

export interface OrderItem {
  id: string;
  product_id: string;
  product_name: string;
  product_image?: string;
  sku: string;
  quantity: number;
  size?: string;
  price: number;
  subtotal: number;
}

export interface CreateOrderData {
  cart_session_id: string;
  user_id: string;
  store_id: string;
  delivery_type: 'delivery' | 'pickup';
  delivery_address?: DeliveryAddress;
  pickup_time?: string;
  payment_method_id: string;
  tip_amount: number;
  special_instructions?: string;
  promo_code?: string;
}

interface OrderStore {
  // State
  currentOrder: Order | null;
  orders: Order[];
  recentOrders: Order[];
  loading: boolean;
  error: string | null;

  // Order Management
  createOrder: (data: CreateOrderData) => Promise<Order>;
  loadOrders: () => Promise<void>;
  loadOrder: (orderId: string) => Promise<Order>;
  cancelOrder: (orderId: string, reason?: string) => Promise<void>;
  reorder: (orderId: string) => Promise<void>;

  // Order Tracking
  trackOrder: (orderId: string) => void;
  updateOrderStatus: (orderId: string, status: string) => void;

  // Validation
  validateOrder: (data: Partial<CreateOrderData>) => Promise<{ valid: boolean; issues: string[] }>;

  // Helpers
  getOrderById: (orderId: string) => Order | undefined;
  clearCurrentOrder: () => void;
  setError: (error: string | null) => void;
}

export const useOrderStore = create<OrderStore>()(
  persist(
    (set, get) => ({
      // Initial state
      currentOrder: null,
      orders: [],
      recentOrders: [],
      loading: false,
      error: null,

      // Create a new order
      createOrder: async (data: CreateOrderData) => {
        try {
          set({ loading: true, error: null });

          // Validate cart first
          const cartStore = useCartStore.getState();
          const cartValid = await cartStore.validateCart();

          if (!cartValid) {
            throw new Error('Cart validation failed. Please review your items.');
          }

          // Validate minimum order amount
          if (cartStore.subtotal < cartStore.minimumOrder) {
            throw new Error(`Minimum order amount is $${cartStore.minimumOrder}`);
          }

          // Create order via API
          const response = await orderService.createOrder(data);
          const order = response.data;

          // Update state
          set((state) => ({
            currentOrder: order,
            orders: [order, ...state.orders],
            recentOrders: [order, ...state.recentOrders.slice(0, 4)] // Keep last 5 orders
          }));

          // Clear cart after successful order
          await cartStore.clearCart();

          // Show success message
          Toast.show({
            type: 'success',
            text1: 'Order Placed!',
            text2: `Order #${order.order_number} confirmed`,
            visibilityTime: 4000,
          });

          return order;
        } catch (error: any) {
          const message = error.response?.data?.message || error.message || 'Failed to create order';
          set({ error: message });

          Toast.show({
            type: 'error',
            text1: 'Order Failed',
            text2: message,
            visibilityTime: 5000,
          });

          throw error;
        } finally {
          set({ loading: false });
        }
      },

      // Load user's orders
      loadOrders: async () => {
        try {
          set({ loading: true, error: null });
          const response = await orderService.getOrders();

          set({
            orders: response.data.orders,
            recentOrders: response.data.orders.slice(0, 5)
          });
        } catch (error: any) {
          const message = error.response?.data?.message || 'Failed to load orders';
          set({ error: message });
          console.error('Load orders error:', error);
        } finally {
          set({ loading: false });
        }
      },

      // Load specific order
      loadOrder: async (orderId: string) => {
        try {
          set({ loading: true, error: null });
          const response = await orderService.getOrder(orderId);
          const order = response.data;

          // Update order in list if exists
          set((state) => ({
            currentOrder: order,
            orders: state.orders.map(o => o.id === orderId ? order : o)
          }));

          return order;
        } catch (error: any) {
          const message = error.response?.data?.message || 'Failed to load order';
          set({ error: message });
          throw error;
        } finally {
          set({ loading: false });
        }
      },

      // Cancel an order
      cancelOrder: async (orderId: string, reason?: string) => {
        try {
          set({ loading: true, error: null });
          await orderService.cancelOrder(orderId, { reason });

          // Update order status locally
          set((state) => ({
            orders: state.orders.map(o =>
              o.id === orderId ? { ...o, status: 'cancelled' as const } : o
            ),
            currentOrder: state.currentOrder?.id === orderId
              ? { ...state.currentOrder, status: 'cancelled' as const }
              : state.currentOrder
          }));

          Toast.show({
            type: 'success',
            text1: 'Order Cancelled',
            text2: 'Your order has been cancelled successfully',
          });
        } catch (error: any) {
          const message = error.response?.data?.message || 'Failed to cancel order';
          set({ error: message });

          Toast.show({
            type: 'error',
            text1: 'Cancellation Failed',
            text2: message,
          });

          throw error;
        } finally {
          set({ loading: false });
        }
      },

      // Reorder items from a previous order
      reorder: async (orderId: string) => {
        try {
          set({ loading: true, error: null });
          const order = get().getOrderById(orderId);

          if (!order) {
            throw new Error('Order not found');
          }

          const cartStore = useCartStore.getState();

          // Clear current cart
          await cartStore.clearCart();

          // Add all items from previous order
          for (const item of order.items) {
            // Note: You'll need to fetch product details or store them with order
            // This is a simplified version
            await orderService.getProductForReorder(item.product_id).then(async (product) => {
              await cartStore.addItem(product.data, item.quantity, item.size);
            });
          }

          Toast.show({
            type: 'success',
            text1: 'Items Added to Cart',
            text2: 'Your previous order items have been added to cart',
          });
        } catch (error: any) {
          const message = error.response?.data?.message || 'Failed to reorder';
          set({ error: message });

          Toast.show({
            type: 'error',
            text1: 'Reorder Failed',
            text2: message,
          });

          throw error;
        } finally {
          set({ loading: false });
        }
      },

      // Track order updates (for real-time tracking)
      trackOrder: (orderId: string) => {
        // This would connect to WebSocket or polling for real-time updates
        // For now, we'll just load the order
        get().loadOrder(orderId);
      },

      // Update order status (usually from WebSocket/push notification)
      updateOrderStatus: (orderId: string, status: string) => {
        set((state) => ({
          orders: state.orders.map(o =>
            o.id === orderId ? { ...o, status: status as Order['status'] } : o
          ),
          currentOrder: state.currentOrder?.id === orderId
            ? { ...state.currentOrder, status: status as Order['status'] }
            : state.currentOrder
        }));
      },

      // Validate order data before submission
      validateOrder: async (data: Partial<CreateOrderData>) => {
        const issues: string[] = [];

        // Check delivery type
        if (!data.delivery_type) {
          issues.push('Delivery type is required');
        }

        // Check delivery address for delivery orders
        if (data.delivery_type === 'delivery' && !data.delivery_address) {
          issues.push('Delivery address is required');
        }

        // Check pickup time for pickup orders
        if (data.delivery_type === 'pickup' && !data.pickup_time) {
          issues.push('Pickup time is required');
        }

        // Check payment method
        if (!data.payment_method_id) {
          issues.push('Payment method is required');
        }

        // Validate with server
        try {
          const response = await orderService.validateOrder(data);
          if (!response.data.valid) {
            issues.push(...response.data.issues);
          }
        } catch (error) {
          issues.push('Unable to validate order with server');
        }

        return {
          valid: issues.length === 0,
          issues
        };
      },

      // Helper functions
      getOrderById: (orderId: string) => {
        const state = get();
        return state.orders.find(o => o.id === orderId);
      },

      clearCurrentOrder: () => {
        set({ currentOrder: null });
      },

      setError: (error: string | null) => {
        set({ error });
      }
    }),
    {
      name: 'order-storage',
      storage: createJSONStorage(() => AsyncStorage),
      partialize: (state) => ({
        recentOrders: state.recentOrders,
        currentOrder: state.currentOrder
      })
    }
  )
);