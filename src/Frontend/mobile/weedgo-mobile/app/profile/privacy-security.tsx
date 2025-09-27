import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Switch,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Stack, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { Colors, BorderRadius, Shadows } from '@/constants/Colors';
import { LinearGradient } from 'expo-linear-gradient';
import { customerService } from '@/services/api/customer';
import { useAuthStore } from '@/stores/authStore';
import * as LocalAuthentication from 'expo-local-authentication';

export default function PrivacySecurityScreen() {
  const router = useRouter();
  const { user, logout } = useAuthStore();
  const isDark = false;
  const theme = isDark ? Colors.dark : Colors.light;

  const [loading, setLoading] = useState(false);
  const [settings, setSettings] = useState({
    biometricLogin: false,
    twoFactorAuth: false,
    loginNotifications: true,
    marketingEmails: false,
    smsNotifications: true,
    pushNotifications: true,
    shareDataWithPartners: false,
    allowAnalytics: true,
  });

  const handleToggle = async (key: keyof typeof settings) => {
    const newValue = !settings[key];
    setSettings(prev => ({ ...prev, [key]: newValue }));

    // Handle specific settings that need API calls
    try {
      if (key === 'biometricLogin') {
        if (newValue) {
          const hasHardware = await LocalAuthentication.hasHardwareAsync();
          const isEnrolled = await LocalAuthentication.isEnrolledAsync();

          if (!hasHardware || !isEnrolled) {
            Alert.alert(
              'Biometric Authentication',
              'Your device does not support biometric authentication or it is not configured.'
            );
            setSettings(prev => ({ ...prev, biometricLogin: false }));
            return;
          }
        }
      }

      // Update preferences on backend
      await customerService.updatePreferences({
        [key]: newValue,
      });
    } catch (error) {
      console.error(`Failed to update ${key}:`, error);
      // Revert the change
      setSettings(prev => ({ ...prev, [key]: !newValue }));
      Alert.alert('Error', 'Failed to update settings. Please try again.');
    }
  };

  const handleChangePassword = () => {
    router.push('/profile/change-password');
  };

  const handleExportData = async () => {
    Alert.alert(
      'Export Your Data',
      'We will prepare your data and send it to your registered email address. This may take up to 24 hours.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Export',
          onPress: async () => {
            try {
              setLoading(true);
              // API call would go here
              Alert.alert('Success', 'Your data export request has been submitted.');
            } catch (error) {
              Alert.alert('Error', 'Failed to request data export.');
            } finally {
              setLoading(false);
            }
          },
        },
      ]
    );
  };

  const handleDeleteAccount = () => {
    Alert.alert(
      'Delete Account',
      'Are you sure you want to delete your account? This action cannot be undone and all your data will be permanently deleted.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              setLoading(true);
              await customerService.deleteAccount('User requested');
              await logout();
              router.replace('/auth/login');
            } catch (error) {
              Alert.alert('Error', 'Failed to delete account.');
            } finally {
              setLoading(false);
            }
          },
        },
      ]
    );
  };

  return (
    <>
      <Stack.Screen
        options={{
          title: 'Privacy & Security',
          headerShown: true,
          headerStyle: {
            backgroundColor: theme.background,
          },
          headerTintColor: theme.primary,
          headerTitleStyle: {
            fontWeight: '600',
          },
          headerLeft: () => (
            <TouchableOpacity onPress={() => router.back()}>
              <Ionicons name="arrow-back" size={24} color={theme.primary} />
            </TouchableOpacity>
          ),
        }}
      />

      <LinearGradient
        colors={[theme.gradientStart, theme.gradientMid, theme.gradientEnd]}
        style={styles.gradientContainer}
        start={{ x: 0, y: 0 }}
        end={{ x: 0.5, y: 1 }}
      >
        <SafeAreaView style={styles.container}>
          <ScrollView showsVerticalScrollIndicator={false}>
            {/* Security Section */}
            <View style={styles.section}>
              <Text style={[styles.sectionTitle, { color: theme.text }]}>Security</Text>

              <View style={[styles.card, { backgroundColor: theme.card }]}>
                <TouchableOpacity
                  style={styles.settingRow}
                  onPress={handleChangePassword}
                >
                  <View style={styles.settingInfo}>
                    <Ionicons name="lock-closed-outline" size={24} color={theme.primary} />
                    <View style={styles.settingText}>
                      <Text style={[styles.settingTitle, { color: theme.text }]}>
                        Change Password
                      </Text>
                      <Text style={[styles.settingDescription, { color: theme.textSecondary }]}>
                        Update your account password
                      </Text>
                    </View>
                  </View>
                  <Ionicons name="chevron-forward" size={20} color={theme.textSecondary} />
                </TouchableOpacity>

                <View style={[styles.divider, { backgroundColor: theme.border }]} />

                <View style={styles.settingRow}>
                  <View style={styles.settingInfo}>
                    <Ionicons name="finger-print-outline" size={24} color={theme.primary} />
                    <View style={styles.settingText}>
                      <Text style={[styles.settingTitle, { color: theme.text }]}>
                        Biometric Login
                      </Text>
                      <Text style={[styles.settingDescription, { color: theme.textSecondary }]}>
                        Use Face ID or Touch ID to login
                      </Text>
                    </View>
                  </View>
                  <Switch
                    value={settings.biometricLogin}
                    onValueChange={() => handleToggle('biometricLogin')}
                    trackColor={{ false: theme.border, true: theme.primary }}
                    thumbColor={settings.biometricLogin ? '#fff' : '#f4f3f4'}
                  />
                </View>

                <View style={[styles.divider, { backgroundColor: theme.border }]} />

                <View style={styles.settingRow}>
                  <View style={styles.settingInfo}>
                    <Ionicons name="shield-checkmark-outline" size={24} color={theme.primary} />
                    <View style={styles.settingText}>
                      <Text style={[styles.settingTitle, { color: theme.text }]}>
                        Two-Factor Authentication
                      </Text>
                      <Text style={[styles.settingDescription, { color: theme.textSecondary }]}>
                        Add an extra layer of security
                      </Text>
                    </View>
                  </View>
                  <Switch
                    value={settings.twoFactorAuth}
                    onValueChange={() => handleToggle('twoFactorAuth')}
                    trackColor={{ false: theme.border, true: theme.primary }}
                    thumbColor={settings.twoFactorAuth ? '#fff' : '#f4f3f4'}
                  />
                </View>

                <View style={[styles.divider, { backgroundColor: theme.border }]} />

                <View style={styles.settingRow}>
                  <View style={styles.settingInfo}>
                    <Ionicons name="notifications-outline" size={24} color={theme.primary} />
                    <View style={styles.settingText}>
                      <Text style={[styles.settingTitle, { color: theme.text }]}>
                        Login Notifications
                      </Text>
                      <Text style={[styles.settingDescription, { color: theme.textSecondary }]}>
                        Get notified of new login attempts
                      </Text>
                    </View>
                  </View>
                  <Switch
                    value={settings.loginNotifications}
                    onValueChange={() => handleToggle('loginNotifications')}
                    trackColor={{ false: theme.border, true: theme.primary }}
                    thumbColor={settings.loginNotifications ? '#fff' : '#f4f3f4'}
                  />
                </View>
              </View>
            </View>

            {/* Privacy Section */}
            <View style={styles.section}>
              <Text style={[styles.sectionTitle, { color: theme.text }]}>Privacy</Text>

              <View style={[styles.card, { backgroundColor: theme.card }]}>
                <View style={styles.settingRow}>
                  <View style={styles.settingInfo}>
                    <Ionicons name="mail-outline" size={24} color={theme.primary} />
                    <View style={styles.settingText}>
                      <Text style={[styles.settingTitle, { color: theme.text }]}>
                        Marketing Emails
                      </Text>
                      <Text style={[styles.settingDescription, { color: theme.textSecondary }]}>
                        Receive promotional offers and updates
                      </Text>
                    </View>
                  </View>
                  <Switch
                    value={settings.marketingEmails}
                    onValueChange={() => handleToggle('marketingEmails')}
                    trackColor={{ false: theme.border, true: theme.primary }}
                    thumbColor={settings.marketingEmails ? '#fff' : '#f4f3f4'}
                  />
                </View>

                <View style={[styles.divider, { backgroundColor: theme.border }]} />

                <View style={styles.settingRow}>
                  <View style={styles.settingInfo}>
                    <Ionicons name="chatbubble-outline" size={24} color={theme.primary} />
                    <View style={styles.settingText}>
                      <Text style={[styles.settingTitle, { color: theme.text }]}>
                        SMS Notifications
                      </Text>
                      <Text style={[styles.settingDescription, { color: theme.textSecondary }]}>
                        Receive order updates via SMS
                      </Text>
                    </View>
                  </View>
                  <Switch
                    value={settings.smsNotifications}
                    onValueChange={() => handleToggle('smsNotifications')}
                    trackColor={{ false: theme.border, true: theme.primary }}
                    thumbColor={settings.smsNotifications ? '#fff' : '#f4f3f4'}
                  />
                </View>

                <View style={[styles.divider, { backgroundColor: theme.border }]} />

                <View style={styles.settingRow}>
                  <View style={styles.settingInfo}>
                    <Ionicons name="phone-portrait-outline" size={24} color={theme.primary} />
                    <View style={styles.settingText}>
                      <Text style={[styles.settingTitle, { color: theme.text }]}>
                        Push Notifications
                      </Text>
                      <Text style={[styles.settingDescription, { color: theme.textSecondary }]}>
                        Receive app notifications
                      </Text>
                    </View>
                  </View>
                  <Switch
                    value={settings.pushNotifications}
                    onValueChange={() => handleToggle('pushNotifications')}
                    trackColor={{ false: theme.border, true: theme.primary }}
                    thumbColor={settings.pushNotifications ? '#fff' : '#f4f3f4'}
                  />
                </View>
              </View>
            </View>

            {/* Data & Analytics Section */}
            <View style={styles.section}>
              <Text style={[styles.sectionTitle, { color: theme.text }]}>Data & Analytics</Text>

              <View style={[styles.card, { backgroundColor: theme.card }]}>
                <View style={styles.settingRow}>
                  <View style={styles.settingInfo}>
                    <Ionicons name="share-social-outline" size={24} color={theme.primary} />
                    <View style={styles.settingText}>
                      <Text style={[styles.settingTitle, { color: theme.text }]}>
                        Share with Partners
                      </Text>
                      <Text style={[styles.settingDescription, { color: theme.textSecondary }]}>
                        Share data with trusted partners
                      </Text>
                    </View>
                  </View>
                  <Switch
                    value={settings.shareDataWithPartners}
                    onValueChange={() => handleToggle('shareDataWithPartners')}
                    trackColor={{ false: theme.border, true: theme.primary }}
                    thumbColor={settings.shareDataWithPartners ? '#fff' : '#f4f3f4'}
                  />
                </View>

                <View style={[styles.divider, { backgroundColor: theme.border }]} />

                <View style={styles.settingRow}>
                  <View style={styles.settingInfo}>
                    <Ionicons name="analytics-outline" size={24} color={theme.primary} />
                    <View style={styles.settingText}>
                      <Text style={[styles.settingTitle, { color: theme.text }]}>
                        Analytics
                      </Text>
                      <Text style={[styles.settingDescription, { color: theme.textSecondary }]}>
                        Help us improve by sharing usage data
                      </Text>
                    </View>
                  </View>
                  <Switch
                    value={settings.allowAnalytics}
                    onValueChange={() => handleToggle('allowAnalytics')}
                    trackColor={{ false: theme.border, true: theme.primary }}
                    thumbColor={settings.allowAnalytics ? '#fff' : '#f4f3f4'}
                  />
                </View>

                <View style={[styles.divider, { backgroundColor: theme.border }]} />

                <TouchableOpacity
                  style={styles.settingRow}
                  onPress={handleExportData}
                >
                  <View style={styles.settingInfo}>
                    <Ionicons name="download-outline" size={24} color={theme.primary} />
                    <View style={styles.settingText}>
                      <Text style={[styles.settingTitle, { color: theme.text }]}>
                        Export Your Data
                      </Text>
                      <Text style={[styles.settingDescription, { color: theme.textSecondary }]}>
                        Download a copy of your data
                      </Text>
                    </View>
                  </View>
                  <Ionicons name="chevron-forward" size={20} color={theme.textSecondary} />
                </TouchableOpacity>
              </View>
            </View>

            {/* Danger Zone */}
            <View style={styles.section}>
              <Text style={[styles.sectionTitle, { color: theme.error }]}>Danger Zone</Text>

              <TouchableOpacity
                style={[styles.dangerButton, { borderColor: theme.error }]}
                onPress={handleDeleteAccount}
              >
                <Ionicons name="trash-outline" size={24} color={theme.error} />
                <Text style={[styles.dangerButtonText, { color: theme.error }]}>
                  Delete Account
                </Text>
              </TouchableOpacity>
            </View>
          </ScrollView>
        </SafeAreaView>
      </LinearGradient>
    </>
  );
}

const styles = StyleSheet.create({
  gradientContainer: {
    flex: 1,
  },
  container: {
    flex: 1,
  },
  section: {
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 12,
  },
  card: {
    borderRadius: BorderRadius.large,
    overflow: 'hidden',
    ...Shadows.small,
  },
  settingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
  },
  settingInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  settingText: {
    marginLeft: 12,
    flex: 1,
  },
  settingTitle: {
    fontSize: 16,
    fontWeight: '500',
    marginBottom: 2,
  },
  settingDescription: {
    fontSize: 13,
    lineHeight: 16,
  },
  divider: {
    height: 1,
    marginLeft: 52,
  },
  dangerButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
    borderRadius: BorderRadius.large,
    borderWidth: 2,
    gap: 8,
  },
  dangerButtonText: {
    fontSize: 16,
    fontWeight: '600',
  },
});