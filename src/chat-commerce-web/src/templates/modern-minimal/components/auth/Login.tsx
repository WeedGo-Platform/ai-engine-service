import React, { useState, useEffect } from 'react';
import { useAuth } from '../../../../contexts/AuthContext';
import Button from '../ui/Button';
import Input from '../ui/Input';
import Modal from '../ui/Modal';
import Card from '../ui/Card';
import Badge from '../ui/Badge';
import { LoginFormProps } from '../../../../core/contracts/template.contracts';
import { detectContactType, getContactPlaceholder } from '../../../../utils/validation';

const Login: React.FC<LoginFormProps> = ({ onClose, onSubmit, onRegister }) => {
  const { login, loginWithOTP, sendOTP, error: authError, clearError, isLoading: authLoading } = useAuth();
  const [loginMethod, setLoginMethod] = useState<'password' | 'otp'>('password');
  const [email, setEmail] = useState('');
  const [contactInput, setContactInput] = useState('');
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
    if (!contactInput) return;
    
    try {
      await sendOTP(contactInput);
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
        await loginWithOTP(contactInput, otpCode);
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
    <Modal isOpen onClose={onClose} title="Sign In">
      <div className="space-y-8">
        {/* Header */}
        <div className="text-center">
          <div className="w-12 h-12 bg-black text-white rounded-none flex items-center justify-center mx-auto mb-6 font-mono text-xl">
            →
          </div>
          <h2 className="text-2xl font-light text-gray-900 mb-2">Welcome Back</h2>
          <p className="text-gray-600 text-sm">Access your account</p>
        </div>

        {/* Login Method Toggle */}
        <div className="border border-gray-300">
          <div className="grid grid-cols-2">
            <button
              type="button"
              onClick={() => setLoginMethod('password')}
              className={`py-3 px-4 font-medium transition-colors border-r border-gray-300 ${
                loginMethod === 'password'
                  ? 'bg-black text-white'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
              }`}
            >
              PASSWORD
            </button>
            <button
              type="button"
              onClick={() => setLoginMethod('otp')}
              className={`py-3 px-4 font-medium transition-colors ${
                loginMethod === 'otp'
                  ? 'bg-black text-white'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
              }`}
            >
              PHONE/EMAIL
            </button>
          </div>
        </div>

        <form onSubmit={handleLogin} className="space-y-6">
          {/* Email Field - for password login */}
          {loginMethod === 'password' && (
            <Input
              type="email"
              label="EMAIL"
              value={email}
              placeholder="your.email@domain.com"
              required
              onChange={setEmail}
            />
          )}
          
          {/* Contact Input Field - for OTP login */}
          {loginMethod === 'otp' && (
            <div className="space-y-2">
              <Input
                type="text"
                label="EMAIL OR PHONE"
                value={contactInput}
                placeholder="email@domain.com or (555) 123-4567"
                required
                onChange={setContactInput}
              />
              {contactInput && (
                <div className="text-xs px-1 font-mono">
                  {(() => {
                    const contactInfo = detectContactType(contactInput);
                    if (contactInfo.type === 'email') {
                      return <span className="text-gray-600">EMAIL DETECTED</span>;
                    } else if (contactInfo.type === 'phone') {
                      return <span className="text-gray-600">PHONE DETECTED: {contactInfo.formatted}</span>;
                    } else if (contactInput.length > 0) {
                      return <span className="text-red-600">INVALID FORMAT</span>;
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
                    label="PASSWORD"
                    value={password}
                    placeholder="Enter password"
                    required
                    onChange={setPassword}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-8 text-gray-400 hover:text-gray-600 transition-colors font-mono text-sm"
                  >
                    {showPassword ? 'HIDE' : 'SHOW'}
                  </button>
                </div>
                
                <div className="flex items-center justify-between">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={rememberMe}
                      onChange={(e) => setRememberMe(e.target.checked)}
                      className="w-4 h-4 text-black border-gray-300 rounded-none focus:ring-black"
                    />
                    <span className="text-sm text-gray-600 font-mono">REMEMBER</span>
                  </label>
                  <button
                    type="button"
                    className="text-sm text-black hover:text-gray-600 font-mono"
                    onClick={() => alert('Password reset not implemented')}
                  >
                    FORGOT?
                  </button>
                </div>
              </div>
            </>
          ) : (
            /* OTP Login Fields */
            <>
              {!otpSent ? (
                <div className="space-y-4">
                  <Card variant="outlined" className="p-4">
                    <div className="text-sm text-gray-900 font-mono">
                      <p className="font-medium mb-2">ONE-TIME PASSWORD</p>
                      <p className="text-xs text-gray-600">We will send a verification code to your email or phone.</p>
                    </div>
                  </Card>
                  
                  <Button
                    type="button"
                    onClick={handleSendOTP}
                    disabled={authLoading || !contactInput}
                    loading={authLoading}
                    variant="secondary"
                    className="w-full"
                  >
                    {authLoading ? 'SENDING...' : 'SEND CODE'}
                  </Button>
                </div>
              ) : (
                <div className="space-y-4">
                  <Input
                    type="text"
                    label="VERIFICATION CODE"
                    value={otpCode}
                    placeholder="000000"
                    onChange={(value) => setOtpCode(value.replace(/\D/g, '').slice(0, 6))}
                    className="font-mono text-center tracking-widest"
                  />
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-gray-500 font-mono">NO CODE RECEIVED?</span>
                    <button
                      type="button"
                      onClick={handleSendOTP}
                      disabled={authLoading}
                      className="text-black hover:text-gray-600 font-mono"
                    >
                      RESEND
                    </button>
                  </div>
                </div>
              )}
            </>
          )}

          {/* Error Message */}
          {(localError || authError) && (
            <Card variant="outlined" className="p-4 border-red-600">
              <div className="text-red-600 text-sm font-mono">
                ERROR: {localError || authError}
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
              {authLoading ? 'AUTHENTICATING...' : 'SIGN IN'}
            </Button>
          )}
          
          {/* Security Info */}
          <div className="flex items-center justify-center gap-8 text-xs font-mono">
            <Badge variant="secondary" size="sm">SSL</Badge>
            <Badge variant="secondary" size="sm">SECURE</Badge>
          </div>
        </form>

        {/* Register Link */}
        <div className="text-center pt-6 border-t border-gray-200">
          <p className="text-gray-600 mb-4 font-mono text-xs">NEW USER?</p>
          <Button
            variant="outline"
            onClick={() => {
              onClose();
              onRegister();
            }}
            className="w-full"
          >
            CREATE ACCOUNT
          </Button>
        </div>
      </div>
    </Modal>
  );
};

export default Login;