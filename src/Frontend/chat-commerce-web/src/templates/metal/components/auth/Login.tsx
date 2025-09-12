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
        {/* Header with metal/industrial styling */}
        <div className="text-center">
          <div className="w-16 h-16 bg-gradient-to-br from-red-600 to-red-900 text-white border-4 border-black flex items-center justify-center mx-auto mb-3 text-2xl font-black shadow-lg shadow-red-900/50">
            ⚡
          </div>
          <h2 className="text-2xl font-black text-white mb-1 uppercase tracking-widest">WELCOME BACK</h2>
          <p className="text-gray-400 text-xs uppercase tracking-wider">ENTER THE METAL ZONE</p>
        </div>

        {/* Login Method Toggle with metal styling */}
        <div className="border-4 border-black bg-gradient-to-r from-gray-900 to-black">
          <div className="grid grid-cols-3">
            <button
              type="button"
              onClick={() => setLoginMethod('password')}
              className={`py-3 px-3 font-black uppercase tracking-widest transition-all border-r-4 border-black text-sm ${
                loginMethod === 'password'
                  ? 'bg-gradient-to-br from-red-600 to-red-800 text-white shadow-inner'
                  : 'text-gray-400 hover:text-white hover:bg-red-950/30'
              }`}
            >
              PASSWORD
            </button>
            <button
              type="button"
              onClick={() => setLoginMethod('otp')}
              className={`py-3 px-3 font-black uppercase tracking-widest transition-all border-r-4 border-black text-sm ${
                loginMethod === 'otp'
                  ? 'bg-gradient-to-br from-red-600 to-red-800 text-white shadow-inner'
                  : 'text-gray-400 hover:text-white hover:bg-red-950/30'
              }`}
            >
              PHONE/EMAIL
            </button>
            <button
              type="button"
              onClick={() => setLoginMethod('voice')}
              className={`py-3 px-3 font-black uppercase tracking-widest transition-all text-sm ${
                loginMethod === 'voice'
                  ? 'bg-gradient-to-br from-red-600 to-red-800 text-white shadow-inner'
                  : 'text-gray-400 hover:text-white hover:bg-red-950/30'
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
                className="metal-voice-enrollment"
                buttonClassName="bg-gradient-to-br from-red-600 to-red-900 text-white font-black uppercase tracking-widest px-4 py-2 border-4 border-black shadow-lg shadow-red-900/50 hover:from-red-500 hover:to-red-800 transition-all"
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
                className=""
                buttonClassName="bg-gradient-to-br from-red-600 to-red-900 text-white font-black uppercase tracking-widest px-4 py-2 border-4 border-black shadow-lg shadow-red-900/50 hover:from-red-500 hover:to-red-800 transition-all"
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
                <div className="text-xs px-1 font-black uppercase tracking-wider">
                  {(() => {
                    const contactInfo = detectContactType(contactInput);
                    if (contactInfo.type === 'email') {
                      return <span className="text-green-500">▶ EMAIL DETECTED</span>;
                    } else if (contactInfo.type === 'phone') {
                      return <span className="text-green-500">▶ PHONE: {contactInfo.formatted}</span>;
                    } else if (contactInput.length > 0) {
                      return <span className="text-red-500">✖ INVALID FORMAT</span>;
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
                    className="absolute right-3 top-8 text-gray-400 hover:text-red-500 transition-colors font-black text-xs uppercase tracking-wider"
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
                      className="w-4 h-4 text-red-600 bg-black border-gray-600 rounded-none focus:ring-red-500"
                    />
                    <span className="text-xs text-gray-400 font-black uppercase tracking-wider">REMEMBER</span>
                  </label>
                  <button
                    type="button"
                    className="text-xs text-red-500 hover:text-red-400 font-black uppercase tracking-wider"
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
                  <Card variant="outlined" className="p-4 bg-black/50 border-2 border-red-800">
                    <div className="text-sm text-white font-black">
                      <p className="uppercase mb-2 tracking-wider">⚡ ONE-TIME PASSWORD</p>
                      <p className="text-xs text-gray-400 uppercase">We'll send a verification code.</p>
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
                    className="font-mono text-center tracking-[0.5em] text-xl"
                  />
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-gray-400 font-black uppercase tracking-wider">NO CODE?</span>
                    <button
                      type="button"
                      onClick={handleSendOTP}
                      disabled={loading}
                      className="text-red-500 hover:text-red-400 font-black uppercase tracking-wider"
                    >
                      RESEND
                    </button>
                  </div>
                </div>
              )}
            </>
          )}

          {/* Error Message */}
          {(error || error) && (
            <Card variant="outlined" className="p-4 border-2 border-red-600 bg-red-950/20">
              <div className="text-red-500 text-sm font-black uppercase tracking-wider">
                ✖ ERROR: {error || error}
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
        <div className="text-center pt-4 border-t-4 border-gray-800">
          <p className="text-gray-400 mb-4 font-black text-xs uppercase tracking-wider">NEW METALHEAD?</p>
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