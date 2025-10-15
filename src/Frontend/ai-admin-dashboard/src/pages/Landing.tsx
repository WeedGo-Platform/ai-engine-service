import React from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  ArrowRight, CheckCircle, Star, Users, TrendingUp,
  Shield, Zap, Globe, Mic, ShoppingCart, CreditCard,
  Leaf, Building2, Store, Languages, Bot, Search,
  BarChart3, Truck, Tablet, Smartphone, Monitor,
  Cloud, Database, Activity, Layers, Palette, FileCheck,
  Target, Brain, Headphones, Settings, Lock, CheckSquare
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import SalesChatWidget from '../components/SalesChatWidget';
import LanguageSelector from '../components/LanguageSelector';

const Landing = () => {
  const { user } = useAuth();
  const { t } = useTranslation('landing');

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="bg-white ">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <Leaf className="h-8 w-8 text-primary-600" />
              <span className="ml-2 text-2xl font-bold text-gray-900">WeedGo</span>
            </div>
            <nav className="hidden md:flex space-x-8 items-center">
              <a href="#features" className="text-gray-500 hover:text-gray-900">{t('header.nav.features')}</a>
              <a href="#pricing" className="text-gray-500 hover:text-gray-900">{t('header.nav.pricing')}</a>
              <a href="#testimonials" className="text-gray-500 hover:text-gray-900">{t('header.nav.testimonials')}</a>
              <Link to="/login" className="text-gray-500 hover:text-gray-900">{t('header.nav.login')}</Link>
              <LanguageSelector />
            </nav>
            <Link
              to="/signup"
              className="bg-primary-600 text-white px-6 py-2 rounded-lg hover:bg-primary-700 transition-colors"
            >
              {t('header.getStarted')}
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="bg-gradient-to-br from-green-50 to-emerald-100 py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-8">
              {t('hero.title')}
              <span className="block text-primary-600">{t('hero.titleHighlight')}</span>
            </h1>
            <p className="text-xl text-gray-600 mb-10 max-w-3xl mx-auto">
              {t('hero.subtitle')}
            </p>
            <div className="flex flex-col sm:flex-row gap-6 justify-center">
              <Link
                to="/signup"
                className="bg-primary-600 text-white px-8 py-4 rounded-lg font-semibold hover:bg-primary-700 transition-colors inline-flex items-center"
              >
                {t('hero.startTrial')} <ArrowRight className="ml-2 h-5 w-5" />
              </Link>
              <a
                href="#features"
                className="border border-primary-600 text-primary-600 px-8 py-4 rounded-lg font-semibold hover:bg-primary-50 transition-colors"
              >
                {t('hero.learnMore')}
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-16 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
            <div>
              <div className="text-3xl font-bold text-primary-600">5,540+</div>
              <div className="text-gray-600">{t('stats.products')}</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-primary-600">25+</div>
              <div className="text-gray-600">{t('stats.languages')}</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-primary-600">99.9%</div>
              <div className="text-gray-600">{t('stats.uptime')}</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-primary-600">24/7</div>
              <div className="text-gray-600">{t('stats.support')}</div>
            </div>
          </div>
        </div>
      </section>

      {/* Key Features */}
      <section id="features" className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              {t('features.heading')}
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              {t('features.subheading')}
              <strong className="text-primary-600">{t('features.subheadingHighlight')}</strong>.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* AI-Powered Customer Experience */}
            <div className="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow">
              <Bot className="h-12 w-12 text-primary-600 mb-4" />
              <h3 className="text-xl font-semibold mb-2">{t('features.aiBudtender.title')}</h3>
              <p className="text-gray-600">{t('features.aiBudtender.description')}</p>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow">
              <Mic className="h-12 w-12 text-primary-600 mb-4" />
              <h3 className="text-xl font-semibold mb-2">{t('features.voiceShopping.title')}</h3>
              <p className="text-gray-600">{t('features.voiceShopping.description')}</p>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow">
              <Brain className="h-12 w-12 text-primary-600 mb-4" />
              <h3 className="text-xl font-semibold mb-2">{t('features.predictiveIntelligence.title')}</h3>
              <p className="text-gray-600">{t('features.predictiveIntelligence.description')}</p>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow">
              <Target className="h-12 w-12 text-primary-600 mb-4" />
              <h3 className="text-xl font-semibold mb-2">{t('features.smartRecommendations.title')}</h3>
              <p className="text-gray-600">{t('features.smartRecommendations.description')}</p>
            </div>

            {/* Multi-Channel Commerce */}
            <div className="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow">
              <Monitor className="h-12 w-12 text-primary-600 mb-4" />
              <h3 className="text-xl font-semibold mb-2">{t('features.unifiedCommerce.title')}</h3>
              <p className="text-gray-600">{t('features.unifiedCommerce.description')}</p>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow">
              <Smartphone className="h-12 w-12 text-primary-600 mb-4" />
              <h3 className="text-xl font-semibold mb-2">{t('features.brandedMobileApps.title')}</h3>
              <p className="text-gray-600">{t('features.brandedMobileApps.description')}</p>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow">
              <Tablet className="h-12 w-12 text-primary-600 mb-4" />
              <h3 className="text-xl font-semibold mb-2">{t('features.selfServiceKiosks.title')}</h3>
              <p className="text-gray-600">{t('features.selfServiceKiosks.description')}</p>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow">
              <Truck className="h-12 w-12 text-primary-600 mb-4" />
              <h3 className="text-xl font-semibold mb-2">{t('features.deliveryEcosystem.title')}</h3>
              <p className="text-gray-600">{t('features.deliveryEcosystem.description')}</p>
            </div>

            {/* Global Reach */}
            <div className="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow">
              <Languages className="h-12 w-12 text-primary-600 mb-4" />
              <h3 className="text-xl font-semibold mb-2">{t('features.multiLanguage.title')}</h3>
              <p className="text-gray-600">{t('features.multiLanguage.description')}</p>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow">
              <Globe className="h-12 w-12 text-primary-600 mb-4" />
              <h3 className="text-xl font-semibold mb-2">{t('features.seoOptimization.title')}</h3>
              <p className="text-gray-600">{t('features.seoOptimization.description')}</p>
            </div>

            {/* Security & Compliance */}
            <div className="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow">
              <Shield className="h-12 w-12 text-primary-600 mb-4" />
              <h3 className="text-xl font-semibold mb-2">{t('features.fraudProtection.title')}</h3>
              <p className="text-gray-600">{t('features.fraudProtection.description')}</p>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow">
              <CheckSquare className="h-12 w-12 text-primary-600 mb-4" />
              <h3 className="text-xl font-semibold mb-2">{t('features.complianceAutopilot.title')}</h3>
              <p className="text-gray-600">{t('features.complianceAutopilot.description')}</p>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow">
              <Lock className="h-12 w-12 text-primary-600 mb-4" />
              <h3 className="text-xl font-semibold mb-2">{t('features.ageVerification.title')}</h3>
              <p className="text-gray-600">{t('features.ageVerification.description')}</p>
            </div>

            {/* Business Operations */}
            <div className="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow">
              <BarChart3 className="h-12 w-12 text-primary-600 mb-4" />
              <h3 className="text-xl font-semibold mb-2">{t('features.businessIntelligence.title')}</h3>
              <p className="text-gray-600">{t('features.businessIntelligence.description')}</p>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow">
              <Store className="h-12 w-12 text-primary-600 mb-4" />
              <h3 className="text-xl font-semibold mb-2">{t('features.multiLocation.title')}</h3>
              <p className="text-gray-600">{t('features.multiLocation.description')}</p>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow">
              <Users className="h-12 w-12 text-primary-600 mb-4" />
              <h3 className="text-xl font-semibold mb-2">{t('features.customerLoyalty.title')}</h3>
              <p className="text-gray-600">{t('features.customerLoyalty.description')}</p>
            </div>

            {/* Customization & Branding */}
            <div className="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow">
              <Palette className="h-12 w-12 text-primary-600 mb-4" />
              <h3 className="text-xl font-semibold mb-2">{t('features.brandCustomization.title')}</h3>
              <p className="text-gray-600">{t('features.brandCustomization.description')}</p>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow">
              <Settings className="h-12 w-12 text-primary-600 mb-4" />
              <h3 className="text-xl font-semibold mb-2">{t('features.noCodeCustomization.title')}</h3>
              <p className="text-gray-600">{t('features.noCodeCustomization.description')}</p>
            </div>

            {/* Infrastructure */}
            <div className="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow">
              <Cloud className="h-12 w-12 text-primary-600 mb-4" />
              <h3 className="text-xl font-semibold mb-2">{t('features.uptimeGuarantee.title')}</h3>
              <p className="text-gray-600">{t('features.uptimeGuarantee.description')}</p>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow">
              <Layers className="h-12 w-12 text-primary-600 mb-4" />
              <h3 className="text-xl font-semibold mb-2">{t('features.apiArchitecture.title')}</h3>
              <p className="text-gray-600">{t('features.apiArchitecture.description')}</p>
            </div>
          </div>

          {/* CTA Transition */}
          <div className="mt-16 text-center">
            <div className="bg-gradient-to-r from-primary-50 to-green-50 rounded-2xl p-8 md:p-12">
              <h3 className="text-2xl md:text-3xl font-bold text-gray-900 mb-4">
                {t('features.cta.heading')}
              </h3>
              <p className="text-lg text-gray-600 mb-8 max-w-2xl mx-auto">
                {t('features.cta.description')}
                <strong className="text-primary-600">{t('features.cta.descriptionHighlight')}</strong>
                {t('features.cta.descriptionEnd')}
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
                <Link
                  to="/signup"
                  className="bg-primary-600 text-white px-8 py-4 rounded-lg font-semibold hover:bg-primary-700 transition-colors inline-flex items-center"
                >
                  {t('features.cta.startTrial')} <ArrowRight className="ml-2 h-5 w-5" />
                </Link>
                <a
                  href="#pricing"
                  className="text-primary-600 font-semibold hover:text-primary-700 inline-flex items-center"
                >
                  {t('features.cta.viewPricing')} <ArrowRight className="ml-2 h-5 w-5" />
                </a>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              {t('pricing.heading')}
            </h2>
            <p className="text-xl text-gray-600">
              {t('pricing.subheading')}
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {/* Community and New Business Plan */}
            <div className="bg-white border-2 border-gray-200 rounded-xl p-8 hover:border-primary-300 transition-colors">
              <div className="text-center">
                <h3 className="text-xl font-semibold mb-2">{t('pricing.plans.community.name')}</h3>
                <div className="text-3xl font-bold text-gray-900 mb-1">{t('pricing.plans.community.price')}</div>
                <div className="text-gray-500 mb-6">{t('pricing.plans.community.period')}</div>
                <Link
                  to="/signup?plan=community_and_new_business"
                  className="w-full bg-gray-50 text-gray-900 py-2.5 px-4 rounded-lg hover:bg-gray-50 transition-colors block text-center"
                >
                  {t('pricing.plans.community.cta')}
                </Link>
              </div>
              <ul className="mt-8 space-y-4">
                {t('pricing.plans.community.features', { returnObjects: true }).map((feature: string, index: number) => (
                  <li key={index} className="flex items-start">
                    <CheckCircle className="h-5 w-5 text-primary-500 mr-3 flex-shrink-0 mt-0.5" />
                    <span className="text-gray-700">{feature}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Small Business Plan */}
            <div className="bg-white border-2 border-gray-200 rounded-xl p-8 hover:border-primary-300 transition-colors">
              <div className="text-center">
                <h3 className="text-xl font-semibold mb-2">{t('pricing.plans.smallBusiness.name')}</h3>
                <div className="text-3xl font-bold text-gray-900 mb-1">{t('pricing.plans.smallBusiness.price')}</div>
                <div className="text-gray-500 mb-6">{t('pricing.plans.smallBusiness.period')}</div>
                <Link
                  to="/signup?plan=small_business"
                  className="w-full bg-gray-50 text-gray-900 py-2.5 px-4 rounded-lg hover:bg-gray-50 transition-colors block text-center"
                >
                  {t('pricing.plans.smallBusiness.cta')}
                </Link>
              </div>
              <div className="mb-4 pb-3 border-b border-gray-200">
                <p className="text-sm font-medium text-primary-600">{t('pricing.plans.smallBusiness.everythingIn')}</p>
              </div>
              <ul className="mt-4 space-y-4">
                {t('pricing.plans.smallBusiness.features', { returnObjects: true }).map((feature: string, index: number) => (
                  <li key={index} className="flex items-start">
                    <CheckCircle className="h-5 w-5 text-primary-500 mr-3 flex-shrink-0 mt-0.5" />
                    <span className="text-gray-700">{feature}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Professional and Growing Business Plan */}
            <div className="bg-white border-2 border-primary-500 rounded-xl p-8 relative">
              <div className="absolute -top-6 left-1/2 transform -translate-x-1/2">
                <span className="bg-primary-500 text-white px-4 py-1 rounded-full text-sm font-medium">
                  {t('pricing.plans.professional.badge')}
                </span>
              </div>
              <div className="text-center">
                <h3 className="text-xl font-semibold mb-2">{t('pricing.plans.professional.name')}</h3>
                <div className="text-3xl font-bold text-gray-900 mb-1">{t('pricing.plans.professional.price')}</div>
                <div className="text-gray-500 mb-6">{t('pricing.plans.professional.period')}</div>
                <Link
                  to="/signup?plan=professional_and_growing_business"
                  className="w-full bg-primary-600 text-white py-2.5 px-4 rounded-lg hover:bg-primary-700 transition-colors block text-center"
                >
                  {t('pricing.plans.professional.cta')}
                </Link>
              </div>
              <div className="mb-4 pb-3 border-b border-gray-200">
                <p className="text-sm font-medium text-primary-600">{t('pricing.plans.professional.everythingIn')}</p>
              </div>
              <ul className="mt-4 space-y-4">
                {t('pricing.plans.professional.features', { returnObjects: true }).map((feature: string, index: number) => (
                  <li key={index} className="flex items-start">
                    <CheckCircle className="h-5 w-5 text-primary-500 mr-3 flex-shrink-0 mt-0.5" />
                    <span className="text-gray-700">{feature}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Enterprise Plan */}
            <div className="bg-white border-2 border-gray-200 rounded-xl p-8 hover:border-primary-300 transition-colors">
              <div className="text-center">
                <h3 className="text-xl font-semibold mb-2">{t('pricing.plans.enterprise.name')}</h3>
                <div className="text-3xl font-bold text-gray-900 mb-1">{t('pricing.plans.enterprise.price')}</div>
                <div className="text-gray-500 mb-6">{t('pricing.plans.enterprise.period')}</div>
                <Link
                  to="/signup?plan=enterprise"
                  className="w-full bg-gray-900 text-white py-2.5 px-4 rounded-lg hover:bg-gray-800 transition-colors block text-center"
                >
                  {t('pricing.plans.enterprise.cta')}
                </Link>
              </div>
              <div className="mb-4 pb-3 border-b border-gray-200">
                <p className="text-sm font-medium text-primary-600">{t('pricing.plans.enterprise.everythingIn')}</p>
              </div>
              <ul className="mt-4 space-y-4">
                {t('pricing.plans.enterprise.features', { returnObjects: true }).map((feature: string, index: number) => (
                  <li key={index} className="flex items-start">
                    <CheckCircle className="h-5 w-5 text-primary-500 mr-3 flex-shrink-0 mt-0.5" />
                    <span className="text-gray-700" dangerouslySetInnerHTML={{ __html: feature }} />
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section id="testimonials" className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              {t('testimonials.heading')}
            </h2>
            <p className="text-xl text-gray-600">
              {t('testimonials.subheading')}
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {t('testimonials.items', { returnObjects: true }).map((testimonial: any, index: number) => (
              <div key={index} className="bg-white p-6 rounded-xl ">
                <div className="flex items-center mb-4">
                  {[...Array(5)].map((_, i) => (
                    <Star key={i} className="h-5 w-5 text-yellow-400 fill-current" />
                  ))}
                </div>
                <p className="text-gray-600 mb-4">
                  {testimonial.quote}
                </p>
                <div className="flex items-center">
                  <img
                    className="h-10 w-10 rounded-full"
                    src={`https://ui-avatars.com/api/?name=${encodeURIComponent(testimonial.name)}&background=10b981&color=fff`}
                    alt={testimonial.name}
                  />
                  <div className="ml-3">
                    <p className="font-semibold">{testimonial.name}</p>
                    <p className="text-gray-500 text-sm">{testimonial.title}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-primary-600">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold text-white mb-4">
            {t('cta.heading')}
          </h2>
          <p className="text-xl text-green-100 mb-8 max-w-2xl mx-auto">
            {t('cta.description')}
          </p>
          <Link
            to="/signup"
            className="bg-white text-primary-600 px-8 py-4 rounded-lg font-semibold hover:bg-gray-50 transition-colors inline-flex items-center"
          >
            {t('cta.button')} <ArrowRight className="ml-2 h-5 w-5" />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-4 gap-8">
            <div>
              <div className="flex items-center mb-4">
                <Leaf className="h-6 w-6 text-green-400" />
                <span className="ml-2 text-xl font-bold">WeedGo</span>
              </div>
              <p className="text-gray-400">
                {t('footer.tagline')}
              </p>
            </div>
            <div>
              <h3 className="font-semibold mb-4">{t('footer.product.heading')}</h3>
              <ul className="space-y-2 text-gray-400">
                <li><a href="#features" className="hover:text-white">{t('footer.product.features')}</a></li>
                <li><a href="#pricing" className="hover:text-white">{t('footer.product.pricing')}</a></li>
                <li><a href="#" className="hover:text-white">{t('footer.product.api')}</a></li>
                <li><a href="#" className="hover:text-white">{t('footer.product.integrations')}</a></li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold mb-4">{t('footer.company.heading')}</h3>
              <ul className="space-y-2 text-gray-400">
                <li><a href="#" className="hover:text-white">{t('footer.company.about')}</a></li>
                <li><a href="#" className="hover:text-white">{t('footer.company.careers')}</a></li>
                <li><a href="#" className="hover:text-white">{t('footer.company.contact')}</a></li>
                <li><a href="#" className="hover:text-white">{t('footer.company.blog')}</a></li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold mb-4">{t('footer.support.heading')}</h3>
              <ul className="space-y-2 text-gray-400">
                <li><a href="#" className="hover:text-white">{t('footer.support.helpCenter')}</a></li>
                <li><a href="#" className="hover:text-white">{t('footer.support.documentation')}</a></li>
                <li><a href="#" className="hover:text-white">{t('footer.support.status')}</a></li>
                <li><a href="#" className="hover:text-white">{t('footer.support.security')}</a></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-800 mt-8 pt-8 text-center text-gray-400">
            <p>{t('footer.copyright')}</p>
          </div>
        </div>
      </footer>

      {/* Sales Chat Widget - Only show when not logged in */}
      {!user && <SalesChatWidget />}
    </div>
  );
};

export default Landing;