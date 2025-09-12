import React, { useState, useRef } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { 
  ArrowLeft, ArrowRight, CheckCircle, AlertCircle,
  Building2, Mail, Phone, Globe, CreditCard, Lock, Leaf,
  Eye, EyeOff, Shield
} from 'lucide-react';
import tenantService from '../services/tenantService';

interface FormData {
  // Company Information
  companyName: string;
  businessNumber: string;
  gstHstNumber: string;
  website: string;
  
  // Address
  street: string;
  city: string;
  province: string;
  postalCode: string;
  
  // Contact Details
  contactEmail: string;
  contactPhone: string;
  firstName: string;
  lastName: string;
  
  // Account Setup
  tenantName: string;
  tenantCode: string;
  password: string;
  confirmPassword: string;
  
  // Subscription
  subscriptionTier: string;
  billingCycle: string;
  
  // Payment
  cardNumber: string;
  expiryDate: string;
  cvv: string;
  billingName: string;
}

interface FormErrors {
  [key: string]: string;
}

const TenantSignup = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const selectedPlan = searchParams.get('plan') || 'community';
  
  const [currentStep, setCurrentStep] = useState(1);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [createdUserId, setCreatedUserId] = useState<string | null>(null);
  
  // Voice recording states
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null);
  const [voiceRegistrationStatus, setVoiceRegistrationStatus] = useState<'idle' | 'registering' | 'success' | 'error'>('idle');
  const audioRef = useRef<HTMLAudioElement>(null);
  const [formData, setFormData] = useState<FormData>({
    companyName: '',
    businessNumber: '',
    gstHstNumber: '',
    website: '',
    street: '',
    city: '',
    province: 'ON',
    postalCode: '',
    contactEmail: '',
    contactPhone: '',
    firstName: '',
    lastName: '',
    tenantName: '',
    tenantCode: '',
    password: '',
    confirmPassword: '',
    subscriptionTier: selectedPlan,
    billingCycle: 'monthly',
    cardNumber: '',
    expiryDate: '',
    cvv: '',
    billingName: ''
  });
  
  const [errors, setErrors] = useState<FormErrors>({});
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [passwordStrength, setPasswordStrength] = useState(0);

  const provinces = [
    { code: 'ON', name: 'Ontario' },
    { code: 'BC', name: 'British Columbia' },
    { code: 'AB', name: 'Alberta' },
    { code: 'QC', name: 'Quebec' },
    { code: 'MB', name: 'Manitoba' },
    { code: 'SK', name: 'Saskatchewan' },
    { code: 'NS', name: 'Nova Scotia' },
    { code: 'NB', name: 'New Brunswick' },
    { code: 'NL', name: 'Newfoundland and Labrador' },
    { code: 'PE', name: 'Prince Edward Island' },
    { code: 'NT', name: 'Northwest Territories' },
    { code: 'YT', name: 'Yukon' },
    { code: 'NU', name: 'Nunavut' }
  ];

  const subscriptionPlans = {
    community: { name: 'Community', price: 0, features: ['1 Store', '2 Languages', '1 AI Personality'] },
    basic: { name: 'Basic', price: 99, features: ['5 Stores', '5 Languages', '2 AI Personalities'] },
    small_business: { name: 'Small Business', price: 149, features: ['12 Stores', '10 Languages', '3 AI Personalities'] },
    enterprise: { name: 'Enterprise', price: 299, features: ['Unlimited Stores', '25+ Languages', '5 AI Personalities'] }
  };

  const validateStep = (step: number): boolean => {
    const newErrors: FormErrors = {};
    
    switch (step) {
      case 1: // Company Information
        if (!formData.companyName.trim()) newErrors.companyName = 'Company name is required';
        if (!formData.tenantName.trim()) newErrors.tenantName = 'Brand name is required';
        if (!formData.tenantCode.trim()) newErrors.tenantCode = 'Tenant code is required';
        else if (!/^[A-Z0-9_-]+$/.test(formData.tenantCode)) {
          newErrors.tenantCode = 'Tenant code must contain only uppercase letters, numbers, hyphens, and underscores';
        }
        if (formData.businessNumber && !/^\d{9}$/.test(formData.businessNumber.replace(/\D/g, ''))) {
          newErrors.businessNumber = 'Business number must be 9 digits';
        }
        if (formData.gstHstNumber && !/^\d{9}RT\d{4}$/.test(formData.gstHstNumber.replace(/\s/g, ''))) {
          newErrors.gstHstNumber = 'GST/HST number format: 123456789RT0001';
        }
        break;
        
      case 2: // Contact Details
        if (!formData.contactEmail.trim()) newErrors.contactEmail = 'Email is required';
        else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.contactEmail)) {
          newErrors.contactEmail = 'Please enter a valid email address';
        }
        if (!formData.firstName.trim()) newErrors.firstName = 'First name is required';
        if (!formData.lastName.trim()) newErrors.lastName = 'Last name is required';
        if (!formData.street.trim()) newErrors.street = 'Street address is required';
        if (!formData.city.trim()) newErrors.city = 'City is required';
        if (!formData.postalCode.trim()) newErrors.postalCode = 'Postal code is required';
        else if (!/^[A-Z]\d[A-Z]\s?\d[A-Z]\d$/.test(formData.postalCode.toUpperCase())) {
          newErrors.postalCode = 'Please enter a valid Canadian postal code';
        }
        break;
        
      case 3: // Account Setup
        if (!formData.password) newErrors.password = 'Password is required';
        else if (formData.password.length < 8) {
          newErrors.password = 'Password must be at least 8 characters';
        } else if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(formData.password)) {
          newErrors.password = 'Password must contain uppercase, lowercase, and number';
        }
        if (formData.password !== formData.confirmPassword) {
          newErrors.confirmPassword = 'Passwords do not match';
        }
        break;
        
      case 4: // Payment
        if (formData.subscriptionTier !== 'enterprise' && formData.subscriptionTier !== 'community') {
          if (!formData.cardNumber.trim()) newErrors.cardNumber = 'Card number is required';
          else if (!/^\d{16}$/.test(formData.cardNumber.replace(/\s/g, ''))) {
            newErrors.cardNumber = 'Please enter a valid 16-digit card number';
          }
          if (!formData.expiryDate.trim()) newErrors.expiryDate = 'Expiry date is required';
          else if (!/^(0[1-9]|1[0-2])\/\d{2}$/.test(formData.expiryDate)) {
            newErrors.expiryDate = 'Please enter MM/YY format';
          }
          if (!formData.cvv.trim()) newErrors.cvv = 'CVV is required';
          else if (!/^\d{3,4}$/.test(formData.cvv)) {
            newErrors.cvv = 'CVV must be 3 or 4 digits';
          }
          if (!formData.billingName.trim()) newErrors.billingName = 'Cardholder name is required';
        }
        break;
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const calculatePasswordStrength = (password: string): number => {
    let strength = 0;
    if (password.length >= 8) strength += 25;
    if (password.length >= 12) strength += 10;
    if (/[a-z]/.test(password)) strength += 20;
    if (/[A-Z]/.test(password)) strength += 20;
    if (/\d/.test(password)) strength += 20;
    if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) strength += 15;
    return Math.min(strength, 100);
  };

  const getPasswordStrengthColor = (strength: number): string => {
    if (strength < 30) return 'bg-red-500';
    if (strength < 50) return 'bg-orange-500';
    if (strength < 70) return 'bg-yellow-500';
    if (strength < 90) return 'bg-green-500';
    return 'bg-green-600';
  };

  const getPasswordStrengthText = (strength: number): string => {
    if (strength < 30) return 'Weak';
    if (strength < 50) return 'Fair';
    if (strength < 70) return 'Good';
    if (strength < 90) return 'Strong';
    return 'Very Strong';
  };

  const handleInputChange = (field: keyof FormData, value: string) => {
    let formattedValue = value;
    
    // Auto-format certain fields
    if (field === 'tenantCode') {
      formattedValue = value.toUpperCase().replace(/[^A-Z0-9_-]/g, '');
    } else if (field === 'postalCode') {
      formattedValue = value.toUpperCase().replace(/[^A-Z0-9]/g, '');
      if (formattedValue.length > 3) {
        formattedValue = formattedValue.slice(0, 3) + ' ' + formattedValue.slice(3, 6);
      }
    } else if (field === 'cardNumber') {
      formattedValue = value.replace(/\D/g, '').replace(/(\d{4})(?=\d)/g, '$1 ');
    } else if (field === 'expiryDate') {
      formattedValue = value.replace(/\D/g, '');
      if (formattedValue.length >= 2) {
        formattedValue = formattedValue.slice(0, 2) + '/' + formattedValue.slice(2, 4);
      }
    } else if (field === 'cvv') {
      formattedValue = value.replace(/\D/g, '').slice(0, 4);
    }
    
    // Update password strength when password changes
    if (field === 'password') {
      setPasswordStrength(calculatePasswordStrength(value));
    }
    
    setFormData(prev => ({ ...prev, [field]: formattedValue }));
    
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  const nextStep = () => {
    if (validateStep(currentStep)) {
      setCurrentStep(prev => Math.min(prev + 1, 4));
    }
  };

  const prevStep = () => {
    setCurrentStep(prev => Math.max(prev - 1, 1));
  };

  const handleSubmit = async () => {
    if (!validateStep(4)) return;
    
    setIsSubmitting(true);
    
    try {
      // Prepare the payload according to backend API
      const payload = {
        name: formData.tenantName,
        code: formData.tenantCode,
        company_name: formData.companyName,
        business_number: formData.businessNumber || undefined,
        gst_hst_number: formData.gstHstNumber || undefined,
        address: {
          street: formData.street,
          city: formData.city,
          province: formData.province,
          postal_code: formData.postalCode,
          country: 'Canada'
        },
        contact_email: formData.contactEmail,
        contact_phone: formData.contactPhone || undefined,
        website: formData.website || undefined,
        subscription_tier: formData.subscriptionTier as 'community' | 'basic' | 'small_business' | 'enterprise',
        settings: {
          admin_user: {
            first_name: formData.firstName,
            last_name: formData.lastName,
            email: formData.contactEmail,
            password: formData.password
          },
          billing: {
            cycle: formData.billingCycle,
            card_last_four: formData.cardNumber.slice(-4),
            cardholder_name: formData.billingName
          }
        }
      };

      const result = await tenantService.createTenant(payload);
      
      // Store the created user ID for voice registration
      if (result?.settings?.admin_user?.id) {
        setCreatedUserId(result.settings.admin_user.id);
        setCurrentStep(5); // Move to voice registration step
      } else {
        // If no user ID returned, skip voice registration
        navigate('/signup-success', { 
          state: { 
            tenantName: formData.tenantName,
            tenantCode: formData.tenantCode 
          } 
        });
      }
      
    } catch (error: any) {
      console.error('Signup error:', error);
      
      // Parse error response for specific messages
      let errorMessage = 'Failed to create account';
      let shouldRedirectToUserRegistration = false;
      
      if (error.response?.data?.detail) {
        const detail = error.response.data.detail;
        
        // Check for specific error types
        if (detail.includes('already exists')) {
          if (detail.includes('Tenant')) {
            // Tenant already exists - redirect to user registration
            shouldRedirectToUserRegistration = true;
            errorMessage = 'This tenant already exists. Redirecting you to user registration...';
          } else if (detail.includes('User') || detail.includes('email')) {
            errorMessage = 'A user with this email already exists. Please use a different email or login instead.';
          } else {
            errorMessage = detail;
          }
        } else if (detail.includes('duplicate key')) {
          if (detail.includes('tenants_name_key') || detail.includes('tenants_code_key')) {
            // Tenant already exists - redirect to user registration
            shouldRedirectToUserRegistration = true;
            errorMessage = 'This tenant already exists. Redirecting you to user registration...';
          } else if (detail.includes('users_email_key')) {
            errorMessage = 'This email is already registered. Please use a different email or login instead.';
          } else {
            errorMessage = 'This information is already registered in our system.';
          }
        } else {
          errorMessage = detail;
        }
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      setErrors({ submit: errorMessage });
      
      // If tenant exists, redirect to user registration after a short delay
      if (shouldRedirectToUserRegistration) {
        setTimeout(() => {
          navigate('/user-registration', {
            state: {
              tenantCode: formData.tenantCode,
              tenantName: formData.tenantName,
              contactEmail: formData.contactEmail,
              firstName: formData.firstName,
              lastName: formData.lastName,
              phone: formData.contactPhone
            }
          });
        }, 2000);
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Brand/Tenant Name *
              </label>
              <input
                type="text"
                value={formData.tenantName}
                onChange={(e) => handleInputChange('tenantName', e.target.value)}
                className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 ${
                  errors.tenantName ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="e.g., Green Valley Dispensary"
              />
              {errors.tenantName && (
                <p className="mt-1 text-sm text-red-600">{errors.tenantName}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Tenant Code * (used in URLs)
              </label>
              <input
                type="text"
                value={formData.tenantCode}
                onChange={(e) => handleInputChange('tenantCode', e.target.value)}
                className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 ${
                  errors.tenantCode ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="e.g., GREEN-VALLEY"
              />
              <p className="mt-1 text-sm text-gray-500">
                Will be used in your store URL: {formData.tenantCode.toLowerCase() || 'your-code'}.weedgo.com
              </p>
              {errors.tenantCode && (
                <p className="mt-1 text-sm text-red-600">{errors.tenantCode}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Legal Company Name *
              </label>
              <input
                type="text"
                value={formData.companyName}
                onChange={(e) => handleInputChange('companyName', e.target.value)}
                className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 ${
                  errors.companyName ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="e.g., Green Valley Cannabis Inc."
              />
              {errors.companyName && (
                <p className="mt-1 text-sm text-red-600">{errors.companyName}</p>
              )}
            </div>

            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Business Number
                </label>
                <input
                  type="text"
                  value={formData.businessNumber}
                  onChange={(e) => handleInputChange('businessNumber', e.target.value)}
                  className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 ${
                    errors.businessNumber ? 'border-red-500' : 'border-gray-300'
                  }`}
                  placeholder="123456789"
                />
                <p className="mt-1 text-sm text-gray-500">
                  Canadian Business Number (9 digits)
                </p>
                {errors.businessNumber && (
                  <p className="mt-1 text-sm text-red-600">{errors.businessNumber}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  GST/HST Number
                </label>
                <input
                  type="text"
                  value={formData.gstHstNumber}
                  onChange={(e) => handleInputChange('gstHstNumber', e.target.value)}
                  className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 ${
                    errors.gstHstNumber ? 'border-red-500' : 'border-gray-300'
                  }`}
                  placeholder="123456789RT0001"
                />
                <p className="mt-1 text-sm text-gray-500">
                  Optional - Format: 123456789RT0001
                </p>
                {errors.gstHstNumber && (
                  <p className="mt-1 text-sm text-red-600">{errors.gstHstNumber}</p>
                )}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Website
              </label>
              <input
                type="url"
                value={formData.website}
                onChange={(e) => handleInputChange('website', e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
                placeholder="https://www.yoursite.com"
              />
            </div>
          </div>
        );

      case 2:
        return (
          <div className="space-y-6">
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  First Name *
                </label>
                <input
                  type="text"
                  value={formData.firstName}
                  onChange={(e) => handleInputChange('firstName', e.target.value)}
                  className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 ${
                    errors.firstName ? 'border-red-500' : 'border-gray-300'
                  }`}
                />
                {errors.firstName && (
                  <p className="mt-1 text-sm text-red-600">{errors.firstName}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Last Name *
                </label>
                <input
                  type="text"
                  value={formData.lastName}
                  onChange={(e) => handleInputChange('lastName', e.target.value)}
                  className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 ${
                    errors.lastName ? 'border-red-500' : 'border-gray-300'
                  }`}
                />
                {errors.lastName && (
                  <p className="mt-1 text-sm text-red-600">{errors.lastName}</p>
                )}
              </div>
            </div>

            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Email Address *
                </label>
                <input
                  type="email"
                  value={formData.contactEmail}
                  onChange={(e) => handleInputChange('contactEmail', e.target.value)}
                  className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 ${
                    errors.contactEmail ? 'border-red-500' : 'border-gray-300'
                  }`}
                />
                {errors.contactEmail && (
                  <p className="mt-1 text-sm text-red-600">{errors.contactEmail}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Phone Number
                </label>
                <input
                  type="tel"
                  value={formData.contactPhone}
                  onChange={(e) => handleInputChange('contactPhone', e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
                  placeholder="(555) 123-4567"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Street Address *
              </label>
              <input
                type="text"
                value={formData.street}
                onChange={(e) => handleInputChange('street', e.target.value)}
                className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 ${
                  errors.street ? 'border-red-500' : 'border-gray-300'
                }`}
              />
              {errors.street && (
                <p className="mt-1 text-sm text-red-600">{errors.street}</p>
              )}
            </div>

            <div className="grid md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  City *
                </label>
                <input
                  type="text"
                  value={formData.city}
                  onChange={(e) => handleInputChange('city', e.target.value)}
                  className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 ${
                    errors.city ? 'border-red-500' : 'border-gray-300'
                  }`}
                />
                {errors.city && (
                  <p className="mt-1 text-sm text-red-600">{errors.city}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Province *
                </label>
                <select
                  value={formData.province}
                  onChange={(e) => handleInputChange('province', e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
                >
                  {provinces.map(province => (
                    <option key={province.code} value={province.code}>
                      {province.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Postal Code *
                </label>
                <input
                  type="text"
                  value={formData.postalCode}
                  onChange={(e) => handleInputChange('postalCode', e.target.value)}
                  className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 ${
                    errors.postalCode ? 'border-red-500' : 'border-gray-300'
                  }`}
                  placeholder="A1A 1A1"
                />
                {errors.postalCode && (
                  <p className="mt-1 text-sm text-red-600">{errors.postalCode}</p>
                )}
              </div>
            </div>
          </div>
        );

      case 3:
        return (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Password *
              </label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  value={formData.password}
                  onChange={(e) => handleInputChange('password', e.target.value)}
                  className={`w-full px-4 py-3 pr-12 border rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 ${
                    errors.password ? 'border-red-500' : 'border-gray-300'
                  }`}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-500 hover:text-gray-700"
                >
                  {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                </button>
              </div>
              
              {/* Password Strength Indicator */}
              {formData.password && (
                <div className="mt-2">
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center">
                      <Shield className="h-3 w-3 text-gray-500 mr-1" />
                      <span className="text-xs text-gray-600">Strength:</span>
                    </div>
                    <span className={`text-xs font-medium ${
                      passwordStrength < 30 ? 'text-red-600' :
                      passwordStrength < 50 ? 'text-orange-600' :
                      passwordStrength < 70 ? 'text-yellow-600' :
                      passwordStrength < 90 ? 'text-green-600' :
                      'text-green-700'
                    }`}>
                      {getPasswordStrengthText(passwordStrength)}
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full transition-all duration-300 ${getPasswordStrengthColor(passwordStrength)}`}
                      style={{ width: `${passwordStrength}%` }}
                    />
                  </div>
                </div>
              )}
              
              <p className="mt-1 text-sm text-gray-500">
                Must be at least 8 characters with uppercase, lowercase, and number
              </p>
              {errors.password && (
                <p className="mt-1 text-sm text-red-600">{errors.password}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Confirm Password *
              </label>
              <div className="relative">
                <input
                  type={showConfirmPassword ? "text" : "password"}
                  value={formData.confirmPassword}
                  onChange={(e) => handleInputChange('confirmPassword', e.target.value)}
                  className={`w-full px-4 py-3 pr-12 border rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 ${
                    errors.confirmPassword ? 'border-red-500' : 'border-gray-300'
                  }`}
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-500 hover:text-gray-700"
                >
                  {showConfirmPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                </button>
              </div>
              {errors.confirmPassword && (
                <p className="mt-1 text-sm text-red-600">{errors.confirmPassword}</p>
              )}
            </div>

            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="flex items-start">
                <CheckCircle className="h-5 w-5 text-green-600 mt-0.5 mr-3" />
                <div>
                  <h3 className="font-medium text-green-900">Account Security</h3>
                  <p className="text-sm text-green-700 mt-1">
                    Your account will be secured with industry-standard encryption and multi-factor authentication options.
                  </p>
                </div>
              </div>
            </div>
          </div>
        );

      case 4:
        const selectedPlanInfo = subscriptionPlans[formData.subscriptionTier as keyof typeof subscriptionPlans];
        
        return (
          <div className="space-y-6">
            {/* Plan Summary */}
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-2">Selected Plan: {selectedPlanInfo.name}</h3>
              <div className="text-2xl font-bold text-green-600 mb-2">
                {selectedPlanInfo.price === 0 ? 'FREE' : 
                 selectedPlanInfo.price ? `$${selectedPlanInfo.price}/month` : 'Custom Pricing'}
              </div>
              <ul className="text-sm text-gray-600 space-y-1">
                {selectedPlanInfo.features.map((feature, index) => (
                  <li key={index} className="flex items-center">
                    <CheckCircle className="h-4 w-4 text-green-500 mr-2" />
                    {feature}
                  </li>
                ))}
              </ul>
            </div>

            {/* Billing Cycle */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Billing Cycle
              </label>
              <div className="grid grid-cols-2 gap-4">
                <label className="flex items-center p-4 border rounded-lg cursor-pointer hover:bg-gray-50">
                  <input
                    type="radio"
                    name="billingCycle"
                    value="monthly"
                    checked={formData.billingCycle === 'monthly'}
                    onChange={(e) => handleInputChange('billingCycle', e.target.value)}
                    className="mr-3"
                  />
                  <div>
                    <div className="font-medium">Monthly</div>
                    <div className="text-sm text-gray-500">Billed monthly</div>
                  </div>
                </label>
                <label className="flex items-center p-4 border rounded-lg cursor-pointer hover:bg-gray-50">
                  <input
                    type="radio"
                    name="billingCycle"
                    value="annual"
                    checked={formData.billingCycle === 'annual'}
                    onChange={(e) => handleInputChange('billingCycle', e.target.value)}
                    className="mr-3"
                  />
                  <div>
                    <div className="font-medium">Annual</div>
                    <div className="text-sm text-gray-500">Save 20%</div>
                  </div>
                </label>
              </div>
            </div>

            {/* Payment Information - Skip for Community and Enterprise */}
            {formData.subscriptionTier !== 'enterprise' && formData.subscriptionTier !== 'community' && (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Cardholder Name *
                  </label>
                  <input
                    type="text"
                    value={formData.billingName}
                    onChange={(e) => handleInputChange('billingName', e.target.value)}
                    className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 ${
                      errors.billingName ? 'border-red-500' : 'border-gray-300'
                    }`}
                  />
                  {errors.billingName && (
                    <p className="mt-1 text-sm text-red-600">{errors.billingName}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Card Number *
                  </label>
                  <input
                    type="text"
                    value={formData.cardNumber}
                    onChange={(e) => handleInputChange('cardNumber', e.target.value)}
                    className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 ${
                      errors.cardNumber ? 'border-red-500' : 'border-gray-300'
                    }`}
                    placeholder="1234 5678 9012 3456"
                    maxLength={19}
                  />
                  {errors.cardNumber && (
                    <p className="mt-1 text-sm text-red-600">{errors.cardNumber}</p>
                  )}
                </div>

                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Expiry Date *
                    </label>
                    <input
                      type="text"
                      value={formData.expiryDate}
                      onChange={(e) => handleInputChange('expiryDate', e.target.value)}
                      className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 ${
                        errors.expiryDate ? 'border-red-500' : 'border-gray-300'
                      }`}
                      placeholder="MM/YY"
                      maxLength={5}
                    />
                    {errors.expiryDate && (
                      <p className="mt-1 text-sm text-red-600">{errors.expiryDate}</p>
                    )}
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      CVV *
                    </label>
                    <input
                      type="text"
                      value={formData.cvv}
                      onChange={(e) => handleInputChange('cvv', e.target.value)}
                      className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 ${
                        errors.cvv ? 'border-red-500' : 'border-gray-300'
                      }`}
                      placeholder="123"
                    />
                    {errors.cvv && (
                      <p className="mt-1 text-sm text-red-600">{errors.cvv}</p>
                    )}
                  </div>
                </div>
              </>
            )}

            {formData.subscriptionTier === 'enterprise' && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-start">
                  <AlertCircle className="h-5 w-5 text-blue-600 mt-0.5 mr-3" />
                  <div>
                    <h3 className="font-medium text-blue-900">Enterprise Plan</h3>
                    <p className="text-sm text-blue-700 mt-1">
                      Our sales team will contact you within 24 hours to discuss custom pricing and setup.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {errors.submit && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="flex items-start">
                  <AlertCircle className="h-5 w-5 text-red-600 mt-0.5 mr-3" />
                  <p className="text-sm text-red-700">{errors.submit}</p>
                </div>
              </div>
            )}
          </div>
        );

      default:
        return null;
    }
  };

  const stepTitles = [
    'Company Information',
    'Contact Details',
    'Account Setup',
    'Subscription & Payment'
  ];

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between py-6">
            <Link to="/" className="flex items-center">
              <ArrowLeft className="h-5 w-5 text-gray-400 mr-2" />
              <Leaf className="h-8 w-8 text-green-600" />
              <span className="ml-2 text-2xl font-bold text-gray-900">WeedGo</span>
            </Link>
            <div className="text-sm text-gray-500">
              Already have an account? <Link to="/login" className="text-green-600 hover:text-green-700">Sign in</Link>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 py-12">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Progress Bar */}
          <div className="mb-8">
            <div className="flex items-center justify-between">
              {stepTitles.map((title, index) => (
                <div key={index} className="flex items-center">
                  <div className={`flex items-center justify-center w-10 h-10 rounded-full border-2 ${
                    index + 1 <= currentStep
                      ? 'bg-green-600 border-green-600 text-white'
                      : 'border-gray-300 text-gray-400'
                  }`}>
                    {index + 1 < currentStep ? (
                      <CheckCircle className="h-6 w-6" />
                    ) : (
                      <span>{index + 1}</span>
                    )}
                  </div>
                  {index < stepTitles.length - 1 && (
                    <div className={`flex-1 h-1 mx-4 ${
                      index + 1 < currentStep ? 'bg-green-600' : 'bg-gray-300'
                    }`} />
                  )}
                </div>
              ))}
            </div>
            <div className="flex justify-between mt-2">
              {stepTitles.map((title, index) => (
                <div key={index} className={`text-sm ${
                  index + 1 === currentStep ? 'text-green-600 font-medium' : 'text-gray-500'
                }`}>
                  {title}
                </div>
              ))}
            </div>
          </div>

          {/* Form */}
          <div className="bg-white rounded-xl shadow-sm p-8">
            <div className="mb-8">
              <h1 className="text-2xl font-bold text-gray-900 mb-2">
                {stepTitles[currentStep - 1]}
              </h1>
              <p className="text-gray-600">
                {currentStep === 1 && 'Tell us about your business and brand'}
                {currentStep === 2 && 'Provide your contact information and address'}
                {currentStep === 3 && 'Create your admin account credentials'}
                {currentStep === 4 && 'Select your plan and payment method'}
              </p>
            </div>

            {renderStepContent()}

            {/* Navigation Buttons */}
            <div className="flex justify-between pt-8 mt-8 border-t border-gray-200">
              <button
                onClick={prevStep}
                disabled={currentStep === 1}
                className={`flex items-center px-6 py-3 rounded-lg font-medium ${
                  currentStep === 1
                    ? 'text-gray-400 cursor-not-allowed'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                }`}
              >
                <ArrowLeft className="h-5 w-5 mr-2" />
                Previous
              </button>

              {currentStep < 4 ? (
                <button
                  onClick={nextStep}
                  className="flex items-center px-6 py-3 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 transition-colors"
                >
                  Next
                  <ArrowRight className="h-5 w-5 ml-2" />
                </button>
              ) : (
                <button
                  onClick={handleSubmit}
                  disabled={isSubmitting}
                  className="flex items-center px-8 py-3 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isSubmitting ? 'Creating Account...' : 'Create Account'}
                  {!isSubmitting && <CheckCircle className="h-5 w-5 ml-2" />}
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TenantSignup;