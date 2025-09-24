/**
 * SEO Route Handler
 * Dynamic URL generation and parsing for SEO-optimized routes
 */

import { DynamicRouteParams, RouteGenerator, SEORouteConfig } from '@/types/seo.types';

export class SEORouteHandler implements RouteGenerator {
  private config: SEORouteConfig;
  private defaultPatterns: SEORouteConfig = {
    productDetailPattern: 'dispensary-near-me/{city}/{slug}',
    categoryPattern: 'cannabis/{category}',
    brandPattern: 'brands/{brand}',
    searchPattern: 'search',
    locationPattern: '{city}-dispensary',
    storeLocatorPattern: 'dispensaries-near-me'
  };

  constructor(config?: SEORouteConfig) {
    this.config = { ...this.defaultPatterns, ...config };
  }

  /**
   * Generate SEO-friendly URL from pattern and parameters
   */
  generate(pattern: string, params: DynamicRouteParams): string {
    let url = pattern;

    // Replace placeholders with actual values
    Object.keys(params).forEach(key => {
      const value = params[key];
      if (value) {
        const slug = this.slugify(value);
        url = url.replace(`{${key}}`, slug);
      }
    });

    // Remove any remaining placeholders
    url = url.replace(/\{[^}]+\}/g, '');

    // Clean up double slashes
    url = url.replace(/\/+/g, '/');

    // Remove trailing slash if exists
    url = url.replace(/\/$/, '');

    return `/${url}`;
  }

  /**
   * Parse URL to extract parameters based on pattern
   */
  parse(url: string, pattern: string): DynamicRouteParams | null {
    // Remove leading slash
    url = url.replace(/^\//, '');
    pattern = pattern.replace(/^\//, '');

    const urlParts = url.split('/');
    const patternParts = pattern.split('/');

    if (urlParts.length !== patternParts.length) {
      return null;
    }

    const params: DynamicRouteParams = {};

    for (let i = 0; i < patternParts.length; i++) {
      const patternPart = patternParts[i];
      const urlPart = urlParts[i];

      if (patternPart.startsWith('{') && patternPart.endsWith('}')) {
        const paramName = patternPart.slice(1, -1);
        params[paramName] = urlPart;
      } else if (patternPart !== urlPart) {
        return null;
      }
    }

    return params;
  }

  /**
   * Validate if URL matches pattern
   */
  isValid(url: string, pattern: string): boolean {
    return this.parse(url, pattern) !== null;
  }

  /**
   * Generate product detail URL
   */
  generateProductUrl(product: {
    slug?: string;
    name: string;
    category?: string;
    city?: string;
  }): string {
    const pattern = this.config.productDetailPattern || this.defaultPatterns.productDetailPattern!;

    // Only use the provided slug, don't fall back to slugify
    if (!product.slug) {
      console.error('No slug provided for product:', product.name);
      // Fallback to slugified name only if absolutely necessary
      const slug = this.slugify(product.name);
      console.warn('Using fallback slugified name:', slug);
      return this.generate(pattern, {
        slug,
        category: product.category,
        city: product.city || 'toronto'
      });
    }

    const city = product.city || 'toronto'; // Default city

    return this.generate(pattern, {
      slug: product.slug,
      category: product.category,
      city
    });
  }

  /**
   * Generate category URL
   */
  generateCategoryUrl(category: string): string {
    const pattern = this.config.categoryPattern || this.defaultPatterns.categoryPattern!;
    return this.generate(pattern, { category: this.slugify(category) });
  }

  /**
   * Generate brand URL
   */
  generateBrandUrl(brand: string): string {
    const pattern = this.config.brandPattern || this.defaultPatterns.brandPattern!;
    return this.generate(pattern, { brand: this.slugify(brand) });
  }

  /**
   * Generate location-based URL
   */
  generateLocationUrl(city: string): string {
    const pattern = this.config.locationPattern || this.defaultPatterns.locationPattern!;
    return this.generate(pattern, { city: this.slugify(city) });
  }

  /**
   * Generate search URL with query parameters
   */
  generateSearchUrl(query: string, filters?: Record<string, string>): string {
    const pattern = this.config.searchPattern || this.defaultPatterns.searchPattern!;
    let url = `/${pattern}`;

    const params = new URLSearchParams();
    params.set('q', query);

    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        params.set(key, value);
      });
    }

    return `${url}?${params.toString()}`;
  }

  /**
   * Convert string to SEO-friendly slug
   */
  private slugify(text: string): string {
    return text
      .toLowerCase()
      .trim()
      .replace(/[^\w\s-]/g, '') // Remove special characters
      .replace(/\s+/g, '-') // Replace spaces with hyphens
      .replace(/-+/g, '-') // Replace multiple hyphens with single hyphen
      .replace(/^-+/, '') // Remove leading hyphens
      .replace(/-+$/, ''); // Remove trailing hyphens
  }

  /**
   * Get all configured patterns
   */
  getPatterns(): SEORouteConfig {
    return this.config;
  }

  /**
   * Update route configuration
   */
  updateConfig(config: Partial<SEORouteConfig>): void {
    this.config = { ...this.config, ...config };
  }

  /**
   * Generate breadcrumb URLs
   */
  generateBreadcrumbs(currentPath: string): Array<{ name: string; url: string }> {
    const parts = currentPath.split('/').filter(Boolean);
    const breadcrumbs: Array<{ name: string; url: string }> = [
      { name: 'Home', url: '/' }
    ];

    let accumulatedPath = '';
    parts.forEach((part, index) => {
      accumulatedPath += `/${part}`;
      const name = this.humanize(part);
      breadcrumbs.push({
        name,
        url: accumulatedPath
      });
    });

    return breadcrumbs;
  }

  /**
   * Convert slug back to human-readable text
   */
  private humanize(slug: string): string {
    return slug
      .replace(/-/g, ' ')
      .replace(/\b\w/g, char => char.toUpperCase());
  }

  /**
   * Generate alternate language URLs
   */
  generateAlternateUrls(currentUrl: string, languages: string[]): Array<{ lang: string; url: string }> {
    return languages.map(lang => ({
      lang,
      url: `/${lang}${currentUrl}`
    }));
  }

  /**
   * Generate canonical URL
   */
  generateCanonicalUrl(url: string, baseUrl: string): string {
    // Remove query parameters for canonical
    const urlWithoutQuery = url.split('?')[0];
    // Remove trailing slash
    const cleanUrl = urlWithoutQuery.replace(/\/$/, '');
    return `${baseUrl}${cleanUrl}`;
  }
}

// Export singleton instance
export const seoRouteHandler = new SEORouteHandler();