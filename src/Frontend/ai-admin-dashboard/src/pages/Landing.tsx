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

const Landing = () => {
  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <Leaf className="h-8 w-8 text-green-600" />
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
              className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 transition-colors"
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
              <span className="block text-green-600">Business Platform</span>
            </h1>
            <p className="text-xl text-gray-600 mb-10 max-w-3xl mx-auto">
              Power your dispensary with AI-driven e-commerce, multi-language support, 
              fraud protection, and complete business management—all in one platform.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link
                to="/signup"
                className="bg-green-600 text-white px-8 py-4 rounded-lg font-semibold hover:bg-green-700 transition-colors inline-flex items-center"
              >
                Start Free Trial <ArrowRight className="ml-2 h-5 w-5" />
              </Link>
              <a
                href="#features"
                className="border border-green-600 text-green-600 px-8 py-4 rounded-lg font-semibold hover:bg-green-50 transition-colors"
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
              <div className="text-3xl font-bold text-green-600">5,540+</div>
              <div className="text-gray-600">Products</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-green-600">25+</div>
              <div className="text-gray-600">Languages</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-green-600">99.9%</div>
              <div className="text-gray-600">Uptime</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-green-600">24/7</div>
              <div className="text-gray-600">Support</div>
            </div>
          </div>
        </div>
      </section>

      {/* Key Features */}
      <section id="features" className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Everything You Need to Grow Your Cannabis Business
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              From AI-powered customer service to compliance tracking, WeedGo provides 
              all the tools you need to succeed in the cannabis industry.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {/* Core AI Features */}
            <div className="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow">
              <Bot className="h-12 w-12 text-green-600 mb-4" />
              <h3 className="text-xl font-semibold mb-2">AI Budtender Assistant</h3>
              <p className="text-gray-600">Real-time translation and customer assistance with voice recognition and auto-age verification.</p>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow">
              <Headphones className="h-12 w-12 text-green-600 mb-4" />
              <h3 className="text-xl font-semibold mb-2">Voice Commerce</h3>
              <p className="text-gray-600">Audio-based shopping experience with intelligent voice assistants for personalized guidance.</p>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow">
              <Brain className="h-12 w-12 text-green-600 mb-4" />
              <h3 className="text-xl font-semibold mb-2">Predictive Analytics</h3>
              <p className="text-gray-600">Data-driven insights with automated operations and AI-driven business processes.</p>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow">
              <Search className="h-12 w-12 text-green-600 mb-4" />
              <h3 className="text-xl font-semibold mb-2">Natural Language Search</h3>
              <p className="text-gray-600">Powerful AI-driven search engine that understands natural language queries.</p>
            </div>

            {/* Multi-Language & Accessibility */}
            <div className="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow">
              <Languages className="h-12 w-12 text-green-600 mb-4" />
              <h3 className="text-xl font-semibold mb-2">Multi-Language Support</h3>
              <p className="text-gray-600">Serve customers in 25+ languages with auto-detect and real-time translation features.</p>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow">
              <Target className="h-12 w-12 text-green-600 mb-4" />
              <h3 className="text-xl font-semibold mb-2">AI Recommendations</h3>
              <p className="text-gray-600">Machine learning product recommendations with trending analysis and inventory optimization.</p>
            </div>

            {/* Security & Compliance */}
            <div className="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow">
              <Shield className="h-12 w-12 text-green-600 mb-4" />
              <h3 className="text-xl font-semibold mb-2">Fraud Protection</h3>
              <p className="text-gray-600">Advanced fraud detection with card blacklisting, signature capture, and compliance tracking.</p>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow">
              <CheckSquare className="h-12 w-12 text-green-600 mb-4" />
              <h3 className="text-xl font-semibold mb-2">Cannabis Compliance</h3>
              <p className="text-gray-600">OCS integration, CannSell certification tracking, and regulatory requirement adherence.</p>
            </div>

            {/* Platform Features */}
            <div className="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow">
              <Monitor className="h-12 w-12 text-green-600 mb-4" />
              <h3 className="text-xl font-semibold mb-2">Omnichannel Platform</h3>
              <p className="text-gray-600">Menu, POS, and KIOSK applications for web, tablet, and mobile devices.</p>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow">
              <Palette className="h-12 w-12 text-green-600 mb-4" />
              <h3 className="text-xl font-semibold mb-2">White-Label Solution</h3>
              <p className="text-gray-600">Complete brand customization with template marketplace and independent operations.</p>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow">
              <Truck className="h-12 w-12 text-green-600 mb-4" />
              <h3 className="text-xl font-semibold mb-2">Delivery Management</h3>
              <p className="text-gray-600">Complete delivery tracking and fulfillment system with real-time updates.</p>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow">
              <BarChart3 className="h-12 w-12 text-green-600 mb-4" />
              <h3 className="text-xl font-semibold mb-2">Business Intelligence</h3>
              <p className="text-gray-600">Sales analytics, inventory reports, customer insights, and compliance reporting.</p>
            </div>

            {/* Production & Infrastructure */}
            <div className="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow">
              <Cloud className="h-12 w-12 text-green-600 mb-4" />
              <h3 className="text-xl font-semibold mb-2">Enterprise Infrastructure</h3>
              <p className="text-gray-600">Subdomain routing, CDN integration, and horizontal scaling capabilities.</p>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow">
              <Database className="h-12 w-12 text-green-600 mb-4" />
              <h3 className="text-xl font-semibold mb-2">Data Protection</h3>
              <p className="text-gray-600">Backup systems, health monitoring, and system status tracking for reliability.</p>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow">
              <Globe className="h-12 w-12 text-green-600 mb-4" />
              <h3 className="text-xl font-semibold mb-2">SEO Optimization</h3>
              <p className="text-gray-600">Built-in SEO tools for both static and dynamic content optimization.</p>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow">
              <Activity className="h-12 w-12 text-green-600 mb-4" />
              <h3 className="text-xl font-semibold mb-2">Real-Time Analytics</h3>
              <p className="text-gray-600">Live dashboard with performance metrics, user behavior tracking, and conversion optimization.</p>
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
            <div className="bg-white border-2 border-gray-200 rounded-xl p-8 hover:border-green-300 transition-colors">
              <div className="text-center">
                <h3 className="text-xl font-semibold mb-2">Community and New Business</h3>
                <div className="text-3xl font-bold text-gray-900 mb-1">FREE</div>
                <div className="text-gray-500 mb-6">forever</div>
                <Link
                  to="/signup?plan=community_and_new_business"
                  className="w-full bg-gray-100 text-gray-900 py-2 px-4 rounded-lg hover:bg-gray-200 transition-colors block text-center"
                >
                  Get Started
                </Link>
              </div>
              <ul className="mt-8 space-y-3">
                <li className="flex items-center">
                  <CheckCircle className="h-5 w-5 text-green-500 mr-3" />
                  <span>1 Store Location</span>
                </li>
                <li className="flex items-center">
                  <CheckCircle className="h-5 w-5 text-green-500 mr-3" />
                  <span>2 Languages (EN/FR)</span>
                </li>
                <li className="flex items-center">
                  <CheckCircle className="h-5 w-5 text-green-500 mr-3" />
                  <span>1 AI Personality</span>
                </li>
                <li className="flex items-center">
                  <CheckCircle className="h-5 w-5 text-green-500 mr-3" />
                  <span>Basic POS System</span>
                </li>
                <li className="flex items-center">
                  <CheckCircle className="h-5 w-5 text-green-500 mr-3" />
                  <span>Standard Support</span>
                </li>
              </ul>
            </div>

            {/* Small Business Plan */}
            <div className="bg-white border-2 border-gray-200 rounded-xl p-8 hover:border-green-300 transition-colors">
              <div className="text-center">
                <h3 className="text-xl font-semibold mb-2">Small Business</h3>
                <div className="text-3xl font-bold text-gray-900 mb-1">$99</div>
                <div className="text-gray-500 mb-6">/month</div>
                <Link
                  to="/signup?plan=small_business"
                  className="w-full bg-gray-100 text-gray-900 py-2 px-4 rounded-lg hover:bg-gray-200 transition-colors block text-center"
                >
                  Get Started
                </Link>
              </div>
              <ul className="mt-8 space-y-3">
                <li className="flex items-center">
                  <CheckCircle className="h-5 w-5 text-green-500 mr-3" />
                  <span>5 Store Locations</span>
                </li>
                <li className="flex items-center">
                  <CheckCircle className="h-5 w-5 text-green-500 mr-3" />
                  <span>5 Languages</span>
                </li>
                <li className="flex items-center">
                  <CheckCircle className="h-5 w-5 text-green-500 mr-3" />
                  <span>2 AI Personalities per store</span>
                </li>
                <li className="flex items-center">
                  <CheckCircle className="h-5 w-5 text-green-500 mr-3" />
                  <span>Advanced POS + KIOSK</span>
                </li>
                <li className="flex items-center">
                  <CheckCircle className="h-5 w-5 text-green-500 mr-3" />
                  <span>Delivery Management</span>
                </li>
                <li className="flex items-center">
                  <CheckCircle className="h-5 w-5 text-green-500 mr-3" />
                  <span>Priority Support</span>
                </li>
              </ul>
            </div>

            {/* Professional and Growing Business Plan */}
            <div className="bg-white border-2 border-green-500 rounded-xl p-8 relative">
              <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                <span className="bg-green-500 text-white px-4 py-1 rounded-full text-sm font-medium">
                  Most Popular
                </span>
              </div>
              <div className="text-center">
                <h3 className="text-xl font-semibold mb-2">Professional and Growing Business</h3>
                <div className="text-3xl font-bold text-gray-900 mb-1">$149</div>
                <div className="text-gray-500 mb-6">/month</div>
                <Link
                  to="/signup?plan=professional_and_growing_business"
                  className="w-full bg-green-600 text-white py-2 px-4 rounded-lg hover:bg-green-700 transition-colors block text-center"
                >
                  Get Started
                </Link>
              </div>
              <ul className="mt-8 space-y-3">
                <li className="flex items-center">
                  <CheckCircle className="h-5 w-5 text-green-500 mr-3" />
                  <span>12 Store Locations</span>
                </li>
                <li className="flex items-center">
                  <CheckCircle className="h-5 w-5 text-green-500 mr-3" />
                  <span>10 Languages</span>
                </li>
                <li className="flex items-center">
                  <CheckCircle className="h-5 w-5 text-green-500 mr-3" />
                  <span>3 AI Personalities per store</span>
                </li>
                <li className="flex items-center">
                  <CheckCircle className="h-5 w-5 text-green-500 mr-3" />
                  <span>Full Platform Access</span>
                </li>
                <li className="flex items-center">
                  <CheckCircle className="h-5 w-5 text-green-500 mr-3" />
                  <span>Voice Age Verification</span>
                </li>
                <li className="flex items-center">
                  <CheckCircle className="h-5 w-5 text-green-500 mr-3" />
                  <span>Fraud Protection</span>
                </li>
                <li className="flex items-center">
                  <CheckCircle className="h-5 w-5 text-green-500 mr-3" />
                  <span>24/7 Support</span>
                </li>
              </ul>
            </div>

            {/* Enterprise Plan */}
            <div className="bg-white border-2 border-gray-200 rounded-xl p-8 hover:border-green-300 transition-colors">
              <div className="text-center">
                <h3 className="text-xl font-semibold mb-2">Enterprise</h3>
                <div className="text-3xl font-bold text-gray-900 mb-1">$299</div>
                <div className="text-gray-500 mb-6">/month</div>
                <Link
                  to="/signup?plan=enterprise"
                  className="w-full bg-gray-900 text-white py-2 px-4 rounded-lg hover:bg-gray-800 transition-colors block text-center"
                >
                  Contact Sales
                </Link>
              </div>
              <ul className="mt-8 space-y-3">
                <li className="flex items-center">
                  <CheckCircle className="h-5 w-5 text-green-500 mr-3" />
                  <span>Unlimited Stores</span>
                </li>
                <li className="flex items-center">
                  <CheckCircle className="h-5 w-5 text-green-500 mr-3" />
                  <span>25+ Languages</span>
                </li>
                <li className="flex items-center">
                  <CheckCircle className="h-5 w-5 text-green-500 mr-3" />
                  <span>5 AI Personalities per store</span>
                </li>
                <li className="flex items-center">
                  <CheckCircle className="h-5 w-5 text-green-500 mr-3" />
                  <span>White-label Platform</span>
                </li>
                <li className="flex items-center">
                  <CheckCircle className="h-5 w-5 text-green-500 mr-3" />
                  <span>Support Agent Access</span>
                </li>
                <li className="flex items-center">
                  <CheckCircle className="h-5 w-5 text-green-500 mr-3" />
                  <span>Custom Integrations</span>
                </li>
                <li className="flex items-center">
                  <CheckCircle className="h-5 w-5 text-green-500 mr-3" />
                  <span>Dedicated Support</span>
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
            <div className="bg-white p-6 rounded-xl shadow-sm">
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

            <div className="bg-white p-6 rounded-xl shadow-sm">
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

            <div className="bg-white p-6 rounded-xl shadow-sm">
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
      <section className="py-20 bg-green-600">
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
            className="bg-white text-green-600 px-8 py-4 rounded-lg font-semibold hover:bg-gray-100 transition-colors inline-flex items-center"
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
    </div>
  );
};

export default Landing;