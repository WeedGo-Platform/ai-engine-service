import { endpoints } from '../config/endpoints';
import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery, useMutation } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import apiService from '../services/api';
import { 
  BookOpen,
  MessageSquare,
  ShoppingBag,
  Heart,
  Shield,
  Brain,
  Target,
  TrendingUp,
  Plus,
  Upload,
  Download,
  Play,
  Pause,
  CheckCircle,
  AlertCircle,
  Clock,
  Search,
  Users,
  Award,
  BarChart3,
  FileText,
  Save,
  RefreshCw,
  Zap,
  ChevronRight,
  Settings,
  Filter,
  Tag,
  Database,
  Copy,
  Trash2,
  Edit
} from 'lucide-react';

type ExampleCategory = 'conversation' | 'product' | 'medical' | 'compliance' | 'effects' | 'general';

interface ConversationExample {
  id: string;
  input: string;
  expectedOutput: string;
  category: ExampleCategory;
  tags: string[];
  quality: number;
  usageCount: number;
  lastUsed?: string;
  createdAt: string;
  metadata?: {
    intent?: string;
    entities?: Record<string, any>;
    context?: Record<string, any>;
  };
}

interface ExampleStats {
  totalExamples: number;
  categoryCounts: Record<ExampleCategory, number>;
  averageQuality: number;
  recentlyUsed: number;
  topTags: { tag: string; count: number }[];
}

export default function ExamplesLibrary() {
  const [selectedCategory, setSelectedCategory] = useState<ExampleCategory | 'all'>('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedExample, setSelectedExample] = useState<ConversationExample | null>(null);
  const [isAddingExample, setIsAddingExample] = useState(false);
  const [newExample, setNewExample] = useState({
    input: '',
    expectedOutput: '',
    category: 'conversation' as ExampleCategory,
    tags: [] as string[],
    metadata: {}
  });
  
  // Fetch examples from API
  const { data: examples = [], refetch: refetchExamples } = useQuery({
    queryKey: ['conversation-examples'],
    queryFn: apiService.getTrainingExamples,
    select: (data) => data?.examples || []
  });
  
  // Calculate stats
  const stats: ExampleStats = {
    totalExamples: examples.length,
    categoryCounts: examples.reduce((acc, ex) => {
      const cat = ex.category || 'general';
      acc[cat] = (acc[cat] || 0) + 1;
      return acc;
    }, {} as Record<ExampleCategory, number>),
    averageQuality: examples.reduce((sum, ex) => sum + (ex.quality || 0), 0) / (examples.length || 1),
    recentlyUsed: examples.filter(ex => {
      if (!ex.lastUsed) return false;
      const lastUsed = new Date(ex.lastUsed);
      const dayAgo = new Date(Date.now() - 24 * 60 * 60 * 1000);
      return lastUsed > dayAgo;
    }).length,
    topTags: Object.entries(
      examples.flatMap(ex => ex.tags || [])
        .reduce((acc, tag) => {
          acc[tag] = (acc[tag] || 0) + 1;
          return acc;
        }, {} as Record<string, number>)
    ).map(([tag, count]) => ({ tag, count }))
     .sort((a, b) => b.count - a.count)
     .slice(0, 5)
  };
  
  // Filter examples
  const filteredExamples = examples.filter(ex => {
    const matchesCategory = selectedCategory === 'all' || ex.category === selectedCategory;
    const matchesSearch = !searchTerm || 
      ex.input.toLowerCase().includes(searchTerm.toLowerCase()) ||
      ex.expectedOutput.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (ex.tags || []).some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()));
    return matchesCategory && matchesSearch;
  });
  
  // Add example mutation
  const addExampleMutation = useMutation({
    mutationFn: async (example: typeof newExample) => {
      const response = await fetch(`${endpoints.base}/api/v1/ai/training-examples`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(example)
      });
      if (!response.ok) throw new Error('Failed to add example');
      return response.json();
    },
    onSuccess: () => {
      toast.success('Example added successfully');
      refetchExamples();
      setIsAddingExample(false);
      setNewExample({
        input: '',
        expectedOutput: '',
        category: 'conversation',
        tags: [],
        metadata: {}
      });
    },
    onError: () => {
      toast.error('Failed to add example');
    }
  });
  
  // Delete example mutation
  const deleteExampleMutation = useMutation({
    mutationFn: async (id: string) => {
      const response = await fetch(`${endpoints.base}/api/v1/ai/training-examples/${id}`, {
        method: 'DELETE'
      });
      if (!response.ok) throw new Error('Failed to delete example');
      return response.json();
    },
    onSuccess: () => {
      toast.success('Example deleted');
      refetchExamples();
      setSelectedExample(null);
    },
    onError: () => {
      toast.error('Failed to delete example');
    }
  });
  
  const categories = [
    { id: 'all', label: 'All Examples', icon: Database, color: 'zinc' },
    { id: 'conversation', label: 'Conversation', icon: MessageSquare, color: 'blue' },
    { id: 'product', label: 'Product', icon: ShoppingBag, color: 'purple' },
    { id: 'medical', label: 'Medical', icon: Heart, color: 'red' },
    { id: 'compliance', label: 'Compliance', icon: Shield, color: 'green' },
    { id: 'effects', label: 'Effects', icon: Brain, color: 'yellow' },
    { id: 'general', label: 'General', icon: BookOpen, color: 'gray' }
  ];
  
  return (
    <div className="max-w-7xl mx-auto">
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="space-y-6"
      >
        {/* Header */}
        <div className="bg-white rounded-2xl shadow-sm border border-zinc-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl">
                <BookOpen className="w-6 h-6 text-white" />
              </div>
              <div>
                <h2 className="text-2xl font-bold text-zinc-900">Examples Library</h2>
                <p className="text-sm text-zinc-500">Manage conversation examples for context injection</p>
              </div>
            </div>
            
            <div className="flex items-center gap-3">
              <button
                onClick={() => setIsAddingExample(true)}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
              >
                <Plus className="w-4 h-4" />
                Add Example
              </button>
              <button className="px-4 py-2 border border-zinc-300 rounded-lg hover:bg-zinc-50 flex items-center gap-2">
                <Upload className="w-4 h-4" />
                Import
              </button>
              <button className="px-4 py-2 border border-zinc-300 rounded-lg hover:bg-zinc-50 flex items-center gap-2">
                <Download className="w-4 h-4" />
                Export
              </button>
            </div>
          </div>
          
          {/* Stats */}
          <div className="grid grid-cols-4 gap-4">
            <div className="p-4 bg-zinc-50 rounded-lg">
              <div className="flex items-center gap-2 mb-1">
                <Database className="w-4 h-4 text-zinc-500" />
                <span className="text-sm text-zinc-600">Total Examples</span>
              </div>
              <p className="text-2xl font-bold text-zinc-900">{stats.totalExamples}</p>
            </div>
            <div className="p-4 bg-blue-50 rounded-lg">
              <div className="flex items-center gap-2 mb-1">
                <TrendingUp className="w-4 h-4 text-blue-500" />
                <span className="text-sm text-blue-600">Recently Used</span>
              </div>
              <p className="text-2xl font-bold text-blue-900">{stats.recentlyUsed}</p>
            </div>
            <div className="p-4 bg-green-50 rounded-lg">
              <div className="flex items-center gap-2 mb-1">
                <Award className="w-4 h-4 text-green-500" />
                <span className="text-sm text-green-600">Avg Quality</span>
              </div>
              <p className="text-2xl font-bold text-green-900">{(stats.averageQuality * 100).toFixed(0)}%</p>
            </div>
            <div className="p-4 bg-purple-50 rounded-lg">
              <div className="flex items-center gap-2 mb-1">
                <Tag className="w-4 h-4 text-purple-500" />
                <span className="text-sm text-purple-600">Top Tag</span>
              </div>
              <p className="text-2xl font-bold text-purple-900">
                {stats.topTags[0]?.tag || 'None'}
              </p>
            </div>
          </div>
        </div>
        
        {/* Main Content */}
        <div className="grid grid-cols-12 gap-6">
          {/* Categories Sidebar */}
          <div className="col-span-3">
            <div className="bg-white rounded-xl shadow-sm border border-zinc-200 p-4">
              <h3 className="font-semibold text-zinc-900 mb-4">Categories</h3>
              <div className="space-y-1">
                {categories.map(cat => {
                  const Icon = cat.icon;
                  const count = cat.id === 'all' 
                    ? stats.totalExamples 
                    : stats.categoryCounts[cat.id as ExampleCategory] || 0;
                  
                  return (
                    <button
                      key={cat.id}
                      onClick={() => setSelectedCategory(cat.id as any)}
                      className={`w-full flex items-center justify-between p-3 rounded-lg transition-all ${
                        selectedCategory === cat.id
                          ? 'bg-blue-50 text-blue-700 border border-blue-200'
                          : 'hover:bg-zinc-50 text-zinc-700'
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <Icon className="w-4 h-4" />
                        <span className="font-medium">{cat.label}</span>
                      </div>
                      <span className="text-sm font-semibold">{count}</span>
                    </button>
                  );
                })}
              </div>
            </div>
            
            {/* Top Tags */}
            <div className="bg-white rounded-xl shadow-sm border border-zinc-200 p-4 mt-4">
              <h3 className="font-semibold text-zinc-900 mb-4">Popular Tags</h3>
              <div className="space-y-2">
                {stats.topTags.map(({ tag, count }) => (
                  <div key={tag} className="flex items-center justify-between">
                    <span className="text-sm text-zinc-600">#{tag}</span>
                    <span className="text-xs font-semibold text-zinc-500">{count}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
          
          {/* Examples List */}
          <div className="col-span-9">
            <div className="bg-white rounded-xl shadow-sm border border-zinc-200">
              {/* Search Bar */}
              <div className="p-4 border-b border-zinc-200">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-zinc-400 w-5 h-5" />
                  <input
                    type="text"
                    placeholder="Search examples..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 border border-zinc-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>
              
              {/* Examples Grid */}
              <div className="p-4 space-y-3 max-h-[600px] overflow-y-auto">
                {filteredExamples.map((example) => (
                  <motion.div
                    key={example.id}
                    layout
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="p-4 border border-zinc-200 rounded-lg hover:shadow-md transition-all cursor-pointer"
                    onClick={() => setSelectedExample(example)}
                  >
                    <div className="flex justify-between items-start mb-2">
                      <div className="flex-1">
                        <p className="text-sm font-medium text-zinc-900 mb-1">
                          Input: {example.input}
                        </p>
                        <p className="text-sm text-zinc-600">
                          Expected: {example.expectedOutput}
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={`px-2 py-1 text-xs rounded-full ${
                          example.quality > 0.8 ? 'bg-green-100 text-green-700' :
                          example.quality > 0.5 ? 'bg-yellow-100 text-yellow-700' :
                          'bg-red-100 text-red-700'
                        }`}>
                          {(example.quality * 100).toFixed(0)}% quality
                        </span>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            deleteExampleMutation.mutate(example.id);
                          }}
                          className="p-1 hover:bg-red-50 rounded"
                        >
                          <Trash2 className="w-4 h-4 text-red-500" />
                        </button>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-2 mt-2">
                      <span className="px-2 py-1 bg-zinc-100 text-zinc-600 text-xs rounded">
                        {example.category}
                      </span>
                      {(example.tags || []).slice(0, 3).map(tag => (
                        <span key={tag} className="px-2 py-1 bg-blue-50 text-blue-600 text-xs rounded">
                          #{tag}
                        </span>
                      ))}
                      {example.usageCount > 0 && (
                        <span className="ml-auto text-xs text-zinc-500">
                          Used {example.usageCount} times
                        </span>
                      )}
                    </div>
                  </motion.div>
                ))}
                
                {filteredExamples.length === 0 && (
                  <div className="text-center py-12 text-zinc-500">
                    No examples found. Try adjusting your filters or add a new example.
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
        
        {/* Add Example Modal */}
        <AnimatePresence>
          {isAddingExample && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
              onClick={() => setIsAddingExample(false)}
            >
              <motion.div
                initial={{ scale: 0.9 }}
                animate={{ scale: 1 }}
                exit={{ scale: 0.9 }}
                className="bg-white rounded-xl p-6 w-full max-w-2xl"
                onClick={(e) => e.stopPropagation()}
              >
                <h3 className="text-xl font-bold mb-4">Add New Example</h3>
                
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-zinc-700 mb-1">
                      User Input
                    </label>
                    <textarea
                      value={newExample.input}
                      onChange={(e) => setNewExample({ ...newExample, input: e.target.value })}
                      className="w-full p-3 border border-zinc-300 rounded-lg"
                      rows={2}
                      placeholder="e.g., 'I need something for pain relief'"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-zinc-700 mb-1">
                      Expected Response
                    </label>
                    <textarea
                      value={newExample.expectedOutput}
                      onChange={(e) => setNewExample({ ...newExample, expectedOutput: e.target.value })}
                      className="w-full p-3 border border-zinc-300 rounded-lg"
                      rows={3}
                      placeholder="e.g., 'I can help you find products for pain relief...'"
                    />
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-zinc-700 mb-1">
                        Category
                      </label>
                      <select
                        value={newExample.category}
                        onChange={(e) => setNewExample({ ...newExample, category: e.target.value as ExampleCategory })}
                        className="w-full p-2 border border-zinc-300 rounded-lg"
                      >
                        {categories.filter(c => c.id !== 'all').map(cat => (
                          <option key={cat.id} value={cat.id}>{cat.label}</option>
                        ))}
                      </select>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-zinc-700 mb-1">
                        Tags (comma-separated)
                      </label>
                      <input
                        type="text"
                        placeholder="e.g., pain, medical, indica"
                        onChange={(e) => setNewExample({ 
                          ...newExample, 
                          tags: e.target.value.split(',').map(t => t.trim()).filter(t => t)
                        })}
                        className="w-full p-2 border border-zinc-300 rounded-lg"
                      />
                    </div>
                  </div>
                  
                  <div className="flex justify-end gap-3">
                    <button
                      onClick={() => setIsAddingExample(false)}
                      className="px-4 py-2 border border-zinc-300 rounded-lg hover:bg-zinc-50"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={() => addExampleMutation.mutate(newExample)}
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                    >
                      Add Example
                    </button>
                  </div>
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </div>
  );
}