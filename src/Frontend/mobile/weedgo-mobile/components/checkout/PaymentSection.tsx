import React, { useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Modal,
  ScrollView,
  TextInput,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { PaymentMethod } from '@/stores/orderStore';
import { useProfileStore } from '@/stores/profileStore';
import Toast from 'react-native-toast-message';

interface PaymentSectionProps {
  selectedPayment: PaymentMethod | null;
  onSelectPayment: (payment: PaymentMethod) => void;
}

export function PaymentSection({
  selectedPayment,
  onSelectPayment,
}: PaymentSectionProps) {
  const { paymentMethods, addPaymentMethod } = useProfileStore();
  const [showModal, setShowModal] = useState(false);
  const [addingNew, setAddingNew] = useState(false);
  const [loading, setLoading] = useState(false);

  // If no payment selected and no methods available, show add button
  if (!selectedPayment && paymentMethods.length === 0) {
    return (
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Payment Method</Text>
        <TouchableOpacity
          style={styles.addButton}
          onPress={() => {
            setAddingNew(true);
            setShowModal(true);
          }}
        >
          <Ionicons name="card-outline" size={20} color="#27AE60" />
          <Text style={styles.addButtonText}>Add Payment Method</Text>
        </TouchableOpacity>
      </View>
    );
  }

  const getPaymentIcon = (type: string) => {
    switch (type) {
      case 'card':
        return 'card';
      case 'cash':
        return 'cash';
      case 'etransfer':
        return 'send';
      default:
        return 'card';
    }
  };

  const getCardBrandIcon = (brand?: string) => {
    switch (brand?.toLowerCase()) {
      case 'visa':
        return 'V';
      case 'mastercard':
        return 'M';
      case 'amex':
        return 'A';
      default:
        return null;
    }
  };

  const formatPaymentMethod = (payment: PaymentMethod) => {
    if (payment.type === 'card' && payment.last4) {
      return `•••• ${payment.last4}`;
    }
    if (payment.type === 'cash') {
      return 'Cash on Delivery';
    }
    if (payment.type === 'etransfer') {
      return 'E-Transfer';
    }
    return 'Payment Method';
  };

  const handleAddCard = async () => {
    // In production, this would integrate with a payment provider SDK
    Alert.alert(
      'Add Payment Method',
      'Card payment integration will be available soon. For now, please select Cash on Delivery.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Use Cash',
          onPress: async () => {
            try {
              setLoading(true);
              const cashMethod = await addPaymentMethod({
                type: 'cash',
                is_default: paymentMethods.length === 0,
              });
              onSelectPayment(cashMethod);
              setShowModal(false);
              setAddingNew(false);
            } catch (error) {
              // Error handled in store
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
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Payment Method</Text>

        {selectedPayment ? (
          <TouchableOpacity
            style={styles.paymentCard}
            onPress={() => setShowModal(true)}
          >
            <View style={styles.paymentContent}>
              <Ionicons
                name={getPaymentIcon(selectedPayment.type)}
                size={20}
                color="#27AE60"
              />
              <View style={styles.paymentDetails}>
                <Text style={styles.paymentText}>
                  {formatPaymentMethod(selectedPayment)}
                </Text>
                {selectedPayment.card_brand && (
                  <View style={styles.cardBrand}>
                    <Text style={styles.cardBrandText}>
                      {getCardBrandIcon(selectedPayment.card_brand)}
                    </Text>
                  </View>
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
            <Ionicons name="card-outline" size={20} color="#27AE60" />
            <Text style={styles.addButtonText}>Select Payment Method</Text>
          </TouchableOpacity>
        )}

        <View style={styles.securePayment}>
          <Ionicons name="lock-closed" size={14} color="#666" />
          <Text style={styles.securePaymentText}>
            Your payment information is secure and encrypted
          </Text>
        </View>
      </View>

      {/* Payment Selection Modal */}
      <Modal
        visible={showModal}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={() => setShowModal(false)}
      >
        <View style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>
              {addingNew ? 'Add Payment Method' : 'Select Payment Method'}
            </Text>
            <TouchableOpacity
              onPress={() => {
                setShowModal(false);
                setAddingNew(false);
              }}
            >
              <Ionicons name="close" size={24} color="#333" />
            </TouchableOpacity>
          </View>

          <ScrollView style={styles.modalContent}>
            {!addingNew ? (
              <>
                {/* Existing Payment Methods */}
                {paymentMethods.map((payment) => (
                  <TouchableOpacity
                    key={payment.id}
                    style={[
                      styles.paymentOption,
                      selectedPayment?.id === payment.id && styles.paymentOptionSelected,
                    ]}
                    onPress={() => {
                      onSelectPayment(payment);
                      setShowModal(false);
                    }}
                  >
                    <Ionicons
                      name={getPaymentIcon(payment.type)}
                      size={24}
                      color={selectedPayment?.id === payment.id ? '#27AE60' : '#666'}
                    />
                    <View style={styles.paymentOptionContent}>
                      <Text style={styles.paymentOptionText}>
                        {formatPaymentMethod(payment)}
                      </Text>
                      {payment.is_default && (
                        <Text style={styles.defaultBadge}>Default</Text>
                      )}
                    </View>
                    {selectedPayment?.id === payment.id && (
                      <Ionicons name="checkmark-circle" size={24} color="#27AE60" />
                    )}
                  </TouchableOpacity>
                ))}

                {/* Add New Payment Method Button */}
                <TouchableOpacity
                  style={styles.newPaymentButton}
                  onPress={() => setAddingNew(true)}
                >
                  <Ionicons name="add-circle-outline" size={20} color="#27AE60" />
                  <Text style={styles.newPaymentButtonText}>Add Payment Method</Text>
                </TouchableOpacity>
              </>
            ) : (
              /* Payment Method Options */
              <View style={styles.paymentTypes}>
                <TouchableOpacity
                  style={styles.paymentTypeCard}
                  onPress={handleAddCard}
                  disabled={loading}
                >
                  <Ionicons name="card" size={32} color="#27AE60" />
                  <Text style={styles.paymentTypeTitle}>Credit/Debit Card</Text>
                  <Text style={styles.paymentTypeDescription}>
                    Visa, Mastercard, Amex
                  </Text>
                </TouchableOpacity>

                <TouchableOpacity
                  style={styles.paymentTypeCard}
                  onPress={async () => {
                    try {
                      setLoading(true);
                      const cashMethod = await addPaymentMethod({
                        type: 'cash',
                        is_default: paymentMethods.length === 0,
                      });
                      onSelectPayment(cashMethod);
                      setShowModal(false);
                      setAddingNew(false);
                    } catch (error) {
                      // Error handled in store
                    } finally {
                      setLoading(false);
                    }
                  }}
                  disabled={loading}
                >
                  <Ionicons name="cash" size={32} color="#27AE60" />
                  <Text style={styles.paymentTypeTitle}>Cash on Delivery</Text>
                  <Text style={styles.paymentTypeDescription}>
                    Pay when you receive your order
                  </Text>
                </TouchableOpacity>

                <TouchableOpacity
                  style={[styles.paymentTypeCard, styles.paymentTypeDisabled]}
                  disabled
                >
                  <Ionicons name="send" size={32} color="#CCC" />
                  <Text style={[styles.paymentTypeTitle, styles.textDisabled]}>
                    E-Transfer
                  </Text>
                  <Text style={[styles.paymentTypeDescription, styles.textDisabled]}>
                    Coming soon
                  </Text>
                </TouchableOpacity>
              </View>
            )}
          </ScrollView>

          {loading && (
            <View style={styles.loadingOverlay}>
              <ActivityIndicator size="large" color="#27AE60" />
            </View>
          )}
        </View>
      </Modal>
    </>
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
  paymentCard: {
    backgroundColor: '#F8F9FA',
    borderRadius: 12,
    padding: 12,
  },
  paymentContent: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  paymentDetails: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  paymentText: {
    fontSize: 14,
    color: '#333',
  },
  cardBrand: {
    backgroundColor: '#27AE60',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  cardBrandText: {
    fontSize: 10,
    color: '#FFF',
    fontWeight: 'bold',
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
  securePayment: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 8,
    gap: 4,
  },
  securePaymentText: {
    fontSize: 12,
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
  paymentOption: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#F8F9FA',
    borderRadius: 8,
    marginBottom: 8,
    gap: 12,
  },
  paymentOptionSelected: {
    backgroundColor: '#F0FFF4',
    borderWidth: 1,
    borderColor: '#27AE60',
  },
  paymentOptionContent: {
    flex: 1,
  },
  paymentOptionText: {
    fontSize: 14,
    color: '#333',
  },
  defaultBadge: {
    fontSize: 11,
    color: '#27AE60',
    marginTop: 2,
  },
  newPaymentButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
    backgroundColor: '#F0FFF4',
    borderRadius: 8,
    marginTop: 8,
    gap: 8,
  },
  newPaymentButtonText: {
    fontSize: 14,
    color: '#27AE60',
    fontWeight: '500',
  },
  paymentTypes: {
    gap: 12,
  },
  paymentTypeCard: {
    alignItems: 'center',
    padding: 20,
    backgroundColor: '#F8F9FA',
    borderRadius: 12,
    gap: 8,
  },
  paymentTypeDisabled: {
    opacity: 0.5,
  },
  paymentTypeTitle: {
    fontSize: 16,
    fontWeight: '500',
    color: '#333',
  },
  paymentTypeDescription: {
    fontSize: 12,
    color: '#666',
    textAlign: 'center',
  },
  textDisabled: {
    color: '#CCC',
  },
  loadingOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(255,255,255,0.9)',
    alignItems: 'center',
    justifyContent: 'center',
  },
});