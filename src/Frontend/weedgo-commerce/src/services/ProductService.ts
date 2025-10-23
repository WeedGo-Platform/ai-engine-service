import { BaseService } from './BaseService';
import { Product, ProductCategory, ApiResponse, PaginatedResponse } from '@/types';

export interface ProductFilters {
  category?: ProductCategory;
  search?: string;
  minPrice?: number;
  maxPrice?: number;
  inStock?: boolean;
  featured?: boolean;
  sortBy?: 'name' | 'price' | 'rating' | 'created';
  sortOrder?: 'asc' | 'desc';
  page?: number;
  pageSize?: number;
}

export interface ProductCreateDto {
  name: string;
  description: string;
  category: ProductCategory;
  price: number;
  image: string;
  thc?: number;
  cbd?: number;
  strain?: string;
  weight?: number;
  unit?: string;
  quantity: number;
  featured?: boolean;
}

export interface ProductUpdateDto extends Partial<ProductCreateDto> {
  id: string;
}

/**
 * Service for managing products
 * Implements caching for frequently accessed product data
 */
export class ProductService extends BaseService {
  private readonly basePath = '/api/products';

  /**
   * Get all products with filtering and pagination
   */
  async getProducts(filters?: ProductFilters): Promise<ApiResponse<PaginatedResponse<Product>>> {
    return this.getPaginated<Product>(
      this.basePath,
      filters
    );
  }

  /**
   * Get a single product by ID
   */
  async getProduct(id: string): Promise<ApiResponse<Product>> {
    return this.get<Product>(
      `${this.basePath}/${id}`,
      {
        useCache: true,
        cacheKey: `product-${id}`
      }
    );
  }

  /**
   * Search products
   */
  async searchProducts(query: string): Promise<ApiResponse<Product[]>> {
    return this.get<Product[]>(
      `${this.basePath}/search`,
      {
        params: { q: query },
        useCache: true,
        cacheKey: `search-${query}`
      }
    );
  }

  /**
   * Get featured products
   */
  async getFeaturedProducts(): Promise<ApiResponse<Product[]>> {
    return this.get<Product[]>(
      `${this.basePath}/featured`,
      {
        useCache: true,
        cacheKey: 'featured-products'
      }
    );
  }

  /**
   * Get product categories with counts
   */
  async getCategories(): Promise<ApiResponse<Array<{ category: ProductCategory; count: number }>>> {
    return this.get<Array<{ category: ProductCategory; count: number }>>(
      `${this.basePath}/categories`,
      {
        useCache: true,
        cacheKey: 'product-categories'
      }
    );
  }

  /**
   * Get related products
   */
  async getRelatedProducts(productId: string): Promise<ApiResponse<Product[]>> {
    return this.get<Product[]>(
      `${this.basePath}/${productId}/related`,
      {
        useCache: true,
        cacheKey: `related-${productId}`
      }
    );
  }

  /**
   * Create a new product (admin only)
   */
  async createProduct(product: ProductCreateDto): Promise<ApiResponse<Product>> {
    const response = await this.post<Product>(this.basePath, product);

    // Clear relevant caches
    if (response.data) {
      this.clearCache();
    }

    return response;
  }

  /**
   * Update a product (admin only)
   */
  async updateProduct(product: ProductUpdateDto): Promise<ApiResponse<Product>> {
    const { id, ...updateData } = product;
    const response = await this.put<Product>(`${this.basePath}/${id}`, updateData);

    // Clear relevant caches
    if (response.data) {
      this.clearCache();
    }

    return response;
  }

  /**
   * Delete a product (admin only)
   */
  async deleteProduct(id: string): Promise<ApiResponse<void>> {
    const response = await this.delete<void>(`${this.basePath}/${id}`);

    // Clear relevant caches
    if (response.status === 200 || response.status === 204) {
      this.clearCache();
    }

    return response;
  }

  /**
   * Update product inventory
   */
  async updateInventory(
    productId: string,
    quantity: number,
    operation: 'add' | 'subtract' | 'set'
  ): Promise<ApiResponse<Product>> {
    const response = await this.patch<Product>(
      `${this.basePath}/${productId}/inventory`,
      { quantity, operation }
    );

    // Clear relevant caches
    if (response.data) {
      this.clearCache();
    }

    return response;
  }

  /**
   * Get product reviews
   */
  async getProductReviews(productId: string): Promise<ApiResponse<any[]>> {
    return this.get<any[]>(
      `${this.basePath}/${productId}/reviews`,
      {
        useCache: true,
        cacheKey: `reviews-${productId}`
      }
    );
  }

  /**
   * Add product review
   */
  async addProductReview(
    productId: string,
    review: { rating: number; comment: string }
  ): Promise<ApiResponse<any>> {
    const response = await this.post<any>(
      `${this.basePath}/${productId}/reviews`,
      review
    );

    // Clear review cache
    if (response.data) {
      this.clearCache();
    }

    return response;
  }
}