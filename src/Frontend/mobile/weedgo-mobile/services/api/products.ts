import { apiClient } from './client';
import {
  Product,
  ProductSearchParams,
  ProductSearchResponse,
  Category,
} from '@/types/api.types';
import useStoreStore from '@/stores/storeStore';

class ProductService {
  /**
   * Search products with filters
   */
  async searchProducts(params: ProductSearchParams = {}): Promise<ProductSearchResponse> {
    // Get current store from store state
    const currentStore = useStoreStore.getState().currentStore;

    // Use store_id from params if provided, otherwise use current store
    const storeId = params.store_id || currentStore?.id;

    // Return empty results if no store is available
    if (!storeId) {
      console.warn('No store selected, returning empty results');
      return {
        results: [],
        total: 0,
        offset: params.offset || 0,
        limit: params.limit || 20
      };
    }

    // Build clean params object, excluding undefined values
    const apiParams: any = {
      q: params.q || params.search || '',
      limit: params.limit || 20,
      offset: params.offset || 0,
      store_id: storeId
    };

    // Only add optional params if they have values
    if (params.category) apiParams.category = params.category;
    if (params.brand) apiParams.brand = params.brand;
    if (params.strain_type) apiParams.strain_type = params.strain_type;
    if (params.thc_min !== undefined) apiParams.thc_min = params.thc_min;
    if (params.thc_max !== undefined) apiParams.thc_max = params.thc_max;
    if (params.cbd_min !== undefined) apiParams.cbd_min = params.cbd_min;
    if (params.cbd_max !== undefined) apiParams.cbd_max = params.cbd_max;
    if (params.price_min !== undefined) apiParams.price_min = params.price_min;
    if (params.price_max !== undefined) apiParams.price_max = params.price_max;

    const response = await apiClient.get<ProductSearchResponse>(
      '/api/products/search',
      { params: apiParams }
    );
    return response.data;
  }

  /**
   * Get all product categories by extracting from product search results
   */
  async getCategories(): Promise<Category[]> {
    // Get current store from store state
    const currentStore = useStoreStore.getState().currentStore;
    if (!currentStore) {
      console.warn('No store selected, cannot fetch categories');
      return [];
    }

    // Search products to extract categories dynamically
    const response = await this.searchProducts({
      limit: 100,
      store_id: currentStore.id
    });

    const categoryMap = new Map<string, Category>();

    // Extract unique categories from products
    if (response.results) {
      response.results.forEach(product => {
        if (product.category) {
          const categoryKey = product.category;

          if (!categoryMap.has(categoryKey)) {
            categoryMap.set(categoryKey, {
              id: categoryKey.toLowerCase().replace(/\s+/g, '-'),
              name: product.category,
              slug: categoryKey.toLowerCase().replace(/\s+/g, '-'),
              subcategories: new Map()
            });
          }

          const category = categoryMap.get(categoryKey)!;

          // Add subcategory if it exists
          if (product.subCategory) {
            if (!category.subcategories) {
              category.subcategories = new Map();
            }

            const subKey = product.subCategory;
            if (!category.subcategories.has(subKey)) {
              category.subcategories.set(subKey, {
                id: subKey.toLowerCase().replace(/\s+/g, '-'),
                name: product.subCategory,
                slug: subKey.toLowerCase().replace(/\s+/g, '-'),
                subSubCategories: new Map()
              });
            }

            // Add sub-subcategory if it exists
            if (product.subSubCategory) {
              const subcategory = category.subcategories.get(subKey)!;
              if (!subcategory.subSubCategories) {
                subcategory.subSubCategories = new Map();
              }

              const subSubKey = product.subSubCategory;
              if (!subcategory.subSubCategories.has(subSubKey)) {
                subcategory.subSubCategories.set(subSubKey, {
                  id: subSubKey.toLowerCase().replace(/\s+/g, '-'),
                  name: product.subSubCategory,
                  slug: subSubKey.toLowerCase().replace(/\s+/g, '-')
                });
              }
            }
          }
        }
      });
    }

    // Convert Maps to arrays and return
    const categories = Array.from(categoryMap.values()).map(cat => ({
      ...cat,
      subcategories: cat.subcategories ? Array.from(cat.subcategories.values()).map(sub => ({
        ...sub,
        subSubCategories: sub.subSubCategories ? Array.from(sub.subSubCategories.values()) : []
      })) : []
    }));

    return categories;
  }

  /**
   * Get single product details
   */
  async getProductDetails(productId: string): Promise<Product> {
    const response = await apiClient.get<Product>(
      `/api/products/${productId}/details`
    );
    return response.data;
  }

  /**
   * Get store-specific inventory
   */
  async getStoreInventory(
    storeId: string,
    params: {
      category?: string;
      subcategory?: string;
      brand?: string;
      strain_type?: string;
      size?: string;
      quick_filter?: 'trending' | 'new' | 'staff-picks';
      search?: string;
      limit?: number;
      offset?: number;
    } = {}
  ): Promise<{ products: Product[]; total: number }> {
    // Build clean params object, excluding undefined values
    const apiParams: any = {
      q: params.search || '',
      store_id: storeId,
      limit: params.limit || 20,
      offset: params.offset || 0,
    };

    // Only add optional params if they have values
    if (params.category) apiParams.category = params.category;
    if (params.subcategory) apiParams.subcategory = params.subcategory;
    if (params.brand) apiParams.brand = params.brand;
    if (params.strain_type) apiParams.strain_type = params.strain_type;
    if (params.size) apiParams.size = params.size;

    const response = await apiClient.get<any>(
      '/api/products/search',
      { params: apiParams }
    );

    // Transform response to match expected format
    return {
      products: response.data.results || [],
      total: response.data.total || response.data.results?.length || 0
    };
  }

  /**
   * Get trending products
   */
  async getTrendingProducts(limit: number = 10): Promise<Product[]> {
    const currentStore = useStoreStore.getState().currentStore;
    if (!currentStore) return [];

    const response = await this.getStoreInventory(
      currentStore.id,
      { quick_filter: 'trending', limit }
    );
    return response.products;
  }

  /**
   * Get new products
   */
  async getNewProducts(limit: number = 10): Promise<Product[]> {
    const currentStore = useStoreStore.getState().currentStore;
    if (!currentStore) return [];

    const response = await this.getStoreInventory(
      currentStore.id,
      { quick_filter: 'new', limit }
    );
    return response.products;
  }

  /**
   * Get staff picks
   */
  async getStaffPicks(limit: number = 10): Promise<Product[]> {
    const currentStore = useStoreStore.getState().currentStore;
    if (!currentStore) return [];

    const response = await this.getStoreInventory(
      currentStore.id,
      { quick_filter: 'staff-picks', limit }
    );
    return response.products;
  }

  /**
   * Get products by category
   */
  async getProductsByCategory(
    category: string,
    params: ProductSearchParams = {}
  ): Promise<ProductSearchResponse> {
    return this.searchProducts({ ...params, category });
  }

  /**
   * Get products by brand
   */
  async getProductsByBrand(
    brand: string,
    params: ProductSearchParams = {}
  ): Promise<ProductSearchResponse> {
    return this.searchProducts({ ...params, brand });
  }

  /**
   * Get products by strain type
   */
  async getProductsByStrainType(
    strainType: 'indica' | 'sativa' | 'hybrid' | 'cbd',
    params: ProductSearchParams = {}
  ): Promise<ProductSearchResponse> {
    return this.searchProducts({ ...params, strain_type: strainType });
  }

  /**
   * Get products by THC content range
   */
  async getProductsByTHCRange(
    thcMin: number,
    thcMax: number,
    params: ProductSearchParams = {}
  ): Promise<ProductSearchResponse> {
    return this.searchProducts({ ...params, thc_min: thcMin, thc_max: thcMax });
  }

  /**
   * Get products by CBD content range
   */
  async getProductsByCBDRange(
    cbdMin: number,
    cbdMax: number,
    params: ProductSearchParams = {}
  ): Promise<ProductSearchResponse> {
    return this.searchProducts({ ...params, cbd_min: cbdMin, cbd_max: cbdMax });
  }

  /**
   * Get products by price range
   */
  async getProductsByPriceRange(
    priceMin: number,
    priceMax: number,
    params: ProductSearchParams = {}
  ): Promise<ProductSearchResponse> {
    return this.searchProducts({ ...params, price_min: priceMin, price_max: priceMax });
  }

  /**
   * Search products by query string
   */
  async searchByQuery(query: string, params: ProductSearchParams = {}): Promise<ProductSearchResponse> {
    return this.searchProducts({ ...params, q: query });
  }

  /**
   * Get product recommendations based on a product
   */
  async getRecommendations(productId: string, limit: number = 5): Promise<Product[]> {
    const response = await apiClient.get<{ products: Product[] }>(
      `/api/products/${productId}/recommendations`,
      { params: { limit } }
    );
    return response.data.products;
  }

  /**
   * Get product reviews
   */
  async getProductReviews(
    productId: string,
    params: { limit?: number; offset?: number } = {}
  ): Promise<{ reviews: any[]; total: number }> {
    const response = await apiClient.get<{ reviews: any[]; total: number }>(
      `/api/products/${productId}/reviews`,
      { params }
    );
    return response.data;
  }
}

// Export singleton instance
export const productService = new ProductService();