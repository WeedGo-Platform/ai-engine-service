/**
 * Custom hook for SEO management
 * Provides utilities for managing canonical URLs, meta tags, and SEO data
 */

import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';

interface SEOConfig {
  title?: string;
  description?: string;
  canonical?: string;
  noindex?: boolean;
  nofollow?: boolean;
  ogImage?: string;
  ogTitle?: string;
  ogDescription?: string;
  twitterCard?: string;
  keywords?: string[];
  author?: string;
}

/**
 * Generate canonical URL from current location
 */
export const useCanonicalURL = (customPath?: string): string => {
  const location = useLocation();
  const baseUrl = window.location.origin;

  // Use custom path if provided, otherwise use current pathname
  const path = customPath || location.pathname;

  // Remove trailing slash except for homepage
  const cleanPath = path === '/' ? path : path.replace(/\/$/, '');

  // Remove query parameters for canonical URL
  const canonicalPath = cleanPath.split('?')[0];

  return `${baseUrl}${canonicalPath}`;
};

/**
 * Main SEO hook for managing page metadata
 */
export const useSEO = (config: SEOConfig) => {
  const canonicalUrl = useCanonicalURL(config.canonical);

  // Build robots meta content
  const robotsContent = [
    config.noindex ? 'noindex' : 'index',
    config.nofollow ? 'nofollow' : 'follow'
  ].join(',');

  useEffect(() => {
    // Set canonical URL
    const existingCanonical = document.querySelector('link[rel="canonical"]');
    if (existingCanonical) {
      existingCanonical.setAttribute('href', canonicalUrl);
    } else {
      const link = document.createElement('link');
      link.rel = 'canonical';
      link.href = canonicalUrl;
      document.head.appendChild(link);
    }

    // Cleanup function
    return () => {
      const canonical = document.querySelector('link[rel="canonical"]');
      if (canonical && canonical.getAttribute('href') === canonicalUrl) {
        canonical.remove();
      }
    };
  }, [canonicalUrl]);

  return {
    canonicalUrl,
    robotsContent
  };
};

/**
 * Hook for pagination SEO
 */
export const usePaginationSEO = (currentPage: number, totalPages: number, basePath: string) => {
  const location = useLocation();
  const baseUrl = window.location.origin;

  const prevUrl = currentPage > 1 ? `${baseUrl}${basePath}?page=${currentPage - 1}` : null;
  const nextUrl = currentPage < totalPages ? `${baseUrl}${basePath}?page=${currentPage + 1}` : null;

  useEffect(() => {
    // Add rel="prev" link
    if (prevUrl) {
      const existingPrev = document.querySelector('link[rel="prev"]');
      if (existingPrev) {
        existingPrev.setAttribute('href', prevUrl);
      } else {
        const link = document.createElement('link');
        link.rel = 'prev';
        link.href = prevUrl;
        document.head.appendChild(link);
      }
    }

    // Add rel="next" link
    if (nextUrl) {
      const existingNext = document.querySelector('link[rel="next"]');
      if (existingNext) {
        existingNext.setAttribute('href', nextUrl);
      } else {
        const link = document.createElement('link');
        link.rel = 'next';
        link.href = nextUrl;
        document.head.appendChild(link);
      }
    }

    // Cleanup
    return () => {
      const prevLink = document.querySelector('link[rel="prev"]');
      const nextLink = document.querySelector('link[rel="next"]');
      if (prevLink) prevLink.remove();
      if (nextLink) nextLink.remove();
    };
  }, [prevUrl, nextUrl]);

  return { prevUrl, nextUrl };
};

/**
 * Hook for alternate language SEO
 */
export const useAlternateLangSEO = (languages: Array<{ lang: string; url: string }>) => {
  useEffect(() => {
    const links: HTMLLinkElement[] = [];

    languages.forEach(({ lang, url }) => {
      const link = document.createElement('link');
      link.rel = 'alternate';
      link.hreflang = lang;
      link.href = url;
      document.head.appendChild(link);
      links.push(link);
    });

    // Cleanup
    return () => {
      links.forEach(link => link.remove());
    };
  }, [languages]);
};

export default useSEO;