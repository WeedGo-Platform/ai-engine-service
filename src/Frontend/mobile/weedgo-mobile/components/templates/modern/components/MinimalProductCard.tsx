import React from 'react';
import {
  View,
  Text,
  Image,
  TouchableOpacity,
  StyleSheet,
} from 'react-native';
import { ModernTheme } from '../Theme';

interface Product {
  id: string;
  name: string;
  brand?: string;
  price: number;
  image?: string;
  thc?: number;
  cbd?: number;
  category?: string;
  inStock?: boolean;
}

interface MinimalProductCardProps {
  product: Product;
  onPress: () => void;
  onAddToCart: () => void;
}

export const MinimalProductCard: React.FC<MinimalProductCardProps> = ({
  product,
  onPress,
  onAddToCart,
}) => {
  const theme = ModernTheme;

  return (
    <TouchableOpacity
      style={styles.container}
      onPress={onPress}
      activeOpacity={0.7}
    >
      {/* Product Image */}
      <View style={styles.imageContainer}>
        {product.image ? (
          <Image source={{ uri: product.image }} style={styles.image} />
        ) : (
          <View style={styles.placeholderImage}>
            <Text style={styles.placeholderText}>No Image</Text>
          </View>
        )}
      </View>

      {/* Product Info */}
      <View style={styles.infoContainer}>
        {product.brand && (
          <Text style={styles.brand}>{product.brand.toUpperCase()}</Text>
        )}
        <Text style={styles.name} numberOfLines={2}>
          {product.name}
        </Text>

        {/* Cannabinoid Info */}
        {(product.thc !== undefined || product.cbd !== undefined) && (
          <View style={styles.cannabinoidContainer}>
            {product.thc !== undefined && (
              <Text style={styles.cannabinoidText}>
                THC: {product.thc}%
              </Text>
            )}
            {product.thc !== undefined && product.cbd !== undefined && (
              <Text style={styles.separator}>|</Text>
            )}
            {product.cbd !== undefined && (
              <Text style={styles.cannabinoidText}>
                CBD: {product.cbd}%
              </Text>
            )}
          </View>
        )}

        {/* Price and Add Button */}
        <View style={styles.bottomRow}>
          <Text style={styles.price}>${product.price.toFixed(2)}</Text>
          {product.inStock !== false ? (
            <TouchableOpacity
              style={styles.addButton}
              onPress={(e) => {
                e.stopPropagation();
                onAddToCart();
              }}
              activeOpacity={0.6}
            >
              <Text style={styles.addButtonText}>ADD</Text>
            </TouchableOpacity>
          ) : (
            <View style={styles.outOfStockBadge}>
              <Text style={styles.outOfStockText}>OUT OF STOCK</Text>
            </View>
          )}
        </View>
      </View>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: ModernTheme.colors.surface,
    borderRadius: ModernTheme.borderRadius.md,
    overflow: 'hidden',
    marginHorizontal: 8,
    marginVertical: 4,
    ...ModernTheme.shadows.sm,
  },
  imageContainer: {
    height: 180,
    backgroundColor: ModernTheme.colors.background,
  },
  image: {
    width: '100%',
    height: '100%',
    resizeMode: 'cover',
  },
  placeholderImage: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: ModernTheme.colors.background,
  },
  placeholderText: {
    fontSize: ModernTheme.typography.sizes.caption,
    color: ModernTheme.colors.textSecondary,
  },
  infoContainer: {
    padding: ModernTheme.spacing.md,
  },
  brand: {
    fontSize: ModernTheme.typography.sizes.caption,
    color: ModernTheme.colors.textSecondary,
    letterSpacing: 1,
    marginBottom: 4,
  },
  name: {
    fontSize: ModernTheme.typography.sizes.body,
    color: ModernTheme.colors.text,
    marginBottom: 8,
    lineHeight: ModernTheme.typography.lineHeights.body,
  },
  cannabinoidContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  cannabinoidText: {
    fontSize: ModernTheme.typography.sizes.bodySmall,
    color: ModernTheme.colors.textSecondary,
  },
  separator: {
    marginHorizontal: 8,
    color: ModernTheme.colors.border,
  },
  bottomRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  price: {
    fontSize: 18,
    fontWeight: '300',
    color: ModernTheme.colors.text,
  },
  addButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    backgroundColor: ModernTheme.colors.primary,
    borderRadius: ModernTheme.borderRadius.sm,
  },
  addButtonText: {
    color: '#FFFFFF',
    fontSize: ModernTheme.typography.sizes.bodySmall,
    fontWeight: '500',
    letterSpacing: 0.5,
  },
  outOfStockBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderWidth: 1,
    borderColor: ModernTheme.colors.border,
    borderRadius: ModernTheme.borderRadius.sm,
  },
  outOfStockText: {
    fontSize: ModernTheme.typography.sizes.caption,
    color: ModernTheme.colors.textSecondary,
    letterSpacing: 0.5,
  },
});