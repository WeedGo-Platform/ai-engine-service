import { endpoints } from '../config/endpoints';
import { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, FileJson, FileText, X, AlertCircle, CheckCircle, Eye } from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import axios from 'axios';
import toast from 'react-hot-toast';

interface DatasetExample {
  query: string;
  expected_intent: string;
  expected_response?: string;
  entities?: Record<string, any>;
  products?: string[];
  context?: Record<string, any>;
}

interface DatasetMetadata {
  name: string;
  description: string;
  type: 'conversations' | 'products' | 'intents' | 'slang' | 'medical' | 'custom';
  version: string;
  author: string;
}

interface ParsedDataset {
  metadata: DatasetMetadata;
  examples: DatasetExample[];
  validation: {
    isValid: boolean;
    errors: string[];
    warnings: string[];
    stats: {
      totalExamples: number;
      validExamples: number;
      uniqueIntents: string[];
      coverage: Record<string, number>;
    };
  };
}

interface DatasetUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUploadSuccess: (dataset: any) => void;
}

const DATASET_TEMPLATES = {
  conversations: {
    name: 'Conversation Training',
    description: 'Train the AI on customer conversations',
    example: {
      metadata: {
        name: 'Customer Conversations v1',
        description: 'Real customer interaction examples',
        type: 'conversations',
        version: '1.0',
        author: 'Training Team'
      },
      examples: [
        {
          query: "I'm looking for something to help me sleep",
          expected_intent: 'medical_recommendation',
          expected_response: "I can help you find products for better sleep. Indica strains are typically best for relaxation and sleep. Would you prefer flower, edibles, or oils?",
          entities: { condition: 'insomnia', effect: 'sleep' }
        }
      ]
    }
  },
  products: {
    name: 'Product Mappings',
    description: 'Map queries to specific products',
    example: {
      metadata: {
        name: 'Product Recommendations v1',
        description: 'Product-specific training data',
        type: 'products',
        version: '1.0',
        author: 'Product Team'
      },
      examples: [
        {
          query: "strongest indica you have",
          expected_intent: 'product_search',
          products: ['Pink Kush', 'Death Bubba', 'MK Ultra'],
          entities: { strain_type: 'indica', potency: 'high' }
        }
      ]
    }
  },
  slang: {
    name: 'Cannabis Slang',
    description: 'Understand cannabis terminology and slang',
    example: {
      metadata: {
        name: 'Cannabis Slang Dictionary',
        description: 'Common slang terms and meanings',
        type: 'slang',
        version: '1.0',
        author: 'Language Team'
      },
      examples: [
        {
          query: "got any loud?",
          expected_intent: 'product_search',
          entities: { slang: 'loud', meaning: 'high_quality', potency: 'strong' }
        }
      ]
    }
  }
};

export default function DatasetUploadModal({ isOpen, onClose, onUploadSuccess }: DatasetUploadModalProps) {
  const [file, setFile] = useState<File | null>(null);
  const [parsedDataset, setParsedDataset] = useState<ParsedDataset | null>(null);
  const [selectedTemplate, setSelectedTemplate] = useState<keyof typeof DATASET_TEMPLATES>('conversations');
  const [showPreview, setShowPreview] = useState(false);
  const [dragActive, setDragActive] = useState(false);

  // File validation and parsing
  const validateDataset = (data: any): ParsedDataset => {
    const errors: string[] = [];
    const warnings: string[] = [];
    
    // Check metadata
    if (!data.metadata) {
      errors.push('Missing metadata section');
    } else {
      if (!data.metadata.name) errors.push('Missing dataset name');
      if (!data.metadata.type) errors.push('Missing dataset type');
      if (!data.metadata.version) warnings.push('Missing version information');
    }

    // Check examples
    if (!data.examples || !Array.isArray(data.examples)) {
      errors.push('Missing or invalid examples array');
    } else {
      if (data.examples.length === 0) {
        errors.push('Dataset contains no examples');
      } else {
        // Validate each example
        data.examples.forEach((ex: any, idx: number) => {
          if (!ex.query) {
            errors.push(`Example ${idx + 1}: Missing query`);
          }
          if (!ex.expected_intent) {
            warnings.push(`Example ${idx + 1}: Missing expected_intent`);
          }
          if (ex.expected_intent === 'product_search' && !ex.products && !ex.entities) {
            warnings.push(`Example ${idx + 1}: Product search without products or entities`);
          }
        });
      }
    }

    // Calculate statistics
    const validExamples = data.examples?.filter((ex: any) => ex.query && ex.expected_intent) || [];
    const intents = [...new Set(validExamples.map((ex: any) => ex.expected_intent))];
    const intentCoverage = intents.reduce<Record<string, number>>((acc, intent) => {
      acc[intent as string] = validExamples.filter((ex: any) => ex.expected_intent === intent).length;
      return acc;
    }, {});

    return {
      metadata: data.metadata || {},
      examples: data.examples || [],
      validation: {
        isValid: errors.length === 0,
        errors,
        warnings,
        stats: {
          totalExamples: data.examples?.length || 0,
          validExamples: validExamples.length,
          uniqueIntents: intents as string[],
          coverage: intentCoverage as Record<string, number>
        }
      }
    };
  };

  // File handling
  const handleFile = useCallback((file: File) => {
    const reader = new FileReader();
    
    reader.onload = async (e) => {
      try {
        let data;
        
        if (file.name.endsWith('.json')) {
          data = JSON.parse(e.target?.result as string);
        } else if (file.name.endsWith('.csv')) {
          // Parse CSV to our format
          const csvText = e.target?.result as string;
          const lines = csvText.split('\n');
          const headers = lines[0].split(',').map(h => h.trim());
          
          const examples = lines.slice(1).filter(line => line.trim()).map(line => {
            const values = line.split(',').map(v => v.trim());
            const example: any = {};
            headers.forEach((header, idx) => {
              if (header === 'entities' || header === 'products' || header === 'context') {
                try {
                  example[header] = JSON.parse(values[idx] || '{}');
                } catch {
                  example[header] = values[idx];
                }
              } else {
                example[header] = values[idx];
              }
            });
            return example;
          });
          
          data = {
            metadata: {
              name: file.name.replace('.csv', ''),
              type: 'custom',
              version: '1.0',
              author: 'Uploaded'
            },
            examples
          };
        } else {
          throw new Error('Unsupported file format. Please use JSON or CSV.');
        }
        
        const validated = validateDataset(data);
        setParsedDataset(validated);
        
        if (!validated.validation.isValid) {
          toast.error(`Dataset validation failed: ${validated.validation.errors[0]}`);
        } else if (validated.validation.warnings.length > 0) {
          toast('Dataset has warnings. Check the preview for details.', { icon: '⚠️' });
        } else {
          toast.success('Dataset validated successfully!');
        }
      } catch (error: any) {
        toast.error(`Failed to parse file: ${error.message}`);
        setParsedDataset(null);
      }
    };
    
    reader.readAsText(file);
  }, []);

  // Drag and drop handlers
  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      setFile(droppedFile);
      handleFile(droppedFile);
    }
  }, [handleFile]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
  }, []);

  // Upload mutation
  const uploadMutation = useMutation({
    mutationFn: async (dataset: ParsedDataset) => {
      const response = await axios.post(endpoints.datasets.upload, {
        metadata: dataset.metadata,
        examples: dataset.examples
      });
      return response.data;
    },
    onSuccess: (data) => {
      toast.success('Dataset uploaded successfully!');
      onUploadSuccess(data);
      onClose();
    },
    onError: (error: any) => {
      toast.error(`Upload failed: ${error.response?.data?.detail || error.message}`);
    }
  });

  const handleUpload = () => {
    if (parsedDataset && parsedDataset.validation.isValid) {
      uploadMutation.mutate(parsedDataset);
    }
  };

  const downloadTemplate = () => {
    const template = DATASET_TEMPLATES[selectedTemplate].example;
    const blob = new Blob([JSON.stringify(template, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${selectedTemplate}_template.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
          onClick={onClose}
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            className="bg-white rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="p-6 border-b border-gray-200">
              <div className="flex justify-between items-center">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">Upload Training Dataset</h2>
                  <p className="text-gray-600 mt-1">Upload high-quality training data to improve AI performance</p>
                </div>
                <button
                  onClick={onClose}
                  className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Content */}
            <div className="p-6 overflow-y-auto max-h-[calc(90vh-200px)]">
              {/* Template Selection */}
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-3">1. Choose Dataset Type</h3>
                <div className="grid grid-cols-3 gap-4">
                  {Object.entries(DATASET_TEMPLATES).map(([key, template]) => (
                    <button
                      key={key}
                      onClick={() => setSelectedTemplate(key as keyof typeof DATASET_TEMPLATES)}
                      className={`p-4 rounded-lg border-2 transition-all ${
                        selectedTemplate === key
                          ? 'border-weed-green-500 bg-green-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <h4 className="font-semibold text-gray-900">{template.name}</h4>
                      <p className="text-sm text-gray-600 mt-1">{template.description}</p>
                    </button>
                  ))}
                </div>
                <button
                  onClick={downloadTemplate}
                  className="mt-3 text-sm text-weed-green-600 hover:text-weed-green-700 flex items-center gap-1"
                >
                  <FileJson className="w-4 h-4" />
                  Download {DATASET_TEMPLATES[selectedTemplate].name} Template
                </button>
              </div>

              {/* File Upload */}
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-3">2. Upload Dataset File</h3>
                <div
                  onDrop={handleDrop}
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                    dragActive
                      ? 'border-weed-green-500 bg-green-50'
                      : 'border-gray-300 hover:border-gray-400'
                  }`}
                >
                  <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600 mb-2">
                    Drag and drop your dataset file here, or click to browse
                  </p>
                  <p className="text-sm text-gray-500 mb-4">
                    Supports JSON and CSV formats (max 10MB)
                  </p>
                  <input
                    type="file"
                    accept=".json,.csv"
                    onChange={(e) => {
                      const selectedFile = e.target.files?.[0];
                      if (selectedFile) {
                        setFile(selectedFile);
                        handleFile(selectedFile);
                      }
                    }}
                    className="hidden"
                    id="file-upload"
                  />
                  <label
                    htmlFor="file-upload"
                    className="inline-flex items-center px-4 py-2 bg-weed-green-500 text-white rounded-lg hover:bg-weed-green-600 cursor-pointer"
                  >
                    <Upload className="w-4 h-4 mr-2" />
                    Choose File
                  </label>
                </div>
                
                {file && (
                  <div className="mt-3 flex items-center justify-between bg-gray-50 p-3 rounded-lg">
                    <div className="flex items-center gap-2">
                      <FileText className="w-4 h-4 text-gray-500" />
                      <span className="text-sm text-gray-700">{file.name}</span>
                      <span className="text-xs text-gray-500">
                        ({(file.size / 1024).toFixed(2)} KB)
                      </span>
                    </div>
                    <button
                      onClick={() => {
                        setFile(null);
                        setParsedDataset(null);
                      }}
                      className="text-red-500 hover:text-red-600"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                )}
              </div>

              {/* Validation Results */}
              {parsedDataset && (
                <div className="mb-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">3. Validation Results</h3>
                  
                  {/* Status */}
                  <div className={`p-4 rounded-lg mb-4 ${
                    parsedDataset.validation.isValid
                      ? 'bg-green-50 border border-green-200'
                      : 'bg-red-50 border border-red-200'
                  }`}>
                    <div className="flex items-center gap-2">
                      {parsedDataset.validation.isValid ? (
                        <CheckCircle className="w-5 h-5 text-green-600" />
                      ) : (
                        <AlertCircle className="w-5 h-5 text-red-600" />
                      )}
                      <span className={`font-semibold ${
                        parsedDataset.validation.isValid ? 'text-green-900' : 'text-red-900'
                      }`}>
                        {parsedDataset.validation.isValid ? 'Dataset Valid' : 'Validation Failed'}
                      </span>
                    </div>
                  </div>

                  {/* Statistics */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                    <div className="bg-gray-50 p-3 rounded-lg">
                      <p className="text-xs text-gray-600">Total Examples</p>
                      <p className="text-2xl font-bold text-gray-900">
                        {parsedDataset.validation.stats.totalExamples}
                      </p>
                    </div>
                    <div className="bg-gray-50 p-3 rounded-lg">
                      <p className="text-xs text-gray-600">Valid Examples</p>
                      <p className="text-2xl font-bold text-green-600">
                        {parsedDataset.validation.stats.validExamples}
                      </p>
                    </div>
                    <div className="bg-gray-50 p-3 rounded-lg">
                      <p className="text-xs text-gray-600">Unique Intents</p>
                      <p className="text-2xl font-bold text-blue-600">
                        {parsedDataset.validation.stats.uniqueIntents.length}
                      </p>
                    </div>
                    <div className="bg-gray-50 p-3 rounded-lg">
                      <p className="text-xs text-gray-600">Quality Score</p>
                      <p className="text-2xl font-bold text-purple-600">
                        {Math.round((parsedDataset.validation.stats.validExamples / 
                          parsedDataset.validation.stats.totalExamples) * 100)}%
                      </p>
                    </div>
                  </div>

                  {/* Errors */}
                  {parsedDataset.validation.errors.length > 0 && (
                    <div className="mb-4">
                      <h4 className="font-semibold text-red-900 mb-2">Errors</h4>
                      <ul className="space-y-1">
                        {parsedDataset.validation.errors.map((error, idx) => (
                          <li key={idx} className="text-sm text-red-700 flex items-start gap-2">
                            <span className="text-red-500 mt-0.5">•</span>
                            <span>{error}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Warnings */}
                  {parsedDataset.validation.warnings.length > 0 && (
                    <div className="mb-4">
                      <h4 className="font-semibold text-yellow-900 mb-2">Warnings</h4>
                      <ul className="space-y-1">
                        {parsedDataset.validation.warnings.slice(0, 5).map((warning, idx) => (
                          <li key={idx} className="text-sm text-yellow-700 flex items-start gap-2">
                            <span className="text-yellow-500 mt-0.5">•</span>
                            <span>{warning}</span>
                          </li>
                        ))}
                        {parsedDataset.validation.warnings.length > 5 && (
                          <li className="text-sm text-yellow-600 italic">
                            ... and {parsedDataset.validation.warnings.length - 5} more warnings
                          </li>
                        )}
                      </ul>
                    </div>
                  )}

                  {/* Preview Button */}
                  <button
                    onClick={() => setShowPreview(!showPreview)}
                    className="text-sm text-weed-green-600 hover:text-weed-green-700 flex items-center gap-1"
                  >
                    <Eye className="w-4 h-4" />
                    {showPreview ? 'Hide' : 'Show'} Dataset Preview
                  </button>

                  {/* Dataset Preview */}
                  {showPreview && (
                    <div className="mt-4 bg-gray-50 rounded-lg p-4 max-h-64 overflow-y-auto">
                      <h4 className="font-semibold text-gray-900 mb-2">Dataset Examples</h4>
                      <div className="space-y-3">
                        {parsedDataset.examples.slice(0, 5).map((example, idx) => (
                          <div key={idx} className="bg-white p-3 rounded border border-gray-200">
                            <p className="text-sm">
                              <span className="font-medium">Query:</span> {example.query}
                            </p>
                            <p className="text-sm text-gray-600">
                              <span className="font-medium">Intent:</span> {example.expected_intent}
                            </p>
                            {example.entities && Object.keys(example.entities).length > 0 && (
                              <p className="text-xs text-gray-500 mt-1">
                                <span className="font-medium">Entities:</span> {JSON.stringify(example.entities)}
                              </p>
                            )}
                          </div>
                        ))}
                        {parsedDataset.examples.length > 5 && (
                          <p className="text-sm text-gray-500 italic text-center">
                            ... and {parsedDataset.examples.length - 5} more examples
                          </p>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="p-6 border-t border-gray-200 bg-gray-50">
              <div className="flex justify-between items-center">
                <div className="text-sm text-gray-600">
                  {parsedDataset && (
                    <span>
                      Ready to upload {parsedDataset.validation.stats.validExamples} training examples
                    </span>
                  )}
                </div>
                <div className="flex gap-3">
                  <button
                    onClick={onClose}
                    className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleUpload}
                    disabled={!parsedDataset || !parsedDataset.validation.isValid || uploadMutation.isPending}
                    className="px-4 py-2 bg-weed-green-500 text-white rounded-lg hover:bg-weed-green-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                  >
                    {uploadMutation.isPending ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                        Uploading...
                      </>
                    ) : (
                      <>
                        <Upload className="w-4 h-4" />
                        Upload Dataset
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}