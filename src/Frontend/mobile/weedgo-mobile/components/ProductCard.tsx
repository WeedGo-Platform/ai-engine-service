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
import { Colors } from '@/constants/Colors';

const { width } = Dimensions.get('window');
const cardWidth = (width - 48) / 2; // 2 columns with padding

interface ProductCardProps {
  product: Product;
  onPress?: () => void;
}

export function ProductCard({ product, onPress }: ProductCardProps) {
  const router = useRouter();
  const { addItem, getCartItem } = useCartStore();
  const cartItem = getCartItem(product.sku || product.id);

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

  const getStrainTypeColor = (type?: string) => {
    switch (type) {
      case 'indica':
        return '#9C27B0';
      case 'sativa':
        return '#4CAF50';
      case 'hybrid':
        return '#FF9800';
      case 'cbd':
        return '#2196F3';
      default:
        return Colors.light.gray;
    }
  };

  return (
    <TouchableOpacity style={styles.card} onPress={handlePress}>
      <View style={styles.imageContainer}>
        {product.image || product.images?.[0] ? (
          <Image
            source={{ uri: product.image || product.images[0] }}
            style={styles.image}
            resizeMode="cover"
          />
        ) : (
          <View style={styles.placeholderImage}>
            <Ionicons name="leaf-outline" size={40} color={Colors.light.gray} />
          </View>
        )}

        {!product.inStock && (
          <View style={styles.outOfStockBadge}>
            <Text style={styles.outOfStockText}>Out of Stock</Text>
          </View>
        )}

        {product.strainType && (
          <View
            style={[
              styles.strainBadge,
              { backgroundColor: getStrainTypeColor(product.strainType?.toLowerCase()) },
            ]}
          >
            <Text style={styles.strainText}>
              {(product.strainType || '').toUpperCase()}
            </Text>
          </View>
        )}
      </View>
      <View style={styles.info}>
        {product.brand ? (
          <Text style={styles.brand} numberOfLines={1}>
            {product.brand}
          </Text>
        ) : null}

        <Text style={styles.name} numberOfLines={2}>
          {product.name || 'Unnamed Product'}
        </Text>

        <View style={styles.cannabinoids}>
          {product.thcContent?.display && product.thcContent.display !== "0.0-0.0%" && (
            <Text style={styles.thc}>THC {product.thcContent.display}</Text>
          )}
          {product.cbdContent?.display && product.cbdContent.display !== "0.0-0.0%" && (
            <Text style={styles.cbd}>CBD {product.cbdContent.display}</Text>
          )}
        </View>

        {product.rating && product.rating > 0 && (
          <View style={styles.rating}>
            <Ionicons name="star" size={12} color="#FFB800" />
            <Text style={styles.ratingText}>{product.rating.toFixed(1)}</Text>
            {product.reviewCount !== undefined && (
              <Text style={styles.ratingCount}>({product.reviewCount})</Text>
            )}
          </View>
        )}

        <View style={styles.footer}>
          <View>
            <Text style={styles.price}>
              ${product.price || product.basePrice || '0.00'}
            </Text>
            {product.size ? (
              <Text style={styles.size}>{product.size}</Text>
            ) : null}
          </View>

          <TouchableOpacity
            style={[
              styles.addButton,
              !product.inStock && styles.addButtonDisabled,
              cartItem && styles.addButtonAdded,
            ]}
            onPress={handleAddToCart}
            disabled={!product.inStock}
          >
            {cartItem ? (
              <>
                <Ionicons name="checkmark" size={16} color="white" />
                <Text style={styles.addButtonText}>{cartItem.quantity}</Text>
              </>
            ) : (
              <Ionicons name="add" size={20} color="white" />
            )}
          </TouchableOpacity>
        </View>
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: {
    width: cardWidth,
    backgroundColor: 'white',
    borderRadius: 12,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 4,
    elevation: 3,
  },
  imageContainer: {
    width: '100%',
    height: cardWidth * 0.8,
    borderTopLeftRadius: 12,
    borderTopRightRadius: 12,
    overflow: 'hidden',
    backgroundColor: Colors.light.backgroundSecondary,
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
    backgroundColor: Colors.light.backgroundSecondary,
  },
  outOfStockBadge: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  outOfStockText: {
    color: 'white',
    fontSize: 14,
    fontWeight: '600',
  },
  strainBadge: {
    position: 'absolute',
    top: 8,
    left: 8,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  strainText: {
    color: 'white',
    fontSize: 10,
    fontWeight: '600',
  },
  info: {
    padding: 12,
  },
  brand: {
    fontSize: 11,
    color: Colors.light.gray,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 2,
  },
  name: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.light.text,
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
    color: '#9C27B0',
    fontWeight: '500',
  },
  cbd: {
    fontSize: 12,
    color: '#2196F3',
    fontWeight: '500',
  },
  rating: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginBottom: 8,
  },
  ratingText: {
    fontSize: 12,
    color: Colors.light.text,
    fontWeight: '500',
  },
  ratingCount: {
    fontSize: 11,
    color: Colors.light.gray,
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  price: {
    fontSize: 18,
    fontWeight: '700',
    color: Colors.light.primary,
  },
  size: {
    fontSize: 11,
    color: Colors.light.gray,
    marginTop: 2,
  },
  addButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: Colors.light.primary,
    justifyContent: 'center',
    alignItems: 'center',
    flexDirection: 'row',
    gap: 2,
  },
  addButtonDisabled: {
    backgroundColor: Colors.light.gray,
  },
  addButtonAdded: {
    backgroundColor: Colors.light.success,
  },
  addButtonText: {
    color: 'white',
    fontSize: 12,
    fontWeight: '600',
  },
});