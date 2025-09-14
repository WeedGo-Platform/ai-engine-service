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
    <div className="w-80 bg-white border rounded-lg shadow-sm h-fit sticky top-4">
      <div className="p-4 border-b flex justify-between items-center">
        <h3 className="font-semibold text-lg">Filters</h3>
        <button
          onClick={onClose}
          className="p-1 hover:bg-gray-100 rounded"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
      <div className="p-4 space-y-4 max-h-[calc(100vh-200px)] overflow-y-auto">
        {/* Subcategories */}
        {availableSubcategories.length > 0 && (
          <div>
            <h4 className="font-semibold text-sm mb-2">Subcategories</h4>
            <div className="space-y-1 max-h-40 overflow-y-auto">
              {availableSubcategories.map(subcat => (
                <label key={subcat} className="flex items-center gap-2 text-sm">
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
            <h4 className="font-semibold text-sm mb-2">Plant Type</h4>
            <div className="space-y-1">
              {availablePlantTypes.map(type => (
                <label key={type} className="flex items-center gap-2 text-sm">
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
            <h4 className="font-semibold text-sm mb-2">Size</h4>
            <div className="space-y-1 max-h-40 overflow-y-auto">
              {availableSizes.map(size => (
                <label key={size} className="flex items-center gap-2 text-sm">
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
          <h4 className="font-semibold text-sm mb-2">Sort by Price</h4>
          <div className="flex gap-2">
            <button
              onClick={() => onFilterChange({ ...selectedFilters, priceSort: 'none' })}
              className={`px-3 py-1 text-sm rounded border ${
                selectedFilters.priceSort === 'none'
                  ? 'bg-blue-100 border-blue-300 text-blue-700'
                  : 'bg-white hover:bg-gray-50'
              }`}
            >
              <ArrowUpDown className="w-3 h-3 inline mr-1" />
              Default
            </button>
            <button
              onClick={() => onFilterChange({ ...selectedFilters, priceSort: 'asc' })}
              className={`px-3 py-1 text-sm rounded border ${
                selectedFilters.priceSort === 'asc'
                  ? 'bg-blue-100 border-blue-300 text-blue-700'
                  : 'bg-white hover:bg-gray-50'
              }`}
            >
              <ArrowUp className="w-3 h-3 inline mr-1" />
              Low to High
            </button>
            <button
              onClick={() => onFilterChange({ ...selectedFilters, priceSort: 'desc' })}
              className={`px-3 py-1 text-sm rounded border ${
                selectedFilters.priceSort === 'desc'
                  ? 'bg-blue-100 border-blue-300 text-blue-700'
                  : 'bg-white hover:bg-gray-50'
              }`}
            >
              <ArrowDown className="w-3 h-3 inline mr-1" />
              High to Low
            </button>
          </div>
        </div>

        {/* THC Sort */}
        <div>
          <h4 className="font-semibold text-sm mb-2">Sort by THC %</h4>
          <div className="flex gap-2">
            <button
              onClick={() => onFilterChange({ ...selectedFilters, thcSort: 'none' })}
              className={`px-3 py-1 text-sm rounded border ${
                selectedFilters.thcSort === 'none'
                  ? 'bg-blue-100 border-blue-300 text-blue-700'
                  : 'bg-white hover:bg-gray-50'
              }`}
            >
              <ArrowUpDown className="w-3 h-3 inline mr-1" />
              Default
            </button>
            <button
              onClick={() => onFilterChange({ ...selectedFilters, thcSort: 'asc' })}
              className={`px-3 py-1 text-sm rounded border ${
                selectedFilters.thcSort === 'asc'
                  ? 'bg-blue-100 border-blue-300 text-blue-700'
                  : 'bg-white hover:bg-gray-50'
              }`}
            >
              <ArrowUp className="w-3 h-3 inline mr-1" />
              Low to High
            </button>
            <button
              onClick={() => onFilterChange({ ...selectedFilters, thcSort: 'desc' })}
              className={`px-3 py-1 text-sm rounded border ${
                selectedFilters.thcSort === 'desc'
                  ? 'bg-blue-100 border-blue-300 text-blue-700'
                  : 'bg-white hover:bg-gray-50'
              }`}
            >
              <ArrowDown className="w-3 h-3 inline mr-1" />
              High to Low
            </button>
          </div>
        </div>

        {/* CBD Sort */}
        <div>
          <h4 className="font-semibold text-sm mb-2">Sort by CBD %</h4>
          <div className="flex gap-2">
            <button
              onClick={() => onFilterChange({ ...selectedFilters, cbdSort: 'none' })}
              className={`px-3 py-1 text-sm rounded border ${
                selectedFilters.cbdSort === 'none'
                  ? 'bg-blue-100 border-blue-300 text-blue-700'
                  : 'bg-white hover:bg-gray-50'
              }`}
            >
              <ArrowUpDown className="w-3 h-3 inline mr-1" />
              Default
            </button>
            <button
              onClick={() => onFilterChange({ ...selectedFilters, cbdSort: 'asc' })}
              className={`px-3 py-1 text-sm rounded border ${
                selectedFilters.cbdSort === 'asc'
                  ? 'bg-blue-100 border-blue-300 text-blue-700'
                  : 'bg-white hover:bg-gray-50'
              }`}
            >
              <ArrowUp className="w-3 h-3 inline mr-1" />
              Low to High
            </button>
            <button
              onClick={() => onFilterChange({ ...selectedFilters, cbdSort: 'desc' })}
              className={`px-3 py-1 text-sm rounded border ${
                selectedFilters.cbdSort === 'desc'
                  ? 'bg-blue-100 border-blue-300 text-blue-700'
                  : 'bg-white hover:bg-gray-50'
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
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={selectedFilters.inStockOnly}
              onChange={(e) => onFilterChange({
                ...selectedFilters,
                inStockOnly: e.target.checked
              })}
              className="rounded"
            />
            In Stock Only
          </label>
        </div>
      </div>

      {/* Clear Filters */}
      <div className="p-4 border-t">
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
          className="w-full py-2 text-sm text-gray-600 hover:text-gray-900 border rounded hover:bg-gray-50"
        >
          Clear All Filters
        </button>
      </div>
    </div>
  );
};

export default FilterPanel;