/**
 * Session Timeout Warning Modal
 *
 * Displays a warning modal when user's session is about to expire
 * Provides options to extend session or logout
 */

import React, { useState, useEffect } from 'react';
import {
  Modal,
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { formatDuration } from '@/utils/jwtUtils';

export interface SessionTimeoutWarningProps {
  visible: boolean;
  timeRemainingMs: number;
  onExtend: () => Promise<void>;
  onLogout: () => void;
  onDismiss?: () => void;
}

export function SessionTimeoutWarning({
  visible,
  timeRemainingMs,
  onExtend,
  onLogout,
  onDismiss,
}: SessionTimeoutWarningProps) {
  const [extending, setExtending] = useState(false);
  const [countdown, setCountdown] = useState(timeRemainingMs);

  // Update countdown every second
  useEffect(() => {
    if (!visible) return;

    setCountdown(timeRemainingMs);

    const interval = setInterval(() => {
      setCountdown((prev) => {
        const next = prev - 1000;
        if (next <= 0) {
          clearInterval(interval);
          // Auto-logout when time runs out
          onLogout();
          return 0;
        }
        return next;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [visible, timeRemainingMs]);

  const handleExtend = async () => {
    setExtending(true);
    try {
      await onExtend();
      // Modal will be dismissed by parent component
    } catch (error) {
      console.error('Failed to extend session:', error);
    } finally {
      setExtending(false);
    }
  };

  if (!visible) return null;

  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      onRequestClose={onDismiss}
    >
      <View style={styles.overlay}>
        <View style={styles.modal}>
          {/* Icon */}
          <View style={styles.iconContainer}>
            <View style={styles.iconCircle}>
              <Ionicons name="time-outline" size={48} color="#FF9800" />
            </View>
          </View>

          {/* Title */}
          <Text style={styles.title}>Session Expiring Soon</Text>

          {/* Message */}
          <Text style={styles.message}>
            Your session will expire in{' '}
            <Text style={styles.countdown}>{formatDuration(countdown)}</Text>
          </Text>

          <Text style={styles.subMessage}>
            Would you like to extend your session?
          </Text>

          {/* Buttons */}
          <View style={styles.buttons}>
            <TouchableOpacity
              style={[styles.button, styles.logoutButton]}
              onPress={onLogout}
              disabled={extending}
            >
              <Text style={styles.logoutButtonText}>Logout</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.button, styles.extendButton]}
              onPress={handleExtend}
              disabled={extending}
            >
              {extending ? (
                <ActivityIndicator size="small" color="#FFF" />
              ) : (
                <Text style={styles.extendButtonText}>Extend Session</Text>
              )}
            </TouchableOpacity>
          </View>

          {/* Dismiss link */}
          {onDismiss && (
            <TouchableOpacity style={styles.dismissButton} onPress={onDismiss}>
              <Text style={styles.dismissText}>Remind me later</Text>
            </TouchableOpacity>
          )}
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  modal: {
    backgroundColor: '#FFF',
    borderRadius: 20,
    padding: 24,
    width: '100%',
    maxWidth: 400,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  iconContainer: {
    marginBottom: 20,
  },
  iconCircle: {
    width: 96,
    height: 96,
    borderRadius: 48,
    backgroundColor: '#FFF3E0',
    justifyContent: 'center',
    alignItems: 'center',
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    color: '#333',
    marginBottom: 12,
    textAlign: 'center',
  },
  message: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginBottom: 8,
    lineHeight: 24,
  },
  countdown: {
    fontWeight: '700',
    color: '#FF9800',
    fontSize: 18,
  },
  subMessage: {
    fontSize: 14,
    color: '#999',
    textAlign: 'center',
    marginBottom: 24,
  },
  buttons: {
    flexDirection: 'row',
    gap: 12,
    width: '100%',
  },
  button: {
    flex: 1,
    paddingVertical: 14,
    paddingHorizontal: 20,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 48,
  },
  logoutButton: {
    backgroundColor: '#F5F5F5',
    borderWidth: 1,
    borderColor: '#E0E0E0',
  },
  logoutButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#666',
  },
  extendButton: {
    backgroundColor: '#27AE60',
  },
  extendButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFF',
  },
  dismissButton: {
    marginTop: 16,
    paddingVertical: 8,
  },
  dismissText: {
    fontSize: 14,
    color: '#999',
    textDecorationLine: 'underline',
  },
});
