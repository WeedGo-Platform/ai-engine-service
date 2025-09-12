import React, { useState, useEffect } from 'react';
import { FiTruck, FiMapPin, FiCalendar, FiClock, FiUser, FiMail, FiPhone } from 'react-icons/fi';
import { CheckoutSession, DeliveryAddress, checkoutService } from '../../services/checkout';

interface DeliveryDetailsProps {
  session: CheckoutSession;
  onContinue: (data: any) => void;
  onBack: () => void;
  theme: any;
}

const DeliveryDetails: React.FC<DeliveryDetailsProps> = ({ session, onContinue, onBack, theme }) => {
  const [fulfillmentType, setFulfillmentType] = useState<'delivery' | 'pickup'>('delivery');
  const [customerInfo, setCustomerInfo] = useState({
    customer_email: session.customer_email || '',
    customer_phone: session.customer_phone || '',
    customer_first_name: session.customer_first_name || '',
    customer_last_name: session.customer_last_name || ''
  });
  
  const [deliveryAddress, setDeliveryAddress] = useState<DeliveryAddress>({
    street_address: '',
    unit_number: '',
    city: '',
    province_state: '',
    postal_code: '',
    country: 'CA'
  });
  
  const [pickupDetails, setPickupDetails] = useState({
    pickup_store_id: '',
    pickup_datetime: ''
  });
  
  const [deliveryInstructions, setDeliveryInstructions] = useState('');
  const [ageVerified, setAgeVerified] = useState(false);
  const [medicalCard, setMedicalCard] = useState({
    verified: false,
    number: ''
  });
  
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [pickupLocations, setPickupLocations] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadPickupLocations();
  }, []);

  const loadPickupLocations = async () => {
    try {
      const locations = await checkoutService.getPickupLocations();
      setPickupLocations(locations);
    } catch (error) {
      console.error('Failed to load pickup locations:', error);
    }
  };

  const validateForm = () => {
    const newErrors: Record<string, string> = {};
    
    // Customer info validation
    if (!customerInfo.customer_email) {
      newErrors.customer_email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(customerInfo.customer_email)) {
      newErrors.customer_email = 'Invalid email format';
    }
    
    if (!customerInfo.customer_phone) {
      newErrors.customer_phone = 'Phone number is required';
    }
    
    if (!customerInfo.customer_first_name) {
      newErrors.customer_first_name = 'First name is required';
    }
    
    if (!customerInfo.customer_last_name) {
      newErrors.customer_last_name = 'Last name is required';
    }
    
    // Delivery/Pickup validation
    if (fulfillmentType === 'delivery') {
      if (!deliveryAddress.street_address) {
        newErrors.street_address = 'Street address is required';
      }
      if (!deliveryAddress.city) {
        newErrors.city = 'City is required';
      }
      if (!deliveryAddress.province_state) {
        newErrors.province_state = 'Province is required';
      }
      if (!deliveryAddress.postal_code) {
        newErrors.postal_code = 'Postal code is required';
      }
    } else {
      if (!pickupDetails.pickup_store_id) {
        newErrors.pickup_store = 'Please select a pickup location';
      }
      if (!pickupDetails.pickup_datetime) {
        newErrors.pickup_datetime = 'Please select a pickup date and time';
      }
    }
    
    // Age verification
    if (!ageVerified) {
      newErrors.age_verification = 'You must be 19+ to place an order';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async () => {
    if (!validateForm()) return;
    
    setLoading(true);
    
    const data = {
      ...customerInfo,
      fulfillment_type: fulfillmentType as 'delivery' | 'pickup' | 'shipping',
      ...(fulfillmentType === 'delivery' ? {
        delivery_address: deliveryAddress,
        delivery_instructions: deliveryInstructions
      } : {
        ...pickupDetails
      }),
      age_verified: ageVerified,
      age_verification_method: 'self_declaration',
      medical_card_verified: medicalCard.verified,
      medical_card_number: medicalCard.verified ? medicalCard.number : undefined
    };
    
    onContinue(data);
  };

  const provinces = [
    { code: 'AB', name: 'Alberta' },
    { code: 'BC', name: 'British Columbia' },
    { code: 'MB', name: 'Manitoba' },
    { code: 'NB', name: 'New Brunswick' },
    { code: 'NL', name: 'Newfoundland and Labrador' },
    { code: 'NS', name: 'Nova Scotia' },
    { code: 'ON', name: 'Ontario' },
    { code: 'PE', name: 'Prince Edward Island' },
    { code: 'QC', name: 'Quebec' },
    { code: 'SK', name: 'Saskatchewan' }
  ];

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white rounded-lg shadow">
        {/* Fulfillment Type Selection */}
        <div className="p-6 border-b">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Fulfillment Method</h2>
          <div className="grid grid-cols-2 gap-4">
            <button
              onClick={() => setFulfillmentType('delivery')}
              className={`p-4 border-2 rounded-lg flex items-center space-x-3 transition-colors ${
                fulfillmentType === 'delivery' 
                  ? `border-blue-500 ${theme.secondary}` 
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <FiTruck className="w-5 h-5" />
              <span className="font-medium">Delivery</span>
            </button>
            
            <button
              onClick={() => setFulfillmentType('pickup')}
              className={`p-4 border-2 rounded-lg flex items-center space-x-3 transition-colors ${
                fulfillmentType === 'pickup' 
                  ? `border-blue-500 ${theme.secondary}` 
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <FiMapPin className="w-5 h-5" />
              <span className="font-medium">Pickup</span>
            </button>
          </div>
        </div>

        {/* Customer Information */}
        <div className="p-6 border-b">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Customer Information</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                <FiUser className="inline w-4 h-4 mr-1" />
                First Name
              </label>
              <input
                type="text"
                value={customerInfo.customer_first_name}
                onChange={(e) => setCustomerInfo({ ...customerInfo, customer_first_name: e.target.value })}
                className={`w-full px-3 py-2 border rounded-md focus:ring-blue-500 focus:border-blue-500 ${
                  errors.customer_first_name ? 'border-red-300' : 'border-gray-300'
                }`}
              />
              {errors.customer_first_name && (
                <p className="mt-1 text-sm text-red-600">{errors.customer_first_name}</p>
              )}
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                <FiUser className="inline w-4 h-4 mr-1" />
                Last Name
              </label>
              <input
                type="text"
                value={customerInfo.customer_last_name}
                onChange={(e) => setCustomerInfo({ ...customerInfo, customer_last_name: e.target.value })}
                className={`w-full px-3 py-2 border rounded-md focus:ring-blue-500 focus:border-blue-500 ${
                  errors.customer_last_name ? 'border-red-300' : 'border-gray-300'
                }`}
              />
              {errors.customer_last_name && (
                <p className="mt-1 text-sm text-red-600">{errors.customer_last_name}</p>
              )}
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                <FiMail className="inline w-4 h-4 mr-1" />
                Email
              </label>
              <input
                type="email"
                value={customerInfo.customer_email}
                onChange={(e) => setCustomerInfo({ ...customerInfo, customer_email: e.target.value })}
                className={`w-full px-3 py-2 border rounded-md focus:ring-blue-500 focus:border-blue-500 ${
                  errors.customer_email ? 'border-red-300' : 'border-gray-300'
                }`}
              />
              {errors.customer_email && (
                <p className="mt-1 text-sm text-red-600">{errors.customer_email}</p>
              )}
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                <FiPhone className="inline w-4 h-4 mr-1" />
                Phone
              </label>
              <input
                type="tel"
                value={customerInfo.customer_phone}
                onChange={(e) => setCustomerInfo({ ...customerInfo, customer_phone: e.target.value })}
                placeholder="(123) 456-7890"
                className={`w-full px-3 py-2 border rounded-md focus:ring-blue-500 focus:border-blue-500 ${
                  errors.customer_phone ? 'border-red-300' : 'border-gray-300'
                }`}
              />
              {errors.customer_phone && (
                <p className="mt-1 text-sm text-red-600">{errors.customer_phone}</p>
              )}
            </div>
          </div>
        </div>

        {/* Delivery Address or Pickup Location */}
        <div className="p-6 border-b">
          {fulfillmentType === 'delivery' ? (
            <>
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Delivery Address</h2>
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Street Address
                    </label>
                    <input
                      type="text"
                      value={deliveryAddress.street_address}
                      onChange={(e) => setDeliveryAddress({ ...deliveryAddress, street_address: e.target.value })}
                      className={`w-full px-3 py-2 border rounded-md focus:ring-blue-500 focus:border-blue-500 ${
                        errors.street_address ? 'border-red-300' : 'border-gray-300'
                      }`}
                    />
                    {errors.street_address && (
                      <p className="mt-1 text-sm text-red-600">{errors.street_address}</p>
                    )}
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Unit/Apt (Optional)
                    </label>
                    <input
                      type="text"
                      value={deliveryAddress.unit_number}
                      onChange={(e) => setDeliveryAddress({ ...deliveryAddress, unit_number: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      City
                    </label>
                    <input
                      type="text"
                      value={deliveryAddress.city}
                      onChange={(e) => setDeliveryAddress({ ...deliveryAddress, city: e.target.value })}
                      className={`w-full px-3 py-2 border rounded-md focus:ring-blue-500 focus:border-blue-500 ${
                        errors.city ? 'border-red-300' : 'border-gray-300'
                      }`}
                    />
                    {errors.city && (
                      <p className="mt-1 text-sm text-red-600">{errors.city}</p>
                    )}
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Province
                    </label>
                    <select
                      value={deliveryAddress.province_state}
                      onChange={(e) => setDeliveryAddress({ ...deliveryAddress, province_state: e.target.value })}
                      className={`w-full px-3 py-2 border rounded-md focus:ring-blue-500 focus:border-blue-500 ${
                        errors.province_state ? 'border-red-300' : 'border-gray-300'
                      }`}
                    >
                      <option value="">Select Province</option>
                      {provinces.map(prov => (
                        <option key={prov.code} value={prov.code}>{prov.name}</option>
                      ))}
                    </select>
                    {errors.province_state && (
                      <p className="mt-1 text-sm text-red-600">{errors.province_state}</p>
                    )}
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Postal Code
                    </label>
                    <input
                      type="text"
                      value={deliveryAddress.postal_code}
                      onChange={(e) => setDeliveryAddress({ ...deliveryAddress, postal_code: e.target.value.toUpperCase() })}
                      placeholder="A1A 1A1"
                      className={`w-full px-3 py-2 border rounded-md focus:ring-blue-500 focus:border-blue-500 ${
                        errors.postal_code ? 'border-red-300' : 'border-gray-300'
                      }`}
                    />
                    {errors.postal_code && (
                      <p className="mt-1 text-sm text-red-600">{errors.postal_code}</p>
                    )}
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Delivery Instructions (Optional)
                  </label>
                  <textarea
                    value={deliveryInstructions}
                    onChange={(e) => setDeliveryInstructions(e.target.value)}
                    rows={3}
                    placeholder="Gate code, special instructions, etc."
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>
            </>
          ) : (
            <>
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Pickup Details</h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    <FiMapPin className="inline w-4 h-4 mr-1" />
                    Pickup Location
                  </label>
                  <select
                    value={pickupDetails.pickup_store_id}
                    onChange={(e) => setPickupDetails({ ...pickupDetails, pickup_store_id: e.target.value })}
                    className={`w-full px-3 py-2 border rounded-md focus:ring-blue-500 focus:border-blue-500 ${
                      errors.pickup_store ? 'border-red-300' : 'border-gray-300'
                    }`}
                  >
                    <option value="">Select a location</option>
                    {pickupLocations.map(location => (
                      <option key={location.id} value={location.id}>
                        {location.name} - {location.address}
                      </option>
                    ))}
                  </select>
                  {errors.pickup_store && (
                    <p className="mt-1 text-sm text-red-600">{errors.pickup_store}</p>
                  )}
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    <FiCalendar className="inline w-4 h-4 mr-1" />
                    Pickup Date & Time
                  </label>
                  <input
                    type="datetime-local"
                    value={pickupDetails.pickup_datetime}
                    onChange={(e) => setPickupDetails({ ...pickupDetails, pickup_datetime: e.target.value })}
                    min={new Date().toISOString().slice(0, 16)}
                    className={`w-full px-3 py-2 border rounded-md focus:ring-blue-500 focus:border-blue-500 ${
                      errors.pickup_datetime ? 'border-red-300' : 'border-gray-300'
                    }`}
                  />
                  {errors.pickup_datetime && (
                    <p className="mt-1 text-sm text-red-600">{errors.pickup_datetime}</p>
                  )}
                </div>
              </div>
            </>
          )}
        </div>

        {/* Compliance */}
        <div className="p-6 border-b">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Age Verification & Compliance</h2>
          
          <div className="space-y-4">
            <label className="flex items-start">
              <input
                type="checkbox"
                checked={ageVerified}
                onChange={(e) => setAgeVerified(e.target.checked)}
                className="mt-1 mr-3 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <span className="text-sm text-gray-700">
                I confirm that I am 19 years of age or older and am legally allowed to purchase cannabis products in my province.
              </span>
            </label>
            {errors.age_verification && (
              <p className="text-sm text-red-600">{errors.age_verification}</p>
            )}
            
            <label className="flex items-start">
              <input
                type="checkbox"
                checked={medicalCard.verified}
                onChange={(e) => setMedicalCard({ ...medicalCard, verified: e.target.checked })}
                className="mt-1 mr-3 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <span className="text-sm text-gray-700">
                I have a valid medical cannabis authorization (optional)
              </span>
            </label>
            
            {medicalCard.verified && (
              <div className="ml-7">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Medical Authorization Number
                </label>
                <input
                  type="text"
                  value={medicalCard.number}
                  onChange={(e) => setMedicalCard({ ...medicalCard, number: e.target.value })}
                  placeholder="Enter your authorization number"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            )}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="p-6 flex justify-between">
          <button
            onClick={onBack}
            className="px-6 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors"
          >
            Back to Cart
          </button>
          
          <button
            onClick={handleSubmit}
            disabled={loading}
            className={`px-6 py-2 text-white rounded-md transition-colors disabled:opacity-50 ${theme.primary}`}
          >
            {loading ? 'Processing...' : 'Continue to Payment'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default DeliveryDetails;