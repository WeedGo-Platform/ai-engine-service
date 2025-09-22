import React from 'react';
import {
  View,
  Text,
  Image,
  TouchableOpacity,
  StyleSheet,
  Animated,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { PotPalaceTheme } from '../Theme';

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

interface PotPalaceProductCardProps {
  product: Product;
  onPress: () => void;
  onAddToCart: () => void;
}

export const PotPalaceProductCard: React.FC<PotPalaceProductCardProps> = ({
  product,
  onPress,
  onAddToCart,
}) => {
  const scaleAnim = React.useRef(new Animated.Value(1)).current;
  const theme = PotPalaceTheme;

  const handlePressIn = () => {
    Animated.spring(scaleAnim, {
      toValue: 0.95,
      useNativeDriver: true,
    }).start();
  };

  const handlePressOut = () => {
    Animated.spring(scaleAnim, {
      toValue: 1,
      friction: 3,
      tension: 100,
      useNativeDriver: true,
    }).start();
  };

  return (
    <Animated.View
      style={[
        styles.container,
        {
          transform: [{ scale: scaleAnim }],
        },
      ]}
    >
      <TouchableOpacity
        onPress={onPress}
        onPressIn={handlePressIn}
        onPressOut={handlePressOut}
        activeOpacity={0.9}
      >
        <LinearGradient
          colors={['#FFFFFF', '#F5F5DC']}
          style={styles.gradient}
        >
          {/* Cannabis Leaf Badge */}
          <View style={styles.badge}>
            <Text style={styles.badgeText}>🌿</Text>
          </View>

          {/* Product Image */}
          <View style={styles.imageContainer}>
            {product.image ? (
              <Image source={{ uri: product.image }} style={styles.image} />
            ) : (
              <View style={styles.placeholderImage}>
                <Text style={styles.placeholderEmoji}>🌱</Text>
              </View>
            )}
          </View>

          {/* Product Info */}
          <View style={styles.infoContainer}>
            {product.brand && (
              <Text style={styles.brand}>{product.brand}</Text>
            )}
            <Text style={styles.name} numberOfLines={2}>
              {product.name}
            </Text>

            {/* THC/CBD Pills */}
            <View style={styles.cannabinoidContainer}>
              {product.thc !== undefined && (
                <View style={[styles.pill, styles.thcPill]}>
                  <Text style={styles.pillText}>THC {product.thc}%</Text>
                </View>
              )}
              {product.cbd !== undefined && (
                <View style={[styles.pill, styles.cbdPill]}>
                  <Text style={styles.pillText}>CBD {product.cbd}%</Text>
                </View>
              )}
            </View>

            {/* Price and Add to Cart */}
            <View style={styles.bottomRow}>
              <Text style={styles.price}>${product.price.toFixed(2)}</Text>
              <TouchableOpacity
                style={styles.addButton}
                onPress={onAddToCart}
                activeOpacity={0.7}
              >
                <LinearGradient
                  colors={[theme.colors.primary, '#66BB6A']}
                  style={styles.buttonGradient}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 1 }}
                >
                  <Text style={styles.addButtonText}>+</Text>
                </LinearGradient>
              </TouchableOpacity>
            </View>

            {/* Out of Stock Overlay */}
            {product.inStock === false && (
              <View style={styles.outOfStockOverlay}>
                <Text style={styles.outOfStockText}>Out of Stock</Text>
              </View>
            )}
          </View>
        </LinearGradient>
      </TouchableOpacity>
    </Animated.View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    margin: 8,
    borderRadius: PotPalaceTheme.borderRadius.md,
    ...PotPalaceTheme.shadows.md,
  },
  gradient: {
    borderRadius: PotPalaceTheme.borderRadius.md,
    overflow: 'hidden',
  },
  badge: {
    position: 'absolute',
    top: 8,
    right: 8,
    backgroundColor: PotPalaceTheme.colors.accent,
    width: 32,
    height: 32,
    borderRadius: PotPalaceTheme.borderRadius.round,
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 1,
  },
  badgeText: {
    fontSize: 18,
  },
  imageContainer: {
    height: 150,
    backgroundColor: PotPalaceTheme.colors.surface,
    borderTopLeftRadius: PotPalaceTheme.borderRadius.md,
    borderTopRightRadius: PotPalaceTheme.borderRadius.md,
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
    backgroundColor: '#F0F8F0',
  },
  placeholderEmoji: {
    fontSize: 48,
  },
  infoContainer: {
    padding: PotPalaceTheme.spacing.md,
  },
  brand: {
    fontSize: PotPalaceTheme.typography.sizes.caption,
    color: PotPalaceTheme.colors.textSecondary,
    marginBottom: 4,
    fontWeight: '500',
  },
  name: {
    fontSize: PotPalaceTheme.typography.sizes.body,
    color: PotPalaceTheme.colors.text,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  cannabinoidContainer: {
    flexDirection: 'row',
    marginBottom: 12,
  },
  pill: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: PotPalaceTheme.borderRadius.round,
    marginRight: 6,
  },
  thcPill: {
    backgroundColor: 'rgba(76, 175, 80, 0.2)',
  },
  cbdPill: {
    backgroundColor: 'rgba(156, 39, 176, 0.2)',
  },
  pillText: {
    fontSize: PotPalaceTheme.typography.sizes.caption,
    color: PotPalaceTheme.colors.text,
    fontWeight: '600',
  },
  bottomRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  price: {
    fontSize: 20,
    fontWeight: 'bold',
    color: PotPalaceTheme.colors.primary,
  },
  addButton: {
    borderRadius: PotPalaceTheme.borderRadius.round,
    overflow: 'hidden',
  },
  buttonGradient: {
    width: 36,
    height: 36,
    justifyContent: 'center',
    alignItems: 'center',
  },
  addButtonText: {
    color: '#FFFFFF',
    fontSize: 24,
    fontWeight: 'bold',
  },
  outOfStockOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    justifyContent: 'center',
    alignItems: 'center',
    borderRadius: PotPalaceTheme.borderRadius.md,
  },
  outOfStockText: {
    color: PotPalaceTheme.colors.error,
    fontSize: PotPalaceTheme.typography.sizes.body,
    fontWeight: 'bold',
  },
});