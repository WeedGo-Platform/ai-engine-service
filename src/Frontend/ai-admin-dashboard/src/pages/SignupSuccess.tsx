import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  CheckCircle, ArrowRight, Mail, Phone, BookOpen, 
  Settings, Store, Leaf 
} from 'lucide-react';

interface LocationState {
  tenantName: string;
  tenantCode: string;
}

const SignupSuccess = () => {
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
              Welcome to WeedGo!
            </h1>
            <p className="text-xl text-gray-600 mb-8">
              Your account for <span className="font-semibold text-primary-600">{tenantName}</span> has been successfully created.
            </p>

            {/* Account Details */}
            <div className="bg-primary-50 border border-green-200 rounded-lg p-6 mb-8">
              <h3 className="font-semibold text-primary-900 mb-4">Your Account Details</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-primary-700">Tenant Name:</span>
                  <span className="font-medium text-primary-900">{tenantName}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-primary-700">Tenant Code:</span>
                  <span className="font-medium text-primary-900">{tenantCode}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-primary-700">Store URL:</span>
                  <span className="font-medium text-primary-900">{tenantCode.toLowerCase()}.weedgo.com</span>
                </div>
              </div>
            </div>

            {/* Next Steps */}
            <div className="text-left mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-6">Next Steps</h2>
              
              <div className="space-y-4">
                <div className="flex items-start p-6 bg-gray-50 rounded-lg">
                  <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary-600 text-white text-sm font-medium mr-4 mt-0.5">
                    1
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900 mb-1">Check Your Email</h3>
                    <p className="text-sm text-gray-600">
                      We've sent you a welcome email with important account information and setup instructions.
                    </p>
                  </div>
                </div>

                <div className="flex items-start p-6 bg-gray-50 rounded-lg">
                  <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary-600 text-white text-sm font-medium mr-4 mt-0.5">
                    2
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900 mb-1">Access Your Dashboard</h3>
                    <p className="text-sm text-gray-600">
                      Log in to your admin dashboard to configure your store settings, add products, and customize your AI assistants.
                    </p>
                  </div>
                </div>

                <div className="flex items-start p-6 bg-gray-50 rounded-lg">
                  <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary-600 text-white text-sm font-medium mr-4 mt-0.5">
                    3
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900 mb-1">Setup Your First Store</h3>
                    <p className="text-sm text-gray-600">
                      Add your first store location, configure operating hours, and set up your product inventory.
                    </p>
                  </div>
                </div>

                <div className="flex items-start p-6 bg-gray-50 rounded-lg">
                  <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary-600 text-white text-sm font-medium mr-4 mt-0.5">
                    4
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900 mb-1">Configure AI Assistants</h3>
                    <p className="text-sm text-gray-600">
                      Customize your AI budtender personalities and set up multi-language support for your customers.
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
                <span className="font-medium text-gray-900">Access Dashboard</span>
                <span className="text-sm text-gray-500">Configure your platform</span>
              </Link>

              <a
                href="#"
                className="flex flex-col items-center p-6 border border-gray-200 rounded-lg hover:border-primary-300 hover:bg-primary-50 transition-colors"
              >
                <BookOpen className="h-8 w-8 text-primary-600 mb-2" />
                <span className="font-medium text-gray-900">Documentation</span>
                <span className="text-sm text-gray-500">Setup guides & tutorials</span>
              </a>

              <a
                href="#"
                className="flex flex-col items-center p-6 border border-gray-200 rounded-lg hover:border-primary-300 hover:bg-primary-50 transition-colors"
              >
                <Phone className="h-8 w-8 text-primary-600 mb-2" />
                <span className="font-medium text-gray-900">Support</span>
                <span className="text-sm text-gray-500">Get help from our team</span>
              </a>
            </div>

            {/* Primary CTA */}
            <div className="space-y-4">
              <Link
                to="/login"
                className="inline-flex items-center px-8 py-4 bg-primary-600 text-white rounded-lg font-semibold hover:bg-primary-700 transition-colors"
              >
                Access Your Dashboard
                <ArrowRight className="ml-2 h-5 w-5" />
              </Link>
              
              <div className="text-sm text-gray-500">
                Need help getting started? Contact our support team at{' '}
                <a href="mailto:support@weedgo.com" className="text-primary-600 hover:text-primary-700">
                  support@weedgo.com
                </a>
              </div>
            </div>
          </div>

          {/* Additional Resources */}
          <div className="mt-8 bg-white rounded-xl  p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Resources to Get You Started</h3>
            
            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-medium text-gray-900 mb-2">Quick Setup Guide</h4>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>• Store configuration and branding</li>
                  <li>• Product catalog setup</li>
                  <li>• Payment processing configuration</li>
                  <li>• AI assistant customization</li>
                </ul>
              </div>
              
              <div>
                <h4 className="font-medium text-gray-900 mb-2">Training & Support</h4>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>• Video tutorials and webinars</li>
                  <li>• 24/7 customer support chat</li>
                  <li>• Community forum access</li>
                  <li>• Dedicated account manager (Enterprise)</li>
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