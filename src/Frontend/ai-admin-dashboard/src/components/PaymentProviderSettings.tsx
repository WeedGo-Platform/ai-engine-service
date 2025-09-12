import React, { useState, useEffect } from 'react';
import {
  CreditCard,
  Settings,
  Check,
  X,
  AlertCircle,
  Eye,
  EyeOff,
  Save,
  TestTube,
  Shield
} from 'lucide-react';

interface PaymentProvider {
  enabled: boolean;
  account_id?: string;
  publishable_key?: string;
  secret_key?: string;
  location_id?: string;
  access_token?: string;
  store_id?: string;
  api_token?: string;
  client_id?: string;
  client_secret?: string;
  webhook_endpoint?: string;
  payment_methods?: string[];
  test_mode?: boolean;
}

interface PaymentProviderSettings {
  stripe?: PaymentProvider;
  square?: PaymentProvider;
  moneris?: PaymentProvider;
  paypal?: PaymentProvider;
  interac?: PaymentProvider;
  default_provider?: string;
  fallback_provider?: string;
  currency?: string;
  auto_capture?: boolean;
  receipt_email?: boolean;
}

interface PaymentProviderSettingsProps {
  tenantId: string;
  settings: PaymentProviderSettings;
  onSave: (settings: PaymentProviderSettings) => Promise<void>;
  onValidate?: (provider: string) => Promise<void>;
}

const PROVIDERS = [
  { id: 'stripe', name: 'Stripe', icon: '💳' },
  { id: 'square', name: 'Square', icon: '⬜' },
  { id: 'moneris', name: 'Moneris', icon: '🍁' },
  { id: 'paypal', name: 'PayPal', icon: '💰' },
  { id: 'interac', name: 'Interac', icon: '🏦' }
];

const PAYMENT_METHODS = [
  { id: 'credit_card', name: 'Credit Card' },
  { id: 'debit_card', name: 'Debit Card' },
  { id: 'apple_pay', name: 'Apple Pay' },
  { id: 'google_pay', name: 'Google Pay' },
  { id: 'tap', name: 'Tap to Pay' },
  { id: 'interac', name: 'Interac' },
  { id: 'paypal', name: 'PayPal' }
];

const PaymentProviderSettingsComponent: React.FC<PaymentProviderSettingsProps> = ({
  tenantId,
  settings: initialSettings,
  onSave,
  onValidate
}) => {
  const [settings, setSettings] = useState<PaymentProviderSettings>(initialSettings || {});
  const [activeProvider, setActiveProvider] = useState<string | null>(null);
  const [showSecrets, setShowSecrets] = useState<{ [key: string]: boolean }>({});
  const [saving, setSaving] = useState(false);
  const [validating, setValidating] = useState<string | null>(null);
  const [errors, setErrors] = useState<{ [key: string]: string }>({});

  const handleProviderToggle = (providerId: string) => {
    setSettings(prev => ({
      ...prev,
      [providerId]: {
        ...prev[providerId as keyof PaymentProviderSettings],
        enabled: !prev[providerId as keyof PaymentProviderSettings]?.enabled
      }
    }));
  };

  const handleProviderFieldChange = (providerId: string, field: string, value: any) => {
    setSettings(prev => ({
      ...prev,
      [providerId]: {
        ...prev[providerId as keyof PaymentProviderSettings],
        [field]: value
      }
    }));
  };

  const handlePaymentMethodToggle = (providerId: string, method: string) => {
    const provider = settings[providerId as keyof PaymentProviderSettings] as PaymentProvider;
    const methods = provider?.payment_methods || [];
    const updated = methods.includes(method)
      ? methods.filter(m => m !== method)
      : [...methods, method];
    
    handleProviderFieldChange(providerId, 'payment_methods', updated);
  };

  const handleSave = async () => {
    setSaving(true);
    setErrors({});
    
    try {
      await onSave(settings);
    } catch (error: any) {
      setErrors({ save: error.message || 'Failed to save settings' });
    } finally {
      setSaving(false);
    }
  };

  const handleValidate = async (providerId: string) => {
    if (!onValidate) return;
    
    setValidating(providerId);
    setErrors({});
    
    try {
      await onValidate(providerId);
    } catch (error: any) {
      setErrors({ [providerId]: error.message || 'Validation failed' });
    } finally {
      setValidating(null);
    }
  };

  const getProviderFields = (providerId: string) => {
    switch (providerId) {
      case 'stripe':
        return [
          { id: 'account_id', label: 'Account ID', type: 'text' },
          { id: 'publishable_key', label: 'Publishable Key', type: 'text' },
          { id: 'secret_key', label: 'Secret Key', type: 'password' },
          { id: 'webhook_endpoint', label: 'Webhook Endpoint', type: 'text' }
        ];
      case 'square':
        return [
          { id: 'location_id', label: 'Location ID', type: 'text' },
          { id: 'access_token', label: 'Access Token', type: 'password' }
        ];
      case 'moneris':
        return [
          { id: 'store_id', label: 'Store ID', type: 'text' },
          { id: 'api_token', label: 'API Token', type: 'password' }
        ];
      case 'paypal':
        return [
          { id: 'client_id', label: 'Client ID', type: 'text' },
          { id: 'client_secret', label: 'Client Secret', type: 'password' }
        ];
      case 'interac':
        return [
          { id: 'merchant_id', label: 'Merchant ID', type: 'text' },
          { id: 'api_key', label: 'API Key', type: 'password' }
        ];
      default:
        return [];
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold flex items-center gap-2">
          <CreditCard className="w-6 h-6" />
          Payment Provider Settings
        </h2>
        <button
          onClick={handleSave}
          disabled={saving}
          className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 flex items-center gap-2"
        >
          <Save className="w-4 h-4" />
          {saving ? 'Saving...' : 'Save Changes'}
        </button>
      </div>

      {errors.save && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2">
          <AlertCircle className="w-5 h-5 text-red-500" />
          <span className="text-red-700">{errors.save}</span>
        </div>
      )}

      {/* Provider Tabs */}
      <div className="flex gap-2 mb-6 border-b">
        {PROVIDERS.map(provider => (
          <button
            key={provider.id}
            onClick={() => setActiveProvider(provider.id)}
            className={`px-4 py-2 font-medium transition-colors ${
              activeProvider === provider.id
                ? 'border-b-2 border-blue-500 text-blue-600'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <span className="mr-2">{provider.icon}</span>
            {provider.name}
          </button>
        ))}
      </div>

      {/* Provider Configuration */}
      {activeProvider && (
        <div className="space-y-6">
          {/* Enable/Disable Toggle */}
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center gap-3">
              <Shield className="w-5 h-5 text-gray-600" />
              <span className="font-medium">
                Enable {PROVIDERS.find(p => p.id === activeProvider)?.name}
              </span>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={settings[activeProvider as keyof PaymentProviderSettings]?.enabled || false}
                onChange={() => handleProviderToggle(activeProvider)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
            </label>
          </div>

          {settings[activeProvider as keyof PaymentProviderSettings]?.enabled && (
            <>
              {/* Provider Fields */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {getProviderFields(activeProvider).map(field => (
                  <div key={field.id}>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      {field.label}
                    </label>
                    <div className="relative">
                      <input
                        type={
                          field.type === 'password' && !showSecrets[field.id]
                            ? 'password'
                            : 'text'
                        }
                        value={settings[activeProvider as keyof PaymentProviderSettings]?.[field.id] || ''}
                        onChange={(e) => handleProviderFieldChange(activeProvider, field.id, e.target.value)}
                        className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder={`Enter ${field.label.toLowerCase()}`}
                      />
                      {field.type === 'password' && (
                        <button
                          type="button"
                          onClick={() => setShowSecrets(prev => ({ ...prev, [field.id]: !prev[field.id] }))}
                          className="absolute right-2 top-2.5 text-gray-500 hover:text-gray-700"
                        >
                          {showSecrets[field.id] ? (
                            <EyeOff className="w-4 h-4" />
                          ) : (
                            <Eye className="w-4 h-4" />
                          )}
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>

              {/* Payment Methods */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Supported Payment Methods
                </label>
                <div className="flex flex-wrap gap-2">
                  {PAYMENT_METHODS.map(method => {
                    const provider = settings[activeProvider as keyof PaymentProviderSettings] as PaymentProvider;
                    const isSelected = provider?.payment_methods?.includes(method.id) || false;
                    
                    return (
                      <button
                        key={method.id}
                        onClick={() => handlePaymentMethodToggle(activeProvider, method.id)}
                        className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                          isSelected
                            ? 'bg-blue-100 text-blue-700'
                            : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                        }`}
                      >
                        {method.name}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Test Mode */}
              <div className="flex items-center gap-3">
                <input
                  type="checkbox"
                  id="test-mode"
                  checked={settings[activeProvider as keyof PaymentProviderSettings]?.test_mode || false}
                  onChange={(e) => handleProviderFieldChange(activeProvider, 'test_mode', e.target.checked)}
                  className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                />
                <label htmlFor="test-mode" className="flex items-center gap-2 text-sm font-medium text-gray-700">
                  <TestTube className="w-4 h-4" />
                  Test Mode
                </label>
              </div>

              {/* Validate Configuration */}
              {onValidate && (
                <div className="flex items-center gap-4">
                  <button
                    onClick={() => handleValidate(activeProvider)}
                    disabled={validating === activeProvider}
                    className="bg-green-500 text-white px-4 py-2 rounded-lg hover:bg-green-600 flex items-center gap-2"
                  >
                    <Check className="w-4 h-4" />
                    {validating === activeProvider ? 'Validating...' : 'Validate Configuration'}
                  </button>
                  {errors[activeProvider] && (
                    <span className="text-red-600 text-sm">{errors[activeProvider]}</span>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      )}

      {/* General Settings */}
      <div className="mt-8 pt-6 border-t">
        <h3 className="text-lg font-semibold mb-4">General Settings</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Default Provider
            </label>
            <select
              value={settings.default_provider || ''}
              onChange={(e) => setSettings(prev => ({ ...prev, default_provider: e.target.value }))}
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select provider</option>
              {PROVIDERS.filter(p => settings[p.id as keyof PaymentProviderSettings]?.enabled).map(provider => (
                <option key={provider.id} value={provider.id}>
                  {provider.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Fallback Provider
            </label>
            <select
              value={settings.fallback_provider || ''}
              onChange={(e) => setSettings(prev => ({ ...prev, fallback_provider: e.target.value }))}
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select provider</option>
              {PROVIDERS.filter(p => 
                settings[p.id as keyof PaymentProviderSettings]?.enabled && 
                p.id !== settings.default_provider
              ).map(provider => (
                <option key={provider.id} value={provider.id}>
                  {provider.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Currency
            </label>
            <select
              value={settings.currency || 'CAD'}
              onChange={(e) => setSettings(prev => ({ ...prev, currency: e.target.value }))}
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="CAD">CAD - Canadian Dollar</option>
              <option value="USD">USD - US Dollar</option>
            </select>
          </div>

          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              id="auto-capture"
              checked={settings.auto_capture !== false}
              onChange={(e) => setSettings(prev => ({ ...prev, auto_capture: e.target.checked }))}
              className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
            />
            <label htmlFor="auto-capture" className="text-sm font-medium text-gray-700">
              Auto-capture payments
            </label>
          </div>

          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              id="receipt-email"
              checked={settings.receipt_email !== false}
              onChange={(e) => setSettings(prev => ({ ...prev, receipt_email: e.target.checked }))}
              className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
            />
            <label htmlFor="receipt-email" className="text-sm font-medium text-gray-700">
              Email receipts to customers
            </label>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PaymentProviderSettingsComponent;