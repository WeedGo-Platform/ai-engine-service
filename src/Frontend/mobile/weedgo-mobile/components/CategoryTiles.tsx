import React, { useEffect } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Colors } from '@/constants/Colors';
import useProductsStore from '@/stores/productsStore';

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

// Icon mapping for common cannabis subcategories
const categoryIconMap: Record<string, keyof typeof Ionicons.glyphMap> = {
  // Flower subcategories
  flower: 'flower-outline',
  'dried flower': 'flower-outline',
  'whole flower': 'flower-outline',
  'milled flower': 'flower-outline',

  // Pre-rolls subcategories
  'pre-roll': 'leaf-outline',
  'pre-rolls': 'leaf-outline',
  preroll: 'leaf-outline',
  prerolls: 'leaf-outline',
  'infused pre-rolls': 'sparkles-outline',

  // Edibles subcategories
  edibles: 'nutrition-outline',
  edible: 'nutrition-outline',
  gummies: 'nutrition-outline',
  chocolates: 'cafe-outline',
  beverages: 'beer-outline',
  baked: 'restaurant-outline',

  // Concentrates subcategories
  concentrates: 'water-outline',
  concentrate: 'water-outline',
  'hash & kief': 'water-outline',
  resin: 'water-outline',
  rosin: 'water-outline',
  distillate: 'water-outline',

  // Vapes subcategories
  vapes: 'cloud-outline',
  vape: 'cloud-outline',
  cartridges: 'cloud-outline',
  'vape kits': 'cloud-outline',
  'disposable vapes': 'cloud-outline',

  // Oils & Capsules
  oils: 'eyedrop-outline',
  oil: 'eyedrop-outline',
  capsules: 'medical-outline',

  // Topicals subcategories
  topicals: 'hand-left-outline',
  topical: 'hand-left-outline',
  'bath & body': 'hand-left-outline',

  // Other
  accessories: 'construct-outline',
  accessory: 'construct-outline',
  gear: 'construct-outline',
  cbd: 'medical-outline',
  tinctures: 'eyedrop-outline',
  tincture: 'eyedrop-outline',
  seeds: 'leaf-outline',
};

// Color mapping for subcategories
const categoryColorMap: Record<string, string> = {
  // Flower subcategories
  flower: '#E8F5E9',
  'dried flower': '#E8F5E9',
  'whole flower': '#E8F5E9',
  'milled flower': '#E1F5FE',

  // Pre-rolls subcategories
  'pre-roll': '#F1F8E9',
  'pre-rolls': '#F1F8E9',
  preroll: '#F1F8E9',
  prerolls: '#F1F8E9',
  'infused pre-rolls': '#FFF9C4',

  // Edibles subcategories
  edibles: '#EFEBE9',
  edible: '#EFEBE9',
  gummies: '#FFECB3',
  chocolates: '#EFEBE9',
  beverages: '#E0F2F1',
  baked: '#FFF3E0',

  // Concentrates subcategories
  concentrates: '#FFF8E1',
  concentrate: '#FFF8E1',
  'hash & kief': '#FFF8E1',
  resin: '#FFE0B2',
  rosin: '#FFECB3',
  distillate: '#FFF9C4',

  // Vapes subcategories
  vapes: '#E3F2FD',
  vape: '#E3F2FD',
  cartridges: '#E3F2FD',
  'vape kits': '#E1F5FE',
  'disposable vapes': '#E0F7FA',

  // Oils & Capsules
  oils: '#F3E5F5',
  oil: '#F3E5F5',
  capsules: '#EDE7F6',

  // Topicals subcategories
  topicals: '#FCE4EC',
  topical: '#FCE4EC',
  'bath & body': '#FCE4EC',

  // Other
  accessories: '#F5F5F5',
  accessory: '#F5F5F5',
  gear: '#F5F5F5',
  cbd: '#E8F5E9',
  tinctures: '#F3E5F5',
  tincture: '#F3E5F5',
  seeds: '#C8E6C9',
};

export function CategoryTiles({ selectedCategory, onSelectCategory }: CategoryTilesProps) {
  const categories = useProductsStore((state) => state.categories);
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Categories</Text>
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.scrollContent}
      >
        {categories.map((category) => {
          const icon = categoryIconMap[category.id.toLowerCase()] || 'cube-outline';
          const color = categoryColorMap[category.id.toLowerCase()] || '#F5F5F5';

          return (
            <CategoryTile
              key={category.id}
              id={category.id}
              name={category.name}
              icon={icon}
              color={color}
              isSelected={selectedCategory === category.id}
              onPress={onSelectCategory}
            />
          );
        })}
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