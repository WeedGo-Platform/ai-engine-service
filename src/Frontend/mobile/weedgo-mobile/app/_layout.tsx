import { useEffect, useState } from 'react';
import { Stack, useRouter, useSegments, useRootNavigation, Slot } from 'expo-router';
import { View, ActivityIndicator, useColorScheme } from 'react-native';
import { useAuthStore } from '@/stores/authStore';
import useStoreStore from '@/stores/storeStore';
import { Colors } from '@/constants/Colors';
import Toast from 'react-native-toast-message';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { FloatingChatBubble } from '@/components/FloatingChatBubble';
import { BlurView } from 'expo-blur';

export default function RootLayout() {
  const [isReady, setIsReady] = useState(false);
  const { isAuthenticated, isLoading, loadStoredAuth } = useAuthStore();
  const { loadStores } = useStoreStore();
  const segments = useSegments();
  const router = useRouter();
  const rootNav = useRootNavigation();
  const colorScheme = useColorScheme();
  const isDark = true; // Force dark mode for now
  const theme = isDark ? Colors.dark : Colors.light;

  // Load stored auth and stores on mount
  useEffect(() => {
    const initApp = async () => {
      // Load auth and stores in parallel
      await Promise.all([
        loadStoredAuth(),
        loadStores() // This will fetch stores and set nearest as default
      ]);
      setIsReady(true);
    };
    initApp();
  }, []);

  // Handle auth navigation - SIMPLIFIED FOR NOW
  useEffect(() => {
    if (!isReady || !rootNav?.isReady()) return;

    const inAuthGroup = segments[0] === '(auth)';

    // Skip auth for now - go directly to products page
    if (segments.length === 0 || inAuthGroup) {
      // If at root or in auth, redirect to main app
      router.replace('/(tabs)');
    }
  }, [segments, isReady, rootNav?.isReady()]);

  // Show loading screen while checking auth
  if (!isReady || isLoading) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: theme.background }}>
        <ActivityIndicator size="large" color={theme.primary} />
      </View>
    );
  }

  return (
    <GestureHandlerRootView style={{ flex: 1, backgroundColor: theme.background }}>
      <Stack
        screenOptions={{
          headerStyle: {
            backgroundColor: 'transparent',
          },
          headerTransparent: true,
          headerBlurEffect: isDark ? 'dark' : 'light',
          headerTintColor: theme.text,
          contentStyle: {
            backgroundColor: theme.background,
          },
        }}
      >
        <Stack.Screen name="(auth)" options={{ headerShown: false }} />
        <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
        <Stack.Screen name="(modals)" options={{ presentation: 'modal', headerShown: false }} />
        <Stack.Screen name="checkout" options={{ headerShown: false }} />
        <Stack.Screen name="orders" options={{ headerShown: false }} />
        <Stack.Screen name="product" options={{ headerShown: false }} />
      </Stack>
      {/* Chat disabled for now: {isAuthenticated && <FloatingChatBubble />} */}
      <Toast />
    </GestureHandlerRootView>
  );
}