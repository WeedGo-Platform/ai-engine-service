import React from 'react';
import { Link } from 'react-router-dom';
import { ChevronRightIcon, HomeIcon } from '@heroicons/react/24/outline';

export interface BreadcrumbItem {
  name: string;
  url?: string;
  current?: boolean;
}

interface BreadcrumbsProps {
  items: BreadcrumbItem[];
  className?: string;
  separator?: 'chevron' | 'slash' | 'arrow';
  showHome?: boolean;
}

const Breadcrumbs: React.FC<BreadcrumbsProps> = ({
  items,
  className = '',
  separator = 'chevron',
  showHome = true
}) => {
  const getSeparator = () => {
    switch (separator) {
      case 'slash':
        return <span className="mx-2 text-gray-400">/</span>;
      case 'arrow':
        return <span className="mx-2 text-gray-400">→</span>;
      default:
        return <ChevronRightIcon className="h-4 w-4 mx-2 text-gray-400" />;
    }
  };

  const allItems = showHome
    ? [{ name: 'Home', url: '/' }, ...items]
    : items;

  return (
    <nav className={`flex items-center text-sm ${className}`} aria-label="Breadcrumb">
      <ol className="flex items-center space-x-1">
        {allItems.map((item, index) => (
          <li key={index} className="flex items-center">
            {index > 0 && getSeparator()}

            {index === 0 && showHome ? (
              <Link
                to={item.url || '/'}
                className="text-gray-500 hover:text-primary-600 transition-colors"
                aria-label="Home"
              >
                <HomeIcon className="h-4 w-4" />
              </Link>
            ) : item.current || !item.url ? (
              <span className="text-gray-900 font-medium" aria-current="page">
                {item.name}
              </span>
            ) : (
              <Link
                to={item.url}
                className="text-gray-500 hover:text-primary-600 transition-colors"
              >
                {item.name}
              </Link>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
};

export default Breadcrumbs;