/**
 * Delivery Tracking Service
 * Manages WebSocket connection for real-time delivery tracking
 */

import { API_URL } from '../api/client';

export interface DeliveryLocation {
  latitude: number;
  longitude: number;
  timestamp: string;
  accuracy?: number;
  speed?: number;
  heading?: number;
}

export interface DeliveryUpdate {
  type: 'initial_status' | 'status_change' | 'current_location' | 'location_update' | 'eta_update';
  status?: string;
  assigned_to?: string;
  estimated_time?: string;
  location?: DeliveryLocation;
  eta?: string;
  message?: string;
}

export type DeliveryTrackingCallback = (update: DeliveryUpdate) => void;
export type ConnectionStatusCallback = (connected: boolean) => void;

class DeliveryTrackingService {
  private ws: WebSocket | null = null;
  private deliveryId: string | null = null;
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 5;
  private reconnectDelay: number = 2000;
  private pingInterval: NodeJS.Timeout | null = null;
  private callbacks: Set<DeliveryTrackingCallback> = new Set();
  private connectionCallbacks: Set<ConnectionStatusCallback> = new Set();

  /**
   * Connect to delivery tracking WebSocket
   */
  connect(deliveryId: string): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      console.log('[TrackingService] Already connected');
      return;
    }

    this.deliveryId = deliveryId;

    // Convert http://localhost:5024 to ws://localhost:5024
    const wsUrl = API_URL.replace('http://', 'ws://').replace('https://', 'wss://');
    const url = `${wsUrl}/api/v1/delivery/ws/${deliveryId}`;

    console.log(`[TrackingService] Connecting to WebSocket: ${url}`);

    try {
      this.ws = new WebSocket(url);

      this.ws.onopen = () => {
        console.log('[TrackingService] WebSocket connected');
        this.reconnectAttempts = 0;
        this.startPing();
        this.notifyConnectionStatus(true);
      };

      this.ws.onmessage = (event) => {
        try {
          const update: DeliveryUpdate = JSON.parse(event.data);
          console.log('[TrackingService] Received update:', update);
          this.notifyCallbacks(update);
        } catch (error) {
          console.error('[TrackingService] Error parsing message:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('[TrackingService] WebSocket error:', error);
      };

      this.ws.onclose = () => {
        console.log('[TrackingService] WebSocket closed');
        this.stopPing();
        this.notifyConnectionStatus(false);
        this.attemptReconnect();
      };
    } catch (error) {
      console.error('[TrackingService] Error creating WebSocket:', error);
    }
  }

  /**
   * Disconnect from WebSocket
   */
  disconnect(): void {
    this.stopPing();

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    this.deliveryId = null;
    this.reconnectAttempts = 0;
    this.notifyConnectionStatus(false);
  }

  /**
   * Subscribe to delivery updates
   */
  subscribe(callback: DeliveryTrackingCallback): () => void {
    this.callbacks.add(callback);

    // Return unsubscribe function
    return () => {
      this.callbacks.delete(callback);
    };
  }

  /**
   * Subscribe to connection status changes
   */
  subscribeToConnectionStatus(callback: ConnectionStatusCallback): () => void {
    this.connectionCallbacks.add(callback);

    // Return unsubscribe function
    return () => {
      this.connectionCallbacks.delete(callback);
    };
  }

  /**
   * Send ping to keep connection alive
   */
  private startPing(): void {
    this.pingInterval = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send('ping');
      }
    }, 30000); // Ping every 30 seconds
  }

  /**
   * Stop ping interval
   */
  private stopPing(): void {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }

  /**
   * Attempt to reconnect to WebSocket
   */
  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('[TrackingService] Max reconnect attempts reached');
      return;
    }

    if (!this.deliveryId) {
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * this.reconnectAttempts;

    console.log(`[TrackingService] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

    setTimeout(() => {
      if (this.deliveryId) {
        this.connect(this.deliveryId);
      }
    }, delay);
  }

  /**
   * Notify all subscribed callbacks
   */
  private notifyCallbacks(update: DeliveryUpdate): void {
    this.callbacks.forEach(callback => {
      try {
        callback(update);
      } catch (error) {
        console.error('[TrackingService] Error in callback:', error);
      }
    });
  }

  /**
   * Notify connection status callbacks
   */
  private notifyConnectionStatus(connected: boolean): void {
    this.connectionCallbacks.forEach(callback => {
      try {
        callback(connected);
      } catch (error) {
        console.error('[TrackingService] Error in connection callback:', error);
      }
    });
  }

  /**
   * Check if currently connected
   */
  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }
}

// Export singleton instance
export const deliveryTrackingService = new DeliveryTrackingService();
export default deliveryTrackingService;
