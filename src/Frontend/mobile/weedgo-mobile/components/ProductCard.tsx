import React from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Image,
  Dimensions,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { Product } from '@/types/api.types';
import useCartStore from '@/stores/cartStore';
import { useWishlistStore } from '@/stores/wishlistStore';
import { useAuthStore } from '@/stores/authStore';
import { Colors, BorderRadius, Shadows, Gradients } from '@/constants/Colors';
import { LinearGradient } from 'expo-linear-gradient';

const { width } = Dimensions.get('window');
const cardWidth = (width - 32 - 16) / 2; // 2 columns with 16px padding on each side and 16px gap
const isDark = false; // Use light theme for colorful design
const theme = isDark ? Colors.dark : Colors.light;

interface ProductCardProps {
  product: Product;
  onPress?: () => void;
}

export function ProductCard({ product, onPress }: ProductCardProps) {
  const router = useRouter();
  const { addItem, getCartItem } = useCartStore();
  const { addToWishlist, removeFromWishlist, isInWishlist } = useWishlistStore();
  const { isAuthenticated } = useAuthStore();
  const [isWishlistLoading, setIsWishlistLoading] = React.useState(false);

  // Guard against invalid product
  if (!product || typeof product !== 'object') {
    return null;
  }

  // Debug: Log disabled to prevent console spam
  // Uncomment to debug:
  // console.log('ProductCard received product with keys:', Object.keys(product));
  // console.log('Product stock field:', product.inStock);

  // Use API fields directly
  const image = product.image || product.images?.[0];
  const strainType = product.strainType;
  const inStock = product.inStock;
  const price = product.price;
  const thcContent = product.thcContent;
  const cbdContent = product.cbdContent;


  const cartItem = getCartItem(product.sku);
  const inWishlist = isInWishlist(product.id);

  const handlePress = () => {
    if (onPress) {
      onPress();
    } else {
      router.push(`/product/${product.id}`);
    }
  };

  const handleAddToCart = async (e: any) => {
    e.stopPropagation();
    await addItem(product, 1, product.size);
  };

  const handleToggleWishlist = async (e: any) => {
    e.stopPropagation();
    if (!isAuthenticated) {
      // Redirect to login if not authenticated
      router.push('/(auth)/login');
      return;
    }

    setIsWishlistLoading(true);
    try {
      if (inWishlist) {
        await removeFromWishlist(product.id);
      } else {
        await addToWishlist(product);
      }
    } catch (error) {
      console.error('Error toggling wishlist:', error);
    } finally {
      setIsWishlistLoading(false);
    }
  };

  const formatStrainType = (type?: string | null) => {
    if (!type) return '';
    const lowerType = type.toLowerCase();
    // Simplify to just the main strain type
    if (lowerType.includes('indica')) {
      return 'INDICA';
    } else if (lowerType.includes('sativa')) {
      return 'SATIVA';
    } else if (lowerType.includes('hybrid')) {
      return 'HYBRID';
    } else if (lowerType.includes('blend')) {
      return 'BLEND';
    } else if (lowerType.includes('cbd')) {
      return 'CBD';
    }
    return type.toUpperCase();
  };

  const getStrainTypeGradient = (type?: string | null): [string, string] => {
    if (!type) return ['#6B7280', '#4B5563'];
    const lowerType = type.toLowerCase();
    if (lowerType?.includes('indica')) {
      return ['#3B82F6', '#2563EB']; // Blue gradient for Indica/Indica Dominant
    } else if (lowerType?.includes('sativa')) {
      return ['#FB923C', '#F97316']; // Bright orange gradient for Sativa/Sativa Dominant
    } else if (lowerType?.includes('hybrid')) {
      return ['#10B981', '#059669']; // Green gradient for Hybrid
    } else if (lowerType?.includes('blend')) {
      return ['#A855F7', '#9333EA']; // Purple gradient for Blend
    } else if (lowerType?.includes('cbd')) {
      return ['#06B6D4', '#0891B2']; // Teal gradient for CBD
    } else {
      return ['#6B7280', '#4B5563']; // Default gray gradient
    }
  };

  const getStrainTypeColor = (type?: string | null) => {
    if (!type) return '#6B7280';
    const lowerType = type.toLowerCase();
    if (lowerType?.includes('indica')) {
      return '#3B82F6'; // Blue for Indica/Indica Dominant
    } else if (lowerType?.includes('sativa')) {
      return '#FB923C'; // Bright orange for Sativa/Sativa Dominant
    } else if (lowerType?.includes('hybrid')) {
      return '#10B981'; // Green for Hybrid
    } else if (lowerType?.includes('blend')) {
      return '#A855F7'; // Purple for Blend
    } else if (lowerType?.includes('cbd')) {
      return '#06B6D4'; // Teal for CBD
    } else {
      return '#6B7280'; // Gray default
    }
  };

  return (
    <TouchableOpacity style={styles.cardContainer} onPress={handlePress} activeOpacity={0.95}>
      <LinearGradient
        colors={isDark ? Gradients.cardDark : Gradients.card}
        style={styles.card}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
      >
        <View style={styles.imageContainer}>
          {!!image && (
            <Image
              source={{ uri: image }}
              style={styles.image}
              resizeMode="cover"
            />
          )}

          {inStock === false && (
            <View style={styles.outOfStockBadge}>
              <Text style={styles.outOfStockText}>Out of Stock</Text>
            </View>
          )}

          {!!strainType && (
            <LinearGradient
              colors={getStrainTypeGradient(strainType)}
              style={styles.strainBadge}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
            >
              <Text style={styles.strainText}>
                {formatStrainType(strainType)}
              </Text>
            </LinearGradient>
          )}

          {isAuthenticated && (
            <TouchableOpacity
              style={styles.wishlistButton}
              onPress={handleToggleWishlist}
              disabled={isWishlistLoading}
              activeOpacity={0.8}
            >
              <LinearGradient
                colors={inWishlist ? ['#EF4444', '#DC2626'] : ['rgba(0,0,0,0.5)', 'rgba(0,0,0,0.5)']}
                style={styles.wishlistButtonGradient}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
              >
                <Ionicons
                  name={inWishlist ? 'heart' : 'heart-outline'}
                  size={18}
                  color="white"
                />
              </LinearGradient>
            </TouchableOpacity>
          )}
        </View>
        <View style={styles.info}>
          {Boolean(product.brand) && (
            <Text style={styles.brand} numberOfLines={1}>
              {String(product.brand)}
            </Text>
          )}

          <Text style={styles.name} numberOfLines={2}>
            {product.name || 'Unnamed Product'}
          </Text>
          <View style={styles.cannabinoids}>
            {!!(thcContent?.display && thcContent.display !== "0%" && thcContent.display !== "0.0-0.0%") && (
              <Text style={styles.thc}>THC {thcContent.display}</Text>
            )}
            {!!(cbdContent?.display && cbdContent.display !== "0%" && cbdContent.display !== "0.0-0.0%") && (
              <Text style={styles.cbd}>CBD {cbdContent.display}</Text>
            )}
          </View>

          {!!product.rating && product.rating > 0 && (
            <View style={styles.rating}>
              <Ionicons name="star" size={12} color="#FFC107" />
              <Text style={styles.ratingText}>{product.rating.toFixed(1)}</Text>
              {product.reviewCount !== undefined && product.reviewCount !== null && (
                <Text style={styles.ratingCount}>({product.reviewCount})</Text>
              )}
            </View>
          )}

          <View style={styles.footer}>
            <View>
              <Text style={styles.price}>
                ${price ? price.toFixed(2) : '0.00'}
              </Text>
              {!!product.size && (
                <Text style={styles.size}>{product.size}</Text>
              )}
            </View>
            <TouchableOpacity
              onPress={handleAddToCart}
              disabled={inStock === false}
              activeOpacity={0.8}
            >
              <LinearGradient
                colors={cartItem ? ['#10B981', '#059669'] : ['#3B82F6', '#2563EB']}
                style={[
                  styles.addButton,
                  inStock === false && styles.addButtonDisabled,
                ]}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
              >
                {cartItem ? (
                  <React.Fragment>
                    <Ionicons name="checkmark" size={16} color="white" />
                    <Text style={styles.addButtonText}>{cartItem.quantity}</Text>
                  </React.Fragment>
                ) : (
                  <Ionicons name="add" size={20} color="white" />
                )}
              </LinearGradient>
            </TouchableOpacity>
          </View>
        </View>
      </LinearGradient>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  cardContainer: {
    width: cardWidth,
    marginBottom: 16,
  },
  card: {
    width: '100%',
    borderRadius: BorderRadius.xl,
    borderWidth: 1.5,
    borderColor: 'rgba(255, 255, 255, 0.5)',
    overflow: 'hidden',
    ...Shadows.colorful,
  },
  imageContainer: {
    width: '100%',
    height: cardWidth * 0.8,
    borderTopLeftRadius: BorderRadius.xl,
    borderTopRightRadius: BorderRadius.xl,
    overflow: 'hidden',
    backgroundColor: theme.surface,
  },
  image: {
    width: '100%',
    height: '100%',
  },
  placeholderImage: {
    width: '100%',
    height: '100%',
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: theme.surface,
  },
  outOfStockBadge: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(239, 68, 68, 0.85)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  outOfStockText: {
    color: 'white',
    fontSize: 14,
    fontWeight: '700',
    letterSpacing: 1,
  },
  strainBadge: {
    position: 'absolute',
    top: 8,
    left: 8,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: BorderRadius.full,
    borderWidth: 1.5,
    borderColor: 'rgba(255, 255, 255, 0.5)',
    ...Shadows.small,
  },
  strainText: {
    color: 'white',
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  info: {
    padding: 12,
  },
  brand: {
    fontSize: 11,
    color: theme.textTertiary,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 2,
  },
  name: {
    fontSize: 14,
    fontWeight: '600',
    color: theme.text,
    marginBottom: 6,
    minHeight: 36,
  },
  cannabinoids: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 4,
  },
  thc: {
    fontSize: 12,
    color: '#FF6B35',
    fontWeight: '700',
    backgroundColor: 'rgba(255, 107, 53, 0.15)',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: BorderRadius.md,
    borderWidth: 1,
    borderColor: 'rgba(255, 107, 53, 0.3)',
  },
  cbd: {
    fontSize: 12,
    color: '#4A90E2',
    fontWeight: '700',
    backgroundColor: 'rgba(74, 144, 226, 0.15)',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: BorderRadius.md,
    borderWidth: 1,
    borderColor: 'rgba(74, 144, 226, 0.3)',
  },
  rating: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginBottom: 8,
  },
  ratingText: {
    fontSize: 12,
    color: theme.text,
    fontWeight: '500',
  },
  ratingCount: {
    fontSize: 11,
    color: theme.textSecondary,
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  price: {
    fontSize: 18,
    fontWeight: '800',
    color: '#059669',
  },
  size: {
    fontSize: 11,
    color: theme.textSecondary,
    marginTop: 2,
  },
  addButton: {
    width: 40,
    height: 40,
    borderRadius: BorderRadius.full,
    justifyContent: 'center',
    alignItems: 'center',
    flexDirection: 'row',
    gap: 2,
    borderWidth: 1.5,
    borderColor: 'rgba(255, 255, 255, 0.5)',
    ...Shadows.medium,
  },
  addButtonDisabled: {
    opacity: 0.4,
  },
  addButtonText: {
    color: 'white',
    fontSize: 12,
    fontWeight: '600',
  },
  wishlistButton: {
    position: 'absolute',
    top: 8,
    right: 8,
    zIndex: 10,
  },
  wishlistButtonGradient: {
    width: 32,
    height: 32,
    borderRadius: BorderRadius.full,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1.5,
    borderColor: 'rgba(255, 255, 255, 0.5)',
    ...Shadows.medium,
  },
});