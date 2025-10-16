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
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white ">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center py-6">
            <Leaf className="h-8 w-8 text-primary-600" />
            <span className="ml-2 text-2xl font-bold text-gray-900">WeedGo</span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 py-12">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-white rounded-xl  p-8 text-center">
            {/* Success Icon */}
            <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-primary-100 mb-6">
              <CheckCircle className="h-8 w-8 text-primary-600" />
            </div>

            {/* Success Message */}
            <h1 className="text-3xl font-bold text-gray-900 mb-4">
              {t('signup:success.title')}
            </h1>
            <p className="text-xl text-gray-600 mb-8">
              {t('signup:success.description', { tenantName })}
            </p>

            {/* Account Details */}
            <div className="bg-primary-50 border border-green-200 rounded-lg p-6 mb-8">
              <h3 className="font-semibold text-primary-900 mb-4">{t('signup:success.accountDetails.title')}</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-primary-700">{t('signup:success.accountDetails.tenantName')}</span>
                  <span className="font-medium text-primary-900">{tenantName}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-primary-700">{t('signup:success.accountDetails.tenantCode')}</span>
                  <span className="font-medium text-primary-900">{tenantCode}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-primary-700">{t('signup:success.accountDetails.storeUrl')}</span>
                  <span className="font-medium text-primary-900">{tenantCode.toLowerCase()}.weedgo.com</span>
                </div>
              </div>
            </div>

            {/* Next Steps */}
            <div className="text-left mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-6">{t('signup:success.nextSteps.title')}</h2>

              <div className="space-y-4">
                <div className="flex items-start p-6 bg-gray-50 rounded-lg">
                  <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary-600 text-white text-sm font-medium mr-4 mt-0.5">
                    1
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900 mb-1">{t('signup:success.nextSteps.checkEmail.title')}</h3>
                    <p className="text-sm text-gray-600">
                      {t('signup:success.nextSteps.checkEmail.description')}
                    </p>
                  </div>
                </div>

                <div className="flex items-start p-6 bg-gray-50 rounded-lg">
                  <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary-600 text-white text-sm font-medium mr-4 mt-0.5">
                    2
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900 mb-1">{t('signup:success.nextSteps.accessDashboard.title')}</h3>
                    <p className="text-sm text-gray-600">
                      {t('signup:success.nextSteps.accessDashboard.description')}
                    </p>
                  </div>
                </div>

                <div className="flex items-start p-6 bg-gray-50 rounded-lg">
                  <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary-600 text-white text-sm font-medium mr-4 mt-0.5">
                    3
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900 mb-1">{t('signup:success.nextSteps.setupStore.title')}</h3>
                    <p className="text-sm text-gray-600">
                      {t('signup:success.nextSteps.setupStore.description')}
                    </p>
                  </div>
                </div>

                <div className="flex items-start p-6 bg-gray-50 rounded-lg">
                  <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary-600 text-white text-sm font-medium mr-4 mt-0.5">
                    4
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900 mb-1">{t('signup:success.nextSteps.configureAI.title')}</h3>
                    <p className="text-sm text-gray-600">
                      {t('signup:success.nextSteps.configureAI.description')}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="grid md:grid-cols-3 gap-6 mb-8">
              <Link
                to="/login"
                className="flex flex-col items-center p-6 border border-gray-200 rounded-lg hover:border-primary-300 hover:bg-primary-50 transition-colors"
              >
                <Settings className="h-8 w-8 text-primary-600 mb-2" />
                <span className="font-medium text-gray-900">{t('signup:success.quickActions.dashboard.title')}</span>
                <span className="text-sm text-gray-500">{t('signup:success.quickActions.dashboard.description')}</span>
              </Link>

              <a
                href="#"
                className="flex flex-col items-center p-6 border border-gray-200 rounded-lg hover:border-primary-300 hover:bg-primary-50 transition-colors"
              >
                <BookOpen className="h-8 w-8 text-primary-600 mb-2" />
                <span className="font-medium text-gray-900">{t('signup:success.quickActions.documentation.title')}</span>
                <span className="text-sm text-gray-500">{t('signup:success.quickActions.documentation.description')}</span>
              </a>

              <a
                href="#"
                className="flex flex-col items-center p-6 border border-gray-200 rounded-lg hover:border-primary-300 hover:bg-primary-50 transition-colors"
              >
                <Phone className="h-8 w-8 text-primary-600 mb-2" />
                <span className="font-medium text-gray-900">{t('signup:success.quickActions.support.title')}</span>
                <span className="text-sm text-gray-500">{t('signup:success.quickActions.support.description')}</span>
              </a>
            </div>

            {/* Primary CTA */}
            <div className="space-y-4">
              <Link
                to="/login"
                className="inline-flex items-center px-8 py-4 bg-primary-600 text-white rounded-lg font-semibold hover:bg-primary-700 transition-colors"
              >
                {t('signup:success.cta.button')}
                <ArrowRight className="ml-2 h-5 w-5" />
              </Link>

              <div className="text-sm text-gray-500">
                {t('signup:success.cta.help')}{' '}
                <a href={`mailto:${t('signup:success.cta.email')}`} className="text-primary-600 hover:text-primary-700">
                  {t('signup:success.cta.email')}
                </a>
              </div>
            </div>
          </div>

          {/* Additional Resources */}
          <div className="mt-8 bg-white rounded-xl  p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">{t('signup:success.resources.title')}</h3>

            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-medium text-gray-900 mb-2">{t('signup:success.resources.quickSetup.title')}</h4>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>• {t('signup:success.resources.quickSetup.item1')}</li>
                  <li>• {t('signup:success.resources.quickSetup.item2')}</li>
                  <li>• {t('signup:success.resources.quickSetup.item3')}</li>
                  <li>• {t('signup:success.resources.quickSetup.item4')}</li>
                </ul>
              </div>

              <div>
                <h4 className="font-medium text-gray-900 mb-2">{t('signup:success.resources.training.title')}</h4>
                <ul className="text-sm text-gray-600 space-y-1">
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