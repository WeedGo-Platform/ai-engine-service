# Product API Gap Analysis Report

## Executive Summary
This report provides a comprehensive analysis of the product-related API endpoints expected by the frontend e-commerce application versus what is actually implemented in the backend.

## Frontend Expected Product API Endpoints

Based on analysis of `/Users/charrcy/projects/WeedGo/frontend/web-app/ecommerce-web`, the frontend expects the following product-related endpoints:

### Core Product Endpoints (from app/lib/api.server.ts)
1. **GET /api/products** - Get paginated products with filters
   - Query params: category, subCategory, strainType, plantType, search, priceMin, priceMax, onSale, inStock, sortBy, page, pageSize
   - Expected response: PaginatedResponse<Product>

2. **GET /api/products/{idOrSlug}** - Get single product details
   - Path param: product ID or slug
   - Expected response: Product object

3. **POST /api/products/batch** - Get multiple products by IDs
   - Body: { ids: string[] }
   - Expected response: Product[]

4. **GET /api/products/featured** - Get featured products
   - Query param: limit (default 8)
   - Expected response: Product[]

5. **GET /api/products/bestsellers** - Get bestselling products
   - Query param: limit (default 8)
   - Expected response: Product[]

6. **GET /api/products/new-arrivals** - Get new arrival products
   - Query param: limit (default 8)
   - Expected response: Product[]

### Search Endpoints (from various components)
7. **GET /api/search/products** - Search products
   - Query params: q (search query), filters
   - Expected response: Product[]

8. **GET /api/products/search** - Alternative search endpoint
   - Query params: q, limit
   - Expected response: { results: Product[] }

### Recommendation Endpoints (from components/RecommendationSection.tsx)
9. **GET /api/products/{id}/related** - Get related products
   - Query param: limit
   - Expected response: Product[]

10. **GET /api/products/{id}/frequently-bought** - Get frequently bought together
    - Query param: limit
    - Expected response: Product[]

11. **GET /api/products/recommended** - Get recommended products
    - Query params: based_on (product ID), limit
    - Expected response: Product[]

### Additional Endpoints Used in Components
12. **GET /api/products?featured=true** - Featured products filter
13. **GET /api/products?onSale=true** - Sale products filter
14. **GET /api/products?sort=rating&order=desc** - Top-rated products
15. **GET /api/products?sort=createdAt&order=desc** - New arrivals
16. **GET /api/products?categories={category}&limit={limit}&sort=popularity** - Category-specific popular products

## Backend Implemented Product Endpoints

Based on analysis of `/Users/charrcy/projects/WeedGo/microservices/ai-engine-service/src/Backend`, the following product endpoints are actually implemented:

### Product Endpoints (api/product_endpoints.py)
✅ **GET /api/products** - Paginated products with filters
✅ **GET /api/products/{id_or_slug}** - Single product details
✅ **POST /api/products/batch** - Get products by IDs
✅ **GET /api/products/featured** - Featured products
✅ **GET /api/products/bestsellers** - Bestselling products
✅ **GET /api/products/new-arrivals** - New arrival products

### Product Details Endpoints (api/product_details_endpoints.py)
✅ **GET /api/products/details/{product_id}** - Comprehensive product details

### Search Endpoints (api/search_endpoints.py)
✅ **GET /api/search/products** - Product search with filters

### Promotion/Recommendation Endpoints (api/promotion_endpoints.py)
✅ **GET /api/promotions/recommendations/similar/{product_id}** - Similar products
✅ **GET /api/promotions/recommendations/complementary/{product_id}** - Complementary products
✅ **GET /api/promotions/recommendations/trending** - Trending products

### Cart Recommendation Endpoints (api/cart_endpoints.py)
✅ **GET /api/cart/recommendations** - Cart-based recommendations

## Gap Analysis

### ❌ Missing Endpoints
1. **GET /api/products/{id}/related** - Frontend expects this specific path
   - Backend has similar functionality at `/api/promotions/recommendations/similar/{product_id}`
   - **Action Required**: Add route alias or update frontend

2. **GET /api/products/{id}/frequently-bought** - Frontend expects this specific path
   - Backend has cart recommendations but not product-specific frequently bought
   - **Action Required**: Implement endpoint or update frontend

3. **GET /api/products/recommended** - Frontend expects this for product-based recommendations
   - Backend has similar functionality but different path
   - **Action Required**: Add endpoint or update frontend

4. **GET /api/products/search** - Alternative search endpoint expected by SearchBar component
   - Backend has `/api/search/products` instead
   - **Action Required**: Add route alias or update frontend

### ⚠️ Path Mismatches
1. **Recommendation endpoints** are under `/api/promotions/recommendations/` in backend but frontend expects them under `/api/products/`
2. **Search endpoint** is at `/api/search/products` but some frontend components expect `/api/products/search`

### ⚠️ Response Format Differences
1. **Product fields mapping**:
   - Frontend expects: `slug`, `description`, `images[]`, `sizes[]`, `basePrice`, `compareAtPrice`, `rating`, `reviewCount`, `featured`, `bestseller`, `newArrival`, `onSale`, `tags[]`
   - Backend provides: `sku`, `short_description`, `image_url`, `price`, `quantity_available`, `in_stock`
   - **Missing fields**: slug, images array, sizes array, ratings, reviews, tags

2. **Category field format**:
   - Frontend expects specific category types from tenant.ts
   - Backend provides string categories from database

### ⚠️ Query Parameter Differences
1. **Sort parameter**:
   - Frontend sends: `sortBy` with values like 'popular', 'price-asc', 'price-desc', 'newest', 'rating', 'thc-high', 'thc-low'
   - Backend expects: `sortBy` and `sortOrder` separately

2. **Filter parameters**:
   - Frontend sends: `subCategory`, `strainType`, `plantType`
   - Backend supports these but may have case sensitivity issues

## Recommendations

### Priority 1: Critical Fixes
1. **Add missing product transformation layer** to map backend fields to frontend expected format
2. **Implement slug generation** for products (currently missing)
3. **Add product images array support** (frontend expects array, backend has single image_url)
4. **Implement product sizes/variants structure** expected by frontend

### Priority 2: Route Alignment
1. **Add route aliases** for mismatched paths:
   ```python
   # Add to product_endpoints.py
   @router.get("/{id}/related")  # Alias for similar products
   @router.get("/{id}/frequently-bought")  # New endpoint needed
   @router.get("/search")  # Alias for search
   ```

2. **Or update frontend** to use existing backend paths

### Priority 3: Feature Implementation
1. **Implement product reviews/ratings** system (currently missing)
2. **Add frequently bought together** tracking and endpoint
3. **Implement product tags** system
4. **Add proper featured/bestseller/new arrival flags** to products

### Priority 4: Data Enhancements
1. **Add multiple images support** per product
2. **Implement product variants/sizes** properly
3. **Add compare-at pricing** for sales
4. **Implement proper slug generation** from product names

## Database Schema Considerations
The backend uses `inventory_products_view` which appears to be based on OCS (Ontario Cannabis Store) catalog structure. This may need adaptation for the more generic e-commerce structure expected by the frontend.

## Conclusion
While the backend implements most core product endpoints, there are significant gaps in:
1. Response format and field mapping
2. Route path alignment
3. Missing features like reviews, ratings, and product relationships
4. Product variant/size structure

The backend appears to be built for a specific cannabis retail use case while the frontend expects a more generic e-commerce API structure. A transformation layer or API adapter pattern would help bridge these gaps.