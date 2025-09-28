import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  Modal,
  FlatList,
  StyleSheet,
  ActivityIndicator,
  SafeAreaView,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useChatStore } from '../../stores/chatStore';
import { Personality } from '../../services/chat/agentService';

export function PersonalitySelector() {
  const [modalVisible, setModalVisible] = useState(false);
  const [loading, setLoading] = useState(false);
  const [personalities, setPersonalities] = useState<Personality[]>([]);

  const {
    personality,
    fetchPersonalities,
    changePersonality,
    availablePersonalities
  } = useChatStore();

  useEffect(() => {
    if (modalVisible && availablePersonalities.length === 0) {
      loadPersonalities();
    }
  }, [modalVisible]);

  const loadPersonalities = async () => {
    setLoading(true);
    try {
      const result = await fetchPersonalities();
      setPersonalities(result);
    } catch (error) {
      console.error('Failed to load personalities:', error);
    }
    setLoading(false);
  };

  const handleSelectPersonality = async (personalityId: string) => {
    setLoading(true);
    const success = await changePersonality(personalityId);
    if (success) {
      setModalVisible(false);
    }
    setLoading(false);
  };

  const renderPersonalityItem = ({ item }: { item: Personality }) => {
    const isSelected = personality?.id === item.id;

    return (
      <TouchableOpacity
        style={[styles.personalityItem, isSelected && styles.selectedItem]}
        onPress={() => handleSelectPersonality(item.id)}
        disabled={loading}
      >
        <View style={styles.personalityContent}>
          <Text style={[styles.personalityName, isSelected && styles.selectedText]}>
            {item.name || item.id}
          </Text>
          {isSelected && (
            <Ionicons name="checkmark-circle" size={24} color="#4ade80" />
          )}
        </View>
      </TouchableOpacity>
    );
  };

  return (
    <>
      <TouchableOpacity onPress={() => setModalVisible(true)} style={styles.iconButton}>
        <Ionicons name="settings-outline" size={24} color="#fff" />
      </TouchableOpacity>

      <Modal
        animationType="slide"
        transparent={true}
        visible={modalVisible}
        onRequestClose={() => setModalVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <SafeAreaView style={styles.modalSafeArea}>
              <View style={styles.modalHeader}>
                <Text style={styles.modalTitle}>Select Personality</Text>
                <TouchableOpacity
                  onPress={() => setModalVisible(false)}
                  style={styles.closeButton}
                >
                  <Ionicons name="close" size={24} color="#6b7280" />
                </TouchableOpacity>
              </View>

              {loading && !availablePersonalities.length ? (
                <View style={styles.loadingContainer}>
                  <ActivityIndicator size="large" color="#667eea" />
                  <Text style={styles.loadingText}>Loading personalities...</Text>
                </View>
              ) : (
                <FlatList
                  data={availablePersonalities.length ? availablePersonalities : personalities}
                  renderItem={renderPersonalityItem}
                  keyExtractor={(item) => item.id}
                  contentContainerStyle={styles.listContent}
                  ItemSeparatorComponent={() => <View style={styles.separator} />}
                />
              )}

              {loading && availablePersonalities.length > 0 && (
                <View style={styles.loadingOverlay}>
                  <ActivityIndicator size="large" color="#667eea" />
                </View>
              )}
            </SafeAreaView>
          </View>
        </View>
      </Modal>
    </>
  );
}

const styles = StyleSheet.create({
  iconButton: {
    padding: 4,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#fff',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    maxHeight: '70%',
    minHeight: 300,
  },
  modalSafeArea: {
    flex: 1,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1f2937',
  },
  closeButton: {
    padding: 4,
  },
  listContent: {
    paddingVertical: 8,
  },
  personalityItem: {
    paddingHorizontal: 20,
    paddingVertical: 16,
  },
  selectedItem: {
    backgroundColor: '#f0fdf4',
  },
  personalityContent: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  personalityName: {
    fontSize: 16,
    color: '#374151',
    textTransform: 'capitalize',
  },
  selectedText: {
    color: '#16a34a',
    fontWeight: '600',
  },
  separator: {
    height: 1,
    backgroundColor: '#f3f4f6',
    marginHorizontal: 20,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 40,
  },
  loadingText: {
    marginTop: 12,
    fontSize: 14,
    color: '#6b7280',
  },
  loadingOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    justifyContent: 'center',
    alignItems: 'center',
  },
});