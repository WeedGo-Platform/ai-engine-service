import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5024';

export interface ChatMessage {
  text: string;
  context?: any;
}

export interface ChatResponse {
  message: string;
  products?: any[];
  suggestions?: string[];
}

class ChatService {
  private apiClient = axios.create({
    baseURL: `${API_BASE_URL}/api`,
    headers: {
      'Content-Type': 'application/json'
    }
  });

  constructor() {
    // Add auth token to requests if available
    this.apiClient.interceptors.request.use((config) => {
      const token = localStorage.getItem('authToken');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });
  }

  async sendMessage(text: string, context?: any): Promise<ChatResponse> {
    try {
      const response = await this.apiClient.post('/chat/search', {
        query: text,
        context,
        store_id: localStorage.getItem('selected_store_id')
      });

      return {
        message: response.data.response || response.data.message || "I found some products that might interest you.",
        products: response.data.products || [],
        suggestions: response.data.suggestions || []
      };
    } catch (error) {
      console.error('Chat service error:', error);

      // Try to search products directly as fallback
      try {
        const searchResponse = await this.apiClient.get('/products', {
          params: {
            search: text,
            limit: 5
          }
        });

        return {
          message: `I found ${searchResponse.data.data?.length || 0} products matching "${text}".`,
          products: searchResponse.data.data || [],
          suggestions: []
        };
      } catch (fallbackError) {
        return {
          message: "I'm having trouble connecting to the server. Please try again later.",
          products: [],
          suggestions: []
        };
      }
    }
  }

  async getProductRecommendations(preferences: any): Promise<any[]> {
    try {
      const response = await this.apiClient.post('/chat/recommendations', {
        preferences,
        store_id: localStorage.getItem('selected_store_id')
      });

      return response.data.products || [];
    } catch (error) {
      console.error('Recommendations error:', error);
      return [];
    }
  }

  async searchProducts(query: string): Promise<any[]> {
    try {
      const response = await this.apiClient.get('/kiosk/products/search', {
        params: {
          q: query,
          store_id: localStorage.getItem('selected_store_id')
        }
      });

      return response.data.products || [];
    } catch (error) {
      console.error('Product search error:', error);

      // Fallback to regular products endpoint
      try {
        const fallbackResponse = await this.apiClient.get('/products', {
          params: {
            search: query,
            limit: 20
          }
        });
        return fallbackResponse.data.data || [];
      } catch (fallbackError) {
        console.error('Fallback search error:', fallbackError);
        return [];
      }
    }
  }
}

export const chatService = new ChatService();