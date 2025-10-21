import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getApiEndpoint } from '../config/app.config';
import {
  UserCheck, UserX, AlertCircle, CheckCircle, XCircle,
  Mail, Phone, Calendar, Building, MapPin, Globe,
  FileText, Clock, TrendingUp, RefreshCw
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../contexts/AuthContext';

interface PendingAccount {
  tenant_id: string;
  tenant_code: string;
  store_name: string;
  license_number: string;
  contact_email: string;
  contact_phone?: string;
  contact_name: string;
  contact_role: string;
  submitted_at: string;
  verification_tier: string;
  needs_manual_review: boolean;
}

interface PendingAccountDetail extends PendingAccount {
  crsa_address: string;
  crsa_municipality?: string;
  crsa_store_status: string;
  crsa_website?: string;
  email_domain: string;
  domain_matches_crsa: boolean;
  subscription_tier: string;
  account_status: string;
}

interface ReviewStats {
  total_pending: number;
  pending_this_week: number;
  avg_review_time_hours: number;
  approval_rate: number;
}

const TenantReview: React.FC = () => {
  const { t } = useTranslation(['signup', 'common']);
  const { user, isSuperAdmin, isTenantAdmin, getAuthHeader } = useAuth();
  const queryClient = useQueryClient();
  const [selectedAccount, setSelectedAccount] = useState<string | null>(null);
  const [rejectReason, setRejectReason] = useState('');
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [adminNotes, setAdminNotes] = useState('');

  // Check permissions
  const canReview = isSuperAdmin() || isTenantAdmin();

  // Fetch pending accounts
  const { data: pendingAccounts, isLoading: accountsLoading } = useQuery<PendingAccount[]>({
    queryKey: ['pending-accounts'],
    queryFn: async () => {
      const response = await fetch(getApiEndpoint('/admin/pending-review/'), {
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeader()
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch pending accounts');
      }

      return response.json();
    },
    enabled: canReview
  });

  // Fetch review stats
  const { data: stats, isLoading: statsLoading } = useQuery<ReviewStats>({
    queryKey: ['review-stats'],
    queryFn: async () => {
      const response = await fetch(getApiEndpoint('/admin/pending-review/stats'), {
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeader()
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch stats');
      }

      return response.json();
    },
    enabled: canReview
  });

  // Fetch account detail
  const { data: accountDetail, isLoading: detailLoading } = useQuery<PendingAccountDetail>({
    queryKey: ['account-detail', selectedAccount],
    queryFn: async () => {
      const response = await fetch(getApiEndpoint(`/admin/pending-review/${selectedAccount}`), {
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeader()
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch account detail');
      }

      return response.json();
    },
    enabled: !!selectedAccount && canReview
  });

  // Approve mutation
  const approveMutation = useMutation({
    mutationFn: async (tenantId: string) => {
      const response = await fetch(getApiEndpoint(`/admin/pending-review/${tenantId}/approve`), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeader()
        },
        body: JSON.stringify({
          admin_notes: adminNotes || null,
          send_welcome_email: true
        })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to approve account');
      }

      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pending-accounts'] });
      queryClient.invalidateQueries({ queryKey: ['review-stats'] });
      setSelectedAccount(null);
      setAdminNotes('');
      alert(t('signup:review.messages.approved'));
    },
    onError: (error: Error) => {
      alert(t('signup:review.messages.approveFailed', { error: error.message }));
    }
  });

  // Reject mutation
  const rejectMutation = useMutation({
    mutationFn: async (tenantId: string) => {
      const response = await fetch(getApiEndpoint(`/admin/pending-review/${tenantId}/reject`), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeader()
        },
        body: JSON.stringify({
          reason: rejectReason,
          send_notification: true
        })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to reject account');
      }

      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pending-accounts'] });
      queryClient.invalidateQueries({ queryKey: ['review-stats'] });
      setSelectedAccount(null);
      setShowRejectModal(false);
      setRejectReason('');
      alert(t('signup:review.messages.rejected'));
    },
    onError: (error: Error) => {
      alert(t('signup:review.messages.rejectFailed', { error: error.message }));
    }
  });

  if (!canReview) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <AlertCircle className="h-10 w-10 sm:h-12 sm:w-12 text-yellow-500 dark:text-yellow-400 mx-auto mb-4" />
          <p className="text-sm sm:text-base text-gray-600 dark:text-gray-400">{t('signup:review.messages.noPermission')}</p>
        </div>
      </div>
    );
  }

  if (accountsLoading || statsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 dark:border-primary-400"></div>
      </div>
    );
  }

  return (
    <div className="space-y-4 sm:space-y-6 p-3 sm:p-0">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 sm:gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl lg:text-3xl font-bold text-gray-900 dark:text-white transition-colors">{t('signup:review.title')}</h1>
          <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400 mt-1 transition-colors">
            {t('signup:review.description')}
          </p>
        </div>
        <button
          onClick={() => queryClient.invalidateQueries({ queryKey: ['pending-accounts'] })}
          className="w-full sm:w-auto flex items-center justify-center gap-2 px-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-200 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-all active:scale-95 touch-manipulation"
        >
          <RefreshCw className="h-4 w-4" />
          <span className="text-sm">{t('signup:review.refresh')}</span>
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 lg:gap-6">
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 sm:p-6 shadow-sm transition-colors">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs sm:text-sm font-medium text-gray-600 dark:text-gray-400">{t('signup:review.stats.totalPending')}</p>
              <p className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white">
                {stats?.total_pending || 0}
              </p>
            </div>
            <Clock className="h-7 w-7 sm:h-8 sm:w-8 text-yellow-600 dark:text-yellow-400" />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 sm:p-6 shadow-sm transition-colors">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs sm:text-sm font-medium text-gray-600 dark:text-gray-400">{t('signup:review.stats.thisWeek')}</p>
              <p className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white">
                {stats?.pending_this_week || 0}
              </p>
            </div>
            <TrendingUp className="h-7 w-7 sm:h-8 sm:w-8 text-blue-600 dark:text-blue-400" />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 sm:p-6 shadow-sm transition-colors">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs sm:text-sm font-medium text-gray-600 dark:text-gray-400">{t('signup:review.stats.avgReviewTime')}</p>
              <p className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white">
                {stats?.avg_review_time_hours || 0}h
              </p>
            </div>
            <Clock className="h-7 w-7 sm:h-8 sm:w-8 text-purple-600 dark:text-purple-400" />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 sm:p-6 shadow-sm transition-colors">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs sm:text-sm font-medium text-gray-600 dark:text-gray-400">{t('signup:review.stats.approvalRate')}</p>
              <p className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white">
                {stats?.approval_rate || 0}%
              </p>
            </div>
            <CheckCircle className="h-7 w-7 sm:h-8 sm:w-8 text-green-600 dark:text-green-400" />
          </div>
        </div>
      </div>

      {/* Pending Accounts List */}
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-sm transition-colors">
        <div className="px-4 sm:px-6 py-3 sm:py-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-white">{t('signup:review.table.title')}</h2>
        </div>

        {pendingAccounts && pendingAccounts.length > 0 ? (
          <div className="overflow-x-auto -mx-4 sm:mx-0">
            <div className="inline-block min-w-full align-middle">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-700/50">
                <tr>
                  <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    {t('signup:review.table.storeName')}
                  </th>
                  <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider hidden md:table-cell">
                    {t('signup:review.table.contact')}
                  </th>
                  <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider hidden lg:table-cell">
                    {t('signup:review.table.licenseNumber')}
                  </th>
                  <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider hidden sm:table-cell">
                    {t('signup:review.table.submitted')}
                  </th>
                  <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    {t('signup:review.table.tier')}
                  </th>
                  <th className="px-3 sm:px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    {t('signup:review.table.actions')}
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                {pendingAccounts.map((account) => (
                  <tr key={account.tenant_id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
                    <td className="px-3 sm:px-6 py-3 sm:py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <Building className="h-4 w-4 sm:h-5 sm:w-5 text-gray-400 dark:text-gray-500 mr-2 flex-shrink-0" />
                        <div className="min-w-0">
                          <div className="text-xs sm:text-sm font-medium text-gray-900 dark:text-white truncate">
                            {account.store_name}
                          </div>
                          <div className="text-xs text-gray-500 dark:text-gray-400 truncate">
                            {account.tenant_code}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-3 sm:px-6 py-3 sm:py-4 whitespace-nowrap hidden md:table-cell">
                      <div className="text-xs sm:text-sm text-gray-900 dark:text-white">{account.contact_name}</div>
                      <div className="text-xs text-gray-500 dark:text-gray-400">{account.contact_email}</div>
                    </td>
                    <td className="px-3 sm:px-6 py-3 sm:py-4 whitespace-nowrap text-xs sm:text-sm text-gray-900 dark:text-white hidden lg:table-cell">
                      {account.license_number}
                    </td>
                    <td className="px-3 sm:px-6 py-3 sm:py-4 whitespace-nowrap text-xs sm:text-sm text-gray-500 dark:text-gray-400 hidden sm:table-cell">
                      {new Date(account.submitted_at).toLocaleDateString()}
                    </td>
                    <td className="px-3 sm:px-6 py-3 sm:py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        account.verification_tier === 'auto_approved'
                          ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-400'
                          : 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-400'
                      }`}>
                        {account.verification_tier}
                      </span>
                    </td>
                    <td className="px-3 sm:px-6 py-3 sm:py-4 whitespace-nowrap text-right text-xs sm:text-sm font-medium">
                      <button
                        onClick={() => setSelectedAccount(account.tenant_id)}
                        className="text-primary-600 dark:text-primary-400 hover:text-primary-900 dark:hover:text-primary-300 transition-colors"
                      >
                        {t('signup:review.table.review')}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            </div>
          </div>
        ) : (
          <div className="p-8 sm:p-12 text-center">
            <CheckCircle className="h-10 w-10 sm:h-12 sm:w-12 text-green-500 dark:text-green-400 mx-auto mb-4" />
            <p className="text-sm sm:text-base text-gray-600 dark:text-gray-400">{t('signup:review.table.noPending')}</p>
          </div>
        )}
      </div>

      {/* Account Detail Modal */}
      {selectedAccount && accountDetail && (
        <div className="fixed inset-0 bg-black dark:bg-black bg-opacity-50 dark:bg-opacity-70 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto border border-gray-200 dark:border-gray-700">
            {/* Modal Header */}
            <div className="px-4 sm:px-6 py-3 sm:py-4 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center sticky top-0 bg-white dark:bg-gray-800 z-10">
              <h2 className="text-lg sm:text-xl font-bold text-gray-900 dark:text-white">{t('signup:review.modal.title')}</h2>
              <button
                onClick={() => setSelectedAccount(null)}
                className="text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
              >
                <XCircle className="h-5 w-5 sm:h-6 sm:w-6" />
              </button>
            </div>

            {/* Modal Content */}
            <div className="p-4 sm:p-6 space-y-4 sm:space-y-6">
              {/* Store Information */}
              <div>
                <h3 className="text-base sm:text-lg font-semibold mb-3 sm:mb-4 flex items-center text-gray-900 dark:text-white">
                  <Building className="h-4 w-4 sm:h-5 sm:w-5 mr-2" />
                  {t('signup:review.modal.storeInfo')}
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
                  <div>
                    <label className="text-xs sm:text-sm font-medium text-gray-600 dark:text-gray-400">{t('signup:review.modal.storeName')}</label>
                    <p className="text-sm sm:text-base text-gray-900 dark:text-white">{accountDetail.store_name}</p>
                  </div>
                  <div>
                    <label className="text-xs sm:text-sm font-medium text-gray-600 dark:text-gray-400">{t('signup:review.modal.licenseNumber')}</label>
                    <p className="text-sm sm:text-base text-gray-900 dark:text-white">{accountDetail.license_number}</p>
                  </div>
                  <div>
                    <label className="text-xs sm:text-sm font-medium text-gray-600 dark:text-gray-400">{t('signup:review.modal.crsaAddress')}</label>
                    <p className="text-sm sm:text-base text-gray-900 dark:text-white">{accountDetail.crsa_address}</p>
                  </div>
                  <div>
                    <label className="text-xs sm:text-sm font-medium text-gray-600 dark:text-gray-400">{t('signup:review.modal.municipality')}</label>
                    <p className="text-sm sm:text-base text-gray-900 dark:text-white">{accountDetail.crsa_municipality || 'N/A'}</p>
                  </div>
                  <div>
                    <label className="text-xs sm:text-sm font-medium text-gray-600 dark:text-gray-400">{t('signup:review.modal.crsaStatus')}</label>
                    <p className="text-sm sm:text-base text-gray-900 dark:text-white">{accountDetail.crsa_store_status}</p>
                  </div>
                  <div>
                    <label className="text-xs sm:text-sm font-medium text-gray-600 dark:text-gray-400">{t('signup:review.modal.crsaWebsite')}</label>
                    <p className="text-sm sm:text-base text-gray-900 dark:text-white break-all">{accountDetail.crsa_website || 'N/A'}</p>
                  </div>
                </div>
              </div>

              {/* Contact Information */}
              <div>
                <h3 className="text-base sm:text-lg font-semibold mb-3 sm:mb-4 flex items-center text-gray-900 dark:text-white">
                  <Mail className="h-4 w-4 sm:h-5 sm:w-5 mr-2" />
                  {t('signup:review.modal.contactInfo')}
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
                  <div>
                    <label className="text-xs sm:text-sm font-medium text-gray-600 dark:text-gray-400">{t('signup:review.modal.contactName')}</label>
                    <p className="text-sm sm:text-base text-gray-900 dark:text-white">{accountDetail.contact_name}</p>
                  </div>
                  <div>
                    <label className="text-xs sm:text-sm font-medium text-gray-600 dark:text-gray-400">{t('signup:review.modal.role')}</label>
                    <p className="text-sm sm:text-base text-gray-900 dark:text-white">{accountDetail.contact_role}</p>
                  </div>
                  <div>
                    <label className="text-xs sm:text-sm font-medium text-gray-600 dark:text-gray-400">{t('signup:review.modal.email')}</label>
                    <p className="text-sm sm:text-base text-gray-900 dark:text-white break-all">{accountDetail.contact_email}</p>
                  </div>
                  <div>
                    <label className="text-xs sm:text-sm font-medium text-gray-600 dark:text-gray-400">{t('signup:review.modal.phone')}</label>
                    <p className="text-sm sm:text-base text-gray-900 dark:text-white">{accountDetail.contact_phone || 'N/A'}</p>
                  </div>
                </div>
              </div>

              {/* Verification Context */}
              <div>
                <h3 className="text-base sm:text-lg font-semibold mb-3 sm:mb-4 flex items-center text-gray-900 dark:text-white">
                  <FileText className="h-4 w-4 sm:h-5 sm:w-5 mr-2" />
                  {t('signup:review.modal.verificationContext')}
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
                  <div>
                    <label className="text-xs sm:text-sm font-medium text-gray-600 dark:text-gray-400">{t('signup:review.modal.emailDomain')}</label>
                    <p className="text-sm sm:text-base text-gray-900 dark:text-white">{accountDetail.email_domain}</p>
                  </div>
                  <div>
                    <label className="text-xs sm:text-sm font-medium text-gray-600 dark:text-gray-400">{t('signup:review.modal.domainMatchesCrsa')}</label>
                    <p className={`text-sm sm:text-base font-semibold ${accountDetail.domain_matches_crsa ? 'text-green-600 dark:text-green-400' : 'text-yellow-600 dark:text-yellow-400'}`}>
                      {accountDetail.domain_matches_crsa ? t('signup:review.modal.yes') : t('signup:review.modal.no')}
                    </p>
                  </div>
                  <div>
                    <label className="text-xs sm:text-sm font-medium text-gray-600 dark:text-gray-400">{t('signup:review.modal.verificationTier')}</label>
                    <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
                      accountDetail.verification_tier === 'auto_approved'
                        ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-400'
                        : 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-400'
                    }`}>
                      {accountDetail.verification_tier}
                    </span>
                  </div>
                  <div>
                    <label className="text-xs sm:text-sm font-medium text-gray-600 dark:text-gray-400">{t('signup:review.modal.submitted')}</label>
                    <p className="text-sm sm:text-base text-gray-900 dark:text-white">
                      {new Date(accountDetail.submitted_at).toLocaleString()}
                    </p>
                  </div>
                </div>
              </div>

              {/* Admin Notes */}
              <div>
                <label className="block text-xs sm:text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  {t('signup:review.modal.adminNotes')}
                </label>
                <textarea
                  value={adminNotes}
                  onChange={(e) => setAdminNotes(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg focus:ring-primary-500 dark:focus:ring-primary-400 focus:border-primary-500 dark:focus:border-primary-400 text-sm transition-colors"
                  rows={3}
                  placeholder={t('signup:review.modal.adminNotesPlaceholder')}
                />
              </div>

              {/* Actions */}
              <div className="flex flex-col-reverse sm:flex-row justify-end gap-2 sm:gap-4 pt-3 sm:pt-4 border-t border-gray-200 dark:border-gray-700 sticky bottom-0 bg-white dark:bg-gray-800 -mx-4 sm:-mx-6 px-4 sm:px-6 pb-4 sm:pb-0">
                <button
                  onClick={() => {
                    setShowRejectModal(true);
                  }}
                  className="w-full sm:w-auto flex items-center justify-center gap-2 px-4 py-2 bg-red-600 dark:bg-red-500 text-white rounded-lg hover:bg-red-700 dark:hover:bg-red-600 transition-all active:scale-95 touch-manipulation"
                  disabled={rejectMutation.isPending}
                >
                  <UserX className="h-4 w-4" />
                  <span className="text-sm">{t('signup:review.modal.reject')}</span>
                </button>
                <button
                  onClick={() => approveMutation.mutate(selectedAccount)}
                  className="w-full sm:w-auto flex items-center justify-center gap-2 px-4 py-2 bg-green-600 dark:bg-green-500 text-white rounded-lg hover:bg-green-700 dark:hover:bg-green-600 transition-all active:scale-95 touch-manipulation"
                  disabled={approveMutation.isPending}
                >
                  <UserCheck className="h-4 w-4" />
                  <span className="text-sm">{approveMutation.isPending ? t('signup:review.modal.approving') : t('signup:review.modal.approve')}</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Reject Modal */}
      {showRejectModal && selectedAccount && (
        <div className="fixed inset-0 bg-black dark:bg-black bg-opacity-50 dark:bg-opacity-70 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg max-w-md w-full mx-4 border border-gray-200 dark:border-gray-700">
            <div className="px-4 sm:px-6 py-3 sm:py-4 border-b border-gray-200 dark:border-gray-700">
              <h2 className="text-lg sm:text-xl font-bold text-gray-900 dark:text-white">{t('signup:review.reject.title')}</h2>
            </div>
            <div className="p-4 sm:p-6 space-y-4">
              <p className="text-sm sm:text-base text-gray-600 dark:text-gray-400">
                {t('signup:review.reject.description')}
              </p>
              <textarea
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg focus:ring-red-500 dark:focus:ring-red-400 focus:border-red-500 dark:focus:border-red-400 text-sm transition-colors"
                rows={4}
                placeholder={t('signup:review.reject.reasonPlaceholder')}
                required
              />
              <div className="flex flex-col-reverse sm:flex-row justify-end gap-2 sm:gap-4">
                <button
                  onClick={() => {
                    setShowRejectModal(false);
                    setRejectReason('');
                  }}
                  className="w-full sm:w-auto px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-600 transition-all active:scale-95 touch-manipulation text-sm"
                >
                  {t('signup:review.reject.cancel')}
                </button>
                <button
                  onClick={() => {
                    if (rejectReason.length < 10) {
                      alert(t('signup:review.reject.minLength'));
                      return;
                    }
                    rejectMutation.mutate(selectedAccount);
                  }}
                  className="w-full sm:w-auto px-4 py-2 bg-red-600 dark:bg-red-500 text-white rounded-lg hover:bg-red-700 dark:hover:bg-red-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all active:scale-95 touch-manipulation text-sm"
                  disabled={rejectMutation.isPending || rejectReason.length < 10}
                >
                  {rejectMutation.isPending ? t('signup:review.reject.rejecting') : t('signup:review.reject.confirm')}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TenantReview;
