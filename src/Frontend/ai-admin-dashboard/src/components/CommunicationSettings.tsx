import React, { useState } from 'react';
import { MessageSquare, Mail, Eye, EyeOff, Check, X } from 'lucide-react';

export interface CommunicationSettings {
  sms: {
    provider: string;
    enabled: boolean;
    twilio?: {
      accountSid: string;
      authToken: string;
      phoneNumber: string;
      verifyServiceSid?: string;
    };
  };
  email: {
    provider: string;
    enabled: boolean;
    sendgrid?: {
      apiKey: string;
      fromEmail: string;
      fromName: string;
      replyToEmail?: string;
    };
  };
}

interface CommunicationSettingsProps {
  tenantId: string;
  settings: CommunicationSettings;
  onSave: (settings: CommunicationSettings) => Promise<void>;
  onValidate: (channel: 'sms' | 'email') => Promise<void>;
}

const CommunicationSettingsComponent: React.FC<CommunicationSettingsProps> = ({
  tenantId,
  settings,
  onSave,
  onValidate,
}) => {
  const [formData, setFormData] = useState<CommunicationSettings>(settings);
  const [showSecrets, setShowSecrets] = useState<{ [key: string]: boolean }>({});
  const [saving, setSaving] = useState(false);
  const [validating, setValidating] = useState<string | null>(null);

  const handleChange = (channel: 'sms' | 'email', provider: string, field: string, value: string | boolean) => {
    setFormData(prev => ({
      ...prev,
      [channel]: {
        ...prev[channel],
        [provider]: {
          ...prev[channel][provider as keyof typeof prev[typeof channel]],
          [field]: value,
        },
      },
    }));
  };

  const handleProviderChange = (channel: 'sms' | 'email', provider: string) => {
    setFormData(prev => ({
      ...prev,
      [channel]: {
        ...prev[channel],
        provider,
      },
    }));
  };

  const handleToggleEnabled = (channel: 'sms' | 'email') => {
    setFormData(prev => ({
      ...prev,
      [channel]: {
        ...prev[channel],
        enabled: !prev[channel].enabled,
      },
    }));
  };

  const toggleSecretVisibility = (key: string) => {
    setShowSecrets(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await onSave(formData);
    } finally {
      setSaving(false);
    }
  };

  const handleValidate = async (channel: 'sms' | 'email') => {
    setValidating(channel);
    try {
      await onValidate(channel);
    } finally {
      setValidating(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* SMS Settings */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 transition-colors duration-200">
        <div className="mb-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <MessageSquare className="w-5 h-5 text-gray-600 dark:text-gray-300" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">SMS Configuration</h3>
          </div>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={formData.sms.enabled}
              onChange={() => handleToggleEnabled('sms')}
              className="rounded border-gray-300 text-accent-600 focus:ring-accent-500"
            />
            <span className="text-sm text-gray-600 dark:text-gray-300">Enable SMS</span>
          </label>
        </div>

        {formData.sms.enabled && (
          <>
            {/* Provider Selection */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                SMS Provider
              </label>
              <select
                value={formData.sms.provider}
                onChange={(e) => handleProviderChange('sms', e.target.value)}
                className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm focus:border-accent-500 dark:focus:border-accent-400 focus:ring-accent-500 dark:focus:ring-accent-400 transition-colors"
              >
                <option value="twilio">Twilio</option>
                <option value="messagebird">MessageBird (Coming Soon)</option>
                <option value="sns">AWS SNS (Coming Soon)</option>
              </select>
            </div>

            {/* Twilio Configuration */}
            {formData.sms.provider === 'twilio' && (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Account SID
                  </label>
                  <input
                    type="text"
                    value={formData.sms.twilio?.accountSid || ''}
                    onChange={(e) => handleChange('sms', 'twilio', 'accountSid', e.target.value)}
                    className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm focus:border-accent-500 dark:focus:border-accent-400 focus:ring-accent-500 dark:focus:ring-accent-400 transition-colors"
                    placeholder="ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Auth Token
                  </label>
                  <div className="relative">
                    <input
                      type={showSecrets['twilio-auth'] ? 'text' : 'password'}
                      value={formData.sms.twilio?.authToken || ''}
                      onChange={(e) => handleChange('sms', 'twilio', 'authToken', e.target.value)}
                      className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm focus:border-accent-500 dark:focus:border-accent-400 focus:ring-accent-500 dark:focus:ring-accent-400 pr-10 transition-colors"
                      placeholder="Enter your Twilio auth token"
                    />
                    <button
                      type="button"
                      onClick={() => toggleSecretVisibility('twilio-auth')}
                      className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                    >
                      {showSecrets['twilio-auth'] ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Phone Number
                  </label>
                  <input
                    type="text"
                    value={formData.sms.twilio?.phoneNumber || ''}
                    onChange={(e) => handleChange('sms', 'twilio', 'phoneNumber', e.target.value)}
                    className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm focus:border-accent-500 dark:focus:border-accent-400 focus:ring-accent-500 dark:focus:ring-accent-400 transition-colors"
                    placeholder="+1234567890"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Verify Service SID (Optional)
                  </label>
                  <input
                    type="text"
                    value={formData.sms.twilio?.verifyServiceSid || ''}
                    onChange={(e) => handleChange('sms', 'twilio', 'verifyServiceSid', e.target.value)}
                    className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm focus:border-accent-500 dark:focus:border-accent-400 focus:ring-accent-500 dark:focus:ring-accent-400 transition-colors"
                    placeholder="VAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                  />
                  <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">Used for OTP verification</p>
                </div>

                <button
                  onClick={() => handleValidate('sms')}
                  disabled={validating === 'sms'}
                  className="px-4 py-2 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-900 dark:text-white rounded-lg font-medium transition-colors disabled:opacity-50"
                >
                  {validating === 'sms' ? 'Validating...' : 'Test SMS Configuration'}
                </button>
              </div>
            )}
          </>
        )}
      </div>

      {/* Email Settings */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 transition-colors duration-200">
        <div className="mb-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Mail className="w-5 h-5 text-gray-600 dark:text-gray-300" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Email Configuration</h3>
          </div>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={formData.email.enabled}
              onChange={() => handleToggleEnabled('email')}
              className="rounded border-gray-300 text-accent-600 focus:ring-accent-500"
            />
            <span className="text-sm text-gray-600 dark:text-gray-300">Enable Email</span>
          </label>
        </div>

        {formData.email.enabled && (
          <>
            {/* Provider Selection */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Email Provider
              </label>
              <select
                value={formData.email.provider}
                onChange={(e) => handleProviderChange('email', e.target.value)}
                className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm focus:border-accent-500 dark:focus:border-accent-400 focus:ring-accent-500 dark:focus:ring-accent-400 transition-colors"
              >
                <option value="sendgrid">SendGrid</option>
                <option value="mailgun">Mailgun (Coming Soon)</option>
                <option value="ses">AWS SES (Coming Soon)</option>
                <option value="smtp">SMTP (Coming Soon)</option>
              </select>
            </div>

            {/* SendGrid Configuration */}
            {formData.email.provider === 'sendgrid' && (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    API Key
                  </label>
                  <div className="relative">
                    <input
                      type={showSecrets['sendgrid-api'] ? 'text' : 'password'}
                      value={formData.email.sendgrid?.apiKey || ''}
                      onChange={(e) => handleChange('email', 'sendgrid', 'apiKey', e.target.value)}
                      className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm focus:border-accent-500 dark:focus:border-accent-400 focus:ring-accent-500 dark:focus:ring-accent-400 pr-10 transition-colors"
                      placeholder="SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                    />
                    <button
                      type="button"
                      onClick={() => toggleSecretVisibility('sendgrid-api')}
                      className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                    >
                      {showSecrets['sendgrid-api'] ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    From Email
                  </label>
                  <input
                    type="email"
                    value={formData.email.sendgrid?.fromEmail || ''}
                    onChange={(e) => handleChange('email', 'sendgrid', 'fromEmail', e.target.value)}
                    className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm focus:border-accent-500 dark:focus:border-accent-400 focus:ring-accent-500 dark:focus:ring-accent-400 transition-colors"
                    placeholder="noreply@example.com"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    From Name
                  </label>
                  <input
                    type="text"
                    value={formData.email.sendgrid?.fromName || ''}
                    onChange={(e) => handleChange('email', 'sendgrid', 'fromName', e.target.value)}
                    className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm focus:border-accent-500 dark:focus:border-accent-400 focus:ring-accent-500 dark:focus:ring-accent-400 transition-colors"
                    placeholder="Your Company Name"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Reply-To Email (Optional)
                  </label>
                  <input
                    type="email"
                    value={formData.email.sendgrid?.replyToEmail || ''}
                    onChange={(e) => handleChange('email', 'sendgrid', 'replyToEmail', e.target.value)}
                    className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm focus:border-accent-500 dark:focus:border-accent-400 focus:ring-accent-500 dark:focus:ring-accent-400 transition-colors"
                    placeholder="support@example.com"
                  />
                </div>

                <button
                  onClick={() => handleValidate('email')}
                  disabled={validating === 'email'}
                  className="px-4 py-2 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-900 dark:text-white rounded-lg font-medium transition-colors disabled:opacity-50"
                >
                  {validating === 'email' ? 'Validating...' : 'Test Email Configuration'}
                </button>
              </div>
            )}
          </>
        )}
      </div>

      {/* Save Button */}
      <div className="flex justify-end">
        <button
          onClick={handleSave}
          disabled={saving}
          className="px-6 py-2 bg-accent-600 dark:bg-accent-500 text-white rounded-lg hover:bg-accent-700 dark:hover:bg-accent-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          {saving ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
              Saving...
            </>
          ) : (
            <>
              <Check className="w-4 h-4" />
              Save Communication Settings
            </>
          )}
        </button>
      </div>
    </div>
  );
};

export default CommunicationSettingsComponent;