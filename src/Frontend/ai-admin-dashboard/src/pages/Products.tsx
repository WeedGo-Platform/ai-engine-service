import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';
import { Product } from '../types';
import { Leaf, Plus, Edit2, Trash2, Search, Filter } from 'lucide-react';
import toast from 'react-hot-toast';
import { confirmToastAsync } from '../components/ConfirmToast';

const Products: React.FC = () => {
  const queryClient = useQueryClient();
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedStrainType, setSelectedStrainType] = useState<string>('all');
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingProduct, setEditingProduct] = useState<Product | null>(null);

  const { data: products, isLoading, error } = useQuery({
    queryKey: ['products', searchTerm, selectedCategory, selectedStrainType],
    queryFn: async () => {
      const params: any = {};
      if (searchTerm) params.search = searchTerm;
      if (selectedCategory !== 'all') params.category = selectedCategory;
      if (selectedStrainType !== 'all') params.strain_type = selectedStrainType;
      const response = await api.products.getAll(params);
      return response.data;
    },
  });

  const createMutation = useMutation({
    mutationFn: (product: Partial<Product>) => api.products.create(product),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] });
      setShowAddModal(false);
    },
  });

  const updateMutation = useMutation({
    mutationFn: (data: { id: string; product: Partial<Product> }) =>
      api.products.update(data.id, data.product),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] });
      setEditingProduct(null);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.products.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] });
    },
  });

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'flower':
        return 'bg-primary-100 dark:bg-primary-900/30 text-primary-800 dark:text-primary-300';
      case 'edibles':
        return 'bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-300';
      case 'concentrates':
        return 'bg-orange-100 dark:bg-orange-900/30 text-orange-800 dark:text-orange-300';
      case 'vapes':
        return 'bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300';
      case 'accessories':
        return 'bg-gray-50 dark:bg-gray-700 text-gray-800 dark:text-gray-300';
      default:
        return 'bg-gray-50 dark:bg-gray-700 text-gray-800 dark:text-gray-300';
    }
  };

  const getStrainColor = (strain: string) => {
    switch (strain) {
      case 'indica':
        return 'bg-indigo-100 dark:bg-indigo-900/30 text-indigo-800 dark:text-indigo-300';
      case 'sativa':
        return 'bg-warning-100 dark:bg-warning-900/30 text-warning-800 dark:text-warning-300';
      case 'hybrid':
        return 'bg-pink-100 dark:bg-pink-900/30 text-pink-800 dark:text-pink-300';
      case 'cbd':
        return 'bg-cyan-100 dark:bg-cyan-900/30 text-cyan-800 dark:text-cyan-300';
      default:
        return 'bg-gray-50 dark:bg-gray-700 text-gray-800 dark:text-gray-300';
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 dark:border-primary-400"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-danger-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 px-4 py-3 rounded">
        Error loading products: {(error as Error).message}
      </div>
    );
  }

  return (
    <div className="space-y-4 sm:space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 sm:gap-0">
        <h1 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white">Product Catalog</h1>
        <button
          onClick={() => setShowAddModal(true)}
          className="w-full sm:w-auto bg-primary-600 dark:bg-primary-700 text-white px-4 py-2 rounded-lg hover:bg-primary-700 dark:hover:bg-primary-600 flex items-center justify-center gap-2 font-medium text-sm active:scale-95 transition-all touch-manipulation"
        >
          <Plus className="h-4 w-4 sm:h-5 sm:h-5" />
          Add Product
        </button>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-4 sm:p-6">
        <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 mb-4 sm:mb-6">
          <div className="flex-1 min-w-0">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 dark:text-gray-500 h-4 w-4 sm:h-5 sm:w-5" />
              <input
                type="text"
                placeholder="Search products..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-9 sm:pl-10 pr-4 py-2 text-sm border border-gray-200 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 dark:focus:ring-primary-400 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 transition-colors"
              />
            </div>
          </div>
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="px-3 sm:px-4 py-2 text-sm border border-gray-200 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 dark:focus:ring-primary-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white transition-colors"
          >
            <option value="all">All Categories</option>
            <option value="flower">Flower</option>
            <option value="edibles">Edibles</option>
            <option value="concentrates">Concentrates</option>
            <option value="vapes">Vapes</option>
            <option value="accessories">Accessories</option>
          </select>
          <select
            value={selectedStrainType}
            onChange={(e) => setSelectedStrainType(e.target.value)}
            className="px-3 sm:px-4 py-2 text-sm border border-gray-200 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 dark:focus:ring-primary-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white transition-colors"
          >
            <option value="all">All Strains</option>
            <option value="indica">Indica</option>
            <option value="sativa">Sativa</option>
            <option value="hybrid">Hybrid</option>
            <option value="cbd">CBD</option>
          </select>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3 sm:gap-4 lg:gap-6">
          {products?.data?.map((product: Product) => (
            <div key={product.id} className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg hover:shadow-lg dark:hover:shadow-2xl transition-all active:scale-[0.98]">
              <div className="p-4 sm:p-6">
                <div className="flex justify-between items-start mb-2">
                  <Leaf className="h-6 w-6 sm:h-8 sm:w-8 text-primary-600 dark:text-primary-400" />
                  <div className="flex gap-1 sm:gap-2">
                    <button
                      onClick={() => setEditingProduct(product)}
                      className="p-1.5 text-indigo-600 dark:text-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 rounded transition-colors active:scale-95 touch-manipulation"
                      aria-label="Edit product"
                    >
                      <Edit2 className="h-3.5 w-3.5 sm:h-4 sm:w-4" />
                    </button>
                    <button
                      onClick={() => {
                        if (confirmToastAsync('Are you sure you want to delete this product?')) {
                          deleteMutation.mutate(product.id);
                        }
                      }}
                      className="p-1.5 text-danger-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition-colors active:scale-95 touch-manipulation"
                      aria-label="Delete product"
                    >
                      <Trash2 className="h-3.5 w-3.5 sm:h-4 sm:w-4" />
                    </button>
                  </div>
                </div>

                <h3 className="text-sm sm:text-base font-semibold text-gray-900 dark:text-white mb-1 line-clamp-2">{product.name}</h3>
                <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400 mb-2">{product.brand}</p>

                <div className="flex gap-2 mb-2">
                  <span className={`px-2 py-1 text-xs rounded-full ${getCategoryColor(product.category)}`}>
                    {product.category}
                  </span>
                  <span className={`px-2 py-1 text-xs rounded-full ${getStrainColor(product.strain_type)}`}>
                    {product.strain_type}
                  </span>
                </div>

                <div className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                  <div>THC: {product.thc_content}%</div>
                  <div>CBD: {product.cbd_content}%</div>
                </div>

                <div className="text-2xl font-bold text-primary-600 dark:text-primary-400">
                  ${product.price.toFixed(2)}
                </div>

                <div className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                  SKU: {product.sku}
                </div>

                {product.effects && product.effects.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1">
                    {product.effects.slice(0, 3).map((effect, index) => (
                      <span key={index} className="text-xs bg-gray-50 dark:bg-gray-700 text-gray-600 dark:text-gray-300 px-2 py-1 rounded">
                        {effect}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        {(!products?.data || products.data.length === 0) && (
          <div className="text-center py-12">
            <Leaf className="mx-auto h-12 w-12 text-gray-400 dark:text-gray-600" />
            <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">No products found</h3>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              Get started by adding a new product to your catalog.
            </p>
          </div>
        )}
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Total Products</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {products?.data?.length || 0}
              </p>
            </div>
            <Leaf className="h-8 w-8 text-primary-600 dark:text-primary-400" />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Flower Products</p>
              <p className="text-2xl font-bold text-primary-600 dark:text-primary-400">
                {products?.data?.filter((p: Product) => p.category === 'flower').length || 0}
              </p>
            </div>
            <Leaf className="h-8 w-8 text-primary-600 dark:text-primary-400" />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Avg THC %</p>
              <p className="text-2xl font-bold text-orange-600 dark:text-orange-400">
                {products?.data?.length ?
                  (products.data.reduce((sum: number, p: Product) => sum + p.thc_content, 0) / products.data.length).toFixed(1)
                  : '0.0'
                }%
              </p>
            </div>
            <Filter className="h-8 w-8 text-orange-600 dark:text-orange-400" />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Avg Price</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                ${products?.data?.length ?
                  (products.data.reduce((sum: number, p: Product) => sum + p.price, 0) / products.data.length).toFixed(2)
                  : '0.00'
                }
              </p>
            </div>
            <Leaf className="h-8 w-8 text-accent-600 dark:text-accent-400" />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Products;