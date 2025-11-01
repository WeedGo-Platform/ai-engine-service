import React, { useState, useEffect, useCallback } from 'react';
import {
  Plus,
  Upload,
  Trash2,
  Edit,
  Check,
  X,
  AlertCircle,
  Info,
  Crown,
  Volume2,
  FileAudio,
  Loader2,
  Users,
  Copy
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useStoreContext } from '../contexts/StoreContext';
import toast from 'react-hot-toast';
import VoiceTestModal from './VoiceTestModal';
import CreateEditPersonalityModal from './CreateEditPersonalityModal';
import VoiceRecordUploadModal from './VoiceRecordUploadModal';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

export interface Personality {
  id: string;
  tenant_id: string;
  name: string;
  personality_name: string;
  tone: string;
  description?: string;
  is_default: boolean;
  is_active: boolean;
  has_voice_sample: boolean;
  voice_provider: string;
  created_at?: string;
  updated_at?: string;
  personality_type?: string;
  greeting_message?: string;
  system_prompt?: string;
  response_style?: any;
  traits?: any;
}

interface TierLimits {
  subscription_tier: string;
  limits: {
    default_personalities: number;
    custom_personalities_allowed: number;
    custom_personalities_used: number;
    custom_personalities_remaining: number;
    can_create_more: boolean;
  };
}

interface AudioValidation {
  valid: boolean;
  duration: number;
  sample_rate: number;
  bit_depth: number;
  file_size_mb: number;
  format: string;
}

interface QualityAssessment {
  score: number;
  rating: 'excellent' | 'good' | 'acceptable' | 'poor';
  warnings: string[];
}

const Personalities: React.FC = () => {
  const { token } = useAuth();
  const { currentStore } = useStoreContext();
  const [personalities, setPersonalities] = useState<Personality[]>([]);
  const [tierLimits, setTierLimits] = useState<TierLimits | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedPersonality, setSelectedPersonality] = useState<Personality | null>(null);
  const [showVoiceUpload, setShowVoiceUpload] = useState(false);
  const [uploadingVoice, setUploadingVoice] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [validation, setValidation] = useState<AudioValidation | null>(null);
  const [quality, setQuality] = useState<QualityAssessment | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [showVoiceTest, setShowVoiceTest] = useState(false);
  const [testPersonality, setTestPersonality] = useState<Personality | null>(null);
  const [showCreateEdit, setShowCreateEdit] = useState(false);
  const [editPersonality, setEditPersonality] = useState<Personality | null>(null);
  const [isEditMode, setIsEditMode] = useState(false);
  const [templatePersonality, setTemplatePersonality] = useState<Personality | null>(null);

  // Fetch personalities
  const fetchPersonalities = useCallback(async () => {
    if (!currentStore?.tenant_id) return;  // Wait for full store data with tenant_id

    setIsLoading(true);
    try {
      const response = await fetch(
        `${API_BASE_URL}/personalities?tenant_id=${currentStore.tenant_id}&include_defaults=true`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'X-Store-ID': currentStore.id
          }
        }
      );

      if (!response.ok) throw new Error('Failed to fetch personalities');

      const data = await response.json();
      setPersonalities(data.personalities || []);
    } catch (error) {
      console.error('Error fetching personalities:', error);
      toast.error('Failed to load personalities');
    } finally {
      setIsLoading(false);
    }
  }, [token, currentStore]);

  // Fetch tier limits
  const fetchTierLimits = useCallback(async () => {
    if (!currentStore?.tenant_id) return;  // Wait for full store data with tenant_id

    try {
      const response = await fetch(
        `${API_BASE_URL}/personalities/limits/${currentStore.tenant_id}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'X-Store-ID': currentStore.id
          }
        }
      );

      if (!response.ok) throw new Error('Failed to fetch tier limits');

      const data = await response.json();
      setTierLimits(data);
    } catch (error) {
      console.error('Error fetching tier limits:', error);
    }
  }, [token, currentStore]);

  useEffect(() => {
    fetchPersonalities();
    fetchTierLimits();
  }, [fetchPersonalities, fetchTierLimits]);

  // Validate voice file
  const validateVoiceFile = async (file: File) => {
    const formData = new FormData();
    formData.append('audio', file);

    try {
      const response = await fetch(
        '${API_BASE_URL}/personalities/validate-voice',
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`
          },
          body: formData
        }
      );

      if (!response.ok) {
        const error = await response.json();
        toast.error(error.detail || 'Validation failed');
        return false;
      }

      const data = await response.json();
      setValidation(data.validation);
      setQuality(data.quality);
      return true;
    } catch (error) {
      console.error('Validation error:', error);
      toast.error('Failed to validate audio file');
      return false;
    }
  };

  // Handle file selection
  const handleFileSelect = async (file: File) => {
    if (!file.name.endsWith('.wav')) {
      toast.error('Only WAV files are supported');
      return;
    }

    setSelectedFile(file);
    await validateVoiceFile(file);
  };

  // Handle drag and drop
  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      await handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  // Upload voice sample
  const uploadVoiceSample = async () => {
    if (!selectedPersonality || !selectedFile) return;

    setUploadingVoice(true);
    const formData = new FormData();
    formData.append('audio', selectedFile);

    try {
      const response = await fetch(
        `${API_BASE_URL}/personalities/${selectedPersonality.id}/voice`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`
          },
          body: formData
        }
      );

      if (!response.ok) {
        const error = await response.json();
        toast.error(error.detail || 'Upload failed');
        return;
      }

      await response.json(); // Consume response
      toast.success('Voice sample uploaded successfully!');

      // Refresh personalities
      await fetchPersonalities();

      // Reset state
      setShowVoiceUpload(false);
      setSelectedFile(null);
      setValidation(null);
      setQuality(null);
    } catch (error) {
      console.error('Upload error:', error);
      toast.error('Failed to upload voice sample');
    } finally {
      setUploadingVoice(false);
    }
  };

  // Delete voice sample
  const deleteVoiceSample = async (personalityId: string) => {
    if (!confirm('Are you sure you want to delete this voice sample?')) return;

    try {
      const response = await fetch(
        `${API_BASE_URL}/personalities/${personalityId}/voice`,
        {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );

      if (!response.ok) throw new Error('Failed to delete voice sample');

      toast.success('Voice sample deleted');
      await fetchPersonalities();
    } catch (error) {
      console.error('Delete error:', error);
      toast.error('Failed to delete voice sample');
    }
  };

  // Copy default personality as template
  const handleCopyAsTemplate = (personality: Personality) => {
    // Create a template copy with cleared ID and custom naming
    const template: Personality = {
      ...personality,
      id: '', // Clear ID so a new one is created
      name: '', // User will need to provide a unique name
      personality_name: `${personality.personality_name} (Copy)`,
      is_default: false,
      has_voice_sample: false, // Don't copy voice sample
      tenant_id: currentStore?.tenant_id || personality.tenant_id
    };

    setTemplatePersonality(template);
    setIsEditMode(false);
    setEditPersonality(null);
    setShowCreateEdit(true);
  };

  // Get quality color
  const getQualityColor = (rating: string) => {
    switch (rating) {
      case 'excellent': return 'text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/30';
      case 'good': return 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/30';
      case 'acceptable': return 'text-yellow-600 dark:text-yellow-400 bg-yellow-50 dark:bg-yellow-900/30';
      case 'poor': return 'text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/30';
      default: return 'text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-900/30';
    }
  };

  // Show message if no store selected or tenant_id not loaded yet
  if (!currentStore?.tenant_id) {
    return (
      <div className="flex flex-col items-center justify-center h-64 space-y-4">
        <AlertCircle className="h-12 w-12 text-gray-400" />
        <div className="text-center">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            {!currentStore?.id ? 'No Store Selected' : 'Loading Store Data...'}
          </h3>
          <p className="text-gray-600 dark:text-gray-400">
            {!currentStore?.id
              ? 'Please select a store from the dropdown to manage AI personalities'
              : 'Loading tenant information...'}
          </p>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 text-accent-600 dark:text-accent-400 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            AI Personalities
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Manage voice-enabled AI personalities for your store
          </p>
        </div>

        <div className="flex items-center gap-4">
          {/* Create Button */}
          {tierLimits && tierLimits.limits.can_create_more && (
            <button
              onClick={() => {
                setIsEditMode(false);
                setEditPersonality(null);
                setTemplatePersonality(null);
                setShowCreateEdit(true);
              }}
              className="flex items-center gap-2 px-4 py-2 bg-accent-600 dark:bg-accent-500 text-white rounded-md hover:bg-accent-700 dark:hover:bg-accent-600 transition-colors"
            >
              <Plus className="h-5 w-5" />
              Create Personality
            </button>
          )}


          {/* Tier Info */}
          {tierLimits && (
            <div className="text-right">
              <div className="text-sm text-gray-600 dark:text-gray-400">
                {tierLimits.subscription_tier.replace('_', ' ').toUpperCase()} Plan
              </div>
              <div className="text-lg font-semibold text-gray-900 dark:text-white">
                {tierLimits.limits.custom_personalities_used} / {tierLimits.limits.custom_personalities_allowed} Custom
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Tier Info Banner */}
      {tierLimits && !tierLimits.limits.can_create_more && (
        <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-yellow-600 dark:text-yellow-400 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="text-sm font-medium text-yellow-800 dark:text-yellow-200">
                Personality Limit Reached
              </h3>
              <p className="text-sm text-yellow-700 dark:text-yellow-300 mt-1">
                You've reached the maximum of {tierLimits.limits.custom_personalities_allowed} custom personalities for your plan.
                Upgrade to create more personalized AI assistants.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Empty State */}
      {personalities.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-64 space-y-4 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg">
          <Users className="h-16 w-16 text-gray-400" />
          <div className="text-center max-w-md">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              No Personalities Found
            </h3>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              No AI personalities have been configured yet. Create your first personality or load default personalities from the database.
            </p>
            <div className="text-sm text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 rounded p-3">
              <strong>Tip:</strong> Run the seed script to add default personalities (marcel, shanté, zac):
              <code className="block mt-2 text-xs bg-gray-100 dark:bg-gray-700 p-2 rounded">
                PGPASSWORD=weedgo123 psql -h localhost -p 5434 -U weedgo -d ai_engine -f migrations/seed_default_personalities.sql
              </code>
            </div>
          </div>
        </div>
      ) : (
        /* Personalities Grid */
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {personalities.map((personality) => (
            <div
            key={personality.id}
            className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 hover:shadow-lg transition-shadow"
          >
            {/* Header */}
            <div className="flex items-start justify-between mb-4">
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                    {personality.personality_name || personality.name}
                  </h3>
                  {personality.is_default && (
                    <Crown className="h-4 w-4 text-yellow-500" />
                  )}
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400 capitalize mt-1">
                  {personality.tone} tone
                </p>
              </div>

              <div className="flex items-center gap-2">
                {personality.is_default ? (
                  <button
                    onClick={() => handleCopyAsTemplate(personality)}
                    className="flex items-center gap-1 px-2 py-1 text-xs bg-accent-100 dark:bg-accent-900/30 text-accent-700 dark:text-accent-300 rounded hover:bg-accent-200 dark:hover:bg-accent-900/50 transition-colors"
                    title="Copy as template for new personality"
                  >
                    <Copy className="h-3 w-3" />
                    Copy Template
                  </button>
                ) : (
                  <button
                    onClick={() => {
                      setIsEditMode(true);
                      setEditPersonality(personality);
                      setTemplatePersonality(null);
                      setShowCreateEdit(true);
                    }}
                    className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                    title="Edit personality"
                  >
                    <Edit className="h-4 w-4" />
                  </button>
                )}
              </div>
            </div>

            {/* Voice Status */}
            <div className="mb-4">
              <div className="flex items-center gap-2 text-sm">
                {personality.has_voice_sample ? (
                  <>
                    <Check className="h-4 w-4 text-green-500" />
                    <span className="text-green-600 dark:text-green-400 font-medium">
                      Voice sample uploaded
                    </span>
                  </>
                ) : (
                  <>
                    <AlertCircle className="h-4 w-4 text-gray-400" />
                    <span className="text-gray-500 dark:text-gray-400">
                      No voice sample
                    </span>
                  </>
                )}
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Provider: {personality.voice_provider}
              </div>
            </div>

            {/* Actions */}
            <div className="space-y-2">
              {personality.has_voice_sample ? (
                <>
                  {/* Test Voice Button - Full Width */}
                  <button
                    onClick={() => {
                      setTestPersonality(personality);
                      setShowVoiceTest(true);
                    }}
                    className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-accent-600 dark:bg-accent-500 text-white rounded-md hover:bg-accent-700 dark:hover:bg-accent-600 transition-colors text-sm"
                  >
                    <Volume2 className="h-4 w-4" />
                    Test Voice
                  </button>

                  {/* Replace and Delete - Side by Side */}
                  <div className="flex gap-2">
                    <button
                      onClick={() => {
                        setSelectedPersonality(personality);
                        setShowVoiceUpload(true);
                      }}
                      className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors text-sm"
                    >
                      <Upload className="h-4 w-4" />
                      Replace
                    </button>
                    <button
                      onClick={() => deleteVoiceSample(personality.id)}
                      className="px-3 py-2 bg-red-50 dark:bg-red-900/30 text-red-600 dark:text-red-400 rounded-md hover:bg-red-100 dark:hover:bg-red-900/50 transition-colors"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </>
              ) : (
                <button
                  onClick={() => {
                    setSelectedPersonality(personality);
                    setShowVoiceUpload(true);
                  }}
                  className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-accent-600 dark:bg-accent-500 text-white rounded-md hover:bg-accent-700 dark:hover:bg-accent-600 transition-colors text-sm"
                >
                  <Upload className="h-4 w-4" />
                  Upload Voice
                </button>
              )}
            </div>
          </div>
        ))}
        </div>
      )}

      {/* Voice Upload Modal - New Improved Version */}
      <VoiceRecordUploadModal
        isOpen={showVoiceUpload}
        onClose={() => {
          setShowVoiceUpload(false);
          setSelectedPersonality(null);
        }}
        personalityId={selectedPersonality?.id || ''}
        personalityName={selectedPersonality?.personality_name || ''}
        onUploadComplete={() => {
          fetchPersonalities();
        }}
        token={token}
      />

      {/* Voice Test Modal */}
      {showVoiceTest && testPersonality && token && (
        <VoiceTestModal
          personality={{
            id: testPersonality.id,
            personality_name: testPersonality.personality_name || testPersonality.name,
            name: testPersonality.name,
            has_voice_sample: testPersonality.has_voice_sample,
            voice_provider: testPersonality.voice_provider
          }}
          onClose={() => {
            setShowVoiceTest(false);
            setTestPersonality(null);
          }}
          token={token}
        />
      )}

      {/* Create/Edit Personality Modal */}
      {showCreateEdit && currentStore?.tenant_id && token && (
        <CreateEditPersonalityModal
          personality={editPersonality || templatePersonality}
          isEdit={isEditMode}
          tenantId={currentStore.tenant_id}
          token={token}
          onClose={() => {
            setShowCreateEdit(false);
            setEditPersonality(null);
            setTemplatePersonality(null);
            setIsEditMode(false);
          }}
          onSuccess={() => {
            fetchPersonalities();
            fetchTierLimits();
          }}
        />
      )}
    </div>
  );
};

export default Personalities;
