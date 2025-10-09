import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { profileService } from '@/services/api/profile';
import { addressService, DeliveryAddress as AddressServiceType } from '@/services/api/addresses';
import { DeliveryAddress, PaymentMethod } from './orderStore';
import Toast from 'react-native-toast-message';

export interface UserProfile {
  id: string;
  phone: string;
  email?: string;
  first_name: string;
  last_name: string;
  date_of_birth?: string;
  profile_image?: string;

  // Preferences
  preferences: {
    notifications_enabled: boolean;
    email_notifications: boolean;
    sms_notifications: boolean;
    marketing_opt_in: boolean;
    default_tip_percentage: number;
    preferred_store_id?: string;
    delivery_instructions?: string;
  };

  // Stats
  total_orders: number;
  total_spent: number;
  loyalty_points: number;
  member_since: string;

  // Quick checkout data
  default_address_id?: string;
  default_payment_id?: string;
  average_tip: number;
}

interface ProfileStore {
  // State
  profile: UserProfile | null;
  addresses: DeliveryAddress[];
  paymentMethods: PaymentMethod[];
  defaultAddress: DeliveryAddress | null;
  defaultPayment: PaymentMethod | null;
  loading: boolean;
  error: string | null;

  // Profile Management
  loadProfile: () => Promise<void>;
  updateProfile: (data: Partial<UserProfile>) => Promise<void>;
  uploadProfileImage: (imageUri: string) => Promise<void>;

  // Address Management
  loadAddresses: () => Promise<void>;
  addAddress: (address: Omit<DeliveryAddress, 'id'>) => Promise<DeliveryAddress>;
  updateAddress: (addressId: string, data: Partial<DeliveryAddress>) => Promise<void>;
  deleteAddress: (addressId: string) => Promise<void>;
  setDefaultAddress: (addressId: string) => Promise<void>;

  // Payment Management
  loadPaymentMethods: () => Promise<void>;
  addPaymentMethod: (payment: Omit<PaymentMethod, 'id'>) => Promise<PaymentMethod>;
  updatePaymentMethod: (paymentId: string, data: Partial<PaymentMethod>) => Promise<void>;
  deletePaymentMethod: (paymentId: string) => Promise<void>;
  setDefaultPayment: (paymentId: string) => Promise<void>;

  // Preferences
  updatePreferences: (preferences: Partial<UserProfile['preferences']>) => Promise<void>;
  updateDefaultTip: (percentage: number) => Promise<void>;

  // Checkout Helpers
  getCheckoutDefaults: () => {
    deliveryMethod: 'delivery' | 'pickup';
    address: DeliveryAddress | null;
    paymentMethod: PaymentMethod | null;
    tipPercentage: number;
  };

  // Validation
  validateAddress: (address: Partial<DeliveryAddress>) => boolean;

  // Helpers
  clearProfile: () => void;
  setError: (error: string | null) => void;
}

export const useProfileStore = create<ProfileStore>()(
  persist(
    (set, get) => ({
      // Initial state
      profile: null,
      addresses: [],
      paymentMethods: [],
      defaultAddress: null,
      defaultPayment: null,
      loading: false,
      error: null,

      // Load user profile
      loadProfile: async () => {
        try {
          set({ loading: true, error: null });
          const response = await profileService.getProfile();
          const profile = response.data;

          set({ profile });

          // Load related data
          await Promise.all([
            get().loadAddresses(),
            get().loadPaymentMethods()
          ]);
        } catch (error: any) {
          const message = error.response?.data?.message || 'Failed to load profile';
          set({ error: message });
          console.error('Load profile error:', error);
        } finally {
          set({ loading: false });
        }
      },

      // Update profile
      updateProfile: async (data: Partial<UserProfile>) => {
        try {
          set({ loading: true, error: null });
          const response = await profileService.updateProfile(data);

          set({ profile: response.data });

          Toast.show({
            type: 'success',
            text1: 'Profile Updated',
            text2: 'Your profile has been updated successfully',
          });
        } catch (error: any) {
          const message = error.response?.data?.message || 'Failed to update profile';
          set({ error: message });

          Toast.show({
            type: 'error',
            text1: 'Update Failed',
            text2: message,
          });

          throw error;
        } finally {
          set({ loading: false });
        }
      },

      // Upload profile image
      uploadProfileImage: async (imageUri: string) => {
        try {
          set({ loading: true, error: null });

          const formData = new FormData();
          formData.append('image', {
            uri: imageUri,
            type: 'image/jpeg',
            name: 'profile.jpg',
          } as any);

          const response = await profileService.uploadProfileImage(formData);

          set((state) => ({
            profile: state.profile ? {
              ...state.profile,
              profile_image: response.data.image_url
            } : null
          }));

          Toast.show({
            type: 'success',
            text1: 'Image Uploaded',
            text2: 'Your profile image has been updated',
          });
        } catch (error: any) {
          const message = error.response?.data?.message || 'Failed to upload image';
          set({ error: message });

          Toast.show({
            type: 'error',
            text1: 'Upload Failed',
            text2: message,
          });

          throw error;
        } finally {
          set({ loading: false });
        }
      },

      // Load addresses
      loadAddresses: async () => {
        try {
          const addresses = await addressService.getAddresses();

          const defaultAddr = addresses.find((a: DeliveryAddress) =>
            a.is_default || a.id === get().profile?.default_address_id
          );

          set({
            addresses,
            defaultAddress: defaultAddr || addresses[0] || null
          });
        } catch (error: any) {
          console.error('Load addresses error:', error);
        }
      },

      // Add new address
      addAddress: async (address: Omit<DeliveryAddress, 'id'>) => {
        try {
          set({ loading: true, error: null });
          const newAddress = await addressService.addAddress(address);

          set((state) => ({
            addresses: [...state.addresses, newAddress],
            defaultAddress: state.defaultAddress || newAddress // Set as default if no default exists
          }));

          Toast.show({
            type: 'success',
            text1: 'Address Added',
            text2: 'New delivery address has been added',
          });

          return newAddress;
        } catch (error: any) {
          const message = error.response?.data?.message || error.message || 'Failed to add address';
          set({ error: message });

          Toast.show({
            type: 'error',
            text1: 'Failed to Add Address',
            text2: message,
          });

          throw error;
        } finally {
          set({ loading: false });
        }
      },

      // Update address
      updateAddress: async (addressId: string, data: Partial<DeliveryAddress>) => {
        try {
          set({ loading: true, error: null });
          const updatedAddress = await addressService.updateAddress(addressId, data);

          set((state) => ({
            addresses: state.addresses.map(a =>
              a.id === addressId ? { ...a, ...updatedAddress } : a
            ),
            defaultAddress: state.defaultAddress?.id === addressId
              ? { ...state.defaultAddress, ...updatedAddress }
              : state.defaultAddress
          }));

          Toast.show({
            type: 'success',
            text1: 'Address Updated',
            text2: 'Your address has been updated successfully',
          });
        } catch (error: any) {
          const message = error.response?.data?.message || error.message || 'Failed to update address';
          set({ error: message });

          Toast.show({
            type: 'error',
            text1: 'Update Failed',
            text2: message,
          });

          throw error;
        } finally {
          set({ loading: false });
        }
      },

      // Delete address
      deleteAddress: async (addressId: string) => {
        try {
          set({ loading: true, error: null });
          await addressService.deleteAddress(addressId);

          set((state) => {
            const addresses = state.addresses.filter(a => a.id !== addressId);
            const defaultAddress = state.defaultAddress?.id === addressId
              ? addresses.find(a => a.is_default) || addresses[0] || null
              : state.defaultAddress;

            return { addresses, defaultAddress };
          });

          Toast.show({
            type: 'success',
            text1: 'Address Deleted',
            text2: 'The address has been removed',
          });
        } catch (error: any) {
          const message = error.response?.data?.message || error.message || 'Failed to delete address';
          set({ error: message });

          Toast.show({
            type: 'error',
            text1: 'Delete Failed',
            text2: message,
          });

          throw error;
        } finally {
          set({ loading: false });
        }
      },

      // Set default address
      setDefaultAddress: async (addressId: string) => {
        try {
          const address = get().addresses.find(a => a.id === addressId);
          if (!address) return;

          await addressService.setDefaultAddress(addressId);

          set((state) => ({
            // Update is_default flag on all addresses
            addresses: state.addresses.map(a => ({
              ...a,
              is_default: a.id === addressId
            })),
            defaultAddress: { ...address, is_default: true },
            profile: state.profile ? {
              ...state.profile,
              default_address_id: addressId
            } : null
          }));

          Toast.show({
            type: 'success',
            text1: 'Default Address Set',
            text2: 'Your default delivery address has been updated',
          });
        } catch (error: any) {
          const message = error.response?.data?.message || error.message || 'Failed to set default address';
          Toast.show({
            type: 'error',
            text1: 'Update Failed',
            text2: message,
          });
        }
      },

      // Load payment methods
      loadPaymentMethods: async () => {
        try {
          const response = await profileService.getPaymentMethods();
          const paymentMethods = response.data.payment_methods;

          const defaultPayment = paymentMethods.find((p: PaymentMethod) => p.is_default);

          set({
            paymentMethods,
            defaultPayment: defaultPayment || paymentMethods[0] || null
          });
        } catch (error: any) {
          console.error('Load payment methods error:', error);
        }
      },

      // Add payment method
      addPaymentMethod: async (payment: Omit<PaymentMethod, 'id'>) => {
        try {
          set({ loading: true, error: null });
          const response = await profileService.addPaymentMethod(payment);
          const newPayment = response.data;

          set((state) => ({
            paymentMethods: [...state.paymentMethods, newPayment],
            defaultPayment: state.defaultPayment || newPayment
          }));

          Toast.show({
            type: 'success',
            text1: 'Payment Method Added',
            text2: 'New payment method has been added',
          });

          return newPayment;
        } catch (error: any) {
          const message = error.response?.data?.message || 'Failed to add payment method';
          set({ error: message });

          Toast.show({
            type: 'error',
            text1: 'Failed to Add Payment',
            text2: message,
          });

          throw error;
        } finally {
          set({ loading: false });
        }
      },

      // Update payment method
      updatePaymentMethod: async (paymentId: string, data: Partial<PaymentMethod>) => {
        try {
          set({ loading: true, error: null });
          const response = await profileService.updatePaymentMethod(paymentId, data);
          const updatedPayment = response.data;

          set((state) => ({
            paymentMethods: state.paymentMethods.map(p =>
              p.id === paymentId ? updatedPayment : p
            ),
            defaultPayment: state.defaultPayment?.id === paymentId
              ? updatedPayment
              : state.defaultPayment
          }));

          Toast.show({
            type: 'success',
            text1: 'Payment Updated',
            text2: 'Your payment method has been updated',
          });
        } catch (error: any) {
          const message = error.response?.data?.message || 'Failed to update payment method';
          set({ error: message });

          Toast.show({
            type: 'error',
            text1: 'Update Failed',
            text2: message,
          });

          throw error;
        } finally {
          set({ loading: false });
        }
      },

      // Delete payment method
      deletePaymentMethod: async (paymentId: string) => {
        try {
          set({ loading: true, error: null });
          await profileService.deletePaymentMethod(paymentId);

          set((state) => {
            const paymentMethods = state.paymentMethods.filter(p => p.id !== paymentId);
            const defaultPayment = state.defaultPayment?.id === paymentId
              ? paymentMethods.find(p => p.is_default) || paymentMethods[0] || null
              : state.defaultPayment;

            return { paymentMethods, defaultPayment };
          });

          Toast.show({
            type: 'success',
            text1: 'Payment Method Removed',
            text2: 'The payment method has been removed',
          });
        } catch (error: any) {
          const message = error.response?.data?.message || 'Failed to delete payment method';
          set({ error: message });

          Toast.show({
            type: 'error',
            text1: 'Delete Failed',
            text2: message,
          });

          throw error;
        } finally {
          set({ loading: false });
        }
      },

      // Set default payment method
      setDefaultPayment: async (paymentId: string) => {
        try {
          const payment = get().paymentMethods.find(p => p.id === paymentId);
          if (!payment) return;

          await profileService.setDefaultPaymentMethod(paymentId);

          set((state) => ({
            defaultPayment: payment,
            paymentMethods: state.paymentMethods.map(p => ({
              ...p,
              is_default: p.id === paymentId
            }))
          }));

          Toast.show({
            type: 'success',
            text1: 'Default Payment Set',
            text2: 'Your default payment method has been updated',
          });
        } catch (error: any) {
          const message = error.response?.data?.message || 'Failed to set default payment';
          Toast.show({
            type: 'error',
            text1: 'Update Failed',
            text2: message,
          });
        }
      },

      // Update preferences
      updatePreferences: async (preferences: Partial<UserProfile['preferences']>) => {
        try {
          set({ loading: true, error: null });
          const response = await profileService.updatePreferences(preferences);

          set((state) => ({
            profile: state.profile ? {
              ...state.profile,
              preferences: {
                ...state.profile.preferences,
                ...preferences
              }
            } : null
          }));

          Toast.show({
            type: 'success',
            text1: 'Preferences Updated',
            text2: 'Your preferences have been saved',
          });
        } catch (error: any) {
          const message = error.response?.data?.message || 'Failed to update preferences';
          set({ error: message });

          Toast.show({
            type: 'error',
            text1: 'Update Failed',
            text2: message,
          });

          throw error;
        } finally {
          set({ loading: false });
        }
      },

      // Update default tip percentage
      updateDefaultTip: async (percentage: number) => {
        await get().updatePreferences({ default_tip_percentage: percentage });
      },

      // Get checkout defaults for 3-tap checkout
      getCheckoutDefaults: () => {
        const state = get();
        const profile = state.profile;

        return {
          // Pre-select delivery if user has saved address
          deliveryMethod: state.defaultAddress ? 'delivery' : 'pickup',

          // Use default or most recent address
          address: state.defaultAddress || state.addresses[0] || null,

          // Use default or most recent payment
          paymentMethod: state.defaultPayment || state.paymentMethods[0] || null,

          // Smart tip suggestion based on user preference or average
          tipPercentage: profile?.preferences?.default_tip_percentage ||
                        profile?.average_tip ||
                        0.15
        };
      },

      // Validate address
      validateAddress: (address: Partial<DeliveryAddress>) => {
        if (!address.street) return false;
        if (!address.city) return false;
        if (!address.province) return false;
        if (!address.postal_code) return false;

        // Basic Canadian postal code validation
        const postalCodeRegex = /^[A-Za-z]\d[A-Za-z][ -]?\d[A-Za-z]\d$/;
        if (!postalCodeRegex.test(address.postal_code)) return false;

        return true;
      },

      // Clear profile data (on logout)
      clearProfile: () => {
        set({
          profile: null,
          addresses: [],
          paymentMethods: [],
          defaultAddress: null,
          defaultPayment: null,
          error: null
        });
      },

      // Set error
      setError: (error: string | null) => {
        set({ error });
      }
    }),
    {
      name: 'profile-storage',
      storage: createJSONStorage(() => AsyncStorage),
      partialize: (state) => ({
        profile: state.profile,
        addresses: state.addresses,
        paymentMethods: state.paymentMethods,
        defaultAddress: state.defaultAddress,
        defaultPayment: state.defaultPayment
      })
    }
  )
);