import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
  Modal,
  TextInput,
  KeyboardAvoidingView,
  Platform,
  RefreshControl,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useAuthStore } from '@/stores/authStore';
import { Colors, BorderRadius, Shadows } from '@/constants/Colors';
import { LinearGradient } from 'expo-linear-gradient';
import { addressService, DeliveryAddress } from '@/services/api/addresses';

export default function DeliveryAddressesScreen() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();
  const isDark = true;
  const theme = isDark ? Colors.dark : Colors.light;

  const [addresses, setAddresses] = useState<DeliveryAddress[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingAddress, setEditingAddress] = useState<DeliveryAddress | null>(null);

  // Form state
  const [formName, setFormName] = useState('');
  const [formStreet, setFormStreet] = useState('');
  const [formCity, setFormCity] = useState('');
  const [formProvince, setFormProvince] = useState('');
  const [formPostalCode, setFormPostalCode] = useState('');
  const [formUnit, setFormUnit] = useState('');
  const [formInstructions, setFormInstructions] = useState('');
  const [formType, setFormType] = useState<'home' | 'work' | 'other'>('home');
  const [formIsDefault, setFormIsDefault] = useState(false);

  useEffect(() => {
    if (!isAuthenticated) {
      router.replace('/(auth)/login');
    } else {
      loadAddresses();
    }
  }, [isAuthenticated]);

  const loadAddresses = async () => {
    try {
      const data = await addressService.getAddresses();
      setAddresses(data);
    } catch (error: any) {
      // Only log and show errors for unexpected failures
      if (error.statusCode !== 404 && error.response?.status !== 404 &&
          error.statusCode !== 401 && error.status !== 401) {
        console.error('Failed to load addresses:', error);
        Alert.alert('Error', 'Failed to load addresses. Please try again.');
      }
      // Set empty array on error
      setAddresses([]);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadAddresses();
  };

  const handleAddAddress = () => {
    setEditingAddress(null);
    setFormName('');
    setFormStreet('');
    setFormCity('');
    setFormProvince('');
    setFormPostalCode('');
    setFormUnit('');
    setFormInstructions('');
    setFormType('home');
    setFormIsDefault(addresses.length === 0);
    setModalVisible(true);
  };

  const handleEditAddress = (address: DeliveryAddress) => {
    setEditingAddress(address);
    setFormName(address.name || '');
    setFormStreet(address.street);
    setFormCity(address.city);
    setFormProvince(address.province);
    setFormPostalCode(address.postal_code);
    setFormUnit(address.unit || '');
    setFormInstructions(address.instructions || '');
    setFormType(address.type || 'home');
    setFormIsDefault(address.is_default || false);
    setModalVisible(true);
  };

  const handleDeleteAddress = (address: DeliveryAddress) => {
    if (address.is_default) {
      Alert.alert('Error', 'Cannot delete default address. Please set another address as default first.');
      return;
    }

    Alert.alert(
      'Delete Address',
      'Are you sure you want to delete this address?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              if (address.id) {
                await addressService.deleteAddress(address.id);
                await loadAddresses();
              }
            } catch (error) {
              Alert.alert('Error', 'Failed to delete address');
            }
          },
        },
      ]
    );
  };

  const handleSetDefault = async (address: DeliveryAddress) => {
    try {
      if (address.id) {
        await addressService.setDefaultAddress(address.id);
        await loadAddresses();
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to set default address');
    }
  };

  const handleSaveAddress = async () => {
    if (!formName || !formStreet || !formCity || !formProvince || !formPostalCode) {
      Alert.alert('Error', 'Please fill in all required fields');
      return;
    }

    setSaving(true);
    try {
      const addressData: DeliveryAddress = {
        name: formName,
        street: formStreet,
        city: formCity,
        province: formProvince,
        postal_code: formPostalCode,
        unit: formUnit,
        instructions: formInstructions,
        type: formType,
        is_default: formIsDefault,
      };

      if (editingAddress && editingAddress.id) {
        // Update existing address
        await addressService.updateAddress(editingAddress.id, addressData);
      } else {
        // Add new address
        await addressService.addAddress(addressData);
      }

      await loadAddresses();
      setModalVisible(false);
    } catch (error) {
      Alert.alert('Error', 'Failed to save address');
    } finally {
      setSaving(false);
    }
  };

  const getTypeIcon = (type?: string) => {
    switch (type) {
      case 'home':
        return 'home';
      case 'work':
        return 'business';
      default:
        return 'location';
    }
  };

  return (
    <LinearGradient
      colors={[theme.gradientStart, theme.gradientMid, theme.gradientEnd]}
      style={styles.gradientContainer}
      start={{ x: 0, y: 0 }}
      end={{ x: 0.5, y: 1 }}
    >
      <SafeAreaView style={styles.container}>
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
            <Ionicons name="arrow-back" size={24} color={theme.text} />
          </TouchableOpacity>
          <Text style={[styles.headerTitle, { color: theme.text }]}>Delivery Addresses</Text>
          <View style={{ width: 24 }} />
        </View>

        {loading ? (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color={theme.primary} />
          </View>
        ) : (
          <ScrollView
            style={styles.content}
            showsVerticalScrollIndicator={false}
            refreshControl={
              <RefreshControl refreshing={refreshing} onRefresh={handleRefresh} />
            }
          >
            {addresses.length === 0 ? (
              <View style={styles.emptyContainer}>
                <Ionicons name="location-outline" size={64} color={theme.textSecondary} />
                <Text style={[styles.emptyText, { color: theme.textSecondary }]}>
                  No addresses saved
                </Text>
                <TouchableOpacity
                  style={[styles.addButton, { backgroundColor: theme.primary }]}
                  onPress={handleAddAddress}
                >
                  <Text style={styles.addButtonText}>Add First Address</Text>
                </TouchableOpacity>
              </View>
            ) : (
              <>
                {addresses.map((address, index) => (
                  <View
                    key={address.id || index}
                    style={[styles.addressCard, { backgroundColor: theme.cardBackground }]}
                  >
                    <View style={styles.addressHeader}>
                      <View style={styles.addressTypeContainer}>
                        <Ionicons
                          name={getTypeIcon(address.type)}
                          size={20}
                          color={theme.primary}
                        />
                        <Text style={[styles.addressName, { color: theme.text }]}>
                          {address.name}
                        </Text>
                        {address.is_default && (
                          <View style={[styles.defaultBadge, { backgroundColor: theme.primary }]}>
                            <Text style={styles.defaultBadgeText}>Default</Text>
                          </View>
                        )}
                      </View>
                      <View style={styles.addressActions}>
                        <TouchableOpacity
                          onPress={() => handleEditAddress(address)}
                          style={styles.actionButton}
                        >
                          <Ionicons name="pencil" size={18} color={theme.primary} />
                        </TouchableOpacity>
                        <TouchableOpacity
                          onPress={() => handleDeleteAddress(address)}
                          style={styles.actionButton}
                        >
                          <Ionicons name="trash-outline" size={18} color={theme.error} />
                        </TouchableOpacity>
                      </View>
                    </View>
                    <Text style={[styles.addressText, { color: theme.textSecondary }]}>
                      {address.unit ? `${address.unit} - ` : ''}{address.street}
                    </Text>
                    <Text style={[styles.addressText, { color: theme.textSecondary }]}>
                      {address.city}, {address.province} {address.postal_code}
                    </Text>
                    {address.instructions && (
                      <Text style={[styles.instructionsText, { color: theme.textSecondary }]}>
                        📍 {address.instructions}
                      </Text>
                    )}
                    {!address.is_default && (
                      <TouchableOpacity
                        style={styles.setDefaultButton}
                        onPress={() => handleSetDefault(address)}
                      >
                        <Text style={[styles.setDefaultText, { color: theme.primary }]}>
                          Set as Default
                        </Text>
                      </TouchableOpacity>
                    )}
                  </View>
                ))}
                {/* Bottom spacing for FAB */}
                <View style={{ height: 80 }} />
              </>
            )}
          </ScrollView>
        )}

        {/* Floating Action Button */}
        {addresses.length > 0 && !loading && (
          <TouchableOpacity
            style={[styles.fab, { backgroundColor: theme.primary }]}
            onPress={handleAddAddress}
            activeOpacity={0.8}
          >
            <LinearGradient
              colors={[theme.primary, theme.primaryDark]}
              style={styles.fabGradient}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
            >
              <Ionicons name="add" size={28} color="white" />
            </LinearGradient>
          </TouchableOpacity>
        )}

        {/* Add/Edit Modal */}
        <Modal
          visible={modalVisible}
          animationType="slide"
          transparent={true}
          onRequestClose={() => setModalVisible(false)}
        >
          <KeyboardAvoidingView
            style={styles.modalContainer}
            behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          >
            <View style={[styles.modalContent, { backgroundColor: theme.background }]}>
              <View style={styles.modalHeader}>
                <Text style={[styles.modalTitle, { color: theme.text }]}>
                  {editingAddress ? 'Edit Address' : 'Add New Address'}
                </Text>
                <TouchableOpacity onPress={() => setModalVisible(false)}>
                  <Ionicons name="close" size={24} color={theme.text} />
                </TouchableOpacity>
              </View>

              <ScrollView showsVerticalScrollIndicator={false}>
                <View style={styles.form}>
                  <View style={styles.inputGroup}>
                    <Text style={[styles.label, { color: theme.textSecondary }]}>Name *</Text>
                    <TextInput
                      style={[styles.input, { backgroundColor: theme.cardBackground, color: theme.text }]}
                      value={formName}
                      onChangeText={setFormName}
                      placeholder="e.g., Home, Work"
                      placeholderTextColor={theme.textSecondary}
                    />
                  </View>

                  <View style={styles.inputGroup}>
                    <Text style={[styles.label, { color: theme.textSecondary }]}>Street Address *</Text>
                    <TextInput
                      style={[styles.input, { backgroundColor: theme.cardBackground, color: theme.text }]}
                      value={formStreet}
                      onChangeText={setFormStreet}
                      placeholder="123 Main Street"
                      placeholderTextColor={theme.textSecondary}
                    />
                  </View>

                  <View style={styles.inputGroup}>
                    <Text style={[styles.label, { color: theme.textSecondary }]}>Unit/Apt (Optional)</Text>
                    <TextInput
                      style={[styles.input, { backgroundColor: theme.cardBackground, color: theme.text }]}
                      value={formUnit}
                      onChangeText={setFormUnit}
                      placeholder="Apt 4B"
                      placeholderTextColor={theme.textSecondary}
                    />
                  </View>

                  <View style={styles.row}>
                    <View style={[styles.inputGroup, { flex: 1 }]}>
                      <Text style={[styles.label, { color: theme.textSecondary }]}>City *</Text>
                      <TextInput
                        style={[styles.input, { backgroundColor: theme.cardBackground, color: theme.text }]}
                        value={formCity}
                        onChangeText={setFormCity}
                        placeholder="Toronto"
                        placeholderTextColor={theme.textSecondary}
                      />
                    </View>
                    <View style={[styles.inputGroup, { width: 80, marginLeft: 12 }]}>
                      <Text style={[styles.label, { color: theme.textSecondary }]}>Province *</Text>
                      <TextInput
                        style={[styles.input, { backgroundColor: theme.cardBackground, color: theme.text }]}
                        value={formProvince}
                        onChangeText={setFormProvince}
                        placeholder="ON"
                        placeholderTextColor={theme.textSecondary}
                        maxLength={2}
                        autoCapitalize="characters"
                      />
                    </View>
                  </View>

                  <View style={styles.inputGroup}>
                    <Text style={[styles.label, { color: theme.textSecondary }]}>Postal Code *</Text>
                    <TextInput
                      style={[styles.input, { backgroundColor: theme.cardBackground, color: theme.text }]}
                      value={formPostalCode}
                      onChangeText={setFormPostalCode}
                      placeholder="M5V 3A8"
                      placeholderTextColor={theme.textSecondary}
                      autoCapitalize="characters"
                    />
                  </View>

                  <View style={styles.inputGroup}>
                    <Text style={[styles.label, { color: theme.textSecondary }]}>Delivery Instructions</Text>
                    <TextInput
                      style={[styles.input, styles.textArea, { backgroundColor: theme.cardBackground, color: theme.text }]}
                      value={formInstructions}
                      onChangeText={setFormInstructions}
                      placeholder="Ring doorbell, leave at door, etc."
                      placeholderTextColor={theme.textSecondary}
                      multiline
                      numberOfLines={3}
                    />
                  </View>

                  <View style={styles.inputGroup}>
                    <Text style={[styles.label, { color: theme.textSecondary }]}>Type</Text>
                    <View style={styles.typeButtons}>
                      {(['home', 'work', 'other'] as const).map((type) => (
                        <TouchableOpacity
                          key={type}
                          style={[
                            styles.typeButton,
                            { backgroundColor: theme.cardBackground },
                            formType === type && { backgroundColor: theme.primary },
                          ]}
                          onPress={() => setFormType(type)}
                        >
                          <Text
                            style={[
                              styles.typeButtonText,
                              { color: theme.text },
                              formType === type && { color: 'white' },
                            ]}
                          >
                            {type.charAt(0).toUpperCase() + type.slice(1)}
                          </Text>
                        </TouchableOpacity>
                      ))}
                    </View>
                  </View>

                  <TouchableOpacity
                    style={styles.checkboxContainer}
                    onPress={() => setFormIsDefault(!formIsDefault)}
                  >
                    <View
                      style={[
                        styles.checkbox,
                        { borderColor: theme.border },
                        formIsDefault && { backgroundColor: theme.primary, borderColor: theme.primary },
                      ]}
                    >
                      {formIsDefault && <Ionicons name="checkmark" size={16} color="white" />}
                    </View>
                    <Text style={[styles.checkboxLabel, { color: theme.text }]}>
                      Set as default address
                    </Text>
                  </TouchableOpacity>
                </View>

                <View style={styles.modalButtons}>
                  <TouchableOpacity
                    style={[styles.cancelButton, { backgroundColor: theme.cardBackground }]}
                    onPress={() => setModalVisible(false)}
                  >
                    <Text style={[styles.cancelButtonText, { color: theme.text }]}>Cancel</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={[styles.saveButton, { backgroundColor: theme.primary }]}
                    onPress={handleSaveAddress}
                    disabled={saving}
                  >
                    {saving ? (
                      <ActivityIndicator color="white" />
                    ) : (
                      <Text style={styles.saveButtonText}>Save</Text>
                    )}
                  </TouchableOpacity>
                </View>
              </ScrollView>
            </View>
          </KeyboardAvoidingView>
        </Modal>
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
  content: {
    flex: 1,
    padding: 16,
  },
  loadingContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  emptyContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingTop: 100,
  },
  emptyText: {
    fontSize: 16,
    marginTop: 16,
    marginBottom: 24,
  },
  addButton: {
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: BorderRadius.medium,
  },
  addButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
  addressCard: {
    padding: 16,
    borderRadius: BorderRadius.medium,
    marginBottom: 12,
    ...Shadows.small,
  },
  addressHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  addressTypeContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  addressName: {
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
  defaultBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 12,
    marginLeft: 8,
  },
  defaultBadgeText: {
    color: 'white',
    fontSize: 12,
    fontWeight: '500',
  },
  addressActions: {
    flexDirection: 'row',
  },
  actionButton: {
    padding: 4,
    marginLeft: 12,
  },
  addressText: {
    fontSize: 14,
    marginBottom: 2,
  },
  instructionsText: {
    fontSize: 13,
    marginTop: 4,
    fontStyle: 'italic',
  },
  setDefaultButton: {
    marginTop: 12,
    paddingVertical: 4,
  },
  setDefaultText: {
    fontSize: 14,
    fontWeight: '500',
  },
  fab: {
    position: 'absolute',
    right: 20,
    bottom: 20,
    width: 56,
    height: 56,
    borderRadius: 28,
    elevation: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 5,
  },
  fabGradient: {
    width: 56,
    height: 56,
    borderRadius: 28,
    alignItems: 'center',
    justifyContent: 'center',
  },
  modalContainer: {
    flex: 1,
    justifyContent: 'flex-end',
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
  },
  modalContent: {
    borderTopLeftRadius: BorderRadius.large,
    borderTopRightRadius: BorderRadius.large,
    padding: 20,
    maxHeight: '90%',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '600',
  },
  form: {
    marginBottom: 20,
  },
  inputGroup: {
    marginBottom: 16,
  },
  label: {
    fontSize: 14,
    fontWeight: '500',
    marginBottom: 8,
  },
  input: {
    borderRadius: BorderRadius.small,
    padding: 12,
    fontSize: 16,
  },
  textArea: {
    minHeight: 80,
    textAlignVertical: 'top',
  },
  row: {
    flexDirection: 'row',
  },
  typeButtons: {
    flexDirection: 'row',
    gap: 8,
  },
  typeButton: {
    flex: 1,
    padding: 12,
    borderRadius: BorderRadius.small,
    alignItems: 'center',
  },
  typeButtonText: {
    fontSize: 14,
    fontWeight: '500',
  },
  checkboxContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 8,
  },
  checkbox: {
    width: 24,
    height: 24,
    borderRadius: 4,
    borderWidth: 2,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 8,
  },
  checkboxLabel: {
    fontSize: 14,
  },
  modalButtons: {
    flexDirection: 'row',
    gap: 12,
  },
  cancelButton: {
    flex: 1,
    padding: 16,
    borderRadius: BorderRadius.medium,
    alignItems: 'center',
  },
  cancelButtonText: {
    fontSize: 16,
    fontWeight: '600',
  },
  saveButton: {
    flex: 1,
    padding: 16,
    borderRadius: BorderRadius.medium,
    alignItems: 'center',
  },
  saveButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
});