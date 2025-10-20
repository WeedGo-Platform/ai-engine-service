import { useState, useEffect } from 'react';
import { getApiEndpoint } from '../../config/app.config';
import { X, Search, UserPlus, User, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import axios from 'axios';

interface Customer {
  id: string;
  name: string;
  email?: string;
  phone?: string;
  loyalty_points?: number;
  is_verified?: boolean;
  birth_date?: string;
  address?: {
    street: string;
    city: string;
    province: string;
    postal_code: string;
  };
}

interface CustomerModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelect: (customer: Customer) => void;
}

export default function CustomerModal({ isOpen, onClose, onSelect }: CustomerModalProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(false);
  const [showNewCustomerForm, setShowNewCustomerForm] = useState(false);
  const [newCustomer, setNewCustomer] = useState<Partial<Customer>>({
    name: '',
    email: '',
    phone: '',
    birth_date: ''
  });
  const [error, setError] = useState<string | null>(null);

  // Search customers
  const searchCustomers = async (query: string) => {
    if (!query) {
      setCustomers([]);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await axios.get(getApiEndpoint('/customers/search'), {
        params: { q: query }
      });
      setCustomers(response.data.customers || []);
    } catch (err) {
      console.error('Error searching customers:', err);
      setError('Failed to search customers');
      setCustomers([]);
    } finally {
      setLoading(false);
    }
  };

  // Debounced search
  useEffect(() => {
    const timer = setTimeout(() => {
      if (searchTerm) {
        searchCustomers(searchTerm);
      } else {
        setCustomers([]);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [searchTerm]);

  // Create new customer
  const handleCreateCustomer = async () => {
    if (!newCustomer.name || !newCustomer.birth_date) {
      setError('Name and birth date are required');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await axios.post(getApiEndpoint('/customers'), newCustomer);
      const created = response.data;
      
      // Verify age
      if (newCustomer.birth_date) {
        const ageResponse = await axios.post(getApiEndpoint('/customers/verify-age'), {
          birth_date: newCustomer.birth_date
        });
        created.is_verified = ageResponse.data.is_valid;
      }

      onSelect(created);
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create customer');
    } finally {
      setLoading(false);
    }
  };

  // Calculate age from birth date
  const calculateAge = (birthDate: string) => {
    const birth = new Date(birthDate);
    const today = new Date();
    let age = today.getFullYear() - birth.getFullYear();
    const monthDiff = today.getMonth() - birth.getMonth();
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
      age--;
    }
    return age;
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black dark:bg-black bg-opacity-50 dark:bg-opacity-70 flex items-center justify-center z-50 p-0 sm:p-4 transition-colors duration-200">
      <div className="bg-white dark:bg-gray-800 h-full sm:h-auto sm:rounded-lg border-0 sm:border border-gray-200 dark:border-gray-700 w-full sm:max-w-2xl overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-4 sm:p-6 border-b border-gray-200 dark:border-gray-700 sticky top-0 bg-white dark:bg-gray-800 z-10">
          <h2 className="text-lg sm:text-2xl font-bold text-gray-900 dark:text-white">
            {showNewCustomerForm ? 'New Customer' : 'Select Customer'}
          </h2>
          <button
            onClick={onClose}
            className="p-2 -mr-2 text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
            aria-label="Close customer modal"
          >
            <X className="w-5 h-5 sm:w-6 sm:h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-4 sm:p-6">
          {!showNewCustomerForm ? (
            <>
              {/* Search */}
              <div className="mb-6">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 dark:text-gray-500 w-5 h-5" />
                  <input
                    type="text"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    placeholder="Search by name, email, or phone..."
                    className="w-full pl-10 pr-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 transition-colors"
                    autoFocus
                  />
                </div>
              </div>

              {/* Customer List */}
              <div className="space-y-2 max-h-[60vh] sm:max-h-96 overflow-y-auto">
                {loading ? (
                  <div className="text-center py-8">
                    <Loader2 className="w-6 h-6 sm:w-8 sm:h-8 animate-spin mx-auto mb-2 text-gray-400 dark:text-gray-500" />
                    <p className="text-sm sm:text-base text-gray-500 dark:text-gray-400">Searching...</p>
                  </div>
                ) : customers.length > 0 ? (
                  customers.map(customer => (
                    <button
                      key={customer.id}
                      onClick={() => {
                        onSelect(customer);
                        onClose();
                      }}
                      className="w-full p-4 sm:p-6 bg-gray-50 dark:bg-gray-700 hover:bg-gray-100 dark:hover:bg-gray-600 rounded-lg text-left transition-colors border border-transparent dark:border-gray-600 active:scale-[0.98] touch-manipulation"
                    >
                      <div className="flex items-start justify-between">
                        <div>
                          <div className="flex items-center gap-2">
                            <p className="font-medium text-gray-900 dark:text-white">{customer.name}</p>
                            {customer.is_verified && (
                              <CheckCircle className="w-4 h-4 text-primary-500" />
                            )}
                          </div>
                          {customer.email && (
                            <p className="text-sm text-gray-600 dark:text-gray-300">{customer.email}</p>
                          )}
                          {customer.phone && (
                            <p className="text-sm text-gray-600 dark:text-gray-300">{customer.phone}</p>
                          )}
                          {customer.birth_date && (
                            <p className="text-sm text-gray-500 dark:text-gray-400">
                              Age: {calculateAge(customer.birth_date)} years
                            </p>
                          )}
                        </div>
                        {customer.loyalty_points && (
                          <div className="text-right">
                            <p className="text-sm text-gray-500 dark:text-gray-400">Points</p>
                            <p className="font-medium text-primary-600 dark:text-primary-400">{customer.loyalty_points}</p>
                          </div>
                        )}
                      </div>
                    </button>
                  ))
                ) : searchTerm ? (
                  <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                    <User className="w-12 h-12 mx-auto mb-2" />
                    <p>No customers found</p>
                    <button
                      onClick={() => {
                        setShowNewCustomerForm(true);
                        setNewCustomer({ ...newCustomer, name: searchTerm });
                      }}
                      className="mt-4 px-4 py-2 bg-accent-500 dark:bg-accent-600 text-white rounded-lg hover:bg-accent-600 dark:hover:bg-accent-700 transition-colors"
                    >
                      <UserPlus className="w-4 h-4 inline mr-2" />
                      Create New Customer
                    </button>
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-400 dark:text-gray-500">
                    <p>Enter a search term to find customers</p>
                  </div>
                )}
              </div>

              {/* Quick Actions */}
              <div className="mt-6 flex flex-col sm:flex-row gap-2 sm:gap-4">
                <button
                  onClick={() => setShowNewCustomerForm(true)}
                  className="flex-1 px-4 py-2.5 sm:py-2 bg-primary-500 dark:bg-primary-600 text-white rounded-lg hover:bg-primary-600 dark:hover:bg-primary-700 transition-colors active:scale-95 font-medium touch-manipulation"
                >
                  <UserPlus className="w-4 h-4 inline mr-2" />
                  New Customer
                </button>
                <button
                  onClick={() => {
                    onSelect({
                      id: 'anonymous',
                      name: 'Anonymous Customer',
                      is_verified: true
                    });
                    onClose();
                  }}
                  className="flex-1 px-4 py-2.5 sm:py-2 bg-gray-500 dark:bg-gray-600 text-white rounded-lg hover:bg-gray-600 dark:hover:bg-gray-700 transition-colors active:scale-95 font-medium touch-manipulation"
                >
                  <User className="w-4 h-4 inline mr-2" />
                  Anonymous Sale
                </button>
              </div>
            </>
          ) : (
            /* New Customer Form */
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Full Name *
                </label>
                <input
                  type="text"
                  value={newCustomer.name}
                  onChange={(e) => setNewCustomer({ ...newCustomer, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 transition-colors"
                  placeholder="John Doe"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Birth Date * (for age verification)
                </label>
                <input
                  type="date"
                  value={newCustomer.birth_date}
                  onChange={(e) => setNewCustomer({ ...newCustomer, birth_date: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 transition-colors"
                  max={new Date().toISOString().split('T')[0]}
                />
                {newCustomer.birth_date && (
                  <p className={`text-sm mt-1 ${
                    calculateAge(newCustomer.birth_date) >= 19 ? 'text-primary-600 dark:text-primary-400' : 'text-danger-600 dark:text-red-400'
                  }`}>
                    Age: {calculateAge(newCustomer.birth_date)} years
                    {calculateAge(newCustomer.birth_date) < 19 && ' (Must be 19+ to purchase)'}
                  </p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Email
                </label>
                <input
                  type="email"
                  value={newCustomer.email}
                  onChange={(e) => setNewCustomer({ ...newCustomer, email: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 transition-colors"
                  placeholder="john@example.com"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Phone
                </label>
                <input
                  type="tel"
                  value={newCustomer.phone}
                  onChange={(e) => setNewCustomer({ ...newCustomer, phone: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 transition-colors"
                  placeholder="(555) 123-4567"
                />
              </div>

              {/* Error Message */}
              {error && (
                <div className="p-4 bg-danger-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-center gap-2 transition-colors">
                  <AlertCircle className="w-5 h-5 text-red-500 dark:text-red-400" />
                  <span className="text-sm text-red-700 dark:text-red-400">{error}</span>
                </div>
              )}

              {/* Form Actions */}
              <div className="flex flex-col-reverse sm:flex-row gap-2 sm:gap-4 pt-4">
                <button
                  onClick={() => {
                    setShowNewCustomerForm(false);
                    setNewCustomer({ name: '', email: '', phone: '', birth_date: '' });
                    setError(null);
                  }}
                  className="flex-1 px-4 py-2.5 sm:py-2 text-gray-700 dark:text-gray-300 bg-gray-50 dark:bg-gray-600 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-500 transition-colors active:scale-95 font-medium touch-manipulation"
                >
                  Back
                </button>
                <button
                  onClick={handleCreateCustomer}
                  disabled={loading || !newCustomer.name || !newCustomer.birth_date}
                  className="flex-1 px-4 py-2.5 sm:py-2 bg-accent-500 dark:bg-accent-600 text-white rounded-lg hover:bg-accent-600 dark:hover:bg-accent-700 disabled:bg-gray-300 dark:disabled:bg-gray-600 disabled:cursor-not-allowed transition-colors active:scale-95 font-semibold touch-manipulation"
                >
                  {loading ? (
                    <>
                      <Loader2 className="w-4 h-4 inline mr-2 animate-spin" />
                      <span>Creating...</span>
                    </>
                  ) : (
                    'Create Customer'
                  )}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}