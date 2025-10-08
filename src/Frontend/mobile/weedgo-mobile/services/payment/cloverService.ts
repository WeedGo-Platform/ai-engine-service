/**
 * Clover Payment Service
 * Handles tokenization and payment processing via Clover API
 * Docs: https://docs.clover.com/docs/ecommerce-overview
 */

import { API_URL } from '../api/client';

export interface CardDetails {
  cardNumber: string;
  expiryMonth: string;
  expiryYear: string;
  cvv: string;
  postalCode: string;
}

export interface CloverToken {
  token: string;
  card: {
    brand: string;
    last4: string;
    exp_month: string;
    exp_year: string;
  };
}

export interface PaymentResult {
  success: boolean;
  paymentId?: string;
  error?: string;
  transactionId?: string;
}

class CloverPaymentService {
  /**
   * Note: Merchant credentials are stored securely on the backend
   * Mobile app only handles client-side validation and sends card data to backend
   */

  /**
   * Validate card number using Luhn algorithm
   */
  validateCardNumber(cardNumber: string): boolean {
    const cleaned = cardNumber.replace(/\s/g, '');

    if (!/^\d+$/.test(cleaned)) return false;
    if (cleaned.length < 13 || cleaned.length > 19) return false;

    // Luhn algorithm
    let sum = 0;
    let isEven = false;

    for (let i = cleaned.length - 1; i >= 0; i--) {
      let digit = parseInt(cleaned[i], 10);

      if (isEven) {
        digit *= 2;
        if (digit > 9) digit -= 9;
      }

      sum += digit;
      isEven = !isEven;
    }

    return sum % 10 === 0;
  }

  /**
   * Get card brand from card number
   */
  getCardBrand(cardNumber: string): string {
    const cleaned = cardNumber.replace(/\s/g, '');

    if (/^4/.test(cleaned)) return 'visa';
    if (/^5[1-5]/.test(cleaned)) return 'mastercard';
    if (/^3[47]/.test(cleaned)) return 'amex';
    if (/^6(?:011|5)/.test(cleaned)) return 'discover';

    return 'unknown';
  }

  /**
   * Validate CVV
   */
  validateCVV(cvv: string, cardBrand: string): boolean {
    if (cardBrand === 'amex') {
      return /^\d{4}$/.test(cvv);
    }
    return /^\d{3}$/.test(cvv);
  }

  /**
   * Validate expiry date
   */
  validateExpiry(month: string, year: string): boolean {
    const monthNum = parseInt(month, 10);
    const yearNum = parseInt(year, 10);

    if (monthNum < 1 || monthNum > 12) return false;

    const now = new Date();
    const currentYear = now.getFullYear() % 100; // Last 2 digits
    const currentMonth = now.getMonth() + 1;

    if (yearNum < currentYear) return false;
    if (yearNum === currentYear && monthNum < currentMonth) return false;

    return true;
  }

  /**
   * Tokenize card details via backend
   * Backend handles all Clover API interactions securely
   */
  async tokenizeCard(cardDetails: CardDetails): Promise<CloverToken> {
    // Validate card details on client side first
    if (!this.validateCardNumber(cardDetails.cardNumber)) {
      throw new Error('Invalid card number');
    }

    if (!this.validateExpiry(cardDetails.expiryMonth, cardDetails.expiryYear)) {
      throw new Error('Invalid or expired card');
    }

    const brand = this.getCardBrand(cardDetails.cardNumber);
    if (!this.validateCVV(cardDetails.cvv, brand)) {
      throw new Error('Invalid CVV');
    }

    try {
      // Send to backend - backend handles Clover API with secure credentials
      const response = await fetch(`${API_URL}/api/v1/payment/tokenize`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          card: {
            number: cardDetails.cardNumber.replace(/\s/g, ''),
            exp_month: cardDetails.expiryMonth,
            exp_year: cardDetails.expiryYear,
            cvv: cardDetails.cvv,
            zip: cardDetails.postalCode,
          },
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Tokenization failed');
      }

      const data = await response.json();

      return {
        token: data.token,
        card: {
          brand: brand,
          last4: cardDetails.cardNumber.slice(-4),
          exp_month: cardDetails.expiryMonth,
          exp_year: cardDetails.expiryYear,
        },
      };
    } catch (error: any) {
      console.error('[CloverService] Tokenization error:', error);
      throw new Error(error.message || 'Failed to tokenize card');
    }
  }

  /**
   * Process payment with tokenized card via backend
   */
  async processPayment(params: {
    token: string;
    amount: number; // in cents
    currency?: string;
    orderId: string;
    description?: string;
  }): Promise<PaymentResult> {
    try {
      const response = await fetch(`${API_URL}/api/v1/payment/charge`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          token: params.token,
          amount: params.amount,
          currency: params.currency || 'CAD',
          order_id: params.orderId,
          description: params.description,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Payment failed');
      }

      const data = await response.json();

      return {
        success: true,
        paymentId: data.payment_id,
        transactionId: data.transaction_id,
      };
    } catch (error: any) {
      console.error('[CloverService] Payment error:', error);
      return {
        success: false,
        error: error.message || 'Payment processing failed',
      };
    }
  }

  /**
   * Save tokenized card to user profile
   */
  async saveCard(params: {
    userId: string;
    token: string;
    cardBrand: string;
    last4: string;
    expMonth: string;
    expYear: string;
    isDefault?: boolean;
  }) {
    try {
      const response = await fetch(`${API_URL}/api/v1/payment/save-card`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(params),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Failed to save card');
      }

      return await response.json();
    } catch (error: any) {
      console.error('[CloverService] Save card error:', error);
      throw error;
    }
  }

  /**
   * Format card number with spaces
   */
  formatCardNumber(value: string): string {
    const cleaned = value.replace(/\s/g, '');
    const groups = cleaned.match(/.{1,4}/g) || [];
    return groups.join(' ');
  }

  /**
   * Format expiry date (MM/YY)
   */
  formatExpiry(value: string): string {
    const cleaned = value.replace(/\D/g, '');
    if (cleaned.length >= 2) {
      return `${cleaned.slice(0, 2)}/${cleaned.slice(2, 4)}`;
    }
    return cleaned;
  }
}

// Export singleton instance
export const cloverService = new CloverPaymentService();
export default cloverService;
