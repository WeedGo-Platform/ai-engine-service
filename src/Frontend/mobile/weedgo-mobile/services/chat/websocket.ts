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
  private maxReconnectAttempts = 10;
  private reconnectTimeout: NodeJS.Timeout | null = null;
  private baseReconnectDelay = 1000; // Start with 1 second
  private maxReconnectDelay = 30000; // Max 30 seconds
  private messageQueue: Message[] = [];
  private isConnected = false;
  private sessionId: string | null = null;
  private listeners: Map<string, Set<Function>> = new Map();
  private pingInterval: NodeJS.Timeout | null = null;
  private wsUrl: string = '';
  private storeId: string | null = null;
  private userId: string | null = null;
  private agentId: string | null = 'dispensary';  // Default to dispensary for mobile
  private personalityId: string | null = 'marcel';  // Default to marcel for mobile

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

  async connect(storeId?: string, userId?: string, agentId?: string, personalityId?: string) {
    if (this.isConnected && this.ws?.readyState === WebSocket.OPEN) {
      console.log('Already connected to chat');
      return;
    }

    this.storeId = storeId || this.storeId;
    this.userId = userId || this.userId;
    this.agentId = agentId || this.agentId;
    this.personalityId = personalityId || this.personalityId;

    // Build WebSocket URL with query parameters
    // Use API URL and convert to WebSocket protocol
    const apiUrl = process.env.EXPO_PUBLIC_API_URL || 'http://10.0.0.29:5024';
    const baseUrl = apiUrl.replace('http://', 'ws://').replace('https://', 'wss://');
    const params = new URLSearchParams();
    if (this.sessionId) params.append('session_id', this.sessionId);
    if (this.storeId) params.append('store_id', this.storeId);
    if (this.userId) params.append('user_id', this.userId);
    // Don't send agent_id and personality_id as URL params - they're managed via session_update

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

        // Don't send session_update here - wait for connection message with session_id
        // The server needs to send us the session_id first

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

                // Add a small delay to ensure session is fully established on backend
                setTimeout(() => {
                  // NOW send session_update after session is established
                  const agentToSend = this.agentId || 'dispensary';
                  const personalityToSend = this.personalityId || 'marcel';

                  this.sendRawMessage({
                    type: 'session_update',
                    agent: agentToSend,
                    personality: personalityToSend
                  });
                  console.log(`[WebSocket] Session ${data.session_id} established, setting agent: ${agentToSend}, personality: ${personalityToSend}`);
                }, 100); // 100ms delay to ensure session is ready

                // Emit connected event with session ID
                this.emit('connected', { sessionId: data.session_id });

                // Process queued messages now that session is established
                this.processMessageQueue();
              }
              break;

            case 'session':
              // Save new session ID
              if (data.session_id) {
                const isNewSession = this.sessionId !== data.session_id;
                this.saveSessionId(data.session_id);

                // If this is a new session, send session_update
                if (isNewSession) {
                  const agentToSend = this.agentId || 'dispensary';
                  const personalityToSend = this.personalityId || 'marcel';

                  this.sendRawMessage({
                    type: 'session_update',
                    agent: agentToSend,
                    personality: personalityToSend
                  });
                  console.log(`[WebSocket] New session ${data.session_id}, setting agent: ${agentToSend}, personality: ${personalityToSend}`);

                  // Emit connected event with session ID
                  this.emit('connected', { sessionId: data.session_id });

                  // Process queued messages
                  this.processMessageQueue();
                }
              }
              break;

            case 'session_updated':
              // Log successful personality update
              console.log('Personality updated:', data.agent, data.personality);
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

      this.ws.onerror = (error: any) => {
        // Only log critical errors, not connection failures during reconnects
        if (this.reconnectAttempts === 0) {
          console.error('WebSocket error:', error);
          this.emit('error', {
            message: 'Connection error',
            error,
            isRetrying: this.reconnectAttempts < this.maxReconnectAttempts,
          });
        } else {
          // During reconnection, only log to console
          console.log(`WebSocket reconnection attempt ${this.reconnectAttempts} failed`);
        }
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

    // Use exponential backoff starting from 1 second
    const delay = Math.min(
      this.baseReconnectDelay * Math.pow(1.5, this.reconnectAttempts),
      this.maxReconnectDelay
    );
    this.reconnectAttempts++;

    console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts} of ${this.maxReconnectAttempts})`);

    // Emit reconnecting event with attempt info
    this.emit('reconnecting', {
      attempt: this.reconnectAttempts,
      maxAttempts: this.maxReconnectAttempts,
      delay,
    });

    this.reconnectTimeout = setTimeout(() => {
      if (this.reconnectAttempts <= this.maxReconnectAttempts) {
        this.setupWebSocket();
      } else {
        console.error('Max reconnection attempts reached. Connection failed.');
        this.emit('connection_failed', {
          reason: 'Max reconnection attempts reached',
        });
      }
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
      // Don't send agent/personality in messages - they're managed at session level
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
      this.connect(this.storeId, this.userId, this.agentId, this.personalityId);
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

  // Manual reconnection
  reconnect() {
    // Reset attempts for manual reconnection
    this.reconnectAttempts = 0;

    if (this.ws?.readyState === WebSocket.OPEN) {
      this.disconnect();
    }

    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    // Immediate reconnect for manual trigger
    this.setupWebSocket();
  }

  // Reset connection attempts (useful when app comes back to foreground)
  resetReconnectAttempts() {
    this.reconnectAttempts = 0;
  }

  // Getters
  getIsConnected() {
    return this.isConnected && this.ws?.readyState === WebSocket.OPEN;
  }

  sendSessionUpdate(agentId?: string, personalityId?: string) {
    const updateMessage = {
      type: 'session_update',
      agent: agentId || this.agentId,
      personality: personalityId || this.personalityId
    };

    console.log('[WebSocket] Sending session update:', updateMessage);

    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(updateMessage));
      // Update local references
      if (agentId) this.agentId = agentId;
      if (personalityId) this.personalityId = personalityId;
    } else {
      console.warn('[WebSocket] Cannot send session update - WebSocket not connected');
    }
  }

  getSessionId() {
    return this.sessionId;
  }

  getConnectionState() {
    return {
      isConnected: this.isConnected,
      reconnectAttempts: this.reconnectAttempts,
      maxReconnectAttempts: this.maxReconnectAttempts,
      readyState: this.ws?.readyState,
    };
  }
}

// Export singleton instance
const chatWebSocketService = new ChatWebSocketService();
export default chatWebSocketService;