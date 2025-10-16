import React, { useState, useRef } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import {
  ArrowLeft, ArrowRight, CheckCircle, AlertCircle, Leaf,
  Eye, EyeOff, Shield, Loader2, UserPlus, LogIn, CheckCircle2
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import tenantService from '../services/tenantService';
import '../styles/signup-animations.css';

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
  const { t } = useTranslation(['signup', 'common']);
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const selectedPlan = searchParams.get('plan') || 'community';
  
  const [currentStep, setCurrentStep] = useState(1);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitProgress, setSubmitProgress] = useState<{
    step: 'idle' | 'checking' | 'creating' | 'uploading' | 'complete';
    message: string;
  }>({ step: 'idle', message: '' });
  const [showSuccessAnimation, setShowSuccessAnimation] = useState(false);
  const [logoFile, setLogoFile] = useState<File | null>(null);
  const [logoPreview, setLogoPreview] = useState<string | null>(null);
  
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
  
  const [errors, setErrors] = useState<FormErrors & { existingTenant?: any }>({});
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [passwordStrength, setPasswordStrength] = useState(0);

  const provinces = [
    { code: 'ON', name: t('signup:provinces.ON') },
    { code: 'BC', name: t('signup:provinces.BC') },
    { code: 'AB', name: t('signup:provinces.AB') },
    { code: 'QC', name: t('signup:provinces.QC') },
    { code: 'MB', name: t('signup:provinces.MB') },
    { code: 'SK', name: t('signup:provinces.SK') },
    { code: 'NS', name: t('signup:provinces.NS') },
    { code: 'NB', name: t('signup:provinces.NB') },
    { code: 'NL', name: t('signup:provinces.NL') },
    { code: 'PE', name: t('signup:provinces.PE') },
    { code: 'NT', name: t('signup:provinces.NT') },
    { code: 'YT', name: t('signup:provinces.YT') },
    { code: 'NU', name: t('signup:provinces.NU') }
  ];

  const subscriptionPlans = {
    community_and_new_business: {
      name: t('signup:plans.community_and_new_business.name'),
      price: 0,
      features: [
        t('signup:plans.community_and_new_business.features.stores'),
        t('signup:plans.community_and_new_business.features.languages'),
        t('signup:plans.community_and_new_business.features.personalities')
      ]
    },
    small_business: {
      name: t('signup:plans.small_business.name'),
      price: 99,
      features: [
        t('signup:plans.small_business.features.stores'),
        t('signup:plans.small_business.features.languages'),
        t('signup:plans.small_business.features.personalities')
      ]
    },
    professional_and_growing_business: {
      name: t('signup:plans.professional_and_growing_business.name'),
      price: 149,
      features: [
        t('signup:plans.professional_and_growing_business.features.stores'),
        t('signup:plans.professional_and_growing_business.features.languages'),
        t('signup:plans.professional_and_growing_business.features.personalities')
      ]
    },
    enterprise: {
      name: t('signup:plans.enterprise.name'),
      price: 299,
      features: [
        t('signup:plans.enterprise.features.stores'),
        t('signup:plans.enterprise.features.languages'),
        t('signup:plans.enterprise.features.personalities')
      ]
    }
  };

  const validateStep = (step: number): boolean => {
    const newErrors: FormErrors = {};
    
    switch (step) {
      case 1: // Company Information
        if (!formData.tenantName.trim()) newErrors.tenantName = t('signup:validation.brandNameRequired');
        if (!formData.website.trim()) newErrors.website = t('signup:validation.websiteRequired');
        if (!formData.tenantCode.trim()) newErrors.tenantCode = t('signup:validation.brandCodeRequired');
        else if (!/^[A-Z0-9_-]+$/.test(formData.tenantCode)) {
          newErrors.tenantCode = t('signup:validation.brandCodeFormat');
        }
        if (!formData.companyName.trim()) newErrors.companyName = t('signup:validation.companyNameRequired');
        if (!formData.businessNumber.trim()) newErrors.businessNumber = t('signup:validation.businessNumberRequired');
        else if (!/^\d{9}$/.test(formData.businessNumber.replace(/\D/g, ''))) {
          newErrors.businessNumber = t('signup:validation.businessNumberFormat');
        }
        if (!formData.gstHstNumber.trim()) newErrors.gstHstNumber = t('signup:validation.gstHstRequired');
        else if (!/^\d{9}RT\d{4}$/.test(formData.gstHstNumber.replace(/\s/g, ''))) {
          newErrors.gstHstNumber = t('signup:validation.gstHstFormat');
        }
        break;

      case 2: // Contact Details
        if (!formData.contactEmail.trim()) newErrors.contactEmail = t('signup:validation.emailRequired');
        else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.contactEmail)) {
          newErrors.contactEmail = t('signup:validation.emailInvalid');
        }
        if (!formData.firstName.trim()) newErrors.firstName = t('signup:validation.firstNameRequired');
        if (!formData.lastName.trim()) newErrors.lastName = t('signup:validation.lastNameRequired');
        if (!formData.street.trim()) newErrors.street = t('signup:validation.streetRequired');
        if (!formData.city.trim()) newErrors.city = t('signup:validation.cityRequired');
        if (!formData.postalCode.trim()) newErrors.postalCode = t('signup:validation.postalCodeRequired');
        else if (!/^[A-Z]\d[A-Z]\s?\d[A-Z]\d$/.test(formData.postalCode.toUpperCase())) {
          newErrors.postalCode = t('signup:validation.postalCodeFormat');
        }
        break;

      case 3: // Account Setup
        if (!formData.password) newErrors.password = t('signup:validation.passwordRequired');
        else if (formData.password.length < 8) {
          newErrors.password = t('signup:validation.passwordLength');
        } else if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(formData.password)) {
          newErrors.password = t('signup:validation.passwordComplexity');
        }
        if (formData.password !== formData.confirmPassword) {
          newErrors.confirmPassword = t('signup:validation.passwordMismatch');
        }
        break;

      case 4: // Payment
        if (formData.subscriptionTier !== 'enterprise' && formData.subscriptionTier !== 'community_and_new_business') {
          if (!formData.cardNumber.trim()) newErrors.cardNumber = t('signup:validation.cardNumberRequired');
          else if (!/^\d{16}$/.test(formData.cardNumber.replace(/\s/g, ''))) {
            newErrors.cardNumber = t('signup:validation.cardNumberFormat');
          }
          if (!formData.expiryDate.trim()) newErrors.expiryDate = t('signup:validation.expiryRequired');
          else if (!/^(0[1-9]|1[0-2])\/\d{2}$/.test(formData.expiryDate)) {
            newErrors.expiryDate = t('signup:validation.expiryFormat');
          }
          if (!formData.cvv.trim()) newErrors.cvv = t('signup:validation.cvvRequired');
          else if (!/^\d{3,4}$/.test(formData.cvv)) {
            newErrors.cvv = t('signup:validation.cvvFormat');
          }
          if (!formData.billingName.trim()) newErrors.billingName = t('signup:validation.cardholderRequired');
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
    if (strength < 30) return t('signup:passwordStrength.weak');
    if (strength < 50) return t('signup:passwordStrength.fair');
    if (strength < 70) return t('signup:passwordStrength.good');
    if (strength < 90) return t('signup:passwordStrength.strong');
    return t('signup:passwordStrength.veryStrong');
  };

  const generateBrandCodeFromWebsite = (website: string): string => {
    // Extract domain name from URL (handles with or without protocol)
    let domain = website
      .replace(/^https?:\/\//, '') // Remove protocol if present
      .replace(/^www\./, ''); // Remove www if present

    // Get the main domain name (before first dot or slash)
    domain = domain.split('/')[0].split('.')[0];

    // Convert to uppercase and replace non-alphanumeric with hyphens
    let brandCode = domain.toUpperCase().replace(/[^A-Z0-9]/g, '-');

    // Remove consecutive hyphens and trim
    brandCode = brandCode.replace(/-+/g, '-').replace(/^-|-$/g, '');

    // Limit length to 20 characters
    return brandCode.substring(0, 20);
  };

  const handleInputChange = (field: keyof FormData, value: string) => {
    let formattedValue = value;

    // Auto-format certain fields
    if (field === 'tenantCode') {
      // Brand code is readonly, don't allow manual changes
      return;
    } else if (field === 'website') {
      // Auto-generate brand code from website
      const brandCode = generateBrandCodeFromWebsite(value);
      setFormData(prev => ({ ...prev, website: value, tenantCode: brandCode }));
      // Clear both errors
      if (errors.website) {
        setErrors(prev => ({ ...prev, website: '' }));
      }
      if (errors.tenantCode) {
        setErrors(prev => ({ ...prev, tenantCode: '' }));
      }
      return;
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
    setSubmitProgress({ step: 'checking', message: t('signup:tenant.progress.verifying') });

    try {
      // Add smooth delay for better UX
      await new Promise(resolve => setTimeout(resolve, 500));

      // First check if tenant already exists
      const checkResult = await tenantService.checkTenantExists(
        formData.tenantCode,
        formData.website || undefined
      );

      if (checkResult.exists) {
        // Show cleaner error message
        const conflict = checkResult.conflicts[0];
        const errorMessage = conflict.type === 'code'
          ? t('signup:tenant.errors.tenantExists', { code: conflict.value })
          : t('signup:tenant.errors.websiteExists', { website: conflict.value });

        setErrors({
          submit: errorMessage,
          existingTenant: conflict.existing_tenant,
          conflictDetails: {
            name: conflict.existing_tenant.name,
            code: conflict.existing_tenant.code,
            contact: conflict.existing_tenant.contact_email
          }
        });
        setSubmitProgress({ step: 'idle', message: '' });
        setIsSubmitting(false);
        return;
      }

      // Update progress
      setSubmitProgress({ step: 'creating', message: t('signup:tenant.progress.creating') });
      // Prepare the payload according to backend API
      const payload = {
        name: formData.tenantName,
        code: formData.tenantCode,
        company_name: formData.companyName,
        business_number: formData.businessNumber,
        gst_hst_number: formData.gstHstNumber,
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
        subscription_tier: formData.subscriptionTier as 'community_and_new_business' | 'small_business' | 'professional_and_growing_business' | 'enterprise',
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

      // Create tenant with admin user (now uses atomic signup endpoint)
      const result = await tenantService.createTenant(payload);

      // Upload logo if provided
      if (logoFile && result?.id) {
        setSubmitProgress({ step: 'uploading', message: t('signup:tenant.progress.uploading') });
        await new Promise(resolve => setTimeout(resolve, 500));

        const uploadFormData = new FormData();
        uploadFormData.append('file', logoFile);

        try {
          await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:5024'}/api/uploads/tenant/${result.id}/logo`, {
            method: 'POST',
            body: uploadFormData,
          });
        } catch (error) {
          console.error('Logo upload failed, but account was created successfully');
        }
      }

      // Mark as complete and show success
      setSubmitProgress({ step: 'complete', message: t('signup:tenant.progress.complete') });
      setShowSuccessAnimation(true);
      await new Promise(resolve => setTimeout(resolve, 2000));

      // Navigate to success page
      navigate('/signup-success', {
        state: {
          tenantName: formData.tenantName,
          tenantCode: formData.tenantCode
        }
      });
      
    } catch (error: any) {
      console.error('Signup error:', error);
      console.error('Error response:', error.response);
      console.error('Error data:', error.response?.data);

      // Parse error response for specific messages
      let errorMessage = 'Failed to create account. ';

      if (error.response?.status === 409) {
        // Conflict error - this shouldn't happen as we check first, but handle it
        const detail = error.response.data?.detail || '';
        errorMessage = detail || 'This tenant already exists.';

        // Try to get the existing tenant info for navigation options
        try {
          const checkResult = await tenantService.checkTenantExists(
            formData.tenantCode,
            formData.website || undefined
          );
          if (checkResult.exists && checkResult.conflicts.length > 0) {
            setErrors({
              submit: errorMessage,
              existingTenant: checkResult.conflicts[0].existing_tenant
            });
          } else {
            setErrors({ submit: errorMessage });
          }
        } catch (e) {
          setErrors({ submit: errorMessage });
        }
        setIsSubmitting(false);
        return;
      } else if (error.response?.data?.detail) {
        const detail = typeof error.response.data.detail === 'string'
          ? error.response.data.detail
          : JSON.stringify(error.response.data.detail);

        // Check for specific error types
        if (detail.includes('User') || detail.includes('email')) {
          errorMessage = 'A user with this email already exists. Please use a different email or login instead.';
        } else if (detail.includes('duplicate key')) {
          if (detail.includes('users_email_key')) {
            errorMessage = 'This email is already registered. Please use a different email or login instead.';
          } else {
            errorMessage = 'This information is already registered in our system.';
          }
        } else if (detail.includes('validation error') || detail.includes('field required')) {
          errorMessage = 'Please check all required fields are filled correctly. ' + detail;
        } else {
          errorMessage = detail;
        }
      } else if (error.response?.status === 422) {
        // Validation error from FastAPI
        errorMessage = 'Validation error: Please check all required fields are filled correctly.';
        if (error.response?.data?.errors) {
          const errors = error.response.data.errors;
          errorMessage += ' ' + JSON.stringify(errors);
        }
      } else if (error.response?.status === 500) {
        errorMessage = 'Server error occurred. Please try again later or contact support.';
      } else if (error.response?.status === 404) {
        errorMessage = 'Service not available. Please ensure the backend is running.';
      } else if (!error.response) {
        errorMessage = 'Network error: Unable to connect to the server. Please check your connection.';
      } else if (error.message) {
        errorMessage = error.message;
      }

      setErrors({ submit: errorMessage });
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
                {t('signup:tenant.companyInfo.brandName')} *
              </label>
              <input
                type="text"
                value={formData.tenantName}
                onChange={(e) => handleInputChange('tenantName', e.target.value)}
                className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 ${
                  errors.tenantName ? 'border-red-500' : 'border-gray-200'
                }`}
                placeholder={t('signup:tenant.companyInfo.brandNamePlaceholder')}
              />
              {errors.tenantName && (
                <p className="mt-1 text-sm text-danger-600">{errors.tenantName}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {t('signup:tenant.companyInfo.website')} *
              </label>
              <input
                type="text"
                value={formData.website}
                onChange={(e) => handleInputChange('website', e.target.value)}
                className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 ${
                  errors.website ? 'border-red-500' : 'border-gray-200'
                }`}
                placeholder={t('signup:tenant.companyInfo.websitePlaceholder')}
              />
              <p className="mt-1 text-sm text-gray-500">
                {t('signup:tenant.companyInfo.websiteHelp')}
              </p>
              {errors.website && (
                <p className="mt-1 text-sm text-danger-600">{errors.website}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {t('signup:tenant.companyInfo.brandCodeAuto')}
              </label>
              <input
                type="text"
                value={formData.tenantCode}
                readOnly
                className="w-full px-4 py-3 border rounded-lg bg-gray-50 cursor-not-allowed border-gray-200"
                placeholder={t('signup:tenant.companyInfo.brandCodePlaceholder')}
              />
              <p className="mt-1 text-sm text-gray-500">
                {t('signup:tenant.companyInfo.brandCodeHelp', { code: formData.tenantCode.toLowerCase() || 'your-code' })}
              </p>
              {errors.tenantCode && (
                <p className="mt-1 text-sm text-danger-600">{errors.tenantCode}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {t('signup:tenant.companyInfo.legalCompanyName')} *
              </label>
              <input
                type="text"
                value={formData.companyName}
                onChange={(e) => handleInputChange('companyName', e.target.value)}
                className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 ${
                  errors.companyName ? 'border-red-500' : 'border-gray-200'
                }`}
                placeholder={t('signup:tenant.companyInfo.legalCompanyPlaceholder')}
              />
              {errors.companyName && (
                <p className="mt-1 text-sm text-danger-600">{errors.companyName}</p>
              )}
            </div>

            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('signup:tenant.companyInfo.businessNumber')} *
                </label>
                <input
                  type="text"
                  value={formData.businessNumber}
                  onChange={(e) => handleInputChange('businessNumber', e.target.value)}
                  className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 ${
                    errors.businessNumber ? 'border-red-500' : 'border-gray-200'
                  }`}
                  placeholder={t('signup:tenant.companyInfo.businessNumberPlaceholder')}
                />
                <p className="mt-1 text-sm text-gray-500">
                  {t('signup:tenant.companyInfo.businessNumberHelp')}
                </p>
                {errors.businessNumber && (
                  <p className="mt-1 text-sm text-danger-600">{errors.businessNumber}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('signup:tenant.companyInfo.gstHstNumber')} *
                </label>
                <input
                  type="text"
                  value={formData.gstHstNumber}
                  onChange={(e) => handleInputChange('gstHstNumber', e.target.value)}
                  className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 ${
                    errors.gstHstNumber ? 'border-red-500' : 'border-gray-200'
                  }`}
                  placeholder={t('signup:tenant.companyInfo.gstHstPlaceholder')}
                />
                <p className="mt-1 text-sm text-gray-500">
                  {t('signup:tenant.companyInfo.gstHstHelp')}
                </p>
                {errors.gstHstNumber && (
                  <p className="mt-1 text-sm text-danger-600">{errors.gstHstNumber}</p>
                )}
              </div>
            </div>


            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {t('signup:tenant.companyInfo.logoUpload')}
              </label>
              <div className="space-y-2">
                <div className="flex items-center space-x-3">
                  <input
                    type="file"
                    accept="image/png,image/jpeg,image/jpg,image/webp"
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (file) {
                        setLogoFile(file);
                        const reader = new FileReader();
                        reader.onloadend = () => {
                          setLogoPreview(reader.result as string);
                        };
                        reader.readAsDataURL(file);
                      }
                    }}
                    className="flex-1 px-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  />
                  {logoPreview && (
                    <img
                      src={logoPreview}
                      alt="Logo preview"
                      className="w-16 h-16 object-contain border border-gray-200 rounded"
                    />
                  )}
                </div>
                <div className="text-xs text-gray-500">
                  {t('signup:tenant.companyInfo.logoUploadHelp')}
                </div>
              </div>
            </div>
          </div>
        );

      case 2:
        return (
          <div className="space-y-6">
            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('signup:tenant.contactInfo.firstName')} *
                </label>
                <input
                  type="text"
                  value={formData.firstName}
                  onChange={(e) => handleInputChange('firstName', e.target.value)}
                  className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 ${
                    errors.firstName ? 'border-red-500' : 'border-gray-200'
                  }`}
                />
                {errors.firstName && (
                  <p className="mt-1 text-sm text-danger-600">{errors.firstName}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('signup:tenant.contactInfo.lastName')} *
                </label>
                <input
                  type="text"
                  value={formData.lastName}
                  onChange={(e) => handleInputChange('lastName', e.target.value)}
                  className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 ${
                    errors.lastName ? 'border-red-500' : 'border-gray-200'
                  }`}
                />
                {errors.lastName && (
                  <p className="mt-1 text-sm text-danger-600">{errors.lastName}</p>
                )}
              </div>
            </div>

            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('signup:tenant.contactInfo.email')} *
                </label>
                <input
                  type="email"
                  value={formData.contactEmail}
                  onChange={(e) => handleInputChange('contactEmail', e.target.value)}
                  className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 ${
                    errors.contactEmail ? 'border-red-500' : 'border-gray-200'
                  }`}
                />
                {errors.contactEmail && (
                  <p className="mt-1 text-sm text-danger-600">{errors.contactEmail}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('signup:tenant.contactInfo.phone')}
                </label>
                <input
                  type="tel"
                  value={formData.contactPhone}
                  onChange={(e) => handleInputChange('contactPhone', e.target.value)}
                  className="w-full px-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  placeholder={t('signup:tenant.contactInfo.phonePlaceholder')}
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {t('signup:tenant.contactInfo.street')} *
              </label>
              <input
                type="text"
                value={formData.street}
                onChange={(e) => handleInputChange('street', e.target.value)}
                className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 ${
                  errors.street ? 'border-red-500' : 'border-gray-200'
                }`}
              />
              {errors.street && (
                <p className="mt-1 text-sm text-danger-600">{errors.street}</p>
              )}
            </div>

            <div className="grid md:grid-cols-3 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('signup:tenant.contactInfo.city')} *
                </label>
                <input
                  type="text"
                  value={formData.city}
                  onChange={(e) => handleInputChange('city', e.target.value)}
                  className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 ${
                    errors.city ? 'border-red-500' : 'border-gray-200'
                  }`}
                />
                {errors.city && (
                  <p className="mt-1 text-sm text-danger-600">{errors.city}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('signup:tenant.contactInfo.province')} *
                </label>
                <select
                  value={formData.province}
                  onChange={(e) => handleInputChange('province', e.target.value)}
                  className="w-full px-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
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
                  {t('signup:tenant.contactInfo.postalCode')} *
                </label>
                <input
                  type="text"
                  value={formData.postalCode}
                  onChange={(e) => handleInputChange('postalCode', e.target.value)}
                  className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 ${
                    errors.postalCode ? 'border-red-500' : 'border-gray-200'
                  }`}
                  placeholder={t('signup:tenant.contactInfo.postalCodePlaceholder')}
                />
                {errors.postalCode && (
                  <p className="mt-1 text-sm text-danger-600">{errors.postalCode}</p>
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
                {t('signup:tenant.accountSetup.password')} *
              </label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  value={formData.password}
                  onChange={(e) => handleInputChange('password', e.target.value)}
                  className={`w-full px-4 py-3 pr-12 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 ${
                    errors.password ? 'border-red-500' : 'border-gray-200'
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
                      <span className="text-xs text-gray-600">{t('signup:tenant.accountSetup.passwordStrength')}</span>
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
                  <div className="w-full bg-gray-100 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full transition-all duration-300 ${getPasswordStrengthColor(passwordStrength)}`}
                      style={{ width: `${passwordStrength}%` }}
                    />
                  </div>
                </div>
              )}

              <p className="mt-1 text-sm text-gray-500">
                {t('signup:tenant.accountSetup.passwordHelp')}
              </p>
              {errors.password && (
                <p className="mt-1 text-sm text-danger-600">{errors.password}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {t('signup:tenant.accountSetup.confirmPassword')} *
              </label>
              <div className="relative">
                <input
                  type={showConfirmPassword ? "text" : "password"}
                  value={formData.confirmPassword}
                  onChange={(e) => handleInputChange('confirmPassword', e.target.value)}
                  className={`w-full px-4 py-3 pr-12 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 ${
                    errors.confirmPassword ? 'border-red-500' : 'border-gray-200'
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
                <p className="mt-1 text-sm text-danger-600">{errors.confirmPassword}</p>
              )}
            </div>

            <div className="bg-primary-50 border border-green-200 rounded-lg p-6">
              <div className="flex items-start">
                <CheckCircle className="h-5 w-5 text-primary-600 mt-0.5 mr-3" />
                <div>
                  <h3 className="font-medium text-primary-900">{t('signup:tenant.accountSetup.securityTitle')}</h3>
                  <p className="text-sm text-primary-700 mt-1">
                    {t('signup:tenant.accountSetup.securityDescription')}
                  </p>
                </div>
              </div>
            </div>
          </div>
        );

      case 4:
        const selectedPlanInfo = subscriptionPlans[formData.subscriptionTier as keyof typeof subscriptionPlans];

        // Show error message prominently at the top if there's a submit error
        if (errors.submit) {
          return (
            <div className="space-y-6">
              <div className="bg-red-50 border-l-4 border-red-500 rounded-lg p-4">
                <div className="flex items-start">
                  <AlertCircle className="h-5 w-5 text-red-500 mt-0.5 mr-3 flex-shrink-0" />
                  <div>
                    <h3 className="text-sm font-semibold text-red-800 mb-1">{t('signup:tenant.errors.accountCreationFailed')}</h3>
                    <p className="text-sm text-red-700">{errors.submit}</p>
                    <div className="mt-3 flex gap-3">
                      <button
                        type="button"
                        onClick={() => {
                          setErrors({ submit: '' });
                          setIsSubmitting(false);
                        }}
                        className="text-sm px-3 py-1.5 bg-white border border-red-300 text-red-700 rounded-md hover:bg-red-50"
                      >
                        {t('signup:tenant.errors.tryAgain')}
                      </button>
                      {errors.existingTenant && (
                        <>
                          <button
                            type="button"
                            onClick={() => navigate('/user-registration', {
                              state: {
                                tenantCode: errors.existingTenant.code,
                                tenantName: errors.existingTenant.name
                              }
                            })}
                            className="text-sm px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-all transform hover:scale-105 flex items-center gap-2"
                          >
                            <UserPlus className="h-4 w-4" />
                            {t('signup:tenant.errors.registerAsUser')}
                          </button>
                          <button
                            type="button"
                            onClick={() => navigate('/login')}
                            className="text-sm px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-all transform hover:scale-105 flex items-center gap-2"
                          >
                            <LogIn className="h-4 w-4" />
                            {t('signup:tenant.errors.signInInstead')}
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              </div>
              {/* Show the selected plan and payment form even with error */}
              {selectedPlanInfo && (
                <>
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
                    <div className="flex justify-between items-start mb-2">
                      <h3 className="text-lg font-semibold">{t('signup:tenant.subscription.selectedPlan', { plan: selectedPlanInfo.name })}</h3>
                      <button
                        type="button"
                        onClick={() => handleInputChange('subscriptionTier', '')}
                        className="text-sm text-primary-600 hover:text-primary-700 underline"
                      >
                        {t('signup:tenant.subscription.changePlan')}
                      </button>
                    </div>
                    <div className="text-2xl font-bold text-primary-600 mb-2">
                      {selectedPlanInfo.price === 0 ? t('signup:tenant.subscription.free') :
                       selectedPlanInfo.price ? t('signup:tenant.subscription.perMonth', { price: selectedPlanInfo.price }) : t('signup:tenant.subscription.customPricing')}
                    </div>
                    <ul className="text-sm text-gray-600 space-y-1">
                      {selectedPlanInfo.features.map((feature, index) => (
                        <li key={index} className="flex items-center">
                          <CheckCircle className="h-4 w-4 text-primary-500 mr-2" />
                          {feature}
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Billing Cycle */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      {t('signup:tenant.subscription.billingCycle')}
                    </label>
                    <div className="grid grid-cols-2 gap-6">
                      <label className="flex items-center p-6 border rounded-lg cursor-pointer hover:bg-gray-50">
                        <input
                          type="radio"
                          name="billingCycle"
                          value="monthly"
                          checked={formData.billingCycle === 'monthly'}
                          onChange={(e) => handleInputChange('billingCycle', e.target.value)}
                          className="mr-3"
                        />
                        <div>
                          <div className="font-medium">{t('signup:tenant.subscription.monthly')}</div>
                          <div className="text-sm text-gray-500">{t('signup:tenant.subscription.monthlyBilled')}</div>
                        </div>
                      </label>
                      <label className="flex items-center p-6 border rounded-lg cursor-pointer hover:bg-gray-50">
                        <input
                          type="radio"
                          name="billingCycle"
                          value="annual"
                          checked={formData.billingCycle === 'annual'}
                          onChange={(e) => handleInputChange('billingCycle', e.target.value)}
                          className="mr-3"
                        />
                        <div>
                          <div className="font-medium">{t('signup:tenant.subscription.annual')}</div>
                          <div className="text-sm text-gray-500">{t('signup:tenant.subscription.annualSave')}</div>
                        </div>
                      </label>
                    </div>
                  </div>

                  {/* Payment fields for non-free plans */}
                  {selectedPlanInfo.price !== 0 && (
                    <>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            {t('signup:tenant.payment.cardholderName')} <span className="text-red-500">*</span>
                          </label>
                          <input
                            type="text"
                            value={formData.billingName}
                            onChange={(e) => handleInputChange('billingName', e.target.value)}
                            className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 ${
                              errors.billingName ? 'border-red-500' : 'border-gray-300'
                            }`}
                            placeholder={t('signup:tenant.payment.cardholderPlaceholder')}
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            {t('signup:tenant.payment.cardNumber')} <span className="text-red-500">*</span>
                          </label>
                          <input
                            type="text"
                            value={formData.cardNumber}
                            onChange={(e) => handleInputChange('cardNumber', e.target.value.replace(/\s/g, '').replace(/(.{4})/g, '$1 ').trim())}
                            maxLength={19}
                            className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 ${
                              errors.cardNumber ? 'border-red-500' : 'border-gray-300'
                            }`}
                            placeholder={t('signup:tenant.payment.cardNumberPlaceholder')}
                          />
                        </div>
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            {t('signup:tenant.payment.expiryDate')} <span className="text-red-500">*</span>
                          </label>
                          <input
                            type="text"
                            value={formData.expiryDate}
                            onChange={(e) => {
                              let value = e.target.value.replace(/\D/g, '');
                              if (value.length >= 2) {
                                value = value.substring(0, 2) + '/' + value.substring(2, 4);
                              }
                              handleInputChange('expiryDate', value);
                            }}
                            maxLength={5}
                            className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 ${
                              errors.expiryDate ? 'border-red-500' : 'border-gray-300'
                            }`}
                            placeholder={t('signup:tenant.payment.expiryPlaceholder')}
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            {t('signup:tenant.payment.cvv')} <span className="text-red-500">*</span>
                          </label>
                          <input
                            type="text"
                            value={formData.cvv}
                            onChange={(e) => handleInputChange('cvv', e.target.value.replace(/\D/g, '').substring(0, 4))}
                            maxLength={4}
                            className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 ${
                              errors.cvv ? 'border-red-500' : 'border-gray-300'
                            }`}
                            placeholder={t('signup:tenant.payment.cvvPlaceholder')}
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            {t('signup:tenant.payment.postalCode')}
                          </label>
                          <input
                            type="text"
                            value={formData.billingPostalCode}
                            onChange={(e) => handleInputChange('billingPostalCode', e.target.value)}
                            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                            placeholder={t('signup:tenant.payment.postalCodePlaceholder')}
                          />
                        </div>
                      </div>
                    </>
                  )}
                </>
              )}
            </div>
          );
        }

        if (!selectedPlanInfo) {
          return (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold mb-4">{t('signup:tenant.subscription.choosePlan')}</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {Object.entries(subscriptionPlans).map(([key, plan]) => (
                  <div
                    key={key}
                    onClick={() => handleInputChange('subscriptionTier', key)}
                    className="border rounded-lg p-4 cursor-pointer hover:border-primary-500 hover:shadow-lg transition-all"
                  >
                    <h4 className="font-semibold text-lg mb-2">{plan.name}</h4>
                    <div className="text-2xl font-bold text-primary-600 mb-3">
                      {plan.price === 0 ? t('signup:tenant.subscription.free') : plan.price ? t('signup:tenant.subscription.perMonth', { price: plan.price }) : t('signup:tenant.subscription.customPricing')}
                    </div>
                    <ul className="text-sm space-y-1">
                      {plan.features.slice(0, 3).map((feature, idx) => (
                        <li key={idx} className="flex items-start">
                          <CheckCircle className="h-4 w-4 text-green-500 mr-1 mt-0.5 flex-shrink-0" />
                          <span className="text-gray-600">{feature}</span>
                        </li>
                      ))}
                    </ul>
                    <button
                      type="button"
                      className="mt-4 w-full py-2 px-4 bg-primary-600 text-white rounded-md hover:bg-primary-700"
                    >
                      {t('signup:tenant.subscription.selectPlan')}
                    </button>
                  </div>
                ))}
              </div>
            </div>
          );
        }

        return (
          <div className="space-y-6">
            {/* Plan Summary */}
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
              <div className="flex justify-between items-start mb-2">
                <h3 className="text-lg font-semibold">{t('signup:tenant.subscription.selectedPlan', { plan: selectedPlanInfo.name })}</h3>
                <button
                  type="button"
                  onClick={() => handleInputChange('subscriptionTier', '')}
                  className="text-sm text-primary-600 hover:text-primary-700 underline"
                >
                  {t('signup:tenant.subscription.changePlan')}
                </button>
              </div>
              <div className="text-2xl font-bold text-primary-600 mb-2">
                {selectedPlanInfo.price === 0 ? t('signup:tenant.subscription.free') :
                 selectedPlanInfo.price ? t('signup:tenant.subscription.perMonth', { price: selectedPlanInfo.price }) : t('signup:tenant.subscription.customPricing')}
              </div>
              <ul className="text-sm text-gray-600 space-y-1">
                {selectedPlanInfo.features.map((feature, index) => (
                  <li key={index} className="flex items-center">
                    <CheckCircle className="h-4 w-4 text-primary-500 mr-2" />
                    {feature}
                  </li>
                ))}
              </ul>
            </div>

            {/* Billing Cycle */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {t('signup:tenant.subscription.billingCycle')}
              </label>
              <div className="grid grid-cols-2 gap-6">
                <label className="flex items-center p-6 border rounded-lg cursor-pointer hover:bg-gray-50">
                  <input
                    type="radio"
                    name="billingCycle"
                    value="monthly"
                    checked={formData.billingCycle === 'monthly'}
                    onChange={(e) => handleInputChange('billingCycle', e.target.value)}
                    className="mr-3"
                  />
                  <div>
                    <div className="font-medium">{t('signup:tenant.subscription.monthly')}</div>
                    <div className="text-sm text-gray-500">{t('signup:tenant.subscription.monthlyBilled')}</div>
                  </div>
                </label>
                <label className="flex items-center p-6 border rounded-lg cursor-pointer hover:bg-gray-50">
                  <input
                    type="radio"
                    name="billingCycle"
                    value="annual"
                    checked={formData.billingCycle === 'annual'}
                    onChange={(e) => handleInputChange('billingCycle', e.target.value)}
                    className="mr-3"
                  />
                  <div>
                    <div className="font-medium">{t('signup:tenant.subscription.annual')}</div>
                    <div className="text-sm text-gray-500">{t('signup:tenant.subscription.annualSave')}</div>
                  </div>
                </label>
              </div>
            </div>

            {/* Payment Information - Skip for Community and Enterprise */}
            {formData.subscriptionTier !== 'enterprise' && formData.subscriptionTier !== 'community_and_new_business' && (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    {t('signup:tenant.payment.cardholderName')} *
                  </label>
                  <input
                    type="text"
                    value={formData.billingName}
                    onChange={(e) => handleInputChange('billingName', e.target.value)}
                    className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 ${
                      errors.billingName ? 'border-red-500' : 'border-gray-200'
                    }`}
                  />
                  {errors.billingName && (
                    <p className="mt-1 text-sm text-danger-600">{errors.billingName}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    {t('signup:tenant.payment.cardNumber')} *
                  </label>
                  <input
                    type="text"
                    value={formData.cardNumber}
                    onChange={(e) => handleInputChange('cardNumber', e.target.value)}
                    className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 ${
                      errors.cardNumber ? 'border-red-500' : 'border-gray-200'
                    }`}
                    placeholder={t('signup:tenant.payment.cardNumberPlaceholder')}
                    maxLength={19}
                  />
                  {errors.cardNumber && (
                    <p className="mt-1 text-sm text-danger-600">{errors.cardNumber}</p>
                  )}
                </div>

                <div className="grid md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      {t('signup:tenant.payment.expiryDate')} *
                    </label>
                    <input
                      type="text"
                      value={formData.expiryDate}
                      onChange={(e) => handleInputChange('expiryDate', e.target.value)}
                      className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 ${
                        errors.expiryDate ? 'border-red-500' : 'border-gray-200'
                      }`}
                      placeholder={t('signup:tenant.payment.expiryPlaceholder')}
                      maxLength={5}
                    />
                    {errors.expiryDate && (
                      <p className="mt-1 text-sm text-danger-600">{errors.expiryDate}</p>
                    )}
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      {t('signup:tenant.payment.cvv')} *
                    </label>
                    <input
                      type="text"
                      value={formData.cvv}
                      onChange={(e) => handleInputChange('cvv', e.target.value)}
                      className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 ${
                        errors.cvv ? 'border-red-500' : 'border-gray-200'
                      }`}
                      placeholder={t('signup:tenant.payment.cvvPlaceholder')}
                    />
                    {errors.cvv && (
                      <p className="mt-1 text-sm text-danger-600">{errors.cvv}</p>
                    )}
                  </div>
                </div>
              </>
            )}

            {formData.subscriptionTier === 'enterprise' && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
                <div className="flex items-start">
                  <AlertCircle className="h-5 w-5 text-accent-600 mt-0.5 mr-3" />
                  <div>
                    <h3 className="font-medium text-blue-900">{t('signup:tenant.subscription.enterpriseTitle')}</h3>
                    <p className="text-sm text-accent-700 mt-1">
                      {t('signup:tenant.subscription.enterpriseDescription')}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {errors.submit && (
              <div className="bg-danger-50 border border-red-200 rounded-lg p-6">
                <div className="flex items-start">
                  <AlertCircle className="h-5 w-5 text-danger-600 mt-0.5 mr-3" />
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
    t('signup:tenant.steps.company'),
    t('signup:tenant.steps.contact'),
    t('signup:tenant.steps.account'),
    t('signup:tenant.steps.payment')
  ];

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Success Animation Overlay */}
      {showSuccessAnimation && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 animate-fadeIn">
          <div className="bg-white rounded-2xl p-8 max-w-md w-full mx-4 animate-scaleIn">
            <div className="text-center">
              <div className="mx-auto h-20 w-20 bg-green-100 rounded-full flex items-center justify-center mb-4 animate-scaleIn">
                <svg
                  className="h-12 w-12 text-green-600 success-check"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="3"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M20 6 L9 17 L4 12"></path>
                </svg>
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-2 animate-fadeInUp">
                {t('signup:tenant.success.welcome')}
              </h3>
              <p className="text-gray-600 mb-6 animate-fadeInUp" style={{ animationDelay: '0.1s' }}>
                {t('signup:tenant.success.accountCreated')}
              </p>
              <div className="space-y-2 animate-fadeInUp" style={{ animationDelay: '0.2s' }}>
                <p className="text-sm text-gray-500">{t('signup:tenant.success.tenantCode')}</p>
                <p className="text-lg font-mono font-bold text-primary-600 bg-gray-50 py-2 px-4 rounded-lg">
                  {formData.tenantCode}
                </p>
              </div>
              <div className="mt-6 animate-fadeInUp" style={{ animationDelay: '0.3s' }}>
                <div className="h-1 w-full bg-gray-200 rounded-full overflow-hidden">
                  <div className="h-full bg-gradient-to-r from-green-500 to-green-600 loading-shimmer"></div>
                </div>
                <p className="text-sm text-gray-500 mt-2">{t('signup:tenant.success.preparing')}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Header */}
      <header className="bg-white ">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between py-6">
            <Link to="/" className="flex items-center">
              <ArrowLeft className="h-5 w-5 text-gray-400 mr-2" />
              <Leaf className="h-8 w-8 text-primary-600" />
              <span className="ml-2 text-2xl font-bold text-gray-900">{t('signup:tenant.header.title')}</span>
            </Link>
            <div className="text-sm text-gray-500">
              {t('signup:tenant.header.alreadyHaveAccount')} <Link to="/login" className="text-primary-600 hover:text-primary-700">{t('signup:tenant.header.signIn')}</Link>
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
                      ? 'bg-primary-600 border-primary-600 text-white'
                      : 'border-gray-200 text-gray-400'
                  }`}>
                    {index + 1 < currentStep ? (
                      <CheckCircle className="h-6 w-6" />
                    ) : (
                      <span>{index + 1}</span>
                    )}
                  </div>
                  {index < stepTitles.length - 1 && (
                    <div className={`flex-1 h-1 mx-4 ${
                      index + 1 < currentStep ? 'bg-primary-600' : 'bg-gray-300'
                    }`} />
                  )}
                </div>
              ))}
            </div>
            <div className="flex justify-between mt-2">
              {stepTitles.map((title, index) => (
                <div key={index} className={`text-sm ${
                  index + 1 === currentStep ? 'text-primary-600 font-medium' : 'text-gray-500'
                }`}>
                  {title}
                </div>
              ))}
            </div>
          </div>

          {/* Form */}
          <div className="bg-white rounded-xl  p-8">
            <div className="mb-8">
              <h1 className="text-2xl font-bold text-gray-900 mb-2">
                {stepTitles[currentStep - 1]}
              </h1>
              <p className="text-gray-600">
                {currentStep === 1 && t('signup:tenant.stepDescriptions.company')}
                {currentStep === 2 && t('signup:tenant.stepDescriptions.contact')}
                {currentStep === 3 && t('signup:tenant.stepDescriptions.account')}
                {currentStep === 4 && t('signup:tenant.stepDescriptions.payment')}
              </p>
            </div>

            <div className="step-content">
              {renderStepContent()}
            </div>

            {/* Navigation Buttons */}
            <div className="flex justify-between pt-8 mt-8 border-t border-gray-200">
              <button
                onClick={prevStep}
                disabled={currentStep === 1}
                className={`flex items-center px-6 py-3 rounded-lg font-medium ${
                  currentStep === 1
                    ? 'text-gray-400 cursor-not-allowed'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                }`}
              >
                <ArrowLeft className="h-5 w-5 mr-2" />
                {t('signup:tenant.navigation.previous')}
              </button>

              {currentStep < 4 ? (
                <button
                  onClick={nextStep}
                  className="flex items-center px-6 py-3 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 transition-colors"
                >
                  {t('signup:tenant.navigation.next')}
                  <ArrowRight className="h-5 w-5 ml-2" />
                </button>
              ) : (
                <button
                  onClick={handleSubmit}
                  disabled={isSubmitting}
                  className="relative flex items-center px-8 py-3 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 transition-all transform hover:scale-105 disabled:opacity-70 disabled:cursor-not-allowed disabled:transform-none overflow-hidden"
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                      <span className="animate-pulse">
                        {submitProgress.message || t('signup:tenant.progress.processing')}
                      </span>
                    </>
                  ) : (
                    <>
                      <span>{t('signup:tenant.navigation.createAccount')}</span>
                      <CheckCircle className="h-5 w-5 ml-2" />
                    </>
                  )}
                  {submitProgress.step === 'complete' && (
                    <div className="absolute inset-0 bg-green-600 flex items-center justify-center animate-slideIn">
                      <CheckCircle2 className="h-6 w-6 text-white animate-scaleIn" />
                    </div>
                  )}
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