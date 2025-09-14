import axios from 'axios';

const API_BASE_URL = 'http://localhost:5024/api';

export interface Product {
  id: string;
  name: string;
  brand: string;
  category: string;
  subcategory: string;
  thc_content: number;
  cbd_content: number;
  price: number;
  weight_grams?: number;
  dried_flower_equivalent?: number;
  quantity_available: number;
  sku?: string;
  barcode?: string;
  image_url?: string;
}

export interface Customer {
  id: string;
  name: string;
  email?: string;
  phone?: string;
  loyalty_points?: number;
  is_verified?: boolean;
  birth_date?: string;
  address?: {
    street: string;
    city: string;
    province: string;
    postal_code: string;
  };
  medical_card?: string;
  preferences?: {
    favorite_categories: string[];
    preferred_potency: 'low' | 'medium' | 'high';
  };
}

export interface CartItem {
  product: Product;
  quantity: number;
  discount?: number;
  discount_type?: 'percentage' | 'fixed';
  promotion?: string;
  price_override?: number;
}

export interface Transaction {
  id: string;
  store_id: string;
  cashier_id: string;
  customer_id?: string;
  items: CartItem[];
  subtotal: number;
  discounts: number;
  tax: number;
  total: number;
  payment_method: 'cash' | 'card' | 'debit' | 'split';
  payment_details?: {
    cash_amount?: number;
    card_amount?: number;
    change_given?: number;
    card_last_four?: string;
    authorization_code?: string;
  };
  status: 'completed' | 'parked' | 'cancelled' | 'refunded';
  timestamp: string;
  receipt_number: string;
  notes?: string;
}

export interface CashDrawer {
  id: string;
  opening_amount: number;
  current_amount: number;
  expected_amount: number;
  cash_sales: number;
  cash_refunds: number;
  cash_drops: number;
  opened_at: string;
  closed_at?: string;
  opened_by: string;
  closed_by?: string;
  status: 'open' | 'closed';
  discrepancy?: number;
}

export interface Promotion {
  id: string;
  name: string;
  type: 'percentage' | 'fixed' | 'bogo' | 'bundle';
  value: number;
  conditions?: {
    min_purchase?: number;
    categories?: string[];
    products?: string[];
    customer_groups?: string[];
    day_of_week?: number[];
    time_range?: { start: string; end: string };
  };
  start_date: string;
  end_date: string;
  is_active: boolean;
}

class POSService {
  // Product Methods
  async searchProducts(query: string, category?: string): Promise<Product[]> {
    const params: any = { q: query };
    if (category) params.category = category;
    const response = await axios.get(`${API_BASE_URL}/products/search`, { params });
    return response.data;
  }

  async getProductByBarcode(barcode: string): Promise<Product> {
    const response = await axios.get(`${API_BASE_URL}/products/barcode/${barcode}`);
    return response.data;
  }

  async getProductById(id: string): Promise<Product> {
    const response = await axios.get(`${API_BASE_URL}/products/${id}`);
    return response.data;
  }

  // Customer Methods
  async searchCustomers(query: string): Promise<Customer[]> {
    const response = await axios.get(`${API_BASE_URL}/customers/search`, { 
      params: { q: query } 
    });
    return response.data;
  }

  async getCustomerById(id: string): Promise<Customer> {
    const response = await axios.get(`${API_BASE_URL}/customers/${id}`);
    return response.data;
  }

  async createCustomer(customer: Partial<Customer>): Promise<Customer> {
    const response = await axios.post(`${API_BASE_URL}/customers`, customer);
    return response.data;
  }

  async verifyCustomerAge(birthDate: string): Promise<{ is_valid: boolean; age: number }> {
    const response = await axios.post(`${API_BASE_URL}/customers/verify-age`, { 
      birth_date: birthDate 
    });
    return response.data;
  }

  // Transaction Methods
  async createTransaction(transaction: Partial<Transaction>): Promise<Transaction> {
    const response = await axios.post(`${API_BASE_URL}/pos/transactions`, transaction);
    return response.data;
  }

  async parkTransaction(transaction: Partial<Transaction>): Promise<Transaction> {
    const response = await axios.post(`${API_BASE_URL}/pos/transactions/park`, transaction);
    return response.data;
  }

  async getParkedTransactions(storeId: string): Promise<Transaction[]> {
    const response = await axios.get(`${API_BASE_URL}/pos/transactions/parked?store_id=${storeId}`);
    return response.data;
  }

  async resumeTransaction(transactionId: string): Promise<Transaction> {
    const response = await axios.put(`${API_BASE_URL}/pos/transactions/${transactionId}/resume`);
    return response.data;
  }

  async getTransactionHistory(storeId: string, startDate?: string, endDate?: string): Promise<Transaction[]> {
    const params: any = { store_id: storeId };
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
    const response = await axios.get(`${API_BASE_URL}/pos/transactions`, { params });
    return response.data;
  }

  async refundTransaction(transactionId: string, items?: string[]): Promise<Transaction> {
    const response = await axios.post(`${API_BASE_URL}/pos/transactions/${transactionId}/refund`, {
      items
    });
    return response.data;
  }

  async processRefund(transactionId: string, refundData: {
    amount: number;
    reason: string;
    items?: any[];
    processed_by: string;
  }): Promise<any> {
    const response = await axios.post(`${API_BASE_URL}/pos/transactions/${transactionId}/refund`, refundData);
    return response.data;
  }

  // Cash Drawer Methods
  async openCashDrawer(storeId: string, openingAmount: number): Promise<CashDrawer> {
    const response = await axios.post(`${API_BASE_URL}/stores/${storeId}/cash-drawer/open`, {
      opening_amount: openingAmount
    });
    return response.data;
  }

  async closeCashDrawer(storeId: string, countedAmount: number): Promise<CashDrawer> {
    const response = await axios.post(`${API_BASE_URL}/stores/${storeId}/cash-drawer/close`, {
      counted_amount: countedAmount
    });
    return response.data;
  }

  async getCashDrawerStatus(storeId: string): Promise<CashDrawer> {
    const response = await axios.get(`${API_BASE_URL}/stores/${storeId}/cash-drawer`);
    return response.data;
  }

  async addCashDrop(storeId: string, amount: number, reason: string): Promise<void> {
    await axios.post(`${API_BASE_URL}/stores/${storeId}/cash-drawer/drop`, {
      amount,
      reason
    });
  }

  // Promotion Methods
  async getActivePromotions(storeId: string): Promise<Promotion[]> {
    const response = await axios.get(`${API_BASE_URL}/stores/${storeId}/promotions/active`);
    return response.data;
  }

  async applyPromotion(promotionId: string, cart: CartItem[]): Promise<{
    applicable: boolean;
    discount_amount: number;
    affected_items: string[];
  }> {
    const response = await axios.post(`${API_BASE_URL}/promotions/${promotionId}/apply`, {
      cart
    });
    return response.data;
  }

  // Receipt Methods
  async printReceipt(transactionId: string): Promise<void> {
    await axios.post(`${API_BASE_URL}/transactions/${transactionId}/receipt/print`);
  }

  async emailReceipt(transactionId: string, email: string): Promise<void> {
    await axios.post(`${API_BASE_URL}/transactions/${transactionId}/receipt/email`, { 
      email 
    });
  }

  // Payment Processing
  async processCardPayment(amount: number, terminalId: string): Promise<{
    success: boolean;
    authorization_code?: string;
    error?: string;
  }> {
    const response = await axios.post(`${API_BASE_URL}/payments/card`, {
      amount,
      terminal_id: terminalId
    });
    return response.data;
  }

  // Inventory Check
  async checkInventory(productId: string, quantity: number): Promise<{
    available: boolean;
    current_stock: number;
  }> {
    const response = await axios.get(`${API_BASE_URL}/products/${productId}/inventory`, {
      params: { quantity }
    });
    return response.data;
  }

  // Reports
  async getDailySalesReport(storeId: string, date: string): Promise<{
    total_sales: number;
    transaction_count: number;
    average_basket: number;
    top_products: Array<{ product_id: string; name: string; quantity: number; revenue: number }>;
    payment_breakdown: Record<string, number>;
  }> {
    const response = await axios.get(`${API_BASE_URL}/stores/${storeId}/reports/daily`, {
      params: { date }
    });
    return response.data;
  }

  // Hardware Integration
  async testPrinter(printerId: string): Promise<{ success: boolean; message: string }> {
    const response = await axios.post(`${API_BASE_URL}/hardware/printer/${printerId}/test`);
    return response.data;
  }

  async testScanner(scannerId: string): Promise<{ success: boolean; message: string }> {
    const response = await axios.post(`${API_BASE_URL}/hardware/scanner/${scannerId}/test`);
    return response.data;
  }

  async testTerminal(terminalId: string): Promise<{ success: boolean; message: string }> {
    const response = await axios.post(`${API_BASE_URL}/hardware/terminal/${terminalId}/test`);
    return response.data;
  }
}

export default new POSService();