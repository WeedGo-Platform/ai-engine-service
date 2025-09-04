/**
 * WebSocket Service for Real-time Communications
 * Implements singleton pattern for WebSocket connection management
 * Provides real-time updates for model deployments, training, and system metrics
 */

import type { WebSocketMessage, DeploymentProgress, ResourceMetrics } from './websocket.types';

// Re-export types for convenience
export type { WebSocketMessage, DeploymentProgress, ResourceMetrics } from './websocket.types';

// Simple EventEmitter implementation for browser compatibility
class EventEmitter {
  private events: Map<string, Set<Function>> = new Map();

  on(event: string, callback: Function): void {
    if (!this.events.has(event)) {
      this.events.set(event, new Set());
    }
    this.events.get(event)!.add(callback);
  }

  once(event: string, callback: Function): void {
    const onceWrapper = (...args: any[]) => {
      callback(...args);
      this.off(event, onceWrapper);
    };
    this.on(event, onceWrapper);
  }

  off(event: string, callback: Function): void {
    if (this.events.has(event)) {
      this.events.get(event)!.delete(callback);
    }
  }

  emit(event: string, ...args: any[]): void {
    if (this.events.has(event)) {
      this.events.get(event)!.forEach(callback => {
        try {
          callback(...args);
        } catch (error) {
          console.error(`Error in event listener for ${event}:`, error);
        }
      });
    }
  }

  removeAllListeners(event?: string): void {
    if (event) {
      this.events.delete(event);
    } else {
      this.events.clear();
    }
  }
}

class WebSocketService extends EventEmitter {
  private static instance: WebSocketService;
  private ws: WebSocket | null = null;
  private reconnectTimer: number | null = null;
  private heartbeatTimer: number | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private url: string;
  private isConnecting = false;
  private messageQueue: WebSocketMessage[] = [];
  private subscribers: Map<string, Set<(data: any) => void>> = new Map();

  private constructor() {
    super();
    // URL will be set during connect
    this.url = '';
  }

  public static getInstance(): WebSocketService {
    if (!WebSocketService.instance) {
      WebSocketService.instance = new WebSocketService();
    }
    return WebSocketService.instance;
  }

  /**
   * Connect to WebSocket server
   */
  public async connect(): Promise<void> {
    // Set URL from endpoints configuration if not already set
    if (!this.url) {
      const { endpoints } = await import('../config/endpoints');
      this.url = endpoints.websocket.models;
    }

    return new Promise((resolve, reject) => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        resolve();
        return;
      }

      if (this.isConnecting) {
        // Wait for existing connection attempt
        this.once('connected', resolve);
        this.once('error', reject);
        return;
      }

      this.isConnecting = true;
      console.log('[WebSocket] Connecting to:', this.url);

      try {
        this.ws = new WebSocket(this.url);

        this.ws.onopen = () => {
          console.log('[WebSocket] Connected successfully');
          this.isConnecting = false;
          this.reconnectAttempts = 0;
          this.startHeartbeat();
          this.flushMessageQueue();
          this.emit('connected');
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (error) {
            console.error('[WebSocket] Failed to parse message:', error);
          }
        };

        this.ws.onerror = (error) => {
          console.error('[WebSocket] Error:', error);
          this.isConnecting = false;
          this.emit('error', error);
          reject(error);
        };

        this.ws.onclose = (event) => {
          console.log('[WebSocket] Connection closed:', event.code, event.reason);
          this.isConnecting = false;
          this.stopHeartbeat();
          this.emit('disconnected');
          
          // Attempt to reconnect if not a normal closure
          if (event.code !== 1000 && event.code !== 1001) {
            this.scheduleReconnect();
          }
        };
      } catch (error) {
        console.error('[WebSocket] Failed to create connection:', error);
        this.isConnecting = false;
        reject(error);
      }
    });
  }

  /**
   * Disconnect from WebSocket server
   */
  public disconnect(): void {
    this.stopHeartbeat();
    this.cancelReconnect();
    
    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }
    
    this.emit('disconnected');
  }

  /**
   * Send a message through WebSocket
   */
  public send(type: string, payload: any): void {
    const message: WebSocketMessage = {
      type,
      payload,
      timestamp: new Date().toISOString()
    };

    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      // Queue message for later delivery
      this.messageQueue.push(message);
      
      // Attempt to connect if not connected
      if (!this.isConnecting && this.ws?.readyState !== WebSocket.CONNECTING) {
        this.connect().catch(console.error);
      }
    }
  }

  /**
   * Subscribe to specific message types
   */
  public subscribe(type: string, callback: (data: any) => void): () => void {
    if (!this.subscribers.has(type)) {
      this.subscribers.set(type, new Set());
    }
    
    this.subscribers.get(type)!.add(callback);
    
    // Return unsubscribe function
    return () => {
      const callbacks = this.subscribers.get(type);
      if (callbacks) {
        callbacks.delete(callback);
        if (callbacks.size === 0) {
          this.subscribers.delete(type);
        }
      }
    };
  }

  /**
   * Request deployment status
   */
  public requestDeploymentStatus(deploymentId: string): void {
    this.send('deployment.status', { deploymentId });
  }

  /**
   * Request resource metrics
   */
  public requestResourceMetrics(): void {
    this.send('metrics.request', {});
  }

  /**
   * Subscribe to deployment progress updates
   */
  public onDeploymentProgress(callback: (progress: DeploymentProgress) => void): () => void {
    return this.subscribe('deployment.progress', callback);
  }

  /**
   * Subscribe to resource metrics updates
   */
  public onResourceMetrics(callback: (metrics: ResourceMetrics) => void): () => void {
    return this.subscribe('metrics.update', callback);
  }

  /**
   * Subscribe to model health updates
   */
  public onModelHealth(callback: (health: any) => void): () => void {
    return this.subscribe('model.health', callback);
  }

  /**
   * Handle incoming WebSocket messages
   */
  private handleMessage(message: WebSocketMessage): void {
    // Emit to general listeners
    this.emit('message', message);
    
    // Notify specific subscribers
    const callbacks = this.subscribers.get(message.type);
    if (callbacks) {
      callbacks.forEach(callback => {
        try {
          callback(message.payload);
        } catch (error) {
          console.error(`[WebSocket] Error in subscriber for ${message.type}:`, error);
        }
      });
    }

    // Handle special message types
    switch (message.type) {
      case 'pong':
        // Heartbeat response
        break;
      
      case 'deployment.progress':
        this.emit('deploymentProgress', message.payload);
        break;
      
      case 'metrics.update':
        this.emit('resourceMetrics', message.payload);
        break;
      
      case 'model.health':
        this.emit('modelHealth', message.payload);
        break;
      
      case 'error':
        console.error('[WebSocket] Server error:', message.payload);
        this.emit('serverError', message.payload);
        break;
    }
  }

  /**
   * Start heartbeat to keep connection alive
   */
  private startHeartbeat(): void {
    this.stopHeartbeat();
    
    this.heartbeatTimer = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.send('ping', {});
      }
    }, 30000); // Send heartbeat every 30 seconds
  }

  /**
   * Stop heartbeat
   */
  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  /**
   * Schedule reconnection attempt
   */
  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('[WebSocket] Max reconnection attempts reached');
      this.emit('maxReconnectAttemptsReached');
      return;
    }

    this.reconnectAttempts++;
    const delay = Math.min(this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1), 30000);
    
    console.log(`[WebSocket] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
    
    this.reconnectTimer = setTimeout(() => {
      this.connect().catch(error => {
        console.error('[WebSocket] Reconnection failed:', error);
      });
    }, delay);
  }

  /**
   * Cancel scheduled reconnection
   */
  private cancelReconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  /**
   * Flush queued messages
   */
  private flushMessageQueue(): void {
    while (this.messageQueue.length > 0 && this.ws?.readyState === WebSocket.OPEN) {
      const message = this.messageQueue.shift();
      if (message) {
        this.ws.send(JSON.stringify(message));
      }
    }
  }

  /**
   * Get connection status
   */
  public get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  /**
   * Get connection state
   */
  public get connectionState(): string {
    if (!this.ws) return 'disconnected';
    
    switch (this.ws.readyState) {
      case WebSocket.CONNECTING:
        return 'connecting';
      case WebSocket.OPEN:
        return 'connected';
      case WebSocket.CLOSING:
        return 'closing';
      case WebSocket.CLOSED:
        return 'closed';
      default:
        return 'unknown';
    }
  }
}

// Export singleton instance
export const wsService = WebSocketService.getInstance();
export default wsService;
export type { WebSocketService };