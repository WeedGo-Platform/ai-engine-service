import React, { useState } from 'react';
import {
  Globe,
  Key,
  AlertCircle,
  Check,
  Eye,
  EyeOff,
  RefreshCw,
  Shield,
  Info
} from 'lucide-react';

interface OnlinePaymentSettingsProps {
  storeId: string;
  initialSettings?: any;
  onSave?: (settings: any) => Promise<void>;
}

interface OnlinePaymentConfig {
  enabled: boolean;
  provider: string;
  accessToken: string;
  merchantId?: string;
  environment: 'sandbox' | 'production';
  webhookUrl?: string;
  supportedCardTypes: string[];
  require3DS?: boolean;
  platformFeePercentage?: number;
  platformFeeFixed?: number;
}

const SUPPORTED_PROVIDERS = [
  {
    id: 'clover',
    name: 'Clover',
    description: 'Clover payment processing for Canadian merchants',
    requiredFields: ['accessToken', 'merchantId'],
    features: ['Credit/Debit Cards', 'Tap to Pay', 'Recurring Payments', 'Refunds'],
    icon: '🍀'
  },
  {
    id: 'moneris',
    name: 'Moneris',
    description: 'Leading Canadian payment processor',
    requiredFields: ['storeId', 'apiToken'],
    features: ['Credit/Debit Cards', 'Interac Online', 'Pre-authorization'],
    icon: '💳'
  }
];

const OnlinePaymentSettings: React.FC<OnlinePaymentSettingsProps> = ({
  storeId,
  initialSettings = {},
  onSave
}) => {
  const [settings, setSettings] = useState<OnlinePaymentConfig>({
    enabled: false,
    provider: 'clover',
    accessToken: '',
    merchantId: '',
    environment: 'sandbox',
    webhookUrl: '',
    supportedCardTypes: ['visa', 'mastercard', 'amex'],
    require3DS: false,
    platformFeePercentage: 2.0,
    platformFeeFixed: 0.0,
    ...initialSettings
  });

  const [showToken, setShowToken] = useState(false);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);

  const selectedProvider = SUPPORTED_PROVIDERS.find(p => p.id === settings.provider);

  const handleProviderChange = (providerId: string) => {
    setSettings({
      ...settings,
      provider: providerId,
      // Reset provider-specific fields when switching
      accessToken: '',
      merchantId: '',
      webhookUrl: ''
    });
    setTestResult(null);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      if (onSave) {
        await onSave(settings);
      }
    } catch (error) {
      console.error('Failed to save online payment settings:', error);
    } finally {
      setSaving(false);
    }
  };

  const testConnection = async () => {
    setTesting(true);
    setTestResult(null);

    try {
      // Call backend API to test the payment provider connection
      const response = await fetch(`/api/stores/${storeId}/payment/test`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          provider: settings.provider,
          config: {
            accessToken: settings.accessToken,
            merchantId: settings.merchantId,
            environment: settings.environment
          }
        })
      });

      const result = await response.json();

      if (response.ok) {
        setTestResult({
          success: true,
          message: 'Connection successful! Payment provider is configured correctly.'
        });
      } else {
        setTestResult({
          success: false,
          message: result.error || 'Connection failed. Please check your credentials.'
        });
      }
    } catch (error) {
      setTestResult({
        success: false,
        message: 'Failed to test connection. Please check your network.'
      });
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Enable/Disable Toggle */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Globe className="w-6 h-6 text-primary-600" />
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Online Payments</h3>
              <p className="text-sm text-gray-500">Accept payments through your ecommerce website</p>
            </div>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={settings.enabled}
              onChange={(e) => setSettings({ ...settings, enabled: e.target.checked })}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
          </label>
        </div>
      </div>

      {settings.enabled && (
        <>
          {/* Provider Selection */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Payment Provider</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {SUPPORTED_PROVIDERS.map((provider) => (
                <div
                  key={provider.id}
                  onClick={() => handleProviderChange(provider.id)}
                  className={`relative rounded-lg border-2 p-4 cursor-pointer transition-all ${
                    settings.provider === provider.id
                      ? 'border-primary-500 bg-primary-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-start space-x-3">
                    <span className="text-2xl">{provider.icon}</span>
                    <div className="flex-1">
                      <h4 className="font-semibold text-gray-900">{provider.name}</h4>
                      <p className="text-sm text-gray-500 mt-1">{provider.description}</p>
                      <div className="mt-3 flex flex-wrap gap-2">
                        {provider.features.map((feature, idx) => (
                          <span
                            key={idx}
                            className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-700"
                          >
                            {feature}
                          </span>
                        ))}
                      </div>
                    </div>
                    {settings.provider === provider.id && (
                      <Check className="w-5 h-5 text-primary-600" />
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Provider Configuration */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">
                {selectedProvider?.name} Configuration
              </h3>
              <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                settings.environment === 'production'
                  ? 'bg-green-100 text-green-800'
                  : 'bg-yellow-100 text-yellow-800'
              }`}>
                {settings.environment === 'production' ? 'Production' : 'Sandbox'}
              </span>
            </div>

            <div className="space-y-4">
              {/* Environment Toggle */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Environment
                </label>
                <select
                  value={settings.environment}
                  onChange={(e) => setSettings({ ...settings, environment: e.target.value as 'sandbox' | 'production' })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                >
                  <option value="sandbox">Sandbox (Testing)</option>
                  <option value="production">Production (Live)</option>
                </select>
              </div>

              {/* Access Token */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  <Key className="w-4 h-4 inline mr-1" />
                  Access Token
                  <span className="text-red-500 ml-1">*</span>
                </label>
                <div className="mt-1 relative">
                  <input
                    type={showToken ? "text" : "password"}
                    value={settings.accessToken}
                    onChange={(e) => setSettings({ ...settings, accessToken: e.target.value })}
                    placeholder="Enter your provider access token"
                    className="block w-full pr-10 rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                  />
                  <button
                    type="button"
                    onClick={() => setShowToken(!showToken)}
                    className="absolute inset-y-0 right-0 pr-3 flex items-center"
                  >
                    {showToken ? (
                      <EyeOff className="h-4 w-4 text-gray-400" />
                    ) : (
                      <Eye className="h-4 w-4 text-gray-400" />
                    )}
                  </button>
                </div>
                <p className="mt-1 text-xs text-gray-500">
                  This token will be encrypted and stored securely
                </p>
              </div>

              {/* Merchant ID (Clover specific) */}
              {settings.provider === 'clover' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Merchant ID
                    <span className="text-red-500 ml-1">*</span>
                  </label>
                  <input
                    type="text"
                    value={settings.merchantId || ''}
                    onChange={(e) => setSettings({ ...settings, merchantId: e.target.value })}
                    placeholder="Your Clover Merchant ID"
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                  />
                </div>
              )}

              {/* Webhook URL (Display only) */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Webhook URL
                </label>
                <div className="mt-1 flex rounded-md shadow-sm">
                  <input
                    type="text"
                    value={`https://api.weedgo.ca/webhooks/${settings.provider}/${storeId}`}
                    readOnly
                    className="block w-full rounded-md border-gray-300 bg-gray-50 shadow-sm sm:text-sm"
                  />
                  <button
                    type="button"
                    onClick={() => {
                      navigator.clipboard.writeText(`https://api.weedgo.ca/webhooks/${settings.provider}/${storeId}`);
                    }}
                    className="ml-3 inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                  >
                    Copy
                  </button>
                </div>
                <p className="mt-1 text-xs text-gray-500">
                  Configure this URL in your {selectedProvider?.name} dashboard for webhook notifications
                </p>
              </div>
            </div>
          </div>

          {/* Advanced Settings */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Advanced Settings</h3>

            <div className="space-y-4">
              {/* 3D Secure */}
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Shield className="w-5 h-5 text-gray-400" />
                  <div>
                    <label className="text-sm font-medium text-gray-700">
                      Require 3D Secure
                    </label>
                    <p className="text-xs text-gray-500">
                      Additional authentication for card payments
                    </p>
                  </div>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={settings.require3DS || false}
                    onChange={(e) => setSettings({ ...settings, require3DS: e.target.checked })}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                </label>
              </div>

              {/* Platform Fees */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Platform Fee (%)
                  </label>
                  <input
                    type="number"
                    value={settings.platformFeePercentage || 0}
                    onChange={(e) => setSettings({ ...settings, platformFeePercentage: parseFloat(e.target.value) })}
                    step="0.01"
                    min="0"
                    max="10"
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Fixed Fee ($)
                  </label>
                  <input
                    type="number"
                    value={settings.platformFeeFixed || 0}
                    onChange={(e) => setSettings({ ...settings, platformFeeFixed: parseFloat(e.target.value) })}
                    step="0.01"
                    min="0"
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                  />
                </div>
              </div>

              {/* Supported Card Types */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Accepted Card Types
                </label>
                <div className="space-y-2">
                  {['visa', 'mastercard', 'amex', 'discover'].map((cardType) => (
                    <label key={cardType} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={settings.supportedCardTypes?.includes(cardType) || false}
                        onChange={(e) => {
                          const types = settings.supportedCardTypes || [];
                          if (e.target.checked) {
                            setSettings({ ...settings, supportedCardTypes: [...types, cardType] });
                          } else {
                            setSettings({ ...settings, supportedCardTypes: types.filter(t => t !== cardType) });
                          }
                        }}
                        className="rounded border-gray-300 text-primary-600 shadow-sm focus:border-primary-300 focus:ring focus:ring-primary-200 focus:ring-opacity-50"
                      />
                      <span className="ml-2 text-sm text-gray-700 capitalize">{cardType}</span>
                    </label>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Test Connection */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Test Connection</h3>
                <p className="text-sm text-gray-500 mt-1">
                  Verify your payment provider settings are correct
                </p>
              </div>
              <button
                onClick={testConnection}
                disabled={!settings.accessToken || testing}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:bg-gray-300 disabled:cursor-not-allowed"
              >
                {testing ? (
                  <>
                    <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                    Testing...
                  </>
                ) : (
                  <>
                    <RefreshCw className="w-4 h-4 mr-2" />
                    Test Connection
                  </>
                )}
              </button>
            </div>

            {testResult && (
              <div className={`mt-4 p-4 rounded-lg ${
                testResult.success
                  ? 'bg-green-50 border border-green-200'
                  : 'bg-red-50 border border-red-200'
              }`}>
                <div className="flex items-start">
                  {testResult.success ? (
                    <Check className="w-5 h-5 text-green-600 mt-0.5 mr-2" />
                  ) : (
                    <AlertCircle className="w-5 h-5 text-red-600 mt-0.5 mr-2" />
                  )}
                  <p className={`text-sm ${
                    testResult.success ? 'text-green-800' : 'text-red-800'
                  }`}>
                    {testResult.message}
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Info Box */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex">
              <Info className="w-5 h-5 text-blue-600 mt-0.5 mr-2 flex-shrink-0" />
              <div className="text-sm text-blue-800">
                <p className="font-semibold mb-1">Important Notes:</p>
                <ul className="list-disc ml-5 space-y-1">
                  <li>Ensure your {selectedProvider?.name} account is properly configured for Canadian payments</li>
                  <li>Test your integration in sandbox mode before switching to production</li>
                  <li>Platform fees will be automatically calculated on each transaction</li>
                  <li>All payment data is encrypted and stored securely</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Save Button */}
          <div className="flex justify-end space-x-3">
            <button
              onClick={handleSave}
              disabled={saving || !settings.accessToken}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:bg-gray-300 disabled:cursor-not-allowed"
            >
              {saving ? 'Saving...' : 'Save Settings'}
            </button>
          </div>
        </>
      )}
    </div>
  );
};

export default OnlinePaymentSettings;