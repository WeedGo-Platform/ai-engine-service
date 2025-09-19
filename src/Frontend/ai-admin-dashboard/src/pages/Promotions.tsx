import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  Plus, Edit2, Trash2, Calendar, DollarSign, 
  Tag, Users, TrendingUp, Package, Copy, CheckCircle 
} from 'lucide-react';
import { format } from 'date-fns';
import axios from 'axios';
import toast from 'react-hot-toast';

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
  const [activeTab, setActiveTab] = useState<'promotions' | 'tiers' | 'analytics'>('promotions');
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