import React, { useEffect, useState, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  TextInput,
  RefreshControl,
  ActivityIndicator,
  Dimensions,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { FlashList } from '@shopify/flash-list';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { useAuthStore } from '@/stores/authStore';
import useProductsStore from '@/stores/productsStore';
import useCartStore from '@/stores/cartStore';
import { Colors } from '@/constants/Colors';
import { StoreSelector } from '@/components/StoreSelector';
import { CategoryTiles } from '@/components/CategoryTiles';
import { QuickFilters } from '@/components/QuickFilters';
import { ProductCard } from '@/components/ProductCard';
import { Product } from '@/types/api.types';

const { width } = Dimensions.get('window');

export default function HomeScreen() {
  const router = useRouter();
  const { user, isAuthenticated } = useAuthStore();
  const { getItemCount } = useCartStore();
  const {
    products,
    loading,
    refreshing,
    error,
    filters,
    pagination,
    loadProducts,
    loadCategories,
    setFilters,
    refreshProducts,
    loadMore,
    searchProducts,
  } = useProductsStore();

  const [searchQuery, setSearchQuery] = useState('');
  const [searchTimer, setSearchTimer] = useState<NodeJS.Timeout | null>(null);

  // Load initial data
  useEffect(() => {
    loadCategories();
    loadProducts(true);
  }, []);

  // Handle search with debouncing
  const handleSearch = useCallback((query: string) => {
    setSearchQuery(query);

    // Clear existing timer
    if (searchTimer) {
      clearTimeout(searchTimer);
    }

    // Set new timer for debounced search
    const timer = setTimeout(() => {
      searchProducts(query);
    }, 500);

    setSearchTimer(timer);

    return () => {
      if (timer) clearTimeout(timer);
    };
  }, [searchTimer]);

  // Handle category selection
  const handleCategorySelect = (categoryId: string) => {
    if (filters.category === categoryId) {
      // Deselect if same category
      setFilters({ category: undefined });
    } else {
      setFilters({ category: categoryId });
    }
  };

  // Handle quick filter selection
  const handleQuickFilterSelect = (filterId: string | undefined) => {
    setFilters({ quickFilter: filterId as any });
  };

  // Handle pull to refresh
  const handleRefresh = () => {
    refreshProducts();
  };

  // Handle load more (pagination)
  const handleLoadMore = () => {
    if (!loading && pagination.hasMore) {
      loadMore();
    }
  };

  // Render header components
  const renderHeader = () => (
    <View>
      {/* Store Selector */}
      <StoreSelector />

      {/* Search Bar */}
      <View style={styles.searchContainer}>
        <View style={styles.searchBar}>
          <Ionicons name="search" size={20} color={Colors.light.gray} />
          <TextInput
            style={styles.searchInput}
            placeholder="Search products..."
            value={searchQuery}
            onChangeText={handleSearch}
            placeholderTextColor={Colors.light.gray}
            returnKeyType="search"
          />
          {searchQuery.length > 0 && (
            <TouchableOpacity
              onPress={() => {
                setSearchQuery('');
                searchProducts('');
              }}
            >
              <Ionicons name="close-circle" size={20} color={Colors.light.gray} />
            </TouchableOpacity>
          )}
        </View>

        {/* Cart Icon */}
        <TouchableOpacity
          style={styles.cartButton}
          onPress={() => router.push('/(tabs)/cart')}
        >
          <Ionicons name="cart-outline" size={24} color={Colors.light.text} />
          {getItemCount() > 0 && (
            <View style={styles.cartBadge}>
              <Text style={styles.cartBadgeText}>{getItemCount()}</Text>
            </View>
          )}
        </TouchableOpacity>
      </View>

      {/* Categories */}
      <CategoryTiles
        selectedCategory={filters.category}
        onSelectCategory={handleCategorySelect}
      />

      {/* Quick Filters */}
      <QuickFilters
        selectedFilter={filters.quickFilter}
        onSelectFilter={handleQuickFilterSelect}
      />

      {/* Products Header */}
      <View style={styles.productsHeader}>
        <Text style={styles.productsTitle}>
          {filters.category
            ? `${filters.category.charAt(0).toUpperCase() + filters.category.slice(1)} Products`
            : filters.quickFilter
            ? quickFilterTitles[filters.quickFilter] || 'Products'
            : 'All Products'}
        </Text>
        <Text style={styles.productCount}>
          {pagination.total} {pagination.total === 1 ? 'item' : 'items'}
        </Text>
      </View>
    </View>
  );

  // Render product item
  const renderProduct = ({ item }: { item: Product }) => (
    <ProductCard product={item} />
  );

  // Render empty state
  const renderEmpty = () => {
    if (loading) return null;

    return (
      <View style={styles.emptyContainer}>
        <Ionicons name="search-outline" size={64} color={Colors.light.gray} />
        <Text style={styles.emptyTitle}>No products found</Text>
        <Text style={styles.emptyText}>
          {searchQuery
            ? `No results for "${searchQuery}"`
            : filters.category
            ? `No products in this category`
            : `No products available`}
        </Text>
        {(searchQuery || filters.category) && (
          <TouchableOpacity
            style={styles.clearButton}
            onPress={() => {
              setSearchQuery('');
              setFilters({ category: undefined, quickFilter: undefined });
            }}
          >
            <Text style={styles.clearButtonText}>Clear filters</Text>
          </TouchableOpacity>
        )}
      </View>
    );
  };

  // Render footer (loading more indicator)
  const renderFooter = () => {
    if (!pagination.hasMore || !loading || products.length === 0) return null;

    return (
      <View style={styles.footerLoader}>
        <ActivityIndicator size="small" color={Colors.light.primary} />
      </View>
    );
  };

  // Error handling
  if (error && !loading && products.length === 0) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.errorContainer}>
          <Ionicons name="alert-circle-outline" size={64} color={Colors.light.error} />
          <Text style={styles.errorTitle}>Oops! Something went wrong</Text>
          <Text style={styles.errorText}>{error}</Text>
          <TouchableOpacity
            style={styles.retryButton}
            onPress={() => loadProducts(true)}
          >
            <Text style={styles.retryButtonText}>Try Again</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <FlashList
        data={products}
        renderItem={renderProduct}
        ListHeaderComponent={renderHeader}
        ListEmptyComponent={renderEmpty}
        ListFooterComponent={renderFooter}
        numColumns={2}
        estimatedItemSize={250}
        keyExtractor={(item) => item.id}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={handleRefresh}
            tintColor={Colors.light.primary}
          />
        }
        onEndReached={handleLoadMore}
        onEndReachedThreshold={0.8}
        contentContainerStyle={styles.listContent}
        ItemSeparatorComponent={() => <View style={{ height: 0 }} />}
        columnWrapperStyle={styles.row}
        showsVerticalScrollIndicator={false}
      />
    </SafeAreaView>
  );
}

const quickFilterTitles: Record<string, string> = {
  trending: 'Trending Products',
  new: 'New Arrivals',
  'staff-picks': 'Staff Picks',
  'on-sale': 'On Sale',
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.light.background,
  },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    gap: 12,
  },
  searchBar: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'white',
    borderRadius: 12,
    paddingHorizontal: 12,
    height: 44,
    borderWidth: 1,
    borderColor: Colors.light.border,
  },
  searchInput: {
    flex: 1,
    fontSize: 16,
    color: Colors.light.text,
    marginLeft: 8,
  },
  cartButton: {
    position: 'relative',
    padding: 8,
  },
  cartBadge: {
    position: 'absolute',
    top: 2,
    right: 2,
    backgroundColor: Colors.light.primary,
    borderRadius: 10,
    minWidth: 20,
    height: 20,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 4,
  },
  cartBadgeText: {
    color: 'white',
    fontSize: 11,
    fontWeight: '600',
  },
  productsHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  productsTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: Colors.light.text,
  },
  productCount: {
    fontSize: 14,
    color: Colors.light.gray,
  },
  listContent: {
    paddingBottom: 20,
  },
  row: {
    paddingHorizontal: 16,
    justifyContent: 'space-between',
  },
  emptyContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 60,
    paddingHorizontal: 32,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: Colors.light.text,
    marginTop: 16,
  },
  emptyText: {
    fontSize: 14,
    color: Colors.light.gray,
    textAlign: 'center',
    marginTop: 8,
  },
  clearButton: {
    marginTop: 16,
    paddingHorizontal: 20,
    paddingVertical: 10,
    backgroundColor: Colors.light.primary,
    borderRadius: 20,
  },
  clearButtonText: {
    color: 'white',
    fontSize: 14,
    fontWeight: '600',
  },
  errorContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 32,
  },
  errorTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: Colors.light.text,
    marginTop: 16,
  },
  errorText: {
    fontSize: 14,
    color: Colors.light.gray,
    textAlign: 'center',
    marginTop: 8,
  },
  retryButton: {
    marginTop: 16,
    paddingHorizontal: 24,
    paddingVertical: 12,
    backgroundColor: Colors.light.primary,
    borderRadius: 8,
  },
  retryButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
  footerLoader: {
    paddingVertical: 20,
    alignItems: 'center',
  },
});