/**
 * WebSocket Types and Interfaces
 * Separated to avoid circular dependencies and export issues
 */

export interface WebSocketMessage {
  type: string;
  payload: any;
  timestamp: string;
}

export interface DeploymentProgress {
  deploymentId: string;
  modelId: string;
  status: 'starting' | 'downloading' | 'loading' | 'initializing' | 'testing' | 'completed' | 'failed';
  progress: number;
  message: string;
  details?: {
    downloadProgress?: number;
    memoryUsage?: number;
    initTime?: number;
    errorMessage?: string;
  };
}

export interface ResourceMetrics {
  cpu: number;
  memory: number;
  gpu?: number;
  disk: number;
  network: {
    in: number;
    out: number;
  };
}