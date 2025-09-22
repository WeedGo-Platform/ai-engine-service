import React from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
} from 'react-native';
import { Colors } from '@/constants/Colors';

interface CategoryTileProps {
  id: string;
  name: string;
  icon: string;
  color: string;
  isSelected?: boolean;
  onPress: (id: string) => void;
}

const CategoryTile: React.FC<CategoryTileProps> = ({
  id,
  name,
  icon,
  color,
  isSelected,
  onPress,
}) => {
  return (
    <TouchableOpacity
      style={[
        styles.tile,
        isSelected && styles.selectedTile,
        { backgroundColor: isSelected ? color : 'white' }
      ]}
      onPress={() => onPress(id)}
    >
      <Text style={[styles.icon, isSelected && styles.selectedIcon]}>{icon}</Text>
      <Text style={[styles.name, isSelected && styles.selectedName]}>{name}</Text>
    </TouchableOpacity>
  );
};

interface CategoryTilesProps {
  selectedCategory?: string;
  onSelectCategory: (categoryId: string) => void;
}

const categories = [
  { id: 'flower', name: 'Flower', icon: '🌸', color: '#E8F5E9' },
  { id: 'prerolls', name: 'Pre-Rolls', icon: '🍃', color: '#F1F8E9' },
  { id: 'edibles', name: 'Edibles', icon: '🍫', color: '#EFEBE9' },
  { id: 'concentrates', name: 'Concentrates', icon: '💎', color: '#FFF8E1' },
  { id: 'vapes', name: 'Vapes', icon: '💨', color: '#E3F2FD' },
  { id: 'topicals', name: 'Topicals', icon: '🧴', color: '#FCE4EC' },
  { id: 'accessories', name: 'Gear', icon: '🔧', color: '#F5F5F5' },
];

export function CategoryTiles({ selectedCategory, onSelectCategory }: CategoryTilesProps) {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Categories</Text>
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.scrollContent}
      >
        {categories.map((category) => (
          <CategoryTile
            key={category.id}
            {...category}
            isSelected={selectedCategory === category.id}
            onPress={onSelectCategory}
          />
        ))}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    paddingVertical: 16,
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
    color: Colors.light.text,
    marginBottom: 12,
    paddingHorizontal: 16,
  },
  scrollContent: {
    paddingHorizontal: 16,
    gap: 12,
  },
  tile: {
    width: 80,
    height: 80,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
    borderWidth: 1,
    borderColor: Colors.light.border,
  },
  selectedTile: {
    borderColor: Colors.light.primary,
    borderWidth: 2,
  },
  icon: {
    fontSize: 28,
    marginBottom: 4,
  },
  selectedIcon: {
    transform: [{ scale: 1.1 }],
  },
  name: {
    fontSize: 11,
    color: Colors.light.text,
    fontWeight: '500',
  },
  selectedName: {
    color: Colors.light.primary,
    fontWeight: '600',
  },
});