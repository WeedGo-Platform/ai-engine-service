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
      setError('TRANSMISSION FAILED');
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
      setError(err.message || 'ACCESS DENIED');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal isOpen onClose={onClose} title="SYSTEM ACCESS">
      <div className="space-y-4">
        {/* Header with Matrix-like effect */}
        <div className="text-center relative">
          <div className="w-12 h-12 bg-gray-900 border-2 border-cyan-400 text-cyan-400 flex items-center justify-center mx-auto mb-3 font-mono text-lg relative">
            <span className="animate-pulse">{'<>'}</span>
            {/* Glowing effect */}
            <div className="absolute inset-0 border-2 border-cyan-400 animate-pulse opacity-50"></div>
          </div>
          <h2 className="text-xl font-bold text-cyan-100 mb-1 font-mono uppercase tracking-wider">
            INITIATE CONNECTION
          </h2>
          <p className="text-cyan-400 text-xs font-mono">{'>>> '} NEURAL LINK PROTOCOL</p>
        </div>

        {/* Authentication Method Toggle */}
        <div className="grid grid-cols-3 border-2 border-cyan-800">
          <button
            type="button"
            onClick={() => setLoginMethod('password')}
            className={`py-4 px-4 font-mono uppercase font-bold transition-all duration-300 border-r-2 border-cyan-800 ${
              loginMethod === 'password'
                ? 'bg-cyan-900 text-cyan-100 shadow-lg shadow-cyan-400/20'
                : 'text-cyan-400 hover:text-cyan-100 hover:bg-gray-800/50'
            }`}
          >
            <div className="flex items-center justify-center gap-2">
              <span className="text-lg">⚡</span>
              <span className="hidden sm:inline">PASSWORD</span>
              <span className="sm:hidden">PASS</span>
            </div>
          </button>
          <button
            type="button"
            onClick={() => setLoginMethod('otp')}
            className={`py-4 px-4 font-mono uppercase font-bold transition-all duration-300 border-r-2 border-cyan-800 ${
              loginMethod === 'otp'
                ? 'bg-cyan-900 text-cyan-100 shadow-lg shadow-cyan-400/20'
                : 'text-cyan-400 hover:text-cyan-100 hover:bg-gray-800/50'
            }`}
          >
            <div className="flex items-center justify-center gap-2">
              <span className="text-lg">📡</span>
              <span className="hidden sm:inline">NEURAL</span>
              <span className="sm:hidden">CODE</span>
            </div>
          </button>
          <button
            type="button"
            onClick={() => setLoginMethod('voice')}
            className={`py-4 px-4 font-mono uppercase font-bold transition-all duration-300 ${
              loginMethod === 'voice'
                ? 'bg-cyan-900 text-cyan-100 shadow-lg shadow-cyan-400/20'
                : 'text-cyan-400 hover:text-cyan-100 hover:bg-gray-800/50'
            }`}
          >
            <div className="flex items-center justify-center gap-2">
              <span className="text-lg">🎤</span>
              <span className="hidden sm:inline">BIOMETRIC</span>
              <span className="sm:hidden">VOICE</span>
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
                className="dark-tech-voice-enrollment"
                buttonClassName="bg-cyan-900 text-cyan-100 hover:bg-cyan-800 border-2 border-cyan-400 font-mono uppercase tracking-wider shadow-lg shadow-cyan-400/20 transition-all duration-300"
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
                buttonClassName="bg-cyan-900 text-cyan-100 hover:bg-cyan-800 border-2 border-cyan-400 font-mono uppercase tracking-wider shadow-lg shadow-cyan-400/20 transition-all duration-300"
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
              label="USER IDENTITY"
              value={email}
              placeholder="neural.interface@matrix.net"
              required
              onChange={setEmail}
            />
          )}
          
          {/* Contact Input Field - for OTP login */}
          {loginMethod === 'otp' && (
            <div className="space-y-2">
              <Input
                type="text"
                label="NEURAL INTERFACE"
                value={contactInput}
                placeholder="neural.link@matrix.net or +1-555-HACK"
                required
                onChange={setContactInput}
              />
              {contactInput && (
                <div className="text-xs px-2 font-mono">
                  {(() => {
                    const contactInfo = detectContactType(contactInput);
                    if (contactInfo.type === 'email') {
                      return <span className="text-cyan-400">📧 EMAIL PROTOCOL DETECTED</span>;
                    } else if (contactInfo.type === 'phone') {
                      return <span className="text-cyan-400">📡 NEURAL LINK DETECTED: {contactInfo.formatted}</span>;
                    } else if (contactInput.length > 0) {
                      return <span className="text-red-400">⚠ INVALID INTERFACE FORMAT</span>;
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
                    label="ACCESS CODE"
                    value={password}
                    placeholder="Enter security passphrase"
                    required
                    onChange={setPassword}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-9 text-cyan-400 hover:text-cyan-100 transition-colors font-mono text-sm"
                  >
                    {showPassword ? '👁️‍🗨️' : '👁️'}
                  </button>
                </div>
                
                <div className="flex items-center justify-between">
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={rememberMe}
                      onChange={(e) => setRememberMe(e.target.checked)}
                      className="w-4 h-4 text-cyan-400 bg-gray-800 border-2 border-cyan-600 focus:ring-cyan-400 focus:ring-2"
                    />
                    <span className="text-sm text-cyan-300 font-mono uppercase">CACHE IDENTITY</span>
                  </label>
                  <button
                    type="button"
                    className="text-sm text-magenta-400 hover:text-magenta-300 font-mono uppercase"
                    onClick={() => alert('RECOVERY PROTOCOL NOT AVAILABLE')}
                  >
                    LOST ACCESS?
                  </button>
                </div>
              </div>
            </>
          ) : (
            /* OTP Login Fields */
            <>
              {!otpSent ? (
                <div className="space-y-6">
                  <Card variant="filled" className="p-6 border-cyan-800">
                    <div className="flex items-start gap-4">
                      <span className="text-2xl animate-pulse">📡</span>
                      <div className="text-sm text-cyan-100 font-mono">
                        <p className="font-bold mb-2 uppercase">QUANTUM AUTHENTICATION</p>
                        <p className="text-xs text-cyan-400">
                          INITIATING SECURE TRANSMISSION TO YOUR EMAIL OR NEURAL LINK...
                        </p>
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
                    {loading ? 'TRANSMITTING...' : 'SEND QUANTUM KEY ⚡'}
                  </Button>
                </div>
              ) : (
                <div className="space-y-4">
                  <Input
                    type="text"
                    label="QUANTUM KEY"
                    value={otpCode}
                    placeholder="000000"
                    onChange={(value) => setOtpCode(value.replace(/\D/g, '').slice(0, 6))}
                    className="font-mono text-center tracking-widest text-lg"
                  />
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-cyan-500 font-mono uppercase">NO SIGNAL RECEIVED?</span>
                    <button
                      type="button"
                      onClick={handleSendOTP}
                      disabled={loading}
                      className="text-magenta-400 hover:text-magenta-300 font-mono uppercase font-bold"
                    >
                      {loading ? 'TRANSMITTING...' : 'RETRANSMIT 🔄'}
                    </button>
                  </div>
                </div>
              )}
            </>
          )}

          {/* Error Message */}
          {error && (
            <Card variant="filled" className="p-4 border-red-500 bg-red-900/20">
              <div className="flex items-center gap-3 text-red-400 text-sm font-mono">
                <span className="animate-pulse text-lg">⚠</span>
                <span className="uppercase">SYSTEM ERROR: {error}</span>
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
              {loading ? 'ESTABLISHING LINK...' : 'JACK IN ⚡'}
            </Button>
          )}
        </form>
        )}

        {/* Register Link */}
        <div className="text-center pt-4 border-t-2 border-cyan-800/50">
          <p className="text-cyan-400 mb-4 font-mono text-sm uppercase">NEW TO THE MATRIX?</p>
          <Button
            variant="outline"
            onClick={() => {
              onClose();
              onRegister();
            }}
            className="w-full"
          >
            CREATE NEURAL PROFILE ⚡
          </Button>
          <p className="text-xs text-cyan-500 mt-3 font-mono">
            {'>>> '} GAIN ACCESS TO THE DIGITAL UNDERGROUND
          </p>
        </div>
      </div>
    </Modal>
  );
};

export default Login;