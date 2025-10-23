import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Shield, Save, AlertCircle, CheckCircle, Clock, RefreshCw } from 'lucide-react';
import ocsService, { StoreOCSConfig, OCSPositionHistory, OCSEventHistory } from '../services/ocsService';

interface OCSComplianceTabProps {
  storeId: string;
  tenantId: string;
  currentConfig?: {
    ocs_key?: string;
    license_number?: string;
  };
  onConfigUpdate?: () => void;
}

const OCSComplianceTab: React.FC<OCSComplianceTabProps> = ({
  storeId,
  tenantId,
  currentConfig,
  onConfigUpdate,
}) => {
  const { t } = useTranslation(['stores', 'common']);

  // Form state - Store Configuration
  const [ocsKey, setOcsKey] = useState(currentConfig?.ocs_key || '');
  const [licenseNumber, setLicenseNumber] = useState(currentConfig?.license_number || '');
  
  // OAuth Configuration (optional for advanced setup)
  const [showOAuthConfig, setShowOAuthConfig] = useState(false);
  const [oauthClientId, setOauthClientId] = useState('');
  const [oauthClientSecret, setOauthClientSecret] = useState('');
  const [oauthTokenUrl, setOauthTokenUrl] = useState('https://login.microsoftonline.com/common/oauth2/v2.0/token');
  const [oauthScope, setOauthScope] = useState('https://graph.microsoft.com/.default');
  
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  // History state
  const [positionHistory, setPositionHistory] = useState<OCSPositionHistory[]>([]);
  const [eventHistory, setEventHistory] = useState<OCSEventHistory[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [submittingPosition, setSubmittingPosition] = useState(false);

  useEffect(() => {
    setOcsKey(currentConfig?.ocs_key || '');
    setLicenseNumber(currentConfig?.license_number || '');
  }, [currentConfig]);

  useEffect(() => {
    if (ocsKey && licenseNumber) {
      loadHistory();
    }
  }, [storeId, ocsKey, licenseNumber]);

  const loadHistory = async () => {
    try {
      setLoadingHistory(true);
      const [positions, events] = await Promise.all([
        ocsService.getPositionHistory(storeId, 10),
        ocsService.getEventHistory(storeId, 20),
      ]);
      setPositionHistory(positions);
      setEventHistory(events);
    } catch (err: any) {
      console.error('Failed to load OCS history:', err);
    } finally {
      setLoadingHistory(false);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      setError(null);
      setSuccess(false);

      const config: StoreOCSConfig = {
        ocs_key: ocsKey.trim() || undefined,
        license_number: licenseNumber.trim() || undefined,
        oauth_client_id: oauthClientId.trim() || undefined,
        oauth_client_secret: oauthClientSecret.trim() || undefined,
        oauth_token_url: oauthTokenUrl.trim() || undefined,
        oauth_scope: oauthScope.trim() || undefined,
      };

      await ocsService.updateStoreConfig(storeId, config);

      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);

      if (onConfigUpdate) {
        onConfigUpdate();
      }

      // Load history after successful save
      if (config.ocs_key && config.license_number) {
        loadHistory();
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to save OCS configuration');
      console.error('Failed to save OCS config:', err);
    } finally {
      setSaving(false);
    }
  };

  const handleManualSync = async () => {
    try {
      setSubmittingPosition(true);
      setError(null);

      await ocsService.submitPosition({ store_id: storeId });

      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);

      // Reload history
      await loadHistory();
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to submit position');
      console.error('Failed to submit position:', err);
    } finally {
      setSubmittingPosition(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'success':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
            <CheckCircle className="w-3 h-3" />
            Success
          </span>
        );
      case 'failed':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200">
            <AlertCircle className="w-3 h-3" />
            Failed
          </span>
        );
      case 'pending':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200">
            <Clock className="w-3 h-3" />
            Pending
          </span>
        );
      default:
        return null;
    }
  };

  const isConfigured = ocsKey && licenseNumber;

  return (
    <div className="space-y-6">
      {/* Configuration Section */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <div className="flex items-center gap-2 mb-4">
          <Shield className="w-5 h-5 text-primary-600 dark:text-primary-400" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            OCS Integration Configuration
          </h3>
        </div>

        {error && (
          <div className="mb-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
            <div className="flex items-center gap-2 text-red-800 dark:text-red-200">
              <AlertCircle className="w-5 h-5" />
              <span>{error}</span>
            </div>
          </div>
        )}

        {success && (
          <div className="mb-4 p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
            <div className="flex items-center gap-2 text-green-800 dark:text-green-200">
              <CheckCircle className="w-5 h-5" />
              <span>Configuration saved successfully</span>
            </div>
          </div>
        )}

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              OCS Hash Key
            </label>
            <input
              type="text"
              value={ocsKey}
              onChange={(e) => setOcsKey(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              placeholder="Enter OCS hash key"
            />
            <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
              The unique hash key assigned to this store by OCS
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              CRSA License Number
            </label>
            <input
              type="text"
              value={licenseNumber}
              onChange={(e) => setLicenseNumber(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              placeholder="Enter CRSA license number"
            />
            <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
              Cannabis Retail Store Authorization license number
            </p>
          </div>

          {/* OAuth Configuration Section (Collapsible) */}
          <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
            <button
              type="button"
              onClick={() => setShowOAuthConfig(!showOAuthConfig)}
              className="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400"
            >
              <Shield className="w-4 h-4" />
              {showOAuthConfig ? 'Hide' : 'Show'} Advanced OAuth Configuration
            </button>
            <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
              Optional: Configure OAuth credentials if using custom authentication
            </p>
            
            {showOAuthConfig && (
              <div className="mt-4 space-y-4 p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    OAuth Client ID
                  </label>
                  <input
                    type="text"
                    value={oauthClientId}
                    onChange={(e) => setOauthClientId(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    placeholder="Enter OAuth Client ID"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    OAuth Client Secret
                  </label>
                  <input
                    type="password"
                    value={oauthClientSecret}
                    onChange={(e) => setOauthClientSecret(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    placeholder="Enter OAuth Client Secret"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    OAuth Token URL
                  </label>
                  <input
                    type="url"
                    value={oauthTokenUrl}
                    onChange={(e) => setOauthTokenUrl(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    OAuth Scope
                  </label>
                  <input
                    type="text"
                    value={oauthScope}
                    onChange={(e) => setOauthScope(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  />
                </div>
              </div>
            )}
          </div>

          <div className="flex gap-3">
            <button
              onClick={handleSave}
              disabled={saving}
              className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Save className="w-4 h-4" />
              {saving ? 'Saving...' : 'Save Configuration'}
            </button>

            {isConfigured && (
              <button
                onClick={handleManualSync}
                disabled={submittingPosition}
                className="flex items-center gap-2 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <RefreshCw className={`w-4 h-4 ${submittingPosition ? 'animate-spin' : ''}`} />
                {submittingPosition ? 'Submitting...' : 'Manual Sync'}
              </button>
            )}
          </div>
        </div>
      </div>

      {/* History Section */}
      {isConfigured && (
        <>
          {/* Position History */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Position Submission History
              </h3>
              <button
                onClick={loadHistory}
                disabled={loadingHistory}
                className="text-sm text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300"
              >
                <RefreshCw className={`w-4 h-4 ${loadingHistory ? 'animate-spin' : ''}`} />
              </button>
            </div>

            {positionHistory.length === 0 ? (
              <p className="text-sm text-gray-500 dark:text-gray-400">
                No position submissions yet
              </p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50 dark:bg-gray-700">
                    <tr>
                      <th className="px-4 py-2 text-left text-gray-700 dark:text-gray-300">Date</th>
                      <th className="px-4 py-2 text-left text-gray-700 dark:text-gray-300">Items</th>
                      <th className="px-4 py-2 text-left text-gray-700 dark:text-gray-300">Quantity</th>
                      <th className="px-4 py-2 text-left text-gray-700 dark:text-gray-300">Status</th>
                      <th className="px-4 py-2 text-left text-gray-700 dark:text-gray-300">Submitted</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                    {positionHistory.map((position) => (
                      <tr key={position.id}>
                        <td className="px-4 py-3 text-gray-900 dark:text-white">
                          {position.snapshot_date}
                        </td>
                        <td className="px-4 py-3 text-gray-900 dark:text-white">
                          {position.total_items}
                        </td>
                        <td className="px-4 py-3 text-gray-900 dark:text-white">
                          {position.total_quantity}
                        </td>
                        <td className="px-4 py-3">{getStatusBadge(position.status)}</td>
                        <td className="px-4 py-3 text-gray-600 dark:text-gray-400">
                          {position.submitted_at
                            ? new Date(position.submitted_at).toLocaleString()
                            : '-'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Event History */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Event Submission History
              </h3>
            </div>

            {eventHistory.length === 0 ? (
              <p className="text-sm text-gray-500 dark:text-gray-400">No events submitted yet</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50 dark:bg-gray-700">
                    <tr>
                      <th className="px-4 py-2 text-left text-gray-700 dark:text-gray-300">Type</th>
                      <th className="px-4 py-2 text-left text-gray-700 dark:text-gray-300">
                        Transaction ID
                      </th>
                      <th className="px-4 py-2 text-left text-gray-700 dark:text-gray-300">Status</th>
                      <th className="px-4 py-2 text-left text-gray-700 dark:text-gray-300">Retries</th>
                      <th className="px-4 py-2 text-left text-gray-700 dark:text-gray-300">Submitted</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                    {eventHistory.map((event) => (
                      <tr key={event.id}>
                        <td className="px-4 py-3 text-gray-900 dark:text-white">
                          {event.transaction_type}
                        </td>
                        <td className="px-4 py-3 text-gray-600 dark:text-gray-400 font-mono text-xs">
                          {event.transaction_id.substring(0, 8)}...
                        </td>
                        <td className="px-4 py-3">{getStatusBadge(event.status)}</td>
                        <td className="px-4 py-3 text-gray-900 dark:text-white">
                          {event.retry_count}
                        </td>
                        <td className="px-4 py-3 text-gray-600 dark:text-gray-400">
                          {event.submitted_at ? new Date(event.submitted_at).toLocaleString() : '-'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
};

export default OCSComplianceTab;
