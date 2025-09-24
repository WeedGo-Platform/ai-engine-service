import React, { useState, useEffect, useRef } from 'react';
import { LazyLoadImage } from 'react-lazy-load-image-component';
import 'react-lazy-load-image-component/src/effects/blur.css';

interface OptimizedImageProps {
  src: string;
  alt: string;
  title?: string;
  className?: string;
  width?: number | string;
  height?: number | string;
  loading?: 'lazy' | 'eager';
  sizes?: string;
  srcSet?: string;
  placeholder?: string;
  onLoad?: () => void;
  onError?: () => void;
  useLazyLoad?: boolean;
  priority?: boolean;
  objectFit?: 'contain' | 'cover' | 'fill' | 'none' | 'scale-down';
}

const OptimizedImage: React.FC<OptimizedImageProps> = ({
  src,
  alt,
  title,
  className = '',
  width,
  height,
  loading = 'lazy',
  sizes,
  srcSet,
  placeholder = '/placeholder.png',
  onLoad,
  onError,
  useLazyLoad = true,
  priority = false,
  objectFit = 'cover',
}) => {
  const [imageSrc, setImageSrc] = useState<string>(src);
  const [isError, setIsError] = useState(false);
  const imgRef = useRef<HTMLImageElement>(null);

  useEffect(() => {
    setImageSrc(src);
    setIsError(false);
  }, [src]);

  const handleError = () => {
    setIsError(true);
    setImageSrc(placeholder);
    onError?.();
  };

  const handleLoad = () => {
    setIsError(false);
    onLoad?.();
  };

  // Generate optimized srcSet for different screen sizes
  const generateSrcSet = () => {
    if (srcSet) return srcSet;

    // If it's a product image, generate multiple sizes
    if (src.includes('product') || src.includes('ocs')) {
      const sizes = [320, 640, 768, 1024, 1280];
      return sizes
        .map(size => {
          // This assumes your image server supports size parameters
          const url = new URL(src);
          url.searchParams.set('w', size.toString());
          return `${url.toString()} ${size}w`;
        })
        .join(', ');
    }

    return undefined;
  };

  // Generate sizes attribute for responsive images
  const generateSizes = () => {
    if (sizes) return sizes;

    // Default responsive sizes
    return '(max-width: 640px) 100vw, (max-width: 768px) 50vw, 33vw';
  };

  // Generate descriptive alt text if not provided
  const generateAltText = () => {
    if (alt) return alt;

    // Extract meaningful text from URL
    const filename = src.split('/').pop()?.split('?')[0] || '';
    const name = filename
      .replace(/\.[^/.]+$/, '') // Remove extension
      .replace(/[-_]/g, ' ') // Replace separators with spaces
      .replace(/\b\w/g, l => l.toUpperCase()); // Capitalize words

    return `${name} - Cannabis Product Image`;
  };

  const imageProps = {
    src: imageSrc,
    alt: generateAltText(),
    title: title || generateAltText(),
    className: `${className} ${isError ? 'opacity-50' : ''}`,
    width,
    height,
    onError: handleError,
    onLoad: handleLoad,
    style: { objectFit },
  };

  // For priority images, don't use lazy loading
  if (priority || !useLazyLoad) {
    return (
      <img
        {...imageProps}
        ref={imgRef}
        loading={priority ? 'eager' : loading}
        srcSet={generateSrcSet()}
        sizes={generateSizes()}
        decoding="async"
        fetchPriority={priority ? 'high' : 'auto'}
      />
    );
  }

  // Use lazy loading component for non-priority images
  return (
    <LazyLoadImage
      {...imageProps}
      effect="blur"
      placeholderSrc={placeholder}
      threshold={100}
      delayTime={0}
      delayMethod="debounce"
      srcSet={generateSrcSet()}
      sizes={generateSizes()}
    />
  );
};

export default OptimizedImage;