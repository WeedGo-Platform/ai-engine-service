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
      icon: '🌱',
      title: 'Premium Quality',
      description: 'Carefully curated selection of top-tier cannabis products from trusted cultivators'
    },
    {
      icon: '🚚',
      title: 'Same-Day Delivery',
      description: 'Fast, discreet delivery to your door with real-time tracking and updates'
    },
    {
      icon: '🛡️',
      title: 'Licensed & Legal',
      description: 'Fully compliant with Ontario regulations, ensuring safe and legal transactions'
    }
  ];

  return (
    <div className="bg-[#FAFAF8]">
      {/* Use template Hero component */}
      <Hero
        title="Premium Cannabis, Delivered"
        subtitle="Experience quality and convenience with our curated selection of cannabis products, delivered directly to your door."
        primaryButton={{
          text: 'Browse Products',
          href: '/products'
        }}
        secondaryButton={!isAuthenticated ? {
          text: 'Create Account',
          href: '/register'
        } : undefined}
      />

      {/* Features Section with better spacing and hierarchy */}
      <div className="py-20 px-4 max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-display font-bold text-[#1F2937] mb-4">
            Why Choose Us
          </h2>
          <p className="text-lg text-[#6B7280] max-w-2xl mx-auto">
            We're committed to providing the best cannabis shopping experience in Ontario
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8">
          {features.map((feature, index) => (
            <CategoryCard
              key={index}
              category={{
                id: `feature-${index}`,
                name: feature.title,
                slug: feature.title.toLowerCase().replace(/\s+/g, '-'),
                description: feature.description,
                image: feature.icon
              }}
              title={feature.title}
              description={feature.description}
              icon={feature.icon}
              onClick={() => {}}
            />
          ))}
        </div>
      </div>

      {/* How It Works Section */}
      <div className="py-20 px-4 bg-white">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-display font-bold text-[#1F2937] mb-4">
              Simple, Safe, Secure
            </h2>
            <p className="text-lg text-[#6B7280] max-w-2xl mx-auto">
              Getting your favorite products has never been easier
            </p>
          </div>

          <div className="grid md:grid-cols-4 gap-8">
            {[
              { step: '01', title: 'Browse', description: 'Explore our curated selection of premium products' },
              { step: '02', title: 'Select', description: 'Choose your favorites and add them to your cart' },
              { step: '03', title: 'Checkout', description: 'Complete your order with secure payment options' },
              { step: '04', title: 'Enjoy', description: 'Receive same-day delivery right to your door' }
            ].map((item, index) => (
              <div key={index} className="text-center">
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-[#2D5F3F]/10 text-[#2D5F3F] font-display text-2xl font-bold mb-4">
                  {item.step}
                </div>
                <h3 className="text-xl font-semibold text-[#1F2937] mb-2">{item.title}</h3>
                <p className="text-[#6B7280] text-sm">{item.description}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Call to Action Section with better visual design */}
      <div className="py-24 px-4 text-center bg-gradient-to-br from-[#2D5F3F] to-[#3B7A55] text-white relative overflow-hidden">
        {/* Subtle background accent */}
        <div className="absolute top-20 right-20 w-64 h-64 bg-[#C9A86A] rounded-full opacity-10 blur-3xl" />
        <div className="absolute bottom-20 left-20 w-80 h-80 bg-white rounded-full opacity-5 blur-3xl" />

        <div className="relative z-10 max-w-3xl mx-auto">
          <h2 className="text-3xl md:text-4xl font-display font-bold mb-4">
            Ready to Experience the Difference?
          </h2>
          <p className="text-lg text-white/90 mb-10 max-w-2xl mx-auto">
            Join our community and discover premium cannabis products delivered with care
          </p>
          <div className="flex gap-4 justify-center flex-wrap">
            <Link to="/products">
              <Button variant="primary" size="lg" className="bg-white text-[#2D5F3F] hover:bg-[#C9A86A] hover:text-white">
                Shop Now
              </Button>
            </Link>
            {!isAuthenticated && (
              <Link to="/register">
                <Button variant="outline" size="lg" className="border-white text-white hover:bg-white hover:text-[#2D5F3F]">
                  Create Account
                </Button>
              </Link>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Home;