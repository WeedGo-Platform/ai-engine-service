import React, { useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Modal,
  FlatList,
  SafeAreaView,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import useStoreStore from '@/stores/storeStore';
import { Colors, Gradients, BorderRadius, Shadows } from '@/constants/Colors';
import { LinearGradient } from 'expo-linear-gradient';
import { Store } from '@/types/api.types';
import { formatShortAddress } from '@/utils/formatters';

export function StoreSelector() {
  const { currentStore, stores, setCurrentStore, getStoreHours, loadStores } = useStoreStore();
  const [modalVisible, setModalVisible] = useState(false);

  React.useEffect(() => {
    loadStores();
  }, []);

  const handleSelectStore = (store: Store) => {
    setCurrentStore(store);
    setModalVisible(false);
  };

  if (!currentStore) {
    return (
      <TouchableOpacity
        onPress={() => setModalVisible(true)}
        activeOpacity={0.8}
      >
        <LinearGradient
          colors={Gradients.primary}
          style={styles.selector}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
        >
          <View style={styles.selectorContent}>
            <Ionicons name="location-outline" size={20} color="white" />
            <Text style={[styles.selectText, { color: 'white' }]}>Select a store</Text>
            <Ionicons name="chevron-down" size={20} color="white" />
          </View>
        </LinearGradient>
      </TouchableOpacity>
    );
  }

  return (
    <>
      <TouchableOpacity
        onPress={() => setModalVisible(true)}
        activeOpacity={0.8}
      >
        <LinearGradient
          colors={['rgba(255, 255, 255, 0.98)', 'rgba(240, 250, 255, 0.95)']}
          style={styles.selector}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
        >
          <View style={styles.selectorContent}>
            <View style={styles.storeInfo}>
              <View style={styles.storeHeader}>
                <Ionicons name="location" size={18} color={Colors.light.primary} />
                <Text style={styles.storeName}>{currentStore.name}</Text>
                <Ionicons name="chevron-down" size={18} color={Colors.light.primary} />
              </View>
              <Text style={styles.storeHours}>{getStoreHours()}</Text>
            </View>
          </View>
        </LinearGradient>
      </TouchableOpacity>

      <Modal
        animationType="slide"
        transparent={true}
        visible={modalVisible}
        onRequestClose={() => setModalVisible(false)}
      >
        <SafeAreaView style={styles.modalContainer}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Select Store</Text>
              <TouchableOpacity onPress={() => setModalVisible(false)}>
                <Ionicons name="close" size={24} color={Colors.light.text} />
              </TouchableOpacity>
            </View>

            <FlatList
              data={stores}
              keyExtractor={(item, index) => `${item.id}-${index}`}
              renderItem={({ item }) => (
                <TouchableOpacity
                  style={[
                    styles.storeItem,
                    currentStore?.id === item.id && styles.selectedStore,
                  ]}
                  onPress={() => handleSelectStore(item)}
                >
                  <View style={styles.storeItemContent}>
                    <Text style={styles.storeItemName}>{item.name}</Text>
                    <Text style={styles.storeItemAddress}>{formatShortAddress(item.address)}</Text>
                    <View style={styles.storeFeatures}>
                      {item.pickup_available && (
                        <View style={styles.featureBadge}>
                          <Ionicons name="bag-outline" size={14} color={Colors.light.primary} />
                          <Text style={styles.featureText}>Pickup</Text>
                        </View>
                      )}
                      {item.delivery_available && (
                        <View style={styles.featureBadge}>
                          <Ionicons name="bicycle-outline" size={14} color={Colors.light.primary} />
                          <Text style={styles.featureText}>Delivery</Text>
                        </View>
                      )}
                    </View>
                  </View>
                  {currentStore?.id === item.id && (
                    <Ionicons name="checkmark-circle" size={24} color={Colors.light.primary} />
                  )}
                </TouchableOpacity>
              )}
              ItemSeparatorComponent={() => <View style={styles.separator} />}
            />
          </View>
        </SafeAreaView>
      </Modal>
    </>
  );
}

const styles = StyleSheet.create({
  selector: {
    paddingHorizontal: 16,
    paddingVertical: 14,
    marginHorizontal: 16,
    marginVertical: 8,
    borderRadius: BorderRadius.xl,
    borderWidth: 1.5,
    borderColor: 'rgba(255, 255, 255, 0.5)',
    ...Shadows.medium,
  },
  selectorContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  storeInfo: {
    flex: 1,
  },
  storeHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  storeName: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.light.text,
    flex: 1,
  },
  storeHours: {
    fontSize: 13,
    color: Colors.light.success,
    marginTop: 2,
    marginLeft: 24,
  },
  selectText: {
    fontSize: 16,
    color: Colors.light.text,
    flex: 1,
    marginLeft: 8,
  },
  modalContainer: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
  },
  modalContent: {
    flex: 1,
    backgroundColor: 'white',
    marginTop: 100,
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: Colors.light.border,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: Colors.light.text,
  },
  storeItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
  },
  selectedStore: {
    backgroundColor: Colors.light.primaryLight,
  },
  storeItemContent: {
    flex: 1,
  },
  storeItemName: {
    fontSize: 16,
    fontWeight: '500',
    color: Colors.light.text,
    marginBottom: 4,
  },
  storeItemAddress: {
    fontSize: 14,
    color: Colors.light.gray,
    marginBottom: 8,
  },
  storeFeatures: {
    flexDirection: 'row',
    gap: 8,
  },
  featureBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: Colors.light.backgroundSecondary,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  featureText: {
    fontSize: 12,
    color: Colors.light.text,
  },
  separator: {
    height: 1,
    backgroundColor: Colors.light.border,
    marginLeft: 16,
  },
});