import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';
import { Product } from '../types';
import { Leaf, Plus, Edit2, Trash2, Search, Filter } from 'lucide-react';

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
        return 'bg-primary-100 text-primary-800';
      case 'edibles':
        return 'bg-purple-100 text-purple-800';
      case 'concentrates':
        return 'bg-orange-100 text-orange-800';
      case 'vapes':
        return 'bg-blue-100 text-blue-800';
      case 'accessories':
        return 'bg-gray-50 text-gray-800';
      default:
        return 'bg-gray-50 text-gray-800';
    }
  };

  const getStrainColor = (strain: string) => {
    switch (strain) {
      case 'indica':
        return 'bg-indigo-100 text-indigo-800';
      case 'sativa':
        return 'bg-warning-100 text-warning-800';
      case 'hybrid':
        return 'bg-pink-100 text-pink-800';
      case 'cbd':
        return 'bg-cyan-100 text-cyan-800';
      default:
        return 'bg-gray-50 text-gray-800';
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-danger-50 border border-red-200 text-red-700 px-4 py-3 rounded">
        Error loading products: {(error as Error).message}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Product Catalog</h1>
        <button
          onClick={() => setShowAddModal(true)}
          className="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 flex items-center gap-2"
        >
          <Plus className="h-5 w-5" />
          Add Product
        </button>
      </div>

      <div className="bg-white rounded-lg  p-6">
        <div className="flex gap-6 mb-6">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
              <input
                type="text"
                placeholder="Search products..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>
          </div>
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-500"
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
            className="px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-500"
          >
            <option value="all">All Strains</option>
            <option value="indica">Indica</option>
            <option value="sativa">Sativa</option>
            <option value="hybrid">Hybrid</option>
            <option value="cbd">CBD</option>
          </select>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {products?.data?.map((product: Product) => (
            <div key={product.id} className="bg-white border border-gray-200 rounded-lg hover:border border-gray-200 transition-">
              <div className="p-6">
                <div className="flex justify-between items-start mb-2">
                  <Leaf className="h-8 w-8 text-primary-600" />
                  <div className="flex gap-1">
                    <button
                      onClick={() => setEditingProduct(product)}
                      className="text-indigo-600 hover:text-indigo-900"
                    >
                      <Edit2 className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => {
                        if (confirm('Are you sure you want to delete this product?')) {
                          deleteMutation.mutate(product.id);
                        }
                      }}
                      className="text-danger-600 hover:text-red-900"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
                
                <h3 className="font-semibold text-gray-900 mb-1">{product.name}</h3>
                <p className="text-sm text-gray-600 mb-2">{product.brand}</p>
                
                <div className="flex gap-2 mb-2">
                  <span className={`px-2 py-1 text-xs rounded-full ${getCategoryColor(product.category)}`}>
                    {product.category}
                  </span>
                  <span className={`px-2 py-1 text-xs rounded-full ${getStrainColor(product.strain_type)}`}>
                    {product.strain_type}
                  </span>
                </div>
                
                <div className="text-sm text-gray-600 mb-2">
                  <div>THC: {product.thc_content}%</div>
                  <div>CBD: {product.cbd_content}%</div>
                </div>
                
                <div className="text-2xl font-bold text-primary-600">
                  ${product.price.toFixed(2)}
                </div>
                
                <div className="text-xs text-gray-500 mt-2">
                  SKU: {product.sku}
                </div>
                
                {product.effects && product.effects.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1">
                    {product.effects.slice(0, 3).map((effect, index) => (
                      <span key={index} className="text-xs bg-gray-50 text-gray-600 px-2 py-1 rounded">
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
            <Leaf className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No products found</h3>
            <p className="mt-1 text-sm text-gray-500">
              Get started by adding a new product to your catalog.
            </p>
          </div>
        )}
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg  p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Products</p>
              <p className="text-2xl font-bold text-gray-900">
                {products?.data?.length || 0}
              </p>
            </div>
            <Leaf className="h-8 w-8 text-primary-600" />
          </div>
        </div>

        <div className="bg-white rounded-lg  p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Flower Products</p>
              <p className="text-2xl font-bold text-primary-600">
                {products?.data?.filter((p: Product) => p.category === 'flower').length || 0}
              </p>
            </div>
            <Leaf className="h-8 w-8 text-primary-600" />
          </div>
        </div>

        <div className="bg-white rounded-lg  p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Avg THC %</p>
              <p className="text-2xl font-bold text-orange-600">
                {products?.data?.length ? 
                  (products.data.reduce((sum: number, p: Product) => sum + p.thc_content, 0) / products.data.length).toFixed(1)
                  : '0.0'
                }%
              </p>
            </div>
            <Filter className="h-8 w-8 text-orange-600" />
          </div>
        </div>

        <div className="bg-white rounded-lg  p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Avg Price</p>
              <p className="text-2xl font-bold text-gray-900">
                ${products?.data?.length ? 
                  (products.data.reduce((sum: number, p: Product) => sum + p.price, 0) / products.data.length).toFixed(2)
                  : '0.00'
                }
              </p>
            </div>
            <Leaf className="h-8 w-8 text-accent-600" />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Products;