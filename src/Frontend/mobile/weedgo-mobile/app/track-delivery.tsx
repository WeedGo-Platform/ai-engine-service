/**
 * Delivery Tracking Screen
 * Real-time tracking of delivery with map view and status updates
 */

import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Animated,
} from 'react-native';
import { useLocalSearchParams, router } from 'expo-router';
import MapView, { Marker, Polyline, PROVIDER_GOOGLE } from 'react-native-maps';
import { Ionicons } from '@expo/vector-icons';
import deliveryTrackingService, {
  DeliveryUpdate,
  DeliveryLocation,
} from '@/services/delivery/trackingService';

// Delivery status configuration
const DELIVERY_STATUSES = [
  { key: 'pending', label: 'Order Received', icon: 'receipt-outline' },
  { key: 'preparing', label: 'Preparing Order', icon: 'timer-outline' },
  { key: 'ready_for_pickup', label: 'Ready for Pickup', icon: 'checkmark-circle-outline' },
  { key: 'picked_up', label: 'Picked Up', icon: 'car-outline' },
  { key: 'en_route', label: 'On the Way', icon: 'navigate-outline' },
  { key: 'arrived', label: 'Driver Arrived', icon: 'location-outline' },
  { key: 'completed', label: 'Delivered', icon: 'checkmark-done-outline' },
];

export default function TrackDeliveryScreen() {
  const { deliveryId, orderId } = useLocalSearchParams();
  const [connected, setConnected] = useState(false);
  const [currentStatus, setCurrentStatus] = useState('pending');
  const [driverLocation, setDriverLocation] = useState<DeliveryLocation | null>(null);
  const [estimatedTime, setEstimatedTime] = useState<string | null>(null);
  const [deliveryAddress, setDeliveryAddress] = useState<any>(null);
  const mapRef = useRef<MapView>(null);
  const pulseAnim = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    if (!deliveryId) {
      console.error('[TrackDelivery] No delivery ID provided');
      return;
    }

    // Connect to tracking service
    deliveryTrackingService.connect(deliveryId as string);

    // Subscribe to updates
    const unsubscribe = deliveryTrackingService.subscribe(handleDeliveryUpdate);
    const unsubscribeStatus = deliveryTrackingService.subscribeToConnectionStatus(setConnected);

    // Start pulse animation
    startPulseAnimation();

    return () => {
      unsubscribe();
      unsubscribeStatus();
      deliveryTrackingService.disconnect();
    };
  }, [deliveryId]);

  const startPulseAnimation = () => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, {
          toValue: 1.2,
          duration: 1000,
          useNativeDriver: true,
        }),
        Animated.timing(pulseAnim, {
          toValue: 1,
          duration: 1000,
          useNativeDriver: true,
        }),
      ])
    ).start();
  };

  const handleDeliveryUpdate = (update: DeliveryUpdate) => {
    console.log('[TrackDelivery] Received update:', update);

    switch (update.type) {
      case 'initial_status':
        if (update.status) {
          setCurrentStatus(update.status);
        }
        if (update.estimated_time) {
          setEstimatedTime(update.estimated_time);
        }
        break;

      case 'status_change':
        if (update.status) {
          setCurrentStatus(update.status);
        }
        break;

      case 'current_location':
      case 'location_update':
        if (update.location) {
          setDriverLocation(update.location);
          // Center map on driver
          if (mapRef.current) {
            mapRef.current.animateToRegion({
              latitude: update.location.latitude,
              longitude: update.location.longitude,
              latitudeDelta: 0.02,
              longitudeDelta: 0.02,
            });
          }
        }
        break;

      case 'eta_update':
        if (update.eta) {
          setEstimatedTime(update.eta);
        }
        break;
    }
  };

  const getCurrentStatusIndex = (): number => {
    return DELIVERY_STATUSES.findIndex(s => s.key === currentStatus);
  };

  const formatETA = (eta: string | null): string => {
    if (!eta) return 'Calculating...';

    try {
      const etaDate = new Date(eta);
      const now = new Date();
      const diffMinutes = Math.round((etaDate.getTime() - now.getTime()) / 60000);

      if (diffMinutes < 0) return 'Any moment now';
      if (diffMinutes < 60) return `${diffMinutes} minutes`;

      const hours = Math.floor(diffMinutes / 60);
      const minutes = diffMinutes % 60;
      return `${hours}h ${minutes}m`;
    } catch {
      return eta;
    }
  };

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
          <Ionicons name="arrow-back" size={24} color="#000" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Track Delivery</Text>
        <View style={styles.connectionIndicator}>
          <View
            style={[
              styles.connectionDot,
              { backgroundColor: connected ? '#4CAF50' : '#FF5722' },
            ]}
          />
        </View>
      </View>

      {/* Map View */}
      <View style={styles.mapContainer}>
        {driverLocation ? (
          <MapView
            ref={mapRef}
            provider={PROVIDER_GOOGLE}
            style={styles.map}
            initialRegion={{
              latitude: driverLocation.latitude,
              longitude: driverLocation.longitude,
              latitudeDelta: 0.05,
              longitudeDelta: 0.05,
            }}
            showsUserLocation
            showsMyLocationButton
          >
            {/* Driver Location Marker */}
            <Marker
              coordinate={{
                latitude: driverLocation.latitude,
                longitude: driverLocation.longitude,
              }}
              title="Driver Location"
              description="Your delivery is on its way"
            >
              <Animated.View
                style={[
                  styles.driverMarker,
                  { transform: [{ scale: pulseAnim }] },
                ]}
              >
                <Ionicons name="car" size={24} color="#FFF" />
              </Animated.View>
            </Marker>

            {/* Delivery Address Marker */}
            {deliveryAddress && (
              <Marker
                coordinate={{
                  latitude: deliveryAddress.latitude,
                  longitude: deliveryAddress.longitude,
                }}
                title="Delivery Address"
                description={deliveryAddress.street}
                pinColor="#4CAF50"
              />
            )}
          </MapView>
        ) : (
          <View style={styles.mapPlaceholder}>
            <ActivityIndicator size="large" color="#4CAF50" />
            <Text style={styles.mapPlaceholderText}>Loading map...</Text>
          </View>
        )}
      </View>

      {/* ETA Card */}
      <View style={styles.etaCard}>
        <View style={styles.etaIcon}>
          <Ionicons name="time-outline" size={32} color="#4CAF50" />
        </View>
        <View style={styles.etaInfo}>
          <Text style={styles.etaLabel}>Estimated Arrival</Text>
          <Text style={styles.etaTime}>{formatETA(estimatedTime)}</Text>
        </View>
      </View>

      {/* Status Timeline */}
      <ScrollView style={styles.timelineContainer}>
        <Text style={styles.timelineTitle}>Delivery Status</Text>

        {DELIVERY_STATUSES.map((status, index) => {
          const currentIndex = getCurrentStatusIndex();
          const isCompleted = index <= currentIndex;
          const isCurrent = index === currentIndex;

          return (
            <View key={status.key} style={styles.timelineItem}>
              <View style={styles.timelineIconContainer}>
                <View
                  style={[
                    styles.timelineIcon,
                    isCompleted && styles.timelineIconCompleted,
                    isCurrent && styles.timelineIconCurrent,
                  ]}
                >
                  <Ionicons
                    name={status.icon as any}
                    size={20}
                    color={isCompleted ? '#FFF' : '#999'}
                  />
                </View>
                {index < DELIVERY_STATUSES.length - 1 && (
                  <View
                    style={[
                      styles.timelineLine,
                      isCompleted && styles.timelineLineCompleted,
                    ]}
                  />
                )}
              </View>

              <View style={styles.timelineContent}>
                <Text
                  style={[
                    styles.timelineLabel,
                    isCurrent && styles.timelineLabelCurrent,
                    isCompleted && styles.timelineLabelCompleted,
                  ]}
                >
                  {status.label}
                </Text>
                {isCurrent && (
                  <Text style={styles.timelineSubtext}>In progress...</Text>
                )}
              </View>
            </View>
          );
        })}
      </ScrollView>

      {/* Contact Driver Button */}
      {currentStatus === 'en_route' && (
        <TouchableOpacity style={styles.contactButton}>
          <Ionicons name="call-outline" size={20} color="#FFF" />
          <Text style={styles.contactButtonText}>Contact Driver</Text>
        </TouchableOpacity>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: 60,
    paddingBottom: 15,
    paddingHorizontal: 16,
    backgroundColor: '#FFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E0E0E0',
  },
  backButton: {
    padding: 8,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#000',
  },
  connectionIndicator: {
    padding: 8,
  },
  connectionDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
  },
  mapContainer: {
    height: 300,
    backgroundColor: '#E0E0E0',
  },
  map: {
    flex: 1,
  },
  mapPlaceholder: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  mapPlaceholderText: {
    marginTop: 16,
    fontSize: 14,
    color: '#666',
  },
  driverMarker: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: '#4CAF50',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 3,
    borderColor: '#FFF',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.3,
    shadowRadius: 4,
    elevation: 5,
  },
  etaCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFF',
    margin: 16,
    padding: 16,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  etaIcon: {
    marginRight: 16,
  },
  etaInfo: {
    flex: 1,
  },
  etaLabel: {
    fontSize: 14,
    color: '#666',
    marginBottom: 4,
  },
  etaTime: {
    fontSize: 24,
    fontWeight: '700',
    color: '#000',
  },
  timelineContainer: {
    flex: 1,
    backgroundColor: '#FFF',
    marginHorizontal: 16,
    marginBottom: 16,
    borderRadius: 12,
    padding: 16,
  },
  timelineTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#000',
    marginBottom: 20,
  },
  timelineItem: {
    flexDirection: 'row',
    marginBottom: 8,
  },
  timelineIconContainer: {
    alignItems: 'center',
    marginRight: 16,
  },
  timelineIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#F5F5F5',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: '#E0E0E0',
  },
  timelineIconCompleted: {
    backgroundColor: '#4CAF50',
    borderColor: '#4CAF50',
  },
  timelineIconCurrent: {
    backgroundColor: '#2196F3',
    borderColor: '#2196F3',
  },
  timelineLine: {
    width: 2,
    flex: 1,
    backgroundColor: '#E0E0E0',
    marginTop: 4,
  },
  timelineLineCompleted: {
    backgroundColor: '#4CAF50',
  },
  timelineContent: {
    flex: 1,
    paddingTop: 8,
  },
  timelineLabel: {
    fontSize: 16,
    color: '#666',
  },
  timelineLabelCurrent: {
    fontWeight: '600',
    color: '#2196F3',
  },
  timelineLabelCompleted: {
    color: '#000',
  },
  timelineSubtext: {
    fontSize: 12,
    color: '#2196F3',
    marginTop: 4,
  },
  contactButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#4CAF50',
    margin: 16,
    padding: 16,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  contactButtonText: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
});
