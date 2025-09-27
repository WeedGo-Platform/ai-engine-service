import React from 'react';
import { IBreadcrumbsProps } from '../../types';
import { clsx } from 'clsx';

export const PotPalaceBreadcrumbs: React.FC<IBreadcrumbsProps> = ({
  items,
  separator = '→',
  className
}) => {
  return (
    <nav className={clsx('flex items-center gap-2', className)}>
      {items.map((item, index) => (
        <React.Fragment key={index}>
          {index > 0 && (
            <span className="text-green-400 font-bold">{separator}</span>
          )}
          {item.href ? (
            <a
              href={item.href}
              className="text-gray-700 hover:text-green-600 font-semibold transition-colors"
            >
              {item.label}
            </a>
          ) : (
            <span className="text-gray-800 font-bold">
              {item.label}
            </span>
          )}
        </React.Fragment>
      ))}
    </nav>
  );
};
