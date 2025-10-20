import React, { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Settings,
  ArrowRight,
  Info,
  CreditCard,
  Store as StoreIcon
} from 'lucide-react';
import { useTranslation } from 'react-i18next';

/**
 * TenantPaymentSettings - Redirect to Store Settings
 *
 * Note: Payment provider configuration has been consolidated into Store Settings
 * to avoid duplication and provide a better user experience.
 *
 * Users are redirected to:
 * - Store Settings → Payment Tab → Online Payment Settings (for provider config)
 * - Payments page (for transaction history and analytics)
 *
 * This consolidation provides:
 * - Single source of truth for payment configuration
 * - Better UX (settings where users expect them)
 * - Unified V2 backend architecture
 */
const TenantPaymentSettings: React.FC = () => {
  const { t } = useTranslation(['payments', 'common']);
  const { tenantId } = useParams<{ tenantId: string }>();
  const navigate = useNavigate();

  // Auto-redirect after 3 seconds
  useEffect(() => {
    const timer = setTimeout(() => {
      // Navigate to dashboard or stores list
      navigate('/dashboard/tenants');
    }, 5000);

    return () => clearTimeout(timer);
  }, [navigate]);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center p-6">
      <div className="max-w-2xl w-full bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8">
        {/* Icon */}
        <div className="flex justify-center mb-6">
          <div className="p-4 bg-blue-100 dark:bg-blue-900 rounded-full">
            <Settings className="w-12 h-12 text-blue-600 dark:text-blue-400" />
          </div>
        </div>

        {/* Title */}
        <h1 className="text-3xl font-bold text-center text-gray-900 dark:text-white mb-4">
          Payment Settings Have Moved
        </h1>

        {/* Description */}
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-6 mb-6">
          <div className="flex items-start gap-3">
            <Info className="w-5 h-5 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
            <div className="text-sm text-blue-900 dark:text-blue-100">
              <p className="font-semibold mb-2">Payment configuration is now managed at the store level</p>
              <p className="mb-2">
                We've consolidated payment settings into Store Settings to provide a better user experience
                and avoid duplication. This change brings all store-specific configurations into one place.
              </p>
              <p className="text-blue-800 dark:text-blue-200">
                You'll be redirected to the tenants page in a few seconds...
              </p>
            </div>
          </div>
        </div>

        {/* Navigation Options */}
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
            Where to find payment settings now:
          </h2>

          {/* Option 1: Store Settings */}
          <button
            onClick={() => navigate('/dashboard/tenants')}
            className="w-full flex items-center justify-between p-4 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 border border-blue-200 dark:border-blue-800 rounded-lg hover:shadow-md transition-all group"
          >
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-600 rounded-lg">
                <StoreIcon className="w-5 h-5 text-white" />
              </div>
              <div className="text-left">
                <div className="font-semibold text-gray-900 dark:text-white">
                  Store Settings → Payment Tab
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  Configure payment providers (Clover, Moneris, Interac)
                </div>
              </div>
            </div>
            <ArrowRight className="w-5 h-5 text-blue-600 dark:text-blue-400 group-hover:translate-x-1 transition-transform" />
          </button>

          {/* Option 2: Payments Page */}
          <button
            onClick={() => navigate('/dashboard/payments')}
            className="w-full flex items-center justify-between p-4 bg-gradient-to-r from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 border border-purple-200 dark:border-purple-800 rounded-lg hover:shadow-md transition-all group"
          >
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-600 rounded-lg">
                <CreditCard className="w-5 h-5 text-white" />
              </div>
              <div className="text-left">
                <div className="font-semibold text-gray-900 dark:text-white">
                  Payments Page
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  View transactions, refunds, and payment analytics
                </div>
              </div>
            </div>
            <ArrowRight className="w-5 h-5 text-purple-600 dark:text-purple-400 group-hover:translate-x-1 transition-transform" />
          </button>
        </div>

        {/* Quick Guide */}
        <div className="mt-8 pt-6 border-t border-gray-200 dark:border-gray-700">
          <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">
            📖 Quick Guide: Configuring Payment Providers
          </h3>
          <ol className="text-sm text-gray-600 dark:text-gray-400 space-y-2 list-decimal list-inside">
            <li>Go to <strong className="text-gray-900 dark:text-white">Tenants</strong> and select your tenant</li>
            <li>Click <strong className="text-gray-900 dark:text-white">Manage Stores</strong></li>
            <li>Click the <strong className="text-gray-900 dark:text-white">Settings</strong> icon for a store</li>
            <li>Navigate to the <strong className="text-gray-900 dark:text-white">Payment</strong> tab</li>
            <li>Click <strong className="text-gray-900 dark:text-white">Online Payment Settings</strong></li>
            <li>Select your provider (Clover, Moneris, or Interac) and configure credentials</li>
          </ol>
        </div>

        {/* Footer */}
        <div className="mt-6 text-center text-xs text-gray-500 dark:text-gray-400">
          <p>Payment settings consolidated as part of V2 Payment System refactor (Phase 2)</p>
          <p className="mt-1">All payment data stored securely with AES-256 encryption</p>
        </div>
      </div>
    </div>
  );
};

export default TenantPaymentSettings;
