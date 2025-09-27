import React, { useState, useEffect } from 'react';
import { getApiUrl } from '../../config/app.config';
import { X, Scan, Loader2, CheckCircle2 } from 'lucide-react';
import QRCode from 'qrcode';

interface QRLoginModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (customer: any) => void;
  language: string;
}

const translations: Record<string, any> = {
  en: {
    title: 'Scan QR Code to Sign In',
    instructions: 'Use your phone to scan this QR code',
    waitingText: 'Waiting for scan...',
    successText: 'Successfully signed in!',
    orText: 'Or enter code manually',
    codeLabel: 'Enter Code',
    submitBtn: 'Submit',
  },
  fr: {
    title: 'Scanner le code QR pour vous connecter',
    instructions: 'Utilisez votre téléphone pour scanner ce code QR',
    waitingText: 'En attente du scan...',
    successText: 'Connexion réussie!',
    orText: 'Ou entrez le code manuellement',
    codeLabel: 'Entrez le code',
    submitBtn: 'Soumettre',
  },
  zh: {
    title: '扫描二维码登录',
    instructions: '使用手机扫描此二维码',
    waitingText: '等待扫描中...',
    successText: '登录成功！',
    orText: '或手动输入代码',
    codeLabel: '输入代码',
    submitBtn: '提交',
  },
};

export default function QRLoginModal({
  isOpen,
  onClose,
  onSuccess,
  language,
}: QRLoginModalProps) {
  const [qrCodeUrl, setQrCodeUrl] = useState('');
  const [sessionCode, setSessionCode] = useState('');
  const [manualCode, setManualCode] = useState('');
  const [isPolling, setIsPolling] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [error, setError] = useState('');

  const t = translations[language] || translations['en'];

  useEffect(() => {
    if (isOpen) {
      generateQRCode();
    }
    return () => {
      setIsPolling(false);
    };
  }, [isOpen]);

  const generateQRCode = async () => {
    try {
      // Generate QR session on backend
      const response = await fetch(getApiUrl('/api/kiosk/auth/qr-generate'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });

      if (!response.ok) {
        throw new Error('Failed to generate QR session');
      }

      const data = await response.json();
      const code = data.session_code;
      setSessionCode(code);

      // Generate QR code URL for mobile app to scan
      const loginUrl = `${window.location.origin}/kiosk-login?code=${code}&store=${encodeURIComponent(
        localStorage.getItem('currentStoreId') || ''
      )}`;

      // Create QR code image
      const qrUrl = await QRCode.toDataURL(loginUrl, {
        width: 300,
        margin: 2,
        color: {
          dark: '#000000',
          light: '#FFFFFF',
        },
      });

      setQrCodeUrl(qrUrl);

      // Start polling for login
      startPolling(code);
    } catch (err) {
      console.error('Failed to generate QR code:', err);
      setError('Failed to generate QR code');
    }
  };

  const startPolling = (code: string) => {
    setIsPolling(true);
    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(getApiUrl(`/api/kiosk/auth/check-qr/${code}`));

        if (response.ok) {
          const data = await response.json();
          if (data.authenticated) {
            clearInterval(pollInterval);
            setIsPolling(false);
            setIsSuccess(true);
            setTimeout(() => {
              onSuccess(data.customer);
            }, 1500);
          }
        }
      } catch (err) {
        console.error('Polling error:', err);
      }
    }, 2000); // Poll every 2 seconds

    // Stop polling after 5 minutes
    setTimeout(() => {
      clearInterval(pollInterval);
      setIsPolling(false);
    }, 300000);
  };

  const handleManualSubmit = async () => {
    setError('');

    try {
      const response = await fetch(getApiUrl('/api/kiosk/auth/manual-code'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: manualCode }),
      });

      if (response.ok) {
        const data = await response.json();
        setIsSuccess(true);
        setTimeout(() => {
          onSuccess(data.customer);
        }, 1500);
      } else {
        setError('Invalid code');
      }
    } catch (err) {
      setError('Failed to verify code');
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg m-4">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <h3 className="text-2xl font-semibold flex items-center">
            <Scan className="w-8 h-8 mr-3 text-primary-600" />
            {t.title}
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
          {isSuccess ? (
            <div className="text-center py-8">
              <CheckCircle className="w-20 h-20 text-green-500 mx-auto mb-4" />
              <p className="text-xl font-semibold text-gray-800">{t.successText}</p>
            </div>
          ) : (
            <>
              {/* QR Code Display */}
              <div className="text-center mb-6">
                <p className="text-gray-600 mb-4">{t.instructions}</p>

                {qrCodeUrl ? (
                  <div className="inline-block p-4 bg-white rounded-lg shadow-lg">
                    <img src={qrCodeUrl} alt="QR Code" className="w-64 h-64" />
                  </div>
                ) : (
                  <div className="inline-flex items-center justify-center w-64 h-64 bg-gray-100 rounded-lg">
                    <Loader2 className="w-12 h-12 animate-spin text-gray-400" />
                  </div>
                )}

                {isPolling && (
                  <div className="mt-4 flex items-center justify-center text-gray-600">
                    <Loader2 className="w-5 h-5 animate-spin mr-2" />
                    {t.waitingText}
                  </div>
                )}
              </div>

              {/* Divider */}
              <div className="flex items-center my-6">
                <div className="flex-1 border-t border-gray-300"></div>
                <span className="px-4 text-gray-500">{t.orText}</span>
                <div className="flex-1 border-t border-gray-300"></div>
              </div>

              {/* Manual Code Entry */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t.codeLabel}
                </label>
                <div className="flex space-x-2">
                  <input
                    type="text"
                    value={manualCode}
                    onChange={(e) => setManualCode(e.target.value.toUpperCase())}
                    placeholder="XXXX-XXXX"
                    className="flex-1 px-4 py-3 border-2 rounded-lg focus:outline-none focus:border-primary-500 text-lg"
                    maxLength={9}
                  />
                  <button
                    onClick={handleManualSubmit}
                    disabled={manualCode.length < 4}
                    className="px-6 py-3 bg-primary-600 text-white rounded-lg font-semibold hover:bg-primary-700 transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed"
                  >
                    {t.submitBtn}
                  </button>
                </div>

                {error && (
                  <div className="mt-2 text-sm text-red-600">{error}</div>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}