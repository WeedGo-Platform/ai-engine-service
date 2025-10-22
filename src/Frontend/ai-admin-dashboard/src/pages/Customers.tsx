import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';
import { Customer } from '../types';
import { Users, Mail, Phone, Calendar, ShoppingBag, Star, Search, UserPlus, X, MapPin, CreditCard, Clock, Package } from 'lucide-react';
import { useStoreContext } from '../contexts/StoreContext';
import { formatCurrency } from '../utils/currency';

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
        return 'bg-primary-100 dark:bg-primary-900/30 text-primary-800 dark:text-primary-300';
      case 'inactive':
        return 'bg-gray-50 dark:bg-gray-700 text-gray-800 dark:text-gray-300';
      case 'banned':
        return 'bg-danger-100 dark:bg-red-900/30 text-danger-800 dark:text-red-300';
      default:
        return 'bg-gray-50 dark:bg-gray-700 text-gray-800 dark:text-gray-300';
    }
  };

  const getTypeColor = (type: string) => {
    return type === 'medical'
      ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300'
      : 'bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-300';
  };

  // Show "No Store Selected" UI if no store is selected
  if (!currentStore) {
    return (
      <div className="h-full flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="text-center">
          <div className="mb-4">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-primary-100 dark:bg-primary-900/30 rounded-full">
              <Users className="w-8 h-8 text-primary-600 dark:text-primary-400" />
            </div>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">No Store Selected</h3>
          <p className="text-gray-500 dark:text-gray-400">Please select a store to manage customers</p>
        </div>
      </div>
    );
  }

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
        Error loading customers: {(error as Error).message}
      </div>
    );
  }

  return (
    <div className="space-y-4 sm:space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 sm:gap-0">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white">Customer Management</h1>
          <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400 mt-1">Managing customers for {currentStore.name}</p>
        </div>
        <button className="w-full sm:w-auto bg-primary-600 dark:bg-primary-700 text-white px-4 py-2.5 sm:py-2 rounded-lg hover:bg-primary-700 dark:hover:bg-primary-600 flex items-center justify-center gap-2 font-medium text-sm active:scale-95 transition-all touch-manipulation">
          <UserPlus className="h-4 w-4 sm:h-5 sm:w-5" />
          Add Customer
        </button>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg p-4 sm:p-6">
        <div className="flex flex-col sm:flex-row gap-3 sm:gap-6 mb-4 sm:mb-6">
          <div className="flex-1 min-w-0">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 dark:text-gray-500 h-4 w-4 sm:h-5 sm:w-5" />
              <input
                type="text"
                placeholder="Search customers..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-9 sm:pl-10 pr-4 py-2 text-sm border border-gray-200 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 dark:focus:ring-primary-400 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 transition-colors"
              />
            </div>
          </div>
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="px-3 sm:px-4 py-2 text-sm border border-gray-200 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 dark:focus:ring-primary-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white transition-colors"
          >
            <option value="all">All Types</option>
            <option value="recreational">Recreational</option>
            <option value="medical">Medical</option>
          </select>
        </div>

        <div className="overflow-x-auto -mx-4 sm:-mx-6">
          <div className="inline-block min-w-full align-middle px-4 sm:px-6">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead className="bg-gray-50 dark:bg-gray-700">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Customer
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Contact
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Loyalty Points
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Total Spent
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Orders
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
              {customers?.map((customer: any) => (
                <tr key={customer.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="flex-shrink-0 h-10 w-10 bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center">
                        <Users className="h-5 w-5 text-gray-600 dark:text-gray-400" />
                      </div>
                      <div className="ml-4">
                        <div className="text-sm font-medium text-gray-900 dark:text-white">
                          {customer.name || 'Unknown Customer'}
                        </div>
                        <div className="text-sm text-gray-500 dark:text-gray-400">
                          ID: {customer.id.slice(0, 8)}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900 dark:text-white flex items-center gap-1">
                      <Mail className="h-4 w-4 text-gray-400 dark:text-gray-500" />
                      {customer.email}
                    </div>
                    {customer.phone && (
                      <div className="text-sm text-gray-500 dark:text-gray-400 flex items-center gap-1">
                        <Phone className="h-4 w-4 text-gray-400 dark:text-gray-500" />
                        {customer.phone}
                      </div>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getTypeColor(customer.customer_type || 'regular')}`}>
                      {customer.customer_type || 'regular'}
                    </span>
                    {customer.medical_license && (
                      <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                        Lic: {customer.medical_license}
                      </div>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <Star className="h-4 w-4 text-yellow-400 mr-1" />
                      <span className="text-sm text-gray-900 dark:text-white">{customer.loyalty_points || 0}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                    {formatCurrency(parseFloat(customer.total_spent) || 0)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <ShoppingBag className="h-4 w-4 text-gray-400 dark:text-gray-500 mr-1" />
                      <span className="text-sm text-gray-900 dark:text-white">{customer.order_count || 0}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${customer.is_verified ? 'bg-primary-100 dark:bg-primary-900/30 text-primary-800 dark:text-primary-300' : 'bg-gray-50 dark:bg-gray-700 text-gray-800 dark:text-gray-300'}`}>
                      {customer.is_verified ? 'Verified' : 'Unverified'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button
                      onClick={() => setSelectedCustomer(customer)}
                      className="text-indigo-600 dark:text-indigo-400 hover:text-indigo-900 dark:hover:text-indigo-300"
                    >
                      View
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          </div>
        </div>

        {(!customers || customers.length === 0) && (
          <div className="text-center py-12">
            <Users className="mx-auto h-12 w-12 text-gray-400 dark:text-gray-600" />
            <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">No customers found</h3>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              Get started by adding a new customer.
            </p>
          </div>
        )}
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 lg:gap-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 sm:p-6 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs sm:text-sm font-medium text-gray-600 dark:text-gray-400">Total Customers</p>
              <p className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white">
                {customers?.length || 0}
              </p>
            </div>
            <Users className="h-6 w-6 sm:h-8 sm:w-8 text-primary-600 dark:text-primary-400" />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 sm:p-6 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs sm:text-sm font-medium text-gray-600 dark:text-gray-400">Medical Patients</p>
              <p className="text-xl sm:text-2xl font-bold text-accent-600 dark:text-accent-400">
                {customers?.filter((c: any) => c.customer_type === 'medical').length || 0}
              </p>
            </div>
            <Users className="h-6 w-6 sm:h-8 sm:w-8 text-accent-600 dark:text-accent-400" />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 sm:p-6 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs sm:text-sm font-medium text-gray-600 dark:text-gray-400">Avg Spent</p>
              <p className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white">
                ${customers?.length ?
                  (customers.reduce((sum: number, c: any) => sum + (parseFloat(c.total_spent) || 0), 0) / customers.length).toFixed(2)
                  : '0.00'
                }
              </p>
            </div>
            <ShoppingBag className="h-6 w-6 sm:h-8 sm:w-8 text-purple-600 dark:text-purple-400" />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 sm:p-6 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs sm:text-sm font-medium text-gray-600 dark:text-gray-400">Total Points</p>
              <p className="text-xl sm:text-2xl font-bold text-warning-600 dark:text-warning-400">
                {customers?.reduce((sum: number, c: any) => sum + (c.loyalty_points || 0), 0) || 0}
              </p>
            </div>
            <Star className="h-6 w-6 sm:h-8 sm:w-8 text-warning-600 dark:text-warning-400" />
          </div>
        </div>
      </div>

      {/* Customer Details Modal */}
      {selectedCustomer && (
        <div className="fixed inset-0 bg-gray-500 dark:bg-black bg-opacity-75 dark:bg-opacity-70 flex items-center justify-center z-50 p-0 sm:p-4">
          <div className="bg-white dark:bg-gray-800 h-full sm:h-auto sm:rounded-lg border-0 sm:border border-gray-200 dark:border-gray-700 sm:max-w-3xl w-full max-h-full sm:max-h-[90vh] overflow-y-auto flex flex-col">
            <div className="p-4 sm:p-6 border-b border-gray-200 dark:border-gray-700 flex-shrink-0 sticky top-0 bg-white dark:bg-gray-800 z-10">
              <div className="flex justify-between items-center">
                <h2 className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-white">Customer Details</h2>
                <button
                  onClick={() => setSelectedCustomer(null)}
                  className="p-2 -mr-2 text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                  aria-label="Close customer details"
                >
                  <X className="h-5 w-5 sm:h-6 sm:w-6" />
                </button>
              </div>
            </div>

            <div className="p-4 sm:p-6 space-y-4 sm:space-y-6 flex-1 overflow-y-auto">
              {/* Customer Header */}
              <div className="flex items-center space-x-3 sm:space-x-4">
                <div className="h-12 w-12 sm:h-16 sm:w-16 bg-primary-100 dark:bg-primary-900/30 rounded-full flex items-center justify-center flex-shrink-0">
                  <Users className="h-6 w-6 sm:h-8 sm:w-8 text-primary-600 dark:text-primary-400" />
                </div>
                <div className="flex-1 min-w-0">
                  {isEditMode ? (
                    <input
                      type="text"
                      value={editedCustomer?.name || ''}
                      onChange={(e) => handleFieldChange('name', e.target.value)}
                      className="text-base sm:text-lg font-semibold text-gray-900 dark:text-white border border-gray-300 dark:border-gray-600 rounded px-2 py-1 w-full bg-white dark:bg-gray-700 transition-colors"
                      placeholder="Customer Name"
                    />
                  ) : (
                    <h3 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-white truncate">
                      {selectedCustomer.name || 'Unknown Customer'}
                    </h3>
                  )}
                  <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400 truncate">Customer ID: {selectedCustomer.id}</p>
                </div>
              </div>

              {/* Contact Information */}
              <div>
                <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">Contact Information</h4>
                <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 space-y-3">
                  <div className="flex items-center space-x-2">
                    <Mail className="h-4 w-4 text-gray-400 dark:text-gray-500" />
                    {isEditMode ? (
                      <input
                        type="email"
                        value={editedCustomer?.email || ''}
                        onChange={(e) => handleFieldChange('email', e.target.value)}
                        className="text-sm text-gray-900 dark:text-white border border-gray-300 dark:border-gray-600 rounded px-2 py-1 flex-1 bg-white dark:bg-gray-600"
                        placeholder="Email Address"
                      />
                    ) : (
                      <span className="text-sm text-gray-900 dark:text-white">{selectedCustomer.email}</span>
                    )}
                  </div>
                  <div className="flex items-center space-x-2">
                    <Phone className="h-4 w-4 text-gray-400 dark:text-gray-500" />
                    {isEditMode ? (
                      <input
                        type="tel"
                        value={editedCustomer?.phone || ''}
                        onChange={(e) => handleFieldChange('phone', e.target.value)}
                        className="text-sm text-gray-900 dark:text-white border border-gray-300 dark:border-gray-600 rounded px-2 py-1 flex-1 bg-white dark:bg-gray-600"
                        placeholder="Phone Number"
                      />
                    ) : (
                      <span className="text-sm text-gray-900 dark:text-white">{selectedCustomer.phone || 'No phone'}</span>
                    )}
                  </div>
                  {selectedCustomer.birth_date && (
                    <div className="flex items-center space-x-2">
                      <Calendar className="h-4 w-4 text-gray-400 dark:text-gray-500" />
                      <span className="text-sm text-gray-900 dark:text-white">Born: {selectedCustomer.birth_date}</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Customer Stats */}
              <div>
                <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">Customer Statistics</h4>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4">
                  <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                    <div className="flex items-center space-x-2 mb-1">
                      <Star className="h-4 w-4 text-yellow-500" />
                      <span className="text-xs text-gray-600 dark:text-gray-400">Loyalty Points</span>
                    </div>
                    {isEditMode ? (
                      <input
                        type="number"
                        value={editedCustomer?.loyalty_points || 0}
                        onChange={(e) => handleFieldChange('loyalty_points', parseInt(e.target.value) || 0)}
                        className="text-lg font-semibold text-gray-900 dark:text-white border border-gray-300 dark:border-gray-600 rounded px-2 py-1 w-full bg-white dark:bg-gray-600"
                        min="0"
                      />
                    ) : (
                      <p className="text-lg font-semibold text-gray-900 dark:text-white">
                        {selectedCustomer.loyalty_points || 0}
                      </p>
                    )}
                  </div>
                  <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                    <div className="flex items-center space-x-2 mb-1">
                      <CreditCard className="h-4 w-4 text-green-500" />
                      <span className="text-xs text-gray-600 dark:text-gray-400">Total Spent</span>
                    </div>
                    <p className="text-lg font-semibold text-gray-900 dark:text-white">
                                          <p className="text-2xl font-bold text-primary-600 dark:text-primary-400">
                      {formatCurrency(parseFloat(selectedCustomer.total_spent || '0'))}
                    </p>
                    </p>
                  </div>
                  <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                    <div className="flex items-center space-x-2 mb-1">
                      <Package className="h-4 w-4 text-blue-500" />
                      <span className="text-xs text-gray-600 dark:text-gray-400">Total Orders</span>
                    </div>
                    <p className="text-lg font-semibold text-gray-900 dark:text-white">
                      {selectedCustomer.order_count || 0}
                    </p>
                  </div>
                  <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                    <div className="flex items-center space-x-2 mb-1">
                      <Clock className="h-4 w-4 text-purple-500" />
                      <span className="text-xs text-gray-600 dark:text-gray-400">Status</span>
                    </div>
                    <p className="text-lg font-semibold text-gray-900 dark:text-white">
                      {selectedCustomer.is_verified ? 'Verified' : 'Unverified'}
                    </p>
                  </div>
                </div>
              </div>

              {/* Additional Info */}
              <div>
                <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">Additional Information</h4>
                <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600 dark:text-gray-400">Customer Type</span>
                    <span className={`px-2 py-1 text-xs rounded-full ${getTypeColor(selectedCustomer.customer_type || 'regular')}`}>
                      {selectedCustomer.customer_type || 'regular'}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600 dark:text-gray-400">Age Verified</span>
                    <span className="text-sm font-medium text-gray-900 dark:text-white">
                      {selectedCustomer.is_verified ? 'Yes' : 'No'}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600 dark:text-gray-400">Marketing Consent</span>
                    {isEditMode ? (
                      <input
                        type="checkbox"
                        checked={editedCustomer?.marketing_consent || false}
                        onChange={(e) => handleFieldChange('marketing_consent', e.target.checked)}
                        className="h-4 w-4 text-primary-600 dark:text-primary-400 rounded"
                      />
                    ) : (
                      <span className="text-sm font-medium text-gray-900 dark:text-white">
                        {selectedCustomer.marketing_consent ? 'Yes' : 'No'}
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {/* Recent Orders Section (placeholder) */}
              <div>
                <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">Recent Orders</h4>
                <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                  <p className="text-sm text-gray-500 dark:text-gray-400 text-center">
                    Order history will be displayed here
                  </p>
                </div>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="p-4 sm:p-6 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700 flex-shrink-0 sticky bottom-0">
              <div className="flex flex-col-reverse sm:flex-row justify-end gap-2 sm:gap-3">
                {isEditMode ? (
                  <>
                    <button
                      onClick={handleCancelEdit}
                      className="w-full sm:w-auto px-4 py-2.5 sm:py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600 font-medium transition-colors active:scale-95 touch-manipulation"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleSaveEdit}
                      disabled={updateMutation.isPending}
                      className="w-full sm:w-auto px-4 py-2.5 sm:py-2 bg-primary-600 dark:bg-primary-700 text-white rounded-lg hover:bg-primary-700 dark:hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed font-semibold transition-colors active:scale-95 touch-manipulation"
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
                      className="w-full sm:w-auto px-4 py-2.5 sm:py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600 font-medium transition-colors active:scale-95 touch-manipulation"
                    >
                      Close
                    </button>
                    <button
                      onClick={handleEditClick}
                      className="w-full sm:w-auto px-4 py-2.5 sm:py-2 bg-primary-600 dark:bg-primary-700 text-white rounded-lg hover:bg-primary-700 dark:hover:bg-primary-600 font-semibold transition-colors active:scale-95 touch-manipulation"
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