import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  CheckCircle, ArrowRight, Mail, Phone, BookOpen,
  Settings, Store, Leaf
} from 'lucide-react';
import { useTranslation } from 'react-i18next';

interface LocationState {
  tenantName: string;
  tenantCode: string;
}

const SignupSuccess = () => {
  const { t } = useTranslation(['signup', 'common']);
  const location = useLocation();
  const state = location.state as LocationState;

  const tenantName = state?.tenantName || 'your business';
  const tenantCode = state?.tenantCode || 'your-store';

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 transition-colors">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center py-4 sm:py-6">
            <Leaf className="h-7 w-7 sm:h-8 sm:w-8 text-primary-600 dark:text-primary-400" />
            <span className="ml-2 text-xl sm:text-2xl font-bold text-gray-900 dark:text-white">WeedGo</span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 py-8 sm:py-12">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm p-6 sm:p-8 text-center transition-colors">
            {/* Success Icon */}
            <div className="mx-auto flex items-center justify-center h-14 w-14 sm:h-16 sm:w-16 rounded-full bg-primary-100 dark:bg-primary-900/30 mb-4 sm:mb-6">
              <CheckCircle className="h-7 w-7 sm:h-8 sm:w-8 text-primary-600 dark:text-primary-400" />
            </div>

            {/* Success Message */}
            <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white mb-3 sm:mb-4">
              {t('signup:success.title')}
            </h1>
            <p className="text-lg sm:text-xl text-gray-600 dark:text-gray-300 mb-6 sm:mb-8">
              {t('signup:success.description', { tenantName })}
            </p>

            {/* Account Details */}
            <div className="bg-primary-50 dark:bg-primary-900/20 border border-green-200 dark:border-green-700/50 rounded-lg p-4 sm:p-6 mb-6 sm:mb-8 transition-colors">
              <h3 className="font-semibold text-primary-900 dark:text-primary-300 mb-3 sm:mb-4 text-sm sm:text-base">{t('signup:success.accountDetails.title')}</h3>
              <div className="space-y-2 text-xs sm:text-sm">
                <div className="flex flex-col sm:flex-row sm:justify-between gap-1 sm:gap-0">
                  <span className="text-primary-700 dark:text-primary-400">{t('signup:success.accountDetails.tenantName')}</span>
                  <span className="font-medium text-primary-900 dark:text-primary-200">{tenantName}</span>
                </div>
                <div className="flex flex-col sm:flex-row sm:justify-between gap-1 sm:gap-0">
                  <span className="text-primary-700 dark:text-primary-400">{t('signup:success.accountDetails.tenantCode')}</span>
                  <span className="font-medium text-primary-900 dark:text-primary-200">{tenantCode}</span>
                </div>
                <div className="flex flex-col sm:flex-row sm:justify-between gap-1 sm:gap-0">
                  <span className="text-primary-700 dark:text-primary-400">{t('signup:success.accountDetails.storeUrl')}</span>
                  <span className="font-medium text-primary-900 dark:text-primary-200 break-all">{tenantCode.toLowerCase()}.weedgo.com</span>
                </div>
              </div>
            </div>

            {/* Next Steps */}
            <div className="text-left mb-6 sm:mb-8">
              <h2 className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-white mb-4 sm:mb-6">{t('signup:success.nextSteps.title')}</h2>

              <div className="space-y-3 sm:space-y-4">
                <div className="flex items-start p-4 sm:p-6 bg-gray-50 dark:bg-gray-700/50 rounded-lg transition-colors">
                  <div className="flex items-center justify-center w-7 h-7 sm:w-8 sm:h-8 rounded-full bg-primary-600 dark:bg-primary-500 text-white text-xs sm:text-sm font-medium mr-3 sm:mr-4 mt-0.5 flex-shrink-0">
                    1
                  </div>
                  <div className="min-w-0">
                    <h3 className="font-medium text-gray-900 dark:text-white mb-1 text-sm sm:text-base">{t('signup:success.nextSteps.checkEmail.title')}</h3>
                    <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-300">
                      {t('signup:success.nextSteps.checkEmail.description')}
                    </p>
                  </div>
                </div>

                <div className="flex items-start p-4 sm:p-6 bg-gray-50 dark:bg-gray-700/50 rounded-lg transition-colors">
                  <div className="flex items-center justify-center w-7 h-7 sm:w-8 sm:h-8 rounded-full bg-primary-600 dark:bg-primary-500 text-white text-xs sm:text-sm font-medium mr-3 sm:mr-4 mt-0.5 flex-shrink-0">
                    2
                  </div>
                  <div className="min-w-0">
                    <h3 className="font-medium text-gray-900 dark:text-white mb-1 text-sm sm:text-base">{t('signup:success.nextSteps.accessDashboard.title')}</h3>
                    <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-300">
                      {t('signup:success.nextSteps.accessDashboard.description')}
                    </p>
                  </div>
                </div>

                <div className="flex items-start p-4 sm:p-6 bg-gray-50 dark:bg-gray-700/50 rounded-lg transition-colors">
                  <div className="flex items-center justify-center w-7 h-7 sm:w-8 sm:h-8 rounded-full bg-primary-600 dark:bg-primary-500 text-white text-xs sm:text-sm font-medium mr-3 sm:mr-4 mt-0.5 flex-shrink-0">
                    3
                  </div>
                  <div className="min-w-0">
                    <h3 className="font-medium text-gray-900 dark:text-white mb-1 text-sm sm:text-base">{t('signup:success.nextSteps.setupStore.title')}</h3>
                    <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-300">
                      {t('signup:success.nextSteps.setupStore.description')}
                    </p>
                  </div>
                </div>

                <div className="flex items-start p-4 sm:p-6 bg-gray-50 dark:bg-gray-700/50 rounded-lg transition-colors">
                  <div className="flex items-center justify-center w-7 h-7 sm:w-8 sm:h-8 rounded-full bg-primary-600 dark:bg-primary-500 text-white text-xs sm:text-sm font-medium mr-3 sm:mr-4 mt-0.5 flex-shrink-0">
                    4
                  </div>
                  <div className="min-w-0">
                    <h3 className="font-medium text-gray-900 dark:text-white mb-1 text-sm sm:text-base">{t('signup:success.nextSteps.configureAI.title')}</h3>
                    <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-300">
                      {t('signup:success.nextSteps.configureAI.description')}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4 lg:gap-6 mb-6 sm:mb-8">
              <Link
                to="/login"
                className="flex flex-col items-center p-4 sm:p-6 border border-gray-200 dark:border-gray-600 rounded-lg hover:border-primary-300 dark:hover:border-primary-500 hover:bg-primary-50 dark:hover:bg-primary-900/20 transition-all active:scale-95 touch-manipulation"
              >
                <Settings className="h-7 w-7 sm:h-8 sm:w-8 text-primary-600 dark:text-primary-400 mb-2 flex-shrink-0" />
                <span className="font-medium text-gray-900 dark:text-white text-sm sm:text-base text-center">{t('signup:success.quickActions.dashboard.title')}</span>
                <span className="text-xs sm:text-sm text-gray-500 dark:text-gray-400 text-center">{t('signup:success.quickActions.dashboard.description')}</span>
              </Link>

              <a
                href="#"
                className="flex flex-col items-center p-4 sm:p-6 border border-gray-200 dark:border-gray-600 rounded-lg hover:border-primary-300 dark:hover:border-primary-500 hover:bg-primary-50 dark:hover:bg-primary-900/20 transition-all active:scale-95 touch-manipulation"
              >
                <BookOpen className="h-7 w-7 sm:h-8 sm:w-8 text-primary-600 dark:text-primary-400 mb-2 flex-shrink-0" />
                <span className="font-medium text-gray-900 dark:text-white text-sm sm:text-base text-center">{t('signup:success.quickActions.documentation.title')}</span>
                <span className="text-xs sm:text-sm text-gray-500 dark:text-gray-400 text-center">{t('signup:success.quickActions.documentation.description')}</span>
              </a>

              <a
                href="#"
                className="flex flex-col items-center p-4 sm:p-6 border border-gray-200 dark:border-gray-600 rounded-lg hover:border-primary-300 dark:hover:border-primary-500 hover:bg-primary-50 dark:hover:bg-primary-900/20 transition-all active:scale-95 touch-manipulation"
              >
                <Phone className="h-7 w-7 sm:h-8 sm:w-8 text-primary-600 dark:text-primary-400 mb-2 flex-shrink-0" />
                <span className="font-medium text-gray-900 dark:text-white text-sm sm:text-base text-center">{t('signup:success.quickActions.support.title')}</span>
                <span className="text-xs sm:text-sm text-gray-500 dark:text-gray-400 text-center">{t('signup:success.quickActions.support.description')}</span>
              </a>
            </div>

            {/* Primary CTA */}
            <div className="space-y-3 sm:space-y-4">
              <Link
                to="/login"
                className="inline-flex items-center justify-center w-full sm:w-auto px-6 sm:px-8 py-3 sm:py-4 bg-primary-600 dark:bg-primary-500 text-white rounded-lg font-semibold hover:bg-primary-700 dark:hover:bg-primary-600 transition-all active:scale-95 touch-manipulation text-sm sm:text-base"
              >
                {t('signup:success.cta.button')}
                <ArrowRight className="ml-2 h-4 w-4 sm:h-5 sm:w-5 flex-shrink-0" />
              </Link>

              <div className="text-xs sm:text-sm text-gray-500 dark:text-gray-400">
                {t('signup:success.cta.help')}{' '}
                <a href={`mailto:${t('signup:success.cta.email')}`} className="text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 transition-colors">
                  {t('signup:success.cta.email')}
                </a>
              </div>
            </div>
          </div>

          {/* Additional Resources */}
          <div className="mt-6 sm:mt-8 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-sm p-4 sm:p-6 transition-colors">
            <h3 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-white mb-3 sm:mb-4">{t('signup:success.resources.title')}</h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6">
              <div>
                <h4 className="font-medium text-gray-900 dark:text-white mb-2 text-sm sm:text-base">{t('signup:success.resources.quickSetup.title')}</h4>
                <ul className="text-xs sm:text-sm text-gray-600 dark:text-gray-300 space-y-1">
                  <li>• {t('signup:success.resources.quickSetup.item1')}</li>
                  <li>• {t('signup:success.resources.quickSetup.item2')}</li>
                  <li>• {t('signup:success.resources.quickSetup.item3')}</li>
                  <li>• {t('signup:success.resources.quickSetup.item4')}</li>
                </ul>
              </div>

              <div>
                <h4 className="font-medium text-gray-900 dark:text-white mb-2 text-sm sm:text-base">{t('signup:success.resources.training.title')}</h4>
                <ul className="text-xs sm:text-sm text-gray-600 dark:text-gray-300 space-y-1">
                  <li>• {t('signup:success.resources.training.item1')}</li>
                  <li>• {t('signup:success.resources.training.item2')}</li>
                  <li>• {t('signup:success.resources.training.item3')}</li>
                  <li>• {t('signup:success.resources.training.item4')}</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SignupSuccess;