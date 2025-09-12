import React, { useState, useRef, useEffect } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Upload, X, CheckCircle, AlertCircle, FileSpreadsheet, TruckIcon, Loader2, Package } from 'lucide-react';
import * as XLSX from 'xlsx';
import { api } from '../services/api';
import { useStoreContext } from '../contexts/StoreContext';
import StoreSelector from './StoreSelector';

interface ASNItem {
  shipment_id?: string;
  container_id?: string;
  sku: string;
  item_name?: string;
  unit_price: number;
  vendor?: string;
  brand?: string;
  case_gtin?: string;
  packaged_on_date?: string;
  batch_lot?: string;
  gtin_barcode?: string;
  each_gtin?: string;
  shipped_qty: number;
  received_qty?: number;
  retail_price?: number;
  uom?: string;
  uom_conversion?: number;
  uom_conversion_qty?: number;
  exists_in_inventory?: boolean;
  is_new_batch?: boolean;
  image_url?: string;
  product_name?: string;
}

interface ASNImportModalProps {
  isOpen: boolean;
  onClose: () => void;
  suppliers: any[];
}

const ASNImportModal: React.FC<ASNImportModalProps> = ({ isOpen, onClose, suppliers }) => {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { currentStore } = useStoreContext();
  
  const [step, setStep] = useState<'upload' | 'review' | 'create'>('upload');
  const [asnItems, setAsnItems] = useState<ASNItem[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingProgress, setProcessingProgress] = useState(0);
  const [uploadedFileName, setUploadedFileName] = useState<string>('');
  
  // Form state for PO creation
  const [poNumber, setPoNumber] = useState('');
  const [supplierId, setSupplierId] = useState('');
  const [expectedDate, setExpectedDate] = useState('');
  const [notes, setNotes] = useState('');
  
  const [error, setError] = useState<string | null>(null);

  // Set default supplier to OCS Wholesale and today's date when modal opens
  useEffect(() => {
    if (isOpen && suppliers?.length > 0) {
      // Find OCS Wholesale supplier
      const ocsSupplier = suppliers.find((s: any) => 
        s.name?.toLowerCase().includes('ocs') || 
        s.name?.toLowerCase().includes('wholesale')
      );
      if (ocsSupplier) {
        setSupplierId(ocsSupplier.id);
      }
      // Set today's date as default
      const today = new Date().toISOString().split('T')[0];
      setExpectedDate(today);
    }
  }, [isOpen, suppliers]);

  // Check if item exists in inventory (client-side API call)
  const checkInventoryExists = async (sku: string, batchLot?: string): Promise<{exists: boolean, isNewBatch: boolean}> => {
    try {
      const params = new URLSearchParams();
      params.append('sku', sku);
      
      // Check SKU exists
      const skuResponse = await fetch(`http://localhost:5024/api/inventory/check?${params.toString()}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (!skuResponse.ok) {
        return { exists: false, isNewBatch: false };
      }
      
      const skuData = await skuResponse.json();
      
      // If SKU doesn't exist, it's completely new
      if (!skuData.exists) {
        return { exists: false, isNewBatch: false };
      }
      
      // If batch lot provided, check if this specific batch exists
      if (batchLot) {
        params.append('batch_lot', batchLot);
        const batchResponse = await fetch(`http://localhost:5024/api/inventory/check?${params.toString()}`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        });
        
        if (batchResponse.ok) {
          const batchData = await batchResponse.json();
          // SKU exists but batch doesn't = new batch
          return { exists: true, isNewBatch: !batchData.exists };
        }
      }
      
      return { exists: true, isNewBatch: false };
    } catch (error) {
      console.error('Error checking inventory:', error);
      return { exists: false, isNewBatch: false };
    }
  };

  // Get product image from catalog
  const getProductImage = async (sku: string): Promise<{image_url: string | null, product_name: string, retail_price?: number}> => {
    try {
      // Trim and encode the SKU for the URL
      const trimmedSku = encodeURIComponent(sku.trim());
      const response = await fetch(`http://localhost:5024/api/inventory/products/${trimmedSku}/image`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        return {
          image_url: data.image_url,
          product_name: data.product_name || 'Unknown Product',
          retail_price: data.retail_price
        };
      }
      return { image_url: null, product_name: 'Unknown Product', retail_price: undefined };
    } catch (error) {
      console.error('Error getting product image:', error);
      return { image_url: null, product_name: 'Unknown Product', retail_price: undefined };
    }
  };

  // Check if file has been imported before
  const checkDuplicateImport = async (filename: string): Promise<boolean> => {
    try {
      const params = new URLSearchParams();
      params.append('filename', filename);
      
      const response = await fetch(`http://localhost:5024/api/inventory/asn/check-duplicate?${params.toString()}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        return data.is_duplicate || false;
      }
      return false;
    } catch (error) {
      console.error('Error checking duplicate import:', error);
      return false;
    }
  };

  // Mark file as imported
  const markFileAsImported = async (filename: string): Promise<void> => {
    try {
      const params = new URLSearchParams();
      params.append('filename', filename);
      
      await fetch(`http://localhost:5024/api/inventory/asn/mark-imported?${params.toString()}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
    } catch (error) {
      console.error('Error marking file as imported:', error);
    }
  };

  // Process Excel file on client side
  const processExcelFile = async (file: File) => {
    setIsProcessing(true);
    setProcessingProgress(0);
    setError(null);
    
    try {
      const data = await file.arrayBuffer();
      const workbook = XLSX.read(data, { type: 'array' });
      const sheetName = workbook.SheetNames[0];
      const worksheet = workbook.Sheets[sheetName];
      const jsonData = XLSX.utils.sheet_to_json(worksheet);
      
      if (jsonData.length === 0) {
        throw new Error('Excel file is empty');
      }
      
      // Validate required columns
      const firstRow = jsonData[0] as any;
      if (!('SKU' in firstRow) || !('Shipped_Qty' in firstRow)) {
        throw new Error('Missing required columns: SKU and Shipped_Qty');
      }
      
      const items: ASNItem[] = [];
      const totalRows = jsonData.length;
      
      // Process each row and check inventory
      for (let i = 0; i < jsonData.length; i++) {
        const row = jsonData[i] as any;
        setProcessingProgress(Math.round(((i + 1) / totalRows) * 100));
        
        const sku = String(row.SKU || '');
        const batchLot = row.BatchLot ? String(row.BatchLot) : undefined;
        
        // Check if this SKU + BatchLot exists in inventory
        const inventoryCheck = await checkInventoryExists(sku, batchLot);
        
        // Get product image
        const productInfo = await getProductImage(sku);
        
        // Parse the row data
        const item: ASNItem = {
          shipment_id: row.ShipmentID ? String(row.ShipmentID) : undefined,
          container_id: row.ContainerID ? String(row.ContainerID) : undefined,
          sku: sku,
          item_name: row.ItemName ? String(row.ItemName) : productInfo.product_name,
          unit_price: parseFloat(row.UnitPrice) || 0,
          vendor: row.Vendor ? String(row.Vendor) : undefined,
          brand: row.Brand ? String(row.Brand) : undefined,
          case_gtin: row.CaseGTIN ? String(row.CaseGTIN) : undefined,
          packaged_on_date: row.PackagedOnDate ? String(row.PackagedOnDate) : undefined,
          batch_lot: batchLot,
          gtin_barcode: row.Barcode ? String(row.Barcode) : undefined,
          each_gtin: row.EachGTIN ? String(row.EachGTIN) : undefined,
          shipped_qty: parseInt(row.Shipped_Qty) || 0,
          received_qty: parseInt(row.Shipped_Qty) || 0, // Default to shipped quantity
          retail_price: productInfo.retail_price || parseFloat(row.RetailPrice) || 0,
          uom: row.UOM ? String(row.UOM) : undefined,
          uom_conversion: parseFloat(row.UOMCONVERSION) || 1,
          uom_conversion_qty: parseInt(row.UOMCONVERSIONQTY) || 1,
          exists_in_inventory: inventoryCheck.exists,
          is_new_batch: inventoryCheck.isNewBatch,
          image_url: productInfo.image_url,
          product_name: productInfo.product_name
        };
        
        items.push(item);
      }
      
      setAsnItems(items);
      setStep('review');
      setIsProcessing(false);
      setProcessingProgress(0);
      
    } catch (error: any) {
      setError(error.message || 'Failed to process Excel file');
      setIsProcessing(false);
      setProcessingProgress(0);
    }
  };

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
        setError('Please upload an Excel file (.xlsx or .xls)');
        return;
      }
      
      // Check if this file has already been imported
      const isDuplicate = await checkDuplicateImport(file.name);
      if (isDuplicate) {
        setError(`File "${file.name}" has already been imported. Please select a different file.`);
        if (fileInputRef.current) {
          fileInputRef.current.value = '';
        }
        return;
      }
      
      // Store the filename for later
      setUploadedFileName(file.name);
      
      // Extract filename without extension and use as PO Number
      const fileNameWithoutExt = file.name.replace(/\.(xlsx|xls)$/i, '');
      setPoNumber(fileNameWithoutExt);
      
      processExcelFile(file);
    }
  };

  // Create Purchase Order using existing endpoint
  const createPOMutation = useMutation({
    mutationFn: async () => {
      // Prepare purchase order items from ASN data
      const poItems = asnItems.map(item => ({
        sku: item.sku,
        batch_lot: item.batch_lot,
        quantity_ordered: item.shipped_qty,
        unit_cost: item.unit_price,
        item_name: item.item_name,
        vendor: item.vendor,
        brand: item.brand,
        case_gtin: item.case_gtin,
        packaged_on_date: item.packaged_on_date,
        gtin_barcode: item.gtin_barcode,
        each_gtin: item.each_gtin,
        shipped_qty: item.shipped_qty,
        uom: item.uom,
        uom_conversion: item.uom_conversion,
        uom_conversion_qty: item.uom_conversion_qty,
        exists_in_inventory: item.exists_in_inventory
      }));

      // Prepare purchase order data matching API expectations
      const purchaseOrder = {
        supplier_id: supplierId,
        store_id: currentStore?.id,  // Include store_id from context
        items: poItems.map(item => ({
          sku: item.sku,
          quantity: item.shipped_qty,  // Use shipped_qty as the quantity
          unit_cost: item.unit_cost,
          batch_lot: item.batch_lot,
          expiry_date: null,  // Add if available in your data
          case_gtin: item.case_gtin,
          gtin_barcode: item.gtin_barcode,
          each_gtin: item.each_gtin
        })),
        expected_date: expectedDate || null,
        notes: `PO Number: ${poNumber}${notes ? `\n${notes}` : ''}`  // Include PO number in notes
      };

      const response = await fetch('http://localhost:5024/api/inventory/purchase-orders', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Store-ID': currentStore?.id || '',  // Ensure store ID is in header
        },
        body: JSON.stringify(purchaseOrder),
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to create purchase order');
      }
      
      return response.json();
    },
    onSuccess: async (data) => {
      // Mark the file as imported
      if (uploadedFileName) {
        await markFileAsImported(uploadedFileName);
      }
      queryClient.invalidateQueries({ queryKey: ['purchase-orders'] });
      alert(`Purchase Order ${poNumber} created successfully!`);
      handleClose();
    },
    onError: (error: Error) => {
      setError(error.message);
    },
  });

  const handleCreatePO = () => {
    if (!poNumber || !supplierId) {
      setError('Please fill in all required fields');
      return;
    }
    if (!currentStore) {
      setError('Please select a store before creating a purchase order');
      return;
    }
    createPOMutation.mutate();
  };

  const handleClose = () => {
    setStep('upload');
    setAsnItems([]);
    setPoNumber('');
    setSupplierId('');
    setExpectedDate('');
    setNotes('');
    setError(null);
    setIsProcessing(false);
    setProcessingProgress(0);
    onClose();
  };

  if (!isOpen) return null;

  const existingItemsCount = asnItems.filter(item => item.exists_in_inventory).length;
  const newItemsCount = asnItems.filter(item => !item.exists_in_inventory).length;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg max-w-6xl w-full max-h-[90vh] overflow-hidden">
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-xl font-bold flex items-center gap-2">
            <TruckIcon className="h-6 w-6 text-green-600" />
            Import ASN (Advance Shipping Notice)
          </h2>
          <button onClick={handleClose} className="text-gray-500 hover:text-gray-700">
            <X className="h-6 w-6" />
          </button>
        </div>

        <div className="p-6 overflow-y-auto" style={{ maxHeight: 'calc(90vh - 200px)' }}>
          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-red-600" />
              <span className="text-red-700">{error}</span>
            </div>
          )}

          {step === 'upload' && (
            <div className="space-y-6">
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center">
                <FileSpreadsheet className="mx-auto h-16 w-16 text-gray-400 mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  Upload ASN Excel File
                </h3>
                <p className="text-sm text-gray-600 mb-4">
                  Select an Excel file (.xlsx or .xls) containing ASN data
                </p>
                {isProcessing ? (
                  <div className="space-y-4">
                    <div className="flex items-center justify-center gap-2">
                      <Loader2 className="h-5 w-5 animate-spin text-green-600" />
                      <span>Processing Excel and checking inventory...</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-green-600 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${processingProgress}%` }}
                      />
                    </div>
                    <p className="text-sm text-gray-600">{processingProgress}% complete</p>
                  </div>
                ) : (
                  <>
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept=".xlsx,.xls"
                      onChange={handleFileSelect}
                      className="hidden"
                    />
                    <button
                      onClick={() => fileInputRef.current?.click()}
                      className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 flex items-center gap-2 mx-auto"
                    >
                      <Upload className="h-5 w-5" />
                      Select File
                    </button>
                  </>
                )}
              </div>

              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="font-medium mb-2">Required Excel Columns:</h4>
                <div className="grid grid-cols-4 gap-2 text-sm text-gray-600">
                  <span>• ShipmentID</span>
                  <span>• ContainerID</span>
                  <span>• SKU *</span>
                  <span>• ItemName</span>
                  <span>• UnitPrice</span>
                  <span>• Vendor</span>
                  <span>• Brand</span>
                  <span>• CaseGTIN</span>
                  <span>• PackagedOnDate</span>
                  <span>• BatchLot</span>
                  <span>• GTINBarCode</span>
                  <span>• EachGTIN</span>
                  <span>• Shipped_Qty *</span>
                  <span>• UOM</span>
                  <span>• UOMCONVERSION</span>
                  <span>• UOMCONVERSIONQTY</span>
                </div>
                <p className="text-xs text-gray-500 mt-2">* Required fields</p>
              </div>
            </div>
          )}

          {step === 'review' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium">Review Imported Items</h3>
                <div className="flex gap-4">
                  <span className="text-sm">
                    <span className="font-medium text-green-600">{newItemsCount}</span> new items
                  </span>
                  <span className="text-sm">
                    <span className="font-medium text-blue-600">{existingItemsCount}</span> existing items
                  </span>
                  <span className="text-sm">
                    <span className="font-medium">{asnItems.length}</span> total items
                  </span>
                </div>
              </div>

              <div className="overflow-x-auto border rounded-lg">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Image</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">SKU</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Item Name</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Quantity</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Unit Price</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Total</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Vendor</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {asnItems.map((item, index) => (
                      <tr key={index} className={item.exists_in_inventory && !item.is_new_batch ? 'bg-blue-50' : ''}>
                        <td className="px-4 py-3 whitespace-nowrap">
                          <div className="flex flex-col items-center gap-1">
                            {item.is_new_batch ? (
                              <>
                                <span className="px-2 py-1 text-xs font-semibold rounded-full bg-yellow-100 text-yellow-800">
                                  New Batch
                                </span>
                              </>
                            ) : item.exists_in_inventory ? (
                              <span className="flex items-center gap-1 text-blue-600">
                                <CheckCircle className="h-4 w-4" />
                                <span className="text-xs">Exists</span>
                              </span>
                            ) : (
                              <span className="flex items-center gap-1 text-green-600">
                                <AlertCircle className="h-4 w-4" />
                                <span className="text-xs">New</span>
                              </span>
                            )}
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          {item.image_url ? (
                            <img 
                              src={item.image_url} 
                              alt={item.product_name || item.item_name || 'Product'}
                              className="h-12 w-12 object-cover rounded"
                              onError={(e) => {
                                (e.target as HTMLImageElement).style.display = 'none';
                              }}
                            />
                          ) : (
                            <div className="h-12 w-12 bg-gray-200 rounded flex items-center justify-center">
                              <Package className="h-6 w-6 text-gray-400" />
                            </div>
                          )}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm font-medium">{item.sku}</td>
                        <td className="px-4 py-3 text-sm">{item.item_name || '-'}</td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm">{item.shipped_qty}</td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm">${item.unit_price.toFixed(2)}</td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm font-medium">
                          ${(item.shipped_qty * item.unit_price).toFixed(2)}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm">{item.vendor || '-'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="flex justify-between">
                <button
                  onClick={() => setStep('upload')}
                  className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  Back
                </button>
                <button
                  onClick={() => setStep('create')}
                  className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700"
                >
                  Continue to Create PO
                </button>
              </div>
            </div>
          )}

          {step === 'create' && (
            <div className="space-y-6">
              <h3 className="text-lg font-medium">Create Purchase Order</h3>
              
              {/* Store Selector */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Store *
                </label>
                <StoreSelector className="w-full" showStats={false} />
                {!currentStore && (
                  <p className="mt-1 text-sm text-red-600">Please select a store</p>
                )}
              </div>
              
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    PO Number *
                  </label>
                  <input
                    type="text"
                    value={poNumber}
                    onChange={(e) => setPoNumber(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
                    placeholder="PO-2024-001"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Supplier *
                  </label>
                  <select
                    value={supplierId}
                    onChange={(e) => setSupplierId(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
                  >
                    <option value="">Select Supplier</option>
                    {suppliers?.map((supplier: any) => (
                      <option key={supplier.id} value={supplier.id}>
                        {supplier.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Expected Date
                  </label>
                  <input
                    type="date"
                    value={expectedDate}
                    onChange={(e) => setExpectedDate(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
                  />
                </div>

                <div className="col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Notes
                  </label>
                  <textarea
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
                    rows={2}
                    placeholder="Additional notes..."
                  />
                </div>
              </div>

              {/* Items Table */}
              <div className="space-y-4">
                <h4 className="font-medium text-gray-900">Order Items</h4>
                <div className="overflow-x-auto border rounded-lg">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Item Name</th>
                        <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Qty Expected</th>
                        <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Qty Received</th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Unit Price</th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Retail Price</th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Line Total</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {asnItems.map((item, index) => (
                        <tr key={index}>
                          <td className="px-4 py-3">
                            <div className="flex items-center gap-3">
                              {item.image_url ? (
                                <img 
                                  src={item.image_url} 
                                  alt={item.item_name || 'Product'}
                                  className="h-10 w-10 object-cover rounded"
                                  onError={(e) => {
                                    (e.target as HTMLImageElement).style.display = 'none';
                                  }}
                                />
                              ) : (
                                <div className="h-10 w-10 bg-gray-200 rounded flex items-center justify-center">
                                  <Package className="h-5 w-5 text-gray-400" />
                                </div>
                              )}
                              <div>
                                <div className="text-sm font-medium text-gray-900">{item.item_name || item.product_name}</div>
                                <div className="text-xs text-gray-500">SKU: {item.sku}</div>
                                {item.batch_lot && <div className="text-xs text-gray-500">Batch: {item.batch_lot}</div>}
                              </div>
                            </div>
                          </td>
                          <td className="px-4 py-3 text-center">
                            <span className="text-sm font-medium">{item.shipped_qty}</span>
                          </td>
                          <td className="px-4 py-3 text-center">
                            <input
                              type="number"
                              value={item.received_qty || item.shipped_qty}
                              onChange={(e) => {
                                const newItems = [...asnItems];
                                newItems[index].received_qty = parseInt(e.target.value) || 0;
                                setAsnItems(newItems);
                              }}
                              className="w-20 px-2 py-1 text-center border border-gray-300 rounded"
                              min="0"
                            />
                          </td>
                          <td className="px-4 py-3 text-right">
                            <span className="text-sm">${item.unit_price.toFixed(2)}</span>
                          </td>
                          <td className="px-4 py-3 text-right">
                            <input
                              type="number"
                              value={item.retail_price || 0}
                              onChange={(e) => {
                                const newItems = [...asnItems];
                                newItems[index].retail_price = parseFloat(e.target.value) || 0;
                                setAsnItems(newItems);
                              }}
                              className="w-24 px-2 py-1 text-right border border-gray-300 rounded"
                              min="0"
                              step="0.01"
                              placeholder="0.00"
                            />
                          </td>
                          <td className="px-4 py-3 text-right">
                            <span className="text-sm font-medium">
                              ${(item.shipped_qty * item.unit_price).toFixed(2)}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                    <tfoot className="bg-gray-50">
                      <tr>
                        <td colSpan={5} className="px-4 py-3 text-right font-medium text-gray-700">
                          Total:
                        </td>
                        <td className="px-4 py-3 text-right font-bold text-gray-900">
                          ${asnItems.reduce((sum, item) => sum + (item.shipped_qty * item.unit_price), 0).toFixed(2)}
                        </td>
                      </tr>
                    </tfoot>
                  </table>
                </div>
              </div>

              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="font-medium mb-2">Summary</h4>
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600">Total Items:</span>
                    <span className="ml-2 font-medium">{asnItems.length}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Total Quantity:</span>
                    <span className="ml-2 font-medium">
                      {asnItems.reduce((sum, item) => sum + item.shipped_qty, 0)}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-600">Total Amount:</span>
                    <span className="ml-2 font-medium">
                      ${asnItems.reduce((sum, item) => sum + (item.shipped_qty * item.unit_price), 0).toFixed(2)}
                    </span>
                  </div>
                </div>
              </div>

              <div className="flex justify-between">
                <button
                  onClick={() => setStep('review')}
                  className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  Back
                </button>
                <button
                  onClick={handleCreatePO}
                  disabled={createPOMutation.isPending}
                  className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 disabled:opacity-50"
                >
                  {createPOMutation.isPending ? 'Creating...' : 'Create Purchase Order'}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ASNImportModal;