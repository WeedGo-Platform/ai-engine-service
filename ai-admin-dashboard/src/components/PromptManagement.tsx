import React, { useState, useEffect, useCallback, Fragment } from 'react';
import { Dialog, Transition, Tab } from '@headlessui/react';
import {
  Settings,
  FileText,
  Edit,
  Trash2,
  Save,
  X,
  Plus,
  Play,
  Download,
  Upload,
  RefreshCw,
  Search,
  Filter,
  Check,
  AlertTriangle,
  AlertCircle,
  Copy,
  Archive,
  RotateCcw,
  Code,
  CheckCircle,
  XCircle
} from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import clsx from 'clsx';

interface PromptTemplate {
  id: string;
  template: string;
  variables: string[];
  output_format?: string;
  required_fields?: string[];
  optional_fields?: string[];
  valid_outputs?: string[];
  max_length?: number;
  allow_empty?: boolean;
  max_items?: number;
  _multilingual?: boolean;
  _languages?: any;
}

interface PromptFile {
  filename: string;
  name: string;
  prompts: Record<string, PromptTemplate>;
  last_modified?: string;
  size?: number;
  size_bytes?: number;
  backup_available?: boolean;
  description?: string;
  prompt_count?: number;
  isMultilingual?: boolean;
}

interface TestResult {
  success: boolean;
  output: any;
  error?: string;
  execution_time?: number;
  tokens_used?: number;
}

const PromptManagement: React.FC = () => {
  const queryClient = useQueryClient();
  const [selectedFile, setSelectedFile] = useState<PromptFile | null>(null);
  const [selectedPrompt, setSelectedPrompt] = useState<string | null>(null);
  const [editMode, setEditMode] = useState(false);
  const [editedTemplate, setEditedTemplate] = useState<PromptTemplate | null>(null);
  const [testDialogOpen, setTestDialogOpen] = useState(false);
  const [testVariables, setTestVariables] = useState<Record<string, string>>({});
  const [testResult, setTestResult] = useState<TestResult | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterCategory, setFilterCategory] = useState('all');
  const [backupDialogOpen, setBackupDialogOpen] = useState(false);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [newPromptData, setNewPromptData] = useState({
    id: '',
    template: '',
    variables: '',
    output_format: 'text'
  });
  const [autoFormat, setAutoFormat] = useState(true);

  // Fetch prompt files
  const { data: files, isLoading } = useQuery({
    queryKey: ['prompt-files'],
    queryFn: async () => {
      const response = await fetch('http://localhost:5024/api/v1/prompts/files');
      if (!response.ok) throw new Error('Failed to load prompt files');
      const data = await response.json();
      return data.files as PromptFile[];
    }
  });

  // Set selected file on load
  useEffect(() => {
    if (files && files.length > 0 && !selectedFile) {
      setSelectedFile(files[0]);
    }
  }, [files, selectedFile]);

  // Save prompt mutation
  const savePromptMutation = useMutation({
    mutationFn: async ({ filename, promptId, data }: { filename: string; promptId: string; data: PromptTemplate }) => {
      const response = await fetch(`http://localhost:5024/api/v1/prompts/${filename}/${promptId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      if (!response.ok) throw new Error('Failed to save prompt');
      return response.json();
    },
    onSuccess: () => {
      toast.success('Prompt saved successfully');
      queryClient.invalidateQueries({ queryKey: ['prompt-files'] });
      setEditMode(false);
    },
    onError: () => {
      toast.error('Failed to save prompt');
    }
  });

  // Test prompt mutation
  const testPromptMutation = useMutation({
    mutationFn: async ({ template, variables }: { template: string; variables: Record<string, string> }) => {
      const response = await fetch('http://localhost:5024/api/v1/prompts/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ template, variables })
      });
      if (!response.ok) throw new Error('Failed to test prompt');
      return response.json() as Promise<TestResult>;
    },
    onSuccess: (data) => {
      setTestResult(data);
    },
    onError: (error) => {
      setTestResult({
        success: false,
        output: null,
        error: error instanceof Error ? error.message : 'Unknown error'
      });
    }
  });

  // Create backup mutation
  const createBackupMutation = useMutation({
    mutationFn: async (filename: string) => {
      const response = await fetch(`http://localhost:5024/api/v1/prompts/backups/${filename}`, {
        method: 'POST'
      });
      if (!response.ok) throw new Error('Failed to create backup');
      return response.json();
    },
    onSuccess: (data) => {
      toast.success(`Backup created: ${data.backup_file}`);
      queryClient.invalidateQueries({ queryKey: ['prompt-files'] });
      setBackupDialogOpen(false);
    },
    onError: () => {
      toast.error('Failed to create backup');
    }
  });

  // Create prompt mutation
  const createPromptMutation = useMutation({
    mutationFn: async ({ filename, data }: { filename: string; data: PromptTemplate }) => {
      const response = await fetch(`http://localhost:5024/api/v1/prompts/${filename}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id: data.id,
          data: data
        })
      });
      if (!response.ok) throw new Error('Failed to create prompt');
      return response.json();
    },
    onSuccess: () => {
      toast.success('Prompt created successfully');
      queryClient.invalidateQueries({ queryKey: ['prompt-files'] });
      setCreateDialogOpen(false);
      setNewPromptData({ id: '', template: '', variables: '', output_format: 'text' });
    },
    onError: () => {
      toast.error('Failed to create prompt');
    }
  });

  // Delete prompt mutation
  const deletePromptMutation = useMutation({
    mutationFn: async ({ filename, promptId }: { filename: string; promptId: string }) => {
      const response = await fetch(`http://localhost:5024/api/v1/prompts/${filename}/${promptId}`, {
        method: 'DELETE'
      });
      if (!response.ok) throw new Error('Failed to delete prompt');
      return response.json();
    },
    onSuccess: () => {
      toast.success('Prompt deleted successfully');
      queryClient.invalidateQueries({ queryKey: ['prompt-files'] });
      if (selectedPrompt === deletePromptMutation.variables?.promptId) {
        setSelectedPrompt(null);
        setEditedTemplate(null);
      }
    },
    onError: () => {
      toast.error('Failed to delete prompt');
    }
  });

  const handleFileSelect = async (file: PromptFile) => {
    // Fetch the file content with prompts
    try {
      const response = await fetch(`http://localhost:5024/api/v1/prompts/files/${file.name || file.filename}`);
      if (response.ok) {
        const data = await response.json();
        
        // Check if this is a multilingual prompt file
        const isMultilingual = file.name === 'multilingual_prompts.json' || 
          (data.content && Object.values(data.content).some(p => 
            typeof p === 'object' && ('en' in p || 'es' in p || 'fr' in p)
          ));
        
        if (isMultilingual) {
          // Handle multilingual prompts differently
          const transformedPrompts: Record<string, PromptTemplate> = {};
          
          Object.entries(data.content || {}).forEach(([promptId, langData]: [string, any]) => {
            // For multilingual, we'll show the English version as the main template
            // and indicate it's multilingual
            const englishData = langData.en || langData;
            transformedPrompts[promptId] = {
              id: promptId,
              template: englishData.template || `[Multilingual: ${Object.keys(langData).join(', ')}]`,
              variables: englishData.variables || [],
              output_format: englishData.output_format || 'text',
              _multilingual: true,
              _languages: langData
            };
          });
          
          const fileWithPrompts = {
            ...file,
            prompts: transformedPrompts,
            isMultilingual: true
          };
          setSelectedFile(fileWithPrompts);
          
          // Auto-select the first prompt if available
          const promptIds = Object.keys(transformedPrompts);
          if (promptIds.length > 0) {
            const firstPromptId = promptIds[0];
            setSelectedPrompt(firstPromptId);
            setEditedTemplate(transformedPrompts[firstPromptId]);
          }
        } else {
          // Handle standard prompts
          const fileWithPrompts = {
            ...file,
            prompts: data.content || {},
            isMultilingual: false
          };
          setSelectedFile(fileWithPrompts);
          
          // Auto-select the first prompt if available
          const promptIds = Object.keys(data.content || {});
          if (promptIds.length > 0) {
            const firstPromptId = promptIds[0];
            setSelectedPrompt(firstPromptId);
            setEditedTemplate({ 
              ...data.content[firstPromptId], 
              id: firstPromptId,
              variables: data.content[firstPromptId].variables || []
            });
          }
        }
      } else {
        setSelectedFile(file);
      }
    } catch (error) {
      console.error('Error fetching file content:', error);
      setSelectedFile(file);
    }
    setEditMode(false);
  };

  const handlePromptSelect = (promptId: string) => {
    setSelectedPrompt(promptId);
    setEditMode(false);
    if (selectedFile && selectedFile.prompts[promptId]) {
      setEditedTemplate({ 
        ...selectedFile.prompts[promptId], 
        id: promptId,
        variables: selectedFile.prompts[promptId].variables || []
      });
    }
  };

  const handleSavePrompt = () => {
    if (!selectedFile || !selectedPrompt || !editedTemplate) return;
    savePromptMutation.mutate({
      filename: selectedFile.name || selectedFile.name || selectedFile.filename,
      promptId: selectedPrompt,
      data: editedTemplate
    });
  };

  const handleTestPrompt = () => {
    if (!editedTemplate) return;
    testPromptMutation.mutate({
      template: editedTemplate.template,
      variables: testVariables
    });
  };

  const handleCreateBackup = () => {
    if (!selectedFile) return;
    createBackupMutation.mutate(selectedFile.name || selectedFile.filename);
  };

  const handleCreatePrompt = () => {
    if (!selectedFile || !newPromptData.id || !newPromptData.template) {
      toast.error('Please fill in all required fields');
      return;
    }

    const variables = newPromptData.variables ? newPromptData.variables.split(',').map(v => v.trim()).filter(v => v) : [];
    const promptData: PromptTemplate = {
      id: newPromptData.id,
      template: newPromptData.template,
      variables,
      output_format: newPromptData.output_format
    };

    createPromptMutation.mutate({
      filename: selectedFile.name || selectedFile.filename,
      data: promptData
    });
  };

  const handleDeletePrompt = (promptId: string) => {
    if (!selectedFile) return;
    if (!window.confirm(`Are you sure you want to delete the prompt "${promptId}"?`)) return;
    
    deletePromptMutation.mutate({
      filename: selectedFile.name || selectedFile.filename,
      promptId
    });
  };

  const validatePrompt = (template: PromptTemplate): string[] => {
    const errors: string[] = [];
    
    // Ensure variables is an array
    const variables = template.variables || [];
    
    variables.forEach(variable => {
      if (!template.template.includes(`{${variable}}`)) {
        errors.push(`Variable "{${variable}}" is defined but not used in template`);
      }
    });
    
    const variablePattern = /\{(\w+)\}/g;
    const matches = template.template.matchAll(variablePattern);
    for (const match of matches) {
      if (!variables.includes(match[1])) {
        errors.push(`Variable "{${match[1]}}" is used but not defined`);
      }
    }
    
    if (template.output_format === 'json' && template.required_fields && template.required_fields.length === 0) {
      errors.push('JSON output format requires at least one required field');
    }
    
    return errors;
  };

  const formatTemplate = (template: string): string => {
    return template
      .replace(/\\n/g, '\n')
      .replace(/\n{3,}/g, '\n\n')
      .trim();
  };

  const filteredPrompts = selectedFile && selectedFile.prompts
    ? Object.entries(selectedFile.prompts).filter(([id, prompt]) => {
        const matchesSearch = searchTerm === '' || 
          id.toLowerCase().includes(searchTerm.toLowerCase()) ||
          prompt.template.toLowerCase().includes(searchTerm.toLowerCase());
        
        const matchesFilter = filterCategory === 'all' ||
          (filterCategory === 'search' && id.includes('search')) ||
          (filterCategory === 'intent' && id.includes('intent')) ||
          (filterCategory === 'conversation' && id.includes('conversation')) ||
          (filterCategory === 'education' && id.includes('education'));
        
        return matchesSearch && matchesFilter;
      })
    : [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <Settings className="w-6 h-6" />
              Prompt Management System
            </h2>
            <p className="text-sm text-gray-600 mt-1">
              Manage and test AI prompt templates
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => queryClient.invalidateQueries({ queryKey: ['prompt-files'] })}
              disabled={isLoading}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <RefreshCw className={clsx('w-5 h-5', isLoading && 'animate-spin')} />
            </button>
            <button
              onClick={() => setBackupDialogOpen(true)}
              disabled={!selectedFile}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              <Archive className="w-4 h-4" />
              Backup
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-12 gap-6">
        {/* File List */}
        <div className="col-span-3">
          <div className="bg-white rounded-lg shadow-sm p-4">
            <h3 className="text-lg font-semibold mb-4">Prompt Files</h3>
            <div className="space-y-2">
              {files?.map((file) => (
                <button
                  key={file.name || file.filename}
                  onClick={() => handleFileSelect(file)}
                  className={clsx(
                    'w-full text-left p-3 rounded-lg transition-colors',
                    (selectedFile?.filename === file.filename || selectedFile?.name === file.name)
                      ? 'bg-blue-50 border-2 border-blue-500'
                      : 'hover:bg-gray-50 border-2 border-transparent'
                  )}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <FileText className="w-4 h-4 text-gray-500" />
                      <span className="font-medium">
                        {(file.name || file.filename || '').replace('.json', '')}
                      </span>
                      {(file.name === 'multilingual_prompts.json' || file.filename === 'multilingual_prompts.json') && (
                        <span className="ml-2 text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
                          🌍 Multi
                        </span>
                      )}
                    </div>
                    <span className="text-xs bg-gray-100 px-2 py-1 rounded">
                      {file.prompt_count || (file.prompts ? Object.keys(file.prompts).length : 0)}
                    </span>
                  </div>
                  {file.backup_available && (
                    <span className="text-xs text-green-600 mt-1 block">
                      Backup available
                    </span>
                  )}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="col-span-9">
          <div className="bg-white rounded-lg shadow-sm">
            <Tab.Group>
              <Tab.List className="flex space-x-1 rounded-t-lg bg-gray-100 p-1">
                <Tab className={({ selected }) =>
                  clsx(
                    'w-full rounded-lg py-2.5 text-sm font-medium leading-5',
                    'ring-white ring-opacity-60 ring-offset-2 ring-offset-blue-400 focus:outline-none focus:ring-2',
                    selected
                      ? 'bg-white text-blue-700 shadow'
                      : 'text-gray-700 hover:bg-white/[0.12] hover:text-gray-900'
                  )
                }>
                  Prompts
                </Tab>
                <Tab className={({ selected }) =>
                  clsx(
                    'w-full rounded-lg py-2.5 text-sm font-medium leading-5',
                    'ring-white ring-opacity-60 ring-offset-2 ring-offset-blue-400 focus:outline-none focus:ring-2',
                    selected
                      ? 'bg-white text-blue-700 shadow'
                      : 'text-gray-700 hover:bg-white/[0.12] hover:text-gray-900'
                  )
                }>
                  Editor
                </Tab>
                <Tab className={({ selected }) =>
                  clsx(
                    'w-full rounded-lg py-2.5 text-sm font-medium leading-5',
                    'ring-white ring-opacity-60 ring-offset-2 ring-offset-blue-400 focus:outline-none focus:ring-2',
                    selected
                      ? 'bg-white text-blue-700 shadow'
                      : 'text-gray-700 hover:bg-white/[0.12] hover:text-gray-900'
                  )
                }>
                  Test
                </Tab>
                <Tab className={({ selected }) =>
                  clsx(
                    'w-full rounded-lg py-2.5 text-sm font-medium leading-5',
                    'ring-white ring-opacity-60 ring-offset-2 ring-offset-blue-400 focus:outline-none focus:ring-2',
                    selected
                      ? 'bg-white text-blue-700 shadow'
                      : 'text-gray-700 hover:bg-white/[0.12] hover:text-gray-900'
                  )
                }>
                  Validation
                </Tab>
              </Tab.List>
              
              <Tab.Panels className="p-6">
                {/* Prompts Tab */}
                <Tab.Panel>
                  <div className="space-y-4">
                    <div className="flex gap-4 items-center">
                      <div className="flex-1 relative">
                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                        <input
                          type="text"
                          placeholder="Search prompts..."
                          value={searchTerm}
                          onChange={(e) => setSearchTerm(e.target.value)}
                          className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                      </div>
                      <select
                        value={filterCategory}
                        onChange={(e) => setFilterCategory(e.target.value)}
                        className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      >
                        <option value="all">All Categories</option>
                        <option value="search">Search</option>
                        <option value="intent">Intent</option>
                        <option value="conversation">Conversation</option>
                        <option value="education">Education</option>
                      </select>
                      <button
                        onClick={() => setCreateDialogOpen(true)}
                        disabled={!selectedFile}
                        className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                      >
                        <Plus className="w-4 h-4" />
                        New Prompt
                      </button>
                    </div>

                    {filteredPrompts.length === 0 ? (
                      <div className="text-center py-12 text-gray-500">
                        No prompts found. Try adjusting your search or filter.
                      </div>
                    ) : (
                      <div className="grid grid-cols-2 gap-4">
                        {filteredPrompts.map(([id, prompt]) => (
                          <div
                            key={id}
                            onClick={() => handlePromptSelect(id)}
                            className={clsx(
                              'p-4 border rounded-lg cursor-pointer transition-all',
                              selectedPrompt === id
                                ? 'border-blue-500 bg-blue-50'
                                : 'border-gray-200 hover:border-gray-300 hover:shadow-sm'
                            )}
                          >
                            <div className="flex justify-between items-start mb-2">
                              <h4 className="font-semibold text-gray-900">
                                {id.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                              </h4>
                              <div className="flex gap-1">
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handlePromptSelect(id);
                                    setEditMode(true);
                                  }}
                                  className="p-1 hover:bg-gray-100 rounded"
                                >
                                  <Edit className="w-4 h-4 text-gray-500" />
                                </button>
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleDeletePrompt(id);
                                  }}
                                  className="p-1 hover:bg-red-100 rounded"
                                >
                                  <Trash2 className="w-4 h-4 text-red-500" />
                                </button>
                              </div>
                            </div>
                            <p className="text-sm text-gray-600 mb-2 line-clamp-2">
                              {prompt.template}
                            </p>
                            <div className="flex flex-wrap gap-1">
                              {prompt.variables && prompt.variables.slice(0, 3).map(v => (
                                <span key={v} className="text-xs bg-gray-100 px-2 py-1 rounded">
                                  {v}
                                </span>
                              ))}
                              {prompt.variables && prompt.variables.length > 3 && (
                                <span className="text-xs bg-gray-100 px-2 py-1 rounded">
                                  +{prompt.variables.length - 3} more
                                </span>
                              )}
                            </div>
                            {prompt.output_format && (
                              <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded mt-2 inline-block">
                                {prompt.output_format}
                              </span>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </Tab.Panel>

                {/* Editor Tab */}
                <Tab.Panel>
                  {selectedFile && !selectedPrompt ? (
                    <div className="p-6">
                      <h3 className="text-lg font-semibold mb-4">Select a prompt to edit</h3>
                      <div className="grid grid-cols-3 gap-3">
                        {Object.entries(selectedFile.prompts || {}).map(([id, prompt]) => (
                          <button
                            key={id}
                            onClick={() => handlePromptSelect(id)}
                            className={clsx(
                              "p-4 border-2 rounded-lg transition-all text-left",
                              selectedPrompt === id 
                                ? "border-blue-500 bg-blue-50" 
                                : "border-gray-200 hover:border-blue-500 hover:bg-blue-50"
                            )}
                          >
                            <h4 className="font-medium text-gray-900 mb-1">
                              {id.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                            </h4>
                            <p className="text-sm text-gray-600 line-clamp-2">
                              {(prompt as any).template?.substring(0, 100)}...
                            </p>
                          </button>
                        ))}
                      </div>
                    </div>
                  ) : selectedPrompt && editedTemplate ? (
                    <div className="space-y-4">
                      <div className="flex justify-between items-center">
                        <h3 className="text-lg font-semibold">
                          Editing: {selectedPrompt.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                        </h3>
                        <div className="flex gap-2">
                          <label className="flex items-center gap-2">
                            <input
                              type="checkbox"
                              checked={autoFormat}
                              onChange={(e) => setAutoFormat(e.target.checked)}
                              className="rounded"
                            />
                            <span className="text-sm">Auto-format</span>
                          </label>
                          <button
                            onClick={handleSavePrompt}
                            disabled={!editMode || savePromptMutation.isPending}
                            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                          >
                            <Save className="w-4 h-4" />
                            Save
                          </button>
                          <button
                            onClick={() => setEditMode(!editMode)}
                            className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                          >
                            {editMode ? 'Cancel' : 'Edit'}
                          </button>
                        </div>
                      </div>

                      <div className="space-y-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Template
                          </label>
                          <textarea
                            value={editedTemplate.template}
                            onChange={(e) => {
                              const value = autoFormat ? formatTemplate(e.target.value) : e.target.value;
                              setEditedTemplate({ ...editedTemplate, template: value });
                            }}
                            disabled={!editMode}
                            className="w-full h-96 p-4 border border-gray-300 rounded-lg font-mono text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-50"
                          />
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                              Variables (comma-separated)
                            </label>
                            <input
                              type="text"
                              value={editedTemplate.variables ? editedTemplate.variables.join(', ') : ''}
                              onChange={(e) => {
                                const vars = e.target.value.split(',').map(v => v.trim()).filter(v => v);
                                setEditedTemplate({ ...editedTemplate, variables: vars });
                              }}
                              disabled={!editMode}
                              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-50"
                            />
                            <p className="text-xs text-gray-500 mt-1">
                              💡 Tip: Use Examples Library to inject context into prompts with {'{examples}'}
                            </p>
                          </div>

                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                              Output Format
                            </label>
                            <select
                              value={editedTemplate.output_format || 'text'}
                              onChange={(e) => setEditedTemplate({ ...editedTemplate, output_format: e.target.value })}
                              disabled={!editMode}
                              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-50"
                            >
                              <option value="text">Text</option>
                              <option value="json">JSON</option>
                              <option value="list">List</option>
                              <option value="single_word">Single Word</option>
                              <option value="yes_no">Yes/No</option>
                              <option value="number">Number</option>
                            </select>
                          </div>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="text-center py-12">
                      <Edit className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                      <p className="text-gray-500">Select a prompt from the Prompts tab to edit it</p>
                    </div>
                  )}
                </Tab.Panel>

                {/* Test Tab */}
                <Tab.Panel>
                  {selectedFile && !selectedPrompt ? (
                    <div className="p-6">
                      <h3 className="text-lg font-semibold mb-4">Select a prompt to test</h3>
                      <div className="grid grid-cols-3 gap-3">
                        {Object.entries(selectedFile.prompts || {}).map(([id, prompt]) => (
                          <button
                            key={id}
                            onClick={() => handlePromptSelect(id)}
                            className={clsx(
                              "p-4 border-2 rounded-lg transition-all text-left",
                              selectedPrompt === id 
                                ? "border-blue-500 bg-blue-50" 
                                : "border-gray-200 hover:border-blue-500 hover:bg-blue-50"
                            )}
                          >
                            <h4 className="font-medium text-gray-900 mb-1">
                              {id.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                            </h4>
                            <p className="text-sm text-gray-600 line-clamp-2">
                              {(prompt as any).template?.substring(0, 100)}...
                            </p>
                          </button>
                        ))}
                      </div>
                    </div>
                  ) : selectedPrompt && editedTemplate ? (
                    <div className="grid grid-cols-2 gap-6">
                      <div>
                        <h3 className="text-lg font-semibold mb-4">Input Variables</h3>
                        <div className="space-y-3">
                          {editedTemplate.variables && editedTemplate.variables.map(variable => (
                            <div key={variable}>
                              <label className="block text-sm font-medium text-gray-700 mb-1">
                                {variable}
                              </label>
                              <input
                                type="text"
                                value={testVariables[variable] || ''}
                                onChange={(e) => setTestVariables({
                                  ...testVariables,
                                  [variable]: e.target.value
                                })}
                                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                              />
                            </div>
                          ))}
                          <button
                            onClick={handleTestPrompt}
                            disabled={testPromptMutation.isPending}
                            className="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                          >
                            <Play className="w-4 h-4" />
                            Run Test
                          </button>
                        </div>
                      </div>

                      <div>
                        <h3 className="text-lg font-semibold mb-4">Test Result</h3>
                        {testPromptMutation.isPending && (
                          <div className="flex items-center justify-center h-64">
                            <RefreshCw className="w-8 h-8 animate-spin text-blue-600" />
                          </div>
                        )}
                        {testResult && (
                          <div className="space-y-3">
                            <div className={clsx(
                              'p-3 rounded-lg',
                              testResult.success ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'
                            )}>
                              <div className="flex items-center gap-2">
                                {testResult.success ? (
                                  <CheckCircle className="w-5 h-5" />
                                ) : (
                                  <XCircle className="w-5 h-5" />
                                )}
                                <span className="font-medium">
                                  {testResult.success ? 'Test successful' : 'Test failed'}
                                </span>
                              </div>
                            </div>

                            {testResult.execution_time && (
                              <p className="text-sm text-gray-600">
                                Execution time: {testResult.execution_time}ms
                              </p>
                            )}

                            {testResult.tokens_used && (
                              <p className="text-sm text-gray-600">
                                Tokens used: {testResult.tokens_used}
                              </p>
                            )}

                            <div>
                              <label className="block text-sm font-medium text-gray-700 mb-1">
                                Output
                              </label>
                              <pre className="p-4 bg-gray-900 text-gray-100 rounded-lg overflow-x-auto text-sm">
                                {testResult.error || JSON.stringify(testResult.output, null, 2)}
                              </pre>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  ) : (
                    <div className="text-center py-12">
                      <Play className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                      <p className="text-gray-500">Select a prompt from the Prompts tab to test it</p>
                    </div>
                  )}
                </Tab.Panel>

                {/* Validation Tab */}
                <Tab.Panel>
                  {selectedFile && !selectedPrompt ? (
                    <div className="p-6">
                      <h3 className="text-lg font-semibold mb-4">Select a prompt to validate</h3>
                      <div className="grid grid-cols-3 gap-3">
                        {Object.entries(selectedFile.prompts || {}).map(([id, prompt]) => (
                          <button
                            key={id}
                            onClick={() => handlePromptSelect(id)}
                            className={clsx(
                              "p-4 border-2 rounded-lg transition-all text-left",
                              selectedPrompt === id 
                                ? "border-blue-500 bg-blue-50" 
                                : "border-gray-200 hover:border-blue-500 hover:bg-blue-50"
                            )}
                          >
                            <h4 className="font-medium text-gray-900 mb-1">
                              {id.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                            </h4>
                            <p className="text-sm text-gray-600 line-clamp-2">
                              {(prompt as any).template?.substring(0, 100)}...
                            </p>
                          </button>
                        ))}
                      </div>
                    </div>
                  ) : selectedPrompt && editedTemplate ? (
                    <div className="space-y-6">
                      <h3 className="text-lg font-semibold">
                        Validation: {selectedPrompt.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </h3>

                      {(() => {
                        const errors = validatePrompt(editedTemplate);
                        return errors.length > 0 ? (
                          <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                            <div className="flex items-start gap-2">
                              <AlertTriangle className="w-5 h-5 text-yellow-600 mt-0.5" />
                              <div>
                                <p className="font-medium text-yellow-800">
                                  Found {errors.length} validation issue(s):
                                </p>
                                <ul className="mt-2 space-y-1">
                                  {errors.map((error, i) => (
                                    <li key={i} className="text-sm text-yellow-700">
                                      • {error}
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            </div>
                          </div>
                        ) : (
                          <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                            <div className="flex items-center gap-2">
                              <CheckCircle className="w-5 h-5 text-green-600" />
                              <p className="font-medium text-green-800">
                                All validation checks passed
                              </p>
                            </div>
                          </div>
                        );
                      })()}

                      <div className="grid grid-cols-2 gap-6">
                        <div className="bg-gray-50 p-4 rounded-lg">
                          <h4 className="font-medium mb-3">Template Analysis</h4>
                          <dl className="space-y-2">
                            <div className="flex justify-between text-sm">
                              <dt className="text-gray-600">Template Length</dt>
                              <dd className="font-medium">{editedTemplate.template.length} characters</dd>
                            </div>
                            <div className="flex justify-between text-sm">
                              <dt className="text-gray-600">Variables</dt>
                              <dd className="font-medium">{editedTemplate.variables.length} defined</dd>
                            </div>
                            <div className="flex justify-between text-sm">
                              <dt className="text-gray-600">Output Format</dt>
                              <dd className="font-medium">{editedTemplate.output_format || 'text'}</dd>
                            </div>
                            {editedTemplate.max_length && (
                              <div className="flex justify-between text-sm">
                                <dt className="text-gray-600">Max Length</dt>
                                <dd className="font-medium">{editedTemplate.max_length} characters</dd>
                              </div>
                            )}
                          </dl>
                        </div>

                        <div className="bg-gray-50 p-4 rounded-lg">
                          <h4 className="font-medium mb-3">Best Practices</h4>
                          <ul className="space-y-2">
                            <li className="flex items-center gap-2 text-sm">
                              {editedTemplate.template.includes('CRITICAL') ? 
                                <CheckCircle className="w-4 h-4 text-green-600" /> : 
                                <AlertCircle className="w-4 h-4 text-yellow-600" />
                              }
                              <span>Uses clear instruction markers</span>
                            </li>
                            <li className="flex items-center gap-2 text-sm">
                              {editedTemplate.template.includes('Example') || editedTemplate.template.includes('example') ? 
                                <CheckCircle className="w-4 h-4 text-green-600" /> : 
                                <AlertCircle className="w-4 h-4 text-yellow-600" />
                              }
                              <span>Includes examples</span>
                            </li>
                            <li className="flex items-center gap-2 text-sm">
                              {editedTemplate.output_format ? 
                                <CheckCircle className="w-4 h-4 text-green-600" /> : 
                                <XCircle className="w-4 h-4 text-red-600" />
                              }
                              <span>Specifies output format</span>
                            </li>
                            <li className="flex items-center gap-2 text-sm">
                              {editedTemplate.variables.every(v => editedTemplate.template.includes(`{${v}}`)) ? 
                                <CheckCircle className="w-4 h-4 text-green-600" /> : 
                                <XCircle className="w-4 h-4 text-red-600" />
                              }
                              <span>All variables used in template</span>
                            </li>
                          </ul>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="text-center py-12">
                      <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                      <p className="text-gray-500">Select a prompt from the Prompts tab to validate it</p>
                    </div>
                  )}
                </Tab.Panel>
              </Tab.Panels>
            </Tab.Group>
          </div>
        </div>
      </div>

      {/* Create Prompt Dialog */}
      <Transition appear show={createDialogOpen} as={Fragment}>
        <Dialog as="div" className="relative z-10" onClose={() => setCreateDialogOpen(false)}>
          <Transition.Child
            as={Fragment}
            enter="ease-out duration-300"
            enterFrom="opacity-0"
            enterTo="opacity-100"
            leave="ease-in duration-200"
            leaveFrom="opacity-100"
            leaveTo="opacity-0"
          >
            <div className="fixed inset-0 bg-black bg-opacity-25" />
          </Transition.Child>

          <div className="fixed inset-0 overflow-y-auto">
            <div className="flex min-h-full items-center justify-center p-4 text-center">
              <Transition.Child
                as={Fragment}
                enter="ease-out duration-300"
                enterFrom="opacity-0 scale-95"
                enterTo="opacity-100 scale-100"
                leave="ease-in duration-200"
                leaveFrom="opacity-100 scale-100"
                leaveTo="opacity-0 scale-95"
              >
                <Dialog.Panel className="w-full max-w-2xl transform overflow-hidden rounded-2xl bg-white p-6 text-left align-middle shadow-xl transition-all">
                  <Dialog.Title as="h3" className="text-lg font-medium leading-6 text-gray-900">
                    Create New Prompt
                  </Dialog.Title>
                  
                  <div className="mt-4 space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Prompt ID
                      </label>
                      <input
                        type="text"
                        value={newPromptData.id}
                        onChange={(e) => setNewPromptData({ ...newPromptData, id: e.target.value })}
                        placeholder="e.g., product_search_extraction"
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                      <p className="mt-1 text-xs text-gray-500">Use snake_case</p>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Template
                      </label>
                      <textarea
                        value={newPromptData.template}
                        onChange={(e) => setNewPromptData({ ...newPromptData, template: e.target.value })}
                        placeholder="Enter your prompt template here. Use {variable_name} for variables."
                        rows={8}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Variables (comma-separated)
                        </label>
                        <input
                          type="text"
                          value={newPromptData.variables}
                          onChange={(e) => setNewPromptData({ ...newPromptData, variables: e.target.value })}
                          placeholder="e.g., message, context, user_input"
                          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Output Format
                        </label>
                        <select
                          value={newPromptData.output_format}
                          onChange={(e) => setNewPromptData({ ...newPromptData, output_format: e.target.value })}
                          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        >
                          <option value="text">Text</option>
                          <option value="json">JSON</option>
                          <option value="list">List</option>
                          <option value="single_word">Single Word</option>
                          <option value="yes_no">Yes/No</option>
                          <option value="number">Number</option>
                        </select>
                      </div>
                    </div>
                  </div>

                  <div className="mt-6 flex justify-end gap-3">
                    <button
                      type="button"
                      className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                      onClick={() => setCreateDialogOpen(false)}
                    >
                      Cancel
                    </button>
                    <button
                      type="button"
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                      onClick={handleCreatePrompt}
                      disabled={createPromptMutation.isPending}
                    >
                      Create
                    </button>
                  </div>
                </Dialog.Panel>
              </Transition.Child>
            </div>
          </div>
        </Dialog>
      </Transition>

      {/* Backup Dialog */}
      <Transition appear show={backupDialogOpen} as={Fragment}>
        <Dialog as="div" className="relative z-10" onClose={() => setBackupDialogOpen(false)}>
          <Transition.Child
            as={Fragment}
            enter="ease-out duration-300"
            enterFrom="opacity-0"
            enterTo="opacity-100"
            leave="ease-in duration-200"
            leaveFrom="opacity-100"
            leaveTo="opacity-0"
          >
            <div className="fixed inset-0 bg-black bg-opacity-25" />
          </Transition.Child>

          <div className="fixed inset-0 overflow-y-auto">
            <div className="flex min-h-full items-center justify-center p-4 text-center">
              <Transition.Child
                as={Fragment}
                enter="ease-out duration-300"
                enterFrom="opacity-0 scale-95"
                enterTo="opacity-100 scale-100"
                leave="ease-in duration-200"
                leaveFrom="opacity-100 scale-100"
                leaveTo="opacity-0 scale-95"
              >
                <Dialog.Panel className="w-full max-w-md transform overflow-hidden rounded-2xl bg-white p-6 text-left align-middle shadow-xl transition-all">
                  <Dialog.Title as="h3" className="text-lg font-medium leading-6 text-gray-900">
                    Create Backup
                  </Dialog.Title>
                  
                  <div className="mt-4">
                    <p className="text-sm text-gray-500">
                      Create a backup of the current prompt file?
                    </p>
                    {selectedFile && (
                      <div className="mt-3 p-3 bg-gray-50 rounded-lg">
                        <p className="text-sm font-medium">File: {selectedFile.name || selectedFile.filename}</p>
                      </div>
                    )}
                  </div>

                  <div className="mt-6 flex justify-end gap-3">
                    <button
                      type="button"
                      className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                      onClick={() => setBackupDialogOpen(false)}
                    >
                      Cancel
                    </button>
                    <button
                      type="button"
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                      onClick={handleCreateBackup}
                      disabled={createBackupMutation.isPending}
                    >
                      Create Backup
                    </button>
                  </div>
                </Dialog.Panel>
              </Transition.Child>
            </div>
          </div>
        </Dialog>
      </Transition>
    </div>
  );
};

export default PromptManagement;