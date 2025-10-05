import React from 'react';
import { View, Text, TouchableOpacity, ScrollView, StyleSheet } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';

interface QuickActionPillsProps {
  actions: Array<{ label: string; action: string; data?: any }>;
  onActionPress: (action: string, data?: any) => void;
}

export const QuickActionPills: React.FC<QuickActionPillsProps> = ({
  actions,
  onActionPress
}) => {
  if (!actions || actions.length === 0) return null;

  return (
    <ScrollView
      horizontal
      showsHorizontalScrollIndicator={false}
      style={styles.container}
      contentContainerStyle={styles.contentContainer}
    >
      {actions.map((action, index) => {
        const isAddToCart = action.action === 'add_to_cart' || action.label.toLowerCase().includes('add to cart');
        const gradientColors = isAddToCart ? ['#8B5CF6', '#7C3AED'] : ['#22C55E', '#16A34A'];

        return (
          <TouchableOpacity
            key={`${action.label}-${index}`}
            onPress={() => onActionPress(action.action, action.data)}
            style={styles.pillWrapper}
            activeOpacity={0.8}
          >
            <LinearGradient
              colors={gradientColors}
              style={styles.pill}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 0 }}
            >
              <Text style={styles.pillText}>{action.label}</Text>
              <Ionicons name="arrow-forward" size={14} color="#FFF" />
            </LinearGradient>
          </TouchableOpacity>
        );
      })}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    marginTop: 8,
    marginBottom: 4,
    maxHeight: 44,
  },
  contentContainer: {
    paddingHorizontal: 4,
  },
  pillWrapper: {
    marginHorizontal: 4,
  },
  pill: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 20,
    gap: 6,
  },
  pillText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '600',
  },
});
