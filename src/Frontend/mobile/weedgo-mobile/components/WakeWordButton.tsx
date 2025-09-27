import React, { useEffect, useState } from 'react';
import {
  View,
  TouchableOpacity,
  Text,
  StyleSheet,
  Animated,
  Modal,
  Switch,
  Platform,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useWakeWordDetection } from '../hooks/useWakeWordDetection';

interface WakeWordButtonProps {
  onCommand?: (command: string) => void;
  style?: any;
}

export const WakeWordButton: React.FC<WakeWordButtonProps> = ({
  onCommand,
  style,
}) => {
  const {
    isListening,
    isConnected,
    lastDetection,
    state,
    error,
    startListening,
    stopListening,
    toggleListening,
    updateConfig,
    resetDetection,
    config,
  } = useWakeWordDetection();

  const [showSettings, setShowSettings] = useState(false);
  const [pulseAnim] = useState(new Animated.Value(1));
  const [glowAnim] = useState(new Animated.Value(0));

  // Pulse animation when listening
  useEffect(() => {
    if (isListening) {
      const pulse = Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, {
            toValue: 1.2,
            duration: 1000,
            useNativeDriver: true,
          }),
          Animated.timing(pulseAnim, {
            toValue: 1,
            duration: 1000,
            useNativeDriver: true,
          }),
        ])
      );
      pulse.start();

      return () => pulse.stop();
    } else {
      pulseAnim.setValue(1);
    }
  }, [isListening, pulseAnim]);

  // Glow animation when wake word detected
  useEffect(() => {
    if (state === 'wake_word_detected' || state === 'listening_command') {
      Animated.sequence([
        Animated.timing(glowAnim, {
          toValue: 1,
          duration: 300,
          useNativeDriver: true,
        }),
        Animated.timing(glowAnim, {
          toValue: 0,
          duration: 2000,
          useNativeDriver: true,
        }),
      ]).start();
    }
  }, [state, glowAnim]);

  // Handle wake word detection
  useEffect(() => {
    if (lastDetection?.detected) {
      console.log(`Wake word detected: ${lastDetection.wakeWord} (${lastDetection.confidence})`);
      // Reset after processing
      setTimeout(() => resetDetection(), 3000);
    }
  }, [lastDetection, resetDetection]);

  const getButtonColor = () => {
    if (error) return '#ff4444';
    if (!isConnected) return '#999999';
    if (state === 'listening_command') return '#00ff00';
    if (isListening) return '#4CAF50';
    return '#2196F3';
  };

  const getStatusText = () => {
    if (error) return 'Error';
    if (!isConnected) return 'Offline';
    if (state === 'listening_command') return 'Listening...';
    if (state === 'processing') return 'Processing...';
    if (isListening) return `Say "${config.models[0].replace('_', ' ')}"`;
    return 'Tap to Start';
  };

  const getIconName = () => {
    if (error) return 'alert-circle';
    if (!isConnected) return 'wifi-off';
    if (state === 'listening_command') return 'ear';
    if (isListening) return 'mic';
    return 'mic-off';
  };

  return (
    <>
      <View style={[styles.container, style]}>
        {/* Settings button */}
        <TouchableOpacity
          style={styles.settingsButton}
          onPress={() => setShowSettings(true)}
        >
          <Ionicons name="settings-outline" size={20} color="#666" />
        </TouchableOpacity>

        {/* Main wake word button */}
        <Animated.View
          style={[
            styles.buttonContainer,
            {
              transform: [{ scale: pulseAnim }],
            },
          ]}
        >
          {/* Glow effect */}
          {state === 'listening_command' && (
            <Animated.View
              style={[
                styles.glowEffect,
                {
                  opacity: glowAnim,
                  backgroundColor: getButtonColor(),
                },
              ]}
            />
          )}

          <TouchableOpacity
            style={[
              styles.button,
              {
                backgroundColor: getButtonColor(),
              },
            ]}
            onPress={toggleListening}
            disabled={!config.enabled}
          >
            <Ionicons
              name={getIconName()}
              size={32}
              color="white"
            />
          </TouchableOpacity>
        </Animated.View>

        {/* Status text */}
        <Text style={styles.statusText}>{getStatusText()}</Text>

        {/* Wake word indicator */}
        {lastDetection?.detected && (
          <View style={styles.detectionIndicator}>
            <Text style={styles.detectionText}>
              Detected: {lastDetection.wakeWord}
            </Text>
            <Text style={styles.confidenceText}>
              {(lastDetection.confidence * 100).toFixed(0)}% confident
            </Text>
          </View>
        )}

        {/* Error message */}
        {error && (
          <Text style={styles.errorText}>{error}</Text>
        )}
      </View>

      {/* Settings Modal */}
      <Modal
        visible={showSettings}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setShowSettings(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Wake Word Settings</Text>

            {/* Enable/Disable */}
            <View style={styles.settingRow}>
              <Text style={styles.settingLabel}>Enable Wake Word</Text>
              <Switch
                value={config.enabled}
                onValueChange={(value) => updateConfig({ enabled: value })}
              />
            </View>

            {/* Continuous Listening */}
            <View style={styles.settingRow}>
              <Text style={styles.settingLabel}>Always Listening</Text>
              <Switch
                value={config.continuousListening}
                onValueChange={(value) => updateConfig({ continuousListening: value })}
                disabled={!config.enabled}
              />
            </View>

            {/* Privacy Mode */}
            <View style={styles.settingRow}>
              <Text style={styles.settingLabel}>Privacy Mode</Text>
              <Switch
                value={config.privacyMode}
                onValueChange={(value) => updateConfig({ privacyMode: value })}
              />
            </View>

            {/* Sensitivity Slider */}
            <View style={styles.settingColumn}>
              <Text style={styles.settingLabel}>
                Sensitivity: {(config.sensitivity * 100).toFixed(0)}%
              </Text>
              <View style={styles.slider}>
                {/* Simplified - use actual Slider component */}
                <Text>Low</Text>
                <Text>High</Text>
              </View>
            </View>

            {/* Wake Words */}
            <View style={styles.settingColumn}>
              <Text style={styles.settingLabel}>Wake Words:</Text>
              {config.models.map((model, index) => (
                <Text key={index} style={styles.wakeWordItem}>
                  • {model.replace(/_/g, ' ')}
                </Text>
              ))}
            </View>

            {/* Connection Status */}
            <View style={styles.connectionStatus}>
              <Ionicons
                name={isConnected ? 'checkmark-circle' : 'close-circle'}
                size={20}
                color={isConnected ? '#4CAF50' : '#ff4444'}
              />
              <Text style={styles.connectionText}>
                {isConnected ? 'Connected' : 'Disconnected'}
              </Text>
            </View>

            {/* Close button */}
            <TouchableOpacity
              style={styles.closeButton}
              onPress={() => setShowSettings(false)}
            >
              <Text style={styles.closeButtonText}>Done</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </>
  );
};

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    padding: 20,
  },
  settingsButton: {
    position: 'absolute',
    top: 0,
    right: 0,
    padding: 10,
  },
  buttonContainer: {
    position: 'relative',
    alignItems: 'center',
    justifyContent: 'center',
  },
  button: {
    width: 80,
    height: 80,
    borderRadius: 40,
    alignItems: 'center',
    justifyContent: 'center',
    elevation: 5,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
  },
  glowEffect: {
    position: 'absolute',
    width: 100,
    height: 100,
    borderRadius: 50,
    opacity: 0.3,
  },
  statusText: {
    marginTop: 10,
    fontSize: 14,
    color: '#666',
  },
  detectionIndicator: {
    marginTop: 10,
    padding: 10,
    backgroundColor: '#e8f5e9',
    borderRadius: 8,
    alignItems: 'center',
  },
  detectionText: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#2e7d32',
  },
  confidenceText: {
    fontSize: 12,
    color: '#4caf50',
    marginTop: 2,
  },
  errorText: {
    marginTop: 5,
    fontSize: 12,
    color: '#ff4444',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalContent: {
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 20,
    width: '85%',
    maxWidth: 400,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 20,
    textAlign: 'center',
  },
  settingRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  settingColumn: {
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  settingLabel: {
    fontSize: 14,
    color: '#333',
  },
  slider: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 10,
  },
  wakeWordItem: {
    fontSize: 12,
    color: '#666',
    marginLeft: 10,
    marginTop: 5,
  },
  connectionStatus: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 15,
    padding: 10,
    backgroundColor: '#f5f5f5',
    borderRadius: 8,
  },
  connectionText: {
    marginLeft: 5,
    fontSize: 14,
    color: '#333',
  },
  closeButton: {
    marginTop: 20,
    backgroundColor: '#2196F3',
    padding: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  closeButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
  },
});