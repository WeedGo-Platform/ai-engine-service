import { useEffect, useState } from 'react';
import { Stack, useRouter, useSegments, useRootNavigation, Slot } from 'expo-router';
import { View, ActivityIndicator } from 'react-native';
import { useAuthStore } from '@/stores/authStore';
import useStoreStore from '@/stores/storeStore';
import { Colors } from '@/constants/Colors';
import Toast from 'react-native-toast-message';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { FloatingChatBubble } from '@/components/FloatingChatBubble';

export default function RootLayout() {
  const [isReady, setIsReady] = useState(false);
  const { isAuthenticated, isLoading, loadStoredAuth } = useAuthStore();
  const { loadStores } = useStoreStore();
  const segments = useSegments();
  const router = useRouter();
  const rootNav = useRootNavigation();

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
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: Colors.light.background }}>
        <ActivityIndicator size="large" color={Colors.light.primary} />
      </View>
    );
  }

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <Stack>
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