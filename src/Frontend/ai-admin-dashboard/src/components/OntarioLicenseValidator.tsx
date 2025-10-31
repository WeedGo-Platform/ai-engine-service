import React, { useState } from 'react';
import axios from 'axios';
import { useTranslation } from 'react-i18next';

interface LicenseValidationResult {
  is_valid: boolean;
  license_number?: string;
  store_name?: string;
  address?: string;
  municipality?: string;
  store_status?: string;
  website?: string;
  error_message?: string;
  verification_tier?: string;
  domain_match?: boolean;
  auto_fill_data?: {
    store_name: string;
    address: string;
    municipality: string;
    website?: string;
    license_number: string;
    license_status: string;
  };
}

interface OntarioLicenseValidatorProps {
  onValidationSuccess: (data: LicenseValidationResult, autoCreateStore: boolean) => void;
  initialLicenseNumber?: string;
  email?: string;
}

const OntarioLicenseValidator: React.FC<OntarioLicenseValidatorProps> = ({
  onValidationSuccess,
  initialLicenseNumber = '',
  email
}) => {
  const { t } = useTranslation('signup');
  const [licenseNumber, setLicenseNumber] = useState(initialLicenseNumber);
  const [isValidating, setIsValidating] = useState(false);
  const [validationResult, setValidationResult] = useState<LicenseValidationResult | null>(null);
  const [showSearchResults, setShowSearchResults] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [autoCreateStore, setAutoCreateStore] = useState(true); // Default to checked

  const API_BASE_URL = 'http://localhost:5024';

  const validateLicense = async () => {
    if (!licenseNumber.trim()) {
      setValidationResult({
        is_valid: false,
        error_message: 'Please enter a license number'
      });
      return;
    }

    setIsValidating(true);
    setValidationResult(null);

    try {
      const response = await axios.post(`${API_BASE_URL}/api/crsa/validate`, {
        license_number: licenseNumber.trim(),
        email: email || undefined
      });

      const result = response.data as LicenseValidationResult;
      setValidationResult(result);

      if (result.is_valid && result.auto_fill_data) {
        onValidationSuccess(result, autoCreateStore);
      }
    } catch (error: any) {
      console.error('License validation error:', error);
      setValidationResult({
        is_valid: false,
        error_message: error.response?.data?.detail || 'Failed to validate license'
      });
    } finally {
      setIsValidating(false);
    }
  };

  const searchStores = async () => {
    if (!searchQuery.trim() || searchQuery.trim().length < 2) {
      return;
    }

    setIsSearching(true);

    try {
      const response = await axios.post(`${API_BASE_URL}/api/crsa/search`, {
        query: searchQuery.trim(),
        limit: 10,
        authorized_only: true
      });

      setSearchResults(response.data.stores || []);
      setShowSearchResults(true);
    } catch (error) {
      console.error('Store search error:', error);
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  const selectStore = (store: any) => {
    setLicenseNumber(store.license_number);
    setShowSearchResults(false);
    setSearchQuery('');
    // Auto-validate after selection
    setTimeout(() => {
      const input = document.querySelector('input[name="license_number"]') as HTMLInputElement;
      if (input) {
        input.value = store.license_number;
        validateLicense();
      }
    }, 100);
  };

  return (
    <div className="space-y-4">
      {/* License Number Input */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          {t('tenant.ontario.licenseLabel')} <span className="text-red-500">*</span>
        </label>
        <div className="flex gap-2">
          <input
            type="text"
            name="license_number"
            value={licenseNumber}
            onChange={(e) => setLicenseNumber(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault();
                validateLicense();
              }
            }}
            placeholder={t('tenant.ontario.licensePlaceholder')}
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <button
            onClick={validateLicense}
            disabled={isValidating || !licenseNumber.trim()}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              isValidating || !licenseNumber.trim()
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-blue-600 text-white hover:bg-blue-700'
            }`}
          >
            {isValidating ? (
              <div className="flex items-center gap-2">
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                <span>{t('tenant.ontario.validating')}</span>
              </div>
            ) : (
              t('tenant.ontario.validate')
            )}
          </button>
        </div>
        <p className="text-xs text-gray-500 mt-1">
          {t('tenant.ontario.licenseHelpText')}
        </p>
      </div>

      {/* Validation Result */}
      {validationResult && (
        <div
          className={`p-4 rounded-lg border-2 ${
            validationResult.is_valid
              ? 'bg-green-50 border-green-500'
              : 'bg-red-50 border-red-500'
          }`}
        >
          {validationResult.is_valid ? (
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-green-700 font-semibold">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                <span>{t('tenant.ontario.validatedSuccess')}</span>
              </div>
              {validationResult.store_name && (
                <div className="grid grid-cols-2 gap-2 text-sm mt-3">
                  <div>
                    <p className="text-gray-600">{t('tenant.ontario.storeNameLabel')}</p>
                    <p className="font-semibold text-gray-900">{validationResult.store_name}</p>
                  </div>
                  <div>
                    <p className="text-gray-600">{t('tenant.ontario.municipalityLabel')}</p>
                    <p className="font-semibold text-gray-900">{validationResult.municipality}</p>
                  </div>
                  <div className="col-span-2">
                    <p className="text-gray-600">{t('tenant.ontario.addressLabel')}</p>
                    <p className="font-semibold text-gray-900">{validationResult.address}</p>
                  </div>
                  {validationResult.website && (
                    <div className="col-span-2">
                      <p className="text-gray-600">{t('tenant.ontario.websiteLabel')}</p>
                      <p className="font-semibold text-blue-600">{validationResult.website}</p>
                    </div>
                  )}
                </div>
              )}
              
              {/* Auto-create store checkbox */}
              {validationResult.store_name && (
                <div className="mt-4 pt-4 border-t border-green-200">
                  <label className="flex items-start gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={autoCreateStore}
                      onChange={(e) => {
                        setAutoCreateStore(e.target.checked);
                        // Notify parent with updated preference
                        if (validationResult.is_valid && validationResult.auto_fill_data) {
                          onValidationSuccess(validationResult, e.target.checked);
                        }
                      }}
                      className="mt-1 h-4 w-4 text-green-600 focus:ring-green-500 border-gray-300 rounded"
                    />
                    <div className="flex-1">
                      <span className="text-sm font-medium text-green-800">
                        Create <strong>{validationResult.store_name}</strong> as my first store
                      </span>
                      <p className="text-xs text-green-700 mt-1">
                        This store will be automatically created when you complete signup. You can uncheck this to add stores manually later.
                      </p>
                    </div>
                  </label>
                </div>
              )}
            </div>
          ) : (
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-red-700 font-semibold">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
                <span>{t('tenant.ontario.validationFailed')}</span>
              </div>
              <p className="text-red-700 text-sm">{validationResult.error_message}</p>
            </div>
          )}
        </div>
      )}

      {/* Store Search Alternative */}
      <div className="border-t pt-4">
        <p className="text-sm text-gray-600 mb-2">
          {t('tenant.ontario.searchIntro')}
        </p>
        <div className="flex gap-2">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault();
                searchStores();
              }
            }}
            placeholder={t('tenant.ontario.searchPlaceholder')}
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
          />
          <button
            onClick={searchStores}
            disabled={isSearching || searchQuery.trim().length < 2}
            className={`px-4 py-2 rounded-lg font-medium text-sm transition-colors ${
              isSearching || searchQuery.trim().length < 2
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-gray-600 text-white hover:bg-gray-700'
            }`}
          >
            {isSearching ? t('tenant.ontario.searching') : t('tenant.ontario.search')}
          </button>
        </div>

        {/* Search Results */}
        {showSearchResults && (
          <div className="mt-3 border rounded-lg max-h-60 overflow-y-auto">
            {searchResults.length > 0 ? (
              <div className="divide-y">
                {searchResults.map((store) => (
                  <button
                    key={store.id}
                    onClick={() => selectStore(store)}
                    className="w-full text-left p-3 hover:bg-blue-50 transition-colors"
                  >
                    <p className="font-semibold text-gray-900">{store.store_name}</p>
                    <p className="text-sm text-gray-600">{store.address}</p>
                    <p className="text-xs text-gray-500 mt-1">
                      {t('tenant.ontario.licenseField')} {store.license_number} • {store.municipality}
                    </p>
                    {store.is_available ? (
                      <span className="inline-block mt-1 text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded">
                        {t('tenant.ontario.availableForSignup')}
                      </span>
                    ) : (
                      <span className="inline-block mt-1 text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded">
                        {t('tenant.ontario.alreadyRegistered')}
                      </span>
                    )}
                  </button>
                ))}
              </div>
            ) : (
              <p className="p-4 text-sm text-gray-500 text-center">
                {t('tenant.ontario.noStoresFound')}
              </p>
            )}
          </div>
        )}
      </div>

      {/* Help Text */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
        <p className="text-sm text-blue-800">
          <strong>{t('tenant.ontario.needHelp')}</strong> {t('tenant.ontario.helpText')}
        </p>
      </div>
    </div>
  );
};

export default OntarioLicenseValidator;
