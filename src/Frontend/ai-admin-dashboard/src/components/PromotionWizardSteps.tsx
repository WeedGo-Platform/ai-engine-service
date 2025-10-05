import React from 'react';
import { CheckCircle } from 'lucide-react';

interface StepProps {
  formData: any;
  setFormData: (data: any) => void;
  stores?: any[];
  tenants?: any[];
  selectedStores: string[];
  toggleStore: (id: string) => void;
  setSelectedStores: (stores: string[]) => void;
  selectedTenant: string | null;
  setSelectedTenant: (id: string | null) => void;
  userRole: 'platform_admin' | 'tenant_admin' | 'store_manager';
  currentStore?: any;
  toggleDayOfWeek: (day: number) => void;
}

// Step 1: Basic Info
export const Step1BasicInfo: React.FC<StepProps> = ({ formData, setFormData }) => (
  <div className="space-y-6 animate-fadeIn">
    <div>
      <h3 className="text-lg font-semibold text-gray-900 mb-2">Basic Information</h3>
      <p className="text-sm text-gray-600">Start by giving your promotion a name and description</p>
    </div>

    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div className="md:col-span-2">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Promotion Name *
        </label>
        <input
          type="text"
          required
          value={formData.name}
          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          placeholder="e.g., Summer Sale 2025"
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Promo Code (Optional)
        </label>
        <input
          type="text"
          value={formData.code}
          onChange={(e) => setFormData({ ...formData, code: e.target.value.toUpperCase() })}
          placeholder="e.g., SUMMER25"
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Priority (0-100)
        </label>
        <input
          type="number"
          min="0"
          max="100"
          value={formData.priority || 0}
          onChange={(e) => setFormData({ ...formData, priority: parseInt(e.target.value) || 0 })}
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
        />
      </div>

      <div className="md:col-span-2">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Description (Optional)
        </label>
        <textarea
          value={formData.description}
          onChange={(e) => setFormData({ ...formData, description: e.target.value })}
          rows={3}
          placeholder="Describe what this promotion offers..."
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all resize-none"
        />
      </div>
    </div>
  </div>
);

// Step 2: Discount Details
export const Step2Discount: React.FC<StepProps> = ({ formData, setFormData }) => (
  <div className="space-y-6 animate-fadeIn">
    <div>
      <h3 className="text-lg font-semibold text-gray-900 mb-2">Discount Details</h3>
      <p className="text-sm text-gray-600">Configure the discount type and value</p>
    </div>

    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Promotion Type *
        </label>
        <select
          value={formData.type}
          onChange={(e) => setFormData({ ...formData, type: e.target.value })}
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
        >
          <option value="percentage">Percentage Discount</option>
          <option value="fixed_amount">Fixed Amount</option>
          <option value="bogo">Buy One Get One</option>
          <option value="bundle">Bundle Deal</option>
          <option value="tiered">Tiered Discount</option>
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Discount Type *
        </label>
        <select
          value={formData.discount_type}
          onChange={(e) => setFormData({ ...formData, discount_type: e.target.value })}
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
        >
          <option value="percentage">Percentage (%)</option>
          <option value="amount">Fixed Amount ($)</option>
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Discount Value *
        </label>
        <div className="relative">
          <input
            type="number"
            required
            min="0"
            step="0.01"
            value={formData.discount_value}
            onChange={(e) => setFormData({ ...formData, discount_value: e.target.value ? parseFloat(e.target.value) : 0 })}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
          />
          <span className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-500">
            {formData.discount_type === 'percentage' ? '%' : '$'}
          </span>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Minimum Purchase
        </label>
        <input
          type="number"
          min="0"
          step="0.01"
          value={formData.min_purchase_amount || ''}
          onChange={(e) => setFormData({ ...formData, min_purchase_amount: e.target.value ? parseFloat(e.target.value) : undefined })}
          placeholder="Optional"
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
        />
      </div>

      {formData.discount_type === 'percentage' && (
        <div className="md:col-span-2">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Maximum Discount Amount
          </label>
          <input
            type="number"
            min="0"
            step="0.01"
            value={formData.max_discount_amount || ''}
            onChange={(e) => setFormData({ ...formData, max_discount_amount: e.target.value ? parseFloat(e.target.value) : undefined })}
            placeholder="Optional - Cap the discount amount"
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
          />
        </div>
      )}
    </div>
  </div>
);

// Step 3: Scope & Schedule
export const Step3Scope: React.FC<StepProps> = ({
  formData,
  setFormData,
  stores,
  tenants,
  selectedStores,
  toggleStore,
  setSelectedStores,
  selectedTenant,
  setSelectedTenant,
  userRole,
  currentStore,
  toggleDayOfWeek
}) => (
  <div className="space-y-6 animate-fadeIn">
    <div>
      <h3 className="text-lg font-semibold text-gray-900 mb-2">Scope & Schedule</h3>
      <p className="text-sm text-gray-600">Define where and when this promotion applies</p>
    </div>

    {/* Tenant Selection (Platform Admin Only) */}
    {userRole === 'platform_admin' && (
      <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <label className="block text-sm font-medium text-gray-900 mb-2">
          Tenant (Optional)
        </label>
        <select
          value={selectedTenant || ''}
          onChange={(e) => setSelectedTenant(e.target.value || null)}
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
        >
          <option value="">All Tenants (Global)</option>
          {tenants?.map((tenant) => (
            <option key={tenant.id} value={tenant.id}>{tenant.name}</option>
          ))}
        </select>
        <p className="mt-2 text-xs text-gray-600">
          Leave blank to apply globally, or select a specific tenant
        </p>
      </div>
    )}

    {/* Store Selection (Platform Admin & Tenant Admin) */}
    {(userRole === 'platform_admin' || userRole === 'tenant_admin') && (
      <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
        <label className="block text-sm font-medium text-gray-900 mb-3">
          Stores
        </label>
        <div className="space-y-2 max-h-48 overflow-y-auto">
          <label className="flex items-center p-3 bg-white rounded-lg hover:bg-gray-50 cursor-pointer transition-colors">
            <input
              type="checkbox"
              checked={selectedStores.length === 0}
              onChange={() => setSelectedStores([])}
              className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
            />
            <span className="ml-3 text-sm font-medium text-gray-900">All Stores</span>
          </label>
          {stores?.map((store) => (
            <label key={store.id} className="flex items-center p-3 bg-white rounded-lg hover:bg-gray-50 cursor-pointer transition-colors">
              <input
                type="checkbox"
                checked={selectedStores.includes(store.id)}
                onChange={() => toggleStore(store.id)}
                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
              />
              <span className="ml-3 text-sm text-gray-900">{store.name} ({store.store_code})</span>
            </label>
          ))}
        </div>
      </div>
    )}

    {/* Store Context Display (Store Manager) */}
    {userRole === 'store_manager' && currentStore && (
      <div className="p-4 bg-gray-50 border border-gray-300 rounded-lg">
        <label className="block text-sm font-medium text-gray-700 mb-2">Store</label>
        <div className="flex items-center p-3 bg-white rounded-lg">
          <CheckCircle className="h-5 w-5 text-green-600" />
          <span className="ml-3 text-sm font-medium text-gray-900">
            {currentStore.name} ({currentStore.store_code})
          </span>
        </div>
        <p className="mt-2 text-xs text-gray-600">Promotion will apply to your store only</p>
      </div>
    )}

    {/* Date Range */}
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Start Date *
        </label>
        <input
          type="datetime-local"
          required
          value={formData.start_date ? formData.start_date.slice(0, 16) : ''}
          onChange={(e) => setFormData({ ...formData, start_date: new Date(e.target.value).toISOString() })}
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          End Date
        </label>
        <input
          type="datetime-local"
          value={formData.end_date ? formData.end_date.slice(0, 16) : ''}
          onChange={(e) => setFormData({ ...formData, end_date: e.target.value ? new Date(e.target.value).toISOString() : undefined })}
          disabled={formData.is_continuous}
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:bg-gray-100"
        />
      </div>
    </div>

    {/* Continuous & Recurrence */}
    <div className="space-y-4 p-4 bg-purple-50 border border-purple-200 rounded-lg">
      <label className="flex items-center">
        <input
          type="checkbox"
          checked={formData.is_continuous}
          onChange={(e) => setFormData({
            ...formData,
            is_continuous: e.target.checked,
            end_date: e.target.checked ? undefined : formData.end_date
          })}
          className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
        />
        <span className="ml-3 text-sm font-medium text-gray-900">Continuous (No End Date)</span>
      </label>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Recurrence
        </label>
        <select
          value={formData.recurrence_type}
          onChange={(e) => setFormData({ ...formData, recurrence_type: e.target.value })}
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
        >
          <option value="none">No Recurrence</option>
          <option value="daily">Daily</option>
          <option value="weekly">Weekly (Specific Days)</option>
        </select>
      </div>

      {formData.recurrence_type === 'weekly' && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Days of Week</label>
          <div className="flex flex-wrap gap-2">
            {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((day, idx) => (
              <button
                key={day}
                type="button"
                onClick={() => toggleDayOfWeek(idx)}
                className={`px-4 py-2 rounded-lg font-medium transition-all ${
                  (formData.day_of_week || []).includes(idx)
                    ? 'bg-primary-600 text-white shadow-md'
                    : 'bg-white text-gray-700 border border-gray-300 hover:border-primary-500'
                }`}
              >
                {day}
              </button>
            ))}
          </div>
        </div>
      )}

      {(formData.recurrence_type === 'daily' || formData.recurrence_type === 'weekly') && (
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm text-gray-700 mb-1">Start Time</label>
            <input
              type="time"
              value={formData.time_start || ''}
              onChange={(e) => setFormData({ ...formData, time_start: e.target.value || undefined })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-700 mb-1">End Time</label>
            <input
              type="time"
              value={formData.time_end || ''}
              onChange={(e) => setFormData({ ...formData, time_end: e.target.value || undefined })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
        </div>
      )}
    </div>
  </div>
);

// Step 4: Settings
export const Step4Settings: React.FC<StepProps> = ({ formData, setFormData }) => (
  <div className="space-y-6 animate-fadeIn">
    <div>
      <h3 className="text-lg font-semibold text-gray-900 mb-2">Additional Settings</h3>
      <p className="text-sm text-gray-600">Configure usage limits and preferences</p>
    </div>

    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Total Usage Limit
        </label>
        <input
          type="number"
          min="0"
          value={formData.total_usage_limit || ''}
          onChange={(e) => setFormData({ ...formData, total_usage_limit: e.target.value ? parseInt(e.target.value) : undefined })}
          placeholder="Unlimited"
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Per Customer Limit
        </label>
        <input
          type="number"
          min="0"
          value={formData.usage_limit_per_customer || ''}
          onChange={(e) => setFormData({ ...formData, usage_limit_per_customer: e.target.value ? parseInt(e.target.value) : undefined })}
          placeholder="Unlimited"
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
        />
      </div>
    </div>

    <div className="space-y-3 p-4 bg-gray-50 rounded-lg">
      <label className="flex items-center">
        <input
          type="checkbox"
          checked={formData.stackable}
          onChange={(e) => setFormData({ ...formData, stackable: e.target.checked })}
          className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
        />
        <span className="ml-3 text-sm text-gray-900">Allow stacking with other promotions</span>
      </label>

      <label className="flex items-center">
        <input
          type="checkbox"
          checked={formData.first_time_customer_only}
          onChange={(e) => setFormData({ ...formData, first_time_customer_only: e.target.checked })}
          className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
        />
        <span className="ml-3 text-sm text-gray-900">First-time customers only</span>
      </label>

      <label className="flex items-center">
        <input
          type="checkbox"
          checked={formData.active}
          onChange={(e) => setFormData({ ...formData, active: e.target.checked })}
          className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
        />
        <span className="ml-3 text-sm text-gray-900">Active</span>
      </label>
    </div>
  </div>
);

// Step 5: Review
export const Step5Review: React.FC<StepProps> = ({ formData, selectedStores, stores, selectedTenant, tenants, userRole, currentStore }) => {
  const getStoreNames = () => {
    if (userRole === 'store_manager') {
      return currentStore ? [currentStore.name] : [];
    }
    if (selectedStores.length === 0) return ['All Stores'];
    return selectedStores.map(id => stores?.find(s => s.id === id)?.name || id);
  };

  const getTenantName = () => {
    if (!selectedTenant) return 'All Tenants';
    return tenants?.find(t => t.id === selectedTenant)?.name || selectedTenant;
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Review & Confirm</h3>
        <p className="text-sm text-gray-600">Review all details before creating the promotion</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="p-4 bg-gray-50 rounded-lg">
          <h4 className="text-sm font-semibold text-gray-900 mb-3">Basic Info</h4>
          <dl className="space-y-2">
            <div>
              <dt className="text-xs text-gray-600">Name</dt>
              <dd className="text-sm font-medium text-gray-900">{formData.name}</dd>
            </div>
            {formData.code && (
              <div>
                <dt className="text-xs text-gray-600">Code</dt>
                <dd className="text-sm font-medium text-gray-900">{formData.code}</dd>
              </div>
            )}
          </dl>
        </div>

        <div className="p-4 bg-gray-50 rounded-lg">
          <h4 className="text-sm font-semibold text-gray-900 mb-3">Discount</h4>
          <dl className="space-y-2">
            <div>
              <dt className="text-xs text-gray-600">Value</dt>
              <dd className="text-sm font-medium text-gray-900">
                {formData.discount_type === 'percentage' ? `${formData.discount_value}%` : `$${formData.discount_value}`}
              </dd>
            </div>
            {formData.min_purchase_amount && (
              <div>
                <dt className="text-xs text-gray-600">Min Purchase</dt>
                <dd className="text-sm font-medium text-gray-900">${formData.min_purchase_amount}</dd>
              </div>
            )}
          </dl>
        </div>

        <div className="p-4 bg-gray-50 rounded-lg">
          <h4 className="text-sm font-semibold text-gray-900 mb-3">Scope</h4>
          <dl className="space-y-2">
            {userRole === 'platform_admin' && (
              <div>
                <dt className="text-xs text-gray-600">Tenant</dt>
                <dd className="text-sm font-medium text-gray-900">{getTenantName()}</dd>
              </div>
            )}
            <div>
              <dt className="text-xs text-gray-600">Stores</dt>
              <dd className="text-sm font-medium text-gray-900">{getStoreNames().join(', ')}</dd>
            </div>
          </dl>
        </div>

        <div className="p-4 bg-gray-50 rounded-lg">
          <h4 className="text-sm font-semibold text-gray-900 mb-3">Schedule</h4>
          <dl className="space-y-2">
            <div>
              <dt className="text-xs text-gray-600">Duration</dt>
              <dd className="text-sm font-medium text-gray-900">
                {formData.is_continuous ? 'Continuous' : formData.end_date ? 'Limited' : 'No end date'}
              </dd>
            </div>
            {formData.recurrence_type !== 'none' && (
              <div>
                <dt className="text-xs text-gray-600">Recurrence</dt>
                <dd className="text-sm font-medium text-gray-900 capitalize">{formData.recurrence_type}</dd>
              </div>
            )}
          </dl>
        </div>
      </div>
    </div>
  );
};
