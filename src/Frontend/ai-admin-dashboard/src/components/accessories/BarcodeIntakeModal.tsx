import React, { useState, useEffect, useRef } from 'react';
import {
  X, Scan, Loader2, Check, AlertCircle, Camera,
  Search, Package, DollarSign, Hash, Image
} from 'lucide-react';
import axios from 'axios';

interface BarcodeIntakeModalProps {
  isOpen: boolean;
  onClose: () => void;
  onComplete: (data: any) => void;
  storeId: string;
}

const BarcodeIntakeModal: React.FC<BarcodeIntakeModalProps> = ({
  isOpen,
  onClose,
  onComplete,
  storeId
}) => {
  const [barcode, setBarcode] = useState('');
  const [scanning, setScanning] = useState(false);
  const [scanResult, setScanResult] = useState<any>(null);
  const [error, setError] = useState('');
  const [manualEntry, setManualEntry] = useState(false);
  
  // Intake form fields
  const [quantity, setQuantity] = useState(1);
  const [costPrice, setCostPrice] = useState('');
  const [retailPrice, setRetailPrice] = useState('');
  const [location, setLocation] = useState('');
  
  const barcodeInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isOpen && barcodeInputRef.current) {
      barcodeInputRef.current.focus();
    }
  }, [isOpen]);

  // Handle barcode scan
  const handleScan = async () => {
    if (!barcode) {
      setError('Please enter a barcode');
      return;
    }

    setScanning(true);
    setError('');
    setScanResult(null);

    try {
      const response = await axios.post('http://localhost:5024/api/accessories/barcode/scan', {
        barcode,
        store_id: storeId,
        scan_type: 'intake'
      });

      setScanResult(response.data);
      
      // Pre-fill prices if found
      if (response.data.data) {
        if (response.data.data.price) {
          setRetailPrice(response.data.data.price.toString());
        }
        if (response.data.data.msrp) {
          setCostPrice((response.data.data.msrp * 0.5).toFixed(2)); // Assume 50% margin
        }
      }

      if (response.data.requires_manual_entry) {
        setManualEntry(true);
      }
    } catch (error) {
      console.error('Scan error:', error);
      setError('Failed to scan barcode. Please try again.');
    } finally {
      setScanning(false);
    }
  };

  // Handle intake submission
  const handleIntake = async () => {
    if (!scanResult || !costPrice || !retailPrice || quantity < 1) {
      setError('Please fill in all required fields');
      return;
    }

    try {
      const intakeData = {
        barcode,
        store_id: storeId,
        name: scanResult.data?.name || 'Unknown Product',
        brand: scanResult.data?.brand,
        category_id: scanResult.data?.category_id,
        quantity,
        cost_price: parseFloat(costPrice),
        retail_price: parseFloat(retailPrice),
        image_url: scanResult.data?.image_url,
        description: scanResult.data?.description,
        location,
        auto_create_catalog: true
      };

      const response = await axios.post(
        'http://localhost:5024/api/accessories/inventory/intake',
        intakeData
      );

      if (response.data.success) {
        onComplete(response.data);
        handleReset();
      }
    } catch (error) {
      console.error('Intake error:', error);
      setError('Failed to add item to inventory');
    }
  };

  // Reset form
  const handleReset = () => {
    setBarcode('');
    setScanResult(null);
    setQuantity(1);
    setCostPrice('');
    setRetailPrice('');
    setLocation('');
    setError('');
    setManualEntry(false);
  };

  // Handle enter key for quick scanning
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !scanning) {
      handleScan();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center gap-3">
            <Scan className="w-6 h-6 text-blue-600" />
            <h2 className="text-xl font-semibold">Barcode Intake</h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Barcode Input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Scan or Enter Barcode
            </label>
            <div className="flex gap-2">
              <input
                ref={barcodeInputRef}
                type="text"
                value={barcode}
                onChange={(e) => setBarcode(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Scan barcode or enter manually..."
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={scanning}
              />
              <button
                onClick={handleScan}
                disabled={scanning || !barcode}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {scanning ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Scanning...
                  </>
                ) : (
                  <>
                    <Search className="w-4 h-4" />
                    Lookup
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="flex items-center gap-2 p-3 bg-red-50 text-red-700 rounded-lg">
              <AlertCircle className="w-5 h-5" />
              <span>{error}</span>
            </div>
          )}

          {/* Scan Result */}
          {scanResult && (
            <div className="space-y-4">
              {/* Product Info */}
              <div className="p-4 bg-gray-50 rounded-lg">
                <div className="flex items-start gap-4">
                  {scanResult.data?.image_url ? (
                    <img
                      src={scanResult.data.image_url}
                      alt={scanResult.data.name}
                      className="w-20 h-20 object-cover rounded"
                    />
                  ) : (
                    <div className="w-20 h-20 bg-gray-200 rounded flex items-center justify-center">
                      <Package className="w-8 h-8 text-gray-400" />
                    </div>
                  )}
                  
                  <div className="flex-1">
                    <h3 className="font-semibold text-lg">
                      {scanResult.data?.name || 'Unknown Product'}
                    </h3>
                    {scanResult.data?.brand && (
                      <p className="text-sm text-gray-600">Brand: {scanResult.data.brand}</p>
                    )}
                    {scanResult.data?.description && (
                      <p className="text-sm text-gray-500 mt-1">{scanResult.data.description}</p>
                    )}
                    
                    <div className="flex items-center gap-4 mt-2">
                      <span className={`text-xs px-2 py-1 rounded ${
                        scanResult.confidence > 0.7 ? 'bg-green-100 text-green-700' :
                        scanResult.confidence > 0.4 ? 'bg-yellow-100 text-yellow-700' :
                        'bg-red-100 text-red-700'
                      }`}>
                        Confidence: {(scanResult.confidence * 100).toFixed(0)}%
                      </span>
                      <span className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded">
                        Source: {scanResult.source}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Intake Form */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Quantity *
                  </label>
                  <input
                    type="number"
                    value={quantity}
                    onChange={(e) => setQuantity(parseInt(e.target.value) || 0)}
                    min="1"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Location
                  </label>
                  <input
                    type="text"
                    value={location}
                    onChange={(e) => setLocation(e.target.value)}
                    placeholder="e.g., Shelf A1"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Cost Price *
                  </label>
                  <div className="relative">
                    <DollarSign className="absolute left-3 top-2.5 w-4 h-4 text-gray-400" />
                    <input
                      type="number"
                      value={costPrice}
                      onChange={(e) => setCostPrice(e.target.value)}
                      step="0.01"
                      placeholder="0.00"
                      className="w-full pl-9 pr-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Retail Price *
                  </label>
                  <div className="relative">
                    <DollarSign className="absolute left-3 top-2.5 w-4 h-4 text-gray-400" />
                    <input
                      type="number"
                      value={retailPrice}
                      onChange={(e) => setRetailPrice(e.target.value)}
                      step="0.01"
                      placeholder="0.00"
                      className="w-full pl-9 pr-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>
              </div>

              {/* Margin Calculation */}
              {costPrice && retailPrice && (
                <div className="p-3 bg-green-50 rounded-lg">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">Margin:</span>
                    <span className="font-medium text-green-700">
                      ${(parseFloat(retailPrice) - parseFloat(costPrice)).toFixed(2)} 
                      ({((parseFloat(retailPrice) - parseFloat(costPrice)) / parseFloat(retailPrice) * 100).toFixed(1)}%)
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-sm mt-1">
                    <span className="text-gray-600">Total Value:</span>
                    <span className="font-medium">
                      ${(quantity * parseFloat(retailPrice)).toFixed(2)}
                    </span>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Manual Entry Notice */}
          {manualEntry && (
            <div className="p-3 bg-yellow-50 text-yellow-800 rounded-lg">
              <p className="text-sm">
                Product not found in database. It will be added to the catalog when you complete the intake.
              </p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-between items-center p-6 border-t bg-gray-50">
          <button
            onClick={handleReset}
            className="px-4 py-2 text-gray-600 hover:text-gray-800"
          >
            Reset
          </button>
          
          <div className="flex gap-3">
            <button
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              onClick={handleIntake}
              disabled={!scanResult || !costPrice || !retailPrice}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              <Check className="w-4 h-4" />
              Add to Inventory
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BarcodeIntakeModal;