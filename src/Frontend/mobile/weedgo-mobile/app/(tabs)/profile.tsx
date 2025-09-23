import React, { useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Alert, ActivityIndicator } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useAuthStore } from '@/stores/authStore';
import { Colors } from '@/constants/Colors';
import { biometricAuth } from '@/utils/biometric';
import { authService } from '@/services/api/auth';

export default function ProfileScreen() {
  const router = useRouter();
  const { user, isAuthenticated, logout, biometricEnabled, setBiometricEnabled, isLoading } = useAuthStore();
  const [profileLoading, setProfileLoading] = React.useState(false);

  // Fetch user profile on mount if authenticated
  useEffect(() => {
    if (isAuthenticated && !user) {
      fetchUserProfile();
    }
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
          <Ionicons name="person-circle" size={80} color={Colors.light.gray} />
          <Text style={styles.guestTitle}>Sign in to view your profile</Text>
          <Text style={styles.guestSubtext}>
            Create an account or sign in to access your orders, favorites, and more
          </Text>
          <TouchableOpacity
            style={styles.signInButton}
            onPress={() => router.push('/(auth)/login')}
          >
            <Text style={styles.signInButtonText}>Sign In / Create Account</Text>
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
          <ActivityIndicator size="large" color={Colors.light.primary} />
          <Text style={styles.loadingText}>Loading profile...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView showsVerticalScrollIndicator={false}>
        {/* Profile Header */}
        <View style={styles.profileHeader}>
          <View style={styles.avatarContainer}>
            {user?.profile_image ? (
              <View style={styles.avatar} />
            ) : (
              <Ionicons name="person-circle" size={80} color={Colors.light.primary} />
            )}
          </View>
          <Text style={styles.userName}>
            {user?.first_name || user?.firstName} {user?.last_name || user?.lastName}
          </Text>
          <Text style={styles.userPhone}>{user?.phone}</Text>
          {user?.email && <Text style={styles.userEmail}>{user?.email}</Text>}
        </View>

        {/* Menu Options */}
        <View style={styles.menuSection}>
          <TouchableOpacity style={styles.menuItem}>
            <Ionicons name="person-outline" size={24} color={Colors.light.text} />
            <Text style={styles.menuText}>Edit Profile</Text>
            <Ionicons name="chevron-forward" size={20} color={Colors.light.gray} />
          </TouchableOpacity>

          <TouchableOpacity style={styles.menuItem}>
            <Ionicons name="location-outline" size={24} color={Colors.light.text} />
            <Text style={styles.menuText}>Delivery Addresses</Text>
            <Ionicons name="chevron-forward" size={20} color={Colors.light.gray} />
          </TouchableOpacity>

          <TouchableOpacity style={styles.menuItem}>
            <Ionicons name="card-outline" size={24} color={Colors.light.text} />
            <Text style={styles.menuText}>Payment Methods</Text>
            <Ionicons name="chevron-forward" size={20} color={Colors.light.gray} />
          </TouchableOpacity>

          <TouchableOpacity style={styles.menuItem}>
            <Ionicons name="time-outline" size={24} color={Colors.light.text} />
            <Text style={styles.menuText}>Order History</Text>
            <Ionicons name="chevron-forward" size={20} color={Colors.light.gray} />
          </TouchableOpacity>

          <TouchableOpacity style={styles.menuItem}>
            <Ionicons name="heart-outline" size={24} color={Colors.light.text} />
            <Text style={styles.menuText}>Favorites</Text>
            <Ionicons name="chevron-forward" size={20} color={Colors.light.gray} />
          </TouchableOpacity>
        </View>

        {/* Settings Section */}
        <View style={styles.menuSection}>
          <Text style={styles.sectionTitle}>Settings</Text>

          <TouchableOpacity style={styles.menuItem}>
            <Ionicons name="notifications-outline" size={24} color={Colors.light.text} />
            <Text style={styles.menuText}>Notifications</Text>
            <Ionicons name="chevron-forward" size={20} color={Colors.light.gray} />
          </TouchableOpacity>

          <TouchableOpacity style={styles.menuItem} onPress={handleBiometricToggle}>
            <Ionicons name="finger-print-outline" size={24} color={Colors.light.text} />
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
            <Ionicons name="lock-closed-outline" size={24} color={Colors.light.text} />
            <Text style={styles.menuText}>Privacy & Security</Text>
            <Ionicons name="chevron-forward" size={20} color={Colors.light.gray} />
          </TouchableOpacity>
        </View>

        {/* Support Section */}
        <View style={styles.menuSection}>
          <Text style={styles.sectionTitle}>Support</Text>

          <TouchableOpacity style={styles.menuItem}>
            <Ionicons name="help-circle-outline" size={24} color={Colors.light.text} />
            <Text style={styles.menuText}>Help Center</Text>
            <Ionicons name="chevron-forward" size={20} color={Colors.light.gray} />
          </TouchableOpacity>

          <TouchableOpacity style={styles.menuItem}>
            <Ionicons name="document-text-outline" size={24} color={Colors.light.text} />
            <Text style={styles.menuText}>Terms of Service</Text>
            <Ionicons name="chevron-forward" size={20} color={Colors.light.gray} />
          </TouchableOpacity>

          <TouchableOpacity style={styles.menuItem}>
            <Ionicons name="shield-checkmark-outline" size={24} color={Colors.light.text} />
            <Text style={styles.menuText}>Privacy Policy</Text>
            <Ionicons name="chevron-forward" size={20} color={Colors.light.gray} />
          </TouchableOpacity>
        </View>

        {/* Sign Out Button */}
        <TouchableOpacity style={styles.signOutButton} onPress={handleLogout}>
          <Ionicons name="log-out-outline" size={24} color={Colors.light.error} />
          <Text style={styles.signOutText}>Sign Out</Text>
        </TouchableOpacity>

        {/* Version */}
        <Text style={styles.version}>Version 1.0.0</Text>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.light.background,
  },
  guestContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  guestTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: Colors.light.text,
    marginTop: 16,
    marginBottom: 8,
  },
  guestSubtext: {
    fontSize: 14,
    color: Colors.light.gray,
    textAlign: 'center',
    marginBottom: 24,
    paddingHorizontal: 20,
  },
  signInButton: {
    backgroundColor: Colors.light.primary,
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
  },
  signInButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
  profileHeader: {
    alignItems: 'center',
    padding: 24,
    borderBottomWidth: 1,
    borderBottomColor: Colors.light.border,
  },
  avatarContainer: {
    marginBottom: 16,
  },
  avatar: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: Colors.light.backgroundSecondary,
  },
  userName: {
    fontSize: 24,
    fontWeight: '700',
    color: Colors.light.text,
    marginBottom: 4,
  },
  userPhone: {
    fontSize: 14,
    color: Colors.light.gray,
  },
  userEmail: {
    fontSize: 14,
    color: Colors.light.gray,
    marginTop: 2,
  },
  menuSection: {
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: Colors.light.border,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.light.gray,
    marginLeft: 20,
    marginBottom: 8,
    textTransform: 'uppercase',
  },
  menuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    paddingHorizontal: 20,
  },
  menuText: {
    flex: 1,
    fontSize: 16,
    color: Colors.light.text,
    marginLeft: 12,
  },
  toggle: {
    width: 48,
    height: 28,
    borderRadius: 14,
    backgroundColor: Colors.light.backgroundSecondary,
    padding: 2,
  },
  toggleActive: {
    backgroundColor: Colors.light.primary,
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
    borderWidth: 1,
    borderColor: Colors.light.error,
    borderRadius: 8,
  },
  signOutText: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.light.error,
    marginLeft: 8,
  },
  version: {
    fontSize: 12,
    color: Colors.light.gray,
    textAlign: 'center',
    marginBottom: 20,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 12,
    fontSize: 14,
    color: Colors.light.gray,
  },
});