import React from 'react';
import { Link } from 'react-router-dom';
import { useSelector } from 'react-redux';
import { RootState } from '@store/index';
import { useSEO } from '@hooks/useSEO';
import { useTemplateComponents } from '@templates/TemplateProvider';

const Home: React.FC = () => {
  const { isAuthenticated } = useSelector((state: RootState) => state.auth);

  // Get template components
  const { Button, Hero, CategoryCard, Badge } = useTemplateComponents();

  // SEO Configuration
  useSEO({
    title: 'Cannabis Dispensary Near Me | Same-Day Delivery',
    description: 'Premium cannabis delivery at your fingertips. Browse our selection of top-quality products and get them delivered to your door. Order online for same-day delivery.',
    keywords: ['cannabis', 'dispensary', 'delivery', 'near me', 'weed', 'marijuana'],
    ogTitle: 'Cannabis Dispensary Near Me | Same-Day Delivery',
    ogDescription: 'Premium cannabis delivery at your fingertips. Order online for same-day delivery.',
  });

  const features = [
    {
      icon: '💰',
      title: 'Best Prices',
      description: 'Competitive pricing on all premium cannabis products'
    },
    {
      icon: '⚡',
      title: 'Fast Delivery',
      description: 'Same-day delivery available in select areas'
    },
    {
      icon: '✅',
      title: 'Safe & Legal',
      description: 'Fully licensed and compliant with Ontario regulations'
    }
  ];

  return (
    <>
      {/* Use template Hero component */}
      <Hero
        title="Welcome to WeedGo Commerce"
        subtitle="Premium cannabis delivery at your fingertips. Browse our selection of top-quality products and get them delivered to your door."
        primaryButton={{
          text: 'Browse Products',
          href: '/products'
        }}
        secondaryButton={!isAuthenticated ? {
          text: 'Create Account',
          href: '/register'
        } : undefined}
      />

      {/* Features Section using template components */}
      <div className="py-16 px-4 max-w-7xl mx-auto">
        <div className="grid md:grid-cols-3 gap-8">
          {features.map((feature, index) => (
            <CategoryCard
              key={index}
              title={feature.title}
              description={feature.description}
              icon={feature.icon}
              onClick={() => {}}
            />
          ))}
        </div>
      </div>

      {/* Call to Action Section */}
      <div className="py-20 px-4 text-center bg-gray-50">
        <h2 className="text-3xl font-bold mb-4">Ready to Get Started?</h2>
        <p className="text-lg text-gray-600 mb-8 max-w-2xl mx-auto">
          Join thousands of satisfied customers.
        </p>
        <div className="flex gap-4 justify-center flex-wrap">
          <Link to="/products">
            <Button variant="primary" size="lg">
              Shop Now
            </Button>
          </Link>
          {!isAuthenticated && (
            <Link to="/register">
              <Button variant="secondary" size="lg">
                Create Account
              </Button>
            </Link>
          )}
        </div>
      </div>
    </>
  );
};

export default Home;