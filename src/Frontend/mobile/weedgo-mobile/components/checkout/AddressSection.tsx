import React, { useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Modal,
  ScrollView,
  TextInput,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { DeliveryAddress } from '@/stores/orderStore';
import { useProfileStore } from '@/stores/profileStore';
import Toast from 'react-native-toast-message';
import { AddressAutocompleteInput } from './AddressAutocompleteInput';
import { AddressSuggestion } from '@/services/mapboxAutocomplete';

interface AddressSectionProps {
  selectedAddress: DeliveryAddress | null;
  onSelectAddress: (address: DeliveryAddress) => void;
  estimatedTime?: string;
}

export function AddressSection({
  selectedAddress,
  onSelectAddress,
  estimatedTime,
}: AddressSectionProps) {
  const { addresses, addAddress, updateAddress, deleteAddress, setDefaultAddress, validateAddress } = useProfileStore();
  const [showModal, setShowModal] = useState(false);
  const [addingNew, setAddingNew] = useState(false);
  const [editingAddress, setEditingAddress] = useState<DeliveryAddress | null>(null);
  const [loading, setLoading] = useState(false);

  // Form state for new/edit address
  const [newAddress, setNewAddress] = useState<Partial<DeliveryAddress>>({
    street: '',
    unit: '',
    city: '',
    province: 'ON', // Default to Ontario
    postal_code: '',
    instructions: '',
  });

  // If no address selected and no addresses available, show inline form
  if (!selectedAddress && addresses.length === 0) {
    return <QuickAddressForm onSave={onSelectAddress} />;
  }

  const handleAddAddress = async () => {
    if (!validateAddress(newAddress)) {
      Toast.show({
        type: 'error',
        text1: 'Invalid Address',
        text2: 'Please fill in all required fields',
      });
      return;
    }

    try {
      setLoading(true);
      const savedAddress = await addAddress(newAddress as Omit<DeliveryAddress, 'id'>);
      onSelectAddress(savedAddress);
      setShowModal(false);
      setAddingNew(false);
      setEditingAddress(null);
      resetForm();
    } catch (error) {
      // Error handled in store
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateAddress = async () => {
    if (!editingAddress?.id || !validateAddress(newAddress)) {
      Toast.show({
        type: 'error',
        text1: 'Invalid Address',
        text2: 'Please fill in all required fields',
      });
      return;
    }

    try {
      setLoading(true);
      await updateAddress(editingAddress.id, newAddress);

      // Update selected address if it was the one being edited
      if (selectedAddress?.id === editingAddress.id) {
        onSelectAddress({ ...editingAddress, ...newAddress } as DeliveryAddress);
      }

      setShowModal(false);
      setAddingNew(false);
      setEditingAddress(null);
      resetForm();
    } catch (error) {
      // Error handled in store
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteAddress = async (addressId: string) => {
    try {
      setLoading(true);
      await deleteAddress(addressId);

      // If deleted address was selected, clear selection
      if (selectedAddress?.id === addressId) {
        const remainingAddresses = addresses.filter(a => a.id !== addressId);
        if (remainingAddresses.length > 0) {
          onSelectAddress(remainingAddresses[0]);
        }
      }
    } catch (error) {
      // Error handled in store
    } finally {
      setLoading(false);
    }
  };

  const handleSetDefault = async (addressId: string) => {
    try {
      await setDefaultAddress(addressId);
    } catch (error) {
      // Error handled in store
    }
  };

  const handleEditAddress = (address: DeliveryAddress) => {
    setEditingAddress(address);
    setNewAddress({
      street: address.street,
      unit: address.unit,
      city: address.city,
      province: address.province,
      postal_code: address.postal_code,
      instructions: address.instructions,
      label: address.label,
    });
    setAddingNew(true);
    setShowModal(true);
  };

  const resetForm = () => {
    setNewAddress({
      street: '',
      unit: '',
      city: '',
      province: 'ON',
      postal_code: '',
      instructions: '',
    });
  };

  const formatAddress = (address: DeliveryAddress) => {
    const parts = [address.street];
    if (address.unit) parts.push(`Unit ${address.unit}`);
    parts.push(`${address.city}, ${address.province}`);
    parts.push(address.postal_code);
    return parts.join(', ');
  };

  return (
    <>
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Delivery Address</Text>

        {selectedAddress ? (
          <TouchableOpacity
            style={styles.addressCard}
            onPress={() => setShowModal(true)}
          >
            <View style={styles.addressContent}>
              <Ionicons name="location" size={20} color="#27AE60" />
              <View style={styles.addressDetails}>
                <Text style={styles.addressText} numberOfLines={2}>
                  {formatAddress(selectedAddress)}
                </Text>
                {selectedAddress.instructions && (
                  <Text style={styles.instructions} numberOfLines={1}>
                    Note: {selectedAddress.instructions}
                  </Text>
                )}
              </View>
              <Ionicons name="chevron-forward" size={20} color="#666" />
            </View>
          </TouchableOpacity>
        ) : (
          <TouchableOpacity
            style={styles.addButton}
            onPress={() => setShowModal(true)}
          >
            <Ionicons name="add-circle-outline" size={20} color="#27AE60" />
            <Text style={styles.addButtonText}>Add Delivery Address</Text>
          </TouchableOpacity>
        )}

        {estimatedTime && (
          <View style={styles.estimatedTime}>
            <Ionicons name="time-outline" size={16} color="#666" />
            <Text style={styles.estimatedTimeText}>
              Estimated delivery: {estimatedTime}
            </Text>
          </View>
        )}
      </View>

      {/* Address Selection Modal */}
      <Modal
        visible={showModal}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={() => setShowModal(false)}
      >
        <KeyboardAvoidingView
          style={styles.modalContainer}
          behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        >
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>
              {editingAddress ? 'Edit Address' : addingNew ? 'Add New Address' : 'Select Address'}
            </Text>
            <TouchableOpacity
              onPress={() => {
                setShowModal(false);
                setAddingNew(false);
                setEditingAddress(null);
                resetForm();
              }}
            >
              <Ionicons name="close" size={24} color="#333" />
            </TouchableOpacity>
          </View>

          <ScrollView style={styles.modalContent}>
            {!addingNew ? (
              <>
                {/* Existing Addresses */}
                {addresses.map((address) => (
                  <View key={address.id} style={styles.addressOptionContainer}>
                    <TouchableOpacity
                      style={[
                        styles.addressOption,
                        selectedAddress?.id === address.id && styles.addressOptionSelected,
                      ]}
                      onPress={() => {
                        onSelectAddress(address);
                        setShowModal(false);
                      }}
                    >
                      <View style={styles.addressOptionContent}>
                        <View style={styles.addressHeader}>
                          <Text style={styles.addressOptionText}>
                            {formatAddress(address)}
                          </Text>
                          {address.is_default && (
                            <View style={styles.defaultBadge}>
                              <Text style={styles.defaultBadgeText}>DEFAULT</Text>
                            </View>
                          )}
                        </View>
                        {address.instructions && (
                          <Text style={styles.addressOptionInstructions}>
                            Note: {address.instructions}
                          </Text>
                        )}
                      </View>
                      {selectedAddress?.id === address.id && (
                        <Ionicons name="checkmark-circle" size={24} color="#27AE60" />
                      )}
                    </TouchableOpacity>

                    {/* Address Actions */}
                    <View style={styles.addressActions}>
                      {!address.is_default && (
                        <TouchableOpacity
                          style={styles.actionButton}
                          onPress={() => handleSetDefault(address.id!)}
                        >
                          <Ionicons name="star-outline" size={18} color="#666" />
                          <Text style={styles.actionButtonText}>Set Default</Text>
                        </TouchableOpacity>
                      )}

                      <TouchableOpacity
                        style={styles.actionButton}
                        onPress={() => handleEditAddress(address)}
                      >
                        <Ionicons name="pencil-outline" size={18} color="#27AE60" />
                        <Text style={[styles.actionButtonText, { color: '#27AE60' }]}>Edit</Text>
                      </TouchableOpacity>

                      <TouchableOpacity
                        style={styles.actionButton}
                        onPress={() => {
                          Alert.alert(
                            'Delete Address',
                            'Are you sure you want to delete this address?',
                            [
                              { text: 'Cancel', style: 'cancel' },
                              {
                                text: 'Delete',
                                style: 'destructive',
                                onPress: () => handleDeleteAddress(address.id!),
                              },
                            ]
                          );
                        }}
                      >
                        <Ionicons name="trash-outline" size={18} color="#FF6B6B" />
                        <Text style={[styles.actionButtonText, { color: '#FF6B6B' }]}>Delete</Text>
                      </TouchableOpacity>
                    </View>
                  </View>
                ))}

                {/* Add New Address Button */}
                <TouchableOpacity
                  style={styles.newAddressButton}
                  onPress={() => setAddingNew(true)}
                >
                  <Ionicons name="add-circle-outline" size={20} color="#27AE60" />
                  <Text style={styles.newAddressButtonText}>Add New Address</Text>
                </TouchableOpacity>
              </>
            ) : (
              /* New Address Form */
              <View style={styles.form}>
                <Text style={styles.formLabel}>Street Address *</Text>
                <AddressAutocompleteInput
                  value={newAddress.street || ''}
                  onAddressSelect={(address, suggestion) => {
                    setNewAddress({
                      ...newAddress,
                      street: address.street || '',
                      city: address.city || '',
                      province: address.province || 'ON',
                      postal_code: address.postal_code || '',
                    });
                  }}
                  placeholder="Search for your address..."
                  autoFocus={true}
                />

                <Text style={styles.formLabel}>Unit/Apartment (Optional)</Text>
                <TextInput
                  style={styles.input}
                  placeholder="Unit/Apt"
                  value={newAddress.unit}
                  onChangeText={(text) => setNewAddress({ ...newAddress, unit: text })}
                />

                <View style={styles.row}>
                  <View style={styles.inputHalf}>
                    <Text style={styles.formLabel}>City *</Text>
                    <TextInput
                      style={styles.input}
                      placeholder="City"
                      value={newAddress.city}
                      onChangeText={(text) => setNewAddress({ ...newAddress, city: text })}
                      autoCapitalize="words"
                    />
                  </View>

                  <View style={styles.inputHalf}>
                    <Text style={styles.formLabel}>Province</Text>
                    <View style={styles.pickerContainer}>
                      <Text style={styles.pickerValue}>{newAddress.province}</Text>
                    </View>
                  </View>
                </View>

                <Text style={styles.formLabel}>Postal Code *</Text>
                <TextInput
                  style={styles.input}
                  placeholder="e.g., M5V 3A8"
                  value={newAddress.postal_code}
                  onChangeText={(text) => setNewAddress({ ...newAddress, postal_code: text.toUpperCase() })}
                  autoCapitalize="characters"
                  maxLength={7}
                />

                <TextInput
                  style={[styles.input, styles.textArea]}
                  placeholder="Delivery Instructions (Optional)"
                  value={newAddress.instructions}
                  onChangeText={(text) => setNewAddress({ ...newAddress, instructions: text })}
                  multiline
                  numberOfLines={3}
                />

                <View style={styles.formButtons}>
                  <TouchableOpacity
                    style={[styles.formButton, styles.cancelButton]}
                    onPress={() => {
                      setAddingNew(false);
                      setEditingAddress(null);
                      resetForm();
                    }}
                  >
                    <Text style={styles.cancelButtonText}>Cancel</Text>
                  </TouchableOpacity>

                  <TouchableOpacity
                    style={[styles.formButton, styles.saveButton]}
                    onPress={editingAddress ? handleUpdateAddress : handleAddAddress}
                    disabled={loading}
                  >
                    {loading ? (
                      <ActivityIndicator size="small" color="#FFF" />
                    ) : (
                      <Text style={styles.saveButtonText}>
                        {editingAddress ? 'Update Address' : 'Save Address'}
                      </Text>
                    )}
                  </TouchableOpacity>
                </View>
              </View>
            )}
          </ScrollView>
        </KeyboardAvoidingView>
      </Modal>
    </>
  );
}

// Quick inline form for first-time users
function QuickAddressForm({ onSave }: { onSave: (address: DeliveryAddress) => void }) {
  const { addAddress, validateAddress } = useProfileStore();
  const [address, setAddress] = useState<Partial<DeliveryAddress>>({
    street: '',
    unit: '',
    city: '',
    province: 'ON',
    postal_code: '',
    instructions: '',
  });
  const [loading, setLoading] = useState(false);

  const handleSave = async () => {
    if (!validateAddress(address)) {
      Toast.show({
        type: 'error',
        text1: 'Invalid Address',
        text2: 'Please fill in all required fields',
      });
      return;
    }

    try {
      setLoading(true);
      const savedAddress = await addAddress(address as Omit<DeliveryAddress, 'id'>);
      onSave(savedAddress);
    } catch (error) {
      // Error handled in store
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.quickForm}>
      <Text style={styles.sectionTitle}>Delivery Address</Text>
      <Text style={styles.quickFormHint}>Search for your delivery address to continue</Text>

      <Text style={styles.formLabel}>Street Address *</Text>
      <AddressAutocompleteInput
        value={address.street || ''}
        onAddressSelect={(selectedAddress, suggestion) => {
          setAddress({
            ...address,
            street: selectedAddress.street || '',
            city: selectedAddress.city || '',
            province: selectedAddress.province || 'ON',
            postal_code: selectedAddress.postal_code || '',
          });
        }}
        placeholder="Search for your address..."
        autoFocus={true}
      />

      <View style={styles.row}>
        <View style={styles.inputHalf}>
          <Text style={styles.formLabel}>Unit/Apartment</Text>
          <TextInput
            style={styles.input}
            placeholder="Unit/Apt"
            value={address.unit}
            onChangeText={(text) => setAddress({ ...address, unit: text })}
          />
        </View>

        <View style={styles.inputHalf}>
          <Text style={styles.formLabel}>City *</Text>
          <TextInput
            style={styles.input}
            placeholder="City"
            value={address.city}
            onChangeText={(text) => setAddress({ ...address, city: text })}
            autoCapitalize="words"
          />
        </View>
      </View>

      <View style={styles.row}>
        <View style={styles.inputHalf}>
          <Text style={styles.formLabel}>Province</Text>
          <View style={styles.pickerContainer}>
            <Text style={styles.pickerValue}>{address.province}</Text>
          </View>
        </View>

        <View style={styles.inputHalf}>
          <Text style={styles.formLabel}>Postal Code *</Text>
          <TextInput
            style={styles.input}
            placeholder="M5V 3A8"
            value={address.postal_code}
            onChangeText={(text) => setAddress({ ...address, postal_code: text.toUpperCase() })}
            autoCapitalize="characters"
            maxLength={7}
          />
        </View>
      </View>

      <TouchableOpacity
        style={[styles.saveButton, loading && styles.buttonDisabled]}
        onPress={handleSave}
        disabled={loading}
      >
        {loading ? (
          <ActivityIndicator size="small" color="#FFF" />
        ) : (
          <Text style={styles.saveButtonText}>Save & Continue</Text>
        )}
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  section: {
    backgroundColor: '#FFF',
    marginTop: 12,
    padding: 16,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 12,
  },
  addressCard: {
    backgroundColor: '#F8F9FA',
    borderRadius: 12,
    padding: 12,
  },
  addressContent: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  addressDetails: {
    flex: 1,
  },
  addressText: {
    fontSize: 14,
    color: '#333',
    lineHeight: 20,
  },
  instructions: {
    fontSize: 12,
    color: '#666',
    marginTop: 4,
  },
  addButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#F0FFF4',
    padding: 12,
    borderRadius: 8,
    gap: 8,
  },
  addButtonText: {
    fontSize: 14,
    color: '#27AE60',
    fontWeight: '500',
  },
  estimatedTime: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 8,
    gap: 4,
  },
  estimatedTimeText: {
    fontSize: 13,
    color: '#666',
  },
  modalContainer: {
    flex: 1,
    backgroundColor: '#FFF',
  },
  modalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#EEE',
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
  },
  modalContent: {
    flex: 1,
    padding: 16,
  },
  addressOptionContainer: {
    marginBottom: 12,
  },
  addressOption: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#F8F9FA',
    borderRadius: 8,
  },
  addressOptionSelected: {
    backgroundColor: '#F0FFF4',
    borderWidth: 1,
    borderColor: '#27AE60',
  },
  addressOptionContent: {
    flex: 1,
  },
  addressHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 4,
  },
  addressOptionText: {
    flex: 1,
    fontSize: 14,
    color: '#333',
    lineHeight: 20,
  },
  defaultBadge: {
    backgroundColor: '#27AE60',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
  },
  defaultBadgeText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#FFF',
    letterSpacing: 0.5,
  },
  addressOptionInstructions: {
    fontSize: 12,
    color: '#666',
    fontStyle: 'italic',
  },
  addressActions: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    gap: 8,
    marginTop: 8,
    paddingHorizontal: 4,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingVertical: 6,
    paddingHorizontal: 10,
    backgroundColor: '#F8F9FA',
    borderRadius: 6,
  },
  actionButtonText: {
    fontSize: 12,
    fontWeight: '500',
    color: '#666',
  },
  newAddressButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
    backgroundColor: '#F0FFF4',
    borderRadius: 8,
    marginTop: 8,
    gap: 8,
  },
  newAddressButtonText: {
    fontSize: 14,
    color: '#27AE60',
    fontWeight: '500',
  },
  form: {
    gap: 16,
  },
  formLabel: {
    fontSize: 13,
    fontWeight: '500',
    color: '#666',
    marginBottom: 6,
  },
  input: {
    backgroundColor: '#F8F9FA',
    padding: 12,
    borderRadius: 8,
    fontSize: 14,
    color: '#333',
  },
  textArea: {
    minHeight: 80,
    textAlignVertical: 'top',
  },
  row: {
    flexDirection: 'row',
    gap: 12,
  },
  inputHalf: {
    flex: 1,
  },
  pickerContainer: {
    backgroundColor: '#F8F9FA',
    padding: 12,
    borderRadius: 8,
    justifyContent: 'center',
    minHeight: 48,
  },
  pickerValue: {
    fontSize: 14,
    color: '#333',
    fontWeight: '500',
  },
  formButtons: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 16,
  },
  formButton: {
    flex: 1,
    padding: 14,
    borderRadius: 8,
    alignItems: 'center',
  },
  cancelButton: {
    backgroundColor: '#F8F9FA',
  },
  cancelButtonText: {
    fontSize: 15,
    color: '#666',
    fontWeight: '500',
  },
  saveButton: {
    backgroundColor: '#27AE60',
  },
  saveButtonText: {
    fontSize: 15,
    color: '#FFF',
    fontWeight: '600',
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  quickForm: {
    backgroundColor: '#FFF',
    marginTop: 12,
    padding: 16,
    gap: 12,
  },
  quickFormHint: {
    fontSize: 13,
    color: '#666',
    marginTop: -8,
    marginBottom: 4,
  },
});