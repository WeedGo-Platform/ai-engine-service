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
import { FlashList } from '@shopify/flash-list';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { LinearGradient } from 'expo-linear-gradient';
import useProductsStore from '@/stores/productsStore';
import { ProductCard } from '@/components/ProductCard';
import { CategoryTiles } from '@/components/CategoryTiles';
import { QuickFilters } from '@/components/QuickFilters';
import { useTheme } from '@/contexts/ThemeContext';
import { Colors, BorderRadius, Shadows } from '@/constants/Colors';
import { Product } from '@/types/api.types';

const { width } = Dimensions.get('window');

export default function SearchScreen() {
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState('');
  const [searchTimer, setSearchTimer] = useState<NodeJS.Timeout | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  const { theme, isDark } = useTheme();

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

  const styles = React.useMemo(() => createStyles(theme, isDark), [theme, isDark]);

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
          <Ionicons name="search" size={20} color={theme.textSecondary} />
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
              <Ionicons name="close-circle" size={20} color={theme.textSecondary} />
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
            color={filters.category || filters.quickFilter ? theme.primary : theme.text}
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
          <Ionicons name="search-outline" size={64} color={theme.textSecondary} />
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
          <Ionicons name="search-outline" size={64} color={theme.textSecondary} />
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
        <ActivityIndicator size="small" color={theme.primary} />
      </View>
    );
  };

  return (
    <View style={{ flex: 1 }}>
      <LinearGradient
        colors={isDark ? [theme.background, theme.backgroundSecondary, theme.surface] : [theme.gradientStart, theme.gradientMid, theme.gradientEnd]}
        style={styles.gradientContainer}
        start={{ x: 0, y: 0 }}
        end={{ x: 0.5, y: 1 }}
      >
        <KeyboardAvoidingView
          style={styles.container}
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          keyboardVerticalOffset={0}
        >
          {renderHeader()}

          {loading && products.length === 0 ? (
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="large" color={theme.primary} />
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
      </LinearGradient>
    </View>
  );
}

const createStyles = (theme: any, isDark: boolean) => StyleSheet.create({
  gradientContainer: {
    flex: 1,
  },
  container: {
    flex: 1,
    backgroundColor: 'transparent',
  },
  headerContainer: {
    backgroundColor: theme.glass,
    paddingBottom: 8,
    borderBottomWidth: 1,
    borderBottomColor: theme.glassBorder,
  },
  searchContainer: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    paddingTop: Platform.OS === 'ios' ? 50 : 40, // Add padding for status bar
    paddingBottom: 8,
    gap: 8,
  },
  searchBar: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: theme.inputBackground,
    borderRadius: BorderRadius.xl,
    paddingHorizontal: 16,
    height: 48,
    gap: 8,
    borderWidth: 1,
    borderColor: theme.glassBorder,
    ...Shadows.small,
  },
  searchInput: {
    flex: 1,
    fontSize: 16,
    color: theme.text,
  },
  filterButton: {
    width: 48,
    height: 48,
    backgroundColor: theme.glass,
    borderRadius: BorderRadius.full,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: theme.glassBorder,
    ...Shadows.small,
  },
  filtersContainer: {
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  filterTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: theme.text,
    marginBottom: 8,
    marginTop: 8,
  },
  resultsInfo: {
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  resultsText: {
    fontSize: 14,
    color: theme.textSecondary,
  },
  suggestionsContainer: {
    padding: 16,
  },
  suggestionsTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: theme.text,
    marginBottom: 12,
  },
  suggestionChip: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    backgroundColor: theme.glass,
    borderRadius: BorderRadius.xl,
    marginRight: 8,
    marginBottom: 8,
    alignSelf: 'flex-start',
    borderWidth: 1,
    borderColor: theme.glassBorder,
  },
  suggestionText: {
    fontSize: 14,
    color: theme.text,
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
    fontWeight: '700',
    color: theme.text,
    marginTop: 16,
  },
  emptySubtext: {
    fontSize: 14,
    color: theme.textSecondary,
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
    backgroundColor: theme.error,
    padding: 12,
    borderRadius: BorderRadius.lg,
    ...Shadows.medium,
  },
  errorText: {
    color: 'white',
    fontSize: 14,
    textAlign: 'center',
  },
});