import React, { useState, useEffect } from 'react';
import { getApiUrl } from '../../config/app.config';
import {
  X, ShoppingCart, Package, Info, Leaf, Star,
  Heart, Share2, TrendingUp, Award, Clock,
  AlertCircle, CheckCircle, Sparkles, Droplets,
  Wind, Brain, Smile, Battery, Minus, Plus,
  FlaskConical, Activity, Hash, Calendar,
  MapPin, Shield, Truck, Scale, Box, Gauge,
  Thermometer, Zap, Factory, Mountain, Flower,
  FileText, DollarSign, BarChart, Warehouse,
  Building2, Tag, Layers, TestTube, Pill
} from 'lucide-react';
import { useStoreContext } from '../../contexts/StoreContext';
import { formatCurrency } from '../../utils/currency';

interface ProductDetailsModalProps {
  isOpen: boolean;
  onClose: () => void;
  product: any;
  onAddToCart: (quantity: number) => void;
}

interface ProductDetails {
  basic_info?: any;
  categorization?: any;
  cannabinoids?: any;
  inventory?: any;
  pricing?: any;
  physical_specs?: any;
  production?: any;
  description?: any;
  hardware?: any;
  ratings?: any;
  logistics?: any;
  metadata?: any;
  raw_data?: any;
}

interface ReviewData {
  average_rating: number;
  total_reviews: number;
  rating_distribution: Record<string, number>;
  recommended_percentage: number;
}

interface Review {
  id: string;
  rating: number;
  title: string;
  review_text: string;
  is_recommended: boolean;
  user_name: string;
  created_at: string;
  helpful_count: number;
  is_verified_purchase: boolean;
}

export default function ProductDetailsModal({
  isOpen,
  onClose,
  product,
  onAddToCart
}: ProductDetailsModalProps) {
  const { currentStore } = useStoreContext();
  const [activeTab, setActiveTab] = useState('overview');
  const [quantity, setQuantity] = useState(1);
  const [selectedImage, setSelectedImage] = useState(0);
  const [isFavorite, setIsFavorite] = useState(false);
  const [loading, setLoading] = useState(false);
  const [productDetails, setProductDetails] = useState<ProductDetails | null>(null);
  const [reviewData, setReviewData] = useState<ReviewData | null>(null);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [reviewsPage, setReviewsPage] = useState(1);

  // Fetch comprehensive product details (ALL 97 fields)
  useEffect(() => {
    const fetchProductDetails = async () => {
      if (!product?.ocs_variant_number && !product?.sku && !product?.id) return;

      setLoading(true);
      try {
        const productId = product.ocs_variant_number || product.sku || product.id;
        const storeId = currentStore?.id || product.store_id;

        // Fetch comprehensive product details with all 97 fields
        const detailsResponse = await fetch(
          getApiUrl(`/api/products/details/${encodeURIComponent(productId)}${storeId ? `?store_id=${storeId}` : ''}`)
        );

        if (detailsResponse.ok) {
          const details = await detailsResponse.json();
          setProductDetails(details);
          console.log('Fetched product details with fields:', Object.keys(details.raw_data || {}).length);
        }
      } catch (error) {
        console.error('Error fetching product details:', error);
      } finally {
        setLoading(false);
      }
    };

    if (isOpen && product) {
      fetchProductDetails();
    }
  }, [isOpen, product, currentStore]);

  // Fetch reviews and ratings
  useEffect(() => {
    const fetchReviews = async () => {
      if (!product?.sku && !product?.ocs_variant_number) return;

      try {
        const sku = product.sku || product.ocs_variant_number;

        // Fetch ratings summary
        const ratingsResponse = await fetch(
          getApiUrl(`/api/v1/reviews/products/${sku}/ratings`)
        );

        if (ratingsResponse.ok) {
          const ratings = await ratingsResponse.json();
          setReviewData(ratings);
        }

        // Fetch reviews list
        const reviewsResponse = await fetch(
          getApiUrl(`/api/v1/reviews/products/${sku}/reviews?page=${reviewsPage}&limit=10`)
        );

        if (reviewsResponse.ok) {
          const reviewsList = await reviewsResponse.json();
          setReviews(reviewsList);
        }
      } catch (error) {
        console.error('Error fetching reviews:', error);
      }
    };

    if (isOpen && product) {
      fetchReviews();
    }
  }, [isOpen, product, reviewsPage]);

  if (!isOpen || !product) return null;

  // Reorganized tabs to display ALL 97 fields
  const tabs = [
    { id: 'overview', label: 'Overview', icon: Info },
    { id: 'cannabinoids', label: 'Cannabinoids', icon: FlaskConical },
    { id: 'production', label: 'Production', icon: Factory },
    { id: 'physical', label: 'Physical & Packaging', icon: Package },
    { id: 'inventory', label: 'Inventory & Pricing', icon: DollarSign },
    { id: 'description', label: 'Description', icon: FileText },
    { id: 'hardware', label: 'Hardware', icon: Battery },
    { id: 'reviews', label: 'Reviews', icon: Star },
    { id: 'logistics', label: 'Logistics', icon: Truck },
    { id: 'technical', label: 'Technical Data', icon: BarChart }
  ];

  // Get plant type color
  const getPlantTypeColor = (type: string) => {
    const lowerType = type?.toLowerCase() || '';
    if (lowerType.includes('sativa')) return 'bg-orange-500';
    if (lowerType.includes('indica')) return 'bg-purple-500';
    if (lowerType.includes('hybrid')) return 'bg-green-500';
    if (lowerType.includes('cbd')) return 'bg-blue-500';
    return 'bg-gray-500';
  };

  // Extract ALL data from API response
  const details = productDetails || {};
  const basicInfo = details.basic_info || {};
  const categorization = details.categorization || {};
  const cannabinoids = details.cannabinoids || {};
  const inventory = details.inventory || {};
  const pricing = details.pricing || {};
  const physicalSpecs = details.physical_specs || {};
  const production = details.production || {};
  const description = details.description || {};
  const hardware = details.hardware || {};
  const ratings = details.ratings || {};
  const logistics = details.logistics || {};
  const metadata = details.metadata || {};
  const rawData = details.raw_data || {};

  // Product images
  const productImages = [
    metadata.image_url || product.primary_image || product.image_url || '/placeholder-product.jpg'
  ];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-7xl w-full max-h-[95vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="bg-white border-b px-6 py-4 flex justify-between items-center">
          <div>
            <h2 className="text-2xl font-bold text-gray-800">
              {basicInfo.product_name || product.name || product.product_name}
            </h2>
            <p className="text-sm text-gray-600">
              {basicInfo.brand || product.brand} • {basicInfo.supplier_name}
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto">
          <div className="grid grid-cols-2 gap-6 p-6">
            {/* Left Column - Image and Key Info */}
            <div>
              {/* Main Image */}
              <div className="relative mb-4">
                <img
                  src={productImages[selectedImage]}
                  alt={basicInfo.product_name}
                  className="w-full h-96 object-cover rounded-lg"
                  onError={(e) => {
                    (e.target as HTMLImageElement).src = '/placeholder-product.jpg';
                  }}
                />

                {/* Product Badges */}
                <div className="absolute top-4 left-4 flex flex-wrap gap-2 max-w-[70%]">
                  {product.is_featured && (
                    <span className="px-3 py-1 bg-yellow-500 text-white rounded-full text-sm flex items-center gap-1">
                      <Award className="w-4 h-4" />
                      Featured
                    </span>
                  )}
                  {product.is_new && (
                    <span className="px-3 py-1 bg-blue-500 text-white rounded-full text-sm flex items-center gap-1">
                      <Sparkles className="w-4 h-4" />
                      New
                    </span>
                  )}
                  {product.is_sale && (
                    <span className="px-3 py-1 bg-red-500 text-white rounded-full text-sm flex items-center gap-1">
                      <TrendingUp className="w-4 h-4" />
                      Sale
                    </span>
                  )}
                  {production.ontario_grown === 'Yes' && (
                    <span className="px-3 py-1 bg-green-600 text-white rounded-full text-sm flex items-center gap-1">
                      <MapPin className="w-4 h-4" />
                      Ontario Grown
                    </span>
                  )}
                  {production.craft === 'YES' && (
                    <span className="px-3 py-1 bg-purple-600 text-white rounded-full text-sm flex items-center gap-1">
                      <Award className="w-4 h-4" />
                      Craft Cannabis
                    </span>
                  )}
                </div>

                {/* Favorite Button */}
                <button
                  onClick={() => setIsFavorite(!isFavorite)}
                  className="absolute top-4 right-4 p-2 bg-white rounded-full shadow-md hover:scale-110 transition-transform"
                >
                  <Heart className={`w-5 h-5 ${isFavorite ? 'fill-red-500 text-red-500' : 'text-gray-600'}`} />
                </button>
              </div>

              {/* Key Product Identifiers */}
              <div className="bg-gray-50 rounded-lg p-4 space-y-3">
                <h3 className="font-semibold mb-2 text-gray-700">Product Identifiers</h3>

                {basicInfo.ocs_variant_number && (
                  <div className="flex items-center gap-2 text-sm">
                    <Hash className="w-4 h-4 text-gray-500" />
                    <span className="text-gray-600">OCS Variant:</span>
                    <span className="font-mono font-medium">{basicInfo.ocs_variant_number}</span>
                  </div>
                )}

                {basicInfo.ocs_item_number && (
                  <div className="flex items-center gap-2 text-sm">
                    <Hash className="w-4 h-4 text-gray-500" />
                    <span className="text-gray-600">OCS Item:</span>
                    <span className="font-mono font-medium">{basicInfo.ocs_item_number}</span>
                  </div>
                )}

                {basicInfo.gtin && (
                  <div className="flex items-center gap-2 text-sm">
                    <Tag className="w-4 h-4 text-gray-500" />
                    <span className="text-gray-600">GTIN/Barcode:</span>
                    <span className="font-mono font-medium">{basicInfo.gtin}</span>
                  </div>
                )}

                {basicInfo.sku && (
                  <div className="flex items-center gap-2 text-sm">
                    <Tag className="w-4 h-4 text-gray-500" />
                    <span className="text-gray-600">SKU:</span>
                    <span className="font-mono font-medium">{basicInfo.sku}</span>
                  </div>
                )}

                {basicInfo.slug && (
                  <div className="flex items-center gap-2 text-sm">
                    <FileText className="w-4 h-4 text-gray-500" />
                    <span className="text-gray-600">Slug:</span>
                    <span className="font-mono text-xs break-all">{basicInfo.slug}</span>
                  </div>
                )}
              </div>

              {/* Category Info */}
              <div className="mt-4 bg-blue-50 rounded-lg p-4 space-y-2">
                <h3 className="font-semibold mb-2 text-gray-700">Categorization</h3>

                <div className="grid grid-cols-2 gap-2 text-sm">
                  {categorization.category && (
                    <div>
                      <span className="text-gray-600">Category:</span>
                      <span className="ml-2 font-medium">{categorization.category}</span>
                    </div>
                  )}

                  {categorization.sub_category && (
                    <div>
                      <span className="text-gray-600">Subcategory:</span>
                      <span className="ml-2 font-medium">{categorization.sub_category}</span>
                    </div>
                  )}

                  {categorization.sub_sub_category && (
                    <div>
                      <span className="text-gray-600">Sub-subcategory:</span>
                      <span className="ml-2 font-medium">{categorization.sub_sub_category}</span>
                    </div>
                  )}

                  {categorization.plant_type && (
                    <div className="flex items-center gap-2">
                      <Leaf className="w-4 h-4 text-gray-500" />
                      <span className={`px-2 py-1 text-white text-xs rounded-full ${
                        getPlantTypeColor(categorization.plant_type)
                      }`}>
                        {categorization.plant_type}
                      </span>
                    </div>
                  )}

                  {categorization.strain_type && (
                    <div>
                      <span className="text-gray-600">Strain:</span>
                      <span className="ml-2 font-medium">{categorization.strain_type}</span>
                    </div>
                  )}

                  {categorization.street_name && (
                    <div>
                      <span className="text-gray-600">Street Name:</span>
                      <span className="ml-2 font-medium italic">{categorization.street_name}</span>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Right Column - Purchase Section and Tabs */}
            <div className="flex flex-col">
              {/* Price and Purchase Section */}
              <div className="bg-primary-50 rounded-lg p-4 mb-4">
                <div className="flex items-baseline gap-2 mb-4">
                  {product.is_sale && product.sale_price ? (
                    <>
                      <span className="text-3xl font-bold text-red-600">
                        {formatCurrency(product.sale_price)}
                      </span>
                      <span className="text-lg text-gray-500 line-through">
                        {formatCurrency(pricing.retail_price || pricing.unit_price || product.price || 0)}
                      </span>
                    </>
                  ) : (
                    <span className="text-3xl font-bold text-primary-600">
                      {formatCurrency(pricing.retail_price || pricing.unit_price || pricing.effective_price || product.price || 0)}
                    </span>
                  )}
                  {pricing.unit_cost && (
                    <span className="text-sm text-gray-500">(Cost: {formatCurrency(pricing.unit_cost)})</span>
                  )}
                </div>

                {/* THC/CBD Content Display */}
                <div className="space-y-2 mb-4">
                  {/* THC Content */}
                  {(cannabinoids.thc_content_per_unit || cannabinoids.maximum_thc_content_percent > 0) && (
                    <div className="bg-green-100 rounded-lg p-2">
                      <div className="flex justify-between items-center">
                        <span className="text-sm font-semibold text-green-800">THC Content</span>
                        <span className="text-sm text-green-700">
                          {cannabinoids.thc_content_per_unit ?
                            `${cannabinoids.thc_content_per_unit} mg/unit` :
                            `${cannabinoids.minimum_thc_content_percent || 0}-${cannabinoids.maximum_thc_content_percent || 0}%`
                          }
                        </span>
                      </div>
                      {cannabinoids.thc_content_per_volume > 0 && (
                        <span className="text-xs text-green-600">
                          Volume: {cannabinoids.thc_content_per_volume} mg/ml
                        </span>
                      )}
                    </div>
                  )}

                  {/* CBD Content */}
                  {(cannabinoids.cbd_content_per_unit || cannabinoids.maximum_cbd_content_percent > 0) && (
                    <div className="bg-blue-100 rounded-lg p-2">
                      <div className="flex justify-between items-center">
                        <span className="text-sm font-semibold text-blue-800">CBD Content</span>
                        <span className="text-sm text-blue-700">
                          {cannabinoids.cbd_content_per_unit ?
                            `${cannabinoids.cbd_content_per_unit} mg/unit` :
                            `${cannabinoids.minimum_cbd_content_percent || 0}-${cannabinoids.maximum_cbd_content_percent || 0}%`
                          }
                        </span>
                      </div>
                      {cannabinoids.cbd_content_per_volume > 0 && (
                        <span className="text-xs text-blue-600">
                          Volume: {cannabinoids.cbd_content_per_volume} mg/ml
                        </span>
                      )}
                    </div>
                  )}
                </div>

                {/* Size and Pack Info */}
                <div className="grid grid-cols-3 gap-2 mb-4 text-sm">
                  {physicalSpecs.size && (
                    <div className="bg-white rounded p-2">
                      <Scale className="w-4 h-4 text-gray-500 mb-1" />
                      <span className="font-medium">{physicalSpecs.size}</span>
                    </div>
                  )}
                  {physicalSpecs.pack_size && (
                    <div className="bg-white rounded p-2">
                      <Box className="w-4 h-4 text-gray-500 mb-1" />
                      <span className="font-medium">Pack: {physicalSpecs.pack_size}</span>
                    </div>
                  )}
                  {physicalSpecs.unit_of_measure && (
                    <div className="bg-white rounded p-2">
                      <Gauge className="w-4 h-4 text-gray-500 mb-1" />
                      <span className="font-medium">{physicalSpecs.unit_of_measure}</span>
                    </div>
                  )}
                </div>

                {/* Quantity Selector */}
                <div className="flex items-center gap-4 mb-4">
                  <span className="text-sm font-medium">Quantity:</span>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setQuantity(Math.max(1, quantity - 1))}
                      className="p-1 bg-white rounded-lg hover:bg-gray-100"
                    >
                      <Minus className="w-4 h-4" />
                    </button>
                    <span className="w-12 text-center font-semibold">{quantity}</span>
                    <button
                      onClick={() => setQuantity(Math.min(
                        inventory.quantity_available || 99,
                        quantity + 1
                      ))}
                      className="p-1 bg-white rounded-lg hover:bg-gray-100"
                    >
                      <Plus className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                {/* Stock Status */}
                <div className="flex items-center gap-2 mb-4">
                  {inventory.in_stock ? (
                    <>
                      <CheckCircle className="w-4 h-4 text-green-600" />
                      <span className="text-sm text-green-600">
                        {inventory.stock_status === 'in_stock' ? 'In Stock' :
                         inventory.stock_status === 'low_stock' ? `Low Stock (${inventory.quantity_available} left)` :
                         'Limited Availability'}
                      </span>
                    </>
                  ) : (
                    <>
                      <AlertCircle className="w-4 h-4 text-red-600" />
                      <span className="text-sm text-red-600">Out of Stock</span>
                    </>
                  )}
                  {logistics.catalog_stock_status && (
                    <span className="text-xs text-gray-500 ml-2">
                      (Catalog: {logistics.catalog_stock_status})
                    </span>
                  )}
                </div>

                {/* Add to Cart Button */}
                <button
                  onClick={() => onAddToCart(quantity)}
                  disabled={inventory.quantity_available === 0}
                  className="w-full py-3 bg-primary-600 text-white rounded-lg font-semibold hover:bg-primary-700 transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  <ShoppingCart className="w-5 h-5" />
                  {inventory.quantity_available === 0 ? 'Out of Stock' :
                   `Add to Cart - ${formatCurrency((pricing.effective_price || pricing.unit_price || product.price || 0) * quantity)}`}
                </button>
              </div>

              {/* Tabs */}
              <div className="border-b mb-4">
                <div className="flex flex-wrap gap-1">
                  {tabs.map(tab => (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className={`px-3 py-2 flex items-center gap-1 text-sm border-b-2 transition-colors ${
                        activeTab === tab.id
                          ? 'border-primary-500 text-primary-600'
                          : 'border-transparent text-gray-500 hover:text-gray-700'
                      }`}
                    >
                      <tab.icon className="w-4 h-4" />
                      {tab.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Tab Content */}
              <div className="flex-1 overflow-y-auto">
                {loading ? (
                  <div className="flex items-center justify-center py-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
                  </div>
                ) : (
                  <>
                    {/* Overview Tab */}
                    {activeTab === 'overview' && (
                      <div className="space-y-4">
                        {/* Short Description */}
                        {description.product_short_description && (
                          <div>
                            <h3 className="font-semibold mb-2">Quick Overview</h3>
                            <p className="text-gray-600">{description.product_short_description}</p>
                          </div>
                        )}

                        {/* Long Description */}
                        {description.product_long_description && (
                          <div>
                            <h3 className="font-semibold mb-2">Detailed Description</h3>
                            <p className="text-gray-600">{description.product_long_description}</p>
                          </div>
                        )}

                        {/* Key Features Grid */}
                        <div className="grid grid-cols-2 gap-4">
                          {physicalSpecs.dried_flower_cannabis_equivalency && (
                            <div className="bg-yellow-50 rounded-lg p-3">
                              <Flower className="w-5 h-5 text-yellow-600 mb-1" />
                              <span className="text-sm text-gray-600">Flower Equivalent</span>
                              <p className="font-semibold">{physicalSpecs.dried_flower_cannabis_equivalency}g</p>
                            </div>
                          )}

                          {production.extraction_process && (
                            <div className="bg-purple-50 rounded-lg p-3">
                              <TestTube className="w-5 h-5 text-purple-600 mb-1" />
                              <span className="text-sm text-gray-600">Extraction</span>
                              <p className="font-semibold">{production.extraction_process}</p>
                            </div>
                          )}
                        </div>

                        {/* Rating Summary */}
                        {reviewData && (
                          <div className="bg-gray-50 rounded-lg p-4">
                            <div className="flex items-center gap-4">
                              <div className="text-center">
                                <div className="text-3xl font-bold">{reviewData.average_rating.toFixed(1)}</div>
                                <div className="flex mt-1">
                                  {[...Array(5)].map((_, i) => (
                                    <Star
                                      key={i}
                                      className={`w-4 h-4 ${
                                        i < Math.floor(reviewData.average_rating)
                                          ? 'text-yellow-500 fill-current'
                                          : 'text-gray-300'
                                      }`}
                                    />
                                  ))}
                                </div>
                                <div className="text-sm text-gray-600 mt-1">
                                  {reviewData.total_reviews} reviews
                                </div>
                              </div>
                              {reviewData.recommended_percentage > 0 && (
                                <div className="text-center border-l pl-4">
                                  <div className="text-2xl font-bold text-green-600">
                                    {reviewData.recommended_percentage}%
                                  </div>
                                  <div className="text-sm text-gray-600">Recommended</div>
                                </div>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Cannabinoids Tab - Display ALL cannabinoid fields */}
                    {activeTab === 'cannabinoids' && (
                      <div className="space-y-4">
                        <h3 className="font-semibold mb-3">Complete Cannabinoid Profile</h3>

                        {/* THC Details */}
                        <div className="bg-green-50 rounded-lg p-4">
                          <h4 className="font-medium text-green-800 mb-2 flex items-center gap-2">
                            <FlaskConical className="w-4 h-4" />
                            THC Content
                          </h4>
                          <div className="grid grid-cols-2 gap-2 text-sm">
                            {cannabinoids.thc_content_per_unit && (
                              <div>
                                <span className="text-gray-600">Per Unit:</span>
                                <span className="ml-2 font-medium">{cannabinoids.thc_content_per_unit} mg</span>
                              </div>
                            )}
                            {cannabinoids.thc_content_per_volume > 0 && (
                              <div>
                                <span className="text-gray-600">Per Volume:</span>
                                <span className="ml-2 font-medium">{cannabinoids.thc_content_per_volume} mg/ml</span>
                              </div>
                            )}
                            {(cannabinoids.minimum_thc_content_percent > 0 || cannabinoids.maximum_thc_content_percent > 0) && (
                              <div className="col-span-2">
                                <span className="text-gray-600">Range:</span>
                                <span className="ml-2 font-medium">
                                  {cannabinoids.minimum_thc_content_percent}% - {cannabinoids.maximum_thc_content_percent}%
                                </span>
                              </div>
                            )}
                          </div>
                        </div>

                        {/* CBD Details */}
                        <div className="bg-blue-50 rounded-lg p-4">
                          <h4 className="font-medium text-blue-800 mb-2 flex items-center gap-2">
                            <FlaskConical className="w-4 h-4" />
                            CBD Content
                          </h4>
                          <div className="grid grid-cols-2 gap-2 text-sm">
                            {cannabinoids.cbd_content_per_unit && (
                              <div>
                                <span className="text-gray-600">Per Unit:</span>
                                <span className="ml-2 font-medium">{cannabinoids.cbd_content_per_unit} mg</span>
                              </div>
                            )}
                            {cannabinoids.cbd_content_per_volume > 0 && (
                              <div>
                                <span className="text-gray-600">Per Volume:</span>
                                <span className="ml-2 font-medium">{cannabinoids.cbd_content_per_volume} mg/ml</span>
                              </div>
                            )}
                            {(cannabinoids.minimum_cbd_content_percent > 0 || cannabinoids.maximum_cbd_content_percent > 0) && (
                              <div className="col-span-2">
                                <span className="text-gray-600">Range:</span>
                                <span className="ml-2 font-medium">
                                  {cannabinoids.minimum_cbd_content_percent}% - {cannabinoids.maximum_cbd_content_percent}%
                                </span>
                              </div>
                            )}
                          </div>
                        </div>

                        {/* Terpenes */}
                        {cannabinoids.terpenes && (
                          <div className="bg-purple-50 rounded-lg p-4">
                            <h4 className="font-medium text-purple-800 mb-2 flex items-center gap-2">
                              <Droplets className="w-4 h-4" />
                              Terpene Profile
                            </h4>
                            <div className="flex flex-wrap gap-2">
                              {cannabinoids.terpenes.split(',').map((terpene: string, idx: number) => (
                                <span key={idx} className="px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-sm">
                                  {terpene.trim()}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Production Tab - ALL production fields */}
                    {activeTab === 'production' && (
                      <div className="space-y-4">
                        <h3 className="font-semibold mb-3">Production Details</h3>

                        <div className="grid grid-cols-2 gap-4 text-sm">
                          {production.grow_method && (
                            <div className="bg-green-50 rounded-lg p-3">
                              <Factory className="w-4 h-4 text-green-600 mb-1" />
                              <span className="text-gray-600">Grow Method</span>
                              <p className="font-medium">{production.grow_method}</p>
                            </div>
                          )}

                          {production.growing_method && production.growing_method !== production.grow_method && (
                            <div className="bg-green-50 rounded-lg p-3">
                              <Factory className="w-4 h-4 text-green-600 mb-1" />
                              <span className="text-gray-600">Growing Method</span>
                              <p className="font-medium">{production.growing_method}</p>
                            </div>
                          )}

                          {production.grow_region && (
                            <div className="bg-blue-50 rounded-lg p-3">
                              <Mountain className="w-4 h-4 text-blue-600 mb-1" />
                              <span className="text-gray-600">Grow Region</span>
                              <p className="font-medium">{production.grow_region}</p>
                            </div>
                          )}

                          {production.grow_medium && (
                            <div className="bg-yellow-50 rounded-lg p-3">
                              <Layers className="w-4 h-4 text-yellow-600 mb-1" />
                              <span className="text-gray-600">Grow Medium</span>
                              <p className="font-medium">{production.grow_medium}</p>
                            </div>
                          )}

                          {production.drying_method && (
                            <div className="bg-orange-50 rounded-lg p-3">
                              <Wind className="w-4 h-4 text-orange-600 mb-1" />
                              <span className="text-gray-600">Drying Method</span>
                              <p className="font-medium">{production.drying_method}</p>
                            </div>
                          )}

                          {production.trimming_method && (
                            <div className="bg-purple-50 rounded-lg p-3">
                              <Wrench className="w-4 h-4" />
                              <span className="text-gray-600">Trimming Method</span>
                              <p className="font-medium">{production.trimming_method}</p>
                            </div>
                          )}

                          {production.extraction_process && (
                            <div className="bg-indigo-50 rounded-lg p-3">
                              <TestTube className="w-4 h-4 text-indigo-600 mb-1" />
                              <span className="text-gray-600">Extraction Process</span>
                              <p className="font-medium">{production.extraction_process}</p>
                            </div>
                          )}
                        </div>

                        {/* Special Designations */}
                        <div className="flex gap-4">
                          {production.ontario_grown && (
                            <div className={`px-4 py-2 rounded-lg ${
                              production.ontario_grown === 'Yes' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'
                            }`}>
                              <MapPin className="w-4 h-4 inline mr-1" />
                              Ontario Grown: {production.ontario_grown}
                            </div>
                          )}

                          {production.craft && (
                            <div className={`px-4 py-2 rounded-lg ${
                              production.craft === 'YES' ? 'bg-purple-100 text-purple-700' : 'bg-gray-100 text-gray-600'
                            }`}>
                              <Award className="w-4 h-4 inline mr-1" />
                              Craft Cannabis: {production.craft}
                            </div>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Physical & Packaging Tab - ALL physical spec fields */}
                    {activeTab === 'physical' && (
                      <div className="space-y-4">
                        <h3 className="font-semibold mb-3">Physical Specifications & Packaging</h3>

                        {/* Dimensions */}
                        <div>
                          <h4 className="font-medium mb-2">Package Dimensions</h4>
                          <div className="grid grid-cols-3 gap-2 text-sm">
                            {physicalSpecs.physical_dimension_width && (
                              <div className="bg-gray-50 rounded p-2">
                                <span className="text-gray-600">Width:</span>
                                <span className="ml-1 font-medium">{physicalSpecs.physical_dimension_width}cm</span>
                              </div>
                            )}
                            {physicalSpecs.physical_dimension_height && (
                              <div className="bg-gray-50 rounded p-2">
                                <span className="text-gray-600">Height:</span>
                                <span className="ml-1 font-medium">{physicalSpecs.physical_dimension_height}cm</span>
                              </div>
                            )}
                            {physicalSpecs.physical_dimension_depth && (
                              <div className="bg-gray-50 rounded p-2">
                                <span className="text-gray-600">Depth:</span>
                                <span className="ml-1 font-medium">{physicalSpecs.physical_dimension_depth}cm</span>
                              </div>
                            )}
                            {physicalSpecs.physical_dimension_volume && (
                              <div className="bg-gray-50 rounded p-2">
                                <span className="text-gray-600">Volume:</span>
                                <span className="ml-1 font-medium">{physicalSpecs.physical_dimension_volume}ml</span>
                              </div>
                            )}
                            {physicalSpecs.physical_dimension_weight && (
                              <div className="bg-gray-50 rounded p-2">
                                <span className="text-gray-600">Weight:</span>
                                <span className="ml-1 font-medium">{physicalSpecs.physical_dimension_weight}kg</span>
                              </div>
                            )}
                            {physicalSpecs.net_weight && (
                              <div className="bg-gray-50 rounded p-2">
                                <span className="text-gray-600">Net Weight:</span>
                                <span className="ml-1 font-medium">{physicalSpecs.net_weight}g</span>
                              </div>
                            )}
                          </div>
                        </div>

                        {/* Pack Information */}
                        <div>
                          <h4 className="font-medium mb-2">Packaging Information</h4>
                          <div className="grid grid-cols-2 gap-2 text-sm">
                            {physicalSpecs.pack_size && (
                              <div>
                                <span className="text-gray-600">Pack Size:</span>
                                <span className="ml-2 font-medium">{physicalSpecs.pack_size}</span>
                              </div>
                            )}
                            {physicalSpecs.number_of_items_in_retail_pack > 0 && (
                              <div>
                                <span className="text-gray-600">Items per Pack:</span>
                                <span className="ml-2 font-medium">{physicalSpecs.number_of_items_in_retail_pack}</span>
                              </div>
                            )}
                            {physicalSpecs.eaches_per_inner_pack && (
                              <div>
                                <span className="text-gray-600">Per Inner Pack:</span>
                                <span className="ml-2 font-medium">{physicalSpecs.eaches_per_inner_pack}</span>
                              </div>
                            )}
                            {physicalSpecs.eaches_per_master_case && (
                              <div>
                                <span className="text-gray-600">Per Master Case:</span>
                                <span className="ml-2 font-medium">{physicalSpecs.eaches_per_master_case}</span>
                              </div>
                            )}
                          </div>
                        </div>

                        {/* Cannabis Equivalency */}
                        {physicalSpecs.dried_flower_cannabis_equivalency && (
                          <div className="bg-yellow-50 rounded-lg p-3">
                            <h4 className="font-medium mb-1 flex items-center gap-2">
                              <Flower className="w-4 h-4 text-yellow-600" />
                              Dried Flower Equivalency
                            </h4>
                            <p className="text-lg font-semibold">{physicalSpecs.dried_flower_cannabis_equivalency}g</p>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Inventory & Pricing Tab */}
                    {activeTab === 'inventory' && (
                      <div className="space-y-4">
                        <h3 className="font-semibold mb-3">Inventory & Pricing Information</h3>

                        {/* Pricing */}
                        <div className="bg-green-50 rounded-lg p-4">
                          <h4 className="font-medium mb-2">Pricing</h4>
                          <div className="grid grid-cols-2 gap-2 text-sm">
                            {pricing.unit_price && (
                              <div>
                                <span className="text-gray-600">Unit Price:</span>
                                <span className="ml-2 font-medium">{formatCurrency(pricing.unit_price)}</span>
                              </div>
                            )}
                            {pricing.unit_cost && (
                              <div>
                                <span className="text-gray-600">Unit Cost:</span>
                                <span className="ml-2 font-medium">{formatCurrency(pricing.unit_cost)}</span>
                              </div>
                            )}
                            {pricing.retail_price && (
                              <div>
                                <span className="text-gray-600">Retail Price:</span>
                                <span className="ml-2 font-medium">{formatCurrency(pricing.retail_price)}</span>
                              </div>
                            )}
                            {pricing.override_price && (
                              <div>
                                <span className="text-gray-600">Override Price:</span>
                                <span className="ml-2 font-medium">{formatCurrency(pricing.override_price)}</span>
                              </div>
                            )}
                            {pricing.effective_price && (
                              <div className="col-span-2">
                                <span className="text-gray-600">Effective Price:</span>
                                <span className="ml-2 font-bold text-lg">{formatCurrency(pricing.effective_price)}</span>
                              </div>
                            )}
                          </div>
                        </div>

                        {/* Stock Levels */}
                        <div className="bg-blue-50 rounded-lg p-4">
                          <h4 className="font-medium mb-2">Stock Levels</h4>
                          <div className="grid grid-cols-2 gap-2 text-sm">
                            {inventory.quantity_on_hand !== null && (
                              <div>
                                <span className="text-gray-600">On Hand:</span>
                                <span className="ml-2 font-medium">{inventory.quantity_on_hand}</span>
                              </div>
                            )}
                            {inventory.quantity_available !== null && (
                              <div>
                                <span className="text-gray-600">Available:</span>
                                <span className="ml-2 font-medium">{inventory.quantity_available}</span>
                              </div>
                            )}
                            {inventory.quantity_reserved !== null && (
                              <div>
                                <span className="text-gray-600">Reserved:</span>
                                <span className="ml-2 font-medium">{inventory.quantity_reserved}</span>
                              </div>
                            )}
                            {inventory.reorder_point !== null && (
                              <div>
                                <span className="text-gray-600">Reorder Point:</span>
                                <span className="ml-2 font-medium">{inventory.reorder_point}</span>
                              </div>
                            )}
                            {inventory.reorder_quantity !== null && (
                              <div>
                                <span className="text-gray-600">Reorder Qty:</span>
                                <span className="ml-2 font-medium">{inventory.reorder_quantity}</span>
                              </div>
                            )}
                            {inventory.min_stock_level !== null && (
                              <div>
                                <span className="text-gray-600">Min Stock:</span>
                                <span className="ml-2 font-medium">{inventory.min_stock_level}</span>
                              </div>
                            )}
                            {inventory.max_stock_level !== null && (
                              <div>
                                <span className="text-gray-600">Max Stock:</span>
                                <span className="ml-2 font-medium">{inventory.max_stock_level}</span>
                              </div>
                            )}
                          </div>
                        </div>

                        {/* Inventory Status */}
                        <div className="flex gap-2">
                          <div className={`px-3 py-2 rounded-lg ${
                            inventory.in_stock ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                          }`}>
                            Stock Status: {inventory.stock_status || 'Unknown'}
                          </div>
                          {inventory.is_available !== null && (
                            <div className={`px-3 py-2 rounded-lg ${
                              inventory.is_available ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'
                            }`}>
                              Available: {inventory.is_available ? 'Yes' : 'No'}
                            </div>
                          )}
                        </div>

                        {inventory.last_restock_date && (
                          <div className="text-sm text-gray-600">
                            Last Restock: {new Date(inventory.last_restock_date).toLocaleDateString()}
                          </div>
                        )}
                      </div>
                    )}

                    {/* Description Tab - ALL description fields */}
                    {activeTab === 'description' && (
                      <div className="space-y-4">
                        {description.product_short_description && (
                          <div>
                            <h3 className="font-semibold mb-2">Short Description</h3>
                            <p className="text-gray-600">{description.product_short_description}</p>
                          </div>
                        )}

                        {description.product_long_description && (
                          <div>
                            <h3 className="font-semibold mb-2">Full Description</h3>
                            <p className="text-gray-600">{description.product_long_description}</p>
                          </div>
                        )}

                        {description.ingredients && (
                          <div>
                            <h3 className="font-semibold mb-2">Ingredients</h3>
                            <p className="text-gray-600">{description.ingredients}</p>
                          </div>
                        )}

                        {description.carrier_oil && description.carrier_oil !== '-' && (
                          <div>
                            <h3 className="font-semibold mb-2">Carrier Oil</h3>
                            <p className="text-gray-600">{description.carrier_oil}</p>
                          </div>
                        )}

                        {description.food_allergens && (
                          <div className="bg-red-50 rounded-lg p-3">
                            <h3 className="font-semibold mb-2 text-red-700">Allergen Information</h3>
                            <p className="text-red-600">{description.food_allergens}</p>
                          </div>
                        )}

                        {description.storage_criteria && (
                          <div className="bg-blue-50 rounded-lg p-3">
                            <h3 className="font-semibold mb-2 text-blue-700">Storage Instructions</h3>
                            <p className="text-blue-600">{description.storage_criteria}</p>
                          </div>
                        )}

                        {description.colour && (
                          <div>
                            <h3 className="font-semibold mb-2">Color</h3>
                            <p className="text-gray-600">{description.colour}</p>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Hardware Tab - ALL hardware fields */}
                    {activeTab === 'hardware' && (
                      <div className="space-y-4">
                        <h3 className="font-semibold mb-3">Hardware Specifications</h3>

                        {Object.values(hardware).some(val => val) ? (
                          <div className="grid grid-cols-2 gap-4 text-sm">
                            {hardware.heating_element_type && (
                              <div className="bg-orange-50 rounded-lg p-3">
                                <Thermometer className="w-4 h-4 text-orange-600 mb-1" />
                                <span className="text-gray-600">Heating Element</span>
                                <p className="font-medium">{hardware.heating_element_type}</p>
                              </div>
                            )}

                            {hardware.battery_type && (
                              <div className="bg-blue-50 rounded-lg p-3">
                                <Battery className="w-4 h-4 text-blue-600 mb-1" />
                                <span className="text-gray-600">Battery Type</span>
                                <p className="font-medium">{hardware.battery_type}</p>
                              </div>
                            )}

                            {hardware.temperature_control !== null && (
                              <div className="bg-green-50 rounded-lg p-3">
                                <Gauge className="w-4 h-4 text-green-600 mb-1" />
                                <span className="text-gray-600">Temp Control</span>
                                <p className="font-medium">{hardware.temperature_control || 'No'}</p>
                              </div>
                            )}

                            {hardware.temperature_display !== null && (
                              <div className="bg-purple-50 rounded-lg p-3">
                                <Thermometer className="w-4 h-4 text-purple-600 mb-1" />
                                <span className="text-gray-600">Temp Display</span>
                                <p className="font-medium">{hardware.temperature_display || 'No'}</p>
                              </div>
                            )}

                            {hardware.rechargeable_battery !== null && (
                              <div className="bg-yellow-50 rounded-lg p-3">
                                <Zap className="w-4 h-4 text-yellow-600 mb-1" />
                                <span className="text-gray-600">Rechargeable</span>
                                <p className="font-medium">{hardware.rechargeable_battery || 'No'}</p>
                              </div>
                            )}

                            {hardware.removable_battery !== null && (
                              <div className="bg-red-50 rounded-lg p-3">
                                <Battery className="w-4 h-4 text-red-600 mb-1" />
                                <span className="text-gray-600">Removable Battery</span>
                                <p className="font-medium">{hardware.removable_battery || 'No'}</p>
                              </div>
                            )}

                            {hardware.replacement_parts_available !== null && (
                              <div className="bg-indigo-50 rounded-lg p-3">
                                <Wrench className="w-4 h-4" />
                                <span className="text-gray-600">Replacement Parts</span>
                                <p className="font-medium">{hardware.replacement_parts_available || 'No'}</p>
                              </div>
                            )}

                            {hardware.compatibility && (
                              <div className="bg-gray-50 rounded-lg p-3">
                                <Layers className="w-4 h-4 text-gray-600 mb-1" />
                                <span className="text-gray-600">Compatibility</span>
                                <p className="font-medium">{hardware.compatibility}</p>
                              </div>
                            )}
                          </div>
                        ) : (
                          <p className="text-gray-500 text-center py-8">
                            No hardware specifications available for this product.
                          </p>
                        )}
                      </div>
                    )}

                    {/* Reviews Tab */}
                    {activeTab === 'reviews' && (
                      <div className="space-y-4">
                        {/* Rating Distribution */}
                        {reviewData && reviewData.rating_distribution && (
                          <div>
                            <h3 className="font-semibold mb-3">Rating Breakdown</h3>
                            {Object.entries(reviewData.rating_distribution)
                              .sort((a, b) => Number(b[0]) - Number(a[0]))
                              .map(([rating, count]) => (
                                <div key={rating} className="flex items-center gap-3 mb-2">
                                  <span className="text-sm w-4">{rating}</span>
                                  <Star className="w-4 h-4 text-yellow-500 fill-current" />
                                  <div className="flex-1 bg-gray-200 rounded-full h-2">
                                    <div
                                      className="bg-yellow-500 h-2 rounded-full"
                                      style={{
                                        width: `${(Number(count) / reviewData.total_reviews) * 100}%`
                                      }}
                                    />
                                  </div>
                                  <span className="text-sm text-gray-600 w-12 text-right">
                                    {count}
                                  </span>
                                </div>
                              ))}
                          </div>
                        )}

                        {/* Reviews List */}
                        <div>
                          <h3 className="font-semibold mb-3">Customer Reviews</h3>
                          {reviews.length > 0 ? (
                            <div className="space-y-4">
                              {reviews.map((review) => (
                                <div key={review.id} className="border-b pb-4">
                                  <div className="flex items-center gap-2 mb-1">
                                    <div className="flex">
                                      {[...Array(5)].map((_, i) => (
                                        <Star
                                          key={i}
                                          className={`w-4 h-4 ${
                                            i < review.rating
                                              ? 'text-yellow-500 fill-current'
                                              : 'text-gray-300'
                                          }`}
                                        />
                                      ))}
                                    </div>
                                    {review.is_verified_purchase && (
                                      <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded">
                                        Verified Purchase
                                      </span>
                                    )}
                                  </div>
                                  {review.title && (
                                    <h4 className="font-medium mb-1">{review.title}</h4>
                                  )}
                                  <p className="text-sm text-gray-600 mb-2">{review.review_text}</p>
                                  <div className="flex items-center justify-between text-xs text-gray-500">
                                    <span>{review.user_name} - {new Date(review.created_at).toLocaleDateString()}</span>
                                    {review.helpful_count > 0 && (
                                      <span>{review.helpful_count} found this helpful</span>
                                    )}
                                  </div>
                                </div>
                              ))}
                              {reviews.length >= 10 && (
                                <button
                                  onClick={() => setReviewsPage(reviewsPage + 1)}
                                  className="w-full py-2 text-primary-600 hover:text-primary-700 font-medium"
                                >
                                  Load More Reviews
                                </button>
                              )}
                            </div>
                          ) : (
                            <p className="text-gray-500 text-center py-4">
                              No reviews yet. Be the first to review this product!
                            </p>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Logistics Tab - ALL logistics fields */}
                    {activeTab === 'logistics' && (
                      <div className="space-y-4">
                        <h3 className="font-semibold mb-3">Logistics & Fulfillment</h3>

                        <div className="grid grid-cols-2 gap-4">
                          {logistics.fulfilment_method && (
                            <div className="bg-blue-50 rounded-lg p-3">
                              <Truck className="w-4 h-4 text-blue-600 mb-1" />
                              <span className="text-gray-600">Fulfillment Method</span>
                              <p className="font-medium">{logistics.fulfilment_method}</p>
                            </div>
                          )}

                          {logistics.delivery_tier && (
                            <div className="bg-green-50 rounded-lg p-3">
                              <Package className="w-4 h-4 text-green-600 mb-1" />
                              <span className="text-gray-600">Delivery Tier</span>
                              <p className="font-medium">{logistics.delivery_tier}</p>
                            </div>
                          )}

                          {logistics.catalog_stock_status && (
                            <div className="bg-yellow-50 rounded-lg p-3">
                              <Warehouse className="w-4 h-4 text-yellow-600 mb-1" />
                              <span className="text-gray-600">Catalog Stock Status</span>
                              <p className="font-medium">{logistics.catalog_stock_status}</p>
                            </div>
                          )}

                          {logistics.inventory_status && (
                            <div className="bg-purple-50 rounded-lg p-3">
                              <Box className="w-4 h-4 text-purple-600 mb-1" />
                              <span className="text-gray-600">Inventory Status</span>
                              <p className="font-medium">{logistics.inventory_status}</p>
                            </div>
                          )}
                        </div>

                        {inventory.store_id && (
                          <div className="text-sm text-gray-600">
                            <Building2 className="w-4 h-4 inline mr-1" />
                            Store ID: {inventory.store_id}
                          </div>
                        )}
                      </div>
                    )}

                    {/* Technical Data Tab - Metadata and system fields */}
                    {activeTab === 'technical' && (
                      <div className="space-y-4">
                        <h3 className="font-semibold mb-3">Technical Information</h3>

                        {/* System IDs */}
                        <div>
                          <h4 className="font-medium mb-2">System Identifiers</h4>
                          <div className="space-y-1 text-sm font-mono bg-gray-50 rounded p-3">
                            {rawData.product_id && (
                              <div>Product ID: {rawData.product_id}</div>
                            )}
                            {rawData.inventory_id && (
                              <div>Inventory ID: {rawData.inventory_id}</div>
                            )}
                            {inventory.store_id && (
                              <div>Store ID: {inventory.store_id}</div>
                            )}
                          </div>
                        </div>

                        {/* Timestamps */}
                        <div>
                          <h4 className="font-medium mb-2">Timestamps</h4>
                          <div className="space-y-1 text-sm">
                            {metadata.product_created_at && (
                              <div>
                                <span className="text-gray-600">Product Created:</span>
                                <span className="ml-2">{new Date(metadata.product_created_at).toLocaleString()}</span>
                              </div>
                            )}
                            {metadata.product_updated_at && (
                              <div>
                                <span className="text-gray-600">Product Updated:</span>
                                <span className="ml-2">{new Date(metadata.product_updated_at).toLocaleString()}</span>
                              </div>
                            )}
                            {metadata.inventory_created_at && (
                              <div>
                                <span className="text-gray-600">Inventory Created:</span>
                                <span className="ml-2">{new Date(metadata.inventory_created_at).toLocaleString()}</span>
                              </div>
                            )}
                            {metadata.inventory_updated_at && (
                              <div>
                                <span className="text-gray-600">Inventory Updated:</span>
                                <span className="ml-2">{new Date(metadata.inventory_updated_at).toLocaleString()}</span>
                              </div>
                            )}
                          </div>
                        </div>

                        {/* Raw Data Count */}
                        <div className="bg-gray-50 rounded-lg p-3">
                          <h4 className="font-medium mb-2">Data Completeness</h4>
                          <p className="text-sm text-gray-600">
                            Total Fields Available: {Object.keys(rawData).filter(k => rawData[k] !== null).length} / {Object.keys(rawData).length}
                          </p>
                          <div className="mt-2 bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-green-500 h-2 rounded-full"
                              style={{
                                width: `${(Object.keys(rawData).filter(k => rawData[k] !== null).length / Object.keys(rawData).length) * 100}%`
                              }}
                            />
                          </div>
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}