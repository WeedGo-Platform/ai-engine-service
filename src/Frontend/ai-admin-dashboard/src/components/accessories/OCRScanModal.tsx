import React, { useState, useRef, useCallback, useMemo } from 'react';
import { X, Camera, Upload, Loader2, Check, AlertCircle, Sparkles, Crop, RotateCw } from 'lucide-react';
import axios from 'axios';
import { getApiEndpoint } from '../../config/app.config';
import Cropper from 'react-easy-crop';
import { Area } from 'react-easy-crop/types';
import { getSubcategoriesForCategory, getCategorySlug } from '../../constants/subcategories';

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
  success: boolean;
  extracted_data: ExtractedData & {
    confidence?: number;
    provider?: string;
    extraction_time?: number;
  };
  confidence: number;
  requires_review: boolean;
}

const OCRScanModal: React.FC<OCRScanModalProps> = ({
  isOpen,
  onClose,
  onComplete,
  storeId,
  categories
}) => {
  const [step, setStep] = useState<'upload' | 'processing' | 'review'>('upload');
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [imagePreviews, setImagePreviews] = useState<string[]>([]);
  const [extractedData, setExtractedData] = useState<ExtractedData>({});
  const [extractionResult, setExtractionResult] = useState<ExtractionResult | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentProcessingIndex, setCurrentProcessingIndex] = useState(0);
  const [error, setError] = useState('');
  const [showCamera, setShowCamera] = useState(false);
  const [cameraStream, setCameraStream] = useState<MediaStream | null>(null);
  const [showCropper, setShowCropper] = useState(false);
  const [currentCropImage, setCurrentCropImage] = useState<string>('');
  const [currentCropIndex, setCurrentCropIndex] = useState<number>(-1);
  const [crop, setCrop] = useState({ x: 0, y: 0 });
  const [zoom, setZoom] = useState(1);
  const [rotation, setRotation] = useState(0);
  const [croppedAreaPixels, setCroppedAreaPixels] = useState<Area | null>(null);

  // Form state for review/edit
  const [formData, setFormData] = useState({
    name: '',
    brand: '',
    category_id: '',
    subcategory: '',
    sku: '',
    barcode: '',
    size_variant: '',
    cost_price: '',
    retail_price: '',
    quantity: '',
    location: '',
    description: ''
  });

  // Get available subcategories based on selected category
  const availableSubcategories = useMemo(() => {
    if (!formData.category_id) return [];
    const slug = getCategorySlug(formData.category_id, categories);
    return getSubcategoriesForCategory(slug);
  }, [formData.category_id, categories]);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  if (!isOpen) return null;

  // Handle file selection (multiple files)
  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || []);
    if (files.length > 0) {
      setSelectedFiles(prev => [...prev, ...files]);
      setError('');

      // Create previews for all files
      files.forEach(file => {
        const reader = new FileReader();
        reader.onload = (e) => {
          setImagePreviews(prev => [...prev, e.target?.result as string]);
        };
        reader.readAsDataURL(file);
      });
    }
  };

  // Remove a specific image
  const removeImage = (index: number) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
    setImagePreviews(prev => prev.filter((_, i) => i !== index));
  };

  // Open camera
  const openCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment' } // Use rear camera on mobile
      });
      setCameraStream(stream);
      setShowCamera(true);
      
      // Wait for video element to be ready
      setTimeout(() => {
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
      }, 100);
    } catch (err) {
      console.error('Camera access error:', err);
      setError('Unable to access camera. Please grant camera permissions or use file upload.');
    }
  };

  // Close camera and stop stream
  const closeCamera = () => {
    if (cameraStream) {
      cameraStream.getTracks().forEach(track => track.stop());
      setCameraStream(null);
    }
    setShowCamera(false);
  };

  // Capture photo from camera
  const capturePhoto = () => {
    if (videoRef.current && canvasRef.current) {
      const video = videoRef.current;
      const canvas = canvasRef.current;
      
      // Set canvas size to match video
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      
      // Draw current video frame to canvas
      const ctx = canvas.getContext('2d');
      if (ctx) {
        ctx.drawImage(video, 0, 0);
        
        // Convert canvas to blob and create file
        canvas.toBlob((blob) => {
          if (blob) {
            const file = new File([blob], `camera-${Date.now()}.jpg`, { type: 'image/jpeg' });
            setSelectedFiles(prev => [...prev, file]);
            
            // Create preview
            const reader = new FileReader();
            reader.onload = (e) => {
              setImagePreviews(prev => [...prev, e.target?.result as string]);
            };
            reader.readAsDataURL(file);
            
            // Close camera after capture
            closeCamera();
          }
        }, 'image/jpeg', 0.95);
      }
    }
  };

  // Open cropper for an image
  const openCropper = (index: number) => {
    setCurrentCropImage(imagePreviews[index]);
    setCurrentCropIndex(index);
    setCrop({ x: 0, y: 0 });
    setZoom(1);
    setRotation(0);
    setShowCropper(true);
  };

  // Handle crop complete
  const onCropComplete = useCallback((croppedArea: Area, croppedAreaPixels: Area) => {
    setCroppedAreaPixels(croppedAreaPixels);
  }, []);

  // Create cropped image
  const createCroppedImage = async (imageSrc: string, pixelCrop: Area, rotation: number = 0): Promise<Blob | null> => {
    const image = new Image();
    image.src = imageSrc;
    
    return new Promise((resolve) => {
      image.onload = () => {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        
        if (!ctx) {
          resolve(null);
          return;
        }

        const maxSize = Math.max(image.width, image.height);
        const safeArea = 2 * ((maxSize / 2) * Math.sqrt(2));

        canvas.width = safeArea;
        canvas.height = safeArea;

        ctx.translate(safeArea / 2, safeArea / 2);
        ctx.rotate((rotation * Math.PI) / 180);
        ctx.translate(-safeArea / 2, -safeArea / 2);

        ctx.drawImage(
          image,
          safeArea / 2 - image.width * 0.5,
          safeArea / 2 - image.height * 0.5
        );

        const data = ctx.getImageData(0, 0, safeArea, safeArea);

        canvas.width = pixelCrop.width;
        canvas.height = pixelCrop.height;

        ctx.putImageData(
          data,
          0 - safeArea / 2 + image.width * 0.5 - pixelCrop.x,
          0 - safeArea / 2 + image.height * 0.5 - pixelCrop.y
        );

        canvas.toBlob((blob) => {
          resolve(blob);
        }, 'image/jpeg', 0.95);
      };
    });
  };

  // Apply crop
  const applyCrop = async () => {
    if (!croppedAreaPixels || currentCropIndex === -1) return;

    try {
      const croppedBlob = await createCroppedImage(
        currentCropImage,
        croppedAreaPixels,
        rotation
      );

      if (croppedBlob) {
        // Create new file from cropped blob
        const croppedFile = new File(
          [croppedBlob],
          `cropped-${Date.now()}.jpg`,
          { type: 'image/jpeg' }
        );

        // Update the file and preview at the current index
        setSelectedFiles(prev => {
          const newFiles = [...prev];
          newFiles[currentCropIndex] = croppedFile;
          return newFiles;
        });

        // Create new preview
        const reader = new FileReader();
        reader.onload = (e) => {
          setImagePreviews(prev => {
            const newPreviews = [...prev];
            newPreviews[currentCropIndex] = e.target?.result as string;
            return newPreviews;
          });
        };
        reader.readAsDataURL(croppedFile);

        // Close cropper
        setShowCropper(false);
        setCurrentCropIndex(-1);
        setCurrentCropImage('');
      }
    } catch (error) {
      console.error('Crop error:', error);
      setError('Failed to crop image');
    }
  };

  // Merge extracted data from multiple images
  const mergeExtractedData = (existing: ExtractedData, newData: ExtractedData, existingConfidence: number, newConfidence: number): ExtractedData => {
    const merged = { ...existing };
    
    // Merge strategy: Smart merging based on field type and confidence
    Object.keys(newData).forEach((key) => {
      const newValue = newData[key as keyof ExtractedData];
      const existingValue = merged[key as keyof ExtractedData];
      
      // If field doesn't exist yet, take the new value
      if (!existingValue && newValue) {
        (merged as any)[key] = newValue;
        return;
      }
      
      // If new value is empty, keep existing
      if (!newValue) {
        return;
      }
      
      // Special handling for barcode - prefer valid UPC/EAN format
      if (key === 'barcode' && typeof newValue === 'string' && typeof existingValue === 'string') {
        const newIsValid = /^\d{12,13}$/.test(newValue);
        const existingIsValid = /^\d{12,13}$/.test(existingValue);
        
        // If new is valid and existing isn't, take new
        if (newIsValid && !existingIsValid) {
          (merged as any)[key] = newValue;
        }
        // If both valid or both invalid, prefer the one with higher confidence
        else if (newConfidence > existingConfidence) {
          (merged as any)[key] = newValue;
        }
        return;
      }
      
      // For other fields, prefer longer/more complete values, but consider confidence
      if (typeof newValue === 'string' && typeof existingValue === 'string') {
        // If new value is significantly longer (20% or more), take it
        if (newValue.length > existingValue.length * 1.2) {
          (merged as any)[key] = newValue;
        }
        // If lengths similar, prefer higher confidence extraction
        else if (Math.abs(newValue.length - existingValue.length) < existingValue.length * 0.2 && newConfidence > existingConfidence) {
          (merged as any)[key] = newValue;
        }
      } else if (newValue && !existingValue) {
        (merged as any)[key] = newValue;
      }
    });
    
    return merged;
  };

  // Process all images with OCR
  const processImages = async () => {
    if (selectedFiles.length === 0) {
      setError('Please select at least one image');
      return;
    }

    setIsProcessing(true);
    setError('');
    setStep('processing');

    let mergedData: ExtractedData = {};
    let highestConfidence = 0;
    let bestProvider = '';

    try {
      // Process each image sequentially
      for (let i = 0; i < selectedFiles.length; i++) {
        setCurrentProcessingIndex(i);
        const file = selectedFiles[i];

        // Convert image to base64
        const base64Image = await new Promise<string>((resolve, reject) => {
          const reader = new FileReader();
          reader.onload = () => {
            if (typeof reader.result === 'string') {
              const base64 = reader.result.split(',')[1];
              resolve(base64);
            } else {
              reject(new Error('Failed to read image as base64'));
            }
          };
          reader.onerror = () => reject(reader.error);
          reader.readAsDataURL(file);
        });

        // Call OCR API
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
        
        // DEBUG: Log what we received
        console.log(`🔍 Image ${i + 1} response:`, {
          barcode: result.extracted_data?.barcode,
          product_name: result.extracted_data?.product_name,
          confidence: result.confidence
        });
        
        // Merge data from this image with accumulated data
        const currentConfidence = result.confidence || 0;
        mergedData = mergeExtractedData(mergedData, result.extracted_data, highestConfidence, currentConfidence);
        
        // DEBUG: Log merged data
        console.log(`🔍 After merge:`, {
          barcode: mergedData.barcode,
          product_name: mergedData.product_name
        });
        
        // Track highest confidence
        if (currentConfidence > highestConfidence) {
          highestConfidence = currentConfidence;
          bestProvider = result.extracted_data.provider || '';
        }
      }

      // Create final result with merged data
      const finalResult: ExtractionResult = {
        success: highestConfidence > 0,
        extracted_data: mergedData,
        confidence: highestConfidence,
        requires_review: highestConfidence < 0.8
      };

      setExtractionResult(finalResult);
      setExtractedData(mergedData);

      // Populate form with merged extracted data
      setFormData({
        name: mergedData.product_name || '',
        brand: mergedData.brand || '',
        sku: mergedData.sku || '',
        barcode: mergedData.barcode || '',
        size_variant: mergedData.size_variant || '',
        category_id: findCategoryId(mergedData.category || ''),
        subcategory: '',
        cost_price: '',
        retail_price: mergedData.price || '',
        quantity: mergedData.quantity || '1',
        location: '',
        description: mergedData.description || ''
      });

      setStep('review');

    } catch (err: any) {
      console.error('OCR extraction error:', err);
      setError(err.response?.data?.error || 'Failed to extract data from images');
      setStep('upload');
    } finally {
      setIsProcessing(false);
      setCurrentProcessingIndex(0);
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
        subcategory: formData.subcategory || null,
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
    setSelectedFiles([]);
    setImagePreviews([]);
    setExtractedData({});
    setExtractionResult(null);
    setError('');
    setCurrentProcessingIndex(0);
    setFormData({
      name: '',
      brand: '',
      sku: '',
      barcode: '',
      size_variant: '',
      category_id: '',
      subcategory: '',
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
              {/* Help Text */}
              <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                <p className="text-sm text-blue-800 dark:text-blue-200">
                  📸 <strong>Tip:</strong> Capture multiple angles (front, back, sides) for complete product details. We'll combine all information automatically.
                </p>
              </div>

              {/* Image Previews Grid */}
              {imagePreviews.length > 0 ? (
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
                      {imagePreviews.length} image{imagePreviews.length !== 1 ? 's' : ''} selected
                    </p>
                    <button
                      onClick={() => {
                        setSelectedFiles([]);
                        setImagePreviews([]);
                      }}
                      className="text-sm text-red-600 dark:text-red-400 hover:underline"
                    >
                      Clear all
                    </button>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    {imagePreviews.map((preview, index) => (
                      <div key={index} className="relative group">
                        <img
                          src={preview}
                          alt={`Product ${index + 1}`}
                          className="w-full h-32 object-cover rounded-lg border-2 border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900"
                        />
                        <div className="absolute top-1 left-1 px-2 py-0.5 bg-black bg-opacity-60 text-white text-xs rounded">
                          {index + 1}
                        </div>
                        <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-40 transition-opacity rounded-lg flex items-center justify-center gap-2">
                          <button
                            onClick={() => openCropper(index)}
                            className="p-2 bg-blue-500 text-white rounded-full hover:bg-blue-600 opacity-0 group-hover:opacity-100 transition-opacity shadow-lg"
                            title="Crop image"
                          >
                            <Crop className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => removeImage(index)}
                            className="p-2 bg-red-500 text-white rounded-full hover:bg-red-600 opacity-0 group-hover:opacity-100 transition-opacity shadow-lg"
                            title="Remove image"
                          >
                            <X className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-12 text-center">
                  <Camera className="w-16 h-16 mx-auto text-gray-400 dark:text-gray-500 mb-4" />
                  <p className="text-gray-600 dark:text-gray-300 mb-2">
                    Upload or capture product photos
                  </p>
                  <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
                    Multiple images recommended • JPG, PNG (max 10MB each)
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
                  <span>Add Photos</span>
                </button>
                <button
                  onClick={openCamera}
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
                multiple
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
                onClick={processImages}
                disabled={selectedFiles.length === 0 || isProcessing}
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
                Processing image {currentProcessingIndex + 1} of {selectedFiles.length}
              </p>
              <div className="w-64 h-2 bg-gray-200 dark:bg-gray-700 rounded-full mt-4 overflow-hidden">
                <div
                  className="h-full bg-purple-600 dark:bg-purple-500 transition-all duration-300"
                  style={{ width: `${((currentProcessingIndex + 1) / selectedFiles.length) * 100}%` }}
                />
              </div>
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
                  <span className={`text-lg font-bold ${getConfidenceColor(extractionResult.confidence)}`}>
                    {(extractionResult.confidence * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="flex items-center gap-2 text-xs text-gray-600 dark:text-gray-400">
                  <Sparkles className="w-4 h-4" />
                  <span>Processed {imagePreviews.length} image{imagePreviews.length !== 1 ? 's' : ''} • {extractionResult.extracted_data.provider || 'Unknown'}</span>
                </div>
                {extractionResult.requires_review && (
                  <div className="mt-2 flex items-center gap-2 text-xs text-yellow-600 dark:text-yellow-400">
                    <AlertCircle className="w-4 h-4" />
                    <span>Please review and verify extracted data</span>
                  </div>
                )}
              </div>

              {/* Image Gallery (thumbnails) */}
              {imagePreviews.length > 0 && (
                <div>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">
                    Captured from {imagePreviews.length} angle{imagePreviews.length !== 1 ? 's' : ''}:
                  </p>
                  <div className="flex gap-2 overflow-x-auto pb-2">
                    {imagePreviews.map((preview, index) => (
                      <div key={index} className="relative flex-shrink-0">
                        <img
                          src={preview}
                          alt={`Angle ${index + 1}`}
                          className="w-20 h-20 object-cover rounded border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900"
                        />
                        <div className="absolute bottom-0 right-0 px-1.5 py-0.5 bg-black bg-opacity-70 text-white text-xs rounded-tl">
                          {index + 1}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
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
                    onChange={(e) => setFormData({ ...formData, category_id: e.target.value, subcategory: '' })}
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

                {/* Subcategory */}
                {formData.category_id && availableSubcategories.length > 0 && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Subcategory
                    </label>
                    <select
                      value={formData.subcategory}
                      onChange={(e) => setFormData({ ...formData, subcategory: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 dark:focus:ring-purple-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    >
                      <option value="">Select subcategory (optional)</option>
                      {availableSubcategories.map(subcat => (
                        <option key={subcat} value={subcat}>
                          {subcat}
                        </option>
                      ))}
                    </select>
                  </div>
                )}

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

                {/* Size/Variant */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Size / Variant
                  </label>
                  <input
                    type="text"
                    value={formData.size_variant}
                    onChange={(e) => setFormData({ ...formData, size_variant: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 dark:focus:ring-purple-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    placeholder="e.g., King Size, 1¼, 25 packs"
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

      {/* Camera Modal */}
      {showCamera && (
        <div className="fixed inset-0 bg-black bg-opacity-90 z-[60] flex items-center justify-center">
          <div className="relative w-full h-full flex flex-col">
            {/* Camera Header */}
            <div className="absolute top-0 left-0 right-0 z-10 flex items-center justify-between p-4 bg-gradient-to-b from-black/50 to-transparent">
              <h3 className="text-white text-lg font-semibold">Take Photo</h3>
              <button
                onClick={closeCamera}
                className="p-2 bg-white/10 hover:bg-white/20 rounded-full transition-colors"
              >
                <X className="w-6 h-6 text-white" />
              </button>
            </div>

            {/* Camera Video */}
            <div className="flex-1 flex items-center justify-center">
              <video
                ref={videoRef}
                autoPlay
                playsInline
                className="max-w-full max-h-full object-contain"
              />
            </div>

            {/* Capture Button */}
            <div className="absolute bottom-0 left-0 right-0 p-6 bg-gradient-to-t from-black/50 to-transparent">
              <div className="flex justify-center">
                <button
                  onClick={capturePhoto}
                  className="w-16 h-16 bg-white rounded-full border-4 border-white shadow-lg hover:scale-110 transition-transform active:scale-95"
                >
                  <div className="w-full h-full rounded-full bg-white" />
                </button>
              </div>
              <p className="text-white text-center mt-4 text-sm">
                Position the product clearly and tap to capture
              </p>
            </div>

            {/* Hidden canvas for capture */}
            <canvas ref={canvasRef} className="hidden" />
          </div>
        </div>
      )}

      {/* Image Cropper Modal */}
      {showCropper && (
        <div className="fixed inset-0 bg-black bg-opacity-95 z-[70] flex flex-col">
          {/* Cropper Header */}
          <div className="flex items-center justify-between p-4 bg-black bg-opacity-50">
            <h3 className="text-white text-lg font-semibold">Crop Image</h3>
            <div className="flex items-center gap-3">
              <button
                onClick={() => setRotation((prev) => (prev + 90) % 360)}
                className="p-2 bg-white/10 hover:bg-white/20 rounded-lg transition-colors"
                title="Rotate 90°"
              >
                <RotateCw className="w-5 h-5 text-white" />
              </button>
              <button
                onClick={() => {
                  setShowCropper(false);
                  setCurrentCropIndex(-1);
                  setCurrentCropImage('');
                }}
                className="p-2 bg-white/10 hover:bg-white/20 rounded-lg transition-colors"
              >
                <X className="w-5 h-5 text-white" />
              </button>
            </div>
          </div>

          {/* Cropper Area */}
          <div className="flex-1 relative">
            <Cropper
              image={currentCropImage}
              crop={crop}
              zoom={zoom}
              rotation={rotation}
              aspect={undefined}
              onCropChange={setCrop}
              onCropComplete={onCropComplete}
              onZoomChange={setZoom}
              objectFit="contain"
              showGrid={true}
              restrictPosition={false}
            />
          </div>

          {/* Cropper Controls */}
          <div className="bg-black bg-opacity-50 p-6 space-y-4">
            {/* Zoom Slider */}
            <div>
              <label className="block text-white text-sm mb-2">Zoom</label>
              <input
                type="range"
                min={1}
                max={3}
                step={0.1}
                value={zoom}
                onChange={(e) => setZoom(parseFloat(e.target.value))}
                className="w-full"
              />
            </div>

            {/* Action Buttons */}
            <div className="flex gap-3">
              <button
                onClick={() => {
                  setShowCropper(false);
                  setCurrentCropIndex(-1);
                  setCurrentCropImage('');
                }}
                className="flex-1 px-4 py-3 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={applyCrop}
                className="flex-1 px-4 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium"
              >
                Apply Crop
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default OCRScanModal;
