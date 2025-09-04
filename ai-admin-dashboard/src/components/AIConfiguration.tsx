import { endpoints } from '../config/endpoints';
import React, { useState } from 'react';
import {
  Settings,
  Brain,
  MessageSquare,
  Tag,
  Sliders,
  Filter,
  Plus,
  Trash2,
  Edit,
  Save,
  X,
  ToggleLeft,
  ToggleRight,
  Search,
  AlertCircle
} from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiService from '../services/api';

// Skip Words Management Component
const SkipWordsManager: React.FC = () => {
  const [newWord, setNewWord] = useState('');
  const [newCategory, setNewCategory] = useState('general');
  const [newDescription, setNewDescription] = useState('');
  const [filterCategory, setFilterCategory] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const queryClient = useQueryClient();

  // Fetch skip words
  const { data: skipWordsData, isLoading } = useQuery({
    queryKey: ['skipWords', filterCategory],
    queryFn: async () => {
      const params = filterCategory !== 'all' ? `?category=${filterCategory}` : '';
      const response = await fetch(`${endpoints.skipWords.list}${params}`);
      return response.json();
    }
  });

  // Add skip word mutation
  const addMutation = useMutation({
    mutationFn: async (data: { word: string; category: string; description: string }) => {
      const response = await fetch(endpoints.skipWords.create, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['skipWords'] });
      setNewWord('');
      setNewDescription('');
    }
  });

  // Delete skip word mutation
  const deleteMutation = useMutation({
    mutationFn: async (word: string) => {
      const response = await fetch(endpoints.skipWords.delete(word), {
        method: 'DELETE'
      });
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['skipWords'] });
    }
  });

  // Toggle skip word mutation
  const toggleMutation = useMutation({
    mutationFn: async (word: string) => {
      const response = await fetch(endpoints.skipWords.toggle(word), {
        method: 'PUT'
      });
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['skipWords'] });
    }
  });

  const categories = ['all', 'conversational', 'question', 'request', 'polite', 'action', 'greeting', 'response', 'generic'];

  const filteredWords = skipWordsData?.skip_words?.filter((word: any) =>
    word.word.toLowerCase().includes(searchTerm.toLowerCase())
  ) || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h3 className="text-xl font-bold text-gray-800 flex items-center gap-2">
            <Filter className="w-5 h-5" />
            Skip Words Management
          </h3>
          <p className="text-sm text-gray-600 mt-1">
            Words excluded from product search to improve relevance
          </p>
        </div>
        <div className="text-sm text-gray-600">
          Total: {filteredWords.length} words
        </div>
      </div>

      {/* Add New Word */}
      <div className="bg-gray-50 p-4 rounded-lg space-y-3">
        <h4 className="font-medium text-gray-700">Add New Skip Word</h4>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          <input
            type="text"
            placeholder="Word to skip"
            value={newWord}
            onChange={(e) => setNewWord(e.target.value.toLowerCase())}
            className="px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
          <select
            value={newCategory}
            onChange={(e) => setNewCategory(e.target.value)}
            className="px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            {categories.filter(c => c !== 'all').map(cat => (
              <option key={cat} value={cat}>{cat}</option>
            ))}
          </select>
          <input
            type="text"
            placeholder="Description (optional)"
            value={newDescription}
            onChange={(e) => setNewDescription(e.target.value)}
            className="px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
          <button
            onClick={() => {
              if (newWord) {
                addMutation.mutate({ word: newWord, category: newCategory, description: newDescription });
              }
            }}
            disabled={!newWord || addMutation.isPending}
            className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 disabled:bg-gray-400 flex items-center justify-center gap-2"
          >
            <Plus className="w-4 h-4" />
            Add Word
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-4">
        <div className="flex-1">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              type="text"
              placeholder="Search words..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
        </div>
        <select
          value={filterCategory}
          onChange={(e) => setFilterCategory(e.target.value)}
          className="px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
        >
          {categories.map(cat => (
            <option key={cat} value={cat}>
              {cat === 'all' ? 'All Categories' : cat}
            </option>
          ))}
        </select>
      </div>

      {/* Skip Words List */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Word
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Category
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Description
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {isLoading ? (
                <tr>
                  <td colSpan={5} className="px-6 py-4 text-center text-gray-500">
                    Loading skip words...
                  </td>
                </tr>
              ) : filteredWords.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-4 text-center text-gray-500">
                    No skip words found
                  </td>
                </tr>
              ) : (
                filteredWords.map((word: any) => (
                  <tr key={word.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="font-mono text-sm">{word.word}</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="px-2 py-1 text-xs rounded-full bg-gray-100 text-gray-800">
                        {word.category}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      {word.description || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <button
                        onClick={() => toggleMutation.mutate(word.word)}
                        className="flex items-center gap-1"
                      >
                        {word.active ? (
                          <>
                            <ToggleRight className="w-5 h-5 text-green-600" />
                            <span className="text-xs text-green-600">Active</span>
                          </>
                        ) : (
                          <>
                            <ToggleLeft className="w-5 h-5 text-gray-400" />
                            <span className="text-xs text-gray-400">Inactive</span>
                          </>
                        )}
                      </button>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right">
                      <button
                        onClick={() => {
                          if (confirm(`Delete skip word "${word.word}"?`)) {
                            deleteMutation.mutate(word.word);
                          }
                        }}
                        className="text-red-600 hover:text-red-800"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

// Medical Intents Manager Component
const MedicalIntentsManager: React.FC = () => {
  const [selectedIntent, setSelectedIntent] = useState<any>(null);
  const [newKeyword, setNewKeyword] = useState('');
  const queryClient = useQueryClient();

  // Fetch medical intents
  const { data: intentsData, isLoading } = useQuery({
    queryKey: ['medicalIntents'],
    queryFn: async () => {
      const response = await fetch(endpoints.medicalIntents);
      return response.json();
    }
  });

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h3 className="text-xl font-bold text-gray-800 flex items-center gap-2">
            <Brain className="w-5 h-5" />
            Medical Intents Configuration
          </h3>
          <p className="text-sm text-gray-600 mt-1">
            Configure medical conditions and their product mappings
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Intents List */}
        <div className="bg-white rounded-lg shadow">
          <div className="p-4 border-b">
            <h4 className="font-medium text-gray-700">Medical Intents</h4>
          </div>
          <div className="p-4 space-y-2">
            {intentsData?.intents?.map((intent: any) => (
              <div
                key={intent.id}
                onClick={() => setSelectedIntent(intent)}
                className={`p-3 rounded-lg cursor-pointer transition-colors ${
                  selectedIntent?.id === intent.id
                    ? 'bg-indigo-50 border-indigo-300'
                    : 'bg-gray-50 hover:bg-gray-100'
                } border`}
              >
                <div className="flex justify-between items-start">
                  <div>
                    <h5 className="font-medium text-gray-800">{intent.intent_name}</h5>
                    <p className="text-sm text-gray-600 mt-1">{intent.description}</p>
                    <p className="text-xs text-gray-500 mt-2">
                      Search: <span className="font-mono">{intent.search_query}</span>
                    </p>
                  </div>
                  <span className={`px-2 py-1 text-xs rounded-full ${
                    intent.active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'
                  }`}>
                    {intent.active ? 'Active' : 'Inactive'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Keywords Management */}
        <div className="bg-white rounded-lg shadow">
          <div className="p-4 border-b">
            <h4 className="font-medium text-gray-700">
              Keywords for {selectedIntent?.intent_name || 'Select an intent'}
            </h4>
          </div>
          {selectedIntent ? (
            <div className="p-4 space-y-4">
              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder="Add keyword"
                  value={newKeyword}
                  onChange={(e) => setNewKeyword(e.target.value)}
                  className="flex-1 px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
                <button className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700">
                  <Plus className="w-4 h-4" />
                </button>
              </div>
              <div className="space-y-2">
                {selectedIntent.keywords?.map((keyword: any) => (
                  <div key={keyword} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                    <span className="font-mono text-sm">{keyword}</span>
                    <button className="text-red-600 hover:text-red-800">
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="p-8 text-center text-gray-500">
              Select an intent to manage keywords
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// System Configuration Component
const SystemConfigManager: React.FC = () => {
  const [editingConfig, setEditingConfig] = useState<any>(null);
  const queryClient = useQueryClient();

  // Fetch system config
  const { data: configData, isLoading } = useQuery({
    queryKey: ['systemConfig'],
    queryFn: async () => {
      const response = await fetch(endpoints.systemConfig);
      return response.json();
    }
  });

  const configCategories = {
    search: { icon: Search, color: 'blue' },
    response: { icon: MessageSquare, color: 'green' },
    model: { icon: Brain, color: 'purple' },
    cache: { icon: Settings, color: 'orange' }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h3 className="text-xl font-bold text-gray-800 flex items-center gap-2">
            <Sliders className="w-5 h-5" />
            System Configuration
          </h3>
          <p className="text-sm text-gray-600 mt-1">
            Core system parameters and settings
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {configData?.configs?.map((config: any) => {
          const Icon = configCategories[config.category as keyof typeof configCategories]?.icon || Settings;
          const color = configCategories[config.category as keyof typeof configCategories]?.color || 'gray';
          
          return (
            <div key={config.id} className="bg-white rounded-lg shadow p-4">
              <div className="flex items-start justify-between mb-3">
                <Icon className={`w-5 h-5 text-${color}-600`} />
                <span className={`px-2 py-1 text-xs rounded-full bg-${color}-100 text-${color}-800`}>
                  {config.category}
                </span>
              </div>
              <h4 className="font-medium text-gray-800 mb-1">{config.config_key}</h4>
              <p className="text-xs text-gray-600 mb-3">{config.description}</p>
              
              {editingConfig?.id === config.id ? (
                <div className="flex gap-2">
                  <input
                    type={config.config_type === 'integer' ? 'number' : 'text'}
                    value={editingConfig.value}
                    onChange={(e) => setEditingConfig({ ...editingConfig, value: e.target.value })}
                    className="flex-1 px-2 py-1 text-sm border rounded focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                  <button
                    onClick={() => {
                      // Save logic here
                      setEditingConfig(null);
                    }}
                    className="text-green-600 hover:text-green-800"
                  >
                    <Save className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => setEditingConfig(null)}
                    className="text-gray-600 hover:text-gray-800"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ) : (
                <div className="flex items-center justify-between">
                  <span className="font-mono text-sm text-indigo-600">{config.config_value}</span>
                  <button
                    onClick={() => setEditingConfig({ id: config.id, value: config.config_value })}
                    className="text-gray-600 hover:text-gray-800"
                  >
                    <Edit className="w-4 h-4" />
                  </button>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

// Main AI Configuration Component
const AIConfiguration: React.FC = () => {
  const [activeTab, setActiveTab] = useState('skip-words');

  const tabs = [
    { id: 'skip-words', label: 'Skip Words', icon: Filter },
    { id: 'medical-intents', label: 'Medical Intents', icon: Brain },
    { id: 'system-config', label: 'System Config', icon: Sliders }
  ];

  return (
    <div className="p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-800">AI Configuration</h2>
        <p className="text-gray-600 mt-1">
          Manage AI engine behavior and search parameters
        </p>
      </div>

      {/* Tabs */}
      <div className="border-b mb-6">
        <div className="flex space-x-8">
          {tabs.map(tab => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 pb-3 px-1 border-b-2 transition-colors ${
                  activeTab === tab.id
                    ? 'border-indigo-600 text-indigo-600'
                    : 'border-transparent text-gray-600 hover:text-gray-800'
                }`}
              >
                <Icon className="w-4 h-4" />
                {tab.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Tab Content */}
      <div>
        {activeTab === 'skip-words' && <SkipWordsManager />}
        {activeTab === 'medical-intents' && <MedicalIntentsManager />}
        {activeTab === 'system-config' && <SystemConfigManager />}
      </div>
    </div>
  );
};

export default AIConfiguration;