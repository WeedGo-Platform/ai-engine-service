import React from 'react';
import {
  View,
  Text,
  Image,
  TouchableOpacity,
  StyleSheet,
} from 'react-native';
import { HeadlessTheme } from '../Theme';

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

interface BasicProductCardProps {
  product: Product;
  onPress: () => void;
  onAddToCart: () => void;
}

export const BasicProductCard: React.FC<BasicProductCardProps> = ({
  product,
  onPress,
  onAddToCart,
}) => {
  const theme = HeadlessTheme;

  return (
    <TouchableOpacity
      style={styles.container}
      onPress={onPress}
      activeOpacity={0.7}
    >
      {product.image ? (
        <Image source={{ uri: product.image }} style={styles.image} />
      ) : (
        <View style={styles.imagePlaceholder}>
          <Text style={styles.imagePlaceholderText}>No Image</Text>
        </View>
      )}

      <View style={styles.content}>
        {product.brand && (
          <Text style={styles.brand}>{product.brand}</Text>
        )}
        <Text style={styles.name} numberOfLines={2}>
          {product.name}
        </Text>

        {(product.thc !== undefined || product.cbd !== undefined) && (
          <Text style={styles.cannabinoids}>
            {product.thc !== undefined && `THC: ${product.thc}%`}
            {product.thc !== undefined && product.cbd !== undefined && ' • '}
            {product.cbd !== undefined && `CBD: ${product.cbd}%`}
          </Text>
        )}

        <View style={styles.footer}>
          <Text style={styles.price}>${product.price.toFixed(2)}</Text>
          {product.inStock !== false ? (
            <TouchableOpacity
              style={styles.addButton}
              onPress={(e) => {
                e.stopPropagation();
                onAddToCart();
              }}
            >
              <Text style={styles.addButtonText}>Add to Cart</Text>
            </TouchableOpacity>
          ) : (
            <Text style={styles.outOfStock}>Out of Stock</Text>
          )}
        </View>
      </View>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: HeadlessTheme.colors.surface,
    borderRadius: HeadlessTheme.borderRadius.md,
    marginVertical: HeadlessTheme.spacing.xs,
    marginHorizontal: HeadlessTheme.spacing.sm,
    overflow: 'hidden',
    ...HeadlessTheme.shadows.md,
  },
  image: {
    width: '100%',
    height: 200,
    resizeMode: 'cover',
  },
  imagePlaceholder: {
    width: '100%',
    height: 200,
    backgroundColor: HeadlessTheme.colors.background,
    justifyContent: 'center',
    alignItems: 'center',
  },
  imagePlaceholderText: {
    color: HeadlessTheme.colors.textSecondary,
    fontSize: HeadlessTheme.typography.sizes.body,
  },
  content: {
    padding: HeadlessTheme.spacing.md,
  },
  brand: {
    fontSize: HeadlessTheme.typography.sizes.caption,
    color: HeadlessTheme.colors.textSecondary,
    marginBottom: HeadlessTheme.spacing.xs,
  },
  name: {
    fontSize: HeadlessTheme.typography.sizes.body,
    color: HeadlessTheme.colors.text,
    fontWeight: '600',
    marginBottom: HeadlessTheme.spacing.xs,
  },
  cannabinoids: {
    fontSize: HeadlessTheme.typography.sizes.bodySmall,
    color: HeadlessTheme.colors.textSecondary,
    marginBottom: HeadlessTheme.spacing.sm,
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: HeadlessTheme.spacing.sm,
  },
  price: {
    fontSize: HeadlessTheme.typography.sizes.h3,
    color: HeadlessTheme.colors.text,
    fontWeight: 'bold',
  },
  addButton: {
    backgroundColor: HeadlessTheme.colors.primary,
    paddingHorizontal: HeadlessTheme.spacing.md,
    paddingVertical: HeadlessTheme.spacing.sm,
    borderRadius: HeadlessTheme.borderRadius.sm,
  },
  addButtonText: {
    color: '#FFFFFF',
    fontSize: HeadlessTheme.typography.sizes.button,
    fontWeight: '600',
  },
  outOfStock: {
    color: HeadlessTheme.colors.error,
    fontSize: HeadlessTheme.typography.sizes.bodySmall,
  },
});