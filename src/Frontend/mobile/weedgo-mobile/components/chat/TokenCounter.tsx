import React, { useState, useEffect, useRef } from 'react';
import { View, Text, StyleSheet, Animated } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

interface TokenCounterProps {
  currentTokens: number;
  isProcessing: boolean;
}

export const TokenCounter: React.FC<TokenCounterProps> = ({
  currentTokens,
  isProcessing
}) => {
  const [displayTokens, setDisplayTokens] = useState(currentTokens);
  const pulseAnim = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    if (isProcessing) {
      // Simulate token counting during processing
      const interval = setInterval(() => {
        setDisplayTokens(prev => prev + Math.floor(Math.random() * 5) + 1);
      }, 100);

      // Pulse animation
      Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, {
            toValue: 1.2,
            duration: 500,
            useNativeDriver: true,
          }),
          Animated.timing(pulseAnim, {
            toValue: 1,
            duration: 500,
            useNativeDriver: true,
          }),
        ])
      ).start();

      return () => {
        clearInterval(interval);
        pulseAnim.stopAnimation();
      };
    } else {
      setDisplayTokens(currentTokens);
      pulseAnim.setValue(1);
    }
  }, [isProcessing, currentTokens]);

  const getTokenColor = () => {
    if (displayTokens < 1000) return '#22C55E';
    if (displayTokens < 2000) return '#F59E0B';
    return '#EF4444';
  };

  return (
    <View style={styles.container}>
      <Animated.View style={[styles.tokenBadge, { transform: [{ scale: pulseAnim }] }]}>
        <Ionicons name="flash" size={12} color={getTokenColor()} />
        <Text style={[styles.tokenText, { color: getTokenColor() }]}>
          {displayTokens.toLocaleString()}
        </Text>
      </Animated.View>
      {isProcessing && (
        <View style={styles.processingDot} />
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    backgroundColor: 'rgba(255, 255, 255, 0.15)',
    borderRadius: 16,
  },
  tokenBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  tokenText: {
    fontSize: 12,
    fontWeight: '600',
  },
  processingDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#22C55E',
    marginLeft: 6,
  },
});
