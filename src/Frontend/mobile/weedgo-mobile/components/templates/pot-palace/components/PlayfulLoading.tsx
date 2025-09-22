import React, { useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Animated,
  Easing,
} from 'react-native';
import { PotPalaceTheme } from '../Theme';

interface PlayfulLoadingProps {
  size?: 'small' | 'medium' | 'large';
  message?: string;
}

export const PlayfulLoading: React.FC<PlayfulLoadingProps> = ({
  size = 'medium',
  message,
}) => {
  const rotateAnim = useRef(new Animated.Value(0)).current;
  const scaleAnim = useRef(new Animated.Value(1)).current;
  const pulseAnim = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    // Rotation animation for the main leaf
    Animated.loop(
      Animated.timing(rotateAnim, {
        toValue: 1,
        duration: 2000,
        easing: Easing.linear,
        useNativeDriver: true,
      })
    ).start();

    // Pulse animation for the surrounding leaves
    Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, {
          toValue: 1.2,
          duration: 800,
          easing: Easing.inOut(Easing.ease),
          useNativeDriver: true,
        }),
        Animated.timing(pulseAnim, {
          toValue: 1,
          duration: 800,
          easing: Easing.inOut(Easing.ease),
          useNativeDriver: true,
        }),
      ])
    ).start();

    // Scale animation for bounce effect
    Animated.loop(
      Animated.sequence([
        Animated.timing(scaleAnim, {
          toValue: 1.1,
          duration: 600,
          easing: Easing.back(1.5),
          useNativeDriver: true,
        }),
        Animated.timing(scaleAnim, {
          toValue: 1,
          duration: 600,
          easing: Easing.elastic(1),
          useNativeDriver: true,
        }),
      ])
    ).start();
  }, []);

  const getSize = () => {
    switch (size) {
      case 'small':
        return { emoji: 24, container: 60 };
      case 'large':
        return { emoji: 48, container: 120 };
      default:
        return { emoji: 36, container: 90 };
    }
  };

  const sizeConfig = getSize();

  const spin = rotateAnim.interpolate({
    inputRange: [0, 1],
    outputRange: ['0deg', '360deg'],
  });

  return (
    <View style={styles.container}>
      <View
        style={[
          styles.loadingContainer,
          {
            width: sizeConfig.container,
            height: sizeConfig.container,
          },
        ]}
      >
        {/* Central rotating leaf */}
        <Animated.Text
          style={[
            styles.centralLeaf,
            {
              fontSize: sizeConfig.emoji,
              transform: [{ rotate: spin }, { scale: scaleAnim }],
            },
          ]}
        >
          🌿
        </Animated.Text>

        {/* Pulsing surrounding leaves */}
        <Animated.Text
          style={[
            styles.leafTop,
            {
              fontSize: sizeConfig.emoji * 0.6,
              transform: [{ scale: pulseAnim }],
            },
          ]}
        >
          🍃
        </Animated.Text>
        <Animated.Text
          style={[
            styles.leafRight,
            {
              fontSize: sizeConfig.emoji * 0.6,
              transform: [{ scale: pulseAnim }],
            },
          ]}
        >
          🍃
        </Animated.Text>
        <Animated.Text
          style={[
            styles.leafBottom,
            {
              fontSize: sizeConfig.emoji * 0.6,
              transform: [{ scale: pulseAnim }],
            },
          ]}
        >
          🍃
        </Animated.Text>
        <Animated.Text
          style={[
            styles.leafLeft,
            {
              fontSize: sizeConfig.emoji * 0.6,
              transform: [{ scale: pulseAnim }],
            },
          ]}
        >
          🍃
        </Animated.Text>
      </View>

      {message && (
        <Animated.View
          style={{
            transform: [{ scale: scaleAnim }],
          }}
        >
          <Text style={styles.message}>{message}</Text>
        </Animated.View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: PotPalaceTheme.spacing.lg,
  },
  loadingContainer: {
    justifyContent: 'center',
    alignItems: 'center',
    position: 'relative',
  },
  centralLeaf: {
    position: 'absolute',
  },
  leafTop: {
    position: 'absolute',
    top: 0,
  },
  leafRight: {
    position: 'absolute',
    right: 0,
  },
  leafBottom: {
    position: 'absolute',
    bottom: 0,
  },
  leafLeft: {
    position: 'absolute',
    left: 0,
  },
  message: {
    marginTop: PotPalaceTheme.spacing.lg,
    fontSize: PotPalaceTheme.typography.sizes.body,
    color: PotPalaceTheme.colors.primary,
    fontWeight: '600',
    textAlign: 'center',
  },
});