import AsyncStorage from '@react-native-async-storage/async-storage';

export type OrderStatus =
  | 'pending'
  | 'confirmed'
  | 'preparing'
  | 'ready_for_pickup'
  | 'out_for_delivery'
  | 'delivered'
  | 'cancelled';

export interface OrderUpdate {
  orderId: string;
  status: OrderStatus;
  timestamp: Date;
  message?: string;
  estimatedTime?: string;
  driverLocation?: {
    latitude: number;
    longitude: number;
  };
}

interface TrackingListener {
  orderId: string;
  callback: (update: OrderUpdate) => void;
}

class OrderTrackingService {
  private ws: WebSocket | null = null;
  private listeners: Map<string, Set<(update: OrderUpdate) => void>> = new Map();
  private reconnectTimeout: NodeJS.Timeout | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private subscribedOrders: Set<string> = new Set();

  /**
   * Connect to order tracking WebSocket
   */
  async connect(): Promise<void> {
    if (this.ws?.readyState === WebSocket.OPEN) {
      console.log('Already connected to order tracking');
      return;
    }

    const wsUrl = process.env.EXPO_PUBLIC_WS_URL || 'ws://10.0.0.169:5024';
    const authToken = await AsyncStorage.getItem('auth_token');

    const url = `${wsUrl}/orders/track${authToken ? `?token=${authToken}` : ''}`;

    this.setupWebSocket(url);
  }

  private setupWebSocket(url: string) {
    try {
      console.log('Connecting to order tracking:', url);
      this.ws = new WebSocket(url);

      this.ws.onopen = () => {
        console.log('Order tracking connected');
        this.reconnectAttempts = 0;

        // Re-subscribe to all tracked orders
        this.subscribedOrders.forEach(orderId => {
          this.subscribeToOrder(orderId);
        });
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.handleMessage(data);
        } catch (error) {
          console.error('Failed to parse order tracking message:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('Order tracking error:', error);
      };

      this.ws.onclose = () => {
        console.log('Order tracking disconnected');
        this.scheduleReconnect();
      };
    } catch (error) {
      console.error('Failed to setup order tracking WebSocket:', error);
    }
  }

  private handleMessage(data: any) {
    switch (data.type) {
      case 'order_update':
        this.notifyListeners(data.order_id, {
          orderId: data.order_id,
          status: data.status,
          timestamp: new Date(data.timestamp),
          message: data.message,
          estimatedTime: data.estimated_time,
        });
        break;

      case 'location_update':
        this.notifyListeners(data.order_id, {
          orderId: data.order_id,
          status: 'out_for_delivery',
          timestamp: new Date(),
          driverLocation: {
            latitude: data.latitude,
            longitude: data.longitude,
          },
        });
        break;

      case 'delivery_complete':
        this.notifyListeners(data.order_id, {
          orderId: data.order_id,
          status: 'delivered',
          timestamp: new Date(data.timestamp),
          message: 'Your order has been delivered!',
        });
        this.untrackOrder(data.order_id);
        break;

      case 'order_cancelled':
        this.notifyListeners(data.order_id, {
          orderId: data.order_id,
          status: 'cancelled',
          timestamp: new Date(data.timestamp),
          message: data.reason || 'Order has been cancelled',
        });
        this.untrackOrder(data.order_id);
        break;

      default:
        console.log('Unknown order tracking message:', data);
    }
  }

  private notifyListeners(orderId: string, update: OrderUpdate) {
    const callbacks = this.listeners.get(orderId);
    if (callbacks) {
      callbacks.forEach(callback => {
        try {
          callback(update);
        } catch (error) {
          console.error('Error in order tracking listener:', error);
        }
      });
    }
  }

  private scheduleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.log('Max reconnection attempts reached');
      return;
    }

    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
    }

    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
    this.reconnectAttempts++;

    console.log(`Reconnecting order tracking in ${delay}ms`);

    this.reconnectTimeout = setTimeout(() => {
      this.connect();
    }, delay);
  }

  /**
   * Track a specific order
   */
  trackOrder(orderId: string, callback: (update: OrderUpdate) => void) {
    // Add listener
    if (!this.listeners.has(orderId)) {
      this.listeners.set(orderId, new Set());
    }
    this.listeners.get(orderId)?.add(callback);

    // Subscribe to order updates
    this.subscribeToOrder(orderId);

    // Return unsubscribe function
    return () => {
      this.listeners.get(orderId)?.delete(callback);
      if (this.listeners.get(orderId)?.size === 0) {
        this.listeners.delete(orderId);
        this.untrackOrder(orderId);
      }
    };
  }

  private subscribeToOrder(orderId: string) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'subscribe',
        order_id: orderId,
      }));
      this.subscribedOrders.add(orderId);
    }
  }

  private untrackOrder(orderId: string) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'unsubscribe',
        order_id: orderId,
      }));
    }
    this.subscribedOrders.delete(orderId);
    this.listeners.delete(orderId);
  }

  /**
   * Get order status via REST API
   */
  async getOrderStatus(orderId: string): Promise<OrderUpdate | null> {
    try {
      const apiUrl = process.env.EXPO_PUBLIC_API_URL || 'http://10.0.0.169:5024';
      const authToken = await AsyncStorage.getItem('auth_token');

      const response = await fetch(`${apiUrl}/api/orders/${orderId}/status`, {
        headers: {
          'Authorization': authToken ? `Bearer ${authToken}` : '',
        },
      });

      if (response.ok) {
        const data = await response.json();
        return {
          orderId: data.order_id,
          status: data.status,
          timestamp: new Date(data.updated_at),
          message: data.status_message,
          estimatedTime: data.estimated_delivery,
        };
      }
      return null;
    } catch (error) {
      console.error('Failed to get order status:', error);
      return null;
    }
  }

  /**
   * Send delivery instructions
   */
  async sendDeliveryInstructions(orderId: string, instructions: string): Promise<boolean> {
    try {
      const apiUrl = process.env.EXPO_PUBLIC_API_URL || 'http://10.0.0.169:5024';
      const authToken = await AsyncStorage.getItem('auth_token');

      const response = await fetch(`${apiUrl}/api/orders/${orderId}/instructions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': authToken ? `Bearer ${authToken}` : '',
        },
        body: JSON.stringify({ instructions }),
      });

      return response.ok;
    } catch (error) {
      console.error('Failed to send delivery instructions:', error);
      return false;
    }
  }

  /**
   * Rate delivery experience
   */
  async rateDelivery(orderId: string, rating: number, feedback?: string): Promise<boolean> {
    try {
      const apiUrl = process.env.EXPO_PUBLIC_API_URL || 'http://10.0.0.169:5024';
      const authToken = await AsyncStorage.getItem('auth_token');

      const response = await fetch(`${apiUrl}/api/orders/${orderId}/rate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': authToken ? `Bearer ${authToken}` : '',
        },
        body: JSON.stringify({ rating, feedback }),
      });

      return response.ok;
    } catch (error) {
      console.error('Failed to rate delivery:', error);
      return false;
    }
  }

  /**
   * Disconnect from tracking service
   */
  disconnect() {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    this.listeners.clear();
    this.subscribedOrders.clear();
  }
}

// Export singleton instance
export const orderTrackingService = new OrderTrackingService();