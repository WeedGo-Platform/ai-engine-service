import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Building2, User, Mail, Lock, Phone, AlertCircle, CheckCircle, Shield, Eye, EyeOff } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import tenantService from '../services/tenantService';

interface LocationState {
  tenantCode?: string;
  tenantName?: string;
  tenantId?: string;
  contactEmail?: string;
  firstName?: string;
  lastName?: string;
  phone?: string;
}

interface FormData {
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  password: string;
  confirmPassword: string;
}

const UserRegistration = () => {
  const { t } = useTranslation(['signup', 'common']);
  const navigate = useNavigate();
  const location = useLocation();
  const state = location.state as LocationState;
  
  const [tenantInfo, setTenantInfo] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [formData, setFormData] = useState<FormData>({
    firstName: state?.firstName || '',
    lastName: state?.lastName || '',
    email: state?.contactEmail || '',
    phone: state?.phone || '',
    password: '',
    confirmPassword: ''
  });
  const [passwordStrength, setPasswordStrength] = useState(0);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  useEffect(() => {
    fetchTenantInfo();
  }, []);

  const fetchTenantInfo = async () => {
    if (!state?.tenantCode) {
      navigate('/signup');
      return;
    }

    setIsLoading(true);
    try {
      const tenant = await tenantService.getTenantByCode(state.tenantCode);
      setTenantInfo(tenant);
      
      // Pre-fill email if available
      if (tenant.contact_email && !formData.email) {
        setFormData(prev => ({ ...prev, email: tenant.contact_email }));
      }
    } catch (error) {
      console.error('Failed to fetch tenant:', error);
      setErrors({ fetch: t('signup:userRegistration.errors.loadFailed') });
    } finally {
      setIsLoading(false);
    }
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

  const handleInputChange = (field: keyof FormData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    
    // Update password strength
    if (field === 'password') {
      setPasswordStrength(calculatePasswordStrength(value));
    }
    
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.firstName.trim()) {
      newErrors.firstName = t('signup:validation.firstNameRequired');
    }

    if (!formData.lastName.trim()) {
      newErrors.lastName = t('signup:validation.lastNameRequired');
    }

    if (!formData.email.trim()) {
      newErrors.email = t('signup:validation.emailRequired');
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = t('signup:validation.emailInvalid');
    }

    if (!formData.password) {
      newErrors.password = t('signup:validation.passwordRequired');
    } else if (formData.password.length < 8) {
      newErrors.password = t('signup:validation.passwordLength');
    } else if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(formData.password)) {
      newErrors.password = t('signup:validation.passwordComplexity');
    }

    if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = t('signup:validation.passwordMismatch');
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm() || !tenantInfo) return;
    
    setIsSubmitting(true);
    setErrors({});
    
    try {
      // Create user through the backend API
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:5024'}/api/users/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          tenant_id: tenantInfo.id,
          email: formData.email,
          password: formData.password,
          first_name: formData.firstName,
          last_name: formData.lastName,
          phone: formData.phone || undefined,
          role: 'admin'
        })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to create user account');
      }

      const result = await response.json();
      
      // Navigate to verification page
      navigate('/verification', {
        state: {
          email: formData.email,
          phone: formData.phone || undefined,
          userId: result.id,
          tenantName: tenantInfo.name
        }
      });
      
    } catch (error: any) {
      console.error('Registration error:', error);

      // Parse error message
      let errorMessage = t('signup:userRegistration.errors.failed');

      if (error.message?.includes('already exists') || error.message?.includes('duplicate')) {
        errorMessage = t('signup:userRegistration.errors.alreadyExists');
      } else if (error.message) {
        errorMessage = error.message;
      }

      setErrors({ submit: errorMessage });
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">{t('signup:userRegistration.loading')}</p>
        </div>
      </div>
    );
  }

  if (!tenantInfo) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">{t('signup:userRegistration.tenantNotFound')}</h2>
          <p className="text-gray-600 mb-4">{t('signup:userRegistration.tenantNotFoundDescription')}</p>
          <button
            onClick={() => navigate('/signup')}
            className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
          >
            {t('signup:userRegistration.goToSignup')}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-green-100 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md mx-auto">
        <div className="text-center mb-8">
          <div className="mx-auto h-12 w-12 bg-primary-600 rounded-full flex items-center justify-center mb-4">
            <User className="h-6 w-6 text-white" />
          </div>
          <h2 className="text-3xl font-bold text-gray-900">{t('signup:userRegistration.title')}</h2>
          <p className="mt-2 text-gray-600">{t('signup:userRegistration.joinTenant', { tenantName: tenantInfo.name })}</p>
        </div>

        <div className="bg-white border border-gray-200 rounded-lg p-8">
          {/* Tenant Information (Read-only) */}
          <div className="mb-6 p-6 bg-gray-50 rounded-lg">
            <div className="flex items-center mb-2">
              <Building2 className="h-5 w-5 text-gray-500 mr-2" />
              <span className="text-sm font-medium text-gray-700">{t('signup:userRegistration.tenantInfo')}</span>
            </div>
            <div className="space-y-2">
              <div>
                <span className="text-xs text-gray-500">{t('signup:userRegistration.tenantName')}</span>
                <p className="font-medium text-gray-900">{tenantInfo.name}</p>
              </div>
              <div>
                <span className="text-xs text-gray-500">{t('signup:userRegistration.tenantCode')}</span>
                <p className="font-mono text-sm text-gray-700">{tenantInfo.code}</p>
              </div>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('signup:userRegistration.firstName')} *
                </label>
                <input
                  type="text"
                  value={formData.firstName}
                  onChange={(e) => handleInputChange('firstName', e.target.value)}
                  className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 ${
                    errors.firstName ? 'border-red-500' : 'border-gray-200'
                  }`}
                  placeholder={t('signup:userRegistration.firstNamePlaceholder')}
                />
                {errors.firstName && (
                  <p className="mt-1 text-sm text-danger-600">{errors.firstName}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('signup:userRegistration.lastName')} *
                </label>
                <input
                  type="text"
                  value={formData.lastName}
                  onChange={(e) => handleInputChange('lastName', e.target.value)}
                  className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 ${
                    errors.lastName ? 'border-red-500' : 'border-gray-200'
                  }`}
                  placeholder={t('signup:userRegistration.lastNamePlaceholder')}
                />
                {errors.lastName && (
                  <p className="mt-1 text-sm text-danger-600">{errors.lastName}</p>
                )}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Mail className="inline h-4 w-4 mr-1" />
                {t('signup:userRegistration.email')} *
              </label>
              <input
                type="email"
                value={formData.email}
                readOnly
                className="w-full px-3 py-2 border rounded-lg bg-gray-50 border-gray-200 cursor-not-allowed"
                placeholder={t('signup:userRegistration.emailPlaceholder')}
              />
              {errors.email && (
                <p className="mt-1 text-sm text-danger-600">{errors.email}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Phone className="inline h-4 w-4 mr-1" />
                {t('signup:userRegistration.phone')}
              </label>
              <input
                type="tel"
                value={formData.phone}
                onChange={(e) => handleInputChange('phone', e.target.value)}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                placeholder={t('signup:userRegistration.phonePlaceholder')}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Lock className="inline h-4 w-4 mr-1" />
                {t('signup:userRegistration.password')} *
              </label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  value={formData.password}
                  onChange={(e) => handleInputChange('password', e.target.value)}
                  className={`w-full px-3 py-2 pr-10 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 ${
                    errors.password ? 'border-red-500' : 'border-gray-200'
                  }`}
                  placeholder={t('signup:userRegistration.passwordPlaceholder')}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-500 hover:text-gray-700"
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
              {errors.password && (
                <p className="mt-1 text-sm text-danger-600">{errors.password}</p>
              )}

              {/* Password Strength Indicator */}
              {formData.password && (
                <div className="mt-2">
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center">
                      <Shield className="h-3 w-3 text-gray-500 mr-1" />
                      <span className="text-xs text-gray-600">{t('signup:userRegistration.passwordStrength')}</span>
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

              <p className="mt-1 text-xs text-gray-500">
                {t('signup:userRegistration.passwordHelp')}
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Lock className="inline h-4 w-4 mr-1" />
                {t('signup:userRegistration.confirmPassword')} *
              </label>
              <div className="relative">
                <input
                  type={showConfirmPassword ? "text" : "password"}
                  value={formData.confirmPassword}
                  onChange={(e) => handleInputChange('confirmPassword', e.target.value)}
                  className={`w-full px-3 py-2 pr-10 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 ${
                    errors.confirmPassword ? 'border-red-500' : 'border-gray-200'
                  }`}
                  placeholder={t('signup:userRegistration.passwordPlaceholder')}
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-500 hover:text-gray-700"
                >
                  {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
              {errors.confirmPassword && (
                <p className="mt-1 text-sm text-danger-600">{errors.confirmPassword}</p>
              )}
            </div>

            {errors.submit && (
              <div className="bg-danger-50 border border-red-200 rounded-lg p-6">
                <div className="flex items-start">
                  <AlertCircle className="h-5 w-5 text-danger-600 mt-0.5 mr-3" />
                  <p className="text-sm text-red-700">{errors.submit}</p>
                </div>
              </div>
            )}

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full py-3 px-4 bg-primary-600 text-white font-medium rounded-lg hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isSubmitting ? t('signup:userRegistration.creating') : t('signup:userRegistration.createButton')}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-gray-600">
              {t('signup:userRegistration.alreadyHaveAccount')}{' '}
              <a href="/login" className="text-primary-600 hover:text-primary-700 font-medium">
                {t('signup:userRegistration.signIn')}
              </a>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UserRegistration;