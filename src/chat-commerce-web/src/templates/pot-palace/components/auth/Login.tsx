import React, { useState, useEffect } from 'react';
import { useAuth } from '../../../../contexts/AuthContext';
import Button from '../ui/Button';
import Input from '../ui/Input';
import Modal from '../ui/Modal';
import Card from '../ui/Card';
import Badge from '../ui/Badge';
import { LoginFormProps } from '../../../../core/contracts/template.contracts';

const Login: React.FC<LoginFormProps> = ({ onClose, onSubmit, onRegister }) => {
  const { login, loginWithOTP, sendOTP, error: authError, clearError, isLoading: authLoading } = useAuth();
  const [loginMethod, setLoginMethod] = useState<'password' | 'otp'>('password');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [otpCode, setOtpCode] = useState('');
  const [localError, setLocalError] = useState('');
  const [otpSent, setOtpSent] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);

  // Clear errors when switching login methods
  useEffect(() => {
    setLocalError('');
    clearError();
    setOtpSent(false);
    setOtpCode('');
  }, [loginMethod, clearError]);

  // Load remembered email
  useEffect(() => {
    const rememberedEmail = localStorage.getItem('rememberedEmail');
    if (rememberedEmail) {
      setEmail(rememberedEmail);
      setRememberMe(true);
    }
  }, []);

  const handleSendOTP = async () => {
    if (!email) return;
    
    try {
      await sendOTP(email);
      setOtpSent(true);
    } catch (err: any) {
      setLocalError(err.message || 'Failed to send verification code');
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError('');

    try {
      if (loginMethod === 'password') {
        await login({ email, password });
      } else {
        await loginWithOTP(email, otpCode);
      }
      
      if (rememberMe) {
        localStorage.setItem('rememberedEmail', email);
      } else {
        localStorage.removeItem('rememberedEmail');
      }
      
      // Call the parent onSubmit to handle any additional logic
      if (onSubmit) {
        await onSubmit({ email, password: loginMethod === 'password' ? password : undefined, otp: loginMethod === 'otp' ? otpCode : undefined });
      }
      
      onClose();
    } catch (err: any) {
      setLocalError(err.message || 'Authentication failed');
    }
  };

  return (
    <Modal isOpen onClose={onClose} title="Welcome Back to Pot Palace">
      <div className="space-y-6">
        {/* Logo and Header */}
        <div className="text-center">
          <div className="flex justify-center mb-4">
            <div className="relative">
              <div className="absolute inset-0 bg-gradient-to-r from-purple-400 to-pink-400 rounded-full blur-xl opacity-30 animate-pulse"></div>
              <div className="relative z-10 w-20 h-20 bg-gradient-to-br from-purple-100 to-pink-100 rounded-full flex items-center justify-center">
                <span className="text-3xl">🌿</span>
              </div>
            </div>
          </div>
          <h2 className="text-2xl font-bold text-purple-800 mb-2">Welcome Back!</h2>
          <p className="text-purple-600">Sign in to your premium cannabis experience</p>
        </div>

        {/* Login Method Toggle */}
        <div className="flex bg-purple-100 rounded-xl p-1">
          <button
            type="button"
            onClick={() => setLoginMethod('password')}
            className={`flex-1 py-2.5 px-4 rounded-lg font-semibold transition-all duration-300 ${
              loginMethod === 'password'
                ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-lg'
                : 'text-purple-600 hover:text-purple-800'
            }`}
          >
            <div className="flex items-center justify-center gap-2">
              <span>🔐</span>
              Password
            </div>
          </button>
          <button
            type="button"
            onClick={() => setLoginMethod('otp')}
            className={`flex-1 py-2.5 px-4 rounded-lg font-semibold transition-all duration-300 ${
              loginMethod === 'otp'
                ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-lg'
                : 'text-purple-600 hover:text-purple-800'
            }`}
          >
            <div className="flex items-center justify-center gap-2">
              <span>📱</span>
              One-Time Code
            </div>
          </button>
        </div>

        <form onSubmit={handleLogin} className="space-y-6">
          {/* Email Field */}
          <Input
            type="email"
            label="Email Address"
            value={email}
            placeholder="Enter your email address"
            required
            onChange={setEmail}
          />

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
                        <p className="text-xs">We'll send a magical verification code to your email for passwordless sign-in.</p>
                      </div>
                    </div>
                  </Card>
                  
                  <Button
                    type="button"
                    onClick={handleSendOTP}
                    disabled={authLoading || !email}
                    loading={authLoading}
                    variant="secondary"
                    className="w-full"
                  >
                    {authLoading ? 'Sending Magic Code...' : 'Send Verification Code 🌿'}
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
                    <span className="text-xs text-purple-600">Didn't receive the code?</span>
                    <button
                      type="button"
                      onClick={handleSendOTP}
                      disabled={authLoading}
                      className="text-xs text-pink-600 hover:text-pink-700 font-semibold"
                    >
                      {authLoading ? 'Sending...' : 'Resend Code 🔄'}
                    </button>
                  </div>
                </div>
              )}
            </>
          )}

          {/* Error Message */}
          {(localError || authError) && (
            <Card variant="filled" className="p-4 bg-gradient-to-r from-red-100 to-red-50 border-red-300">
              <div className="flex items-center gap-2 text-red-700 text-sm">
                <span>⚠️</span>
                {localError || authError}
              </div>
            </Card>
          )}

          {/* Submit Button */}
          {(loginMethod === 'password' || (loginMethod === 'otp' && otpSent)) && (
            <Button
              type="submit"
              disabled={authLoading}
              loading={authLoading}
              className="w-full"
              size="lg"
            >
              {authLoading ? 'Signing In...' : 'Sign In ✨'}
            </Button>
          )}
          
          {/* Security Badge */}
          <div className="flex items-center justify-center gap-4 text-xs">
            <Badge variant="secondary" size="sm">🔒 SSL Encrypted</Badge>
            <Badge variant="secondary" size="sm">🌿 Cannabis Verified</Badge>
          </div>
        </form>

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