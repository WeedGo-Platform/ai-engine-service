import { useEffect, useState } from 'react';
import { Stack, useRouter, useSegments, useRootNavigation, Slot } from 'expo-router';
import { View, ActivityIndicator } from 'react-native';
import { useAuthStore } from '@/stores/authStore';
import { Colors } from '@/constants/Colors';

export default function RootLayout() {
  const [isReady, setIsReady] = useState(false);
  const { isAuthenticated, isLoading, loadStoredAuth } = useAuthStore();
  const segments = useSegments();
  const router = useRouter();
  const rootNav = useRootNavigation();

  // Load stored auth on mount
  useEffect(() => {
    const initAuth = async () => {
      await loadStoredAuth();
      setIsReady(true);
    };
    initAuth();
  }, []);

  // Handle auth navigation
  useEffect(() => {
    if (!isReady || !rootNav?.isReady()) return;

    const inAuthGroup = segments[0] === '(auth)';
    const inProtectedGroup = segments[0] === '(tabs)' ||
                            segments[0] === 'checkout' ||
                            segments[0] === 'orders' ||
                            segments[0] === 'product';

    if (!isAuthenticated && inProtectedGroup) {
      // User is not authenticated and trying to access protected route
      // Redirect to login
      router.replace('/(auth)/login');
    } else if (isAuthenticated && inAuthGroup) {
      // User is authenticated but in auth flow
      // Redirect to home
      router.replace('/(tabs)');
    }
  }, [isAuthenticated, segments, isReady, rootNav?.isReady()]);

  // Show loading screen while checking auth
  if (!isReady || isLoading) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: Colors.light.background }}>
        <ActivityIndicator size="large" color={Colors.light.primary} />
      </View>
    );
  }

  return (
    <Stack>
      <Stack.Screen name="(auth)" options={{ headerShown: false }} />
      <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
      <Stack.Screen name="(modals)" options={{ presentation: 'modal', headerShown: false }} />
      <Stack.Screen name="checkout" options={{ headerShown: false }} />
      <Stack.Screen name="orders" options={{ headerShown: false }} />
      <Stack.Screen name="product" options={{ headerShown: false }} />
    </Stack>
  );
}