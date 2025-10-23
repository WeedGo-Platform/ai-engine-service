/**
 * Advanced filter panel for product search
 */

import React, { useState, useEffect } from 'react';
import {
  FunnelIcon,
  XMarkIcon,
  ChevronDownIcon,
  ChevronUpIcon,
} from '@heroicons/react/24/outline';
import { StarIcon } from '@heroicons/react/20/solid';
import type { SearchFilters } from '@services/searchService';
import { searchService } from '@services/searchService';

interface FilterPanelProps {
  filters: SearchFilters;
  onFiltersChange: (filters: SearchFilters) => void;
  onReset?: () => void;
  className?: string;
  isMobile?: boolean;
}

interface FilterOptions {
  categories: Array<{ value: string; label: string; count: number }>;
  brands: Array<{ value: string; label: string; count: number }>;
  strains: Array<{ value: string; label: string; count: number }>;
  priceRange: { min: number; max: number };
  thcRange: { min: number; max: number };
  cbdRange: { min: number; max: number };
}

const FilterPanel: React.FC<FilterPanelProps> = ({
  filters,
  onFiltersChange,
  onReset,
  className = '',
  isMobile = false,
}) => {
  const [isOpen, setIsOpen] = useState(!isMobile);
  const [filterOptions, setFilterOptions] = useState<FilterOptions>({
    categories: [],
    brands: [],
    strains: [],
    priceRange: { min: 0, max: 1000 },
    thcRange: { min: 0, max: 30 },
    cbdRange: { min: 0, max: 30 },
  });

  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set(['category', 'price', 'availability'])
  );

  // Fetch filter options
  useEffect(() => {
    const fetchOptions = async () => {
      try {
        const options = await searchService.getFilterOptions(filters.category);
        setFilterOptions(options);
      } catch (error) {
        console.error('Failed to fetch filter options:', error);
      }
    };

    fetchOptions();
  }, [filters.category]);

  const toggleSection = (section: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(section)) {
      newExpanded.delete(section);
    } else {
      newExpanded.add(section);
    }
    setExpandedSections(newExpanded);
  };

  const handleFilterChange = (key: keyof SearchFilters, value: any) => {
    onFiltersChange({
      ...filters,
      [key]: value,
    });
  };

  const handlePriceRangeChange = (min?: number, max?: number) => {
    onFiltersChange({
      ...filters,
      priceMin: min,
      priceMax: max,
    });
  };

  const handleTHCRangeChange = (min?: number, max?: number) => {
    onFiltersChange({
      ...filters,
      thcMin: min,
      thcMax: max,
    });
  };

  const handleCBDRangeChange = (min?: number, max?: number) => {
    onFiltersChange({
      ...filters,
      cbdMin: min,
      cbdMax: max,
    });
  };

  const handleReset = () => {
    if (onReset) {
      onReset();
    } else {
      onFiltersChange({});
    }
  };

  const getActiveFilterCount = () => {
    let count = 0;
    if (filters.category) count++;
    if (filters.brand) count++;
    if (filters.strain) count++;
    if (filters.priceMin !== undefined || filters.priceMax !== undefined) count++;
    if (filters.thcMin !== undefined || filters.thcMax !== undefined) count++;
    if (filters.cbdMin !== undefined || filters.cbdMax !== undefined) count++;
    if (filters.inStock !== undefined) count++;
    if (filters.onSale !== undefined) count++;
    if (filters.rating !== undefined) count++;
    return count;
  };

  const renderFilterSection = (
    title: string,
    key: string,
    children: React.ReactNode
  ) => {
    const isExpanded = expandedSections.has(key);

    return (
      <div className="border-b border-gray-200 py-4">
        <button
          onClick={() => toggleSection(key)}
          className="flex items-center justify-between w-full text-left"
          aria-expanded={isExpanded}
          aria-controls={`filter-section-${key}`}
        >
          <span className="text-sm font-medium text-gray-900">{title}</span>
          {isExpanded ? (
            <ChevronUpIcon className="h-4 w-4 text-gray-400" />
          ) : (
            <ChevronDownIcon className="h-4 w-4 text-gray-400" />
          )}
        </button>
        {isExpanded && (
          <div id={`filter-section-${key}`} className="mt-4">
            {children}
          </div>
        )}
      </div>
    );
  };

  const renderContent = () => (
    <div className="space-y-4">
      {/* Active filter count */}
      {getActiveFilterCount() > 0 && (
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600">
            {getActiveFilterCount()} filters applied
          </span>
          <button
            onClick={handleReset}
            className="text-sm text-blue-600 hover:text-blue-800"
          >
            Clear all
          </button>
        </div>
      )}

      {/* Categories */}
      {filterOptions.categories.length > 0 &&
        renderFilterSection(
          'Categories',
          'category',
          <div className="space-y-2">
            {filterOptions.categories.map((category) => (
              <label
                key={category.value}
                className="flex items-center justify-between cursor-pointer hover:bg-gray-50 p-1 rounded"
              >
                <div className="flex items-center">
                  <input
                    type="radio"
                    name="category"
                    value={category.value}
                    checked={filters.category === category.value}
                    onChange={(e) =>
                      handleFilterChange(
                        'category',
                        e.target.checked ? category.value : undefined
                      )
                    }
                    className="h-4 w-4 text-green-600 border-gray-300 focus:ring-green-500"
                  />
                  <span className="ml-2 text-sm text-gray-700">
                    {category.label}
                  </span>
                </div>
                <span className="text-xs text-gray-500">({category.count})</span>
              </label>
            ))}
          </div>
        )}

      {/* Price Range */}
      {renderFilterSection(
        'Price',
        'price',
        <div className="space-y-3">
          <div className="flex gap-2">
            <input
              type="number"
              placeholder="Min"
              value={filters.priceMin || ''}
              onChange={(e) =>
                handlePriceRangeChange(
                  e.target.value ? parseFloat(e.target.value) : undefined,
                  filters.priceMax
                )
              }
              className="w-1/2 px-3 py-1 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-green-500 text-sm"
              min={filterOptions.priceRange.min}
              max={filterOptions.priceRange.max}
            />
            <input
              type="number"
              placeholder="Max"
              value={filters.priceMax || ''}
              onChange={(e) =>
                handlePriceRangeChange(
                  filters.priceMin,
                  e.target.value ? parseFloat(e.target.value) : undefined
                )
              }
              className="w-1/2 px-3 py-1 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-green-500 text-sm"
              min={filterOptions.priceRange.min}
              max={filterOptions.priceRange.max}
            />
          </div>
          <div className="flex justify-between text-xs text-gray-500">
            <span>${filterOptions.priceRange.min}</span>
            <span>${filterOptions.priceRange.max}</span>
          </div>
        </div>
      )}

      {/* Brands */}
      {filterOptions.brands.length > 0 &&
        renderFilterSection(
          'Brands',
          'brand',
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {filterOptions.brands.map((brand) => (
              <label
                key={brand.value}
                className="flex items-center justify-between cursor-pointer hover:bg-gray-50 p-1 rounded"
              >
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    value={brand.value}
                    checked={filters.brand === brand.value}
                    onChange={(e) =>
                      handleFilterChange(
                        'brand',
                        e.target.checked ? brand.value : undefined
                      )
                    }
                    className="h-4 w-4 text-green-600 border-gray-300 rounded focus:ring-green-500"
                  />
                  <span className="ml-2 text-sm text-gray-700">
                    {brand.label}
                  </span>
                </div>
                <span className="text-xs text-gray-500">({brand.count})</span>
              </label>
            ))}
          </div>
        )}

      {/* Strains */}
      {filterOptions.strains.length > 0 &&
        renderFilterSection(
          'Strains',
          'strain',
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {filterOptions.strains.map((strain) => (
              <label
                key={strain.value}
                className="flex items-center justify-between cursor-pointer hover:bg-gray-50 p-1 rounded"
              >
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    value={strain.value}
                    checked={filters.strain?.includes(strain.value) || false}
                    onChange={(e) =>
                      handleFilterChange(
                        'strain',
                        e.target.checked ? strain.value : undefined
                      )
                    }
                    className="h-4 w-4 text-green-600 border-gray-300 rounded focus:ring-green-500"
                  />
                  <span className="ml-2 text-sm text-gray-700">
                    {strain.label}
                  </span>
                </div>
                <span className="text-xs text-gray-500">({strain.count})</span>
              </label>
            ))}
          </div>
        )}

      {/* THC Range */}
      {renderFilterSection(
        'THC Content',
        'thc',
        <div className="space-y-3">
          <div className="flex gap-2">
            <input
              type="number"
              placeholder="Min %"
              value={filters.thcMin || ''}
              onChange={(e) =>
                handleTHCRangeChange(
                  e.target.value ? parseFloat(e.target.value) : undefined,
                  filters.thcMax
                )
              }
              className="w-1/2 px-3 py-1 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-green-500 text-sm"
              min={0}
              max={30}
              step={0.1}
            />
            <input
              type="number"
              placeholder="Max %"
              value={filters.thcMax || ''}
              onChange={(e) =>
                handleTHCRangeChange(
                  filters.thcMin,
                  e.target.value ? parseFloat(e.target.value) : undefined
                )
              }
              className="w-1/2 px-3 py-1 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-green-500 text-sm"
              min={0}
              max={30}
              step={0.1}
            />
          </div>
          <div className="flex justify-between text-xs text-gray-500">
            <span>0%</span>
            <span>30%</span>
          </div>
        </div>
      )}

      {/* CBD Range */}
      {renderFilterSection(
        'CBD Content',
        'cbd',
        <div className="space-y-3">
          <div className="flex gap-2">
            <input
              type="number"
              placeholder="Min %"
              value={filters.cbdMin || ''}
              onChange={(e) =>
                handleCBDRangeChange(
                  e.target.value ? parseFloat(e.target.value) : undefined,
                  filters.cbdMax
                )
              }
              className="w-1/2 px-3 py-1 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-green-500 text-sm"
              min={0}
              max={30}
              step={0.1}
            />
            <input
              type="number"
              placeholder="Max %"
              value={filters.cbdMax || ''}
              onChange={(e) =>
                handleCBDRangeChange(
                  filters.cbdMin,
                  e.target.value ? parseFloat(e.target.value) : undefined
                )
              }
              className="w-1/2 px-3 py-1 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-green-500 text-sm"
              min={0}
              max={30}
              step={0.1}
            />
          </div>
          <div className="flex justify-between text-xs text-gray-500">
            <span>0%</span>
            <span>30%</span>
          </div>
        </div>
      )}

      {/* Availability */}
      {renderFilterSection(
        'Availability',
        'availability',
        <div className="space-y-2">
          <label className="flex items-center cursor-pointer hover:bg-gray-50 p-1 rounded">
            <input
              type="checkbox"
              checked={filters.inStock === true}
              onChange={(e) =>
                handleFilterChange('inStock', e.target.checked || undefined)
              }
              className="h-4 w-4 text-green-600 border-gray-300 rounded focus:ring-green-500"
            />
            <span className="ml-2 text-sm text-gray-700">In Stock Only</span>
          </label>
          <label className="flex items-center cursor-pointer hover:bg-gray-50 p-1 rounded">
            <input
              type="checkbox"
              checked={filters.onSale === true}
              onChange={(e) =>
                handleFilterChange('onSale', e.target.checked || undefined)
              }
              className="h-4 w-4 text-green-600 border-gray-300 rounded focus:ring-green-500"
            />
            <span className="ml-2 text-sm text-gray-700">On Sale</span>
          </label>
        </div>
      )}

      {/* Rating */}
      {renderFilterSection(
        'Rating',
        'rating',
        <div className="space-y-2">
          {[4, 3, 2, 1].map((rating) => (
            <label
              key={rating}
              className="flex items-center cursor-pointer hover:bg-gray-50 p-1 rounded"
            >
              <input
                type="radio"
                name="rating"
                value={rating}
                checked={filters.rating === rating}
                onChange={(e) =>
                  handleFilterChange(
                    'rating',
                    e.target.checked ? rating : undefined
                  )
                }
                className="h-4 w-4 text-green-600 border-gray-300 focus:ring-green-500"
              />
              <div className="ml-2 flex items-center">
                <div className="flex items-center">
                  {[...Array(5)].map((_, i) => (
                    <StarIcon
                      key={i}
                      className={`h-4 w-4 ${
                        i < rating ? 'text-yellow-400' : 'text-gray-300'
                      }`}
                    />
                  ))}
                </div>
                <span className="ml-1 text-sm text-gray-700">& Up</span>
              </div>
            </label>
          ))}
        </div>
      )}
    </div>
  );

  // Mobile view
  if (isMobile) {
    return (
      <>
        <button
          onClick={() => setIsOpen(true)}
          className={`flex items-center justify-center px-4 py-2 border border-gray-300 rounded-md bg-white text-sm font-medium text-gray-700 hover:bg-gray-50 ${className}`}
        >
          <FunnelIcon className="h-5 w-5 mr-2" />
          Filters
          {getActiveFilterCount() > 0 && (
            <span className="ml-2 px-2 py-0.5 bg-green-100 text-green-800 rounded-full text-xs">
              {getActiveFilterCount()}
            </span>
          )}
        </button>

        {/* Mobile filter modal */}
        {isOpen && (
          <div className="fixed inset-0 z-50 overflow-hidden">
            <div className="absolute inset-0 bg-black bg-opacity-50" onClick={() => setIsOpen(false)} />
            <div className="absolute right-0 top-0 h-full w-80 bg-white shadow-xl">
              <div className="flex items-center justify-between p-4 border-b">
                <h2 className="text-lg font-semibold">Filters</h2>
                <button
                  onClick={() => setIsOpen(false)}
                  className="p-1 hover:bg-gray-100 rounded"
                >
                  <XMarkIcon className="h-6 w-6" />
                </button>
              </div>
              <div className="p-4 overflow-y-auto h-full pb-20">
                {renderContent()}
              </div>
            </div>
          </div>
        )}
      </>
    );
  }

  // Desktop view
  return <div className={`bg-white rounded-lg ${className}`}>{renderContent()}</div>;
};

export default FilterPanel;