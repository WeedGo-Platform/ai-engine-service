import React, { useState, useRef, useEffect } from 'react';
import { Upload, AlertCircle, CheckCircle, FileText, Loader2, Calendar, Package, Search, Filter, Download, Eye, ChevronDown, ChevronUp, Info, Leaf, FlaskConical, Box, Zap } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
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
      const response = await fetch(`http://localhost:5024/api/province/catalog/${selectedProvince.toLowerCase()}/stats`);
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
      
      const response = await fetch(`http://localhost:5024/api/province/catalog/${selectedProvince.toLowerCase()}?${params}`);
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
          message: 'Invalid file type. Please upload a CSV or Excel file.'
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
        message: 'Please select a file to upload.'
      });
      return;
    }

    setUploadStatus({ type: 'uploading', message: 'Processing catalog file...' });

    try {
      const result = await uploadProvincialCatalog(selectedFile, selectedProvince);
      
      setUploadStatus({
        type: 'success',
        message: 'Catalog uploaded successfully!',
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
        message: error instanceof Error ? error.message : 'Failed to upload catalog'
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
          message: 'Invalid file type. Please upload a CSV or Excel file.'
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
    <div className="max-w-7xl mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Provincial Product Catalog</h1>
        <p className="text-gray-600">
          View and manage product catalogs from provincial cannabis distributors.
        </p>
      </div>

      {/* Catalog Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center">
            <Package className="h-10 w-10 text-blue-600 mr-3" />
            <div>
              <p className="text-sm font-medium text-gray-600">Total Products</p>
              <p className="text-2xl font-bold text-gray-900">{catalogStats?.total_products || 0}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center">
            <Calendar className="h-10 w-10 text-green-600 mr-3" />
            <div>
              <p className="text-sm font-medium text-gray-600">Last Updated</p>
              <p className="text-lg font-semibold text-gray-900">
                {catalogStats?.last_updated ? formatDate(catalogStats.last_updated) : 'Never'}
              </p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center">
            <Filter className="h-10 w-10 text-purple-600 mr-3" />
            <div>
              <p className="text-sm font-medium text-gray-600">Categories</p>
              <p className="text-2xl font-bold text-gray-900">
                {Object.keys(catalogStats?.categories || {}).length}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Province Selection and Upload Section (Super Admin Only) */}
      {canUpload && (
        <>
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Select Province
                </label>
                <select
                  value={selectedProvince}
                  onChange={(e) => setSelectedProvince(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="ON">Ontario (OCS)</option>
                  <option value="BC" disabled>British Columbia (Coming Soon)</option>
                  <option value="AB" disabled>Alberta (Coming Soon)</option>
                  <option value="QC" disabled>Quebec (Coming Soon)</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Upload New Catalog
                </label>
                <div className="flex items-center space-x-2">
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
                    className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 cursor-pointer"
                  >
                    <Upload className="h-4 w-4 mr-2" />
                    Choose File
                  </label>
                  {selectedFile && (
                    <span className="text-sm text-gray-600">{selectedFile.name}</span>
                  )}
                  <button
                    onClick={handleUpload}
                    disabled={!selectedFile || uploadStatus.type === 'uploading'}
                    className={`px-4 py-2 rounded-md font-medium transition-colors ${
                      !selectedFile || uploadStatus.type === 'uploading'
                        ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                        : 'bg-blue-600 text-white hover:bg-blue-700'
                    }`}
                  >
                    {uploadStatus.type === 'uploading' ? (
                      <>
                        <Loader2 className="inline-block h-4 w-4 mr-2 animate-spin" />
                        Uploading...
                      </>
                    ) : (
                      'Upload'
                    )}
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Upload Status */}
          {uploadStatus.type !== 'idle' && (
            <div className={`rounded-lg p-4 mb-6 ${
              uploadStatus.type === 'error' ? 'bg-red-50 border border-red-200' :
              uploadStatus.type === 'success' ? 'bg-green-50 border border-green-200' :
              'bg-blue-50 border border-blue-200'
            }`}>
              <div className="flex items-start">
                {uploadStatus.type === 'uploading' && (
                  <Loader2 className="h-5 w-5 text-blue-600 mr-3 animate-spin" />
                )}
                {uploadStatus.type === 'success' && (
                  <CheckCircle className="h-5 w-5 text-green-600 mr-3" />
                )}
                {uploadStatus.type === 'error' && (
                  <AlertCircle className="h-5 w-5 text-red-600 mr-3" />
                )}
                
                <div className="flex-1">
                  <p className={`text-sm font-medium ${
                    uploadStatus.type === 'error' ? 'text-red-800' :
                    uploadStatus.type === 'success' ? 'text-green-800' :
                    'text-blue-800'
                  }`}>
                    {uploadStatus.message}
                  </p>
                  
                  {uploadStatus.stats && (
                    <div className="mt-2 text-sm text-gray-600">
                      <p>Total Records: {uploadStatus.stats.totalRecords}</p>
                      <p>Inserted: {uploadStatus.stats.inserted}</p>
                      <p>Updated: {uploadStatus.stats.updated}</p>
                      {uploadStatus.stats.errors > 0 && (
                        <p className="text-red-600">Errors: {uploadStatus.stats.errors}</p>
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
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Viewing Province Catalog
              </label>
              <select
                value={selectedProvince}
                onChange={(e) => setSelectedProvince(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="ON">Ontario (OCS)</option>
                <option value="BC" disabled>British Columbia (Coming Soon)</option>
                <option value="AB" disabled>Alberta (Coming Soon)</option>
                <option value="QC" disabled>Quebec (Coming Soon)</option>
              </select>
            </div>
            <div className="text-sm text-gray-500">
              <Calendar className="inline-block h-4 w-4 mr-1" />
              Last catalog update: {catalogStats?.last_updated ? formatDate(catalogStats.last_updated) : 'Never'}
            </div>
          </div>
        </div>
      )}

      {/* Search and Filter Bar */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search products..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
          
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Categories</option>
            {Object.keys(catalogStats?.categories || {}).map(category => (
              <option key={category} value={category}>
                {category} ({catalogStats?.categories[category]})
              </option>
            ))}
          </select>
          
          <button className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50">
            <Download className="h-4 w-4 inline-block mr-2" />
            Export
          </button>
        </div>
      </div>

      {/* Products Table */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                {/* ID column first (not in Excel but needed for database) */}
                <th className="sticky left-0 z-10 bg-gray-50 px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">ID</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">Slug</th>
                {/* Match Excel column order and names exactly */}
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">Category</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">Sub-Category</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">Sub-Sub-Category</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">Product Name</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">Brand</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">Supplier Name</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">Product Short Description</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">Product Long Description</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">Size</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">Colour</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">Image URL</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">Unit of Measure</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">Stock Status</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">Unit Price</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">Pack Size</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">Minimum THC Content (%)</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">Maximum THC Content (%)</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">THC Content Per Unit</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">THC Content Per Volume</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">Minimum CBD Content (%)</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">Maximum CBD Content (%)</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">CBD Content Per Unit</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">CBD Content Per Volume</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">Dried Flower Cannabis Equivalency</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">Plant Type</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">Terpenes</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">GrowingMethod</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">Number of Items in a Retail Pack</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">GTIN</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">OCS Item Number</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">OCS Variant Number</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">Physical Dimension Width</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">Physical Dimension Height</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">Physical Dimension Depth</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">Physical Dimension Volume</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">Physical Dimension Weight</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">Eaches Per Inner Pack</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">Eaches Per Master Case</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">Inventory Status</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">Storage Criteria</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">Food Allergens</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">Ingredients</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">Street Name</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">Grow Medium</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">Grow Method</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">Grow Region</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">Drying Method</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">Trimming Method</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">Extraction Process</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">Carrier Oil</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">Heating Element Type</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">Battery Type</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">Rechargeable Battery</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">Removable Battery</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">Replacement Parts Available</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">Temperature Control</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">Temperature Display</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">Compatibility</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">THC Min</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">THC Max</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">CBD Min</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">CBD Max</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">Net Weight</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">Ontario Grown</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">Craft</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">Fulfilment Method</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">Delivery Tier</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">Strain Type</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">Rating</th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">Rating Count</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {isLoading ? (
                <tr>
                  <td colSpan={71} className="px-6 py-4 text-center text-gray-500">
                    <Loader2 className="inline-block h-5 w-5 animate-spin mr-2" />
                    Loading catalog...
                  </td>
                </tr>
              ) : catalogProducts && catalogProducts.length > 0 ? (
                catalogProducts.map((product: any) => (
                  <tr key={product.ocs_variant_number || product.id} className="hover:bg-gray-50">
                    {/* Match the column order of headers */}
                    <td className="sticky left-0 z-10 bg-white px-3 py-2 whitespace-nowrap text-xs text-gray-900">{product.id || 'N/A'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900 max-w-xs truncate" title={product.slug || '-'}>{product.slug || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900">{product.category || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900">{product.sub_category || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900">{product.sub_sub_category || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900">{product.product_name || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900">{product.brand || product.brand_name || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900">{product.supplier_name || '-'}</td>
                    <td className="px-3 py-2 max-w-xs truncate text-xs text-gray-900" title={product.product_short_description}>{product.product_short_description || '-'}</td>
                    <td className="px-3 py-2 max-w-xs truncate text-xs text-gray-900" title={product.product_long_description}>{product.product_long_description || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900">{product.size || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900">{product.colour || '-'}</td>
                    <td className="px-3 py-2 max-w-xs truncate text-xs text-gray-900" title={product.image_url}>{product.image_url || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900">{product.unit_of_measure || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900">{product.stock_status || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900">{product.unit_price ?? '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900">{product.pack_size || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900">{product.minimum_thc_content_percent ?? '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900">{product.maximum_thc_content_percent ?? '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900">{product.thc_content_per_unit || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900">{product.thc_content_per_volume || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900">{product.minimum_cbd_content_percent ?? '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900">{product.maximum_cbd_content_percent ?? '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900">{product.cbd_content_per_unit || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900">{product.cbd_content_per_volume || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900">{product.dried_flower_cannabis_equivalency || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900">{product.plant_type || '-'}</td>
                    <td className="px-3 py-2 max-w-xs truncate text-xs text-gray-900" title={product.terpenes}>{product.terpenes || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900">{product.growing_method || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900">{product.number_of_items_in_retail_pack || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900">{product.gtin || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900">{product.ocs_item_number || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900">{product.ocs_variant_number || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900">{product.physical_dimension_width || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900">{product.physical_dimension_height || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900">{product.physical_dimension_depth || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900">{product.physical_dimension_volume || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900">{product.physical_dimension_weight || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900">{product.eaches_per_inner_pack || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900">{product.eaches_per_master_case || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900">{product.inventory_status || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900">{product.storage_criteria || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900">{product.food_allergens || '-'}</td>
                    <td className="px-3 py-2 max-w-xs truncate text-xs text-gray-900" title={product.ingredients}>{product.ingredients || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900">{product.street_name || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900">{product.grow_medium || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900">{product.grow_method || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900">{product.grow_region || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900">{product.drying_method || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900">{product.trimming_method || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900">{product.extraction_process || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900">{product.carrier_oil || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900">{product.heating_element_type || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900">{product.battery_type || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900">{product.rechargeable_battery ?? '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900">{product.removable_battery ?? '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900">{product.replacement_parts_available ?? '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900">{product.temperature_control || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900">{product.temperature_display || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900">{product.compatibility || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900">{product.thc_min || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900">{product.thc_max || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900">{product.cbd_min || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900">{product.cbd_max || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900">{product.net_weight || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900">{product.ontario_grown || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900">{product.craft || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900">{product.fulfilment_method || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900">{product.delivery_tier || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900">{product.strain_type || '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900">{product.rating ?? '-'}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-900">{product.rating_count ?? '-'}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={71} className="px-6 py-4 text-center text-gray-500">
                    No products found in catalog
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        
        {/* Pagination */}
        {catalogProducts && catalogProducts.length > 0 && (
          <div className="bg-gray-50 px-6 py-3 flex items-center justify-between">
            <div className="text-sm text-gray-700">
              Showing page {currentPage} of results
            </div>
            <div className="flex space-x-2">
              <button
                onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                disabled={currentPage === 1}
                className="px-3 py-1 border border-gray-300 rounded-md text-sm text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Previous
              </button>
              <button
                onClick={() => setCurrentPage(currentPage + 1)}
                disabled={catalogProducts.length < productsPerPage}
                className="px-3 py-1 border border-gray-300 rounded-md text-sm text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Instructions (Super Admin Only) */}
      {canUpload && (
        <div className="mt-8 bg-blue-50 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-blue-900 mb-3">Upload Instructions</h3>
          <ul className="space-y-2 text-sm text-blue-800">
            <li className="flex items-start">
              <span className="block w-1.5 h-1.5 rounded-full bg-blue-600 mt-1.5 mr-2 flex-shrink-0"></span>
              <span>The OCS catalog file should contain all required columns as per the OCS specification.</span>
            </li>
            <li className="flex items-start">
              <span className="block w-1.5 h-1.5 rounded-full bg-blue-600 mt-1.5 mr-2 flex-shrink-0"></span>
              <span>Products are matched and updated using the OCS Variant Number as the unique key.</span>
            </li>
            <li className="flex items-start">
              <span className="block w-1.5 h-1.5 rounded-full bg-blue-600 mt-1.5 mr-2 flex-shrink-0"></span>
              <span>New products will be inserted, existing products will be updated with the latest information.</span>
            </li>
            <li className="flex items-start">
              <span className="block w-1.5 h-1.5 rounded-full bg-blue-600 mt-1.5 mr-2 flex-shrink-0"></span>
              <span>Rating and rating count fields will be preserved during updates.</span>
            </li>
          </ul>
        </div>
      )}
    </div>
  );
};

export default ProvincialCatalogUpload;