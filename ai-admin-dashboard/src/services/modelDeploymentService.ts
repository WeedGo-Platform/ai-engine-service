/**
 * Model Deployment Service
 * Handles all model deployment operations with real-time progress tracking
 * Implements retry logic, error handling, and fallback mechanisms
 */

import apiService from './api';
import { wsService } from './websocket';
import type { DeploymentProgress } from './websocket.types';

export interface ModelDeploymentConfig {
  modelId: string;
  version?: string;
  environment?: 'development' | 'staging' | 'production';
  configuration?: {
    temperature?: number;
    max_tokens?: number;
    top_p?: number;
    repetition_penalty?: number;
  };
  resources?: {
    cpu?: number;
    memory?: number;
    gpu?: boolean;
  };
}

export interface DeploymentStatus {
  deploymentId: string;
  modelId: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'rolled_back';
  progress: number;
  currentStep: string;
  steps: DeploymentStep[];
  startTime: string;
  endTime?: string;
  error?: string;
  logs: DeploymentLog[];
}

export interface DeploymentStep {
  name: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'skipped';
  progress: number;
  startTime?: string;
  endTime?: string;
  message?: string;
}

export interface DeploymentLog {
  timestamp: string;
  level: 'info' | 'warning' | 'error';
  message: string;
  details?: any;
}

export interface ModelHealth {
  modelId: string;
  status: 'healthy' | 'degraded' | 'unhealthy';
  latency: number;
  throughput: number;
  errorRate: number;
  lastChecked: string;
  checks: {
    memory: boolean;
    cpu: boolean;
    gpu?: boolean;
    inference: boolean;
    api: boolean;
  };
}

class ModelDeploymentService {
  private static instance: ModelDeploymentService;
  private deploymentStatusCache: Map<string, DeploymentStatus> = new Map();
  private pollingIntervals: Map<string, number> = new Map();
  private wsConnected = false;
  private retryAttempts: Map<string, number> = new Map();
  private maxRetries = 3;
  private pollingInterval = 2000; // 2 seconds

  private constructor() {
    // Don't initialize WebSocket immediately to avoid import issues
    // Will be initialized on first use
  }

  public static getInstance(): ModelDeploymentService {
    if (!ModelDeploymentService.instance) {
      ModelDeploymentService.instance = new ModelDeploymentService();
      // Initialize WebSocket after instance creation
      setTimeout(() => {
        ModelDeploymentService.instance.initializeWebSocket();
      }, 0);
    }
    return ModelDeploymentService.instance;
  }

  /**
   * Initialize WebSocket connection for real-time updates
   */
  private async initializeWebSocket(): Promise<void> {
    try {
      await wsService.connect();
      this.wsConnected = true;

      // Subscribe to deployment progress updates
      wsService.onDeploymentProgress((progress: DeploymentProgress) => {
        this.handleDeploymentProgress(progress);
      });

      // Handle connection state changes
      wsService.on('disconnected', () => {
        this.wsConnected = false;
        console.log('[ModelDeployment] WebSocket disconnected, falling back to polling');
        
        // Switch active deployments to polling
        this.deploymentStatusCache.forEach((status, deploymentId) => {
          if (status.status === 'in_progress') {
            this.startPolling(deploymentId);
          }
        });
      });

      wsService.on('connected', () => {
        this.wsConnected = true;
        console.log('[ModelDeployment] WebSocket reconnected, switching from polling');
        
        // Stop polling for active deployments
        this.pollingIntervals.forEach((interval) => {
          clearInterval(interval);
        });
        this.pollingIntervals.clear();
      });
    } catch (error) {
      console.error('[ModelDeployment] Failed to initialize WebSocket:', error);
      this.wsConnected = false;
    }
  }

  /**
   * Deploy a model with progress tracking
   */
  public async deployModel(config: ModelDeploymentConfig): Promise<DeploymentStatus> {
    try {
      // Initialize deployment status
      const deploymentId = this.generateDeploymentId();
      const initialStatus: DeploymentStatus = {
        deploymentId,
        modelId: config.modelId,
        status: 'pending',
        progress: 0,
        currentStep: 'Initializing deployment',
        steps: this.createDeploymentSteps(),
        startTime: new Date().toISOString(),
        logs: [{
          timestamp: new Date().toISOString(),
          level: 'info',
          message: 'Deployment initiated',
          details: config
        }]
      };

      this.deploymentStatusCache.set(deploymentId, initialStatus);

      // Start the deployment
      const response = await apiService.deployModel(config.modelId, {
        deployment_id: deploymentId,
        version_id: config.version || 'v1.0', // API expects version_id, not version
        environment: config.environment,
        configuration: config.configuration,
        resources: config.resources
      });

      // Update status
      initialStatus.status = 'in_progress';
      this.updateDeploymentStep(deploymentId, 0, 'in_progress');

      // Subscribe to updates
      if (this.wsConnected) {
        wsService.requestDeploymentStatus(deploymentId);
      } else {
        this.startPolling(deploymentId);
      }

      return initialStatus;
    } catch (error) {
      console.error('[ModelDeployment] Deployment failed:', error);
      throw error;
    }
  }

  /**
   * Get deployment status
   */
  public async getDeploymentStatus(deploymentId: string): Promise<DeploymentStatus | null> {
    // Check cache first
    if (this.deploymentStatusCache.has(deploymentId)) {
      return this.deploymentStatusCache.get(deploymentId)!;
    }

    // Fetch from API
    try {
      const response = await apiService.getDeploymentStatus(deploymentId);
      const status = this.mapApiResponseToStatus(response);
      this.deploymentStatusCache.set(deploymentId, status);
      return status;
    } catch (error) {
      console.error('[ModelDeployment] Failed to get deployment status:', error);
      return null;
    }
  }

  /**
   * Rollback a deployment
   */
  public async rollbackDeployment(deploymentId: string): Promise<boolean> {
    try {
      const currentStatus = await this.getDeploymentStatus(deploymentId);
      if (!currentStatus) {
        throw new Error('Deployment not found');
      }

      // Call rollback API
      await apiService.rollbackDeployment(deploymentId);

      // Update status
      currentStatus.status = 'rolled_back';
      currentStatus.endTime = new Date().toISOString();
      currentStatus.logs.push({
        timestamp: new Date().toISOString(),
        level: 'warning',
        message: 'Deployment rolled back',
      });

      this.deploymentStatusCache.set(deploymentId, currentStatus);
      
      // Stop monitoring
      this.stopPolling(deploymentId);

      return true;
    } catch (error) {
      console.error('[ModelDeployment] Rollback failed:', error);
      throw error;
    }
  }

  /**
   * Test a model before deployment
   */
  public async testModel(modelId: string, testCases?: any[]): Promise<{
    passed: boolean;
    results: any[];
    metrics: {
      latency: number;
      accuracy: number;
      errorRate: number;
    };
  }> {
    try {
      const response = await apiService.testModel(modelId, testCases);
      return response;
    } catch (error) {
      console.error('[ModelDeployment] Model testing failed:', error);
      throw error;
    }
  }

  /**
   * Get model health status
   */
  public async getModelHealth(modelId: string): Promise<ModelHealth> {
    try {
      const response = await apiService.getModelHealth(modelId);
      return {
        modelId,
        status: response.status,
        latency: response.latency_ms,
        throughput: response.throughput_per_min,
        errorRate: response.error_rate,
        lastChecked: new Date().toISOString(),
        checks: {
          memory: response.checks?.memory ?? true,
          cpu: response.checks?.cpu ?? true,
          gpu: response.checks?.gpu,
          inference: response.checks?.inference ?? true,
          api: response.checks?.api ?? true,
        }
      };
    } catch (error) {
      console.error('[ModelDeployment] Failed to get model health:', error);
      throw error;
    }
  }

  /**
   * Delete a model with cleanup
   */
  public async deleteModel(modelId: string, cleanup = true): Promise<boolean> {
    try {
      await apiService.deleteModel(modelId, { cleanup });
      
      // Remove from any caches
      this.deploymentStatusCache.forEach((status, deploymentId) => {
        if (status.modelId === modelId) {
          this.deploymentStatusCache.delete(deploymentId);
          this.stopPolling(deploymentId);
        }
      });

      return true;
    } catch (error) {
      console.error('[ModelDeployment] Failed to delete model:', error);
      throw error;
    }
  }

  /**
   * Get deployment logs
   */
  public async getDeploymentLogs(
    deploymentId: string,
    filters?: {
      level?: 'info' | 'warning' | 'error';
      startTime?: string;
      endTime?: string;
      limit?: number;
    }
  ): Promise<DeploymentLog[]> {
    try {
      const response = await apiService.getDeploymentLogs(deploymentId, filters);
      return response.logs;
    } catch (error) {
      console.error('[ModelDeployment] Failed to get deployment logs:', error);
      
      // Return cached logs if available
      const cachedStatus = this.deploymentStatusCache.get(deploymentId);
      return cachedStatus?.logs || [];
    }
  }

  /**
   * Retry failed deployment
   */
  public async retryDeployment(deploymentId: string): Promise<DeploymentStatus> {
    const attempts = this.retryAttempts.get(deploymentId) || 0;
    
    if (attempts >= this.maxRetries) {
      throw new Error(`Maximum retry attempts (${this.maxRetries}) reached`);
    }

    const currentStatus = await this.getDeploymentStatus(deploymentId);
    if (!currentStatus || currentStatus.status !== 'failed') {
      throw new Error('Can only retry failed deployments');
    }

    this.retryAttempts.set(deploymentId, attempts + 1);

    // Reset status
    currentStatus.status = 'in_progress';
    currentStatus.progress = 0;
    currentStatus.logs.push({
      timestamp: new Date().toISOString(),
      level: 'info',
      message: `Retrying deployment (attempt ${attempts + 1}/${this.maxRetries})`,
    });

    // Restart deployment
    try {
      await apiService.retryDeployment(deploymentId);
      
      if (this.wsConnected) {
        wsService.requestDeploymentStatus(deploymentId);
      } else {
        this.startPolling(deploymentId);
      }

      return currentStatus;
    } catch (error) {
      currentStatus.status = 'failed';
      currentStatus.error = `Retry failed: ${error}`;
      throw error;
    }
  }

  /**
   * Handle deployment progress updates from WebSocket
   */
  private handleDeploymentProgress(progress: DeploymentProgress): void {
    const status = this.deploymentStatusCache.get(progress.deploymentId);
    if (!status) return;

    // Update status
    status.progress = progress.progress;
    status.currentStep = progress.message;

    // Update step status
    const stepIndex = this.getStepIndex(progress.status);
    if (stepIndex >= 0) {
      this.updateDeploymentStep(progress.deploymentId, stepIndex, 'completed');
      if (stepIndex < status.steps.length - 1) {
        this.updateDeploymentStep(progress.deploymentId, stepIndex + 1, 'in_progress');
      }
    }

    // Add log entry
    status.logs.push({
      timestamp: new Date().toISOString(),
      level: 'info',
      message: progress.message,
      details: progress.details
    });

    // Handle completion
    if (progress.status === 'completed') {
      status.status = 'completed';
      status.endTime = new Date().toISOString();
      status.progress = 100;
      this.stopPolling(progress.deploymentId);
      this.retryAttempts.delete(progress.deploymentId);
    } else if (progress.status === 'failed') {
      status.status = 'failed';
      status.endTime = new Date().toISOString();
      status.error = progress.details?.errorMessage;
      this.stopPolling(progress.deploymentId);
    }

    // Emit update event
    this.emitStatusUpdate(progress.deploymentId, status);
  }

  /**
   * Start polling for deployment status
   */
  private startPolling(deploymentId: string): void {
    // Don't start if already polling
    if (this.pollingIntervals.has(deploymentId)) return;

    const interval = setInterval(async () => {
      try {
        const response = await apiService.getDeploymentStatus(deploymentId);
        
        if (response.status === 'completed' || response.status === 'failed') {
          this.stopPolling(deploymentId);
        }

        const status = this.mapApiResponseToStatus(response);
        this.deploymentStatusCache.set(deploymentId, status);
        this.emitStatusUpdate(deploymentId, status);
      } catch (error) {
        console.error('[ModelDeployment] Polling error:', error);
      }
    }, this.pollingInterval);

    this.pollingIntervals.set(deploymentId, interval);
  }

  /**
   * Stop polling for deployment status
   */
  private stopPolling(deploymentId: string): void {
    const interval = this.pollingIntervals.get(deploymentId);
    if (interval) {
      clearInterval(interval);
      this.pollingIntervals.delete(deploymentId);
    }
  }

  /**
   * Create deployment steps
   */
  private createDeploymentSteps(): DeploymentStep[] {
    return [
      { name: 'Validating configuration', status: 'pending', progress: 0 },
      { name: 'Downloading model weights', status: 'pending', progress: 0 },
      { name: 'Loading model into memory', status: 'pending', progress: 0 },
      { name: 'Initializing inference engine', status: 'pending', progress: 0 },
      { name: 'Running health checks', status: 'pending', progress: 0 },
      { name: 'Updating routing configuration', status: 'pending', progress: 0 },
      { name: 'Finalizing deployment', status: 'pending', progress: 0 }
    ];
  }

  /**
   * Update deployment step status
   */
  private updateDeploymentStep(
    deploymentId: string,
    stepIndex: number,
    status: DeploymentStep['status']
  ): void {
    const deployment = this.deploymentStatusCache.get(deploymentId);
    if (!deployment || !deployment.steps[stepIndex]) return;

    const step = deployment.steps[stepIndex];
    step.status = status;
    
    if (status === 'in_progress') {
      step.startTime = new Date().toISOString();
    } else if (status === 'completed' || status === 'failed') {
      step.endTime = new Date().toISOString();
      step.progress = status === 'completed' ? 100 : step.progress;
    }

    // Update overall progress
    const completedSteps = deployment.steps.filter(s => s.status === 'completed').length;
    deployment.progress = Math.round((completedSteps / deployment.steps.length) * 100);
  }

  /**
   * Get step index from status
   */
  private getStepIndex(status: string): number {
    const stepMap: { [key: string]: number } = {
      'starting': 0,
      'downloading': 1,
      'loading': 2,
      'initializing': 3,
      'testing': 4,
      'routing': 5,
      'completed': 6
    };
    return stepMap[status] ?? -1;
  }

  /**
   * Map API response to DeploymentStatus
   */
  private mapApiResponseToStatus(response: any): DeploymentStatus {
    return {
      deploymentId: response.deployment_id,
      modelId: response.model_id,
      status: response.status,
      progress: response.progress || 0,
      currentStep: response.current_step || '',
      steps: response.steps || this.createDeploymentSteps(),
      startTime: response.start_time,
      endTime: response.end_time,
      error: response.error,
      logs: response.logs || []
    };
  }

  /**
   * Generate unique deployment ID
   */
  private generateDeploymentId(): string {
    return `deploy_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Emit status update event
   */
  private emitStatusUpdate(deploymentId: string, status: DeploymentStatus): void {
    // Emit custom event for UI components to listen to
    window.dispatchEvent(new CustomEvent('deploymentStatusUpdate', {
      detail: { deploymentId, status }
    }));
  }

  /**
   * Subscribe to deployment status updates
   */
  public onStatusUpdate(
    deploymentId: string,
    callback: (status: DeploymentStatus) => void
  ): () => void {
    const handler = (event: Event) => {
      const customEvent = event as CustomEvent;
      if (customEvent.detail.deploymentId === deploymentId) {
        callback(customEvent.detail.status);
      }
    };

    window.addEventListener('deploymentStatusUpdate', handler);

    // Return unsubscribe function
    return () => {
      window.removeEventListener('deploymentStatusUpdate', handler);
    };
  }
}

// Export singleton instance
export const modelDeploymentService = ModelDeploymentService.getInstance();

// Export everything needed by components
export { ModelDeploymentService };
// The interfaces are already exported at their declaration, no need to re-export