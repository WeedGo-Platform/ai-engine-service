import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { productsApi, ProductFilters, Category, Brand } from '@api/products';
import { IProduct } from '@templates/types';

interface ProductsState {
  products: IProduct[];
  featuredProducts: IProduct[];
  saleProducts: IProduct[];
  categories: Category[];
  brands: Brand[];
  currentProduct: IProduct | null;
  filters: ProductFilters;
  searchQuery: string;
  total: number;
  page: number;
  limit: number;
  hasMore: boolean;
  isLoading: boolean;
  error: string | null;
}

const initialState: ProductsState = {
  products: [],
  featuredProducts: [],
  saleProducts: [],
  categories: [],
  brands: [],
  currentProduct: null,
  filters: {},
  searchQuery: '',
  total: 0,
  page: 0,
  limit: 20,
  hasMore: false,
  isLoading: false,
  error: null,
};

// Async thunks
export const fetchProducts = createAsyncThunk(
  'products/fetchProducts',
  async ({
    storeId,
    filters,
    page = 0,
    limit = 20,
  }: {
    storeId: string;
    filters?: ProductFilters;
    page?: number;
    limit?: number;
  }) => {
    const response = await productsApi.browse(storeId, filters, limit, page * limit);
    return response;
  }
);

export const fetchProduct = createAsyncThunk(
  'products/fetchProduct',
  async (sku: string) => {
    const product = await productsApi.getProduct(sku);
    return product;
  }
);

export const searchProducts = createAsyncThunk(
  'products/searchProducts',
  async ({
    query,
    filters,
    limit = 20,
    offset = 0,
  }: {
    query: string;
    filters?: ProductFilters;
    limit?: number;
    offset?: number;
  }) => {
    const response = await productsApi.search({ query, filters, limit, offset });
    return response;
  }
);

export const fetchCategories = createAsyncThunk(
  'products/fetchCategories',
  async () => {
    const categories = await productsApi.getCategories();
    return categories;
  }
);

export const fetchBrands = createAsyncThunk('products/fetchBrands', async () => {
  const brands = await productsApi.getBrands();
  return brands;
});

export const fetchFeaturedProducts = createAsyncThunk(
  'products/fetchFeaturedProducts',
  async ({ storeId, limit = 8 }: { storeId: string; limit?: number }) => {
    const products = await productsApi.getFeaturedProducts(storeId, limit);
    return products;
  }
);

export const fetchSaleProducts = createAsyncThunk(
  'products/fetchSaleProducts',
  async ({ storeId, limit = 12 }: { storeId: string; limit?: number }) => {
    const products = await productsApi.getSaleProducts(storeId, limit);
    return products;
  }
);

const productsSlice = createSlice({
  name: 'products',
  initialState,
  reducers: {
    setFilters: (state, action: PayloadAction<ProductFilters>) => {
      state.filters = action.payload;
      state.page = 0; // Reset page when filters change
    },
    clearFilters: (state) => {
      state.filters = {};
      state.page = 0;
    },
    setSearchQuery: (state, action: PayloadAction<string>) => {
      state.searchQuery = action.payload;
      state.page = 0;
    },
    setPage: (state, action: PayloadAction<number>) => {
      state.page = action.payload;
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    // Fetch products
    builder
      .addCase(fetchProducts.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchProducts.fulfilled, (state, action) => {
        state.isLoading = false;
        if (action.payload.page === 0) {
          state.products = action.payload.products;
        } else {
          state.products = [...state.products, ...action.payload.products];
        }
        state.total = action.payload.total;
        state.page = action.payload.page;
        state.hasMore = action.payload.has_more;
      })
      .addCase(fetchProducts.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to fetch products';
      });

    // Fetch single product
    builder
      .addCase(fetchProduct.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchProduct.fulfilled, (state, action) => {
        state.isLoading = false;
        state.currentProduct = action.payload;
      })
      .addCase(fetchProduct.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to fetch product';
      });

    // Search products
    builder
      .addCase(searchProducts.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(searchProducts.fulfilled, (state, action) => {
        state.isLoading = false;
        state.products = action.payload.products;
        state.total = action.payload.total;
        state.hasMore = action.payload.has_more;
      })
      .addCase(searchProducts.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to search products';
      });

    // Fetch categories
    builder
      .addCase(fetchCategories.pending, (state) => {
        state.isLoading = true;
      })
      .addCase(fetchCategories.fulfilled, (state, action) => {
        state.isLoading = false;
        state.categories = action.payload;
      })
      .addCase(fetchCategories.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to fetch categories';
      });

    // Fetch brands
    builder
      .addCase(fetchBrands.pending, (state) => {
        state.isLoading = true;
      })
      .addCase(fetchBrands.fulfilled, (state, action) => {
        state.isLoading = false;
        state.brands = action.payload;
      })
      .addCase(fetchBrands.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to fetch brands';
      });

    // Fetch featured products
    builder
      .addCase(fetchFeaturedProducts.fulfilled, (state, action) => {
        state.featuredProducts = action.payload;
      });

    // Fetch sale products
    builder
      .addCase(fetchSaleProducts.fulfilled, (state, action) => {
        state.saleProducts = action.payload;
      });
  },
});

export const { setFilters, clearFilters, setSearchQuery, setPage, clearError } =
  productsSlice.actions;

export default productsSlice.reducer;