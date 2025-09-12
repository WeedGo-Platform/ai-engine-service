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

  const handleSendOTP = async () => {
    if (!contactInput) return;
    setError('');
    setLoading(true);
    
    try {
      // In a real implementation, this would call an API to send OTP
      // For now, we'll just simulate it
      await new Promise(resolve => setTimeout(resolve, 1000));
      setOtpSent(true);
    } catch (err: any) {
      setError(err.message || 'Failed to send verification code');
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

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
      
      // Call the parent onSubmit to handle any additional logic
      if (onSubmit) {
        await onSubmit({ email, password: loginMethod === 'password' ? password : undefined, otp: loginMethod === 'otp' ? otpCode : undefined });
      }
      
      onClose();
    } catch (err: any) {
      setError(err.message || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal isOpen onClose={onClose} title="Sign In">
      <div className="space-y-4">
        {/* Header with vintage styling */}
        <div className="text-center">
          <div className="w-16 h-16 bg-gradient-to-br from-amber-700 to-amber-900 text-amber-100 rounded-lg shadow-lg flex items-center justify-center mx-auto mb-3 text-2xl font-serif">
            ✉
          </div>
          <h2 className="text-2xl font-serif text-amber-900 mb-1">Welcome Back</h2>
          <p className="text-amber-700 text-sm italic">Access your vintage collection</p>
        </div>

        {/* Login Method Toggle with vintage styling */}
        <div className="border-2 border-amber-700 rounded-lg overflow-hidden">
          <div className="grid grid-cols-3">
            <button
              type="button"
              onClick={() => setLoginMethod('password')}
              className={`py-3 px-3 font-serif font-medium transition-all border-r-2 border-amber-700 text-sm ${
                loginMethod === 'password'
                  ? 'bg-gradient-to-br from-amber-700 to-amber-800 text-amber-50 shadow-inner'
                  : 'text-amber-800 hover:text-amber-900 hover:bg-amber-50'
              }`}
            >
              PASSWORD
            </button>
            <button
              type="button"
              onClick={() => setLoginMethod('otp')}
              className={`py-3 px-3 font-serif font-medium transition-all border-r-2 border-amber-700 text-sm ${
                loginMethod === 'otp'
                  ? 'bg-gradient-to-br from-amber-700 to-amber-800 text-amber-50 shadow-inner'
                  : 'text-amber-800 hover:text-amber-900 hover:bg-amber-50'
              }`}
            >
              PHONE/EMAIL
            </button>
            <button
              type="button"
              onClick={() => setLoginMethod('voice')}
              className={`py-3 px-3 font-serif font-medium transition-all text-sm ${
                loginMethod === 'voice'
                  ? 'bg-gradient-to-br from-amber-700 to-amber-800 text-amber-50 shadow-inner'
                  : 'text-amber-800 hover:text-amber-900 hover:bg-amber-50'
              }`}
            >
              VOICE
            </button>
          </div>
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
                className="vintage-voice-enrollment"
                buttonClassName="bg-gradient-to-br from-amber-700 to-amber-800 text-amber-50 font-serif px-4 py-2 rounded-lg shadow-lg hover:from-amber-600 hover:to-amber-700 transition-all duration-200 border-2 border-amber-600"
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
                buttonClassName="bg-gradient-to-br from-amber-700 to-amber-800 text-amber-50 font-serif px-4 py-2 rounded-lg shadow-lg hover:from-amber-600 hover:to-amber-700 transition-all duration-200 border-2 border-amber-600"
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
              label="EMAIL ADDRESS"
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
                <div className="text-xs px-1 font-serif italic">
                  {(() => {
                    const contactInfo = detectContactType(contactInput);
                    if (contactInfo.type === 'email') {
                      return <span className="text-amber-700">Email detected</span>;
                    } else if (contactInfo.type === 'phone') {
                      return <span className="text-amber-700">Phone detected: {contactInfo.formatted}</span>;
                    } else if (contactInput.length > 0) {
                      return <span className="text-red-700">Invalid format</span>;
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
                    placeholder="Enter your password"
                    required
                    onChange={setPassword}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-9 text-amber-600 hover:text-amber-800 transition-colors text-sm font-serif"
                  >
                    {showPassword ? 'Hide' : 'Show'}
                  </button>
                </div>
                
                <div className="flex items-center justify-between">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={rememberMe}
                      onChange={(e) => setRememberMe(e.target.checked)}
                      className="w-4 h-4 text-amber-700 border-amber-400 rounded focus:ring-amber-500"
                    />
                    <span className="text-sm text-amber-700 font-serif">Remember me</span>
                  </label>
                  <button
                    type="button"
                    className="text-sm text-amber-700 hover:text-amber-900 font-serif italic underline"
                    onClick={() => alert('Password reset not implemented')}
                  >
                    Forgot password?
                  </button>
                </div>
              </div>
            </>
          ) : (
            /* OTP Login Fields */
            <>
              {!otpSent ? (
                <div className="space-y-4">
                  <Card variant="outlined" className="p-4 bg-amber-50 border-amber-300">
                    <div className="text-sm text-amber-900 font-serif">
                      <p className="font-bold mb-2">One-Time Password</p>
                      <p className="text-xs text-amber-700 italic">We'll send a verification code to your email or phone.</p>
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
                    {loading ? 'Sending...' : 'Send Code'}
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
                    <span className="text-amber-600 font-serif italic">No code received?</span>
                    <button
                      type="button"
                      onClick={handleSendOTP}
                      disabled={loading}
                      className="text-amber-700 hover:text-amber-900 font-serif underline"
                    >
                      Resend
                    </button>
                  </div>
                </div>
              )}
            </>
          )}

          {/* Error Message */}
          {(error || error) && (
            <Card variant="outlined" className="p-4 border-red-700 bg-red-50">
              <div className="text-red-700 text-sm font-serif">
                Error: {error || error}
              </div>
            </Card>
          )}

          {/* Submit Button */}
          {(loginMethod === 'password' || (loginMethod === 'otp' && otpSent)) && loginMethod !== 'voice' && (
            <Button
              type="submit"
              disabled={loading}
              loading={loading}
              className="w-full"
              size="lg"
            >
              {loading ? 'Authenticating...' : 'Sign In'}
            </Button>
          )}
        </form>
        )}

        {/* Register Link */}
        <div className="text-center pt-4 border-t-2 border-amber-200">
          <p className="text-amber-700 mb-4 font-serif text-sm italic">New to our collection?</p>
          <Button
            variant="outline"
            onClick={() => {
              onClose();
              onRegister();
            }}
            className="w-full"
          >
            Create Account
          </Button>
        </div>
      </div>
    </Modal>
  );
};

export default Login;