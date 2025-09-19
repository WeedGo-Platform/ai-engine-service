import React, { useState, useEffect } from 'react';
import {
  X, Building2, Mail, Phone, Globe, CreditCard, Package,
  MapPin, Upload, Save, AlertCircle, Users, UserPlus, Lock,
  Ban, UserX, Shield, RefreshCw
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import tenantService from '../services/tenantService';

interface TenantEditModalProps {
  tenant: any;
  isOpen: boolean;
  onClose: () => void;
  onSave: (updatedTenant: any) => Promise<void>;
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
      const response = await fetch(`http://localhost:5024/api/tenants/${tenant.id}/users`);
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
    const resetMethod = window.confirm(
      'Click OK to send a password reset link via email\n' +
      'Click Cancel to generate a one-time password'
    );
    
    try {
      const response = await fetch(`http://localhost:5024/api/tenants/${tenant.id}/users/${userId}/reset-password`, {
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
      const response = await fetch(`http://localhost:5024/api/tenants/${tenant.id}/users/${userId}/toggle-active`, {
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
      const response = await fetch(`http://localhost:5024/api/tenants/${tenant.id}/users/${userId}`, {
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
    
    if (!confirm('Are you sure you want to delete this user? This action cannot be undone.')) return;
    
    setUserError(null);
    setUserSuccess(null);
    
    try {
      const response = await fetch(`http://localhost:5024/api/tenants/${tenant.id}/users/${userId}`, {
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
      await onSave(editedTenant);
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
        
        <div className="relative bg-white rounded-lg border border-gray-200 max-w-4xl w-full max-h-[90vh] overflow-hidden">
          <div className="flex items-center justify-between p-6 border-b">
            <h2 className="text-xl font-semibold">
              {readOnly ? 'View' : 'Edit'} Organization
            </h2>
            <button onClick={onClose} className="text-gray-400 hover:text-gray-500">
              <X className="w-5 h-5" />
            </button>
          </div>

          <div className="border-b">
            <div className="flex space-x-1 px-4">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 px-4 py-2 border-b-2 transition-colors ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-accent-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  <tab.icon className="w-4 h-4" />
                  {tab.label}
                </button>
              ))}
            </div>
          </div>

          <div className="p-6 overflow-y-auto max-h-[calc(90vh-180px)]">
            {/* Tab content here - same as existing TenantManagement but with readOnly support */}
            {activeTab === 'general' && (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Organization Name
                    </label>
                    <input
                      type="text"
                      value={editedTenant?.name || ''}
                      onChange={(e) => setEditedTenant({ ...editedTenant, name: e.target.value })}
                      disabled={readOnly}
                      className="w-full px-3 py-2 border border-gray-200 rounded-lg"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Organization Code
                    </label>
                    <input
                      type="text"
                      value={editedTenant?.code || ''}
                      disabled
                      className="w-full px-3 py-2 border border-gray-200 rounded-lg bg-gray-50"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      <Mail className="inline w-4 h-4 mr-1" />
                      Contact Email
                    </label>
                    <input
                      type="email"
                      value={editedTenant?.contact_email || ''}
                      onChange={(e) => setEditedTenant({ ...editedTenant, contact_email: e.target.value })}
                      disabled={readOnly}
                      className="w-full px-3 py-2 border border-gray-200 rounded-lg"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      <Phone className="inline w-4 h-4 mr-1" />
                      Contact Phone
                    </label>
                    <input
                      type="tel"
                      value={editedTenant?.contact_phone || ''}
                      onChange={(e) => setEditedTenant({ ...editedTenant, contact_phone: e.target.value })}
                      disabled={readOnly}
                      className="w-full px-3 py-2 border border-gray-200 rounded-lg"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    <Globe className="inline w-4 h-4 mr-1" />
                    Website
                  </label>
                  <input
                    type="url"
                    value={editedTenant?.website || ''}
                    onChange={(e) => setEditedTenant({ ...editedTenant, website: e.target.value })}
                    disabled={readOnly}
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg"
                  />
                </div>

                {!readOnly && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      <Upload className="inline w-4 h-4 mr-1" />
                      Logo
                    </label>
                    <div className="flex items-center gap-6">
                      {logoPreview && (
                        <img src={logoPreview} alt="Logo preview" className="w-16 h-16 object-contain border rounded" />
                      )}
                      <input
                        type="file"
                        accept="image/*"
                        onChange={handleFileChange}
                        className="flex-1"
                      />
                    </div>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'address' && (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Street</label>
                  <input
                    type="text"
                    value={editedTenant?.address?.street || ''}
                    onChange={(e) => setEditedTenant({
                      ...editedTenant,
                      address: { ...editedTenant?.address, street: e.target.value }
                    })}
                    disabled={readOnly}
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg"
                  />
                </div>
                <div className="grid grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">City</label>
                    <input
                      type="text"
                      value={editedTenant?.address?.city || ''}
                      onChange={(e) => setEditedTenant({
                        ...editedTenant,
                        address: { ...editedTenant?.address, city: e.target.value }
                      })}
                      disabled={readOnly}
                      className="w-full px-3 py-2 border border-gray-200 rounded-lg"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Province</label>
                    <input
                      type="text"
                      value={editedTenant?.address?.province || ''}
                      onChange={(e) => setEditedTenant({
                        ...editedTenant,
                        address: { ...editedTenant?.address, province: e.target.value }
                      })}
                      disabled={readOnly}
                      className="w-full px-3 py-2 border border-gray-200 rounded-lg"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Postal Code</label>
                    <input
                      type="text"
                      value={editedTenant?.address?.postal_code || ''}
                      onChange={(e) => setEditedTenant({
                        ...editedTenant,
                        address: { ...editedTenant?.address, postal_code: e.target.value }
                      })}
                      disabled={readOnly}
                      className="w-full px-3 py-2 border border-gray-200 rounded-lg"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Country</label>
                    <input
                      type="text"
                      value={editedTenant?.address?.country || 'Canada'}
                      onChange={(e) => setEditedTenant({
                        ...editedTenant,
                        address: { ...editedTenant?.address, country: e.target.value }
                      })}
                      disabled={readOnly}
                      className="w-full px-3 py-2 border border-gray-200 rounded-lg"
                    />
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'billing' && (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Company Name</label>
                    <input
                      type="text"
                      value={editedTenant?.company_name || ''}
                      onChange={(e) => setEditedTenant({ ...editedTenant, company_name: e.target.value })}
                      disabled={readOnly}
                      className="w-full px-3 py-2 border border-gray-200 rounded-lg"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Business Number</label>
                    <input
                      type="text"
                      value={editedTenant?.business_number || ''}
                      onChange={(e) => setEditedTenant({ ...editedTenant, business_number: e.target.value })}
                      disabled={readOnly}
                      className="w-full px-3 py-2 border border-gray-200 rounded-lg"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">GST/HST Number</label>
                  <input
                    type="text"
                    value={editedTenant?.gst_hst_number || ''}
                    onChange={(e) => setEditedTenant({ ...editedTenant, gst_hst_number: e.target.value })}
                    disabled={readOnly}
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Currency</label>
                  <select
                    value={editedTenant?.currency || 'CAD'}
                    onChange={(e) => setEditedTenant({ ...editedTenant, currency: e.target.value })}
                    disabled={readOnly}
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg"
                  >
                    <option value="CAD">CAD</option>
                    <option value="USD">USD</option>
                  </select>
                </div>
              </div>
            )}

            {activeTab === 'subscription' && (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Subscription Tier</label>
                  <select
                    value={editedTenant?.subscription_tier || 'community'}
                    onChange={(e) => setEditedTenant({ ...editedTenant, subscription_tier: e.target.value })}
                    disabled={readOnly}
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg"
                  >
                    <option value="community_and_new_business">Community and New Business</option>
                    <option value="small_business">Small Business</option>
                    <option value="professional_and_growing_business">Professional and Growing Business</option>
                    <option value="enterprise">Enterprise</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Max Stores</label>
                  <input
                    type="number"
                    value={editedTenant?.max_stores || 1}
                    onChange={(e) => setEditedTenant({ ...editedTenant, max_stores: parseInt(e.target.value) })}
                    disabled={readOnly}
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                  <select
                    value={editedTenant?.status || 'active'}
                    onChange={(e) => setEditedTenant({ ...editedTenant, status: e.target.value })}
                    disabled={readOnly}
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg"
                  >
                    <option value="active">Active</option>
                    <option value="suspended">Suspended</option>
                    <option value="inactive">Inactive</option>
                  </select>
                </div>
              </div>
            )}

            {activeTab === 'users' && showUsersTab && (
              <div className="space-y-4">
                {userError && (
                  <div className="p-4 bg-danger-50 border border-red-200 rounded-lg">
                    <p className="text-sm text-red-700">{userError}</p>
                  </div>
                )}
                
                {userSuccess && (
                  <div className="p-4 bg-primary-50 border border-green-200 rounded-lg">
                    <p className="text-sm text-primary-700">{userSuccess}</p>
                  </div>
                )}

                <div className="flex justify-between items-center">
                  <h3 className="text-lg font-medium">Admin Users</h3>
                  {!readOnly && (
                    <button
                      onClick={() => setShowAddUserForm(true)}
                      className="flex items-center gap-2 px-4 py-2 bg-accent-600 text-white rounded-lg hover:bg-accent-700"
                    >
                      <UserPlus className="w-4 h-4" />
                      Add User
                    </button>
                  )}
                </div>

                {showAddUserForm && !readOnly && (
                  <div className="p-6 bg-gray-50 rounded-lg space-y-3">
                    <h4 className="font-medium">Add New User</h4>
                    <div className="grid grid-cols-2 gap-4">
                      <input
                        type="email"
                        placeholder="Email"
                        value={newUser.email}
                        onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                        className="px-3 py-2 border border-gray-200 rounded-lg"
                      />
                      <input
                        type="password"
                        placeholder="Password"
                        value={newUser.password}
                        onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                        className="px-3 py-2 border border-gray-200 rounded-lg"
                      />
                      <input
                        type="text"
                        placeholder="First Name"
                        value={newUser.first_name}
                        onChange={(e) => setNewUser({ ...newUser, first_name: e.target.value })}
                        className="px-3 py-2 border border-gray-200 rounded-lg"
                      />
                      <input
                        type="text"
                        placeholder="Last Name"
                        value={newUser.last_name}
                        onChange={(e) => setNewUser({ ...newUser, last_name: e.target.value })}
                        className="px-3 py-2 border border-gray-200 rounded-lg"
                      />
                      <select
                        value={newUser.role}
                        onChange={(e) => setNewUser({ ...newUser, role: e.target.value })}
                        className="px-3 py-2 border border-gray-200 rounded-lg col-span-2"
                      >
                        <option value="tenant_admin">Tenant Admin</option>
                        <option value="store_manager">Store Manager</option>
                        <option value="staff">Staff</option>
                      </select>
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={handleAddUser}
                        className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
                      >
                        Add User
                      </button>
                      <button
                        onClick={() => setShowAddUserForm(false)}
                        className="px-4 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                )}

                {loadingUsers ? (
                  <div className="text-center py-4">Loading users...</div>
                ) : (
                  <div className="space-y-2">
                    {tenantUsers.map((user: any) => (
                      <div key={user.id} className="flex items-center justify-between p-4 bg-white border rounded-lg">
                        <div>
                          <p className="font-medium">{user.first_name} {user.last_name}</p>
                          <p className="text-sm text-gray-500">{user.email}</p>
                        </div>
                        <div className="flex items-center gap-4">
                          <select
                            value={user.role}
                            onChange={(e) => handleUpdateUserRole(user.id, e.target.value)}
                            disabled={readOnly}
                            className="px-2 py-1 text-sm border border-gray-200 rounded"
                          >
                            <option value="tenant_admin">Tenant Admin</option>
                            <option value="store_manager">Store Manager</option>
                            <option value="staff">Staff</option>
                          </select>
                          <span className={`px-2 py-1 text-xs rounded-full ${
                            user.active ? 'bg-primary-100 text-primary-700' : 'bg-danger-100 text-red-700'
                          }`}>
                            {user.active ? 'Active' : 'Blocked'}
                          </span>
                          {!readOnly && (
                            <div className="flex gap-1">
                              <button
                                onClick={() => handleResetPassword(user.id)}
                                className="p-1 text-accent-600 hover:bg-blue-50 rounded"
                                title="Reset Password"
                              >
                                <RefreshCw className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => handleToggleUserStatus(user.id, user.active)}
                                className="p-1 text-orange-600 hover:bg-orange-50 rounded"
                                title={user.active ? "Block User" : "Unblock User"}
                              >
                                {user.active ? <Ban className="w-4 h-4" /> : <Lock className="w-4 h-4" />}
                              </button>
                              <button
                                onClick={() => handleDeleteUser(user.id)}
                                className="p-1 text-danger-600 hover:bg-danger-50 rounded"
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

          <div className="flex justify-end gap-4 p-6 border-t">
            <button
              onClick={onClose}
              className="px-4 py-2 text-gray-700 bg-gray-50 rounded-lg hover:bg-gray-50"
            >
              Cancel
            </button>
            {!readOnly && (
              <button
                onClick={handleSave}
                disabled={isSaving}
                className="flex items-center gap-2 px-4 py-2 bg-accent-600 text-white rounded-lg hover:bg-accent-700 disabled:opacity-50"
              >
                {isSaving ? (
                  <>Saving...</>
                ) : (
                  <>
                    <Save className="w-4 h-4" />
                    Save Changes
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