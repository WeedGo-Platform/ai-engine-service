/**
 * Token Refresh Scheduler
 *
 * Manages automatic token refresh before expiration
 * Monitors token expiry and triggers refresh at optimal times
 */

import { AppState, AppStateStatus } from 'react-native';
import { shouldRefreshToken, getTimeUntilExpiry, formatDuration } from '@/utils/jwtUtils';

type RefreshCallback = () => Promise<void>;

interface SchedulerConfig {
  // Minutes before expiry to refresh (default: 5)
  refreshThresholdMinutes: number;
  // Check interval in milliseconds (default: 1 minute)
  checkIntervalMs: number;
  // Whether to refresh on app foreground (default: true)
  refreshOnForeground: boolean;
}

class TokenRefreshScheduler {
  private refreshCallback: RefreshCallback | null = null;
  private currentToken: string | null = null;
  private intervalId: NodeJS.Timeout | null = null;
  private appStateSubscription: any = null;
  private isRefreshing: boolean = false;

  private config: SchedulerConfig = {
    refreshThresholdMinutes: 5,
    checkIntervalMs: 60 * 1000, // 1 minute
    refreshOnForeground: true,
  };

  /**
   * Initialize the scheduler with a refresh callback
   *
   * @param token - Current access token
   * @param refreshCallback - Async function to call when refresh is needed
   * @param config - Optional configuration
   */
  public start(
    token: string,
    refreshCallback: RefreshCallback,
    config?: Partial<SchedulerConfig>
  ): void {
    // Stop any existing scheduler
    this.stop();

    // Update configuration
    if (config) {
      this.config = { ...this.config, ...config };
    }

    this.currentToken = token;
    this.refreshCallback = refreshCallback;

    // Start periodic checking
    this.startPeriodicCheck();

    // Subscribe to app state changes
    if (this.config.refreshOnForeground) {
      this.subscribeToAppState();
    }

    console.log('🔄 Token refresh scheduler started', {
      threshold: `${this.config.refreshThresholdMinutes} minutes`,
      checkInterval: `${this.config.checkIntervalMs / 1000} seconds`,
    });

    // Do initial check immediately
    this.checkAndRefresh();
  }

  /**
   * Stop the scheduler
   */
  public stop(): void {
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }

    if (this.appStateSubscription) {
      this.appStateSubscription.remove();
      this.appStateSubscription = null;
    }

    this.currentToken = null;
    this.refreshCallback = null;
    this.isRefreshing = false;

    console.log('🛑 Token refresh scheduler stopped');
  }

  /**
   * Update the current token being monitored
   */
  public updateToken(token: string): void {
    this.currentToken = token;
    console.log('🔄 Token refresh scheduler updated with new token');

    // Check immediately with new token
    this.checkAndRefresh();
  }

  /**
   * Force a refresh check immediately
   */
  public async forceCheck(): Promise<void> {
    await this.checkAndRefresh();
  }

  /**
   * Start periodic token checking
   */
  private startPeriodicCheck(): void {
    this.intervalId = setInterval(() => {
      this.checkAndRefresh();
    }, this.config.checkIntervalMs);
  }

  /**
   * Subscribe to app state changes
   */
  private subscribeToAppState(): void {
    this.appStateSubscription = AppState.addEventListener(
      'change',
      (nextAppState: AppStateStatus) => {
        if (nextAppState === 'active') {
          console.log('📱 App foregrounded - checking token status');
          this.checkAndRefresh();
        }
      }
    );
  }

  /**
   * Check if token needs refresh and trigger if necessary
   */
  private async checkAndRefresh(): Promise<void> {
    // Guard against concurrent refreshes
    if (this.isRefreshing) {
      console.log('⏳ Token refresh already in progress, skipping check');
      return;
    }

    if (!this.currentToken || !this.refreshCallback) {
      return;
    }

    try {
      // Check if token should be refreshed
      const shouldRefresh = shouldRefreshToken(
        this.currentToken,
        this.config.refreshThresholdMinutes
      );

      if (shouldRefresh) {
        const timeRemaining = getTimeUntilExpiry(this.currentToken);
        const formattedTime = timeRemaining ? formatDuration(timeRemaining) : 'expired';

        console.log(`🔄 Token expiring soon (${formattedTime}), triggering refresh`);

        this.isRefreshing = true;

        try {
          await this.refreshCallback();
          console.log('✅ Token refreshed successfully');
        } catch (error: any) {
          console.error('❌ Token refresh failed:', error);

          // If refresh fails with 401/403, stop the scheduler
          // (auth store will handle logout)
          if (error?.response?.status === 401 || error?.response?.status === 403) {
            console.log('🛑 Invalid refresh token, stopping scheduler');
            this.stop();
          }
        } finally {
          this.isRefreshing = false;
        }
      } else {
        // Log time remaining for debugging
        const timeRemaining = getTimeUntilExpiry(this.currentToken);
        if (timeRemaining !== null) {
          const formattedTime = formatDuration(timeRemaining);
          console.log(`✅ Token valid for ${formattedTime}`);
        }
      }
    } catch (error) {
      console.error('Error in token refresh check:', error);
      this.isRefreshing = false;
    }
  }

  /**
   * Check if scheduler is currently running
   */
  public isRunning(): boolean {
    return this.intervalId !== null;
  }

  /**
   * Get current configuration
   */
  public getConfig(): SchedulerConfig {
    return { ...this.config };
  }

  /**
   * Update configuration (requires restart to take effect)
   */
  public updateConfig(config: Partial<SchedulerConfig>): void {
    this.config = { ...this.config, ...config };

    // If scheduler is running, restart with new config
    if (this.isRunning() && this.currentToken && this.refreshCallback) {
      const token = this.currentToken;
      const callback = this.refreshCallback;
      this.start(token, callback, this.config);
    }
  }
}

// Export singleton instance
export const tokenRefreshScheduler = new TokenRefreshScheduler();
