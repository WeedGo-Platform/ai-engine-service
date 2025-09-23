#!/bin/bash

# Kill the bundler to stop compilation errors
pkill -f "expo start" || true

# Fix common TypeScript errors

# 1. Fix missing primaryLight color in Colors
echo "Adding primaryLight to Colors..."
sed -i '' 's/primary: string;/primary: string;\n  primaryLight: string;/' constants/Colors.ts

# 2. Fix authStore login return type
echo "Fixing authStore login method..."
sed -i '' 's/login: async (phone) =>/login: async (phone): Promise<LoginResponse | void> =>/' stores/authStore.ts

# 3. Add missing methods to authStore
echo "Adding missing auth methods..."
cat >> stores/authStore.ts << 'EOF'

  // Additional methods
  checkPhone: async (phone: string) => {
    try {
      return await authService.checkPhone(phone);
    } catch (error) {
      console.error('Check phone error:', error);
      throw error;
    }
  },

  resendOTP: async (phone: string) => {
    try {
      return await authService.login(phone);
    } catch (error) {
      console.error('Resend OTP error:', error);
      throw error;
    }
  },

  setBiometricEnabled: (enabled: boolean) => {
    set({ biometricEnabled: enabled });
  },
EOF

# 4. Fix cart store image URL issues
echo "Fixing cartStore image URLs..."
sed -i '' 's/product\.image\.url/product.image/g' stores/cartStore.ts

# 5. Fix profile service methods
echo "Adding missing profile service methods..."
cat >> services/api/profile.ts << 'EOF'

  async getProfile(): Promise<Profile> {
    const response = await apiClient.get<Profile>('/api/v1/profile');
    return response.data;
  }

  async uploadProfileImage(file: File): Promise<{ url: string }> {
    const formData = new FormData();
    formData.append('image', file);
    const response = await apiClient.post<{ url: string }>('/api/v1/profile/image', formData);
    return response.data;
  }

  async getPaymentMethods(): Promise<PaymentMethod[]> {
    const response = await apiClient.get<PaymentMethod[]>('/api/v1/profile/payment-methods');
    return response.data;
  }

  async addPaymentMethod(method: Omit<PaymentMethod, 'id'>): Promise<PaymentMethod> {
    const response = await apiClient.post<PaymentMethod>('/api/v1/profile/payment-methods', method);
    return response.data;
  }

  async updatePaymentMethod(id: string, updates: Partial<PaymentMethod>): Promise<PaymentMethod> {
    const response = await apiClient.put<PaymentMethod>(`/api/v1/profile/payment-methods/${id}`, updates);
    return response.data;
  }

  async deletePaymentMethod(id: string): Promise<void> {
    await apiClient.delete(`/api/v1/profile/payment-methods/${id}`);
  }

  async setDefaultPaymentMethod(id: string): Promise<void> {
    await apiClient.put(`/api/v1/profile/payment-methods/${id}/default`);
  }
EOF

echo "TypeScript fixes applied!"