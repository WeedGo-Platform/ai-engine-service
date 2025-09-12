import React, { useState, useEffect } from 'react';
import Modal from '../ui/Modal';
import { LoginFormProps } from '../../../../core/contracts/template.contracts';
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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    
    try {
      if (loginMethod === 'password') {
        if (!email || !password) {
          setError('Please fill in all fields');
          return;
        }
        
        // Remember email if checkbox is checked
        if (rememberMe) {
          localStorage.setItem('rememberedEmail', email);
        } else {
          localStorage.removeItem('rememberedEmail');
        }
        
        await onSubmit({ email, password });
        await onSubmit({ email, password });
      } else {
        if (!contactInput || !otpCode) {
          setError('Please enter your contact and verification code');
          return;
        }
        
        await onSubmit({ email: contactInput, otp: otpCode });
        await onSubmit({ email: contactInput, otp: otpCode });
      }
    } catch (err: any) {
      setError(err.message || 'Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal isOpen onClose={onClose} title="Welcome Back">
      <div className="space-y-3">
        {/* Logo and Header */}
        <div className="text-center">
          <div className="flex justify-center mb-2">
            <div className="relative">
              <div className="text-5xl lion-glow" style={{ color: '#FCD34D' }}>
                🦁
              </div>
              <div className="absolute -bottom-1 left-1/2 transform -translate-x-1/2">
                <div className="flex space-x-1">
                  <div className="w-1.5 h-1.5 rounded-full bg-red-500"></div>
                  <div className="w-1.5 h-1.5 rounded-full bg-yellow-500"></div>
                  <div className="w-1.5 h-1.5 rounded-full bg-green-500"></div>
                </div>
              </div>
            </div>
          </div>
          <h2 className="text-xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-red-500 via-yellow-400 to-green-500">
            WELCOME BACK
          </h2>
          <p className="text-xs text-yellow-300 opacity-80 mt-1">
            One Love, One Heart, One Destiny
          </p>
        </div>

        {/* Login Method Selector */}
        <div className="grid grid-cols-3 gap-2">
          <button
            onClick={() => setLoginMethod('password')}
            className={`px-3 py-2 rounded-lg transition-all text-sm ${
              loginMethod === 'password'
                ? 'bg-gradient-to-r from-red-500 via-yellow-500 to-green-500 text-black font-bold'
                : 'bg-black/30 text-yellow-300 border border-yellow-500/30'
            }`}
          >
            Password
          </button>
          <button
            onClick={() => setLoginMethod('otp')}
            className={`px-3 py-2 rounded-lg transition-all text-sm ${
              loginMethod === 'otp'
                ? 'bg-gradient-to-r from-red-500 via-yellow-500 to-green-500 text-black font-bold'
                : 'bg-black/30 text-yellow-300 border border-yellow-500/30'
            }`}
          >
            OTP Code
          </button>
          <button
            onClick={() => setLoginMethod('voice')}
            className={`px-3 py-2 rounded-lg transition-all text-sm ${
              loginMethod === 'voice'
                ? 'bg-gradient-to-r from-red-500 via-yellow-500 to-green-500 text-black font-bold'
                : 'bg-black/30 text-yellow-300 border border-yellow-500/30'
            }`}
          >
            Voice
          </button>
        </div>

        {/* Error Display */}
        {(error || error) && (
          <div className="p-3 rounded-lg bg-red-900/50 border border-red-500/50 text-red-300 text-sm">
            {error || error}
          </div>
        )}

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
                className="rasta-vibes-voice-enrollment"
                buttonClassName="bg-gradient-to-r from-red-500 via-yellow-500 to-green-500 text-black font-bold rounded-lg hover:from-red-400 hover:via-yellow-400 hover:to-green-400 transform transition-all hover:scale-105 active:scale-95"
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
                buttonClassName="bg-gradient-to-r from-red-500 via-yellow-500 to-green-500 text-black font-bold rounded-lg hover:from-red-400 hover:via-yellow-400 hover:to-green-400 transform transition-all hover:scale-105 active:scale-95"
                waveformClassName=""
                showAgeVerification={true}
              />
            )}
          </div>
        ) : (
        <form onSubmit={handleSubmit} className="space-y-3">
          {loginMethod === 'password' ? (
            <>
              <div>
                <label className="block text-sm font-medium text-yellow-300 mb-2">
                  Email Address
                </label>
                <div className="relative">
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full px-4 py-3 bg-black/50 border-2 border-yellow-500/30 rounded-lg text-yellow-100 placeholder-yellow-700 focus:outline-none focus:border-yellow-400 focus:ring-2 focus:ring-yellow-400/20"
                    placeholder="your@email.com"
                    required
                  />
                  <span className="absolute left-3 top-3.5 text-yellow-500">
                    ✉️
                  </span>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-yellow-300 mb-2">
                  Password
                </label>
                <div className="relative">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full px-4 py-3 bg-black/50 border-2 border-yellow-500/30 rounded-lg text-yellow-100 placeholder-yellow-700 focus:outline-none focus:border-yellow-400 focus:ring-2 focus:ring-yellow-400/20 pr-12"
                    placeholder="Enter your password"
                    required
                  />
                  <span className="absolute left-3 top-3.5 text-yellow-500">
                    🔒
                  </span>
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-3.5 text-yellow-500 hover:text-yellow-400"
                  >
                    {showPassword ? '👁️' : '👁️‍🗨️'}
                  </button>
                </div>
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="rememberMe"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="w-4 h-4 rounded border-yellow-500/30 bg-black/50 text-yellow-500 focus:ring-yellow-400/20"
                />
                <label htmlFor="rememberMe" className="ml-2 text-sm text-yellow-300">
                  Remember me
                </label>
              </div>
            </>
          ) : (
            <>
              <div>
                <label className="block text-sm font-medium text-yellow-300 mb-2">
                  Email or Phone
                </label>
                <div className="relative">
                  <input
                    type="text"
                    value={contactInput}
                    onChange={(e) => setContactInput(e.target.value)}
                    className="w-full px-4 py-3 bg-black/50 border-2 border-yellow-500/30 rounded-lg text-yellow-100 placeholder-yellow-700 focus:outline-none focus:border-yellow-400 focus:ring-2 focus:ring-yellow-400/20"
                    placeholder="Enter email or phone"
                    required
                  />
                  <span className="absolute left-3 top-3.5 text-yellow-500">
                    📱
                  </span>
                </div>
                {!otpSent && (
                  <button
                    type="button"
                    onClick={handleSendOTP}
                    disabled={!contactInput || loading}
                    className="mt-2 w-full px-4 py-2 bg-gradient-to-r from-green-600 to-green-500 text-white rounded-lg hover:from-green-500 hover:to-green-400 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Send Verification Code
                  </button>
                )}
              </div>

              {otpSent && (
                <div>
                  <label className="block text-sm font-medium text-yellow-300 mb-2">
                    Verification Code
                  </label>
                  <div className="relative">
                    <input
                      type="text"
                      value={otpCode}
                      onChange={(e) => setOtpCode(e.target.value)}
                      className="w-full px-4 py-3 bg-black/50 border-2 border-yellow-500/30 rounded-lg text-yellow-100 placeholder-yellow-700 focus:outline-none focus:border-yellow-400 focus:ring-2 focus:ring-yellow-400/20"
                      placeholder="Enter 6-digit code"
                      maxLength={6}
                      required
                    />
                    <span className="absolute left-3 top-3.5 text-yellow-500">
                      🔢
                    </span>
                  </div>
                </div>
              )}
            </>
          )}

          {/* Submit Button */}
          {loginMethod !== 'voice' && (
            <button
              type="submit"
              disabled={loading || (loginMethod === 'otp' && !otpSent)}
              className="w-full px-6 py-3 bg-gradient-to-r from-red-500 via-yellow-500 to-green-500 text-black font-bold rounded-lg hover:from-red-400 hover:via-yellow-400 hover:to-green-400 disabled:opacity-50 disabled:cursor-not-allowed transform transition-all hover:scale-105 active:scale-95"
            >
              {loading ? 'Signing In...' : 'Sign In'}
            </button>
          )}
        </form>
        )}

        {/* Footer Links */}
        <div className="text-center space-y-2">
          <button
            onClick={onRegister}
            className="text-yellow-300 hover:text-yellow-200 text-sm"
          >
            Don't have an account? <span className="font-bold">Join the Movement</span>
          </button>
          <div className="text-xs text-green-300 opacity-60">
            Peace • Love • Unity • Respect
          </div>
        </div>
      </div>
    </Modal>
  );
};

export default Login;