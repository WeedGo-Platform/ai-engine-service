import React, { useState, useRef, useEffect } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Upload, X, CheckCircle, AlertCircle, FileSpreadsheet, TruckIcon, Loader2, Package } from 'lucide-react';
import * as XLSX from 'xlsx';
import { api } from '../services/api';
import { useStoreContext } from '../contexts/StoreContext';
import { useAuth } from '../contexts/AuthContext';
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
  const { user, isStoreManager } = useAuth();
  
  const [step, setStep] = useState<'upload' | 'review' | 'create'>('upload');
  const [asnItems, setAsnItems] = useState<ASNItem[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingProgress, setProcessingProgress] = useState(0);
  const [uploadedFileName, setUploadedFileName] = useState<string>('');
  
  // Form state for PO creation
  const [poNumber, setPoNumber] = useState('');
  const [supplierId, setSupplierId] = useState('');
  const [notes, setNotes] = useState('');
  const [charges, setCharges] = useState(0);
  const [discount, setDiscount] = useState(0);
  const [paidInFull, setPaidInFull] = useState(false);
  
  const [error, setError] = useState<string | null>(null);

  // Set OCS Wholesale as default supplier for Ontario stores
  useEffect(() => {
    if (isOpen && suppliers?.length > 0) {
      // Always use OCS Wholesale for Ontario stores
      const ocsSupplier = suppliers.find((s: any) => 
        s.name?.toLowerCase().includes('ocs') || 
        s.name?.toLowerCase().includes('wholesale')
      );
      if (ocsSupplier) {
        setSupplierId(ocsSupplier.id);
      }
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
      console.error('Error checking inventory:', error instanceof Error ? error.message : String(error));
      return { exists: false, isNewBatch: false };
    }
  };

  // Get product image from catalog with retry logic
  const getProductImage = async (sku: string, retryCount = 0): Promise<{image_url: string | null, product_name: string, retail_price?: number}> => {
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
        // Ensure we return the full image URL if it exists
        return {
          image_url: data.image_url || null,
          product_name: data.product_name || sku, // Use SKU as fallback name
          retail_price: data.retail_price
        };
      }
      
      // Retry on failure if we have retries left
      if (retryCount > 0) {
        await new Promise(resolve => setTimeout(resolve, 500)); // Wait 500ms before retry
        return getProductImage(sku, retryCount - 1);
      }
      
      return { image_url: null, product_name: sku, retail_price: undefined };
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      console.error(`Error getting product image for SKU ${sku}:`, errorMessage);
      // Don't retry on 429 errors to avoid making rate limiting worse
      // Only retry on other errors if we have retries left
      if (retryCount > 0 && !errorMessage.includes('429') && !errorMessage.includes('Too Many Requests')) {
        await new Promise(resolve => setTimeout(resolve, 1000)); // Wait 1s before retry
        return getProductImage(sku, retryCount - 1);
      }
      return { image_url: null, product_name: sku, retail_price: undefined };
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
      console.error('Error checking duplicate import:', error instanceof Error ? error.message : String(error));
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
      console.error('Error marking file as imported:', error instanceof Error ? error.message : String(error));
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
      
      // Add delay function to avoid rate limiting
      const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));
      
      // Process each row and check inventory with rate limiting
      for (let i = 0; i < jsonData.length; i++) {
        // Add delay between items to avoid 429 rate limit errors (500ms per item)
        if (i > 0) {
          await delay(500);
        }
        const row = jsonData[i] as any;
        setProcessingProgress(Math.round(((i + 1) / totalRows) * 100));
        
        const sku = String(row.SKU || '');
        const batchLot = row.BatchLot ? String(row.BatchLot) : undefined;
        
        // Check if this SKU + BatchLot exists in inventory
        const inventoryCheck = await checkInventoryExists(sku, batchLot);
        
        // Get product image
        const productInfo = await getProductImage(sku);
        
        // Convert date format from "MM/DD/YYYY 12:00:00 AM" to "YYYY-MM-DD"
        let formattedPackagedOnDate: string | undefined = undefined;
        if (row.PackagedOnDate) {
          const dateStr = String(row.PackagedOnDate);
          // Try to parse various date formats
          if (dateStr.includes('/')) {
            // Handle "MM/DD/YYYY" or "MM/DD/YYYY 12:00:00 AM" format
            const parts = dateStr.split(' ')[0].split('/');
            if (parts.length === 3) {
              const month = parts[0].padStart(2, '0');
              const day = parts[1].padStart(2, '0');
              const year = parts[2];
              formattedPackagedOnDate = `${year}-${month}-${day}`;
            }
          } else if (dateStr.includes('-')) {
            // Already in YYYY-MM-DD format
            formattedPackagedOnDate = dateStr.split(' ')[0];
          }
        }
        
        // Debug: Log the row to see actual column names
        if (i === 0) {
          console.log('First data row columns:', Object.keys(row));
          console.log('GTINBarCode value:', row.GTINBarCode);
          console.log('Full row data:', row);
        }

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
          packaged_on_date: formattedPackagedOnDate,
          batch_lot: batchLot,
          // Use exact column name from Excel: GTINBarCode (capital C in Code)
          gtin_barcode: row.GTINBarCode ? String(row.GTINBarCode) : undefined,
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
      if (!poNumber || !asnItems.length) {
        throw new Error('Invalid PO data');
      }

      // Get store details to determine province and supplier
      let storeProvince = 'ON'; // Default to Ontario
      let vendorName = 'OCS'; // Default vendor
      
      if (currentStore?.id) {
        try {
          // Fetch store details to get province
          const storeResponse = await fetch(`http://localhost:5024/api/stores/${currentStore.id}`);
          if (storeResponse.ok) {
            const storeData = await storeResponse.json();
            storeProvince = storeData.province || 'ON';
          }
        } catch (error) {
          console.error('Failed to fetch store details:', error instanceof Error ? error.message : String(error));
        }
      }

      // Prepare purchase order items from ASN data
      const poItems = asnItems.map(item => ({
        sku: item.sku,
        batch_lot: item.batch_lot,
        quantity_ordered: item.shipped_qty,
        unit_cost: item.unit_price,
        item_name: item.item_name,
        vendor: item.vendor || vendorName,  // Use determined vendor
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

      // packaged_on_date is optional - use today's date as fallback if missing
      const itemsWithoutPackagedDate = poItems.filter(item => !item.packaged_on_date);
      if (itemsWithoutPackagedDate.length > 0) {
        console.warn(`Missing packaged_on_date for ${itemsWithoutPackagedDate.length} items. Using today's date as fallback.`);
      }

      // Calculate totals
      const subtotal = poItems.reduce((sum, item) => sum + (item.shipped_qty * item.unit_cost), 0);
      const totalAmount = subtotal + charges - discount;
      
      // Determine supplier based on province
      let finalSupplierId = supplierId;
      if (!finalSupplierId) {
        // For Ontario, use OCS Wholesale
        if (storeProvince === 'ON') {
          const ocsSupplier = suppliers.find((s: any) => 
            s.name?.toLowerCase().includes('ocs') || 
            s.name?.toLowerCase().includes('wholesale')
          );
          if (ocsSupplier) {
            finalSupplierId = ocsSupplier.id;
            vendorName = 'OCS Wholesale';
          }
        }
        // Add logic for other provinces as needed
      }

      // Prepare purchase order data matching API expectations
      const purchaseOrder = {
        supplier_id: finalSupplierId,
        store_id: currentStore?.id || undefined, // Include store_id in the request body
        items: poItems.map(item => {
          // Debug: Log the gtin_barcode being sent
          console.log(`Sending item ${item.sku}: gtin_barcode=${item.gtin_barcode}, case_gtin=${item.case_gtin}`);
          return {
            sku: item.sku,
            quantity: item.shipped_qty,  // Use shipped_qty as the quantity
            unit_cost: item.unit_cost,
            batch_lot: item.batch_lot,
            case_gtin: item.case_gtin,
            packaged_on_date: item.packaged_on_date || new Date().toISOString().split('T')[0],  // Use today if missing
            gtin_barcode: item.gtin_barcode,  // Required field
            each_gtin: item.each_gtin,
            vendor: item.vendor,  // Use vendor from above logic
            brand: item.brand || item.item_name || 'Unknown',  // Required
            shipped_qty: item.shipped_qty,  // Required
            uom: item.uom || 'EACH',  // Required with default
            uom_conversion: item.uom_conversion || 1,  // Required with default
            uom_conversion_qty: item.uom_conversion_qty || 1  // Required with default
          }
        }),
        expected_date: new Date().toISOString().split('T')[0], // Use today's date
        excel_filename: uploadedFileName || poNumber,  // Required for PO number generation
        notes: `PO Number: ${poNumber}
${notes ? `Notes: ${notes}` : ''}
Additional Charges: $${charges.toFixed(2)}
Discount: $${discount.toFixed(2)}
Total: $${totalAmount.toFixed(2)}
Payment Status: ${paidInFull ? 'Paid in Full' : 'Pending'}`  // Include all financial details in notes
      };

      const response = await fetch('http://localhost:5024/api/inventory/purchase-orders', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Store-ID': currentStore?.id || '',  // Ensure store ID is in header
          'X-Tenant-ID': currentStore?.tenant_id || ''
        },
        body: JSON.stringify(purchaseOrder),
      });
      
      if (!response.ok) {
        let errorMessage = 'Failed to create purchase order';
        try {
          const errorData = await response.json();
          console.error('Purchase order creation failed:', JSON.stringify(errorData, null, 2));
          errorMessage = errorData.detail || errorMessage;
        } catch (e) {
          console.error('Failed to parse error response');
        }
        throw new Error(errorMessage);
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
      console.error('Purchase order creation error:', error.message);
      setError(error.message);
    },
  });

  const handleCreatePO = () => {
    if (!poNumber) {
      setError('Please enter a PO Number');
      return;
    }
    // Check if we have a store selected
    if (!currentStore) {
      setError('Please select a store before creating a purchase order');
      return;
    }
    // Ensure we have OCS supplier
    if (!supplierId) {
      const ocsSupplier = suppliers.find((s: any) => 
        s.name?.toLowerCase().includes('ocs') || 
        s.name?.toLowerCase().includes('wholesale')
      );
      if (ocsSupplier) {
        setSupplierId(ocsSupplier.id);
      }
    }
    createPOMutation.mutate();
  };

  const handleClose = () => {
    setStep('upload');
    setAsnItems([]);
    setPoNumber('');
    setSupplierId('');
    setNotes('');
    setCharges(0);
    setDiscount(0);
    setPaidInFull(false);
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
                          {item.image_url && item.image_url !== 'null' && item.image_url !== 'undefined' ? (
                            <img 
                              src={item.image_url} 
                              alt={item.product_name || item.item_name || 'Product'}
                              className="h-12 w-12 object-cover rounded"
                              loading="eager"
                              onError={(e) => {
                                // If image fails to load, hide it and log the error
                                console.error(`Failed to load image for SKU ${item.sku}:`, item.image_url);
                                (e.target as HTMLImageElement).style.visibility = 'hidden';
                              }}
                            />
                          ) : (
                            <div className="h-12 w-12 bg-gray-100 rounded flex items-center justify-center text-xs text-gray-500">
                              {item.sku?.substring(0, 3)}
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
              
              {/* Store Selector - Show selector for non-store managers, show store name for store managers */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Store *
                </label>
                {isStoreManager() ? (
                  // For store managers, show their assigned store
                  currentStore ? (
                    <div className="px-3 py-2 border border-gray-300 rounded-md bg-gray-50">
                      {currentStore.name}
                    </div>
                  ) : (
                    <div className="px-3 py-2 border border-red-300 rounded-md bg-red-50 text-red-600">
                      No stores available
                    </div>
                  )
                ) : (
                  // For other roles, show the store selector
                  <StoreSelector className="w-full" showStats={false} />
                )}
                {!currentStore && (
                  <p className="mt-1 text-sm text-red-600">Please select a store</p>
                )}
              </div>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    PO Number *
                  </label>
                  <input
                    type="text"
                    value={poNumber}
                    onChange={(e) => setPoNumber(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
                    placeholder="ASN_SO005932532"
                  />
                </div>

                <div>
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
                              {item.image_url && item.image_url !== 'null' && item.image_url !== 'undefined' ? (
                                <img 
                                  src={item.image_url} 
                                  alt={item.item_name || 'Product'}
                                  className="h-10 w-10 object-cover rounded"
                                  loading="eager"
                                  onError={(e) => {
                                    // If image fails to load, hide it and log the error
                                    console.error(`Failed to load image for SKU ${item.sku}:`, item.image_url);
                                    (e.target as HTMLImageElement).style.visibility = 'hidden';
                                  }}
                                />
                              ) : (
                                <div className="h-10 w-10 bg-gray-100 rounded flex items-center justify-center text-xs text-gray-500">
                                  {item.sku?.substring(0, 3)}
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

              {/* Charges Section */}
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <h4 className="font-medium mb-3 text-yellow-900">Charges</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Additional Charges (e.g., shipping)
                    </label>
                    <input
                      type="number"
                      value={charges}
                      onChange={(e) => setCharges(parseFloat(e.target.value) || 0)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-500"
                      placeholder="0.00"
                      step="0.01"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Discount
                    </label>
                    <input
                      type="number"
                      value={discount}
                      onChange={(e) => setDiscount(parseFloat(e.target.value) || 0)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-500"
                      placeholder="0.00"
                      step="0.01"
                    />
                  </div>
                </div>
              </div>

              {/* Summary Section */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="font-medium mb-3">Summary</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Total Items:</span>
                    <span className="font-medium">{asnItems.length}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Total Quantity:</span>
                    <span className="font-medium">
                      {asnItems.reduce((sum, item) => sum + item.shipped_qty, 0)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Subtotal:</span>
                    <span className="font-medium">
                      ${asnItems.reduce((sum, item) => sum + (item.shipped_qty * item.unit_price), 0).toFixed(2)}
                    </span>
                  </div>
                  {charges > 0 && (
                    <div className="flex justify-between text-yellow-700">
                      <span>Additional Charges:</span>
                      <span className="font-medium">+${charges.toFixed(2)}</span>
                    </div>
                  )}
                  {discount > 0 && (
                    <div className="flex justify-between text-green-700">
                      <span>Discount:</span>
                      <span className="font-medium">-${discount.toFixed(2)}</span>
                    </div>
                  )}
                  <div className="border-t pt-2 flex justify-between font-bold text-base">
                    <span>Total:</span>
                    <span>
                      ${(asnItems.reduce((sum, item) => sum + (item.shipped_qty * item.unit_price), 0) + charges - discount).toFixed(2)}
                    </span>
                  </div>
                  
                  {/* Paid in Full Checkbox */}
                  <div className="border-t pt-3 mt-3">
                    <label className="flex items-center space-x-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={paidInFull}
                        onChange={(e) => setPaidInFull(e.target.checked)}
                        className="h-4 w-4 text-green-600 focus:ring-green-500 border-gray-300 rounded"
                      />
                      <span className="text-sm font-medium text-gray-700">Paid in Full</span>
                    </label>
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