import React, { useState, useEffect, useCallback } from 'react';
import { productSearchService, Product } from '../../services/productSearch';

interface EnhancedProductFilterProps {
  onResultsChange?: (results: Product[]) => void;
  theme?: any;
  className?: string;
}

const EnhancedProductFilter: React.FC<EnhancedProductFilterProps> = ({
  onResultsChange,
  theme,
  className = ''
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<Product[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [priceRange, setPriceRange] = useState<[number, number]>([0, 500]);
  const [selectedStrain, setSelectedStrain] = useState<string>('all');
  const [selectedEffects, setSelectedEffects] = useState<string[]>([]);
  const [selectedPotency, setSelectedPotency] = useState<string>('all');
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [recentSearches, setRecentSearches] = useState<string[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const [searchDebounceTimer, setSearchDebounceTimer] = useState<NodeJS.Timeout | null>(null);

  // Effects options
  const effects = [
    { id: 'relaxed', label: '😌 Relaxed', emoji: '😌' },
    { id: 'happy', label: '😊 Happy', emoji: '😊' },
    { id: 'energetic', label: '⚡ Energetic', emoji: '⚡' },
    { id: 'creative', label: '🎨 Creative', emoji: '🎨' },
    { id: 'focused', label: '🎯 Focused', emoji: '🎯' },
    { id: 'sleepy', label: '😴 Sleepy', emoji: '😴' }
  ];

  // Potency levels
  const potencyLevels = [
    { id: 'all', label: 'All Potencies', range: null },
    { id: 'mild', label: '🌱 Mild (< 15% THC)', range: [0, 15] },
    { id: 'moderate', label: '🌿 Moderate (15-20% THC)', range: [15, 20] },
    { id: 'strong', label: '💪 Strong (20-25% THC)', range: [20, 25] },
    { id: 'very-strong', label: '🚀 Very Strong (> 25% THC)', range: [25, 100] }
  ];

  // Load recent searches from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('recentProductSearches');
    if (saved) {
      setRecentSearches(JSON.parse(saved).slice(0, 5));
    }
  }, []);

  // Auto-search with debounce
  useEffect(() => {
    if (searchDebounceTimer) {
      clearTimeout(searchDebounceTimer);
    }

    if (searchQuery.length > 2) {
      setIsTyping(true);
      const timer = setTimeout(() => {
        performSearch();
        setIsTyping(false);
      }, 500);
      setSearchDebounceTimer(timer);
    } else if (searchQuery.length === 0) {
      setSearchResults([]);
      setIsTyping(false);
      if (onResultsChange) onResultsChange([]);
    }

    return () => {
      if (searchDebounceTimer) {
        clearTimeout(searchDebounceTimer);
      }
    };
  }, [searchQuery, selectedCategory, selectedStrain, priceRange, selectedEffects, selectedPotency]);

  const performSearch = useCallback(async () => {
    setIsSearching(true);
    try {
      // Load and search products
      const allProducts = await productSearchService.loadProducts();
      let results = searchQuery ? productSearchService.searchProducts(searchQuery, allProducts) : allProducts;
      
      // Apply filters
      if (selectedCategory !== 'all') {
        results = results.filter(p => p.category?.toLowerCase() === selectedCategory);
      }
      
      if (selectedStrain !== 'all') {
        results = results.filter(p => p.strain?.toLowerCase() === selectedStrain);
      }
      
      // Price filter
      results = results.filter(p => {
        const price = parseFloat(p.price?.toString() || '0');
        return price >= priceRange[0] && price <= priceRange[1];
      });
      
      // Effects filter (mock implementation - would need real data)
      if (selectedEffects.length > 0) {
        results = results.filter(p => {
          // This would need actual effects data in products
          return true; // Placeholder
        });
      }
      
      // Potency filter (mock implementation - would need real THC data)
      if (selectedPotency !== 'all') {
        const potency = potencyLevels.find(p => p.id === selectedPotency);
        if (potency?.range) {
          results = results.filter(p => {
            // This would need actual THC percentage data
            return true; // Placeholder
          });
        }
      }
      
      setSearchResults(results);
      if (onResultsChange) onResultsChange(results);
      
      // Save to recent searches
      if (searchQuery && !recentSearches.includes(searchQuery)) {
        const updated = [searchQuery, ...recentSearches].slice(0, 5);
        setRecentSearches(updated);
        localStorage.setItem('recentProductSearches', JSON.stringify(updated));
      }
    } catch (error) {
      console.error('Search failed:', error);
      setSearchResults([]);
      if (onResultsChange) onResultsChange([]);
    } finally {
      setIsSearching(false);
    }
  }, [searchQuery, selectedCategory, selectedStrain, priceRange, selectedEffects, selectedPotency, onResultsChange, recentSearches]);

  const handleEffectToggle = (effectId: string) => {
    setSelectedEffects(prev => 
      prev.includes(effectId) 
        ? prev.filter(e => e !== effectId)
        : [...prev, effectId]
    );
  };

  const clearFilters = () => {
    setSearchQuery('');
    setSelectedCategory('all');
    setSelectedStrain('all');
    setPriceRange([0, 500]);
    setSelectedEffects([]);
    setSelectedPotency('all');
    setSearchResults([]);
    if (onResultsChange) onResultsChange([]);
  };

  const activeFiltersCount = [
    selectedCategory !== 'all',
    selectedStrain !== 'all',
    priceRange[0] > 0 || priceRange[1] < 500,
    selectedEffects.length > 0,
    selectedPotency !== 'all'
  ].filter(Boolean).length;

  return (
    <div className={`bg-white rounded-xl shadow-sm border border-gray-200 p-4 ${className}`}>
      {/* Search Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-gray-800 uppercase tracking-wider">
          Product Search
        </h3>
        {activeFiltersCount > 0 && (
          <button
            onClick={clearFilters}
            className="text-xs text-blue-600 hover:text-blue-700 font-medium flex items-center gap-1"
          >
            Clear all ({activeFiltersCount})
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>
      
      {/* Search Input with Autocomplete */}
      <div className="relative mb-4">
        <div className="relative">
          <input
            type="text"
            placeholder="Search products, strains, effects..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full px-4 py-2.5 bg-white text-gray-700 border border-gray-200 rounded-xl 
                     focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent 
                     placeholder-gray-400 text-sm pr-10 shadow-sm"
          />
          <div className="absolute right-3 top-1/2 -translate-y-1/2">
            {isTyping ? (
              <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
            ) : (
              <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            )}
          </div>
        </div>
        
        {/* Recent Searches */}
        {recentSearches.length > 0 && !searchQuery && (
          <div className="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg">
            <div className="px-3 py-2 border-b border-gray-100">
              <span className="text-xs text-gray-500 font-medium">Recent Searches</span>
            </div>
            {recentSearches.map((search, idx) => (
              <button
                key={idx}
                onClick={() => setSearchQuery(search)}
                className="w-full px-3 py-2 text-left text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-2"
              >
                <svg className="w-3 h-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                {search}
              </button>
            ))}
          </div>
        )}
      </div>
      
      {/* Quick Filters */}
      <div className="grid grid-cols-2 gap-2 mb-3">
        {/* Category Filter */}
        <div>
          <label className="text-xs text-gray-600 block mb-1.5 font-medium">Category</label>
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="w-full px-3 py-2 bg-white text-gray-700 border border-gray-200 rounded-lg 
                     focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent 
                     text-xs shadow-sm"
          >
            <option value="all">All Categories</option>
            <option value="flower">🌸 Flower</option>
            <option value="edibles">🍪 Edibles</option>
            <option value="concentrates">💎 Concentrates</option>
            <option value="vapes">💨 Vapes</option>
            <option value="topicals">🧴 Topicals</option>
            <option value="accessories">🔧 Accessories</option>
          </select>
        </div>
        
        {/* Strain Type Filter */}
        <div>
          <label className="text-xs text-gray-600 block mb-1.5 font-medium">Strain Type</label>
          <select
            value={selectedStrain}
            onChange={(e) => setSelectedStrain(e.target.value)}
            className="w-full px-3 py-2 bg-white text-gray-700 border border-gray-200 rounded-lg 
                     focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent 
                     text-xs shadow-sm"
          >
            <option value="all">All Strains</option>
            <option value="sativa">🌅 Sativa</option>
            <option value="indica">🌙 Indica</option>
            <option value="hybrid">🌈 Hybrid</option>
            <option value="cbd">💚 CBD Dominant</option>
          </select>
        </div>
      </div>
      
      {/* Advanced Filters Toggle */}
      <button
        onClick={() => setShowAdvanced(!showAdvanced)}
        className="w-full mb-3 px-3 py-2 bg-gray-50 hover:bg-gray-100 text-gray-700 text-xs font-medium 
                 rounded-lg flex items-center justify-center gap-2 transition-colors"
      >
        <svg 
          className={`w-4 h-4 transition-transform ${showAdvanced ? 'rotate-180' : ''}`} 
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
        {showAdvanced ? 'Hide' : 'Show'} Advanced Filters
        {activeFiltersCount > 0 && (
          <span className="ml-1 px-1.5 py-0.5 bg-blue-500 text-white rounded-full text-xs">
            {activeFiltersCount}
          </span>
        )}
      </button>
      
      {/* Advanced Filters */}
      {showAdvanced && (
        <div className="space-y-4 mb-4 p-3 bg-gray-50 rounded-lg">
          {/* Effects Selection */}
          <div>
            <label className="text-xs text-gray-600 block mb-2 font-medium">Desired Effects</label>
            <div className="grid grid-cols-3 gap-2">
              {effects.map(effect => (
                <button
                  key={effect.id}
                  onClick={() => handleEffectToggle(effect.id)}
                  className={`px-2 py-1.5 text-xs rounded-lg border transition-all ${
                    selectedEffects.includes(effect.id)
                      ? 'bg-blue-500 text-white border-blue-500'
                      : 'bg-white text-gray-700 border-gray-200 hover:border-gray-300'
                  }`}
                >
                  {effect.emoji} {effect.label.split(' ')[1]}
                </button>
              ))}
            </div>
          </div>
          
          {/* Potency Level */}
          <div>
            <label className="text-xs text-gray-600 block mb-1.5 font-medium">Potency Level</label>
            <select
              value={selectedPotency}
              onChange={(e) => setSelectedPotency(e.target.value)}
              className="w-full px-3 py-2 bg-white text-gray-700 border border-gray-200 rounded-lg 
                       focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent 
                       text-xs shadow-sm"
            >
              {potencyLevels.map(level => (
                <option key={level.id} value={level.id}>{level.label}</option>
              ))}
            </select>
          </div>
          
          {/* Price Range Slider */}
          <div>
            <label className="text-xs text-gray-600 block mb-2 font-medium">
              Price Range: ${priceRange[0]} - ${priceRange[1]}
            </label>
            <div className="px-2">
              <div className="relative h-2 bg-gray-200 rounded-full">
                <div 
                  className="absolute h-2 bg-blue-500 rounded-full"
                  style={{
                    left: `${(priceRange[0] / 500) * 100}%`,
                    right: `${100 - (priceRange[1] / 500) * 100}%`
                  }}
                />
              </div>
              <div className="flex gap-2 items-center mt-2">
                <input
                  type="range"
                  min="0"
                  max="500"
                  value={priceRange[0]}
                  onChange={(e) => setPriceRange([Math.min(parseInt(e.target.value), priceRange[1] - 10), priceRange[1]])}
                  className="flex-1 accent-blue-500"
                />
                <input
                  type="range"
                  min="0"
                  max="500"
                  value={priceRange[1]}
                  onChange={(e) => setPriceRange([priceRange[0], Math.max(parseInt(e.target.value), priceRange[0] + 10)])}
                  className="flex-1 accent-blue-500"
                />
              </div>
              <div className="flex justify-between mt-1">
                <span className="text-xs text-gray-500">$0</span>
                <span className="text-xs text-gray-500">$500+</span>
              </div>
            </div>
          </div>
        </div>
      )}
      
      {/* Results Summary */}
      {(isSearching || searchResults.length > 0) && (
        <div className="mt-4 p-3 bg-blue-50 rounded-lg">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-blue-700">
              {isSearching ? (
                <span className="flex items-center gap-2">
                  <div className="w-3 h-3 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
                  Searching...
                </span>
              ) : (
                `Found ${searchResults.length} product${searchResults.length !== 1 ? 's' : ''}`
              )}
            </span>
            {searchResults.length > 0 && (
              <button
                className="text-xs text-blue-600 hover:text-blue-700 font-medium"
                onClick={() => {
                  // This could trigger showing results in chat or another panel
                  console.log('View results:', searchResults);
                }}
              >
                View Results →
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default EnhancedProductFilter;