/**
 * Payment processing service for secure checkout
 */

import apiClient from '@api/client';
import { sanitizeInput } from '@utils/security';
import { logger } from '@utils/logger';

// Payment types
export interface PaymentMethod {
  id: string;
  type: 'credit_card' | 'debit_card' | 'interac' | 'cash';
  last4?: string;
  brand?: string;
  expiryMonth?: number;
  expiryYear?: number;
  holderName?: string;
  isDefault?: boolean;
}

export interface PaymentDetails {
  method: string;
  cardNumber?: string;
  cardholderName?: string;
  expiryMonth?: string;
  expiryYear?: string;
  cvv?: string;
  saveCard?: boolean;
  useStoredCard?: string;
  billingAddress?: {
    street: string;
    city: string;
    province: string;
    postalCode: string;
    country: string;
  };
}

export interface PaymentIntent {
  id: string;
  amount: number;
  currency: string;
  status: 'pending' | 'processing' | 'succeeded' | 'failed' | 'cancelled';
  clientSecret?: string;
  paymentMethod?: string;
  metadata?: Record<string, any>;
}

export interface PaymentResult {
  success: boolean;
  transactionId?: string;
  message?: string;
  error?: string;
  requiresAction?: boolean;
  actionUrl?: string;
}

class PaymentService {
  private static instance: PaymentService;

  private constructor() {}

  public static getInstance(): PaymentService {
    if (!PaymentService.instance) {
      PaymentService.instance = new PaymentService();
    }
    return PaymentService.instance;
  }

  /**
   * Create payment intent for order
   */
  async createPaymentIntent(orderId: string, amount: number): Promise<PaymentIntent> {
    try {
      const response = await apiClient.post('/api/payments/intent', {
        order_id: orderId,
        amount: amount,
      });

      return response.data;
    } catch (error) {
      logger.error('Failed to create payment intent', error);
      throw new Error('Failed to initialize payment. Please try again.');
    }
  }

  /**
   * Process payment for order
   */
  async processPayment(
    orderId: string,
    paymentDetails: PaymentDetails
  ): Promise<PaymentResult> {
    try {
      // Sanitize payment details
      const sanitizedDetails = this.sanitizePaymentDetails(paymentDetails);

      // Validate payment details
      const validation = this.validatePaymentDetails(sanitizedDetails);
      if (!validation.isValid) {
        throw new Error(validation.error || 'Invalid payment details');
      }

      // Process payment through API
      const response = await apiClient.post(`/api/orders/${orderId}/payment`, {
        payment_method: sanitizedDetails.method,
        card_number: sanitizedDetails.cardNumber ? this.maskCardNumber(sanitizedDetails.cardNumber) : undefined,
        cardholder_name: sanitizedDetails.cardholderName,
        expiry_month: sanitizedDetails.expiryMonth,
        expiry_year: sanitizedDetails.expiryYear,
        cvv: sanitizedDetails.cvv,
        save_card: sanitizedDetails.saveCard,
        stored_card_id: sanitizedDetails.useStoredCard,
        billing_address: sanitizedDetails.billingAddress,
      });

      return {
        success: response.data.success,
        transactionId: response.data.transaction_id,
        message: response.data.message,
        requiresAction: response.data.requires_action,
        actionUrl: response.data.action_url,
      };
    } catch (error: any) {
      logger.error('Payment processing failed', error);

      return {
        success: false,
        error: error.response?.data?.message || error.message || 'Payment failed. Please try again.',
      };
    }
  }

  /**
   * Confirm payment after 3DS or additional verification
   */
  async confirmPayment(
    paymentIntentId: string,
    verificationData?: any
  ): Promise<PaymentResult> {
    try {
      const response = await apiClient.post(`/api/payments/${paymentIntentId}/confirm`, {
        verification_data: verificationData,
      });

      return {
        success: response.data.success,
        transactionId: response.data.transaction_id,
        message: response.data.message,
      };
    } catch (error: any) {
      logger.error('Payment confirmation failed', error);

      return {
        success: false,
        error: error.response?.data?.message || 'Payment confirmation failed',
      };
    }
  }

  /**
   * Get stored payment methods for user
   */
  async getStoredPaymentMethods(): Promise<PaymentMethod[]> {
    try {
      const response = await apiClient.get('/api/payments/methods');
      return response.data.methods;
    } catch (error) {
      logger.error('Failed to fetch payment methods', error);
      return [];
    }
  }

  /**
   * Add new payment method
   */
  async addPaymentMethod(paymentDetails: PaymentDetails): Promise<PaymentMethod> {
    try {
      const sanitizedDetails = this.sanitizePaymentDetails(paymentDetails);

      const response = await apiClient.post('/api/payments/methods', {
        type: sanitizedDetails.method,
        card_number: sanitizedDetails.cardNumber,
        cardholder_name: sanitizedDetails.cardholderName,
        expiry_month: sanitizedDetails.expiryMonth,
        expiry_year: sanitizedDetails.expiryYear,
        billing_address: sanitizedDetails.billingAddress,
      });

      return response.data.method;
    } catch (error: any) {
      logger.error('Failed to add payment method', error);
      throw new Error(error.response?.data?.message || 'Failed to add payment method');
    }
  }

  /**
   * Remove payment method
   */
  async removePaymentMethod(methodId: string): Promise<boolean> {
    try {
      await apiClient.delete(`/api/payments/methods/${methodId}`);
      return true;
    } catch (error) {
      logger.error('Failed to remove payment method', error);
      return false;
    }
  }

  /**
   * Set default payment method
   */
  async setDefaultPaymentMethod(methodId: string): Promise<boolean> {
    try {
      await apiClient.patch(`/api/payments/methods/${methodId}/default`);
      return true;
    } catch (error) {
      logger.error('Failed to set default payment method', error);
      return false;
    }
  }

  /**
   * Validate payment amount against order
   */
  async validatePaymentAmount(orderId: string, amount: number): Promise<boolean> {
    try {
      const response = await apiClient.post('/api/payments/validate', {
        order_id: orderId,
        amount: amount,
      });

      return response.data.valid;
    } catch (error) {
      logger.error('Payment amount validation failed', error);
      return false;
    }
  }

  /**
   * Get payment status
   */
  async getPaymentStatus(transactionId: string): Promise<PaymentIntent> {
    try {
      const response = await apiClient.get(`/api/payments/${transactionId}/status`);
      return response.data;
    } catch (error) {
      logger.error('Failed to get payment status', error);
      throw new Error('Failed to get payment status');
    }
  }

  /**
   * Cancel payment
   */
  async cancelPayment(transactionId: string): Promise<boolean> {
    try {
      await apiClient.post(`/api/payments/${transactionId}/cancel`);
      return true;
    } catch (error) {
      logger.error('Failed to cancel payment', error);
      return false;
    }
  }

  /**
   * Refund payment
   */
  async refundPayment(
    transactionId: string,
    amount?: number,
    reason?: string
  ): Promise<PaymentResult> {
    try {
      const response = await apiClient.post(`/api/payments/${transactionId}/refund`, {
        amount: amount,
        reason: reason,
      });

      return {
        success: response.data.success,
        transactionId: response.data.refund_id,
        message: response.data.message,
      };
    } catch (error: any) {
      logger.error('Refund failed', error);

      return {
        success: false,
        error: error.response?.data?.message || 'Refund failed',
      };
    }
  }

  /**
   * Sanitize payment details to prevent XSS
   */
  private sanitizePaymentDetails(details: PaymentDetails): PaymentDetails {
    return {
      ...details,
      cardholderName: details.cardholderName ? sanitizeInput(details.cardholderName) : undefined,
      cardNumber: details.cardNumber?.replace(/\s/g, ''),
      cvv: details.cvv?.replace(/\D/g, ''),
      billingAddress: details.billingAddress ? {
        street: sanitizeInput(details.billingAddress.street),
        city: sanitizeInput(details.billingAddress.city),
        province: sanitizeInput(details.billingAddress.province),
        postalCode: sanitizeInput(details.billingAddress.postalCode),
        country: sanitizeInput(details.billingAddress.country),
      } : undefined,
    };
  }

  /**
   * Validate payment details
   */
  private validatePaymentDetails(details: PaymentDetails): {
    isValid: boolean;
    error?: string;
  } {
    // Cash payments don't need validation
    if (details.method === 'cash') {
      return { isValid: true };
    }

    // Using stored card
    if (details.useStoredCard) {
      return { isValid: true };
    }

    // New card validation
    if (!details.cardNumber || !details.cardholderName || !details.expiryMonth ||
        !details.expiryYear || !details.cvv) {
      return { isValid: false, error: 'Missing required payment information' };
    }

    // Validate card number with Luhn algorithm
    if (!this.validateCardNumber(details.cardNumber)) {
      return { isValid: false, error: 'Invalid card number' };
    }

    // Validate expiry
    const currentYear = new Date().getFullYear();
    const currentMonth = new Date().getMonth() + 1;
    const expYear = parseInt(details.expiryYear);
    const expMonth = parseInt(details.expiryMonth);

    if (expYear < currentYear || (expYear === currentYear && expMonth < currentMonth)) {
      return { isValid: false, error: 'Card has expired' };
    }

    // Validate CVV
    if (details.cvv.length < 3 || details.cvv.length > 4) {
      return { isValid: false, error: 'Invalid CVV' };
    }

    return { isValid: true };
  }

  /**
   * Validate card number using Luhn algorithm
   */
  private validateCardNumber(cardNumber: string): boolean {
    const digits = cardNumber.replace(/\D/g, '');

    if (digits.length < 13 || digits.length > 19) {
      return false;
    }

    let sum = 0;
    let isEven = false;

    for (let i = digits.length - 1; i >= 0; i--) {
      let digit = parseInt(digits[i], 10);

      if (isEven) {
        digit *= 2;
        if (digit > 9) {
          digit -= 9;
        }
      }

      sum += digit;
      isEven = !isEven;
    }

    return sum % 10 === 0;
  }

  /**
   * Mask card number for display
   */
  private maskCardNumber(cardNumber: string): string {
    const cleaned = cardNumber.replace(/\D/g, '');
    const last4 = cleaned.slice(-4);
    const masked = cleaned.slice(0, -4).replace(/./g, '*');
    return masked + last4;
  }

  /**
   * Detect card brand
   */
  detectCardBrand(cardNumber: string): string {
    const cleaned = cardNumber.replace(/\D/g, '');

    const patterns: Record<string, RegExp> = {
      visa: /^4/,
      mastercard: /^5[1-5]/,
      amex: /^3[47]/,
      discover: /^6(?:011|5)/,
      jcb: /^35/,
      diners: /^3(?:0[0-5]|[68])/,
    };

    for (const [brand, pattern] of Object.entries(patterns)) {
      if (pattern.test(cleaned)) {
        return brand;
      }
    }

    return 'unknown';
  }

  /**
   * Format card number for display
   */
  formatCardNumber(cardNumber: string, brand?: string): string {
    const cleaned = cardNumber.replace(/\D/g, '');

    if (brand === 'amex') {
      // Amex: 4-6-5
      return cleaned.replace(/(\d{4})(\d{6})(\d{5})/, '$1 $2 $3');
    } else {
      // Others: 4-4-4-4
      return cleaned.replace(/(\d{4})(?=\d)/g, '$1 ');
    }
  }
}

// Export singleton instance
export const paymentService = PaymentService.getInstance();

// Export default
export default paymentService;