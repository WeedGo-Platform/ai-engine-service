import React from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
} from 'react-native';
import { Colors, Gradients, BorderRadius, Shadows } from '@/constants/Colors';
import { LinearGradient } from 'expo-linear-gradient';

interface FilterPill {
  id: string;
  label: string;
  icon?: string;
}

const quickFilters: FilterPill[] = [
  { id: 'trending', label: 'Trending', icon: '🔥' },
  { id: 'new', label: 'New Arrivals', icon: '✨' },
  { id: 'staff-picks', label: 'Staff Picks', icon: '⭐' },
  { id: 'on-sale', label: 'On Sale', icon: '💰' },
];

// Gradient colors for each filter
const filterGradients: Record<string, string[]> = {
  'trending': Gradients.warm,
  'new': Gradients.purple,
  'staff-picks': Gradients.accent,
  'on-sale': Gradients.secondary,
};

interface QuickFiltersProps {
  selectedFilter?: string;
  onSelectFilter: (filterId: string | undefined) => void;
}

export function QuickFilters({ selectedFilter, onSelectFilter }: QuickFiltersProps) {
  const handlePress = (filterId: string) => {
    // Toggle filter - if already selected, deselect it
    onSelectFilter(selectedFilter === filterId ? undefined : filterId);
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Quick Filters</Text>
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.scrollContent}
      >
        {quickFilters.map((filter) => (
          <TouchableOpacity
            key={filter.id}
            onPress={() => handlePress(filter.id)}
            activeOpacity={0.8}
            style={styles.pillContainer}
          >
            {selectedFilter === filter.id ? (
              <LinearGradient
                colors={filterGradients[filter.id] || Gradients.primary}
                style={styles.pill}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
              >
                {filter.icon && <Text style={styles.icon}>{filter.icon}</Text>}
                <Text style={[styles.label, styles.selectedLabel]}>
                  {filter.label}
                </Text>
              </LinearGradient>
            ) : (
              <View style={[styles.pill, styles.unselectedPill]}>
                {filter.icon && <Text style={styles.icon}>{filter.icon}</Text>}
                <Text style={styles.label}>
                  {filter.label}
                </Text>
              </View>
            )}
          </TouchableOpacity>
        ))}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    paddingVertical: 12,
  },
  title: {
    fontSize: 18,
    fontWeight: '700',
    color: Colors.light.text,
    marginBottom: 12,
    paddingHorizontal: 16,
  },
  scrollContent: {
    paddingHorizontal: 16,
    gap: 8,
  },
  pillContainer: {
    marginRight: 8,
  },
  pill: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: BorderRadius.full,
    borderWidth: 1.5,
    borderColor: 'rgba(255, 255, 255, 0.5)',
    ...Shadows.small,
  },
  unselectedPill: {
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    borderColor: Colors.light.border,
  },
  icon: {
    fontSize: 16,
    marginRight: 6,
  },
  label: {
    fontSize: 14,
    color: Colors.light.text,
    fontWeight: '600',
  },
  selectedLabel: {
    color: 'white',
    fontWeight: '700',
    textShadowColor: 'rgba(0, 0, 0, 0.2)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 2,
  },
});