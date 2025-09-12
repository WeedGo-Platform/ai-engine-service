import { apiClient } from './api-client';

// Get the axios instance from the centralized client
const api = apiClient.getAxiosInstance();

// Add auth token interceptor
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Types for unified authentication
export interface UserContext {
  type: 'customer' | 'admin';
  role: string;
  tenant_id: string | null;
  store_id: string | null;
  permissions: string[];
  access_token: string;
}

export interface UnifiedLoginResponse {
  message: string;
  user_id: string;
  email: string;
  name: string;
  available_contexts: UserContext[];
  default_context: string;
}

export interface ContextSwitchResponse {
  message: string;
  new_context: UserContext;
}

// Unified Auth API
export const unifiedAuthApi = {
  // Unified login that returns all available contexts
  login: async (email: string, password: string, preferredContext?: string) => {
    try {
      const response = await api.post<UnifiedLoginResponse>('/api/v1/auth/context/login', {
        email,
        password,
        context: preferredContext
      });
      
      // Store the user info and contexts
      if (response.data) {
        localStorage.setItem('user_id', response.data.user_id);
        localStorage.setItem('user_email', response.data.email);
        localStorage.setItem('user_name', response.data.name);
        localStorage.setItem('available_contexts', JSON.stringify(response.data.available_contexts));
        localStorage.setItem('current_context', response.data.default_context);
        
        // Set the default context token
        const defaultContext = response.data.available_contexts.find(
          ctx => ctx.type === response.data.default_context
        );
        if (defaultContext) {
          localStorage.setItem('access_token', defaultContext.access_token);
          localStorage.setItem('user_role', defaultContext.role);
        }
      }
      
      return response.data;
    } catch (error) {
      console.error('Unified login failed:', error);
      throw error;
    }
  },
  
  // Switch between customer and admin contexts
  switchContext: async (targetContext: 'customer' | 'admin') => {
    try {
      const response = await api.post<ContextSwitchResponse>('/api/v1/auth/context/switch-context', {
        target_context: targetContext
      });
      
      // Update the stored context and token
      if (response.data?.new_context) {
        localStorage.setItem('current_context', targetContext);
        localStorage.setItem('access_token', response.data.new_context.access_token);
        localStorage.setItem('user_role', response.data.new_context.role);
      }
      
      return response.data;
    } catch (error) {
      console.error('Context switch failed:', error);
      throw error;
    }
  },
  
  // Get available contexts for current user
  getMyContexts: async () => {
    try {
      const response = await api.get('/api/v1/auth/context/contexts');
      return response.data;
    } catch (error) {
      console.error('Failed to get contexts:', error);
      throw error;
    }
  },
  
  // Register user with dual role (admin + customer)
  registerDualRole: async (data: {
    email: string;
    password: string;
    first_name: string;
    last_name: string;
    admin_role: string;
    tenant_id?: string;
    store_id?: string;
  }) => {
    try {
      const response = await api.post('/api/v1/auth/context/register-dual-role', data);
      
      // Store contexts if registration successful
      if (response.data?.contexts) {
        localStorage.setItem('user_id', response.data.user_id);
        localStorage.setItem('user_email', response.data.email);
        localStorage.setItem('available_contexts', JSON.stringify(response.data.contexts));
        
        // Set admin context as default for dual-role users
        const adminContext = response.data.contexts.find((ctx: UserContext) => ctx.type === 'admin');
        if (adminContext) {
          localStorage.setItem('access_token', adminContext.access_token);
          localStorage.setItem('current_context', 'admin');
          localStorage.setItem('user_role', adminContext.role);
        }
      }
      
      return response.data;
    } catch (error) {
      console.error('Dual role registration failed:', error);
      throw error;
    }
  },
  
  // Clear all auth data
  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_id');
    localStorage.removeItem('user_email');
    localStorage.removeItem('user_name');
    localStorage.removeItem('user_role');
    localStorage.removeItem('available_contexts');
    localStorage.removeItem('current_context');
    localStorage.removeItem('user');
  },
  
  // Check if user has multiple contexts
  hasMultipleContexts: (): boolean => {
    const contexts = localStorage.getItem('available_contexts');
    if (!contexts) return false;
    try {
      const parsed = JSON.parse(contexts);
      return Array.isArray(parsed) && parsed.length > 1;
    } catch {
      return false;
    }
  },
  
  // Get current context type
  getCurrentContext: (): 'customer' | 'admin' | null => {
    const context = localStorage.getItem('current_context');
    return context as 'customer' | 'admin' | null;
  },
  
  // Get stored contexts
  getStoredContexts: (): UserContext[] => {
    const contexts = localStorage.getItem('available_contexts');
    if (!contexts) return [];
    try {
      return JSON.parse(contexts);
    } catch {
      return [];
    }
  }
};

export default unifiedAuthApi;