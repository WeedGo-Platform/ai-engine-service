import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
  TextInput,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Stack, useLocalSearchParams, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { Colors } from '@/constants/Colors';
import { orderTrackingService, OrderUpdate, OrderStatus } from '@/services/orderTracking';
import * as Haptics from 'expo-haptics';

interface StatusStep {
  status: OrderStatus;
  label: string;
  icon: keyof typeof Ionicons.glyphMap;
  description: string;
}

const statusSteps: StatusStep[] = [
  {
    status: 'confirmed',
    label: 'Order Confirmed',
    icon: 'checkmark-circle',
    description: 'Your order has been received',
  },
  {
    status: 'preparing',
    label: 'Preparing',
    icon: 'time',
    description: 'Your order is being prepared',
  },
  {
    status: 'ready_for_pickup',
    label: 'Ready',
    icon: 'bag-check',
    description: 'Ready for pickup/delivery',
  },
  {
    status: 'out_for_delivery',
    label: 'On the Way',
    icon: 'bicycle',
    description: 'Your order is on its way',
  },
  {
    status: 'delivered',
    label: 'Delivered',
    icon: 'checkmark-done-circle',
    description: 'Order completed',
  },
];

export default function OrderTrackingScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const [currentStatus, setCurrentStatus] = useState<OrderUpdate | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [deliveryInstructions, setDeliveryInstructions] = useState('');
  const [showInstructionsInput, setShowInstructionsInput] = useState(false);
  const [sendingInstructions, setSendingInstructions] = useState(false);

  useEffect(() => {
    if (!id) return;

    // Connect to tracking service
    orderTrackingService.connect();

    // Subscribe to order updates
    const unsubscribe = orderTrackingService.trackOrder(id, handleOrderUpdate);

    // Load initial status
    loadOrderStatus();

    return () => {
      unsubscribe();
    };
  }, [id]);

  const handleOrderUpdate = (update: OrderUpdate) => {
    console.log('Order update received:', update);
    setCurrentStatus(update);

    // Haptic feedback for status changes
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);

    // Show notification for important updates
    if (update.status === 'out_for_delivery' || update.status === 'delivered') {
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    }
  };

  const loadOrderStatus = async () => {
    if (!id) return;

    setLoading(true);
    const status = await orderTrackingService.getOrderStatus(id);
    if (status) {
      setCurrentStatus(status);
    }
    setLoading(false);
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadOrderStatus();
    setRefreshing(false);
  };

  const handleSendInstructions = async () => {
    if (!id || !deliveryInstructions.trim()) return;

    setSendingInstructions(true);
    const success = await orderTrackingService.sendDeliveryInstructions(id, deliveryInstructions);

    if (success) {
      setDeliveryInstructions('');
      setShowInstructionsInput(false);
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    }
    setSendingInstructions(false);
  };

  const getStatusIndex = (status: OrderStatus): number => {
    const index = statusSteps.findIndex(s => s.status === status);
    return index >= 0 ? index : -1;
  };

  const renderStatusSteps = () => {
    const currentIndex = getStatusIndex(currentStatus?.status || 'pending');

    return (
      <View style={styles.stepsContainer}>
        {statusSteps.map((step, index) => {
          const isCompleted = index <= currentIndex;
          const isCurrent = index === currentIndex;

          return (
            <View key={step.status} style={styles.stepWrapper}>
              <View style={styles.stepContent}>
                <View
                  style={[
                    styles.stepIcon,
                    isCompleted && styles.stepIconCompleted,
                    isCurrent && styles.stepIconCurrent,
                  ]}
                >
                  <Ionicons
                    name={step.icon}
                    size={24}
                    color={isCompleted ? 'white' : Colors.light.gray}
                  />
                </View>
                <View style={styles.stepInfo}>
                  <Text
                    style={[
                      styles.stepLabel,
                      isCompleted && styles.stepLabelCompleted,
                    ]}
                  >
                    {step.label}
                  </Text>
                  <Text style={styles.stepDescription}>
                    {isCurrent && currentStatus?.message
                      ? currentStatus.message
                      : step.description}
                  </Text>
                  {isCurrent && currentStatus?.timestamp && (
                    <Text style={styles.stepTime}>
                      {new Date(currentStatus.timestamp).toLocaleTimeString()}
                    </Text>
                  )}
                </View>
              </View>
              {index < statusSteps.length - 1 && (
                <View
                  style={[
                    styles.stepLine,
                    isCompleted && styles.stepLineCompleted,
                  ]}
                />
              )}
            </View>
          );
        })}
      </View>
    );
  };

  const renderDeliveryInfo = () => {
    if (currentStatus?.status !== 'out_for_delivery') return null;

    return (
      <View style={styles.deliveryCard}>
        <View style={styles.deliveryHeader}>
          <Ionicons name="bicycle" size={24} color={Colors.light.primary} />
          <Text style={styles.deliveryTitle}>Delivery in Progress</Text>
        </View>

        {currentStatus.estimatedTime && (
          <View style={styles.infoRow}>
            <Ionicons name="time-outline" size={20} color={Colors.light.gray} />
            <Text style={styles.infoText}>
              Estimated arrival: {currentStatus.estimatedTime}
            </Text>
          </View>
        )}

        {currentStatus.driverLocation && (
          <TouchableOpacity style={styles.mapButton}>
            <Ionicons name="map-outline" size={20} color={Colors.light.primary} />
            <Text style={styles.mapButtonText}>Track on Map</Text>
          </TouchableOpacity>
        )}

        {!showInstructionsInput ? (
          <TouchableOpacity
            style={styles.instructionsButton}
            onPress={() => setShowInstructionsInput(true)}
          >
            <Ionicons name="chatbubble-outline" size={20} color={Colors.light.text} />
            <Text style={styles.instructionsButtonText}>
              Add Delivery Instructions
            </Text>
          </TouchableOpacity>
        ) : (
          <View style={styles.instructionsInput}>
            <TextInput
              style={styles.textInput}
              placeholder="e.g., Leave at door, ring bell..."
              value={deliveryInstructions}
              onChangeText={setDeliveryInstructions}
              multiline
              maxLength={200}
            />
            <View style={styles.instructionsActions}>
              <TouchableOpacity
                onPress={() => setShowInstructionsInput(false)}
                style={styles.cancelButton}
              >
                <Text style={styles.cancelButtonText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                onPress={handleSendInstructions}
                style={styles.sendButton}
                disabled={!deliveryInstructions.trim() || sendingInstructions}
              >
                {sendingInstructions ? (
                  <ActivityIndicator size="small" color="white" />
                ) : (
                  <Text style={styles.sendButtonText}>Send</Text>
                )}
              </TouchableOpacity>
            </View>
          </View>
        )}
      </View>
    );
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={Colors.light.primary} />
        </View>
      </SafeAreaView>
    );
  }

  return (
    <>
      <Stack.Screen
        options={{
          title: `Order #${id?.slice(-6).toUpperCase()}`,
          headerShown: true,
        }}
      />

      <SafeAreaView style={styles.container} edges={['bottom']}>
        <KeyboardAvoidingView
          style={styles.container}
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        >
          <ScrollView
            style={styles.scrollView}
            contentContainerStyle={styles.scrollContent}
            refreshControl={
              <RefreshControl
                refreshing={refreshing}
                onRefresh={handleRefresh}
                tintColor={Colors.light.primary}
              />
            }
            showsVerticalScrollIndicator={false}
          >
            {/* Status Timeline */}
            {renderStatusSteps()}

            {/* Delivery Info */}
            {renderDeliveryInfo()}

            {/* Order Complete Actions */}
            {currentStatus?.status === 'delivered' && (
              <View style={styles.completeCard}>
                <Ionicons
                  name="checkmark-done-circle"
                  size={48}
                  color={Colors.light.success}
                />
                <Text style={styles.completeTitle}>Order Delivered!</Text>
                <Text style={styles.completeSubtitle}>
                  Thank you for your order
                </Text>
                <TouchableOpacity style={styles.rateButton}>
                  <Ionicons name="star-outline" size={20} color="white" />
                  <Text style={styles.rateButtonText}>Rate Delivery</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={styles.reorderButton}
                  onPress={() => router.push('/(tabs)/')}
                >
                  <Text style={styles.reorderButtonText}>Order Again</Text>
                </TouchableOpacity>
              </View>
            )}

            {/* Cancelled Order */}
            {currentStatus?.status === 'cancelled' && (
              <View style={styles.cancelledCard}>
                <Ionicons
                  name="close-circle"
                  size={48}
                  color={Colors.light.error}
                />
                <Text style={styles.cancelledTitle}>Order Cancelled</Text>
                <Text style={styles.cancelledSubtitle}>
                  {currentStatus.message || 'Your order has been cancelled'}
                </Text>
                <TouchableOpacity
                  style={styles.browseButton}
                  onPress={() => router.push('/(tabs)/')}
                >
                  <Text style={styles.browseButtonText}>Browse Products</Text>
                </TouchableOpacity>
              </View>
            )}
          </ScrollView>
        </KeyboardAvoidingView>
      </SafeAreaView>
    </>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.light.background,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 16,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  stepsContainer: {
    backgroundColor: Colors.light.card,
    borderRadius: 12,
    padding: 20,
    marginBottom: 16,
  },
  stepWrapper: {
    marginBottom: 8,
  },
  stepContent: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  stepIcon: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: Colors.light.inputBackground,
    justifyContent: 'center',
    alignItems: 'center',
  },
  stepIconCompleted: {
    backgroundColor: Colors.light.primary,
  },
  stepIconCurrent: {
    backgroundColor: Colors.light.primary,
    shadowColor: Colors.light.primary,
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 4,
  },
  stepInfo: {
    flex: 1,
    marginLeft: 12,
  },
  stepLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.light.gray,
    marginBottom: 4,
  },
  stepLabelCompleted: {
    color: Colors.light.text,
  },
  stepDescription: {
    fontSize: 14,
    color: Colors.light.gray,
  },
  stepTime: {
    fontSize: 12,
    color: Colors.light.primary,
    marginTop: 4,
  },
  stepLine: {
    width: 2,
    height: 24,
    backgroundColor: Colors.light.border,
    marginLeft: 23,
    marginTop: 4,
  },
  stepLineCompleted: {
    backgroundColor: Colors.light.primary,
  },
  deliveryCard: {
    backgroundColor: Colors.light.card,
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
  },
  deliveryHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  deliveryTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: Colors.light.text,
    marginLeft: 8,
  },
  infoRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  infoText: {
    fontSize: 14,
    color: Colors.light.text,
    marginLeft: 8,
  },
  mapButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: Colors.light.primary + '10',
    padding: 12,
    borderRadius: 8,
    marginBottom: 12,
  },
  mapButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.light.primary,
    marginLeft: 8,
  },
  instructionsButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: Colors.light.inputBackground,
    padding: 12,
    borderRadius: 8,
  },
  instructionsButtonText: {
    fontSize: 14,
    color: Colors.light.text,
    marginLeft: 8,
  },
  instructionsInput: {
    marginTop: 12,
  },
  textInput: {
    backgroundColor: Colors.light.inputBackground,
    borderRadius: 8,
    padding: 12,
    minHeight: 80,
    fontSize: 14,
    color: Colors.light.text,
  },
  instructionsActions: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    gap: 8,
    marginTop: 8,
  },
  cancelButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  cancelButtonText: {
    fontSize: 14,
    color: Colors.light.gray,
  },
  sendButton: {
    backgroundColor: Colors.light.primary,
    paddingHorizontal: 20,
    paddingVertical: 8,
    borderRadius: 8,
    minWidth: 60,
    alignItems: 'center',
  },
  sendButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: 'white',
  },
  completeCard: {
    backgroundColor: Colors.light.card,
    borderRadius: 12,
    padding: 24,
    alignItems: 'center',
  },
  completeTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: Colors.light.text,
    marginTop: 12,
    marginBottom: 8,
  },
  completeSubtitle: {
    fontSize: 14,
    color: Colors.light.gray,
    marginBottom: 24,
  },
  rateButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.light.primary,
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 24,
    marginBottom: 12,
  },
  rateButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: 'white',
    marginLeft: 8,
  },
  reorderButton: {
    paddingHorizontal: 24,
    paddingVertical: 12,
  },
  reorderButtonText: {
    fontSize: 16,
    color: Colors.light.primary,
  },
  cancelledCard: {
    backgroundColor: Colors.light.card,
    borderRadius: 12,
    padding: 24,
    alignItems: 'center',
  },
  cancelledTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: Colors.light.text,
    marginTop: 12,
    marginBottom: 8,
  },
  cancelledSubtitle: {
    fontSize: 14,
    color: Colors.light.gray,
    marginBottom: 24,
    textAlign: 'center',
  },
  browseButton: {
    backgroundColor: Colors.light.primary,
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 24,
  },
  browseButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: 'white',
  },
});