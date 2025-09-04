import { endpoints } from '../config/endpoints';
import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, Save, X, Trash2, Copy, FileText, AlertCircle, Brain } from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import axios from 'axios';
import toast from 'react-hot-toast';
import { INTENT_CATEGORIES } from './IntentManager';

interface DatasetExample {
  id: string;
  query: string;
  expected_intent: string;
  expected_response: string;
  entities: Record<string, any>;
  products?: string[];
  context?: Record<string, any>;
}

interface Dataset {
  id?: string;
  name: string;
  description: string;
  type: string;
  examples: DatasetExample[];
  metadata: {
    version: string;
    author: string;
    tags: string[];
    target_accuracy: number;
  };
}

interface DatasetCreationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (dataset: Dataset) => void;
  initialDataset?: Dataset;
}

// Intent templates for quick example creation
const EXAMPLE_TEMPLATES = {
  product_search: {
    query: "I'm looking for [product type]",
    expected_response: "I'll help you find the perfect [product type]. Let me show you our best options.",
    entities: { product_type: "", characteristics: [] }
  },
  medical_recommendation: {
    query: "I need something for [condition]",
    expected_response: "I understand you're looking for relief from [condition]. Here are some options that may help.",
    entities: { condition: "", symptoms: [], preferred_method: "" }
  },
  purchase_intent: {
    query: "I want to buy [quantity] of [product]",
    expected_response: "Great! I'll add [quantity] of [product] to your cart.",
    entities: { quantity: "", product: "", action: "add_to_cart" }
  },
  information_request: {
    query: "What's the difference between [option1] and [option2]?",
    expected_response: "Let me explain the key differences between [option1] and [option2].",
    entities: { comparison_items: [], aspect: "" }
  }
};

export default function DatasetCreationModal({
  isOpen,
  onClose,
  onSave,
  initialDataset
}: DatasetCreationModalProps) {
  const [dataset, setDataset] = useState<Dataset>(initialDataset || {
    name: '',
    description: '',
    type: 'custom',
    examples: [],
    metadata: {
      version: '1.0',
      author: 'Admin',
      tags: [],
      target_accuracy: 0.85
    }
  });

  const [currentExample, setCurrentExample] = useState<DatasetExample>({
    id: '',
    query: '',
    expected_intent: 'product_search',
    expected_response: '',
    entities: {},
    products: [],
    context: {}
  });

  const [entityKey, setEntityKey] = useState('');
  const [entityValue, setEntityValue] = useState('');
  const [tagInput, setTagInput] = useState('');
  const [bulkImportText, setBulkImportText] = useState('');
  const [showBulkImport, setShowBulkImport] = useState(false);

  // Auto-generate response using AI
  const generateResponseMutation = useMutation({
    mutationFn: async (query: string) => {
      const response = await axios.post(endpoints.ai.generateResponse, {
        query,
        intent: currentExample.expected_intent
      });
      return response.data;
    },
    onSuccess: (data) => {
      setCurrentExample(prev => ({
        ...prev,
        expected_response: data.response,
        entities: { ...prev.entities, ...data.entities }
      }));
      toast.success('Response generated');
    },
    onError: () => {
      toast.error('Failed to generate response');
    }
  });

  // Add example to dataset
  const addExample = () => {
    if (!currentExample.query || !currentExample.expected_intent) {
      toast.error('Query and intent are required');
      return;
    }

    const newExample = {
      ...currentExample,
      id: `example_${Date.now()}`
    };

    setDataset(prev => ({
      ...prev,
      examples: [...prev.examples, newExample]
    }));

    // Reset current example
    setCurrentExample({
      id: '',
      query: '',
      expected_intent: 'product_search',
      expected_response: '',
      entities: {},
      products: [],
      context: {}
    });

    toast.success('Example added');
  };

  // Remove example
  const removeExample = (id: string) => {
    setDataset(prev => ({
      ...prev,
      examples: prev.examples.filter(ex => ex.id !== id)
    }));
  };

  // Duplicate example
  const duplicateExample = (example: DatasetExample) => {
    const newExample = {
      ...example,
      id: `example_${Date.now()}`,
      query: example.query + ' (copy)'
    };
    setDataset(prev => ({
      ...prev,
      examples: [...prev.examples, newExample]
    }));
  };

  // Add entity
  const addEntity = () => {
    if (entityKey && entityValue) {
      setCurrentExample(prev => ({
        ...prev,
        entities: {
          ...prev.entities,
          [entityKey]: entityValue
        }
      }));
      setEntityKey('');
      setEntityValue('');
    }
  };

  // Add tag
  const addTag = () => {
    if (tagInput && !dataset.metadata.tags.includes(tagInput)) {
      setDataset(prev => ({
        ...prev,
        metadata: {
          ...prev.metadata,
          tags: [...prev.metadata.tags, tagInput]
        }
      }));
      setTagInput('');
    }
  };

  // Bulk import examples
  const handleBulkImport = () => {
    try {
      const lines = bulkImportText.split('\n').filter(line => line.trim());
      const newExamples: DatasetExample[] = [];

      lines.forEach(line => {
        // Expected format: query | intent | response
        const parts = line.split('|').map(p => p.trim());
        if (parts.length >= 2) {
          newExamples.push({
            id: `example_${Date.now()}_${Math.random()}`,
            query: parts[0],
            expected_intent: parts[1] || 'product_search',
            expected_response: parts[2] || '',
            entities: {},
            products: [],
            context: {}
          });
        }
      });

      if (newExamples.length > 0) {
        setDataset(prev => ({
          ...prev,
          examples: [...prev.examples, ...newExamples]
        }));
        setBulkImportText('');
        setShowBulkImport(false);
        toast.success(`Imported ${newExamples.length} examples`);
      } else {
        toast.error('No valid examples found in import text');
      }
    } catch (error) {
      toast.error('Failed to parse bulk import');
    }
  };

  // Apply template
  const applyTemplate = (templateKey: keyof typeof EXAMPLE_TEMPLATES) => {
    const template = EXAMPLE_TEMPLATES[templateKey];
    setCurrentExample(prev => ({
      ...prev,
      query: template.query,
      expected_response: template.expected_response,
      expected_intent: templateKey,
      entities: template.entities
    }));
  };

  // Save dataset
  const handleSave = () => {
    if (!dataset.name) {
      toast.error('Dataset name is required');
      return;
    }

    if (dataset.examples.length === 0) {
      toast.error('Add at least one example');
      return;
    }

    onSave(dataset);
    toast.success('Dataset saved successfully');
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
            className="bg-white rounded-xl shadow-2xl max-w-6xl w-full max-h-[90vh] overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="p-6 border-b border-gray-200 bg-gradient-to-r from-weed-green-500 to-weed-green-600">
              <div className="flex justify-between items-center">
                <div className="text-white">
                  <h2 className="text-2xl font-bold">
                    {initialDataset ? 'Edit Dataset' : 'Create New Dataset'}
                  </h2>
                  <p className="mt-1 opacity-90">Build high-quality training data for AI</p>
                </div>
                <button
                  onClick={onClose}
                  className="p-2 hover:bg-white/20 rounded-lg transition-colors"
                >
                  <X className="w-5 h-5 text-white" />
                </button>
              </div>
            </div>

            {/* Content */}
            <div className="flex h-[calc(90vh-200px)]">
              {/* Left Panel - Dataset Info & Current Example */}
              <div className="w-1/2 p-6 border-r border-gray-200 overflow-y-auto">
                {/* Dataset Info */}
                <div className="mb-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Dataset Information</h3>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Dataset Name *
                      </label>
                      <input
                        type="text"
                        value={dataset.name}
                        onChange={(e) => setDataset({ ...dataset, name: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-weed-green-500"
                        placeholder="e.g., Cannabis Slang Training v2"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Description
                      </label>
                      <textarea
                        value={dataset.description}
                        onChange={(e) => setDataset({ ...dataset, description: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-weed-green-500"
                        rows={2}
                        placeholder="Describe the purpose of this dataset..."
                      />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Type
                        </label>
                        <select
                          value={dataset.type}
                          onChange={(e) => setDataset({ ...dataset, type: e.target.value })}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-weed-green-500"
                        >
                          <option value="custom">Custom</option>
                          <option value="conversations">Conversations</option>
                          <option value="products">Products</option>
                          <option value="slang">Slang</option>
                          <option value="medical">Medical</option>
                        </select>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Target Accuracy
                        </label>
                        <input
                          type="range"
                          min="0"
                          max="100"
                          value={dataset.metadata.target_accuracy * 100}
                          onChange={(e) => setDataset({
                            ...dataset,
                            metadata: {
                              ...dataset.metadata,
                              target_accuracy: parseFloat(e.target.value) / 100
                            }
                          })}
                          className="w-full"
                        />
                        <span className="text-sm text-gray-600">
                          {(dataset.metadata.target_accuracy * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Tags
                      </label>
                      <div className="flex flex-wrap gap-2 mb-2">
                        {dataset.metadata.tags.map((tag, idx) => (
                          <span
                            key={idx}
                            className="px-2 py-1 bg-weed-green-100 text-weed-green-700 rounded-full text-sm flex items-center gap-1"
                          >
                            {tag}
                            <button
                              onClick={() => setDataset({
                                ...dataset,
                                metadata: {
                                  ...dataset.metadata,
                                  tags: dataset.metadata.tags.filter((_, i) => i !== idx)
                                }
                              })}
                              className="text-weed-green-600 hover:text-red-600"
                            >
                              <X className="w-3 h-3" />
                            </button>
                          </span>
                        ))}
                      </div>
                      <div className="flex gap-2">
                        <input
                          type="text"
                          value={tagInput}
                          onChange={(e) => setTagInput(e.target.value)}
                          onKeyPress={(e) => e.key === 'Enter' && addTag()}
                          className="flex-1 px-3 py-1 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-weed-green-500"
                          placeholder="Add tag..."
                        />
                        <button
                          onClick={addTag}
                          className="px-3 py-1 bg-weed-green-500 text-white rounded-lg hover:bg-weed-green-600"
                        >
                          Add
                        </button>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Current Example */}
                <div className="border-t pt-6">
                  <div className="flex justify-between items-center mb-4">
                    <h3 className="text-lg font-semibold text-gray-900">Add Example</h3>
                    <div className="flex gap-2">
                      <button
                        onClick={() => setShowBulkImport(true)}
                        className="text-sm text-gray-600 hover:text-gray-700"
                      >
                        <FileText className="w-4 h-4 inline mr-1" />
                        Bulk Import
                      </button>
                    </div>
                  </div>

                  {/* Quick Templates */}
                  <div className="mb-4">
                    <p className="text-sm text-gray-600 mb-2">Quick Templates:</p>
                    <div className="flex flex-wrap gap-2">
                      {Object.keys(EXAMPLE_TEMPLATES).map(key => (
                        <button
                          key={key}
                          onClick={() => applyTemplate(key as keyof typeof EXAMPLE_TEMPLATES)}
                          className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs hover:bg-gray-200"
                        >
                          {key.replace(/_/g, ' ')}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Query *
                      </label>
                      <input
                        type="text"
                        value={currentExample.query}
                        onChange={(e) => setCurrentExample({ ...currentExample, query: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-weed-green-500"
                        placeholder="Customer query..."
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Expected Intent *
                      </label>
                      <select
                        value={currentExample.expected_intent}
                        onChange={(e) => setCurrentExample({ ...currentExample, expected_intent: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-weed-green-500"
                      >
                        {Object.entries(INTENT_CATEGORIES).map(([key, category]) => (
                          <optgroup key={key} label={category.label}>
                            <option value={key}>{category.label} (General)</option>
                            {category.subcategories.map(sub => (
                              <option key={sub} value={`${key}.${sub}`}>
                                → {sub.replace(/_/g, ' ')}
                              </option>
                            ))}
                          </optgroup>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Expected Response
                      </label>
                      <div className="relative">
                        <textarea
                          value={currentExample.expected_response}
                          onChange={(e) => setCurrentExample({ ...currentExample, expected_response: e.target.value })}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-weed-green-500"
                          rows={3}
                          placeholder="AI response..."
                        />
                        <button
                          onClick={() => currentExample.query && generateResponseMutation.mutate(currentExample.query)}
                          disabled={!currentExample.query || generateResponseMutation.isPending}
                          className="absolute top-2 right-2 p-1 text-purple-600 hover:bg-purple-50 rounded disabled:opacity-50"
                          title="Generate with AI"
                        >
                          <Brain className="w-4 h-4" />
                        </button>
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Entities
                      </label>
                      <div className="flex flex-wrap gap-2 mb-2">
                        {Object.entries(currentExample.entities).map(([key, value]) => (
                          <span
                            key={key}
                            className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-sm"
                          >
                            {key}: {JSON.stringify(value)}
                            <button
                              onClick={() => {
                                const newEntities = { ...currentExample.entities };
                                delete newEntities[key];
                                setCurrentExample({ ...currentExample, entities: newEntities });
                              }}
                              className="ml-1 text-blue-600 hover:text-red-600"
                            >
                              <X className="w-3 h-3 inline" />
                            </button>
                          </span>
                        ))}
                      </div>
                      <div className="flex gap-2">
                        <input
                          type="text"
                          value={entityKey}
                          onChange={(e) => setEntityKey(e.target.value)}
                          className="flex-1 px-3 py-1 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-weed-green-500"
                          placeholder="Entity key..."
                        />
                        <input
                          type="text"
                          value={entityValue}
                          onChange={(e) => setEntityValue(e.target.value)}
                          className="flex-1 px-3 py-1 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-weed-green-500"
                          placeholder="Entity value..."
                        />
                        <button
                          onClick={addEntity}
                          className="px-3 py-1 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
                        >
                          Add
                        </button>
                      </div>
                    </div>

                    <button
                      onClick={addExample}
                      className="w-full px-4 py-2 bg-weed-green-500 text-white rounded-lg hover:bg-weed-green-600 flex items-center justify-center gap-2"
                    >
                      <Plus className="w-4 h-4" />
                      Add Example to Dataset
                    </button>
                  </div>
                </div>
              </div>

              {/* Right Panel - Examples List */}
              <div className="w-1/2 p-6 overflow-y-auto bg-gray-50">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-semibold text-gray-900">
                    Examples ({dataset.examples.length})
                  </h3>
                  {dataset.examples.length > 0 && (
                    <span className="text-sm text-gray-600">
                      Quality Score: {Math.round((dataset.examples.filter(e => e.expected_response).length / dataset.examples.length) * 100)}%
                    </span>
                  )}
                </div>

                {dataset.examples.length === 0 ? (
                  <div className="text-center py-12">
                    <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-600">No examples added yet</p>
                    <p className="text-sm text-gray-500 mt-2">
                      Add examples using the form on the left
                    </p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {dataset.examples.map((example, idx) => (
                      <motion.div
                        key={example.id}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="bg-white p-4 rounded-lg border border-gray-200"
                      >
                        <div className="flex justify-between items-start mb-2">
                          <span className="text-xs text-gray-500">#{idx + 1}</span>
                          <div className="flex gap-1">
                            <button
                              onClick={() => duplicateExample(example)}
                              className="p-1 text-gray-600 hover:bg-gray-100 rounded"
                              title="Duplicate"
                            >
                              <Copy className="w-3 h-3" />
                            </button>
                            <button
                              onClick={() => removeExample(example.id)}
                              className="p-1 text-red-600 hover:bg-red-50 rounded"
                              title="Remove"
                            >
                              <Trash2 className="w-3 h-3" />
                            </button>
                          </div>
                        </div>
                        
                        <div className="space-y-2">
                          <div>
                            <span className="text-xs text-gray-600">Query:</span>
                            <p className="text-sm text-gray-900">{example.query}</p>
                          </div>
                          
                          <div>
                            <span className="text-xs text-gray-600">Intent:</span>
                            <span className="ml-2 px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs">
                              {example.expected_intent}
                            </span>
                          </div>
                          
                          {example.expected_response && (
                            <div>
                              <span className="text-xs text-gray-600">Response:</span>
                              <p className="text-sm text-gray-700">{example.expected_response}</p>
                            </div>
                          )}
                          
                          {Object.keys(example.entities).length > 0 && (
                            <div>
                              <span className="text-xs text-gray-600">Entities:</span>
                              <div className="flex flex-wrap gap-1 mt-1">
                                {Object.entries(example.entities).map(([key, value]) => (
                                  <span key={key} className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs">
                                    {key}: {JSON.stringify(value)}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      </motion.div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Footer */}
            <div className="p-6 border-t border-gray-200 bg-gray-50">
              <div className="flex justify-between items-center">
                <div className="text-sm text-gray-600">
                  {dataset.examples.length > 0 && (
                    <span>
                      {dataset.examples.length} examples ready for training
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
                    onClick={handleSave}
                    disabled={!dataset.name || dataset.examples.length === 0}
                    className="px-4 py-2 bg-weed-green-500 text-white rounded-lg hover:bg-weed-green-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                  >
                    <Save className="w-4 h-4" />
                    Save Dataset
                  </button>
                </div>
              </div>
            </div>

            {/* Bulk Import Modal */}
            <AnimatePresence>
              {showBulkImport && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center"
                  onClick={() => setShowBulkImport(false)}
                >
                  <motion.div
                    initial={{ scale: 0.9 }}
                    animate={{ scale: 1 }}
                    className="bg-white rounded-lg p-6 max-w-2xl w-full max-h-[80vh] overflow-hidden"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <h3 className="text-lg font-semibold mb-4">Bulk Import Examples</h3>
                    <p className="text-sm text-gray-600 mb-4">
                      Format: query | intent | response (one per line)
                    </p>
                    <textarea
                      value={bulkImportText}
                      onChange={(e) => setBulkImportText(e.target.value)}
                      className="w-full h-64 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-weed-green-500 font-mono text-sm"
                      placeholder="I need indica for sleep | medical_recommendation | I'll help you find relaxing indica strains perfect for sleep."
                    />
                    <div className="flex justify-end gap-3 mt-4">
                      <button
                        onClick={() => setShowBulkImport(false)}
                        className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
                      >
                        Cancel
                      </button>
                      <button
                        onClick={handleBulkImport}
                        className="px-4 py-2 bg-weed-green-500 text-white rounded-lg hover:bg-weed-green-600"
                      >
                        Import
                      </button>
                    </div>
                  </motion.div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}