import AsyncStorage from '@react-native-async-storage/async-storage';

export interface Message {
  id?: string;
  type: 'message' | 'product' | 'action' | 'error';
  content: string;
  products?: any[];
  action?: any;
  timestamp: number;
  isVoice?: boolean;
  context?: {
    store_id?: string;
    user_id?: string;
  };
}

export interface ChatResponse {
  id: string;
  type: 'text' | 'product' | 'action';
  content: string;
  products?: any[];
  action?: any;
  timestamp: number;
}

class ChatWebSocketService {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectTimeout: NodeJS.Timeout | null = null;
  private messageQueue: Message[] = [];
  private isConnected = false;
  private sessionId: string | null = null;
  private listeners: Map<string, Set<Function>> = new Map();
  private pingInterval: NodeJS.Timeout | null = null;
  private wsUrl: string = '';
  private storeId: string | null = null;
  private userId: string | null = null;

  constructor() {
    this.loadSessionId();
  }

  private async loadSessionId() {
    try {
      const id = await AsyncStorage.getItem('chat_session_id');
      if (id) {
        this.sessionId = id;
      }
    } catch (error) {
      console.error('Failed to load session ID:', error);
    }
  }

  private async saveSessionId(id: string) {
    try {
      this.sessionId = id;
      await AsyncStorage.setItem('chat_session_id', id);
    } catch (error) {
      console.error('Failed to save session ID:', error);
    }
  }

  async connect(storeId?: string, userId?: string) {
    if (this.isConnected && this.ws?.readyState === WebSocket.OPEN) {
      console.log('Already connected to chat');
      return;
    }

    this.storeId = storeId || this.storeId;
    this.userId = userId || this.userId;

    // Build WebSocket URL with query parameters
    const baseUrl = process.env.EXPO_PUBLIC_WS_URL || 'ws://10.0.0.29:5024';
    const params = new URLSearchParams();
    if (this.sessionId) params.append('session_id', this.sessionId);
    if (this.storeId) params.append('store_id', this.storeId);
    if (this.userId) params.append('user_id', this.userId);

    this.wsUrl = `${baseUrl}/chat/ws${params.toString() ? '?' + params.toString() : ''}`;

    this.setupWebSocket();
  }

  private setupWebSocket() {
    try {
      console.log('Connecting to WebSocket:', this.wsUrl);
      this.ws = new WebSocket(this.wsUrl);

      this.ws.onopen = () => {
        console.log('WebSocket connected');
        this.isConnected = true;
        this.reconnectAttempts = 0;

        // Don't send init message - the server handles connection automatically
        // The server sends a 'connection' type message upon successful connection

        // Emit connected event
        this.emit('connected', { sessionId: this.sessionId });

        // Process queued messages
        this.processMessageQueue();

        // Start ping interval to keep connection alive
        this.startPingInterval();
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('Received message:', data);

          // Handle different message types
          switch (data.type) {
            case 'connection':
              // Handle initial connection message from server
              if (data.session_id) {
                this.saveSessionId(data.session_id);
              }
              break;

            case 'session':
              // Save new session ID
              if (data.session_id) {
                this.saveSessionId(data.session_id);
              }
              break;

            case 'response':
            case 'message':
              this.emit('response', {
                id: data.id || `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
                type: data.response_type || 'text',
                content: data.content || data.message,
                products: data.products,
                action: data.action,
                timestamp: data.timestamp || Date.now(),
              });
              break;

            case 'product_card':
              this.emit('product_card', {
                message: data.message,
                products: data.products,
              });
              break;

            case 'typing':
              this.emit('typing', {});
              break;

            case 'error':
              this.emit('error', {
                message: data.message || 'An error occurred',
                code: data.code,
              });
              break;

            case 'pong':
              // Pong received, connection is alive
              break;

            default:
              console.log('Unknown message type:', data.type);
              // Emit as generic response
              this.emit('response', data);
          }
        } catch (error) {
          console.error('Failed to parse message:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.emit('error', { message: 'Connection error', error });
      };

      this.ws.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason);
        this.isConnected = false;
        this.stopPingInterval();
        this.emit('disconnected', {});

        // Attempt to reconnect
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          this.scheduleReconnect();
        }
      };
    } catch (error) {
      console.error('Failed to setup WebSocket:', error);
      this.emit('error', { message: 'Failed to connect', error });
    }
  }

  private startPingInterval() {
    this.stopPingInterval();
    this.pingInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.sendRawMessage({ type: 'ping' });
      }
    }, 30000); // Ping every 30 seconds
  }

  private stopPingInterval() {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }

  private scheduleReconnect() {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
    }

    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
    this.reconnectAttempts++;

    console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);

    this.reconnectTimeout = setTimeout(() => {
      this.setupWebSocket();
    }, delay);
  }

  private processMessageQueue() {
    while (this.messageQueue.length > 0) {
      const message = this.messageQueue.shift();
      if (message) {
        this.sendRawMessage(message);
      }
    }
  }

  private sendRawMessage(data: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      console.log('WebSocket not ready, queueing message');
      this.messageQueue.push(data);
    }
  }

  sendMessage(content: string, isVoice: boolean = false, context?: any) {
    const message = {
      type: 'message',
      content,
      is_voice: isVoice,
      timestamp: Date.now(),
      session_id: this.sessionId,
      store_id: context?.store_id || this.storeId,
      user_id: context?.user_id || this.userId,
    };

    this.sendRawMessage(message);
  }

  disconnect() {
    this.stopPingInterval();

    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    this.isConnected = false;
    this.reconnectAttempts = 0;
    this.messageQueue = [];
  }

  clearSession() {
    this.sessionId = null;
    AsyncStorage.removeItem('chat_session_id');

    // Reconnect with new session
    if (this.isConnected) {
      this.disconnect();
      this.connect(this.storeId, this.userId);
    }
  }

  // Event emitter methods
  on(event: string, callback: Function) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)?.add(callback);
  }

  off(event: string, callback: Function) {
    this.listeners.get(event)?.delete(callback);
  }

  private emit(event: string, data: any) {
    const callbacks = this.listeners.get(event);
    if (callbacks) {
      callbacks.forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`Error in ${event} listener:`, error);
        }
      });
    }
  }

  // Getters
  getIsConnected() {
    return this.isConnected;
  }

  getSessionId() {
    return this.sessionId;
  }
}

// Export singleton instance
const chatWebSocketService = new ChatWebSocketService();
export default chatWebSocketService;