/**
 * WebSocket Service for Real-time AGI Updates
 * Implements automatic reconnection, typed message handling, and event-driven architecture
 * Following SOLID principles with clear separation of concerns
 */

import { EventEmitter } from 'events';
import {
  IAgent, IAgentTask, IActivity, ISecurityEvent,
  ILearningMetrics, IPattern, ISystemStats
} from '../types';

// WebSocket Configuration
const WS_BASE_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:5024';
const WS_RECONNECT_INTERVAL = 5000; // 5 seconds
const WS_MAX_RECONNECT_ATTEMPTS = 10;
const WS_HEARTBEAT_INTERVAL = 30000; // 30 seconds

/**
 * WebSocket message types for type-safe communication
 */
export enum WSMessageType {
  // Connection events
  CONNECTION_ESTABLISHED = 'connection_established',
  CONNECTION_CLOSED = 'connection_closed',
  HEARTBEAT = 'heartbeat',
  PONG = 'pong',

  // Agent events
  AGENT_STATUS_CHANGED = 'agent_status_changed',
  AGENT_TASK_CREATED = 'agent_task_created',
  AGENT_TASK_UPDATED = 'agent_task_updated',
  AGENT_TASK_COMPLETED = 'agent_task_completed',
  AGENT_METRICS_UPDATED = 'agent_metrics_updated',

  // System events
  SYSTEM_STATS_UPDATED = 'system_stats_updated',
  ACTIVITY_CREATED = 'activity_created',

  // Security events
  SECURITY_EVENT_TRIGGERED = 'security_event_triggered',
  SECURITY_STATUS_CHANGED = 'security_status_changed',
  RATE_LIMIT_EXCEEDED = 'rate_limit_exceeded',

  // Learning events
  LEARNING_METRICS_UPDATED = 'learning_metrics_updated',
  PATTERN_DETECTED = 'pattern_detected',
  FEEDBACK_RECEIVED = 'feedback_received',

  // Error events
  ERROR = 'error',
  WARNING = 'warning'
}

/**
 * Base WebSocket message structure
 */
export interface IWSMessage<T = any> {
  type: WSMessageType;
  timestamp: string;
  data?: T;
  metadata?: {
    source?: string;
    correlation_id?: string;
    user_id?: string;
  };
}

/**
 * WebSocket connection state
 */
export enum WSConnectionState {
  CONNECTING = 'connecting',
  CONNECTED = 'connected',
  DISCONNECTED = 'disconnected',
  RECONNECTING = 'reconnecting',
  ERROR = 'error'
}

/**
 * WebSocket Service Options
 */
export interface IWebSocketOptions {
  url?: string;
  autoReconnect?: boolean;
  maxReconnectAttempts?: number;
  reconnectInterval?: number;
  heartbeatInterval?: number;
  authToken?: string;
}

/**
 * WebSocket Service Class
 * Manages real-time communication with the AGI backend
 */
export class WebSocketService extends EventEmitter {
  private ws?: WebSocket;
  private url: string;
  private connectionState: WSConnectionState = WSConnectionState.DISCONNECTED;
  private reconnectAttempts = 0;
  private reconnectTimer?: NodeJS.Timeout;
  private heartbeatTimer?: NodeJS.Timeout;
  private messageQueue: IWSMessage[] = [];
  private options: Required<IWebSocketOptions>;
  private listeners = new Map<string, Set<Function>>();

  constructor(options: IWebSocketOptions = {}) {
    super();

    this.url = options.url || `${WS_BASE_URL}/ws/agi`;
    this.options = {
      url: this.url,
      autoReconnect: options.autoReconnect ?? true,
      maxReconnectAttempts: options.maxReconnectAttempts ?? WS_MAX_RECONNECT_ATTEMPTS,
      reconnectInterval: options.reconnectInterval ?? WS_RECONNECT_INTERVAL,
      heartbeatInterval: options.heartbeatInterval ?? WS_HEARTBEAT_INTERVAL,
      authToken: options.authToken || ''
    };
  }

  /**
   * Connect to WebSocket server
   */
  public connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        resolve();
        return;
      }

      this.connectionState = WSConnectionState.CONNECTING;
      this.emit('stateChange', this.connectionState);

      try {
        // Add auth token to URL if available
        const wsUrl = this.options.authToken
          ? `${this.url}?token=${this.options.authToken}`
          : this.url;

        this.ws = new WebSocket(wsUrl);
        this.setupEventHandlers(resolve, reject);
      } catch (error) {
        this.connectionState = WSConnectionState.ERROR;
        this.emit('stateChange', this.connectionState);
        reject(error);
      }
    });
  }

  /**
   * Setup WebSocket event handlers
   */
  private setupEventHandlers(
    onConnect?: () => void,
    onError?: (error: any) => void
  ): void {
    if (!this.ws) return;

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.connectionState = WSConnectionState.CONNECTED;
      this.reconnectAttempts = 0;

      this.emit('stateChange', this.connectionState);
      this.emit('connected');

      this.startHeartbeat();
      this.flushMessageQueue();

      if (onConnect) onConnect();
    };

    this.ws.onmessage = (event) => {
      try {
        const message: IWSMessage = JSON.parse(event.data);
        this.handleMessage(message);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
        this.emit('error', error);
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      this.connectionState = WSConnectionState.ERROR;
      this.emit('stateChange', this.connectionState);
      this.emit('error', error);

      if (onError) onError(error);
    };

    this.ws.onclose = (event) => {
      console.log('WebSocket disconnected', { code: event.code, reason: event.reason });
      this.connectionState = WSConnectionState.DISCONNECTED;
      this.emit('stateChange', this.connectionState);
      this.emit('disconnected', { code: event.code, reason: event.reason });

      this.stopHeartbeat();

      if (this.options.autoReconnect &&
          this.reconnectAttempts < this.options.maxReconnectAttempts) {
        this.scheduleReconnect();
      }
    };
  }

  /**
   * Handle incoming WebSocket messages
   */
  private handleMessage(message: IWSMessage): void {
    // Emit raw message for debugging
    this.emit('message', message);

    // Handle specific message types
    switch (message.type) {
      case WSMessageType.PONG:
        // Heartbeat response received
        break;

      case WSMessageType.AGENT_STATUS_CHANGED:
        this.emit('agentStatusChanged', message.data as IAgent);
        break;

      case WSMessageType.AGENT_TASK_CREATED:
      case WSMessageType.AGENT_TASK_UPDATED:
      case WSMessageType.AGENT_TASK_COMPLETED:
        this.emit('agentTaskUpdate', message.data as IAgentTask);
        break;

      case WSMessageType.SYSTEM_STATS_UPDATED:
        this.emit('systemStatsUpdated', message.data as ISystemStats);
        break;

      case WSMessageType.ACTIVITY_CREATED:
        this.emit('activityCreated', message.data as IActivity);
        break;

      case WSMessageType.SECURITY_EVENT_TRIGGERED:
        this.emit('securityEvent', message.data as ISecurityEvent);
        break;

      case WSMessageType.LEARNING_METRICS_UPDATED:
        this.emit('learningMetricsUpdated', message.data as ILearningMetrics);
        break;

      case WSMessageType.PATTERN_DETECTED:
        this.emit('patternDetected', message.data as IPattern);
        break;

      case WSMessageType.ERROR:
        this.emit('serverError', message.data);
        break;

      case WSMessageType.WARNING:
        this.emit('serverWarning', message.data);
        break;

      default:
        // Emit unknown message types for extensibility
        this.emit(message.type, message.data);
    }

    // Notify type-specific listeners
    this.notifyListeners(message.type, message);
  }

  /**
   * Send message through WebSocket
   */
  public send<T = any>(type: WSMessageType, data?: T, metadata?: any): void {
    const message: IWSMessage<T> = {
      type,
      timestamp: new Date().toISOString(),
      data,
      metadata
    };

    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      // Queue message if not connected
      this.messageQueue.push(message);

      // Attempt to reconnect if not already trying
      if (this.connectionState === WSConnectionState.DISCONNECTED &&
          this.options.autoReconnect) {
        this.connect();
      }
    }
  }

  /**
   * Subscribe to specific message types
   */
  public subscribe(
    type: WSMessageType | string,
    handler: (data: any) => void
  ): () => void {
    if (!this.listeners.has(type)) {
      this.listeners.set(type, new Set());
    }

    this.listeners.get(type)!.add(handler);

    // Return unsubscribe function
    return () => {
      const handlers = this.listeners.get(type);
      if (handlers) {
        handlers.delete(handler);
        if (handlers.size === 0) {
          this.listeners.delete(type);
        }
      }
    };
  }

  /**
   * Notify type-specific listeners
   */
  private notifyListeners(type: string, message: IWSMessage): void {
    const handlers = this.listeners.get(type);
    if (handlers) {
      handlers.forEach(handler => {
        try {
          handler(message.data);
        } catch (error) {
          console.error(`Error in message handler for ${type}:`, error);
        }
      });
    }
  }

  /**
   * Disconnect from WebSocket server
   */
  public disconnect(): void {
    this.options.autoReconnect = false;

    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = undefined;
    }

    this.stopHeartbeat();

    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = undefined;
    }

    this.connectionState = WSConnectionState.DISCONNECTED;
    this.emit('stateChange', this.connectionState);
  }

  /**
   * Schedule reconnection attempt
   */
  private scheduleReconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
    }

    this.connectionState = WSConnectionState.RECONNECTING;
    this.emit('stateChange', this.connectionState);
    this.reconnectAttempts++;

    const delay = this.calculateReconnectDelay();
    console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);

    this.reconnectTimer = setTimeout(() => {
      this.connect().catch(error => {
        console.error('Reconnection failed:', error);
      });
    }, delay);
  }

  /**
   * Calculate reconnect delay with exponential backoff
   */
  private calculateReconnectDelay(): number {
    const baseDelay = this.options.reconnectInterval;
    const maxDelay = 60000; // 1 minute max
    const delay = Math.min(baseDelay * Math.pow(1.5, this.reconnectAttempts - 1), maxDelay);
    return delay + Math.random() * 1000; // Add jitter
  }

  /**
   * Start heartbeat to keep connection alive
   */
  private startHeartbeat(): void {
    this.stopHeartbeat();

    this.heartbeatTimer = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.send(WSMessageType.HEARTBEAT);
      }
    }, this.options.heartbeatInterval);
  }

  /**
   * Stop heartbeat timer
   */
  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = undefined;
    }
  }

  /**
   * Flush queued messages
   */
  private flushMessageQueue(): void {
    while (this.messageQueue.length > 0 &&
           this.ws &&
           this.ws.readyState === WebSocket.OPEN) {
      const message = this.messageQueue.shift();
      if (message) {
        this.ws.send(JSON.stringify(message));
      }
    }
  }

  /**
   * Get current connection state
   */
  public getConnectionState(): WSConnectionState {
    return this.connectionState;
  }

  /**
   * Check if connected
   */
  public isConnected(): boolean {
    return this.connectionState === WSConnectionState.CONNECTED;
  }

  /**
   * Update authentication token
   */
  public updateAuthToken(token: string): void {
    this.options.authToken = token;

    // Reconnect with new token if currently connected
    if (this.isConnected()) {
      this.disconnect();
      this.options.autoReconnect = true;
      this.connect();
    }
  }

  /**
   * Get WebSocket statistics
   */
  public getStats(): {
    state: WSConnectionState;
    reconnectAttempts: number;
    queuedMessages: number;
    listeners: number;
  } {
    return {
      state: this.connectionState,
      reconnectAttempts: this.reconnectAttempts,
      queuedMessages: this.messageQueue.length,
      listeners: this.listeners.size
    };
  }
}

// Export singleton instance
export const wsService = new WebSocketService();

// Export for testing
export default WebSocketService;