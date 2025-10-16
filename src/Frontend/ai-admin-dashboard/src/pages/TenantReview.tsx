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
          <AlertCircle className="h-12 w-12 text-yellow-500 mx-auto mb-4" />
          <p className="text-gray-600">{t('signup:review.messages.noPermission')}</p>
        </div>
      </div>
    );
  }

  if (accountsLoading || statsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{t('signup:review.title')}</h1>
          <p className="text-sm text-gray-500 mt-1">
            {t('signup:review.description')}
          </p>
        </div>
        <button
          onClick={() => queryClient.invalidateQueries({ queryKey: ['pending-accounts'] })}
          className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
        >
          <RefreshCw className="h-4 w-4" />
          {t('signup:review.refresh')}
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg p-6 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">{t('signup:review.stats.totalPending')}</p>
              <p className="text-2xl font-bold text-gray-900">
                {stats?.total_pending || 0}
              </p>
            </div>
            <Clock className="h-8 w-8 text-yellow-600" />
          </div>
        </div>

        <div className="bg-white rounded-lg p-6 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">{t('signup:review.stats.thisWeek')}</p>
              <p className="text-2xl font-bold text-gray-900">
                {stats?.pending_this_week || 0}
              </p>
            </div>
            <TrendingUp className="h-8 w-8 text-blue-600" />
          </div>
        </div>

        <div className="bg-white rounded-lg p-6 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">{t('signup:review.stats.avgReviewTime')}</p>
              <p className="text-2xl font-bold text-gray-900">
                {stats?.avg_review_time_hours || 0}h
              </p>
            </div>
            <Clock className="h-8 w-8 text-purple-600" />
          </div>
        </div>

        <div className="bg-white rounded-lg p-6 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">{t('signup:review.stats.approvalRate')}</p>
              <p className="text-2xl font-bold text-gray-900">
                {stats?.approval_rate || 0}%
              </p>
            </div>
            <CheckCircle className="h-8 w-8 text-green-600" />
          </div>
        </div>
      </div>

      {/* Pending Accounts List */}
      <div className="bg-white rounded-lg shadow-sm">
        <div className="px-6 py-4 border-b">
          <h2 className="text-lg font-semibold">{t('signup:review.table.title')}</h2>
        </div>

        {pendingAccounts && pendingAccounts.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    {t('signup:review.table.storeName')}
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    {t('signup:review.table.contact')}
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    {t('signup:review.table.licenseNumber')}
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    {t('signup:review.table.submitted')}
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    {t('signup:review.table.tier')}
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    {t('signup:review.table.actions')}
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {pendingAccounts.map((account) => (
                  <tr key={account.tenant_id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <Building className="h-5 w-5 text-gray-400 mr-2" />
                        <div>
                          <div className="text-sm font-medium text-gray-900">
                            {account.store_name}
                          </div>
                          <div className="text-xs text-gray-500">
                            {account.tenant_code}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{account.contact_name}</div>
                      <div className="text-xs text-gray-500">{account.contact_email}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {account.license_number}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(account.submitted_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        account.verification_tier === 'auto_approved'
                          ? 'bg-green-100 text-green-800'
                          : 'bg-yellow-100 text-yellow-800'
                      }`}>
                        {account.verification_tier}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <button
                        onClick={() => setSelectedAccount(account.tenant_id)}
                        className="text-primary-600 hover:text-primary-900"
                      >
                        {t('signup:review.table.review')}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="p-12 text-center">
            <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
            <p className="text-gray-600">{t('signup:review.table.noPending')}</p>
          </div>
        )}
      </div>

      {/* Account Detail Modal */}
      {selectedAccount && accountDetail && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            {/* Modal Header */}
            <div className="px-6 py-4 border-b flex justify-between items-center">
              <h2 className="text-xl font-bold">{t('signup:review.modal.title')}</h2>
              <button
                onClick={() => setSelectedAccount(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                <XCircle className="h-6 w-6" />
              </button>
            </div>

            {/* Modal Content */}
            <div className="p-6 space-y-6">
              {/* Store Information */}
              <div>
                <h3 className="text-lg font-semibold mb-4 flex items-center">
                  <Building className="h-5 w-5 mr-2" />
                  {t('signup:review.modal.storeInfo')}
                </h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium text-gray-600">{t('signup:review.modal.storeName')}</label>
                    <p className="text-gray-900">{accountDetail.store_name}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-600">{t('signup:review.modal.licenseNumber')}</label>
                    <p className="text-gray-900">{accountDetail.license_number}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-600">{t('signup:review.modal.crsaAddress')}</label>
                    <p className="text-gray-900">{accountDetail.crsa_address}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-600">{t('signup:review.modal.municipality')}</label>
                    <p className="text-gray-900">{accountDetail.crsa_municipality || 'N/A'}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-600">{t('signup:review.modal.crsaStatus')}</label>
                    <p className="text-gray-900">{accountDetail.crsa_store_status}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-600">{t('signup:review.modal.crsaWebsite')}</label>
                    <p className="text-gray-900">{accountDetail.crsa_website || 'N/A'}</p>
                  </div>
                </div>
              </div>

              {/* Contact Information */}
              <div>
                <h3 className="text-lg font-semibold mb-4 flex items-center">
                  <Mail className="h-5 w-5 mr-2" />
                  {t('signup:review.modal.contactInfo')}
                </h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium text-gray-600">{t('signup:review.modal.contactName')}</label>
                    <p className="text-gray-900">{accountDetail.contact_name}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-600">{t('signup:review.modal.role')}</label>
                    <p className="text-gray-900">{accountDetail.contact_role}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-600">{t('signup:review.modal.email')}</label>
                    <p className="text-gray-900">{accountDetail.contact_email}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-600">{t('signup:review.modal.phone')}</label>
                    <p className="text-gray-900">{accountDetail.contact_phone || 'N/A'}</p>
                  </div>
                </div>
              </div>

              {/* Verification Context */}
              <div>
                <h3 className="text-lg font-semibold mb-4 flex items-center">
                  <FileText className="h-5 w-5 mr-2" />
                  {t('signup:review.modal.verificationContext')}
                </h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium text-gray-600">{t('signup:review.modal.emailDomain')}</label>
                    <p className="text-gray-900">{accountDetail.email_domain}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-600">{t('signup:review.modal.domainMatchesCrsa')}</label>
                    <p className={`font-semibold ${accountDetail.domain_matches_crsa ? 'text-green-600' : 'text-yellow-600'}`}>
                      {accountDetail.domain_matches_crsa ? t('signup:review.modal.yes') : t('signup:review.modal.no')}
                    </p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-600">{t('signup:review.modal.verificationTier')}</label>
                    <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
                      accountDetail.verification_tier === 'auto_approved'
                        ? 'bg-green-100 text-green-800'
                        : 'bg-yellow-100 text-yellow-800'
                    }`}>
                      {accountDetail.verification_tier}
                    </span>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-600">{t('signup:review.modal.submitted')}</label>
                    <p className="text-gray-900">
                      {new Date(accountDetail.submitted_at).toLocaleString()}
                    </p>
                  </div>
                </div>
              </div>

              {/* Admin Notes */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('signup:review.modal.adminNotes')}
                </label>
                <textarea
                  value={adminNotes}
                  onChange={(e) => setAdminNotes(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-primary-500 focus:border-primary-500"
                  rows={3}
                  placeholder={t('signup:review.modal.adminNotesPlaceholder')}
                />
              </div>

              {/* Actions */}
              <div className="flex justify-end gap-4 pt-4 border-t">
                <button
                  onClick={() => {
                    setShowRejectModal(true);
                  }}
                  className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
                  disabled={rejectMutation.isPending}
                >
                  <UserX className="h-4 w-4" />
                  {t('signup:review.modal.reject')}
                </button>
                <button
                  onClick={() => approveMutation.mutate(selectedAccount)}
                  className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                  disabled={approveMutation.isPending}
                >
                  <UserCheck className="h-4 w-4" />
                  {approveMutation.isPending ? t('signup:review.modal.approving') : t('signup:review.modal.approve')}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Reject Modal */}
      {showRejectModal && selectedAccount && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg max-w-md w-full mx-4">
            <div className="px-6 py-4 border-b">
              <h2 className="text-xl font-bold">{t('signup:review.reject.title')}</h2>
            </div>
            <div className="p-6 space-y-4">
              <p className="text-gray-600">
                {t('signup:review.reject.description')}
              </p>
              <textarea
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-red-500 focus:border-red-500"
                rows={4}
                placeholder={t('signup:review.reject.reasonPlaceholder')}
                required
              />
              <div className="flex justify-end gap-4">
                <button
                  onClick={() => {
                    setShowRejectModal(false);
                    setRejectReason('');
                  }}
                  className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
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
                  className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
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
