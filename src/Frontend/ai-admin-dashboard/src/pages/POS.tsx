import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  ShoppingCart, Users, UserPlus, CreditCard, DollarSign,
  Printer, Scan, History, PauseCircle, Tag, Percent,
  Calendar, CheckCircle, X, Search, Plus, Minus, Trash2,
  Settings, AlertCircle, Calculator, Clock, User, Loader2,
  Maximize, Minimize, Wifi, Bluetooth, Usb, Network, RefreshCw, Zap
} from 'lucide-react';
import axios from 'axios';
import PaymentModal from '../components/pos/PaymentModal';
import CustomerModal from '../components/pos/CustomerModal';
import posService from '../services/posService';

interface Product {
  id: string;
  sku?: string;
  name: string;
  brand: string;
  category: string;
  sub_category?: string;
  subcategory?: string;
  thc_content: number;
  cbd_content: number;
  price: number;
  unit_price?: number;
  size?: string;
  weight_grams?: number;
  dried_flower_equivalent?: number;
  stock_quantity?: number;
  available_quantity?: number;
  quantity_available?: number;
  image_url?: string;
  in_stock?: boolean;
}

interface CartItem {
  product: Product;
  quantity: number;
  discount?: number;
  promotion?: string;
}

interface Customer {
  id: string;
  name: string;
  email?: string;
  phone?: string;
  loyalty_points?: number;
  is_verified?: boolean;
  birth_date?: string;
}

interface Transaction {
  id: string;
  customer_id?: string;
  items: CartItem[];
  subtotal: number;
  tax: number;
  total: number;
  payment_method: 'cash' | 'card' | 'debit';
  status: 'completed' | 'parked' | 'cancelled';
  timestamp: string;
}

export default function POS() {
  // State management
  const [activeTab, setActiveTab] = useState<'sale' | 'history' | 'parked' | 'settings'>('sale');
  const [cart, setCart] = useState<CartItem[]>([]);
  const [customer, setCustomer] = useState<Customer | null>(null);
  const [products, setProducts] = useState<Product[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [showCustomerModal, setShowCustomerModal] = useState(false);
  const [showAgeVerification, setShowAgeVerification] = useState(false);
  const [parkedSales, setParkedSales] = useState<Transaction[]>([]);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchLoading, setSearchLoading] = useState(false);
  const [customerSearchTerm, setCustomerSearchTerm] = useState('');
  const [transactionLoading, setTransactionLoading] = useState(false);
  const [barcodeInput, setBarcodeInput] = useState('');
  const [scannerEnabled, setScannerEnabled] = useState(false);
  const [mobileCartOpen, setMobileCartOpen] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const posContainerRef = useRef<HTMLDivElement>(null);
  const [detectedScanners, setDetectedScanners] = useState<any[]>([]);
  const [selectedScanner, setSelectedScanner] = useState<string | null>(null);
  const [detectingHardware, setDetectingHardware] = useState(false);
  const [testingScanner, setTestingScanner] = useState<string | null>(null);
  
  // Hardware settings
  const [hardwareSettings, setHardwareSettings] = useState({
    terminal: { enabled: false, id: '' },
    printer: { enabled: false, id: '' },
    scanner: { enabled: false, id: '' },
    cash_drawer: { enabled: false, auto_open: true }
  });

  // Calculate valid age date (19 years ago in most provinces, 21 in Quebec)
  const getValidAgeDate = () => {
    const today = new Date();
    const validAge = 19; // Or 21 for Quebec
    const validDate = new Date(today.getFullYear() - validAge, today.getMonth(), today.getDate());
    return validDate.toLocaleDateString('en-CA');
  };

  // Calculate dried flower equivalent
  const calculateDriedFlowerEquivalent = () => {
    return cart.reduce((total, item) => {
      // For cannabis products, use size if available (e.g., "3.5g" -> 3.5)
      let equivalent = item.product.dried_flower_equivalent || 0;
      
      // If no dried_flower_equivalent, try to parse from size for flower products
      if (!equivalent && item.product.category === 'Flower' && item.product.size) {
        const sizeMatch = item.product.size.match(/([\d.]+)g/);
        if (sizeMatch) {
          equivalent = parseFloat(sizeMatch[1]);
        }
      }
      
      return total + (equivalent * item.quantity);
    }, 0);
  };

  // Calculate totals
  const calculateTotals = () => {
    const subtotal = cart.reduce((total, item) => {
      const itemPrice = item.product.price * item.quantity;
      const discount = item.discount || 0;
      return total + (itemPrice - (itemPrice * discount / 100));
    }, 0);
    const tax = subtotal * 0.13; // 13% tax rate
    const total = subtotal + tax;
    return { subtotal, tax, total };
  };

  // Fetch products from API
  const fetchProducts = useCallback(async (query: string = '', category: string = 'all') => {
    try {
      setSearchLoading(true);
      const params = new URLSearchParams({ q: query || '', limit: '50' });
      if (category !== 'all') {
        params.append('category', category);
      }
      
      const response = await axios.get(`http://localhost:5024/api/search/products?${params}`);
      const productsData = response.data.products || [];
      
      // Map API response to our Product interface
      const mappedProducts = productsData.map((p: any) => ({
        ...p,
        price: p.price || p.unit_price || 0,
        quantity_available: p.available_quantity || p.stock_quantity || 0,
        subcategory: p.sub_category || p.subcategory,
      }));
      
      setProducts(mappedProducts);
    } catch (error) {
      console.error('Error fetching products:', error);
    } finally {
      setSearchLoading(false);
    }
  }, []);

  // Initial load
  // Fetch parked orders
  const fetchParkedOrders = async () => {
    try {
      const parkedOrders = await posService.getParkedTransactions('store_001');
      setParkedSales(parkedOrders);
    } catch (error) {
      console.error('Failed to fetch parked orders:', error);
    }
  };

  // Fetch transaction history
  const detectScanners = async () => {
    setDetectingHardware(true);
    try {
      const response = await axios.get('http://localhost:5024/api/hardware/scanners/detect');
      setDetectedScanners(response.data);
      
      // Auto-select first connected scanner if none selected
      if (!selectedScanner && response.data.length > 0) {
        const connectedScanner = response.data.find((s: any) => 
          s.status === 'connected' || s.status === 'paired'
        );
        if (connectedScanner) {
          setSelectedScanner(connectedScanner.id);
          setScannerEnabled(true);
        }
      }
    } catch (error) {
      console.error('Failed to detect scanners:', error);
    } finally {
      setDetectingHardware(false);
    }
  };

  const testScanner = async (scannerId: string) => {
    setTestingScanner(scannerId);
    try {
      const response = await axios.get(`http://localhost:5024/api/hardware/scanners/${scannerId}/test`);
      if (response.data.success) {
        alert(`Scanner test successful! Test barcode: ${response.data.test_barcode}`);
      } else {
        alert('Scanner test failed');
      }
    } catch (error) {
      console.error('Failed to test scanner:', error);
      alert('Failed to test scanner');
    } finally {
      setTestingScanner(null);
    }
  };

  const fetchTransactionHistory = async () => {
    try {
      const history = await posService.getTransactionHistory('store_001');
      // Filter out parked transactions for the history view
      const completedTransactions = history.filter(t => t.status === 'completed');
      setTransactions(completedTransactions);
    } catch (error) {
      console.error('Failed to fetch transaction history:', error);
    }
  };

  useEffect(() => {
    fetchProducts();
    fetchParkedOrders();
    fetchTransactionHistory();
  }, []);

  // Handle barcode scanning
  useEffect(() => {
    const handleBarcodeInput = async (e: KeyboardEvent) => {
      // Only process if scanner is enabled and we're on the sale tab
      if (!scannerEnabled || activeTab !== 'sale') return;
      
      // Barcode scanners typically send Enter key at the end
      if (e.key === 'Enter' && barcodeInput.length > 0) {
        try {
          const product = await posService.getProductByBarcode(barcodeInput);
          addToCart(product);
          setBarcodeInput('');
        } catch (error) {
          console.error('Product not found for barcode:', barcodeInput);
          // Try searching by SKU as fallback
          const products = await axios.get(`http://localhost:5024/api/search/products`, {
            params: { q: barcodeInput, limit: 1 }
          });
          if (products.data.products?.length > 0) {
            const product = products.data.products[0];
            addToCart({
              ...product,
              price: product.price || product.unit_price || 0,
              quantity_available: product.available_quantity || product.stock_quantity || 0,
              subcategory: product.sub_category || product.subcategory,
            });
          } else {
            alert(`Product not found for barcode: ${barcodeInput}`);
          }
          setBarcodeInput('');
        }
      } else if (e.key.length === 1 && !e.ctrlKey && !e.metaKey && !e.altKey) {
        // Build up the barcode string
        setBarcodeInput(prev => prev + e.key);
      }
    };

    // Clear barcode input after timeout (scanner sends chars quickly)
    let clearTimer: NodeJS.Timeout;
    const resetBarcodeInput = () => {
      clearTimer = setTimeout(() => {
        setBarcodeInput('');
      }, 1000);
    };

    if (scannerEnabled) {
      window.addEventListener('keydown', handleBarcodeInput);
      window.addEventListener('keyup', resetBarcodeInput);
    }

    return () => {
      window.removeEventListener('keydown', handleBarcodeInput);
      window.removeEventListener('keyup', resetBarcodeInput);
      if (clearTimer) clearTimeout(clearTimer);
    };
  }, [barcodeInput, scannerEnabled, activeTab]);

  // Debounced search
  useEffect(() => {
    const timer = setTimeout(() => {
      fetchProducts(searchTerm, selectedCategory);
    }, 300);

    return () => clearTimeout(timer);
  }, [searchTerm, selectedCategory, fetchProducts]);

  // Add to cart
  const addToCart = (product: Product) => {
    const existingItem = cart.find(item => item.product.id === product.id);
    if (existingItem) {
      updateQuantity(product.id, existingItem.quantity + 1);
    } else {
      setCart([...cart, { product, quantity: 1 }]);
    }
  };

  // Update quantity
  const updateQuantity = (productId: string, quantity: number) => {
    if (quantity <= 0) {
      removeFromCart(productId);
    } else {
      setCart(cart.map(item => 
        item.product.id === productId 
          ? { ...item, quantity } 
          : item
      ));
    }
  };

  // Remove from cart
  const removeFromCart = (productId: string) => {
    setCart(cart.filter(item => item.product.id !== productId));
  };

  // Apply discount
  const applyDiscount = (productId: string, discount: number) => {
    setCart(cart.map(item => 
      item.product.id === productId 
        ? { ...item, discount } 
        : item
    ));
  };

  // Park sale
  const parkSale = async () => {
    if (cart.length === 0) return;
    
    setTransactionLoading(true);
    try {
      const { subtotal, tax, total } = calculateTotals();
      
      const parkedData = {
        store_id: 'store_001', // TODO: Get from context
        cashier_id: 'cashier_001', // TODO: Get from auth context
        customer_id: customer?.id === 'anonymous' ? undefined : customer?.id,
        items: cart.map(item => ({
          product: item.product,
          quantity: item.quantity,
          discount: item.discount || 0,
          discount_type: 'percentage',
          promotion: item.promotion || null
        })),
        subtotal,
        discounts: cart.reduce((sum, item) => {
          const itemPrice = item.product.price * item.quantity;
          return sum + (itemPrice * (item.discount || 0) / 100);
        }, 0),
        tax,
        total,
        payment_method: 'cash',
        status: 'parked',
        receipt_number: `PARK-${Date.now()}`
      };
      
      const parkedTransaction = await posService.parkTransaction(parkedData);
      // Refresh parked orders from database to ensure consistency
      await fetchParkedOrders();
      setCart([]);
      setCustomer(null);
      alert('Sale parked successfully!');
    } catch (error) {
      console.error('Failed to park transaction:', error);
      alert('Failed to park sale. Please try again.');
    } finally {
      setTransactionLoading(false);
    }
  };

  // Resume parked sale
  const resumeParkedSale = async (transaction: Transaction) => {
    try {
      const resumed = await posService.resumeTransaction(transaction.id);
      setCart(resumed.items);
      
      // Load customer data if present
      if (resumed.customer_id && resumed.customer_id !== 'anonymous') {
        try {
          const customerData = await posService.getCustomerById(resumed.customer_id);
          setCustomer(customerData);
        } catch (error) {
          console.error('Failed to load customer:', error);
        }
      }
      
      // Refresh parked orders from database
      await fetchParkedOrders();
      setActiveTab('sale');
    } catch (error) {
      console.error('Failed to resume transaction:', error);
      alert('Failed to resume sale. Please try again.');
    }
  };

  // Toggle fullscreen mode
  const toggleFullscreen = () => {
    if (!posContainerRef.current) return;
    
    if (!document.fullscreenElement) {
      posContainerRef.current.requestFullscreen().then(() => {
        setIsFullscreen(true);
      }).catch((err) => {
        console.error('Error attempting to enable fullscreen:', err);
      });
    } else {
      document.exitFullscreen().then(() => {
        setIsFullscreen(false);
      }).catch((err) => {
        console.error('Error attempting to exit fullscreen:', err);
      });
    }
  };

  // Listen for fullscreen changes
  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };

    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => {
      document.removeEventListener('fullscreenchange', handleFullscreenChange);
    };
  }, []);

  // Auto-detect scanners when settings tab is opened
  useEffect(() => {
    if (activeTab === 'settings' && detectedScanners.length === 0) {
      detectScanners();
    }
  }, [activeTab]);

  const { subtotal, tax, total } = calculateTotals();
  const driedFlowerEquivalent = calculateDriedFlowerEquivalent();

  return (
    <div ref={posContainerRef} className="h-full flex flex-col bg-gray-50">
      {/* Mobile Cart Backdrop */}
      {mobileCartOpen && (
        <div
          className="fixed inset-0 z-40 bg-gray-600 bg-opacity-75 lg:hidden"
          onClick={() => setMobileCartOpen(false)}
        />
      )}

      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="px-3 sm:px-6 py-3 sm:py-4">
          <div className="flex items-center justify-between">
            <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4">
              <h1 className="text-lg sm:text-2xl font-bold">Point of Sale</h1>
              <div className="hidden sm:flex items-center gap-2 px-4 py-2 bg-green-50 text-green-700 rounded-lg">
                <Calendar className="w-4 h-4" />
                <span className="text-sm font-medium">Valid ID Date: {getValidAgeDate()} or earlier</span>
              </div>
            </div>
            <div className="flex items-center gap-2 sm:gap-4">
              <button
                onClick={() => setScannerEnabled(!scannerEnabled)}
                className={`p-2 rounded-lg transition-colors ${
                  scannerEnabled 
                    ? 'bg-green-100 text-green-600 hover:bg-green-200' 
                    : 'hover:bg-gray-100'
                }`}
                title={scannerEnabled ? 'Scanner Enabled' : 'Scanner Disabled'}
              >
                <Scan className="w-5 h-5" />
              </button>
              <button 
                onClick={toggleFullscreen}
                className={`p-2 rounded-lg transition-colors ${
                  isFullscreen 
                    ? 'bg-blue-100 text-blue-600 hover:bg-blue-200' 
                    : 'hover:bg-gray-100'
                }`}
                title={isFullscreen ? 'Exit Fullscreen' : 'Enter Fullscreen'}
              >
                {isFullscreen ? (
                  <Minimize className="w-5 h-5" />
                ) : (
                  <Maximize className="w-5 h-5" />
                )}
              </button>
            </div>
          </div>
          
          {/* Tabs */}
          <div className="flex gap-1 sm:gap-4 mt-3 sm:mt-4 overflow-x-auto">
            <button
              onClick={() => setActiveTab('sale')}
              className={`px-2 sm:px-4 py-1.5 sm:py-2 rounded-lg font-medium whitespace-nowrap ${
                activeTab === 'sale' ? 'bg-blue-500 text-white' : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              <ShoppingCart className="w-4 h-4 inline mr-1 sm:mr-2" />
              <span className="text-sm sm:text-base">New Sale</span>
            </button>
            <button
              onClick={() => setActiveTab('parked')}
              className={`px-2 sm:px-4 py-1.5 sm:py-2 rounded-lg font-medium whitespace-nowrap ${
                activeTab === 'parked' ? 'bg-blue-500 text-white' : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              <PauseCircle className="w-4 h-4 inline mr-1 sm:mr-2" />
              <span className="text-sm sm:text-base">Parked ({parkedSales.length})</span>
            </button>
            <button
              onClick={() => setActiveTab('history')}
              className={`px-2 sm:px-4 py-1.5 sm:py-2 rounded-lg font-medium whitespace-nowrap ${
                activeTab === 'history' ? 'bg-blue-500 text-white' : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              <History className="w-4 h-4 inline mr-1 sm:mr-2" />
              <span className="text-sm sm:text-base">History</span>
            </button>
            <button
              onClick={() => setActiveTab('settings')}
              className={`px-2 sm:px-4 py-1.5 sm:py-2 rounded-lg font-medium whitespace-nowrap ${
                activeTab === 'settings' ? 'bg-blue-500 text-white' : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              <Settings className="w-4 h-4 inline mr-1 sm:mr-2" />
              <span className="text-sm sm:text-base">Settings</span>
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      {activeTab === 'sale' && (
        <div className="flex-1 flex flex-col lg:flex-row overflow-hidden">
          {/* Mobile Cart Button */}
          <button
            onClick={() => setMobileCartOpen(true)}
            className="lg:hidden fixed bottom-4 right-4 z-30 bg-green-500 text-white rounded-full p-4 shadow-lg"
          >
            <ShoppingCart className="w-6 h-6" />
            {cart.length > 0 && (
              <span className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs font-bold">
                {cart.length}
              </span>
            )}
          </button>

          {/* Product Catalog */}
          <div className="flex-1 p-3 sm:p-6 overflow-y-auto">
            {/* Search and Filters */}
            <div className="mb-4 flex flex-col sm:flex-row gap-2 sm:gap-4">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                <input
                  type="text"
                  placeholder="Search products..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border rounded-lg text-sm sm:text-base"
                />
                {scannerEnabled && barcodeInput && (
                  <div className="absolute right-3 top-1/2 transform -translate-y-1/2 text-xs text-gray-500">
                    Scanning: {barcodeInput}
                  </div>
                )}
              </div>
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="px-4 py-2 border rounded-lg text-sm sm:text-base"
              >
                <option value="all">All Categories</option>
                <option value="Flower">Flower</option>
                <option value="Pre-Rolls">Pre-Rolls</option>
                <option value="Vapes">Vapes</option>
                <option value="Edibles">Edibles</option>
                <option value="Beverages">Beverages</option>
                <option value="Extracts">Extracts</option>
                <option value="Topicals">Topicals</option>
                <option value="Accessories">Accessories</option>
              </select>
            </div>

            {/* Product Grid */}
            {searchLoading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
              </div>
            ) : products.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <p>No products found</p>
              </div>
            ) : (
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                {products.map(product => {
                  const inStock = product.quantity_available > 0;
                  const lowStock = product.quantity_available > 0 && product.quantity_available < 10;
                  
                  return (
                    <div
                      key={product.id}
                      onClick={() => inStock && addToCart(product)}
                      className={`bg-white p-4 rounded-lg shadow transition-all ${
                        inStock 
                          ? 'hover:shadow-lg cursor-pointer hover:scale-[1.02]' 
                          : 'opacity-60 cursor-not-allowed'
                      }`}
                    >
                      {product.image_url && (
                        <img 
                          src={product.image_url} 
                          alt={product.name}
                          className="w-full h-32 object-cover rounded mb-3"
                          onError={(e) => {
                            (e.target as HTMLImageElement).style.display = 'none';
                          }}
                        />
                      )}
                      <h3 className="font-semibold text-sm line-clamp-2">{product.name}</h3>
                      <p className="text-xs text-gray-500 mt-1">{product.brand}</p>
                      {product.size && (
                        <p className="text-xs text-gray-600 mt-1">{product.size}</p>
                      )}
                      <div className="mt-2 flex items-center justify-between">
                        <span className="text-lg font-bold">${product.price.toFixed(2)}</span>
                        <span className={`text-xs ${
                          !inStock ? 'text-red-500 font-medium' :
                          lowStock ? 'text-yellow-600' : 
                          'text-gray-500'
                        }`}>
                          {!inStock ? 'Out of Stock' :
                           lowStock ? `Low (${product.quantity_available})` :
                           `Stock: ${product.quantity_available}`}
                        </span>
                      </div>
                      <div className="mt-2 text-xs text-gray-600">
                        THC: {product.thc_content?.toFixed(1) || 0}% | CBD: {product.cbd_content?.toFixed(1) || 0}%
                      </div>
                      {product.sub_category && (
                        <div className="mt-1 text-xs text-gray-500">
                          {product.sub_category}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Cart Sidebar - Fixed on mobile, static on desktop */}
          <div className={`fixed inset-y-0 right-0 z-50 w-full sm:w-96 bg-white transform transition-transform duration-300 lg:static lg:translate-x-0 ${
            mobileCartOpen ? 'translate-x-0' : 'translate-x-full'
          } lg:border-l flex flex-col`}>
            {/* Customer Section */}
            <div className="p-4 border-b">
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-semibold">Customer</h3>
                <button
                  onClick={() => setShowCustomerModal(true)}
                  className="text-blue-500 hover:text-blue-600"
                >
                  {customer ? 'Change' : 'Select'}
                </button>
              </div>
              {customer ? (
                <div className="bg-gray-50 p-3 rounded-lg">
                  <p className="font-medium">{customer.name}</p>
                  <p className="text-sm text-gray-600">{customer.phone}</p>
                  {customer.loyalty_points && (
                    <p className="text-sm text-green-600">Points: {customer.loyalty_points}</p>
                  )}
                </div>
              ) : (
                <div className="flex gap-2">
                  <button
                    onClick={() => setShowCustomerModal(true)}
                    className="flex-1 px-3 py-2 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100"
                  >
                    <Users className="w-4 h-4 inline mr-1" />
                    Returning
                  </button>
                  <button
                    onClick={() => setCustomer({ id: 'new', name: 'New Customer', is_verified: false })}
                    className="flex-1 px-3 py-2 bg-green-50 text-green-600 rounded-lg hover:bg-green-100"
                  >
                    <UserPlus className="w-4 h-4 inline mr-1" />
                    New
                  </button>
                  <button
                    onClick={() => setCustomer({ id: 'anon', name: 'Anonymous', is_verified: true })}
                    className="flex-1 px-3 py-2 bg-gray-50 text-gray-600 rounded-lg hover:bg-gray-100"
                  >
                    <User className="w-4 h-4 inline mr-1" />
                    Anonymous
                  </button>
                </div>
              )}
            </div>

            {/* Weight Limit Warning */}
            {driedFlowerEquivalent > 0 && (
              <div className={`px-4 py-3 ${driedFlowerEquivalent > 30 ? 'bg-red-50 text-red-700' : 'bg-blue-50 text-blue-700'}`}>
                <div className="flex items-center gap-2">
                  <AlertCircle className="w-4 h-4" />
                  <span className="text-sm font-medium">
                    Dried Flower Equivalent: {driedFlowerEquivalent.toFixed(1)}g / 30g
                  </span>
                </div>
                {driedFlowerEquivalent > 30 && (
                  <p className="text-xs mt-1">Exceeds legal limit!</p>
                )}
              </div>
            )}

            {/* Cart Items */}
            <div className="flex-1 overflow-y-auto p-4">
              {cart.length === 0 ? (
                <div className="text-center text-gray-400 py-8">
                  <ShoppingCart className="w-12 h-12 mx-auto mb-2" />
                  <p>Cart is empty</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {cart.map(item => (
                    <div key={item.product.id} className="bg-gray-50 p-3 rounded-lg">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h4 className="font-medium">{item.product.name}</h4>
                          <p className="text-sm text-gray-600">
                            ${item.product.price.toFixed(2)} x {item.quantity}
                          </p>
                          {item.discount && (
                            <p className="text-sm text-green-600">
                              Discount: {item.discount}%
                            </p>
                          )}
                        </div>
                        <button
                          onClick={() => removeFromCart(item.product.id)}
                          className="text-red-500 hover:text-red-600"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                      <div className="flex items-center gap-2 mt-2">
                        <button
                          onClick={() => updateQuantity(item.product.id, item.quantity - 1)}
                          className="w-8 h-8 flex items-center justify-center bg-white rounded border hover:bg-gray-50"
                        >
                          <Minus className="w-4 h-4" />
                        </button>
                        <span className="w-12 text-center">{item.quantity}</span>
                        <button
                          onClick={() => updateQuantity(item.product.id, item.quantity + 1)}
                          className="w-8 h-8 flex items-center justify-center bg-white rounded border hover:bg-gray-50"
                        >
                          <Plus className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => {
                            const discount = prompt('Enter discount percentage:');
                            if (discount) applyDiscount(item.product.id, parseFloat(discount));
                          }}
                          className="ml-auto px-2 py-1 text-xs bg-yellow-50 text-yellow-700 rounded hover:bg-yellow-100"
                        >
                          <Tag className="w-3 h-3 inline mr-1" />
                          Discount
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Totals */}
            <div className="border-t p-4 space-y-2">
              <div className="flex justify-between text-sm">
                <span>Subtotal</span>
                <span>${subtotal.toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span>Tax (13%)</span>
                <span>${tax.toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-lg font-bold">
                <span>Total</span>
                <span>${total.toFixed(2)}</span>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="p-4 border-t space-y-2">
              <div className="grid grid-cols-2 gap-2">
                <button
                  onClick={parkSale}
                  className="px-4 py-2 bg-yellow-500 text-white rounded-lg hover:bg-yellow-600"
                >
                  <PauseCircle className="w-4 h-4 inline mr-1" />
                  Park Sale
                </button>
                <button
                  onClick={() => { setCart([]); setCustomer(null); }}
                  className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600"
                >
                  <X className="w-4 h-4 inline mr-1" />
                  Clear
                </button>
              </div>
              <button
                onClick={() => setShowPaymentModal(true)}
                disabled={cart.length === 0 || !customer || driedFlowerEquivalent > 30}
                className="w-full px-4 py-3 bg-green-500 text-white rounded-lg hover:bg-green-600 disabled:bg-gray-300 disabled:cursor-not-allowed"
              >
                <CreditCard className="w-4 h-4 inline mr-2" />
                Process Payment
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Parked Sales Tab */}
      {activeTab === 'parked' && (
        <div className="flex-1 p-3 sm:p-6 overflow-y-auto">
          <h2 className="text-lg sm:text-xl font-bold mb-4">Parked Sales</h2>
          {parkedSales.length === 0 ? (
            <div className="text-center text-gray-400 py-12">
              <PauseCircle className="w-12 h-12 mx-auto mb-2" />
              <p>No parked sales</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4">
              {parkedSales.map(sale => (
                <div key={sale.id} className="bg-white p-4 rounded-lg shadow">
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <p className="font-semibold">#{sale.id.slice(-6)}</p>
                      <p className="text-sm text-gray-500">
                        {new Date(sale.timestamp).toLocaleString()}
                      </p>
                    </div>
                    <span className="text-lg font-bold">${sale.total.toFixed(2)}</span>
                  </div>
                  <p className="text-sm text-gray-600 mb-3">
                    {sale.items.length} items
                  </p>
                  <button
                    onClick={() => resumeParkedSale(sale)}
                    className="w-full px-3 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
                  >
                    Resume Sale
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* History Tab */}
      {activeTab === 'history' && (
        <div className="flex-1 p-3 sm:p-6 overflow-y-auto">
          <h2 className="text-lg sm:text-xl font-bold mb-4">Transaction History</h2>
          <div className="bg-white rounded-lg shadow overflow-x-auto">
            <table className="w-full min-w-[640px]">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-2 sm:px-4 py-2 sm:py-3 text-left text-xs sm:text-sm font-medium text-gray-700">ID</th>
                  <th className="px-2 sm:px-4 py-2 sm:py-3 text-left text-xs sm:text-sm font-medium text-gray-700">Date</th>
                  <th className="px-2 sm:px-4 py-2 sm:py-3 text-left text-xs sm:text-sm font-medium text-gray-700 hidden sm:table-cell">Customer</th>
                  <th className="px-2 sm:px-4 py-2 sm:py-3 text-left text-xs sm:text-sm font-medium text-gray-700">Items</th>
                  <th className="px-2 sm:px-4 py-2 sm:py-3 text-left text-xs sm:text-sm font-medium text-gray-700">Total</th>
                  <th className="px-2 sm:px-4 py-2 sm:py-3 text-left text-xs sm:text-sm font-medium text-gray-700 hidden lg:table-cell">Payment</th>
                  <th className="px-2 sm:px-4 py-2 sm:py-3 text-left text-xs sm:text-sm font-medium text-gray-700">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {transactions.map(transaction => (
                  <tr key={transaction.id} className="hover:bg-gray-50">
                    <td className="px-2 sm:px-4 py-2 sm:py-3 text-xs sm:text-sm">#{transaction.id.slice(-6)}</td>
                    <td className="px-2 sm:px-4 py-2 sm:py-3 text-xs sm:text-sm">{new Date(transaction.timestamp).toLocaleDateString()}</td>
                    <td className="px-2 sm:px-4 py-2 sm:py-3 text-xs sm:text-sm hidden sm:table-cell">{transaction.customer_id || 'Guest'}</td>
                    <td className="px-2 sm:px-4 py-2 sm:py-3 text-xs sm:text-sm">{transaction.items.length}</td>
                    <td className="px-2 sm:px-4 py-2 sm:py-3 text-xs sm:text-sm font-medium">${transaction.total.toFixed(2)}</td>
                    <td className="px-2 sm:px-4 py-2 sm:py-3 text-xs sm:text-sm hidden lg:table-cell">{transaction.payment_method}</td>
                    <td className="px-2 sm:px-4 py-2 sm:py-3 text-xs sm:text-sm">
                      <span className={`px-2 py-1 rounded-full text-xs ${
                        transaction.status === 'completed' ? 'bg-green-100 text-green-700' :
                        transaction.status === 'parked' ? 'bg-yellow-100 text-yellow-700' :
                        'bg-red-100 text-red-700'
                      }`}>
                        {transaction.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Settings Tab */}
      {activeTab === 'settings' && (
        <div className="flex-1 p-3 sm:p-6 overflow-y-auto">
          <h2 className="text-xl font-bold mb-6">POS Settings</h2>
          
          <div className="space-y-6">
            {/* Hardware Configuration */}
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold mb-4">Hardware Configuration</h3>
              
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <CreditCard className="w-5 h-5 text-gray-400" />
                    <div>
                      <p className="font-medium">Payment Terminal</p>
                      <p className="text-sm text-gray-500">Connect card reader</p>
                    </div>
                  </div>
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={hardwareSettings.terminal.enabled}
                      onChange={(e) => setHardwareSettings({
                        ...hardwareSettings,
                        terminal: { ...hardwareSettings.terminal, enabled: e.target.checked }
                      })}
                      className="rounded"
                    />
                    <span className="text-sm">Enabled</span>
                  </label>
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Printer className="w-5 h-5 text-gray-400" />
                    <div>
                      <p className="font-medium">Receipt Printer</p>
                      <p className="text-sm text-gray-500">Print receipts</p>
                    </div>
                  </div>
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={hardwareSettings.printer.enabled}
                      onChange={(e) => setHardwareSettings({
                        ...hardwareSettings,
                        printer: { ...hardwareSettings.printer, enabled: e.target.checked }
                      })}
                      className="rounded"
                    />
                    <span className="text-sm">Enabled</span>
                  </label>
                </div>

                {/* Barcode Scanner Section */}
                <div className="border-t pt-4">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <Scan className="w-5 h-5 text-gray-400" />
                      <div>
                        <p className="font-medium">Barcode Scanners</p>
                        <p className="text-sm text-gray-500">Manage connected scanners</p>
                      </div>
                    </div>
                    <button
                      onClick={detectScanners}
                      disabled={detectingHardware}
                      className="px-3 py-1 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 flex items-center gap-2 text-sm"
                    >
                      {detectingHardware ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <RefreshCw className="w-4 h-4" />
                      )}
                      Detect Scanners
                    </button>
                  </div>
                  
                  {/* Scanner List */}
                  {detectedScanners.length > 0 ? (
                    <div className="space-y-3">
                      {detectedScanners.map((scanner) => (
                        <div key={scanner.id} className="p-3 bg-gray-50 rounded-lg">
                          <div className="flex items-start justify-between">
                            <div className="flex items-start gap-3">
                              {/* Connection Type Icon */}
                              {scanner.type === 'USB' && <Usb className="w-5 h-5 text-gray-500 mt-1" />}
                              {scanner.type === 'Bluetooth' && <Bluetooth className="w-5 h-5 text-blue-500 mt-1" />}
                              {scanner.type === 'Network' && <Network className="w-5 h-5 text-green-500 mt-1" />}
                              
                              <div className="flex-1">
                                <p className="font-medium text-sm">{scanner.name}</p>
                                <p className="text-xs text-gray-500">
                                  {scanner.manufacturer}
                                  {scanner.vendor_id && ` (${scanner.vendor_id}:${scanner.product_id})`}
                                </p>
                                <div className="flex items-center gap-2 mt-2">
                                  <span className={`text-xs px-2 py-1 rounded ${
                                    scanner.status === 'connected' || scanner.status === 'paired' ? 
                                    'bg-green-100 text-green-700' : 
                                    'bg-gray-100 text-gray-600'
                                  }`}>
                                    {scanner.status}
                                  </span>
                                  {scanner.confidence && (
                                    <span className={`text-xs px-2 py-1 rounded ${
                                      scanner.confidence === 'high' ? 'bg-blue-100 text-blue-700' :
                                      scanner.confidence === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                                      'bg-gray-100 text-gray-600'
                                    }`}>
                                      {scanner.confidence === 'high' ? '✓ Scanner' : 
                                       scanner.confidence === 'medium' ? 'Likely Scanner' : 
                                       'Possible Scanner'}
                                    </span>
                                  )}
                                  {scanner.capabilities && (
                                    <span className="text-xs text-gray-500">
                                      {scanner.capabilities.join(', ')}
                                    </span>
                                  )}
                                </div>
                              </div>
                            </div>
                            
                            <div className="flex items-center gap-2">
                              <button
                                onClick={() => testScanner(scanner.id)}
                                disabled={testingScanner === scanner.id}
                                className="px-2 py-1 text-xs bg-blue-50 text-blue-600 rounded hover:bg-blue-100"
                              >
                                {testingScanner === scanner.id ? (
                                  <Loader2 className="w-3 h-3 animate-spin" />
                                ) : (
                                  'Test'
                                )}
                              </button>
                              <label className="flex items-center gap-1">
                                <input
                                  type="checkbox"
                                  checked={selectedScanner === scanner.id}
                                  onChange={(e) => {
                                    if (e.target.checked) {
                                      setSelectedScanner(scanner.id);
                                      setScannerEnabled(true);
                                    } else {
                                      setSelectedScanner(null);
                                      setScannerEnabled(false);
                                    }
                                  }}
                                  className="rounded text-sm"
                                />
                                <span className="text-xs">Active</span>
                              </label>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-4 text-sm text-gray-500">
                      <Scan className="w-8 h-8 mx-auto mb-2 text-gray-300" />
                      <p>No scanners detected</p>
                      <p className="text-xs mt-1">Connect a scanner and click "Detect Scanners"</p>
                    </div>
                  )}
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <DollarSign className="w-5 h-5 text-gray-400" />
                    <div>
                      <p className="font-medium">Cash Drawer</p>
                      <p className="text-sm text-gray-500">Manage cash</p>
                    </div>
                  </div>
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={hardwareSettings.cash_drawer.enabled}
                      onChange={(e) => setHardwareSettings({
                        ...hardwareSettings,
                        cash_drawer: { ...hardwareSettings.cash_drawer, enabled: e.target.checked }
                      })}
                      className="rounded"
                    />
                    <span className="text-sm">Enabled</span>
                  </label>
                </div>
              </div>
            </div>

            {/* Cash Management */}
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold mb-4">Cash Management</h3>
              <div className="grid grid-cols-2 gap-4">
                <button className="px-4 py-2 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100">
                  <Calculator className="w-4 h-4 inline mr-2" />
                  Open Register
                </button>
                <button className="px-4 py-2 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100">
                  <DollarSign className="w-4 h-4 inline mr-2" />
                  Cash Count
                </button>
                <button className="px-4 py-2 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100">
                  <Clock className="w-4 h-4 inline mr-2" />
                  End of Day
                </button>
                <button className="px-4 py-2 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100">
                  <Printer className="w-4 h-4 inline mr-2" />
                  Print Report
                </button>
              </div>
            </div>

            {/* Discount Settings */}
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold mb-4">Discounts & Promotions</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <p className="font-medium">Senior Discount</p>
                    <p className="text-sm text-gray-500">10% off for 65+</p>
                  </div>
                  <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-sm">Active</span>
                </div>
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <p className="font-medium">Happy Hour</p>
                    <p className="text-sm text-gray-500">15% off 4-6pm</p>
                  </div>
                  <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-sm">Active</span>
                </div>
                <button className="w-full px-4 py-2 border-2 border-dashed border-gray-300 text-gray-500 rounded-lg hover:border-gray-400">
                  <Plus className="w-4 h-4 inline mr-2" />
                  Add Promotion
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Payment Modal */}
      {showPaymentModal && (
        <PaymentModal
          isOpen={showPaymentModal}
          onClose={() => setShowPaymentModal(false)}
          total={calculateTotals().total}
          onComplete={async (payment) => {
            // Handle payment completion
            setTransactionLoading(true);
            try {
              const { subtotal, tax, total } = calculateTotals();
              
              // Create transaction via API
              const transactionData = {
                store_id: 'store_001', // TODO: Get from context
                cashier_id: 'cashier_001', // TODO: Get from auth context
                customer_id: customer?.id === 'anonymous' ? undefined : customer?.id,
                items: cart.map(item => ({
                  product: item.product,
                  quantity: item.quantity,
                  discount: item.discount,
                  promotion: item.promotion
                })),
                subtotal,
                discounts: cart.reduce((sum, item) => {
                  const itemPrice = item.product.price * item.quantity;
                  return sum + (itemPrice * (item.discount || 0) / 100);
                }, 0),
                tax,
                total,
                payment_method: payment.method,
                payment_details: {
                  cash_amount: payment.cashAmount,
                  card_amount: payment.cardAmount,
                  change_given: payment.changeGiven,
                  card_last_four: payment.cardLastFour,
                  authorization_code: payment.authorizationCode
                },
                status: 'completed',
                receipt_number: `R${Date.now()}`,
                timestamp: new Date().toISOString()
              };
              
              const transaction = await posService.createTransaction(transactionData);
              
              // Refresh transaction history to show the new transaction
              await fetchTransactionHistory();
              
              // Print receipt if requested
              if (payment.printReceipt) {
                await posService.printReceipt(transaction.id);
              }
              
              // Email receipt if requested
              if (payment.emailReceipt) {
                await posService.emailReceipt(transaction.id, payment.emailReceipt);
              }
              
              // Clear cart and customer
              setCart([]);
              setCustomer(null);
              
              // Show success message
              alert(`Payment successful! ${payment.printReceipt ? 'Receipt printed.' : ''}`);
            } catch (error) {
              console.error('Failed to create transaction:', error);
              alert('Failed to process transaction. Please try again.');
            } finally {
              setTransactionLoading(false);
            }
          }}
        />
      )}

      {/* Customer Modal */}
      {showCustomerModal && (
        <CustomerModal
          isOpen={showCustomerModal}
          onClose={() => setShowCustomerModal(false)}
          onSelect={(selectedCustomer) => {
            setCustomer(selectedCustomer);
            setShowCustomerModal(false);
          }}
        />
      )}
    </div>
  );
}