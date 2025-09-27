import { getApiUrl } from '../../config/app.config';
import React, { useState } from 'react';
import { getApiUrl } from '../../config/app.config';
import { X, Phone, Mail, ChevronRight, Loader2 } from 'lucide-react';

interface CustomerAuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (customer: any) => void;
  language: string;
}

const translations: Record<string, any> = {
  en: {
    title: 'Sign In',
    phoneLabel: 'Phone Number',
    emailLabel: 'Email Address',
    phonePlaceholder: 'Enter your phone number',
    emailPlaceholder: 'Enter your email address',
    continueBtn: 'Continue',
    orText: 'OR',
    verifyTitle: 'Enter Verification Code',
    verifyText: 'We sent a code to',
    codeLabel: 'Verification Code',
    verifyBtn: 'Verify',
    resendCode: 'Resend Code',
    signInSuccess: 'Successfully signed in!',
  },
  fr: {
    title: 'Se connecter',
    phoneLabel: 'Numéro de téléphone',
    emailLabel: 'Adresse e-mail',
    phonePlaceholder: 'Entrez votre numéro de téléphone',
    emailPlaceholder: 'Entrez votre adresse e-mail',
    continueBtn: 'Continuer',
    orText: 'OU',
    verifyTitle: 'Entrez le code de vérification',
    verifyText: 'Nous avons envoyé un code à',
    codeLabel: 'Code de vérification',
    verifyBtn: 'Vérifier',
    resendCode: 'Renvoyer le code',
    signInSuccess: 'Connexion réussie!',
  },
  zh: {
    title: '登录',
    phoneLabel: '手机号码',
    emailLabel: '电子邮箱',
    phonePlaceholder: '请输入您的手机号码',
    emailPlaceholder: '请输入您的电子邮箱',
    continueBtn: '继续',
    orText: '或',
    verifyTitle: '输入验证码',
    verifyText: '我们已发送验证码至',
    codeLabel: '验证码',
    verifyBtn: '验证',
    resendCode: '重新发送验证码',
    signInSuccess: '登录成功！',
  },
};

export default function CustomerAuthModal({
  isOpen,
  onClose,
  onSuccess,
  language,
}: CustomerAuthModalProps) {
  const [authMethod, setAuthMethod] = useState<'phone' | 'email'>('phone');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [email, setEmail] = useState('');
  const [verificationCode, setVerificationCode] = useState('');
  const [showVerification, setShowVerification] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const t = translations[language] || translations['en'];

  if (!isOpen) return null;

  const handleSendCode = async () => {
    setIsLoading(true);
    setError('');

    try {
      const identifier = authMethod === 'phone' ? phoneNumber : email;

      const response = await fetch(getApiUrl('api/kiosk/auth/send-code', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          identifier,
          method: authMethod,
        }),
      });

      if (response.ok) {
        setShowVerification(true);
      } else {
        const data = await response.json();
        setError(data.error || 'Failed to send verification code');
      }
    } catch (err) {
      setError('Failed to send verification code');
    } finally {
      setIsLoading(false);
    }
  };

  const handleVerify = async () => {
    setIsLoading(true);
    setError('');

    try {
      const identifier = authMethod === 'phone' ? phoneNumber : email;

      const response = await fetch(getApiUrl('api/kiosk/auth/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          identifier,
          code: verificationCode,
          method: authMethod,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        onSuccess(data.customer);
      } else {
        const data = await response.json();
        setError(data.error || 'Invalid verification code');
      }
    } catch (err) {
      setError('Verification failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleResendCode = () => {
    setVerificationCode('');
    handleSendCode();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg m-4">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <h3 className="text-2xl font-semibold">
            {showVerification ? t.verifyTitle : t.title}
          </h3>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {!showVerification ? (
            <>
              {/* Auth Method Tabs */}
              <div className="flex space-x-2 mb-6">
                <button
                  onClick={() => setAuthMethod('phone')}
                  className={`flex-1 p-3 rounded-lg font-medium transition-all ${
                    authMethod === 'phone'
                      ? 'bg-primary-100 text-primary-600 border-2 border-primary-500'
                      : 'bg-gray-100 text-gray-600 border-2 border-transparent'
                  }`}
                >
                  <Phone className="inline-block w-5 h-5 mr-2" />
                  {t.phoneLabel}
                </button>
                <button
                  onClick={() => setAuthMethod('email')}
                  className={`flex-1 p-3 rounded-lg font-medium transition-all ${
                    authMethod === 'email'
                      ? 'bg-primary-100 text-primary-600 border-2 border-primary-500'
                      : 'bg-gray-100 text-gray-600 border-2 border-transparent'
                  }`}
                >
                  <Mail className="inline-block w-5 h-5 mr-2" />
                  {t.emailLabel}
                </button>
              </div>

              {/* Input Field */}
              <div className="mb-6">
                {authMethod === 'phone' ? (
                  <input
                    type="tel"
                    value={phoneNumber}
                    onChange={(e) => setPhoneNumber(e.target.value)}
                    placeholder={t.phonePlaceholder}
                    className="w-full px-4 py-3 text-lg border-2 rounded-lg focus:outline-none focus:border-primary-500"
                    autoFocus
                  />
                ) : (
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder={t.emailPlaceholder}
                    className="w-full px-4 py-3 text-lg border-2 rounded-lg focus:outline-none focus:border-primary-500"
                    autoFocus
                  />
                )}
              </div>

              {/* Error Message */}
              {error && (
                <div className="mb-4 p-3 bg-red-50 text-red-600 rounded-lg">
                  {error}
                </div>
              )}

              {/* Continue Button */}
              <button
                onClick={handleSendCode}
                disabled={
                  isLoading ||
                  (authMethod === 'phone' ? !phoneNumber : !email)
                }
                className="w-full p-4 bg-primary-600 text-white rounded-lg font-semibold text-lg hover:bg-primary-700 transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center justify-center"
              >
                {isLoading ? (
                  <Loader2 className="w-6 h-6 animate-spin" />
                ) : (
                  <>
                    {t.continueBtn}
                    <ChevronRight className="ml-2 w-5 h-5" />
                  </>
                )}
              </button>
            </>
          ) : (
            <>
              {/* Verification Screen */}
              <div className="text-center mb-6">
                <p className="text-gray-600">
                  {t.verifyText}{' '}
                  <span className="font-semibold">
                    {authMethod === 'phone' ? phoneNumber : email}
                  </span>
                </p>
              </div>

              {/* Verification Code Input */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t.codeLabel}
                </label>
                <input
                  type="text"
                  value={verificationCode}
                  onChange={(e) => setVerificationCode(e.target.value)}
                  placeholder="000000"
                  className="w-full px-4 py-3 text-2xl text-center tracking-widest border-2 rounded-lg focus:outline-none focus:border-primary-500"
                  maxLength={6}
                  autoFocus
                />
              </div>

              {/* Error Message */}
              {error && (
                <div className="mb-4 p-3 bg-red-50 text-red-600 rounded-lg">
                  {error}
                </div>
              )}

              {/* Action Buttons */}
              <div className="space-y-3">
                <button
                  onClick={handleVerify}
                  disabled={isLoading || verificationCode.length < 6}
                  className="w-full p-4 bg-primary-600 text-white rounded-lg font-semibold text-lg hover:bg-primary-700 transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center justify-center"
                >
                  {isLoading ? (
                    <Loader2 className="w-6 h-6 animate-spin" />
                  ) : (
                    t.verifyBtn
                  )}
                </button>

                <button
                  onClick={handleResendCode}
                  className="w-full p-3 text-primary-600 hover:bg-primary-50 rounded-lg font-medium transition-colors"
                >
                  {t.resendCode}
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}