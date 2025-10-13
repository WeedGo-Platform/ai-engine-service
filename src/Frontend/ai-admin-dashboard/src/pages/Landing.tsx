import React from 'react';
import { Link } from 'react-router-dom';
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

const Landing = () => {
  const { user } = useAuth();

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
            <nav className="hidden md:flex space-x-8">
              <a href="#features" className="text-gray-500 hover:text-gray-900">Features</a>
              <a href="#pricing" className="text-gray-500 hover:text-gray-900">Pricing</a>
              <a href="#testimonials" className="text-gray-500 hover:text-gray-900">Testimonials</a>
              <Link to="/login" className="text-gray-500 hover:text-gray-900">Login</Link>
            </nav>
            <Link
              to="/signup"
              className="bg-primary-600 text-white px-6 py-2 rounded-lg hover:bg-primary-700 transition-colors"
            >
              Get Started
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="bg-gradient-to-br from-green-50 to-emerald-100 py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-8">
              The Complete Cannabis
              <span className="block text-primary-600">Business Platform</span>
            </h1>
            <p className="text-xl text-gray-600 mb-10 max-w-3xl mx-auto">
              Power your dispensary with AI-driven e-commerce, multi-language support, 
              fraud protection, and complete business management—all in one platform.
            </p>
            <div className="flex flex-col sm:flex-row gap-6 justify-center">
              <Link
                to="/signup"
                className="bg-primary-600 text-white px-8 py-4 rounded-lg font-semibold hover:bg-primary-700 transition-colors inline-flex items-center"
              >
                Start Free Trial <ArrowRight className="ml-2 h-5 w-5" />
              </Link>
              <a
                href="#features"
                className="border border-primary-600 text-primary-600 px-8 py-4 rounded-lg font-semibold hover:bg-primary-50 transition-colors"
              >
                Learn More
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
              <div className="text-gray-600">Products</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-primary-600">25+</div>
              <div className="text-gray-600">Languages</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-primary-600">99.9%</div>
              <div className="text-gray-600">Uptime</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-primary-600">24/7</div>
              <div className="text-gray-600">Support</div>
            </div>
          </div>
        </div>
      </section>

      {/* Key Features */}
      <section id="features" className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Everything You Need to Dominate Your Market
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Built exclusively for cannabis retailers, WeedGo combines cutting-edge AI,
              enterprise-grade infrastructure, and industry-specific tools to help you
              <strong className="text-primary-600"> sell more, serve better, and scale faster</strong>.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* AI-Powered Customer Experience */}
            <div className="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow">
              <Bot className="h-12 w-12 text-primary-600 mb-4" />
              <h3 className="text-xl font-semibold mb-2">AI Budtender 24/7</h3>
              <p className="text-gray-600">Never miss a sale. Your AI assistant handles customer questions instantly in any language, recommends products, and even verifies age automatically.</p>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow">
              <Mic className="h-12 w-12 text-primary-600 mb-4" />
              <h3 className="text-xl font-semibold mb-2">Voice Shopping</h3>
              <p className="text-gray-600">Accessibility meets convenience. Customers can browse, search, and order hands-free—perfect for in-store kiosks and mobile shoppers.</p>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow">
              <Brain className="h-12 w-12 text-primary-600 mb-4" />
              <h3 className="text-xl font-semibold mb-2">Predictive Intelligence</h3>
              <p className="text-gray-600">Know what sells before it happens. AI predicts demand, optimizes inventory levels, and alerts you to reorder at the perfect time.</p>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow">
              <Target className="h-12 w-12 text-primary-600 mb-4" />
              <h3 className="text-xl font-semibold mb-2">Smart Recommendations</h3>
              <p className="text-gray-600">Boost average order value by 40%. Machine learning suggests complementary products based on purchase patterns and customer preferences.</p>
            </div>

            {/* Multi-Channel Commerce */}
            <div className="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow">
              <Monitor className="h-12 w-12 text-primary-600 mb-4" />
              <h3 className="text-xl font-semibold mb-2">Unified Commerce Platform</h3>
              <p className="text-gray-600">One system for everything—web storefront, in-store POS, kiosk, mobile app, and TV menu displays. Your inventory syncs in real-time across all channels.</p>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow">
              <Smartphone className="h-12 w-12 text-primary-600 mb-4" />
              <h3 className="text-xl font-semibold mb-2">Branded Mobile Apps</h3>
              <p className="text-gray-600">Your customers download YOUR app (iOS & Android). Build loyalty with push notifications, exclusive deals, and seamless mobile ordering.</p>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow">
              <Tablet className="h-12 w-12 text-primary-600 mb-4" />
              <h3 className="text-xl font-semibold mb-2">Self-Service Kiosks</h3>
              <p className="text-gray-600">Reduce wait times and labor costs. Customers browse, order, and pay on tablets—your staff focuses on high-value interactions.</p>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow">
              <Truck className="h-12 w-12 text-primary-600 mb-4" />
              <h3 className="text-xl font-semibold mb-2">Delivery Ecosystem</h3>
              <p className="text-gray-600">Complete delivery management with driver apps, real-time GPS tracking, customer notifications, and route optimization. Compete with the big players.</p>
            </div>

            {/* Global Reach */}
            <div className="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow">
              <Languages className="h-12 w-12 text-primary-600 mb-4" />
              <h3 className="text-xl font-semibold mb-2">25+ Languages, Zero Barriers</h3>
              <p className="text-gray-600">Serve every customer in their native language. Auto-detection, real-time translation, and localized content—expand into any market instantly.</p>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow">
              <Globe className="h-12 w-12 text-primary-600 mb-4" />
              <h3 className="text-xl font-semibold mb-2">SEO That Actually Works</h3>
              <p className="text-gray-600">Dynamic, AI-powered SEO optimization. Your product pages rank higher on Google automatically—no SEO agency required.</p>
            </div>

            {/* Security & Compliance */}
            <div className="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow">
              <Shield className="h-12 w-12 text-primary-600 mb-4" />
              <h3 className="text-xl font-semibold mb-2">Fraud Protection Suite</h3>
              <p className="text-gray-600">Stop chargebacks before they happen. AI detects suspicious patterns, blacklists fraudulent cards, and captures signatures for every transaction.</p>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow">
              <CheckSquare className="h-12 w-12 text-primary-600 mb-4" />
              <h3 className="text-xl font-semibold mb-2">Compliance Autopilot</h3>
              <p className="text-gray-600">Stay compliant without the headache. Automatic age verification, CannSell tracking, OCS integration, and audit-ready reports at your fingertips.</p>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow">
              <Lock className="h-12 w-12 text-primary-600 mb-4" />
              <h3 className="text-xl font-semibold mb-2">Multi-Layer Age Verification</h3>
              <p className="text-gray-600">Voice recognition, ID scanning, facial matching, and manual override—verify customers' age through multiple methods for complete regulatory confidence.</p>
            </div>

            {/* Business Operations */}
            <div className="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow">
              <BarChart3 className="h-12 w-12 text-primary-600 mb-4" />
              <h3 className="text-xl font-semibold mb-2">Real-Time Business Intelligence</h3>
              <p className="text-gray-600">See everything in one dashboard—sales trends, top products, customer behavior, staff performance, and profit margins updated every second.</p>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow">
              <Store className="h-12 w-12 text-primary-600 mb-4" />
              <h3 className="text-xl font-semibold mb-2">Multi-Location Command Center</h3>
              <p className="text-gray-600">Manage unlimited stores from one dashboard. Transfer inventory between locations, compare performance, and maintain consistent branding effortlessly.</p>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow">
              <Users className="h-12 w-12 text-primary-600 mb-4" />
              <h3 className="text-xl font-semibold mb-2">Customer Loyalty Engine</h3>
              <p className="text-gray-600">Turn first-time buyers into regulars. Points programs, VIP tiers, birthday rewards, and referral bonuses—all automated and customizable.</p>
            </div>

            {/* Customization & Branding */}
            <div className="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow">
              <Palette className="h-12 w-12 text-primary-600 mb-4" />
              <h3 className="text-xl font-semibold mb-2">Your Brand, Your Way</h3>
              <p className="text-gray-600">Complete white-label customization. Choose from premium templates or go fully custom—logos, colors, fonts, and layouts that scream YOU.</p>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow">
              <Settings className="h-12 w-12 text-primary-600 mb-4" />
              <h3 className="text-xl font-semibold mb-2">No-Code Customization</h3>
              <p className="text-gray-600">Change anything without a developer. Drag-and-drop page builder, custom forms, promotional banners—update your store in minutes, not weeks.</p>
            </div>

            {/* Infrastructure */}
            <div className="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow">
              <Cloud className="h-12 w-12 text-primary-600 mb-4" />
              <h3 className="text-xl font-semibold mb-2">99.9% Uptime Guarantee</h3>
              <p className="text-gray-600">Enterprise cloud infrastructure that scales automatically. Lightning-fast load times, global CDN, and redundant backups—your store never goes down.</p>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow">
              <Layers className="h-12 w-12 text-primary-600 mb-4" />
              <h3 className="text-xl font-semibold mb-2">API-First Architecture</h3>
              <p className="text-gray-600">Integrate with anything. Full REST API access lets you connect accounting software, marketing tools, or custom applications seamlessly.</p>
            </div>
          </div>

          {/* CTA Transition */}
          <div className="mt-16 text-center">
            <div className="bg-gradient-to-r from-primary-50 to-green-50 rounded-2xl p-8 md:p-12">
              <h3 className="text-2xl md:text-3xl font-bold text-gray-900 mb-4">
                Ready to See What WeedGo Can Do for Your Business?
              </h3>
              <p className="text-lg text-gray-600 mb-8 max-w-2xl mx-auto">
                Join hundreds of cannabis retailers who've already made the switch.
                <strong className="text-primary-600"> Start free, scale unlimited, and transform your business</strong> with the only platform built specifically for you.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
                <Link
                  to="/signup"
                  className="bg-primary-600 text-white px-8 py-4 rounded-lg font-semibold hover:bg-primary-700 transition-colors inline-flex items-center"
                >
                  Start Free Trial <ArrowRight className="ml-2 h-5 w-5" />
                </Link>
                <a
                  href="#pricing"
                  className="text-primary-600 font-semibold hover:text-primary-700 inline-flex items-center"
                >
                  View Pricing Plans <ArrowRight className="ml-2 h-5 w-5" />
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
              Simple, Transparent Pricing
            </h2>
            <p className="text-xl text-gray-600">
              Choose the plan that fits your business needs
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {/* Community and New Business Plan */}
            <div className="bg-white border-2 border-gray-200 rounded-xl p-8 hover:border-primary-300 transition-colors">
              <div className="text-center">
                <h3 className="text-xl font-semibold mb-2">Community and New Business</h3>
                <div className="text-3xl font-bold text-gray-900 mb-1">FREE</div>
                <div className="text-gray-500 mb-6">forever</div>
                <Link
                  to="/signup?plan=community_and_new_business"
                  className="w-full bg-gray-50 text-gray-900 py-2.5 px-4 rounded-lg hover:bg-gray-50 transition-colors block text-center"
                >
                  Get Started
                </Link>
              </div>
              <ul className="mt-8 space-y-4">
                <li className="flex items-start">
                  <CheckCircle className="h-5 w-5 text-primary-500 mr-3 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">Unlimited store locations to scale at your pace</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="h-5 w-5 text-primary-500 mr-3 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">Bilingual support (English & French)</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="h-5 w-5 text-primary-500 mr-3 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">AI-powered budtender personality</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="h-5 w-5 text-primary-500 mr-3 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">Complete POS & kiosk system</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="h-5 w-5 text-primary-500 mr-3 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">Customizable e-commerce storefront</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="h-5 w-5 text-primary-500 mr-3 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">Digital menu display system</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="h-5 w-5 text-primary-500 mr-3 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">Built-in delivery management</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="h-5 w-5 text-primary-500 mr-3 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">Advanced fraud protection & age verification</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="h-5 w-5 text-primary-500 mr-3 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">Community support</span>
                </li>
              </ul>
            </div>

            {/* Small Business Plan */}
            <div className="bg-white border-2 border-gray-200 rounded-xl p-8 hover:border-primary-300 transition-colors">
              <div className="text-center">
                <h3 className="text-xl font-semibold mb-2">Small Business</h3>
                <div className="text-3xl font-bold text-gray-900 mb-1">$99</div>
                <div className="text-gray-500 mb-6">/month</div>
                <Link
                  to="/signup?plan=small_business"
                  className="w-full bg-gray-50 text-gray-900 py-2.5 px-4 rounded-lg hover:bg-gray-50 transition-colors block text-center"
                >
                  Get Started
                </Link>
              </div>
              <div className="mb-4 pb-3 border-b border-gray-200">
                <p className="text-sm font-medium text-primary-600">Everything in Free, plus:</p>
              </div>
              <ul className="mt-4 space-y-4">
                <li className="flex items-start">
                  <CheckCircle className="h-5 w-5 text-primary-500 mr-3 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">Expand to 5 languages for diverse markets</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="h-5 w-5 text-primary-500 mr-3 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">2 AI personalities to match your brand voice</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="h-5 w-5 text-primary-500 mr-3 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">Professional-grade POS with advanced features</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="h-5 w-5 text-primary-500 mr-3 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">Dedicated tablet kiosk application</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="h-5 w-5 text-primary-500 mr-3 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">Premium e-commerce templates</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="h-5 w-5 text-primary-500 mr-3 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">TV-ready menu display for in-store marketing</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="h-5 w-5 text-primary-500 mr-3 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">Priority support when you need it</span>
                </li>
              </ul>
            </div>

            {/* Professional and Growing Business Plan */}
            <div className="bg-white border-2 border-primary-500 rounded-xl p-8 relative">
              <div className="absolute -top-6 left-1/2 transform -translate-x-1/2">
                <span className="bg-primary-500 text-white px-4 py-1 rounded-full text-sm font-medium">
                  Most Popular
                </span>
              </div>
              <div className="text-center">
                <h3 className="text-xl font-semibold mb-2">Professional and Growing Business</h3>
                <div className="text-3xl font-bold text-gray-900 mb-1">$149</div>
                <div className="text-gray-500 mb-6">/month</div>
                <Link
                  to="/signup?plan=professional_and_growing_business"
                  className="w-full bg-primary-600 text-white py-2.5 px-4 rounded-lg hover:bg-primary-700 transition-colors block text-center"
                >
                  Get Started
                </Link>
              </div>
              <div className="mb-4 pb-3 border-b border-gray-200">
                <p className="text-sm font-medium text-primary-600">Everything in Small Business, plus:</p>
              </div>
              <ul className="mt-4 space-y-4">
                <li className="flex items-start">
                  <CheckCircle className="h-5 w-5 text-primary-500 mr-3 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">Reach global markets with 10 languages</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="h-5 w-5 text-primary-500 mr-3 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">3 AI personalities for personalized experiences</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="h-5 w-5 text-primary-500 mr-3 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">Unlock all platform features & integrations</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="h-5 w-5 text-primary-500 mr-3 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700"><strong>Custom e-commerce design</strong> ($5,000 value)</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="h-5 w-5 text-primary-500 mr-3 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">Branded mobile app for iOS & Android</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="h-5 w-5 text-primary-500 mr-3 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">Live delivery tracking for customers</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="h-5 w-5 text-primary-500 mr-3 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">Driver app for seamless operations</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="h-5 w-5 text-primary-500 mr-3 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">Complete API access for custom integrations</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="h-5 w-5 text-primary-500 mr-3 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">Professional SEO optimization & content rewrite</span>
                </li>
              </ul>
            </div>

            {/* Enterprise Plan */}
            <div className="bg-white border-2 border-gray-200 rounded-xl p-8 hover:border-primary-300 transition-colors">
              <div className="text-center">
                <h3 className="text-xl font-semibold mb-2">Enterprise</h3>
                <div className="text-3xl font-bold text-gray-900 mb-1">$299</div>
                <div className="text-gray-500 mb-6">/month</div>
                <Link
                  to="/signup?plan=enterprise"
                  className="w-full bg-gray-900 text-white py-2.5 px-4 rounded-lg hover:bg-gray-800 transition-colors block text-center"
                >
                  Contact Sales
                </Link>
              </div>
              <div className="mb-4 pb-3 border-b border-gray-200">
                <p className="text-sm font-medium text-primary-600">Everything in Professional, plus:</p>
              </div>
              <ul className="mt-4 space-y-4">
                <li className="flex items-start">
                  <CheckCircle className="h-5 w-5 text-primary-500 mr-3 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700"><strong>25+ languages</strong> for true global reach</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="h-5 w-5 text-primary-500 mr-3 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">5 AI personalities to serve every customer segment</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="h-5 w-5 text-primary-500 mr-3 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700"><strong>White-label platform</strong> - fully rebrand as your own</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="h-5 w-5 text-primary-500 mr-3 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">Dedicated MVP server for maximum performance</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="h-5 w-5 text-primary-500 mr-3 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">AI-powered marketing automation suite</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="h-5 w-5 text-primary-500 mr-3 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">Dynamic SEO rewriting to dominate search rankings</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="h-5 w-5 text-primary-500 mr-3 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">AI-optimized promotional ads targeted to your customers</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="h-5 w-5 text-primary-500 mr-3 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">Custom feature development tailored to your needs</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="h-5 w-5 text-primary-500 mr-3 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">Direct access to support engineers</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="h-5 w-5 text-primary-500 mr-3 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">Priority custom integrations with your systems</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="h-5 w-5 text-primary-500 mr-3 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">24/7 dedicated account manager</span>
                </li>
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
              Trusted by Cannabis Businesses Worldwide
            </h2>
            <p className="text-xl text-gray-600">
              See what our customers are saying about WeedGo
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="bg-white p-6 rounded-xl ">
              <div className="flex items-center mb-4">
                {[...Array(5)].map((_, i) => (
                  <Star key={i} className="h-5 w-5 text-yellow-400 fill-current" />
                ))}
              </div>
              <p className="text-gray-600 mb-4">
                "WeedGo transformed our business. The AI assistant has increased our 
                sales by 40% and the multi-language support helps us serve our diverse 
                customer base."
              </p>
              <div className="flex items-center">
                <img
                  className="h-10 w-10 rounded-full"
                  src="https://ui-avatars.com/api/?name=Sarah+Johnson&background=10b981&color=fff"
                  alt="Sarah Johnson"
                />
                <div className="ml-3">
                  <p className="font-semibold">Sarah Johnson</p>
                  <p className="text-gray-500 text-sm">Owner, Green Valley Dispensary</p>
                </div>
              </div>
            </div>

            <div className="bg-white p-6 rounded-xl ">
              <div className="flex items-center mb-4">
                {[...Array(5)].map((_, i) => (
                  <Star key={i} className="h-5 w-5 text-yellow-400 fill-current" />
                ))}
              </div>
              <p className="text-gray-600 mb-4">
                "The fraud protection and compliance features are game-changers. 
                We've prevented thousands in fraudulent transactions and stay 
                compliant effortlessly."
              </p>
              <div className="flex items-center">
                <img
                  className="h-10 w-10 rounded-full"
                  src="https://ui-avatars.com/api/?name=Mike+Chen&background=10b981&color=fff"
                  alt="Mike Chen"
                />
                <div className="ml-3">
                  <p className="font-semibold">Mike Chen</p>
                  <p className="text-gray-500 text-sm">Manager, Urban Leaf Co.</p>
                </div>
              </div>
            </div>

            <div className="bg-white p-6 rounded-xl ">
              <div className="flex items-center mb-4">
                {[...Array(5)].map((_, i) => (
                  <Star key={i} className="h-5 w-5 text-yellow-400 fill-current" />
                ))}
              </div>
              <p className="text-gray-600 mb-4">
                "Scaling from 1 to 8 locations was seamless with WeedGo. The 
                multi-tenant architecture and centralized management tools are 
                exactly what we needed."
              </p>
              <div className="flex items-center">
                <img
                  className="h-10 w-10 rounded-full"
                  src="https://ui-avatars.com/api/?name=Lisa+Rodriguez&background=10b981&color=fff"
                  alt="Lisa Rodriguez"
                />
                <div className="ml-3">
                  <p className="font-semibold">Lisa Rodriguez</p>
                  <p className="text-gray-500 text-sm">CEO, Cannabis Collective</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-primary-600">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold text-white mb-4">
            Ready to Transform Your Cannabis Business?
          </h2>
          <p className="text-xl text-green-100 mb-8 max-w-2xl mx-auto">
            Join thousands of dispensaries already using WeedGo to increase sales, 
            improve compliance, and deliver exceptional customer experiences.
          </p>
          <Link
            to="/signup"
            className="bg-white text-primary-600 px-8 py-4 rounded-lg font-semibold hover:bg-gray-50 transition-colors inline-flex items-center"
          >
            Start Your Free Trial <ArrowRight className="ml-2 h-5 w-5" />
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
                The complete cannabis business platform powered by AI.
              </p>
            </div>
            <div>
              <h3 className="font-semibold mb-4">Product</h3>
              <ul className="space-y-2 text-gray-400">
                <li><a href="#features" className="hover:text-white">Features</a></li>
                <li><a href="#pricing" className="hover:text-white">Pricing</a></li>
                <li><a href="#" className="hover:text-white">API</a></li>
                <li><a href="#" className="hover:text-white">Integrations</a></li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold mb-4">Company</h3>
              <ul className="space-y-2 text-gray-400">
                <li><a href="#" className="hover:text-white">About</a></li>
                <li><a href="#" className="hover:text-white">Careers</a></li>
                <li><a href="#" className="hover:text-white">Contact</a></li>
                <li><a href="#" className="hover:text-white">Blog</a></li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold mb-4">Support</h3>
              <ul className="space-y-2 text-gray-400">
                <li><a href="#" className="hover:text-white">Help Center</a></li>
                <li><a href="#" className="hover:text-white">Documentation</a></li>
                <li><a href="#" className="hover:text-white">Status</a></li>
                <li><a href="#" className="hover:text-white">Security</a></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-800 mt-8 pt-8 text-center text-gray-400">
            <p>&copy; 2025 WeedGo. All rights reserved.</p>
          </div>
        </div>
      </footer>

      {/* Sales Chat Widget - Only show when not logged in */}
      {!user && <SalesChatWidget />}
    </div>
  );
};

export default Landing;