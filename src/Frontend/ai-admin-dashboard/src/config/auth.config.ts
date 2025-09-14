// Authentication configuration
export const authConfig = {
  // Token refresh settings
  tokenRefresh: {
    // Enable automatic token refresh
    enabled: import.meta.env.VITE_AUTO_REFRESH_ENABLED !== 'false',
    
    // Buffer time before token expiry to trigger refresh (in seconds)
    // Default: 5 minutes before expiry
    bufferTime: parseInt(import.meta.env.VITE_TOKEN_REFRESH_BUFFER || '300'),
    
    // Maximum number of refresh retry attempts
    maxRetries: parseInt(import.meta.env.VITE_TOKEN_REFRESH_MAX_RETRIES || '3'),
    
    // Retry delay in milliseconds
    retryDelay: parseInt(import.meta.env.VITE_TOKEN_REFRESH_RETRY_DELAY || '1000'),
  },
  
  // Session settings
  session: {
    // Session timeout in seconds (0 = no timeout)
    timeout: parseInt(import.meta.env.VITE_SESSION_TIMEOUT || '0'),
    
    // Check session validity on window focus
    checkOnFocus: import.meta.env.VITE_CHECK_SESSION_ON_FOCUS !== 'false',
    
    // Check session validity interval in seconds (0 = disabled)
    checkInterval: parseInt(import.meta.env.VITE_SESSION_CHECK_INTERVAL || '0'),
  },
  
  // Storage settings
  storage: {
    // Storage key prefix for auth tokens
    keyPrefix: import.meta.env.VITE_AUTH_STORAGE_PREFIX || 'weedgo_auth_',
    
    // Use sessionStorage instead of localStorage
    useSessionStorage: import.meta.env.VITE_USE_SESSION_STORAGE === 'true',
  },
  
  // API endpoints
  endpoints: {
    baseUrl: import.meta.env.VITE_API_URL || 'http://localhost:5024',
    login: '/api/v1/auth/admin/login',
    logout: '/api/v1/auth/admin/logout',
    refresh: '/api/v1/auth/admin/refresh',
    verify: '/api/v1/auth/admin/verify',
    me: '/api/v1/auth/admin/me',
  },
  
  // Redirect settings
  redirects: {
    // URL to redirect after login
    afterLogin: import.meta.env.VITE_AFTER_LOGIN_URL || '/dashboard',
    
    // URL to redirect after logout
    afterLogout: import.meta.env.VITE_AFTER_LOGOUT_URL || '/login',
    
    // URL to redirect when unauthorized
    unauthorized: import.meta.env.VITE_UNAUTHORIZED_URL || '/login',
  },
};

// Helper function to get storage based on config
export const getAuthStorage = () => {
  return authConfig.storage.useSessionStorage ? sessionStorage : localStorage;
};

// Helper function to get storage key with prefix
export const getStorageKey = (key: string) => {
  return `${authConfig.storage.keyPrefix}${key}`;
};