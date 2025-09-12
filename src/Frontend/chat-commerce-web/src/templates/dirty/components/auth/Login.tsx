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
        {/* Header with dirty/grunge styling */}
        <div className="text-center">
          <div className="w-14 h-14 bg-gradient-to-br from-zinc-800 to-black text-gray-400 border-2 border-zinc-700 flex items-center justify-center mx-auto mb-3 text-xl font-bold shadow-inner">
            ☠
          </div>
          <h2 className="text-xl font-bold text-gray-200 mb-1 uppercase tracking-wider">Welcome Back</h2>
          <p className="text-gray-500 text-xs uppercase tracking-wide">Enter the darkness</p>
        </div>

        {/* Login Method Toggle with dirty styling */}
        <div className="border-2 border-zinc-700 bg-zinc-900">
          <div className="grid grid-cols-3">
            <button
              type="button"
              onClick={() => setLoginMethod('password')}
              className={`py-3 px-3 font-bold uppercase tracking-wide transition-all border-r-2 border-zinc-700 text-sm ${
                loginMethod === 'password'
                  ? 'bg-gradient-to-br from-zinc-800 to-black text-gray-100 shadow-inner'
                  : 'text-gray-500 hover:text-gray-300 hover:bg-zinc-800/50'
              }`}
            >
              PASSWORD
            </button>
            <button
              type="button"
              onClick={() => setLoginMethod('otp')}
              className={`py-3 px-3 font-bold uppercase tracking-wide transition-all border-r-2 border-zinc-700 text-sm ${
                loginMethod === 'otp'
                  ? 'bg-gradient-to-br from-zinc-800 to-black text-gray-100 shadow-inner'
                  : 'text-gray-500 hover:text-gray-300 hover:bg-zinc-800/50'
              }`}
            >
              PHONE/EMAIL
            </button>
            <button
              type="button"
              onClick={() => setLoginMethod('voice')}
              className={`py-3 px-3 font-bold uppercase tracking-wide transition-all text-sm ${
                loginMethod === 'voice'
                  ? 'bg-gradient-to-br from-zinc-800 to-black text-gray-100 shadow-inner'
                  : 'text-gray-500 hover:text-gray-300 hover:bg-zinc-800/50'
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
                className="dirty-voice-enrollment"
                buttonClassName="w-full py-3 px-4 bg-gradient-to-br from-zinc-800 to-black text-gray-100 font-bold uppercase tracking-wide border-2 border-zinc-700 hover:border-zinc-600 transition-all duration-300 shadow-lg disabled:opacity-50"
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
                onRegister={onRegister}
                onClose={onClose}
                className=""
                buttonClassName="w-full py-3 px-4 bg-gradient-to-br from-zinc-800 to-black text-gray-100 font-bold uppercase tracking-wide border-2 border-zinc-700 hover:border-zinc-600 transition-all duration-300 shadow-lg disabled:opacity-50"
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
                <div className="text-xs px-1 font-mono uppercase">
                  {(() => {
                    const contactInfo = detectContactType(contactInput);
                    if (contactInfo.type === 'email') {
                      return <span className="text-gray-500">✓ EMAIL DETECTED</span>;
                    } else if (contactInfo.type === 'phone') {
                      return <span className="text-gray-500">✓ PHONE: {contactInfo.formatted}</span>;
                    } else if (contactInput.length > 0) {
                      return <span className="text-red-600">✗ INVALID FORMAT</span>;
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
                    className="absolute right-3 top-8 text-gray-500 hover:text-gray-300 transition-colors font-bold text-xs uppercase"
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
                      className="w-4 h-4 text-zinc-700 bg-zinc-800 border-zinc-600 rounded-none focus:ring-zinc-500"
                    />
                    <span className="text-xs text-gray-500 font-bold uppercase">Remember</span>
                  </label>
                  <button
                    type="button"
                    className="text-xs text-gray-500 hover:text-gray-300 font-bold uppercase"
                    onClick={() => alert('Password reset not implemented')}
                  >
                    Forgot?
                  </button>
                </div>
              </div>
            </>
          ) : (
            /* OTP Login Fields */
            <>
              {!otpSent ? (
                <div className="space-y-4">
                  <Card variant="outlined" className="p-4 bg-zinc-900/50 border-zinc-700">
                    <div className="text-sm text-gray-300 font-bold">
                      <p className="uppercase mb-2">One-Time Password</p>
                      <p className="text-xs text-gray-500">We'll send a verification code to your contact.</p>
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
                    {loading ? 'SENDING...' : 'SEND CODE'}
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
                    <span className="text-gray-500 font-bold uppercase">No code?</span>
                    <button
                      type="button"
                      onClick={handleSendOTP}
                      disabled={loading}
                      className="text-gray-500 hover:text-gray-300 font-bold uppercase"
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
            <Card variant="outlined" className="p-4 border-red-800 bg-red-950/30">
              <div className="text-red-500 text-sm font-bold uppercase">
                ✗ Error: {error || error}
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
              {loading ? 'AUTHENTICATING...' : 'SIGN IN'}
            </Button>
          )}
        </form>
        )}

        {/* Register Link */}
        <div className="text-center pt-4 border-t border-zinc-700">
          <p className="text-gray-500 mb-4 font-bold text-xs uppercase">New user?</p>
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