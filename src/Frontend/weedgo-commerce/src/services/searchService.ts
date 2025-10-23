/**
 * Advanced search and filtering service for products
 */

import apiClient from '@api/client';
import { IProduct } from '@templates/types';
import { logger } from '@utils/logger';

// Search and filter types
export interface SearchFilters {
  query?: string;
  category?: string | string[];
  brand?: string | string[];
  priceMin?: number;
  priceMax?: number;
  thcMin?: number;
  thcMax?: number;
  cbdMin?: number;
  cbdMax?: number;
  strain?: string[];
  effects?: string[];
  terpenes?: string[];
  size?: string[];
  weight?: string[];
  rating?: number;
  inStock?: boolean;
  onSale?: boolean;
  featured?: boolean;
  sortBy?: 'relevance' | 'price_asc' | 'price_desc' | 'rating' | 'newest' | 'name_asc' | 'name_desc' | 'thc_desc' | 'cbd_desc';
  page?: number;
  limit?: number;
}

export interface SearchResult {
  products: IProduct[];
  totalCount: number;
  page: number;
  totalPages: number;
  facets: SearchFacets;
  query: string;
  appliedFilters: SearchFilters;
}

export interface SearchFacets {
  categories: FacetValue[];
  brands: FacetValue[];
  strains: FacetValue[];
  effects: FacetValue[];
  terpenes: FacetValue[];
  sizes: FacetValue[];
  weights: FacetValue[];
  priceRanges: PriceRange[];
  thcRanges: PotencyRange[];
  cbdRanges: PotencyRange[];
}

export interface FacetValue {
  value: string;
  label: string;
  count: number;
}

export interface PriceRange {
  min: number;
  max: number;
  label: string;
  count: number;
}

export interface PotencyRange {
  min: number;
  max: number;
  label: string;
  count: number;
}

export interface SearchSuggestion {
  id: string;
  text: string;
  type: 'product' | 'category' | 'brand' | 'strain';
  count?: number;
  data?: any;
}

export interface SearchHistory {
  query: string;
  timestamp: Date;
  resultsCount: number;
  filters?: SearchFilters;
}

class SearchService {
  private static instance: SearchService;
  private searchHistory: SearchHistory[] = [];
  private searchCache = new Map<string, { result: SearchResult; timestamp: number }>();
  private readonly CACHE_DURATION = 5 * 60 * 1000; // 5 minutes
  private readonly MAX_HISTORY = 10;
  private abortController: AbortController | null = null;

  private constructor() {
    this.loadSearchHistory();
  }

  public static getInstance(): SearchService {
    if (!SearchService.instance) {
      SearchService.instance = new SearchService();
    }
    return SearchService.instance;
  }

  /**
   * Perform advanced product search with filters
   */
  async searchProducts(filters: SearchFilters): Promise<SearchResult> {
    try {
      // Cancel any ongoing search
      if (this.abortController) {
        this.abortController.abort();
      }

      // Create new abort controller for this search
      this.abortController = new AbortController();

      // Check cache
      const cacheKey = this.getCacheKey(filters);
      const cached = this.getFromCache(cacheKey);
      if (cached) {
        logger.debug('Returning cached search results', { cacheKey });
        return cached;
      }

      // Build query parameters
      const params = this.buildSearchParams(filters);

      // Perform search
      const response = await apiClient.get('/api/products/search', {
        params,
        signal: this.abortController.signal,
      });

      const result: SearchResult = {
        products: response.data.products || [],
        totalCount: response.data.total_count || 0,
        page: response.data.page || filters.page || 1,
        totalPages: response.data.total_pages || 1,
        facets: response.data.facets || this.getDefaultFacets(),
        query: filters.query || '',
        appliedFilters: filters,
      };

      // Cache result
      this.addToCache(cacheKey, result);

      // Add to search history
      if (filters.query) {
        this.addToHistory({
          query: filters.query,
          timestamp: new Date(),
          resultsCount: result.totalCount,
          filters,
        });
      }

      return result;
    } catch (error: any) {
      if (error.name === 'AbortError') {
        logger.debug('Search request was cancelled');
        throw error;
      }

      logger.error('Product search failed', error);
      throw new Error('Failed to search products. Please try again.');
    } finally {
      this.abortController = null;
    }
  }

  /**
   * Get search suggestions based on partial query
   */
  async getSearchSuggestions(query: string): Promise<SearchSuggestion[]> {
    if (!query || query.length < 2) {
      return [];
    }

    try {
      const response = await apiClient.get('/api/products/suggestions', {
        params: { q: query, limit: 10 },
      });

      return response.data.suggestions || [];
    } catch (error) {
      logger.error('Failed to get search suggestions', error);
      return this.getOfflineSuggestions(query);
    }
  }

  /**
   * Get popular search terms
   */
  async getPopularSearches(): Promise<string[]> {
    try {
      const response = await apiClient.get('/api/products/popular-searches');
      return response.data.searches || [];
    } catch (error) {
      logger.error('Failed to get popular searches', error);
      return this.getDefaultPopularSearches();
    }
  }

  /**
   * Get related searches for a query
   */
  async getRelatedSearches(query: string): Promise<string[]> {
    try {
      const response = await apiClient.get('/api/products/related-searches', {
        params: { q: query },
      });
      return response.data.searches || [];
    } catch (error) {
      logger.error('Failed to get related searches', error);
      return [];
    }
  }

  /**
   * Apply smart filters based on user preferences
   */
  async getSmartFilters(userPreferences?: any): Promise<SearchFilters> {
    try {
      const response = await apiClient.get('/api/products/smart-filters', {
        params: { preferences: JSON.stringify(userPreferences) },
      });

      return response.data.filters || {};
    } catch (error) {
      logger.error('Failed to get smart filters', error);
      return this.getDefaultSmartFilters(userPreferences);
    }
  }

  /**
   * Get filter options for a specific facet
   */
  async getFacetOptions(facetType: string): Promise<FacetValue[]> {
    try {
      const response = await apiClient.get(`/api/products/facets/${facetType}`);
      return response.data.options || [];
    } catch (error) {
      logger.error('Failed to get facet options', error);
      return [];
    }
  }

  /**
   * Build advanced search query
   */
  buildAdvancedQuery(params: {
    allWords?: string;
    exactPhrase?: string;
    anyWords?: string;
    noneWords?: string;
  }): string {
    const parts: string[] = [];

    if (params.exactPhrase) {
      parts.push(`"${params.exactPhrase}"`);
    }

    if (params.allWords) {
      parts.push(params.allWords.split(' ').map(w => `+${w}`).join(' '));
    }

    if (params.anyWords) {
      parts.push(`(${params.anyWords.split(' ').join(' OR ')})`);
    }

    if (params.noneWords) {
      parts.push(params.noneWords.split(' ').map(w => `-${w}`).join(' '));
    }

    return parts.join(' ').trim();
  }

  /**
   * Parse natural language search query
   */
  parseNaturalQuery(query: string): SearchFilters {
    const filters: SearchFilters = { query };

    // Extract price range
    const priceMatch = query.match(/under \$(\d+)|below \$(\d+)|\$(\d+)-\$(\d+)/i);
    if (priceMatch) {
      if (priceMatch[1] || priceMatch[2]) {
        filters.priceMax = parseInt(priceMatch[1] || priceMatch[2]);
      } else if (priceMatch[3] && priceMatch[4]) {
        filters.priceMin = parseInt(priceMatch[3]);
        filters.priceMax = parseInt(priceMatch[4]);
      }
    }

    // Extract THC/CBD requirements
    const thcMatch = query.match(/(\d+)%?\+? thc|high thc|low thc/i);
    if (thcMatch) {
      if (thcMatch[1]) {
        filters.thcMin = parseInt(thcMatch[1]);
      } else if (query.includes('high thc')) {
        filters.thcMin = 20;
      } else if (query.includes('low thc')) {
        filters.thcMax = 10;
      }
    }

    const cbdMatch = query.match(/(\d+)%?\+? cbd|high cbd|low cbd/i);
    if (cbdMatch) {
      if (cbdMatch[1]) {
        filters.cbdMin = parseInt(cbdMatch[1]);
      } else if (query.includes('high cbd')) {
        filters.cbdMin = 10;
      } else if (query.includes('low cbd')) {
        filters.cbdMax = 5;
      }
    }

    // Extract strain types
    if (/\bindica\b/i.test(query)) filters.strain = ['indica'];
    if (/\bsativa\b/i.test(query)) filters.strain = [...(filters.strain || []), 'sativa'];
    if (/\bhybrid\b/i.test(query)) filters.strain = [...(filters.strain || []), 'hybrid'];

    // Extract categories
    const categories = ['flower', 'edibles', 'concentrates', 'vapes', 'accessories'];
    categories.forEach(cat => {
      if (query.toLowerCase().includes(cat)) {
        filters.category = cat;
      }
    });

    // Extract effects
    const effects = ['relaxed', 'happy', 'euphoric', 'uplifted', 'creative', 'focused', 'energetic', 'sleepy'];
    const matchedEffects = effects.filter(effect => query.toLowerCase().includes(effect));
    if (matchedEffects.length > 0) {
      filters.effects = matchedEffects;
    }

    // Extract sorting preference
    if (/cheapest|lowest price/i.test(query)) {
      filters.sortBy = 'price_asc';
    } else if (/best rated|highest rated|top rated/i.test(query)) {
      filters.sortBy = 'rating';
    } else if (/newest|new arrival|latest/i.test(query)) {
      filters.sortBy = 'newest';
    } else if (/strongest|highest thc|most potent/i.test(query)) {
      filters.sortBy = 'thc_desc';
    }

    // Extract stock preference
    if (/in stock|available/i.test(query)) {
      filters.inStock = true;
    }

    // Extract sale preference
    if (/on sale|discount|deal/i.test(query)) {
      filters.onSale = true;
    }

    return filters;
  }

  /**
   * Get search history
   */
  getSearchHistory(): SearchHistory[] {
    return this.searchHistory;
  }

  /**
   * Get filter options for a category
   */
  async getFilterOptions(category?: string): Promise<any> {
    // Mock implementation - replace with actual API call
    return {
      brands: [],
      strains: [],
      sizes: [],
      weights: [],
      priceRanges: [],
      thcRanges: [],
      cbdRanges: []
    };
  }

  /**
   * Clear search history
   */
  clearSearchHistory(): void {
    this.searchHistory = [];
    this.saveSearchHistory();
  }

  /**
   * Remove specific search from history
   */
  removeFromHistory(query: string): void {
    this.searchHistory = this.searchHistory.filter(h => h.query !== query);
    this.saveSearchHistory();
  }

  /**
   * Build search parameters
   */
  private buildSearchParams(filters: SearchFilters): Record<string, any> {
    const params: Record<string, any> = {};

    if (filters.query) params.q = filters.query;
    if (filters.category) params.category = Array.isArray(filters.category) ? filters.category.join(',') : filters.category;
    if (filters.brand) params.brand = Array.isArray(filters.brand) ? filters.brand.join(',') : filters.brand;
    if (filters.priceMin !== undefined) params.price_min = filters.priceMin;
    if (filters.priceMax !== undefined) params.price_max = filters.priceMax;
    if (filters.thcMin !== undefined) params.thc_min = filters.thcMin;
    if (filters.thcMax !== undefined) params.thc_max = filters.thcMax;
    if (filters.cbdMin !== undefined) params.cbd_min = filters.cbdMin;
    if (filters.cbdMax !== undefined) params.cbd_max = filters.cbdMax;
    if (filters.strain) params.strain = filters.strain.join(',');
    if (filters.effects) params.effects = filters.effects.join(',');
    if (filters.terpenes) params.terpenes = filters.terpenes.join(',');
    if (filters.size) params.size = filters.size.join(',');
    if (filters.weight) params.weight = filters.weight.join(',');
    if (filters.rating !== undefined) params.rating = filters.rating;
    if (filters.inStock !== undefined) params.in_stock = filters.inStock;
    if (filters.onSale !== undefined) params.on_sale = filters.onSale;
    if (filters.featured !== undefined) params.featured = filters.featured;
    if (filters.sortBy) params.sort = filters.sortBy;
    if (filters.page) params.page = filters.page;
    if (filters.limit) params.limit = filters.limit;

    return params;
  }

  /**
   * Get cache key for search filters
   */
  private getCacheKey(filters: SearchFilters): string {
    return JSON.stringify(filters);
  }

  /**
   * Get from cache
   */
  private getFromCache(key: string): SearchResult | null {
    const cached = this.searchCache.get(key);
    if (cached && Date.now() - cached.timestamp < this.CACHE_DURATION) {
      return cached.result;
    }
    this.searchCache.delete(key);
    return null;
  }

  /**
   * Add to cache
   */
  private addToCache(key: string, result: SearchResult): void {
    this.searchCache.set(key, {
      result,
      timestamp: Date.now(),
    });

    // Limit cache size
    if (this.searchCache.size > 50) {
      const firstKey = this.searchCache.keys().next().value;
      if (firstKey) {
        this.searchCache.delete(firstKey);
      }
    }
  }

  /**
   * Add to search history
   */
  private addToHistory(search: SearchHistory): void {
    // Remove duplicate if exists
    this.searchHistory = this.searchHistory.filter(h => h.query !== search.query);

    // Add to beginning
    this.searchHistory.unshift(search);

    // Limit history size
    if (this.searchHistory.length > this.MAX_HISTORY) {
      this.searchHistory = this.searchHistory.slice(0, this.MAX_HISTORY);
    }

    this.saveSearchHistory();
  }

  /**
   * Load search history from localStorage
   */
  private loadSearchHistory(): void {
    try {
      const stored = localStorage.getItem('search_history');
      if (stored) {
        this.searchHistory = JSON.parse(stored);
      }
    } catch (error) {
      logger.error('Failed to load search history', error);
      this.searchHistory = [];
    }
  }

  /**
   * Save search history to localStorage
   */
  private saveSearchHistory(): void {
    try {
      localStorage.setItem('search_history', JSON.stringify(this.searchHistory));
    } catch (error) {
      logger.error('Failed to save search history', error);
    }
  }

  /**
   * Get offline suggestions based on search history
   */
  private getOfflineSuggestions(query: string): SearchSuggestion[] {
    const q = query.toLowerCase();
    return this.searchHistory
      .filter(h => h.query.toLowerCase().includes(q))
      .map((h, index) => ({
        id: `history-${index}`,
        text: h.query,
        type: 'product' as const,
      }))
      .slice(0, 5);
  }

  /**
   * Get default popular searches
   */
  private getDefaultPopularSearches(): string[] {
    return [
      'flower',
      'edibles',
      'indica',
      'sativa',
      'high THC',
      'CBD oil',
      'vape pens',
      'pre-rolls',
      'gummies',
      'concentrates',
    ];
  }

  /**
   * Get default smart filters
   */
  private getDefaultSmartFilters(preferences?: any): SearchFilters {
    const filters: SearchFilters = {
      inStock: true,
      sortBy: 'relevance',
    };

    if (preferences?.favoriteCategory) {
      filters.category = preferences.favoriteCategory;
    }

    if (preferences?.preferredPriceRange) {
      filters.priceMin = preferences.preferredPriceRange.min;
      filters.priceMax = preferences.preferredPriceRange.max;
    }

    if (preferences?.preferredStrain) {
      filters.strain = [preferences.preferredStrain];
    }

    return filters;
  }

  /**
   * Get default facets
   */
  private getDefaultFacets(): SearchFacets {
    return {
      categories: [],
      brands: [],
      strains: [],
      effects: [],
      terpenes: [],
      sizes: [],
      weights: [],
      priceRanges: [],
      thcRanges: [],
      cbdRanges: [],
    };
  }

  /**
   * Cancel ongoing search
   */
  public cancelSearch(): void {
    if (this.abortController) {
      this.abortController.abort();
      this.abortController = null;
    }
  }

  /**
   * Clear search cache
   */
  public clearCache(): void {
    this.searchCache.clear();
  }
}

// Export singleton instance
export const searchService = SearchService.getInstance();

// Export convenience functions
export const searchProducts = (filters: SearchFilters) => searchService.searchProducts(filters);
export const getSearchSuggestions = (query: string) => searchService.getSearchSuggestions(query);
export const getPopularSearches = () => searchService.getPopularSearches();
export const getRelatedSearches = (query: string) => searchService.getRelatedSearches(query);
export const parseNaturalQuery = (query: string) => searchService.parseNaturalQuery(query);
export const getSearchHistory = () => searchService.getSearchHistory();
export const clearSearchHistory = () => searchService.clearSearchHistory();