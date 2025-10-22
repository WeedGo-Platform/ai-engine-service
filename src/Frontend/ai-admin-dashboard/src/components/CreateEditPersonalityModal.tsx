import React, { useState, useEffect } from 'react';
import { X, Save, Loader2, Info } from 'lucide-react';
import toast from 'react-hot-toast';
import { Personality } from './Personalities';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

interface CreateEditPersonalityModalProps {
  personality: Personality | null;
  isEdit: boolean;
  tenantId: string;
  token: string;
  onClose: () => void;
  onSuccess: () => void;
}

const CreateEditPersonalityModal: React.FC<CreateEditPersonalityModalProps> = ({
  personality,
  isEdit,
  tenantId,
  token,
  onClose,
  onSuccess
}) => {
  const [isSaving, setIsSaving] = useState(false);
  const [formData, setFormData] = useState<Partial<Personality>>({
    name: '',
    personality_name: '',
    personality_type: 'assistant',
    tone: 'professional',
    description: '',
    greeting_message: '',
    system_prompt: '',
    response_style: {
      style: 'professional',
      detail_level: 'medium',
      expertise: ''
    },
    traits: {
      tone: 'professional',
      expertise: '',
      approach: ''
    },
    is_active: true,
    is_default: false,
    has_voice_sample: false,
    voice_provider: 'piper'
  });

  // Populate form when editing or using template
  useEffect(() => {
    if (personality) {
      const baseData = {
        ...personality,
        response_style: typeof personality.response_style === 'string'
          ? JSON.parse(personality.response_style)
          : personality.response_style,
        traits: typeof personality.traits === 'string'
          ? JSON.parse(personality.traits)
          : personality.traits
      };

      // If using as template (not editing), clear fields that need to be unique
      if (!isEdit) {
        baseData.id = '';
        baseData.name = '';
        baseData.is_default = false;
        baseData.has_voice_sample = false;
      }

      setFormData(baseData);
    }
  }, [isEdit, personality]);

  const handleInputChange = (field: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleNestedChange = (parent: 'response_style' | 'traits', field: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      [parent]: {
        ...prev[parent],
        [field]: value
      }
    }));
  };

  const validateForm = (): boolean => {
    if (!formData.name?.trim()) {
      toast.error('Name (ID) is required');
      return false;
    }
    if (!formData.personality_name?.trim()) {
      toast.error('Display Name is required');
      return false;
    }
    if (!formData.greeting_message?.trim()) {
      toast.error('Greeting Message is required');
      return false;
    }
    if (!formData.system_prompt?.trim()) {
      toast.error('System Prompt is required');
      return false;
    }

    // Validate name format (lowercase, no spaces)
    if (!/^[a-z_]+$/.test(formData.name || '')) {
      toast.error('Name must be lowercase letters and underscores only');
      return false;
    }

    return true;
  };

  const handleSave = async () => {
    if (!validateForm()) return;

    setIsSaving(true);

    try {
      const url = isEdit
        ? `${API_BASE_URL}/personalities/${personality?.id}`
        : `${API_BASE_URL}/personalities`;

      const method = isEdit ? 'PUT' : 'POST';

      const payload = {
        ...formData,
        tenant_id: tenantId
      };

      const response = await fetch(url, {
        method,
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to save personality');
      }

      toast.success(isEdit ? 'Personality updated successfully!' : 'Personality created successfully!');
      onSuccess();
      onClose();
    } catch (error: any) {
      console.error('Save error:', error);
      toast.error(error.message || 'Failed to save personality');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 dark:bg-opacity-70 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4 flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              {isEdit ? 'Edit Personality' : personality ? `Create from Template: ${personality.personality_name}` : 'Create New Personality'}
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              {isEdit
                ? 'Update personality settings and behavior'
                : personality
                  ? 'Customize this template to create your own personality'
                  : 'Configure a new AI personality for your store'}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Template Info Banner */}
          {!isEdit && personality && (
            <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <Info className="h-5 w-5 text-green-600 dark:text-green-400 flex-shrink-0 mt-0.5" />
                <div className="text-sm text-green-800 dark:text-green-200">
                  <p className="font-medium mb-1">Creating from Default Personality Template</p>
                  <p>
                    You're creating a new custom personality based on <strong>{personality.personality_name}</strong>.
                    The system prompt, tone, and settings have been copied. Customize the Name (ID) and other fields
                    to make this personality your own.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Info Banner */}
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <Info className="h-5 w-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
              <div className="text-sm text-blue-800 dark:text-blue-200">
                <p className="font-medium mb-1">Personality Configuration Guidelines:</p>
                <ul className="list-disc list-inside space-y-1">
                  <li>Name (ID) must be unique and lowercase (e.g., marcel, cannabis_expert)</li>
                  <li>Display Name is what users see (e.g., Marcel, Cannabis Expert)</li>
                  <li>System Prompt defines the AI's behavior and knowledge base</li>
                  <li>Greeting Message is the first message users receive</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Basic Information */}
          <div className="space-y-4">
            <h4 className="text-md font-semibold text-gray-900 dark:text-white">
              Basic Information
            </h4>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Name (ID) */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Name (ID) <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => handleInputChange('name', e.target.value.toLowerCase())}
                  placeholder="e.g., marcel, cannabis_expert"
                  disabled={isEdit}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-2 focus:ring-accent-500 dark:focus:ring-accent-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 disabled:opacity-50 disabled:cursor-not-allowed"
                />
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Lowercase, underscores only. Cannot be changed after creation.
                </p>
              </div>

              {/* Display Name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Display Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={formData.personality_name}
                  onChange={(e) => handleInputChange('personality_name', e.target.value)}
                  placeholder="e.g., Marcel, Cannabis Expert"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-2 focus:ring-accent-500 dark:focus:ring-accent-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500"
                />
              </div>

              {/* Personality Type */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Personality Type
                </label>
                <select
                  value={formData.personality_type}
                  onChange={(e) => handleInputChange('personality_type', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-2 focus:ring-accent-500 dark:focus:ring-accent-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                >
                  <option value="assistant">Assistant</option>
                  <option value="expert">Expert</option>
                  <option value="guide">Guide</option>
                  <option value="consultant">Consultant</option>
                  <option value="educator">Educator</option>
                </select>
              </div>

              {/* Tone */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Tone
                </label>
                <select
                  value={formData.tone}
                  onChange={(e) => {
                    handleInputChange('tone', e.target.value);
                    handleNestedChange('traits', 'tone', e.target.value);
                    handleNestedChange('response_style', 'style', e.target.value);
                  }}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-2 focus:ring-accent-500 dark:focus:ring-accent-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                >
                  <option value="professional">Professional</option>
                  <option value="friendly">Friendly</option>
                  <option value="casual">Casual</option>
                  <option value="expert">Expert</option>
                  <option value="enthusiastic">Enthusiastic</option>
                  <option value="calm">Calm</option>
                </select>
              </div>
            </div>

            {/* Description */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Description (Optional)
              </label>
              <input
                type="text"
                value={formData.description || ''}
                onChange={(e) => handleInputChange('description', e.target.value)}
                placeholder="Brief description of this personality"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-2 focus:ring-accent-500 dark:focus:ring-accent-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500"
              />
            </div>
          </div>

          {/* Messages & Prompts */}
          <div className="space-y-4">
            <h4 className="text-md font-semibold text-gray-900 dark:text-white">
              Messages & Prompts
            </h4>

            {/* Greeting Message */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Greeting Message <span className="text-red-500">*</span>
              </label>
              <textarea
                value={formData.greeting_message}
                onChange={(e) => handleInputChange('greeting_message', e.target.value)}
                placeholder="Hello! I'm here to help you with..."
                rows={2}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-2 focus:ring-accent-500 dark:focus:ring-accent-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500"
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                First message users receive when starting a conversation
              </p>
            </div>

            {/* System Prompt */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                System Prompt <span className="text-red-500">*</span>
              </label>
              <textarea
                value={formData.system_prompt}
                onChange={(e) => handleInputChange('system_prompt', e.target.value)}
                placeholder="You are a knowledgeable assistant who helps users with..."
                rows={6}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-2 focus:ring-accent-500 dark:focus:ring-accent-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 font-mono text-sm"
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Defines the AI's behavior, knowledge base, and response style
              </p>
            </div>
          </div>

          {/* Advanced Settings */}
          <div className="space-y-4">
            <h4 className="text-md font-semibold text-gray-900 dark:text-white">
              Advanced Settings
            </h4>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Detail Level */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Detail Level
                </label>
                <select
                  value={formData.response_style.detail_level}
                  onChange={(e) => handleNestedChange('response_style', 'detail_level', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-2 focus:ring-accent-500 dark:focus:ring-accent-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                >
                  <option value="low">Low - Brief answers</option>
                  <option value="medium">Medium - Balanced</option>
                  <option value="high">High - Detailed</option>
                </select>
              </div>

              {/* Expertise */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Expertise Area
                </label>
                <input
                  type="text"
                  value={formData.response_style.expertise || ''}
                  onChange={(e) => {
                    handleNestedChange('response_style', 'expertise', e.target.value);
                    handleNestedChange('traits', 'expertise', e.target.value);
                  }}
                  placeholder="e.g., cannabis, customer_service"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-2 focus:ring-accent-500 dark:focus:ring-accent-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500"
                />
              </div>

              {/* Approach */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Approach
                </label>
                <input
                  type="text"
                  value={formData.traits.approach || ''}
                  onChange={(e) => handleNestedChange('traits', 'approach', e.target.value)}
                  placeholder="e.g., educational, consultative"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-2 focus:ring-accent-500 dark:focus:ring-accent-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500"
                />
              </div>
            </div>
          </div>

          {/* Status */}
          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              id="is_active"
              checked={formData.is_active}
              onChange={(e) => handleInputChange('is_active', e.target.checked)}
              className="h-4 w-4 text-accent-600 focus:ring-accent-500 border-gray-300 rounded"
            />
            <label htmlFor="is_active" className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Active (personality can be used for conversations)
            </label>
          </div>
        </div>

        {/* Footer */}
        <div className="sticky bottom-0 bg-gray-50 dark:bg-gray-900/50 border-t border-gray-200 dark:border-gray-700 px-6 py-4 flex justify-end gap-3">
          <button
            onClick={onClose}
            disabled={isSaving}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="px-4 py-2 bg-accent-600 dark:bg-accent-500 text-white rounded-md hover:bg-accent-700 dark:hover:bg-accent-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
          >
            {isSaving ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Save className="h-4 w-4" />
                {isEdit ? 'Update Personality' : 'Create Personality'}
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default CreateEditPersonalityModal;
