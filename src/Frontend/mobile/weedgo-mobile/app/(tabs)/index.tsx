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
import { useTheme } from '@/contexts/ThemeContext';
import { Colors, BorderRadius, Shadows, Gradients } from '@/constants/Colors';
import { LinearGradient } from 'expo-linear-gradient';
import { StoreSelector } from '@/components/StoreSelector';
import { CategoryTiles } from '@/components/CategoryTiles';
import { QuickFilters } from '@/components/QuickFilters';
import { ProductCard } from '@/components/ProductCard';
import { EmptyState } from '@/components/EmptyState';
import { Product } from '@/types/api.types';

const { width } = Dimensions.get('window');

export default function HomeScreen() {
  const router = useRouter();
  const { user, isAuthenticated } = useAuthStore();
  const { getItemCount } = useCartStore();
  const { theme, isDark } = useTheme();
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

  const styles = React.useMemo(() => createStyles(theme, isDark), [theme, isDark]);

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
        <LinearGradient
          colors={['rgba(255, 255, 255, 0.95)', 'rgba(250, 250, 255, 0.95)']}
          style={styles.searchBar}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
        >
          <Ionicons name="search" size={20} color={theme.primary} />
          <TextInput
            style={styles.searchInput}
            placeholder="Search products..."
            value={searchQuery}
            onChangeText={handleSearch}
            placeholderTextColor={theme.textSecondary}
            returnKeyType="search"
          />
          {searchQuery.length > 0 && (
            <TouchableOpacity
              onPress={() => {
                setSearchQuery('');
                searchProducts('');
              }}
            >
              <Ionicons name="close-circle" size={20} color={theme.textSecondary} />
            </TouchableOpacity>
          )}
        </LinearGradient>
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

    // Different empty states based on context
    if (searchQuery) {
      return (
        <EmptyState
          icon="search-outline"
          title="No products found"
          subtitle={`We couldn't find any products matching "${searchQuery}"`}
          actionLabel="Clear search"
          onAction={() => {
            setSearchQuery('');
            handleSearch('');
          }}
          suggestions={['Indica', 'Sativa', 'Edibles', 'Pre-rolls']}
          onSuggestionPress={handleSearch}
        />
      );
    }

    if (filters.category || filters.quickFilter) {
      return (
        <EmptyState
          icon="filter-outline"
          title="No products match your filters"
          subtitle="Try adjusting your filters or browse all products"
          actionLabel="Clear filters"
          onAction={() => {
            setFilters({ category: undefined, quickFilter: undefined });
          }}
        />
      );
    }

    // Store has no inventory
    return (
      <EmptyState
        icon="storefront-outline"
        title="Store inventory coming soon"
        subtitle="This store is currently updating their product catalog. Please check back later or try the AI chat assistant for help."
        actionLabel="Open Chat"
        onAction={() => router.push('/(tabs)/chat')}
      />
    );
  };

  // Render footer (loading more indicator)
  const renderFooter = () => {
    if (!pagination.hasMore || !loading || products.length === 0) return null;

    return (
      <View style={styles.footerLoader}>
        <ActivityIndicator size="small" color={theme.primary} />
      </View>
    );
  };

  // Error handling
  if (error && !loading && products.length === 0) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.errorContainer}>
          <Ionicons name="alert-circle-outline" size={64} color={theme.error} />
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
    <View style={{ flex: 1 }}>
      <LinearGradient
        colors={[theme.gradientStart, theme.gradientMid, theme.gradientEnd]}
        style={styles.gradientContainer}
        start={{ x: 0, y: 0 }}
        end={{ x: 0.5, y: 1 }}
      >
        <SafeAreaView style={styles.container}>
          <FlashList
            data={products}
            renderItem={renderProduct}
            ListHeaderComponent={renderHeader}
            ListEmptyComponent={renderEmpty}
            ListFooterComponent={renderFooter}
            numColumns={2}
            keyExtractor={(item, index) => `${item.id}-${index}`}
            refreshControl={
              <RefreshControl
                refreshing={refreshing}
                onRefresh={handleRefresh}
                tintColor={theme.primary}
              />
            }
            onEndReached={handleLoadMore}
            onEndReachedThreshold={0.8}
            contentContainerStyle={styles.listContent}
            ItemSeparatorComponent={() => <View style={{ height: 0 }} />}
            showsVerticalScrollIndicator={false}
          />
        </SafeAreaView>
      </LinearGradient>

    </View>
  );
}

const quickFilterTitles: Record<string, string> = {
  trending: 'Trending Products',
  new: 'New Arrivals',
  'staff-picks': 'Staff Picks',
  'on-sale': 'On Sale',
};

const createStyles = (theme: any, isDark: boolean) => StyleSheet.create({
  gradientContainer: {
    flex: 1,
  },
  container: {
    flex: 1,
    backgroundColor: 'transparent',
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
    borderRadius: BorderRadius.xl,
    paddingHorizontal: 16,
    height: 48,
    borderWidth: 1.5,
    borderColor: 'rgba(255, 255, 255, 0.5)',
    marginRight: 12,
    ...Shadows.medium,
  },
  searchInput: {
    flex: 1,
    fontSize: 16,
    color: theme.text,
    marginLeft: 8,
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
    fontWeight: '700',
    color: theme.text,
  },
  productCount: {
    fontSize: 14,
    color: theme.textSecondary,
  },
  listContent: {
    paddingBottom: 20,
    paddingHorizontal: 16,
  },
  row: {
    justifyContent: 'space-between',
    gap: 16,
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
    color: theme.text,
    marginTop: 16,
  },
  emptyText: {
    fontSize: 14,
    color: theme.textSecondary,
    textAlign: 'center',
    marginTop: 8,
  },
  clearButton: {
    marginTop: 16,
    paddingHorizontal: 24,
    paddingVertical: 12,
    backgroundColor: theme.primary,
    borderRadius: BorderRadius.xl,
    ...Shadows.small,
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
    color: theme.text,
    marginTop: 16,
  },
  errorText: {
    fontSize: 14,
    color: theme.textSecondary,
    textAlign: 'center',
    marginTop: 8,
  },
  retryButton: {
    marginTop: 16,
    paddingHorizontal: 24,
    paddingVertical: 12,
    backgroundColor: theme.primary,
    borderRadius: BorderRadius.xl,
    ...Shadows.medium,
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