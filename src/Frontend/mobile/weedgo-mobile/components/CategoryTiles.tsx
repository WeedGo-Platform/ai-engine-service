import React, { useEffect } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Colors, Gradients, BorderRadius, Shadows } from '@/constants/Colors';
import { LinearGradient } from 'expo-linear-gradient';
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
  const theme = Colors.light;

  // Get gradient colors based on category
  const getGradientColors = () => {
    const categoryLower = id.toLowerCase();
    if (categoryLower.includes('flower')) return Gradients.primary;
    if (categoryLower.includes('edible')) return Gradients.warm;
    if (categoryLower.includes('vape')) return Gradients.cool;
    if (categoryLower.includes('concentrate')) return Gradients.sunset;
    if (categoryLower.includes('pre-roll') || categoryLower.includes('preroll')) return Gradients.sativa;
    if (categoryLower.includes('oil') || categoryLower.includes('capsule')) return Gradients.purple;
    if (categoryLower.includes('topical')) return Gradients.secondary;
    return Gradients.ocean;
  };

  return (
    <TouchableOpacity
      style={styles.tileContainer}
      onPress={() => onPress(id)}
      activeOpacity={0.8}
    >
      <LinearGradient
        colors={isSelected ? getGradientColors() : ['rgba(255, 255, 255, 0.95)', color]}
        style={[
          styles.tile,
          isSelected && styles.selectedTile,
        ]}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
      >
        <Ionicons
          name={icon}
          size={32}
          color={isSelected ? 'white' : theme.primary}
          style={[styles.iconStyle, isSelected && styles.selectedIcon]}
        />
        <Text style={[styles.name, isSelected && styles.selectedName]}>{name}</Text>
      </LinearGradient>
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

// Color mapping for subcategories - vibrant colors
const categoryColorMap: Record<string, string> = {
  // Flower subcategories
  flower: '#E8FFE8',
  'dried flower': '#E8FFE8',
  'whole flower': '#D4FFEA',
  'milled flower': '#C1FFE1',

  // Pre-rolls subcategories
  'pre-roll': '#FFE8D6',
  'pre-rolls': '#FFE8D6',
  preroll: '#FFE8D6',
  prerolls: '#FFE8D6',
  'infused pre-rolls': '#FFD4A3',

  // Edibles subcategories
  edibles: '#FFE8F7',
  edible: '#FFE8F7',
  gummies: '#FFD6F3',
  chocolates: '#FFC4ED',
  beverages: '#E8F4FF',
  baked: '#FFF4E8',

  // Concentrates subcategories
  concentrates: '#FFF0D4',
  concentrate: '#FFF0D4',
  'hash & kief': '#FFE8C1',
  resin: '#FFDBA3',
  rosin: '#FFCE85',
  distillate: '#FFC167',

  // Vapes subcategories
  vapes: '#E8F0FF',
  vape: '#E8F0FF',
  cartridges: '#D6E8FF',
  'vape kits': '#C4DFFF',
  'disposable vapes': '#B3D6FF',

  // Oils & Capsules
  oils: '#F4E8FF',
  oil: '#F4E8FF',
  capsules: '#EDD6FF',

  // Topicals subcategories
  topicals: '#FFE8EA',
  topical: '#FFE8EA',
  'bath & body': '#FFD6DA',

  // Other
  accessories: '#F0F0FF',
  accessory: '#F0F0FF',
  gear: '#E8E8FF',
  cbd: '#E8F7FF',
  tinctures: '#F0E8FF',
  tincture: '#F0E8FF',
  seeds: '#C8FFC8',
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
    fontSize: 20,
    fontWeight: '700',
    color: Colors.light.text,
    marginBottom: 12,
    paddingHorizontal: 16,
  },
  scrollContent: {
    paddingHorizontal: 16,
    gap: 12,
  },
  tileContainer: {
    marginRight: 12,
  },
  tile: {
    width: 85,
    height: 85,
    borderRadius: BorderRadius.xl,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1.5,
    borderColor: 'rgba(255, 255, 255, 0.5)',
    ...Shadows.small,
  },
  selectedTile: {
    borderColor: 'rgba(255, 255, 255, 0.8)',
    borderWidth: 2,
    ...Shadows.colorful,
  },
  iconStyle: {
    marginBottom: 4,
  },
  selectedIcon: {
    transform: [{ scale: 1.2 }],
  },
  name: {
    fontSize: 11,
    color: Colors.light.text,
    fontWeight: '600',
    textAlign: 'center',
    paddingHorizontal: 4,
  },
  selectedName: {
    color: 'white',
    fontWeight: '700',
    textShadowColor: 'rgba(0, 0, 0, 0.2)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 2,
  },
});