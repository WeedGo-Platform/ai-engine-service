import React, { useEffect, useRef } from 'react';
import { View, StyleSheet, Animated } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';

interface AudioWaveformProps {
  isRecording: boolean;
  audioLevel: number;  // 0-1 normalized
  isSpeaking: boolean;
  frequencyData?: number[];  // Optional frequency spectrum data
  style?: any;
}

export const AudioWaveform: React.FC<AudioWaveformProps> = ({
  isRecording,
  audioLevel,
  isSpeaking,
  frequencyData,
  style,
}) => {
  const animatedBars = useRef<Animated.Value[]>([]);
  const barCount = 20;

  // Initialize animated values
  useEffect(() => {
    if (animatedBars.current.length === 0) {
      animatedBars.current = Array.from(
        { length: barCount },
        () => new Animated.Value(0.1)
      );
    }
  }, []);

  // Animate bars based on audio level
  useEffect(() => {
    if (!isRecording) {
      // Reset all bars when not recording
      animatedBars.current.forEach(bar => {
        Animated.timing(bar, {
          toValue: 0.1,
          duration: 300,
          useNativeDriver: false,
        }).start();
      });
      return;
    }

    // Create wave effect
    animatedBars.current.forEach((bar, index) => {
      const delay = index * 30; // Stagger animation
      const baseHeight = audioLevel * 0.5;

      // Add randomness for natural look
      const randomFactor = 0.3 + Math.random() * 0.7;
      const targetHeight = isSpeaking
        ? baseHeight + (Math.sin(Date.now() / 200 + index) * 0.3) * randomFactor
        : 0.1 + audioLevel * 0.2 * randomFactor;

      Animated.sequence([
        Animated.delay(delay),
        Animated.spring(bar, {
          toValue: Math.max(0.1, Math.min(1, targetHeight)),
          friction: 8,
          tension: 40,
          useNativeDriver: false,
        }),
      ]).start();
    });
  }, [isRecording, audioLevel, isSpeaking]);

  // Use frequency data if available
  useEffect(() => {
    if (frequencyData && frequencyData.length > 0 && isRecording) {
      const samplesPerBar = Math.floor(frequencyData.length / barCount);

      animatedBars.current.forEach((bar, index) => {
        const startIdx = index * samplesPerBar;
        const endIdx = startIdx + samplesPerBar;
        const samples = frequencyData.slice(startIdx, endIdx);
        const avg = samples.reduce((a, b) => a + b, 0) / samples.length / 255;

        Animated.timing(bar, {
          toValue: Math.max(0.1, Math.min(1, avg)),
          duration: 50,
          useNativeDriver: false,
        }).start();
      });
    }
  }, [frequencyData, isRecording]);

  const getBarColor = (index: number) => {
    if (!isRecording) return '#666';
    if (isSpeaking) {
      // Green gradient when speaking
      const hue = 120 + (index * 2);
      return `hsl(${hue}, 70%, 50%)`;
    }
    // Blue gradient when silent
    const hue = 200 + (index * 2);
    return `hsl(${hue}, 60%, 40%)`;
  };

  return (
    <View style={[styles.container, style]}>
      <View style={styles.waveform}>
        {animatedBars.current.map((animatedHeight, index) => (
          <Animated.View
            key={index}
            style={[
              styles.bar,
              {
                height: animatedHeight.interpolate({
                  inputRange: [0, 1],
                  outputRange: ['10%', '100%'],
                }),
                backgroundColor: getBarColor(index),
              },
            ]}
          />
        ))}
      </View>

      {isSpeaking && (
        <LinearGradient
          colors={['transparent', 'rgba(0, 255, 0, 0.1)', 'transparent']}
          style={styles.glowEffect}
          start={{ x: 0, y: 0.5 }}
          end={{ x: 1, y: 0.5 }}
        />
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    height: 60,
    paddingHorizontal: 20,
    justifyContent: 'center',
    alignItems: 'center',
  },
  waveform: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    height: '100%',
    gap: 3,
  },
  bar: {
    width: 3,
    borderRadius: 1.5,
    minHeight: 4,
  },
  glowEffect: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    opacity: 0.5,
  },
});