// API Service Layer for WeedGo AI Admin Dashboard
import { API_BASE_URL, endpoints } from '../config/endpoints';

class ApiService {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      });

      if (!response.ok) {
        throw new Error(`API Error: ${response.status} ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API Request Failed: ${endpoint}`, error);
      throw error;
    }
  }

  // Dashboard APIs
  async getDashboardStats() {
    // Fetch multiple metrics for dashboard
    const [aiStats, trainingStats, performanceStats, dashboardData] = await Promise.all([
      this.request<any>('/api/v1/ai/stats').catch(() => ({ accuracy: 0, total_interactions: 0 })),
      this.request<any>('/api/v1/training/accuracy').catch(() => ({ accuracy: 0, examples_count: 0 })),
      this.request<any>('/api/v1/analytics/performance').catch(() => ({ queries_today: 0 })),
      this.request<any>('/api/v1/analytics/dashboard').catch(() => ({}))
    ]);
    
    return {
      accuracy: aiStats.accuracy || trainingStats.accuracy || 0,
      accuracy_trend: dashboardData.accuracy_trend || 0,
      total_examples: aiStats.total_interactions || trainingStats.examples_count || 0,
      examples_today: dashboardData.examples_today || 0,
      unique_patterns: aiStats.unique_intents || 0,
      queries_today: performanceStats.queries_today || dashboardData.queries_today || 0,
      peak_time: dashboardData.peak_time || null
    };
  }

  async getSystemHealth() {
    // Use AI health endpoint for health check
    return this.request<any>('/api/v1/ai/health').catch(() => {
      // Fallback to root endpoint
      return this.request<any>('/health');
    });
  }
  
  async getRecentActivity() {
    // Fetch recent activity from the backend
    const [conversations, trainingActivity] = await Promise.all([
      this.request<any>('/api/v1/conversations/history?limit=5').catch((err) => {
        console.error('Failed to fetch conversations:', err);
        return { conversations: [] };
      }),
      this.request<any>('/api/v1/ai/training-examples?limit=5').catch((err) => {
        console.error('Failed to fetch training examples:', err);
        return { examples: [] };
      })
    ]);
    
    console.log('Fetched conversations:', conversations);
    console.log('Fetched training activity:', trainingActivity);
    
    const activities = [];
    
    // Add conversation activities
    if (conversations.conversations && Array.isArray(conversations.conversations)) {
      conversations.conversations.forEach((conv: any) => {
        // Get the last customer message from the messages array
        const customerMessages = conv.messages?.filter((m: any) => m.sender === 'customer') || [];
        const lastMessage = customerMessages[customerMessages.length - 1]?.message || 
                          conv.messages?.[0]?.message || 
                          'No message content';
        
        const timestamp = conv.end_time || conv.start_time || new Date().toISOString();
        
        activities.push({
          time: this.getRelativeTime(timestamp),
          action: `Customer query processed: "${lastMessage.substring(0, 50)}${lastMessage.length > 50 ? '...' : ''}"`,
          type: 'default'
        });
      });
    }
    
    // Add training activities
    if (trainingActivity.examples && Array.isArray(trainingActivity.examples)) {
      trainingActivity.examples.forEach((example: any) => {
        const input = example.query || example.input || example.user_message || 'Training data';
        // Only add if there's actual content
        if (input && input.trim()) {
          activities.push({
            time: this.getRelativeTime(example.created_at || new Date().toISOString()),
            action: `New training data: "${input.substring(0, 40)}${input.length > 40 ? '...' : ''}"`,
            type: 'success'
          });
        }
      });
    }
    
    // Sort by timestamp and return top 5
    const sortedActivities = activities.sort((a, b) => {
      const timeA = this.parseRelativeTime(a.time);
      const timeB = this.parseRelativeTime(b.time);
      return timeB - timeA;
    }).slice(0, 5);
    
    console.log('Returning activities from database:', sortedActivities);
    
    // NO MOCK DATA - Return only real database data
    return sortedActivities;
  }
  
  private getRelativeTime(timestamp: string): string {
    if (!timestamp) return 'Unknown time';
    
    const now = new Date();
    const time = new Date(timestamp);
    
    // Check for invalid date
    if (isNaN(time.getTime())) {
      return 'Unknown time';
    }
    
    const diff = now.getTime() - time.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    
    if (diff < 0) return 'just now'; // Handle future dates
    if (minutes < 1) return 'just now';
    if (minutes < 60) return `${minutes} min ago`;
    if (hours < 24) return `${hours} hour${hours > 1 ? 's' : ''} ago`;
    if (days === 0) return 'today';
    return `${days} day${days > 1 ? 's' : ''} ago`;
  }
  
  private parseRelativeTime(relativeTime: string): number {
    const now = Date.now();
    if (relativeTime === 'just now' || relativeTime === 'today') return now;
    if (relativeTime === 'Unknown time') return 0; // Sort unknown times to the end
    
    const match = relativeTime.match(/(\d+)\s*(min|hour|day)/i);
    if (!match) return now;
    
    const value = parseInt(match[1]);
    const unit = match[2].toLowerCase();
    
    const multipliers: Record<string, number> = {
      min: 60000,
      hour: 3600000,
      day: 86400000
    };
    
    return now - (value * (multipliers[unit] || 0));
  }

  // Training Center APIs
  async getTrainingDatasets() {
    // Use actual datasets endpoint
    return this.request<any>('/api/v1/ai/datasets').catch(() => ({
      datasets: [],
      total: 0
    }));
  }

  async uploadDataset(metadata: any, examples: any[]) {
    return this.request<any>('/api/v1/datasets/upload', {
      method: 'POST',
      body: JSON.stringify({ metadata, examples }),
    });
  }

  async getIntents() {
    // Use actual intents endpoint
    return this.request<any>('/api/v1/intents').catch(() => ({
      intents: []
    }));
  }

  async createIntent(intent: any) {
    return this.request<any>('/api/v1/intents', {
      method: 'POST',
      body: JSON.stringify(intent),
    });
  }

  async updateIntent(id: string, intent: any) {
    return this.request<any>(`/api/v1/intents/${id}`, {
      method: 'PUT',
      body: JSON.stringify(intent),
    });
  }

  async deleteIntent(id: string) {
    return this.request<any>(`/api/v1/intents/${id}`, {
      method: 'DELETE',
    });
  }

  // Chat APIs
  async sendChatMessage(message: string, sessionId: string, customerId: string, budtenderPersonality?: string) {
    return this.request<any>('/api/v1/chat', {
      method: 'POST',
      body: JSON.stringify({
        message,
        customer_id: customerId,
        session_id: sessionId,
        budtender_personality: budtenderPersonality,
      }),
    });
  }

  async getChatHistory(customerId: string, limit: number = 20, sessionId?: string) {
    const params = new URLSearchParams({
      limit: limit.toString(),
      ...(sessionId && { session_id: sessionId }),
    });
    return this.request<any>(`/api/v1/chat/history/${customerId}?${params}`);
  }

  // Conversation History APIs
  async getConversationHistory(filters: any) {
    // Get all conversations (sessions) from the backend
    const params = new URLSearchParams();
    if (filters.start_date) params.append('start_date', filters.start_date);
    if (filters.end_date) params.append('end_date', filters.end_date);
    if (filters.customer) params.append('customer', filters.customer);
    if (filters.budtender) params.append('budtender', filters.budtender);
    if (filters.intent) params.append('intent', filters.intent);
    
    return this.request<any>(`/api/v1/conversations/history?${params}`);
  }
  
  // Get detailed chat history for a specific customer
  async getCustomerChatHistory(customerId: string, sessionId?: string, limit: number = 20) {
    const params = new URLSearchParams({ limit: limit.toString() });
    if (sessionId) params.append('session_id', sessionId);
    
    return this.request<any>(`/api/v1/chat/history/${customerId}?${params}`);
  }

  // Conversation Flow APIs
  async getConversationFlows() {
    // Use actual conversation flows endpoint
    return this.request<any>('/api/v1/conversation-flows').catch(() => ({
      flows: [],
      total: 0
    }));
  }

  async saveConversationFlow(flow: any) {
    return this.request<any>('/api/v1/conversation-flows', {
      method: 'POST',
      body: JSON.stringify(flow),
    });
  }

  async deleteConversationFlow(flowId: string) {
    return this.request<any>(`/api/v1/conversation-flows/${flowId}`, {
      method: 'DELETE',
    });
  }

  // Service Management APIs
  async getServices() {
    // Check actual service health
    const [aiHealth, analyticsPerf] = await Promise.all([
      this.request<any>('/api/v1/ai/health').catch(() => ({ status: 'error' })),
      this.request<any>('/api/v1/analytics/performance').catch(() => ({ status: 'error' }))
    ]);
    
    return {
      services: [
        { 
          name: 'ai-engine', 
          status: aiHealth.status === 'healthy' ? 'running' : 
                  aiHealth.status === 'degraded' ? 'running' : 'error', 
          replicas: 1 
        },
        { name: 'analytics', status: analyticsPerf.status ? 'running' : 'error', replicas: 1 },
        { name: 'database', status: 'running', replicas: 1 }
      ]
    };
  }

  async getServiceLogs(serviceName: string, filters: any) {
    const params = new URLSearchParams();
    Object.keys(filters).forEach(key => {
      if (filters[key]) params.append(key, filters[key]);
    });
    return this.request<any>(`/api/v1/services/${serviceName}/logs?${params}`);
  }

  async restartService(serviceName: string) {
    return this.request<any>(`/api/v1/services/${serviceName}/restart`, {
      method: 'POST',
    });
  }

  async scaleService(serviceName: string, replicas: number) {
    return this.request<any>(`/api/v1/services/${serviceName}/scale`, {
      method: 'POST',
      body: JSON.stringify({ replicas }),
    });
  }

  // Model Management APIs
  async getActiveModel() {
    // First, check what model is actually loaded right now
    const currentModel = await this.request<any>('/api/v1/models/current').catch(() => null);
    
    if (currentModel && currentModel.status === 'loaded') {
      return {
        model: currentModel.model_id || currentModel.model_name,
        version: 'v1.0',
        status: 'active'
      };
    }
    
    // Fallback to checking versions endpoint
    const versions = await this.request<any>('/api/v1/models/versions').catch(() => []);
    const activeVersion = Array.isArray(versions) ? versions.find((v: any) => v.is_active) : null;
    
    return {
      model: activeVersion?.name || 'unknown',
      version: activeVersion?.version || 'v1.0',
      status: activeVersion ? 'active' : 'inactive'
    };
  }

  async getAvailableModels() {
    // Get models from base endpoint
    const baseModels = await this.request<any>('/api/v1/models/base').catch(() => []);
    
    // Map the API response fields to expected format
    const models = Array.isArray(baseModels) ? baseModels.map((model: any) => ({
      model_id: model.model_id,
      model_name: model.model_name,
      file_path: model.file_path,
      file_size_gb: model.file_size_gb,
      is_available: model.is_available,
      source: model.source,
      download_status: model.download_status
    })) : [];
    
    return {
      models
    };
  }

  async deployModel(modelId: string, options?: any) {
    return this.request<any>('/api/v1/models/deploy', {
      method: 'POST',
      body: JSON.stringify({ 
        model_id: modelId,
        ...options 
      }),
    });
  }
  
  async getDeploymentStatus(deploymentId: string) {
    return this.request<any>(`/api/v1/models/deployments/${deploymentId}`);
  }
  
  async rollbackDeployment(deploymentId: string) {
    return this.request<any>(`/api/v1/models/deployments/${deploymentId}/rollback`, {
      method: 'POST',
    });
  }
  
  async retryDeployment(deploymentId: string) {
    return this.request<any>(`/api/v1/models/deployments/${deploymentId}/retry`, {
      method: 'POST',
    });
  }
  
  async testModel(modelId: string, testCases?: any[]) {
    return this.request<any>('/api/v1/models/test', {
      method: 'POST',
      body: JSON.stringify({ model_id: modelId, test_cases: testCases }),
    });
  }
  
  async getModelHealth(modelId: string) {
    return this.request<any>(`/api/v1/models/${modelId}/health`);
  }
  
  async deleteModel(modelId: string, options?: { cleanup?: boolean }) {
    return this.request<any>(`/api/v1/models/${modelId}`, {
      method: 'DELETE',
      body: JSON.stringify(options || {}),
    });
  }
  
  async getDeploymentLogs(deploymentId: string, filters?: any) {
    const params = new URLSearchParams();
    if (filters) {
      Object.keys(filters).forEach(key => {
        if (filters[key] !== undefined) {
          params.append(key, filters[key].toString());
        }
      });
    }
    return this.request<any>(`/api/v1/models/deployments/${deploymentId}/logs?${params}`);
  }
  
  async getResourceMetrics() {
    return this.request<any>('/api/v1/system/metrics');
  }
  
  async compareModels(modelIds: string[]) {
    return this.request<any>('/api/v1/models/compare', {
      method: 'POST',
      body: JSON.stringify({ model_ids: modelIds }),
    });
  }
  
  async getModelBenchmarks(modelId: string) {
    return this.request<any>(`/api/v1/models/${modelId}/benchmarks`);
  }
  
  async runModelBenchmark(modelId: string, config?: any) {
    return this.request<any>(`/api/v1/models/${modelId}/benchmark`, {
      method: 'POST',
      body: JSON.stringify(config || {}),
    });
  }
  
  async getModelConfigPresets() {
    return this.request<any>('/api/v1/models/config-presets');
  }
  
  async saveModelConfigPreset(name: string, config: any) {
    return this.request<any>('/api/v1/models/config-presets', {
      method: 'POST',
      body: JSON.stringify({ name, config }),
    });
  }
  
  async deleteModelConfigPreset(presetId: string) {
    return this.request<any>(`/api/v1/models/config-presets/${presetId}`, {
      method: 'DELETE',
    });
  }

  async updateModelConfig(config: any) {
    return this.request<any>('/api/v1/models/config', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  async importModel(formData: FormData) {
    return fetch(`${this.baseUrl}/api/v1/models/import`, {
      method: 'POST',
      body: formData,
    }).then(res => {
      if (!res.ok) throw new Error('Failed to import model');
      return res.json();
    });
  }

  async fineTuneModel(formData: FormData) {
    return fetch(`${this.baseUrl}/api/v1/models/fine-tune`, {
      method: 'POST',
      body: formData,
    }).then(res => {
      if (!res.ok) throw new Error('Failed to start fine-tuning');
      return res.json();
    });
  }

  // AI Personality APIs
  async getPersonalities() {
    // Fetch actual personalities from the backend
    return this.request<any>('/api/v1/ai/personalities', {
      method: 'GET',
    });
  }

  async savePersonality(personality: any) {
    console.log('API: Saving personality:', personality);
    const response = await this.request<any>('/api/v1/ai/personality', {
      method: 'POST',
      body: JSON.stringify(personality),
    });
    console.log('API: Save response:', response);
    return response;
  }

  async deletePersonality(personalityId: string) {
    return this.request<any>(`/api/v1/ai/personality/${personalityId}`, {
      method: 'DELETE',
    });
  }

  async activatePersonality(personalityId: string) {
    return this.request<any>(`/api/v1/ai/personality/${personalityId}/activate`, {
      method: 'POST',
    });
  }

  // Analytics APIs
  async getAnalytics(dateRange: { start: string; end: string }) {
    // Use GET method for dashboard analytics endpoint
    const params = new URLSearchParams({
      start_date: dateRange.start,
      end_date: dateRange.end
    });
    return this.request<any>(`/api/v1/analytics/dashboard?${params}`);
  }

  async getMetrics(metric: string, dateRange: { start: string; end: string }) {
    // Use POST method for analytics endpoint with specific metric
    // Map metric names to valid backend values
    const validMetrics = ['conversion', 'engagement', 'product', 'customer'];
    const metricType = validMetrics.includes(metric) ? metric : 'engagement';
    
    return this.request<any>('/api/v1/analytics', {
      method: 'POST',
      body: JSON.stringify({
        metric_type: metricType,
        start_date: dateRange.start,
        end_date: dateRange.end,
        granularity: 'daily'
      }),
    });
  }

  // Decision Tree APIs
  async getDecisionTree() {
    // Get training examples and intents to build decision tree view
    const [examples, intents] = await Promise.all([
      this.request<any>('/api/v1/ai/training-examples').catch(() => ({ examples: [] })),
      this.request<any>('/api/v1/intents').catch(() => [])
    ]);
    
    return {
      sample_queries: examples.examples?.slice(0, 5).map((e: any) => e.input) || [],
      tree_structure: intents
    };
  }

  async getDecisionTreeAnalytics() {
    // Use analytics endpoint for decision tree metrics
    return this.request<any>('/api/v1/analytics', {
      method: 'POST',
      body: JSON.stringify({
        metric_type: 'engagement',
        start_date: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        end_date: new Date().toISOString().split('T')[0],
        granularity: 'daily'
      }),
    });
  }

  // Product APIs
  async searchProducts(query: string, filters?: any) {
    // Use the actual products search endpoint
    return this.request<any>('/api/v1/products/search', {
      method: 'POST',
      body: JSON.stringify({ query, ...filters }),
    });
  }

  // Knowledge Base APIs
  async getProducts(limit: number = 100) {
    return this.request<any>(`/api/v1/products?limit=${limit}`);
  }
  
  async getProductCategories() {
    return this.request<any>('/api/v1/products/categories');
  }
  
  async getMedicalIntents() {
    return this.request<any>('/api/v1/medical-intents');
  }
  
  async addMedicalKeyword(intentId: string, keyword: string) {
    return this.request<any>(`/api/v1/medical-intents/${intentId}/keywords`, {
      method: 'POST',
      body: JSON.stringify({ keyword }),
    });
  }
  
  async removeMedicalKeyword(intentId: string, keyword: string) {
    return this.request<any>(`/api/v1/medical-intents/${intentId}/keywords/${keyword}`, {
      method: 'DELETE',
    });
  }

  // Training Hub APIs
  async getTrainingExamples() {
    return this.request<any>('/api/v1/ai/training-examples');
  }
  
  async addTrainingExamples(examples: any[]) {
    return this.request<any>('/api/v1/training/examples', {
      method: 'POST',
      body: JSON.stringify({ examples }),
    });
  }
  
  async applyTraining() {
    return this.request<any>('/api/v1/training/apply', {
      method: 'POST',
    });
  }
  
  async getTrainingSessions() {
    return this.request<any>('/api/v1/models/training-sessions');
  }
  
  async trainModel(config: any) {
    return this.request<any>('/api/v1/models/train', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }
  
  async getSkipWords() {
    return this.request<any>('/api/v1/skip-words');
  }
  
  async addSkipWord(word: string) {
    return this.request<any>('/api/v1/skip-words', {
      method: 'POST',
      body: JSON.stringify({ word }),
    });
  }
  
  async deleteSkipWord(word: string) {
    return this.request<any>(`/api/v1/skip-words/${word}`, {
      method: 'DELETE',
    });
  }
  
  async toggleSkipWord(word: string) {
    return this.request<any>(`/api/v1/skip-words/${word}/toggle`, {
      method: 'PUT',
    });
  }
  
  // AI Configuration APIs
  async getSystemConfig() {
    return this.request<any>('/api/v1/system-config');
  }
  
  async updateSystemConfig(key: string, value: any) {
    return this.request<any>(`/api/v1/system-config/${key}`, {
      method: 'PUT',
      body: JSON.stringify({ value }),
    });
  }
  
  // Admin APIs
  async clearCache() {
    return this.request<any>('/api/v1/admin/cache/clear', {
      method: 'POST',
    });
  }
  
  async getErrors() {
    return this.request<any>('/api/v1/admin/errors');
  }
  
  // Compliance APIs
  async verifyAge(data: any) {
    return this.request<any>('/api/v1/compliance/verify-age', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }
  
  async getComplianceStatus(customerId: string) {
    return this.request<any>(`/api/v1/compliance/${customerId}`);
  }
  
  // Model Deployment APIs
  async getModelDeployments() {
    return this.request<any>('/api/v1/models/deployments');
  }
  
  async switchModel(modelId: string) {
    return this.request<any>('/api/v1/models/switch', {
      method: 'POST',
      body: JSON.stringify({ model_id: modelId }),
    });
  }
  
  // Training Feedback APIs
  async submitFeedback(feedback: any) {
    return this.request<any>('/api/v1/training/feedback', {
      method: 'POST',
      body: JSON.stringify(feedback),
    });
  }
  
  async submitCorrection(correction: any) {
    return this.request<any>('/api/v1/training/correction', {
      method: 'POST',
      body: JSON.stringify(correction),
    });
  }
  
  async getReviewQueue() {
    return this.request<any>('/api/v1/training/review-queue');
  }
  
  // AI Explanation APIs
  async explainDecision(input: string) {
    return this.request<any>('/api/v1/ai/explain', {
      method: 'POST',
      body: JSON.stringify({ input }),
    });
  }
  
  // Export/Import APIs
  async exportAIData() {
    return this.request<any>('/api/v1/ai/export');
  }
  
  async importAIData(data: any) {
    return this.request<any>('/api/v1/ai/import', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }
  
  // Cart APIs
  async addToCart(customerId: string, product: any) {
    return this.request<any>('/api/v1/cart', {
      method: 'POST',
      body: JSON.stringify({ customer_id: customerId, product }),
    });
  }
  
  async getCart(customerId: string) {
    return this.request<any>(`/api/v1/cart/${customerId}`);
  }
  
  // Analytics Cache APIs
  async getAnalyticsCache() {
    return this.request<any>('/api/v1/analytics/cache');
  }
  
  // AI Soul/Decision Monitoring APIs
  async getDecisionStream() {
    return this.request<any>('/api/v1/ai/decision-stream');
  }
  
  async getContextFactors(sessionId?: string) {
    const params = sessionId ? `?session_id=${sessionId}` : '';
    return this.request<any>(`/api/v1/ai/context-factors${params}`);
  }
  
  async getDecisionPaths(input: string) {
    const params = new URLSearchParams({ input_text: input });
    return this.request<any>(`/api/v1/ai/decision-paths?${params}`);
  }
  
  // Knowledge Base APIs
  async getStrainDatabase(limit: number = 100) {
    return this.request<any>(`/api/v1/knowledge/strains?limit=${limit}`);
  }
  
  async addStrain(strain: any) {
    return this.request<any>('/api/v1/knowledge/strains', {
      method: 'POST',
      body: JSON.stringify(strain),
    });
  }
  
  async updateStrain(strainId: string, strain: any) {
    return this.request<any>(`/api/v1/knowledge/strains/${strainId}`, {
      method: 'PUT',
      body: JSON.stringify(strain),
    });
  }
  
  async deleteStrain(strainId: string) {
    return this.request<any>(`/api/v1/knowledge/strains/${strainId}`, {
      method: 'DELETE',
    });
  }
  
  async getTerpeneProfiles() {
    return this.request<any>('/api/v1/knowledge/terpenes');
  }
  
  async addTerpene(terpene: any) {
    return this.request<any>('/api/v1/knowledge/terpenes', {
      method: 'POST',
      body: JSON.stringify(terpene),
    });
  }
  
  async updateTerpene(terpeneId: string, terpene: any) {
    return this.request<any>(`/api/v1/knowledge/terpenes/${terpeneId}`, {
      method: 'PUT',
      body: JSON.stringify(terpene),
    });
  }
  
  async deleteTerpene(terpeneId: string) {
    return this.request<any>(`/api/v1/knowledge/terpenes/${terpeneId}`, {
      method: 'DELETE',
    });
  }
  
  // Effects APIs
  async getEffects(limit: number = 100, category?: string) {
    const params = new URLSearchParams({ limit: limit.toString() });
    if (category) params.append('category', category);
    return this.request<any>(`/api/v1/knowledge/effects?${params}`);
  }
  
  async addEffect(effect: any) {
    return this.request<any>('/api/v1/knowledge/effects', {
      method: 'POST',
      body: JSON.stringify(effect),
    });
  }
  
  async updateEffect(effectId: string, effect: any) {
    return this.request<any>(`/api/v1/knowledge/effects/${effectId}`, {
      method: 'PUT',
      body: JSON.stringify(effect),
    });
  }
  
  async deleteEffect(effectId: string) {
    return this.request<any>(`/api/v1/knowledge/effects/${effectId}`, {
      method: 'DELETE',
    });
  }
  
  // Educational Content APIs
  async getEducationalContent(limit: number = 50, category?: string, difficulty?: string) {
    const params = new URLSearchParams({ limit: limit.toString() });
    if (category) params.append('category', category);
    if (difficulty) params.append('difficulty', difficulty);
    return this.request<any>(`/api/v1/knowledge/education?${params}`);
  }
  
  async addEducationalContent(content: any) {
    return this.request<any>('/api/v1/knowledge/education', {
      method: 'POST',
      body: JSON.stringify(content),
    });
  }
  
  async updateEducationalContent(contentId: string, content: any) {
    return this.request<any>(`/api/v1/knowledge/education/${contentId}`, {
      method: 'PUT',
      body: JSON.stringify(content),
    });
  }
  
  async deleteEducationalContent(contentId: string) {
    return this.request<any>(`/api/v1/knowledge/education/${contentId}`, {
      method: 'DELETE',
    });
  }
  
  // Service Health APIs
  async getAllServicesHealth() {
    return this.request<any>('/api/v1/services/health');
  }
}

// Create singleton instance
const apiService = new ApiService();

export default apiService;

// Export specific API functions for convenience
export const {
  getDashboardStats,
  getSystemHealth,
  getTrainingDatasets,
  uploadDataset,
  getIntents,
  createIntent,
  updateIntent,
  deleteIntent,
  sendChatMessage,
  getChatHistory,
  getConversationHistory,
  getConversationFlows,
  saveConversationFlow,
  deleteConversationFlow,
  getServices,
  getServiceLogs,
  restartService,
  scaleService,
  getActiveModel,
  getAvailableModels,
  deployModel,
  updateModelConfig,
  importModel,
  fineTuneModel,
  getPersonalities,
  savePersonality,
  deletePersonality,
  activatePersonality,
  getAnalytics,
  getMetrics,
  getDecisionTree,
  getDecisionTreeAnalytics,
  searchProducts,
} = apiService;