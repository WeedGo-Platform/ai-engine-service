import axios from 'axios';
import { API_BASE_URL } from './client';

export interface Promotion {
  id: string;
  code: string;
  discount_percentage: number;
  description: string;
  active: boolean;
  valid_from: string;
  valid_until: string;
  usage_limit?: number;
  times_used?: number;
}

export interface PromoValidationResponse {
  valid: boolean;
  discount?: number;
  message?: string;
}

class PromotionsAPI {
  private baseURL = `${API_BASE_URL}/api/promotions`;

  async getActivePromotions(): Promise<Promotion[]> {
    try {
      const response = await axios.get(`${this.baseURL}/active`);
      return response.data.promotions || [];
    } catch (error) {
      console.error('Error fetching promotions:', error);
      return [];
    }
  }

  async validatePromoCode(code: string, orderTotal?: number): Promise<PromoValidationResponse> {
    try {
      const response = await axios.post(`${this.baseURL}/validate`, {
        code: code.toUpperCase(),
        order_total: orderTotal
      });

      return {
        valid: response.data.valid,
        discount: response.data.discount_percentage,
        message: response.data.message
      };
    } catch (error: any) {
      return {
        valid: false,
        message: error.response?.data?.message || 'Invalid promo code'
      };
    }
  }

  async applyPromoCode(code: string, cartId: string): Promise<PromoValidationResponse> {
    try {
      const response = await axios.post(`${this.baseURL}/apply`, {
        code: code.toUpperCase(),
        cart_id: cartId
      });

      return {
        valid: true,
        discount: response.data.discount_percentage,
        message: 'Promo code applied successfully'
      };
    } catch (error: any) {
      return {
        valid: false,
        message: error.response?.data?.message || 'Failed to apply promo code'
      };
    }
  }
}

export const promotionsAPI = new PromotionsAPI();