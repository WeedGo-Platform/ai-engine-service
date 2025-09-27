import { Tabs } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { View, Text, StyleSheet, Platform } from 'react-native';
import { Colors, GlassStyles, BorderRadius, Gradients, Shadows } from '@/constants/Colors';
import { useAuthStore } from '@/stores/authStore';
import { useTheme } from '@/contexts/ThemeContext';
import { CartBadge } from '@/components/CartBadge';
import { BlurView } from 'expo-blur';
import { LinearGradient } from 'expo-linear-gradient';

export default function TabsLayout() {
  const { isAuthenticated } = useAuthStore();
  const { theme, isDark } = useTheme();

  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: theme.primary,
        tabBarInactiveTintColor: theme.textSecondary,
        tabBarStyle: {
          position: 'absolute',
          bottom: 0,
          left: 0,
          right: 0,
          backgroundColor: 'transparent',
          borderTopWidth: 0,
          height: Platform.OS === 'ios' ? 88 : 65,
          paddingBottom: Platform.OS === 'ios' ? 28 : 8,
          paddingTop: 8,
          borderTopLeftRadius: BorderRadius.xxl,
          borderTopRightRadius: BorderRadius.xxl,
          overflow: 'hidden',
          ...Shadows.colorful,
          elevation: 20,
        },
        tabBarLabelStyle: {
          fontSize: 11,
          fontWeight: '700',
          marginTop: 2,
        },
        tabBarIconStyle: {
          marginTop: 4,
        },
        tabBarBackground: () => (
          <LinearGradient
            colors={isDark ? ['rgba(30, 30, 50, 0.98)', 'rgba(22, 33, 62, 0.95)'] : ['rgba(255, 255, 255, 0.98)', 'rgba(250, 250, 255, 0.95)']}
            style={StyleSheet.absoluteFillObject}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
          />
        ),
        headerStyle: {
          backgroundColor: theme.background,
          elevation: 0,
          shadowOpacity: 0,
          borderBottomWidth: 0,
        },
        headerTransparent: true,
        headerTintColor: theme.text,
        headerTitleStyle: {
          fontWeight: '700',
          fontSize: 18,
        },
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: 'Home',
          tabBarIcon: ({ color, size, focused }) => (
            <View style={[styles.iconContainer, focused && styles.iconFocused]}>
              {focused && (
                <LinearGradient
                  colors={Gradients.primary}
                  style={styles.iconGradientBg}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 1 }}
                />
              )}
              <Ionicons
                name={focused ? "home" : "home-outline"}
                size={24}
                color={focused ? theme.primary : color}
              />
            </View>
          ),
          headerShown: false,
        }}
      />
      <Tabs.Screen
        name="search"
        options={{
          title: 'Search',
          tabBarIcon: ({ color, size, focused }) => (
            <View style={[styles.iconContainer, focused && styles.iconFocused]}>
              {focused && (
                <LinearGradient
                  colors={Gradients.ocean}
                  style={styles.iconGradientBg}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 1 }}
                />
              )}
              <Ionicons
                name={focused ? "search" : "search-outline"}
                size={24}
                color={focused ? theme.strainCBD : color}
              />
            </View>
          ),
          headerShown: false,
        }}
      />
      <Tabs.Screen
        name="cart"
        options={{
          title: 'Cart',
          tabBarIcon: ({ color, size, focused }) => (
            <View style={[styles.iconContainer, focused && styles.iconFocused]}>
              {focused && (
                <LinearGradient
                  colors={Gradients.warm}
                  style={styles.iconGradientBg}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 1 }}
                />
              )}
              <View>
                <Ionicons
                  name={focused ? "cart" : "cart-outline"}
                  size={24}
                  color={focused ? theme.strainSativa : color}
                />
                <CartBadge />
              </View>
            </View>
          ),
          headerTitle: 'Shopping Cart',
          headerShown: false,
        }}
      />
      <Tabs.Screen
        name="chat"
        options={{
          title: 'AI Chat',
          tabBarIcon: ({ color, size, focused }) => (
            <View style={[styles.iconContainer, focused && styles.iconFocused]}>
              {focused && (
                <LinearGradient
                  colors={Gradients.purple}
                  style={styles.iconGradientBg}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 1 }}
                />
              )}
              <Ionicons
                name={focused ? "chatbubbles" : "chatbubbles-outline"}
                size={24}
                color={focused ? theme.strainIndica : color}
              />
            </View>
          ),
          headerShown: false,
        }}
      />
      <Tabs.Screen
        name="profile"
        options={{
          title: 'Profile',
          tabBarIcon: ({ color, size, focused }) => (
            <View style={[styles.iconContainer, focused && styles.iconFocused]}>
              {focused && (
                <LinearGradient
                  colors={Gradients.secondary}
                  style={styles.iconGradientBg}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 1 }}
                />
              )}
              <Ionicons
                name={focused ? "person" : "person-outline"}
                size={24}
                color={focused ? theme.secondary : color}
              />
            </View>
          ),
          headerShown: false,
        }}
      />
    </Tabs>
  );
}

const styles = StyleSheet.create({
  iconContainer: {
    position: 'relative',
    width: 40,
    height: 40,
    justifyContent: 'center',
    alignItems: 'center',
  },
  iconFocused: {
    transform: [{ scale: 1.1 }],
  },
  iconGradientBg: {
    position: 'absolute',
    width: 36,
    height: 36,
    borderRadius: BorderRadius.full,
    opacity: 0.15,
  },
});