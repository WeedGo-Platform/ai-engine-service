/**
 * Type mappers to convert between API and Redux state types
 */

import { Product } from '@/api/products';
import { IProduct } from '@/templates/types';

/**
 * Map API Product to Redux IProduct
 * Handles property name differences and missing fields
 */
export function mapProductToIProduct(product: Product): IProduct {
  return {
    id: product.id,
    sku: product.sku,
    slug: product.slug,
    name: product.name,
    description: product.description || '',
    category: product.category,
    brand: product.brand,
    price: product.price,
    sale_price: product.original_price ? product.price : undefined,
    thc_content: product.thc_content,
    cbd_content: product.cbd_content,
    terpenes: product.terpenes,
    effects: product.effects,
    image_url: product.image_url,
    images: product.images,
    in_stock: product.in_stock,
    quantity_available: product.available_quantity, // Map available_quantity to quantity_available
    unit_weight: product.size ? `${product.size}g` : undefined,
    rating: product.rating,
    reviews_count: product.review_count,
    // Additional IProduct fields that may not exist in Product
    strain: product.strain_type || undefined,
    size: product.size || undefined,
    thc: product.thc_content, // Alias for compatibility
    cbd: product.cbd_content, // Alias for compatibility
  } as IProduct;
}

/**
 * Map Redux IProduct to API Product
 * For sending data back to the API
 */
export function mapIProductToProduct(iProduct: IProduct): Partial<Product> {
  return {
    id: iProduct.id,
    sku: iProduct.sku,
    slug: iProduct.slug,
    name: iProduct.name,
    description: iProduct.description,
    category: iProduct.category,
    brand: iProduct.brand,
    price: iProduct.sale_price || iProduct.price,
    original_price: iProduct.sale_price ? iProduct.price : undefined,
    thc_content: iProduct.thc_content,
    cbd_content: iProduct.cbd_content,
    terpenes: iProduct.terpenes,
    effects: iProduct.effects,
    image_url: iProduct.image_url,
    images: iProduct.images,
    in_stock: iProduct.in_stock,
    available_quantity: iProduct.quantity_available, // Map back
    rating: iProduct.rating,
    review_count: iProduct.reviews_count,
  };
}

/**
 * Map array of Products to IProducts
 */
export function mapProductsToIProducts(products: Product[]): IProduct[] {
  return products.map(mapProductToIProduct);
}

/**
 * Extend IProduct with additional cart item properties
 */
export interface ExtendedCartItem {
  image?: string;
  name?: string;
  sku?: string;
  brand?: string;
  size?: number;
  weight?: number;
  unit?: string;
  category?: string;
  strain?: string;
  thc?: number;
  cbd?: number;
  maxQuantity?: number;
}

/**
 * Create a default Product object for testing
 */
export function createDefaultProduct(): Product {
  return {
    id: '',
    sku: '',
    slug: '',
    name: '',
    brand: '',
    category: '',
    sub_category: '',
    plant_type: null,
    strain_type: null,
    size: 0,
    image_url: '',
    gtin: 0,
    ocs_item_number: 0,
    price: 0,
    unit_price: 0,
    available_quantity: 0,
    in_stock: false,
    stock_status: 'out_of_stock',
    thc_content: 0,
    cbd_content: 0,
    batch_count: 0,
    batches: '[]',
  };
}

/**
 * Create a default IProduct object for testing
 */
export function createDefaultIProduct(): IProduct {
  return {
    id: '',
    sku: '',
    slug: '',
    name: '',
    description: '',
    category: '',
    brand: '',
    price: 0,
    thc_content: 0,
    cbd_content: 0,
    image_url: '',
    in_stock: false,
    quantity_available: 0,
  };
}