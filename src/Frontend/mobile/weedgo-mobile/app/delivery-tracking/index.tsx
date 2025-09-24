import React, { useEffect, useState, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Dimensions,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { Colors, BorderRadius, Shadows, Gradients } from '@/constants/Colors';
import { LinearGradient } from 'expo-linear-gradient';
import MapView, { Marker, Polyline, PROVIDER_GOOGLE } from 'react-native-maps';
import { ordersService } from '@/services/api/orders';

const { width, height } = Dimensions.get('window');

interface DeliveryLocation {
  latitude: number;
  longitude: number;
  heading?: number;
}

interface DeliveryStatus {
  orderId: string;
  status: string;
  driverName?: string;
  driverPhone?: string;
  estimatedTime?: string;
  currentLocation?: DeliveryLocation;
  destinationLocation?: DeliveryLocation;
  route?: DeliveryLocation[];
}

export default function DeliveryTrackingScreen() {
  const router = useRouter();
  const mapRef = useRef<MapView>(null);
  const [activeOrders, setActiveOrders] = useState<any[]>([]);
  const [selectedOrder, setSelectedOrder] = useState<any>(null);
  const [deliveryStatus, setDeliveryStatus] = useState<DeliveryStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [connected, setConnected] = useState(false);
  const isDark = false;
  const theme = isDark ? Colors.dark : Colors.light;

  useEffect(() => {
    loadActiveOrders();
    connectToDeliverySocket();

    return () => {
      disconnectFromDeliverySocket();
    };
  }, []);

  const loadActiveOrders = async () => {
    try {
      const response = await ordersService.getOrders();
      const active = response.data?.filter((order: any) =>
        ['processing', 'confirmed', 'out_for_delivery'].includes(order.status?.toLowerCase())
      ) || [];
      setActiveOrders(active);
      if (active.length > 0 && !selectedOrder) {
        setSelectedOrder(active[0]);
      }
    } catch (error) {
      console.error('Failed to load active orders:', error);
    } finally {
      setLoading(false);
    }
  };

  const connectToDeliverySocket = () => {
    // TODO: Implement WebSocket connection when socket service is available
    // const socket = socketService.connect();
    //
    // socket.on('connect', () => {
    //   console.log('Connected to delivery tracking');
    //   setConnected(true);
    //   if (selectedOrder) {
    //     socket.emit('track_delivery', { orderId: selectedOrder.id });
    //   }
    // });
    //
    // socket.on('delivery_update', (data: DeliveryStatus) => {
    //   console.log('Delivery update received:', data);
    //   setDeliveryStatus(data);
    //
    //   // Center map on driver location
    //   if (data.currentLocation && mapRef.current) {
    //     mapRef.current.animateToRegion({
    //       latitude: data.currentLocation.latitude,
    //       longitude: data.currentLocation.longitude,
    //       latitudeDelta: 0.01,
    //       longitudeDelta: 0.01,
    //     }, 1000);
    //   }
    // });

    // socket.on('delivery_completed', (data: any) => {
    //   Alert.alert(
    //     'Delivery Complete!',
    //     'Your order has been delivered. Enjoy!',
    //     [{ text: 'OK', onPress: () => router.back() }]
    //   );
    // });
    //
    // socket.on('disconnect', () => {
    //   console.log('Disconnected from delivery tracking');
    //   setConnected(false);
    // });
  };

  const disconnectFromDeliverySocket = () => {
    // TODO: Implement WebSocket disconnection
    // socketService.disconnect();
  };

  const handleOrderSelect = (order: any) => {
    setSelectedOrder(order);
    // TODO: Emit tracking event when socket is available
    // const socket = socketService.getSocket();
    // if (socket && socket.connected) {
    //   socket.emit('track_delivery', { orderId: order.id });
    // }
  };

  const handleCallDriver = () => {
    if (deliveryStatus?.driverPhone) {
      // In a real app, you would use Linking to make a phone call
      Alert.alert('Call Driver', `Calling ${deliveryStatus.driverPhone}`);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'confirmed':
        return 'checkmark-circle';
      case 'processing':
        return 'restaurant';
      case 'out_for_delivery':
        return 'bicycle';
      case 'delivered':
        return 'home';
      default:
        return 'time';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'delivered':
        return Gradients.hybrid;
      case 'out_for_delivery':
        return Gradients.primary;
      case 'processing':
      case 'confirmed':
        return Gradients.ocean;
      default:
        return ['#B2BEC3', '#95A5A6'];
    }
  };

  if (loading) {
    return (
      <LinearGradient
        colors={[theme.gradientStart, theme.gradientMid, theme.gradientEnd]}
        style={styles.gradientContainer}
        start={{ x: 0, y: 0 }}
        end={{ x: 0.5, y: 1 }}
      >
        <SafeAreaView style={styles.container}>
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color={theme.primary} />
            <Text style={styles.loadingText}>Loading delivery tracking...</Text>
          </View>
        </SafeAreaView>
      </LinearGradient>
    );
  }

  if (activeOrders.length === 0) {
    return (
      <LinearGradient
        colors={[theme.gradientStart, theme.gradientMid, theme.gradientEnd]}
        style={styles.gradientContainer}
        start={{ x: 0, y: 0 }}
        end={{ x: 0.5, y: 1 }}
      >
        <SafeAreaView style={styles.container}>
          <View style={styles.header}>
            <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
              <Ionicons name="arrow-back" size={24} color={theme.text} />
            </TouchableOpacity>
            <Text style={styles.headerTitle}>Delivery Tracking</Text>
            <View style={{ width: 40 }} />
          </View>
          <View style={styles.emptyContainer}>
            <Ionicons name="navigate-outline" size={64} color={theme.textSecondary} />
            <Text style={styles.emptyTitle}>No Active Deliveries</Text>
            <Text style={styles.emptyText}>
              You don't have any orders being delivered right now
            </Text>
            <TouchableOpacity
              style={styles.shopButton}
              onPress={() => router.push('/orders')}
              activeOpacity={0.8}
            >
              <LinearGradient
                colors={Gradients.primary}
                style={styles.shopButtonGradient}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
              >
                <Text style={styles.shopButtonText}>View Order History</Text>
              </LinearGradient>
            </TouchableOpacity>
          </View>
        </SafeAreaView>
      </LinearGradient>
    );
  }

  return (
    <View style={styles.container}>
      <SafeAreaView style={styles.safeArea}>
        <View style={styles.header}>
          <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
            <Ionicons name="arrow-back" size={24} color={theme.text} />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Live Tracking</Text>
          <View style={styles.connectionStatus}>
            <View style={[styles.connectionDot, connected && styles.connectedDot]} />
            <Text style={styles.connectionText}>{connected ? 'Live' : 'Offline'}</Text>
          </View>
        </View>
      </SafeAreaView>

      {/* Map View */}
      <View style={styles.mapContainer}>
        <MapView
          ref={mapRef}
          provider={PROVIDER_GOOGLE}
          style={styles.map}
          initialRegion={{
            latitude: deliveryStatus?.currentLocation?.latitude || 37.78825,
            longitude: deliveryStatus?.currentLocation?.longitude || -122.4324,
            latitudeDelta: 0.0922,
            longitudeDelta: 0.0421,
          }}
        >
          {deliveryStatus?.currentLocation && (
            <Marker
              coordinate={deliveryStatus.currentLocation}
              title="Driver"
              description={deliveryStatus.driverName}
            >
              <View style={styles.driverMarker}>
                <Ionicons name="bicycle" size={24} color="white" />
              </View>
            </Marker>
          )}
          {deliveryStatus?.destinationLocation && (
            <Marker
              coordinate={deliveryStatus.destinationLocation}
              title="Delivery Address"
            >
              <View style={styles.destinationMarker}>
                <Ionicons name="home" size={24} color="white" />
              </View>
            </Marker>
          )}
          {deliveryStatus?.route && deliveryStatus.route.length > 0 && (
            <Polyline
              coordinates={deliveryStatus.route}
              strokeColor={theme.primary}
              strokeWidth={3}
            />
          )}
        </MapView>
      </View>

      {/* Bottom Sheet */}
      <View style={styles.bottomSheet}>
        <LinearGradient
          colors={['rgba(255, 255, 255, 0.98)', 'rgba(250, 250, 255, 0.95)']}
          style={styles.bottomSheetGradient}
          start={{ x: 0, y: 0 }}
          end={{ x: 0, y: 1 }}
        >
          <View style={styles.sheetHandle} />

          {/* Order Selector */}
          {activeOrders.length > 1 && (
            <ScrollView
              horizontal
              showsHorizontalScrollIndicator={false}
              style={styles.orderSelector}
            >
              {activeOrders.map((order) => (
                <TouchableOpacity
                  key={order.id}
                  style={[
                    styles.orderTab,
                    selectedOrder?.id === order.id && styles.orderTabActive,
                  ]}
                  onPress={() => handleOrderSelect(order)}
                >
                  <Text style={[
                    styles.orderTabText,
                    selectedOrder?.id === order.id && styles.orderTabTextActive,
                  ]}>
                    #{order.orderNumber || order.id}
                  </Text>
                </TouchableOpacity>
              ))}
            </ScrollView>
          )}

          {/* Delivery Status */}
          {selectedOrder && (
            <View style={styles.statusContainer}>
              <View style={styles.statusHeader}>
                <LinearGradient
                  colors={getStatusColor(selectedOrder.status)}
                  style={styles.statusBadge}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 1 }}
                >
                  <Ionicons
                    name={getStatusIcon(selectedOrder.status)}
                    size={20}
                    color="white"
                  />
                  <Text style={styles.statusText}>
                    {selectedOrder.status?.replace(/_/g, ' ').toUpperCase()}
                  </Text>
                </LinearGradient>
                {deliveryStatus?.estimatedTime && (
                  <View style={styles.etaContainer}>
                    <Text style={styles.etaLabel}>ETA</Text>
                    <Text style={styles.etaTime}>{deliveryStatus.estimatedTime}</Text>
                  </View>
                )}
              </View>

              {deliveryStatus?.driverName && (
                <View style={styles.driverInfo}>
                  <View style={styles.driverAvatar}>
                    <Ionicons name="person-circle" size={48} color={theme.primary} />
                  </View>
                  <View style={styles.driverDetails}>
                    <Text style={styles.driverLabel}>Your Driver</Text>
                    <Text style={styles.driverName}>{deliveryStatus.driverName}</Text>
                    {deliveryStatus.driverPhone && (
                      <Text style={styles.driverPhone}>{deliveryStatus.driverPhone}</Text>
                    )}
                  </View>
                  <TouchableOpacity
                    style={styles.callButton}
                    onPress={handleCallDriver}
                  >
                    <LinearGradient
                      colors={Gradients.primary}
                      style={styles.callButtonGradient}
                      start={{ x: 0, y: 0 }}
                      end={{ x: 1, y: 1 }}
                    >
                      <Ionicons name="call" size={20} color="white" />
                    </LinearGradient>
                  </TouchableOpacity>
                </View>
              )}

              {/* Order Details */}
              <View style={styles.orderDetails}>
                <Text style={styles.orderNumber}>
                  Order #{selectedOrder.orderNumber || selectedOrder.id}
                </Text>
                <View style={styles.detailRow}>
                  <Ionicons name="location-outline" size={16} color={theme.textSecondary} />
                  <Text style={styles.detailText} numberOfLines={2}>
                    {selectedOrder.deliveryAddress?.street || 'Delivery Address'}
                  </Text>
                </View>
                <View style={styles.detailRow}>
                  <Ionicons name="basket-outline" size={16} color={theme.textSecondary} />
                  <Text style={styles.detailText}>
                    {selectedOrder.items?.length || 0} items • ${selectedOrder.total || '0.00'}
                  </Text>
                </View>
              </View>
            </View>
          )}
        </LinearGradient>
      </View>
    </View>
  );
}

const isDark = false;
const theme = isDark ? Colors.dark : Colors.light;

const styles = StyleSheet.create({
  gradientContainer: {
    flex: 1,
  },
  container: {
    flex: 1,
    backgroundColor: theme.background,
  },
  safeArea: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    zIndex: 10,
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  backButton: {
    width: 40,
    height: 40,
    justifyContent: 'center',
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: theme.text,
  },
  connectionStatus: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  connectionDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: theme.error,
  },
  connectedDot: {
    backgroundColor: theme.success,
  },
  connectionText: {
    fontSize: 12,
    color: theme.textSecondary,
    fontWeight: '600',
  },
  mapContainer: {
    flex: 1,
  },
  map: {
    ...StyleSheet.absoluteFillObject,
  },
  driverMarker: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: theme.primary,
    justifyContent: 'center',
    alignItems: 'center',
    ...Shadows.medium,
  },
  destinationMarker: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: theme.success,
    justifyContent: 'center',
    alignItems: 'center',
    ...Shadows.medium,
  },
  bottomSheet: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    borderTopLeftRadius: BorderRadius.xxl,
    borderTopRightRadius: BorderRadius.xxl,
    overflow: 'hidden',
    ...Shadows.large,
  },
  bottomSheetGradient: {
    paddingBottom: 34,
  },
  sheetHandle: {
    width: 40,
    height: 4,
    backgroundColor: theme.border,
    borderRadius: 2,
    alignSelf: 'center',
    marginTop: 8,
    marginBottom: 16,
  },
  orderSelector: {
    paddingHorizontal: 16,
    marginBottom: 16,
    maxHeight: 40,
  },
  orderTab: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: BorderRadius.full,
    backgroundColor: theme.surface,
    marginRight: 8,
    borderWidth: 1,
    borderColor: theme.border,
  },
  orderTabActive: {
    backgroundColor: theme.primary,
    borderColor: theme.primary,
  },
  orderTabText: {
    fontSize: 14,
    fontWeight: '600',
    color: theme.textSecondary,
  },
  orderTabTextActive: {
    color: 'white',
  },
  statusContainer: {
    paddingHorizontal: 16,
  },
  statusHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: BorderRadius.full,
    borderWidth: 1.5,
    borderColor: 'rgba(255, 255, 255, 0.5)',
  },
  statusText: {
    fontSize: 14,
    fontWeight: '700',
    color: 'white',
    letterSpacing: 0.5,
  },
  etaContainer: {
    alignItems: 'flex-end',
  },
  etaLabel: {
    fontSize: 12,
    color: theme.textSecondary,
  },
  etaTime: {
    fontSize: 18,
    fontWeight: '700',
    color: theme.text,
  },
  driverInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    backgroundColor: theme.surface,
    borderRadius: BorderRadius.xl,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: theme.border,
  },
  driverAvatar: {
    marginRight: 12,
  },
  driverDetails: {
    flex: 1,
  },
  driverLabel: {
    fontSize: 12,
    color: theme.textSecondary,
  },
  driverName: {
    fontSize: 16,
    fontWeight: '600',
    color: theme.text,
  },
  driverPhone: {
    fontSize: 13,
    color: theme.textSecondary,
  },
  callButton: {
    borderRadius: BorderRadius.full,
    overflow: 'hidden',
    ...Shadows.small,
  },
  callButtonGradient: {
    width: 48,
    height: 48,
    justifyContent: 'center',
    alignItems: 'center',
  },
  orderDetails: {
    paddingVertical: 16,
  },
  orderNumber: {
    fontSize: 16,
    fontWeight: '700',
    color: theme.text,
    marginBottom: 8,
  },
  detailRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 6,
  },
  detailText: {
    fontSize: 14,
    color: theme.textSecondary,
    flex: 1,
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
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 32,
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: theme.text,
    marginTop: 16,
  },
  emptyText: {
    fontSize: 14,
    color: theme.textSecondary,
    textAlign: 'center',
    marginTop: 8,
    marginBottom: 24,
  },
  shopButton: {
    borderRadius: BorderRadius.xl,
    overflow: 'hidden',
    ...Shadows.medium,
  },
  shopButtonGradient: {
    paddingHorizontal: 24,
    paddingVertical: 12,
  },
  shopButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
});