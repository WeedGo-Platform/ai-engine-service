import React, { useState, useRef } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Upload, X, CheckCircle, AlertCircle, FileSpreadsheet, TruckIcon, Loader2 } from 'lucide-react';
import * as XLSX from 'xlsx';
import { api } from '../services/api';

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
  uom?: string;
  uom_conversion?: number;
  uom_conversion_qty?: number;
  exists_in_inventory?: boolean;
}

interface ASNImportModalProps {
  isOpen: boolean;
  onClose: () => void;
  suppliers: any[];
}

const ASNImportModal: React.FC<ASNImportModalProps> = ({ isOpen, onClose, suppliers }) => {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const [step, setStep] = useState<'upload' | 'review' | 'create'>('upload');
  const [asnItems, setAsnItems] = useState<ASNItem[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingProgress, setProcessingProgress] = useState(0);
  
  // Form state for PO creation
  const [poNumber, setPoNumber] = useState('');
  const [supplierId, setSupplierId] = useState('');
  const [expectedDate, setExpectedDate] = useState('');
  const [notes, setNotes] = useState('');
  
  const [error, setError] = useState<string | null>(null);

  // Check if item exists in inventory (client-side API call)
  const checkInventoryExists = async (sku: string, batchLot?: string): Promise<boolean> => {
    try {
      const params = new URLSearchParams();
      params.append('sku', sku);
      if (batchLot) {
        params.append('batch_lot', batchLot);
      }
      
      const response = await fetch(`http://localhost:5024/api/inventory/check?${params.toString()}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        return data.exists || false;
      }
      return false;
    } catch (error) {
      console.error('Error checking inventory:', error);
      return false;
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
        const existsInInventory = await checkInventoryExists(sku, batchLot);
        
        // Parse the row data
        const item: ASNItem = {
          shipment_id: row.ShipmentID ? String(row.ShipmentID) : undefined,
          container_id: row.ContainerID ? String(row.ContainerID) : undefined,
          sku: sku,
          item_name: row.ItemName ? String(row.ItemName) : undefined,
          unit_price: parseFloat(row.UnitPrice) || 0,
          vendor: row.Vendor ? String(row.Vendor) : undefined,
          brand: row.Brand ? String(row.Brand) : undefined,
          case_gtin: row.CaseGTIN ? String(row.CaseGTIN) : undefined,
          packaged_on_date: row.PackagedOnDate ? String(row.PackagedOnDate) : undefined,
          batch_lot: batchLot,
          gtin_barcode: row.GTINBarCode ? String(row.GTINBarCode) : undefined,
          each_gtin: row.EachGTIN ? String(row.EachGTIN) : undefined,
          shipped_qty: parseInt(row.Shipped_Qty) || 0,
          uom: row.UOM ? String(row.UOM) : undefined,
          uom_conversion: parseFloat(row.UOMCONVERSION) || 1,
          uom_conversion_qty: parseInt(row.UOMCONVERSIONQTY) || 1,
          exists_in_inventory: existsInInventory
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

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
        setError('Please upload an Excel file (.xlsx or .xls)');
        return;
      }
      
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
        items: poItems.map(item => ({
          sku: item.sku,
          quantity: item.shipped_qty,  // Use shipped_qty as the quantity
          unit_cost: item.unit_cost,
          batch_lot: item.batch_lot,
          expiry_date: null  // Add if available in your data
        })),
        expected_date: expectedDate || null,
        notes: `PO Number: ${poNumber}${notes ? `\n${notes}` : ''}`  // Include PO number in notes
      };

      const response = await fetch('http://localhost:5024/api/inventory/purchase-orders', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(purchaseOrder),
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to create purchase order');
      }
      
      return response.json();
    },
    onSuccess: (data) => {
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
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">SKU</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Item Name</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Batch Lot</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Quantity</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Unit Price</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Total</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Vendor</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {asnItems.map((item, index) => (
                      <tr key={index} className={item.exists_in_inventory ? 'bg-blue-50' : ''}>
                        <td className="px-4 py-3 whitespace-nowrap">
                          {item.exists_in_inventory ? (
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
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm font-medium">{item.sku}</td>
                        <td className="px-4 py-3 text-sm">{item.item_name || '-'}</td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm">{item.batch_lot || '-'}</td>
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
                    rows={3}
                    placeholder="Additional notes..."
                  />
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