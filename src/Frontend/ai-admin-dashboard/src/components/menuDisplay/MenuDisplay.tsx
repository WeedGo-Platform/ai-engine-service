import React, { useState, useEffect } from 'react';
import { getApiUrl } from '../../config/app.config';
import { Leaf, Monitor, RefreshCw, Maximize2 } from 'lucide-react';
import { useStoreContext } from '../../contexts/StoreContext';
import MenuProductCard from './MenuProductCard';

interface Product {
  id: string;
  sku: string;
  ocs_variant_number: string;
  product_name: string;
  brand: string;
  category: string;
  subcategory: string;
  plant_type?: string;
  strain_type?: string;
  thc_content?: number;
  cbd_content?: number;
  size?: string;
  retail_price: number;
  image_url?: string;
  quantity_available: number;
  is_featured?: boolean;
  is_sale?: boolean;
  sale_price?: number;
}

interface GroupedProducts {
  [subcategory: string]: Product[];
}

interface ColumnData {
  title: string;
  categories: string[];
  products: GroupedProducts;
}

export default function MenuDisplay() {
  const { currentStore } = useStoreContext();
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(new Date());
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [autoScroll, setAutoScroll] = useState(true);
  const containerRef = React.useRef<HTMLDivElement>(null);
  const columnRefs = React.useRef<(HTMLDivElement | null)[]>([]);
  const [columns, setColumns] = useState<ColumnData[]>([
    { title: 'FLOWER', categories: ['flower'], products: {} },
    { title: 'PRE-ROLLS', categories: ['pre-rolls'], products: {} },
    { title: 'VAPES', categories: ['vapes'], products: {} },
    { title: 'MORE', categories: ['edibles', 'concentrates', 'topicals', 'accessories', 'beverages'], products: {} }
  ]);

  // Fetch products from API
  const fetchProducts = async () => {
    if (!currentStore?.id) return;

    try {
      setLoading(true);
      const response = await fetch(
        `${getApiUrl('/api/kiosk/products/browse')}?store_id=${currentStore.id}&limit=500`
      );

      if (response.ok) {
        const data = await response.json();
        setProducts(data.products || []);
        organizeProducts(data.products || []);
        setLastUpdate(new Date());
      }
    } catch (error) {
      console.error('Error fetching products:', error);
    } finally {
      setLoading(false);
    }
  };

  // Organize products into columns and subcategories
  const organizeProducts = (productList: Product[]) => {
    const newColumns: ColumnData[] = [
      { title: 'FLOWER', categories: ['flower'], products: {} },
      { title: 'PRE-ROLLS', categories: ['pre-rolls'], products: {} },
      { title: 'VAPES', categories: ['vapes', 'vape'], products: {} },
      { title: 'MORE', categories: ['edibles', 'concentrates', 'concentrate', 'topicals', 'accessories', 'beverages', 'extracts', 'extract'], products: {} }
    ];

    productList.forEach(product => {
      const category = product.category?.toLowerCase() || '';
      const subcategory = product.subcategory?.toLowerCase() || 'other';
      const subcategoryDisplay = product.subcategory || 'Other';

      // Special handling for different product types
      let columnIndex = -1;

      // Check for pre-rolls (either as category or subcategory under flower)
      if (category === 'pre-rolls' || category === 'pre-roll' ||
          (category === 'flower' && (subcategory.includes('pre-roll') || subcategory.includes('preroll')))) {
        columnIndex = 1; // PRE-ROLLS column
      }
      // Check for hash, kief, resin (these might be subcategories under flower or concentrates)
      else if ((category === 'flower' || category === 'concentrates' || category === 'concentrate') &&
               (subcategory.includes('hash') || subcategory.includes('kief') ||
                subcategory.includes('resin') || subcategory.includes('rosin'))) {
        columnIndex = 3; // MORE column (concentrates)
      }
      // Standard category matching
      else {
        columnIndex = newColumns.findIndex(col =>
          col.categories.includes(category)
        );
      }

      if (columnIndex !== -1) {
        if (!newColumns[columnIndex].products[subcategoryDisplay]) {
          newColumns[columnIndex].products[subcategoryDisplay] = [];
        }
        newColumns[columnIndex].products[subcategoryDisplay].push(product);
      } else {
        // If no match found, log it for debugging and put in MORE column
        console.log(`Product category not matched: ${category}, subcategory: ${subcategory}`, product);
        if (!newColumns[3].products[subcategoryDisplay]) {
          newColumns[3].products[subcategoryDisplay] = [];
        }
        newColumns[3].products[subcategoryDisplay].push(product);
      }
    });

    // Sort products within each subcategory by name
    newColumns.forEach(column => {
      Object.keys(column.products).forEach(subcategory => {
        column.products[subcategory].sort((a, b) => {
          const nameA = a.product_name || '';
          const nameB = b.product_name || '';
          return nameA.localeCompare(nameB);
        });
      });
    });

    setColumns(newColumns);
  };

  // Auto-refresh every 5 minutes
  useEffect(() => {
    fetchProducts();

    if (autoRefresh) {
      const interval = setInterval(fetchProducts, 5 * 60 * 1000); // 5 minutes
      return () => clearInterval(interval);
    }
  }, [currentStore?.id, autoRefresh]);

  // Listen for fullscreen changes
  React.useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };

    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => {
      document.removeEventListener('fullscreenchange', handleFullscreenChange);
    };
  }, []);

  // Auto-scroll functionality for each column
  React.useEffect(() => {
    if (!autoScroll) return;

    const scrollIntervals: NodeJS.Timeout[] = [];

    columnRefs.current.forEach((ref, index) => {
      if (ref && ref.scrollHeight > ref.clientHeight) {
        let scrollDirection = 1; // 1 for down, -1 for up
        let pauseCounter = 0;

        const interval = setInterval(() => {
          if (!ref) return;

          // Pause at top and bottom
          if (pauseCounter > 0) {
            pauseCounter--;
            return;
          }

          // Scroll
          ref.scrollTop += scrollDirection * 2; // Scroll 2 pixels at a time

          // Check if reached bottom
          if (ref.scrollTop + ref.clientHeight >= ref.scrollHeight - 5) {
            scrollDirection = -1;
            pauseCounter = 50; // Pause for ~2.5 seconds (50 * 50ms)
          }
          // Check if reached top
          else if (ref.scrollTop <= 5) {
            scrollDirection = 1;
            pauseCounter = 50; // Pause for ~2.5 seconds
          }
        }, 50); // Run every 50ms for smooth scrolling

        scrollIntervals.push(interval);
      }
    });

    return () => {
      scrollIntervals.forEach(interval => clearInterval(interval));
    };
  }, [autoScroll, products, columns]);

  // Toggle fullscreen for menu display container only
  const toggleFullscreen = async () => {
    if (!document.fullscreenElement) {
      try {
        if (containerRef.current) {
          await containerRef.current.requestFullscreen();
          setIsFullscreen(true);
        }
      } catch (err) {
        console.error('Error entering fullscreen:', err);
      }
    } else {
      try {
        await document.exitFullscreen();
        setIsFullscreen(false);
      } catch (err) {
        console.error('Error exiting fullscreen:', err);
      }
    }
  };

  if (!currentStore) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-900">
        <div className="text-center text-white">
          <Monitor className="w-16 h-16 mx-auto mb-4 text-gray-400" />
          <h2 className="text-2xl font-bold mb-2">No Store Selected</h2>
          <p className="text-gray-400">Please select a store to display the menu</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-900">
        <div className="text-center text-white">
          <RefreshCw className="w-16 h-16 mx-auto mb-4 animate-spin text-primary-500" />
          <h2 className="text-2xl font-bold">Loading Menu...</h2>
        </div>
      </div>
    );
  }

  return (
    <div ref={containerRef} className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <div className="bg-gray-800 border-b border-gray-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Leaf className="w-8 h-8 text-green-500" />
            <div>
              <h1 className="text-2xl font-bold">{currentStore.name} - Menu Display</h1>
              <p className="text-sm text-gray-400">
                Last updated: {lastUpdate.toLocaleTimeString()} |
                {products.length} products |
                Auto-refresh: {autoRefresh ? 'ON' : 'OFF'}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 text-sm">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={autoScroll}
                  onChange={(e) => setAutoScroll(e.target.checked)}
                  className="w-4 h-4 text-green-600 bg-gray-700 border-gray-600 rounded focus:ring-green-500"
                />
                <span className="text-gray-300">Auto-Scroll</span>
              </label>
            </div>
            <button
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={`px-4 py-2 rounded-lg transition-colors ${
                autoRefresh
                  ? 'bg-green-600 hover:bg-green-700'
                  : 'bg-gray-600 hover:bg-gray-700'
              }`}
              title={autoRefresh ? 'Auto-refresh ON' : 'Auto-refresh OFF'}
            >
              <RefreshCw className="w-4 h-4" />
            </button>
            <button
              onClick={fetchProducts}
              className="px-4 py-2 bg-primary-600 hover:bg-primary-700 rounded-lg transition-colors"
            >
              Refresh Now
            </button>
            <button
              onClick={toggleFullscreen}
              className="px-4 py-2 bg-gray-600 hover:bg-gray-700 rounded-lg transition-colors"
            >
              <Maximize2 className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* 4-Column Grid Layout */}
      <div className="p-4">
        <div className="grid grid-cols-4 gap-4 h-[calc(100vh-120px)]">
          {columns.map((column, index) => (
            <div
              key={index}
              className="bg-gray-800 rounded-lg overflow-hidden flex flex-col"
            >
              {/* Column Header */}
              <div className={`px-4 py-3 font-bold text-lg border-b-2 ${
                index === 0 ? 'bg-green-600 border-green-500' :
                index === 1 ? 'bg-blue-600 border-blue-500' :
                index === 2 ? 'bg-purple-600 border-purple-500' :
                'bg-orange-600 border-orange-500'
              }`}>
                {column.title}
              </div>

              {/* Column Content - Scrollable */}
              <div
                ref={el => columnRefs.current[index] = el}
                className="flex-1 overflow-y-auto p-3 space-y-4 scrollbar-hide"
                style={{ scrollBehavior: 'smooth' }}
              >
                {Object.keys(column.products).length === 0 ? (
                  <div className="text-center text-gray-500 py-8">
                    <p>No products available</p>
                  </div>
                ) : (
                  Object.entries(column.products).map(([subcategory, items]) => (
                    <div key={subcategory} className="space-y-2">
                      {/* Subcategory Header */}
                      <div className="bg-gray-700 px-3 py-1 rounded-lg">
                        <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">
                          {subcategory} ({items.length})
                        </h3>
                      </div>

                      {/* Products in Subcategory */}
                      <div className="space-y-2">
                        {items.map(product => (
                          <MenuProductCard
                            key={product.id}
                            product={product}
                          />
                        ))}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Footer Status Bar */}
      <div className="fixed bottom-0 left-0 right-0 bg-gray-800 border-t border-gray-700 px-6 py-2">
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center gap-6">
            <span className="text-gray-400">
              Store: <span className="text-white font-medium">{currentStore.name}</span>
            </span>
            <span className="text-gray-400">
              Location: <span className="text-white">{currentStore.city}</span>
            </span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-green-500">Live Menu</span>
          </div>
        </div>
      </div>
    </div>
  );
}