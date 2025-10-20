import React, { useState } from 'react';
import { X, Eye, EyeOff, Lock, AlertCircle, CheckCircle } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import authService from '../services/authService';
import toast from 'react-hot-toast';

interface ChangePasswordModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

const ChangePasswordModal: React.FC<ChangePasswordModalProps> = ({
  isOpen,
  onClose,
  onSuccess
}) => {
  const { t } = useTranslation(['common']);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<{ [key: string]: string }>({});

  // Password strength validation
  const validatePassword = (password: string): string[] => {
    const errors: string[] = [];
    if (password.length < 8) errors.push(t('common:modals.changePassword.requirements.minLength'));
    if (!/[A-Z]/.test(password)) errors.push(t('common:modals.changePassword.requirements.uppercase'));
    if (!/[a-z]/.test(password)) errors.push(t('common:modals.changePassword.requirements.lowercase'));
    if (!/[0-9]/.test(password)) errors.push(t('common:modals.changePassword.requirements.number'));
    return errors;
  };

  const passwordErrors = newPassword ? validatePassword(newPassword) : [];
  const isPasswordValid = passwordErrors.length === 0;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Clear previous errors
    setErrors({});

    // Validation
    const newErrors: { [key: string]: string } = {};

    if (!currentPassword) {
      newErrors.currentPassword = t('common:modals.changePassword.validation.currentRequired');
    }

    if (!newPassword) {
      newErrors.newPassword = t('common:modals.changePassword.validation.newRequired');
    } else if (passwordErrors.length > 0) {
      newErrors.newPassword = t('common:modals.changePassword.validation.notMeetRequirements');
    }

    if (!confirmPassword) {
      newErrors.confirmPassword = t('common:modals.changePassword.validation.confirmRequired');
    } else if (newPassword !== confirmPassword) {
      newErrors.confirmPassword = t('common:modals.changePassword.validation.notMatch');
    }

    if (currentPassword && newPassword && currentPassword === newPassword) {
      newErrors.newPassword = t('common:modals.changePassword.validation.mustBeDifferent');
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setLoading(true);

    try {
      await authService.changePassword(currentPassword, newPassword);

      toast.success(t('common:toasts.password.changeSuccess'));

      // Clear form
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      setErrors({});

      // Close modal
      onClose();

      // Call success callback
      if (onSuccess) {
        onSuccess();
      }

      // Logout after short delay to allow user to see success message
      setTimeout(async () => {
        await authService.logout();
        window.location.href = '/login';
      }, 1500);

    } catch (error: any) {
      console.error('Password change error:', error);

      if (error.response?.status === 401) {
        setErrors({ currentPassword: t('common:modals.changePassword.validation.incorrectCurrent') });
      } else if (error.response?.data?.detail) {
        // Handle Pydantic validation errors
        const detail = error.response.data.detail;
        if (Array.isArray(detail)) {
          const fieldErrors: { [key: string]: string } = {};
          detail.forEach((err: any) => {
            const field = err.loc[err.loc.length - 1];
            fieldErrors[field] = err.msg;
          });
          setErrors(fieldErrors);
        } else {
          toast.error(detail);
        }
      } else {
        toast.error(t('common:toasts.password.changeFailed'));
      }
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (!loading) {
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      setErrors({});
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-md mx-4">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-primary-100 dark:bg-primary-900 rounded-lg">
              <Lock className="h-5 w-5 text-primary-600 dark:text-primary-400" />
            </div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">{t('common:modals.changePassword.title')}</h2>
          </div>
          <button
            onClick={handleClose}
            disabled={loading}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Current Password */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              {t('common:modals.changePassword.currentPassword')}
            </label>
            <div className="relative">
              <input
                type={showCurrentPassword ? 'text' : 'password'}
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                disabled={loading}
                className={`w-full px-3 py-2 border ${
                  errors.currentPassword ? 'border-red-300 dark:border-red-600' : 'border-gray-300 dark:border-gray-600'
                } rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 pr-10 bg-white dark:bg-gray-700 text-gray-900 dark:text-white dark:placeholder-gray-400`}
                placeholder={t('common:modals.changePassword.placeholders.currentPassword')}
              />
              <button
                type="button"
                onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                {showCurrentPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
              </button>
            </div>
            {errors.currentPassword && (
              <p className="mt-1 text-sm text-red-600 flex items-center gap-1">
                <AlertCircle className="h-4 w-4" />
                {errors.currentPassword}
              </p>
            )}
          </div>

          {/* New Password */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              {t('common:modals.changePassword.newPassword')}
            </label>
            <div className="relative">
              <input
                type={showNewPassword ? 'text' : 'password'}
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                disabled={loading}
                className={`w-full px-3 py-2 border ${
                  errors.newPassword ? 'border-red-300 dark:border-red-600' : 'border-gray-300 dark:border-gray-600'
                } rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 pr-10 bg-white dark:bg-gray-700 text-gray-900 dark:text-white dark:placeholder-gray-400`}
                placeholder={t('common:modals.changePassword.placeholders.newPassword')}
              />
              <button
                type="button"
                onClick={() => setShowNewPassword(!showNewPassword)}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                {showNewPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
              </button>
            </div>
            {errors.newPassword && (
              <p className="mt-1 text-sm text-red-600 flex items-center gap-1">
                <AlertCircle className="h-4 w-4" />
                {errors.newPassword}
              </p>
            )}

            {/* Password strength requirements */}
            {newPassword && (
              <div className="mt-2 space-y-1">
                <p className="text-xs font-medium text-gray-700 dark:text-gray-300">{t('common:modals.changePassword.requirements.title')}</p>
                {[
                  t('common:modals.changePassword.requirements.minLength'),
                  t('common:modals.changePassword.requirements.uppercase'),
                  t('common:modals.changePassword.requirements.lowercase'),
                  t('common:modals.changePassword.requirements.number')
                ].map((requirement, index) => {
                  const isMet = !passwordErrors.includes(requirement);
                  return (
                    <div key={index} className="flex items-center gap-1 text-xs">
                      {isMet ? (
                        <CheckCircle className="h-3 w-3 text-green-500 dark:text-green-400" />
                      ) : (
                        <AlertCircle className="h-3 w-3 text-gray-400 dark:text-gray-500" />
                      )}
                      <span className={isMet ? 'text-green-600 dark:text-green-400' : 'text-gray-500 dark:text-gray-400'}>
                        {requirement}
                      </span>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Confirm Password */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              {t('common:modals.changePassword.confirmPassword')}
            </label>
            <div className="relative">
              <input
                type={showConfirmPassword ? 'text' : 'password'}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                disabled={loading}
                className={`w-full px-3 py-2 border ${
                  errors.confirmPassword ? 'border-red-300 dark:border-red-600' : 'border-gray-300 dark:border-gray-600'
                } rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 pr-10 bg-white dark:bg-gray-700 text-gray-900 dark:text-white dark:placeholder-gray-400`}
                placeholder={t('common:modals.changePassword.placeholders.confirmPassword')}
              />
              <button
                type="button"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                {showConfirmPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
              </button>
            </div>
            {errors.confirmPassword && (
              <p className="mt-1 text-sm text-red-600 flex items-center gap-1">
                <AlertCircle className="h-4 w-4" />
                {errors.confirmPassword}
              </p>
            )}
          </div>

          {/* Security Notice */}
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
            <p className="text-xs text-blue-800 dark:text-blue-300">
              <strong>Security Notice:</strong> {t('common:modals.changePassword.securityNotice')}
            </p>
          </div>

          {/* Buttons */}
          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={handleClose}
              disabled={loading}
              className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {t('common:buttons.cancel')}
            </button>
            <button
              type="submit"
              disabled={loading || !currentPassword || !newPassword || !confirmPassword || !isPasswordValid}
              className="flex-1 px-4 py-2 bg-primary-600 dark:bg-primary-700 text-white rounded-lg hover:bg-primary-700 dark:hover:bg-primary-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <div className="h-4 w-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  {t('common:modals.changePassword.changing')}
                </>
              ) : (
                t('common:modals.changePassword.title')
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ChangePasswordModal;
