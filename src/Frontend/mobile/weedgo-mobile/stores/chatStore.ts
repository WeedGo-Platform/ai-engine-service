import { create } from 'zustand';
import AsyncStorage from '@react-native-async-storage/async-storage';
import chatWebSocketService, { ChatResponse } from '../services/chat/websocket';
import { useAuthStore } from './authStore';
import useStoreStore from './storeStore';
import useCartStore from './cartStore';

export interface ChatAction {
  type: 'add_to_cart' | 'view_product' | 'navigate' | 'search';
  payload: any;
}

export interface ChatMessage {
  id: string;
  type: 'user' | 'assistant' | 'product' | 'action' | 'system';
  content: string;
  products?: any[];
  action?: ChatAction;
  timestamp: Date;
  isVoice?: boolean;
  status?: 'sending' | 'sent' | 'failed';
}

interface ChatStore {
  messages: ChatMessage[];
  isTyping: boolean;
  suggestions: string[];
  isConnected: boolean;
  sessionId: string | null;
  unreadCount: number;

  // Actions
  connect: () => Promise<void>;
  disconnect: () => void;
  sendMessage: (text: string, isVoice?: boolean) => void;
  addMessage: (message: ChatMessage) => void;
  setTyping: (typing: boolean) => void;
  loadHistory: () => Promise<void>;
  clearChat: () => void;
  markAsRead: () => void;

  // Product actions
  addProductToCart: (product: any) => void;
  showProductDetail: (productId: string) => void;

  // Suggestions
  setSuggestions: (suggestions: string[]) => void;

  // Private helper
  saveHistory: (messages: ChatMessage[]) => Promise<void>;
}

const CHAT_HISTORY_KEY = 'chat_history';
const MAX_HISTORY_MESSAGES = 50;

let messageIdCounter = 0;
const generateMessageId = (prefix: string) => `${prefix}_${Date.now()}_${++messageIdCounter}`;

const defaultSuggestions = [
  'Show me indica strains',
  'What has high THC?',
  'Best for sleep',
  'New arrivals',
  'Edibles under $30',
];

export const useChatStore = create<ChatStore>((set, get) => ({
  messages: [],
  isTyping: false,
  suggestions: defaultSuggestions,
  isConnected: false,
  sessionId: null,
  unreadCount: 0,

  connect: async () => {
    const auth = useAuthStore.getState();
    const currentStore = useStoreStore.getState().currentStore;
    const storeId = currentStore?.id || auth.user?.store_id;
    const userId = auth.user?.id;

    try {
      // Connect to WebSocket service
      await chatWebSocketService.connect(storeId, userId);

      // Listen for WebSocket events
      chatWebSocketService.on('connected', (data) => {
        console.log('Chat connected:', data);
        set({ isConnected: true, sessionId: data.sessionId });
      });

      chatWebSocketService.on('response', (data: ChatResponse) => {
        const message: ChatMessage = {
          id: data.id,
          type: 'assistant',
          content: data.content,
          products: data.products,
          action: data.action as ChatAction,
          timestamp: new Date(data.timestamp),
        };
        get().addMessage(message);
        set({ isTyping: false });
      });

      chatWebSocketService.on('product_card', (data) => {
        const message: ChatMessage = {
          id: generateMessageId('product'),
          type: 'product',
          content: data.message || 'Here are some products for you:',
          products: data.products,
          timestamp: new Date(),
        };
        get().addMessage(message);
        set({ isTyping: false });
      });

      chatWebSocketService.on('typing', () => {
        set({ isTyping: true });
      });

      chatWebSocketService.on('error', (error) => {
        console.error('Chat error:', error);
        set({ isTyping: false });

        // Add error message to chat
        const errorMessage: ChatMessage = {
          id: generateMessageId('error'),
          type: 'system',
          content: `Connection error: ${error.message || 'Please try again'}`,
          timestamp: new Date(),
        };
        get().addMessage(errorMessage);
      });

      chatWebSocketService.on('disconnected', () => {
        console.log('Chat disconnected');
        set({ isConnected: false });
      });
    } catch (error) {
      console.error('Failed to connect to chat:', error);
      set({ isConnected: false });
    }

    // Load history from local storage
    await get().loadHistory();

    // Add welcome message if no messages
    const messages = get().messages;
    if (messages.length === 0) {
      const welcomeMessage: ChatMessage = {
        id: generateMessageId('welcome'),
        type: 'assistant',
        content: 'Hi! I\'m your WeedGo AI assistant. How can I help you find the perfect cannabis products today?',
        timestamp: new Date(),
      };
      get().addMessage(welcomeMessage);
    }
  },

  disconnect: () => {
    chatWebSocketService.disconnect();
    set({ isConnected: false });
  },

  sendMessage: (text: string, isVoice = false) => {
    if (!text.trim()) return;

    const userMessage: ChatMessage = {
      id: generateMessageId('user'),
      type: 'user',
      content: text,
      timestamp: new Date(),
      isVoice,
      status: 'sending',
    };

    get().addMessage(userMessage);
    set({ isTyping: true });

    // Check if connected
    if (!chatWebSocketService.getIsConnected()) {
      // Try to reconnect
      const auth = useAuthStore.getState();
      const currentStore = useStoreStore.getState().currentStore;
      const storeId = currentStore?.id || auth.user?.store_id;
      const userId = auth.user?.id;

      chatWebSocketService.connect(storeId, userId).then(() => {
        // Send message after reconnection
        chatWebSocketService.sendMessage(text, isVoice, {
          store_id: storeId,
          user_id: userId,
        });
      }).catch((error) => {
        console.error('Failed to reconnect:', error);
        set((state) => ({
          messages: state.messages.map((msg) =>
            msg.id === userMessage.id ? { ...msg, status: 'failed' } : msg
          ),
          isTyping: false,
        }));
      });
    } else {
      // Send message through WebSocket
      const auth = useAuthStore.getState();
      const currentStore = useStoreStore.getState().currentStore;
      chatWebSocketService.sendMessage(text, isVoice, {
        store_id: currentStore?.id || auth.user?.store_id,
        user_id: auth.user?.id,
      });

      // Update message status after a brief delay
      setTimeout(() => {
        set((state) => ({
          messages: state.messages.map((msg) =>
            msg.id === userMessage.id ? { ...msg, status: 'sent' } : msg
          ),
        }));
      }, 100);
    }
  },

  addMessage: (message: ChatMessage) => {
    set((state) => {
      // Check if message with this ID already exists to prevent duplicates
      const existingIndex = state.messages.findIndex(msg => msg.id === message.id);

      let newMessages;
      if (existingIndex >= 0) {
        // Replace existing message
        newMessages = [...state.messages];
        newMessages[existingIndex] = message;
      } else {
        // Add new message
        newMessages = [...state.messages, message];
      }

      // Keep only the last MAX_HISTORY_MESSAGES
      const trimmedMessages = newMessages.slice(-MAX_HISTORY_MESSAGES);

      // Save to AsyncStorage
      get().saveHistory(trimmedMessages);

      // Increment unread count if assistant message and it's new
      const unreadCount = message.type === 'assistant' && existingIndex === -1
        ? state.unreadCount + 1
        : state.unreadCount;

      return { messages: trimmedMessages, unreadCount };
    });
  },

  setTyping: (typing: boolean) => {
    set({ isTyping: typing });
  },

  loadHistory: async () => {
    try {
      const historyJson = await AsyncStorage.getItem(CHAT_HISTORY_KEY);
      if (historyJson) {
        const history = JSON.parse(historyJson);
        const messages = history.map((msg: any) => ({
          ...msg,
          timestamp: new Date(msg.timestamp),
        }));
        set({ messages });
      }
    } catch (error) {
      console.error('Failed to load chat history:', error);
    }
  },

  saveHistory: async (messages: ChatMessage[]) => {
    try {
      const historyJson = JSON.stringify(messages);
      await AsyncStorage.setItem(CHAT_HISTORY_KEY, historyJson);
    } catch (error) {
      console.error('Failed to save chat history:', error);
    }
  },

  clearChat: () => {
    set({ messages: [], unreadCount: 0 });
    AsyncStorage.removeItem(CHAT_HISTORY_KEY);
    chatWebSocketService.clearSession();

    // Add welcome message
    const welcomeMessage: ChatMessage = {
      id: generateMessageId('welcome'),
      type: 'assistant',
      content: 'Chat cleared. How can I help you today?',
      timestamp: new Date(),
    };
    get().addMessage(welcomeMessage);
  },

  markAsRead: () => {
    set({ unreadCount: 0 });
  },

  addProductToCart: async (product: any) => {
    try {
      await useCartStore.getState().addItem(product, 1, product.size);

      // Add confirmation message
      const confirmMessage: ChatMessage = {
        id: generateMessageId('system'),
        type: 'system',
        content: `Added ${product.name} to your cart!`,
        timestamp: new Date(),
      };
      get().addMessage(confirmMessage);
    } catch (error) {
      console.error('Failed to add product to cart:', error);
      const errorMessage: ChatMessage = {
        id: generateMessageId('error'),
        type: 'system',
        content: `Failed to add product to cart. Please try again.`,
        timestamp: new Date(),
      };
      get().addMessage(errorMessage);
    }
  },

  showProductDetail: (productId: string) => {
    // This will be called from the chat UI component which has access to navigation
    console.log('Navigate to product:', productId);
    // The actual navigation will be handled by the component that uses this
  },

  setSuggestions: (suggestions: string[]) => {
    set({ suggestions });
  },
}));