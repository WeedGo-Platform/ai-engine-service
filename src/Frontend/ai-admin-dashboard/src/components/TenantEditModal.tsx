import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
  X, Building2, Mail, Phone, Globe, CreditCard, Package,
  MapPin, Upload, Save, Users, UserPlus, Lock,
  Ban, UserX, RefreshCw, Check, Star, Store,
  Leaf, Rocket, Crown, TrendingUp, CheckCircle, AlertTriangle, XCircle
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { getApiEndpoint } from '../config/app.config';
import tenantService from '../services/tenantService';

// Subscription plans configuration with Lucide icons
const subscriptionPlans = {
  'community_and_new_business': {
    name: 'Community & New Business',
    maxStores: 1,
    maxLanguages: 2,
    maxAiPersonalities: 1,
    price: 'FREE',
    priceValue: 0,
    features: ['1 Store Location', '2 Languages (EN/FR)', '1 AI Personality', 'Basic POS System', 'Standard Support'],
    color: 'bg-blue-50 border-blue-200',
    iconComponent: Leaf,
    iconColor: 'text-blue-600'
  },
  'small_business': {
    name: 'Small Business',
    maxStores: 5,
    maxLanguages: 5,
    maxAiPersonalities: 2,
    price: '$99/month',
    priceValue: 99,
    features: ['5 Store Locations', '5 Languages', '2 AI Personalities per store', 'Advanced POS + KIOSK', 'Delivery Management', 'Priority Support'],
    color: 'bg-green-50 border-green-200',
    iconComponent: TrendingUp,
    iconColor: 'text-green-600'
  },
  'professional_and_growing_business': {
    name: 'Professional & Growing',
    maxStores: 12,
    maxLanguages: 10,
    maxAiPersonalities: 3,
    price: '$149/month',
    priceValue: 149,
    features: ['12 Store Locations', '10 Languages', '3 AI Personalities per store', 'Full Platform Access', 'Voice Age Verification', 'Fraud Protection', '24/7 Support'],
    color: 'bg-purple-50 border-purple-200',
    iconComponent: Rocket,
    iconColor: 'text-purple-600',
    isPopular: true
  },
  'enterprise': {
    name: 'Enterprise',
    maxStores: 999,
    maxLanguages: 25,
    maxAiPersonalities: 5,
    price: '$299/month',
    priceValue: 299,
    features: ['Unlimited Stores', '25+ Languages', '5 AI Personalities per store', 'Full API Access', 'White Label Options', 'Dedicated Account Manager', 'Custom Training'],
    color: 'bg-gradient-to-r from-purple-50 to-blue-50 border-purple-300',
    iconComponent: Crown,
    iconColor: 'text-indigo-600'
  }
};

interface TenantEditModalProps {
  tenant: any;
  isOpen: boolean;
  onClose: () => void;
  onSave: (updatedTenant: any, logoFile?: File | null) => Promise<void>;
  readOnly?: boolean;
  showUsersTab?: boolean;
}

const TenantEditModal: React.FC<TenantEditModalProps> = ({
  tenant,
  isOpen,
  onClose,
  onSave,
  readOnly = false,
  showUsersTab = true
}) => {
  const { user: currentUser } = useAuth();
  const { t } = useTranslation(['common']);
  const [editedTenant, setEditedTenant] = useState(tenant);
  const [activeTab, setActiveTab] = useState('general');
  const [logoFile, setLogoFile] = useState<File | null>(null);
  const [logoPreview, setLogoPreview] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  
  // User management state
  const [tenantUsers, setTenantUsers] = useState<any[]>([]);
  const [loadingUsers, setLoadingUsers] = useState(false);
  const [userError, setUserError] = useState<string | null>(null);
  const [userSuccess, setUserSuccess] = useState<string | null>(null);
  const [showAddUserForm, setShowAddUserForm] = useState(false);
  const [newUser, setNewUser] = useState({
    email: '',
    first_name: '',
    last_name: '',
    role: 'staff',
    password: ''
  });

  useEffect(() => {
    setEditedTenant(tenant);
    setLogoPreview(tenant?.logo_url || null);
    if (activeTab === 'users' && tenant?.id && showUsersTab) {
      fetchTenantUsers();
    }
  }, [tenant, activeTab, showUsersTab]);

  const fetchTenantUsers = async () => {
    if (!tenant?.id) return;
    
    setLoadingUsers(true);
    setUserError(null);
    
    try {
      const response = await fetch(getApiEndpoint(`/tenants/${tenant.id}/users`));
      if (!response.ok) throw new Error('Failed to fetch users');
      const data = await response.json();
      setTenantUsers(data);
    } catch (err: any) {
      setUserError(err.message);
    } finally {
      setLoadingUsers(false);
    }
  };

  const handleAddUser = async () => {
    setUserError(null);
    setUserSuccess(null);
    
    try {
      await tenantService.createTenantUser(tenant.id, newUser);
      
      setUserSuccess('User added successfully');
      setShowAddUserForm(false);
      setNewUser({ email: '', first_name: '', last_name: '', role: 'staff', password: '' });
      fetchTenantUsers();
    } catch (err: any) {
      setUserError(err.response?.data?.detail || err.message || 'Failed to add user');
    }
  };

  const handleResetPassword = async (userId: string) => {
    setUserError(null);
    setUserSuccess(null);

    // Show options dialog
    const resetMethod = confirmToastAsync(t('common:confirmations.passwordResetMethod'));

    try {
      const response = await fetch(getApiEndpoint(`/tenants/${tenant.id}/users/${userId}/reset-password`), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ method: resetMethod ? 'email' : 'otp' })
      });
      
      if (!response.ok) throw new Error('Failed to reset password');
      const data = await response.json();
      
      if (resetMethod) {
        setUserSuccess('Password reset link sent to user\'s email');
      } else {
        setUserSuccess(`One-time password: ${data.temporary_password || data.otp}`);
      }
    } catch (err: any) {
      setUserError(err.message);
    }
  };

  const handleToggleUserStatus = async (userId: string, currentStatus: boolean) => {
    setUserError(null);
    setUserSuccess(null);
    
    try {
      const response = await fetch(getApiEndpoint(`/tenants/${tenant.id}/users/${userId}/toggle-active`), {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        }
      });
      
      if (!response.ok) throw new Error('Failed to update user status');
      
      const data = await response.json();
      setUserSuccess(data.message || `User ${!currentStatus ? 'activated' : 'blocked'} successfully`);
      fetchTenantUsers();
    } catch (err: any) {
      setUserError(err.message);
    }
  };

  const handleUpdateUserRole = async (userId: string, newRole: string) => {
    setUserError(null);
    setUserSuccess(null);
    
    try {
      const response = await fetch(getApiEndpoint(`/tenants/${tenant.id}/users/${userId}`), {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ role: newRole })
      });
      
      if (!response.ok) throw new Error('Failed to update user role');
      
      setUserSuccess('User role updated successfully');
      fetchTenantUsers();
    } catch (err: any) {
      setUserError(err.message);
    }
  };

  const handleDeleteUser = async (userId: string) => {
    // Check if user is trying to delete themselves
    if (userId === currentUser?.user_id) {
      setUserError('You cannot delete your own account');
      return;
    }

    if (!confirmToastAsync(t('common:confirmations.deleteUserPermanent'))) return;

    setUserError(null);
    setUserSuccess(null);
    
    try {
      const response = await fetch(getApiEndpoint(`/tenants/${tenant.id}/users/${userId}`), {
        method: 'DELETE'
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to delete user');
      }
      
      setUserSuccess('User deleted successfully');
      fetchTenantUsers();
    } catch (err: any) {
      setUserError(err.message);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setLogoFile(file);
      
      const reader = new FileReader();
      reader.onloadend = () => {
        setLogoPreview(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await onSave(editedTenant, logoFile);
      onClose();
    } catch (error) {
      console.error('Failed to save tenant:', error);
    } finally {
      setIsSaving(false);
    }
  };

  if (!isOpen) return null;

  const tabs = [
    { id: 'general', label: 'General', icon: Building2 },
    { id: 'address', label: 'Address', icon: MapPin },
    { id: 'billing', label: 'Billing', icon: CreditCard },
    { id: 'subscription', label: 'Subscription', icon: Package },
    ...(showUsersTab ? [{ id: 'users', label: 'Admin Users', icon: Users }] : [])
  ];

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4">
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75" onClick={onClose}></div>

        <div className="relative bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 max-w-4xl w-full max-h-[85vh] overflow-hidden flex flex-col">
          <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              {readOnly ? 'View' : 'Edit'} Organization
            </h2>
            <button onClick={onClose} className="text-gray-400 hover:text-gray-500 dark:hover:text-gray-300">
              <X className="w-5 h-5" />
            </button>
          </div>

          <div className="border-b border-gray-200 dark:border-gray-700">
            <div className="flex space-x-1 px-4">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 px-4 py-2 border-b-2 transition-colors ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-accent-600 dark:text-accent-400'
                      : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                  }`}
                >
                  <tab.icon className="w-4 h-4" />
                  {tab.label}
                </button>
              ))}
            </div>
          </div>

          <div className="flex-1 p-6 overflow-y-auto" style={{ maxHeight: 'calc(85vh - 200px)' }}>
            {/* Tab content here - same as existing TenantManagement but with readOnly support */}
            {activeTab === 'general' && (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Organization Name
                    </label>
                    <input
                      type="text"
                      value={editedTenant?.name || ''}
                      onChange={(e) => setEditedTenant({ ...editedTenant, name: e.target.value })}
                      disabled={readOnly}
                      className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Organization Code
                    </label>
                    <input
                      type="text"
                      value={editedTenant?.code || ''}
                      disabled
                      className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-gray-50 dark:bg-gray-600 text-gray-900 dark:text-gray-300"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      <Mail className="inline w-4 h-4 mr-1" />
                      Contact Email
                    </label>
                    <input
                      type="email"
                      value={editedTenant?.contact_email || ''}
                      onChange={(e) => setEditedTenant({ ...editedTenant, contact_email: e.target.value })}
                      disabled={readOnly}
                      className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      <Phone className="inline w-4 h-4 mr-1" />
                      Contact Phone
                    </label>
                    <input
                      type="tel"
                      value={editedTenant?.contact_phone || ''}
                      onChange={(e) => setEditedTenant({ ...editedTenant, contact_phone: e.target.value })}
                      disabled={readOnly}
                      className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    <Globe className="inline w-4 h-4 mr-1" />
                    Website
                  </label>
                  <input
                    type="url"
                    value={editedTenant?.website || ''}
                    onChange={(e) => setEditedTenant({ ...editedTenant, website: e.target.value })}
                    disabled={readOnly}
                    className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  />
                </div>

                {!readOnly && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      <Upload className="inline w-4 h-4 mr-1" />
                      Logo
                    </label>
                    <div className="flex items-center gap-6">
                      {(logoPreview || editedTenant?.logo_url) && (
                        <img
                          src={logoPreview || (editedTenant.logo_url.startsWith('http') ? editedTenant.logo_url : `${import.meta.env.VITE_API_URL || 'http://localhost:5024'}${editedTenant.logo_url}`)}
                          alt="Logo"
                          className="w-16 h-16 object-contain border border-gray-200 dark:border-gray-600 rounded"
                        />
                      )}
                      <input
                        type="file"
                        accept="image/*"
                        onChange={handleFileChange}
                        className="flex-1 text-gray-900 dark:text-white"
                      />
                    </div>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'address' && (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Street</label>
                  <input
                    type="text"
                    value={editedTenant?.address?.street || ''}
                    onChange={(e) => setEditedTenant({
                      ...editedTenant,
                      address: { ...editedTenant?.address, street: e.target.value }
                    })}
                    disabled={readOnly}
                    className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  />
                </div>
                <div className="grid grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">City</label>
                    <input
                      type="text"
                      value={editedTenant?.address?.city || ''}
                      onChange={(e) => setEditedTenant({
                        ...editedTenant,
                        address: { ...editedTenant?.address, city: e.target.value }
                      })}
                      disabled={readOnly}
                      className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Province</label>
                    <input
                      type="text"
                      value={editedTenant?.address?.province || ''}
                      onChange={(e) => setEditedTenant({
                        ...editedTenant,
                        address: { ...editedTenant?.address, province: e.target.value }
                      })}
                      disabled={readOnly}
                      className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Postal Code</label>
                    <input
                      type="text"
                      value={editedTenant?.address?.postal_code || ''}
                      onChange={(e) => setEditedTenant({
                        ...editedTenant,
                        address: { ...editedTenant?.address, postal_code: e.target.value }
                      })}
                      disabled={readOnly}
                      className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Country</label>
                    <input
                      type="text"
                      value={editedTenant?.address?.country || 'Canada'}
                      onChange={(e) => setEditedTenant({
                        ...editedTenant,
                        address: { ...editedTenant?.address, country: e.target.value }
                      })}
                      disabled={readOnly}
                      className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    />
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'billing' && (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Company Name</label>
                    <input
                      type="text"
                      value={editedTenant?.company_name || ''}
                      onChange={(e) => setEditedTenant({ ...editedTenant, company_name: e.target.value })}
                      disabled={readOnly}
                      className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Business Number</label>
                    <input
                      type="text"
                      value={editedTenant?.business_number || ''}
                      onChange={(e) => setEditedTenant({ ...editedTenant, business_number: e.target.value })}
                      disabled={readOnly}
                      className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">GST/HST Number</label>
                  <input
                    type="text"
                    value={editedTenant?.gst_hst_number || ''}
                    onChange={(e) => setEditedTenant({ ...editedTenant, gst_hst_number: e.target.value })}
                    disabled={readOnly}
                    className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Currency</label>
                  <select
                    value={editedTenant?.currency || 'CAD'}
                    onChange={(e) => setEditedTenant({ ...editedTenant, currency: e.target.value })}
                    disabled={readOnly}
                    className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  >
                    <option value="CAD">CAD</option>
                    <option value="USD">USD</option>
                  </select>
                </div>
              </div>
            )}

            {activeTab === 'subscription' && (
              <div className="space-y-6">
                {/* Current Plan Display */}
                <div className="p-4 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 border border-blue-200 dark:border-blue-800 rounded-xl">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200">Current Plan</h3>
                    <div className="flex items-center gap-2">
                      {subscriptionPlans[(editedTenant?.subscription_tier as keyof typeof subscriptionPlans) || 'community_and_new_business']?.isPopular && (
                        <span className="px-2 py-1 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-full text-xs font-semibold">
                          Most Popular
                        </span>
                      )}
                      <span className="px-3 py-1 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded-full text-sm font-medium">
                        {subscriptionPlans[(editedTenant?.subscription_tier as keyof typeof subscriptionPlans) || 'community_and_new_business']?.name}
                      </span>
                    </div>
                  </div>
                  <div className="grid grid-cols-4 gap-3 text-sm">
                    <div className="flex items-center gap-1 text-gray-600 dark:text-gray-400">
                      <Store className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                      <span className="font-medium">{editedTenant?.max_stores || 1}</span>
                      <span className="text-gray-500 dark:text-gray-400">Store{(editedTenant?.max_stores || 1) > 1 ? 's' : ''}</span>
                    </div>
                    <div className="flex items-center gap-1 text-gray-600 dark:text-gray-400">
                      <Globe className="w-4 h-4 text-green-600 dark:text-green-400" />
                      <span className="font-medium">{subscriptionPlans[(editedTenant?.subscription_tier as keyof typeof subscriptionPlans) || 'community_and_new_business']?.maxLanguages}</span>
                      <span className="text-gray-500 dark:text-gray-400">Languages</span>
                    </div>
                    <div className="flex items-center gap-1 text-gray-600 dark:text-gray-400">
                      <Users className="w-4 h-4 text-purple-600 dark:text-purple-400" />
                      <span className="font-medium">{subscriptionPlans[(editedTenant?.subscription_tier as keyof typeof subscriptionPlans) || 'community_and_new_business']?.maxAiPersonalities}</span>
                      <span className="text-gray-500 dark:text-gray-400">AI/Store</span>
                    </div>
                    <div className="flex items-center gap-1 text-gray-600 dark:text-gray-400">
                      <CreditCard className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
                      <span className="font-bold text-gray-800 dark:text-gray-200">{subscriptionPlans[(editedTenant?.subscription_tier as keyof typeof subscriptionPlans) || 'community_and_new_business']?.price}</span>
                    </div>
                  </div>
                </div>

                {/* Subscription Plans Grid */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">Select Subscription Plan</label>
                  <div className="grid grid-cols-2 gap-4">
                    {Object.entries(subscriptionPlans).map(([key, plan]) => (
                      <button
                        key={key}
                        onClick={() => {
                          if (!readOnly) {
                            setEditedTenant({
                              ...editedTenant,
                              subscription_tier: key,
                              max_stores: plan.maxStores
                            });
                          }
                        }}
                        disabled={readOnly}
                        className={`relative p-4 rounded-xl border-2 transition-all text-left ${
                          editedTenant?.subscription_tier === key
                            ? `${plan.color} dark:bg-blue-900/30 border-blue-500 dark:border-blue-400 shadow-lg transform scale-[1.02]`
                            : 'bg-white dark:bg-gray-700 border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500 hover:shadow-md'
                        } ${readOnly ? 'opacity-60 cursor-not-allowed' : 'cursor-pointer'}`}
                      >
                        {/* Most Popular Badge */}
                        {plan.isPopular && (
                          <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                            <span className="bg-gradient-to-r from-purple-600 to-blue-600 text-white text-xs font-semibold px-3 py-1 rounded-full">
                              Most Popular
                            </span>
                          </div>
                        )}

                        {editedTenant?.subscription_tier === key && (
                          <div className="absolute top-2 right-2">
                            <div className="w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center">
                              <Check className="w-4 h-4 text-white" />
                            </div>
                          </div>
                        )}

                        <div className="flex items-start gap-3">
                          <div className={`p-2 rounded-lg bg-white/50 dark:bg-gray-600/50 ${plan.iconColor}`}>
                            <plan.iconComponent className="w-6 h-6" />
                          </div>
                          <div className="flex-1">
                            <h4 className="font-semibold text-gray-900 dark:text-white mb-1">{plan.name}</h4>
                            <p className="text-lg font-bold text-primary-600 dark:text-primary-400 mb-2">{plan.price}</p>
                            <div className="space-y-1">
                              {plan.features.slice(0, 3).map((feature, idx) => (
                                <div key={idx} className="flex items-center gap-1 text-xs text-gray-600 dark:text-gray-300">
                                  <Check className="w-3 h-3 text-green-500 dark:text-green-400" />
                                  <span>{feature}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Max Stores (Auto-updated, read-only) */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Max Stores Allowed
                    <span className="ml-2 text-xs text-gray-500 dark:text-gray-400">(Auto-set based on plan)</span>
                  </label>
                  <div className="flex items-center gap-2">
                    <input
                      type="number"
                      value={editedTenant?.max_stores || 1}
                      disabled={true}
                      className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-gray-50 dark:bg-gray-600 text-gray-900 dark:text-gray-300"
                    />
                    <div className="px-3 py-2 bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-800 rounded-lg">
                      <Store className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                    </div>
                  </div>
                  <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                    This tenant can create up to {editedTenant?.max_stores || 1} store location{(editedTenant?.max_stores || 1) > 1 ? 's' : ''}.
                  </p>
                </div>

                {/* Account Status */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Account Status</label>
                  <div className="relative">
                    <select
                      value={editedTenant?.status || 'active'}
                      onChange={(e) => setEditedTenant({ ...editedTenant, status: e.target.value })}
                      disabled={readOnly}
                      className={`w-full pl-10 pr-3 py-2 border rounded-lg appearance-none ${
                        editedTenant?.status === 'active'
                          ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800 text-green-700 dark:text-green-300'
                          : editedTenant?.status === 'suspended'
                          ? 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800 text-yellow-700 dark:text-yellow-300'
                          : 'bg-gray-50 dark:bg-gray-700 border-gray-200 dark:border-gray-600 text-gray-700 dark:text-gray-300'
                      }`}
                    >
                      <option value="active">Active</option>
                      <option value="suspended">Suspended</option>
                      <option value="inactive">Inactive</option>
                    </select>
                    <div className="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none">
                      {editedTenant?.status === 'active' ? (
                        <CheckCircle className="w-4 h-4 text-green-600 dark:text-green-400" />
                      ) : editedTenant?.status === 'suspended' ? (
                        <AlertTriangle className="w-4 h-4 text-yellow-600 dark:text-yellow-400" />
                      ) : (
                        <XCircle className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                      )}
                    </div>
                  </div>
                </div>

                {/* Features List for Current Plan */}
                <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <h4 className="font-medium text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                    <Star className="w-4 h-4 text-yellow-500 dark:text-yellow-400" />
                    Included Features
                  </h4>
                  <div className="grid grid-cols-2 gap-2">
                    {subscriptionPlans[(editedTenant?.subscription_tier as keyof typeof subscriptionPlans) || 'community_and_new_business']?.features.map((feature, idx) => (
                      <div key={idx} className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
                        <Check className="w-4 h-4 text-green-500 dark:text-green-400" />
                        <span>{feature}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'users' && showUsersTab && (
              <div className="space-y-4">
                {userError && (
                  <div className="p-4 bg-danger-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                    <p className="text-sm text-red-700 dark:text-red-300">{userError}</p>
                  </div>
                )}

                {userSuccess && (
                  <div className="p-4 bg-primary-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
                    <p className="text-sm text-primary-700 dark:text-green-300">{userSuccess}</p>
                  </div>
                )}

                <div className="flex justify-between items-center">
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white">Admin Users</h3>
                  {!readOnly && (
                    <button
                      onClick={() => setShowAddUserForm(true)}
                      className="flex items-center gap-2 px-4 py-2 bg-accent-600 dark:bg-accent-700 text-white rounded-lg hover:bg-accent-700 dark:hover:bg-accent-600"
                    >
                      <UserPlus className="w-4 h-4" />
                      Add User
                    </button>
                  )}
                </div>

                {showAddUserForm && !readOnly && (
                  <div className="p-6 bg-gray-50 dark:bg-gray-700 rounded-lg space-y-3">
                    <h4 className="font-medium text-gray-900 dark:text-white">Add New User</h4>
                    <div className="grid grid-cols-2 gap-4">
                      <input
                        type="email"
                        placeholder="Email"
                        value={newUser.email}
                        onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                        className="px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-600 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-400"
                      />
                      <input
                        type="password"
                        placeholder="Password"
                        value={newUser.password}
                        onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                        className="px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-600 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-400"
                      />
                      <input
                        type="text"
                        placeholder="First Name"
                        value={newUser.first_name}
                        onChange={(e) => setNewUser({ ...newUser, first_name: e.target.value })}
                        className="px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-600 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-400"
                      />
                      <input
                        type="text"
                        placeholder="Last Name"
                        value={newUser.last_name}
                        onChange={(e) => setNewUser({ ...newUser, last_name: e.target.value })}
                        className="px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-600 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-400"
                      />
                      <select
                        value={newUser.role}
                        onChange={(e) => setNewUser({ ...newUser, role: e.target.value })}
                        className="px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-600 text-gray-900 dark:text-white col-span-2"
                      >
                        <option value="tenant_admin">Tenant Admin</option>
                        <option value="store_manager">Store Manager</option>
                        <option value="staff">Staff</option>
                      </select>
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={handleAddUser}
                        className="px-4 py-2 bg-primary-600 dark:bg-primary-700 text-white rounded-lg hover:bg-primary-700 dark:hover:bg-primary-600"
                      >
                        Add User
                      </button>
                      <button
                        onClick={() => setShowAddUserForm(false)}
                        className="px-4 py-2 bg-gray-300 dark:bg-gray-600 text-gray-700 dark:text-gray-200 rounded-lg hover:bg-gray-400 dark:hover:bg-gray-500"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                )}

                {loadingUsers ? (
                  <div className="text-center py-4 text-gray-600 dark:text-gray-400">Loading users...</div>
                ) : (
                  <div className="space-y-2">
                    {tenantUsers.map((user: any) => (
                      <div key={user.id} className="flex items-center justify-between p-4 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg">
                        <div>
                          <p className="font-medium text-gray-900 dark:text-white">{user.first_name} {user.last_name}</p>
                          <p className="text-sm text-gray-500 dark:text-gray-400">{user.email}</p>
                        </div>
                        <div className="flex items-center gap-4">
                          <select
                            value={user.role}
                            onChange={(e) => handleUpdateUserRole(user.id, e.target.value)}
                            disabled={readOnly}
                            className="px-2 py-1 text-sm border border-gray-200 dark:border-gray-600 rounded bg-white dark:bg-gray-600 text-gray-900 dark:text-white"
                          >
                            <option value="tenant_admin">Tenant Admin</option>
                            <option value="store_manager">Store Manager</option>
                            <option value="staff">Staff</option>
                          </select>
                          <span className={`px-2 py-1 text-xs rounded-full ${
                            user.active ? 'bg-primary-100 dark:bg-green-900/30 text-primary-700 dark:text-green-300' : 'bg-danger-100 dark:bg-red-900/30 text-red-700 dark:text-red-300'
                          }`}>
                            {user.active ? 'Active' : 'Blocked'}
                          </span>
                          {!readOnly && (
                            <div className="flex gap-1">
                              <button
                                onClick={() => handleResetPassword(user.id)}
                                className="p-1 text-accent-600 dark:text-accent-400 hover:bg-blue-50 dark:hover:bg-blue-900/30 rounded"
                                title="Reset Password"
                              >
                                <RefreshCw className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => handleToggleUserStatus(user.id, user.active)}
                                className="p-1 text-orange-600 dark:text-orange-400 hover:bg-orange-50 dark:hover:bg-orange-900/30 rounded"
                                title={user.active ? "Block User" : "Unblock User"}
                              >
                                {user.active ? <Ban className="w-4 h-4" /> : <Lock className="w-4 h-4" />}
                              </button>
                              <button
                                onClick={() => handleDeleteUser(user.id)}
                                className="p-1 text-danger-600 dark:text-red-400 hover:bg-danger-50 dark:hover:bg-red-900/30 rounded"
                                title="Delete User"
                              >
                                <UserX className="w-4 h-4" />
                              </button>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="flex justify-end gap-4 p-6 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50 flex-shrink-0">
            <button
              onClick={onClose}
              className="px-4 py-2 text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-600"
            >
              Cancel
            </button>
            {!readOnly && (
              <button
                onClick={handleSave}
                disabled={isSaving}
                className="flex items-center gap-2 px-4 py-2 bg-accent-600 dark:bg-accent-700 text-white rounded-lg hover:bg-accent-700 dark:hover:bg-accent-600 disabled:opacity-50"
              >
                {isSaving ? (
                  <>Saving...</>
                ) : (
                  <>
                    <Save className="w-4 h-4" />
                    {activeTab === 'subscription' ? 'Update Subscription' : 'Save Changes'}
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default TenantEditModal;