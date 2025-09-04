import { endpoints } from '../config/endpoints';
import React, { useState } from 'react';
import { Search, Package, AlertCircle, CheckCircle } from 'lucide-react';

const SearchTesting: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchCategory, setSearchCategory] = useState('');
  const [searchStrainType, setSearchStrainType] = useState('');
  const [searchSize, setSearchSize] = useState('');
  const [searchEffects, setSearchEffects] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [rawResponse, setRawResponse] = useState('');

  const testSearch = async () => {
    setLoading(true);
    setError('');
    setSearchResults([]);
    setRawResponse('');

    try {
      // Build search parameters
      const searchParams: any = {};
      if (searchQuery) searchParams.query = searchQuery;
      if (searchCategory) searchParams.category = searchCategory;
      if (searchStrainType) searchParams.strain_type = searchStrainType;
      if (searchSize) searchParams.size = searchSize;
      if (searchEffects) searchParams.effects = searchEffects;

      console.log('Sending search params:', searchParams);

      // Call the existing product search endpoint
      const response = await fetch(endpoints.products.search, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: searchQuery || undefined,
          category: searchCategory || undefined,
          filters: {
            strain_type: searchStrainType || undefined,
            size: searchSize || undefined,
            effects: searchEffects || undefined
          },
          limit: 20
        }),
      });

      const data = await response.json();
      setRawResponse(JSON.stringify(data, null, 2));
      
      if (data.products) {
        setSearchResults(data.products);
      } else {
        setError('No products field in response');
      }
    } catch (err: any) {
      setError(err.message || 'Search failed');
      console.error('Search error:', err);
    } finally {
      setLoading(false);
    }
  };

  const testGeneralBrowse = async () => {
    setSearchQuery('');
    setSearchCategory('');
    setSearchStrainType('');
    setSearchSize('');
    setSearchEffects('');
    
    // Test with empty params (should return general products)
    await testSearch();
  };

  const testSpecificProduct = async (productName: string) => {
    setSearchQuery(productName);
    setSearchCategory('');
    setSearchStrainType('');
    setSearchSize('');
    setSearchEffects('');
    
    setTimeout(() => testSearch(), 100);
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <h2 className="text-2xl font-bold mb-6">Product Search Testing</h2>
      
      {/* Search Parameters */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h3 className="text-lg font-semibold mb-4">Search Parameters</h3>
        
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Query (Product Name)
            </label>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="e.g., Blue Dream, OG Kush, Pink Kush"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Category
            </label>
            <select
              value={searchCategory}
              onChange={(e) => setSearchCategory(e.target.value)}
              className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Categories</option>
              <option value="Flower">Flower</option>
              <option value="Edibles">Edibles</option>
              <option value="Vapes">Vapes</option>
              <option value="Extracts">Extracts</option>
              <option value="Topicals">Topicals</option>
              <option value="Accessories">Accessories</option>
              <option value="Pre-Rolls">Pre-Rolls</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Strain Type
            </label>
            <select
              value={searchStrainType}
              onChange={(e) => setSearchStrainType(e.target.value)}
              className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Any Type</option>
              <option value="sativa">Sativa</option>
              <option value="indica">Indica</option>
              <option value="hybrid">Hybrid</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Size
            </label>
            <input
              type="text"
              value={searchSize}
              onChange={(e) => setSearchSize(e.target.value)}
              className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="e.g., 1g, 3.5g, 7g, 14g"
            />
          </div>
          
          <div className="col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Effects
            </label>
            <input
              type="text"
              value={searchEffects}
              onChange={(e) => setSearchEffects(e.target.value)}
              className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="e.g., relaxation, energy, pain relief, creativity"
            />
          </div>
        </div>
        
        <div className="flex gap-2">
          <button
            onClick={testSearch}
            disabled={loading}
            className="bg-blue-500 text-white px-4 py-2 rounded-md hover:bg-blue-600 disabled:opacity-50 flex items-center gap-2"
          >
            <Search size={18} />
            {loading ? 'Searching...' : 'Search'}
          </button>
          
          <button
            onClick={testGeneralBrowse}
            className="bg-gray-500 text-white px-4 py-2 rounded-md hover:bg-gray-600"
          >
            Test General Browse
          </button>
        </div>
      </div>

      {/* Quick Test Buttons */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h3 className="text-lg font-semibold mb-4">Quick Tests</h3>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => testSpecificProduct('pink kush')}
            className="bg-purple-500 text-white px-3 py-1 rounded hover:bg-purple-600"
          >
            Search "pink kush"
          </button>
          <button
            onClick={() => testSpecificProduct('blue dream')}
            className="bg-blue-500 text-white px-3 py-1 rounded hover:bg-blue-600"
          >
            Search "blue dream"
          </button>
          <button
            onClick={() => testSpecificProduct('og kush')}
            className="bg-green-500 text-white px-3 py-1 rounded hover:bg-green-600"
          >
            Search "og kush"
          </button>
          <button
            onClick={() => testSpecificProduct('gorilla')}
            className="bg-yellow-600 text-white px-3 py-1 rounded hover:bg-yellow-700"
          >
            Search "gorilla"
          </button>
          <button
            onClick={() => {
              setSearchCategory('Flower');
              setSearchQuery('');
              setTimeout(() => testSearch(), 100);
            }}
            className="bg-indigo-500 text-white px-3 py-1 rounded hover:bg-indigo-600"
          >
            All Flower
          </button>
          <button
            onClick={() => {
              setSearchCategory('Vapes');
              setSearchQuery('');
              setTimeout(() => testSearch(), 100);
            }}
            className="bg-teal-500 text-white px-3 py-1 rounded hover:bg-teal-600"
          >
            All Vapes
          </button>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 flex items-start gap-2">
          <AlertCircle className="text-red-500 mt-1" size={18} />
          <div>
            <p className="text-red-800 font-semibold">Error</p>
            <p className="text-red-600">{error}</p>
          </div>
        </div>
      )}

      {/* Search Results */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h3 className="text-lg font-semibold mb-4">
          Search Results ({searchResults.length} products)
        </h3>
        
        {searchResults.length > 0 ? (
          <div className="space-y-3">
            {searchResults.map((product, index) => (
              <div key={index} className="border rounded-lg p-4">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <h4 className="font-semibold text-lg">
                      {product.product_name || 'Unnamed Product'}
                    </h4>
                    <div className="text-sm text-gray-600 space-y-1 mt-2">
                      <p>Brand: {product.brand || 'N/A'}</p>
                      <p>Category: {product.category} {product.sub_category && `/ ${product.sub_category}`}</p>
                      <p>Type: {product.plant_type || product.strain_type || 'N/A'}</p>
                      <p>Size: {product.size || 'N/A'}</p>
                      {(product.thc || product.thc_max_percent) && (
                        <p>THC: {product.thc || product.thc_max_percent}%</p>
                      )}
                      {(product.cbd || product.cbd_max_percent) && (
                        <p>CBD: {product.cbd || product.cbd_max_percent}%</p>
                      )}
                      {product.description && (
                        <p>Description: {product.description}</p>
                      )}
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-bold text-green-600">
                      ${product.price || product.unit_price || '0.00'}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-gray-500 text-center py-8">
            <Package size={48} className="mx-auto mb-3 text-gray-400" />
            <p>No products found. Try adjusting your search criteria.</p>
          </div>
        )}
      </div>

      {/* Raw Response */}
      <div className="bg-gray-100 rounded-lg p-6">
        <h3 className="text-lg font-semibold mb-4">Raw API Response</h3>
        <pre className="bg-white p-4 rounded border overflow-x-auto text-sm">
          {rawResponse || 'No response yet'}
        </pre>
      </div>
    </div>
  );
};

export default SearchTesting;