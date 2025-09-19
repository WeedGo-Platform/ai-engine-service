import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  ShoppingCart, Users, UserPlus, CreditCard, DollarSign,
  Printer, Scan, History, PauseCircle, Tag, Percent,
  Calendar, CheckCircle, X, Search, Plus, Minus, Trash2,
  Settings, AlertCircle, Calculator, Clock, User, Loader2,
  Maximize, Minimize, Wifi, Bluetooth, Usb, Network, RefreshCw, Zap,
  Package, Building2, SlidersHorizontal, ChevronRight, X as CloseIcon
} from 'lucide-react';
import axios from 'axios';
import PaymentModal from '../components/pos/PaymentModal';
import CustomerModal from '../components/pos/CustomerModal';
import FilterPanel from '../components/pos/FilterPanel';
import TransactionHistory from '../components/pos/TransactionHistory';
import posService from '../services/posService';
import { useStoreContext } from '../contexts/StoreContext';
import ProductDetailsModal from '../components/ProductDetailsModal';

interface Batch {
  batch_lot: string;
  quantity_remaining: number;
  case_gtin?: string;
  each_gtin?: string;
  packaged_on_date?: string;
  location_code?: string;
}

interface Product {
  id: string;
  sku?: string;
  name: string;
  brand: string;
  category: string;
  sub_category?: string;
  subcategory?: string;
  plant_type?: string;
  strain_type?: string;
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
  batch_count?: number;
  batches?: Batch[];
}

interface CartItem {
  product: Product;
  quantity: number;
  discount?: number;
  promotion?: string;
  batch?: Batch;
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

// Subcategory color mapping function - returns style object
const getSubcategoryBadgeStyle = (subcategory: string | undefined): React.CSSProperties => {
  if (!subcategory) return {};

  const subcategoryLower = subcategory.toLowerCase();

  // Define bright colors for transparent badges - only color and borderColor needed
  const colorMap: { [key: string]: { color: string; borderColor: string } } = {
    // Main categories
    'dried flower': { color: '#16a34a', borderColor: '#16a34a' },
    'flower': { color: '#16a34a', borderColor: '#16a34a' },
    'pre-roll': { color: '#fb923c', borderColor: '#fb923c' },
    'pre roll': { color: '#fb923c', borderColor: '#fb923c' },

    // Flower subcategories (avoid overlap with plant types)
    'singles': { color: '#fb923c', borderColor: '#fb923c' },
    'multi-pack': { color: '#6366f1', borderColor: '#6366f1' },
    'infused': { color: '#ec4899', borderColor: '#ec4899' },
    'blunts': { color: '#fbbf24', borderColor: '#fbbf24' },

    // Vape subcategories
    'vape': { color: '#06b6d4', borderColor: '#06b6d4' },
    'cartridge': { color: '#06b6d4', borderColor: '#06b6d4' },
    'disposable': { color: '#f43f5e', borderColor: '#f43f5e' },
    'pax pod': { color: '#9333ea', borderColor: '#9333ea' },
    '510 thread': { color: '#0ea5e9', borderColor: '#0ea5e9' },

    // Edible subcategories
    'edible': { color: '#ef4444', borderColor: '#ef4444' },
    'gummies': { color: '#ef4444', borderColor: '#ef4444' },
    'chocolate': { color: '#eab308', borderColor: '#eab308' },
    'baked good': { color: '#fb923c', borderColor: '#fb923c' },
    'mint': { color: '#10b981', borderColor: '#10b981' },
    'capsule': { color: '#6b7280', borderColor: '#6b7280' },

    // Beverage subcategories
    'beverage': { color: '#3b82f6', borderColor: '#3b82f6' },
    'sparkling': { color: '#3b82f6', borderColor: '#3b82f6' },
    'tea': { color: '#22c55e', borderColor: '#22c55e' },
    'shot': { color: '#a855f7', borderColor: '#a855f7' },
    'powder': { color: '#6366f1', borderColor: '#6366f1' },

    // Extract subcategories
    'extract': { color: '#eab308', borderColor: '#eab308' },
    'oil': { color: '#eab308', borderColor: '#eab308' },
    'shatter': { color: '#fb923c', borderColor: '#fb923c' },
    'wax': { color: '#fbbf24', borderColor: '#fbbf24' },
    'resin': { color: '#ef4444', borderColor: '#ef4444' },
    'rosin': { color: '#ec4899', borderColor: '#ec4899' },
    'distillate': { color: '#a855f7', borderColor: '#a855f7' },
    'hash': { color: '#78716c', borderColor: '#78716c' },

    // Topical subcategories
    'topical': { color: '#84cc16', borderColor: '#84cc16' },
    'cream': { color: '#84cc16', borderColor: '#84cc16' },
    'balm': { color: '#14b8a6', borderColor: '#14b8a6' },
    'lotion': { color: '#06b6d4', borderColor: '#06b6d4' },
    'patch': { color: '#9333ea', borderColor: '#9333ea' },

    // Accessory subcategories
    'accessory': { color: '#64748b', borderColor: '#64748b' },
    'pipe': { color: '#64748b', borderColor: '#64748b' },
    'grinder': { color: '#71717a', borderColor: '#71717a' },
    'paper': { color: '#737373', borderColor: '#737373' },
    'storage': { color: '#78716c', borderColor: '#78716c' },
  };

  // Find matching color or use default
  for (const [key, style] of Object.entries(colorMap)) {
    if (subcategoryLower.includes(key)) {
      return {
        backgroundColor: 'rgba(255, 255, 255, 0.85)',
        color: style.color,
        borderColor: style.borderColor,
        borderWidth: '2px',
        borderStyle: 'solid',
        padding: '0.125rem 0.375rem',
        fontSize: '0.625rem',
        fontWeight: '700',
        borderRadius: '0.25rem',
        display: 'inline-block',
        textTransform: 'uppercase',
        letterSpacing: '0.025em',
        textShadow: '0 0 2px rgba(255, 255, 255, 0.9)'
      };
    }
  }

  // Default style for unknown subcategories
  return {
    backgroundColor: 'rgba(255, 255, 255, 0.85)',
    color: '#64748b',
    borderColor: '#64748b',
    borderWidth: '2px',
    borderStyle: 'solid',
    padding: '0.125rem 0.375rem',
    fontSize: '0.625rem',
    fontWeight: '700',
    borderRadius: '0.25rem',
    display: 'inline-block',
    textTransform: 'uppercase',
    letterSpacing: '0.025em',
    textShadow: '0 0 2px rgba(255, 255, 255, 0.9)'
  };
};

// Plant type badge color mapping
const getPlantTypeBadgeStyle = (plantType: string | undefined): React.CSSProperties => {
  if (!plantType) return {};

  const typeLower = plantType.toLowerCase();

  // Define bright colors for transparent badges - only color and borderColor needed
  const colorMap: { [key: string]: { color: string; borderColor: string } } = {
    'indica': { color: '#9333ea', borderColor: '#9333ea' },
    'sativa': { color: '#22c55e', borderColor: '#22c55e' },
    'hybrid': { color: '#3b82f6', borderColor: '#3b82f6' },
    'cbd': { color: '#14b8a6', borderColor: '#14b8a6' },
    'balanced': { color: '#eab308', borderColor: '#eab308' },
    'blend': { color: '#f97316', borderColor: '#f97316' },
  };

  // Find matching color or use default
  for (const [key, style] of Object.entries(colorMap)) {
    if (typeLower.includes(key)) {
      return {
        backgroundColor: 'rgba(255, 255, 255, 0.85)',
        color: style.color,
        borderColor: style.borderColor,
        borderWidth: '2px',
        borderStyle: 'solid',
        padding: '0.125rem 0.375rem',
        fontSize: '0.625rem',
        fontWeight: '700',
        borderRadius: '0.25rem',
        display: 'inline-block',
        textTransform: 'uppercase',
        letterSpacing: '0.025em',
        textShadow: '0 0 2px rgba(255, 255, 255, 0.9)'
      };
    }
  }

  // Default style if no match
  return {
    backgroundColor: 'rgba(255, 255, 255, 0.85)',
    color: '#64748b',
    borderColor: '#64748b',
    borderWidth: '2px',
    borderStyle: 'solid',
    padding: '0.125rem 0.375rem',
    fontSize: '0.625rem',
    fontWeight: '700',
    borderRadius: '0.25rem',
    display: 'inline-block',
    textTransform: 'uppercase',
    letterSpacing: '0.025em',
    textShadow: '0 0 2px rgba(255, 255, 255, 0.9)'
  };
};

export default function POS() {
  // Get store context
  const { currentStore } = useStoreContext();

  // State management
  const [activeTab, setActiveTab] = useState<'sale' | 'history' | 'parked' | 'settings'>('sale');
  const [cart, setCart] = useState<CartItem[]>([]);
  const [customer, setCustomer] = useState<Customer | null>(null);
  const [products, setProducts] = useState<Product[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [showFilterPanel, setShowFilterPanel] = useState(false);
  const [selectedFilters, setSelectedFilters] = useState({
    subcategories: [] as string[],
    plantTypes: [] as string[],
    sizes: [] as string[],
    priceSort: 'none' as 'none' | 'asc' | 'desc',
    thcSort: 'none' as 'none' | 'asc' | 'desc',
    cbdSort: 'none' as 'none' | 'asc' | 'desc',
    inStockOnly: false
  });
  const [discount, setDiscount] = useState({ type: 'none' as 'none' | 'percentage' | 'fixed', value: 0 });
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
  const searchInputRef = useRef<HTMLInputElement>(null);
  const [detectedScanners, setDetectedScanners] = useState<any[]>([]);
  const [selectedProductBatches, setSelectedProductBatches] = useState<Product | null>(null);
  const [selectedScanner, setSelectedScanner] = useState<string | null>(null);
  const [showProductDetailsModal, setShowProductDetailsModal] = useState(false);
  const [selectedProductDetails, setSelectedProductDetails] = useState<any>(null);
  const [loadingProductDetails, setLoadingProductDetails] = useState(false);
  const [activeDetailsTab, setActiveDetailsTab] = useState('basic');
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
      if (!equivalent && item.product.category === 'Flower' && item.product.size && typeof item.product.size === 'string') {
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
      const itemDiscount = item.discount || 0;
      return total + (itemPrice - (itemPrice * itemDiscount / 100));
    }, 0);

    // Apply overall discount
    let discountAmount = 0;
    if (discount.type === 'percentage') {
      discountAmount = subtotal * (discount.value / 100);
    } else if (discount.type === 'fixed') {
      discountAmount = Math.min(discount.value, subtotal);
    }

    const discountedSubtotal = subtotal - discountAmount;
    const tax = discountedSubtotal * 0.13; // 13% tax rate
    const total = discountedSubtotal + tax;
    return { subtotal, discountAmount, discountedSubtotal, tax, total };
  };

  // Fetch products from API
  const fetchProducts = useCallback(async (query: string = '') => {
    try {
      setSearchLoading(true);
      const params = new URLSearchParams({ q: query || '', limit: '50' });

      // Add store filter if available
      if (currentStore?.id) {
        params.append('store_id', currentStore.id);
      }

      const response = await axios.get(`http://localhost:5024/api/search/products?${params}`);
      const productsData = response.data.products || [];

      // Map API response to our Product interface
      let mappedProducts = productsData.map((p: any) => ({
        ...p,
        price: p.price || p.unit_price || 0,
        quantity_available: p.available_quantity || p.stock_quantity || 0,
        subcategory: p.sub_category || p.subcategory,
        size: p.size || p.pack_size
      }));

      // Apply client-side filters
      if (selectedFilters.subcategories.length > 0) {
        mappedProducts = mappedProducts.filter((p: Product) =>
          selectedFilters.subcategories.includes(p.sub_category || p.subcategory)
        );
      }

      if (selectedFilters.plantTypes.length > 0) {
        mappedProducts = mappedProducts.filter((p: Product) => {
          const plantType = p.plant_type || p.strain_type || '';
          return selectedFilters.plantTypes.some(type =>
            plantType.toLowerCase().includes(type.toLowerCase())
          );
        });
      }

      if (selectedFilters.sizes.length > 0) {
        mappedProducts = mappedProducts.filter((p: Product) =>
          selectedFilters.sizes.includes(p.size)
        );
      }

      if (selectedFilters.inStockOnly) {
        mappedProducts = mappedProducts.filter((p: Product) =>
          (p.quantity_available || 0) > 0
        );
      }

      // Apply sorting
      if (selectedFilters.priceSort !== 'none') {
        mappedProducts = [...mappedProducts].sort((a, b) => {
          const diff = a.price - b.price;
          return selectedFilters.priceSort === 'asc' ? diff : -diff;
        });
      }

      if (selectedFilters.thcSort !== 'none') {
        mappedProducts = [...mappedProducts].sort((a, b) => {
          const diff = (a.thc_content || 0) - (b.thc_content || 0);
          return selectedFilters.thcSort === 'asc' ? diff : -diff;
        });
      }

      if (selectedFilters.cbdSort !== 'none') {
        mappedProducts = [...mappedProducts].sort((a, b) => {
          const diff = (a.cbd_content || 0) - (b.cbd_content || 0);
          return selectedFilters.cbdSort === 'asc' ? diff : -diff;
        });
      }

      setProducts(mappedProducts);
    } catch (error) {
      console.error('Error fetching products:', error);
    } finally {
      setSearchLoading(false);
    }
  }, [currentStore, selectedFilters]);

  // Focus search input when switching to sale tab or on initial load
  useEffect(() => {
    if (activeTab === 'sale' && searchInputRef.current) {
      setTimeout(() => {
        searchInputRef.current?.focus();
      }, 100);
    }
  }, [activeTab]);

  // Initial load
  // Fetch parked orders
  const fetchParkedOrders = async () => {
    try {
      const storeId = currentStore?.id || 'store_001';
      const parkedOrders = await posService.getParkedTransactions(storeId);
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
      const storeId = currentStore?.id || 'store_001';
      const history = await posService.getTransactionHistory(storeId);
      // Filter out parked transactions for the history view
      const completedTransactions = history.filter(t => t.status === 'completed');
      setTransactions(completedTransactions);
    } catch (error) {
      console.error('Failed to fetch transaction history:', error);
    }
  };

  useEffect(() => {
    fetchProducts();
    if (currentStore?.id) {
      fetchParkedOrders();
      fetchTransactionHistory();
    }
  }, [currentStore]);

  // Handle barcode scanning
  useEffect(() => {
    const handleBarcodeInput = async (e: KeyboardEvent) => {
      // Only process if scanner is enabled and we're on the sale tab
      if (!scannerEnabled || activeTab !== 'sale') return;

      // Barcode scanners typically send Enter key at the end
      if (e.key === 'Enter' && barcodeInput.length > 0) {
        try {
          // Use search API directly for barcode scanning
          const searchParams: any = { q: barcodeInput, limit: 1 };
          // Add store filter if available
          if (currentStore?.id) {
            searchParams.store_id = currentStore.id;
          }
          const products = await axios.get(`http://localhost:5024/api/search/products`, {
            params: searchParams
          });
          if (products.data.products?.length > 0) {
            const product = products.data.products[0];

            // Parse batches if it's a string
            const batches = typeof product.batches === 'string'
              ? JSON.parse(product.batches)
              : product.batches;

            // Check if barcode matches a specific batch (for GS1-128 barcodes with batch info)
            let matchedBatch = null;
            if (batches && batches.length > 0) {
              // Extract batch/lot from GS1-128 if present (AI 10 = Batch/Lot)
              let batchLotFromBarcode = null;
              if (barcodeInput.startsWith('01') && barcodeInput.length > 30) {
                // GS1-128 format: (01)GTIN(13)DATE(10)BATCH
                // Position 23 onwards typically contains batch/lot after date
                const batchStartPos = barcodeInput.indexOf('10', 16);
                if (batchStartPos > 0) {
                  batchLotFromBarcode = barcodeInput.substring(batchStartPos + 2);
                }
              }

              // Try to find matching batch
              if (batchLotFromBarcode) {
                matchedBatch = batches.find((b: Batch) =>
                  b.batch_lot === batchLotFromBarcode ||
                  b.batch_lot.includes(batchLotFromBarcode) ||
                  batchLotFromBarcode.includes(b.batch_lot)
                );
              }

              // If no match by batch lot, check GTINs
              if (!matchedBatch) {
                matchedBatch = batches.find((b: Batch) =>
                  b.case_gtin === barcodeInput ||
                  b.each_gtin === barcodeInput ||
                  (barcodeInput.includes(b.case_gtin || '') && b.case_gtin) ||
                  (barcodeInput.includes(b.each_gtin || '') && b.each_gtin)
                );
              }

              // If still no match but there's only one batch, use it
              if (!matchedBatch && batches.length === 1) {
                matchedBatch = batches[0];
              }
            }

            addToCart({
              ...product,
              price: product.price || product.unit_price || 0,
              quantity_available: product.available_quantity || product.stock_quantity || 0,
              subcategory: product.sub_category || product.subcategory,
            }, matchedBatch);
            // Clear search term after barcode scan
            setSearchTerm('');
          } else {
            alert(`Product not found for barcode: ${barcodeInput}`);
          }
        } catch (error) {
          console.error('Error searching for product:', error);
          alert(`Product not found for barcode: ${barcodeInput}`);
        } finally {
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
      fetchProducts(searchTerm);
    }, 300);

    return () => clearTimeout(timer);
  }, [searchTerm, selectedFilters, fetchProducts]);

  // Add to cart
  const addToCart = (product: Product, batch?: Batch) => {
    // If batch is provided, add with batch info
    if (batch) {
      const existingBatchItem = cart.find(item =>
        item.product.id === product.id &&
        item.batch?.batch_lot === batch.batch_lot
      );
      if (existingBatchItem) {
        updateQuantityForBatch(product.id, batch.batch_lot, existingBatchItem.quantity + 1);
      } else {
        setCart([...cart, { product, quantity: 1, batch }]);
      }
    } else {
      const existingItem = cart.find(item => item.product.id === product.id && !item.batch);
      if (existingItem) {
        updateQuantity(product.id, existingItem.quantity + 1);
      } else {
        setCart([...cart, { product, quantity: 1 }]);
      }
    }

    // Clear search and return focus to search input after adding to cart
    setTimeout(() => {
      if (searchInputRef.current && activeTab === 'sale') {
        setSearchTerm(''); // Clear search for next scan
        searchInputRef.current.focus();
      }
    }, 100);
  };

  // Update quantity for batch item
  const updateQuantityForBatch = (productId: string, batchLot: string, quantity: number) => {
    if (quantity <= 0) {
      removeFromCartWithBatch(productId, batchLot);
    } else {
      setCart(cart.map(item =>
        item.product.id === productId && item.batch?.batch_lot === batchLot
          ? { ...item, quantity }
          : item
      ));
    }
  };

  // Remove batch item from cart
  const removeFromCartWithBatch = (productId: string, batchLot: string) => {
    setCart(cart.filter(item =>
      !(item.product.id === productId && item.batch?.batch_lot === batchLot)
    ));
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

  // Fetch product details
  const fetchProductDetails = async (productId: string) => {
    setLoadingProductDetails(true);
    try {
      const response = await axios.get(`http://localhost:5024/api/products/details/${productId}`, {
        params: {
          store_id: currentStore?.id
        }
      });

      if (response.data) {
        setSelectedProductDetails(response.data);
        setShowProductDetailsModal(true);
      }
    } catch (error) {
      console.error('Error fetching product details:', error);
    } finally {
      setLoadingProductDetails(false);
    }
  };

  // Park sale
  const parkSale = async () => {
    if (cart.length === 0) return;

    setTransactionLoading(true);
    try {
      const { subtotal, discountAmount, discountedSubtotal, tax, total } = calculateTotals();

      const parkedData = {
        store_id: currentStore?.id || 'store_001',
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

  const { subtotal, discountAmount, discountedSubtotal, tax, total } = calculateTotals();
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
      <div className="bg-white  border-b">
        <div className="px-3 sm:px-6 py-3 sm:py-4">
          <div className="flex items-center justify-between">
            <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-6">
              <h1 className="text-lg sm:text-2xl font-bold">Point of Sale</h1>
              {currentStore && (
                <div className="flex items-center gap-2 px-3 py-1.5 bg-blue-50 text-accent-700 rounded-lg">
                  <Building2 className="w-4 h-4" />
                  <span className="text-sm font-medium">{currentStore.name}</span>
                </div>
              )}
              <div className="hidden sm:flex items-center gap-2 px-4 py-2 bg-primary-50 text-primary-700 rounded-lg">
                <Calendar className="w-4 h-4" />
                <span className="text-sm font-medium">Valid ID Date: {getValidAgeDate()} or earlier</span>
              </div>
            </div>
            <div className="flex items-center gap-2 sm:gap-6">
              <button
                onClick={() => setScannerEnabled(!scannerEnabled)}
                className={`p-2 rounded-lg transition-colors ${
                  scannerEnabled 
                    ? 'bg-primary-100 text-primary-600 hover:bg-green-200' 
                    : 'hover:bg-gray-50'
                }`}
                title={scannerEnabled ? 'Scanner Enabled' : 'Scanner Disabled'}
              >
                <Scan className="w-5 h-5" />
              </button>
              <button 
                onClick={toggleFullscreen}
                className={`p-2 rounded-lg transition-colors ${
                  isFullscreen 
                    ? 'bg-blue-100 text-accent-600 hover:bg-blue-200' 
                    : 'hover:bg-gray-50'
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
          <div className="flex gap-1 sm:gap-6 mt-3 sm:mt-4 overflow-x-auto">
            <button
              onClick={() => setActiveTab('sale')}
              className={`px-2 sm:px-4 py-1.5 sm:py-2 rounded-lg font-medium whitespace-nowrap ${
                activeTab === 'sale' ? 'bg-accent-500 text-white' : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              <ShoppingCart className="w-4 h-4 inline mr-1 sm:mr-2" />
              <span className="text-sm sm:text-base">New Sale</span>
            </button>
            <button
              onClick={() => setActiveTab('parked')}
              className={`px-2 sm:px-4 py-1.5 sm:py-2 rounded-lg font-medium whitespace-nowrap ${
                activeTab === 'parked' ? 'bg-accent-500 text-white' : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              <PauseCircle className="w-4 h-4 inline mr-1 sm:mr-2" />
              <span className="text-sm sm:text-base">Parked ({parkedSales.length})</span>
            </button>
            <button
              onClick={() => setActiveTab('history')}
              className={`px-2 sm:px-4 py-1.5 sm:py-2 rounded-lg font-medium whitespace-nowrap ${
                activeTab === 'history' ? 'bg-accent-500 text-white' : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              <History className="w-4 h-4 inline mr-1 sm:mr-2" />
              <span className="text-sm sm:text-base">History</span>
            </button>
            <button
              onClick={() => setActiveTab('settings')}
              className={`px-2 sm:px-4 py-1.5 sm:py-2 rounded-lg font-medium whitespace-nowrap ${
                activeTab === 'settings' ? 'bg-accent-500 text-white' : 'text-gray-600 hover:bg-gray-50'
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
            className="lg:hidden fixed bottom-4 right-4 z-30 bg-primary-500 text-white rounded-full p-6 border border-gray-200"
          >
            <ShoppingCart className="w-6 h-6" />
            {cart.length > 0 && (
              <span className="absolute -top-2 -right-2 bg-danger-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs font-bold">
                {cart.length}
              </span>
            )}
          </button>

          {/* Product Catalog */}
          <div className="flex-1 p-4 sm:p-6 overflow-y-auto">
            {/* Search and Filters */}
            <div className="mb-4 flex flex-col sm:flex-row gap-2 sm:gap-6">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                <input
                  ref={searchInputRef}
                  type="text"
                  placeholder="Search products or scan barcode..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  onKeyDown={async (e) => {
                    // Handle Enter key for barcode scanning (when scanner is not enabled)
                    if (e.key === 'Enter' && searchTerm.trim() && !scannerEnabled) {
                      e.preventDefault();
                      setSearchLoading(true);
                      try {
                        const searchParams: any = { q: searchTerm.trim(), limit: 1 };
                        // Add store filter if available
                        if (currentStore?.id) {
                          searchParams.store_id = currentStore.id;
                        }
                        const response = await axios.get(`http://localhost:5024/api/search/products`, {
                          params: searchParams
                        });

                        if (response.data.products?.length > 0) {
                          const product = response.data.products[0];

                          // Parse batches if it's a string
                          const batches = typeof product.batches === 'string'
                            ? JSON.parse(product.batches)
                            : product.batches;

                          // Check if search term matches a specific batch (for GS1-128 barcodes with batch info)
                          let matchedBatch = null;
                          if (batches && batches.length > 0) {
                            // Extract batch/lot from GS1-128 if present (AI 10 = Batch/Lot)
                            let batchLotFromBarcode = null;
                            if (searchTerm.startsWith('01') && searchTerm.length > 30) {
                              // GS1-128 format: (01)GTIN(13)DATE(10)BATCH
                              const batchStartPos = searchTerm.indexOf('10', 16);
                              if (batchStartPos > 0) {
                                batchLotFromBarcode = searchTerm.substring(batchStartPos + 2);
                              }
                            }

                            // Try to find matching batch
                            if (batchLotFromBarcode) {
                              matchedBatch = batches.find((b: Batch) =>
                                b.batch_lot === batchLotFromBarcode ||
                                b.batch_lot.includes(batchLotFromBarcode) ||
                                batchLotFromBarcode.includes(b.batch_lot)
                              );
                            }

                            // If no match by batch lot, check GTINs
                            if (!matchedBatch) {
                              matchedBatch = batches.find((b: Batch) =>
                                b.case_gtin === searchTerm ||
                                b.each_gtin === searchTerm ||
                                (searchTerm.includes(b.case_gtin || '') && b.case_gtin) ||
                                (searchTerm.includes(b.each_gtin || '') && b.each_gtin)
                              );
                            }

                            // If still no match but there's only one batch, use it
                            if (!matchedBatch && batches.length === 1) {
                              matchedBatch = batches[0];
                            }
                          }

                          // Add to cart with matched batch
                          addToCart({
                            ...product,
                            price: product.price || product.unit_price || 0,
                            quantity_available: product.available_quantity || product.stock_quantity || 0,
                            subcategory: product.sub_category || product.subcategory,
                          }, matchedBatch);

                          // Clear search term and refocus for next scan
                          setSearchTerm('');
                          setTimeout(() => {
                            searchInputRef.current?.focus();
                          }, 100);
                        }
                      } catch (error) {
                        console.error('Error searching for product:', error);
                      } finally {
                        setSearchLoading(false);
                      }
                    }
                  }}
                  className="w-full pl-10 pr-4 py-2 border rounded-lg text-sm sm:text-base"
                  autoFocus
                />
                {scannerEnabled && barcodeInput && (
                  <div className="absolute right-3 top-1/2 transform -translate-y-1/2 text-xs text-gray-500">
                    Scanning: {barcodeInput}
                  </div>
                )}
              </div>
              <button
                onClick={() => setShowFilterPanel(!showFilterPanel)}
                className={`p-2 border rounded-lg transition-colors relative ${
                  showFilterPanel ? 'bg-blue-50 border-blue-300 text-accent-700' : 'hover:bg-gray-50'
                }`}
                title="Filter products"
              >
                <SlidersHorizontal className="w-5 h-5" />
                {(selectedFilters.subcategories.length + selectedFilters.plantTypes.length + selectedFilters.sizes.length +
                  (selectedFilters.priceSort !== 'none' ? 1 : 0) +
                  (selectedFilters.thcSort !== 'none' ? 1 : 0) +
                  (selectedFilters.cbdSort !== 'none' ? 1 : 0)) > 0 && (
                  <span className="absolute -top-1 -right-1 px-1.5 py-0.5 bg-accent-600 text-white text-xs rounded-full min-w-[18px] text-center">
                    {selectedFilters.subcategories.length + selectedFilters.plantTypes.length + selectedFilters.sizes.length +
                     (selectedFilters.priceSort !== 'none' ? 1 : 0) +
                     (selectedFilters.thcSort !== 'none' ? 1 : 0) +
                     (selectedFilters.cbdSort !== 'none' ? 1 : 0)}
                  </span>
                )}
              </button>
            </div>

            {/* Main Content Area with Product Grid and Filter Panel */}
            <div className="flex gap-6">
              {/* Product Grid Container */}
              <div className="flex-1">
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
                  <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
                {products.map(product => {
                  const inStock = product.quantity_available > 0;
                  const lowStock = product.quantity_available > 0 && product.quantity_available < 10;
                  
                  return (
                    <div
                      key={product.id}
                      onClick={() => {
                        if (inStock) {
                          addToCart(product);
                        }
                      }}
                      className={`bg-white p-6 rounded-lg  transition-all ${
                        inStock
                          ? 'hover:border border-gray-200 cursor-pointer hover:scale-[1.02]'
                          : 'opacity-60 cursor-not-allowed'
                      }`}
                    >
                      {/* Product Image with Badges */}
                      <div className="relative mb-3">
                        {product.image_url ? (
                          <img
                            src={product.image_url}
                            alt={product.name}
                            className="w-full h-32 object-cover rounded"
                            onError={(e) => {
                              (e.target as HTMLImageElement).style.display = 'none';
                            }}
                          />
                        ) : (
                          <div className="w-full h-32 bg-gray-50 rounded flex items-center justify-center">
                            <Package className="w-8 h-8 text-gray-400" />
                          </div>
                        )}

                        {/* Badges overlay on image - positioned at exact corners */}
                        {/* Subcategory Badge (top-left corner) */}
                        {(product.sub_category || product.subcategory) && (
                          <span style={{
                            ...getSubcategoryBadgeStyle(product.sub_category || product.subcategory),
                            position: 'absolute',
                            top: '0',
                            left: '0',
                            borderTopLeftRadius: '0.5rem', // Match image corner radius
                            borderBottomRightRadius: '0.25rem',
                            borderTopRightRadius: '0',
                            borderBottomLeftRadius: '0',
                            boxShadow: '0 1px 3px rgba(0, 0, 0, 0.12)',
                          }}>
                            {product.sub_category || product.subcategory}
                          </span>
                        )}

                        {/* Plant Type Badge (top-right corner) */}
                        {(product.plant_type || product.strain_type) && (
                          <span style={{
                            ...getPlantTypeBadgeStyle(product.plant_type || product.strain_type),
                            position: 'absolute',
                            top: '0',
                            right: '0',
                            borderTopRightRadius: '0.5rem', // Match image corner radius
                            borderBottomLeftRadius: '0.25rem',
                            borderTopLeftRadius: '0',
                            borderBottomRightRadius: '0',
                            boxShadow: '0 1px 3px rgba(0, 0, 0, 0.12)',
                          }}>
                            {(product.plant_type || product.strain_type)?.replace(/\s*Dominant\s*/i, '')}
                          </span>
                        )}
                      </div>
                      <h3 className="font-semibold text-sm line-clamp-2">{product.name}</h3>
                      <div className="flex items-center justify-between mt-1">
                        <div>
                          <p className="text-xs text-gray-500">{product.brand}</p>
                          {(product.size || product.pack_size) && (
                            <p className="text-sm font-medium text-gray-700 mt-1">
                              {product.size || product.pack_size}
                            </p>
                          )}
                        </div>
                      </div>
                      <div className="mt-2 flex items-center justify-between">
                        <span className="text-lg font-bold">${product.price.toFixed(2)}</span>
                        <span className={`text-xs ${
                          !inStock ? 'text-red-500 font-medium' :
                          lowStock ? 'text-warning-600' : 
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
                      {/* Batch tracking indicator */}
                      {product.batch_count > 0 && (
                        <button
                          onClick={async (e) => {
                            e.stopPropagation();
                            // Fetch product details first
                            await fetchProductDetails(product.id || product.sku);
                            // Pass the batches to the modal
                            setSelectedProductBatches(product);
                            setShowProductDetailsModal(true);
                          }}
                          className="mt-2 flex items-center gap-1 text-xs text-accent-600 hover:text-accent-700"
                        >
                          <Package className="w-3 h-3" />
                          <span>{product.batch_count} batch{product.batch_count > 1 ? 'es' : ''}</span>
                        </button>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
              </div>

              {/* Filter Panel - Right Side */}
              <FilterPanel
                isOpen={showFilterPanel}
                onClose={() => setShowFilterPanel(false)}
                selectedFilters={selectedFilters}
                onFilterChange={setSelectedFilters}
                products={products}
              />
            </div>
          </div>

          {/* Cart Sidebar - Fixed on mobile, static on desktop */}
          <div className={`fixed inset-y-0 right-0 z-50 w-full sm:w-96 bg-white transform transition-transform duration-300 lg:static lg:translate-x-0 ${
            mobileCartOpen ? 'translate-x-0' : 'translate-x-full'
          } lg:border-l flex flex-col`}>
            {/* Customer Section */}
            <div className="p-6 border-b">
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-semibold">Customer</h3>
                <button
                  onClick={() => setShowCustomerModal(true)}
                  className="text-accent-500 hover:text-accent-600"
                >
                  {customer ? 'Change' : 'Select'}
                </button>
              </div>
              {customer ? (
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="font-medium">{customer.name}</p>
                  <p className="text-sm text-gray-600">{customer.phone}</p>
                  {customer.loyalty_points && (
                    <p className="text-sm text-primary-600">Points: {customer.loyalty_points}</p>
                  )}
                </div>
              ) : (
                <div className="flex gap-2">
                  <button
                    onClick={() => setShowCustomerModal(true)}
                    className="flex-1 px-3 py-2 bg-blue-50 text-accent-600 rounded-lg hover:bg-blue-100"
                  >
                    <Users className="w-4 h-4 inline mr-1" />
                    Returning
                  </button>
                  <button
                    onClick={() => setCustomer({ id: 'new', name: 'New Customer', is_verified: false })}
                    className="flex-1 px-3 py-2 bg-primary-50 text-primary-600 rounded-lg hover:bg-primary-100"
                  >
                    <UserPlus className="w-4 h-4 inline mr-1" />
                    New
                  </button>
                  <button
                    onClick={() => setCustomer({ id: 'anon', name: 'Anonymous', is_verified: true })}
                    className="flex-1 px-3 py-2 bg-gray-50 text-gray-600 rounded-lg hover:bg-gray-50"
                  >
                    <User className="w-4 h-4 inline mr-1" />
                    Anonymous
                  </button>
                </div>
              )}
            </div>

            {/* Weight Limit Warning */}
            {driedFlowerEquivalent > 0 && (
              <div className={`px-4 py-3 ${driedFlowerEquivalent > 30 ? 'bg-danger-50 text-red-700' : 'bg-blue-50 text-accent-700'}`}>
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
            <div className="flex-1 overflow-y-auto p-6">
              {cart.length === 0 ? (
                <div className="text-center text-gray-400 py-8">
                  <ShoppingCart className="w-12 h-12 mx-auto mb-2" />
                  <p>Cart is empty</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {cart.map((item, index) => (
                    <div key={`${item.product.id}_${item.batch?.batch_lot || 'no-batch'}_${index}`} className="bg-gray-50 p-4 rounded-lg">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h4 className="font-medium">{item.product.name}</h4>
                          <p className="text-sm text-gray-600">
                            ${item.product.price.toFixed(2)} x {item.quantity}
                          </p>
                          {item.batch && (
                            <p className="text-xs text-accent-600">
                              Batch: {item.batch.batch_lot}
                            </p>
                          )}
                          {item.discount && (
                            <p className="text-sm text-primary-600">
                              Discount: {item.discount}%
                            </p>
                          )}
                        </div>
                        <button
                          onClick={() => {
                            if (item.batch) {
                              removeFromCartWithBatch(item.product.id, item.batch.batch_lot);
                            } else {
                              removeFromCart(item.product.id);
                            }
                          }}
                          className="text-red-500 hover:text-danger-600"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                      <div className="flex items-center gap-2 mt-2">
                        <button
                          onClick={() => {
                            if (item.batch) {
                              updateQuantityForBatch(item.product.id, item.batch.batch_lot, item.quantity - 1);
                            } else {
                              updateQuantity(item.product.id, item.quantity - 1);
                            }
                          }}
                          className="w-8 h-8 flex items-center justify-center bg-white rounded border hover:bg-gray-50"
                        >
                          <Minus className="w-4 h-4" />
                        </button>
                        <span className="w-12 text-center">{item.quantity}</span>
                        <button
                          onClick={() => {
                            if (item.batch) {
                              updateQuantityForBatch(item.product.id, item.batch.batch_lot, item.quantity + 1);
                            } else {
                              updateQuantity(item.product.id, item.quantity + 1);
                            }
                          }}
                          className="w-8 h-8 flex items-center justify-center bg-white rounded border hover:bg-gray-50"
                        >
                          <Plus className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => {
                            const discount = prompt('Enter discount percentage:');
                            if (discount) applyDiscount(item.product.id, parseFloat(discount));
                          }}
                          className="ml-auto px-2 py-1 text-xs bg-warning-50 text-yellow-700 rounded hover:bg-warning-100"
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
            <div className="border-t p-6 space-y-2">
              <div className="flex justify-between text-sm">
                <span>Subtotal</span>
                <span>${subtotal.toFixed(2)}</span>
              </div>

              {/* Discount Section */}
              <div className="border-t pt-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm">Discount</span>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => {
                        if (discount.type === 'percentage') {
                          setDiscount({ type: 'none', value: 0 });
                        } else {
                          setDiscount({ type: 'percentage', value: 0 });
                        }
                      }}
                      className={`px-3 py-1 text-xs rounded ${
                        discount.type === 'percentage' ? 'bg-primary-600 text-white' : 'bg-gray-50 text-gray-600 hover:bg-gray-50'
                      }`}
                    >
                      %
                    </button>
                    <button
                      onClick={() => {
                        if (discount.type === 'fixed') {
                          setDiscount({ type: 'none', value: 0 });
                        } else {
                          setDiscount({ type: 'fixed', value: 0 });
                        }
                      }}
                      className={`px-3 py-1 text-xs rounded ${
                        discount.type === 'fixed' ? 'bg-primary-600 text-white' : 'bg-gray-50 text-gray-600 hover:bg-gray-50'
                      }`}
                    >
                      $
                    </button>
                    {discount.type !== 'none' && (
                      <input
                        type="number"
                        value={discount.value || ''}
                        onChange={(e) => setDiscount({ ...discount, value: parseFloat(e.target.value) || 0 })}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') {
                            e.preventDefault();
                          }
                        }}
                        className="w-20 px-2 py-1 border rounded text-sm text-right"
                        placeholder={discount.type === 'percentage' ? '0%' : '$0'}
                        min="0"
                        max={discount.type === 'percentage' ? '100' : undefined}
                      />
                    )}
                  </div>
                </div>
                {discountAmount > 0 && (
                  <div className="flex justify-between text-sm text-primary-600 mt-1">
                    <span>Discount applied</span>
                    <span>-${discountAmount.toFixed(2)}</span>
                  </div>
                )}
              </div>

              {discountAmount > 0 && (
                <div className="flex justify-between text-sm font-medium text-primary-600">
                  <span>After Discount</span>
                  <span>${discountedSubtotal.toFixed(2)}</span>
                </div>
              )}

              <div className="flex justify-between text-sm">
                <span>Tax (13%)</span>
                <span>${tax.toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-lg font-bold border-t pt-2">
                <span>Total</span>
                <span>${total.toFixed(2)}</span>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="p-6 border-t space-y-2">
              <div className="grid grid-cols-2 gap-2">
                <button
                  onClick={parkSale}
                  className="px-4 py-2 bg-warning-500 text-white rounded-lg hover:bg-warning-600"
                >
                  <PauseCircle className="w-4 h-4 inline mr-1" />
                  Park Sale
                </button>
                <button
                  onClick={() => { setCart([]); setCustomer(null); }}
                  className="px-4 py-2 bg-danger-500 text-white rounded-lg hover:bg-danger-600"
                >
                  <X className="w-4 h-4 inline mr-1" />
                  Clear
                </button>
              </div>
              <button
                onClick={() => setShowPaymentModal(true)}
                disabled={cart.length === 0 || !customer || driedFlowerEquivalent > 30}
                className="w-full px-4 py-3 bg-primary-500 text-white rounded-lg hover:bg-primary-600 disabled:bg-gray-300 disabled:cursor-not-allowed"
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
        <div className="flex-1 p-4 sm:p-6 overflow-y-auto">
          <h2 className="text-lg sm:text-xl font-bold mb-4">Parked Sales</h2>
          {parkedSales.length === 0 ? (
            <div className="text-center text-gray-400 py-12">
              <PauseCircle className="w-12 h-12 mx-auto mb-2" />
              <p>No parked sales</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
              {parkedSales.map(sale => (
                <div key={sale.id} className="bg-white p-6 rounded-lg ">
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
                    className="w-full px-3 py-2 bg-accent-500 text-white rounded hover:bg-accent-600"
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
        <TransactionHistory />
      )}

      {/* Settings Tab */}
      {activeTab === 'settings' && (
        <div className="flex-1 p-4 sm:p-6 overflow-y-auto">
          <h2 className="text-xl font-bold mb-6">POS Settings</h2>
          
          <div className="space-y-6">
            {/* Hardware Configuration */}
            <div className="bg-white p-6 rounded-lg ">
              <h3 className="text-lg font-semibold mb-4">Hardware Configuration</h3>
              
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
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
                  <div className="flex items-center gap-4">
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
                    <div className="flex items-center gap-4">
                      <Scan className="w-5 h-5 text-gray-400" />
                      <div>
                        <p className="font-medium">Barcode Scanners</p>
                        <p className="text-sm text-gray-500">Manage connected scanners</p>
                      </div>
                    </div>
                    <button
                      onClick={detectScanners}
                      disabled={detectingHardware}
                      className="px-3 py-1 bg-blue-50 text-accent-600 rounded-lg hover:bg-blue-100 flex items-center gap-2 text-sm"
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
                        <div key={scanner.id} className="p-4 bg-gray-50 rounded-lg">
                          <div className="flex items-start justify-between">
                            <div className="flex items-start gap-4">
                              {/* Connection Type Icon */}
                              {scanner.type === 'USB' && <Usb className="w-5 h-5 text-gray-500 mt-1" />}
                              {scanner.type === 'Bluetooth' && <Bluetooth className="w-5 h-5 text-accent-500 mt-1" />}
                              {scanner.type === 'Network' && <Network className="w-5 h-5 text-primary-500 mt-1" />}
                              
                              <div className="flex-1">
                                <p className="font-medium text-sm">{scanner.name}</p>
                                <p className="text-xs text-gray-500">
                                  {scanner.manufacturer}
                                  {scanner.vendor_id && ` (${scanner.vendor_id}:${scanner.product_id})`}
                                </p>
                                <div className="flex items-center gap-2 mt-2">
                                  <span className={`text-xs px-2 py-1 rounded ${
                                    scanner.status === 'connected' || scanner.status === 'paired' ? 
                                    'bg-primary-100 text-primary-700' : 
                                    'bg-gray-50 text-gray-600'
                                  }`}>
                                    {scanner.status}
                                  </span>
                                  {scanner.confidence && (
                                    <span className={`text-xs px-2 py-1 rounded ${
                                      scanner.confidence === 'high' ? 'bg-blue-100 text-accent-700' :
                                      scanner.confidence === 'medium' ? 'bg-warning-100 text-yellow-700' :
                                      'bg-gray-50 text-gray-600'
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
                                className="px-2 py-1 text-xs bg-blue-50 text-accent-600 rounded hover:bg-blue-100"
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
                  <div className="flex items-center gap-4">
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
            <div className="bg-white p-6 rounded-lg ">
              <h3 className="text-lg font-semibold mb-4">Cash Management</h3>
              <div className="grid grid-cols-2 gap-6">
                <button className="px-4 py-2 bg-blue-50 text-accent-600 rounded-lg hover:bg-blue-100">
                  <Calculator className="w-4 h-4 inline mr-2" />
                  Open Register
                </button>
                <button className="px-4 py-2 bg-blue-50 text-accent-600 rounded-lg hover:bg-blue-100">
                  <DollarSign className="w-4 h-4 inline mr-2" />
                  Cash Count
                </button>
                <button className="px-4 py-2 bg-blue-50 text-accent-600 rounded-lg hover:bg-blue-100">
                  <Clock className="w-4 h-4 inline mr-2" />
                  End of Day
                </button>
                <button className="px-4 py-2 bg-blue-50 text-accent-600 rounded-lg hover:bg-blue-100">
                  <Printer className="w-4 h-4 inline mr-2" />
                  Print Report
                </button>
              </div>
            </div>

            {/* Discount Settings */}
            <div className="bg-white p-6 rounded-lg ">
              <h3 className="text-lg font-semibold mb-4">Discounts & Promotions</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <div>
                    <p className="font-medium">Senior Discount</p>
                    <p className="text-sm text-gray-500">10% off for 65+</p>
                  </div>
                  <span className="px-2 py-1 bg-primary-100 text-primary-700 rounded text-sm">Active</span>
                </div>
                <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <div>
                    <p className="font-medium">Happy Hour</p>
                    <p className="text-sm text-gray-500">15% off 4-6pm</p>
                  </div>
                  <span className="px-2 py-1 bg-primary-100 text-primary-700 rounded text-sm">Active</span>
                </div>
                <button className="w-full px-4 py-2 border-2 border-dashed border-gray-200 text-gray-500 rounded-lg hover:border-gray-300">
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
              const { subtotal, discountAmount, discountedSubtotal, tax, total } = calculateTotals();
              
              // Create transaction via API
              const transactionData = {
                store_id: currentStore?.id || 'store_001',
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


      {/* Product Details Modal with Tabs */}
      <ProductDetailsModal
        isOpen={showProductDetailsModal}
        onClose={() => {
          setShowProductDetailsModal(false);
          setSelectedProductDetails(null);
          setSelectedProductBatches(null);
          setActiveDetailsTab('basic');
          // Focus back to search after modal closes
          setTimeout(() => searchInputRef.current?.focus(), 100);
        }}
        productDetails={selectedProductDetails}
        batches={selectedProductBatches?.batches}
        onAddToCart={addToCart}
        onAddBatchToCart={addToCart}
      />
    </div>
  );
}