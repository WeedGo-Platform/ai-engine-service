import { apiClient } from './client';

export interface Promotion {
  id: string;
  title: string;
  description: string;
  discountType: 'percentage' | 'fixed' | 'bogo' | 'freebie';
  discountValue?: number;
  code?: string;
  image?: string;
  validFrom: string;
  validTo: string;
  minimumPurchase?: number;
  category?: string;
  isActive: boolean;
  usageLimit?: number;
  usageCount?: number;
}

export interface PromotionsResponse {
  data: Promotion[];
  total?: number;
}

class PromoService {
  async getPromotions(): Promise<PromotionsResponse> {
    try {
      const response = await apiClient.get('/api/promotions');
      return response.data;
    } catch (error) {
      console.error('Error fetching promotions:', error);
      return { data: [] };
    }
  }

  async getPromotion(id: string): Promise<Promotion | null> {
    try {
      const response = await apiClient.get(`/api/promotions/${id}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching promotion:', error);
      return null;
    }
  }

  async applyPromoCode(code: string): Promise<{ valid: boolean; discount?: number; message?: string }> {
    try {
      const response = await apiClient.post('/api/promotions/apply', { code });
      return response.data;
    } catch (error) {
      console.error('Error applying promo code:', error);
      return { valid: false, message: 'Invalid promo code' };
    }
  }
}

export const promoService = new PromoService();