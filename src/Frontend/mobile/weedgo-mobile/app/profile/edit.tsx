import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TextInput,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  Image,
  Modal,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons, MaterialIcons } from '@expo/vector-icons';
import { useAuthStore } from '@/stores/authStore';
import { Colors, BorderRadius, Shadows, Gradients } from '@/constants/Colors';
import { LinearGradient } from 'expo-linear-gradient';
import * as ImagePicker from 'expo-image-picker';
import DateTimePicker from '@react-native-community/datetimepicker';
import { customerService } from '@/services/api/customer';
import { Profile } from '@/types/api.types';

export default function EditProfileScreen() {
  const router = useRouter();
  const { user, isAuthenticated } = useAuthStore();
  const isDark = true;
  const theme = isDark ? Colors.dark : Colors.light;

  // Form states
  const [loading, setLoading] = useState(false);
  const [savingField, setSavingField] = useState<string | null>(null);
  const [profile, setProfile] = useState<Profile | null>(null);

  // Form fields
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [dateOfBirth, setDateOfBirth] = useState<Date | null>(null);
  const [profileImage, setProfileImage] = useState('');

  // Verification states
  const [emailVerified, setEmailVerified] = useState(false);
  const [phoneVerified, setPhoneVerified] = useState(true); // Phone is verified if logged in
  const [ageVerified, setAgeVerified] = useState(false);

  // UI states
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [uploadingImage, setUploadingImage] = useState(false);
  const [verifyingEmail, setVerifyingEmail] = useState(false);
  const [verifyingAge, setVerifyingAge] = useState(false);

  useEffect(() => {
    if (!isAuthenticated) {
      router.replace('/(auth)/login');
    } else {
      loadProfile();
    }
  }, [isAuthenticated]);

  const loadProfile = async () => {
    setLoading(true);
    try {
      // Try to get full profile from customer service
      const profileData = await customerService.getProfile().catch(() => null);

      if (profileData) {
        setProfile(profileData);
        setFirstName(profileData.first_name || '');
        setLastName(profileData.last_name || '');
        setEmail(profileData.email || '');
        setPhone(profileData.phone || '');
        setProfileImage(profileData.profile_image || '');
        setEmailVerified(profileData.email_verified || false);
        setPhoneVerified(profileData.phone_verified || true);
        setAgeVerified(profileData.age_verified || false);

        if (profileData.date_of_birth) {
          setDateOfBirth(new Date(profileData.date_of_birth));
        }
      } else if (user) {
        // Fallback to user data from auth store
        setFirstName(user.first_name || user.firstName || '');
        setLastName(user.last_name || user.lastName || '');
        setEmail(user.email || '');
        setPhone(user.phone || '');
        setProfileImage(user.profile_image || '');
      }
    } catch (error) {
      console.error('Failed to load profile:', error);
    } finally {
      setLoading(false);
    }
  };

  const handlePickImage = async () => {
    const permissionResult = await ImagePicker.requestMediaLibraryPermissionsAsync();

    if (!permissionResult.granted) {
      Alert.alert('Permission Denied', 'You need to grant permission to access photos');
      return;
    }

    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      aspect: [1, 1],
      quality: 0.7,
    });

    if (!result.canceled) {
      await uploadProfileImage(result.assets[0].uri);
    }
  };

  const handleTakePhoto = async () => {
    const permissionResult = await ImagePicker.requestCameraPermissionsAsync();

    if (!permissionResult.granted) {
      Alert.alert('Permission Denied', 'You need to grant permission to use camera');
      return;
    }

    const result = await ImagePicker.launchCameraAsync({
      allowsEditing: true,
      aspect: [1, 1],
      quality: 0.7,
    });

    if (!result.canceled) {
      await uploadProfileImage(result.assets[0].uri);
    }
  };

  const uploadProfileImage = async (uri: string) => {
    setUploadingImage(true);
    try {
      const imageUrl = await customerService.uploadProfileImage(uri);
      setProfileImage(imageUrl);

      // If the URL is the same as the input URI, it means it's stored locally only
      if (imageUrl === uri) {
        Alert.alert(
          'Image Selected',
          'Your profile image has been selected. Please log in to save it to your profile.'
        );
      } else {
        Alert.alert('Success', 'Profile image updated');
      }
    } catch (error: any) {
      // Provide more specific error messages
      if (error.statusCode === 401 || error.status === 401) {
        Alert.alert(
          'Authentication Required',
          'Please log in to update your profile image.'
        );
        // Still show the image locally
        setProfileImage(uri);
      } else {
        Alert.alert('Error', 'Failed to upload image. Please try again.');
      }
    } finally {
      setUploadingImage(false);
    }
  };

  const showImageOptions = () => {
    Alert.alert(
      'Change Profile Photo',
      'Choose an option',
      [
        { text: 'Take Photo', onPress: handleTakePhoto },
        { text: 'Choose from Library', onPress: handlePickImage },
        profileImage ? { text: 'Remove Photo', onPress: () => setProfileImage(''), style: 'destructive' } : null,
        { text: 'Cancel', style: 'cancel' },
      ].filter(Boolean)
    );
  };

  const handleSave = async () => {
    if (!firstName || !lastName) {
      Alert.alert('Error', 'Please fill in all required fields');
      return;
    }

    setLoading(true);
    try {
      await customerService.updateProfile({
        first_name: firstName,
        last_name: lastName,
        email,
        date_of_birth: dateOfBirth ? dateOfBirth.toISOString().split('T')[0] : undefined,
        profile_image: profileImage,
      });

      Alert.alert('Success', 'Profile updated successfully', [
        { text: 'OK', onPress: () => router.back() }
      ]);
    } catch (error) {
      Alert.alert('Error', 'Failed to update profile');
    } finally {
      setLoading(false);
    }
  };

  const handleDateChange = (event: any, selectedDate?: Date) => {
    setShowDatePicker(Platform.OS === 'ios');
    if (selectedDate) {
      setDateOfBirth(selectedDate);
      checkAgeVerification(selectedDate);
    }
  };

  const checkAgeVerification = (date: Date) => {
    const age = Math.floor((Date.now() - date.getTime()) / (365.25 * 24 * 60 * 60 * 1000));
    if (age >= 19) { // Legal age in Canada for cannabis
      setAgeVerified(true);
    } else {
      setAgeVerified(false);
      Alert.alert('Age Verification', 'You must be 19 or older to use this service');
    }
  };

  const handleVerifyEmail = async () => {
    if (!email) {
      Alert.alert('Error', 'Please enter an email address');
      return;
    }

    setVerifyingEmail(true);
    try {
      await customerService.requestEmailVerification(email);
      Alert.alert(
        'Verification Email Sent',
        'Please check your email for the verification link',
        [{ text: 'OK' }]
      );
    } catch (error) {
      Alert.alert('Error', 'Failed to send verification email');
    } finally {
      setVerifyingEmail(false);
    }
  };

  const handleVerifyAge = async () => {
    if (!dateOfBirth) {
      Alert.alert('Error', 'Please select your date of birth first');
      return;
    }

    setVerifyingAge(true);
    try {
      const result = await customerService.verifyAge({
        date_of_birth: dateOfBirth.toISOString().split('T')[0],
        verification_method: 'manual',
      });

      if (result.verified) {
        setAgeVerified(true);
        Alert.alert('Success', 'Age verified successfully');
      } else {
        Alert.alert('Verification Failed', result.message || 'Unable to verify age');
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to verify age');
    } finally {
      setVerifyingAge(false);
    }
  };

  const formatDate = (date: Date | null) => {
    if (!date) return 'Select Date';
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  if (loading) {
    return (
      <View style={[styles.container, { backgroundColor: theme.background }]}>
        <ActivityIndicator size="large" color={theme.primary} />
      </View>
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
        <KeyboardAvoidingView
          style={{ flex: 1 }}
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        >
          {/* Header */}
          <View style={styles.header}>
            <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
              <Ionicons name="arrow-back" size={24} color={theme.text} />
            </TouchableOpacity>
            <Text style={[styles.headerTitle, { color: theme.text }]}>Edit Profile</Text>
            <TouchableOpacity onPress={handleSave} disabled={loading}>
              {loading ? (
                <ActivityIndicator size="small" color={theme.primary} />
              ) : (
                <Text style={[styles.saveText, { color: theme.primary }]}>Save</Text>
              )}
            </TouchableOpacity>
          </View>

          <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
            {/* Profile Image Section */}
            <View style={styles.imageSection}>
              <TouchableOpacity onPress={showImageOptions} disabled={uploadingImage}>
                {uploadingImage ? (
                  <View style={[styles.profileImagePlaceholder, { backgroundColor: theme.cardBackground }]}>
                    <ActivityIndicator size="large" color={theme.primary} />
                  </View>
                ) : profileImage ? (
                  <Image source={{ uri: profileImage }} style={styles.profileImage} />
                ) : (
                  <View style={[styles.profileImagePlaceholder, { backgroundColor: theme.cardBackground }]}>
                    <Ionicons name="person" size={50} color={theme.textSecondary} />
                  </View>
                )}
                <LinearGradient
                  colors={Gradients.primary}
                  style={styles.editImageButton}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 1 }}
                >
                  <Ionicons name="camera" size={20} color="white" />
                </LinearGradient>
              </TouchableOpacity>
              <Text style={[styles.changePhotoText, { color: theme.primary }]}>Change Photo</Text>
            </View>

            {/* Verification Status Cards */}
            <View style={styles.verificationSection}>
              <Text style={[styles.sectionTitle, { color: theme.text }]}>Verification Status</Text>

              <View style={[styles.verificationCard, { backgroundColor: theme.cardBackground }]}>
                <View style={styles.verificationRow}>
                  <View style={styles.verificationInfo}>
                    <Ionicons
                      name={phoneVerified ? "checkmark-circle" : "alert-circle"}
                      size={24}
                      color={phoneVerified ? theme.success : theme.warning}
                    />
                    <View style={styles.verificationText}>
                      <Text style={[styles.verificationLabel, { color: theme.text }]}>Phone</Text>
                      <Text style={[styles.verificationStatus, { color: theme.textSecondary }]}>
                        {phone} • {phoneVerified ? 'Verified' : 'Not Verified'}
                      </Text>
                    </View>
                  </View>
                </View>

                <View style={[styles.verificationRow, styles.verificationRowBorder]}>
                  <View style={styles.verificationInfo}>
                    <Ionicons
                      name={emailVerified ? "checkmark-circle" : "alert-circle"}
                      size={24}
                      color={emailVerified ? theme.success : theme.warning}
                    />
                    <View style={styles.verificationText}>
                      <Text style={[styles.verificationLabel, { color: theme.text }]}>Email</Text>
                      <Text style={[styles.verificationStatus, { color: theme.textSecondary }]}>
                        {email || 'Not Set'} • {emailVerified ? 'Verified' : 'Not Verified'}
                      </Text>
                    </View>
                  </View>
                  {!emailVerified && email && (
                    <TouchableOpacity
                      onPress={handleVerifyEmail}
                      disabled={verifyingEmail}
                      style={[styles.verifyButton, { backgroundColor: theme.primary }]}
                    >
                      {verifyingEmail ? (
                        <ActivityIndicator size="small" color="white" />
                      ) : (
                        <Text style={styles.verifyButtonText}>Verify</Text>
                      )}
                    </TouchableOpacity>
                  )}
                </View>

                <View style={[styles.verificationRow, styles.verificationRowBorder]}>
                  <View style={styles.verificationInfo}>
                    <MaterialIcons
                      name={ageVerified ? "verified-user" : "gpp-maybe"}
                      size={24}
                      color={ageVerified ? theme.success : theme.warning}
                    />
                    <View style={styles.verificationText}>
                      <Text style={[styles.verificationLabel, { color: theme.text }]}>Age Verification</Text>
                      <Text style={[styles.verificationStatus, { color: theme.textSecondary }]}>
                        {ageVerified ? 'Verified (19+)' : 'Not Verified'}
                      </Text>
                    </View>
                  </View>
                  {!ageVerified && dateOfBirth && (
                    <TouchableOpacity
                      onPress={handleVerifyAge}
                      disabled={verifyingAge}
                      style={[styles.verifyButton, { backgroundColor: theme.primary }]}
                    >
                      {verifyingAge ? (
                        <ActivityIndicator size="small" color="white" />
                      ) : (
                        <Text style={styles.verifyButtonText}>Verify</Text>
                      )}
                    </TouchableOpacity>
                  )}
                </View>
              </View>
            </View>

            {/* Form Fields */}
            <View style={styles.form}>
              <Text style={[styles.sectionTitle, { color: theme.text }]}>Personal Information</Text>

              <View style={styles.inputGroup}>
                <Text style={[styles.label, { color: theme.textSecondary }]}>First Name *</Text>
                <TextInput
                  style={[styles.input, { backgroundColor: theme.cardBackground, color: theme.text }]}
                  value={firstName}
                  onChangeText={setFirstName}
                  placeholder="Enter first name"
                  placeholderTextColor={theme.textSecondary}
                />
              </View>

              <View style={styles.inputGroup}>
                <Text style={[styles.label, { color: theme.textSecondary }]}>Last Name *</Text>
                <TextInput
                  style={[styles.input, { backgroundColor: theme.cardBackground, color: theme.text }]}
                  value={lastName}
                  onChangeText={setLastName}
                  placeholder="Enter last name"
                  placeholderTextColor={theme.textSecondary}
                />
              </View>

              <View style={styles.inputGroup}>
                <Text style={[styles.label, { color: theme.textSecondary }]}>Email</Text>
                <View style={styles.inputWithIcon}>
                  <TextInput
                    style={[styles.input, { backgroundColor: theme.cardBackground, color: theme.text, flex: 1 }]}
                    value={email}
                    onChangeText={setEmail}
                    placeholder="Enter email"
                    placeholderTextColor={theme.textSecondary}
                    keyboardType="email-address"
                    autoCapitalize="none"
                  />
                  {emailVerified && (
                    <View style={styles.verifiedBadge}>
                      <Ionicons name="checkmark-circle" size={20} color={theme.success} />
                    </View>
                  )}
                </View>
              </View>

              <View style={styles.inputGroup}>
                <Text style={[styles.label, { color: theme.textSecondary }]}>Phone</Text>
                <View style={styles.inputWithIcon}>
                  <TextInput
                    style={[styles.input, { backgroundColor: theme.cardBackground, color: theme.textTertiary, flex: 1 }]}
                    value={phone}
                    editable={false}
                    placeholder="Phone number"
                    placeholderTextColor={theme.textSecondary}
                  />
                  <View style={styles.verifiedBadge}>
                    <Ionicons name="checkmark-circle" size={20} color={theme.success} />
                  </View>
                </View>
                <Text style={[styles.helperText, { color: theme.textTertiary }]}>
                  Phone number cannot be changed
                </Text>
              </View>

              <View style={styles.inputGroup}>
                <Text style={[styles.label, { color: theme.textSecondary }]}>Date of Birth</Text>
                <TouchableOpacity
                  style={[styles.dateInput, { backgroundColor: theme.cardBackground }]}
                  onPress={() => setShowDatePicker(true)}
                >
                  <Text style={[styles.dateText, { color: dateOfBirth ? theme.text : theme.textSecondary }]}>
                    {formatDate(dateOfBirth)}
                  </Text>
                  <Ionicons name="calendar" size={20} color={theme.textSecondary} />
                </TouchableOpacity>
                {ageVerified && (
                  <Text style={[styles.helperText, { color: theme.success }]}>
                    ✓ Age verified (19+)
                  </Text>
                )}
              </View>
            </View>

            {/* Additional Actions */}
            <View style={styles.additionalActions}>
              <TouchableOpacity
                style={[styles.actionButton, { borderColor: theme.border }]}
                onPress={() => router.push('/addresses')}
              >
                <Ionicons name="location" size={20} color={theme.text} />
                <Text style={[styles.actionButtonText, { color: theme.text }]}>Manage Addresses</Text>
                <Ionicons name="chevron-forward" size={20} color={theme.textSecondary} />
              </TouchableOpacity>

            </View>

            {/* Delete Account */}
            <TouchableOpacity
              style={styles.deleteAccount}
              onPress={() => Alert.alert(
                'Delete Account',
                'Are you sure you want to delete your account? This action cannot be undone.',
                [
                  { text: 'Cancel', style: 'cancel' },
                  { text: 'Delete', style: 'destructive', onPress: async () => {
                    try {
                      await customerService.deleteAccount();
                      Alert.alert('Account Deleted', 'Your account has been deleted');
                      router.replace('/(auth)/login');
                    } catch (error) {
                      Alert.alert('Error', 'Failed to delete account');
                    }
                  }}
                ]
              )}
            >
              <Text style={[styles.deleteAccountText, { color: theme.error }]}>Delete Account</Text>
            </TouchableOpacity>
          </ScrollView>

          {/* Date Picker Modal */}
          {showDatePicker && (
            <DateTimePicker
              value={dateOfBirth || new Date(2000, 0, 1)}
              mode="date"
              display={Platform.OS === 'ios' ? 'spinner' : 'default'}
              onChange={handleDateChange}
              maximumDate={new Date()}
              minimumDate={new Date(1900, 0, 1)}
            />
          )}
        </KeyboardAvoidingView>
      </SafeAreaView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  gradientContainer: {
    flex: 1,
  },
  container: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  backButton: {
    padding: 4,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
  },
  saveText: {
    fontSize: 16,
    fontWeight: '600',
  },
  content: {
    flex: 1,
  },
  imageSection: {
    alignItems: 'center',
    paddingVertical: 24,
  },
  profileImage: {
    width: 120,
    height: 120,
    borderRadius: 60,
    borderWidth: 3,
    borderColor: 'white',
  },
  profileImagePlaceholder: {
    width: 120,
    height: 120,
    borderRadius: 60,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 3,
    borderColor: 'rgba(255, 255, 255, 0.2)',
  },
  editImageButton: {
    position: 'absolute',
    bottom: 0,
    right: 0,
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 3,
    borderColor: 'white',
    ...Shadows.small,
  },
  changePhotoText: {
    marginTop: 12,
    fontSize: 16,
    fontWeight: '500',
  },
  verificationSection: {
    paddingHorizontal: 16,
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 12,
  },
  verificationCard: {
    borderRadius: BorderRadius.medium,
    overflow: 'hidden',
    ...Shadows.small,
  },
  verificationRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
  },
  verificationRowBorder: {
    borderTopWidth: 1,
    borderTopColor: 'rgba(255, 255, 255, 0.1)',
  },
  verificationInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  verificationText: {
    marginLeft: 12,
    flex: 1,
  },
  verificationLabel: {
    fontSize: 16,
    fontWeight: '500',
    marginBottom: 2,
  },
  verificationStatus: {
    fontSize: 13,
  },
  verifyButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: BorderRadius.small,
    minWidth: 70,
    alignItems: 'center',
  },
  verifyButtonText: {
    color: 'white',
    fontSize: 14,
    fontWeight: '600',
  },
  form: {
    paddingHorizontal: 16,
    marginBottom: 24,
  },
  inputGroup: {
    marginBottom: 20,
  },
  label: {
    fontSize: 14,
    fontWeight: '500',
    marginBottom: 8,
  },
  input: {
    borderRadius: BorderRadius.small,
    padding: 14,
    fontSize: 16,
    ...Shadows.small,
  },
  inputWithIcon: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  verifiedBadge: {
    position: 'absolute',
    right: 14,
  },
  helperText: {
    fontSize: 12,
    marginTop: 4,
  },
  dateInput: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    borderRadius: BorderRadius.small,
    padding: 14,
    ...Shadows.small,
  },
  dateText: {
    fontSize: 16,
  },
  additionalActions: {
    paddingHorizontal: 16,
    marginBottom: 24,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 16,
    borderBottomWidth: 1,
  },
  actionButtonText: {
    flex: 1,
    fontSize: 16,
    marginLeft: 12,
  },
  deleteAccount: {
    alignItems: 'center',
    paddingVertical: 20,
    marginBottom: 40,
  },
  deleteAccountText: {
    fontSize: 16,
    fontWeight: '500',
  },
});