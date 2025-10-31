import React, { useState, useRef } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import {
  ArrowLeft, ArrowRight, CheckCircle, AlertCircle, Leaf,
  Eye, EyeOff, Shield, Loader2, UserPlus, LogIn, CheckCircle2, CreditCard
} from 'lucide-react';
import { useStripe, useElements, CardElement } from '@stripe/react-stripe-js';
import { useTranslation } from 'react-i18next';
import tenantService from '../services/tenantService';
import OntarioLicenseValidator from '../components/OntarioLicenseValidator';
import AddressAutocomplete, { AddressComponents } from '../components/AddressAutocomplete';
import OTPVerification from '../components/OTPVerification';
import ErrorBoundary from '../components/ErrorBoundary';
import '../styles/signup-animations.css';
import { getApiEndpoint } from '../config/app.config';

interface LicenseValidationResult {
  is_valid: boolean;
  license_number?: string;
  store_name?: string;
  address?: string;
  municipality?: string;
  store_status?: string;
  website?: string;
  error_message?: string;
  verification_tier?: string;
  domain_match?: boolean;
  auto_fill_data?: {
    store_name: string;
    address: string;
    municipality: string;
    website?: string;
    license_number: string;
    license_status: string;
  };
}

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
  emailVerified: boolean;
  phoneVerified: boolean;
  
  // Ontario Licensing (required for ON only)
  crolNumber: string;
  
  // Account Setup
  tenantName: string;
  tenantCode: string;
  password: string;
  confirmPassword: string;
  
  // Subscription
  subscriptionTier: string;
  billingCycle: string;
  
  // Payment
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
  const stripe = useStripe();
  const elements = useElements();
  
  const [currentStep, setCurrentStep] = useState(1);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitProgress, setSubmitProgress] = useState<{
    step: 'idle' | 'checking' | 'creating' | 'uploading' | 'complete';
    message: string;
  }>({ step: 'idle', message: '' });
  const [showSuccessAnimation, setShowSuccessAnimation] = useState(false);
  const [logoFile, setLogoFile] = useState<File | null>(null);
  const [logoPreview, setLogoPreview] = useState<string | null>(null);
  const [crsaValidation, setCrsaValidation] = useState<LicenseValidationResult | null>(null);
  const [showEmailVerification, setShowEmailVerification] = useState(false);
  const [showPhoneVerification, setShowPhoneVerification] = useState(false);
  const [termsAccepted, setTermsAccepted] = useState(false);
  const [privacyAccepted, setPrivacyAccepted] = useState(false);
  const [accuracyAttested, setAccuracyAttested] = useState(false);
  const [authorizationAttested, setAuthorizationAttested] = useState(false);
  
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
    emailVerified: false,
    phoneVerified: false,
    crolNumber: '',
    tenantName: '',
    tenantCode: '',
    password: '',
    confirmPassword: '',
    subscriptionTier: selectedPlan,
    billingCycle: 'monthly',
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
    
    // Validate terms acceptance on step 5
    if (step === 5) {
      if (!termsAccepted) {
        newErrors.terms = t('signup:tenant.legal.termsRequired');
      }
      if (!privacyAccepted) {
        newErrors.privacy = t('signup:tenant.legal.privacyRequired');
      }
      if (!accuracyAttested) {
        newErrors.accuracy = t('signup:tenant.legal.accuracyRequired');
      }
      if (!authorizationAttested) {
        newErrors.authorization = t('signup:tenant.legal.authorizationRequired');
      }
    }
    
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
        // Require email verification
        if (!formData.emailVerified) {
          newErrors.contactEmail = t('signup:validation.emailNotVerified', 'Email must be verified before proceeding');
        }
        // Require phone verification if phone is provided
        if (formData.contactPhone.trim() && !formData.phoneVerified) {
          newErrors.contactPhone = t('signup:validation.phoneNotVerified', 'Phone must be verified before proceeding');
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

      case 3: // Ontario Licensing
        // Ontario-specific validation
        if (formData.province === 'ON') {
          if (!formData.crolNumber.trim()) {
            newErrors.crolNumber = 'CROL number is required for Ontario tenants';
          }
          if (!crsaValidation || !crsaValidation.is_valid) {
            newErrors.crsaValidation = 'Valid CRSA license is required for Ontario tenants';
          } else if (crsaValidation.verification_tier === 'manual_review') {
            newErrors.crsaValidation = 'Your email domain does not match the CRSA website. Please contact support for manual verification.';
          }
        }
        break;

      case 4: // Account Setup
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

      case 5: // Payment
        // For paid tiers, only validate billing name (Stripe handles card validation)
        if (formData.subscriptionTier !== 'enterprise' && formData.subscriptionTier !== 'community_and_new_business') {
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
      let nextStepNum = currentStep + 1;
      
      // Auto-skip step 3 (Ontario Licensing) if province is not Ontario
      if (nextStepNum === 3 && formData.province !== 'ON') {
        nextStepNum = 4;
      }
      
      setCurrentStep(prev => Math.min(nextStepNum, 5));
    }
  };

  const prevStep = () => {
    let prevStepNum = currentStep - 1;
    
    // Auto-skip step 3 (Ontario Licensing) if province is not Ontario when going back
    if (prevStepNum === 3 && formData.province !== 'ON') {
      prevStepNum = 2;
    }
    
    setCurrentStep(prev => Math.max(prevStepNum, 1));
  };

  const handleSubmit = async () => {
    if (!validateStep(5)) return;

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
      
      // Create Stripe payment method for paid tiers
      let paymentMethodId = null;
      const isPaidTier = formData.subscriptionTier !== 'community_and_new_business';
      
      if (isPaidTier && stripe && elements) {
        setSubmitProgress({ step: 'checking', message: 'Processing payment method...' });
        
        const cardElement = elements.getElement(CardElement);
        if (!cardElement) {
          setErrors({ submit: 'Payment details required for paid plans' });
          setIsSubmitting(false);
          return;
        }
        
        const { error, paymentMethod } = await stripe.createPaymentMethod({
          type: 'card',
          card: cardElement,
          billing_details: {
            name: formData.billingName || `${formData.firstName} ${formData.lastName}`,
            email: formData.contactEmail,
            phone: formData.contactPhone || undefined,
          },
        });
        
        if (error) {
          console.error('Stripe payment method error:', error);
          setErrors({ submit: error.message || 'Failed to process payment method' });
          setIsSubmitting(false);
          return;
        }
        
        paymentMethodId = paymentMethod.id;
        console.log('Stripe payment method created:', paymentMethodId);
      }
      
      // Prepare the payload according to backend API
      const payload: any = {
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
        terms_acceptance: {
          accepted_at: new Date().toISOString(),
          version: '1.0',
          accepted_by: formData.contactEmail,
          terms_accepted: termsAccepted,
          privacy_accepted: privacyAccepted,
          accuracy_attested: accuracyAttested,
          authorization_attested: authorizationAttested
        },
        settings: {
          admin_user: {
            first_name: formData.firstName,
            last_name: formData.lastName,
            email: formData.contactEmail,
            password: formData.password
          },
          billing: {
            cycle: formData.billingCycle,
            payment_method_id: paymentMethodId,
            cardholder_name: formData.billingName
          }
        }
      };

      // Add Ontario-specific data if province is ON
      if (formData.province === 'ON') {
        payload.crol_number = formData.crolNumber;
        
        // Add CRSA validation data for store creation
        if (crsaValidation?.is_valid && crsaValidation.auto_fill_data) {
          payload.crsa_license = {
            license_number: crsaValidation.license_number,
            store_name: crsaValidation.auto_fill_data.store_name,
            address: crsaValidation.auto_fill_data.address,
            municipality: crsaValidation.auto_fill_data.municipality,
            website: crsaValidation.auto_fill_data.website,
            verification_tier: crsaValidation.verification_tier || 'auto_approved'
          };
        }
      }


      // Create tenant with admin user (now uses atomic signup endpoint)
      const result = await tenantService.createTenant(payload);

      // Upload logo if provided
      if (logoFile && result?.id) {
        setSubmitProgress({ step: 'uploading', message: t('signup:tenant.progress.uploading') });
        await new Promise(resolve => setTimeout(resolve, 500));

        const uploadFormData = new FormData();
        uploadFormData.append('file', logoFile);

        try {
          await fetch(getApiEndpoint('/uploads/tenant/${result.id}/logo'), {
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
          <div className="space-y-5 sm:space-y-7">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                {t('signup:tenant.companyInfo.brandName')} *
              </label>
              <input
                type="text"
                value={formData.tenantName}
                onChange={(e) => handleInputChange('tenantName', e.target.value)}
                className={`w-full px-4 py-3 border rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 dark:focus:ring-primary-400 focus:border-primary-500 transition-colors ${
                  errors.tenantName ? 'border-red-500 dark:border-red-400' : 'border-gray-200 dark:border-gray-600'
                }`}
                placeholder={t('signup:tenant.companyInfo.brandNamePlaceholder')}
              />
              {errors.tenantName && (
                <p className="mt-1 text-sm text-danger-600 dark:text-danger-400">{errors.tenantName}</p>
              )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-5 sm:gap-8">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  {t('signup:tenant.companyInfo.website')} *
                </label>
                <input
                  type="text"
                  value={formData.website}
                  onChange={(e) => handleInputChange('website', e.target.value)}
                  className={`w-full px-4 py-3 border rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 dark:focus:ring-primary-400 focus:border-primary-500 transition-colors ${
                    errors.website ? 'border-red-500 dark:border-red-400' : 'border-gray-200 dark:border-gray-600'
                  }`}
                  placeholder={t('signup:tenant.companyInfo.websitePlaceholder')}
                />
                <p className="mt-1 text-sm text-gray-500">
                  {t('signup:tenant.companyInfo.websiteHelp')}
                </p>
                {errors.website && (
                  <p className="mt-1 text-sm text-danger-600 dark:text-danger-400">{errors.website}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  {t('signup:tenant.companyInfo.brandCodeAuto')}
                </label>
                <input
                  type="text"
                  value={formData.tenantCode}
                  readOnly
                  className="w-full px-4 py-3 border rounded-lg bg-gray-50 dark:bg-gray-700 cursor-not-allowed border-gray-200 dark:border-gray-600"
                  placeholder={t('signup:tenant.companyInfo.brandCodePlaceholder')}
                />
                <p className="mt-1 text-sm text-gray-500">
                  {t('signup:tenant.companyInfo.brandCodeHelp', { code: formData.tenantCode.toLowerCase() || 'your-code' })}
                </p>
                {errors.tenantCode && (
                  <p className="mt-1 text-sm text-danger-600 dark:text-danger-400">{errors.tenantCode}</p>
                )}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                {t('signup:tenant.companyInfo.legalCompanyName')} *
              </label>
              <input
                type="text"
                value={formData.companyName}
                onChange={(e) => handleInputChange('companyName', e.target.value)}
                className={`w-full px-4 py-3 border rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 dark:focus:ring-primary-400 focus:border-primary-500 transition-colors ${
                  errors.companyName ? 'border-red-500 dark:border-red-400' : 'border-gray-200 dark:border-gray-600'
                }`}
                placeholder={t('signup:tenant.companyInfo.legalCompanyPlaceholder')}
              />
              {errors.companyName && (
                <p className="mt-1 text-sm text-danger-600 dark:text-danger-400">{errors.companyName}</p>
              )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-5 sm:gap-8">
              <div>
                <label className="block text-xs sm:text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  {t('signup:tenant.companyInfo.businessNumber')} *
                </label>
                <input
                  type="text"
                  value={formData.businessNumber}
                  onChange={(e) => handleInputChange('businessNumber', e.target.value)}
                  className={`w-full px-3 sm:px-4 py-2.5 sm:py-3 border rounded-lg text-sm sm:text-base bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 dark:focus:ring-primary-400 focus:border-primary-500 transition-colors ${
                    errors.businessNumber ? 'border-red-500 dark:border-red-400' : 'border-gray-200 dark:border-gray-600'
                  }`}
                  placeholder={t('signup:tenant.companyInfo.businessNumberPlaceholder')}
                />
                <p className="mt-1 text-xs sm:text-sm text-gray-500 dark:text-gray-400">
                  {t('signup:tenant.companyInfo.businessNumberHelp')}
                </p>
                {errors.businessNumber && (
                  <p className="mt-1 text-xs sm:text-sm text-danger-600 dark:text-danger-400">{errors.businessNumber}</p>
                )}
              </div>

              <div>
                <label className="block text-xs sm:text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  {t('signup:tenant.companyInfo.gstHstNumber')} *
                </label>
                <input
                  type="text"
                  value={formData.gstHstNumber}
                  onChange={(e) => handleInputChange('gstHstNumber', e.target.value)}
                  className={`w-full px-3 sm:px-4 py-2.5 sm:py-3 border rounded-lg text-sm sm:text-base bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 dark:focus:ring-primary-400 focus:border-primary-500 transition-colors ${
                    errors.gstHstNumber ? 'border-red-500 dark:border-red-400' : 'border-gray-200 dark:border-gray-600'
                  }`}
                  placeholder={t('signup:tenant.companyInfo.gstHstPlaceholder')}
                />
                <p className="mt-1 text-xs sm:text-sm text-gray-500 dark:text-gray-400">
                  {t('signup:tenant.companyInfo.gstHstHelp')}
                </p>
                {errors.gstHstNumber && (
                  <p className="mt-1 text-xs sm:text-sm text-danger-600 dark:text-danger-400">{errors.gstHstNumber}</p>
                )}
              </div>
            </div>


            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
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
          <div className="space-y-5 sm:space-y-7">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5 sm:gap-8">
              <div>
                <label className="block text-xs sm:text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  {t('signup:tenant.contactInfo.firstName')} *
                </label>
                <input
                  type="text"
                  value={formData.firstName}
                  onChange={(e) => handleInputChange('firstName', e.target.value)}
                  className={`w-full px-3 sm:px-4 py-2.5 sm:py-3 border rounded-lg text-sm sm:text-base bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 dark:focus:ring-primary-400 focus:border-primary-500 transition-colors ${
                    errors.firstName ? 'border-red-500 dark:border-red-400' : 'border-gray-200 dark:border-gray-600'
                  }`}
                />
                {errors.firstName && (
                  <p className="mt-1 text-xs sm:text-sm text-danger-600 dark:text-danger-400">{errors.firstName}</p>
                )}
              </div>

              <div>
                <label className="block text-xs sm:text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  {t('signup:tenant.contactInfo.lastName')} *
                </label>
                <input
                  type="text"
                  value={formData.lastName}
                  onChange={(e) => handleInputChange('lastName', e.target.value)}
                  className={`w-full px-3 sm:px-4 py-2.5 sm:py-3 border rounded-lg text-sm sm:text-base bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 dark:focus:ring-primary-400 focus:border-primary-500 transition-colors ${
                    errors.lastName ? 'border-red-500 dark:border-red-400' : 'border-gray-200 dark:border-gray-600'
                  }`}
                />
                {errors.lastName && (
                  <p className="mt-1 text-xs sm:text-sm text-danger-600 dark:text-danger-400">{errors.lastName}</p>
                )}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-5 sm:gap-8">
              {/* Email Field with Verification */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  {t('signup:tenant.contactInfo.email')} *
                </label>
                <div className="space-y-2">
                  <div className="flex gap-2">
                    <input
                      type="email"
                      value={formData.contactEmail}
                      onChange={(e) => {
                        handleInputChange('contactEmail', e.target.value);
                        // Reset verification if email changes
                        if (formData.emailVerified && e.target.value !== formData.contactEmail) {
                          setFormData(prev => ({ ...prev, emailVerified: false }));
                        }
                      }}
                      disabled={showEmailVerification}
                      className={`flex-1 px-4 py-3 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white transition-colors ${
                        errors.contactEmail ? 'border-red-500 dark:border-red-400' : 
                        formData.emailVerified ? 'border-green-500 dark:border-green-400' :
                        'border-gray-200 dark:border-gray-600'
                      } ${showEmailVerification ? 'opacity-60' : ''}`}
                    />
                    {formData.emailVerified ? (
                      <div className="flex items-center px-3 py-2 bg-green-50 dark:bg-green-900/20 border border-green-500 dark:border-green-400 rounded-lg">
                        <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400" />
                      </div>
                    ) : (
                      <button
                        type="button"
                        onClick={() => {
                          // Validate email first - use same regex as backend Pydantic validator
                          if (!formData.contactEmail.trim()) {
                            setErrors(prev => ({ ...prev, contactEmail: t('signup:validation.emailRequired') }));
                            return;
                          }
                          if (!/^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(formData.contactEmail)) {
                            setErrors(prev => ({ ...prev, contactEmail: t('signup:validation.emailInvalid') }));
                            return;
                          }
                          setShowEmailVerification(true);
                        }}
                        disabled={!formData.contactEmail || showEmailVerification}
                        className="px-4 py-2 bg-primary-600 hover:bg-primary-700 disabled:bg-gray-300 dark:disabled:bg-gray-600 text-white text-sm rounded-lg font-medium transition-colors disabled:cursor-not-allowed whitespace-nowrap"
                      >
                        {t('signup:verification.verify')}
                      </button>
                    )}
                  </div>
                  {errors.contactEmail && (
                    <p className="text-sm text-danger-600 dark:text-danger-400">{errors.contactEmail}</p>
                  )}
                  {showEmailVerification && formData.contactEmail && (
                    <div className="border border-gray-200 dark:border-gray-600 rounded-lg p-4 bg-gray-50 dark:bg-gray-800">
                      <OTPVerification
                        identifier={formData.contactEmail}
                        identifierType="email"
                        onVerified={() => {
                          setFormData(prev => ({ ...prev, emailVerified: true }));
                          setShowEmailVerification(false);
                          setErrors(prev => {
                            const newErrors = { ...prev };
                            delete newErrors.contactEmail;
                            return newErrors;
                          });
                        }}
                        onCancel={() => setShowEmailVerification(false)}
                        onSendOTP={(identifier, type) => tenantService.sendOTP(identifier, type)}
                        onVerifyOTP={(identifier, type, code) => tenantService.verifyOTP(identifier, type, code)}
                        onResendOTP={(identifier, type) => tenantService.resendOTP(identifier, type)}
                      />
                    </div>
                  )}
                </div>
              </div>

              {/* Phone Field with Verification */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  {t('signup:tenant.contactInfo.phone')}
                </label>
                <div className="space-y-2">
                  <div className="flex gap-2">
                    <input
                      type="tel"
                      value={formData.contactPhone}
                      onChange={(e) => {
                        handleInputChange('contactPhone', e.target.value);
                        // Reset verification if phone changes
                        if (formData.phoneVerified && e.target.value !== formData.contactPhone) {
                          setFormData(prev => ({ ...prev, phoneVerified: false }));
                        }
                      }}
                      disabled={showPhoneVerification}
                      className={`flex-1 px-4 py-3 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white transition-colors ${
                        formData.phoneVerified ? 'border-green-500 dark:border-green-400' :
                        'border-gray-200 dark:border-gray-600'
                      } ${showPhoneVerification ? 'opacity-60' : ''}`}
                      placeholder={t('signup:tenant.contactInfo.phonePlaceholder')}
                    />
                    {formData.phoneVerified ? (
                      <div className="flex items-center px-3 py-2 bg-green-50 dark:bg-green-900/20 border border-green-500 dark:border-green-400 rounded-lg">
                        <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400" />
                      </div>
                    ) : formData.contactPhone.trim() ? (
                      <button
                        type="button"
                        onClick={() => setShowPhoneVerification(true)}
                        disabled={!formData.contactPhone || showPhoneVerification}
                        className="px-4 py-2 bg-primary-600 hover:bg-primary-700 disabled:bg-gray-300 dark:disabled:bg-gray-600 text-white text-sm rounded-lg font-medium transition-colors disabled:cursor-not-allowed whitespace-nowrap"
                      >
                        {t('signup:verification.verify')}
                      </button>
                    ) : null}
                  </div>
                  {showPhoneVerification && formData.contactPhone && (
                    <div className="border border-gray-200 dark:border-gray-600 rounded-lg p-4 bg-gray-50 dark:bg-gray-800">
                      <OTPVerification
                        identifier={formData.contactPhone}
                        identifierType="phone"
                        onVerified={() => {
                          setFormData(prev => ({ ...prev, phoneVerified: true }));
                          setShowPhoneVerification(false);
                        }}
                        onCancel={() => setShowPhoneVerification(false)}
                        onSendOTP={(identifier, type) => tenantService.sendOTP(identifier, type)}
                        onVerifyOTP={(identifier, type, code) => tenantService.verifyOTP(identifier, type, code)}
                        onResendOTP={(identifier, type) => tenantService.resendOTP(identifier, type)}
                      />
                    </div>
                  )}
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {t('signup:tenant.contactInfo.phoneOptional')}
                  </p>
                </div>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                {t('signup:tenant.contactInfo.street')} *
              </label>
              <ErrorBoundary fallback={
                <input
                  type="text"
                  value={formData.street}
                  onChange={(e) => handleInputChange('street', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 dark:bg-gray-700 dark:text-white"
                  placeholder={t('signup:tenant.contactInfo.streetPlaceholder')}
                />
              }>
                <AddressAutocomplete
                  value={formData.street}
                  onChange={(addressComponents: AddressComponents) => {
                    // Map province names to codes
                    const provinceMap: { [key: string]: string } = {
                      'Ontario': 'ON',
                      'Quebec': 'QC',
                      'British Columbia': 'BC',
                      'Alberta': 'AB',
                      'Manitoba': 'MB',
                      'Saskatchewan': 'SK',
                      'Nova Scotia': 'NS',
                      'New Brunswick': 'NB',
                      'Newfoundland and Labrador': 'NL',
                      'Prince Edward Island': 'PE',
                      'Northwest Territories': 'NT',
                      'Yukon': 'YT',
                      'Nunavut': 'NU'
                    };
                    
                    // Convert province name to code
                    const provinceCode = provinceMap[addressComponents.province] || addressComponents.province;
                    
                    // Update all address fields at once from autocomplete
                    setFormData({
                      ...formData,
                      street: addressComponents.street,
                      city: addressComponents.city,
                      province: provinceCode,
                      postalCode: addressComponents.postal_code
                    });
                    // Clear address-related errors
                    const newErrors = { ...errors };
                    delete newErrors.street;
                    delete newErrors.city;
                    delete newErrors.postalCode;
                    setErrors(newErrors);
                  }}
                  placeholder={t('signup:tenant.contactInfo.streetPlaceholder') || 'Start typing an address (e.g., 123 Main St, Toronto)'}
                  required
                />
              </ErrorBoundary>
              {errors.street && (
                <p className="mt-1 text-sm text-danger-600 dark:text-danger-400">{errors.street}</p>
              )}
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                💡 Start typing to see address suggestions - city and postal code will auto-fill
              </p>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-3 gap-3 sm:gap-8">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  {t('signup:tenant.contactInfo.city')} *
                </label>
                <input
                  type="text"
                  value={formData.city}
                  readOnly
                  className="w-full px-4 py-3 border border-gray-200 dark:border-gray-600 rounded-lg bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white cursor-not-allowed"
                  placeholder={t('signup:tenant.contactInfo.cityPlaceholder') || 'Auto-filled from address'}
                />
                {errors.city && (
                  <p className="mt-1 text-sm text-danger-600 dark:text-danger-400">{errors.city}</p>
                )}
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Auto-filled</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  {t('signup:tenant.contactInfo.province')} *
                </label>
                <select
                  value={formData.province}
                  onChange={(e) => handleInputChange('province', e.target.value)}
                  className="w-full px-4 py-3 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 dark:focus:ring-primary-400 focus:border-primary-500 transition-colors"
                >
                  {provinces.map(province => (
                    <option key={province.code} value={province.code}>
                      {province.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  {t('signup:tenant.contactInfo.postalCode')} *
                </label>
                <input
                  type="text"
                  value={formData.postalCode}
                  readOnly
                  className="w-full px-4 py-3 border border-gray-200 dark:border-gray-600 rounded-lg bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white cursor-not-allowed"
                  placeholder={t('signup:tenant.contactInfo.postalCodePlaceholder') || 'Auto-filled from address'}
                />
                {errors.postalCode && (
                  <p className="mt-1 text-sm text-danger-600 dark:text-danger-400">{errors.postalCode}</p>
                )}
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Auto-filled</p>
              </div>
            </div>
          </div>
        );

      case 3:
        // Step 3: Ontario Licensing (conditional)
        if (formData.province !== 'ON') {
          return null; // Skip for non-Ontario provinces
        }
        return (
          <div className="space-y-5 sm:space-y-7">
            <div>
              <h3 className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-white mb-2 sm:mb-3">
                Ontario Cannabis Licensing
              </h3>
              <p className="text-sm sm:text-base text-gray-600 dark:text-gray-400">
                Required for Ontario cannabis retailers. CROL is your tenant-level operating license, 
                CRSA is your store-level retail authorization.
              </p>
            </div>

            {/* CROL Number Input */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                CROL Number (Cannabis Retail Operating License) *
              </label>
              <input
                type="text"
                value={formData.crolNumber}
                onChange={(e) => handleInputChange('crolNumber', e.target.value)}
                className={`w-full px-4 py-3 border rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 dark:focus:ring-primary-400 focus:border-primary-500 transition-colors ${
                  errors.crolNumber ? 'border-red-500 dark:border-red-400' : 'border-gray-200 dark:border-gray-600'
                }`}
                placeholder="Enter your OCS CROL number"
              />
              {errors.crolNumber && (
                <p className="mt-1 text-sm text-danger-600 dark:text-danger-400">{errors.crolNumber}</p>
              )}
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                Your tenant-level OCS operating license number
              </p>
            </div>

            {/* CRSA Validator */}
            <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 sm:p-8">
              <h4 className="text-sm sm:text-base font-semibold text-gray-900 dark:text-white mb-4 sm:mb-5">
                CRSA Validation (Cannabis Retail Store Authorization)
              </h4>
              <OntarioLicenseValidator
                email={formData.contactEmail}
                onValidationSuccess={(result) => {
                  setCrsaValidation(result);
                  // Clear any previous validation errors
                  if (errors.crsaValidation) {
                    const newErrors = { ...errors };
                    delete newErrors.crsaValidation;
                    setErrors(newErrors);
                  }
                }}
              />
              {errors.crsaValidation && (
                <div className="mt-4 p-4 bg-red-50 dark:bg-red-900/20 border-2 border-red-500 dark:border-red-400 rounded-lg">
                  <p className="text-sm text-red-700 dark:text-red-400">
                    ⚠️ {errors.crsaValidation}
                  </p>
                </div>
              )}
              {crsaValidation?.is_valid && crsaValidation?.verification_tier === 'auto_approved' && (
                <div className="mt-4 p-4 bg-green-50 dark:bg-green-900/20 border-2 border-green-500 dark:border-green-400 rounded-lg">
                  <p className="text-sm text-green-700 dark:text-green-400 font-semibold">
                    ✓ Domain Verified - Your email domain matches the CRSA website. 
                    Your first store will be created automatically from this license.
                  </p>
                </div>
              )}
            </div>
          </div>
        );

      case 4:
        return (
          <div className="space-y-5 sm:space-y-7">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                {t('signup:tenant.accountSetup.password')} *
              </label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  value={formData.password}
                  onChange={(e) => handleInputChange('password', e.target.value)}
                  className={`w-full px-4 py-3 pr-12 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 ${
                    errors.password ? 'border-red-500 dark:border-red-400' : 'border-gray-200 dark:border-gray-600'
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
                <p className="mt-1 text-sm text-danger-600 dark:text-danger-400">{errors.password}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                {t('signup:tenant.accountSetup.confirmPassword')} *
              </label>
              <div className="relative">
                <input
                  type={showConfirmPassword ? "text" : "password"}
                  value={formData.confirmPassword}
                  onChange={(e) => handleInputChange('confirmPassword', e.target.value)}
                  className={`w-full px-4 py-3 pr-12 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 ${
                    errors.confirmPassword ? 'border-red-500 dark:border-red-400' : 'border-gray-200 dark:border-gray-600'
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
                <p className="mt-1 text-sm text-danger-600 dark:text-danger-400">{errors.confirmPassword}</p>
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

      case 5:
        const selectedPlanInfo = subscriptionPlans[formData.subscriptionTier as keyof typeof subscriptionPlans];

        // Show error message prominently at the top if there's a submit error
        if (errors.submit) {
          return (
            <div className="space-y-5 sm:space-y-7">
              <div className="bg-red-50 dark:bg-red-900/20 border-l-4 border-red-500 rounded-lg p-4 sm:p-6">
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
                  <div className="bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6 sm:p-8">
                    <div className="flex justify-between items-start mb-3">
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
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      {t('signup:tenant.subscription.billingCycle')}
                    </label>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6">
                      <label className="flex items-center p-4 sm:p-6 border-2 border-gray-200 dark:border-gray-700 rounded-lg cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700/50 active:scale-95 transition-all">
                        <input
                          type="radio"
                          name="billingCycle"
                          value="monthly"
                          checked={formData.billingCycle === 'monthly'}
                          onChange={(e) => handleInputChange('billingCycle', e.target.value)}
                          className="mr-3 flex-shrink-0"
                        />
                        <div>
                          <div className="font-medium text-gray-900 dark:text-white">{t('signup:tenant.subscription.monthly')}</div>
                          <div className="text-sm text-gray-500 dark:text-gray-400">{t('signup:tenant.subscription.monthlyBilled')}</div>
                        </div>
                      </label>
                      <label className="flex items-center p-4 sm:p-6 border-2 border-gray-200 dark:border-gray-700 rounded-lg cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700/50 active:scale-95 transition-all">
                        <input
                          type="radio"
                          name="billingCycle"
                          value="annual"
                          checked={formData.billingCycle === 'annual'}
                          onChange={(e) => handleInputChange('billingCycle', e.target.value)}
                          className="mr-3 flex-shrink-0"
                        />
                        <div>
                          <div className="font-medium text-gray-900 dark:text-white">{t('signup:tenant.subscription.annual')}</div>
                          <div className="text-sm text-gray-500 dark:text-gray-400">{t('signup:tenant.subscription.annualSave')}</div>
                        </div>
                      </label>
                    </div>
                  </div>

                  {/* Payment fields for non-free plans */}
                  {selectedPlanInfo.price !== 0 && (
                    <>
                      <div className="mb-6">
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
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

                      <div className="mb-6">
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                          <CreditCard className="inline w-5 h-5 mr-2" />
                          Card Details <span className="text-red-500">*</span>
                        </label>
                        <div className="border rounded-lg p-4 bg-white dark:bg-gray-700">
                          <CardElement
                            options={{
                              style: {
                                base: {
                                  fontSize: '16px',
                                  color: '#424770',
                                  '::placeholder': {
                                    color: '#aab7c4',
                                  },
                                },
                                invalid: {
                                  color: '#9e2146',
                                },
                              },
                            }}
                          />
                        </div>
                        <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
                          🔒 Secured by Stripe • Your card will be charged immediately
                        </p>
                      </div>
                    </>
                  )}

                  {/* Free tier message */}
                  {selectedPlanInfo.price === 0 && (
                    <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-700 rounded-lg p-6 text-center">
                      <CheckCircle className="w-12 h-12 text-green-600 dark:text-green-400 mx-auto mb-3" />
                      <h3 className="text-green-800 dark:text-green-300 text-xl font-semibold">
                        🎉 {t('signup:tenant.subscription.freeSelected')}
                      </h3>
                      <p className="text-green-700 dark:text-green-400 mt-2">
                        {t('signup:tenant.subscription.noPaymentRequired')}
                      </p>
                    </div>
                  )}
                </>
              )}
            </div>
          );
        }

        if (!selectedPlanInfo) {
          return (
            <div className="space-y-5 sm:space-y-7">
              <h3 className="text-lg sm:text-xl font-semibold mb-4 sm:mb-5">{t('signup:tenant.subscription.choosePlan')}</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
                {Object.entries(subscriptionPlans).map(([key, plan]) => (
                  <div
                    key={key}
                    onClick={() => handleInputChange('subscriptionTier', key)}
                    className="border-2 border-gray-200 dark:border-gray-700 rounded-lg p-4 sm:p-6 cursor-pointer hover:border-primary-500 dark:hover:border-primary-400 hover:shadow-lg transition-all bg-white dark:bg-gray-800 active:scale-95"
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
          <div className="space-y-5 sm:space-y-7">
            {/* Plan Summary */}
            <div className="bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 sm:p-8">
              <div className="flex flex-col sm:flex-row justify-between items-start gap-2 sm:gap-0 mb-3">
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
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                {t('signup:tenant.subscription.billingCycle')}
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6">
                <label className="flex items-center p-4 sm:p-6 border-2 border-gray-200 dark:border-gray-700 rounded-lg cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700/50 active:scale-95 transition-all">
                  <input
                    type="radio"
                    name="billingCycle"
                    value="monthly"
                    checked={formData.billingCycle === 'monthly'}
                    onChange={(e) => handleInputChange('billingCycle', e.target.value)}
                    className="mr-3 flex-shrink-0"
                  />
                  <div>
                    <div className="font-medium text-gray-900 dark:text-white">{t('signup:tenant.subscription.monthly')}</div>
                    <div className="text-sm text-gray-500 dark:text-gray-400">{t('signup:tenant.subscription.monthlyBilled')}</div>
                  </div>
                </label>
                <label className="flex items-center p-4 sm:p-6 border-2 border-gray-200 dark:border-gray-700 rounded-lg cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700/50 active:scale-95 transition-all">
                  <input
                    type="radio"
                    name="billingCycle"
                    value="annual"
                    checked={formData.billingCycle === 'annual'}
                    onChange={(e) => handleInputChange('billingCycle', e.target.value)}
                    className="mr-3 flex-shrink-0"
                  />
                  <div>
                    <div className="font-medium text-gray-900 dark:text-white">{t('signup:tenant.subscription.annual')}</div>
                    <div className="text-sm text-gray-500 dark:text-gray-400">{t('signup:tenant.subscription.annualSave')}</div>
                  </div>
                </label>
              </div>
            </div>

            {/* Payment Information - Skip for Community and Enterprise */}
            {formData.subscriptionTier !== 'enterprise' && formData.subscriptionTier !== 'community_and_new_business' && (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    {t('signup:tenant.payment.cardholderName')} *
                  </label>
                  <input
                    type="text"
                    value={formData.billingName}
                    onChange={(e) => handleInputChange('billingName', e.target.value)}
                    className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 ${
                      errors.billingName ? 'border-red-500 dark:border-red-400' : 'border-gray-200 dark:border-gray-600'
                    }`}
                  />
                  {errors.billingName && (
                    <p className="mt-1 text-sm text-danger-600 dark:text-danger-400">{errors.billingName}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                    <CreditCard className="inline w-5 h-5 mr-2" />
                    Card Details *
                  </label>
                  <div className="border rounded-lg p-4 bg-white dark:bg-gray-700">
                    <CardElement
                      options={{
                        style: {
                          base: {
                            fontSize: '16px',
                            color: '#424770',
                            '::placeholder': {
                              color: '#aab7c4',
                            },
                          },
                          invalid: {
                            color: '#9e2146',
                          },
                        },
                      }}
                    />
                  </div>
                  <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
                    🔒 Secured by Stripe • Your card will be charged immediately
                  </p>
                </div>
              </>
            )}

            {formData.subscriptionTier === 'community_and_new_business' && (
              <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-700 rounded-lg p-6 text-center">
                <CheckCircle className="w-12 h-12 text-green-600 dark:text-green-400 mx-auto mb-3" />
                <h3 className="text-green-800 dark:text-green-300 text-xl font-semibold">
                  🎉 Free Tier Selected
                </h3>
                <p className="text-green-700 dark:text-green-400 mt-2">
                  No payment required - continue to create your account!
                </p>
              </div>
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

            {/* Legal Attestations and Terms Acceptance */}
            <div className="border-t-2 border-gray-200 dark:border-gray-700 pt-6 mt-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
                <Shield className="h-5 w-5 mr-2 text-primary-600 dark:text-primary-400" />
                Legal Agreements & Attestations
              </h3>
              
              <div className="space-y-4">
                {/* Terms of Service */}
                <label className={`flex items-start p-4 border-2 rounded-lg cursor-pointer transition-all ${
                  termsAccepted 
                    ? 'border-primary-500 dark:border-primary-400 bg-primary-50 dark:bg-primary-900/10' 
                    : errors.terms 
                      ? 'border-red-500 dark:border-red-400 bg-red-50 dark:bg-red-900/10'
                      : 'border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500'
                }`}>
                  <input
                    type="checkbox"
                    checked={termsAccepted}
                    onChange={(e) => setTermsAccepted(e.target.checked)}
                    className="mt-1 mr-3 h-4 w-4 text-primary-600 focus:ring-primary-500 rounded flex-shrink-0"
                  />
                  <div className="text-sm">
                    <span className="text-gray-700 dark:text-gray-300">I accept the </span>
                    <a 
                      href="/TERMS_OF_SERVICE.md" 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-primary-600 dark:text-primary-400 hover:underline font-medium"
                      onClick={(e) => e.stopPropagation()}
                    >
                      Terms of Service
                    </a>
                    <span className="text-gray-700 dark:text-gray-300">, including AI-targeted advertising from Licensed Producers</span>
                  </div>
                </label>
                {errors.terms && (
                  <p className="text-sm text-red-600 dark:text-red-400 ml-7">{errors.terms}</p>
                )}

                {/* Privacy Policy */}
                <label className={`flex items-start p-4 border-2 rounded-lg cursor-pointer transition-all ${
                  privacyAccepted 
                    ? 'border-primary-500 dark:border-primary-400 bg-primary-50 dark:bg-primary-900/10' 
                    : errors.privacy 
                      ? 'border-red-500 dark:border-red-400 bg-red-50 dark:bg-red-900/10'
                      : 'border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500'
                }`}>
                  <input
                    type="checkbox"
                    checked={privacyAccepted}
                    onChange={(e) => setPrivacyAccepted(e.target.checked)}
                    className="mt-1 mr-3 h-4 w-4 text-primary-600 focus:ring-primary-500 rounded flex-shrink-0"
                  />
                  <div className="text-sm">
                    <span className="text-gray-700 dark:text-gray-300">I accept the </span>
                    <a 
                      href="/PRIVACY_POLICY.md" 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-primary-600 dark:text-primary-400 hover:underline font-medium"
                      onClick={(e) => e.stopPropagation()}
                    >
                      Privacy Policy
                    </a>
                    <span className="text-gray-700 dark:text-gray-300"> and consent to data collection and usage for advertising purposes</span>
                  </div>
                </label>
                {errors.privacy && (
                  <p className="text-sm text-red-600 dark:text-red-400 ml-7">{errors.privacy}</p>
                )}

                {/* Accuracy Attestation */}
                <label className={`flex items-start p-4 border-2 rounded-lg cursor-pointer transition-all ${
                  accuracyAttested 
                    ? 'border-primary-500 dark:border-primary-400 bg-primary-50 dark:bg-primary-900/10' 
                    : errors.accuracy 
                      ? 'border-red-500 dark:border-red-400 bg-red-50 dark:bg-red-900/10'
                      : 'border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500'
                }`}>
                  <input
                    type="checkbox"
                    checked={accuracyAttested}
                    onChange={(e) => setAccuracyAttested(e.target.checked)}
                    className="mt-1 mr-3 h-4 w-4 text-primary-600 focus:ring-primary-500 rounded flex-shrink-0"
                  />
                  <div className="text-sm text-gray-700 dark:text-gray-300">
                    <strong>I certify that all information provided in this registration is accurate, complete, and current.</strong> I understand that providing false or misleading information may result in account suspension or termination.
                  </div>
                </label>
                {errors.accuracy && (
                  <p className="text-sm text-red-600 dark:text-red-400 ml-7">{errors.accuracy}</p>
                )}

                {/* Authorization Attestation */}
                <label className={`flex items-start p-4 border-2 rounded-lg cursor-pointer transition-all ${
                  authorizationAttested 
                    ? 'border-primary-500 dark:border-primary-400 bg-primary-50 dark:bg-primary-900/10' 
                    : errors.authorization 
                      ? 'border-red-500 dark:border-red-400 bg-red-50 dark:bg-red-900/10'
                      : 'border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500'
                }`}>
                  <input
                    type="checkbox"
                    checked={authorizationAttested}
                    onChange={(e) => setAuthorizationAttested(e.target.checked)}
                    className="mt-1 mr-3 h-4 w-4 text-primary-600 focus:ring-primary-500 rounded flex-shrink-0"
                  />
                  <div className="text-sm text-gray-700 dark:text-gray-300">
                    <strong>I am duly authorized by my organization to create this account and bind the organization to these Terms.</strong> I have the legal authority to enter into agreements on behalf of the company listed above.
                  </div>
                </label>
                {errors.authorization && (
                  <p className="text-sm text-red-600 dark:text-red-400 ml-7">{errors.authorization}</p>
                )}

                {/* Information Notice */}
                <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700 rounded-lg p-4 mt-4">
                  <div className="flex items-start">
                    <AlertCircle className="h-5 w-5 text-blue-600 dark:text-blue-400 mt-0.5 mr-3 flex-shrink-0" />
                    <div className="text-sm text-blue-800 dark:text-blue-300">
                      <p className="font-medium mb-1">Important Notice:</p>
                      <ul className="list-disc list-inside space-y-1 text-xs">
                        <li>Your acceptance will be recorded with timestamp and IP address for legal compliance</li>
                        <li>Revenue is generated through AI-targeted advertising from Licensed Producers</li>
                        <li>Customer data will be used (anonymized) to improve product recommendations</li>
                        <li>You must comply with all cannabis laws and regulations in your jurisdiction</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            </div>

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
    t('signup:tenant.steps.ontario'),
    t('signup:tenant.steps.account'),
    t('signup:tenant.steps.payment')
  ];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex flex-col transition-colors duration-200">
      {/* Success Animation Overlay */}
      {showSuccessAnimation && (
        <div className="fixed inset-0 bg-black dark:bg-black bg-opacity-50 dark:bg-opacity-70 flex items-center justify-center z-50 animate-fadeIn">
          <div className="bg-white dark:bg-gray-800 rounded-2xl p-8 max-w-md w-full mx-4 animate-scaleIn border border-transparent dark:border-gray-700">
            <div className="text-center">
              <div className="mx-auto h-20 w-20 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center mb-4 animate-scaleIn">
                <svg
                  className="h-12 w-12 text-green-600 dark:text-green-400 success-check"
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
              <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-2 animate-fadeInUp">
                {t('signup:tenant.success.welcome')}
              </h3>
              <p className="text-gray-600 dark:text-gray-300 mb-6 animate-fadeInUp" style={{ animationDelay: '0.1s' }}>
                {t('signup:tenant.success.accountCreated')}
              </p>
              <div className="space-y-2 animate-fadeInUp" style={{ animationDelay: '0.2s' }}>
                <p className="text-sm text-gray-500 dark:text-gray-400">{t('signup:tenant.success.tenantCode')}</p>
                <p className="text-lg font-mono font-bold text-primary-600 dark:text-primary-400 bg-gray-50 dark:bg-gray-700 py-2 px-4 rounded-lg">
                  {formData.tenantCode}
                </p>
              </div>
              <div className="mt-6 animate-fadeInUp" style={{ animationDelay: '0.3s' }}>
                <div className="h-1 w-full bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                  <div className="h-full bg-gradient-to-r from-green-500 to-green-600 dark:from-green-600 dark:to-green-700 loading-shimmer"></div>
                </div>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">{t('signup:tenant.success.preparing')}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Header */}
      <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 transition-colors duration-200">
        <div className="max-w-5xl mx-auto px-3 sm:px-6 lg:px-8">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between py-3 sm:py-6 gap-2 sm:gap-0">
            <Link to="/" className="flex items-center">
              <ArrowLeft className="h-4 w-4 sm:h-5 sm:w-5 text-gray-400 dark:text-gray-500 mr-1.5 sm:mr-2 flex-shrink-0" />
              <Leaf className="h-5 w-5 sm:h-8 sm:w-8 text-primary-600 dark:text-primary-400 flex-shrink-0" />
              <span className="ml-1.5 sm:ml-2 text-base sm:text-2xl font-bold text-gray-900 dark:text-white">{t('signup:tenant.header.title')}</span>
            </Link>
            <div className="text-xs sm:text-sm text-gray-500 dark:text-gray-400">
              {t('signup:tenant.header.alreadyHaveAccount')} <Link to="/login" className="text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 transition-colors">{t('signup:tenant.header.signIn')}</Link>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 py-6 sm:py-10 lg:py-16">
        <div className="max-w-5xl mx-auto px-3 sm:px-6 lg:px-8">
          {/* Progress Bar */}
          <div className="mb-6 sm:mb-10 lg:mb-12">
            <div className="flex items-center justify-between">
              {stepTitles.map((title, index) => (
                <div key={index} className="flex items-center">
                  <div className={`flex items-center justify-center w-7 h-7 sm:w-9 sm:h-9 lg:w-10 lg:h-10 rounded-full border-2 text-xs sm:text-sm lg:text-base transition-colors ${
                    index + 1 <= currentStep
                      ? 'bg-primary-600 dark:bg-primary-500 border-primary-600 dark:border-primary-500 text-white'
                      : 'border-gray-200 dark:border-gray-600 text-gray-400 dark:text-gray-500'
                  }`}>
                    {index + 1 < currentStep ? (
                      <CheckCircle className="h-4 w-4 sm:h-5 sm:w-5 lg:h-6 lg:w-6" />
                    ) : (
                      <span>{index + 1}</span>
                    )}
                  </div>
                  {index < stepTitles.length - 1 && (
                    <div className={`flex-1 h-0.5 sm:h-1 mx-1 sm:mx-2 lg:mx-4 transition-colors ${
                      index + 1 < currentStep ? 'bg-primary-600 dark:bg-primary-500' : 'bg-gray-300 dark:bg-gray-600'
                    }`} />
                  )}
                </div>
              ))}
            </div>
            <div className="hidden sm:flex justify-between mt-2 sm:mt-3">
              {stepTitles.map((title, index) => (
                <div key={index} className={`text-xs sm:text-sm lg:text-base transition-colors ${
                  index + 1 === currentStep ? 'text-primary-600 dark:text-primary-400 font-medium' : 'text-gray-500 dark:text-gray-400'
                }`}>
                  {title}
                </div>
              ))}
            </div>
          </div>

          {/* Form */}
          <div className="bg-white dark:bg-gray-800 rounded-lg sm:rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4 sm:p-8 lg:p-12 transition-colors duration-200">
            <div className="mb-6 sm:mb-10">
              <h1 className="text-xl sm:text-3xl font-bold text-gray-900 dark:text-white mb-2 sm:mb-3">
                {stepTitles[currentStep - 1]}
              </h1>
              <p className="text-sm sm:text-lg text-gray-600 dark:text-gray-400">
                {currentStep === 1 && t('signup:tenant.stepDescriptions.company')}
                {currentStep === 2 && t('signup:tenant.stepDescriptions.contact')}
                {currentStep === 3 && t('signup:tenant.stepDescriptions.ontario')}
                {currentStep === 4 && t('signup:tenant.stepDescriptions.account')}
                {currentStep === 5 && t('signup:tenant.stepDescriptions.payment')}
              </p>
            </div>

            <div className="step-content">
              {renderStepContent()}
            </div>

            {/* Navigation Buttons */}
            <div className="flex flex-col-reverse sm:flex-row justify-between gap-3 sm:gap-4 pt-6 sm:pt-10 mt-6 sm:mt-10 border-t border-gray-200 dark:border-gray-700">
              <button
                onClick={prevStep}
                disabled={currentStep === 1}
                className={`flex items-center justify-center sm:justify-start px-4 sm:px-6 py-2.5 sm:py-3 rounded-lg font-medium text-sm sm:text-base transition-all active:scale-95 touch-manipulation ${
                  currentStep === 1
                    ? 'text-gray-400 dark:text-gray-600 cursor-not-allowed'
                    : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white hover:bg-gray-50 dark:hover:bg-gray-700'
                }`}
              >
                <ArrowLeft className="h-4 w-4 sm:h-5 sm:w-5 mr-2 flex-shrink-0" />
                <span className="hidden sm:inline">{t('signup:tenant.navigation.previous')}</span>
                <span className="sm:hidden">{t('signup:tenant.navigation.back')}</span>
              </button>

              {currentStep < 5 ? (
                <button
                  onClick={nextStep}
                  className="flex items-center justify-center sm:justify-start px-4 sm:px-6 py-2.5 sm:py-3 bg-primary-600 dark:bg-primary-500 text-white rounded-lg font-medium text-sm sm:text-base hover:bg-primary-700 dark:hover:bg-primary-600 transition-all active:scale-95 touch-manipulation"
                >
                  {t('signup:tenant.navigation.next')}
                  <ArrowRight className="h-4 w-4 sm:h-5 sm:w-5 ml-2 flex-shrink-0" />
                </button>
              ) : (
                <button
                  onClick={handleSubmit}
                  disabled={isSubmitting}
                  className="relative flex items-center justify-center px-6 sm:px-8 py-2.5 sm:py-3 bg-primary-600 dark:bg-primary-500 text-white rounded-lg font-medium text-sm sm:text-base hover:bg-primary-700 dark:hover:bg-primary-600 transition-all active:scale-95 touch-manipulation disabled:opacity-70 disabled:cursor-not-allowed disabled:transform-none overflow-hidden"
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 className="h-4 w-4 sm:h-5 sm:w-5 mr-2 animate-spin flex-shrink-0" />
                      <span className="animate-pulse truncate">
                        {submitProgress.message || t('signup:tenant.progress.processing')}
                      </span>
                    </>
                  ) : (
                    <>
                      <span>{t('signup:tenant.navigation.createAccount')}</span>
                      <CheckCircle className="h-4 w-4 sm:h-5 sm:w-5 ml-2 flex-shrink-0" />
                    </>
                  )}
                  {submitProgress.step === 'complete' && (
                    <div className="absolute inset-0 bg-green-600 dark:bg-green-500 flex items-center justify-center animate-slideIn">
                      <CheckCircle2 className="h-5 w-5 sm:h-6 sm:w-6 text-white animate-scaleIn" />
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