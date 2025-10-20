import React, { useEffect, useState } from 'react';
import { X, ArrowUpDown, ArrowUp, ArrowDown } from 'lucide-react';

interface FilterPanelProps {
  isOpen: boolean;
  onClose: () => void;
  selectedFilters: {
    subcategories: string[];
    plantTypes: string[];
    sizes: string[];
    priceSort: 'none' | 'asc' | 'desc';
    thcSort: 'none' | 'asc' | 'desc';
    cbdSort: 'none' | 'asc' | 'desc';
    inStockOnly: boolean;
  };
  onFilterChange: (filters: any) => void;
  products: any[];
}

const FilterPanel: React.FC<FilterPanelProps> = ({
  isOpen,
  onClose,
  selectedFilters,
  onFilterChange,
  products
}) => {
  const [availableSubcategories, setAvailableSubcategories] = useState<string[]>([]);
  const [availablePlantTypes, setAvailablePlantTypes] = useState<string[]>([]);
  const [availableSizes, setAvailableSizes] = useState<string[]>([]);

  // Extract unique values from products
  useEffect(() => {
    if (products && products.length > 0) {
      // Extract unique subcategories
      const subcategories = [...new Set(products
        .map(p => p.sub_category || p.subcategory)
        .filter(Boolean)
        .sort())];
      setAvailableSubcategories(subcategories);

      // Extract unique plant types
      const plantTypes = [...new Set(products
        .map(p => p.plant_type)
        .filter(Boolean)
        .sort())];
      setAvailablePlantTypes(plantTypes);

      // Extract unique sizes
      const sizesSet = new Set(products
        .map(p => p.size)
        .filter(size => size && typeof size === 'string'));
      const sizes = [...sizesSet].sort((a, b) => {
        // Sort sizes numerically if they contain numbers
        const aNum = parseFloat(a.replace(/[^0-9.]/g, ''));
        const bNum = parseFloat(b.replace(/[^0-9.]/g, ''));
        if (!isNaN(aNum) && !isNaN(bNum)) {
          return aNum - bNum;
        }
        return a.localeCompare(b);
      });
      setAvailableSizes(sizes);
    }
  }, [products]);

  if (!isOpen) return null;

  return (
    <>
      {/* Mobile Backdrop */}
      <div
        className="lg:hidden fixed inset-0 bg-black bg-opacity-50 dark:bg-opacity-70 z-40"
        onClick={onClose}
      />

      {/* Filter Panel - Drawer on mobile, sidebar on desktop */}
      <div className={`
        fixed lg:static inset-y-0 right-0 z-50 lg:z-auto
        w-full sm:w-96 lg:w-80
        bg-white dark:bg-gray-800
        border-l lg:border border-gray-200 dark:border-gray-700
        lg:rounded-lg h-full lg:h-fit lg:sticky lg:top-6
        transform transition-all duration-300
        ${isOpen ? 'translate-x-0' : 'translate-x-full lg:translate-x-0'}
        flex flex-col
      `}>
        <div className="p-4 sm:p-6 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center flex-shrink-0">
          <h3 className="font-semibold text-lg text-gray-900 dark:text-white">Filters</h3>
          <button
            onClick={onClose}
            className="p-2 -mr-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
            aria-label="Close filters"
          >
            <X className="w-5 h-5 text-gray-900 dark:text-white" />
          </button>
        </div>
        <div className="p-4 sm:p-6 space-y-4 sm:space-y-6 flex-1 overflow-y-auto">
        {/* Subcategories */}
        {availableSubcategories.length > 0 && (
          <div>
            <h4 className="font-semibold text-sm mb-2 text-gray-900 dark:text-white">Subcategories</h4>
            <div className="space-y-1 max-h-40 overflow-y-auto">
              {availableSubcategories.map(subcat => (
                <label key={subcat} className="flex items-center gap-2 text-sm text-gray-900 dark:text-white">
                  <input
                    type="checkbox"
                    checked={selectedFilters.subcategories.includes(subcat)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        onFilterChange({
                          ...selectedFilters,
                          subcategories: [...selectedFilters.subcategories, subcat]
                        });
                      } else {
                        onFilterChange({
                          ...selectedFilters,
                          subcategories: selectedFilters.subcategories.filter(s => s !== subcat)
                        });
                      }
                    }}
                    className="rounded"
                  />
                  {subcat}
                </label>
              ))}
            </div>
          </div>
        )}

        {/* Plant Types */}
        {availablePlantTypes.length > 0 && (
          <div>
            <h4 className="font-semibold text-sm mb-2 text-gray-900 dark:text-white">Plant Type</h4>
            <div className="space-y-1">
              {availablePlantTypes.map(type => (
                <label key={type} className="flex items-center gap-2 text-sm text-gray-900 dark:text-white">
                  <input
                    type="checkbox"
                    checked={selectedFilters.plantTypes.includes(type)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        onFilterChange({
                          ...selectedFilters,
                          plantTypes: [...selectedFilters.plantTypes, type]
                        });
                      } else {
                        onFilterChange({
                          ...selectedFilters,
                          plantTypes: selectedFilters.plantTypes.filter(t => t !== type)
                        });
                      }
                    }}
                    className="rounded"
                  />
                  {type}
                </label>
              ))}
            </div>
          </div>
        )}

        {/* Sizes */}
        {availableSizes.length > 0 && (
          <div>
            <h4 className="font-semibold text-sm mb-2 text-gray-900 dark:text-white">Size</h4>
            <div className="space-y-1 max-h-40 overflow-y-auto">
              {availableSizes.map(size => (
                <label key={size} className="flex items-center gap-2 text-sm text-gray-900 dark:text-white">
                  <input
                    type="checkbox"
                    checked={selectedFilters.sizes.includes(size)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        onFilterChange({
                          ...selectedFilters,
                          sizes: [...selectedFilters.sizes, size]
                        });
                      } else {
                        onFilterChange({
                          ...selectedFilters,
                          sizes: selectedFilters.sizes.filter(s => s !== size)
                        });
                      }
                    }}
                    className="rounded"
                  />
                  {size}
                </label>
              ))}
            </div>
          </div>
        )}

        {/* Price Sort */}
        <div>
          <h4 className="font-semibold text-sm mb-2 text-gray-900 dark:text-white">Sort by Price</h4>
          <div className="flex flex-col sm:flex-row gap-2">
            <button
              onClick={() => onFilterChange({ ...selectedFilters, priceSort: 'none' })}
              className={`px-3 py-1 text-sm rounded border ${
                selectedFilters.priceSort === 'none'
                  ? 'bg-blue-100 dark:bg-blue-900/30 border-blue-300 dark:border-blue-700 text-accent-700 dark:text-blue-400'
                  : 'bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 border-gray-200 dark:border-gray-600 text-gray-900 dark:text-white'
              }`}
            >
              <ArrowUpDown className="w-3 h-3 inline mr-1" />
              Default
            </button>
            <button
              onClick={() => onFilterChange({ ...selectedFilters, priceSort: 'asc' })}
              className={`px-3 py-1 text-sm rounded border ${
                selectedFilters.priceSort === 'asc'
                  ? 'bg-blue-100 dark:bg-blue-900/30 border-blue-300 dark:border-blue-700 text-accent-700 dark:text-blue-400'
                  : 'bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 border-gray-200 dark:border-gray-600 text-gray-900 dark:text-white'
              }`}
            >
              <ArrowUp className="w-3 h-3 inline mr-1" />
              Low to High
            </button>
            <button
              onClick={() => onFilterChange({ ...selectedFilters, priceSort: 'desc' })}
              className={`px-3 py-1 text-sm rounded border ${
                selectedFilters.priceSort === 'desc'
                  ? 'bg-blue-100 dark:bg-blue-900/30 border-blue-300 dark:border-blue-700 text-accent-700 dark:text-blue-400'
                  : 'bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 border-gray-200 dark:border-gray-600 text-gray-900 dark:text-white'
              }`}
            >
              <ArrowDown className="w-3 h-3 inline mr-1" />
              High to Low
            </button>
          </div>
        </div>

        {/* THC Sort */}
        <div>
          <h4 className="font-semibold text-sm mb-2 text-gray-900 dark:text-white">Sort by THC %</h4>
          <div className="flex flex-col sm:flex-row gap-2">
            <button
              onClick={() => onFilterChange({ ...selectedFilters, thcSort: 'none' })}
              className={`px-3 py-1 text-sm rounded border ${
                selectedFilters.thcSort === 'none'
                  ? 'bg-blue-100 dark:bg-blue-900/30 border-blue-300 dark:border-blue-700 text-accent-700 dark:text-blue-400'
                  : 'bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 border-gray-200 dark:border-gray-600 text-gray-900 dark:text-white'
              }`}
            >
              <ArrowUpDown className="w-3 h-3 inline mr-1" />
              Default
            </button>
            <button
              onClick={() => onFilterChange({ ...selectedFilters, thcSort: 'asc' })}
              className={`px-3 py-1 text-sm rounded border ${
                selectedFilters.thcSort === 'asc'
                  ? 'bg-blue-100 dark:bg-blue-900/30 border-blue-300 dark:border-blue-700 text-accent-700 dark:text-blue-400'
                  : 'bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 border-gray-200 dark:border-gray-600 text-gray-900 dark:text-white'
              }`}
            >
              <ArrowUp className="w-3 h-3 inline mr-1" />
              Low to High
            </button>
            <button
              onClick={() => onFilterChange({ ...selectedFilters, thcSort: 'desc' })}
              className={`px-3 py-1 text-sm rounded border ${
                selectedFilters.thcSort === 'desc'
                  ? 'bg-blue-100 dark:bg-blue-900/30 border-blue-300 dark:border-blue-700 text-accent-700 dark:text-blue-400'
                  : 'bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 border-gray-200 dark:border-gray-600 text-gray-900 dark:text-white'
              }`}
            >
              <ArrowDown className="w-3 h-3 inline mr-1" />
              High to Low
            </button>
          </div>
        </div>

        {/* CBD Sort */}
        <div>
          <h4 className="font-semibold text-sm mb-2 text-gray-900 dark:text-white">Sort by CBD %</h4>
          <div className="flex flex-col sm:flex-row gap-2">
            <button
              onClick={() => onFilterChange({ ...selectedFilters, cbdSort: 'none' })}
              className={`px-3 py-1 text-sm rounded border ${
                selectedFilters.cbdSort === 'none'
                  ? 'bg-blue-100 dark:bg-blue-900/30 border-blue-300 dark:border-blue-700 text-accent-700 dark:text-blue-400'
                  : 'bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 border-gray-200 dark:border-gray-600 text-gray-900 dark:text-white'
              }`}
            >
              <ArrowUpDown className="w-3 h-3 inline mr-1" />
              Default
            </button>
            <button
              onClick={() => onFilterChange({ ...selectedFilters, cbdSort: 'asc' })}
              className={`px-3 py-1 text-sm rounded border ${
                selectedFilters.cbdSort === 'asc'
                  ? 'bg-blue-100 dark:bg-blue-900/30 border-blue-300 dark:border-blue-700 text-accent-700 dark:text-blue-400'
                  : 'bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 border-gray-200 dark:border-gray-600 text-gray-900 dark:text-white'
              }`}
            >
              <ArrowUp className="w-3 h-3 inline mr-1" />
              Low to High
            </button>
            <button
              onClick={() => onFilterChange({ ...selectedFilters, cbdSort: 'desc' })}
              className={`px-3 py-1 text-sm rounded border ${
                selectedFilters.cbdSort === 'desc'
                  ? 'bg-blue-100 dark:bg-blue-900/30 border-blue-300 dark:border-blue-700 text-accent-700 dark:text-blue-400'
                  : 'bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 border-gray-200 dark:border-gray-600 text-gray-900 dark:text-white'
              }`}
            >
              <ArrowDown className="w-3 h-3 inline mr-1" />
              High to Low
            </button>
          </div>
        </div>

        {/* Stock Status */}
        <div>
          <h4 className="font-semibold text-sm mb-2">Stock</h4>
          <label className="flex items-center gap-2 text-sm text-gray-900 dark:text-white">
            <input
              type="checkbox"
              checked={selectedFilters.inStockOnly}
              onChange={(e) => onFilterChange({
                ...selectedFilters,
                inStockOnly: e.target.checked
              })}
              className="rounded border-gray-300 dark:border-gray-600 dark:bg-gray-700"
            />
            In Stock Only
          </label>
        </div>
        </div>

        {/* Clear Filters */}
        <div className="p-4 sm:p-6 border-t border-gray-200 dark:border-gray-700 flex-shrink-0">
          <button
            onClick={() => onFilterChange({
              subcategories: [],
              plantTypes: [],
              sizes: [],
              priceSort: 'none',
              thcSort: 'none',
              cbdSort: 'none',
              inStockOnly: false
            })}
            className="w-full py-2.5 text-sm font-medium text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white border border-gray-200 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors active:scale-95 touch-manipulation"
          >
            Clear All Filters
          </button>
        </div>
      </div>
    </>
  );
};

export default FilterPanel;