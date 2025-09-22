import React, { useState, useRef, useEffect, useMemo } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import { Upload, AlertCircle, CheckCircle, FileText, Loader2, Search, Filter, Download } from 'lucide-react';
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
    error_details?: string[];
  };
}

interface CatalogProduct {
  // System fields
  id: string;
  slug: string;
  created_at: string;
  updated_at: string;
  rating: number | null;
  rating_count: number;
  
  // OCS Standard fields (69 columns from Excel)
  category: string | null;
  sub_category: string | null;
  sub_sub_category: string | null;
  product_name: string;
  brand: string | null;
  supplier_name: string | null;
  product_short_description: string | null;
  product_long_description: string | null;
  size: string | null;
  colour: string | null;
  image_url: string | null;
  unit_of_measure: string | null;
  stock_status: string | null;
  unit_price: number | null;
  pack_size: number | null;
  minimum_thc_content_percent: number | null;
  maximum_thc_content_percent: number | null;
  thc_content_per_unit: number | null;
  thc_content_per_volume: number | null;
  minimum_cbd_content_percent: number | null;
  maximum_cbd_content_percent: number | null;
  cbd_content_per_unit: number | null;
  cbd_content_per_volume: number | null;
  dried_flower_cannabis_equivalency: number | null;
  plant_type: string | null;
  terpenes: string | null;
  growing_method: string | null;
  number_of_items_in_retail_pack: number | null;
  gtin: number | null;
  ocs_item_number: number | null;
  ocs_variant_number: string | null;
  physical_dimension_width: number | null;
  physical_dimension_height: number | null;
  physical_dimension_depth: number | null;
  physical_dimension_volume: number | null;
  physical_dimension_weight: number | null;
  eaches_per_inner_pack: number | null;
  eaches_per_master_case: number | null;
  inventory_status: string | null;
  storage_criteria: string | null;
  food_allergens: string | null;
  ingredients: string | null;
  street_name: string | null;
  grow_medium: string | null;
  grow_method: string | null;
  grow_region: string | null;
  drying_method: string | null;
  trimming_method: string | null;
  extraction_process: string | null;
  carrier_oil: string | null;
  heating_element_type: string | null;
  battery_type: string | null;
  rechargeable_battery: boolean | null;
  removable_battery: boolean | null;
  replacement_parts_available: boolean | null;
  temperature_control: string | null;
  temperature_display: string | null;
  compatibility: string | null;
  strain_type: string | null;
  net_weight: number | null;
  ontario_grown: string | null;
  craft: string | null;
  fulfilment_method: string | null;
  delivery_tier: string | null;
}

// Column definitions matching Excel format exactly
const columns = [
  { key: 'slug', header: 'Slug', width: 200 },
  { key: 'category', header: 'Category', width: 120 },
  { key: 'sub_category', header: 'Sub-Category', width: 150 },
  { key: 'sub_sub_category', header: 'Sub-Sub-Category', width: 150 },
  { key: 'product_name', header: 'Product Name', width: 200 },
  { key: 'brand', header: 'Brand', width: 120 },
  { key: 'supplier_name', header: 'Supplier Name', width: 150 },
  { key: 'product_short_description', header: 'Product Short Description', width: 200 },
  { key: 'product_long_description', header: 'Product Long Description', width: 250 },
  { key: 'size', header: 'Size', width: 80 },
  { key: 'colour', header: 'Colour', width: 100 },
  { key: 'image_url', header: 'Image URL', width: 200 },
  { key: 'unit_of_measure', header: 'Unit of Measure', width: 120 },
  { key: 'stock_status', header: 'Stock Status', width: 100 },
  { key: 'unit_price', header: 'Unit Price', width: 100 },
  { key: 'pack_size', header: 'Pack Size', width: 100 },
  { key: 'minimum_thc_content_percent', header: 'Minimum THC Content (%)', width: 150 },
  { key: 'maximum_thc_content_percent', header: 'Maximum THC Content (%)', width: 150 },
  { key: 'thc_content_per_unit', header: 'THC Content Per Unit', width: 150 },
  { key: 'thc_content_per_volume', header: 'THC Content Per Volume', width: 150 },
  { key: 'minimum_cbd_content_percent', header: 'Minimum CBD Content (%)', width: 150 },
  { key: 'maximum_cbd_content_percent', header: 'Maximum CBD Content (%)', width: 150 },
  { key: 'cbd_content_per_unit', header: 'CBD Content Per Unit', width: 150 },
  { key: 'cbd_content_per_volume', header: 'CBD Content Per Volume', width: 150 },
  { key: 'dried_flower_cannabis_equivalency', header: 'Dried Flower Cannabis Equivalency', width: 200 },
  { key: 'plant_type', header: 'Plant Type', width: 100 },
  { key: 'terpenes', header: 'Terpenes', width: 150 },
  { key: 'growing_method', header: 'GrowingMethod', width: 120 },
  { key: 'number_of_items_in_retail_pack', header: 'Number of Items in a Retail Pack', width: 180 },
  { key: 'gtin', header: 'GTIN', width: 120 },
  { key: 'ocs_item_number', header: 'OCS Item Number', width: 140 },
  { key: 'ocs_variant_number', header: 'OCS Variant Number', width: 150 },
  { key: 'physical_dimension_width', header: 'Physical Dimension Width', width: 160 },
  { key: 'physical_dimension_height', header: 'Physical Dimension Height', width: 160 },
  { key: 'physical_dimension_depth', header: 'Physical Dimension Depth', width: 160 },
  { key: 'physical_dimension_volume', header: 'Physical Dimension Volume', width: 170 },
  { key: 'physical_dimension_weight', header: 'Physical Dimension Weight', width: 170 },
  { key: 'eaches_per_inner_pack', header: 'Eaches Per Inner Pack', width: 150 },
  { key: 'eaches_per_master_case', header: 'Eaches Per Master Case', width: 160 },
  { key: 'inventory_status', header: 'Inventory Status', width: 120 },
  { key: 'storage_criteria', header: 'Storage Criteria', width: 120 },
  { key: 'food_allergens', header: 'Food Allergens', width: 120 },
  { key: 'ingredients', header: 'Ingredients', width: 150 },
  { key: 'street_name', header: 'Street Name', width: 120 },
  { key: 'grow_medium', header: 'Grow Medium', width: 120 },
  { key: 'grow_method', header: 'Grow Method', width: 120 },
  { key: 'grow_region', header: 'Grow Region', width: 120 },
  { key: 'drying_method', header: 'Drying Method', width: 120 },
  { key: 'trimming_method', header: 'Trimming Method', width: 130 },
  { key: 'extraction_process', header: 'Extraction Process', width: 140 },
  { key: 'carrier_oil', header: 'Carrier Oil', width: 100 },
  { key: 'heating_element_type', header: 'Heating Element Type', width: 150 },
  { key: 'battery_type', header: 'Battery Type', width: 120 },
  { key: 'rechargeable_battery', header: 'Rechargeable Battery', width: 140 },
  { key: 'removable_battery', header: 'Removable Battery', width: 130 },
  { key: 'replacement_parts_available', header: 'Replacement Parts Available', width: 180 },
  { key: 'temperature_control', header: 'Temperature Control', width: 140 },
  { key: 'temperature_display', header: 'Temperature Display', width: 140 },
  { key: 'compatibility', header: 'Compatibility', width: 120 },
  { key: 'strain_type', header: 'Strain Type', width: 100 },
  { key: 'net_weight', header: 'Net Weight', width: 100 },
  { key: 'ontario_grown', header: 'Ontario Grown', width: 120 },
  { key: 'craft', header: 'Craft', width: 80 },
  { key: 'fulfilment_method', header: 'Fulfilment Method', width: 130 },
  { key: 'delivery_tier', header: 'Delivery Tier', width: 120 },
  { key: 'rating', header: 'Rating', width: 80 },
  { key: 'rating_count', header: 'Rating Count', width: 100 },
];

const ProvincialCatalogVirtual: React.FC = () => {
  const { isSuperAdmin } = useAuth();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedProvince, setSelectedProvince] = useState<string>('ON');
  const [uploadStatus, setUploadStatus] = useState<UploadStatus>({ type: 'idle' });
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  
  const parentRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const topScrollRef = useRef<HTMLDivElement>(null);
  const topScrollContentRef = useRef<HTMLDivElement>(null);

  // Check if user can upload
  const canUpload = isSuperAdmin();

  // Fetch ALL catalog products for virtual scrolling
  const { data: allProducts = [], isLoading, refetch: refetchProducts } = useQuery<CatalogProduct[]>({
    queryKey: ['catalog-products-all', selectedProvince, searchTerm, selectedCategory],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (searchTerm) params.append('search', searchTerm);
      if (selectedCategory) params.append('category', selectedCategory);
      
      const response = await fetch(getApiEndpoint(`/province/catalog/${selectedProvince.toLowerCase()}/all?${params}`));
      if (!response.ok) {
        return [];
      }
      return response.json();
    },
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
  });

  // Filter products client-side
  const filteredProducts = useMemo(() => {
    return allProducts;
  }, [allProducts]);

  // Virtual row virtualizer
  const rowVirtualizer = useVirtualizer({
    count: filteredProducts.length,
    getScrollElement: () => scrollContainerRef.current,
    estimateSize: () => 35, // Estimated row height
    overscan: 10, // Render 10 extra rows outside viewport
  });

  // Virtual column virtualizer for horizontal scrolling
  const columnVirtualizer = useVirtualizer({
    horizontal: true,
    count: columns.length,
    getScrollElement: () => scrollContainerRef.current,
    estimateSize: (index) => columns[index].width,
    overscan: 5,
  });

  // Synchronize scroll positions between top and main scrollbars
  useEffect(() => {
    const topScroll = topScrollRef.current;
    const mainScroll = scrollContainerRef.current;
    
    if (!topScroll || !mainScroll) return;

    const handleTopScroll = () => {
      if (mainScroll) {
        mainScroll.scrollLeft = topScroll.scrollLeft;
      }
    };

    const handleMainScroll = () => {
      if (topScroll) {
        topScroll.scrollLeft = mainScroll.scrollLeft;
      }
    };

    topScroll.addEventListener('scroll', handleTopScroll);
    mainScroll.addEventListener('scroll', handleMainScroll);

    return () => {
      topScroll.removeEventListener('scroll', handleTopScroll);
      mainScroll.removeEventListener('scroll', handleMainScroll);
    };
  }, []);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setUploadStatus({ type: 'idle' });
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setUploadStatus({ type: 'uploading', message: 'Processing file...' });

    try {
      const result = await uploadProvincialCatalog(selectedFile, selectedProvince);
      
      setUploadStatus({
        type: 'success',
        message: result.message || 'Upload successful',
        stats: result.stats
      });

      // Refresh the products list
      refetchProducts();
      
      // Clear file selection
      setSelectedFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (error: any) {
      setUploadStatus({
        type: 'error',
        message: error.message || 'Upload failed'
      });
    }
  };

  return (
    <div className="max-w-full mx-auto space-y-6">
      {/* Header */}
      <div className="bg-white  rounded-lg p-6">
        <h1 className="text-2xl font-bold text-gray-900">Provincial Product Catalog (Virtual Scroll)</h1>
        <p className="mt-2 text-gray-600">
          Manage and upload provincial cannabis product catalogs
        </p>
      </div>

      {/* Upload Section */}
      {canUpload && (
        <div className="bg-white  rounded-lg p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Upload Catalog</h2>
          
          <div className="space-y-4">
            {/* Province selector */}
            <div className="max-w-xs">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Province
              </label>
              <select
                value={selectedProvince}
                onChange={(e) => setSelectedProvince(e.target.value)}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                disabled={uploadStatus.type === 'uploading'}
              >
                <option value="ON">Ontario (OCS)</option>
              </select>
            </div>

            {/* File upload */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Upload File
              </label>
              <div className="flex items-center space-x-4">
                <input
                  ref={fileInputRef}
                  type="file"
                  onChange={handleFileSelect}
                  accept=".csv,.xlsx,.xls"
                  className="hidden"
                  disabled={uploadStatus.type === 'uploading'}
                />
                <button
                  onClick={() => fileInputRef.current?.click()}
                  disabled={uploadStatus.type === 'uploading'}
                  className="px-4 py-2 border border-gray-200 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Upload className="inline-block w-4 h-4 mr-2" />
                  Choose File
                </button>
                {selectedFile && (
                  <span className="text-sm text-gray-600">
                    <FileText className="inline-block w-4 h-4 mr-1" />
                    {selectedFile.name}
                  </span>
                )}
              </div>
            </div>

            {/* Upload button */}
            <button
              onClick={handleUpload}
              disabled={!selectedFile || uploadStatus.type === 'uploading'}
              className="px-6 py-2 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {uploadStatus.type === 'uploading' ? (
                <>
                  <Loader2 className="inline-block w-4 h-4 mr-2 animate-spin" />
                  Uploading...
                </>
              ) : (
                'Upload Catalog'
              )}
            </button>

            {/* Status messages */}
            {uploadStatus.type === 'success' && (
              <div className="p-6 bg-primary-50 border border-green-200 rounded-lg">
                <div className="flex">
                  <CheckCircle className="h-5 w-5 text-green-400" />
                  <div className="ml-3">
                    <p className="text-sm font-medium text-primary-800">
                      {uploadStatus.message}
                    </p>
                    {uploadStatus.stats && (
                      <div className="mt-2 text-sm text-primary-700">
                        <p>Total records: {uploadStatus.stats.totalRecords}</p>
                        <p>Inserted: {uploadStatus.stats.inserted}</p>
                        <p>Updated: {uploadStatus.stats.updated}</p>
                        {uploadStatus.stats.errors > 0 && (
                          <p className="text-danger-600">Errors: {uploadStatus.stats.errors}</p>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {uploadStatus.type === 'error' && (
              <div className="p-6 bg-danger-50 border border-red-200 rounded-lg">
                <div className="flex">
                  <AlertCircle className="h-5 w-5 text-red-400" />
                  <div className="ml-3">
                    <p className="text-sm font-medium text-danger-800">
                      {uploadStatus.message}
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Search and Filter */}
      <div className="bg-white  rounded-lg p-6">
        <div className="flex gap-6">
          <div className="flex-1 max-w-md">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search products..."
                className="w-full pl-10 pr-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
          </div>
          <div>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-primary-500 focus:border-primary-500 min-w-[150px]"
            >
              <option value="">All Categories</option>
              <option value="Flower">Flower</option>
              <option value="Pre-Rolls">Pre-Rolls</option>
              <option value="Vapes">Vapes</option>
              <option value="Edibles">Edibles</option>
              <option value="Beverages">Beverages</option>
              <option value="Concentrates">Concentrates</option>
              <option value="Topicals">Topicals</option>
              <option value="Seeds">Seeds</option>
              <option value="Accessories">Accessories</option>
            </select>
          </div>
        </div>
      </div>

      {/* Virtual Scrolling Table */}
      <div className="bg-white  rounded-lg p-6">
        <div className="mb-4 flex justify-between items-center">
          <div>
            <h2 className="text-lg font-medium text-gray-900">
              Catalog Products ({filteredProducts.length} items)
            </h2>
            <p className="text-sm text-gray-500 mt-1">
              Scroll horizontally to view all columns →
            </p>
          </div>
          <button
            className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 border border-gray-200 rounded-lg"
            onClick={() => {
              // Export functionality
              const csvContent = [
                columns.map(c => c.header).join(','),
                ...filteredProducts.map(product => 
                  columns.map(c => {
                    const value = product[c.key as keyof CatalogProduct];
                    return value === null || value === undefined ? '' : String(value);
                  }).join(',')
                )
              ].join('\n');
              
              const blob = new Blob([csvContent], { type: 'text/csv' });
              const url = URL.createObjectURL(blob);
              const a = document.createElement('a');
              a.href = url;
              a.download = `catalog-${selectedProvince}-${new Date().toISOString().split('T')[0]}.csv`;
              a.click();
            }}
          >
            <Download className="inline-block w-4 h-4 mr-2" />
            Export CSV
          </button>
        </div>

        {isLoading ? (
          <div className="flex justify-center items-center h-64">
            <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
          </div>
        ) : filteredProducts.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            No products found. Upload a catalog to get started.
          </div>
        ) : (
          <div ref={parentRef} className="border border-gray-200 rounded-lg">
            {/* Top horizontal scrollbar */}
            <div 
              ref={topScrollRef}
              className="overflow-x-auto overflow-y-hidden border-b border-gray-200 bg-gray-50"
              style={{ height: '20px' }}
            >
              <div 
                ref={topScrollContentRef}
                style={{ 
                  width: `${columnVirtualizer.getTotalSize()}px`,
                  height: '1px'
                }}
              />
            </div>
            
            {/* Main scrollable table container */}
            <div
              ref={scrollContainerRef}
              className="overflow-auto"
              style={{ height: '600px', width: '100%' }}
            >
              <div
                style={{
                  height: `${rowVirtualizer.getTotalSize() + 35}px`, // Add header height
                  width: `${columnVirtualizer.getTotalSize()}px`,
                  position: 'relative',
                  minWidth: '100%'
                }}
              >
                {/* Header */}
                <div
                  className="sticky top-0 z-10 bg-gray-50 border-b border-gray-200"
                  style={{ width: `${columnVirtualizer.getTotalSize()}px` }}
                >
                  {columnVirtualizer.getVirtualItems().map((virtualColumn) => {
                    const column = columns[virtualColumn.index];
                    return (
                      <div
                        key={virtualColumn.key}
                        className="absolute top-0 px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200"
                        style={{
                          left: 0,
                          width: `${virtualColumn.size}px`,
                          transform: `translateX(${virtualColumn.start}px)`,
                        }}
                      >
                        {column.header}
                      </div>
                    );
                  })}
                </div>

                {/* Rows */}
                {rowVirtualizer.getVirtualItems().map((virtualRow) => {
                  const product = filteredProducts[virtualRow.index];
                  return (
                    <div
                      key={virtualRow.key}
                      className="absolute top-0 left-0 w-full flex hover:bg-gray-50"
                      style={{
                        height: `${virtualRow.size}px`,
                        transform: `translateY(${virtualRow.start + 35}px)`, // Add header height
                      }}
                    >
                      {columnVirtualizer.getVirtualItems().map((virtualColumn) => {
                        const column = columns[virtualColumn.index];
                        const value = product[column.key as keyof CatalogProduct];
                        return (
                          <div
                            key={virtualColumn.key}
                            className="absolute top-0 px-3 py-2 text-xs text-gray-900 border-r border-b border-gray-200 truncate"
                            style={{
                              left: 0,
                              width: `${virtualColumn.size}px`,
                              transform: `translateX(${virtualColumn.start}px)`,
                            }}
                            title={String(value ?? '-')}
                          >
                            {value === null || value === undefined ? '-' : String(value)}
                          </div>
                        );
                      })}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ProvincialCatalogVirtual;