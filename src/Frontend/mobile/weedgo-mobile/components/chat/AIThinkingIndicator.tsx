import React, { useEffect, useRef } from 'react';
import { View, Text, StyleSheet, Animated } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';

interface AIThinkingIndicatorProps {
  personality?: string;
}

export const AIThinkingIndicator: React.FC<AIThinkingIndicatorProps> = ({
  personality = 'marcel'
}) => {
  const dots = useRef([
    new Animated.Value(0),
    new Animated.Value(0),
    new Animated.Value(0),
  ]).current;

  useEffect(() => {
    const animations = dots.map((dot, index) =>
      Animated.loop(
        Animated.sequence([
          Animated.delay(index * 200),
          Animated.spring(dot, {
            toValue: 1,
            useNativeDriver: true,
            tension: 40,
            friction: 3,
          }),
          Animated.spring(dot, {
            toValue: 0,
            useNativeDriver: true,
            tension: 40,
            friction: 3,
          }),
        ])
      )
    );

    animations.forEach(anim => anim.start());

    return () => animations.forEach(anim => anim.stop());
  }, []);

  const getThinkingMessage = () => {
    const messages: Record<string, string[]> = {
      marcel: ["Rolling up some ideas...", "Checking the stash...", "Finding that fire..."],
      zac: ["Let me check that for you...", "Searching our selection...", "One moment..."],
      shante: ["Looking into that, sweetie...", "Finding the perfect match...", "Just a sec, hun..."],
      professional: ["Analyzing options...", "Searching inventory...", "Processing request..."],
      default: ["Thinking...", "Processing...", "Just a moment..."]
    };

    const msgs = messages[personality] || messages.default;
    return msgs[Math.floor(Math.random() * msgs.length)];
  };

  return (
    <View style={styles.container}>
      <LinearGradient
        colors={['rgba(34, 197, 94, 0.15)', 'rgba(34, 197, 94, 0.05)']}
        style={styles.bubble}
      >
        <Text style={styles.message}>{getThinkingMessage()}</Text>
        <View style={styles.dotsContainer}>
          {dots.map((dot, index) => (
            <Animated.View
              key={index}
              style={[
                styles.dot,
                {
                  transform: [
                    {
                      translateY: dot.interpolate({
                        inputRange: [0, 1],
                        outputRange: [0, -8],
                      }),
                    },
                  ],
                  opacity: dot.interpolate({
                    inputRange: [0, 1],
                    outputRange: [0.4, 1],
                  }),
                },
              ]}
            />
          ))}
        </View>
      </LinearGradient>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    alignItems: 'flex-start',
    marginVertical: 8,
    paddingHorizontal: 16,
  },
  bubble: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 18,
    borderWidth: 1,
    borderColor: 'rgba(34, 197, 94, 0.2)',
    gap: 12,
  },
  message: {
    color: '#22C55E',
    fontSize: 15,
    fontWeight: '500',
  },
  dotsContainer: {
    flexDirection: 'row',
    gap: 6,
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#22C55E',
  },
});
