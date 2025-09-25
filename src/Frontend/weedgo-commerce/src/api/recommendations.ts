import axios from 'axios';
import { authService } from '@/services/authService';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5024';

export interface RecommendedProduct {
  product_id: string;
  product_name: string;
  brand: string;
  category: string;
  unit_price: number;
  image_url?: string;
  thc_percentage?: number;
  cbd_percentage?: number;
  strain_type?: string;
  score?: number;
}

export interface CartRecommendations {
  complementary: RecommendedProduct[];
  frequently_bought: RecommendedProduct[];
  upsell: RecommendedProduct[];
}

export const recommendationsApi = {
  // Get recommendations for a specific product
  getSimilarProducts: async (productId: string, limit: number = 5): Promise<RecommendedProduct[]> => {
    try {
      // Get store ID from localStorage (saved by StoreContext)
      const storeId = localStorage.getItem('selected_store_id');
      if (!storeId) {
        console.warn('No store selected, cannot fetch recommendations');
        return [];
      }

      // URL encode the product ID to handle special characters
      const encodedProductId = encodeURIComponent(productId);
      const response = await axios.get(
        `${API_URL}/api/promotions/recommendations/similar/${encodedProductId}`,
        {
          params: { store_id: storeId, limit },
          headers: {
            'Content-Type': 'application/json'
          }
        }
      );
      return response.data.products || [];
    } catch (error) {
      console.error('Error fetching similar products:', error);
      return [];
    }
  },

  getComplementaryProducts: async (productId: string, limit: number = 5): Promise<RecommendedProduct[]> => {
    try {
      // Get store ID from localStorage (saved by StoreContext)
      const storeId = localStorage.getItem('selected_store_id');
      if (!storeId) {
        console.warn('No store selected, cannot fetch recommendations');
        return [];
      }

      const encodedProductId = encodeURIComponent(productId);
      const response = await axios.get(
        `${API_URL}/api/promotions/recommendations/complementary/${encodedProductId}`,
        {
          params: { store_id: storeId, limit },
          headers: {
            'Content-Type': 'application/json'
          }
        }
      );
      return response.data.products || [];
    } catch (error) {
      console.error('Error fetching complementary products:', error);
      return [];
    }
  },

  getFrequentlyBoughtTogether: async (productId: string, limit: number = 3): Promise<RecommendedProduct[]> => {
    try {
      // Get store ID from localStorage (saved by StoreContext)
      const storeId = localStorage.getItem('selected_store_id');
      if (!storeId) {
        console.warn('No store selected, cannot fetch recommendations');
        return [];
      }

      const encodedProductId = encodeURIComponent(productId);
      const response = await axios.get(
        `${API_URL}/api/promotions/recommendations/frequently-bought/${encodedProductId}`,
        {
          params: { store_id: storeId, limit },
          headers: {
            'Content-Type': 'application/json'
          }
        }
      );
      return response.data.products || [];
    } catch (error) {
      console.error('Error fetching frequently bought together:', error);
      return [];
    }
  },

  getUpsellProducts: async (productId: string, limit: number = 3): Promise<RecommendedProduct[]> => {
    try {
      // Get store ID from localStorage (saved by StoreContext)
      const storeId = localStorage.getItem('selected_store_id');
      if (!storeId) {
        console.warn('No store selected, cannot fetch recommendations');
        return [];
      }

      const encodedProductId = encodeURIComponent(productId);
      const response = await axios.get(
        `${API_URL}/api/promotions/recommendations/upsell/${encodedProductId}`,
        {
          params: { store_id: storeId, limit },
          headers: {
            'Content-Type': 'application/json'
          }
        }
      );
      return response.data.products || [];
    } catch (error) {
      console.error('Error fetching upsell products:', error);
      return [];
    }
  },

  // Get cart-based recommendations
  getCartRecommendations: async (): Promise<CartRecommendations> => {
    try {
      const sessionId = localStorage.getItem('session_id');
      const token = authService.getAccessToken();

      const headers: any = {
        'Content-Type': 'application/json'
      };

      if (sessionId) {
        headers['X-Session-ID'] = sessionId;
      }

      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await axios.get(
        `${API_URL}/api/cart/recommendations`,
        { headers }
      );

      return response.data || {
        complementary: [],
        frequently_bought: [],
        upsell: []
      };
    } catch (error) {
      console.error('Error fetching cart recommendations:', error);
      return {
        complementary: [],
        frequently_bought: [],
        upsell: []
      };
    }
  },

  // Get trending products
  getTrendingProducts: async (category?: string, limit: number = 10): Promise<RecommendedProduct[]> => {
    try {
      // Get store ID from localStorage (saved by StoreContext)
      const storeId = localStorage.getItem('selected_store_id');
      if (!storeId) {
        console.warn('No store selected, cannot fetch recommendations');
        return [];
      }

      const params: any = { store_id: storeId, limit };
      if (category) {
        params.category = category;
      }

      const response = await axios.get(
        `${API_URL}/api/promotions/recommendations/trending`,
        {
          params,
          headers: {
            'Content-Type': 'application/json'
          }
        }
      );
      return response.data.products || [];
    } catch (error) {
      console.error('Error fetching trending products:', error);
      return [];
    }
  },

  // Get personalized recommendations
  getPersonalizedRecommendations: async (limit: number = 10): Promise<RecommendedProduct[]> => {
    try {
      const token = authService.getAccessToken();
      if (!token) {
        // If no user is logged in, return trending products instead
        return await recommendationsApi.getTrendingProducts(undefined, limit);
      }

      // Extract tenant_id from the token (you may need to decode the JWT)
      // For now, we'll use a placeholder - you should implement proper JWT decoding
      const tenantId = localStorage.getItem('tenant_id');

      if (!tenantId) {
        return await recommendationsApi.getTrendingProducts(undefined, limit);
      }

      const response = await axios.get(
        `${API_URL}/api/promotions/recommendations/personalized/${tenantId}`,
        {
          params: { limit },
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          }
        }
      );
      return response.data.products || [];
    } catch (error) {
      console.error('Error fetching personalized recommendations:', error);
      // Fallback to trending products
      return await recommendationsApi.getTrendingProducts(undefined, limit);
    }
  }
};