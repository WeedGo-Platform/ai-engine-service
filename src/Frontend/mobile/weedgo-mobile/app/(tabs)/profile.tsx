import React, { useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Alert, ActivityIndicator } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useAuthStore } from '@/stores/authStore';
import { Colors, BorderRadius, Shadows, Gradients } from '@/constants/Colors';
import { LinearGradient } from 'expo-linear-gradient';
import { biometricAuth } from '@/utils/biometric';
import { authService } from '@/services/api/auth';
import AsyncStorage from '@react-native-async-storage/async-storage';

export default function ProfileScreen() {
  const router = useRouter();
  const { user, isAuthenticated, logout, biometricEnabled, setBiometricEnabled, isLoading } = useAuthStore();
  const [profileLoading, setProfileLoading] = React.useState(false);
  const [selectedLanguage, setSelectedLanguage] = React.useState('en');
  const [selectedTheme, setSelectedTheme] = React.useState('light');
  const isDark = selectedTheme === 'dark';
  const theme = isDark ? Colors.dark : Colors.light;

  // Fetch user profile and settings on mount if authenticated
  useEffect(() => {
    if (isAuthenticated && !user) {
      fetchUserProfile();
    }
    loadUserSettings();
  }, [isAuthenticated]);

  const fetchUserProfile = async () => {
    setProfileLoading(true);
    try {
      const profile = await authService.getProfile();
      useAuthStore.setState({ user: profile });
    } catch (error) {
      console.log('Failed to fetch profile:', error);
    } finally {
      setProfileLoading(false);
    }
  };

  const loadUserSettings = async () => {
    try {
      const language = await AsyncStorage.getItem('user_language');
      const theme = await AsyncStorage.getItem('user_theme');
      if (language) setSelectedLanguage(language);
      if (theme) setSelectedTheme(theme);
    } catch (error) {
      console.log('Failed to load settings:', error);
    }
  };

  const handleLanguageChange = async (language: string) => {
    setSelectedLanguage(language);
    await AsyncStorage.setItem('user_language', language);
    // Here you would trigger app-wide language change
  };

  const handleThemeChange = async (theme: string) => {
    setSelectedTheme(theme);
    await AsyncStorage.setItem('user_theme', theme);
    // Here you would trigger app-wide theme change
  };

  const handleLogout = () => {
    Alert.alert(
      'Sign Out',
      'Are you sure you want to sign out?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Sign Out',
          style: 'destructive',
          onPress: async () => {
            await logout();
            router.replace('/(auth)/login');
          },
        },
      ]
    );
  };

  const handleBiometricToggle = async () => {
    if (!biometricEnabled) {
      // Enable biometric
      const available = await biometricAuth.isAvailable();
      if (!available) {
        Alert.alert('Not Available', 'Biometric authentication is not available on this device');
        return;
      }

      const result = await biometricAuth.authenticate('Enable biometric login');
      if (result.success) {
        await setBiometricEnabled(true);
        Alert.alert('Success', 'Biometric login enabled');
      }
    } else {
      // Disable biometric
      await setBiometricEnabled(false);
      Alert.alert('Success', 'Biometric login disabled');
    }
  };

  if (!isAuthenticated) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.guestContainer}>
          <Ionicons name="person-circle" size={80} color={theme.textSecondary} />
          <Text style={styles.guestTitle}>Sign in to view your profile</Text>
          <Text style={styles.guestSubtext}>
            Create an account or sign in to access your orders, favorites, and more
          </Text>
          <TouchableOpacity
            style={styles.signInButton}
            onPress={() => router.push('/(auth)/login')}
            activeOpacity={0.8}
          >
            <LinearGradient
              colors={Gradients.primary}
              style={styles.signInGradient}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
            >
              <Text style={styles.signInButtonText}>Sign In / Create Account</Text>
            </LinearGradient>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  // Show loading state while fetching profile
  if (profileLoading || isLoading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={theme.primary} />
          <Text style={styles.loadingText}>Loading profile...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <LinearGradient
      colors={[theme.gradientStart, theme.gradientMid, theme.gradientEnd]}
      style={styles.gradientContainer}
      start={{ x: 0, y: 0 }}
      end={{ x: 0.5, y: 1 }}
    >
      <SafeAreaView style={styles.container}>
        <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.scrollContent}>
        {/* Profile Header */}
        <View style={styles.profileHeader}>
          <View style={styles.avatarContainer}>
            {user?.profile_image ? (
              <View style={styles.avatar} />
            ) : (
              <Ionicons name="person-circle" size={80} color={theme.primary} />
            )}
          </View>
          <Text style={styles.userName}>
            {user?.first_name || user?.firstName} {user?.last_name || user?.lastName}
          </Text>
          <Text style={styles.userPhone}>{user?.phone}</Text>
          {user?.email && <Text style={styles.userEmail}>{user?.email}</Text>}
        </View>

        {/* Quick Actions */}
        <View style={styles.quickActions}>
          <View style={styles.quickActionRow}>
            <TouchableOpacity
              style={styles.quickActionCard}
              onPress={() => router.push('/orders')}
              activeOpacity={0.8}
            >
              <LinearGradient
                colors={['#3B82F6', '#2563EB']}
                style={styles.quickActionGradient}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
              >
                <View style={styles.quickActionHeader}>
                  <View style={styles.quickActionInfo}>
                    <Text style={styles.quickActionTitle}>Orders</Text>
                    <Text style={styles.quickActionCount}>3</Text>
                    <Text style={styles.quickActionSubtitle}>Active</Text>
                  </View>
                  <Ionicons name="receipt-outline" size={28} color="white" />
                </View>
              </LinearGradient>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.quickActionCard}
              onPress={() => router.push('/delivery-tracking')}
              activeOpacity={0.8}
            >
              <LinearGradient
                colors={['#10B981', '#059669']}
                style={styles.quickActionGradient}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
              >
                <View style={styles.quickActionHeader}>
                  <View style={styles.quickActionInfo}>
                    <Text style={styles.quickActionTitle}>Track</Text>
                    <View style={styles.liveBadge}>
                      <View style={styles.liveDot} />
                      <Text style={styles.liveText}>LIVE</Text>
                    </View>
                    <Text style={styles.quickActionSubtitle}>En route</Text>
                  </View>
                  <Ionicons name="navigate-outline" size={28} color="white" />
                </View>
              </LinearGradient>
            </TouchableOpacity>
          </View>

          <View style={styles.quickActionRow}>
            <TouchableOpacity
              style={styles.quickActionCard}
              onPress={() => router.push('/wishlist')}
              activeOpacity={0.8}
            >
              <LinearGradient
                colors={['#EC4899', '#BE185D']}
                style={styles.quickActionGradient}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
              >
                <View style={styles.quickActionHeader}>
                  <View style={styles.quickActionInfo}>
                    <Text style={styles.quickActionTitle}>Wishlist</Text>
                    <Text style={styles.quickActionCount}>12</Text>
                    <Text style={styles.quickActionSubtitle}>Items</Text>
                  </View>
                  <Ionicons name="heart-outline" size={28} color="white" />
                </View>
              </LinearGradient>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.quickActionCard}
              onPress={() => router.push('/promotions')}
              activeOpacity={0.8}
            >
              <LinearGradient
                colors={['#F59E0B', '#D97706']}
                style={styles.quickActionGradient}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
              >
                <View style={styles.quickActionHeader}>
                  <View style={styles.quickActionInfo}>
                    <Text style={styles.quickActionTitle}>Deals</Text>
                    <View style={styles.newBadge}>
                      <Text style={styles.newBadgeText}>NEW</Text>
                    </View>
                    <Text style={styles.quickActionSubtitle}>5 Available</Text>
                  </View>
                  <Ionicons name="pricetag-outline" size={28} color="white" />
                </View>
              </LinearGradient>
            </TouchableOpacity>
          </View>
        </View>

        {/* Menu Options */}
        <View style={styles.menuSection}>
          <TouchableOpacity style={styles.menuItem} onPress={() => router.push('/profile/edit')}>
            <Ionicons name="person-outline" size={24} color={theme.text} />
            <Text style={styles.menuText}>Edit Profile</Text>
            <Ionicons name="chevron-forward" size={20} color={theme.textSecondary} />
          </TouchableOpacity>

          <TouchableOpacity style={styles.menuItem} onPress={() => router.push('/orders')}>
            <Ionicons name="time-outline" size={24} color={theme.text} />
            <Text style={styles.menuText}>Order History</Text>
            <Ionicons name="chevron-forward" size={20} color={theme.textSecondary} />
          </TouchableOpacity>

          <TouchableOpacity style={styles.menuItem} onPress={() => router.push('/delivery-tracking')}>
            <Ionicons name="navigate-outline" size={24} color={theme.text} />
            <Text style={styles.menuText}>Track Delivery</Text>
            <View style={styles.menuLiveBadge}>
              <View style={styles.liveDot} />
              <Text style={styles.liveText}>LIVE</Text>
            </View>
          </TouchableOpacity>

          <TouchableOpacity style={styles.menuItem} onPress={() => router.push('/wishlist')}>
            <Ionicons name="heart-outline" size={24} color={theme.text} />
            <Text style={styles.menuText}>Wishlist</Text>
            <Ionicons name="chevron-forward" size={20} color={theme.textSecondary} />
          </TouchableOpacity>

          <TouchableOpacity style={styles.menuItem} onPress={() => router.push('/promotions')}>
            <Ionicons name="gift-outline" size={24} color={theme.text} />
            <Text style={styles.menuText}>Promotions & Deals</Text>
            <View style={styles.menuNewBadge}>
              <Text style={styles.menuNewText}>NEW</Text>
            </View>
          </TouchableOpacity>

          <TouchableOpacity style={styles.menuItem} onPress={() => router.push('/addresses')}>
            <Ionicons name="location-outline" size={24} color={theme.text} />
            <Text style={styles.menuText}>Delivery Addresses</Text>
            <Ionicons name="chevron-forward" size={20} color={theme.textSecondary} />
          </TouchableOpacity>

          <TouchableOpacity style={styles.menuItem} onPress={() => router.push('/payment-methods')}>
            <Ionicons name="card-outline" size={24} color={theme.text} />
            <Text style={styles.menuText}>Payment Methods</Text>
            <Ionicons name="chevron-forward" size={20} color={theme.textSecondary} />
          </TouchableOpacity>
        </View>

        {/* Settings Section */}
        <View style={styles.menuSection}>
          <Text style={styles.sectionTitle}>Settings</Text>

          <TouchableOpacity style={styles.menuItem} onPress={() => handleLanguageChange(selectedLanguage === 'en' ? 'fr' : 'en')}>
            <Ionicons name="language-outline" size={24} color={theme.text} />
            <Text style={styles.menuText}>Language</Text>
            <View style={styles.menuRight}>
              <Text style={styles.menuValue}>{selectedLanguage === 'en' ? 'English' : 'Français'}</Text>
              <Ionicons name="chevron-forward" size={20} color={theme.textSecondary} />
            </View>
          </TouchableOpacity>

          <TouchableOpacity style={styles.menuItem} onPress={() => handleThemeChange(selectedTheme === 'light' ? 'dark' : 'light')}>
            <Ionicons name="color-palette-outline" size={24} color={theme.text} />
            <Text style={styles.menuText}>Theme</Text>
            <View style={styles.menuRight}>
              <Text style={styles.menuValue}>{selectedTheme === 'light' ? 'Light' : 'Dark'}</Text>
              <Ionicons name="chevron-forward" size={20} color={theme.textSecondary} />
            </View>
          </TouchableOpacity>

          <TouchableOpacity style={styles.menuItem} onPress={() => router.push('/settings/notifications')}>
            <Ionicons name="notifications-outline" size={24} color={theme.text} />
            <Text style={styles.menuText}>Notifications</Text>
            <Ionicons name="chevron-forward" size={20} color={theme.textSecondary} />
          </TouchableOpacity>

          <TouchableOpacity style={styles.menuItem} onPress={handleBiometricToggle}>
            <Ionicons name="finger-print-outline" size={24} color={theme.text} />
            <Text style={styles.menuText}>Biometric Login</Text>
            <View
              style={[
                styles.toggle,
                biometricEnabled && styles.toggleActive,
              ]}
            >
              <View
                style={[
                  styles.toggleDot,
                  biometricEnabled && styles.toggleDotActive,
                ]}
              />
            </View>
          </TouchableOpacity>

          <TouchableOpacity style={styles.menuItem}>
            <Ionicons name="lock-closed-outline" size={24} color={theme.text} />
            <Text style={styles.menuText}>Privacy & Security</Text>
            <Ionicons name="chevron-forward" size={20} color={theme.textSecondary} />
          </TouchableOpacity>
        </View>

        {/* Support Section */}
        <View style={styles.menuSection}>
          <Text style={styles.sectionTitle}>Support</Text>

          <TouchableOpacity style={styles.menuItem}>
            <Ionicons name="help-circle-outline" size={24} color={theme.text} />
            <Text style={styles.menuText}>Help Center</Text>
            <Ionicons name="chevron-forward" size={20} color={theme.textSecondary} />
          </TouchableOpacity>

          <TouchableOpacity style={styles.menuItem}>
            <Ionicons name="document-text-outline" size={24} color={theme.text} />
            <Text style={styles.menuText}>Terms of Service</Text>
            <Ionicons name="chevron-forward" size={20} color={theme.textSecondary} />
          </TouchableOpacity>

          <TouchableOpacity style={styles.menuItem}>
            <Ionicons name="shield-checkmark-outline" size={24} color={theme.text} />
            <Text style={styles.menuText}>Privacy Policy</Text>
            <Ionicons name="chevron-forward" size={20} color={theme.textSecondary} />
          </TouchableOpacity>
        </View>

        {/* Sign Out Button */}
        <TouchableOpacity style={styles.signOutButton} onPress={handleLogout}>
          <Ionicons name="log-out-outline" size={24} color={theme.error} />
          <Text style={styles.signOutText}>Sign Out</Text>
        </TouchableOpacity>

        {/* Version */}
        <Text style={styles.version}>Version 1.0.0</Text>
        </ScrollView>
      </SafeAreaView>
    </LinearGradient>
  );
}

const isDark = true;
const theme = isDark ? Colors.dark : Colors.light;

const styles = StyleSheet.create({
  gradientContainer: {
    flex: 1,
  },
  scrollContent: {
    paddingBottom: 100,
  },
  container: {
    flex: 1,
    backgroundColor: 'transparent',
  },
  guestContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  guestTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: theme.text,
    marginTop: 16,
    marginBottom: 8,
  },
  guestSubtext: {
    fontSize: 14,
    color: theme.textSecondary,
    textAlign: 'center',
    marginBottom: 24,
    paddingHorizontal: 20,
  },
  signInButton: {
    borderRadius: BorderRadius.xl,
    overflow: 'hidden',
    ...Shadows.medium,
  },
  signInGradient: {
    paddingHorizontal: 24,
    paddingVertical: 12,
  },
  signInButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
  quickActions: {
    paddingHorizontal: 16,
    marginTop: 20,
  },
  quickActionRow: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 12,
  },
  quickActionCard: {
    flex: 1,
    height: 100,
    borderRadius: BorderRadius.xl,
    overflow: 'hidden',
    borderWidth: 1.5,
    borderColor: 'rgba(255, 255, 255, 0.3)',
    ...Shadows.colorful,
  },
  quickActionGradient: {
    flex: 1,
    padding: 16,
    justifyContent: 'space-between',
  },
  quickActionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  quickActionInfo: {
    flex: 1,
  },
  quickActionTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: 'white',
    marginBottom: 4,
  },
  quickActionCount: {
    fontSize: 22,
    fontWeight: '800',
    color: 'white',
  },
  quickActionSubtitle: {
    fontSize: 11,
    color: 'rgba(255, 255, 255, 0.9)',
    marginTop: 2,
  },
  quickActionText: {
    fontSize: 14,
    fontWeight: '700',
    color: 'white',
    marginTop: 8,
  },
  liveBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.25)',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: BorderRadius.full,
    gap: 4,
  },
  liveDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#FF3B30',
  },
  liveText: {
    fontSize: 10,
    fontWeight: '700',
    color: 'white',
    letterSpacing: 0.5,
  },
  newBadge: {
    backgroundColor: 'rgba(255, 255, 255, 0.25)',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: BorderRadius.md,
  },
  newBadgeText: {
    fontSize: 10,
    fontWeight: '700',
    color: 'white',
  },
  menuLiveBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: theme.success,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: BorderRadius.md,
    gap: 4,
  },
  menuNewBadge: {
    backgroundColor: theme.accent,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: BorderRadius.md,
  },
  menuNewText: {
    fontSize: 10,
    fontWeight: '700',
    color: theme.text,
  },
  menuRight: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  menuValue: {
    fontSize: 14,
    color: theme.textSecondary,
    marginRight: 8,
  },
  profileHeader: {
    alignItems: 'center',
    padding: 24,
    backgroundColor: theme.glass,
    marginHorizontal: 16,
    marginTop: 16,
    borderRadius: BorderRadius.xl,
    borderWidth: 1,
    borderColor: theme.glassBorder,
    ...Shadows.small,
  },
  avatarContainer: {
    marginBottom: 16,
  },
  avatar: {
    width: 80,
    height: 80,
    borderRadius: BorderRadius.full,
    backgroundColor: theme.surface,
    borderWidth: 2,
    borderColor: theme.primary,
  },
  userName: {
    fontSize: 24,
    fontWeight: '700',
    color: theme.text,
    marginBottom: 4,
  },
  userPhone: {
    fontSize: 14,
    color: theme.textSecondary,
  },
  userEmail: {
    fontSize: 14,
    color: theme.textSecondary,
    marginTop: 2,
  },
  menuSection: {
    paddingVertical: 12,
    marginHorizontal: 16,
    marginTop: 12,
    backgroundColor: theme.glass,
    borderRadius: BorderRadius.xl,
    borderWidth: 1,
    borderColor: theme.glassBorder,
    ...Shadows.small,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: theme.textSecondary,
    marginLeft: 20,
    marginBottom: 8,
    marginTop: 4,
    textTransform: 'uppercase',
  },
  menuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    paddingHorizontal: 20,
    borderRadius: BorderRadius.lg,
  },
  menuText: {
    flex: 1,
    fontSize: 16,
    color: theme.text,
    marginLeft: 12,
  },
  toggle: {
    width: 48,
    height: 28,
    borderRadius: BorderRadius.full,
    backgroundColor: theme.surface,
    padding: 2,
    borderWidth: 1,
    borderColor: theme.glassBorder,
  },
  toggleActive: {
    backgroundColor: theme.primary,
    borderColor: theme.primary,
  },
  toggleDot: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: 'white',
  },
  toggleDotActive: {
    transform: [{ translateX: 20 }],
  },
  signOutButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
    margin: 20,
    backgroundColor: theme.glass,
    borderWidth: 1,
    borderColor: theme.error,
    borderRadius: BorderRadius.xl,
    ...Shadows.small,
  },
  signOutText: {
    fontSize: 16,
    fontWeight: '600',
    color: theme.error,
    marginLeft: 8,
  },
  version: {
    fontSize: 12,
    color: theme.textSecondary,
    textAlign: 'center',
    marginBottom: 100,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 12,
    fontSize: 14,
    color: theme.textSecondary,
  },
});