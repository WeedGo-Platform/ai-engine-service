/**
 * Centralized API Endpoints Configuration
 * All API endpoints and URLs should be defined here
 */

// Get base URLs from environment variables with fallbacks
const API_HOST = import.meta.env.VITE_API_HOST || window.location.hostname;
const API_PORT = import.meta.env.VITE_API_PORT || '5024';
const WS_PORT = import.meta.env.VITE_WS_PORT || API_PORT;

// Determine protocol based on current page protocol
const HTTP_PROTOCOL = window.location.protocol === 'https:' ? 'https:' : 'http:';
const WS_PROTOCOL = window.location.protocol === 'https:' ? 'wss:' : 'ws:';

// Base URLs
export const API_BASE_URL = import.meta.env.VITE_API_URL || `${HTTP_PROTOCOL}//${API_HOST}:${API_PORT}`;
export const WS_BASE_URL = import.meta.env.VITE_WS_URL || `${WS_PROTOCOL}//${API_HOST}:${WS_PORT}`;

// API Version
const API_VERSION = 'v1';

// Construct endpoint paths
export const endpoints = {
  // Base API path
  base: `${API_BASE_URL}/api/${API_VERSION}`,
  
  // WebSocket endpoints
  websocket: {
    models: `${WS_BASE_URL}/api/${API_VERSION}/models/ws`,
  },
  
  // Chat endpoints
  chat: {
    base: `${API_BASE_URL}/api/${API_VERSION}/chat`,
    send: `${API_BASE_URL}/api/${API_VERSION}/chat`,
    users: `${API_BASE_URL}/api/${API_VERSION}/chat/users`,
    history: (customerId: string) => `${API_BASE_URL}/api/${API_VERSION}/chat/history/${customerId}`,
    analyzeDecision: `${API_BASE_URL}/api/${API_VERSION}/chat/analyze-decision`,
  },
  
  // Voice endpoints
  voice: `${API_BASE_URL}/api/voice`,
  voiceEndpoints: {
    status: `${API_BASE_URL}/api/voice/status`,
    configure: `${API_BASE_URL}/api/voice/configure`,
    transcribe: `${API_BASE_URL}/api/voice/transcribe`,
    synthesize: `${API_BASE_URL}/api/voice/synthesize`,
    conversation: `${API_BASE_URL}/api/voice/conversation`,
    stream: `${WS_BASE_URL}/api/voice/stream`,
    performance: `${API_BASE_URL}/api/voice/performance`,
    calibrate: `${API_BASE_URL}/api/voice/calibrate`,
    domains: `${API_BASE_URL}/api/voice/domains`,
  },
  
  // AI endpoints
  ai: {
    datasets: `${API_BASE_URL}/api/${API_VERSION}/ai/datasets`,
    stats: `${API_BASE_URL}/api/${API_VERSION}/ai/stats`,
    train: `${API_BASE_URL}/api/${API_VERSION}/ai/train`,
    personalities: `${API_BASE_URL}/api/${API_VERSION}/ai/personalities`,
    generateResponse: `${API_BASE_URL}/api/${API_VERSION}/ai/generate-response`,
    deleteDataset: (datasetId: string) => `${API_BASE_URL}/api/${API_VERSION}/ai/datasets/${datasetId}`,
    hardDeleteDataset: (datasetId: string) => `${API_BASE_URL}/api/${API_VERSION}/ai/datasets/${datasetId}/hard-delete?confirm=true`,
  },
  
  // Model endpoints
  models: {
    list: `${API_BASE_URL}/api/${API_VERSION}/models`,
    import: `${API_BASE_URL}/api/${API_VERSION}/models/import`,
    versions: `${API_BASE_URL}/api/${API_VERSION}/models/versions`,
    base: `${API_BASE_URL}/api/${API_VERSION}/models/base`,
    trainingSessions: `${API_BASE_URL}/api/${API_VERSION}/models/training-sessions`,
    deployments: `${API_BASE_URL}/api/${API_VERSION}/models/deployments`,
    deploy: `${API_BASE_URL}/api/${API_VERSION}/models/deploy`,
    train: `${API_BASE_URL}/api/${API_VERSION}/models/train`,
    switch: `${API_BASE_URL}/api/${API_VERSION}/models/switch`,
    health: (modelId: string) => `${API_BASE_URL}/api/${API_VERSION}/models/${modelId}/health`,
    delete: (modelId: string) => `${API_BASE_URL}/api/${API_VERSION}/models/${modelId}`,
    test: (modelId: string) => `${API_BASE_URL}/api/${API_VERSION}/models/${modelId}/test`,
    deploymentStatus: (deploymentId: string) => `${API_BASE_URL}/api/${API_VERSION}/models/deployments/${deploymentId}`,
    deploymentLogs: (deploymentId: string) => `${API_BASE_URL}/api/${API_VERSION}/models/deployments/${deploymentId}/logs`,
    rollback: (deploymentId: string) => `${API_BASE_URL}/api/${API_VERSION}/models/deployments/${deploymentId}/rollback`,
    retry: (deploymentId: string) => `${API_BASE_URL}/api/${API_VERSION}/models/deployments/${deploymentId}/retry`,
  },
  
  // Training endpoints
  training: {
    accuracy: `${API_BASE_URL}/api/${API_VERSION}/training/accuracy`,
    examples: `${API_BASE_URL}/api/${API_VERSION}/training/examples`,
    apply: `${API_BASE_URL}/api/${API_VERSION}/training/apply`,
  },
  
  // Intent endpoints
  intents: {
    list: `${API_BASE_URL}/api/${API_VERSION}/intents`,
    create: `${API_BASE_URL}/api/${API_VERSION}/intents`,
    update: (intentId: string) => `${API_BASE_URL}/api/${API_VERSION}/intents/${intentId}`,
    delete: (intentId: string) => `${API_BASE_URL}/api/${API_VERSION}/intents/${intentId}`,
  },
  
  // Skip words endpoints
  skipWords: {
    list: `${API_BASE_URL}/api/${API_VERSION}/skip-words`,
    create: `${API_BASE_URL}/api/${API_VERSION}/skip-words`,
    delete: (word: string) => `${API_BASE_URL}/api/${API_VERSION}/skip-words/${word}`,
    toggle: (word: string) => `${API_BASE_URL}/api/${API_VERSION}/skip-words/${word}/toggle`,
  },
  
  // Medical intents
  medicalIntents: `${API_BASE_URL}/api/${API_VERSION}/medical-intents`,
  
  // System configuration
  systemConfig: `${API_BASE_URL}/api/${API_VERSION}/system-config`,
  
  // Products
  products: {
    search: `${API_BASE_URL}/api/${API_VERSION}/products/search`,
  },
  
  // Sessions
  sessions: {
    close: `${API_BASE_URL}/api/${API_VERSION}/sessions/close`,
  },
  
  // Conversations
  conversations: {
    get: (sessionId: string) => `${API_BASE_URL}/api/${API_VERSION}/conversations/${sessionId}`,
  },
  
  // Datasets
  datasets: {
    upload: `${API_BASE_URL}/api/${API_VERSION}/datasets/upload`,
  },
  
  // Services
  services: {
    logs: (serviceName: string, start: string, end: string) => 
      `${API_BASE_URL}/api/${API_VERSION}/services/${serviceName}/logs?start=${start}&end=${end}`,
  },
  
  // Admin
  admin: {
    clearCache: `${API_BASE_URL}/api/${API_VERSION}/admin/cache/clear`,
  },
};

// Helper function to update API base URL dynamically
export function updateApiBaseUrl(newUrl: string) {
  // This would require making endpoints reactive or implementing a different pattern
  // For now, this is a placeholder for future implementation
  console.warn('Dynamic URL update not yet implemented. Please reload the page after changing API URL.');
}

// Export individual endpoint builders for convenience
export const getApiUrl = (path: string) => `${API_BASE_URL}${path}`;
export const getWsUrl = (path: string) => `${WS_BASE_URL}${path}`;