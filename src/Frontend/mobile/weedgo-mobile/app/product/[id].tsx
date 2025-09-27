import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Image,
  ActivityIndicator,
  Dimensions,
  SafeAreaView,
} from 'react-native';
import { useLocalSearchParams, useRouter, Stack } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import useProductsStore from '@/stores/productsStore';
import useCartStore from '@/stores/cartStore';
import { Colors } from '@/constants/Colors';
import { Product, Terpene } from '@/types/api.types';
import { ReviewsSection } from '@/components/reviews/ReviewsSection';

const { width } = Dimensions.get('window');

export default function ProductDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const { loadProductDetails, getProductById } = useProductsStore();
  const { addItem, getCartItem } = useCartStore();

  const [product, setProduct] = useState<Product | null>(null);
  const [loading, setLoading] = useState(true);
  const [quantity, setQuantity] = useState(1);
  const [selectedSize, setSelectedSize] = useState<string | undefined>();
  const [descriptionExpanded, setDescriptionExpanded] = useState(false);
  const [selectedImageIndex, setSelectedImageIndex] = useState(0);

  const cartItem = product ? getCartItem(product.sku) : undefined;

  useEffect(() => {
    loadProduct();
  }, [id]);

  const loadProduct = async () => {
    if (!id) return;

    setLoading(true);
    try {
      // Try to get from local state first
      let productData = getProductById(id);

      // If not in local state or need more details, fetch from API
      if (!productData || !productData.description) {
        productData = await loadProductDetails(id);
      }

      setProduct(productData);
    } catch (error) {
      console.error('Failed to load product:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddToCart = () => {
    if (!product) return;
    addItem(product, quantity, selectedSize);
    // Show success feedback
  };

  const incrementQuantity = () => {
    setQuantity(prev => prev + 1);
  };

  const decrementQuantity = () => {
    setQuantity(prev => (prev > 1 ? prev - 1 : 1));
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

  const renderTerpenes = (terpenes: Terpene[]) => {
    return (
      <View style={styles.terpenesContainer}>
        <Text style={styles.sectionTitle}>Terpene Profile</Text>
        {terpenes.map((terpene, index) => (
          <View key={index} style={styles.terpeneItem}>
            <View style={styles.terpeneHeader}>
              <Text style={styles.terpeneName}>{terpene.name}</Text>
              <Text style={styles.terpenePercentage}>
                {terpene.percentage}%
              </Text>
            </View>
            <View style={styles.terpeneBar}>
              <View
                style={[
                  styles.terpeneBarFill,
                  { width: `${(terpene.percentage / 5) * 100}%` },
                ]}
              />
            </View>
            {terpene.effects && terpene.effects.length > 0 && (
              <View style={styles.terpeneEffects}>
                {terpene.effects.map((effect, i) => (
                  <Text key={i} style={styles.terpeneEffect}>
                    {terpene.name}
                  </Text>
                ))}
              </View>
            )}
          </View>
        ))}
      </View>
    );
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <Stack.Screen
          options={{
            headerShown: true,
            headerTitle: '',
            headerLeft: () => (
              <TouchableOpacity onPress={() => router.back()}>
                <Ionicons name="arrow-back" size={24} color={Colors.light.text} />
              </TouchableOpacity>
            ),
          }}
        />
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={Colors.light.primary} />
        </View>
      </SafeAreaView>
    );
  }

  if (!product) {
    return (
      <SafeAreaView style={styles.container}>
        <Stack.Screen
          options={{
            headerShown: true,
            headerTitle: 'Product Not Found',
            headerLeft: () => (
              <TouchableOpacity onPress={() => router.back()}>
                <Ionicons name="arrow-back" size={24} color={Colors.light.text} />
              </TouchableOpacity>
            ),
          }}
        />
        <View style={styles.errorContainer}>
          <Ionicons name="alert-circle-outline" size={64} color={Colors.light.error} />
          <Text style={styles.errorText}>Product not found</Text>
          <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
            <Text style={styles.backButtonText}>Go Back</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  const images = product.images && product.images.length > 0
    ? product.images
    : [product.image];

  return (
    <SafeAreaView style={styles.container}>
      <Stack.Screen
        options={{
          headerShown: true,
          headerTitle: product.name,
          headerLeft: () => (
            <TouchableOpacity onPress={() => router.back()}>
              <Ionicons name="arrow-back" size={24} color={Colors.light.text} />
            </TouchableOpacity>
          ),
          headerRight: () => (
            <TouchableOpacity onPress={() => router.push('/(tabs)/cart')}>
              <Ionicons name="cart-outline" size={24} color={Colors.light.text} />
              {cartItem && (
                <View style={styles.cartBadge}>
                  <Text style={styles.cartBadgeText}>{cartItem.quantity}</Text>
                </View>
              )}
            </TouchableOpacity>
          ),
        }}
      />

      <ScrollView showsVerticalScrollIndicator={false}>
        {/* Image Carousel */}
        <View style={styles.imageContainer}>
          <ScrollView
            horizontal
            pagingEnabled
            showsHorizontalScrollIndicator={false}
            onScroll={(event) => {
              const index = Math.round(
                event.nativeEvent.contentOffset.x / width
              );
              setSelectedImageIndex(index);
            }}
            scrollEventThrottle={16}
          >
            {images.map((image, index) => (
              <Image
                key={index}
                source={{ uri: image }}
                style={styles.productImage}
                resizeMode="cover"
              />
            ))}
          </ScrollView>

          {/* Image Dots Indicator */}
          {images.length > 1 && (
            <View style={styles.dotsContainer}>
              {images.map((_, index) => (
                <View
                  key={index}
                  style={[
                    styles.dot,
                    index === selectedImageIndex && styles.activeDot,
                  ]}
                />
              ))}
            </View>
          )}

          {/* Stock Badge */}
          {product.inStock === false && (
            <View style={styles.outOfStockOverlay}>
              <Text style={styles.outOfStockText}>Out of Stock</Text>
            </View>
          )}
        </View>

        <View style={styles.infoContainer}>
          <Text style={styles.brand}>{product.brand}</Text>
          <Text style={styles.productName}>{product.name}</Text>

          {/* Price and Size */}
          <View style={styles.priceContainer}>
            <Text style={styles.price}>${product.price}</Text>
            {product.size && (
              <Text style={styles.size}>{product.size}</Text>
            )}
          </View>

          {/* Strain Type and Cannabinoids */}
          <View style={styles.cannabinoidContainer}>
            {product.strain_type && (
              <View
                style={[
                  styles.strainBadge,
                  { backgroundColor: getStrainTypeColor(product.strain_type) },
                ]}
              >
                <Text style={styles.strainText}>
                  {product.strain_type.toUpperCase()}
                </Text>
              </View>
            )}

            <View style={styles.cannabinoids}>
              {product.thc_content !== undefined && (
                <View style={styles.cannabinoidItem}>
                  <Text style={styles.cannabinoidLabel}>THC</Text>
                  <Text style={styles.cannabinoidValue}>
                    {product.thc_content}%
                  </Text>
                </View>
              )}
              {product.cbd_content !== undefined && (
                <View style={styles.cannabinoidItem}>
                  <Text style={styles.cannabinoidLabel}>CBD</Text>
                  <Text style={styles.cannabinoidValue}>
                    {product.cbd_content}%
                  </Text>
                </View>
              )}
            </View>
          </View>

          {/* Rating */}
          {product.rating && product.rating > 0 && (
            <View style={styles.ratingContainer}>
              <View style={styles.rating}>
                <Ionicons name="star" size={16} color="#FFB800" />
                <Text style={styles.ratingText}>
                  {product.rating.toFixed(1)}
                </Text>
                {product.rating_count && (
                  <Text style={styles.ratingCount}>
                    ({product.rating_count} reviews)
                  </Text>
                )}
              </View>
              <TouchableOpacity>
                <Text style={styles.reviewLink}>Read Reviews</Text>
              </TouchableOpacity>
            </View>
          )}

          {/* Effects */}
          {product.terpenes && product.terpenes.length > 0 && (
            <View style={styles.effectsContainer}>
              <Text style={styles.sectionTitle}>Effects</Text>
              <View style={styles.effectsList}>
                {product.terpenes.map((terpene, index) => (
                  <View key={index} style={styles.effectPill}>
                    <Text style={styles.effectText}>{terpene.name}</Text>
                  </View>
                ))}
              </View>
            </View>
          )}

          {/* Terpenes */}
          {product.terpenes && product.terpenes.length > 0 &&
            renderTerpenes(product.terpenes)
          }

          {/* Description */}
          <View style={styles.descriptionContainer}>
            <Text style={styles.sectionTitle}>Description</Text>
            <Text
              style={styles.description}
              numberOfLines={descriptionExpanded ? undefined : 3}
            >
              {product.description}
            </Text>
            {product.description && product.description.length > 150 && (
              <TouchableOpacity
                onPress={() => setDescriptionExpanded(!descriptionExpanded)}
              >
                <Text style={styles.expandText}>
                  {descriptionExpanded ? 'Show Less' : 'Read More'}
                </Text>
              </TouchableOpacity>
            )}
          </View>
        </View>

        {/* Reviews Section */}
        {product && (
          <View style={styles.reviewsSection}>
            <ReviewsSection
              productId={product.id}
              productName={product.name}
            />
          </View>
        )}
      </ScrollView>

      {/* Bottom Add to Cart Bar */}
      <View style={styles.bottomBar}>
        <View style={styles.quantitySelector}>
          <TouchableOpacity
            style={styles.quantityButton}
            onPress={decrementQuantity}
          >
            <Ionicons name="remove" size={20} color={Colors.light.text} />
          </TouchableOpacity>
          <Text style={styles.quantityText}>{quantity}</Text>
          <TouchableOpacity
            style={styles.quantityButton}
            onPress={incrementQuantity}
          >
            <Ionicons name="add" size={20} color={Colors.light.text} />
          </TouchableOpacity>
        </View>

        <TouchableOpacity
          style={[
            styles.addToCartButton,
            product.inStock === false && styles.addToCartButtonDisabled,
          ]}
          onPress={handleAddToCart}
          disabled={product.inStock === false}
        >
          <Ionicons name="cart-outline" size={20} color="white" />
          <Text style={styles.addToCartText}>
            {product.inStock === false
              ? 'Out of Stock'
              : `Add to Cart • $${(product.price * quantity).toFixed(2)}`}
          </Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.light.background,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
  },
  errorText: {
    fontSize: 16,
    color: Colors.light.gray,
    marginTop: 16,
  },
  backButton: {
    marginTop: 24,
    paddingHorizontal: 24,
    paddingVertical: 12,
    backgroundColor: Colors.light.primary,
    borderRadius: 8,
  },
  backButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
  imageContainer: {
    width: width,
    height: width * 0.8,
    backgroundColor: Colors.light.backgroundSecondary,
  },
  productImage: {
    width: width,
    height: width * 0.8,
  },
  dotsContainer: {
    position: 'absolute',
    bottom: 16,
    left: 0,
    right: 0,
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 6,
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: 'rgba(255, 255, 255, 0.5)',
  },
  activeDot: {
    backgroundColor: 'white',
    width: 24,
  },
  outOfStockOverlay: {
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
    fontSize: 20,
    fontWeight: '600',
  },
  infoContainer: {
    padding: 20,
    paddingBottom: 100,
  },
  brand: {
    fontSize: 14,
    color: Colors.light.gray,
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  productName: {
    fontSize: 24,
    fontWeight: '700',
    color: Colors.light.text,
    marginTop: 4,
  },
  priceContainer: {
    flexDirection: 'row',
    alignItems: 'baseline',
    gap: 8,
    marginTop: 12,
  },
  price: {
    fontSize: 28,
    fontWeight: '700',
    color: Colors.light.primary,
  },
  size: {
    fontSize: 14,
    color: Colors.light.gray,
  },
  cannabinoidContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginTop: 16,
  },
  strainBadge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
  },
  strainText: {
    color: 'white',
    fontSize: 12,
    fontWeight: '600',
  },
  cannabinoids: {
    flexDirection: 'row',
    gap: 16,
  },
  cannabinoidItem: {
    alignItems: 'center',
  },
  cannabinoidLabel: {
    fontSize: 12,
    color: Colors.light.gray,
  },
  cannabinoidValue: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.light.text,
  },
  ratingContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 16,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: Colors.light.border,
  },
  rating: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  ratingText: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.light.text,
  },
  ratingCount: {
    fontSize: 14,
    color: Colors.light.gray,
  },
  reviewLink: {
    fontSize: 14,
    color: Colors.light.primary,
    fontWeight: '500',
  },
  effectsContainer: {
    marginTop: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: Colors.light.text,
    marginBottom: 12,
  },
  effectsList: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  effectPill: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    backgroundColor: Colors.light.primaryLight,
    borderRadius: 16,
  },
  effectText: {
    fontSize: 14,
    color: Colors.light.primary,
    fontWeight: '500',
  },
  terpenesContainer: {
    marginTop: 24,
  },
  terpeneItem: {
    marginBottom: 12,
  },
  terpeneHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  terpeneName: {
    fontSize: 14,
    fontWeight: '500',
    color: Colors.light.text,
  },
  terpenePercentage: {
    fontSize: 14,
    color: Colors.light.gray,
  },
  terpeneBar: {
    height: 8,
    backgroundColor: Colors.light.backgroundSecondary,
    borderRadius: 4,
    overflow: 'hidden',
  },
  terpeneBarFill: {
    height: '100%',
    backgroundColor: Colors.light.primary,
  },
  terpeneEffects: {
    flexDirection: 'row',
    gap: 6,
    marginTop: 4,
  },
  terpeneEffect: {
    fontSize: 11,
    color: Colors.light.gray,
  },
  descriptionContainer: {
    marginTop: 24,
  },
  description: {
    fontSize: 14,
    lineHeight: 20,
    color: Colors.light.text,
  },
  expandText: {
    fontSize: 14,
    color: Colors.light.primary,
    fontWeight: '500',
    marginTop: 8,
  },
  bottomBar: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: 'white',
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    gap: 16,
    borderTopWidth: 1,
    borderTopColor: Colors.light.border,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 10,
  },
  quantitySelector: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.light.backgroundSecondary,
    borderRadius: 8,
    paddingHorizontal: 4,
  },
  quantityButton: {
    padding: 8,
  },
  quantityText: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.light.text,
    marginHorizontal: 16,
  },
  addToCartButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: Colors.light.primary,
    paddingVertical: 14,
    borderRadius: 8,
    gap: 8,
  },
  addToCartButtonDisabled: {
    backgroundColor: Colors.light.gray,
  },
  addToCartText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
  cartBadge: {
    position: 'absolute',
    top: -8,
    right: -8,
    backgroundColor: Colors.light.primary,
    borderRadius: 10,
    minWidth: 20,
    height: 20,
    justifyContent: 'center',
    alignItems: 'center',
  },
  cartBadgeText: {
    color: 'white',
    fontSize: 11,
    fontWeight: '600',
  },
  reviewsSection: {
    marginTop: 24,
    paddingHorizontal: 16,
    paddingBottom: 16,
  },
});