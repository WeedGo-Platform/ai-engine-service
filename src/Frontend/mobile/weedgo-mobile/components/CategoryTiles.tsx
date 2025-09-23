import React from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Colors } from '@/constants/Colors';

interface CategoryTileProps {
  id: string;
  name: string;
  icon: keyof typeof Ionicons.glyphMap;
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
      <Ionicons
        name={icon}
        size={32}
        color={isSelected ? Colors.light.primary : Colors.light.gray}
        style={[styles.iconStyle, isSelected && styles.selectedIcon]}
      />
      <Text style={[styles.name, isSelected && styles.selectedName]}>{name}</Text>
    </TouchableOpacity>
  );
};

interface CategoryTilesProps {
  selectedCategory?: string;
  onSelectCategory: (categoryId: string) => void;
}

const categories = [
  { id: 'flower', name: 'Flower', icon: 'flower-outline' as keyof typeof Ionicons.glyphMap, color: '#E8F5E9' },
  { id: 'prerolls', name: 'Pre-Rolls', icon: 'leaf-outline' as keyof typeof Ionicons.glyphMap, color: '#F1F8E9' },
  { id: 'edibles', name: 'Edibles', icon: 'nutrition-outline' as keyof typeof Ionicons.glyphMap, color: '#EFEBE9' },
  { id: 'concentrates', name: 'Concentrates', icon: 'water-outline' as keyof typeof Ionicons.glyphMap, color: '#FFF8E1' },
  { id: 'vapes', name: 'Vapes', icon: 'cloud-outline' as keyof typeof Ionicons.glyphMap, color: '#E3F2FD' },
  { id: 'topicals', name: 'Topicals', icon: 'hand-left-outline' as keyof typeof Ionicons.glyphMap, color: '#FCE4EC' },
  { id: 'accessories', name: 'Gear', icon: 'construct-outline' as keyof typeof Ionicons.glyphMap, color: '#F5F5F5' },
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
  iconStyle: {
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