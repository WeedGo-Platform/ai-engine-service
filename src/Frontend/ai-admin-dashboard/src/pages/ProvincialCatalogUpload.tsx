import React, { useState, useRef, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Upload, AlertCircle, CheckCircle, FileText, Loader2, Calendar, Package, Search, Filter, Download, Eye, ChevronDown, ChevronUp, Info, Leaf, FlaskConical, Box, Zap } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { getApiEndpoint } from '../config/app.config';
import { uploadProvincialCatalog } from '../services/catalogService';
import { useQuery } from '@tanstack/react-query';

interface UploadStatus {
  type: 'idle' | 'uploading' | 'success' | 'error';
  message?: string;
  stats?: {
    totalRecords?: number;
    inserted?: number;
    updated?: number;
    errors?: number;
  };
}

interface CatalogProduct {
  // System fields
  id: string;
  slug: string;
  created_at: string;
  updated_at: string;
  rating?: number;
  rating_count?: number;
  
  // Product identification
  ocs_variant_number: string;
  ocs_item_number: number;
  gtin: string;
  product_name: string;
  brand: string;
  brand_name?: string; // Alias for compatibility
  supplier_name: string;
  
  // Categories
  category: string;
  sub_category: string;
  subcategory_product_class?: string; // Alias for compatibility
  sub_sub_category: string;
  product_subclass?: string; // Alias for compatibility
  
  // Descriptions
  product_short_description: string;
  product_long_description: string;
  
  // Physical properties
  size: string;
  colour: string;
  net_weight: number;
  unit_of_measure: string;
  pack_size: number;
  number_of_items_in_retail_pack: number;
  
  // Pricing & Inventory
  unit_price: number;
  stock_status: string;
  inventory_status: string;
  
  // THC/CBD Content
  minimum_thc_content_percent: number;
  maximum_thc_content_percent: number;
  thc_content_per_unit: number;
  thc_content_per_volume: number;
  thc_min: number;
  thc_max: number;
  minimum_cbd_content_percent: number;
  maximum_cbd_content_percent: number;
  cbd_content_per_unit: number;
  cbd_content_per_volume: number;
  cbd_min: number;
  cbd_max: number;
  dried_flower_cannabis_equivalency: number;
  
  // Cultivation
  plant_type: string;
  strain_type: string;
  terpenes: string;
  growing_method: string;
  grow_medium: string;
  grow_method: string;
  grow_region: string;
  ontario_grown: string;
  craft: string;
  
  // Processing
  drying_method: string;
  trimming_method: string;
  extraction_process: string;
  carrier_oil: string;
  
  // Product specs
  street_name: string;
  ingredients: string;
  food_allergens: string;
  storage_criteria: string;
  
  // Dimensions
  physical_dimension_width: number;
  physical_dimension_height: number;
  physical_dimension_depth: number;
  physical_dimension_volume: number;
  physical_dimension_weight: number;
  
  // Packaging
  eaches_per_inner_pack: number;
  eaches_per_master_case: number;
  
  // Device specs (for vaporizers)
  heating_element_type: string;
  battery_type: string;
  rechargeable_battery: boolean;
  removable_battery: boolean;
  replacement_parts_available: boolean;
  temperature_control: string;
  temperature_display: string;
  compatibility: string;
  
  // Logistics
  fulfilment_method: string;
  delivery_tier: string;
  
  // Media
  image_url: string;
}

interface CatalogStats {
  total_products: number;
  last_updated: string;
  categories: { [key: string]: number };
}

// Helper component for displaying field details
const DetailField: React.FC<{ label: string; value: any }> = ({ label, value }) => (
  <div className="space-y-1">
    <div className="text-xs font-medium text-gray-500">{label}</div>
    <div className="text-sm text-gray-900">{value || '-'}</div>
  </div>
);

const ProvincialCatalogUpload: React.FC = () => {
  const { t } = useTranslation(['catalog', 'common']);
  const { user, isSuperAdmin } = useAuth();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedProvince, setSelectedProvince] = useState<string>('ON');
  const [uploadStatus, setUploadStatus] = useState<UploadStatus>({ type: 'idle' });
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [expandedRow, setExpandedRow] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'basic' | 'content' | 'physical' | 'cultivation' | 'device' | 'logistics'>('basic');
  const productsPerPage = 20;

  // Check if user can upload
  const canUpload = isSuperAdmin();

  // Fetch catalog stats
  const { data: catalogStats, refetch: refetchStats } = useQuery<CatalogStats>({
    queryKey: ['catalog-stats', selectedProvince],
    queryFn: async () => {
      const response = await fetch(getApiEndpoint(`/province/catalog/${selectedProvince.toLowerCase()}/stats`));
      if (!response.ok) {
        // Return mock data if endpoint doesn't exist yet
        return {
          total_products: 0,
          last_updated: new Date().toISOString(),
          categories: {}
        };
      }
      return response.json();
    }
  });

  // Fetch catalog products
  const { data: catalogProducts, isLoading, refetch: refetchProducts } = useQuery<CatalogProduct[]>({
    queryKey: ['catalog-products', selectedProvince, searchTerm, selectedCategory, currentPage],
    queryFn: async () => {
      const params = new URLSearchParams({
        page: currentPage.toString(),
        limit: productsPerPage.toString(),
        ...(searchTerm && { search: searchTerm }),
        ...(selectedCategory && { category: selectedCategory })
      });
      
      const response = await fetch(getApiEndpoint(`/province/catalog/${selectedProvince.toLowerCase()}?${params}`));
      if (!response.ok) {
        return [];
      }
      const data = await response.json();
      return data.products || [];
    }
  });

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      // Validate file type
      const validTypes = ['.csv', '.xlsx', '.xls'];
      const fileExt = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
      
      if (!validTypes.includes(fileExt)) {
        setUploadStatus({
          type: 'error',
          message: t('catalog:upload.invalidFileType')
        });
        return;
      }
      
      setSelectedFile(file);
      setUploadStatus({ type: 'idle' });
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setUploadStatus({
        type: 'error',
        message: t('catalog:upload.pleaseSelectFile')
      });
      return;
    }

    setUploadStatus({ type: 'uploading', message: t('catalog:upload.processingFile') });

    try {
      const result = await uploadProvincialCatalog(selectedFile, selectedProvince);
      
      setUploadStatus({
        type: 'success',
        message: t('catalog:upload.uploadSuccess'),
        stats: result.stats
      });
      
      // Reset file selection and refresh data
      setSelectedFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      
      // Refresh the catalog data
      refetchStats();
      refetchProducts();
    } catch (error) {
      setUploadStatus({
        type: 'error',
        message: error instanceof Error ? error.message : t('catalog:upload.uploadFailed')
      });
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (!canUpload) return;
    
    const file = e.dataTransfer.files?.[0];
    if (file) {
      const validTypes = ['.csv', '.xlsx', '.xls'];
      const fileExt = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
      
      if (!validTypes.includes(fileExt)) {
        setUploadStatus({
          type: 'error',
          message: t('catalog:upload.invalidFileType')
        });
        return;
      }
      
      setSelectedFile(file);
      setUploadStatus({ type: 'idle' });
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="max-w-7xl mx-auto p-4 sm:p-6">
      <div className="mb-6 sm:mb-8">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white mb-2">{t('catalog:titles.main')}</h1>
        <p className="text-sm sm:text-base text-gray-600 dark:text-gray-400">
          {t('catalog:descriptions.main')}
        </p>
      </div>

      {/* Catalog Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6 mb-4 sm:mb-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 sm:p-6 transition-colors">
          <div className="flex items-center">
            <Package className="h-8 w-8 sm:h-10 sm:w-10 text-accent-600 dark:text-accent-500 mr-3 flex-shrink-0" />
            <div className="min-w-0">
              <p className="text-xs sm:text-sm font-medium text-gray-600 dark:text-gray-400">{t('catalog:stats.totalProducts')}</p>
              <p className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white">{catalogStats?.total_products || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 sm:p-6 transition-colors">
          <div className="flex items-center">
            <Calendar className="h-8 w-8 sm:h-10 sm:w-10 text-primary-600 dark:text-primary-400 mr-3 flex-shrink-0" />
            <div className="min-w-0">
              <p className="text-xs sm:text-sm font-medium text-gray-600 dark:text-gray-400">{t('catalog:stats.lastUpdated')}</p>
              <p className="text-base sm:text-lg font-semibold text-gray-900 dark:text-white truncate">
                {catalogStats?.last_updated ? formatDate(catalogStats.last_updated) : t('catalog:stats.never')}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 sm:p-6 transition-colors">
          <div className="flex items-center">
            <Filter className="h-8 w-8 sm:h-10 sm:w-10 text-purple-600 dark:text-purple-400 mr-3 flex-shrink-0" />
            <div className="min-w-0">
              <p className="text-xs sm:text-sm font-medium text-gray-600 dark:text-gray-400">{t('catalog:stats.categories')}</p>
              <p className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white">
                {Object.keys(catalogStats?.categories || {}).length}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Province Selection and Upload Section (Super Admin Only) */}
      {canUpload && (
        <>
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 sm:p-6 mb-4 sm:mb-6 transition-colors">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  {t('catalog:descriptions.selectProvince')}
                </label>
                <select
                  value={selectedProvince}
                  onChange={(e) => setSelectedProvince(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 transition-colors"
                >
                  <option value="ON">{t('catalog:provinces.ontario')}</option>
                  <option value="BC" disabled>{t('catalog:provinces.bc')}</option>
                  <option value="AB" disabled>{t('catalog:provinces.alberta')}</option>
                  <option value="QC" disabled>{t('catalog:provinces.quebec')}</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  {t('catalog:upload.selectFile')}
                </label>
                <div className="flex flex-col sm:flex-row items-start sm:items-center gap-2 sm:gap-2">
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".csv,.xlsx,.xls"
                    onChange={handleFileSelect}
                    className="hidden"
                    id="file-upload"
                  />
                  <label
                    htmlFor="file-upload"
                    className="inline-flex items-center justify-center px-4 py-2.5 sm:py-2 border border-gray-200 dark:border-gray-600 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 dark:focus:ring-blue-400 cursor-pointer transition-all active:scale-95 touch-manipulation w-full sm:w-auto"
                  >
                    <Upload className="h-4 w-4 mr-2" />
                    {t('catalog:upload.chooseFile')}
                  </label>
                  {selectedFile && (
                    <span className="text-sm text-gray-600 dark:text-gray-400 truncate max-w-full sm:max-w-xs">{selectedFile.name}</span>
                  )}
                  <button
                    onClick={handleUpload}
                    disabled={!selectedFile || uploadStatus.type === 'uploading'}
                    className={`px-4 py-2.5 sm:py-2 rounded-lg font-medium transition-all active:scale-95 touch-manipulation w-full sm:w-auto ${
                      !selectedFile || uploadStatus.type === 'uploading'
                        ? 'bg-gray-300 dark:bg-gray-600 text-gray-500 dark:text-gray-400 cursor-not-allowed'
                        : 'bg-accent-600 dark:bg-accent-500 text-white hover:bg-accent-700 dark:hover:bg-accent-600'
                    }`}
                  >
                    {uploadStatus.type === 'uploading' ? (
                      <>
                        <Loader2 className="inline-block h-4 w-4 mr-2 animate-spin" />
                        {t('catalog:upload.uploading')}
                      </>
                    ) : (
                      t('catalog:upload.uploadButton')
                    )}
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Upload Status */}
          {uploadStatus.type !== 'idle' && (
            <div className={`rounded-lg p-4 sm:p-6 mb-4 sm:mb-6 ${
              uploadStatus.type === 'error' ? 'bg-danger-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800' :
              uploadStatus.type === 'success' ? 'bg-primary-50 dark:bg-green-900/30 border border-green-200 dark:border-green-800' :
              'bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-800'
            }`}>
              <div className="flex items-start">
                {uploadStatus.type === 'uploading' && (
                  <Loader2 className="h-5 w-5 text-accent-600 dark:text-accent-400 mr-3 animate-spin flex-shrink-0" />
                )}
                {uploadStatus.type === 'success' && (
                  <CheckCircle className="h-5 w-5 text-primary-600 dark:text-green-400 mr-3 flex-shrink-0" />
                )}
                {uploadStatus.type === 'error' && (
                  <AlertCircle className="h-5 w-5 text-danger-600 dark:text-red-400 mr-3 flex-shrink-0" />
                )}

                <div className="flex-1 min-w-0">
                  <p className={`text-sm font-medium ${
                    uploadStatus.type === 'error' ? 'text-danger-800 dark:text-red-300' :
                    uploadStatus.type === 'success' ? 'text-primary-800 dark:text-green-300' :
                    'text-blue-800 dark:text-blue-300'
                  }`}>
                    {uploadStatus.message}
                  </p>

                  {uploadStatus.stats && (
                    <div className="mt-2 text-sm text-gray-600 dark:text-gray-400 space-y-1">
                      <p>{t('catalog:stats.totalRecords')}: {uploadStatus.stats.totalRecords}</p>
                      <p>{t('catalog:stats.inserted')}: {uploadStatus.stats.inserted}</p>
                      <p>{t('catalog:stats.updated')}: {uploadStatus.stats.updated}</p>
                      {uploadStatus.stats.errors > 0 && (
                        <p className="text-danger-600 dark:text-red-400">{t('catalog:stats.errors')}: {uploadStatus.stats.errors}</p>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </>
      )}

      {/* Non-Super Admin Province View */}
      {!canUpload && (
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 sm:p-6 mb-4 sm:mb-6 transition-colors">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                {t('catalog:descriptions.viewingProvince')}
              </label>
              <select
                value={selectedProvince}
                onChange={(e) => setSelectedProvince(e.target.value)}
                className="px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 transition-colors"
              >
                <option value="ON">{t('catalog:provinces.ontario')}</option>
                <option value="BC" disabled>{t('catalog:provinces.bc')}</option>
                <option value="AB" disabled>{t('catalog:provinces.alberta')}</option>
                <option value="QC" disabled>{t('catalog:provinces.quebec')}</option>
              </select>
            </div>
            <div className="text-sm text-gray-500 dark:text-gray-400">
              <Calendar className="inline-block h-4 w-4 mr-1" />
              {t('catalog:messages.lastCatalogUpdate')} {catalogStats?.last_updated ? formatDate(catalogStats.last_updated) : t('catalog:stats.never')}
            </div>
          </div>
        </div>
      )}

      {/* Search and Filter Bar */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 sm:p-6 mb-4 sm:mb-6 transition-colors">
        <div className="flex flex-col sm:flex-row gap-3 sm:gap-6">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 sm:h-5 sm:w-5 text-gray-400 dark:text-gray-500" />
              <input
                type="text"
                placeholder={t('catalog:search.placeholder')}
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-9 sm:pl-10 pr-3 py-2 text-sm border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 transition-colors"
              />
            </div>
          </div>

          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="px-3 py-2 text-sm border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 transition-colors"
          >
            <option value="">{t('catalog:search.allCategories')}</option>
            {Object.keys(catalogStats?.categories || {}).map(category => (
              <option key={category} value={category}>
                {category} ({catalogStats?.categories[category]})
              </option>
            ))}
          </select>

          <button className="w-full sm:w-auto px-4 py-2.5 sm:py-2 border border-gray-200 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 active:scale-95 transition-all touch-manipulation">
            <Download className="h-4 w-4 inline-block mr-2" />
            <span className="text-sm font-medium">{t('catalog:buttons.export')}</span>
          </button>
        </div>
      </div>

      {/* Products Table */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden transition-colors">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead className="bg-gray-50 dark:bg-gray-900">
              <tr>
                {/* ID column first (not in Excel but needed for database) */}
                <th className="sticky left-0 z-10 bg-gray-50 dark:bg-gray-900 px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">ID</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">Slug</th>
                {/* Match Excel column order and names exactly */}
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">Category</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">Sub-Category</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">Sub-Sub-Category</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">Product Name</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">Brand</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">Supplier Name</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">Product Short Description</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">Product Long Description</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">Size</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">Colour</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">Image URL</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">Unit of Measure</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">Stock Status</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">Unit Price</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">Pack Size</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">Minimum THC Content (%)</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">Maximum THC Content (%)</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">THC Content Per Unit</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">THC Content Per Volume</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">Minimum CBD Content (%)</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">Maximum CBD Content (%)</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">CBD Content Per Unit</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">CBD Content Per Volume</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">Dried Flower Cannabis Equivalency</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">Plant Type</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">Terpenes</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">GrowingMethod</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">Number of Items in a Retail Pack</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">GTIN</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">OCS Item Number</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">OCS Variant Number</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">Physical Dimension Width</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">Physical Dimension Height</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">Physical Dimension Depth</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">Physical Dimension Volume</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">Physical Dimension Weight</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">Eaches Per Inner Pack</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">Eaches Per Master Case</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">Inventory Status</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">Storage Criteria</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">Food Allergens</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">Ingredients</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">Street Name</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">Grow Medium</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">Grow Method</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">Grow Region</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">Drying Method</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">Trimming Method</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">Extraction Process</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">Carrier Oil</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">Heating Element Type</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">Battery Type</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">Rechargeable Battery</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">Removable Battery</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">Replacement Parts Available</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">Temperature Control</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">Temperature Display</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">Compatibility</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">THC Min</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">THC Max</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">CBD Min</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">CBD Max</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">Net Weight</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">Ontario Grown</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">Craft</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">Fulfilment Method</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">Delivery Tier</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">Strain Type</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">Rating</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">Rating Count</th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
              {isLoading ? (
                <tr>
                  <td colSpan={71} className="px-6 py-4 text-center text-gray-500 dark:text-gray-400">
                    <Loader2 className="inline-block h-5 w-5 animate-spin mr-2" />
                    {t('catalog:table.loadingCatalog')}
                  </td>
                </tr>
              ) : catalogProducts && catalogProducts.length > 0 ? (
                catalogProducts.map((product: any) => (
                  <tr key={product.ocs_variant_number || product.id} className="hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                    {/* Match the column order of headers */}
                    <td className="sticky left-0 z-10 bg-white dark:bg-gray-800 px-3 py-2 whitespace-nowrap text-xs text-gray-900 dark:text-white">{product.id || 'N/A'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900 dark:text-white max-w-xs truncate" title={product.slug || '-'}>{product.slug || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900 dark:text-white">{product.category || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900 dark:text-white">{product.sub_category || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900 dark:text-white">{product.sub_sub_category || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900 dark:text-white">{product.product_name || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900 dark:text-white">{product.brand || product.brand_name || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900 dark:text-white">{product.supplier_name || '-'}</td>
                    <td className="px-3 py-2 max-w-xs truncate text-xs text-gray-900" title={product.product_short_description}>{product.product_short_description || '-'}</td>
                    <td className="px-3 py-2 max-w-xs truncate text-xs text-gray-900" title={product.product_long_description}>{product.product_long_description || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900 dark:text-white">{product.size || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900 dark:text-white">{product.colour || '-'}</td>
                    <td className="px-3 py-2 max-w-xs truncate text-xs text-gray-900" title={product.image_url}>{product.image_url || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900 dark:text-white">{product.unit_of_measure || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900 dark:text-white">{product.stock_status || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900 dark:text-white">{product.unit_price ?? '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900 dark:text-white">{product.pack_size || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900 dark:text-white">{product.minimum_thc_content_percent ?? '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900 dark:text-white">{product.maximum_thc_content_percent ?? '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900 dark:text-white">{product.thc_content_per_unit || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900 dark:text-white">{product.thc_content_per_volume || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900 dark:text-white">{product.minimum_cbd_content_percent ?? '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900 dark:text-white">{product.maximum_cbd_content_percent ?? '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900 dark:text-white">{product.cbd_content_per_unit || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900 dark:text-white">{product.cbd_content_per_volume || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900 dark:text-white">{product.dried_flower_cannabis_equivalency || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900 dark:text-white">{product.plant_type || '-'}</td>
                    <td className="px-3 py-2 max-w-xs truncate text-xs text-gray-900" title={product.terpenes}>{product.terpenes || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900 dark:text-white">{product.growing_method || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900 dark:text-white">{product.number_of_items_in_retail_pack || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900 dark:text-white">{product.gtin || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900 dark:text-white">{product.ocs_item_number || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900 dark:text-white">{product.ocs_variant_number || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900 dark:text-white">{product.physical_dimension_width || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900 dark:text-white">{product.physical_dimension_height || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900 dark:text-white">{product.physical_dimension_depth || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900 dark:text-white">{product.physical_dimension_volume || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900 dark:text-white">{product.physical_dimension_weight || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900 dark:text-white">{product.eaches_per_inner_pack || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900 dark:text-white">{product.eaches_per_master_case || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900 dark:text-white">{product.inventory_status || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900 dark:text-white">{product.storage_criteria || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900 dark:text-white">{product.food_allergens || '-'}</td>
                    <td className="px-3 py-2 max-w-xs truncate text-xs text-gray-900" title={product.ingredients}>{product.ingredients || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900 dark:text-white">{product.street_name || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900 dark:text-white">{product.grow_medium || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900 dark:text-white">{product.grow_method || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900 dark:text-white">{product.grow_region || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900 dark:text-white">{product.drying_method || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900 dark:text-white">{product.trimming_method || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900 dark:text-white">{product.extraction_process || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900 dark:text-white">{product.carrier_oil || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900 dark:text-white">{product.heating_element_type || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900 dark:text-white">{product.battery_type || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900 dark:text-white">{product.rechargeable_battery ?? '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900 dark:text-white">{product.removable_battery ?? '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900 dark:text-white">{product.replacement_parts_available ?? '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900 dark:text-white">{product.temperature_control || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900 dark:text-white">{product.temperature_display || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900 dark:text-white">{product.compatibility || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900 dark:text-white">{product.thc_min || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900 dark:text-white">{product.thc_max || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900 dark:text-white">{product.cbd_min || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900 dark:text-white">{product.cbd_max || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900 dark:text-white">{product.net_weight || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900 dark:text-white">{product.ontario_grown || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900 dark:text-white">{product.craft || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900 dark:text-white">{product.fulfilment_method || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900 dark:text-white">{product.delivery_tier || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900 dark:text-white">{product.strain_type || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900 dark:text-white">{product.rating ?? '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900 dark:text-white">{product.rating_count ?? '-'}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={71} className="px-6 py-4 text-center text-gray-500 dark:text-gray-400">
                    {t('catalog:table.noProductsFound')}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {catalogProducts && catalogProducts.length > 0 && (
          <div className="bg-gray-50 dark:bg-gray-700 px-4 sm:px-6 py-3 flex flex-col sm:flex-row items-center justify-between gap-3 transition-colors">
            <div className="text-sm text-gray-700 dark:text-gray-300">
              {t('catalog:table.showingPage', { page: currentPage })}
            </div>
            <div className="flex space-x-2">
              <button
                onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                disabled={currentPage === 1}
                className="px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg text-sm text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed active:scale-95 transition-all touch-manipulation"
              >
                {t('catalog:buttons.previous')}
              </button>
              <button
                onClick={() => setCurrentPage(currentPage + 1)}
                disabled={catalogProducts.length < productsPerPage}
                className="px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg text-sm text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed active:scale-95 transition-all touch-manipulation"
              >
                {t('catalog:buttons.next')}
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Instructions (Super Admin Only) */}
      {canUpload && (
        <div className="mt-6 sm:mt-8 bg-blue-50 dark:bg-blue-900/30 rounded-lg p-4 sm:p-6 border border-blue-200 dark:border-blue-800 transition-colors">
          <h3 className="text-base sm:text-lg font-semibold text-blue-900 dark:text-blue-300 mb-3">{t('catalog:titles.uploadInstructions')}</h3>
          <ul className="space-y-2 text-sm text-blue-800 dark:text-blue-300">
            <li className="flex items-start">
              <span className="block w-1.5 h-1.5 rounded-full bg-accent-600 mt-1.5 mr-2 flex-shrink-0"></span>
              <span>{t('catalog:instructions.line1')}</span>
            </li>
            <li className="flex items-start">
              <span className="block w-1.5 h-1.5 rounded-full bg-accent-600 mt-1.5 mr-2 flex-shrink-0"></span>
              <span>{t('catalog:instructions.line2')}</span>
            </li>
            <li className="flex items-start">
              <span className="block w-1.5 h-1.5 rounded-full bg-accent-600 mt-1.5 mr-2 flex-shrink-0"></span>
              <span>{t('catalog:instructions.line3')}</span>
            </li>
            <li className="flex items-start">
              <span className="block w-1.5 h-1.5 rounded-full bg-accent-600 mt-1.5 mr-2 flex-shrink-0"></span>
              <span>{t('catalog:instructions.line4')}</span>
            </li>
          </ul>
        </div>
      )}
    </div>
  );
};

export default ProvincialCatalogUpload;