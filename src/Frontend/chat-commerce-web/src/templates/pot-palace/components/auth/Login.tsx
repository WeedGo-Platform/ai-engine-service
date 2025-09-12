import React, { useState, useEffect } from 'react';
import Button from '../ui/Button';
import Input from '../ui/Input';
import Modal from '../ui/Modal';
import Card from '../ui/Card';
import Badge from '../ui/Badge';
import { LoginFormProps } from '../../../../core/contracts/template.contracts';
import { detectContactType, getContactPlaceholder } from '../../../../utils/validation';
import VoiceLogin from '../../../../components/auth/VoiceLogin';
import VoiceEnrollment from '../../../../components/auth/VoiceEnrollment';

const Login: React.FC<LoginFormProps> = ({ onClose, onSubmit, onRegister }) => {
  const [loginMethod, setLoginMethod] = useState<'password' | 'otp' | 'voice'>('password');
  const [email, setEmail] = useState('');
  const [contactInput, setContactInput] = useState('');
  const [password, setPassword] = useState('');
  const [otpCode, setOtpCode] = useState('');
  const [error, setError] = useState('');
  const [otpSent, setOtpSent] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [loading, setLoading] = useState(false);
  const [resendCooldown, setResendCooldown] = useState(0);
  const [currentIdentifier, setCurrentIdentifier] = useState('');
  const [showVoiceEnrollment, setShowVoiceEnrollment] = useState(false);
  const [enrollmentUserId, setEnrollmentUserId] = useState('');

  // Clear errors when switching login methods
  useEffect(() => {
    setError('');
    setOtpSent(false);
    setOtpCode('');
  }, [loginMethod]);

  // Load remembered email
  useEffect(() => {
    const rememberedEmail = localStorage.getItem('rememberedEmail');
    if (rememberedEmail) {
      setEmail(rememberedEmail);
      setRememberMe(true);
    }
  }, []);

  // Resend cooldown timer
  useEffect(() => {
    if (resendCooldown > 0) {
      const timer = setTimeout(() => {
        setResendCooldown(resendCooldown - 1);
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, [resendCooldown]);

  const handleSendOTP = async () => {
    if (!contactInput) return;
    setError('');
    setLoading(true);
    
    try {
      // In a real implementation, this would call an API to send OTP
      // For now, we'll just simulate it
      await new Promise(resolve => setTimeout(resolve, 1000));
      setOtpSent(true);
      setCurrentIdentifier(contactInput);
      setResendCooldown(60); // 60 second cooldown
    } catch (err: any) {
      setError(err.message || 'Failed to send verification code');
    } finally {
      setLoading(false);
    }
  };

  const handleResendOTP = async () => {
    if (!currentIdentifier || resendCooldown > 0) return;
    setError('');
    setLoading(true);
    
    try {
      // In a real implementation, this would call an API to resend OTP
      // For now, we'll just simulate it
      await new Promise(resolve => setTimeout(resolve, 1000));
      setResendCooldown(60); // Reset cooldown
    } catch (err: any) {
      setError(err.message || 'Failed to resend verification code');
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (loginMethod === 'password') {
        await onSubmit({ email, password });
      } else {
        await onSubmit({ email: contactInput, otp: otpCode });
      }
      
      if (rememberMe) {
        localStorage.setItem('rememberedEmail', email);
      } else {
        localStorage.removeItem('rememberedEmail');
      }
      
      onClose();
    } catch (err: any) {
      setError(err.message || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal isOpen onClose={onClose} title="Welcome Back to Pot Palace">
      <div className="space-y-4">
        {/* Logo and Header */}
        <div className="text-center">
          <div className="flex justify-center mb-2">
            <div className="relative">
              <div className="absolute inset-0 bg-gradient-to-r from-purple-400 to-pink-400 rounded-full blur-xl opacity-30 animate-pulse"></div>
              <div className="relative z-10 w-16 h-16 bg-gradient-to-br from-purple-100 to-pink-100 rounded-full flex items-center justify-center">
                <span className="text-2xl">🌿</span>
              </div>
            </div>
          </div>
          <h2 className="text-xl font-bold text-purple-800 mb-1">Welcome Back!</h2>
          <p className="text-sm text-purple-600">Sign in to your premium cannabis experience</p>
        </div>

        {/* Login Method Toggle */}
        <div className="flex bg-purple-100 rounded-xl p-1">
          <button
            type="button"
            onClick={() => setLoginMethod('password')}
            className={`flex-1 py-2.5 px-3 rounded-lg font-semibold transition-all duration-300 ${
              loginMethod === 'password'
                ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-lg'
                : 'text-purple-600 hover:text-purple-800'
            }`}
          >
            <div className="flex items-center justify-center gap-1">
              <span>🔐</span>
              <span className="hidden sm:inline">Password</span>
            </div>
          </button>
          <button
            type="button"
            onClick={() => setLoginMethod('otp')}
            className={`flex-1 py-2.5 px-3 rounded-lg font-semibold transition-all duration-300 ${
              loginMethod === 'otp'
                ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-lg'
                : 'text-purple-600 hover:text-purple-800'
            }`}
          >
            <div className="flex items-center justify-center gap-1">
              <span>📱</span>
              <span className="hidden sm:inline">Code</span>
            </div>
          </button>
          <button
            type="button"
            onClick={() => setLoginMethod('voice')}
            className={`flex-1 py-2.5 px-3 rounded-lg font-semibold transition-all duration-300 ${
              loginMethod === 'voice'
                ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-lg'
                : 'text-purple-600 hover:text-purple-800'
            }`}
          >
            <div className="flex items-center justify-center gap-1">
              <span>🎤</span>
              <span className="hidden sm:inline">Voice</span>
            </div>
          </button>
        </div>

        {/* Voice Login */}
        {loginMethod === 'voice' ? (
          <div className="space-y-4">
            {showVoiceEnrollment ? (
              <VoiceEnrollment
                userId={enrollmentUserId}
                userEmail={email}
                onSuccess={() => {
                  setShowVoiceEnrollment(false);
                  setError('');
                }}
                onCancel={() => {
                  setShowVoiceEnrollment(false);
                  setLoginMethod('password');
                }}
                className="pot-palace-voice-enrollment"
                buttonClassName="pot-palace-button"
              />
            ) : (
              <VoiceLogin
                onSuccess={async (user) => {
                  await onSubmit({ email: user.email });
                  onClose();
                }}
                onCancel={() => setLoginMethod('password')}
                onEnrollRequired={(userEmail) => {
                  setEmail(userEmail);
                  setEnrollmentUserId(userEmail);
                  setShowVoiceEnrollment(true);
                }}
                onRegister={onRegister}
                onClose={onClose}
                className=""
                buttonClassName="w-full py-3 px-4 bg-gradient-to-r from-purple-600 to-pink-600 text-white font-bold rounded-xl hover:from-purple-700 hover:to-pink-700 transition-all duration-300 shadow-lg disabled:opacity-50"
                waveformClassName=""
                showAgeVerification={true}
              />
            )}
          </div>
        ) : (
        <form onSubmit={handleLogin} className="space-y-4">
          {/* Email Field - for password login */}
          {loginMethod === 'password' && (
            <Input
              type="email"
              label="Email Address"
              value={email}
              placeholder="Enter your email address"
              required
              onChange={setEmail}
            />
          )}
          
          {/* Contact Input Field - for OTP login */}
          {loginMethod === 'otp' && (
            <div className="space-y-2">
              <Input
                type="text"
                label="Email or Phone"
                value={contactInput}
                placeholder="Enter email or phone number"
                required
                onChange={setContactInput}
              />
              {contactInput && (
                <div className="text-xs px-2">
                  {(() => {
                    const contactInfo = detectContactType(contactInput);
                    if (contactInfo.type === 'email') {
                      return <span className="text-purple-600">📧 Email detected</span>;
                    } else if (contactInfo.type === 'phone') {
                      return <span className="text-purple-600">📱 Phone detected: {contactInfo.formatted}</span>;
                    } else if (contactInput.length > 0) {
                      return <span className="text-orange-600">⚠️ Please enter a valid email or phone number</span>;
                    }
                    return null;
                  })()}
                </div>
              )}
            </div>
          )}


          {/* Password Login Fields */}
          {loginMethod === 'password' ? (
            <>
              <div className="space-y-4">
                <div className="relative">
                  <Input
                    type={showPassword ? 'text' : 'password'}
                    label="Password"
                    value={password}
                    placeholder="Enter your password"
                    required
                    onChange={setPassword}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-9 text-purple-600 hover:text-purple-800 transition-colors"
                  >
                    {showPassword ? '👁️' : '👁️‍🗨️'}
                  </button>
                </div>
                
                <div className="flex items-center justify-between">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={rememberMe}
                      onChange={(e) => setRememberMe(e.target.checked)}
                      className="w-4 h-4 text-purple-600 border-purple-300 rounded focus:ring-purple-500"
                    />
                    <span className="text-sm text-purple-700">Remember me</span>
                  </label>
                  <button
                    type="button"
                    className="text-sm text-pink-600 hover:text-pink-700 font-medium"
                    onClick={() => alert('Forgot password feature coming soon! 🌿')}
                  >
                    Forgot Password?
                  </button>
                </div>
              </div>
            </>
          ) : (
            /* OTP Login Fields */
            <>
              {!otpSent ? (
                <div className="space-y-4">
                  <Card variant="filled" className="p-4">
                    <div className="flex items-start gap-3">
                      <span className="text-2xl">✨</span>
                      <div className="text-sm text-purple-800">
                        <p className="font-semibold mb-1">Quick & Secure Login</p>
                        <p className="text-xs">We'll send a verification code to your email or phone for passwordless sign-in.</p>
                      </div>
                    </div>
                  </Card>
                  
                  <Button
                    type="button"
                    onClick={handleSendOTP}
                    disabled={loading || !contactInput}
                    loading={loading}
                    variant="secondary"
                    className="w-full"
                  >
                    {loading ? 'Sending Magic Code...' : 'Send Verification Code 🌿'}
                  </Button>
                </div>
              ) : (
                <div className="space-y-4">
                  <Input
                    type="text"
                    label="Verification Code"
                    value={otpCode}
                    placeholder="000000"
                    onChange={(value) => setOtpCode(value.replace(/\D/g, '').slice(0, 6))}
                    className="font-mono text-lg tracking-widest text-center"
                  />
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-purple-600">
                      {resendCooldown > 0 
                        ? `Resend available in ${resendCooldown}s` 
                        : "Didn't receive the code?"}
                    </span>
                    <button
                      type="button"
                      onClick={handleResendOTP}
                      disabled={loading || resendCooldown > 0}
                      className={`text-xs font-semibold transition-colors ${
                        resendCooldown > 0 
                          ? 'text-gray-400 cursor-not-allowed' 
                          : 'text-pink-600 hover:text-pink-700 cursor-pointer'
                      }`}
                    >
                      {loading ? 'Sending...' : 'Resend Code 🔄'}
                    </button>
                  </div>
                </div>
              )}
            </>
          )}

          {/* Error Message */}
          {error && (
            <Card variant="filled" className="p-4 bg-gradient-to-r from-red-100 to-red-50 border-red-300">
              <div className="flex items-center gap-2 text-red-700 text-sm">
                <span>⚠️</span>
                {error}
              </div>
            </Card>
          )}

          {/* Submit Button */}
          {(loginMethod === 'password' || (loginMethod === 'otp' && otpSent)) && (
            <Button
              type="submit"
              disabled={loading}
              loading={loading}
              className="w-full"
              size="lg"
            >
              {loading ? 'Signing In...' : 'Sign In ✨'}
            </Button>
          )}
        </form>
        )}

        {/* Register Link */}
        <div className="text-center pt-4 border-t border-purple-200">
          <p className="text-purple-600 mb-2">New to Pot Palace?</p>
          <Button
            variant="outline"
            onClick={() => {
              onClose();
              onRegister();
            }}
            className="w-full"
          >
            Create Your Account 🌱
          </Button>
          <p className="text-xs text-purple-500 mt-2">Join for exclusive deals and premium rewards!</p>
        </div>
      </div>
    </Modal>
  );
};

export default Login;