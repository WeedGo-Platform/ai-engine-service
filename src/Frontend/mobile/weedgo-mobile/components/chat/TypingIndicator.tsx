import React, { useEffect } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withRepeat,
  withSequence,
  withTiming,
} from 'react-native-reanimated';
import { Colors } from '@/constants/Colors';

export function TypingIndicator() {
  const dot1Opacity = useSharedValue(0.3);
  const dot2Opacity = useSharedValue(0.3);
  const dot3Opacity = useSharedValue(0.3);

  useEffect(() => {
    dot1Opacity.value = withRepeat(
      withSequence(
        withTiming(1, { duration: 400 }),
        withTiming(0.3, { duration: 400 })
      ),
      -1,
      false
    );

    setTimeout(() => {
      dot2Opacity.value = withRepeat(
        withSequence(
          withTiming(1, { duration: 400 }),
          withTiming(0.3, { duration: 400 })
        ),
        -1,
        false
      );
    }, 200);

    setTimeout(() => {
      dot3Opacity.value = withRepeat(
        withSequence(
          withTiming(1, { duration: 400 }),
          withTiming(0.3, { duration: 400 })
        ),
        -1,
        false
      );
    }, 400);
  }, []);

  const dot1Style = useAnimatedStyle(() => ({
    opacity: dot1Opacity.value,
  }));

  const dot2Style = useAnimatedStyle(() => ({
    opacity: dot2Opacity.value,
  }));

  const dot3Style = useAnimatedStyle(() => ({
    opacity: dot3Opacity.value,
  }));

  return (
    <View style={styles.container}>
      <View style={styles.bubble}>
        <Text style={styles.text}>WeedGo AI is typing</Text>
        <View style={styles.dots}>
          <Animated.View style={[styles.dot, dot1Style]} />
          <Animated.View style={[styles.dot, dot2Style]} />
          <Animated.View style={[styles.dot, dot3Style]} />
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: 20,
    paddingVertical: 8,
    alignItems: 'flex-start',
  },
  bubble: {
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#e0e0e0',
    borderRadius: 18,
    borderBottomLeftRadius: 4,
    paddingHorizontal: 16,
    paddingVertical: 10,
    flexDirection: 'row',
    alignItems: 'center',
  },
  text: {
    fontSize: 14,
    color: '#9ca3af',
    marginRight: 8,
  },
  dots: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  dot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: Colors.light.primary,
    marginHorizontal: 2,
  },
});