/**
 * Offline Mode Indicator
 *
 * Displays a banner when app is offline
 * Shows connection status and cached data information
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Animated,
  TouchableOpacity,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { networkMonitor, NetworkStatus, ConnectionType } from '@/services/networkMonitor';

export interface OfflineModeIndicatorProps {
  style?: any;
  showWhenOnline?: boolean; // Show indicator even when online (default: false)
  onRetry?: () => void;
}

export function OfflineModeIndicator({
  style,
  showWhenOnline = false,
  onRetry,
}: OfflineModeIndicatorProps) {
  const [networkStatus, setNetworkStatus] = useState<NetworkStatus | null>(null);
  const [slideAnim] = useState(new Animated.Value(-100)); // Start off-screen
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    // Subscribe to network changes
    const unsubscribe = networkMonitor.subscribe('offline-indicator', (status) => {
      setNetworkStatus(status);

      const shouldShow =
        !status.isConnected ||
        status.isInternetReachable === false ||
        (showWhenOnline && status.isConnected);

      if (shouldShow && !isVisible) {
        // Slide down
        setIsVisible(true);
        Animated.spring(slideAnim, {
          toValue: 0,
          useNativeDriver: true,
          tension: 50,
          friction: 7,
        }).start();
      } else if (!shouldShow && isVisible) {
        // Slide up
        Animated.spring(slideAnim, {
          toValue: -100,
          useNativeDriver: true,
          tension: 50,
          friction: 7,
        }).start(() => {
          setIsVisible(false);
        });
      }
    });

    return () => {
      unsubscribe();
    };
  }, [isVisible, showWhenOnline]);

  if (!networkStatus || (!isVisible && !showWhenOnline)) {
    return null;
  }

  const getConnectionIcon = (): string => {
    if (!networkStatus.isConnected) {
      return 'cloud-offline-outline';
    }
    if (networkStatus.isInternetReachable === false) {
      return 'cloud-offline-outline';
    }
    return 'cloud-done-outline';
  };

  const getConnectionText = (): string => {
    if (!networkStatus.isConnected) {
      return 'No Internet Connection';
    }
    if (networkStatus.isInternetReachable === false) {
      return 'Internet Unreachable';
    }
    if (networkStatus.type === ConnectionType.CELLULAR) {
      return 'Connected via Cellular';
    }
    if (networkStatus.type === ConnectionType.WIFI) {
      return 'Connected via WiFi';
    }
    return 'Connected';
  };

  const getConnectionSubtext = (): string | null => {
    if (!networkStatus.isConnected) {
      return 'Using cached data';
    }
    if (networkStatus.isInternetReachable === false) {
      return 'Check your connection';
    }
    if (networkStatus.details.isConnectionExpensive) {
      return 'Cellular data in use';
    }
    return null;
  };

  const getBgColor = (): string => {
    if (!networkStatus.isConnected || networkStatus.isInternetReachable === false) {
      return '#FF6B6B'; // Red for offline
    }
    if (networkStatus.details.isConnectionExpensive) {
      return '#FF9800'; // Orange for cellular
    }
    return '#27AE60'; // Green for online
  };

  const handleRetry = async () => {
    if (onRetry) {
      onRetry();
    } else {
      // Default: refresh network status
      await networkMonitor.refresh();
    }
  };

  return (
    <Animated.View
      style={[
        styles.container,
        { backgroundColor: getBgColor() },
        { transform: [{ translateY: slideAnim }] },
        style,
      ]}
    >
      <View style={styles.content}>
        <Ionicons
          name={getConnectionIcon()}
          size={20}
          color="#FFF"
          style={styles.icon}
        />

        <View style={styles.textContainer}>
          <Text style={styles.mainText}>{getConnectionText()}</Text>
          {getConnectionSubtext() && (
            <Text style={styles.subText}>{getConnectionSubtext()}</Text>
          )}
        </View>

        {(!networkStatus.isConnected || networkStatus.isInternetReachable === false) && (
          <TouchableOpacity
            style={styles.retryButton}
            onPress={handleRetry}
            hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
          >
            <Ionicons name="refresh-outline" size={20} color="#FFF" />
          </TouchableOpacity>
        )}
      </View>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    zIndex: 1000,
    elevation: 1000,
  },
  content: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    paddingTop: 48, // Account for status bar
  },
  icon: {
    marginRight: 12,
  },
  textContainer: {
    flex: 1,
  },
  mainText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#FFF',
    marginBottom: 2,
  },
  subText: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.9)',
  },
  retryButton: {
    padding: 8,
    marginLeft: 8,
  },
});
