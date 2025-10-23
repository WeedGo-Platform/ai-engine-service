import React, { useEffect, useState, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { HelmetProvider } from 'react-helmet-async';
import { ShoppingCartIcon, HeartIcon, ShareIcon } from '@heroicons/react/24/outline';
import { HeartIcon as HeartSolidIcon } from '@heroicons/react/24/solid';
import { productsApi, Product } from '@api/products';
import { recommendationsApi, RecommendedProduct } from '@api/recommendations';
import { ProductRecommendations } from '@components/ProductRecommendations';
import { addItem } from '@features/cart/cartSlice';
import { RootState } from '@store/index';
import toast from 'react-hot-toast';
import {
  MetaManager,
  generateProductMetaTags,
  generateProductStructuredData
} from '@/services/seo/MetaManager';
import { seoRouteHandler } from '@/services/seo/RouteHandler';
import { useTenant } from '@/contexts/TenantContext';
import Breadcrumbs from '@/components/common/Breadcrumbs';

const ProductDetailSEO: React.FC = () => {
  // Get slug from URL params (supports both slug and SKU for backwards compatibility)
  const { identifier, slug } = useParams<{ identifier?: string; slug?: string }>();
  const productSlug = slug || identifier; // Use slug if available, otherwise identifier
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { tenant } = useTenant();

  const [product, setProduct] = useState<Product | null>(null);
  const [loading, setLoading] = useState(true);
  const [quantity, setQuantity] = useState(1);
  const [isWishlisted, setIsWishlisted] = useState(false);
  const [selectedImage, setSelectedImage] = useState(0);
  const [similarProducts, setSimilarProducts] = useState<RecommendedProduct[]>([]);
  const [frequentlyBought, setFrequentlyBought] = useState<RecommendedProduct[]>([]);
  const [loadingRecommendations, setLoadingRecommendations] = useState(false);

  const { selectedStore } = useSelector((state: RootState) => state.store || {});
  const currentCity = selectedStore?.city || 'toronto';

  useEffect(() => {
    loadProduct();
  }, [productSlug]);

  // Fetch recommendations when product changes
  useEffect(() => {
    const fetchRecommendations = async () => {
      if (!product) return;

      setLoadingRecommendations(true);
      try {
        // Try using SKU first, fall back to ID if needed
        const productIdentifier = product.sku || product.id;

        // Fetch multiple types of recommendations in parallel
        const [similar, frequently] = await Promise.allSettled([
          recommendationsApi.getSimilarProducts(productIdentifier, 8),
          recommendationsApi.getFrequentlyBoughtTogether(productIdentifier, 4)
        ]);

        // Handle results even if some fail
        if (similar.status === 'fulfilled') {
          setSimilarProducts(similar.value);
        }
        if (frequently.status === 'fulfilled') {
          setFrequentlyBought(frequently.value);
        }
      } catch (error) {
        console.error('Error fetching product recommendations:', error);
        // Don't show errors to users for optional features
      } finally {
        setLoadingRecommendations(false);
      }
    };

    fetchRecommendations();
  }, [product]);

  const loadProduct = async () => {
    if (!productSlug) return;

    setLoading(true);
    try {
      // Search for product by slug or SKU using the search endpoint
      const storeId = localStorage.getItem('selected_store_id');
      const response = await productsApi.search({
        query: productSlug,
        limit: 10
      });

      // Find exact match by slug or SKU
      let data: Product | null = null;
      if (response.products && response.products.length > 0) {
        // First try to find by slug
        data = response.products.find(p => p.slug === productSlug) || null;

        // If not found by slug, try by SKU
        if (data === null) {
          data = response.products.find(p => p.sku === productSlug || p.id === productSlug) || null;
        }

        // If still not found, use the first result if it's a close match
        if (data === null && response.products.length === 1) {
          data = response.products[0];
        }
      }

      if (data) {
        setProduct(data);

        // Redirect to SEO-friendly URL if accessed by SKU
        if (data.slug && window.location.pathname.includes(data.sku)) {
          const seoUrl = seoRouteHandler.generateProductUrl({
            slug: data.slug,
            name: data.name,
            category: data.category,
            city: currentCity
          });
          navigate(seoUrl, { replace: true });
        }
      } else {
        toast.error('Product not found');
        navigate('/products');
      }
    } catch (error) {
      console.error('Failed to load product:', error);
      toast.error('Failed to load product details');
    } finally {
      setLoading(false);
    }
  };

  // Generate SEO meta tags
  const metaTags = useMemo(() => {
    if (!product) return null;

    return generateProductMetaTags({
      name: product.name,
      description: product.description || `Premium ${product.category} cannabis product`,
      image: product.image_url,
      price: product.price,
      brand: product.brand,
      category: product.category,
      thc: product.thc_content,
      cbd: product.cbd_content
    });
  }, [product]);

  // Generate structured data
  const structuredData = useMemo(() => {
    if (!product || !tenant) return [];

    return [
      generateProductStructuredData({
        name: product.name,
        description: product.description || '',
        image: product.image_url || '',
        brand: product.brand || 'Unknown',
        sku: product.sku,
        price: product.price,
        currency: 'CAD',
        inStock: product.in_stock,
        storeName: tenant.name || 'Cannabis Store',
        rating: product.rating,
        reviewCount: product.review_count
      })
    ];
  }, [product, tenant]);

  // Generate breadcrumbs
  const breadcrumbItems = useMemo(() => {
    if (!product) return [];

    return [
      { name: 'Products', url: '/products' },
      { name: product.category || 'Cannabis', url: `/products?category=${product.category}` },
      { name: product.name, current: true }
    ];
  }, [product]);

  const handleAddToCart = () => {
    if (!product) return;

    if (!product.in_stock) {
      toast.error('Product is out of stock');
      return;
    }

    if (quantity > product.available_quantity) {
      toast.error(`Only ${product.available_quantity} available`);
      return;
    }

    dispatch(addItem({
      id: product.id,
      sku: product.sku,
      name: product.name,
      price: product.price,
      quantity,
      image: product.image_url,
      thc: product.thc_content,
      cbd: product.cbd_content,
      brand: product.brand,
      category: product.category,
      maxQuantity: product.available_quantity
    }));

    toast.success('Added to cart!');
  };

  const handleQuantityChange = (value: number) => {
    if (!product) return;
    const newQty = Math.max(1, Math.min(value, product.available_quantity));
    setQuantity(newQty);
  };

  const toggleWishlist = () => {
    setIsWishlisted(!isWishlisted);
    toast.success(isWishlisted ? 'Removed from wishlist' : 'Added to wishlist');
  };

  const handleShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: product?.name,
          text: `Check out ${product?.name} - ${product?.thc_content}% THC`,
          url: window.location.href,
        });
      } catch (err) {
        console.log('Share failed:', err);
      }
    } else {
      navigator.clipboard.writeText(window.location.href);
      toast.success('Link copied to clipboard!');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  if (!product) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-gray-500">Product not found</p>
      </div>
    );
  }

  const images = product.images || [product.image_url].filter(Boolean);

  return (
    <HelmetProvider>
      <div className="min-h-screen bg-gray-50">
        {/* SEO Meta Tags */}
        {metaTags && (
          <MetaManager
            meta={metaTags}
            structuredData={structuredData}
            breadcrumbs={breadcrumbItems.map((item, idx) => ({
              name: item.name,
              url: item.url || ''
            }))}
          />
        )}

        {/* Breadcrumbs */}
        <div className="container-max py-4">
          <Breadcrumbs items={breadcrumbItems} showHome={true} />
        </div>

        <div className="container-max py-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
            {/* Image Gallery */}
            <div className="space-y-4">
              <div className="aspect-square bg-white rounded-xl overflow-hidden">
                <img
                  src={images[selectedImage] || '/placeholder.png'}
                  alt={`${product.name} - ${product.category} cannabis product`}
                  className="w-full h-full object-contain"
                  loading="lazy"
                />
              </div>

              {images.length > 1 && (
                <div className="grid grid-cols-4 gap-2">
                  {images.map((img, index) => (
                    <button
                      key={index}
                      onClick={() => setSelectedImage(index)}
                      className={`aspect-square rounded-lg overflow-hidden border-2 ${
                        selectedImage === index ? 'border-primary-500' : 'border-gray-200'
                      }`}
                    >
                      <img
                        src={img}
                        alt={`${product.name} view ${index + 1}`}
                        className="w-full h-full object-cover"
                        loading="lazy"
                      />
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Product Info */}
            <div className="space-y-6">
              {/* Header */}
              <div>
                {product.brand && (
                  <a
                    href={seoRouteHandler.generateBrandUrl(product.brand)}
                    className="text-sm text-primary-600 hover:text-primary-700 font-medium"
                  >
                    {product.brand}
                  </a>
                )}
                <h1 className="text-3xl font-bold text-gray-900 mt-1">{product.name}</h1>

                {/* Rating */}
                {product.rating && (
                  <div className="flex items-center mt-2 space-x-2">
                    <div className="flex text-yellow-400">
                      {[...Array(5)].map((_, i) => (
                        <svg
                          key={i}
                          className={`h-5 w-5 ${i < Math.floor(product.rating!) ? 'fill-current' : 'stroke-current'}`}
                          viewBox="0 0 24 24"
                        >
                          <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
                        </svg>
                      ))}
                    </div>
                    <span className="text-sm text-gray-600">
                      ({product.review_count || 0} reviews)
                    </span>
                  </div>
                )}
              </div>

              {/* Price */}
              <div className="flex items-baseline space-x-3">
                <span className="text-3xl font-bold text-gray-900">
                  ${product.price.toFixed(2)}
                </span>
                {product.original_price && product.original_price > product.price && (
                  <span className="text-xl text-gray-500 line-through">
                    ${product.original_price.toFixed(2)}
                  </span>
                )}
              </div>

              {/* THC/CBD Content */}
              <div className="flex space-x-4">
                {product.thc_content !== undefined && (
                  <div className="flex items-center space-x-1">
                    <span className="text-sm font-medium text-gray-700">THC:</span>
                    <span className="text-sm font-bold text-green-600">
                      {product.thc_content}%
                    </span>
                  </div>
                )}
                {product.cbd_content !== undefined && (
                  <div className="flex items-center space-x-1">
                    <span className="text-sm font-medium text-gray-700">CBD:</span>
                    <span className="text-sm font-bold text-blue-600">
                      {product.cbd_content}%
                    </span>
                  </div>
                )}
              </div>

              {/* Description */}
              {product.description && (
                <div className="prose prose-sm max-w-none">
                  <h2 className="text-lg font-semibold mb-2">Description</h2>
                  <p className="text-gray-600">{product.description}</p>
                </div>
              )}

              {/* Product Details */}
              <div className="border-t pt-4">
                <h3 className="text-lg font-semibold mb-3">Product Details</h3>
                <dl className="space-y-2">
                  <div className="flex justify-between">
                    <dt className="text-gray-600">Category</dt>
                    <dd className="font-medium">
                      <a
                        href={seoRouteHandler.generateCategoryUrl(product.category || 'cannabis')}
                        className="text-primary-600 hover:text-primary-700"
                      >
                        {product.category}
                      </a>
                    </dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-gray-600">SKU</dt>
                    <dd className="font-medium">{product.sku}</dd>
                  </div>
                  {product.strain_type && (
                    <div className="flex justify-between">
                      <dt className="text-gray-600">Strain Type</dt>
                      <dd className="font-medium capitalize">{product.strain_type}</dd>
                    </div>
                  )}
                  <div className="flex justify-between">
                    <dt className="text-gray-600">Availability</dt>
                    <dd className={`font-medium ${product.in_stock ? 'text-green-600' : 'text-red-600'}`}>
                      {product.in_stock ? `In Stock (${product.available_quantity})` : 'Out of Stock'}
                    </dd>
                  </div>
                </dl>
              </div>

              {/* Add to Cart Section */}
              <div className="space-y-4 border-t pt-6">
                <div className="flex items-center space-x-4">
                  <label htmlFor="quantity" className="text-sm font-medium text-gray-700">
                    Quantity:
                  </label>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => handleQuantityChange(quantity - 1)}
                      className="w-8 h-8 rounded-full border border-gray-300 flex items-center justify-center hover:bg-gray-100"
                      disabled={!product.in_stock}
                    >
                      -
                    </button>
                    <input
                      type="number"
                      id="quantity"
                      value={quantity}
                      onChange={(e) => handleQuantityChange(parseInt(e.target.value) || 1)}
                      className="w-16 text-center border-gray-300 rounded-lg"
                      min="1"
                      max={product.available_quantity}
                      disabled={!product.in_stock}
                    />
                    <button
                      onClick={() => handleQuantityChange(quantity + 1)}
                      className="w-8 h-8 rounded-full border border-gray-300 flex items-center justify-center hover:bg-gray-100"
                      disabled={!product.in_stock || quantity >= product.available_quantity}
                    >
                      +
                    </button>
                  </div>
                </div>

                <div className="flex space-x-3">
                  <button
                    onClick={handleAddToCart}
                    disabled={!product.in_stock}
                    className="flex-1 bg-primary-600 text-white px-6 py-3 rounded-lg hover:bg-primary-700 transition-colors flex items-center justify-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <ShoppingCartIcon className="h-5 w-5" />
                    <span>Add to Cart</span>
                  </button>

                  <button
                    onClick={toggleWishlist}
                    className="p-3 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                    aria-label="Add to wishlist"
                  >
                    {isWishlisted ? (
                      <HeartSolidIcon className="h-5 w-5 text-red-500" />
                    ) : (
                      <HeartIcon className="h-5 w-5 text-gray-600" />
                    )}
                  </button>

                  <button
                    onClick={handleShare}
                    className="p-3 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                    aria-label="Share product"
                  >
                    <ShareIcon className="h-5 w-5 text-gray-600" />
                  </button>
                </div>
              </div>

              {/* Store Pickup Info */}
              {selectedStore && (
                <div className="bg-blue-50 rounded-lg p-4">
                  <p className="text-sm text-blue-900">
                    <strong>Pickup available at:</strong> {selectedStore.name}
                  </p>
                  <p className="text-sm text-blue-700 mt-1">
                    {selectedStore.address}
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Recommendations Sections */}
        <div className="container-max py-12 space-y-12">
          {/* Frequently Bought Together */}
          {frequentlyBought.length > 0 && (
            <ProductRecommendations
              title="Frequently Bought Together"
              products={frequentlyBought}
              loading={loadingRecommendations}
              className="border-t pt-8"
            />
          )}

          {/* Similar Products */}
          {similarProducts.length > 0 && (
            <ProductRecommendations
              title="Similar Products"
              products={similarProducts}
              loading={loadingRecommendations}
              className="border-t pt-8"
            />
          )}

          {/* Show loading state if still loading and no products yet */}
          {loadingRecommendations && similarProducts.length === 0 && frequentlyBought.length === 0 && (
            <ProductRecommendations
              title="Recommended for You"
              products={[]}
              loading={true}
              className="border-t pt-8"
            />
          )}
        </div>
      </div>
    </HelmetProvider>
  );
};

export default ProductDetailSEO;