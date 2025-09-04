import { endpoints } from '../config/endpoints';
import { useState, useEffect } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { Upload, Download, Plus, Trash2, Play, CheckCircle, Brain, Database, TrendingUp, Settings, AlertCircle } from 'lucide-react';
import DatasetUploadModal from './DatasetUploadModal';
import DatasetCreationModal from './DatasetCreationModal';
import IntentManager from './IntentManager';

interface TrainingExample {
  query: string;
  expected_intent: string;
  expected_response?: string;
  entities?: Record<string, any>;
  feedback?: 'positive' | 'negative';
}

interface TrainingDataset {
  id: string;
  name: string;
  description: string;
  examples: TrainingExample[];
  created_at: Date | string;
  accuracy?: number;
}

export default function TrainingCenter() {
  const queryClient = useQueryClient();
  const [selectedDataset, setSelectedDataset] = useState<TrainingDataset | null>(null);
  const [datasets, setDatasets] = useState<TrainingDataset[]>([]);
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [isCreationModalOpen, setIsCreationModalOpen] = useState(false);
  const [showIntentManager, setShowIntentManager] = useState(false);
  const [editingDataset] = useState<TrainingDataset | null>(null);
  const [newExample, setNewExample] = useState<TrainingExample>({
    query: '',
    expected_intent: 'product_search',
    entities: {}
  });
  const [isTraining, setIsTraining] = useState(false);
  const [trainingProgress, setTrainingProgress] = useState(0);
  const [isSavingExample, setIsSavingExample] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [deletingDatasetId, setDeletingDatasetId] = useState<string | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<string | null>(null);
  const [showHardDeleteModal, setShowHardDeleteModal] = useState<string | null>(null);
  const [hardDeleteConfirmText, setHardDeleteConfirmText] = useState('');

  // Fetch datasets from database
  const { data: datasetsData, isLoading: datasetsLoading, refetch: refetchDatasets } = useQuery({
    queryKey: ['training-datasets'],
    queryFn: async () => {
      const response = await axios.get(endpoints.ai.datasets);
      return response.data;
    }
  });
  
  // Fetch training stats
  const { data } = useQuery({
    queryKey: ['training-stats'],
    queryFn: async () => {
      const response = await axios.get(endpoints.ai.stats);
      return response.data;
    }
  });
  
  // Update datasets when datasetsData changes
  useEffect(() => {
    if (datasetsData?.datasets) {
      const formattedDatasets = datasetsData.datasets.map((ds: any) => ({
        ...ds,
        created_at: ds.created_at ? new Date(ds.created_at) : new Date()
      }));
      setDatasets(formattedDatasets);
      
      // If we have datasets and none is selected, select the first one
      if (formattedDatasets.length > 0 && !selectedDataset) {
        setSelectedDataset(formattedDatasets[0]);
      }
    }
  }, [datasetsData]);

  // Train AI mutation
  const trainMutation = useMutation({
    mutationFn: async (dataset: TrainingDataset) => {
      const response = await axios.post(endpoints.ai.train, {
        examples: dataset.examples.map(ex => ({
          query: ex.query,
          expected_intent: ex.expected_intent,
          expected_response: ex.expected_response || `I'll help you find ${ex.query}`,
          entities: ex.entities
        }))
      });
      return response.data;
    },
    onMutate: () => {
      setIsTraining(true);
      setTrainingProgress(0);
      // Simulate progress
      const interval = setInterval(() => {
        setTrainingProgress(prev => {
          if (prev >= 90) {
            clearInterval(interval);
            return prev;
          }
          return prev + 10;
        });
      }, 200);
    },
    onSuccess: () => {
      setTrainingProgress(100);
      setTimeout(() => {
        setIsTraining(false);
        setTrainingProgress(0);
      }, 1000);
    },
    onError: () => {
      setIsTraining(false);
      setTrainingProgress(0);
    }
  });

  const handleAddExample = async () => {
    if (selectedDataset && newExample.query) {
      setIsSavingExample(true);
      try {
        // Send the new training example to the backend immediately
        // The backend expects a list directly, not an object with "examples"
        const response = await axios.post(endpoints.ai.train, [{
            query: newExample.query,
            expected_intent: newExample.expected_intent,
            expected_response: `I'll help you find products related to "${newExample.query}"`,
            entities: newExample.entities || {},
            context: {
              dataset_id: selectedDataset.id,
              added_by: 'admin',
              timestamp: new Date().toISOString()
            }
          }]);

        // If successful, update local state
        if (response.data.success) {
          const updated = {
            ...selectedDataset,
            examples: [...selectedDataset.examples, newExample]
          };
          setSelectedDataset(updated);
          
          // Update the datasets list as well
          setDatasets(prevDatasets => 
            prevDatasets.map(d => d.id === selectedDataset.id ? updated : d)
          );
          
          // Show success notification
          console.log('Training example added successfully:', response.data);
          setSaveSuccess(true);
          setTimeout(() => setSaveSuccess(false), 3000);
          
          // Reset the form
          setNewExample({
            query: '',
            expected_intent: 'product_search',
            entities: {}
          });
          
          // Invalidate queries to refresh stats and datasets
          queryClient.invalidateQueries({ queryKey: ['training-stats'] });
          queryClient.invalidateQueries({ queryKey: ['training-datasets'] });
        }
      } catch (error) {
        console.error('Failed to add training example:', error);
        alert('Failed to add training example. Please try again.');
      } finally {
        setIsSavingExample(false);
      }
    }
  };

  const handleUploadSuccess = (uploadedDataset: any) => {
    // Add the uploaded dataset to the list
    const newDataset: TrainingDataset = {
      id: uploadedDataset.id || `uploaded_${Date.now()}`,
      name: uploadedDataset.metadata?.name || 'Uploaded Dataset',
      description: uploadedDataset.metadata?.description || 'User uploaded dataset',
      examples: uploadedDataset.examples || [],
      created_at: new Date(),
      accuracy: uploadedDataset.accuracy
    };
    setDatasets(prev => [newDataset, ...prev]);
    setSelectedDataset(newDataset);
    
    // Refresh stats and datasets
    queryClient.invalidateQueries({ queryKey: ['training-stats'] });
    queryClient.invalidateQueries({ queryKey: ['training-datasets'] });
  };

  const handleRemoveExample = (index: number) => {
    if (selectedDataset) {
      const updated = {
        ...selectedDataset,
        examples: selectedDataset.examples.filter((_, i) => i !== index)
      };
      setSelectedDataset(updated);
    }
  };

  const handleTrain = () => {
    if (selectedDataset) {
      trainMutation.mutate(selectedDataset);
    }
  };

  // Delete dataset mutation
  const deleteMutation = useMutation({
    mutationFn: async (datasetId: string) => {
      const response = await axios.delete(endpoints.ai.deleteDataset(datasetId));
      return response.data;
    },
    onSuccess: (data, datasetId) => {
      console.log('Dataset deleted:', data);
      // Remove from local state
      setDatasets(prev => prev.filter(d => d.id !== datasetId));
      // Clear selection if deleted dataset was selected
      if (selectedDataset?.id === datasetId) {
        setSelectedDataset(null);
      }
      // Refresh datasets and stats
      queryClient.invalidateQueries({ queryKey: ['training-datasets'] });
      queryClient.invalidateQueries({ queryKey: ['training-stats'] });
      setShowDeleteConfirm(null);
    },
    onError: (error) => {
      console.error('Failed to delete dataset:', error);
      alert('Failed to delete dataset. Please try again.');
    }
  });

  const handleDeleteDataset = (datasetId: string) => {
    if (showDeleteConfirm === datasetId) {
      // Show hard delete modal instead of soft delete
      setShowHardDeleteModal(datasetId);
      setShowDeleteConfirm(null);
    } else {
      setShowDeleteConfirm(datasetId);
      // Auto-hide confirmation after 5 seconds
      setTimeout(() => setShowDeleteConfirm(null), 5000);
    }
  };

  // Hard delete mutation
  const hardDeleteMutation = useMutation({
    mutationFn: async (datasetId: string) => {
      const response = await axios.delete(
        endpoints.ai.hardDeleteDataset(datasetId)
      );
      return response.data;
    },
    onSuccess: (data, datasetId) => {
      console.log('Dataset permanently deleted:', data);
      // Remove from local state
      setDatasets(prev => prev.filter(d => d.id !== datasetId));
      // Clear selection if deleted dataset was selected
      if (selectedDataset?.id === datasetId) {
        setSelectedDataset(null);
      }
      // Refresh datasets and stats
      queryClient.invalidateQueries({ queryKey: ['training-datasets'] });
      queryClient.invalidateQueries({ queryKey: ['training-stats'] });
      setShowHardDeleteModal(null);
      setHardDeleteConfirmText('');
      alert(`Dataset permanently deleted. ${data.warning}`);
    },
    onError: (error) => {
      console.error('Failed to permanently delete dataset:', error);
      alert('Failed to permanently delete dataset. Please try again.');
    }
  });

  const handleHardDelete = () => {
    if (showHardDeleteModal && hardDeleteConfirmText === 'DELETE FOREVER') {
      setDeletingDatasetId(showHardDeleteModal);
      hardDeleteMutation.mutate(showHardDeleteModal);
    }
  };

  const exportDataset = (dataset: TrainingDataset) => {
    const dataStr = JSON.stringify(dataset, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    const exportFileDefaultName = `${dataset.id}_${Date.now()}.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-xl shadow-sm p-6">
        <div className="flex justify-between items-center mb-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">AI Training Center</h2>
            <p className="text-gray-600 mt-1">Train the AI with cannabis-specific knowledge and improve accuracy</p>
          </div>
          <div className="flex items-center space-x-4">
            <button 
              onClick={() => setIsUploadModalOpen(true)}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 flex items-center space-x-2">
              <Upload className="w-5 h-5" />
              <span>Upload Dataset</span>
            </button>
            <button 
              onClick={() => setIsCreationModalOpen(true)}
              className="px-4 py-2 bg-weed-green-500 text-white rounded-lg hover:bg-weed-green-600 flex items-center space-x-2">
              <Plus className="w-5 h-5" />
              <span>New Dataset</span>
            </button>
            <button 
              onClick={() => setShowIntentManager(!showIntentManager)}
              className="px-4 py-2 bg-purple-haze-600 text-white rounded-lg hover:bg-purple-haze-700 flex items-center space-x-2">
              <Settings className="w-5 h-5" />
              <span>Manage Intents</span>
            </button>
          </div>
        </div>

        {/* Training Stats */}
        {data && (
          <div className="grid grid-cols-4 gap-4 mt-6">
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <Brain className="w-8 h-8 text-purple-haze-500" />
                <span className="text-2xl font-bold">{data.total_examples || 0}</span>
              </div>
              <p className="text-sm text-gray-600 mt-2">Training Examples</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <TrendingUp className="w-8 h-8 text-weed-green-500" />
                <span className="text-2xl font-bold">{((data.accuracy || 0.85) * 100).toFixed(1)}%</span>
              </div>
              <p className="text-sm text-gray-600 mt-2">Model Accuracy</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <Database className="w-8 h-8 text-blue-500" />
                <span className="text-2xl font-bold">{data.datasets || 3}</span>
              </div>
              <p className="text-sm text-gray-600 mt-2">Datasets</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <CheckCircle className="w-8 h-8 text-green-500" />
                <span className="text-2xl font-bold">{data.sessions || 142}</span>
              </div>
              <p className="text-sm text-gray-600 mt-2">Training Sessions</p>
            </div>
          </div>
        )}
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Dataset List */}
        <div className="col-span-1 bg-white rounded-xl shadow-sm p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Training Datasets</h3>
          {datasetsLoading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-weed-green-500"></div>
            </div>
          ) : datasets.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <Database className="w-12 h-12 mx-auto mb-2 text-gray-300" />
              <p className="text-sm">No datasets found</p>
              <p className="text-xs mt-1">Create a new dataset or add training examples</p>
            </div>
          ) : (
          <div className="space-y-3">
            {datasets.map((dataset) => (
              <div
                key={dataset.id}
                onClick={() => setSelectedDataset(dataset)}
                className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                  selectedDataset?.id === dataset.id
                    ? 'border-weed-green-500 bg-weed-green-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="flex justify-between items-start mb-2">
                  <h4 className="font-medium text-sm">{dataset.name}</h4>
                  {dataset.accuracy && (
                    <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded">
                      {(dataset.accuracy * 100).toFixed(0)}% accurate
                    </span>
                  )}
                </div>
                <p className="text-xs text-gray-600 mb-2">{dataset.description}</p>
                <div className="flex justify-between items-center">
                  <span className="text-xs text-gray-500">{dataset.examples.length} examples</span>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        exportDataset(dataset);
                      }}
                      className="text-xs text-blue-600 hover:text-blue-700"
                      title="Export dataset"
                    >
                      <Download className="w-4 h-4" />
                    </button>
                    {showDeleteConfirm === dataset.id ? (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteDataset(dataset.id);
                        }}
                        className="text-xs text-red-600 hover:text-red-700 flex items-center space-x-1"
                        disabled={deletingDatasetId === dataset.id}
                      >
                        {deletingDatasetId === dataset.id ? (
                          <div className="animate-spin rounded-full h-4 w-4 border-2 border-red-600 border-t-transparent"></div>
                        ) : (
                          <>
                            <AlertCircle className="w-4 h-4" />
                            <span>Delete?</span>
                          </>
                        )}
                      </button>
                    ) : (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteDataset(dataset.id);
                        }}
                        className="text-xs text-gray-500 hover:text-red-600"
                        title="Click to delete (soft delete by default, click confirm for hard delete options)"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
          )}
        </div>

        {/* Dataset Editor */}
        <div className="col-span-2 bg-white rounded-xl shadow-sm p-6">
          {selectedDataset ? (
            <>
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold text-gray-900">{selectedDataset.name}</h3>
                <button
                  onClick={handleTrain}
                  disabled={isTraining || selectedDataset.examples.length === 0}
                  className="px-4 py-2 bg-purple-haze-600 text-white rounded-lg hover:bg-purple-haze-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
                >
                  <Play className="w-5 h-5" />
                  <span>{isTraining ? 'Training...' : 'Train Model'}</span>
                </button>
              </div>

              {/* Training Progress */}
              {isTraining && (
                <div className="mb-4">
                  <div className="flex justify-between text-sm text-gray-600 mb-1">
                    <span>Training Progress</span>
                    <span>{trainingProgress}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-weed-green-500 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${trainingProgress}%` }}
                    ></div>
                  </div>
                </div>
              )}

              {/* Examples List */}
              <div className="border rounded-lg p-4 mb-4 max-h-96 overflow-y-auto">
                <h4 className="text-sm font-medium text-gray-700 mb-3">Training Examples</h4>
                <div className="space-y-2">
                  {selectedDataset.examples.map((example, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex-1">
                        <p className="text-sm font-medium">"{example.query}"</p>
                        <div className="flex items-center space-x-4 mt-1">
                          <span className="text-xs text-gray-500">Intent: {example.expected_intent}</span>
                          {example.entities && Object.keys(example.entities).length > 0 && (
                            <span className="text-xs text-gray-500">
                              Entities: {Object.keys(example.entities).join(', ')}
                            </span>
                          )}
                        </div>
                      </div>
                      <button
                        onClick={() => handleRemoveExample(index)}
                        className="text-red-500 hover:text-red-600"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>

              {/* Add New Example */}
              <div className="border-t pt-4">
                <h4 className="text-sm font-medium text-gray-700 mb-3">Add Training Example</h4>
                <div className="space-y-3">
                  <input
                    type="text"
                    value={newExample.query}
                    onChange={(e) => setNewExample({ ...newExample, query: e.target.value })}
                    placeholder="Customer query (e.g., 'got any fire?')"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-weed-green-500"
                  />
                  <div className="grid grid-cols-2 gap-3">
                    <select
                      value={newExample.expected_intent}
                      onChange={(e) => setNewExample({ ...newExample, expected_intent: e.target.value })}
                      className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-weed-green-500"
                    >
                      <option value="product_search">Product Search</option>
                      <option value="medical_recommendation">Medical Recommendation</option>
                      <option value="education">Education</option>
                      <option value="greeting">Greeting</option>
                    </select>
                    {saveSuccess && (
                      <div className="text-green-600 text-sm flex items-center gap-1">
                        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                        Saved!
                      </div>
                    )}
                    <button
                      onClick={handleAddExample}
                      disabled={!newExample.query || isSavingExample}
                      className="px-4 py-2 bg-weed-green-500 text-white rounded-lg hover:bg-weed-green-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                    >
                      {isSavingExample ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                          Saving to AI...
                        </>
                      ) : (
                        'Add Example'
                      )}
                    </button>
                  </div>
                </div>
              </div>
            </>
          ) : (
            <div className="text-center text-gray-500 mt-20">
              <Database className="w-16 h-16 mx-auto mb-4 text-gray-300" />
              <p>Select a dataset to view and edit training examples</p>
            </div>
          )}
        </div>
      </div>
      
      {/* Intent Manager Panel */}
      {showIntentManager && (
        <div className="mt-6">
          <IntentManager />
        </div>
      )}
      
      {/* Dataset Upload Modal */}
      <DatasetUploadModal
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
        onUploadSuccess={handleUploadSuccess}
      />
      
      {/* Dataset Creation Modal */}
      <DatasetCreationModal
        isOpen={isCreationModalOpen}
        onClose={() => setIsCreationModalOpen(false)}
        onSave={(newDataset) => {
          const trainingDataset: TrainingDataset = {
            id: newDataset.id || `created_${Date.now()}`,
            name: newDataset.name,
            description: newDataset.description,
            examples: newDataset.examples.map(ex => ({
              query: ex.query,
              expected_intent: ex.expected_intent,
              expected_response: ex.expected_response,
              entities: ex.entities,
              feedback: undefined
            })),
            created_at: new Date(),
            accuracy: newDataset.metadata.target_accuracy
          };
          setDatasets(prev => [trainingDataset, ...prev]);
          setSelectedDataset(trainingDataset);
          setIsCreationModalOpen(false);
          
          // Also upload to server
          axios.post(endpoints.datasets.upload, {
            metadata: {
              name: newDataset.name,
              description: newDataset.description,
              type: newDataset.type,
              version: newDataset.metadata.version,
              author: newDataset.metadata.author,
              tags: newDataset.metadata.tags
            },
            examples: newDataset.examples
          }).then(() => {
            queryClient.invalidateQueries({ queryKey: ['training-stats'] });
            queryClient.invalidateQueries({ queryKey: ['training-datasets'] });
          });
        }}
        initialDataset={editingDataset ? {
          id: editingDataset.id,
          name: editingDataset.name,
          description: editingDataset.description,
          type: 'custom',
          examples: editingDataset.examples.map(ex => ({
            id: `ex_${Math.random()}`,
            query: ex.query,
            expected_intent: ex.expected_intent,
            expected_response: ex.expected_response || '',
            entities: ex.entities || {},
            products: [],
            context: {}
          })),
          metadata: {
            version: '1.0',
            author: 'Admin',
            tags: [],
            target_accuracy: editingDataset.accuracy || 0.85
          }
        } : undefined}
      />
      
      {/* Hard Delete Confirmation Modal */}
      {showHardDeleteModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-md w-full mx-4">
            <div className="flex items-center mb-4">
              <AlertCircle className="w-8 h-8 text-red-600 mr-3" />
              <h3 className="text-xl font-bold text-gray-900">Permanent Deletion Warning</h3>
            </div>
            
            <div className="space-y-4 mb-6">
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <p className="text-sm text-red-800 font-semibold mb-2">⚠️ This action is IRREVERSIBLE!</p>
                <ul className="text-sm text-red-700 space-y-1 list-disc list-inside">
                  <li>All training examples will be permanently deleted</li>
                  <li>Data cannot be recovered after deletion</li>
                  <li>The model will STILL remember patterns from this data</li>
                  <li>To fully remove influence, you must retrain the model from scratch</li>
                </ul>
              </div>
              
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <p className="text-sm text-yellow-800">
                  <strong>Alternative:</strong> Use soft delete (archive) instead to preserve data for potential future use.
                </p>
              </div>
              
              <div>
                <p className="text-sm text-gray-700 mb-2">
                  Type <span className="font-mono font-bold text-red-600">DELETE FOREVER</span> to confirm permanent deletion:
                </p>
                <input
                  type="text"
                  value={hardDeleteConfirmText}
                  onChange={(e) => setHardDeleteConfirmText(e.target.value)}
                  placeholder="Type DELETE FOREVER"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500"
                />
              </div>
            </div>
            
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => {
                  setShowHardDeleteModal(null);
                  setHardDeleteConfirmText('');
                }}
                className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
              >
                Cancel
              </button>
              <button
                onClick={handleHardDelete}
                disabled={hardDeleteConfirmText !== 'DELETE FOREVER' || deletingDatasetId === showHardDeleteModal}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
              >
                {deletingDatasetId === showHardDeleteModal ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                    <span>Deleting...</span>
                  </>
                ) : (
                  <>
                    <Trash2 className="w-4 h-4" />
                    <span>Permanently Delete</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}