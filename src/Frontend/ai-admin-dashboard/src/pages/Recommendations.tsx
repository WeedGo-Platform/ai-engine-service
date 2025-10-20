import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  TrendingUp, ShoppingBag, Users, Package2,
  Star, RefreshCw, BarChart3, Zap, Target,
  ArrowUpRight, ArrowDownRight
} from 'lucide-react';
import axios from 'axios';
import { useStoreContext } from '../contexts/StoreContext';

const API_BASE_URL = 'http://localhost:5024';

interface RecommendationMetric {
  recommendation_type: string;
  count: number;
  avg_score: number;
  avg_ctr: number;
  avg_conversion: number;
  revenue_impact: number;
}

interface TopPerformer {
  product_id: string;
  recommended_product_id: string;
  recommendation_type: string;
  source_product: string;
  recommended_product: string;
  click_through_rate: number;
  conversion_rate: number;
  revenue_impact: number;
}

export default function Recommendations() {
  const { currentStore } = useStoreContext();
  const [selectedProduct, setSelectedProduct] = useState<string>('');
  const [activeTab, setActiveTab] = useState<'overview' | 'performance' | 'test'>('overview');

  // Fetch trending products
  const { data: trendingProducts } = useQuery({
    queryKey: ['trending-products'],
    queryFn: async () => {
      const response = await axios.get(`${API_BASE_URL}/api/promotions/recommendations/trending?limit=10`);
      return response.data.products;
    }
  });

  // Fetch recommendation analytics
  const { data: analytics } = useQuery({
    queryKey: ['recommendation-analytics'],
    queryFn: async () => {
      const response = await axios.get(`${API_BASE_URL}/api/promotions/recommendations/analytics`);
      return response.data;
    }
  });

  // Fetch similar products for selected product
  const { data: similarProducts, refetch: refetchSimilar } = useQuery({
    queryKey: ['similar-products', selectedProduct],
    queryFn: async () => {
      if (!selectedProduct) return null;
      const response = await axios.get(
        `${API_BASE_URL}/api/promotions/recommendations/similar/${selectedProduct}?limit=5`
      );
      return response.data.products;
    },
    enabled: !!selectedProduct
  });

  // Fetch complementary products
  const { data: complementaryProducts, refetch: refetchComplementary } = useQuery({
    queryKey: ['complementary-products', selectedProduct],
    queryFn: async () => {
      if (!selectedProduct) return null;
      const response = await axios.get(
        `${API_BASE_URL}/api/promotions/recommendations/complementary/${selectedProduct}?limit=5`
      );
      return response.data.products;
    },
    enabled: !!selectedProduct
  });

  // Fetch frequently bought together
  const { data: frequentlyBought, refetch: refetchFrequent } = useQuery({
    queryKey: ['frequently-bought', selectedProduct],
    queryFn: async () => {
      if (!selectedProduct) return null;
      const response = await axios.get(
        `${API_BASE_URL}/api/promotions/recommendations/frequently-bought/${selectedProduct}?limit=3`
      );
      return response.data.products;
    },
    enabled: !!selectedProduct
  });

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'similar':
        return <Package2 className="h-4 w-4" />;
      case 'complementary':
        return <ShoppingBag className="h-4 w-4" />;
      case 'upsell':
        return <TrendingUp className="h-4 w-4" />;
      case 'crosssell':
        return <Zap className="h-4 w-4" />;
      default:
        return <Star className="h-4 w-4" />;
    }
  };

  const formatPercentage = (value: number | null) => {
    if (value === null || value === undefined) return '0%';
    return `${(value * 100).toFixed(1)}%`;
  };

  const formatCurrency = (value: number | null) => {
    if (value === null || value === undefined) return '$0.00';
    return `$${value.toFixed(2)}`;
  };

  // Show "No Store Selected" UI if no store is selected
  if (!currentStore) {
    return (
      <div className="h-full flex items-center justify-center bg-gray-50 dark:bg-gray-900 dark:bg-gray-900">
        <div className="text-center">
          <div className="mb-4">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-primary-100 dark:bg-primary-900 rounded-full">
              <TrendingUp className="w-8 h-8 text-primary-600 dark:text-primary-400" />
            </div>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">No Store Selected</h3>
          <p className="text-gray-500 dark:text-gray-400 dark:text-gray-400">Please select a store to manage product recommendations</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Product Recommendations</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Managing product recommendations for {currentStore.name}</p>
        </div>
        <button
          onClick={() => {
            refetchSimilar();
            refetchComplementary();
            refetchFrequent();
          }}
          className="flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
        >
          <RefreshCw className="h-5 w-5 mr-2" />
          Refresh Data
        </button>
      </div>

      {/* Tabs */}
      <div className="border-b dark:border-gray-700 border-gray-200 dark:border-gray-700">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('overview')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'overview'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-200'
            }`}
          >
            Overview
          </button>
          <button
            onClick={() => setActiveTab('performance')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'performance'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-200'
            }`}
          >
            Performance
          </button>
          <button
            onClick={() => setActiveTab('test')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'test'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-200'
            }`}
          >
            Test Recommendations
          </button>
        </nav>
      </div>

      {/* Content */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="bg-white dark:bg-gray-800 rounded-lg  p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Products with Recs</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">
                    {analytics?.overall?.products_with_recommendations || 0}
                  </p>
                </div>
                <Target className="h-8 w-8 text-primary-500" />
              </div>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-lg  p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Avg CTR</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">
                    {formatPercentage(analytics?.overall?.avg_ctr)}
                  </p>
                </div>
                <BarChart3 className="h-8 w-8 text-accent-500" />
              </div>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-lg  p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Avg Conversion</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">
                    {formatPercentage(analytics?.overall?.avg_conversion)}
                  </p>
                </div>
                <TrendingUp className="h-8 w-8 text-purple-500" />
              </div>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-lg  p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Revenue Impact</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">
                    {formatCurrency(analytics?.overall?.total_revenue_impact)}
                  </p>
                </div>
                <ArrowUpRight className="h-8 w-8 text-primary-500" />
              </div>
            </div>
          </div>

          {/* Trending Products */}
          <div className="bg-white dark:bg-gray-800 rounded-lg ">
            <div className="p-6 border-b dark:border-gray-700">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Trending Products</h3>
            </div>
            <div className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {trendingProducts?.slice(0, 6).map((product: any) => (
                  <div key={product.product_id} className="border dark:border-gray-700 rounded-lg p-6 hover:bg-gray-50 dark:hover:bg-gray-700">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h4 className="font-medium text-gray-900 dark:text-white text-sm">
                          {product.product_name}
                        </h4>
                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{product.brand}</p>
                        <p className="text-xs text-gray-500 dark:text-gray-400">{product.category}</p>
                      </div>
                      <TrendingUp className="h-4 w-4 text-primary-500" />
                    </div>
                    <div className="mt-3 flex justify-between items-center">
                      <span className="text-lg font-semibold text-gray-900 dark:text-white">
                        ${product.unit_price}
                      </span>
                      {product.thc_percentage && (
                        <span className="text-xs bg-primary-100 text-primary-800 px-2 py-1 rounded">
                          THC: {product.thc_percentage}%
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Recommendation Types Performance */}
          <div className="bg-white dark:bg-gray-800 rounded-lg ">
            <div className="p-6 border-b dark:border-gray-700">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Performance by Type</h3>
            </div>
            <div className="overflow-hidden">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead className="bg-gray-50 dark:bg-gray-900">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Type
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Count
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Avg Score
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      CTR
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Conversion
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Revenue Impact
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                  {analytics?.by_type?.map((type: RecommendationMetric) => (
                    <tr key={type.recommendation_type} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          {getTypeIcon(type.recommendation_type)}
                          <span className="ml-2 text-sm font-medium text-gray-900 dark:text-white capitalize">
                            {type.recommendation_type}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                        {type.count}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                        {(type.avg_score * 100).toFixed(0)}%
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                        {formatPercentage(type.avg_ctr)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                        {formatPercentage(type.avg_conversion)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                        {formatCurrency(type.revenue_impact)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'performance' && (
        <div className="bg-white dark:bg-gray-800 rounded-lg ">
          <div className="p-6 border-b dark:border-gray-700">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Top Performing Recommendations</h3>
          </div>
          <div className="overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-900">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Source Product
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Recommended
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    CTR
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Conversion
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Revenue
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                {analytics?.top_performers?.map((perf: TopPerformer, index: number) => (
                  <tr key={index} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                    <td className="px-6 py-4">
                      <div className="text-sm font-medium text-gray-900 dark:text-white">
                        {perf.source_product}
                      </div>
                      <div className="text-xs text-gray-500 dark:text-gray-400">{perf.product_id}</div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm font-medium text-gray-900 dark:text-white">
                        {perf.recommended_product}
                      </div>
                      <div className="text-xs text-gray-500 dark:text-gray-400">{perf.recommended_product_id}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        {getTypeIcon(perf.recommendation_type)}
                        <span className="ml-2 text-sm text-gray-500 dark:text-gray-400 capitalize">
                          {perf.recommendation_type}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                      {formatPercentage(perf.click_through_rate)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                      {formatPercentage(perf.conversion_rate)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                      {formatCurrency(perf.revenue_impact)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'test' && (
        <div className="space-y-6">
          {/* Product Selector */}
          <div className="bg-white dark:bg-gray-800 rounded-lg  p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Test Recommendations</h3>
            <div className="max-w-md">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Enter Product ID (SKU)
              </label>
              <div className="flex space-x-2">
                <input
                  type="text"
                  value={selectedProduct}
                  onChange={(e) => setSelectedProduct(e.target.value)}
                  placeholder="e.g., 12345"
                  className="flex-1 px-3 py-2 border dark:border-gray-700 border-gray-200 dark:border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
                <button
                  onClick={() => {
                    refetchSimilar();
                    refetchComplementary();
                    refetchFrequent();
                  }}
                  disabled={!selectedProduct}
                  className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Get Recommendations
                </button>
              </div>
            </div>
          </div>

          {selectedProduct && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Similar Products */}
              <div className="bg-white dark:bg-gray-800 rounded-lg ">
                <div className="p-6 border-b dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
                  <h4 className="font-semibold text-gray-900 dark:text-white flex items-center">
                    <Package2 className="h-5 w-5 mr-2 text-primary-500" />
                    Similar Products
                  </h4>
                </div>
                <div className="p-6 space-y-3">
                  {similarProducts?.map((product: any) => (
                    <div key={product.product_id} className="border dark:border-gray-700 rounded-lg p-4 hover:bg-gray-50 dark:hover:bg-gray-700">
                      <div className="font-medium text-sm text-gray-900 dark:text-white">
                        {product.product_name}
                      </div>
                      <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                        {product.brand} • {product.category}
                      </div>
                      <div className="flex justify-between items-center mt-2">
                        <span className="font-semibold text-gray-900 dark:text-white">${product.unit_price}</span>
                        {product.thc_percentage && (
                          <span className="text-xs bg-primary-100 text-primary-800 px-2 py-1 rounded">
                            THC: {product.thc_percentage}%
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                  {!similarProducts?.length && (
                    <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-4">
                      No similar products found
                    </p>
                  )}
                </div>
              </div>

              {/* Complementary Products */}
              <div className="bg-white dark:bg-gray-800 rounded-lg ">
                <div className="p-6 border-b dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
                  <h4 className="font-semibold text-gray-900 dark:text-white flex items-center">
                    <ShoppingBag className="h-5 w-5 mr-2 text-accent-500" />
                    Complementary Products
                  </h4>
                </div>
                <div className="p-6 space-y-3">
                  {complementaryProducts?.map((product: any) => (
                    <div key={product.product_id} className="border dark:border-gray-700 rounded-lg p-4 hover:bg-gray-50 dark:hover:bg-gray-700">
                      <div className="font-medium text-sm text-gray-900 dark:text-white">
                        {product.product_name}
                      </div>
                      <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                        {product.brand} • {product.category}
                      </div>
                      <div className="flex justify-between items-center mt-2">
                        <span className="font-semibold text-gray-900 dark:text-white">${product.unit_price}</span>
                      </div>
                    </div>
                  ))}
                  {!complementaryProducts?.length && (
                    <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-4">
                      No complementary products found
                    </p>
                  )}
                </div>
              </div>

              {/* Frequently Bought Together */}
              <div className="bg-white dark:bg-gray-800 rounded-lg ">
                <div className="p-6 border-b dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
                  <h4 className="font-semibold text-gray-900 dark:text-white flex items-center">
                    <Zap className="h-5 w-5 mr-2 text-purple-500" />
                    Frequently Bought Together
                  </h4>
                </div>
                <div className="p-6 space-y-3">
                  {frequentlyBought?.map((product: any) => (
                    <div key={product.product_id} className="border dark:border-gray-700 rounded-lg p-4 hover:bg-gray-50 dark:hover:bg-gray-700">
                      <div className="font-medium text-sm text-gray-900 dark:text-white">
                        {product.product_name}
                      </div>
                      <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                        {product.brand} • {product.category}
                      </div>
                      <div className="flex justify-between items-center mt-2">
                        <span className="font-semibold text-gray-900 dark:text-white">${product.unit_price}</span>
                      </div>
                    </div>
                  ))}
                  {!frequentlyBought?.length && (
                    <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-4">
                      No frequently bought items found
                    </p>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}