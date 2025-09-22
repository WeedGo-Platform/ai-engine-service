import React from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
} from 'react-native';
import { Colors } from '@/constants/Colors';

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
            style={[
              styles.pill,
              selectedFilter === filter.id && styles.selectedPill,
            ]}
            onPress={() => handlePress(filter.id)}
          >
            {filter.icon && <Text style={styles.icon}>{filter.icon}</Text>}
            <Text
              style={[
                styles.label,
                selectedFilter === filter.id && styles.selectedLabel,
              ]}
            >
              {filter.label}
            </Text>
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
    fontSize: 16,
    fontWeight: '600',
    color: Colors.light.text,
    marginBottom: 12,
    paddingHorizontal: 16,
  },
  scrollContent: {
    paddingHorizontal: 16,
    gap: 8,
  },
  pill: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 14,
    paddingVertical: 8,
    backgroundColor: 'white',
    borderRadius: 20,
    borderWidth: 1,
    borderColor: Colors.light.border,
    marginRight: 8,
  },
  selectedPill: {
    backgroundColor: Colors.light.primary,
    borderColor: Colors.light.primary,
  },
  icon: {
    fontSize: 14,
    marginRight: 4,
  },
  label: {
    fontSize: 14,
    color: Colors.light.text,
    fontWeight: '500',
  },
  selectedLabel: {
    color: 'white',
  },
});