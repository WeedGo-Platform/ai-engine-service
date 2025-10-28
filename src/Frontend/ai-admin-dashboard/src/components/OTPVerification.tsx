import React, { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';

interface OTPVerificationProps {
  identifier: string; // email or phone
  identifierType: 'email' | 'phone';
  onVerified: () => void;
  onCancel?: () => void;
  onSendOTP: (identifier: string, type: 'email' | 'phone') => Promise<{ success: boolean; message?: string; expiresIn?: number }>;
  onVerifyOTP: (identifier: string, type: 'email' | 'phone', code: string) => Promise<{ success: boolean; message?: string }>;
  onResendOTP: (identifier: string, type: 'email' | 'phone') => Promise<{ success: boolean; message?: string; expiresIn?: number }>;
}

const OTPVerification: React.FC<OTPVerificationProps> = ({
  identifier,
  identifierType,
  onVerified,
  onCancel,
  onSendOTP,
  onVerifyOTP,
  onResendOTP,
}) => {
  const { t } = useTranslation();
  const [otp, setOtp] = useState(['', '', '', '', '', '']);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [resendCountdown, setResendCountdown] = useState(0);
  const [otpSent, setOtpSent] = useState(false);
  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

  // Auto-send OTP on mount
  useEffect(() => {
    if (!otpSent && identifier) {
      handleSendOTP();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Countdown timer for resend
  useEffect(() => {
    if (resendCountdown > 0) {
      const timer = setTimeout(() => setResendCountdown(resendCountdown - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [resendCountdown]);

  const handleSendOTP = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await onSendOTP(identifier, identifierType);
      if (result.success) {
        setOtpSent(true);
        setResendCountdown(60); // 60 seconds cooldown
        // Focus first input
        setTimeout(() => inputRefs.current[0]?.focus(), 100);
      } else {
        setError(result.message || t('signup:verification.sendFailed'));
      }
    } catch (err: any) {
      setError(err.message || t('signup:verification.sendError'));
    } finally {
      setLoading(false);
    }
  };

  const handleResendOTP = async () => {
    setOtp(['', '', '', '', '', '']);
    setError(null);
    setSuccess(false);
    setLoading(true);
    try {
      const result = await onResendOTP(identifier, identifierType);
      if (result.success) {
        setOtpSent(true);
        setResendCountdown(60);
        setTimeout(() => inputRefs.current[0]?.focus(), 100);
      } else {
        setError(result.message || t('signup:verification.sendFailed'));
      }
    } catch (err: any) {
      setError(err.message || t('signup:verification.sendError'));
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOTP = async () => {
    const code = otp.join('');
    if (code.length !== 6) {
      setError(t('signup:verification.invalidCode'));
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const result = await onVerifyOTP(identifier, identifierType, code);
      if (result.success) {
        setSuccess(true);
        setError(null);
        // Call onVerified after a short delay to show success state
        setTimeout(() => {
          onVerified();
        }, 1000);
      } else {
        setError(result.message || t('signup:verification.verifyFailed'));
        // Clear OTP on failure
        setOtp(['', '', '', '', '', '']);
        inputRefs.current[0]?.focus();
      }
    } catch (err: any) {
      setError(err.message || t('signup:verification.verifyError'));
      setOtp(['', '', '', '', '', '']);
      inputRefs.current[0]?.focus();
    } finally {
      setLoading(false);
    }
  };

  const handleOtpChange = (index: number, value: string) => {
    // Only allow digits
    if (value && !/^\d$/.test(value)) return;

    const newOtp = [...otp];
    newOtp[index] = value;
    setOtp(newOtp);
    setError(null);

    // Auto-focus next input
    if (value && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }

    // Auto-verify when all 6 digits entered
    if (index === 5 && value) {
      const code = [...newOtp.slice(0, 5), value].join('');
      if (code.length === 6) {
        setTimeout(() => handleVerifyOTP(), 100);
      }
    }
  };

  const handleKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Backspace') {
      if (!otp[index] && index > 0) {
        // If current is empty, focus and clear previous
        inputRefs.current[index - 1]?.focus();
        const newOtp = [...otp];
        newOtp[index - 1] = '';
        setOtp(newOtp);
      }
    } else if (e.key === 'ArrowLeft' && index > 0) {
      inputRefs.current[index - 1]?.focus();
    } else if (e.key === 'ArrowRight' && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  const handlePaste = (e: React.ClipboardEvent) => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData('text').trim();
    const digits = pastedData.replace(/\D/g, '').slice(0, 6);
    
    if (digits.length === 6) {
      const newOtp = digits.split('');
      setOtp(newOtp);
      inputRefs.current[5]?.focus();
      // Auto-verify after paste
      setTimeout(() => handleVerifyOTP(), 100);
    }
  };

  if (!otpSent) {
    return (
      <div className="flex items-center justify-center p-4">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto mb-2"></div>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            {t('signup:verification.sending')}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="text-center">
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
          {identifierType === 'email' 
            ? t('signup:verification.emailSent', { email: identifier })
            : t('signup:verification.smsSent', { phone: identifier })
          }
        </p>
      </div>

      {/* OTP Input */}
      <div className="flex justify-center gap-2" onPaste={handlePaste}>
        {otp.map((digit, index) => (
          <input
            key={index}
            ref={(el) => (inputRefs.current[index] = el)}
            type="text"
            inputMode="numeric"
            maxLength={1}
            value={digit}
            onChange={(e) => handleOtpChange(index, e.target.value)}
            onKeyDown={(e) => handleKeyDown(index, e)}
            disabled={loading || success}
            className={`w-12 h-12 text-center text-xl font-semibold border-2 rounded-lg transition-all
              ${success 
                ? 'border-green-500 bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-300' 
                : error
                ? 'border-red-500 dark:border-red-400 bg-red-50 dark:bg-red-900/20'
                : 'border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 focus:border-primary-500 dark:focus:border-primary-400 focus:ring-2 focus:ring-primary-200 dark:focus:ring-primary-800'
              }
              ${loading ? 'opacity-50 cursor-not-allowed' : ''}
              text-gray-900 dark:text-white
            `}
            aria-label={`Digit ${index + 1}`}
          />
        ))}
      </div>

      {/* Error Message */}
      {error && (
        <div className="text-center">
          <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
        </div>
      )}

      {/* Success Message */}
      {success && (
        <div className="text-center">
          <div className="flex items-center justify-center gap-2 text-green-600 dark:text-green-400">
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            <p className="text-sm font-medium">{t('signup:verification.verified')}</p>
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="flex flex-col sm:flex-row gap-2 justify-center items-center">
        {/* Verify Button */}
        {!success && (
          <button
            onClick={handleVerifyOTP}
            disabled={loading || otp.join('').length !== 6}
            className="px-4 py-2 bg-primary-600 hover:bg-primary-700 disabled:bg-gray-300 dark:disabled:bg-gray-600 text-white rounded-lg font-medium transition-colors disabled:cursor-not-allowed"
          >
            {loading ? t('signup:verification.verifying') : t('signup:verification.verify')}
          </button>
        )}

        {/* Resend Button */}
        {!success && (
          <button
            onClick={handleResendOTP}
            disabled={loading || resendCountdown > 0}
            className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:text-primary-600 dark:hover:text-primary-400 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {resendCountdown > 0 
              ? t('signup:verification.resendIn', { seconds: resendCountdown })
              : t('signup:verification.resend')
            }
          </button>
        )}

        {/* Cancel Button */}
        {onCancel && !success && (
          <button
            onClick={onCancel}
            disabled={loading}
            className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200 disabled:opacity-50 transition-colors"
          >
            {t('signup:verification.cancel')}
          </button>
        )}
      </div>

      <div className="text-center">
        <p className="text-xs text-gray-500 dark:text-gray-400">
          {t('signup:verification.expiryInfo')}
        </p>
      </div>
    </div>
  );
};

export default OTPVerification;
