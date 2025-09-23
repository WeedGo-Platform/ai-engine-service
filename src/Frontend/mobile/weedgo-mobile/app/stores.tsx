import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  Platform,
  Linking,
} from 'react-native';
import * as Location from 'expo-location';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { Colors } from '@/constants/Colors';
import { router } from 'expo-router';
import { storeService } from '@/services/api/stores';
import { Store } from '@/types/api.types';

interface Region {
  latitude: number;
  longitude: number;
  latitudeDelta: number;
  longitudeDelta: number;
}

export default function StoresScreen() {
  const [stores, setStores] = useState<Store[]>([]);
  const [loading, setLoading] = useState(true);
  const [location, setLocation] = useState<Location.LocationObject | null>(null);
  const [region, setRegion] = useState<Region>({
    latitude: 43.6532, // Toronto coordinates as default
    longitude: -79.3832,
    latitudeDelta: 0.0922,
    longitudeDelta: 0.0421,
  });
  const [selectedStore, setSelectedStore] = useState<Store | null>(null);
  const [viewMode, setViewMode] = useState<'map' | 'list'>('list');

  useEffect(() => {
    loadStores();
    requestLocationPermission();
  }, []);

  const requestLocationPermission = async () => {
    try {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Permission needed', 'Please enable location to find stores near you');
        return;
      }

      const currentLocation = await Location.getCurrentPositionAsync({});
      setLocation(currentLocation);
      setRegion({
        latitude: currentLocation.coords.latitude,
        longitude: currentLocation.coords.longitude,
        latitudeDelta: 0.0922,
        longitudeDelta: 0.0421,
      });
    } catch (error) {
      console.error('Error getting location:', error);
    }
  };

  const loadStores = async () => {
    try {
      setLoading(true);
      const response = await storeService.getNearbyStores(
        location?.coords.latitude,
        location?.coords.longitude
      );
      setStores(response);
    } catch (error) {
      console.error('Failed to load stores:', error);
      setStores([]);
    } finally {
      setLoading(false);
    }
  };

  const handleDirections = (store: Store) => {
    const scheme = Platform.select({
      ios: 'maps:',
      android: 'geo:',
    });
    const latLng = `${store.latitude},${store.longitude}`;
    const label = encodeURIComponent(store.name);
    const url = Platform.select({
      ios: `${scheme}${latLng}?q=${label}`,
      android: `${scheme}${latLng}?q=${latLng}(${label})`,
    });

    if (url) {
      Linking.openURL(url);
    }
  };

  const handleCall = (phone: string) => {
    Linking.openURL(`tel:${phone.replace(/\D/g, '')}`);
  };

  const handleStoreSelect = (store: Store) => {
    setSelectedStore(store);
  };

  const renderStoreCard = ({ item }: { item: Store }) => (
    <TouchableOpacity
      style={styles.storeCard}
      onPress={() => handleStoreSelect(item)}
      activeOpacity={0.9}
    >
      <View style={styles.storeInfo}>
        <Text style={styles.storeName}>{item.name}</Text>
        <Text style={styles.storeAddress}>{item.address}</Text>
        <View style={styles.storeDetails}>
          <View style={styles.ratingContainer}>
            <Ionicons name="star" size={14} color={Colors.light.star} />
            <Text style={styles.rating}>{item.rating}</Text>
            <Text style={styles.reviewCount}>({item.reviewCount})</Text>
          </View>
          <Text style={styles.distance}>{item.distance} km away</Text>
        </View>
        <Text style={styles.hours}>{typeof item.hours === 'string' ? item.hours : 'Hours vary'}</Text>
      </View>
      <View style={styles.storeActions}>
        <TouchableOpacity
          style={styles.actionButton}
          onPress={() => handleDirections(item)}
        >
          <Ionicons name="navigate" size={20} color={Colors.light.primary} />
        </TouchableOpacity>
        <TouchableOpacity
          style={styles.actionButton}
          onPress={() => handleCall(item.phone)}
        >
          <Ionicons name="call" size={20} color={Colors.light.primary} />
        </TouchableOpacity>
      </View>
    </TouchableOpacity>
  );


  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={Colors.light.primary} />
        <Text style={styles.loadingText}>Finding nearby stores...</Text>
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()}>
          <Ionicons name="arrow-back" size={24} color={Colors.light.text} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Store Locator</Text>
        <View style={{ width: 24 }} />
      </View>

      {/* List View */}
      <FlatList
        data={stores}
        renderItem={renderStoreCard}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.listContainer}
        showsVerticalScrollIndicator={false}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.light.background,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: 'white',
    borderBottomWidth: 1,
    borderBottomColor: Colors.light.border,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: Colors.light.text,
  },
  viewToggle: {
    flexDirection: 'row',
    backgroundColor: Colors.light.background,
    borderRadius: 20,
    padding: 2,
  },
  toggleButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 18,
  },
  toggleButtonActive: {
    backgroundColor: Colors.light.primary,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 12,
    fontSize: 16,
    color: Colors.light.gray,
  },
  mapContainer: {
    flex: 1,
  },
  map: {
    flex: 1,
  },
  markerContainer: {
    backgroundColor: 'white',
    borderRadius: 20,
    padding: 4,
    borderWidth: 2,
    borderColor: Colors.light.primary,
  },
  calloutContainer: {
    width: 200,
    padding: 12,
  },
  calloutTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.light.text,
    marginBottom: 4,
  },
  calloutAddress: {
    fontSize: 14,
    color: Colors.light.gray,
    marginBottom: 4,
  },
  calloutHours: {
    fontSize: 12,
    color: Colors.light.gray,
    marginBottom: 8,
  },
  calloutButtons: {
    flexDirection: 'row',
    gap: 8,
  },
  calloutButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingVertical: 6,
    paddingHorizontal: 8,
    backgroundColor: Colors.light.primary + '10',
    borderRadius: 8,
  },
  calloutButtonText: {
    fontSize: 12,
    color: Colors.light.primary,
  },
  listContainer: {
    padding: 16,
  },
  storeCard: {
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    flexDirection: 'row',
    justifyContent: 'space-between',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  storeInfo: {
    flex: 1,
  },
  storeName: {
    fontSize: 18,
    fontWeight: '600',
    color: Colors.light.text,
    marginBottom: 4,
  },
  storeAddress: {
    fontSize: 14,
    color: Colors.light.gray,
    marginBottom: 8,
  },
  storeDetails: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 16,
    marginBottom: 4,
  },
  ratingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  rating: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.light.text,
  },
  reviewCount: {
    fontSize: 12,
    color: Colors.light.gray,
  },
  distance: {
    fontSize: 14,
    color: Colors.light.primary,
    fontWeight: '500',
  },
  hours: {
    fontSize: 12,
    color: Colors.light.gray,
  },
  storeActions: {
    justifyContent: 'center',
    gap: 8,
  },
  actionButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: Colors.light.primary + '10',
    justifyContent: 'center',
    alignItems: 'center',
  },
  bottomSheet: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: 'white',
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -2 },
    shadowOpacity: 0.2,
    shadowRadius: 8,
    elevation: 10,
  },
  bottomSheetHandle: {
    width: 40,
    height: 4,
    backgroundColor: Colors.light.border,
    borderRadius: 2,
    alignSelf: 'center',
    marginBottom: 16,
  },
  bottomSheetTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: Colors.light.text,
    marginBottom: 4,
  },
  bottomSheetAddress: {
    fontSize: 14,
    color: Colors.light.gray,
    marginBottom: 8,
  },
  bottomSheetDetails: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 16,
    marginBottom: 8,
  },
  bottomSheetActions: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 16,
  },
  bottomSheetButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 12,
    backgroundColor: Colors.light.primary,
    borderRadius: 12,
  },
  bottomSheetButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: 'white',
  },
  secondaryButton: {
    backgroundColor: 'white',
    borderWidth: 1,
    borderColor: Colors.light.primary,
  },
  secondaryButtonText: {
    color: Colors.light.primary,
  },
});