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
  image_url: string;
  thc_content?: number;
  cbd_content?: number;
  category?: string;
  strain_type?: string;
  inventory_quantity?: number;
}

interface ProductMessageProps {
  products: Product[];
  message?: string;
}

export function ProductMessage({ products, message }: ProductMessageProps) {
  const router = useRouter();
  const { addToCart } = useCartStore();

  const handleAddToCart = (product: Product) => {
    if (product.inventory_quantity === 0) {
      Alert.alert('Out of Stock', 'This product is currently out of stock.');
      return;
    }

    addToCart(product);
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
              source={{ uri: product.image_url }}
              style={styles.productImage}
            />

            <View style={styles.productInfo}>
              <Text style={styles.productName} numberOfLines={2}>
                {product.name}
              </Text>

              {product.category && (
                <View style={styles.badge}>
                  <Text style={styles.badgeText}>{product.category}</Text>
                </View>
              )}

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
                <Text style={styles.price}>${product.price.toFixed(2)}</Text>
                {product.inventory_quantity === 0 && (
                  <Text style={styles.outOfStock}>Out of Stock</Text>
                )}
              </View>

              <TouchableOpacity
                style={[
                  styles.addButton,
                  product.inventory_quantity === 0 && styles.addButtonDisabled
                ]}
                onPress={(e) => {
                  e.stopPropagation();
                  handleAddToCart(product);
                }}
                disabled={product.inventory_quantity === 0}
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
    marginBottom: 6,
    height: 36,
  },
  badge: {
    backgroundColor: Colors.light.primaryLight,
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
    alignSelf: 'flex-start',
    marginBottom: 6,
  },
  badgeText: {
    fontSize: 10,
    color: Colors.light.primary,
    fontWeight: '600',
    textTransform: 'uppercase',
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