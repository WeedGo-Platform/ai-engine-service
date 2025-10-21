import React, { useState, useRef } from 'react';
import { X, Camera, Upload, Loader2, Check, AlertCircle, Sparkles } from 'lucide-react';
import axios from 'axios';
import { getApiEndpoint } from '../../config/app.config';

interface OCRScanModalProps {
  isOpen: boolean;
  onClose: () => void;
  onComplete: (data: any) => void;
  storeId: number;
  categories: Array<{ id: number; name: string; slug: string; icon: string }>;
}

interface ExtractedData {
  product_name?: string;
  brand?: string;
  sku?: string;
  barcode?: string;
  price?: string;
  quantity?: string;
  description?: string;
  category?: string;
  size_variant?: string;
}

interface ExtractionResult {
  extracted_data: ExtractedData;
  confidence_scores: Record<string, number>;
  overall_confidence: number;
  validation_passed: boolean;
  requires_manual_review: boolean;
  provider_used: string;
}

const OCRScanModal: React.FC<OCRScanModalProps> = ({
  isOpen,
  onClose,
  onComplete,
  storeId,
  categories
}) => {
  const [step, setStep] = useState<'upload' | 'processing' | 'review'>('upload');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string>('');
  const [extractedData, setExtractedData] = useState<ExtractedData>({});
  const [extractionResult, setExtractionResult] = useState<ExtractionResult | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState('');

  // Form state for review/edit
  const [formData, setFormData] = useState({
    name: '',
    brand: '',
    sku: '',
    barcode: '',
    category_id: '',
    cost_price: '',
    retail_price: '',
    quantity: '1',
    location: '',
    description: ''
  });

  const fileInputRef = useRef<HTMLInputElement>(null);
  const cameraInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  // Handle file selection
  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setError('');

      // Create preview
      const reader = new FileReader();
      reader.onload = (e) => {
        setImagePreview(e.target?.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  // Process image with OCR
  const processImage = async () => {
    if (!selectedFile) {
      setError('Please select an image first');
      return;
    }

    setIsProcessing(true);
    setError('');
    setStep('processing');

    try {
      // Convert image to base64
      const base64Image = await new Promise<string>((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => {
          if (typeof reader.result === 'string') {
            // Remove data URL prefix (data:image/png;base64,)
            const base64 = reader.result.split(',')[1];
            resolve(base64);
          } else {
            reject(new Error('Failed to read image as base64'));
          }
        };
        reader.onerror = () => reject(reader.error);
        reader.readAsDataURL(selectedFile);
      });

      // Call OCR API with JSON payload
      const response = await axios.post<ExtractionResult>(
        getApiEndpoint('/accessories/ocr/extract'),
        {
          image_data: base64Image,
          store_id: storeId.toString(),
          document_type: 'label'
        },
        {
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      const result = response.data;
      setExtractionResult(result);
      setExtractedData(result.extracted_data);

      // Populate form with extracted data
      setFormData({
        name: result.extracted_data.product_name || '',
        brand: result.extracted_data.brand || '',
        sku: result.extracted_data.sku || '',
        barcode: result.extracted_data.barcode || '',
        category_id: findCategoryId(result.extracted_data.category || ''),
        cost_price: '',  // OCR doesn't extract cost, only retail
        retail_price: result.extracted_data.price || '',
        quantity: result.extracted_data.quantity || '1',
        location: '',
        description: result.extracted_data.description || ''
      });

      setStep('review');

    } catch (err: any) {
      console.error('OCR extraction error:', err);
      setError(err.response?.data?.error || 'Failed to extract data from image');
      setStep('upload');
    } finally {
      setIsProcessing(false);
    }
  };

  // Find category ID by name
  const findCategoryId = (categoryName: string): string => {
    const category = categories.find(
      cat => cat.name.toLowerCase() === categoryName.toLowerCase() ||
             cat.slug === categoryName.toLowerCase()
    );
    return category ? category.id.toString() : '';
  };

  // Submit accessory
  const handleSubmit = async () => {
    try {
      setIsProcessing(true);
      setError('');

      // Validate required fields
      if (!formData.name || !formData.retail_price) {
        setError('Product name and retail price are required');
        return;
      }

      // Create accessory
      await axios.post(getApiEndpoint('/accessories/inventory'), {
        ...formData,
        store_id: storeId,
        quantity: parseInt(formData.quantity) || 1,
        cost_price: parseFloat(formData.cost_price) || 0,
        retail_price: parseFloat(formData.retail_price) || 0,
        category_id: formData.category_id ? parseInt(formData.category_id) : null,
      });

      onComplete({ success: true, data: formData });
      handleClose();

    } catch (err: any) {
      console.error('Error creating accessory:', err);
      setError(err.response?.data?.error || 'Failed to create accessory');
    } finally {
      setIsProcessing(false);
    }
  };

  // Close modal and reset
  const handleClose = () => {
    setStep('upload');
    setSelectedFile(null);
    setImagePreview('');
    setExtractedData({});
    setExtractionResult(null);
    setError('');
    setFormData({
      name: '',
      brand: '',
      sku: '',
      barcode: '',
      category_id: '',
      cost_price: '',
      retail_price: '',
      quantity: '1',
      location: '',
      description: ''
    });
    onClose();
  };

  // Get confidence color
  const getConfidenceColor = (score: number) => {
    if (score >= 0.80) return 'text-green-600 dark:text-green-400';
    if (score >= 0.60) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-red-600 dark:text-red-400';
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 dark:bg-opacity-70 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4 flex items-center justify-between z-10">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-purple-100 dark:bg-purple-900/30 rounded-lg flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-purple-600 dark:text-purple-400" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                OCR Photo Scan
              </h2>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Extract product details from photo
              </p>
            </div>
          </div>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
            disabled={isProcessing}
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {/* Upload Step */}
          {step === 'upload' && (
            <div className="space-y-6">
              {/* Image Preview */}
              {imagePreview ? (
                <div className="relative">
                  <img
                    src={imagePreview}
                    alt="Product preview"
                    className="w-full h-64 object-contain rounded-lg border-2 border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900"
                  />
                  <button
                    onClick={() => {
                      setSelectedFile(null);
                      setImagePreview('');
                    }}
                    className="absolute top-2 right-2 p-1.5 bg-red-500 text-white rounded-full hover:bg-red-600"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ) : (
                <div className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-12 text-center">
                  <Camera className="w-16 h-16 mx-auto text-gray-400 dark:text-gray-500 mb-4" />
                  <p className="text-gray-600 dark:text-gray-300 mb-2">
                    Upload or capture product photo
                  </p>
                  <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
                    Supports JPG, PNG (max 10MB)
                  </p>
                </div>
              )}

              {/* Upload Buttons */}
              <div className="grid grid-cols-2 gap-4">
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="flex items-center justify-center gap-2 px-4 py-3 bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                >
                  <Upload className="w-5 h-5" />
                  <span>Choose File</span>
                </button>
                <button
                  onClick={() => cameraInputRef.current?.click()}
                  className="flex items-center justify-center gap-2 px-4 py-3 bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                >
                  <Camera className="w-5 h-5" />
                  <span>Take Photo</span>
                </button>
              </div>

              {/* Hidden file inputs */}
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handleFileSelect}
                className="hidden"
              />
              <input
                ref={cameraInputRef}
                type="file"
                accept="image/*"
                capture="environment"
                onChange={handleFileSelect}
                className="hidden"
              />

              {/* Error */}
              {error && (
                <div className="flex items-center gap-2 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                  <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0" />
                  <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
                </div>
              )}

              {/* Process Button */}
              <button
                onClick={processImage}
                disabled={!selectedFile || isProcessing}
                className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-purple-600 dark:bg-purple-700 text-white rounded-lg hover:bg-purple-700 dark:hover:bg-purple-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <Sparkles className="w-5 h-5" />
                <span>Extract Data with AI</span>
              </button>
            </div>
          )}

          {/* Processing Step */}
          {step === 'processing' && (
            <div className="flex flex-col items-center justify-center py-12">
              <Loader2 className="w-16 h-16 text-purple-600 dark:text-purple-400 animate-spin mb-4" />
              <p className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                Extracting product details...
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                This may take a few seconds
              </p>
            </div>
          )}

          {/* Review Step */}
          {step === 'review' && extractionResult && (
            <div className="space-y-6">
              {/* Confidence Score */}
              <div className="bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-900 dark:text-white">
                    Extraction Confidence
                  </span>
                  <span className={`text-lg font-bold ${getConfidenceColor(extractionResult.overall_confidence)}`}>
                    {(extractionResult.overall_confidence * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="flex items-center gap-2 text-xs text-gray-600 dark:text-gray-400">
                  <Sparkles className="w-4 h-4" />
                  <span>Processed by {extractionResult.provider_used}</span>
                </div>
                {extractionResult.requires_manual_review && (
                  <div className="mt-2 flex items-center gap-2 text-xs text-yellow-600 dark:text-yellow-400">
                    <AlertCircle className="w-4 h-4" />
                    <span>Please review and verify extracted data</span>
                  </div>
                )}
              </div>

              {/* Image Preview (small) */}
              {imagePreview && (
                <img
                  src={imagePreview}
                  alt="Product"
                  className="w-full h-32 object-contain rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900"
                />
              )}

              {/* Form */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Product Name */}
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Product Name *
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 dark:focus:ring-purple-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    placeholder="e.g., RAW King Size Rolling Papers"
                  />
                </div>

                {/* Brand */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Brand
                  </label>
                  <input
                    type="text"
                    value={formData.brand}
                    onChange={(e) => setFormData({ ...formData, brand: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 dark:focus:ring-purple-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  />
                </div>

                {/* Category */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Category
                  </label>
                  <select
                    value={formData.category_id}
                    onChange={(e) => setFormData({ ...formData, category_id: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 dark:focus:ring-purple-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  >
                    <option value="">Select category</option>
                    {categories.map(cat => (
                      <option key={cat.id} value={cat.id}>
                        {cat.icon} {cat.name}
                      </option>
                    ))}
                  </select>
                </div>

                {/* SKU */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    SKU
                  </label>
                  <input
                    type="text"
                    value={formData.sku}
                    onChange={(e) => setFormData({ ...formData, sku: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 dark:focus:ring-purple-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  />
                </div>

                {/* Barcode */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Barcode
                  </label>
                  <input
                    type="text"
                    value={formData.barcode}
                    onChange={(e) => setFormData({ ...formData, barcode: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 dark:focus:ring-purple-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  />
                </div>

                {/* Cost Price */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Cost Price
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={formData.cost_price}
                    onChange={(e) => setFormData({ ...formData, cost_price: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 dark:focus:ring-purple-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    placeholder="0.00"
                  />
                </div>

                {/* Retail Price */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Retail Price *
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={formData.retail_price}
                    onChange={(e) => setFormData({ ...formData, retail_price: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 dark:focus:ring-purple-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    placeholder="0.00"
                  />
                </div>

                {/* Quantity */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Quantity
                  </label>
                  <input
                    type="number"
                    value={formData.quantity}
                    onChange={(e) => setFormData({ ...formData, quantity: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 dark:focus:ring-purple-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  />
                </div>

                {/* Location */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Location
                  </label>
                  <input
                    type="text"
                    value={formData.location}
                    onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 dark:focus:ring-purple-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    placeholder="e.g., Shelf A3"
                  />
                </div>

                {/* Description */}
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Description
                  </label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    rows={2}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 dark:focus:ring-purple-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  />
                </div>
              </div>

              {/* Error */}
              {error && (
                <div className="flex items-center gap-2 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                  <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0" />
                  <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex flex-col-reverse sm:flex-row gap-3">
                <button
                  onClick={() => setStep('upload')}
                  disabled={isProcessing}
                  className="flex-1 px-6 py-3 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 transition-colors"
                >
                  Scan Another
                </button>
                <button
                  onClick={handleSubmit}
                  disabled={isProcessing || !formData.name || !formData.retail_price}
                  className="flex-1 flex items-center justify-center gap-2 px-6 py-3 bg-purple-600 dark:bg-purple-700 text-white rounded-lg hover:bg-purple-700 dark:hover:bg-purple-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {isProcessing ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      <span>Saving...</span>
                    </>
                  ) : (
                    <>
                      <Check className="w-5 h-5" />
                      <span>Add to Inventory</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default OCRScanModal;
