import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Plus, Edit2, Trash2, Calendar, DollarSign,
  Tag, Users, TrendingUp, Package, Copy, CheckCircle,
  ChevronRight, ChevronDown, Percent, Hash, Search, RotateCcw
} from 'lucide-react';
import { format } from 'date-fns';
import axios from 'axios';
import toast from 'react-hot-toast';
import { useStoreContext } from '../contexts/StoreContext';

const API_BASE_URL = 'http://localhost:5024';

interface Promotion {
  id: string;
  code?: string;
  name: string;
  description?: string;
  type: string;
  discount_type: string;
  discount_value: number;
  min_purchase_amount?: number;
  max_discount_amount?: number;
  usage_limit_per_customer?: number;
  total_usage_limit?: number;
  times_used: number;
  applies_to: string;
  category_ids?: string[];
  brand_ids?: string[];
  product_ids?: string[];
  stackable: boolean;
  priority: number;
  start_date: string;
  end_date?: string;
  active: boolean;
  first_time_customer_only: boolean;
}

export default function Promotions() {
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingPromotion, setEditingPromotion] = useState<Promotion | null>(null);
  const [activeTab, setActiveTab] = useState<'promotions' | 'tiers' | 'analytics' | 'pricing'>('promotions');
  const queryClient = useQueryClient();

  // Fetch active promotions
  const { data: promotions, isLoading } = useQuery({
    queryKey: ['promotions'],
    queryFn: async () => {
      const response = await axios.get(`${API_BASE_URL}/api/promotions/active`);
      return response.data.promotions;
    }
  });

  // Fetch price tiers
  const { data: tiers } = useQuery({
    queryKey: ['price-tiers'],
    queryFn: async () => {
      const response = await axios.get(`${API_BASE_URL}/api/promotions/tiers`);
      return response.data.tiers;
    }
  });

  // Fetch analytics
  const { data: analytics } = useQuery({
    queryKey: ['promotion-analytics'],
    queryFn: async () => {
      const response = await axios.get(`${API_BASE_URL}/api/promotions/analytics`);
      return response.data;
    }
  });

  // Create promotion mutation
  const createPromotion = useMutation({
    mutationFn: async (data: Partial<Promotion>) => {
      const response = await axios.post(`${API_BASE_URL}/api/promotions/create`, data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['promotions'] });
      toast.success('Promotion created successfully!');
      setShowCreateModal(false);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to create promotion');
    }
  });

  const getPromotionTypeIcon = (type: string) => {
    switch (type) {
      case 'percentage':
      case 'fixed_amount':
        return <Tag className="h-4 w-4" />;
      case 'bundle':
        return <Package className="h-4 w-4" />;
      case 'tiered':
        return <TrendingUp className="h-4 w-4" />;
      default:
        return <DollarSign className="h-4 w-4" />;
    }
  };

  const getStatusBadge = (active: boolean, startDate: string, endDate?: string) => {
    const now = new Date();
    const start = new Date(startDate);
    const end = endDate ? new Date(endDate) : null;

    if (!active) {
      return <span className="px-2 py-1 text-xs rounded-full bg-gray-50 text-gray-600">Inactive</span>;
    }
    if (now < start) {
      return <span className="px-2 py-1 text-xs rounded-full bg-warning-100 text-warning-600">Scheduled</span>;
    }
    if (end && now > end) {
      return <span className="px-2 py-1 text-xs rounded-full bg-danger-100 text-danger-600">Expired</span>;
    }
    return <span className="px-2 py-1 text-xs rounded-full bg-primary-100 text-primary-600">Active</span>;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Promotions & Pricing</h1>
          <p className="text-gray-600">Manage discounts, promotions, and price tiers</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
        >
          <Plus className="h-5 w-5 mr-2" />
          Create Promotion
        </button>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('promotions')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'promotions'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-200'
            }`}
          >
            Active Promotions
          </button>
          <button
            onClick={() => setActiveTab('tiers')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'tiers'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-200'
            }`}
          >
            Price Tiers
          </button>
          <button
            onClick={() => setActiveTab('analytics')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'analytics'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-200'
            }`}
          >
            Analytics
          </button>
          <button
            onClick={() => setActiveTab('pricing')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'pricing'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-200'
            }`}
          >
            Default Pricing
          </button>
        </nav>
      </div>

      {/* Content */}
      {activeTab === 'promotions' && (
        <div className="bg-white  rounded-lg">
          {isLoading ? (
            <div className="p-8 text-center">Loading promotions...</div>
          ) : (
            <div className="overflow-hidden">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Promotion
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Code
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Discount
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Usage
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Duration
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {promotions?.map((promo: Promotion) => (
                    <tr key={promo.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="flex-shrink-0">
                            {getPromotionTypeIcon(promo.type)}
                          </div>
                          <div className="ml-3">
                            <div className="text-sm font-medium text-gray-900">{promo.name}</div>
                            <div className="text-sm text-gray-500">{promo.type}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {promo.code ? (
                          <div className="flex items-center">
                            <code className="text-sm bg-gray-50 px-2 py-1 rounded">{promo.code}</code>
                            <button
                              onClick={() => {
                                navigator.clipboard.writeText(promo.code!);
                                toast.success('Code copied!');
                              }}
                              className="ml-2 text-gray-400 hover:text-gray-600"
                            >
                              <Copy className="h-4 w-4" />
                            </button>
                          </div>
                        ) : (
                          <span className="text-gray-400">—</span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          {promo.discount_type === 'percentage' 
                            ? `${promo.discount_value}%` 
                            : `$${promo.discount_value}`}
                        </div>
                        {promo.min_purchase_amount && (
                          <div className="text-xs text-gray-500">
                            Min: ${promo.min_purchase_amount}
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          {promo.times_used || 0} / {promo.total_usage_limit || '∞'}
                        </div>
                        {promo.usage_limit_per_customer && (
                          <div className="text-xs text-gray-500">
                            {promo.usage_limit_per_customer} per customer
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        <div>{format(new Date(promo.start_date), 'MMM d, yyyy')}</div>
                        {promo.end_date && (
                          <div>to {format(new Date(promo.end_date), 'MMM d, yyyy')}</div>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {getStatusBadge(promo.active, promo.start_date, promo.end_date)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <button
                          onClick={() => setEditingPromotion(promo)}
                          className="text-indigo-600 hover:text-indigo-900 mr-3"
                        >
                          <Edit2 className="h-4 w-4" />
                        </button>
                        <button className="text-danger-600 hover:text-red-900">
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {activeTab === 'tiers' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {tiers?.map((tier: any) => (
            <div key={tier.id} className="bg-white rounded-lg  p-6">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">{tier.name}</h3>
                  <p className="text-sm text-gray-500">{tier.customer_type}</p>
                </div>
                {tier.active && (
                  <CheckCircle className="h-5 w-5 text-primary-500" />
                )}
              </div>
              
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Discount</span>
                  <span className="text-sm font-medium">{tier.discount_percentage}%</span>
                </div>
                {tier.min_order_value && (
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Min Order</span>
                    <span className="text-sm font-medium">${tier.min_order_value}</span>
                  </div>
                )}
                {tier.min_monthly_spend && (
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Monthly Spend</span>
                    <span className="text-sm font-medium">${tier.min_monthly_spend}</span>
                  </div>
                )}
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Priority</span>
                  <span className="text-sm font-medium">{tier.priority}</span>
                </div>
              </div>

              <div className="mt-4 pt-4 border-t">
                <button className="w-full px-4 py-2 text-sm text-primary-600 hover:bg-primary-50 rounded-lg">
                  Assign to Customers
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {activeTab === 'analytics' && analytics && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Top Performing Promotions */}
          <div className="bg-white rounded-lg  p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Performing Promotions</h3>
            <div className="space-y-3">
              {analytics.promotions?.slice(0, 5).map((promo: any) => (
                <div key={promo.name} className="flex justify-between items-center">
                  <div>
                    <div className="text-sm font-medium text-gray-900">{promo.name}</div>
                    <div className="text-xs text-gray-500">{promo.times_used} uses</div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-medium">${promo.total_revenue?.toFixed(2) || 0}</div>
                    <div className="text-xs text-gray-500">revenue</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Promotion Stats */}
          <div className="bg-white rounded-lg  p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Overall Stats</h3>
            <div className="grid grid-cols-2 gap-6">
              <div className="bg-gray-50 rounded-lg p-6">
                <div className="text-2xl font-bold text-gray-900">
                  {analytics.promotions?.reduce((sum: number, p: any) => sum + (p.times_used || 0), 0) || 0}
                </div>
                <div className="text-sm text-gray-600">Total Uses</div>
              </div>
              <div className="bg-gray-50 rounded-lg p-6">
                <div className="text-2xl font-bold text-gray-900">
                  ${analytics.promotions?.reduce((sum: number, p: any) => sum + (p.total_discount_given || 0), 0).toFixed(2) || '0.00'}
                </div>
                <div className="text-sm text-gray-600">Total Discounts</div>
              </div>
              <div className="bg-gray-50 rounded-lg p-6">
                <div className="text-2xl font-bold text-gray-900">
                  ${analytics.promotions?.reduce((sum: number, p: any) => sum + (p.total_revenue || 0), 0).toFixed(2) || '0.00'}
                </div>
                <div className="text-sm text-gray-600">Total Revenue</div>
              </div>
              <div className="bg-gray-50 rounded-lg p-6">
                <div className="text-2xl font-bold text-gray-900">
                  ${analytics.promotions?.[0]?.avg_order_value?.toFixed(2) || '0.00'}
                </div>
                <div className="text-sm text-gray-600">Avg Order Value</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'pricing' && (
        <PricingConfiguration />
      )}

      {/* Create/Edit Modal */}
      {(showCreateModal || editingPromotion) && (
        <PromotionModal
          promotion={editingPromotion}
          onClose={() => {
            setShowCreateModal(false);
            setEditingPromotion(null);
          }}
          onSave={(data) => createPromotion.mutate(data)}
        />
      )}
    </div>
  );
}

// Promotion Modal Component
function PromotionModal({ 
  promotion, 
  onClose, 
  onSave 
}: { 
  promotion?: Promotion | null;
  onClose: () => void;
  onSave: (data: Partial<Promotion>) => void;
}) {
  const [formData, setFormData] = useState<Partial<Promotion>>({
    name: promotion?.name || '',
    code: promotion?.code || '',
    description: promotion?.description || '',
    type: promotion?.type || 'percentage',
    discount_type: promotion?.discount_type || 'percentage',
    discount_value: promotion?.discount_value || 0,
    min_purchase_amount: promotion?.min_purchase_amount || undefined,
    max_discount_amount: promotion?.max_discount_amount || undefined,
    usage_limit_per_customer: promotion?.usage_limit_per_customer || undefined,
    total_usage_limit: promotion?.total_usage_limit || undefined,
    applies_to: promotion?.applies_to || 'all',
    stackable: promotion?.stackable || false,
    priority: promotion?.priority || 0,
    start_date: promotion?.start_date || new Date().toISOString(),
    end_date: promotion?.end_date || undefined,
    active: promotion?.active !== undefined ? promotion.active : true,
    first_time_customer_only: promotion?.first_time_customer_only || false,
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(formData);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg border border-gray-200 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b">
          <h2 className="text-xl font-semibold text-gray-900">
            {promotion ? 'Edit Promotion' : 'Create New Promotion'}
          </h2>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div className="grid grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Promotion Name *
              </label>
              <input
                type="text"
                required
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Promo Code
              </label>
              <input
                type="text"
                value={formData.code}
                onChange={(e) => setFormData({ ...formData, code: e.target.value.toUpperCase() })}
                placeholder="e.g., SAVE20"
                className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              rows={2}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Promotion Type *
              </label>
              <select
                value={formData.type}
                onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="percentage">Percentage Discount</option>
                <option value="fixed_amount">Fixed Amount</option>
                <option value="bogo">Buy One Get One</option>
                <option value="bundle">Bundle Deal</option>
                <option value="tiered">Tiered Discount</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Discount Type *
              </label>
              <select
                value={formData.discount_type}
                onChange={(e) => setFormData({ ...formData, discount_type: e.target.value })}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="percentage">Percentage</option>
                <option value="amount">Fixed Amount</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Discount Value *
              </label>
              <input
                type="number"
                required
                min="0"
                step="0.01"
                value={formData.discount_value}
                onChange={(e) => setFormData({ ...formData, discount_value: parseFloat(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Min Purchase
              </label>
              <input
                type="number"
                min="0"
                step="0.01"
                value={formData.min_purchase_amount || ''}
                onChange={(e) => setFormData({ ...formData, min_purchase_amount: e.target.value ? parseFloat(e.target.value) : undefined })}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Max Discount
              </label>
              <input
                type="number"
                min="0"
                step="0.01"
                value={formData.max_discount_amount || ''}
                onChange={(e) => setFormData({ ...formData, max_discount_amount: e.target.value ? parseFloat(e.target.value) : undefined })}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Start Date *
              </label>
              <input
                type="datetime-local"
                required
                value={formData.start_date ? formData.start_date.slice(0, 16) : ''}
                onChange={(e) => setFormData({ ...formData, start_date: new Date(e.target.value).toISOString() })}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                End Date
              </label>
              <input
                type="datetime-local"
                value={formData.end_date ? formData.end_date.slice(0, 16) : ''}
                onChange={(e) => setFormData({ ...formData, end_date: e.target.value ? new Date(e.target.value).toISOString() : undefined })}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Usage Limit (Total)
              </label>
              <input
                type="number"
                min="0"
                value={formData.total_usage_limit || ''}
                onChange={(e) => setFormData({ ...formData, total_usage_limit: e.target.value ? parseInt(e.target.value) : undefined })}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Per Customer Limit
              </label>
              <input
                type="number"
                min="0"
                value={formData.usage_limit_per_customer || ''}
                onChange={(e) => setFormData({ ...formData, usage_limit_per_customer: e.target.value ? parseInt(e.target.value) : undefined })}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={formData.stackable}
                onChange={(e) => setFormData({ ...formData, stackable: e.target.checked })}
                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-200 rounded"
              />
              <span className="ml-2 text-sm text-gray-700">
                Allow stacking with other promotions
              </span>
            </label>

            <label className="flex items-center">
              <input
                type="checkbox"
                checked={formData.first_time_customer_only}
                onChange={(e) => setFormData({ ...formData, first_time_customer_only: e.target.checked })}
                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-200 rounded"
              />
              <span className="ml-2 text-sm text-gray-700">
                First-time customers only
              </span>
            </label>

            <label className="flex items-center">
              <input
                type="checkbox"
                checked={formData.active}
                onChange={(e) => setFormData({ ...formData, active: e.target.checked })}
                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-200 rounded"
              />
              <span className="ml-2 text-sm text-gray-700">
                Active
              </span>
            </label>
          </div>

          <div className="flex justify-end space-x-3 pt-4 border-t">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-300"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
            >
              {promotion ? 'Update' : 'Create'} Promotion
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// Pricing Configuration Component
function PricingConfiguration() {
  const { currentStore } = useStoreContext();
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [selectedSubCategory, setSelectedSubCategory] = useState<string | null>(null);
  const [selectedSubSubCategory, setSelectedSubSubCategory] = useState<string | null>(null);
  const [selectedProduct, setSelectedProduct] = useState<any | null>(null);
  const [markupValue, setMarkupValue] = useState<number>(25); // Will be updated from store settings
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set());
  const [expandedSubCategories, setExpandedSubCategories] = useState<Set<string>>(new Set());
  const [showProducts, setShowProducts] = useState(false);
  const [updateSuccess, setUpdateSuccess] = useState(false);
  const [defaultMarkupEnabled, setDefaultMarkupEnabled] = useState(true);
  const [storeDefaultMarkup, setStoreDefaultMarkup] = useState(25);
  const [settingsUpdateSuccess, setSettingsUpdateSuccess] = useState(false);
  const queryClient = useQueryClient();

  // Fetch store pricing settings
  const { data: pricingSettings } = useQuery({
    queryKey: ['pricing-settings', currentStore?.id],
    queryFn: async () => {
      if (!currentStore?.id) throw new Error('No store selected');

      const token = localStorage.getItem('weedgo_auth_access_token') ||
                    sessionStorage.getItem('weedgo_auth_access_token');

      const response = await axios.get(`${API_BASE_URL}/api/store-inventory/pricing/settings`, {
        headers: {
          'X-Store-ID': currentStore.id,
          ...(token && { 'Authorization': `Bearer ${token}` })
        }
      });
      return response.data.settings;
    },
    enabled: !!currentStore?.id,
    onSuccess: (data) => {
      setDefaultMarkupEnabled(data.default_markup_enabled);
      setStoreDefaultMarkup(data.default_markup_percentage);
      // Set initial markup value to store default
      setMarkupValue(data.default_markup_percentage);
    }
  });

  // Update pricing settings mutation
  const updatePricingSettings = useMutation({
    mutationFn: async (data: {
      default_markup_enabled: boolean;
      default_markup_percentage: number;
    }) => {
      if (!currentStore?.id) throw new Error('No store selected');

      const token = localStorage.getItem('weedgo_auth_access_token') ||
                    sessionStorage.getItem('weedgo_auth_access_token');

      const response = await axios.post(
        `${API_BASE_URL}/api/store-inventory/pricing/settings`,
        data,
        {
          headers: {
            'X-Store-ID': currentStore.id,
            ...(token && { 'Authorization': `Bearer ${token}` })
          }
        }
      );
      return response.data;
    },
    onSuccess: (data) => {
      toast.success('Default markup settings updated!');
      setSettingsUpdateSuccess(true);
      setTimeout(() => setSettingsUpdateSuccess(false), 3000);
      queryClient.invalidateQueries(['pricing-settings', currentStore?.id]);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update settings');
    }
  });

  // Fetch category hierarchy with pricing info
  const { data: categoriesData, isLoading, refetch } = useQuery({
    queryKey: ['pricing-categories', currentStore?.id],
    queryFn: async () => {
      if (!currentStore?.id) throw new Error('No store selected');

      // Get auth token
      const token = localStorage.getItem('weedgo_auth_access_token') ||
                    sessionStorage.getItem('weedgo_auth_access_token');

      const response = await axios.get(`${API_BASE_URL}/api/store-inventory/pricing/categories`, {
        headers: {
          'X-Store-ID': currentStore.id,
          ...(token && { 'Authorization': `Bearer ${token}` })
        }
      });
      return response.data.categories;
    },
    enabled: !!currentStore?.id
  });

  // Fetch products for selected category
  const { data: productsData, isLoading: productsLoading, refetch: refetchProducts } = useQuery({
    queryKey: ['category-products', currentStore?.id, selectedCategory, selectedSubCategory, selectedSubSubCategory],
    queryFn: async () => {
      if (!currentStore?.id || !selectedSubSubCategory) return [];

      // Get auth token
      const token = localStorage.getItem('weedgo_auth_access_token') ||
                    sessionStorage.getItem('weedgo_auth_access_token');

      const params = new URLSearchParams({
        category: selectedCategory || '',
        sub_category: selectedSubCategory || '',
        sub_sub_category: selectedSubSubCategory || ''
      });
      const response = await axios.get(
        `${API_BASE_URL}/api/store-inventory?${params}`,
        {
          headers: {
            'X-Store-ID': currentStore.id,
            ...(token && { 'Authorization': `Bearer ${token}` })
          }
        }
      );
      return response.data.inventory || [];
    },
    enabled: !!currentStore?.id && !!selectedSubSubCategory && showProducts
  });

  // Update pricing mutation
  const updatePricing = useMutation({
    mutationFn: async (data: {
      category?: string;
      sub_category?: string;
      sub_sub_category?: string;
      sku?: string;
      markup_percentage: number;
      update_type: 'markup' | 'fixed';
    }) => {
      if (!currentStore?.id) throw new Error('No store selected');

      // Get auth token
      const token = localStorage.getItem('weedgo_auth_access_token') ||
                    sessionStorage.getItem('weedgo_auth_access_token');

      const response = await axios.post(
        `${API_BASE_URL}/api/store-inventory/pricing/update`,
        data,
        {
          headers: {
            'X-Store-ID': currentStore.id,
            ...(token && { 'Authorization': `Bearer ${token}` })
          }
        }
      );
      return response.data;
    },
    onSuccess: (data) => {
      // Show success toast with details
      const message = data.products_updated === 1
        ? `Successfully updated 1 product!`
        : `Successfully updated ${data.products_updated} products!`;

      toast.success(message, {
        duration: 5000,
        icon: '✅',
      });

      // Trigger success animation
      setUpdateSuccess(true);
      setTimeout(() => setUpdateSuccess(false), 3000);

      // Refresh data
      refetch(); // Refresh category data
      if (showProducts) {
        refetchProducts(); // Refresh products data if products are displayed
      }
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update pricing');
    }
  });

  // Reset price overrides mutation
  const resetOverrides = useMutation({
    mutationFn: async (params: any) => {
      if (!currentStore?.id) throw new Error('No store selected');

      const token = localStorage.getItem('weedgo_auth_access_token') ||
                    sessionStorage.getItem('weedgo_auth_access_token');

      const response = await axios.post(
        `${API_BASE_URL}/api/store-inventory/pricing/reset-overrides`,
        params,
        {
          headers: {
            'X-Store-ID': currentStore.id,
            ...(token && { 'Authorization': `Bearer ${token}` })
          }
        }
      );
      return response.data;
    },
    onSuccess: () => {
      toast.success('Price overrides cleared successfully');
      // Trigger success animation
      setUpdateSuccess(true);
      setTimeout(() => setUpdateSuccess(false), 3000);

      // Refetch data
      refetchCategories();
      if (showProducts && selectedSubSubCategory) {
        refetchProducts();
      }
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to reset price overrides');
    }
  });

  const handleResetOverrides = () => {
    const resetData: any = {};

    // Determine scope
    if (selectedProduct) {
      resetData.sku = selectedProduct.sku;
    } else if (selectedSubSubCategory) {
      resetData.sub_sub_category = selectedSubSubCategory;
      resetData.sub_category = selectedSubCategory;
      resetData.category = selectedCategory;
    } else if (selectedSubCategory) {
      resetData.sub_category = selectedSubCategory;
      resetData.category = selectedCategory;
    } else if (selectedCategory) {
      resetData.category = selectedCategory;
    }

    const scope = selectedProduct ? 'this product' :
                  selectedSubSubCategory ? 'this sub-subcategory' :
                  selectedSubCategory ? 'this subcategory' :
                  selectedCategory ? 'this category' :
                  'ALL products in the store';

    if (window.confirm(`This will remove all price overrides for ${scope} and use the calculated markup. Are you sure?`)) {
      resetOverrides.mutate(resetData);
    }
  };

  const handleApplyMarkup = () => {
    const updateData: any = {
      markup_percentage: markupValue,
      update_type: 'markup'
    };

    // If a specific product is selected, update only that product
    if (selectedProduct) {
      updateData.sku = selectedProduct.sku;
    } else if (selectedSubSubCategory) {
      updateData.sub_sub_category = selectedSubSubCategory;
      updateData.sub_category = selectedSubCategory;
      updateData.category = selectedCategory;
    } else if (selectedSubCategory) {
      updateData.sub_category = selectedSubCategory;
      updateData.category = selectedCategory;
    } else if (selectedCategory) {
      updateData.category = selectedCategory;
    }

    if (!selectedCategory && !selectedSubCategory && !selectedSubSubCategory && !selectedProduct) {
      // Apply to all products - show confirmation
      if (window.confirm(`This will update the markup for ALL products in the store to ${markupValue}%. Are you sure?`)) {
        updatePricing.mutate(updateData);
      }
    } else {
      updatePricing.mutate(updateData);
    }
  };

  const toggleCategory = (category: string) => {
    const newExpanded = new Set(expandedCategories);
    if (newExpanded.has(category)) {
      newExpanded.delete(category);
    } else {
      newExpanded.add(category);
    }
    setExpandedCategories(newExpanded);
  };

  const toggleSubCategory = (key: string) => {
    const newExpanded = new Set(expandedSubCategories);
    if (newExpanded.has(key)) {
      newExpanded.delete(key);
    } else {
      newExpanded.add(key);
    }
    setExpandedSubCategories(newExpanded);
  };

  const selectCategory = (category: string | null, subCategory: string | null = null, subSubCategory: string | null = null) => {
    setSelectedCategory(category);
    setSelectedSubCategory(subCategory);
    setSelectedSubSubCategory(subSubCategory);
    setSelectedProduct(null); // Clear product selection when category changes

    // Show products when sub-sub-category is selected
    setShowProducts(!!subSubCategory);

    // Set default markup based on current average
    if (category && categoriesData?.[category]) {
      const catData = categoriesData[category];
      if (subSubCategory && subCategory && catData.subcategories?.[subCategory]?.subsubcategories?.[subSubCategory]) {
        setMarkupValue(Math.round(catData.subcategories[subCategory].subsubcategories[subSubCategory].avg_markup));
      } else if (subCategory && catData.subcategories?.[subCategory]) {
        setMarkupValue(Math.round(catData.subcategories[subCategory].avg_markup || storeDefaultMarkup));
      } else {
        setMarkupValue(Math.round(catData.avg_markup || storeDefaultMarkup));
      }
    }
  };

  const selectProduct = (product: any) => {
    setSelectedProduct(product);
    // Calculate current markup for this product
    if (product.unit_cost && product.unit_cost > 0) {
      const currentPrice = product.override_price || product.retail_price;
      const currentMarkup = ((currentPrice - product.unit_cost) / product.unit_cost) * 100;
      setMarkupValue(Math.round(currentMarkup));
    }
  };

  if (!currentStore) {
    return (
      <div className="bg-white rounded-lg p-6">
        <div className="text-center text-gray-500">
          Please select a store to manage pricing
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Instructions */}
      <div className="bg-white rounded-lg p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-2">Default Price Configuration</h2>
        <p className="text-sm text-gray-600 mb-4">
          Set markup percentages for products by category. The markup is applied to the unit cost to calculate the retail price.
          More specific settings override general ones (e.g., sub-category overrides category).
        </p>

        {/* Store-wide Default Markup Setting */}
        <div className={`mb-6 p-4 border rounded-lg transition-all ${
          settingsUpdateSuccess ? 'bg-green-50 border-green-400' : 'bg-gray-50 border-gray-200'
        }`}>
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <h3 className="text-sm font-semibold text-gray-900 mb-2 flex items-center">
                Store-wide Default Markup
                {settingsUpdateSuccess && (
                  <CheckCircle className="ml-2 h-4 w-4 text-green-600 animate-bounce" />
                )}
              </h3>
              <div className="flex items-center space-x-4">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={defaultMarkupEnabled}
                    onChange={(e) => setDefaultMarkupEnabled(e.target.checked)}
                    className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                  />
                  <span className="ml-2 text-sm text-gray-700">Enable default markup</span>
                </label>

                <div className="flex items-center space-x-2">
                  <label className="text-sm text-gray-700">Default:</label>
                  <input
                    type="number"
                    value={storeDefaultMarkup}
                    onChange={(e) => setStoreDefaultMarkup(Number(e.target.value))}
                    disabled={!defaultMarkupEnabled}
                    min="0"
                    max="500"
                    className="w-20 px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
                  />
                  <span className="text-sm text-gray-700">%</span>
                </div>

                <button
                  onClick={() => updatePricingSettings.mutate({
                    default_markup_enabled: defaultMarkupEnabled,
                    default_markup_percentage: storeDefaultMarkup
                  })}
                  disabled={updatePricingSettings.isPending}
                  className="px-3 py-1 text-sm bg-primary-600 text-white rounded hover:bg-primary-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
                >
                  {updatePricingSettings.isPending ? 'Saving...' : 'Save Default'}
                </button>
              </div>
              <p className="mt-2 text-xs text-gray-500">
                This default markup will be used when calculating prices for new products or when no specific category markup is set.
              </p>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <label className="text-sm font-medium text-gray-700">Quick Set Markup:</label>
            <button
              onClick={() => setMarkupValue(20)}
              className="px-3 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded"
            >
              20%
            </button>
            <button
              onClick={() => setMarkupValue(storeDefaultMarkup)}
              className="px-3 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded"
            >
              Default
            </button>
            <button
              onClick={() => setMarkupValue(30)}
              className="px-3 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded"
            >
              30%
            </button>
            <button
              onClick={() => setMarkupValue(35)}
              className="px-3 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded"
            >
              35%
            </button>
            <button
              onClick={() => setMarkupValue(40)}
              className="px-3 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded"
            >
              40%
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Category Tree */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-lg">
            <div className="p-4 border-b">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
                <input
                  type="text"
                  placeholder="Search categories..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>
            </div>

            <div className="p-4">
              {isLoading ? (
                <div className="text-center py-8 text-gray-500">Loading categories...</div>
              ) : (
                <div className="space-y-2">
                  {/* All Products Option */}
                  <div
                    onClick={() => selectCategory(null)}
                    className={`p-3 rounded-lg cursor-pointer transition-colors ${
                      !selectedCategory ? 'bg-primary-50 border-2 border-primary-500' : 'hover:bg-gray-50 border border-gray-200'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="font-medium text-gray-900">All Products</div>
                      <div className="text-sm text-gray-500">Store-wide default</div>
                    </div>
                  </div>

                  {/* Category Tree */}
                  {Object.entries(categoriesData || {}).map(([category, catData]: [string, any]) => {
                    const isExpanded = expandedCategories.has(category);
                    const isSelected = selectedCategory === category && !selectedSubCategory;

                    if (searchTerm && !category.toLowerCase().includes(searchTerm.toLowerCase())) {
                      return null;
                    }

                    return (
                      <div key={category} className="border border-gray-200 rounded-lg">
                        <div
                          className={`p-3 cursor-pointer transition-colors ${
                            isSelected ? 'bg-primary-50 border-l-4 border-primary-500' : 'hover:bg-gray-50'
                          }`}
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-2">
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  toggleCategory(category);
                                }}
                                className="p-1 hover:bg-gray-200 rounded"
                              >
                                {isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                              </button>
                              <div
                                onClick={() => selectCategory(category)}
                                className="flex-1"
                              >
                                <span className="font-medium text-gray-900">{category}</span>
                                <span className="ml-2 text-sm text-gray-500">
                                  ({catData.product_count} products)
                                </span>
                                {catData.override_count > 0 && (
                                  <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-yellow-100 text-yellow-800">
                                    {catData.override_count} overrides
                                  </span>
                                )}
                              </div>
                            </div>
                            <div className="text-sm text-gray-600">
                              Avg: {Math.round(catData.avg_markup || storeDefaultMarkup)}%
                            </div>
                          </div>
                        </div>

                        {/* Subcategories */}
                        {isExpanded && catData.subcategories && (
                          <div className="pl-8 pr-3 pb-3">
                            {Object.entries(catData.subcategories).map(([subCategory, subData]: [string, any]) => {
                              const subKey = `${category}-${subCategory}`;
                              const isSubExpanded = expandedSubCategories.has(subKey);
                              const isSubSelected = selectedCategory === category && selectedSubCategory === subCategory && !selectedSubSubCategory;

                              return (
                                <div key={subCategory} className="mt-2">
                                  <div
                                    className={`p-2 rounded cursor-pointer transition-colors ${
                                      isSubSelected ? 'bg-primary-50 border-l-4 border-primary-400' : 'hover:bg-gray-50'
                                    }`}
                                  >
                                    <div className="flex items-center justify-between">
                                      <div className="flex items-center space-x-2">
                                        {subData.subsubcategories && Object.keys(subData.subsubcategories).length > 0 && (
                                          <button
                                            onClick={(e) => {
                                              e.stopPropagation();
                                              toggleSubCategory(subKey);
                                            }}
                                            className="p-1 hover:bg-gray-200 rounded"
                                          >
                                            {isSubExpanded ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
                                          </button>
                                        )}
                                        <div
                                          onClick={() => selectCategory(category, subCategory)}
                                          className="flex-1"
                                        >
                                          <span className="text-sm text-gray-800">{subCategory}</span>
                                          <span className="ml-2 text-xs text-gray-500">
                                            ({subData.product_count})
                                          </span>
                                          {subData.override_count > 0 && (
                                            <span className="ml-2 inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-yellow-100 text-yellow-700">
                                              {subData.override_count}
                                            </span>
                                          )}
                                        </div>
                                      </div>
                                      <div className="text-xs text-gray-600">
                                        {Math.round(subData.avg_markup || storeDefaultMarkup)}%
                                      </div>
                                    </div>
                                  </div>

                                  {/* Sub-subcategories */}
                                  {isSubExpanded && subData.subsubcategories && (
                                    <div className="pl-8 mt-1">
                                      {Object.entries(subData.subsubcategories).map(([subSubCategory, subSubData]: [string, any]) => {
                                        const isSubSubSelected = selectedCategory === category && selectedSubCategory === subCategory && selectedSubSubCategory === subSubCategory;

                                        return (
                                          <div key={subSubCategory}>
                                            <div
                                              onClick={() => selectCategory(category, subCategory, subSubCategory)}
                                              className={`p-2 mt-1 rounded cursor-pointer transition-colors ${
                                                isSubSubSelected ? 'bg-primary-50 border-l-4 border-primary-300' : 'hover:bg-gray-50'
                                              }`}
                                            >
                                              <div className="flex items-center justify-between">
                                                <div>
                                                  <span className="text-xs text-gray-700">{subSubCategory}</span>
                                                  <span className="ml-2 text-xs text-gray-500">
                                                    ({subSubData.product_count})
                                                  </span>
                                                  {subSubData.override_count > 0 && (
                                                    <span className="ml-2 inline-flex items-center px-1 py-0.5 rounded text-xs font-medium bg-yellow-100 text-yellow-600">
                                                      {subSubData.override_count}
                                                    </span>
                                                  )}
                                                </div>
                                                <div className="text-xs text-gray-600">
                                                  {Math.round(subSubData.avg_markup)}%
                                                </div>
                                              </div>
                                            </div>

                                            {/* Products List */}
                                            {isSubSubSelected && showProducts && (
                                              <div className="mt-2 ml-4 p-3 bg-gray-50 rounded-lg">
                                                {productsLoading ? (
                                                  <div className="text-center py-4 text-sm text-gray-500">Loading products...</div>
                                                ) : productsData && productsData.length > 0 ? (
                                                  <div className="space-y-2">
                                                    <div className="text-xs font-semibold text-gray-600 mb-2">Products in this category:</div>
                                                    {productsData.map((product: any) => {
                                                      const isProductSelected = selectedProduct?.sku === product.sku;
                                                      return (
                                                        <div
                                                          key={product.sku}
                                                          onClick={() => selectProduct(product)}
                                                          className={`bg-white p-3 rounded border cursor-pointer transition-all ${
                                                            isProductSelected
                                                              ? 'border-primary-500 bg-primary-50 ring-2 ring-primary-200'
                                                              : 'border-gray-200 hover:border-primary-300 hover:shadow-sm'
                                                          }`}
                                                        >
                                                          <div className="flex items-start space-x-3">
                                                            {/* Product Image */}
                                                            <div className="flex-shrink-0">
                                                              {product.image_url ? (
                                                                <img
                                                                  src={product.image_url}
                                                                  alt={product.product_name}
                                                                  className="h-12 w-12 object-cover rounded"
                                                                  onError={(e) => {
                                                                    (e.target as HTMLImageElement).src = 'https://via.placeholder.com/48x48?text=No+Image';
                                                                  }}
                                                                />
                                                              ) : (
                                                                <div className="h-12 w-12 bg-gray-100 rounded flex items-center justify-center">
                                                                  <Package className="h-6 w-6 text-gray-400" />
                                                                </div>
                                                              )}
                                                            </div>

                                                            {/* Product Details */}
                                                            <div className="flex-1 min-w-0">
                                                              <div className="flex items-start justify-between">
                                                                <div className="flex-1">
                                                                  <div className="text-sm font-medium text-gray-900 truncate">
                                                                    {product.product_name || product.sku}
                                                                  </div>
                                                                  <div className="mt-1 flex items-center space-x-3 text-xs text-gray-500">
                                                                    <span>SKU: {product.sku}</span>
                                                                    <span>•</span>
                                                                    <span>Stock: {product.quantity_available || 0}</span>
                                                                    {product.brand && (
                                                                      <>
                                                                        <span>•</span>
                                                                        <span>Brand: {product.brand}</span>
                                                                      </>
                                                                    )}
                                                                  </div>
                                                                </div>
                                                                <div className="text-right">
                                                                  <div className="text-sm font-semibold text-gray-900">
                                                                    ${(product.override_price || product.retail_price)?.toFixed(2) || '0.00'}
                                                                  </div>
                                                                  <div className="text-xs text-gray-500">
                                                                    Cost: ${product.unit_cost?.toFixed(2) || '0.00'}
                                                                  </div>
                                                                  {/* Markup Badge */}
                                                                  <div className="mt-1">
                                                                    {(() => {
                                                                      const currentPrice = product.override_price || product.retail_price;
                                                                      const markup = product.unit_cost > 0
                                                                        ? Math.round(((currentPrice - product.unit_cost) / product.unit_cost) * 100)
                                                                        : 0;
                                                                      const hasOverride = !!product.override_price;
                                                                      return (
                                                                        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-bold ${
                                                                          hasOverride
                                                                            ? 'bg-yellow-100 text-yellow-800 border border-yellow-300'
                                                                            : 'bg-blue-100 text-blue-800'
                                                                        }`}>
                                                                          {markup}%
                                                                          {hasOverride && (
                                                                            <span className="ml-1 text-yellow-600">✓</span>
                                                                          )}
                                                                        </span>
                                                                      );
                                                                    })()}
                                                                  </div>
                                                                </div>
                                                              </div>
                                                            </div>
                                                          </div>
                                                        </div>
                                                      );
                                                    })}
                                                  </div>
                                                ) : (
                                                  <div className="text-center py-4 text-sm text-gray-500">No products found</div>
                                                )}
                                              </div>
                                            )}
                                          </div>
                                        );
                                      })}
                                    </div>
                                  )}
                                </div>
                              );
                            })}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Pricing Control Panel */}
        <div className="lg:col-span-1">
          <div className={`bg-white rounded-lg p-6 sticky top-6 transition-all duration-500 ${
            updateSuccess ? 'ring-4 ring-green-400 ring-opacity-50 scale-[1.02]' : ''
          }`}>
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center justify-between">
              <span>Apply Markup</span>
              {updateSuccess && (
                <span className="text-green-600 animate-bounce">
                  <CheckCircle className="h-6 w-6" />
                </span>
              )}
            </h3>

            {/* Selected Category Info */}
            <div className={`mb-6 p-4 rounded-lg transition-all duration-300 ${
              updatePricing.isPending
                ? 'bg-yellow-50 border-2 border-yellow-400 animate-pulse'
                : updateSuccess
                ? 'bg-green-50 border-2 border-green-400'
                : 'bg-gray-50'
            }`}>
              <div className="text-sm text-gray-600 mb-1">
                {updatePricing.isPending ? 'Updating:' : 'Applying to:'}
              </div>
              <div className="font-medium text-gray-900">
                {selectedProduct ? (
                  <div>
                    <div className="flex items-center space-x-2 mb-2">
                      {selectedProduct.image_url ? (
                        <img
                          src={selectedProduct.image_url}
                          alt={selectedProduct.product_name}
                          className="h-8 w-8 object-cover rounded"
                          onError={(e) => {
                            (e.target as HTMLImageElement).src = 'https://via.placeholder.com/32x32?text=No+Image';
                          }}
                        />
                      ) : (
                        <div className="h-8 w-8 bg-gray-100 rounded flex items-center justify-center">
                          <Package className="h-4 w-4 text-gray-400" />
                        </div>
                      )}
                      <div>
                        <div className="text-sm font-medium">{selectedProduct.product_name || selectedProduct.sku}</div>
                        <div className="text-xs text-gray-500">SKU: {selectedProduct.sku}</div>
                      </div>
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      {selectedCategory} → {selectedSubCategory} → {selectedSubSubCategory}
                    </div>
                  </div>
                ) : selectedSubSubCategory ? (
                  <div>
                    <div>{selectedCategory}</div>
                    <div className="text-sm text-gray-600">→ {selectedSubCategory}</div>
                    <div className="text-sm text-gray-600">→ {selectedSubSubCategory}</div>
                  </div>
                ) : selectedSubCategory ? (
                  <div>
                    <div>{selectedCategory}</div>
                    <div className="text-sm text-gray-600">→ {selectedSubCategory}</div>
                  </div>
                ) : selectedCategory ? (
                  selectedCategory
                ) : (
                  'All Products (Store-wide)'
                )}
              </div>
            </div>

            {/* Markup Input */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Markup Percentage
              </label>
              <div className="flex items-center space-x-2">
                <input
                  type="number"
                  min="0"
                  max="500"
                  value={markupValue}
                  onChange={(e) => setMarkupValue(parseFloat(e.target.value) || 0)}
                  className="flex-1 px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
                <span className="text-gray-600">%</span>
              </div>
              <div className="mt-2 text-xs text-gray-500">
                Retail Price = Cost × (1 + {markupValue}%)
              </div>
            </div>

            {/* Price Preview */}
            <div className="mb-6 p-4 bg-blue-50 rounded-lg">
              <div className="text-sm font-medium text-blue-900 mb-2">Example Calculation:</div>
              <div className="text-sm text-blue-700">
                {selectedProduct && selectedProduct.unit_cost ? (
                  <>
                    <div>Current cost = ${selectedProduct.unit_cost.toFixed(2)}</div>
                    <div>Current retail = ${(selectedProduct.override_price || selectedProduct.retail_price)?.toFixed(2) || '0.00'}</div>
                    <div className="mt-2 pt-2 border-t border-blue-200">
                      <div className="font-medium">New pricing with {markupValue}% markup:</div>
                      <div>New retail price = ${(selectedProduct.unit_cost * (1 + markupValue / 100)).toFixed(2)}</div>
                      <div className="mt-1">
                        Profit margin: ${(selectedProduct.unit_cost * (markupValue / 100)).toFixed(2)} ({markupValue}%)
                      </div>
                      {selectedProduct.retail_price && (
                        <div className="mt-1 text-xs">
                          Price change: {
                            ((selectedProduct.unit_cost * (1 + markupValue / 100)) - selectedProduct.retail_price) > 0
                              ? `+$${((selectedProduct.unit_cost * (1 + markupValue / 100)) - selectedProduct.retail_price).toFixed(2)}`
                              : `-$${Math.abs((selectedProduct.unit_cost * (1 + markupValue / 100)) - selectedProduct.retail_price).toFixed(2)}`
                          }
                        </div>
                      )}
                    </div>
                  </>
                ) : (
                  <>
                    <div>If cost = $10.00</div>
                    <div>Retail price = ${(10 * (1 + markupValue / 100)).toFixed(2)}</div>
                    <div className="mt-1 font-medium">
                      Profit margin: ${(10 * (markupValue / 100)).toFixed(2)} ({markupValue}%)
                    </div>
                  </>
                )}
              </div>
            </div>

            {/* Apply Button */}
            <button
              onClick={handleApplyMarkup}
              disabled={updatePricing.isPending || updateSuccess}
              className={`w-full px-4 py-3 rounded-lg font-medium transition-all transform duration-300 ${
                updateSuccess
                  ? 'bg-green-500 text-white scale-105 shadow-lg'
                  : updatePricing.isPending
                  ? 'bg-gray-400 text-white cursor-not-allowed'
                  : 'bg-primary-600 text-white hover:bg-primary-700 hover:scale-[1.02] hover:shadow-md active:scale-[0.98]'
              }`}
            >
              {updateSuccess ? (
                <span className="flex items-center justify-center">
                  <CheckCircle className="mr-2 h-5 w-5" />
                  Updated Successfully!
                </span>
              ) : updatePricing.isPending ? (
                <span className="flex items-center justify-center">
                  <svg className="animate-spin h-5 w-5 mr-2" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Updating Prices...
                </span>
              ) : (
                <span className="flex items-center justify-center">
                  <Percent className="mr-2 h-5 w-5" />
                  Apply Markup
                </span>
              )}
            </button>

            {/* Reset Override Button */}
            <button
              onClick={handleResetOverrides}
              disabled={resetOverrides.isPending}
              className="w-full mt-3 px-4 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-all duration-200 font-medium disabled:bg-gray-300 disabled:cursor-not-allowed"
            >
              {resetOverrides.isPending ? (
                <span className="flex items-center justify-center">
                  <svg className="animate-spin h-5 w-5 mr-2" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Resetting...
                </span>
              ) : (
                <span className="flex items-center justify-center">
                  <RotateCcw className="mr-2 h-5 w-5" />
                  Reset Overrides
                </span>
              )}
            </button>

            {/* Warning for store-wide updates */}
            {!selectedCategory && !selectedProduct && (
              <div className="mt-4 p-3 bg-warning-50 border border-warning-200 rounded-lg">
                <div className="text-sm text-warning-800">
                  <strong>Warning:</strong> This will update pricing for all products in the store.
                </div>
              </div>
            )}

            {/* Info for single product update */}
            {selectedProduct && (
              <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <div className="text-sm text-blue-800">
                  <strong>Note:</strong> Only this specific product will be updated.
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}