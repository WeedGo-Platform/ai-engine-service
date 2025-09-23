import React, { useState, useCallback, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  Dimensions,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { FlashList } from '@shopify/flash-list';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import useProductsStore from '@/stores/productsStore';
import { ProductCard } from '@/components/ProductCard';
import { CategoryTiles } from '@/components/CategoryTiles';
import { QuickFilters } from '@/components/QuickFilters';
import { Colors } from '@/constants/Colors';
import { Product } from '@/types/api.types';

const { width } = Dimensions.get('window');

export default function SearchScreen() {
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState('');
  const [searchTimer, setSearchTimer] = useState<NodeJS.Timeout | null>(null);
  const [showFilters, setShowFilters] = useState(false);

  const {
    products,
    loading,
    error,
    filters,
    pagination,
    categories,
    loadProducts,
    loadCategories,
    setFilters,
    searchProducts,
    loadMore,
  } = useProductsStore();

  // Load categories on mount
  useEffect(() => {
    loadCategories();
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
  }, [searchTimer, searchProducts]);

  // Clear search
  const handleClearSearch = () => {
    setSearchQuery('');
    searchProducts('');
  };

  // Handle category selection
  const handleCategorySelect = (categoryId: string) => {
    if (filters.category === categoryId) {
      setFilters({ category: undefined });
    } else {
      setFilters({ category: categoryId });
    }
  };

  // Handle quick filter selection
  const handleQuickFilterSelect = (filterId: string | undefined) => {
    setFilters({ quickFilter: filterId as any });
  };

  // Handle load more
  const handleLoadMore = () => {
    if (!loading && pagination.hasMore) {
      loadMore();
    }
  };

  // Navigate to product detail
  const handleProductPress = (product: Product) => {
    router.push(`/product/${product.id}`);
  };

  // Render search header
  const renderHeader = () => (
    <View style={styles.headerContainer}>
      {/* Search Bar */}
      <View style={styles.searchContainer}>
        <View style={styles.searchBar}>
          <Ionicons name="search" size={20} color={Colors.light.gray} />
          <TextInput
            style={styles.searchInput}
            placeholder="Search products, brands, strains..."
            value={searchQuery}
            onChangeText={handleSearch}
            autoCapitalize="none"
            autoCorrect={false}
            returnKeyType="search"
          />
          {searchQuery.length > 0 && (
            <TouchableOpacity onPress={handleClearSearch}>
              <Ionicons name="close-circle" size={20} color={Colors.light.gray} />
            </TouchableOpacity>
          )}
        </View>

        <TouchableOpacity
          style={styles.filterButton}
          onPress={() => setShowFilters(!showFilters)}
        >
          <Ionicons
            name="options-outline"
            size={24}
            color={filters.category || filters.quickFilter ? Colors.light.primary : Colors.light.text}
          />
        </TouchableOpacity>
      </View>

      {/* Filters Section */}
      {showFilters && (
        <View style={styles.filtersContainer}>
          {/* Categories */}
          {categories.length > 0 && (
            <>
              <Text style={styles.filterTitle}>Categories</Text>
              <CategoryTiles
                selectedCategory={filters.category}
                onSelectCategory={handleCategorySelect}
              />
            </>
          )}

          {/* Quick Filters */}
          <Text style={styles.filterTitle}>Quick Filters</Text>
          <QuickFilters
            selectedFilter={filters.quickFilter}
            onSelectFilter={handleQuickFilterSelect}
          />
        </View>
      )}

      {/* Results Count */}
      {searchQuery && !loading && (
        <View style={styles.resultsInfo}>
          <Text style={styles.resultsText}>
            {products.length === 0
              ? 'No products found'
              : `${pagination.total || products.length} products found`}
          </Text>
        </View>
      )}

    </View>
  );

  // Render product item
  const renderProduct = ({ item }: { item: Product }) => (
    <ProductCard
      product={item}
      onPress={() => handleProductPress(item)}
    />
  );

  // Render empty state
  const renderEmpty = () => {
    if (loading) return null;

    if (searchQuery && products.length === 0) {
      return (
        <View style={styles.emptyContainer}>
          <Ionicons name="search-outline" size={64} color={Colors.light.gray} />
          <Text style={styles.emptyTitle}>No products found</Text>
          <Text style={styles.emptySubtext}>
            Try adjusting your search or filters
          </Text>
        </View>
      );
    }

    if (!searchQuery) {
      return (
        <View style={styles.emptyContainer}>
          <Ionicons name="search-outline" size={64} color={Colors.light.gray} />
          <Text style={styles.emptyTitle}>Search for products</Text>
          <Text style={styles.emptySubtext}>
            Find your favorite strains, edibles, and more
          </Text>
        </View>
      );
    }

    return null;
  };

  // Render footer (loading more indicator)
  const renderFooter = () => {
    if (!pagination.hasMore || !loading) return null;
    return (
      <View style={styles.footerLoader}>
        <ActivityIndicator size="small" color={Colors.light.primary} />
      </View>
    );
  };

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <KeyboardAvoidingView
        style={styles.container}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        keyboardVerticalOffset={0}
      >
        {renderHeader()}

        {loading && products.length === 0 ? (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color={Colors.light.primary} />
          </View>
        ) : (
          <FlashList
            data={products}
            renderItem={renderProduct}
            
            numColumns={2}
            contentContainerStyle={styles.listContent}
            ItemSeparatorComponent={() => <View style={{ height: 16 }} />}
            ListEmptyComponent={renderEmpty}
            ListFooterComponent={renderFooter}
            onEndReached={handleLoadMore}
            onEndReachedThreshold={0.5}
            showsVerticalScrollIndicator={false}
          />
        )}

        {error && (
          <View style={styles.errorContainer}>
            <Text style={styles.errorText}>{error}</Text>
          </View>
        )}
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.light.background,
  },
  headerContainer: {
    backgroundColor: Colors.light.card,
    paddingBottom: 8,
    borderBottomWidth: 1,
    borderBottomColor: Colors.light.border,
  },
  searchContainer: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    paddingTop: 12,
    paddingBottom: 8,
    gap: 8,
  },
  searchBar: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.light.inputBackground,
    borderRadius: 12,
    paddingHorizontal: 12,
    height: 44,
    gap: 8,
  },
  searchInput: {
    flex: 1,
    fontSize: 16,
    color: Colors.light.text,
  },
  filterButton: {
    width: 44,
    height: 44,
    backgroundColor: Colors.light.inputBackground,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
  },
  filtersContainer: {
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  filterTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.light.text,
    marginBottom: 8,
    marginTop: 8,
  },
  resultsInfo: {
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  resultsText: {
    fontSize: 14,
    color: Colors.light.gray,
  },
  suggestionsContainer: {
    padding: 16,
  },
  suggestionsTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.light.text,
    marginBottom: 12,
  },
  suggestionChip: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    backgroundColor: Colors.light.inputBackground,
    borderRadius: 20,
    marginRight: 8,
    marginBottom: 8,
    alignSelf: 'flex-start',
  },
  suggestionText: {
    fontSize: 14,
    color: Colors.light.text,
  },
  listContent: {
    paddingHorizontal: 16,
    paddingVertical: 16,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 64,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: Colors.light.text,
    marginTop: 16,
  },
  emptySubtext: {
    fontSize: 14,
    color: Colors.light.gray,
    marginTop: 8,
  },
  footerLoader: {
    paddingVertical: 16,
    alignItems: 'center',
  },
  errorContainer: {
    position: 'absolute',
    bottom: 100,
    left: 16,
    right: 16,
    backgroundColor: Colors.light.error,
    padding: 12,
    borderRadius: 8,
  },
  errorText: {
    color: 'white',
    fontSize: 14,
    textAlign: 'center',
  },
});