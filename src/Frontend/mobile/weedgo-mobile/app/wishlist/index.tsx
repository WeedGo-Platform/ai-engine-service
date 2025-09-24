import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { FlashList } from '@shopify/flash-list';
import { Ionicons } from '@expo/vector-icons';
import { useRouter, Stack } from 'expo-router';
import { useWishlistStore } from '@/stores/wishlistStore';
import useCartStore from '@/stores/cartStore';
import { ProductCard } from '@/components/ProductCard';
import { EmptyState } from '@/components/EmptyState';
import { Colors } from '@/constants/Colors';
import { Product } from '@/types/api.types';

export default function WishlistScreen() {
  const router = useRouter();
  const { items, removeFromWishlist, clearWishlist } = useWishlistStore();
  const { addItem } = useCartStore();
  const [removingIds, setRemovingIds] = React.useState<Set<string>>(new Set());

  const handleProductPress = (product: Product) => {
    router.push(`/product/${product.id}`);
  };

  const handleRemoveFromWishlist = async (productId: string) => {
    setRemovingIds(prev => new Set([...prev, productId]));
    await removeFromWishlist(productId);
    setRemovingIds(prev => {
      const newSet = new Set(prev);
      newSet.delete(productId);
      return newSet;
    });
  };

  const handleAddToCart = async (product: Product) => {
    await addItem(product, 1);
    // Optionally remove from wishlist after adding to cart
    // await removeFromWishlist(product.id);
  };

  const handleClearAll = () => {
    clearWishlist();
  };

  const renderProduct = ({ item }: { item: typeof items[0] }) => (
    <View style={styles.productContainer}>
      <ProductCard
        product={item.product}
        onPress={() => handleProductPress(item.product)}
      />
      <View style={styles.productActions}>
        <TouchableOpacity
          style={styles.actionButton}
          onPress={() => handleAddToCart(item.product)}
        >
          <Ionicons name="cart-outline" size={20} color={Colors.light.primary} />
          <Text style={styles.actionText}>Add to Cart</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.actionButton, styles.removeButton]}
          onPress={() => handleRemoveFromWishlist(item.productId)}
          disabled={removingIds.has(item.productId)}
        >
          {removingIds.has(item.productId) ? (
            <ActivityIndicator size="small" color={Colors.light.error} />
          ) : (
            <>
              <Ionicons name="heart-dislike-outline" size={20} color={Colors.light.error} />
              <Text style={[styles.actionText, styles.removeText]}>Remove</Text>
            </>
          )}
        </TouchableOpacity>
      </View>
    </View>
  );

  const renderEmpty = () => (
    <EmptyState
      icon="heart-outline"
      title="Your wishlist is empty"
      subtitle="Save your favorite products here for easy access later"
      actionLabel="Start Shopping"
      onAction={() => router.push('/(tabs)/')}
    />
  );

  const renderHeader = () => {
    if (items.length === 0) return null;

    return (
      <View style={styles.header}>
        <Text style={styles.headerTitle}>{items.length} items in wishlist</Text>
        <TouchableOpacity onPress={handleClearAll}>
          <Text style={styles.clearAllText}>Clear All</Text>
        </TouchableOpacity>
      </View>
    );
  };

  return (
    <>
      <Stack.Screen
        options={{
          title: 'Wishlist',
          headerShown: true,
          headerStyle: {
            backgroundColor: Colors.light.background,
          },
          headerTintColor: Colors.light.text,
          headerRight: () => (
            <TouchableOpacity
              onPress={() => router.push('/(tabs)/cart')}
              style={styles.cartButton}
            >
              <Ionicons name="cart-outline" size={24} color={Colors.light.text} />
            </TouchableOpacity>
          ),
        }}
      />

      <SafeAreaView style={styles.container} edges={['bottom']}>
        <FlashList
          data={items}
          renderItem={renderProduct}
          ListHeaderComponent={renderHeader}
          ListEmptyComponent={renderEmpty}
          estimatedItemSize={250}
          keyExtractor={(item) => item.productId}
          contentContainerStyle={styles.listContent}
          ItemSeparatorComponent={() => <View style={styles.separator} />}
          showsVerticalScrollIndicator={false}
        />
      </SafeAreaView>
    </>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.light.background,
  },
  listContent: {
    paddingHorizontal: 16,
    paddingVertical: 16,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  headerTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.light.text,
  },
  clearAllText: {
    fontSize: 14,
    color: Colors.light.error,
  },
  productContainer: {
    marginBottom: 8,
  },
  productActions: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 8,
  },
  actionButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 4,
    paddingVertical: 8,
    paddingHorizontal: 12,
    backgroundColor: Colors.light.card,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: Colors.light.border,
  },
  removeButton: {
    borderColor: Colors.light.error + '30',
  },
  actionText: {
    fontSize: 14,
    color: Colors.light.text,
  },
  removeText: {
    color: Colors.light.error,
  },
  separator: {
    height: 16,
  },
  cartButton: {
    marginRight: 16,
  },
});