import React from 'react';
import {
  View,
  Text,
  Image,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  Alert,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useCartStore } from '../../stores/cartStore';
import { Colors } from '@/constants/Colors';
import Toast from 'react-native-toast-message';

interface Product {
  id: string;
  name: string;
  price: number;
  image?: string;
  image_url?: string;
  thc_content?: number;
  cbd_content?: number;
  category?: string;
  sub_category?: string;
  strain_type?: string;
  inventory_quantity?: number;
  inventory_count?: number;
  brand?: string;
  size?: string;
  stock_status?: string;
  short_description?: string;
}

interface ProductMessageProps {
  products: Product[];
  message?: string;
}

export function ProductMessage({ products, message }: ProductMessageProps) {
  const router = useRouter();
  const { addItem } = useCartStore();

  const handleAddToCart = (product: Product) => {
    const inventory = product.inventory_count ?? product.inventory_quantity ?? 0;
    if (inventory === 0) {
      Alert.alert('Out of Stock', 'This product is currently out of stock.');
      return;
    }

    addItem(product, 1);
    Toast.show({
      type: 'success',
      text1: 'Added to cart',
      text2: product.name,
      visibilityTime: 2000,
    });
  };

  const handleProductPress = (product: Product) => {
    router.push(`/product/${product.id}`);
  };

  return (
    <View style={styles.container}>
      {message && (
        <Text style={styles.message}>{message}</Text>
      )}

      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.scrollContent}
      >
        {products.map((product) => (
          <TouchableOpacity
            key={product.id}
            style={styles.productCard}
            onPress={() => handleProductPress(product)}
            activeOpacity={0.9}
          >
            <Image
              source={{ uri: product.image_url || product.image || 'https://via.placeholder.com/180x120' }}
              style={styles.productImage}
              defaultSource={{ uri: 'https://via.placeholder.com/180x120' }}
            />

            <View style={styles.productInfo}>
              <Text style={styles.productName} numberOfLines={2}>
                {product.name}
              </Text>

              {product.brand && (
                <Text style={styles.brandText}>{product.brand}</Text>
              )}

              {product.short_description && (
                <Text style={styles.description} numberOfLines={2}>
                  {product.short_description}
                </Text>
              )}

              <View style={styles.badgeRow}>
                {product.category && (
                  <View style={styles.badge}>
                    <Text style={styles.badgeText}>{product.category}</Text>
                  </View>
                )}
                {product.strain_type && (
                  <View style={[styles.badge, styles.strainBadge]}>
                    <Text style={styles.badgeText}>{product.strain_type}</Text>
                  </View>
                )}
              </View>

              <View style={styles.cannabinoids}>
                {product.thc_content !== undefined && (
                  <Text style={styles.cannabinoidText}>
                    THC: {product.thc_content}%
                  </Text>
                )}
                {product.cbd_content !== undefined && (
                  <Text style={styles.cannabinoidText}>
                    CBD: {product.cbd_content}%
                  </Text>
                )}
              </View>

              <View style={styles.priceRow}>
                <View>
                  <Text style={styles.price}>${product.price.toFixed(2)}</Text>
                  {product.size && (
                    <Text style={styles.sizeText}>{product.size}</Text>
                  )}
                </View>
                {product.stock_status && product.stock_status !== 'In Stock' && (
                  <Text style={[styles.stockStatus, product.stock_status === 'Out of Stock' && styles.outOfStock]}>
                    {product.stock_status}
                  </Text>
                )}
              </View>

              <TouchableOpacity
                style={[
                  styles.addButton,
                  ((product.inventory_count ?? product.inventory_quantity ?? 0) === 0) && styles.addButtonDisabled
                ]}
                onPress={(e) => {
                  e.stopPropagation();
                  handleAddToCart(product);
                }}
                disabled={(product.inventory_count ?? product.inventory_quantity ?? 0) === 0}
              >
                <Ionicons name="add" size={20} color="#fff" />
                <Text style={styles.addButtonText}>Add to Cart</Text>
              </TouchableOpacity>
            </View>
          </TouchableOpacity>
        ))}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginVertical: 8,
  },
  message: {
    fontSize: 15,
    color: Colors.light.text,
    paddingHorizontal: 20,
    marginBottom: 12,
  },
  scrollContent: {
    paddingHorizontal: 16,
  },
  productCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    marginHorizontal: 4,
    width: 180,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  productImage: {
    width: 180,
    height: 120,
    borderTopLeftRadius: 12,
    borderTopRightRadius: 12,
    backgroundColor: '#f5f5f5',
  },
  productInfo: {
    padding: 12,
  },
  productName: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.light.text,
    marginBottom: 4,
    minHeight: 20,
  },
  brandText: {
    fontSize: 12,
    color: '#888',
    marginBottom: 4,
  },
  description: {
    fontSize: 11,
    color: '#666',
    marginBottom: 6,
    lineHeight: 14,
  },
  badgeRow: {
    flexDirection: 'row',
    gap: 6,
    marginBottom: 6,
  },
  badge: {
    backgroundColor: Colors.light.primaryLight,
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
    alignSelf: 'flex-start',
  },
  strainBadge: {
    backgroundColor: '#e8f5e9',
  },
  badgeText: {
    fontSize: 10,
    color: Colors.light.primary,
    fontWeight: '600',
    textTransform: 'uppercase',
  },
  sizeText: {
    fontSize: 11,
    color: '#888',
    marginTop: 2,
  },
  stockStatus: {
    fontSize: 11,
    color: '#f59e0b',
    fontWeight: '600',
  },
  cannabinoids: {
    flexDirection: 'row',
    marginBottom: 8,
    gap: 12,
  },
  cannabinoidText: {
    fontSize: 12,
    color: '#666',
  },
  priceRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  price: {
    fontSize: 18,
    fontWeight: '700',
    color: Colors.light.primary,
  },
  outOfStock: {
    fontSize: 11,
    color: '#ef4444',
    fontWeight: '600',
  },
  addButton: {
    backgroundColor: Colors.light.primary,
    borderRadius: 8,
    paddingVertical: 8,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 4,
  },
  addButtonDisabled: {
    backgroundColor: '#ccc',
  },
  addButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
});