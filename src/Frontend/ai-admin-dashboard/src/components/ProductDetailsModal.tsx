import React, { useState } from 'react';
import { X, ShoppingCart, Package, MapPin } from 'lucide-react';

interface ProductDetailsModalProps {
  isOpen: boolean;
  onClose: () => void;
  productDetails: any;
  batches?: any;
  onAddToCart?: (product: any) => void;
  onAddBatchToCart?: (product: any, batch: any) => void;
}

const ProductDetailsModal: React.FC<ProductDetailsModalProps> = ({
  isOpen,
  onClose,
  productDetails,
  batches,
  onAddToCart,
  onAddBatchToCart
}) => {
  const [activeTab, setActiveTab] = useState('batches');

  if (!isOpen || !productDetails) return null;

  const tabs = [
    { id: 'batches', label: 'Batch Info' },
    { id: 'basic', label: 'Basic Info' },
    { id: 'categorization', label: 'Categories' },
    { id: 'cannabinoids', label: 'Cannabinoids' },
    { id: 'inventory', label: 'Inventory' },
    { id: 'pricing', label: 'Pricing' },
    { id: 'physical', label: 'Physical Specs' },
    { id: 'production', label: 'Production' },
    { id: 'description', label: 'Description' },
    { id: 'hardware', label: 'Hardware' },
    { id: 'logistics', label: 'Logistics' },
    { id: 'raw', label: 'All Fields' }
  ];

  const renderFieldValue = (value: any) => {
    if (value === null || value === undefined) return 'N/A';
    if (typeof value === 'boolean') return value ? 'Yes' : 'No';
    if (typeof value === 'object') return JSON.stringify(value, null, 2);
    return value.toString();
  };

  const renderSection = (title: string, data: any, includeImage?: boolean) => {
    if (!data) return null;

    const imageUrl = productDetails?.metadata?.image_url || productDetails?.raw_data?.image_url;

    return (
      <div className="space-y-3">
        <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200 border-b border-gray-200 dark:border-gray-700 pb-2">{title}</h3>
        <div className={includeImage && imageUrl ? "grid grid-cols-1 md:grid-cols-3 gap-6" : "grid grid-cols-1 md:grid-cols-2 gap-4"}>
          {includeImage && imageUrl && (
            <div className="md:col-span-1">
              <img
                src={imageUrl}
                alt={data.product_name || 'Product'}
                className="w-full h-auto rounded-lg border border-gray-200 dark:border-gray-700 object-contain bg-gray-50 dark:bg-gray-900"
                onError={(e) => {
                  (e.target as HTMLImageElement).style.display = 'none';
                }}
              />
            </div>
          )}
          <div className={includeImage && imageUrl ? "md:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-4" : "col-span-full grid grid-cols-1 md:grid-cols-2 gap-4"}>
            {Object.entries(data).map(([key, value]) => {
              if (value === null || value === undefined) return null;
              const displayKey = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
              return (
                <div key={key} className="flex flex-col">
                  <span className="text-sm font-medium text-gray-600 dark:text-gray-400">{displayKey}:</span>
                  <span className="text-sm text-gray-900 dark:text-gray-200 break-words">
                    {renderFieldValue(value)}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    );
  };

  const renderTabContent = () => {
    const data = productDetails;

    switch (activeTab) {
      case 'batches':
        return (
          <div className="space-y-4">
            {(() => {
              const batchData = typeof batches === 'string' ? JSON.parse(batches) : batches;
              const batchCount = Array.isArray(batchData) ? batchData.length : 0;

              return batchData && batchData.length > 0 ? (
                <>
                  <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200 border-b border-gray-200 dark:border-gray-700 pb-2">
                    Active Batches ({batchCount})
                  </h3>
                  {batchData.map((batch: any, index: number) => (
                    <div key={index} className="border border-gray-200 dark:border-gray-700 rounded-lg p-6 space-y-2 bg-white dark:bg-gray-800">
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <p className="font-semibold text-gray-900 dark:text-white">Batch/Lot: {batch.batch_lot}</p>
                          <p className="text-sm text-gray-600 dark:text-gray-400">Quantity Remaining: {batch.quantity_remaining}</p>
                        </div>
                        <div className="flex items-center gap-2">
                          {onAddBatchToCart && (
                            <button
                              onClick={() => {
                                // Convert the detailed product to the format expected by addToCart
                                const cartProduct = {
                                  id: productDetails.basic_info?.ocs_variant_number,
                                  sku: productDetails.basic_info?.sku,
                                  name: productDetails.basic_info?.product_name,
                                  brand: productDetails.basic_info?.brand,
                                  price: productDetails.pricing?.effective_price || productDetails.pricing?.retail_price,
                                  category: productDetails.categorization?.category,
                                  sub_category: productDetails.categorization?.sub_category
                                };
                                onAddBatchToCart(cartProduct, batch);
                                onClose();
                              }}
                              className="p-2 bg-blue-100 dark:bg-blue-900 hover:bg-blue-200 dark:hover:bg-blue-800 text-accent-700 dark:text-accent-300 rounded-lg transition-colors"
                              title="Add to Cart"
                            >
                              <ShoppingCart className="w-4 h-4" />
                            </button>
                          )}
                          <span className="px-2 py-1 rounded text-xs bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-300">
                            Active
                          </span>
                        </div>
                      </div>

                      {batch.packaged_on_date && (
                        <div className="text-sm">
                          <span className="text-gray-500 dark:text-gray-400">Packaged On:</span>
                          <p className="font-medium text-gray-900 dark:text-gray-200">{new Date(batch.packaged_on_date).toLocaleDateString()}</p>
                        </div>
                      )}

                      {batch.location_code && (
                        <div className="text-sm flex items-center gap-1">
                          <MapPin className="w-3 h-3 text-gray-500 dark:text-gray-400" />
                          <span className="text-gray-500 dark:text-gray-400">Location:</span>
                          <p className="font-medium text-gray-900 dark:text-gray-200">{batch.location_code}</p>
                        </div>
                      )}

                      {(batch.case_gtin || batch.each_gtin) && (
                        <div className="border-t border-gray-200 dark:border-gray-700 pt-2 mt-2">
                          <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Barcodes:</p>
                          <div className="space-y-1">
                            {batch.case_gtin && (
                              <p className="text-xs text-gray-700 dark:text-gray-300">
                                <span className="text-gray-500 dark:text-gray-400">Case GTIN:</span> {batch.case_gtin}
                              </p>
                            )}
                            {batch.each_gtin && (
                              <p className="text-xs text-gray-700 dark:text-gray-300">
                                <span className="text-gray-500 dark:text-gray-400">Each GTIN:</span> {batch.each_gtin}
                              </p>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </>
              ) : (
                <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                  <Package className="w-12 h-12 mx-auto mb-2 text-gray-300 dark:text-gray-600" />
                  <p>No batch information available</p>
                </div>
              );
            })()}
          </div>
        );

      case 'basic':
        return renderSection('Basic Information', data.basic_info, true);

      case 'categorization':
        return renderSection('Product Categorization', data.categorization);

      case 'cannabinoids':
        return renderSection('Cannabinoid Profile', data.cannabinoids);

      case 'inventory':
        return renderSection('Inventory Status', data.inventory);

      case 'pricing':
        return renderSection('Pricing Information', data.pricing);

      case 'physical':
        return renderSection('Physical Specifications', data.physical_specs);

      case 'production':
        return renderSection('Production Details', data.production);

      case 'description':
        return renderSection('Product Description', data.description);

      case 'hardware':
        return renderSection('Hardware Specifications', data.hardware);

      case 'logistics':
        return renderSection('Logistics & Fulfillment', data.logistics);

      case 'raw':
        return (
          <div className="space-y-3">
            <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200 border-b border-gray-200 dark:border-gray-700 pb-2">All Product Fields (97 columns)</h3>
            <div className="max-h-[500px] overflow-y-auto">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead className="bg-gray-50 dark:bg-gray-900 sticky top-0">
                  <tr>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Field</th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Value</th>
                  </tr>
                </thead>
                <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                  {data.raw_data && Object.entries(data.raw_data).map(([key, value]) => (
                    <tr key={key} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                      <td className="px-4 py-2 text-sm font-medium text-gray-900 dark:text-gray-200">
                        {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </td>
                      <td className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 break-words max-w-md">
                        {renderFieldValue(value)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black bg-opacity-50 dark:bg-opacity-70 flex items-center justify-center p-6">
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 max-w-7xl w-full max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex justify-between items-center p-6 border-b border-gray-200 dark:border-gray-700">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
              {batches ? 'Product & Batch Information' : 'Product Details'}
            </h2>
            {productDetails?.basic_info && (
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                {productDetails.basic_info.product_name} - {productDetails.basic_info.brand}
              </p>
            )}
          </div>
          <button
            onClick={onClose}
            className="text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 transition-colors"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200 dark:border-gray-700">
          <div className="flex overflow-x-auto px-6">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`
                  px-4 py-3 text-sm font-medium whitespace-nowrap border-b-2 transition-colors
                  ${activeTab === tab.id
                    ? 'border-primary-600 text-primary-600 dark:border-primary-500 dark:text-primary-400'
                    : 'border-transparent text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200 hover:border-gray-200 dark:hover:border-gray-600'
                  }
                `}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {renderTabContent()}
        </div>

        {/* Footer */}
        <div className="border-t border-gray-200 dark:border-gray-700 p-6 flex justify-between items-center">
          <div className="text-sm text-gray-600 dark:text-gray-400">
            {productDetails?.inventory?.in_stock ? (
              <span className="text-primary-600 dark:text-primary-400 font-medium">
                In Stock: {productDetails.inventory.quantity_available} units
              </span>
            ) : (
              <span className="text-danger-600 dark:text-danger-400 font-medium">Out of Stock</span>
            )}
          </div>
          <div className="flex gap-4">
            {onAddToCart && productDetails?.inventory?.in_stock && (
              <button
                onClick={() => {
                  // Convert the detailed product back to the format expected by addToCart
                  const cartProduct = {
                    id: productDetails.basic_info?.ocs_variant_number,
                    sku: productDetails.basic_info?.sku,
                    name: productDetails.basic_info?.product_name,
                    brand: productDetails.basic_info?.brand,
                    price: productDetails.pricing?.effective_price || productDetails.pricing?.retail_price,
                    category: productDetails.categorization?.category,
                    sub_category: productDetails.categorization?.sub_category
                  };
                  onAddToCart(cartProduct);
                  onClose();
                }}
                className="px-4 py-2 bg-primary-600 dark:bg-primary-700 text-white rounded-lg hover:bg-primary-700 dark:hover:bg-primary-600 transition-colors"
              >
                Add to Cart
              </button>
            )}
            <button
              onClick={onClose}
              className="px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProductDetailsModal;