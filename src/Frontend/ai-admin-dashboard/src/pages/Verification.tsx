import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate, useLocation } from 'react-router-dom';
import { Mail, Phone, Shield, CheckCircle, AlertCircle, RefreshCcw } from 'lucide-react';

interface LocationState {
  email?: string;
  phone?: string;
  userId?: string;
  tenantName?: string;
}

const Verification = () => {
  const { t } = useTranslation(['auth', 'common']);
  const navigate = useNavigate();
  const location = useLocation();
  const state = location.state as LocationState;
  
  const [emailCode, setEmailCode] = useState('');
  const [phoneCode, setPhoneCode] = useState('');
  const [emailVerified, setEmailVerified] = useState(false);
  const [phoneVerified, setPhoneVerified] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [resendTimer, setResendTimer] = useState<Record<string, number>>({ email: 0, phone: 0 });

  useEffect(() => {
    if (!state?.email) {
      navigate('/signup');
      return;
    }
  }, [state, navigate]);

  useEffect(() => {
    // Countdown timers for resend buttons
    const interval = setInterval(() => {
      setResendTimer(prev => ({
        email: prev.email > 0 ? prev.email - 1 : 0,
        phone: prev.phone > 0 ? prev.phone - 1 : 0
      }));
    }, 1000);
    
    return () => clearInterval(interval);
  }, []);

  const handleVerifyCode = async (type: 'email' | 'phone') => {
    const code = type === 'email' ? emailCode : phoneCode;
    const identifier = type === 'email' ? state.email : state.phone;

    if (!code || code.length < 4) {
      setErrors({ [type]: t('auth:errors.invalidCode') });
      return;
    }
    
    setIsLoading(true);
    setErrors({});
    
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:5024'}/api/v1/auth/otp/verify`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          identifier,
          identifier_type: type,
          code,
          purpose: 'verification'
        })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || t('auth:errors.verificationFailed'));
      }
      
      const result = await response.json();
      
      if (type === 'email') {
        setEmailVerified(true);
      } else {
        setPhoneVerified(true);
      }
      
      // If both are verified (or phone not provided), navigate to success
      if ((emailVerified || type === 'email') && (!state.phone || phoneVerified || type === 'phone')) {
        setTimeout(() => {
          navigate('/signup-success', {
            state: {
              tenantName: state.tenantName,
              userEmail: state.email,
              verified: true
            }
          });
        }, 1500);
      }

    } catch (error: any) {
      setErrors({ [type]: error.message || t('auth:errors.verificationError') });
    } finally {
      setIsLoading(false);
    }
  };

  const handleResendCode = async (type: 'email' | 'phone') => {
    if (resendTimer[type] > 0) return;
    
    const identifier = type === 'email' ? state.email : state.phone;
    
    setIsLoading(true);
    setErrors({});
    
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:5024'}/api/v1/auth/otp/resend`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          identifier,
          identifier_type: type,
          purpose: 'verification'
        })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || t('auth:errors.resendFailed'));
      }
      
      // Set 60 second cooldown
      setResendTimer(prev => ({ ...prev, [type]: 60 }));

    } catch (error: any) {
      setErrors({ [type]: error.message || t('auth:errors.resendFailed') });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSkipVerification = () => {
    navigate('/signup-success', {
      state: {
        tenantName: state.tenantName,
        userEmail: state.email,
        verified: false
      }
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-green-100 dark:from-gray-900 dark:to-gray-800 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md mx-auto">
        <div className="text-center mb-8">
          <div className="mx-auto h-12 w-12 bg-primary-600 dark:bg-primary-700 rounded-full flex items-center justify-center mb-4">
            <Shield className="h-6 w-6 text-white" />
          </div>
          <h2 className="text-3xl font-bold text-gray-900 dark:text-white">{t('auth:verification.title')}</h2>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            {state.phone ? t('auth:verification.subtitleWithPhone') : t('auth:verification.subtitle')}
          </p>
        </div>

        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-8 space-y-6">
          {/* Email Verification */}
          <div className={`border rounded-lg p-6 ${emailVerified ? 'border-primary-500 dark:border-primary-600 bg-primary-50 dark:bg-primary-900/20' : 'border-gray-200 dark:border-gray-700'}`}>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center">
                <Mail className={`h-5 w-5 mr-2 ${emailVerified ? 'text-primary-600 dark:text-primary-400' : 'text-gray-500 dark:text-gray-400'}`} />
                <span className="font-medium text-gray-700 dark:text-gray-300">{t('auth:verification.email.title')}</span>
              </div>
              {emailVerified && <CheckCircle className="h-5 w-5 text-primary-600 dark:text-primary-400" />}
            </div>

            {!emailVerified && (
              <>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                  {t('auth:verification.email.instruction', { email: state.email })}
                </p>

                <div className="flex space-x-2">
                  <input
                    type="text"
                    value={emailCode}
                    onChange={(e) => setEmailCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                    placeholder={t('auth:verification.codePlaceholder')}
                    className="flex-1 px-3 py-2 border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg focus:ring-2 focus:ring-primary-500 dark:focus:ring-primary-400 focus:border-primary-500 dark:focus:border-primary-400 text-center font-mono text-lg"
                    maxLength={6}
                    disabled={isLoading || emailVerified}
                  />
                  <button
                    onClick={() => handleVerifyCode('email')}
                    disabled={isLoading || emailVerified || !emailCode}
                    className="px-4 py-2 bg-primary-600 dark:bg-primary-700 text-white rounded-lg hover:bg-primary-700 dark:hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {t('auth:verification.verify')}
                  </button>
                </div>

                {errors.email && (
                  <p className="mt-2 text-sm text-danger-600 dark:text-red-400">{errors.email}</p>
                )}

                <button
                  onClick={() => handleResendCode('email')}
                  disabled={resendTimer.email > 0 || isLoading}
                  className="mt-2 text-sm text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 disabled:text-gray-400 disabled:cursor-not-allowed flex items-center"
                >
                  <RefreshCcw className="h-3 w-3 mr-1" />
                  {resendTimer.email > 0 ? t('auth:verification.resendTimer', { seconds: resendTimer.email }) : t('auth:verification.resend')}
                </button>
              </>
            )}

            {emailVerified && (
              <p className="text-sm text-primary-600 dark:text-primary-400">{t('auth:verification.email.verified')}</p>
            )}
          </div>

          {/* Phone Verification (if phone provided) */}
          {state.phone && (
            <div className={`border rounded-lg p-6 ${phoneVerified ? 'border-primary-500 dark:border-primary-600 bg-primary-50 dark:bg-primary-900/20' : 'border-gray-200 dark:border-gray-700'}`}>
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center">
                  <Phone className={`h-5 w-5 mr-2 ${phoneVerified ? 'text-primary-600 dark:text-primary-400' : 'text-gray-500 dark:text-gray-400'}`} />
                  <span className="font-medium text-gray-700 dark:text-gray-300">{t('auth:verification.phone.title')}</span>
                </div>
                {phoneVerified && <CheckCircle className="h-5 w-5 text-primary-600 dark:text-primary-400" />}
              </div>

              {!phoneVerified && (
                <>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                    {t('auth:verification.phone.instruction', { phone: state.phone })}
                  </p>

                  <div className="flex space-x-2">
                    <input
                      type="text"
                      value={phoneCode}
                      onChange={(e) => setPhoneCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                      placeholder={t('auth:verification.codePlaceholder')}
                      className="flex-1 px-3 py-2 border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg focus:ring-2 focus:ring-primary-500 dark:focus:ring-primary-400 focus:border-primary-500 dark:focus:border-primary-400 text-center font-mono text-lg"
                      maxLength={6}
                      disabled={isLoading || phoneVerified}
                    />
                    <button
                      onClick={() => handleVerifyCode('phone')}
                      disabled={isLoading || phoneVerified || !phoneCode}
                      className="px-4 py-2 bg-primary-600 dark:bg-primary-700 text-white rounded-lg hover:bg-primary-700 dark:hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {t('auth:verification.verify')}
                    </button>
                  </div>

                  {errors.phone && (
                    <p className="mt-2 text-sm text-danger-600 dark:text-red-400">{errors.phone}</p>
                  )}

                  <button
                    onClick={() => handleResendCode('phone')}
                    disabled={resendTimer.phone > 0 || isLoading}
                    className="mt-2 text-sm text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 disabled:text-gray-400 disabled:cursor-not-allowed flex items-center"
                  >
                    <RefreshCcw className="h-3 w-3 mr-1" />
                    {resendTimer.phone > 0 ? t('auth:verification.resendTimer', { seconds: resendTimer.phone }) : t('auth:verification.resend')}
                  </button>
                </>
              )}

              {phoneVerified && (
                <p className="text-sm text-primary-600 dark:text-primary-400">{t('auth:verification.phone.verified')}</p>
              )}
            </div>
          )}

          {/* Success message when all verified */}
          {emailVerified && (!state.phone || phoneVerified) && (
            <div className="bg-primary-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-6">
              <div className="flex items-center">
                <CheckCircle className="h-5 w-5 text-primary-600 dark:text-primary-400 mr-2" />
                <p className="text-primary-700 dark:text-primary-300 font-medium">{t('auth:verification.allComplete')}</p>
              </div>
            </div>
          )}

          {/* Skip verification option */}
          {!emailVerified && (
            <div className="text-center pt-4 border-t border-gray-200 dark:border-gray-700">
              <button
                onClick={handleSkipVerification}
                className="text-sm text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
              >
                {t('auth:verification.skip')}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Verification;