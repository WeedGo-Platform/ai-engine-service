import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { clsx } from 'clsx';
import { tenantApi, TenantSettings } from '@api/tenant';

export interface LogoProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  showText?: boolean;
  linkToHome?: boolean;
  className?: string;
}

/**
 * Logo component that displays the tenant's logo or business name
 * Responsive and theme-aware
 */
export const Logo: React.FC<LogoProps> = ({
  size = 'md',
  showText = true,
  linkToHome = true,
  className
}) => {
  const [tenant, setTenant] = useState<TenantSettings | null>(null);
  const tenantId = import.meta.env.VITE_TENANT_ID;

  useEffect(() => {
    if (tenantId) {
      tenantApi.getTenantSettings(tenantId).then(settings => {
        if (settings) {
          setTenant(settings);
          console.log('Tenant settings loaded:', settings);
        }
      }).catch(err => {
        console.error('Failed to load tenant settings:', err);
      });
    }
  }, [tenantId]);

  const sizeClasses = {
    sm: {
      height: 'h-8',
      text: 'text-xl'
    },
    md: {
      height: 'h-10',
      text: 'text-2xl'
    },
    lg: {
      height: 'h-12',
      text: 'text-3xl'
    },
    xl: {
      height: 'h-16',
      text: 'text-4xl'
    }
  };

  // Construct full logo URL
  const logoUrl = tenant?.logo_url ?
    (tenant.logo_url.startsWith('http') ? tenant.logo_url : `http://localhost:5024${tenant.logo_url}`)
    : null;

  const [imageError, setImageError] = useState(false);

  const logoContent = (
    <div className={clsx('flex items-center space-x-2', className)}>
      {logoUrl && !imageError ? (
        <img
          src={logoUrl}
          alt={tenant?.display_name || tenant?.business_name || tenant?.name || 'Logo'}
          className={clsx(
            sizeClasses[size].height,
            'object-contain'
          )}
          onError={(e) => {
            console.error('Logo failed to load:', logoUrl);
            setImageError(true);
          }}
        />
      ) : null}
      {showText && tenant && (
        <span
          className={clsx(
            sizeClasses[size].text,
            'font-bold text-primary-600 dark:text-primary-400'
          )}
        >
          {tenant.display_name || tenant.business_name || tenant.name || ''}
        </span>
      )}
    </div>
  );

  if (linkToHome) {
    return (
      <Link to="/" className="inline-block" aria-label="Home">
        {logoContent}
      </Link>
    );
  }

  return logoContent;
};

export default Logo;