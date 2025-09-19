import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Mail, Phone, Shield, CheckCircle, AlertCircle, RefreshCcw } from 'lucide-react';

interface LocationState {
  email?: string;
  phone?: string;
  userId?: string;
  tenantName?: string;
}

const Verification = () => {
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
      setErrors({ [type]: 'Please enter a valid code' });
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
        throw new Error(error.detail || 'Invalid verification code');
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
      setErrors({ [type]: error.message || 'Verification failed' });
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
        throw new Error(error.detail || 'Failed to resend code');
      }
      
      // Set 60 second cooldown
      setResendTimer(prev => ({ ...prev, [type]: 60 }));
      
    } catch (error: any) {
      setErrors({ [type]: error.message || 'Failed to resend code' });
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
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-green-100 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md mx-auto">
        <div className="text-center mb-8">
          <div className="mx-auto h-12 w-12 bg-primary-600 rounded-full flex items-center justify-center mb-4">
            <Shield className="h-6 w-6 text-white" />
          </div>
          <h2 className="text-3xl font-bold text-gray-900">Verify Your Account</h2>
          <p className="mt-2 text-gray-600">
            We've sent verification codes to your email {state.phone && 'and phone'}
          </p>
        </div>

        <div className="bg-white border border-gray-200 rounded-lg p-8 space-y-6">
          {/* Email Verification */}
          <div className={`border rounded-lg p-6 ${emailVerified ? 'border-primary-500 bg-primary-50' : 'border-gray-200'}`}>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center">
                <Mail className={`h-5 w-5 mr-2 ${emailVerified ? 'text-primary-600' : 'text-gray-500'}`} />
                <span className="font-medium text-gray-700">Email Verification</span>
              </div>
              {emailVerified && <CheckCircle className="h-5 w-5 text-primary-600" />}
            </div>
            
            {!emailVerified && (
              <>
                <p className="text-sm text-gray-600 mb-3">
                  Enter the code sent to {state.email}
                </p>
                
                <div className="flex space-x-2">
                  <input
                    type="text"
                    value={emailCode}
                    onChange={(e) => setEmailCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                    placeholder="000000"
                    className="flex-1 px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 text-center font-mono text-lg"
                    maxLength={6}
                    disabled={isLoading || emailVerified}
                  />
                  <button
                    onClick={() => handleVerifyCode('email')}
                    disabled={isLoading || emailVerified || !emailCode}
                    className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Verify
                  </button>
                </div>
                
                {errors.email && (
                  <p className="mt-2 text-sm text-danger-600">{errors.email}</p>
                )}
                
                <button
                  onClick={() => handleResendCode('email')}
                  disabled={resendTimer.email > 0 || isLoading}
                  className="mt-2 text-sm text-primary-600 hover:text-primary-700 disabled:text-gray-400 disabled:cursor-not-allowed flex items-center"
                >
                  <RefreshCcw className="h-3 w-3 mr-1" />
                  {resendTimer.email > 0 ? `Resend in ${resendTimer.email}s` : 'Resend code'}
                </button>
              </>
            )}
            
            {emailVerified && (
              <p className="text-sm text-primary-600">Email verified successfully!</p>
            )}
          </div>

          {/* Phone Verification (if phone provided) */}
          {state.phone && (
            <div className={`border rounded-lg p-6 ${phoneVerified ? 'border-primary-500 bg-primary-50' : 'border-gray-200'}`}>
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center">
                  <Phone className={`h-5 w-5 mr-2 ${phoneVerified ? 'text-primary-600' : 'text-gray-500'}`} />
                  <span className="font-medium text-gray-700">Phone Verification</span>
                </div>
                {phoneVerified && <CheckCircle className="h-5 w-5 text-primary-600" />}
              </div>
              
              {!phoneVerified && (
                <>
                  <p className="text-sm text-gray-600 mb-3">
                    Enter the code sent to {state.phone}
                  </p>
                  
                  <div className="flex space-x-2">
                    <input
                      type="text"
                      value={phoneCode}
                      onChange={(e) => setPhoneCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                      placeholder="000000"
                      className="flex-1 px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 text-center font-mono text-lg"
                      maxLength={6}
                      disabled={isLoading || phoneVerified}
                    />
                    <button
                      onClick={() => handleVerifyCode('phone')}
                      disabled={isLoading || phoneVerified || !phoneCode}
                      className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Verify
                    </button>
                  </div>
                  
                  {errors.phone && (
                    <p className="mt-2 text-sm text-danger-600">{errors.phone}</p>
                  )}
                  
                  <button
                    onClick={() => handleResendCode('phone')}
                    disabled={resendTimer.phone > 0 || isLoading}
                    className="mt-2 text-sm text-primary-600 hover:text-primary-700 disabled:text-gray-400 disabled:cursor-not-allowed flex items-center"
                  >
                    <RefreshCcw className="h-3 w-3 mr-1" />
                    {resendTimer.phone > 0 ? `Resend in ${resendTimer.phone}s` : 'Resend code'}
                  </button>
                </>
              )}
              
              {phoneVerified && (
                <p className="text-sm text-primary-600">Phone verified successfully!</p>
              )}
            </div>
          )}

          {/* Success message when all verified */}
          {emailVerified && (!state.phone || phoneVerified) && (
            <div className="bg-primary-50 border border-green-200 rounded-lg p-6">
              <div className="flex items-center">
                <CheckCircle className="h-5 w-5 text-primary-600 mr-2" />
                <p className="text-primary-700 font-medium">All verifications complete! Redirecting...</p>
              </div>
            </div>
          )}

          {/* Skip verification option */}
          {!emailVerified && (
            <div className="text-center pt-4 border-t border-gray-200">
              <button
                onClick={handleSkipVerification}
                className="text-sm text-gray-600 hover:text-gray-800"
              >
                Skip verification for now
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Verification;