import React, { useState } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { 
  Leaf, Lock, Mail, Eye, EyeOff, AlertCircle, 
  Loader2, Shield, CheckCircle 
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

const Login: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();
  const { t } = useTranslation(['auth', 'common']);
  
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    rememberMe: false
  });
  
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  
  // Get redirect path from location state or default to dashboard
  const from = (location.state as any)?.from?.pathname || '/dashboard';
  
  const validateForm = (): boolean => {
    if (!formData.email) {
      setError(t('common:errors.required'));
      return false;
    }
    
    if (!formData.email.includes('@')) {
      setError(t('common:errors.invalidEmail'));
      return false;
    }
    
    if (!formData.password) {
      setError(t('common:errors.required'));
      return false;
    }
    
    if (formData.password.length < 6) {
      setError(t('auth:errors.loginFailed'));
      return false;
    }
    
    return true;
  };
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Clear previous messages
    setError(null);
    setSuccess(null);
    
    // Validate form
    if (!validateForm()) {
      return;
    }
    
    setLoading(true);
    
    try {
      await login(formData.email, formData.password, formData.rememberMe);

      setSuccess(t('errors:auth.loginSuccess'));

      // Redirect after a short delay for UX
      setTimeout(() => {
        navigate(from, { replace: true });
      }, 1000);

    } catch (err: any) {
      console.error('Login error:', err);

      // Handle specific error cases
      if (err.response?.status === 429) {
        setError(t('errors:auth.tooManyAttempts'));
      } else if (err.response?.status === 403) {
        setError(t('errors:auth.accountDisabled'));
      } else if (err.response?.status === 401) {
        setError(t('errors:auth.invalidCredentials'));
      } else if (err.message === 'Network Error') {
        setError(t('errors:api.networkError'));
      } else {
        // Handle FastAPI validation errors which may be arrays
        const detail = err.response?.data?.detail;
        if (Array.isArray(detail)) {
          // Extract validation error messages
          const messages = detail.map((d: any) => d.msg || d.message || JSON.stringify(d)).join(', ');
          setError(messages || t('errors:auth.validationError'));
        } else if (typeof detail === 'string') {
          setError(detail);
        } else {
          setError(t('errors:auth.loginError'));
        }
      }
    } finally {
      setLoading(false);
    }
  };
  
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
    
    // Clear error when user starts typing
    if (error) {
      setError(null);
    }
  };
  
  return (
    <div className="min-h-screen bg-white dark:bg-gray-900 flex flex-col justify-center py-12 sm:px-6 lg:px-8 transition-colors duration-200">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        {/* Logo and Title */}
        <div className="flex justify-center">
          <div className="bg-primary-600 dark:bg-primary-500 p-4 rounded-xl">
            <Leaf className="h-10 w-10 text-white" />
          </div>
        </div>
        
        <h2 className="mt-6 text-center text-2xl font-semibold text-gray-900 dark:text-white">
          {t('auth:login.title')}
        </h2>

        <p className="mt-2 text-center text-sm text-gray-500 dark:text-gray-400">
          {t('auth:login.subtitle')}
        </p>
      </div>
      
      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white dark:bg-gray-800 py-8 px-4 border border-gray-200 dark:border-gray-700 sm:rounded-xl sm:px-10">
          <form className="space-y-6" onSubmit={handleSubmit}>
            {/* Email Field */}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                {t('auth:login.email')}
              </label>
              <div className="mt-1 relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Mail className="h-5 w-5 text-gray-400 dark:text-gray-500" />
                </div>
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={formData.email}
                  onChange={handleInputChange}
                  className="appearance-none block w-full pl-10 pr-3 py-2.5 border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all sm:text-sm"
                  placeholder={t('common:placeholders.enterEmail')}
                />
              </div>
            </div>
            
            {/* Password Field */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                {t('auth:login.password')}
              </label>
              <div className="mt-1 relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock className="h-5 w-5 text-gray-400 dark:text-gray-500" />
                </div>
                <input
                  id="password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  required
                  value={formData.password}
                  onChange={handleInputChange}
                  className="appearance-none block w-full pl-10 pr-10 py-2.5 border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all sm:text-sm"
                  placeholder={t('common:placeholders.enterPassword')}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center"
                >
                  {showPassword ? (
                    <EyeOff className="h-5 w-5 text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300" />
                  ) : (
                    <Eye className="h-5 w-5 text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300" />
                  )}
                </button>
              </div>
            </div>
            
            {/* Remember Me & Forgot Password */}
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <input
                  id="rememberMe"
                  name="rememberMe"
                  type="checkbox"
                  checked={formData.rememberMe}
                  onChange={handleInputChange}
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-200 dark:border-gray-600 rounded dark:bg-gray-700"
                />
                <label htmlFor="rememberMe" className="ml-2 block text-sm text-gray-600 dark:text-gray-300">
                  {t('auth:login.rememberMe')}
                </label>
              </div>
              
              <div className="text-sm">
                <a href="#" className="font-medium text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 text-sm">
                  {t('auth:login.forgotPassword')}
                </a>
              </div>
            </div>
            
            {/* Error Message */}
            {error && (
              <div className="rounded-lg bg-danger-50 dark:bg-danger-900/20 border border-danger-200 dark:border-danger-800 p-6">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <AlertCircle className="h-5 w-5 text-red-400" />
                  </div>
                  <div className="ml-3">
                    <p className="text-sm text-danger-700 dark:text-danger-400">
                      {error}
                    </p>
                  </div>
                </div>
              </div>
            )}
            
            {/* Success Message */}
            {success && (
              <div className="rounded-lg bg-success-50 dark:bg-success-900/20 border border-success-200 dark:border-success-800 p-6">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <CheckCircle className="h-5 w-5 text-green-400" />
                  </div>
                  <div className="ml-3">
                    <p className="text-sm text-success-700 dark:text-success-400">
                      {success}
                    </p>
                  </div>
                </div>
              </div>
            )}
            
            {/* Submit Button */}
            <div>
              <button
                type="submit"
                disabled={loading}
                className="w-full flex justify-center py-2.5 px-4 border border-transparent rounded-lg text-sm font-medium text-white bg-primary-600 dark:bg-primary-500 hover:bg-primary-700 dark:hover:bg-primary-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
              >
                {loading ? (
                  <>
                    <Loader2 className="animate-spin h-5 w-5 mr-2" />
                    {t('auth:login.signingIn')}
                  </>
                ) : (
                  <>
                    <Shield className="h-5 w-5 mr-2" />
                    {t('auth:login.signIn')}
                  </>
                )}
              </button>
            </div>

            {/* Forgot Password Link */}
            <div className="text-center">
              <Link
                to="/forgot-password"
                className="text-sm text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 hover:underline"
              >
                {t('auth:login.forgotPassword')}
              </Link>
            </div>
          </form>
          
          {/* Signup Link */}
          <div className="mt-6 text-center">
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {t('auth:login.noAccount')}{' '}
              <Link to="/signup" className="font-medium text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300">
                {t('auth:login.signUp')}
              </Link>
            </p>
          </div>
          
          {/* Security Notice */}
          <div className="mt-6">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-200 dark:border-gray-700" />
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-white dark:bg-gray-800 text-gray-400 dark:text-gray-500 text-xs uppercase tracking-wider">
                  {t('auth:login.securityNotice')}
                </span>
              </div>
            </div>
            
            <div className="mt-4 text-center text-xs text-gray-400 dark:text-gray-500">
              {t('auth:login.securityWarning')}
            </div>
            
            <div className="mt-6 text-center">
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {t('auth:login.noAccount')}{' '}
                <Link to="/signup" className="font-medium text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300">
                  {t('auth:login.signUp')}
                </Link>
              </p>
              <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
                <Link to="/" className="font-medium text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300">
                  {t('auth:login.learnMore')}
                </Link>
              </p>
            </div>
          </div>
        </div>
      </div>
      
      {/* Footer */}
      <div className="mt-8 text-center text-xs text-gray-400 dark:text-gray-500">
        {t('auth:login.copyright')}
      </div>
    </div>
  );
};

export default Login;