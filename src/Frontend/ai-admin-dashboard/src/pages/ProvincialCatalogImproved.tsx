import React, { useState, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Upload, AlertCircle, CheckCircle, Loader2, Search, Download,
  ChevronDown, ChevronUp, Package, Calendar, Tag, Leaf,
  FlaskConical, Box, Zap, Truck, Info, ImageIcon
} from 'lucide-react';
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
  id: string;
  slug: string;
  ocs_variant_number: string;
  product_name: string;
  brand: string;
  supplier_name: string;
  category: string;
  sub_category: string;
  sub_sub_category: string;
  image_url: string | null;
  unit_price: number | null;
  size: string | null;
  plant_type: string | null;
  strain_type: string | null;
  thc_content_per_unit: number | null;
  cbd_content_per_unit: number | null;
  minimum_thc_content_percent: number | null;
  maximum_thc_content_percent: number | null;
  minimum_cbd_content_percent: number | null;
  maximum_cbd_content_percent: number | null;
  product_short_description: string | null;
  product_long_description: string | null;
  terpenes: string | null;
  stock_status: string | null;
  inventory_status: string | null;
  [key: string]: any; // Allow for all other fields
}

type TabType = 'basic' | 'cannabinoids' | 'physical' | 'cultivation' | 'device' | 'logistics';

const ProvincialCatalogImproved: React.FC = () => {
  const { t } = useTranslation(['catalog', 'common']);
  const { isSuperAdmin } = useAuth();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedProvince, setSelectedProvince] = useState<string>('ON');
  const [uploadStatus, setUploadStatus] = useState<UploadStatus>({ type: 'idle' });
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [expandedProductId, setExpandedProductId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabType>('basic');

  const canUpload = isSuperAdmin();

  // Fetch all products
  const { data: allProducts = [], isLoading, refetch: refetchProducts } = useQuery<CatalogProduct[]>({
    queryKey: ['catalog-products-all', selectedProvince, searchTerm, selectedCategory],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (searchTerm) params.append('search', searchTerm);
      if (selectedCategory) params.append('category', selectedCategory);

      const response = await fetch(getApiEndpoint(`/province/catalog/${selectedProvince.toLowerCase()}/all?${params}`));
      if (!response.ok) return [];
      return response.json();
    },
    staleTime: 5 * 60 * 1000,
  });

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setUploadStatus({ type: 'idle' });
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    setUploadStatus({ type: 'uploading', message: t('catalog:upload.processingFileShort') });

    try {
      const result = await uploadProvincialCatalog(selectedFile, selectedProvince);
      setUploadStatus({
        type: 'success',
        message: result.message || t('catalog:upload.uploadSuccessShort'),
        stats: result.stats
      });
      refetchProducts();
      setSelectedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
    } catch (error: any) {
      setUploadStatus({
        type: 'error',
        message: error.message || t('catalog:upload.uploadFailedShort')
      });
    }
  };

  const toggleExpand = (productId: string) => {
    setExpandedProductId(expandedProductId === productId ? null : productId);
    setActiveTab('basic'); // Reset to basic tab when expanding
  };

  const exportToCSV = () => {
    const headers = ['ID', 'Product Name', 'Brand', 'Category', 'Price', 'THC %', 'CBD %', 'OCS Variant'];
    const rows = allProducts.map(p => [
      p.id,
      p.product_name,
      p.brand,
      p.category,
      p.unit_price,
      p.thc_content_per_unit,
      p.cbd_content_per_unit,
      p.ocs_variant_number
    ]);

    const csvContent = [headers, ...rows].map(row => row.join(',')).join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `catalog-${selectedProvince}-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
  };

  const renderDetailTabs = (product: CatalogProduct) => {
    const tabs = [
      { id: 'basic', label: 'Basic Info', icon: Info },
      { id: 'cannabinoids', label: 'Cannabinoids', icon: FlaskConical },
      { id: 'physical', label: 'Physical', icon: Box },
      { id: 'cultivation', label: 'Cultivation', icon: Leaf },
      { id: 'device', label: 'Device Specs', icon: Zap },
      { id: 'logistics', label: 'Logistics', icon: Truck },
    ] as const;

    return (
      <div className="border-t border-gray-200 bg-gray-50 p-6">
        {/* Tab Navigation */}
        <div className="flex border-b border-gray-200 mb-4 overflow-x-auto">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as TabType)}
                className={`flex items-center px-4 py-2 text-sm font-medium border-b-2 whitespace-nowrap ${
                  activeTab === tab.id
                    ? 'border-primary-600 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <Icon className="w-4 h-4 mr-2" />
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Tab Content */}
        <div className="space-y-4">
          {activeTab === 'basic' && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <DetailField label="Product Name" value={product.product_name} />
              <DetailField label="Brand" value={product.brand} />
              <DetailField label="Supplier" value={product.supplier_name} />
              <DetailField label="Category" value={product.category} />
              <DetailField label="Sub-Category" value={product.sub_category} />
              <DetailField label="Sub-Sub-Category" value={product.sub_sub_category} />
              <DetailField label="Size" value={product.size} />
              <DetailField label="Colour" value={product.colour} />
              <DetailField label="Unit of Measure" value={product.unit_of_measure} />
              <DetailField label="Unit Price" value={product.unit_price ? `$${product.unit_price}` : null} />
              <DetailField label="Pack Size" value={product.pack_size} />
              <DetailField label="Street Name" value={product.street_name} />
              <DetailField label="OCS Item Number" value={product.ocs_item_number} />
              <DetailField label="OCS Variant Number" value={product.ocs_variant_number} />
              <DetailField label="GTIN" value={product.gtin} />
              <DetailField label="Stock Status" value={product.stock_status} />
              <DetailField label="Inventory Status" value={product.inventory_status} />
              <div className="col-span-full">
                <DetailField label="Short Description" value={product.product_short_description} />
              </div>
              <div className="col-span-full">
                <DetailField label="Long Description" value={product.product_long_description} />
              </div>
            </div>
          )}

          {activeTab === 'cannabinoids' && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <DetailField label="THC Content Per Unit" value={product.thc_content_per_unit ? `${product.thc_content_per_unit} mg` : null} />
              <DetailField label="CBD Content Per Unit" value={product.cbd_content_per_unit ? `${product.cbd_content_per_unit} mg` : null} />
              <DetailField label="Min THC %" value={product.minimum_thc_content_percent ? `${product.minimum_thc_content_percent}%` : null} />
              <DetailField label="Max THC %" value={product.maximum_thc_content_percent ? `${product.maximum_thc_content_percent}%` : null} />
              <DetailField label="Min CBD %" value={product.minimum_cbd_content_percent ? `${product.minimum_cbd_content_percent}%` : null} />
              <DetailField label="Max CBD %" value={product.maximum_cbd_content_percent ? `${product.maximum_cbd_content_percent}%` : null} />
              <DetailField label="THC Per Volume" value={product.thc_content_per_volume} />
              <DetailField label="CBD Per Volume" value={product.cbd_content_per_volume} />
              <DetailField label="THC Min" value={product.thc_min} />
              <DetailField label="THC Max" value={product.thc_max} />
              <DetailField label="CBD Min" value={product.cbd_min} />
              <DetailField label="CBD Max" value={product.cbd_max} />
              <DetailField label="Dried Flower Equivalency" value={product.dried_flower_cannabis_equivalency} />
              <div className="col-span-full">
                <DetailField label="Terpenes" value={product.terpenes} />
              </div>
            </div>
          )}

          {activeTab === 'physical' && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <DetailField label="Width" value={product.physical_dimension_width ? `${product.physical_dimension_width} cm` : null} />
              <DetailField label="Height" value={product.physical_dimension_height ? `${product.physical_dimension_height} cm` : null} />
              <DetailField label="Depth" value={product.physical_dimension_depth ? `${product.physical_dimension_depth} cm` : null} />
              <DetailField label="Volume" value={product.physical_dimension_volume ? `${product.physical_dimension_volume} mL` : null} />
              <DetailField label="Weight" value={product.physical_dimension_weight ? `${product.physical_dimension_weight} g` : null} />
              <DetailField label="Net Weight" value={product.net_weight ? `${product.net_weight} g` : null} />
              <DetailField label="Items in Retail Pack" value={product.number_of_items_in_retail_pack} />
              <DetailField label="Eaches Per Inner Pack" value={product.eaches_per_inner_pack} />
              <DetailField label="Eaches Per Master Case" value={product.eaches_per_master_case} />
              <DetailField label="Storage Criteria" value={product.storage_criteria} />
              <div className="col-span-full">
                <DetailField label="Ingredients" value={product.ingredients} />
              </div>
              <div className="col-span-full">
                <DetailField label="Food Allergens" value={product.food_allergens} />
              </div>
            </div>
          )}

          {activeTab === 'cultivation' && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <DetailField label="Plant Type" value={product.plant_type} />
              <DetailField label="Strain Type" value={product.strain_type} />
              <DetailField label="Growing Method" value={product.growing_method} />
              <DetailField label="Grow Medium" value={product.grow_medium} />
              <DetailField label="Grow Method" value={product.grow_method} />
              <DetailField label="Grow Region" value={product.grow_region} />
              <DetailField label="Drying Method" value={product.drying_method} />
              <DetailField label="Trimming Method" value={product.trimming_method} />
              <DetailField label="Extraction Process" value={product.extraction_process} />
              <DetailField label="Carrier Oil" value={product.carrier_oil} />
              <DetailField label="Ontario Grown" value={product.ontario_grown} />
              <DetailField label="Craft" value={product.craft} />
            </div>
          )}

          {activeTab === 'device' && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <DetailField label="Heating Element Type" value={product.heating_element_type} />
              <DetailField label="Battery Type" value={product.battery_type} />
              <DetailField label="Rechargeable Battery" value={product.rechargeable_battery !== null ? (product.rechargeable_battery ? 'Yes' : 'No') : null} />
              <DetailField label="Removable Battery" value={product.removable_battery !== null ? (product.removable_battery ? 'Yes' : 'No') : null} />
              <DetailField label="Replacement Parts Available" value={product.replacement_parts_available !== null ? (product.replacement_parts_available ? 'Yes' : 'No') : null} />
              <DetailField label="Temperature Control" value={product.temperature_control} />
              <DetailField label="Temperature Display" value={product.temperature_display} />
              <DetailField label="Compatibility" value={product.compatibility} />
            </div>
          )}

          {activeTab === 'logistics' && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <DetailField label="Fulfilment Method" value={product.fulfilment_method} />
              <DetailField label="Delivery Tier" value={product.delivery_tier} />
              <DetailField label="Inventory Status" value={product.inventory_status} />
              <DetailField label="Stock Status" value={product.stock_status} />
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg p-6">
        <h1 className="text-2xl font-bold text-gray-900">{t('catalog:titles.mainVirtual')}</h1>
        <p className="mt-2 text-gray-600">{t('catalog:descriptions.mainVirtual')}</p>
      </div>

      {/* Upload Section */}
      {canUpload && (
        <div className="bg-white rounded-lg p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">{t('catalog:titles.uploadSection')}</h2>

          <div className="space-y-4">
            <div className="max-w-xs">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {t('catalog:descriptions.selectProvince')}
              </label>
              <select
                value={selectedProvince}
                onChange={(e) => setSelectedProvince(e.target.value)}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                disabled={uploadStatus.type === 'uploading'}
              >
                <option value="ON">{t('catalog:provinces.ontario')}</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {t('catalog:upload.uploadFile')}
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
                  {t('catalog:upload.chooseFile')}
                </button>
                {selectedFile && (
                  <span className="text-sm text-gray-600">{selectedFile.name}</span>
                )}
              </div>
            </div>

            <button
              onClick={handleUpload}
              disabled={!selectedFile || uploadStatus.type === 'uploading'}
              className="px-6 py-2 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {uploadStatus.type === 'uploading' ? (
                <>
                  <Loader2 className="inline-block w-4 h-4 mr-2 animate-spin" />
                  {t('catalog:upload.uploading')}
                </>
              ) : (
                t('catalog:upload.uploadCatalog')
              )}
            </button>

            {/* Status messages */}
            {uploadStatus.type === 'success' && (
              <div className="p-6 bg-primary-50 border border-green-200 rounded-lg">
                <div className="flex">
                  <CheckCircle className="h-5 w-5 text-green-400" />
                  <div className="ml-3">
                    <p className="text-sm font-medium text-primary-800">{uploadStatus.message}</p>
                    {uploadStatus.stats && (
                      <div className="mt-2 text-sm text-primary-700">
                        <p>{t('catalog:stats.totalRecordsLabel')}: {uploadStatus.stats.totalRecords}</p>
                        <p>{t('catalog:stats.inserted')}: {uploadStatus.stats.inserted}</p>
                        <p>{t('catalog:stats.updated')}: {uploadStatus.stats.updated}</p>
                        {uploadStatus.stats.errors > 0 && (
                          <p className="text-danger-600">{t('catalog:stats.errors')}: {uploadStatus.stats.errors}</p>
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
                    <p className="text-sm font-medium text-danger-800">{uploadStatus.message}</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Search and Filter */}
      <div className="bg-white rounded-lg p-6">
        <div className="flex gap-6">
          <div className="flex-1 max-w-md">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder={t('catalog:search.placeholder')}
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
              <option value="">{t('catalog:search.allCategories')}</option>
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
          <button
            onClick={exportToCSV}
            className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 border border-gray-200 rounded-lg"
          >
            <Download className="inline-block w-4 h-4 mr-2" />
            {t('catalog:buttons.exportCsv')}
          </button>
        </div>
      </div>

      {/* Product Cards */}
      <div className="bg-white rounded-lg p-6">
        <div className="mb-4">
          <h2 className="text-lg font-medium text-gray-900">
            {t('catalog:titles.catalogProducts')} ({allProducts.length} {t('common:items')})
          </h2>
        </div>

        {isLoading ? (
          <div className="flex justify-center items-center h-64">
            <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
          </div>
        ) : allProducts.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            {t('catalog:table.noProductsUpload')}
          </div>
        ) : (
          <div className="space-y-4">
            {allProducts.map((product) => (
              <div key={product.id} className="border border-gray-200 rounded-lg overflow-hidden hover:shadow-md transition-shadow">
                {/* Product Card Summary */}
                <div className="p-4 cursor-pointer" onClick={() => toggleExpand(product.id)}>
                  <div className="flex gap-4">
                    {/* Product Image */}
                    <div className="flex-shrink-0 w-24 h-24 bg-gray-100 rounded-lg overflow-hidden">
                      {product.image_url ? (
                        <img
                          src={product.image_url}
                          alt={product.product_name}
                          className="w-full h-full object-cover"
                          onError={(e) => {
                            e.currentTarget.src = '';
                            e.currentTarget.style.display = 'none';
                            e.currentTarget.parentElement!.innerHTML = '<div class="w-full h-full flex items-center justify-center"><svg class="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg></div>';
                          }}
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center">
                          <ImageIcon className="w-8 h-8 text-gray-400" />
                        </div>
                      )}
                    </div>

                    {/* Product Info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h3 className="text-lg font-semibold text-gray-900 truncate">{product.product_name}</h3>
                          <p className="text-sm text-gray-600">{product.brand} • {product.supplier_name}</p>
                        </div>
                        <div className="ml-4 text-right">
                          <p className="text-lg font-bold text-primary-600">
                            {product.unit_price != null && !isNaN(Number(product.unit_price))
                              ? `$${Number(product.unit_price).toFixed(2)}`
                              : 'N/A'}
                          </p>
                          {product.size && (
                            <p className="text-sm text-gray-500">{product.size}</p>
                          )}
                        </div>
                      </div>

                      <div className="mt-2 flex flex-wrap gap-2">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                          <Tag className="w-3 h-3 mr-1" />
                          {product.category}
                        </span>
                        {product.sub_category && (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                            {product.sub_category}
                          </span>
                        )}
                        {product.plant_type && (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                            <Leaf className="w-3 h-3 mr-1" />
                            {product.plant_type}
                          </span>
                        )}
                        {product.thc_content_per_unit && (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800">
                            <FlaskConical className="w-3 h-3 mr-1" />
                            THC: {product.thc_content_per_unit}mg
                          </span>
                        )}
                        {product.cbd_content_per_unit && (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-teal-100 text-teal-800">
                            <FlaskConical className="w-3 h-3 mr-1" />
                            CBD: {product.cbd_content_per_unit}mg
                          </span>
                        )}
                      </div>

                      {product.product_short_description && (
                        <p className="mt-2 text-sm text-gray-600 line-clamp-2">{product.product_short_description}</p>
                      )}
                    </div>

                    {/* Expand Icon */}
                    <div className="flex-shrink-0 ml-2">
                      {expandedProductId === product.id ? (
                        <ChevronUp className="w-5 h-5 text-gray-400" />
                      ) : (
                        <ChevronDown className="w-5 h-5 text-gray-400" />
                      )}
                    </div>
                  </div>
                </div>

                {/* Expanded Details with Tabs */}
                {expandedProductId === product.id && renderDetailTabs(product)}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// Helper component for detail fields
const DetailField: React.FC<{ label: string; value: any }> = ({ label, value }) => (
  <div className="space-y-1">
    <div className="text-xs font-medium text-gray-500">{label}</div>
    <div className="text-sm text-gray-900">{value !== null && value !== undefined && value !== '' ? value : '-'}</div>
  </div>
);

export default ProvincialCatalogImproved;
