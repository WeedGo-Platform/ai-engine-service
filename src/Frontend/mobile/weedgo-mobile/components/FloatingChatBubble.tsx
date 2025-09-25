import React, { useRef } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Dimensions,
  Platform,
} from 'react-native';
import {
  PanGestureHandler,
  State,
  GestureHandlerRootView,
  PanGestureHandlerGestureEvent,
} from 'react-native-gesture-handler';
import Animated, {
  useAnimatedStyle,
  useSharedValue,
  withSpring,
  runOnJS,
  useAnimatedGestureHandler,
} from 'react-native-reanimated';
import { useRouter, usePathname } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useChatStore } from '../stores/chatStore';
import { Colors } from '@/constants/Colors';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get('window');
const BUBBLE_SIZE = 56;

export function FloatingChatBubble() {
  const router = useRouter();
  const pathname = usePathname();
  const insets = useSafeAreaInsets();
  const { unreadCount } = useChatStore();

  const translateX = useSharedValue(SCREEN_WIDTH - BUBBLE_SIZE - 20);
  const translateY = useSharedValue(SCREEN_HEIGHT - BUBBLE_SIZE - 120 - insets.bottom);

  // Don't show bubble on chat screen itself
  if (pathname === '/chat' || pathname === '/(tabs)/chat') {
    return null;
  }

  const navigateToChat = () => {
    router.push('/(tabs)/chat');
  };

  const gestureHandler = useAnimatedGestureHandler<
    PanGestureHandlerGestureEvent,
    { startX: number; startY: number }
  >({
    onStart: (_, context) => {
      context.startX = translateX.value;
      context.startY = translateY.value;
    },
    onActive: (event: any, context: any) => {
      translateX.value = context.startX + event.translationX;
      translateY.value = context.startY + event.translationY;
    },
    onEnd: (event: any) => {
      // Snap to edge
      const isLeft = translateX.value < SCREEN_WIDTH / 2;
      const targetX = isLeft ? 20 : SCREEN_WIDTH - BUBBLE_SIZE - 20;

      // Keep within screen bounds
      const minY = insets.top + 20;
      const maxY = SCREEN_HEIGHT - BUBBLE_SIZE - 100 - insets.bottom;
      const targetY = Math.max(minY, Math.min(maxY, translateY.value));

      translateX.value = withSpring(targetX, {
        damping: 15,
        stiffness: 150,
      });
      translateY.value = withSpring(targetY, {
        damping: 15,
        stiffness: 150,
      });

      // If it's a tap (no significant movement), navigate to chat
      if (Math.abs(event.translationX) < 10 && Math.abs(event.translationY) < 10) {
        runOnJS(navigateToChat)();
      }
    },
  });

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [
      { translateX: translateX.value },
      { translateY: translateY.value },
    ],
  }));

  return (
    <PanGestureHandler onGestureEvent={gestureHandler}>
      <Animated.View style={[styles.container, animatedStyle]}>
        <TouchableOpacity
          style={styles.bubble}
          onPress={navigateToChat}
          activeOpacity={0.9}
        >
          <View style={styles.iconContainer}>
            <Ionicons name="chatbubbles" size={28} color="#fff" />
            {!!unreadCount && unreadCount > 0 && (
              <View style={styles.badge}>
                <Text style={styles.badgeText}>
                  {unreadCount > 99 ? '99+' : unreadCount}
                </Text>
              </View>
            )}
          </View>
        </TouchableOpacity>
      </Animated.View>
    </PanGestureHandler>
  );
}

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    zIndex: 9999,
    width: BUBBLE_SIZE,
    height: BUBBLE_SIZE,
  },
  bubble: {
    width: BUBBLE_SIZE,
    height: BUBBLE_SIZE,
    borderRadius: BUBBLE_SIZE / 2,
    backgroundColor: Colors.light.primary,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 4,
    },
    shadowOpacity: 0.3,
    shadowRadius: 4.65,
    elevation: 8,
  },
  iconContainer: {
    width: '100%',
    height: '100%',
    justifyContent: 'center',
    alignItems: 'center',
  },
  badge: {
    position: 'absolute',
    top: -4,
    right: -4,
    backgroundColor: '#ef4444',
    borderRadius: 10,
    minWidth: 20,
    height: 20,
    paddingHorizontal: 4,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: '#fff',
  },
  badgeText: {
    color: '#fff',
    fontSize: 10,
    fontWeight: '700',
  },
});