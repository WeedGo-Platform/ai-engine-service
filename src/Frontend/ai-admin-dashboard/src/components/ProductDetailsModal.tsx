import React, { useState } from 'react';
import { X, ShoppingCart, Package, MapPin, Calendar } from 'lucide-react';

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
        <h3 className="text-lg font-semibold text-gray-800 border-b pb-2">{title}</h3>
        <div className={includeImage && imageUrl ? "grid grid-cols-1 md:grid-cols-3 gap-4" : "grid grid-cols-1 md:grid-cols-2 gap-3"}>
          {includeImage && imageUrl && (
            <div className="md:col-span-1">
              <img
                src={imageUrl}
                alt={data.product_name || 'Product'}
                className="w-full h-auto rounded-lg shadow-md object-contain bg-gray-50"
                onError={(e) => {
                  (e.target as HTMLImageElement).style.display = 'none';
                }}
              />
            </div>
          )}
          <div className={includeImage && imageUrl ? "md:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-3" : "col-span-full grid grid-cols-1 md:grid-cols-2 gap-3"}>
            {Object.entries(data).map(([key, value]) => {
              if (value === null || value === undefined) return null;
              const displayKey = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
              return (
                <div key={key} className="flex flex-col">
                  <span className="text-sm font-medium text-gray-600">{displayKey}:</span>
                  <span className="text-sm text-gray-900 break-words">
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
                  <h3 className="text-lg font-semibold text-gray-800 border-b pb-2">
                    Active Batches ({batchCount})
                  </h3>
                  {batchData.map((batch: any, index: number) => (
                    <div key={index} className="border rounded-lg p-4 space-y-2">
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <p className="font-semibold">Batch/Lot: {batch.batch_lot}</p>
                          <p className="text-sm text-gray-600">Quantity Remaining: {batch.quantity_remaining}</p>
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
                              className="p-2 bg-blue-100 hover:bg-blue-200 text-blue-700 rounded-lg transition-colors"
                              title="Add to Cart"
                            >
                              <ShoppingCart className="w-4 h-4" />
                            </button>
                          )}
                          <span className="px-2 py-1 rounded text-xs bg-green-100 text-green-700">
                            Active
                          </span>
                        </div>
                      </div>

                      {batch.packaged_on_date && (
                        <div className="text-sm">
                          <span className="text-gray-500">Packaged On:</span>
                          <p className="font-medium">{new Date(batch.packaged_on_date).toLocaleDateString()}</p>
                        </div>
                      )}

                      {batch.location_code && (
                        <div className="text-sm flex items-center gap-1">
                          <MapPin className="w-3 h-3 text-gray-500" />
                          <span className="text-gray-500">Location:</span>
                          <p className="font-medium">{batch.location_code}</p>
                        </div>
                      )}

                      {(batch.case_gtin || batch.each_gtin) && (
                        <div className="border-t pt-2 mt-2">
                          <p className="text-sm font-medium text-gray-700 mb-1">Barcodes:</p>
                          <div className="space-y-1">
                            {batch.case_gtin && (
                              <p className="text-xs">
                                <span className="text-gray-500">Case GTIN:</span> {batch.case_gtin}
                              </p>
                            )}
                            {batch.each_gtin && (
                              <p className="text-xs">
                                <span className="text-gray-500">Each GTIN:</span> {batch.each_gtin}
                              </p>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <Package className="w-12 h-12 mx-auto mb-2 text-gray-300" />
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
            <h3 className="text-lg font-semibold text-gray-800 border-b pb-2">All Product Fields (97 columns)</h3>
            <div className="max-h-[500px] overflow-y-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50 sticky top-0">
                  <tr>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Field</th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Value</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {data.raw_data && Object.entries(data.raw_data).map(([key, value]) => (
                    <tr key={key} className="hover:bg-gray-50">
                      <td className="px-4 py-2 text-sm font-medium text-gray-900">
                        {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </td>
                      <td className="px-4 py-2 text-sm text-gray-600 break-words max-w-md">
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
    <div className="fixed inset-0 z-50 bg-black bg-opacity-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-7xl w-full max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex justify-between items-center p-6 border-b">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">
              {batches ? 'Product & Batch Information' : 'Product Details'}
            </h2>
            {productDetails?.basic_info && (
              <p className="text-sm text-gray-600 mt-1">
                {productDetails.basic_info.product_name} - {productDetails.basic_info.brand}
              </p>
            )}
          </div>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 transition-colors"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        {/* Tabs */}
        <div className="border-b">
          <div className="flex overflow-x-auto px-6">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`
                  px-4 py-3 text-sm font-medium whitespace-nowrap border-b-2 transition-colors
                  ${activeTab === tab.id
                    ? 'border-green-600 text-green-600'
                    : 'border-transparent text-gray-600 hover:text-gray-900 hover:border-gray-300'
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
        <div className="border-t p-6 flex justify-between items-center">
          <div className="text-sm text-gray-600">
            {productDetails?.inventory?.in_stock ? (
              <span className="text-green-600 font-medium">
                In Stock: {productDetails.inventory.quantity_available} units
              </span>
            ) : (
              <span className="text-red-600 font-medium">Out of Stock</span>
            )}
          </div>
          <div className="flex gap-3">
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
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
              >
                Add to Cart
              </button>
            )}
            <button
              onClick={onClose}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
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