import { apiClient } from './api-client';

// Get the axios instance from the centralized client
// This already includes tenant headers and auth token interceptors
const api = apiClient.getAxiosInstance();

// Additional auth token interceptor (if not already handled by api-client)
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Admin Management APIs (unified endpoints)
export const modelApi = {
  // Get all available models from models/LLM directory
  getModels: async () => {
    const response = await api.get('/api/admin/models');
    return response.data;
  },

  // Get all agents from prompts/agents directory
  getAgents: async () => {
    const response = await api.get('/api/admin/agents');
    return response.data;
  },

  // Get personalities for a specific agent
  getPersonalities: async (agentId: string) => {
    const response = await api.get(`/api/admin/agents/${agentId}/personalities`);
    return response.data;
  },

  // Get config.json for a specific agent
  getAgentConfig: async (agentId: string) => {
    const response = await api.get(`/api/admin/agents/${agentId}/config`);
    return response.data;
  },


  // Get currently active tools
  getActiveTools: async () => {
    const response = await api.get('/api/admin/active-tools');
    return response.data;
  },
  
  // Get current model status
  getModelStatus: async () => {
    const response = await api.get('/api/admin/model/status');
    return response.data;
  },
  
  // Get current model information (new endpoint)
  getCurrentModel: async () => {
    const response = await api.get('/api/admin/model');
    return response.data;
  },
  
  // Change personality for a specific agent
  changePersonality: async (agentId: string, personalityId: string) => {
    const response = await api.post(`/api/admin/agents/${agentId}/personality?personality_id=${personalityId}`);
    return response.data;
  }
};

// Chat API
export const chatApi = {
  sendMessage: async (message: string, sessionId: string, agentId?: string, userId?: string) => {
    const payload: any = {
      message,
      session_id: sessionId
    };

    // Only include agent_id if it's provided and not empty
    if (agentId && agentId.trim()) {
      payload.agent_id = agentId;
    }

    // Include user_id if provided or get from localStorage
    if (userId) {
      payload.user_id = userId;
    } else {
      // Try to get user from localStorage
      const userStr = localStorage.getItem('user');
      if (userStr) {
        try {
          const user = JSON.parse(userStr);
          if (user && user.id) {
            payload.user_id = user.id;
          }
        } catch (e) {
          console.error('Failed to parse user from localStorage:', e);
        }
      }
    }

    const response = await api.post('/api/v1/chat/message', payload);
    return response.data;
  }
};

// Voice API
export const voiceApi = {
  // Get available voices
  getVoices: async () => {
    try {
      // api.get() already unwraps response.data, so we get the data directly
      const data = await api.get('/api/voice/voices');
      // Backend returns { status: 'success', voices: [...], current_voice: null }
      return data.voices || [];
    } catch (error) {
      console.error('Failed to get voices:', error);
      return [];
    }
  },

  // Change selected voice
  changeVoice: async (voiceId: string) => {
    try {
      const data = await api.post('/api/voice/change', { voice_id: voiceId });
      return data;
    } catch (error) {
      console.error('Failed to change voice:', error);
      throw error;
    }
  },

  // Synthesize speech using backend Piper TTS
  synthesize: async (text: string, voice?: string) => {
    try {
      const formData = new FormData();
      formData.append('text', text);
      if (voice) {
        formData.append('voice', voice);
      }
      formData.append('speed', '1.0');
      formData.append('format', 'wav');

      // Use the raw axios instance for blob responses
      const axiosInstance = api.getAxiosInstance();
      const response = await axiosInstance.post('/api/voice/synthesize', formData, {
        responseType: 'blob',
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      // For blob responses, we need response.data (not unwrapped)
      return response.data;
    } catch (error) {
      console.error('Failed to synthesize speech:', error);
      throw error;
    }
  }
};

// Auth API
export const authApi = {
  // Login with email and password
  login: async (data: { email: string; password: string }) => {
    try {
      const response = await api.post('/api/v2/identity-access/auth/customer/login', data);
      // Store token on successful login
      if (response.data.access_token) {
        localStorage.setItem('access_token', response.data.access_token);
        localStorage.setItem('user', JSON.stringify(response.data.user));
      }
      return response.data;
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  },

  // Register new user
  register: async (data: {
    email: string;
    password: string;
    first_name: string;
    last_name: string;
    date_of_birth: string;
    phone: string
  }) => {
    try {
      const response = await api.post('/api/v2/identity-access/auth/customer/register', data);
      // Store token on successful registration
      if (response.data.access_token) {
        localStorage.setItem('access_token', response.data.access_token);
        localStorage.setItem('user', JSON.stringify(response.data.user));
      }
      return response.data;
    } catch (error) {
      console.error('Registration failed:', error);
      throw error;
    }
  },

  // Logout user
  logout: async () => {
    try {
      await api.post('/api/v2/identity-access/auth/customer/logout');
      // Clear local storage
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      return { success: true };
    } catch (error) {
      console.error('Logout failed:', error);
      // Clear local storage even if API call fails
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      throw error;
    }
  },

  // Verify token
  verifyToken: async () => {
    try {
      const response = await api.get('/api/v2/identity-access/auth/customer/validate');
      return response.data;
    } catch (error) {
      console.error('Token verification failed:', error);
      throw error;
    }
  },

  // Get current user info
  getCurrentUser: async () => {
    try {
      const response = await api.get('/api/v2/identity-access/users/me');
      return response.data;
    } catch (error) {
      console.error('Failed to get user info:', error);
      throw error;
    }
  },

  // Send OTP for login
  sendOTP: async (email: string) => {
    try {
      const response = await api.post('/api/v2/identity-access/auth/otp/send', { email });
      return response.data;
    } catch (error) {
      console.error('Send OTP failed:', error);
      throw error;
    }
  },

  // Verify OTP and login
  verifyOTP: async (email: string, otp: string) => {
    try {
      const response = await api.post('/api/v2/identity-access/auth/otp/verify', { email, otp });
      // Store token on successful OTP verification
      if (response.data.access_token) {
        localStorage.setItem('access_token', response.data.access_token);
        localStorage.setItem('user', JSON.stringify(response.data.user));
      }
      return response.data;
    } catch (error) {
      console.error('Verify OTP failed:', error);
      throw error;
    }
  }
};

// Export both the axios instance and the centralized client
export default api;
export { apiClient };