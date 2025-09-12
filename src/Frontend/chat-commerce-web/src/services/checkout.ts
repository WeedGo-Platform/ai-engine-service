import api from './api';

export interface CheckoutSession {
  id: string;
  session_id: string;
  cart_session_id?: string;
  user_id?: string;
  tenant_id: string;
  store_id: string;
  
  // Customer info
  customer_email?: string;
  customer_phone?: string;
  customer_first_name?: string;
  customer_last_name?: string;
  
  // Fulfillment
  fulfillment_type: 'delivery' | 'pickup' | 'shipping';
  delivery_address?: DeliveryAddress;
  pickup_store_id?: string;
  pickup_datetime?: string;
  delivery_datetime?: string;
  delivery_instructions?: string;
  
  // Pricing
  subtotal: number;
  tax_amount: number;
  delivery_fee: number;
  service_fee: number;
  tip_amount: number;
  discount_amount: number;
  total_amount: number;
  
  // Discounts
  coupon_code?: string;
  discount_id?: string;
  
  // Payment
  payment_method?: string;
  payment_status: string;
  payment_intent_id?: string;
  
  // Compliance
  age_verified: boolean;
  age_verification_method?: string;
  id_verification_token?: string;
  medical_card_verified: boolean;
  medical_card_number?: string;
  
  // Status
  status: 'draft' | 'pending' | 'processing' | 'completed' | 'failed' | 'abandoned' | 'expired';
  expires_at: string;
  completed_at?: string;
  
  metadata?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface DeliveryAddress {
  street_address: string;
  unit_number?: string;
  city: string;
  province_state: string;
  postal_code: string;
  country?: string;
  latitude?: number;
  longitude?: number;
}

export interface InitiateCheckoutRequest {
  cart_session_id?: string;
  session_id?: string;
  tenant_id?: string;
  store_id?: string;
  fulfillment_type?: 'delivery' | 'pickup' | 'shipping';
  customer_email?: string;
  customer_phone?: string;
  customer_first_name?: string;
  customer_last_name?: string;
}

export interface UpdateCheckoutRequest {
  customer_email?: string;
  customer_phone?: string;
  customer_first_name?: string;
  customer_last_name?: string;
  fulfillment_type?: 'delivery' | 'pickup' | 'shipping';
  delivery_address?: DeliveryAddress;
  pickup_store_id?: string;
  pickup_datetime?: string;
  delivery_datetime?: string;
  delivery_instructions?: string;
  tip_amount?: number;
  age_verified?: boolean;
  age_verification_method?: string;
  medical_card_verified?: boolean;
  medical_card_number?: string;
}

export interface ApplyDiscountRequest {
  coupon_code: string;
}

export interface DiscountResponse {
  success: boolean;
  message: string;
  discount_amount?: number;
  discount_type?: string;
  discount_id?: string;
}

export interface TaxCalculationResponse {
  federal_tax: number;
  provincial_tax: number;
  excise_duty: number;
  total_tax: number;
}

export interface DeliveryFeeResponse {
  delivery_fee: number;
  estimated_time_minutes: number;
  zone_name?: string;
}

export interface CompleteCheckoutRequest {
  payment_method: string;
  payment_intent_id?: string;
  card_token?: string;
  save_payment_method?: boolean;
}

export interface CompleteCheckoutResponse {
  success: boolean;
  order_id?: string;
  order_number?: string;
  payment_status: string;
  message?: string;
  checkout_session?: CheckoutSession;
}

class CheckoutService {
  private sessionKey = 'checkout_session_id';

  /**
   * Get or store checkout session ID
   */
  private getSessionId(): string | null {
    return localStorage.getItem(this.sessionKey);
  }

  private setSessionId(sessionId: string): void {
    localStorage.setItem(this.sessionKey, sessionId);
  }

  private clearSessionId(): void {
    localStorage.removeItem(this.sessionKey);
  }

  /**
   * Get session header
   */
  private getSessionHeader(): Record<string, string> {
    const cartSessionId = localStorage.getItem('cart_session_id');
    if (cartSessionId) {
      return { 'X-Session-Id': cartSessionId };
    }
    return {};
  }

  /**
   * Initiate a new checkout session
   */
  async initiateCheckout(request?: InitiateCheckoutRequest): Promise<CheckoutSession> {
    try {
      // Add default tenant_id and store_id if not provided
      const defaultRequest: InitiateCheckoutRequest = {
        tenant_id: 'default_tenant',
        store_id: 'default_store',
        session_id: localStorage.getItem('cart_session_id') || undefined,
        fulfillment_type: 'delivery',
        ...request
      };
      
      const response = await api.post('/api/checkout/initiate', defaultRequest, {
        headers: this.getSessionHeader()
      });
      
      const session = response.data;
      this.setSessionId(session.session_id);
      return session;
    } catch (error) {
      console.error('Error initiating checkout:', error);
      throw error;
    }
  }

  /**
   * Get current checkout session
   */
  async getSession(sessionId?: string): Promise<CheckoutSession | null> {
    try {
      const id = sessionId || this.getSessionId();
      if (!id) {
        return null;
      }

      const response = await api.get(`/api/checkout/session/${id}`, {
        headers: this.getSessionHeader()
      });
      return response.data;
    } catch (error: any) {
      if (error.response?.status === 404) {
        this.clearSessionId();
        return null;
      }
      console.error('Error fetching checkout session:', error);
      throw error;
    }
  }

  /**
   * Update checkout session
   */
  async updateSession(sessionId: string, updates: UpdateCheckoutRequest): Promise<CheckoutSession> {
    try {
      const response = await api.put(`/api/checkout/session/${sessionId}`, updates, {
        headers: this.getSessionHeader()
      });
      return response.data;
    } catch (error) {
      console.error('Error updating checkout session:', error);
      throw error;
    }
  }

  /**
   * Apply a discount code
   */
  async applyDiscount(sessionId: string, request: ApplyDiscountRequest): Promise<DiscountResponse> {
    try {
      const response = await api.post(`/api/checkout/session/${sessionId}/apply-discount`, request, {
        headers: this.getSessionHeader()
      });
      return response.data;
    } catch (error) {
      console.error('Error applying discount:', error);
      throw error;
    }
  }

  /**
   * Remove discount from session
   */
  async removeDiscount(sessionId: string): Promise<CheckoutSession> {
    try {
      const response = await api.delete(`/api/checkout/session/${sessionId}/discount`, {
        headers: this.getSessionHeader()
      });
      return response.data;
    } catch (error) {
      console.error('Error removing discount:', error);
      throw error;
    }
  }

  /**
   * Calculate taxes for checkout
   */
  async calculateTaxes(sessionId: string): Promise<TaxCalculationResponse> {
    try {
      const response = await api.get(`/api/checkout/session/${sessionId}/calculate-taxes`, {
        headers: this.getSessionHeader()
      });
      return response.data;
    } catch (error) {
      console.error('Error calculating taxes:', error);
      throw error;
    }
  }

  /**
   * Calculate delivery fee
   */
  async calculateDeliveryFee(sessionId: string, address: DeliveryAddress): Promise<DeliveryFeeResponse> {
    try {
      const response = await api.post(`/api/checkout/session/${sessionId}/calculate-delivery`, address, {
        headers: this.getSessionHeader()
      });
      return response.data;
    } catch (error) {
      console.error('Error calculating delivery fee:', error);
      throw error;
    }
  }

  /**
   * Complete checkout and create order
   */
  async completeCheckout(sessionId: string, request: CompleteCheckoutRequest): Promise<CompleteCheckoutResponse> {
    try {
      const response = await api.post(`/api/checkout/session/${sessionId}/complete`, request, {
        headers: this.getSessionHeader()
      });
      
      if (response.data.success) {
        this.clearSessionId();
      }
      
      return response.data;
    } catch (error) {
      console.error('Error completing checkout:', error);
      throw error;
    }
  }

  /**
   * Cancel checkout session
   */
  async cancelCheckout(sessionId: string): Promise<void> {
    try {
      await api.post(`/api/checkout/session/${sessionId}/cancel`, {}, {
        headers: this.getSessionHeader()
      });
      this.clearSessionId();
    } catch (error) {
      console.error('Error canceling checkout:', error);
      throw error;
    }
  }

  /**
   * Validate address
   */
  async validateAddress(address: DeliveryAddress): Promise<{ valid: boolean; suggestions?: DeliveryAddress[] }> {
    try {
      const response = await api.post('/api/checkout/validate-address', address);
      return response.data;
    } catch (error) {
      console.error('Error validating address:', error);
      throw error;
    }
  }

  /**
   * Get available pickup locations
   */
  async getPickupLocations(): Promise<any[]> {
    try {
      const response = await api.get('/api/checkout/pickup-locations');
      return response.data;
    } catch (error) {
      console.error('Error fetching pickup locations:', error);
      return [];
    }
  }

  /**
   * Check if checkout session is expired
   */
  isSessionExpired(session: CheckoutSession): boolean {
    if (!session.expires_at) return false;
    return new Date(session.expires_at) < new Date();
  }

  /**
   * Get time remaining for checkout session
   */
  getTimeRemaining(session: CheckoutSession): number {
    if (!session.expires_at) return 0;
    const remaining = new Date(session.expires_at).getTime() - new Date().getTime();
    return Math.max(0, remaining);
  }
}

// Export singleton instance
export const checkoutService = new CheckoutService();