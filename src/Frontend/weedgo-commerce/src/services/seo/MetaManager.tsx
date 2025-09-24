/**
 * SEO Meta Manager Component
 * Manages meta tags, structured data, and Open Graph/Twitter Card tags
 */

import React, { useEffect } from 'react';
import { Helmet } from 'react-helmet-async';
import {
  SEOMetaData,
  StructuredData,
  ProductStructuredData,
  LocalBusinessStructuredData,
  BreadcrumbStructuredData
} from '@/types/seo.types';

interface MetaManagerProps {
  meta: SEOMetaData;
  structuredData?: StructuredData[];
  breadcrumbs?: Array<{ name: string; url: string }>;
}

export const MetaManager: React.FC<MetaManagerProps> = ({
  meta,
  structuredData = [],
  breadcrumbs
}) => {
  // Generate breadcrumb structured data if breadcrumbs provided
  const breadcrumbStructuredData: BreadcrumbStructuredData | null = breadcrumbs ? {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: breadcrumbs.map((item, index) => ({
      '@type': 'ListItem',
      position: index + 1,
      name: item.name,
      item: item.url ? `${window.location.origin}${item.url}` : undefined
    }))
  } : null;

  // Combine all structured data
  const allStructuredData = [
    ...structuredData,
    ...(breadcrumbStructuredData ? [breadcrumbStructuredData] : [])
  ];

  return (
    <Helmet>
      {/* Basic Meta Tags */}
      <title>{meta.title}</title>
      <meta name="description" content={meta.description} />
      {meta.keywords && meta.keywords.length > 0 && (
        <meta name="keywords" content={meta.keywords.join(', ')} />
      )}
      {meta.author && <meta name="author" content={meta.author} />}
      {meta.robots && <meta name="robots" content={meta.robots} />}
      {meta.viewport && <meta name="viewport" content={meta.viewport} />}
      {meta.themeColor && <meta name="theme-color" content={meta.themeColor} />}

      {/* Canonical URL */}
      {meta.canonical && <link rel="canonical" href={meta.canonical} />}

      {/* Language and Region */}
      {meta.language && <meta httpEquiv="content-language" content={meta.language} />}
      {meta.alternateLanguages?.map((alt) => (
        <link key={alt.hreflang} rel="alternate" hrefLang={alt.hreflang} href={alt.href} />
      ))}

      {/* Open Graph Tags */}
      {meta.ogTitle && <meta property="og:title" content={meta.ogTitle} />}
      {meta.ogDescription && <meta property="og:description" content={meta.ogDescription} />}
      {meta.ogImage && <meta property="og:image" content={meta.ogImage} />}
      {meta.ogType && <meta property="og:type" content={meta.ogType} />}
      {meta.ogUrl && <meta property="og:url" content={meta.ogUrl} />}
      {meta.ogSiteName && <meta property="og:site_name" content={meta.ogSiteName} />}

      {/* Twitter Card Tags */}
      {meta.twitterCard && <meta name="twitter:card" content={meta.twitterCard} />}
      {meta.twitterTitle && <meta name="twitter:title" content={meta.twitterTitle} />}
      {meta.twitterDescription && <meta name="twitter:description" content={meta.twitterDescription} />}
      {meta.twitterImage && <meta name="twitter:image" content={meta.twitterImage} />}
      {meta.twitterSite && <meta name="twitter:site" content={meta.twitterSite} />}
      {meta.twitterCreator && <meta name="twitter:creator" content={meta.twitterCreator} />}

      {/* Structured Data */}
      {allStructuredData.map((data, index) => (
        <script
          key={index}
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(data) }}
        />
      ))}
    </Helmet>
  );
};

/**
 * Generate product structured data
 */
export const generateProductStructuredData = (product: {
  name: string;
  description: string;
  image: string | string[];
  brand: string;
  sku: string;
  price: number;
  currency: string;
  inStock: boolean;
  storeName: string;
  rating?: number;
  reviewCount?: number;
}): ProductStructuredData => {
  return {
    '@context': 'https://schema.org',
    '@type': 'Product',
    name: product.name,
    description: product.description,
    image: product.image,
    brand: {
      '@type': 'Brand',
      name: product.brand
    },
    sku: product.sku,
    offers: {
      '@type': 'Offer',
      url: window.location.href,
      priceCurrency: product.currency,
      price: product.price.toString(),
      availability: product.inStock
        ? 'https://schema.org/InStock'
        : 'https://schema.org/OutOfStock',
      seller: {
        '@type': 'Organization',
        name: product.storeName
      }
    },
    ...(product.rating && product.reviewCount ? {
      aggregateRating: {
        '@type': 'AggregateRating',
        ratingValue: product.rating.toString(),
        reviewCount: product.reviewCount.toString()
      }
    } : {})
  };
};

/**
 * Generate local business structured data
 */
export const generateLocalBusinessStructuredData = (business: {
  name: string;
  description: string;
  url: string;
  telephone: string;
  streetAddress: string;
  city: string;
  state: string;
  postalCode: string;
  country: string;
  latitude?: string;
  longitude?: string;
  openingHours?: Array<{
    dayOfWeek: string | string[];
    opens: string;
    closes: string;
  }>;
  priceRange?: string;
  image?: string | string[];
  socialProfiles?: string[];
}): LocalBusinessStructuredData => {
  return {
    '@context': 'https://schema.org',
    '@type': 'Dispensary',
    name: business.name,
    description: business.description,
    url: business.url,
    telephone: business.telephone,
    address: {
      '@type': 'PostalAddress',
      streetAddress: business.streetAddress,
      addressLocality: business.city,
      addressRegion: business.state,
      postalCode: business.postalCode,
      addressCountry: business.country
    },
    ...(business.latitude && business.longitude ? {
      geo: {
        '@type': 'GeoCoordinates',
        latitude: business.latitude,
        longitude: business.longitude
      }
    } : {}),
    ...(business.openingHours ? {
      openingHoursSpecification: business.openingHours.map(hours => ({
        '@type': 'OpeningHoursSpecification',
        dayOfWeek: hours.dayOfWeek,
        opens: hours.opens,
        closes: hours.closes
      }))
    } : {}),
    ...(business.priceRange ? { priceRange: business.priceRange } : {}),
    ...(business.image ? { image: business.image } : {}),
    ...(business.socialProfiles && business.socialProfiles.length > 0 ? {
      sameAs: business.socialProfiles
    } : {})
  };
};

/**
 * Generate default meta tags for product pages
 */
export const generateProductMetaTags = (product: {
  name: string;
  description: string;
  image?: string;
  price?: number;
  brand?: string;
  category?: string;
  thc?: number;
  cbd?: number;
}): SEOMetaData => {
  const title = `${product.name} | ${product.brand || ''} | Cannabis Dispensary Near Me`;
  const description = product.description.length > 160
    ? product.description.substring(0, 157) + '...'
    : product.description;

  const keywords = [
    product.name,
    product.brand,
    product.category,
    'cannabis',
    'dispensary',
    'weed',
    'marijuana',
    product.thc ? `${product.thc}% THC` : null,
    product.cbd ? `${product.cbd}% CBD` : null
  ].filter(Boolean) as string[];

  return {
    title,
    description,
    keywords,
    canonical: window.location.href.split('?')[0],
    ogTitle: title,
    ogDescription: description,
    ogImage: product.image,
    ogType: 'product',
    ogUrl: window.location.href,
    twitterCard: 'summary_large_image',
    twitterTitle: title,
    twitterDescription: description,
    twitterImage: product.image,
    robots: 'index,follow',
    viewport: 'width=device-width, initial-scale=1.0'
  };
};

/**
 * Generate default meta tags for category pages
 */
export const generateCategoryMetaTags = (category: {
  name: string;
  description?: string;
  productCount?: number;
  city?: string;
}): SEOMetaData => {
  const cityText = category.city ? `in ${category.city}` : '';
  const title = `${category.name} Cannabis Products ${cityText} | Dispensary Near Me`;
  const description = category.description ||
    `Browse our selection of ${category.name.toLowerCase()} cannabis products ${cityText}. ${
      category.productCount ? `${category.productCount} products available.` : ''
    } Same-day delivery and pickup available.`;

  return {
    title,
    description,
    keywords: [
      category.name,
      'cannabis',
      category.city,
      'dispensary',
      'delivery',
      'near me'
    ].filter(Boolean) as string[],
    canonical: window.location.href.split('?')[0],
    ogTitle: title,
    ogDescription: description,
    ogType: 'website',
    ogUrl: window.location.href,
    twitterCard: 'summary',
    twitterTitle: title,
    twitterDescription: description,
    robots: 'index,follow',
    viewport: 'width=device-width, initial-scale=1.0'
  };
};