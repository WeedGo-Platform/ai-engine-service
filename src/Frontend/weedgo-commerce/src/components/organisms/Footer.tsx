import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Logo } from '../atoms/Logo';
import { Button } from '../atoms/Button';
import { Input } from '../atoms/Input';
import { clsx } from 'clsx';
import toast from 'react-hot-toast';
import apiClient from '@api/client';

export interface FooterProps {
  className?: string;
}

/**
 * Application footer with links, newsletter, and company info
 */
export const Footer: React.FC<FooterProps> = ({ className }) => {
  const { t } = useTranslation();
  const [email, setEmail] = useState('');
  const [isSubscribing, setIsSubscribing] = useState(false);

  const handleNewsletterSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;

    // Validate email
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      toast.error('Please enter a valid email address');
      return;
    }

    setIsSubscribing(true);
    try {
      await apiClient.post('/api/newsletter/subscribe', { email });
      toast.success(t('footer.newsletterSuccess'));
      setEmail('');
    } catch (error: any) {
      const message = error.response?.data?.message || t('footer.newsletterError');
      toast.error(message);
    } finally {
      setIsSubscribing(false);
    }
  };

  const socialLinks = [
    { name: 'Facebook', icon: '📘', href: '#' },
    { name: 'Twitter', icon: '🐦', href: '#' },
    { name: 'Instagram', icon: '📷', href: '#' },
    { name: 'LinkedIn', icon: '💼', href: '#' }
  ];

  const footerLinks = {
    products: [
      { label: t('footer.allProducts'), path: '/products' },
      { label: t('footer.flower'), path: '/products?category=flower' },
      { label: t('footer.edibles'), path: '/products?category=edibles' },
      { label: t('footer.concentrates'), path: '/products?category=concentrates' },
      { label: t('footer.accessories'), path: '/products?category=accessories' }
    ],
    support: [
      { label: t('footer.contact'), path: '/contact' },
      { label: t('footer.faq'), path: '/faq' },
      { label: t('footer.shipping'), path: '/shipping' },
      { label: t('footer.returns'), path: '/returns' },
      { label: t('footer.trackOrder'), path: '/track-order' }
    ],
    company: [
      { label: t('footer.about'), path: '/about' },
      { label: t('footer.careers'), path: '/careers' },
      { label: t('footer.blog'), path: '/blog' },
      { label: t('footer.partners'), path: '/partners' },
      { label: t('footer.press'), path: '/press' }
    ],
    legal: [
      { label: t('footer.privacy'), path: '/privacy' },
      { label: t('footer.terms'), path: '/terms' },
      { label: t('footer.ageVerification'), path: '/age-verification' },
      { label: t('footer.accessibility'), path: '/accessibility' },
      { label: t('footer.cookies'), path: '/cookies' }
    ]
  };

  return (
    <footer className={clsx('bg-gray-900 dark:bg-gray-950 text-white', className)}>
      {/* Main Footer Content */}
      <div className="container-max py-12">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-8">
          {/* Company Info */}
          <div className="lg:col-span-2">
            <Logo showText={true} size="lg" className="mb-4" />
            <p className="text-gray-400 mb-6 text-sm leading-relaxed">
              {t('footer.description')}
            </p>

            {/* Social Links */}
            <div className="flex space-x-3">
              {socialLinks.map(social => (
                <a
                  key={social.name}
                  href={social.href}
                  className="w-10 h-10 flex items-center justify-center rounded-lg bg-gray-800 hover:bg-gray-700 transition-colors"
                  aria-label={social.name}
                >
                  <span className="text-xl">{social.icon}</span>
                </a>
              ))}
            </div>
          </div>

          {/* Products */}
          <div>
            <h3 className="text-lg font-semibold mb-4">{t('footer.products')}</h3>
            <ul className="space-y-2">
              {footerLinks.products.map(link => (
                <li key={link.path}>
                  <Link
                    to={link.path}
                    className="text-gray-400 hover:text-white text-sm transition-colors"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Customer Support */}
          <div>
            <h3 className="text-lg font-semibold mb-4">{t('footer.customerService')}</h3>
            <ul className="space-y-2">
              {footerLinks.support.map(link => (
                <li key={link.path}>
                  <Link
                    to={link.path}
                    className="text-gray-400 hover:text-white text-sm transition-colors"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Newsletter */}
          <div className="lg:col-span-2">
            <h3 className="text-lg font-semibold mb-4">{t('footer.newsletter')}</h3>
            <p className="text-gray-400 text-sm mb-4">
              {t('footer.newsletterText')}
            </p>

            <form onSubmit={handleNewsletterSubmit} className="flex flex-col sm:flex-row gap-2">
              <Input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder={t('footer.emailPlaceholder')}
                required
                className="flex-1"
                variant="filled"
              />
              <Button
                type="submit"
                variant="primary"
                isLoading={isSubscribing}
              >
                {t('footer.subscribe')}
              </Button>
            </form>

            <p className="text-xs text-gray-500 mt-3">
              {t('footer.newsletterDisclaimer')}
            </p>
          </div>
        </div>

        {/* Additional Links Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mt-12 pt-8 border-t border-gray-800">
          <div>
            <h4 className="text-sm font-semibold mb-3 text-gray-300">{t('footer.company')}</h4>
            <ul className="space-y-2">
              {footerLinks.company.map(link => (
                <li key={link.path}>
                  <Link
                    to={link.path}
                    className="text-gray-500 hover:text-gray-300 text-xs transition-colors"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h4 className="text-sm font-semibold mb-3 text-gray-300">{t('footer.legal')}</h4>
            <ul className="space-y-2">
              {footerLinks.legal.map(link => (
                <li key={link.path}>
                  <Link
                    to={link.path}
                    className="text-gray-500 hover:text-gray-300 text-xs transition-colors"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          <div className="col-span-2">
            <h4 className="text-sm font-semibold mb-3 text-gray-300">{t('footer.contact')}</h4>
            <div className="space-y-2 text-xs text-gray-500">
              <p>📍 123 Cannabis Street, Toronto, ON M5V 3A8</p>
              <p>📞 1-800-WEEDGO (1-800-933-346)</p>
              <p>📧 support@weedgo.com</p>
              <p>🕒 Mon-Sun: 9:00 AM - 10:00 PM EST</p>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Bar */}
      <div className="border-t border-gray-800 bg-black/30">
        <div className="container-max py-4">
          <div className="flex flex-col md:flex-row justify-between items-center text-xs text-gray-500">
            <div className="mb-2 md:mb-0">
              © {new Date().getFullYear()} WeedGo Commerce. {t('footer.allRights')}
            </div>

            <div className="flex items-center space-x-4">
              <span className="flex items-center">
                <svg className="w-4 h-4 mr-1 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M2.166 4.999A11.954 11.954 0 0010 1.944 11.954 11.954 0 0017.834 5c.11.65.166 1.32.166 2.001 0 5.225-3.34 9.67-8 11.317C5.34 16.67 2 12.225 2 7c0-.682.057-1.35.166-2.001zm11.541 3.708a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                {t('footer.securePayments')}
              </span>

              <span className="flex items-center">
                <svg className="w-4 h-4 mr-1 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                {t('footer.ageVerified')}
              </span>

              <span className="flex items-center">
                <svg className="w-4 h-4 mr-1 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M8.433 7.418c.155-.103.346-.196.567-.267v1.698a2.305 2.305 0 01-.567-.267C8.07 8.34 8 8.114 8 8c0-.114.07-.34.433-.582zM11 12.849v-1.698c.22.071.412.164.567.267.364.243.433.468.433.582 0 .114-.07.34-.433.582a2.305 2.305 0 01-.567.267z" />
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-13a1 1 0 10-2 0v.092a4.535 4.535 0 00-1.676.662C6.602 6.234 6 7.009 6 8c0 .99.602 1.765 1.324 2.246.48.32 1.054.545 1.676.662v1.941c-.391-.127-.68-.317-.843-.504a1 1 0 10-1.51 1.31c.562.649 1.413 1.076 2.353 1.253V15a1 1 0 102 0v-.092a4.535 4.535 0 001.676-.662C13.398 13.766 14 12.991 14 12c0-.99-.602-1.765-1.324-2.246A4.535 4.535 0 0011 9.092V7.151c.391.127.68.317.843.504a1 1 0 101.511-1.31c-.563-.649-1.413-1.076-2.354-1.253V5z" clipRule="evenodd" />
                </svg>
                {t('footer.licensedRetailer')}
              </span>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
};