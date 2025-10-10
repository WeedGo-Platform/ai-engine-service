import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';
import { Customer } from '../types';
import { Users, Mail, Phone, Calendar, ShoppingBag, Star, Search, UserPlus, X, MapPin, CreditCard, Clock, Package } from 'lucide-react';
import { useStoreContext } from '../contexts/StoreContext';

const Customers: React.FC = () => {
  const { currentStore } = useStoreContext();
  const queryClient = useQueryClient();
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedType, setSelectedType] = useState<string>('all');
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null);
  const [isEditMode, setIsEditMode] = useState(false);
  const [editedCustomer, setEditedCustomer] = useState<any>(null);

  const { data: customers, isLoading, error } = useQuery({
    queryKey: ['customers', searchTerm, selectedType, currentStore?.id],
    queryFn: async () => {
      if (!currentStore?.id) {
        return [];
      }
      const params: any = { store_id: currentStore.id };
      if (searchTerm) params.search = searchTerm;
      if (selectedType !== 'all') params.customer_type = selectedType;
      const response = await api.customers.getAll(params);
      // The API returns {customers: [...]}
      return response.data?.customers || [];
    },
    enabled: !!currentStore?.id,
  });

  const updateMutation = useMutation({
    mutationFn: (data: { id: string; customer: Partial<Customer> }) =>
      api.customers.update(data.id, data.customer),
    onSuccess: (updatedData) => {
      queryClient.invalidateQueries({ queryKey: ['customers'] });
      setSelectedCustomer(updatedData.data);
      setIsEditMode(false);
      setEditedCustomer(null);
    },
  });

  const handleEditClick = () => {
    setIsEditMode(true);
    setEditedCustomer({ ...selectedCustomer });
  };

  const handleCancelEdit = () => {
    setIsEditMode(false);
    setEditedCustomer(null);
  };

  const handleSaveEdit = async () => {
    if (!editedCustomer || !selectedCustomer) return;

    try {
      await updateMutation.mutateAsync({
        id: selectedCustomer.id,
        customer: editedCustomer
      });
    } catch (error) {
      console.error('Error updating customer:', error);
    }
  };

  const handleFieldChange = (field: string, value: any) => {
    setEditedCustomer(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-primary-100 text-primary-800';
      case 'inactive':
        return 'bg-gray-50 text-gray-800';
      case 'banned':
        return 'bg-danger-100 text-danger-800';
      default:
        return 'bg-gray-50 text-gray-800';
    }
  };

  const getTypeColor = (type: string) => {
    return type === 'medical' ? 'bg-blue-100 text-blue-800' : 'bg-purple-100 text-purple-800';
  };

  // Show "No Store Selected" UI if no store is selected
  if (!currentStore) {
    return (
      <div className="h-full flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="mb-4">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-primary-100 rounded-full">
              <Users className="w-8 h-8 text-primary-600" />
            </div>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No Store Selected</h3>
          <p className="text-gray-500">Please select a store to manage customers</p>
        </div>
      </div>
    );
  }

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
        Error loading customers: {(error as Error).message}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Customer Management</h1>
          <p className="text-sm text-gray-500 mt-1">Managing customers for {currentStore.name}</p>
        </div>
        <button className="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 flex items-center gap-2">
          <UserPlus className="h-5 w-5" />
          Add Customer
        </button>
      </div>

      <div className="bg-white rounded-lg  p-6">
        <div className="flex gap-6 mb-6">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
              <input
                type="text"
                placeholder="Search customers..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>
          </div>
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-500"
          >
            <option value="all">All Types</option>
            <option value="recreational">Recreational</option>
            <option value="medical">Medical</option>
          </select>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Customer
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Contact
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Loyalty Points
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Total Spent
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Orders
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {customers?.map((customer: any) => (
                <tr key={customer.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="flex-shrink-0 h-10 w-10 bg-gray-100 rounded-full flex items-center justify-center">
                        <Users className="h-5 w-5 text-gray-600" />
                      </div>
                      <div className="ml-4">
                        <div className="text-sm font-medium text-gray-900">
                          {customer.name || 'Unknown Customer'}
                        </div>
                        <div className="text-sm text-gray-500">
                          ID: {customer.id.slice(0, 8)}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900 flex items-center gap-1">
                      <Mail className="h-4 w-4 text-gray-400" />
                      {customer.email}
                    </div>
                    {customer.phone && (
                      <div className="text-sm text-gray-500 flex items-center gap-1">
                        <Phone className="h-4 w-4 text-gray-400" />
                        {customer.phone}
                      </div>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getTypeColor(customer.customer_type || 'regular')}`}>
                      {customer.customer_type || 'regular'}
                    </span>
                    {customer.medical_license && (
                      <div className="text-xs text-gray-500 mt-1">
                        Lic: {customer.medical_license}
                      </div>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <Star className="h-4 w-4 text-yellow-400 mr-1" />
                      <span className="text-sm text-gray-900">{customer.loyalty_points || 0}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${(parseFloat(customer.total_spent) || 0).toFixed(2)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <ShoppingBag className="h-4 w-4 text-gray-400 mr-1" />
                      <span className="text-sm text-gray-900">{customer.order_count || 0}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${customer.is_verified ? 'bg-primary-100 text-primary-800' : 'bg-gray-50 text-gray-800'}`}>
                      {customer.is_verified ? 'Verified' : 'Unverified'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button
                      onClick={() => setSelectedCustomer(customer)}
                      className="text-indigo-600 hover:text-indigo-900"
                    >
                      View
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {(!customers || customers.length === 0) && (
          <div className="text-center py-12">
            <Users className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No customers found</h3>
            <p className="mt-1 text-sm text-gray-500">
              Get started by adding a new customer.
            </p>
          </div>
        )}
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg  p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Customers</p>
              <p className="text-2xl font-bold text-gray-900">
                {customers?.length || 0}
              </p>
            </div>
            <Users className="h-8 w-8 text-primary-600" />
          </div>
        </div>

        <div className="bg-white rounded-lg  p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Medical Patients</p>
              <p className="text-2xl font-bold text-accent-600">
                {customers?.filter((c: any) => c.customer_type === 'medical').length || 0}
              </p>
            </div>
            <Users className="h-8 w-8 text-accent-600" />
          </div>
        </div>

        <div className="bg-white rounded-lg  p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Avg Spent</p>
              <p className="text-2xl font-bold text-gray-900">
                ${customers?.length ? 
                  (customers.reduce((sum: number, c: any) => sum + (parseFloat(c.total_spent) || 0), 0) / customers.length).toFixed(2)
                  : '0.00'
                }
              </p>
            </div>
            <ShoppingBag className="h-8 w-8 text-purple-600" />
          </div>
        </div>

        <div className="bg-white rounded-lg  p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Points</p>
              <p className="text-2xl font-bold text-warning-600">
                {customers?.reduce((sum: number, c: any) => sum + (c.loyalty_points || 0), 0) || 0}
              </p>
            </div>
            <Star className="h-8 w-8 text-warning-600" />
          </div>
        </div>
      </div>

      {/* Customer Details Modal */}
      {selectedCustomer && (
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg max-w-3xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <div className="flex justify-between items-center">
                <h2 className="text-xl font-semibold text-gray-900">Customer Details</h2>
                <button
                  onClick={() => setSelectedCustomer(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="h-6 w-6" />
                </button>
              </div>
            </div>

            <div className="p-6 space-y-6">
              {/* Customer Header */}
              <div className="flex items-center space-x-4">
                <div className="h-16 w-16 bg-primary-100 rounded-full flex items-center justify-center">
                  <Users className="h-8 w-8 text-primary-600" />
                </div>
                <div className="flex-1">
                  {isEditMode ? (
                    <input
                      type="text"
                      value={editedCustomer?.name || ''}
                      onChange={(e) => handleFieldChange('name', e.target.value)}
                      className="text-lg font-semibold text-gray-900 border border-gray-300 rounded px-2 py-1 w-full"
                      placeholder="Customer Name"
                    />
                  ) : (
                    <h3 className="text-lg font-semibold text-gray-900">
                      {selectedCustomer.name || 'Unknown Customer'}
                    </h3>
                  )}
                  <p className="text-sm text-gray-500">Customer ID: {selectedCustomer.id}</p>
                </div>
              </div>

              {/* Contact Information */}
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-3">Contact Information</h4>
                <div className="bg-gray-50 rounded-lg p-4 space-y-3">
                  <div className="flex items-center space-x-2">
                    <Mail className="h-4 w-4 text-gray-400" />
                    {isEditMode ? (
                      <input
                        type="email"
                        value={editedCustomer?.email || ''}
                        onChange={(e) => handleFieldChange('email', e.target.value)}
                        className="text-sm text-gray-900 border border-gray-300 rounded px-2 py-1 flex-1"
                        placeholder="Email Address"
                      />
                    ) : (
                      <span className="text-sm text-gray-900">{selectedCustomer.email}</span>
                    )}
                  </div>
                  <div className="flex items-center space-x-2">
                    <Phone className="h-4 w-4 text-gray-400" />
                    {isEditMode ? (
                      <input
                        type="tel"
                        value={editedCustomer?.phone || ''}
                        onChange={(e) => handleFieldChange('phone', e.target.value)}
                        className="text-sm text-gray-900 border border-gray-300 rounded px-2 py-1 flex-1"
                        placeholder="Phone Number"
                      />
                    ) : (
                      <span className="text-sm text-gray-900">{selectedCustomer.phone || 'No phone'}</span>
                    )}
                  </div>
                  {selectedCustomer.birth_date && (
                    <div className="flex items-center space-x-2">
                      <Calendar className="h-4 w-4 text-gray-400" />
                      <span className="text-sm text-gray-900">Born: {selectedCustomer.birth_date}</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Customer Stats */}
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-3">Customer Statistics</h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-gray-50 rounded-lg p-4">
                    <div className="flex items-center space-x-2 mb-1">
                      <Star className="h-4 w-4 text-yellow-500" />
                      <span className="text-xs text-gray-600">Loyalty Points</span>
                    </div>
                    {isEditMode ? (
                      <input
                        type="number"
                        value={editedCustomer?.loyalty_points || 0}
                        onChange={(e) => handleFieldChange('loyalty_points', parseInt(e.target.value) || 0)}
                        className="text-lg font-semibold text-gray-900 border border-gray-300 rounded px-2 py-1 w-full"
                        min="0"
                      />
                    ) : (
                      <p className="text-lg font-semibold text-gray-900">
                        {selectedCustomer.loyalty_points || 0}
                      </p>
                    )}
                  </div>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <div className="flex items-center space-x-2 mb-1">
                      <CreditCard className="h-4 w-4 text-green-500" />
                      <span className="text-xs text-gray-600">Total Spent</span>
                    </div>
                    <p className="text-lg font-semibold text-gray-900">
                      ${parseFloat(selectedCustomer.total_spent || '0').toFixed(2)}
                    </p>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <div className="flex items-center space-x-2 mb-1">
                      <Package className="h-4 w-4 text-blue-500" />
                      <span className="text-xs text-gray-600">Total Orders</span>
                    </div>
                    <p className="text-lg font-semibold text-gray-900">
                      {selectedCustomer.order_count || 0}
                    </p>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <div className="flex items-center space-x-2 mb-1">
                      <Clock className="h-4 w-4 text-purple-500" />
                      <span className="text-xs text-gray-600">Status</span>
                    </div>
                    <p className="text-lg font-semibold text-gray-900">
                      {selectedCustomer.is_verified ? 'Verified' : 'Unverified'}
                    </p>
                  </div>
                </div>
              </div>

              {/* Additional Info */}
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-3">Additional Information</h4>
                <div className="bg-gray-50 rounded-lg p-4 space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Customer Type</span>
                    <span className={`px-2 py-1 text-xs rounded-full ${getTypeColor(selectedCustomer.customer_type || 'regular')}`}>
                      {selectedCustomer.customer_type || 'regular'}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Age Verified</span>
                    <span className="text-sm font-medium text-gray-900">
                      {selectedCustomer.is_verified ? 'Yes' : 'No'}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Marketing Consent</span>
                    {isEditMode ? (
                      <input
                        type="checkbox"
                        checked={editedCustomer?.marketing_consent || false}
                        onChange={(e) => handleFieldChange('marketing_consent', e.target.checked)}
                        className="h-4 w-4 text-primary-600 rounded"
                      />
                    ) : (
                      <span className="text-sm font-medium text-gray-900">
                        {selectedCustomer.marketing_consent ? 'Yes' : 'No'}
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {/* Recent Orders Section (placeholder) */}
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-3">Recent Orders</h4>
                <div className="bg-gray-50 rounded-lg p-4">
                  <p className="text-sm text-gray-500 text-center">
                    Order history will be displayed here
                  </p>
                </div>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="p-6 border-t border-gray-200 bg-gray-50">
              <div className="flex justify-end space-x-3">
                {isEditMode ? (
                  <>
                    <button
                      onClick={handleCancelEdit}
                      className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-100"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleSaveEdit}
                      disabled={updateMutation.isPending}
                      className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {updateMutation.isPending ? 'Saving...' : 'Save Changes'}
                    </button>
                  </>
                ) : (
                  <>
                    <button
                      onClick={() => {
                        setSelectedCustomer(null);
                        setIsEditMode(false);
                        setEditedCustomer(null);
                      }}
                      className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-100"
                    >
                      Close
                    </button>
                    <button
                      onClick={handleEditClick}
                      className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
                    >
                      Edit Customer
                    </button>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Customers;