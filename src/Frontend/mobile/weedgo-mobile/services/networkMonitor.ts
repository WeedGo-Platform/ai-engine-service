/**
 * Network Connectivity Monitor
 *
 * Monitors network connectivity status and provides real-time updates
 * Uses @react-native-community/netinfo for native network detection
 */

import NetInfo, { NetInfoState, NetInfoStateType } from '@react-native-community/netinfo';

export enum ConnectionType {
  NONE = 'none',
  WIFI = 'wifi',
  CELLULAR = 'cellular',
  ETHERNET = 'ethernet',
  BLUETOOTH = 'bluetooth',
  UNKNOWN = 'unknown',
}

export interface NetworkStatus {
  isConnected: boolean;
  isInternetReachable: boolean | null;
  type: ConnectionType;
  details: {
    isConnectionExpensive: boolean | null;
    cellularGeneration: string | null;
    carrier: string | null;
    ipAddress: string | null;
    subnet: string | null;
  };
}

type NetworkChangeCallback = (status: NetworkStatus) => void;

class NetworkMonitor {
  private listeners: Map<string, NetworkChangeCallback> = new Map();
  private currentStatus: NetworkStatus | null = null;
  private unsubscribe: (() => void) | null = null;

  constructor() {
    this.initialize();
  }

  /**
   * Initialize network monitoring
   */
  private async initialize() {
    // Get initial network state
    const state = await NetInfo.fetch();
    this.currentStatus = this.parseNetInfoState(state);

    // Subscribe to network state changes
    this.unsubscribe = NetInfo.addEventListener((state) => {
      const newStatus = this.parseNetInfoState(state);
      const statusChanged = this.hasStatusChanged(this.currentStatus, newStatus);

      if (statusChanged) {
        console.log('📡 Network status changed:', {
          from: this.currentStatus?.isConnected ? 'connected' : 'disconnected',
          to: newStatus.isConnected ? 'connected' : 'disconnected',
          type: newStatus.type,
        });

        this.currentStatus = newStatus;
        this.notifyListeners(newStatus);
      }
    });
  }

  /**
   * Parse NetInfo state into our NetworkStatus format
   */
  private parseNetInfoState(state: NetInfoState): NetworkStatus {
    const type = this.mapConnectionType(state.type);
    const isConnected = state.isConnected ?? false;
    const isInternetReachable = state.isInternetReachable;

    return {
      isConnected,
      isInternetReachable,
      type,
      details: {
        isConnectionExpensive: state.details?.isConnectionExpensive ?? null,
        cellularGeneration: state.details && 'cellularGeneration' in state.details
          ? state.details.cellularGeneration
          : null,
        carrier: state.details && 'carrier' in state.details
          ? state.details.carrier
          : null,
        ipAddress: state.details?.ipAddress ?? null,
        subnet: state.details?.subnet ?? null,
      },
    };
  }

  /**
   * Map NetInfo connection type to our ConnectionType enum
   */
  private mapConnectionType(type: NetInfoStateType): ConnectionType {
    switch (type) {
      case NetInfoStateType.wifi:
        return ConnectionType.WIFI;
      case NetInfoStateType.cellular:
        return ConnectionType.CELLULAR;
      case NetInfoStateType.ethernet:
        return ConnectionType.ETHERNET;
      case NetInfoStateType.bluetooth:
        return ConnectionType.BLUETOOTH;
      case NetInfoStateType.none:
        return ConnectionType.NONE;
      default:
        return ConnectionType.UNKNOWN;
    }
  }

  /**
   * Check if network status has meaningfully changed
   */
  private hasStatusChanged(oldStatus: NetworkStatus | null, newStatus: NetworkStatus): boolean {
    if (!oldStatus) return true;

    return (
      oldStatus.isConnected !== newStatus.isConnected ||
      oldStatus.type !== newStatus.type ||
      oldStatus.isInternetReachable !== newStatus.isInternetReachable
    );
  }

  /**
   * Notify all registered listeners of network status change
   */
  private notifyListeners(status: NetworkStatus) {
    this.listeners.forEach((callback, id) => {
      try {
        callback(status);
      } catch (error) {
        console.error(`Error in network listener ${id}:`, error);
      }
    });
  }

  /**
   * Subscribe to network status changes
   *
   * @param id - Unique identifier for this listener
   * @param callback - Function to call when network status changes
   * @returns Unsubscribe function
   */
  public subscribe(id: string, callback: NetworkChangeCallback): () => void {
    this.listeners.set(id, callback);

    // Immediately call with current status if available
    if (this.currentStatus) {
      callback(this.currentStatus);
    }

    // Return unsubscribe function
    return () => {
      this.listeners.delete(id);
    };
  }

  /**
   * Get current network status
   */
  public async getStatus(): Promise<NetworkStatus> {
    if (this.currentStatus) {
      return this.currentStatus;
    }

    // Fetch current state if not yet initialized
    const state = await NetInfo.fetch();
    return this.parseNetInfoState(state);
  }

  /**
   * Check if currently connected to internet
   */
  public async isConnected(): Promise<boolean> {
    const status = await this.getStatus();
    return status.isConnected && (status.isInternetReachable !== false);
  }

  /**
   * Check if connection is expensive (cellular data)
   * Useful for deciding whether to download large files
   */
  public async isConnectionExpensive(): Promise<boolean> {
    const status = await this.getStatus();
    return status.details.isConnectionExpensive === true;
  }

  /**
   * Get connection type
   */
  public async getConnectionType(): Promise<ConnectionType> {
    const status = await this.getStatus();
    return status.type;
  }

  /**
   * Wait for internet connection (with timeout)
   *
   * @param timeoutMs - Maximum time to wait in milliseconds
   * @returns Promise that resolves when connected or rejects on timeout
   */
  public async waitForConnection(timeoutMs: number = 10000): Promise<void> {
    return new Promise((resolve, reject) => {
      let timeoutId: NodeJS.Timeout;
      let unsubscribe: (() => void) | null = null;

      const cleanup = () => {
        if (timeoutId) clearTimeout(timeoutId);
        if (unsubscribe) unsubscribe();
      };

      // Check current status first
      this.isConnected().then((connected) => {
        if (connected) {
          cleanup();
          resolve();
          return;
        }

        // Wait for connection
        unsubscribe = this.subscribe('waitForConnection', (status) => {
          if (status.isConnected && status.isInternetReachable !== false) {
            cleanup();
            resolve();
          }
        });

        // Set timeout
        timeoutId = setTimeout(() => {
          cleanup();
          reject(new Error('Connection timeout'));
        }, timeoutMs);
      });
    });
  }

  /**
   * Refresh network status
   * Forces a re-check of the network state
   */
  public async refresh(): Promise<NetworkStatus> {
    const state = await NetInfo.fetch();
    const status = this.parseNetInfoState(state);
    this.currentStatus = status;
    return status;
  }

  /**
   * Cleanup and stop monitoring
   */
  public destroy() {
    if (this.unsubscribe) {
      this.unsubscribe();
      this.unsubscribe = null;
    }
    this.listeners.clear();
    this.currentStatus = null;
  }
}

// Export singleton instance
export const networkMonitor = new NetworkMonitor();
