import { useEffect, useState } from 'react';
import { Stack, useRouter, useSegments, useRootNavigation, Slot } from 'expo-router';
import { View, ActivityIndicator, useColorScheme } from 'react-native';
import { useAuthStore } from '@/stores/authStore';
import useStoreStore from '@/stores/storeStore';
import { useTenantStore } from '@/stores/tenantStore';
import { useThemeStore } from '@/stores/themeStore';
import { ThemeProvider, useTheme } from '@/contexts/ThemeContext';
import { Colors } from '@/constants/Colors';
import Toast from 'react-native-toast-message';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { FloatingChatBubble } from '@/components/FloatingChatBubble';
import { BlurView } from 'expo-blur';
// TODO: Re-enable after native rebuild (npx expo prebuild --clean && npx expo run:ios)
// import { OfflineModeIndicator } from '@/components/OfflineModeIndicator';
// import { SessionTimeoutWarning } from '@/components/SessionTimeoutWarning';

function RootLayoutContent() {
  const [isReady, setIsReady] = useState(false);
  const { isAuthenticated, isLoading, loadStoredAuth } = useAuthStore();
  const { loadStores } = useStoreStore();
  const { loadTenant } = useTenantStore();
  const segments = useSegments();
  const router = useRouter();
  const rootNav = useRootNavigation();
  const { theme, isDark } = useTheme();

  // Load stored auth and stores on mount
  useEffect(() => {
    const initApp = async () => {
      // Load auth, stores, and tenant in parallel
      await Promise.all([
        loadStoredAuth(),
        loadStores(), // This will fetch stores and set nearest as default
        loadTenant()  // Load tenant settings for branding
      ]);
      setIsReady(true);
    };
    initApp();
  }, []);

  // Handle auth navigation
  useEffect(() => {
    if (!isReady || !rootNav?.isReady()) return;

    const inAuthGroup = segments[0] === '(auth)';
    const inTabsGroup = segments[0] === '(tabs)';

    // Only redirect from root to tabs, allow auth navigation
    if (segments.length === 0) {
      // If at root, redirect to main app
      router.replace('/(tabs)');
    }
    // Allow navigation to auth screens when needed
    // The auth screens will handle their own redirects after successful login
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
      {/* TODO: Re-enable after running: npx expo prebuild --clean && npx expo run:ios */}
      {/* <OfflineModeIndicator /> */}
      {/* {isAuthenticated && <SessionTimeoutWarning />} */}
      <Toast />
    </GestureHandlerRootView>
  );
}

export default function RootLayout() {
  return (
    <ThemeProvider>
      <RootLayoutContent />
    </ThemeProvider>
  );
}