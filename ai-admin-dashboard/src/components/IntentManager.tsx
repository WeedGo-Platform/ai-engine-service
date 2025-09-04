import { endpoints } from '../config/endpoints';
import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, Edit2, Trash2, Save, X, Tag } from 'lucide-react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import toast from 'react-hot-toast';

// Comprehensive intent categories for cannabis business
export const INTENT_CATEGORIES = {
  // Core Shopping Intents
  product_search: {
    label: 'Product Search',
    color: 'green',
    description: 'Customer looking for specific products',
    subcategories: [
      'strain_search',
      'category_search',
      'effect_based_search',
      'price_range_search',
      'brand_search',
      'potency_search'
    ]
  },
  
  // Medical & Wellness
  medical_recommendation: {
    label: 'Medical Recommendation',
    color: 'blue',
    description: 'Medical cannabis guidance',
    subcategories: [
      'pain_relief',
      'anxiety_treatment',
      'sleep_aid',
      'appetite_stimulation',
      'nausea_relief',
      'inflammation_reduction',
      'seizure_control',
      'ptsd_management'
    ]
  },
  
  // Purchase & Transaction
  purchase_intent: {
    label: 'Purchase Intent',
    color: 'purple',
    description: 'Ready to buy or add to cart',
    subcategories: [
      'add_to_cart',
      'bulk_purchase',
      'quick_buy',
      'reorder_previous',
      'subscription_setup'
    ]
  },
  
  // Information Seeking
  information_request: {
    label: 'Information Request',
    color: 'yellow',
    description: 'Seeking product or service information',
    subcategories: [
      'dosage_inquiry',
      'consumption_methods',
      'onset_duration',
      'side_effects',
      'drug_interactions',
      'legal_questions',
      'storage_advice'
    ]
  },
  
  // Customer Service
  customer_service: {
    label: 'Customer Service',
    color: 'orange',
    description: 'Support and service requests',
    subcategories: [
      'order_status',
      'return_request',
      'complaint',
      'delivery_inquiry',
      'loyalty_program',
      'account_help'
    ]
  },
  
  // Comparison & Decision
  comparison: {
    label: 'Product Comparison',
    color: 'indigo',
    description: 'Comparing products or options',
    subcategories: [
      'strain_comparison',
      'price_comparison',
      'effect_comparison',
      'brand_comparison',
      'format_comparison'
    ]
  },
  
  // Discovery & Exploration
  discovery: {
    label: 'Discovery',
    color: 'pink',
    description: 'Browsing and exploring options',
    subcategories: [
      'new_products',
      'trending_items',
      'seasonal_offerings',
      'limited_editions',
      'staff_picks'
    ]
  },
  
  // Education
  education: {
    label: 'Education',
    color: 'teal',
    description: 'Learning about cannabis',
    subcategories: [
      'terpene_education',
      'cannabinoid_info',
      'growing_info',
      'history_culture',
      'consumption_safety'
    ]
  },
  
  // Social & Greeting
  social: {
    label: 'Social Interaction',
    color: 'gray',
    description: 'Greetings and social exchanges',
    subcategories: [
      'greeting',
      'goodbye',
      'thank_you',
      'small_talk',
      'feedback'
    ]
  }
};

interface Intent {
  id: string;
  name: string;
  category: string;
  subcategory?: string;
  description: string;
  examples: string[];
  responses: string[];
  entities: string[];
  confidence_threshold: number;
  active: boolean;
  created_at: Date;
  usage_count: number;
}

export default function IntentManager() {
  const queryClient = useQueryClient();
  const [isCreating, setIsCreating] = useState(false);
  const [editingIntent, setEditingIntent] = useState<Intent | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  // Fetch existing intents
  const { data: intents = [] } = useQuery({
    queryKey: ['intents'],
    queryFn: async () => {
      const response = await axios.get(endpoints.intents.list);
      return response.data;
    }
  });

  // Create new intent
  const createIntentMutation = useMutation({
    mutationFn: async (intent: Partial<Intent>) => {
      const response = await axios.post(endpoints.intents.list, intent);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['intents'] });
      toast.success('Intent created successfully');
      setIsCreating(false);
      setEditingIntent(null);
    },
    onError: (error: any) => {
      toast.error(`Failed to create intent: ${error.response?.data?.detail || error.message}`);
    }
  });

  // Update intent
  const updateIntentMutation = useMutation({
    mutationFn: async (intent: Intent) => {
      const response = await axios.put(endpoints.intents.update(intent.id), intent);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['intents'] });
      toast.success('Intent updated successfully');
      setEditingIntent(null);
    },
    onError: (error: any) => {
      toast.error(`Failed to update intent: ${error.response?.data?.detail || error.message}`);
    }
  });

  // Delete intent
  const deleteIntentMutation = useMutation({
    mutationFn: async (intentId: string) => {
      await axios.delete(endpoints.intents.delete(intentId));
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['intents'] });
      toast.success('Intent deleted successfully');
    },
    onError: (error: any) => {
      toast.error(`Failed to delete intent: ${error.response?.data?.detail || error.message}`);
    }
  });

  // Filter intents
  const filteredIntents = intents.filter((intent: Intent) => {
    const matchesSearch = intent.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          intent.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = selectedCategory === 'all' || intent.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  // Default intent template
  const createNewIntent = () => {
    const newIntent: Partial<Intent> = {
      id: `custom_${Date.now()}`,
      name: '',
      category: 'product_search',
      description: '',
      examples: [''],
      responses: [''],
      entities: [],
      confidence_threshold: 0.7,
      active: true,
      usage_count: 0
    };
    setEditingIntent(newIntent as Intent);
    setIsCreating(true);
  };

  return (
    <div className="bg-white rounded-xl shadow-sm p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h3 className="text-xl font-bold text-gray-900">Intent Management</h3>
          <p className="text-gray-600 mt-1">Define and manage AI understanding of customer intents</p>
        </div>
        <button
          onClick={createNewIntent}
          className="px-4 py-2 bg-weed-green-500 text-white rounded-lg hover:bg-weed-green-600 flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          New Intent
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-4 mb-6">
        <input
          type="text"
          placeholder="Search intents..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-weed-green-500"
        />
        <select
          value={selectedCategory}
          onChange={(e) => setSelectedCategory(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-weed-green-500"
        >
          <option value="all">All Categories</option>
          {Object.entries(INTENT_CATEGORIES).map(([key, category]) => (
            <option key={key} value={key}>{category.label}</option>
          ))}
        </select>
      </div>

      {/* Intent Categories Overview */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        {Object.entries(INTENT_CATEGORIES).map(([key, category]) => {
          const count = intents.filter((i: Intent) => i.category === key).length;
          return (
            <div
              key={key}
              className="p-4 border border-gray-200 rounded-lg hover:border-weed-green-400 cursor-pointer transition-colors"
              onClick={() => setSelectedCategory(key)}
            >
              <div className="flex justify-between items-start mb-2">
                <Tag className={`w-5 h-5 text-${category.color}-500`} />
                <span className="text-2xl font-bold text-gray-900">{count}</span>
              </div>
              <h4 className="font-semibold text-gray-900">{category.label}</h4>
              <p className="text-xs text-gray-600 mt-1">{category.description}</p>
              <div className="mt-2">
                <p className="text-xs text-gray-500">Subcategories: {category.subcategories.length}</p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Intent List */}
      <div className="space-y-3">
        {filteredIntents.map((intent: Intent) => (
          <motion.div
            key={intent.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="p-4 border border-gray-200 rounded-lg hover:border-weed-green-400 transition-colors"
          >
            <div className="flex justify-between items-start">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <h4 className="font-semibold text-gray-900">{intent.name}</h4>
                  <span className={`px-2 py-1 text-xs rounded-full bg-${
                    INTENT_CATEGORIES[intent.category as keyof typeof INTENT_CATEGORIES]?.color || 'gray'
                  }-100 text-${
                    INTENT_CATEGORIES[intent.category as keyof typeof INTENT_CATEGORIES]?.color || 'gray'
                  }-700`}>
                    {INTENT_CATEGORIES[intent.category as keyof typeof INTENT_CATEGORIES]?.label || intent.category}
                  </span>
                  {intent.subcategory && (
                    <span className="text-xs text-gray-500">→ {intent.subcategory}</span>
                  )}
                </div>
                <p className="text-sm text-gray-600">{intent.description}</p>
                <div className="flex items-center gap-4 mt-2">
                  <span className="text-xs text-gray-500">
                    {intent.examples.length} examples
                  </span>
                  <span className="text-xs text-gray-500">
                    {intent.responses.length} responses
                  </span>
                  <span className="text-xs text-gray-500">
                    Used {intent.usage_count} times
                  </span>
                  <span className={`text-xs ${intent.active ? 'text-green-600' : 'text-red-600'}`}>
                    {intent.active ? 'Active' : 'Inactive'}
                  </span>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setEditingIntent(intent)}
                  className="p-2 text-gray-600 hover:text-weed-green-600 hover:bg-gray-100 rounded-lg"
                >
                  <Edit2 className="w-4 h-4" />
                </button>
                <button
                  onClick={() => deleteIntentMutation.mutate(intent.id)}
                  className="p-2 text-gray-600 hover:text-red-600 hover:bg-gray-100 rounded-lg"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Intent Editor Modal */}
      <AnimatePresence>
        {editingIntent && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
            onClick={() => {
              setEditingIntent(null);
              setIsCreating(false);
            }}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-white rounded-xl shadow-2xl max-w-3xl w-full max-h-[90vh] overflow-hidden"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="p-6 border-b border-gray-200">
                <div className="flex justify-between items-center">
                  <h3 className="text-xl font-bold text-gray-900">
                    {isCreating ? 'Create New Intent' : 'Edit Intent'}
                  </h3>
                  <button
                    onClick={() => {
                      setEditingIntent(null);
                      setIsCreating(false);
                    }}
                    className="p-2 hover:bg-gray-100 rounded-lg"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
              </div>

              <div className="p-6 overflow-y-auto max-h-[calc(90vh-200px)]">
                {/* Basic Information */}
                <div className="space-y-4 mb-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Intent Name
                    </label>
                    <input
                      type="text"
                      value={editingIntent.name}
                      onChange={(e) => setEditingIntent({ ...editingIntent, name: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-weed-green-500"
                      placeholder="e.g., find_indica_for_sleep"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Category
                      </label>
                      <select
                        value={editingIntent.category}
                        onChange={(e) => setEditingIntent({ ...editingIntent, category: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-weed-green-500"
                      >
                        {Object.entries(INTENT_CATEGORIES).map(([key, category]) => (
                          <option key={key} value={key}>{category.label}</option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Subcategory
                      </label>
                      <select
                        value={editingIntent.subcategory || ''}
                        onChange={(e) => setEditingIntent({ ...editingIntent, subcategory: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-weed-green-500"
                      >
                        <option value="">None</option>
                        {INTENT_CATEGORIES[editingIntent.category as keyof typeof INTENT_CATEGORIES]?.subcategories.map(sub => (
                          <option key={sub} value={sub}>{sub.replace(/_/g, ' ')}</option>
                        ))}
                      </select>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Description
                    </label>
                    <textarea
                      value={editingIntent.description}
                      onChange={(e) => setEditingIntent({ ...editingIntent, description: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-weed-green-500"
                      rows={2}
                      placeholder="Describe what this intent represents..."
                    />
                  </div>
                </div>

                {/* Examples */}
                <div className="mb-6">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Example Queries
                  </label>
                  {editingIntent.examples.map((example, idx) => (
                    <div key={idx} className="flex gap-2 mb-2">
                      <input
                        type="text"
                        value={example}
                        onChange={(e) => {
                          const newExamples = [...editingIntent.examples];
                          newExamples[idx] = e.target.value;
                          setEditingIntent({ ...editingIntent, examples: newExamples });
                        }}
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-weed-green-500"
                        placeholder="Example query..."
                      />
                      <button
                        onClick={() => {
                          const newExamples = editingIntent.examples.filter((_, i) => i !== idx);
                          setEditingIntent({ ...editingIntent, examples: newExamples });
                        }}
                        className="p-2 text-red-600 hover:bg-red-50 rounded-lg"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                  <button
                    onClick={() => setEditingIntent({
                      ...editingIntent,
                      examples: [...editingIntent.examples, '']
                    })}
                    className="text-sm text-weed-green-600 hover:text-weed-green-700"
                  >
                    + Add Example
                  </button>
                </div>

                {/* Responses */}
                <div className="mb-6">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Response Templates
                  </label>
                  {editingIntent.responses.map((response, idx) => (
                    <div key={idx} className="flex gap-2 mb-2">
                      <textarea
                        value={response}
                        onChange={(e) => {
                          const newResponses = [...editingIntent.responses];
                          newResponses[idx] = e.target.value;
                          setEditingIntent({ ...editingIntent, responses: newResponses });
                        }}
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-weed-green-500"
                        rows={2}
                        placeholder="Response template..."
                      />
                      <button
                        onClick={() => {
                          const newResponses = editingIntent.responses.filter((_, i) => i !== idx);
                          setEditingIntent({ ...editingIntent, responses: newResponses });
                        }}
                        className="p-2 text-red-600 hover:bg-red-50 rounded-lg"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                  <button
                    onClick={() => setEditingIntent({
                      ...editingIntent,
                      responses: [...editingIntent.responses, '']
                    })}
                    className="text-sm text-weed-green-600 hover:text-weed-green-700"
                  >
                    + Add Response
                  </button>
                </div>

                {/* Entities */}
                <div className="mb-6">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Expected Entities
                  </label>
                  <div className="flex flex-wrap gap-2 mb-2">
                    {editingIntent.entities.map((entity, idx) => (
                      <span
                        key={idx}
                        className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full flex items-center gap-1"
                      >
                        {entity}
                        <button
                          onClick={() => {
                            const newEntities = editingIntent.entities.filter((_, i) => i !== idx);
                            setEditingIntent({ ...editingIntent, entities: newEntities });
                          }}
                          className="ml-1 text-gray-500 hover:text-red-600"
                        >
                          <X className="w-3 h-3" />
                        </button>
                      </span>
                    ))}
                  </div>
                  <input
                    type="text"
                    placeholder="Add entity (press Enter)"
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') {
                        const input = e.target as HTMLInputElement;
                        if (input.value) {
                          setEditingIntent({
                            ...editingIntent,
                            entities: [...editingIntent.entities, input.value]
                          });
                          input.value = '';
                        }
                      }
                    }}
                    className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-weed-green-500"
                  />
                </div>

                {/* Settings */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Confidence Threshold
                    </label>
                    <input
                      type="range"
                      min="0"
                      max="100"
                      value={editingIntent.confidence_threshold * 100}
                      onChange={(e) => setEditingIntent({
                        ...editingIntent,
                        confidence_threshold: parseFloat(e.target.value) / 100
                      })}
                      className="w-full"
                    />
                    <span className="text-sm text-gray-600">
                      {(editingIntent.confidence_threshold * 100).toFixed(0)}%
                    </span>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Status
                    </label>
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={editingIntent.active}
                        onChange={(e) => setEditingIntent({
                          ...editingIntent,
                          active: e.target.checked
                        })}
                        className="rounded text-weed-green-500 focus:ring-weed-green-500"
                      />
                      <span className="text-sm">Active</span>
                    </label>
                  </div>
                </div>
              </div>

              <div className="p-6 border-t border-gray-200 bg-gray-50">
                <div className="flex justify-end gap-3">
                  <button
                    onClick={() => {
                      setEditingIntent(null);
                      setIsCreating(false);
                    }}
                    className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={() => {
                      if (isCreating) {
                        createIntentMutation.mutate(editingIntent);
                      } else {
                        updateIntentMutation.mutate(editingIntent);
                      }
                    }}
                    disabled={!editingIntent.name || !editingIntent.description}
                    className="px-4 py-2 bg-weed-green-500 text-white rounded-lg hover:bg-weed-green-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                  >
                    <Save className="w-4 h-4" />
                    {isCreating ? 'Create Intent' : 'Save Changes'}
                  </button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}