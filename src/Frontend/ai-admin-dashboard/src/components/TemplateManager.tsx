import React, { useState, useEffect } from 'react';
import {
  FileText, Plus, Edit, Trash2, Copy, Search, Filter, X, Save,
  Mail, Smartphone, Bell, Hash, Clock, User, CheckCircle, AlertCircle,
  Eye, Code, Type, Image, Link2, List, Bold, Italic, Underline
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useStoreContext } from '../contexts/StoreContext';
import toast from 'react-hot-toast';

interface Template {
  id: string;
  name: string;
  type: 'email' | 'sms' | 'push';
  subject?: string;
  content: string;
  variables: string[];
  category: string;
  is_active: boolean;
  usage_count: number;
  created_at: string;
  updated_at: string;
  created_by_name: string;
}

interface TemplateManagerProps {
  onSelectTemplate?: (template: Template) => void;
  selectedType?: 'email' | 'sms' | 'push';
}

const TemplateManager: React.FC<TemplateManagerProps> = ({ onSelectTemplate, selectedType }) => {
  const { user } = useAuth();
  const { currentStore } = useStoreContext();
  const [templates, setTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState<'all' | 'email' | 'sms' | 'push'>('all');
  const [filterCategory, setFilterCategory] = useState<string>('all');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState<Template | null>(null);
  const [previewTemplate, setPreviewTemplate] = useState<Template | null>(null);

  // Form state for create/edit
  const [formData, setFormData] = useState({
    name: '',
    type: 'email' as 'email' | 'sms' | 'push',
    subject: '',
    content: '',
    category: 'general',
    is_active: true,
    variables: [] as string[]
  });

  const categories = [
    'general',
    'promotional',
    'transactional',
    'notification',
    'reminder',
    'welcome',
    'abandoned_cart',
    'order_confirmation',
    'shipping',
    'feedback'
  ];

  const variablePresets = [
    { name: 'customer_name', label: 'Customer Name', example: 'John Doe' },
    { name: 'store_name', label: 'Store Name', example: 'Pot Palace' },
    { name: 'order_number', label: 'Order Number', example: 'ORD-12345' },
    { name: 'order_total', label: 'Order Total', example: '$99.99' },
    { name: 'product_name', label: 'Product Name', example: 'Blue Dream' },
    { name: 'discount_code', label: 'Discount Code', example: 'SAVE20' },
    { name: 'tracking_number', label: 'Tracking Number', example: 'TRK-98765' },
    { name: 'appointment_date', label: 'Appointment Date', example: '2024-03-15' },
    { name: 'points_balance', label: 'Points Balance', example: '500' }
  ];

  useEffect(() => {
    if (currentStore?.id) {
      fetchTemplates();
    }
  }, [currentStore]);

  const fetchTemplates = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/communications/templates`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'X-Store-ID': currentStore?.id || ''
          }
        }
      );

      if (response.ok) {
        const data = await response.json();
        setTemplates(data.templates || []);
      } else {
        toast.error('Failed to fetch templates');
      }
    } catch (error) {
      console.error('Error fetching templates:', error);
      toast.error('Failed to fetch templates');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTemplate = async () => {
    try {
      const token = localStorage.getItem('token');
      const payload = {
        ...formData,
        store_id: currentStore?.id
      };

      const response = await fetch(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/communications/templates`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
            'X-Store-ID': currentStore?.id || ''
          },
          body: JSON.stringify(payload)
        }
      );

      if (response.ok) {
        toast.success('Template created successfully');
        setShowCreateModal(false);
        resetForm();
        fetchTemplates();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to create template');
      }
    } catch (error) {
      toast.error('Failed to create template');
    }
  };

  const handleUpdateTemplate = async () => {
    if (!editingTemplate) return;

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/communications/templates/${editingTemplate.id}`,
        {
          method: 'PUT',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
            'X-Store-ID': currentStore?.id || ''
          },
          body: JSON.stringify(formData)
        }
      );

      if (response.ok) {
        toast.success('Template updated successfully');
        setEditingTemplate(null);
        resetForm();
        fetchTemplates();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to update template');
      }
    } catch (error) {
      toast.error('Failed to update template');
    }
  };

  const handleDeleteTemplate = async (templateId: string) => {
    if (!confirm('Are you sure you want to delete this template?')) return;

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/communications/templates/${templateId}`,
        {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`,
            'X-Store-ID': currentStore?.id || ''
          }
        }
      );

      if (response.ok) {
        toast.success('Template deleted successfully');
        fetchTemplates();
      } else {
        toast.error('Failed to delete template');
      }
    } catch (error) {
      toast.error('Failed to delete template');
    }
  };

  const handleDuplicateTemplate = async (template: Template) => {
    const duplicatedTemplate = {
      ...template,
      name: `${template.name} (Copy)`,
      id: undefined
    };

    setFormData({
      name: duplicatedTemplate.name,
      type: duplicatedTemplate.type,
      subject: duplicatedTemplate.subject || '',
      content: duplicatedTemplate.content,
      category: duplicatedTemplate.category,
      is_active: true,
      variables: duplicatedTemplate.variables
    });
    setShowCreateModal(true);
  };

  const extractVariables = (content: string) => {
    const regex = /\{\{(\w+)\}\}/g;
    const matches = content.matchAll(regex);
    const vars = new Set<string>();
    for (const match of matches) {
      vars.add(match[1]);
    }
    return Array.from(vars);
  };

  const insertVariable = (variable: string) => {
    const cursorPosition = (document.getElementById('template-content') as HTMLTextAreaElement)?.selectionStart || formData.content.length;
    const newContent =
      formData.content.slice(0, cursorPosition) +
      `{{${variable}}}` +
      formData.content.slice(cursorPosition);

    setFormData(prev => ({
      ...prev,
      content: newContent,
      variables: extractVariables(newContent)
    }));
  };

  const resetForm = () => {
    setFormData({
      name: '',
      type: 'email',
      subject: '',
      content: '',
      category: 'general',
      is_active: true,
      variables: []
    });
  };

  const filteredTemplates = templates.filter(template => {
    const matchesSearch = template.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          template.content.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesType = filterType === 'all' || template.type === filterType;
    const matchesCategory = filterCategory === 'all' || template.category === filterCategory;
    const matchesSelectedType = !selectedType || template.type === selectedType;

    return matchesSearch && matchesType && matchesCategory && matchesSelectedType;
  });

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'email': return Mail;
      case 'sms': return Smartphone;
      case 'push': return Bell;
      default: return FileText;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div className="flex items-center space-x-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search templates..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 pr-4 py-2 border rounded-lg w-64 focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
          </div>

          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value as any)}
            className="px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
          >
            <option value="all">All Types</option>
            <option value="email">Email</option>
            <option value="sms">SMS</option>
            <option value="push">Push</option>
          </select>

          <select
            value={filterCategory}
            onChange={(e) => setFilterCategory(e.target.value)}
            className="px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
          >
            <option value="all">All Categories</option>
            {categories.map(cat => (
              <option key={cat} value={cat}>
                {cat.charAt(0).toUpperCase() + cat.slice(1).replace('_', ' ')}
              </option>
            ))}
          </select>
        </div>

        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 flex items-center space-x-2"
        >
          <Plus className="h-4 w-4" />
          <span>Create Template</span>
        </button>
      </div>

      {/* Templates Grid */}
      {loading ? (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600" />
        </div>
      ) : filteredTemplates.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
          <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600">No templates found</p>
          <p className="text-sm text-gray-500 mt-2">Create your first template to get started</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredTemplates.map(template => {
            const Icon = getTypeIcon(template.type);
            return (
              <div
                key={template.id}
                className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-lg transition-shadow cursor-pointer"
                onClick={() => onSelectTemplate && onSelectTemplate(template)}
              >
                <div className="flex justify-between items-start mb-3">
                  <div className="flex items-center space-x-2">
                    <div className={`p-2 rounded-lg ${
                      template.type === 'email' ? 'bg-blue-100' :
                      template.type === 'sms' ? 'bg-green-100' :
                      'bg-purple-100'
                    }`}>
                      <Icon className={`h-5 w-5 ${
                        template.type === 'email' ? 'text-blue-600' :
                        template.type === 'sms' ? 'text-green-600' :
                        'text-purple-600'
                      }`} />
                    </div>
                    <div>
                      <h3 className="font-medium text-gray-900">{template.name}</h3>
                      <p className="text-xs text-gray-500 capitalize">{template.category}</p>
                    </div>
                  </div>
                  <div className="flex space-x-1">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setPreviewTemplate(template);
                      }}
                      className="p-1 hover:bg-gray-100 rounded"
                      title="Preview"
                    >
                      <Eye className="h-4 w-4 text-gray-500" />
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setEditingTemplate(template);
                        setFormData({
                          name: template.name,
                          type: template.type,
                          subject: template.subject || '',
                          content: template.content,
                          category: template.category,
                          is_active: template.is_active,
                          variables: template.variables
                        });
                      }}
                      className="p-1 hover:bg-gray-100 rounded"
                      title="Edit"
                    >
                      <Edit className="h-4 w-4 text-gray-500" />
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDuplicateTemplate(template);
                      }}
                      className="p-1 hover:bg-gray-100 rounded"
                      title="Duplicate"
                    >
                      <Copy className="h-4 w-4 text-gray-500" />
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteTemplate(template.id);
                      }}
                      className="p-1 hover:bg-gray-100 rounded"
                      title="Delete"
                    >
                      <Trash2 className="h-4 w-4 text-red-500" />
                    </button>
                  </div>
                </div>

                {template.subject && (
                  <p className="text-sm font-medium text-gray-700 mb-2">
                    Subject: {template.subject}
                  </p>
                )}

                <p className="text-sm text-gray-600 line-clamp-3 mb-3">
                  {template.content}
                </p>

                {template.variables.length > 0 && (
                  <div className="flex flex-wrap gap-1 mb-3">
                    {template.variables.map(variable => (
                      <span
                        key={variable}
                        className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded"
                      >
                        {`{{${variable}}}`}
                      </span>
                    ))}
                  </div>
                )}

                <div className="flex justify-between items-center text-xs text-gray-500">
                  <span className="flex items-center">
                    <Clock className="h-3 w-3 mr-1" />
                    {new Date(template.updated_at).toLocaleDateString()}
                  </span>
                  <span className="flex items-center">
                    <Hash className="h-3 w-3 mr-1" />
                    Used {template.usage_count} times
                  </span>
                </div>

                {!template.is_active && (
                  <div className="mt-2 px-2 py-1 bg-yellow-100 text-yellow-800 text-xs rounded text-center">
                    Inactive
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Create/Edit Modal */}
      {(showCreateModal || editingTemplate) && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl max-w-3xl w-full max-h-[90vh] overflow-hidden">
            <div className="bg-gradient-to-r from-purple-600 to-purple-700 px-6 py-4 flex items-center justify-between">
              <h2 className="text-xl font-semibold text-white">
                {editingTemplate ? 'Edit Template' : 'Create Template'}
              </h2>
              <button
                onClick={() => {
                  setShowCreateModal(false);
                  setEditingTemplate(null);
                  resetForm();
                }}
                className="text-white hover:text-gray-200"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="p-6 overflow-y-auto" style={{ maxHeight: 'calc(90vh - 140px)' }}>
              <div className="space-y-4">
                {/* Name and Type */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Template Name
                    </label>
                    <input
                      type="text"
                      value={formData.name}
                      onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                      className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500"
                      placeholder="e.g., Welcome Email"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Type
                    </label>
                    <select
                      value={formData.type}
                      onChange={(e) => setFormData(prev => ({ ...prev, type: e.target.value as any }))}
                      className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500"
                    >
                      <option value="email">Email</option>
                      <option value="sms">SMS</option>
                      <option value="push">Push Notification</option>
                    </select>
                  </div>
                </div>

                {/* Category */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Category
                  </label>
                  <select
                    value={formData.category}
                    onChange={(e) => setFormData(prev => ({ ...prev, category: e.target.value }))}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500"
                  >
                    {categories.map(cat => (
                      <option key={cat} value={cat}>
                        {cat.charAt(0).toUpperCase() + cat.slice(1).replace('_', ' ')}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Subject (for email and push) */}
                {(formData.type === 'email' || formData.type === 'push') && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      {formData.type === 'email' ? 'Subject' : 'Title'}
                    </label>
                    <input
                      type="text"
                      value={formData.subject}
                      onChange={(e) => setFormData(prev => ({ ...prev, subject: e.target.value }))}
                      className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500"
                      placeholder={formData.type === 'email' ? 'Email subject...' : 'Notification title...'}
                    />
                  </div>
                )}

                {/* Variables */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Available Variables
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {variablePresets.map(variable => (
                      <button
                        key={variable.name}
                        onClick={() => insertVariable(variable.name)}
                        className="px-3 py-1 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm"
                        title={`Example: ${variable.example}`}
                      >
                        {`{{${variable.name}}}`}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Content */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Content
                  </label>
                  <textarea
                    id="template-content"
                    value={formData.content}
                    onChange={(e) => {
                      const content = e.target.value;
                      setFormData(prev => ({
                        ...prev,
                        content,
                        variables: extractVariables(content)
                      }));
                    }}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500"
                    rows={formData.type === 'sms' ? 4 : 10}
                    placeholder={
                      formData.type === 'email'
                        ? 'Email body content...\n\nUse {{variable_name}} to insert dynamic content.'
                        : formData.type === 'sms'
                        ? 'SMS message (160 characters)...'
                        : 'Push notification message...'
                    }
                    maxLength={formData.type === 'sms' ? 160 : undefined}
                  />
                  {formData.type === 'sms' && (
                    <p className="text-xs text-gray-500 mt-1">
                      {formData.content.length}/160 characters
                    </p>
                  )}
                </div>

                {/* Active Status */}
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="is_active"
                    checked={formData.is_active}
                    onChange={(e) => setFormData(prev => ({ ...prev, is_active: e.target.checked }))}
                    className="h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
                  />
                  <label htmlFor="is_active" className="ml-2 text-sm text-gray-700">
                    Template is active and can be used
                  </label>
                </div>

                {/* Detected Variables */}
                {formData.variables.length > 0 && (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <div className="flex items-start">
                      <AlertCircle className="h-5 w-5 text-blue-600 mt-0.5" />
                      <div className="ml-3">
                        <h4 className="text-sm font-medium text-blue-900">Detected Variables</h4>
                        <div className="flex flex-wrap gap-2 mt-2">
                          {formData.variables.map(variable => (
                            <span
                              key={variable}
                              className="px-2 py-1 bg-white text-blue-700 text-xs rounded border border-blue-300"
                            >
                              {`{{${variable}}}`}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>

            <div className="bg-gray-50 px-6 py-4 flex justify-end space-x-3 border-t">
              <button
                onClick={() => {
                  setShowCreateModal(false);
                  setEditingTemplate(null);
                  resetForm();
                }}
                className="px-4 py-2 text-gray-700 hover:text-gray-900"
              >
                Cancel
              </button>
              <button
                onClick={editingTemplate ? handleUpdateTemplate : handleCreateTemplate}
                className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 flex items-center"
              >
                <Save className="h-4 w-4 mr-2" />
                {editingTemplate ? 'Update Template' : 'Create Template'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Preview Modal */}
      {previewTemplate && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[80vh] overflow-hidden">
            <div className="bg-gradient-to-r from-purple-600 to-purple-700 px-6 py-4 flex items-center justify-between">
              <h2 className="text-xl font-semibold text-white">Template Preview</h2>
              <button
                onClick={() => setPreviewTemplate(null)}
                className="text-white hover:text-gray-200"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="p-6 overflow-y-auto" style={{ maxHeight: 'calc(80vh - 80px)' }}>
              <div className="space-y-4">
                <div>
                  <h3 className="font-medium text-gray-900 mb-1">{previewTemplate.name}</h3>
                  <p className="text-sm text-gray-500">
                    {previewTemplate.type.toUpperCase()} • {previewTemplate.category}
                  </p>
                </div>

                {previewTemplate.subject && (
                  <div>
                    <label className="text-sm font-medium text-gray-700">
                      {previewTemplate.type === 'email' ? 'Subject:' : 'Title:'}
                    </label>
                    <p className="mt-1 p-3 bg-gray-50 rounded-lg">{previewTemplate.subject}</p>
                  </div>
                )}

                <div>
                  <label className="text-sm font-medium text-gray-700">Content:</label>
                  <div className="mt-1 p-4 bg-gray-50 rounded-lg whitespace-pre-wrap">
                    {previewTemplate.content}
                  </div>
                </div>

                {previewTemplate.variables.length > 0 && (
                  <div>
                    <label className="text-sm font-medium text-gray-700">Variables:</label>
                    <div className="flex flex-wrap gap-2 mt-2">
                      {previewTemplate.variables.map(variable => (
                        <span
                          key={variable}
                          className="px-3 py-1 bg-purple-100 text-purple-700 text-sm rounded-lg"
                        >
                          {`{{${variable}}}`}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                <div className="pt-4 border-t text-sm text-gray-500">
                  <p>Created by: {previewTemplate.created_by_name}</p>
                  <p>Last updated: {new Date(previewTemplate.updated_at).toLocaleString()}</p>
                  <p>Used: {previewTemplate.usage_count} times</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TemplateManager;