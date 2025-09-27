import { create } from 'zustand';
import { productService } from '@/services/api/products';
import { Product, Category } from '@/types/api.types';
import useStoreStore from '@/stores/storeStore';

interface ProductFilters {
  category?: string;
  subcategory?: string;
  brand?: string;
  strainType?: 'indica' | 'sativa' | 'hybrid' | 'cbd';
  thcMin?: number;
  thcMax?: number;
  cbdMin?: number;
  cbdMax?: number;
  priceMin?: number;
  priceMax?: number;
  size?: string;
  quickFilter?: 'trending' | 'new' | 'staff-picks' | 'on-sale';
  search?: string;
  sortBy?: 'price_asc' | 'price_desc' | 'name' | 'thc' | 'cbd' | 'rating';
}

interface ProductsStore {
  // State
  products: Product[];
  categories: Category[];
  filters: ProductFilters;
  loading: boolean;
  refreshing: boolean;
  error: string | null;
  pagination: {
    page: number;
    limit: number;
    total: number;
    hasMore: boolean;
  };
  searchQuery: string;

  // Actions
  loadProducts: (reset?: boolean) => Promise<void>;
  loadCategories: () => Promise<void>;
  setFilters: (filters: Partial<ProductFilters>) => void;
  clearFilters: () => void;
  searchProducts: (query: string) => Promise<void>;
  loadMore: () => Promise<void>;
  refreshProducts: () => Promise<void>;
  setSelectedStore: (storeId: string) => void;
  getProductById: (id: string) => Product | undefined;
  loadProductDetails: (productId: string) => Promise<Product>;
}

const defaultFilters: ProductFilters = {
  sortBy: 'name',
};

const useProductsStore = create<ProductsStore>((set, get) => ({
  // Initial state
  products: [],
  categories: [],
  filters: defaultFilters,
  loading: false,
  refreshing: false,
  error: null,
  pagination: {
    page: 0,
    limit: 20,
    total: 0,
    hasMore: true,
  },
  searchQuery: '',

  // Load products with current filters
  loadProducts: async (reset = false) => {
    const state = get();
    const { filters, pagination } = state;

    // Get current store from storeStore
    const currentStore = useStoreStore.getState().currentStore;
    if (!currentStore) {
      set({ error: 'No store selected' });
      return;
    }

    // Don't load if already loading
    if (state.loading && !reset) return;

    set({ loading: true, error: null });

    try {
      const offset = reset ? 0 : pagination.page * pagination.limit;

      const response = await productService.getStoreInventory(
        currentStore.id,
        {
          category: filters.category,
          subcategory: filters.subcategory,
          brand: filters.brand,
          strain_type: filters.strainType,
          size: filters.size,
          quick_filter: filters.quickFilter,
          search: filters.search || '',
          limit: pagination.limit,
          offset,
        }
      );

      const newProducts = reset
        ? response.products
        : [...state.products, ...response.products];


      set({
        products: newProducts,
        pagination: {
          ...pagination,
          page: reset ? 0 : pagination.page,
          total: response.total,
          hasMore: newProducts.length < response.total,
        },
        loading: false,
      });
    } catch (error: any) {
      set({
        error: error.message || 'Failed to load products',
        loading: false,
      });
    }
  },

  // Load product categories
  loadCategories: async () => {
    try {
      const categories = await productService.getCategories();
      set({ categories });
    } catch (error: any) {
      set({ error: error.message || 'Failed to load categories' });
    }
  },

  // Set filters and reload products
  setFilters: (newFilters: Partial<ProductFilters>) => {
    const state = get();
    const updatedFilters = { ...state.filters, ...newFilters };

    set({
      filters: updatedFilters,
      pagination: { ...state.pagination, page: 0 }
    });

    // Reload products with new filters
    state.loadProducts(true);
  },

  // Clear all filters
  clearFilters: () => {
    set({
      filters: defaultFilters,
      searchQuery: '',
      pagination: { page: 0, limit: 20, total: 0, hasMore: true }
    });

    get().loadProducts(true);
  },

  // Search products
  searchProducts: async (query: string) => {
    const state = get();

    set({
      searchQuery: query,
      filters: { ...state.filters, search: query },
      pagination: { ...state.pagination, page: 0 }
    });

    await state.loadProducts(true);
  },

  // Load more products (pagination)
  loadMore: async () => {
    const state = get();
    const { pagination, loading } = state;

    if (loading || !pagination.hasMore) return;

    set({
      pagination: {
        ...pagination,
        page: pagination.page + 1,
      },
    });

    await state.loadProducts(false);
  },

  // Refresh products (pull to refresh)
  refreshProducts: async () => {
    const state = get();

    set({ refreshing: true });

    try {
      // Reset pagination and reload
      set({
        pagination: { page: 0, limit: 20, total: 0, hasMore: true }
      });

      await state.loadProducts(true);

      // Also refresh categories
      await state.loadCategories();
    } finally {
      set({ refreshing: false });
    }
  },

  // Set selected store (now just triggers reload since store is managed in storeStore)
  setSelectedStore: (storeId: string) => {
    set({
      products: [],
      pagination: { page: 0, limit: 20, total: 0, hasMore: true }
    });

    // Reload products for new store
    get().loadProducts(true);
  },

  // Get product by ID from local state
  getProductById: (id: string) => {
    return get().products.find(p => p.id === id);
  },

  // Load detailed product information
  loadProductDetails: async (productId: string) => {
    try {
      const product = await productService.getProductDetails(productId);

      // Update local state with detailed product
      const state = get();
      const updatedProducts = state.products.map(p =>
        p.id === productId ? product : p
      );

      set({ products: updatedProducts });

      return product;
    } catch (error: any) {
      set({ error: error.message || 'Failed to load product details' });
      throw error;
    }
  },
}));

export default useProductsStore;