import React, { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useSelector, useDispatch } from 'react-redux';
import { useTranslation } from 'react-i18next';
import {
  ShoppingCartIcon,
  UserIcon,
  MagnifyingGlassIcon as SearchIcon,
  Bars3Icon as MenuIcon,
  XMarkIcon as XIcon,
  HomeIcon,
  CubeIcon,
  ChatBubbleLeftRightIcon as ChatAlt2Icon,
  GlobeAltIcon
} from '@heroicons/react/24/outline';
import { RootState } from '@store/index';
import ChatInterface from '@components/chat/ChatInterface';
import StoreSelector from '@components/common/StoreSelector';
import { logout } from '@features/auth/authSlice';

interface MainLayoutProps {
  children: React.ReactNode;
}

const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  const { t, i18n } = useTranslation();
  const location = useLocation();
  const navigate = useNavigate();
  const dispatch = useDispatch();

  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [isChatOpen, setIsChatOpen] = useState(false);

  const { items } = useSelector((state: RootState) => state.cart);
  const { isAuthenticated, user } = useSelector((state: RootState) => state.auth);
  const cartItemCount = items.reduce((total, item) => total + item.quantity, 0);

  // Language options
  const languages = [
    { code: 'en', label: 'English', flag: '🇺🇸' },
    { code: 'fr', label: 'Français', flag: '🇫🇷' },
    { code: 'es', label: 'Español', flag: '🇪🇸' },
    { code: 'de', label: 'Deutsch', flag: '🇩🇪' },
    { code: 'it', label: 'Italiano', flag: '🇮🇹' },
    { code: 'pt', label: 'Português', flag: '🇧🇷' }
  ];

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/products?search=${encodeURIComponent(searchQuery)}`);
      setIsSearchOpen(false);
      setSearchQuery('');
    }
  };

  const handleLogout = () => {
    dispatch(logout());
    navigate('/');
  };

  const handleLanguageChange = (langCode: string) => {
    i18n.changeLanguage(langCode);
  };

  // Close mobile menu on route change
  useEffect(() => {
    setIsMobileMenuOpen(false);
  }, [location]);

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      {/* Header */}
      <header className="sticky top-0 z-40 bg-white shadow-md">
        {/* Top Bar */}
        <div className="bg-primary-600 text-white py-2">
          <div className="container-max flex justify-between items-center text-sm">
            <div className="flex items-center space-x-4">
              <StoreSelector />
              <span>🕒 {t('header.hours')}: 9AM - 10PM</span>
            </div>
            <div className="flex items-center space-x-4">
              <div className="relative group">
                <button className="flex items-center space-x-1 hover:opacity-80">
                  <GlobeAltIcon className="h-4 w-4" />
                  <span>{languages.find(l => l.code === i18n.language)?.label}</span>
                </button>
                <div className="absolute right-0 mt-2 py-2 w-48 bg-white rounded-lg shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200">
                  {languages.map(lang => (
                    <button
                      key={lang.code}
                      onClick={() => handleLanguageChange(lang.code)}
                      className={`w-full px-4 py-2 text-left text-gray-700 hover:bg-gray-100 flex items-center space-x-2 ${
                        i18n.language === lang.code ? 'bg-primary-50' : ''
                      }`}
                    >
                      <span>{lang.flag}</span>
                      <span>{lang.label}</span>
                    </button>
                  ))}
                </div>
              </div>
              <span>📞 1-800-WEEDGO</span>
            </div>
          </div>
        </div>

        {/* Main Navigation */}
        <nav className="py-4">
          <div className="container-max">
            <div className="flex items-center justify-between">
              {/* Logo */}
              <Link to="/" className="flex items-center space-x-2">
                <div className="h-10 w-10 bg-primary-500 rounded-full flex items-center justify-center">
                  <span className="text-white font-bold text-xl">W</span>
                </div>
                <span className="text-2xl font-bold text-primary-600">WeedGo</span>
              </Link>

              {/* Desktop Navigation */}
              <div className="hidden md:flex items-center space-x-8">
                <Link
                  to="/"
                  className={`flex items-center space-x-1 hover:text-primary-500 transition-colors ${
                    location.pathname === '/' ? 'text-primary-500' : 'text-gray-700'
                  }`}
                >
                  <HomeIcon className="h-5 w-5" />
                  <span>{t('nav.home')}</span>
                </Link>
                <Link
                  to="/products"
                  className={`flex items-center space-x-1 hover:text-primary-500 transition-colors ${
                    location.pathname === '/products' ? 'text-primary-500' : 'text-gray-700'
                  }`}
                >
                  <CubeIcon className="h-5 w-5" />
                  <span>{t('nav.products')}</span>
                </Link>
              </div>

              {/* Search Bar */}
              <div className="hidden md:block flex-1 max-w-lg mx-8">
                <form onSubmit={handleSearch} className="relative">
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder={t('search.placeholder')}
                    className="w-full pl-10 pr-4 py-2 rounded-full border border-gray-300 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  />
                  <SearchIcon className="absolute left-3 top-2.5 h-5 w-5 text-gray-400" />
                  <button
                    type="submit"
                    className="absolute right-2 top-1 px-3 py-1.5 bg-primary-500 text-white rounded-full hover:bg-primary-600 transition-colors text-sm"
                  >
                    {t('search.button')}
                  </button>
                </form>
              </div>

              {/* Right Actions */}
              <div className="flex items-center space-x-4">
                {/* Chat Button */}
                <button
                  onClick={() => setIsChatOpen(!isChatOpen)}
                  className="p-2 hover:bg-gray-100 rounded-full transition-colors relative"
                  aria-label="Open chat"
                >
                  <ChatAlt2Icon className="h-6 w-6 text-gray-700" />
                  <span className="absolute -top-1 -right-1 h-3 w-3 bg-green-500 rounded-full animate-pulse"></span>
                </button>

                {/* User Menu */}
                <div className="relative group">
                  <button className="p-2 hover:bg-gray-100 rounded-full transition-colors">
                    <UserIcon className="h-6 w-6 text-gray-700" />
                  </button>
                  <div className="absolute right-0 mt-2 py-2 w-48 bg-white rounded-lg shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200">
                    {isAuthenticated ? (
                      <>
                        <Link
                          to="/profile"
                          className="block px-4 py-2 text-gray-700 hover:bg-gray-100"
                        >
                          {t('nav.profile')}
                        </Link>
                        <Link
                          to="/orders"
                          className="block px-4 py-2 text-gray-700 hover:bg-gray-100"
                        >
                          {t('nav.orders')}
                        </Link>
                        <hr className="my-2" />
                        <button
                          onClick={handleLogout}
                          className="block w-full text-left px-4 py-2 text-gray-700 hover:bg-gray-100"
                        >
                          {t('nav.logout')}
                        </button>
                      </>
                    ) : (
                      <>
                        <Link
                          to="/login"
                          className="block px-4 py-2 text-gray-700 hover:bg-gray-100"
                        >
                          {t('nav.login')}
                        </Link>
                        <Link
                          to="/register"
                          className="block px-4 py-2 text-gray-700 hover:bg-gray-100"
                        >
                          {t('nav.register')}
                        </Link>
                      </>
                    )}
                  </div>
                </div>

                {/* Cart */}
                <Link
                  to="/cart"
                  className="p-2 hover:bg-gray-100 rounded-full transition-colors relative"
                >
                  <ShoppingCartIcon className="h-6 w-6 text-gray-700" />
                  {cartItemCount > 0 && (
                    <span className="absolute -top-1 -right-1 h-5 w-5 bg-red-500 text-white rounded-full flex items-center justify-center text-xs font-bold">
                      {cartItemCount}
                    </span>
                  )}
                </Link>

                {/* Mobile Menu Toggle */}
                <button
                  onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                  className="md:hidden p-2 hover:bg-gray-100 rounded-full transition-colors"
                >
                  {isMobileMenuOpen ? (
                    <XIcon className="h-6 w-6 text-gray-700" />
                  ) : (
                    <MenuIcon className="h-6 w-6 text-gray-700" />
                  )}
                </button>
              </div>
            </div>

            {/* Mobile Search */}
            <div className={`md:hidden mt-4 ${isSearchOpen ? 'block' : 'hidden'}`}>
              <form onSubmit={handleSearch} className="relative">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder={t('search.placeholder')}
                  className="w-full pl-10 pr-4 py-2 rounded-full border border-gray-300 focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
                <SearchIcon className="absolute left-3 top-2.5 h-5 w-5 text-gray-400" />
              </form>
            </div>
          </div>
        </nav>

        {/* Mobile Menu */}
        {isMobileMenuOpen && (
          <div className="md:hidden border-t border-gray-200">
            <div className="py-2">
              <Link
                to="/"
                className="block px-4 py-2 text-gray-700 hover:bg-gray-100"
              >
                {t('nav.home')}
              </Link>
              <Link
                to="/products"
                className="block px-4 py-2 text-gray-700 hover:bg-gray-100"
              >
                {t('nav.products')}
              </Link>
              <button
                onClick={() => setIsSearchOpen(!isSearchOpen)}
                className="block w-full text-left px-4 py-2 text-gray-700 hover:bg-gray-100"
              >
                {t('nav.search')}
              </button>
            </div>
          </div>
        )}
      </header>

      {/* Main Content */}
      <main className="flex-grow">
        {children}
      </main>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-12 mt-auto">
        <div className="container-max">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            {/* Company Info */}
            <div>
              <h3 className="text-lg font-bold mb-4">WeedGo Commerce</h3>
              <p className="text-gray-400 mb-4">
                {t('footer.description')}
              </p>
              <div className="flex space-x-4">
                <a href="#" className="hover:text-primary-400">
                  <span className="text-2xl">📘</span>
                </a>
                <a href="#" className="hover:text-primary-400">
                  <span className="text-2xl">🐦</span>
                </a>
                <a href="#" className="hover:text-primary-400">
                  <span className="text-2xl">📷</span>
                </a>
              </div>
            </div>

            {/* Quick Links */}
            <div>
              <h3 className="text-lg font-bold mb-4">{t('footer.quickLinks')}</h3>
              <ul className="space-y-2">
                <li>
                  <Link to="/products" className="text-gray-400 hover:text-white">
                    {t('footer.allProducts')}
                  </Link>
                </li>
                <li>
                  <Link to="/products?category=flower" className="text-gray-400 hover:text-white">
                    {t('footer.flower')}
                  </Link>
                </li>
                <li>
                  <Link to="/products?category=edibles" className="text-gray-400 hover:text-white">
                    {t('footer.edibles')}
                  </Link>
                </li>
                <li>
                  <Link to="/products?category=concentrates" className="text-gray-400 hover:text-white">
                    {t('footer.concentrates')}
                  </Link>
                </li>
              </ul>
            </div>

            {/* Customer Service */}
            <div>
              <h3 className="text-lg font-bold mb-4">{t('footer.customerService')}</h3>
              <ul className="space-y-2">
                <li>
                  <Link to="/contact" className="text-gray-400 hover:text-white">
                    {t('footer.contact')}
                  </Link>
                </li>
                <li>
                  <Link to="/faq" className="text-gray-400 hover:text-white">
                    {t('footer.faq')}
                  </Link>
                </li>
                <li>
                  <Link to="/shipping" className="text-gray-400 hover:text-white">
                    {t('footer.shipping')}
                  </Link>
                </li>
                <li>
                  <Link to="/returns" className="text-gray-400 hover:text-white">
                    {t('footer.returns')}
                  </Link>
                </li>
              </ul>
            </div>

            {/* Newsletter */}
            <div>
              <h3 className="text-lg font-bold mb-4">{t('footer.newsletter')}</h3>
              <p className="text-gray-400 mb-4">
                {t('footer.newsletterText')}
              </p>
              <form className="flex">
                <input
                  type="email"
                  placeholder={t('footer.emailPlaceholder')}
                  className="flex-1 px-4 py-2 rounded-l-lg bg-gray-800 text-white border border-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
                <button
                  type="submit"
                  className="px-4 py-2 bg-primary-500 text-white rounded-r-lg hover:bg-primary-600 transition-colors"
                >
                  {t('footer.subscribe')}
                </button>
              </form>
            </div>
          </div>

          {/* Bottom Bar */}
          <div className="mt-12 pt-8 border-t border-gray-800">
            <div className="flex flex-col md:flex-row justify-between items-center">
              <p className="text-gray-400 text-sm">
                © 2024 WeedGo Commerce. {t('footer.allRights')}
              </p>
              <div className="flex space-x-6 mt-4 md:mt-0">
                <Link to="/privacy" className="text-gray-400 text-sm hover:text-white">
                  {t('footer.privacy')}
                </Link>
                <Link to="/terms" className="text-gray-400 text-sm hover:text-white">
                  {t('footer.terms')}
                </Link>
                <Link to="/age-verification" className="text-gray-400 text-sm hover:text-white">
                  {t('footer.ageVerification')}
                </Link>
              </div>
            </div>
          </div>
        </div>
      </footer>

      {/* Chat Interface */}
      {isChatOpen && (
        <ChatInterface onClose={() => setIsChatOpen(false)} />
      )}
    </div>
  );
};

export default MainLayout;