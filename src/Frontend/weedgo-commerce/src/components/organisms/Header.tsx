import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useSelector } from 'react-redux';
import { useTranslation } from 'react-i18next';
import {
  ShoppingCartIcon,
  UserIcon,
  Bars3Icon as MenuIcon,
  XMarkIcon as XIcon,
  HomeIcon,
  CubeIcon,
  ChatBubbleLeftRightIcon as ChatIcon
} from '@heroicons/react/24/outline';
import { RootState } from '@store/index';
import { Logo } from '../atoms/Logo';
import { Badge } from '../atoms/Badge';
import { Button } from '../atoms/Button';
import { SearchBar } from '../molecules/SearchBar';
import { LanguageSelector } from '../molecules/LanguageSelector';
import StoreSelector from '@components/common/StoreSelector';
import { useMediaQuery } from '@/hooks/useMediaQuery';
import { clsx } from 'clsx';

export interface HeaderProps {
  onChatToggle?: () => void;
  className?: string;
}

/**
 * Main application header with navigation, search, and user controls
 */
export const Header: React.FC<HeaderProps> = ({ onChatToggle, className }) => {
  const { t } = useTranslation();
  const location = useLocation();
  const isMobile = useMediaQuery('(max-width: 768px)');

  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);

  const { items } = useSelector((state: RootState) => state.cart);
  const { isAuthenticated, user } = useSelector((state: RootState) => state.auth);
  const cartItemCount = items.reduce((total, item) => total + item.quantity, 0);

  const navItems = [
    { path: '/', label: t('nav.home'), icon: HomeIcon },
    { path: '/products', label: t('nav.products'), icon: CubeIcon }
  ];

  return (
    <header className={clsx('sticky top-0 z-40 bg-white dark:bg-gray-900 shadow-md', className)}>
      {/* Top Bar */}
      <div className="bg-primary-600 dark:bg-primary-700 text-white py-2">
        <div className="container-max flex justify-between items-center text-sm">
          <div className="flex items-center space-x-4">
            <StoreSelector />
            <span className="hidden sm:inline">🕒 {t('header.hours')}: 9AM - 10PM</span>
          </div>
          <div className="flex items-center space-x-4">
            <LanguageSelector />
            <span className="hidden sm:inline">📞 1-800-WEEDGO</span>
          </div>
        </div>
      </div>

      {/* Main Navigation */}
      <nav className="py-4">
        <div className="container-max">
          <div className="flex items-center justify-between">
            {/* Logo */}
            <Logo size={isMobile ? 'sm' : 'md'} />

            {/* Desktop Navigation */}
            {!isMobile && (
              <>
                <div className="flex items-center space-x-6">
                  {navItems.map(item => (
                    <Link
                      key={item.path}
                      to={item.path}
                      className={clsx(
                        'flex items-center space-x-1 px-3 py-2 rounded-lg transition-colors',
                        location.pathname === item.path
                          ? 'bg-primary-50 text-primary-600 dark:bg-primary-900/30 dark:text-primary-400'
                          : 'hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300'
                      )}
                    >
                      <item.icon className="h-5 w-5" />
                      <span>{item.label}</span>
                    </Link>
                  ))}
                </div>

                {/* Search Bar */}
                <SearchBar variant="default" className="flex-1 mx-6" />

                {/* Desktop Actions */}
                <div className="flex items-center space-x-3">
                  {/* Chat Button */}
                  {onChatToggle && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={onChatToggle}
                      leftIcon={<ChatIcon className="h-5 w-5" />}
                      className="relative"
                    >
                      <span className="absolute -top-1 -right-1 h-3 w-3 bg-green-500 rounded-full animate-pulse" />
                    </Button>
                  )}

                  {/* User Menu */}
                  <UserMenu
                    isAuthenticated={isAuthenticated}
                    user={user}
                    isOpen={isUserMenuOpen}
                    onToggle={() => setIsUserMenuOpen(!isUserMenuOpen)}
                  />

                  {/* Cart */}
                  <Link to="/cart" className="relative">
                    <Button variant="ghost" size="sm" leftIcon={<ShoppingCartIcon className="h-5 w-5" />}>
                      {cartItemCount > 0 && (
                        <Badge variant="danger" size="xs" className="absolute -top-2 -right-2">
                          {cartItemCount}
                        </Badge>
                      )}
                    </Button>
                  </Link>
                </div>
              </>
            )}

            {/* Mobile Menu Toggle */}
            {isMobile && (
              <div className="flex items-center space-x-3">
                <Link to="/cart" className="relative p-2">
                  <ShoppingCartIcon className="h-6 w-6 text-gray-700 dark:text-gray-300" />
                  {cartItemCount > 0 && (
                    <Badge variant="danger" size="xs" className="absolute -top-1 -right-1">
                      {cartItemCount}
                    </Badge>
                  )}
                </Link>

                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                  leftIcon={isMobileMenuOpen ? <XIcon className="h-6 w-6" /> : <MenuIcon className="h-6 w-6" />}
                />
              </div>
            )}
          </div>

          {/* Mobile Menu */}
          {isMobile && isMobileMenuOpen && (
            <MobileMenu
              navItems={navItems}
              isAuthenticated={isAuthenticated}
              onClose={() => setIsMobileMenuOpen(false)}
            />
          )}
        </div>
      </nav>
    </header>
  );
};

// User Menu Component
const UserMenu: React.FC<{
  isAuthenticated: boolean;
  user: any;
  isOpen: boolean;
  onToggle: () => void;
}> = ({ isAuthenticated, user, isOpen, onToggle }) => {
  const { t } = useTranslation();

  return (
    <div className="relative">
      <Button
        variant="ghost"
        size="sm"
        onClick={onToggle}
        leftIcon={<UserIcon className="h-5 w-5" />}
      />

      {isOpen && (
        <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-gray-200 dark:border-gray-700 z-50">
          {isAuthenticated ? (
            <>
              <Link
                to="/profile"
                className="block px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                {t('nav.profile')}
              </Link>
              <Link
                to="/orders"
                className="block px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                {t('nav.orders')}
              </Link>
              <hr className="my-1 border-gray-200 dark:border-gray-700" />
              <button
                className="block w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                {t('nav.logout')}
              </button>
            </>
          ) : (
            <>
              <Link
                to="/login"
                className="block px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                {t('nav.login')}
              </Link>
              <Link
                to="/register"
                className="block px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                {t('nav.register')}
              </Link>
            </>
          )}
        </div>
      )}
    </div>
  );
};

// Mobile Menu Component
const MobileMenu: React.FC<{
  navItems: any[];
  isAuthenticated: boolean;
  onClose: () => void;
}> = ({ navItems, isAuthenticated, onClose }) => {
  const { t } = useTranslation();

  return (
    <div className="mt-4 py-4 border-t border-gray-200 dark:border-gray-700">
      <SearchBar variant="compact" className="mb-4" />

      <div className="space-y-2">
        {navItems.map(item => (
          <Link
            key={item.path}
            to={item.path}
            onClick={onClose}
            className="flex items-center space-x-2 px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
          >
            <item.icon className="h-5 w-5" />
            <span>{item.label}</span>
          </Link>
        ))}

        <hr className="my-2 border-gray-200 dark:border-gray-700" />

        {isAuthenticated ? (
          <>
            <Link
              to="/profile"
              onClick={onClose}
              className="block px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
            >
              {t('nav.profile')}
            </Link>
            <Link
              to="/orders"
              onClick={onClose}
              className="block px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
            >
              {t('nav.orders')}
            </Link>
          </>
        ) : (
          <>
            <Link
              to="/login"
              onClick={onClose}
              className="block px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
            >
              {t('nav.login')}
            </Link>
            <Link
              to="/register"
              onClick={onClose}
              className="block px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
            >
              {t('nav.register')}
            </Link>
          </>
        )}
      </div>
    </div>
  );
};