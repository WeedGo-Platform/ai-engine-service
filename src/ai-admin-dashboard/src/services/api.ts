import axios from 'axios';

const API_BASE_URL = 'http://localhost:5024';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  }
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

  // Load model with optional agent and personality
  loadModel: async (params: {
    model: string;
    agent?: string;
    personality?: string;
    apply_config?: boolean;
  }) => {
    const response = await api.post('/api/admin/load-model', params);
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
  }
};

// Chat API
export const chatApi = {
  sendMessage: async (message: string, sessionId: string, agentId?: string) => {
    const payload: any = {
      message,
      session_id: sessionId
    };
    
    // Only include agent_id if it's provided and not empty
    if (agentId && agentId.trim()) {
      payload.agent_id = agentId;
    }
    
    const response = await api.post('/api/chat', payload);
    return response.data;
  }
};

export default api;