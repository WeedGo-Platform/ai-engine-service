import { useState, useEffect, useRef } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import apiService from '../services/api';
import toast from 'react-hot-toast';
import { User, Plus, Trash2, Edit2, Check, X, Upload, Image } from 'lucide-react';

interface Personality {
  id: string;
  name: string;
  avatar?: string;
  emoji?: string; // Add emoji as avatar option
  age: string;
  gender: string;
  traits: string[];
  communication_style: string;
  knowledge_level: string;
  humor_level: 'none' | 'light' | 'moderate' | 'high';
  formality: 'very_casual' | 'casual' | 'balanced' | 'formal' | 'very_formal';
  empathy_level: 'low' | 'medium' | 'high';
  description: string;
  sample_responses: {
    greeting: string;
    product_recommendation: string;
    no_stock: string;
    closing: string;
  };
  active: boolean;
}

export default function AIPersonality() {
  const queryClient = useQueryClient();
  
  // Fetch personalities from API
  const { data: personalitiesData, isLoading, error } = useQuery({
    queryKey: ['personalities'],
    queryFn: () => apiService.getPersonalities(),
  });
  
  const personalities = personalitiesData?.personalities || [];
  const [selectedPersonality, setSelectedPersonality] = useState<Personality | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editForm, setEditForm] = useState<Personality | null>(null);
  const [showNewPersonalityModal, setShowNewPersonalityModal] = useState(false);
  const [newPersonalityForm, setNewPersonalityForm] = useState<Partial<Personality>>({
    name: '',
    emoji: '🧑‍🌾', // Default emoji avatar
    age: '',
    gender: 'Male',
    traits: [],
    communication_style: '',
    knowledge_level: 'Expert',
    humor_level: 'moderate',
    formality: 'balanced',
    empathy_level: 'medium',
    description: '',
    sample_responses: {
      greeting: '',
      product_recommendation: '',
      no_stock: '',
      closing: ''
    },
    active: false
  });
  const [newTrait, setNewTrait] = useState('');
  const [avatarType, setAvatarType] = useState<'emoji' | 'upload'>('emoji');
  const [uploadedAvatar, setUploadedAvatar] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  // Edit mode avatar state
  const [editAvatarType, setEditAvatarType] = useState<'emoji' | 'upload'>('emoji');
  const [editUploadedAvatar, setEditUploadedAvatar] = useState<string | null>(null);
  const editFileInputRef = useRef<HTMLInputElement>(null);

  // Handle file upload for avatar
  const handleAvatarUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (file.size > 5 * 1024 * 1024) { // 5MB limit
        toast.error('Avatar image must be less than 5MB');
        return;
      }
      
      const reader = new FileReader();
      reader.onloadend = () => {
        const base64String = reader.result as string;
        setUploadedAvatar(base64String);
        setNewPersonalityForm({ ...newPersonalityForm, avatar: base64String, emoji: undefined });
      };
      reader.readAsDataURL(file);
    }
  };
  
  // Handle file upload for edit avatar
  const handleEditAvatarUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (file.size > 5 * 1024 * 1024) { // 5MB limit
        toast.error('Avatar image must be less than 5MB');
        return;
      }
      
      const reader = new FileReader();
      reader.onloadend = () => {
        const base64String = reader.result as string;
        setEditUploadedAvatar(base64String);
        if (editForm) {
          setEditForm({ ...editForm, avatar: base64String, emoji: undefined });
        }
      };
      reader.readAsDataURL(file);
    }
  };

  // Set selected personality when data is fetched
  useEffect(() => {
    if (personalities.length > 0 && !selectedPersonality) {
      // Set the first active personality as selected
      const activePersonality = personalities.find((p: Personality) => p.active);
      if (activePersonality) {
        setSelectedPersonality(activePersonality);
      } else if (personalities.length > 0) {
        setSelectedPersonality(personalities[0]);
      }
    }
  }, [personalities, selectedPersonality]);

  // Save personality mutation
  const savePersonality = useMutation({
    mutationFn: (personality: Personality) => apiService.savePersonality(personality),
    onSuccess: () => {
      setIsEditing(false);
      setEditForm(null);
      setEditAvatarType('emoji');
      setEditUploadedAvatar(null);
      toast.success('Personality saved successfully');
      queryClient.invalidateQueries({ queryKey: ['personalities'] });
    },
    onError: () => {
      toast.error('Failed to save personality');
    }
  });



  // Create new personality
  const createPersonality = () => {
    if (!newPersonalityForm.name || !newPersonalityForm.description) {
      toast.error('Please fill in all required fields');
      return;
    }

    const newPersonality: Personality = {
      id: `personality-${Date.now()}`,
      name: newPersonalityForm.name!,
      avatar: newPersonalityForm.avatar || undefined,
      emoji: newPersonalityForm.emoji || (avatarType === 'emoji' ? '🧑‍🌾' : undefined),
      age: newPersonalityForm.age || '30',
      gender: newPersonalityForm.gender || 'Male',
      traits: newPersonalityForm.traits || [],
      communication_style: newPersonalityForm.communication_style || '',
      knowledge_level: newPersonalityForm.knowledge_level || 'Expert',
      humor_level: newPersonalityForm.humor_level || 'moderate',
      formality: newPersonalityForm.formality || 'balanced',
      empathy_level: newPersonalityForm.empathy_level || 'medium',
      description: newPersonalityForm.description!,
      sample_responses: newPersonalityForm.sample_responses || {
        greeting: '',
        product_recommendation: '',
        no_stock: '',
        closing: ''
      },
      active: false
    };

    savePersonality.mutate(newPersonality);
    setShowNewPersonalityModal(false);
    resetNewPersonalityForm();
  };

  // Reset new personality form
  const resetNewPersonalityForm = () => {
    setNewPersonalityForm({
      name: '',
      avatar: undefined,
      emoji: '🧑‍🌾',
      age: '',
      gender: 'Male',
      traits: [],
      communication_style: '',
      knowledge_level: 'Expert',
      humor_level: 'moderate',
      formality: 'balanced',
      empathy_level: 'medium',
      description: '',
      sample_responses: {
        greeting: '',
        product_recommendation: '',
        no_stock: '',
        closing: ''
      },
      active: false
    });
    setNewTrait('');
    setAvatarType('emoji');
    setUploadedAvatar(null);
  };

  // Add trait to new personality
  const addTraitToNewPersonality = () => {
    if (newTrait.trim()) {
      setNewPersonalityForm(prev => ({
        ...prev,
        traits: [...(prev.traits || []), newTrait.trim()]
      }));
      setNewTrait('');
    }
  };

  // Remove trait from new personality
  const removeTraitFromNewPersonality = (index: number) => {
    setNewPersonalityForm(prev => ({
      ...prev,
      traits: prev.traits?.filter((_, i) => i !== index) || []
    }));
  };

  // Delete personality mutation
  const deletePersonalityMutation = useMutation({
    mutationFn: (id: string) => apiService.deletePersonality(id),
    onSuccess: (_, deletedId) => {
      toast.success('Personality deleted successfully');
      queryClient.invalidateQueries({ queryKey: ['personalities'] });
      // If we deleted the selected personality, select another one
      if (selectedPersonality?.id === deletedId) {
        const remaining = personalities.filter(p => p.id !== deletedId);
        setSelectedPersonality(remaining[0] || null);
      }
    },
    onError: (error) => {
      console.error('Failed to delete personality:', error);
      toast.error('Failed to delete personality');
    }
  });

  const deletePersonality = (id: string) => {
    if (personalities.find(p => p.id === id)?.active) {
      toast.error('Cannot delete active personality. Please deactivate it first.');
      return;
    }
    if (confirm(`Are you sure you want to delete this personality?`)) {
      deletePersonalityMutation.mutate(id);
    }
  };

  // Activate personality mutation
  const activatePersonalityMutation = useMutation({
    mutationFn: (id: string) => apiService.activatePersonality(id),
    onSuccess: () => {
      toast.success('Personality activated successfully');
      queryClient.invalidateQueries({ queryKey: ['personalities'] });
    },
    onError: (error) => {
      console.error('Failed to activate personality:', error);
      toast.error('Failed to activate personality');
    }
  });

  const activatePersonality = (id: string) => {
    activatePersonalityMutation.mutate(id);
  };

  // Start editing
  const startEdit = (personality: Personality) => {
    setEditForm({ 
      ...personality,
      traits: Array.isArray(personality.traits) ? personality.traits : []
    });
    setIsEditing(true);
    // Set avatar type based on existing data
    if (personality.avatar) {
      setEditAvatarType('upload');
      setEditUploadedAvatar(personality.avatar);
    } else {
      setEditAvatarType('emoji');
      setEditUploadedAvatar(null);
    }
  };

  // Save edit
  const saveEdit = () => {
    if (editForm) {
      // Ensure all required fields are present for the API
      const personalityData = {
        ...editForm,
        // Add missing fields that API expects
        humor_style: editForm.humor_level === 'none' ? 'none' : 'witty', // API expects humor_style
        response_length: 'medium', // Default value
        jargon_level: 'moderate', // Default value
        sales_approach: 'consultative', // Default value
        // Ensure traits is an array
        traits: editForm.traits || [],
        // Ensure sample_responses has all fields
        sample_responses: {
          greeting: editForm.sample_responses?.greeting || '',
          product_recommendation: editForm.sample_responses?.product_recommendation || '',
          no_stock: editForm.sample_responses?.no_stock || '',
          closing: editForm.sample_responses?.closing || ''
        }
      };
      
      console.log('Saving personality with data:', personalityData);
      savePersonality.mutate(personalityData);
    }
  };

  // Cancel edit
  const cancelEdit = () => {
    setIsEditing(false);
    setEditForm(null);
    setEditAvatarType('emoji');
    setEditUploadedAvatar(null);
  };

  // Show loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-weed-green-500 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading personalities...</p>
        </div>
      </div>
    );
  }

  // Show error state
  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <h3 className="text-red-800 font-semibold mb-2">Error Loading Personalities</h3>
        <p className="text-red-600">Failed to load personality data. Please check if the API server is running.</p>
        <button 
          onClick={() => queryClient.invalidateQueries({ queryKey: ['personalities'] })}
          className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-xl shadow-sm p-6">
        <div className="flex justify-between items-center mb-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">AI Personality Setup</h2>
            <p className="text-gray-600 mt-1">Configure the personality and communication style of your AI budtender</p>
          </div>
          <button 
            onClick={() => setShowNewPersonalityModal(true)}
            className="px-4 py-2 bg-weed-green-500 text-white rounded-lg hover:bg-weed-green-600 flex items-center space-x-2"
          >
            <Plus className="w-5 h-5" />
            <span>New Personality</span>
          </button>
        </div>

        {/* Active Personality Banner */}
        {personalities.find(p => p.active) && (
          <div className="bg-gradient-to-r from-weed-green-500 to-weed-green-600 rounded-lg p-4 text-white">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center">
                  <User className="w-8 h-8" />
                </div>
                <div>
                  <p className="text-sm opacity-90">Currently Active</p>
                  <p className="text-xl font-bold">{personalities.find(p => p.active)?.name}</p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-sm opacity-90">Communication Style</p>
                <p className="font-medium">{personalities.find(p => p.active)?.communication_style}</p>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Personality List */}
        <div className="col-span-1 space-y-4">
          <div className="bg-white rounded-xl shadow-sm p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Personalities</h3>
            <div className="space-y-3">
              {personalities.map((personality) => (
                <div
                  key={personality.id}
                  onClick={() => setSelectedPersonality(personality)}
                  className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                    selectedPersonality?.id === personality.id
                      ? 'border-weed-green-500 bg-weed-green-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 bg-gray-200 rounded-full flex items-center justify-center text-xl overflow-hidden">
                        {personality.avatar ? (
                          <img src={personality.avatar} alt={personality.name} className="w-full h-full object-cover" />
                        ) : personality.emoji ? (
                          personality.emoji
                        ) : (
                          <User className="w-6 h-6 text-gray-600" />
                        )}
                      </div>
                      <div>
                        <h4 className="font-medium">{personality.name}</h4>
                        <p className="text-xs text-gray-500">{personality.age} • {personality.gender}</p>
                      </div>
                    </div>
                    {personality.active && (
                      <span className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded-full">Active</span>
                    )}
                  </div>
                  <p className="text-sm text-gray-600">{personality.description}</p>
                  <div className="flex flex-wrap gap-1 mt-2">
                    {Array.isArray(personality.traits) && personality.traits.slice(0, 3).map((trait) => (
                      <span key={trait} className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded">
                        {trait}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Personality Details */}
        <div className="col-span-2 bg-white rounded-xl shadow-sm p-6">
          {selectedPersonality && !isEditing ? (
            <>
              <div className="flex justify-between items-start mb-6">
                <div>
                  <h3 className="text-2xl font-bold text-gray-900">{selectedPersonality.name}</h3>
                  <p className="text-gray-600 mt-1">{selectedPersonality.description}</p>
                </div>
                <div className="flex space-x-2">
                  <button
                    onClick={() => startEdit(selectedPersonality)}
                    className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 flex items-center space-x-2"
                  >
                    <Edit2 className="w-4 h-4" />
                    <span>Edit</span>
                  </button>
                  {!selectedPersonality.active && (
                    <>
                      <button
                        onClick={() => activatePersonality(selectedPersonality.id)}
                        className="px-4 py-2 bg-weed-green-500 text-white rounded-lg hover:bg-weed-green-600 flex items-center space-x-2"
                      >
                        <Check className="w-4 h-4" />
                        <span>Activate</span>
                      </button>
                      {!['marcel', 'shante', 'kareem'].includes(selectedPersonality.id) && (
                        <button
                          onClick={() => deletePersonality(selectedPersonality.id)}
                          className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 flex items-center space-x-2"
                        >
                          <Trash2 className="w-4 h-4" />
                          <span>Delete</span>
                        </button>
                      )}
                    </>
                  )}
                </div>
              </div>

              {/* Personality Attributes */}
              <div className="grid grid-cols-2 gap-6 mb-6">
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-3">Characteristics</h4>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Age</span>
                      <span className="text-sm font-medium">{selectedPersonality.age}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Gender</span>
                      <span className="text-sm font-medium">{selectedPersonality.gender}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Knowledge Level</span>
                      <span className="text-sm font-medium">{selectedPersonality.knowledge_level}</span>
                    </div>
                  </div>
                </div>

                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-3">Communication Style</h4>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Humor</span>
                      <span className="text-sm font-medium capitalize">{selectedPersonality.humor_level}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Formality</span>
                      <span className="text-sm font-medium capitalize">{selectedPersonality.formality.replace('_', ' ')}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Empathy</span>
                      <span className="text-sm font-medium capitalize">{selectedPersonality.empathy_level}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Traits */}
              <div className="mb-6">
                <h4 className="text-sm font-medium text-gray-700 mb-3">Personality Traits</h4>
                <div className="flex flex-wrap gap-2">
                  {Array.isArray(selectedPersonality.traits) && selectedPersonality.traits.map((trait) => (
                    <span key={trait} className="px-3 py-1 bg-purple-haze-100 text-purple-haze-700 rounded-full text-sm">
                      {trait}
                    </span>
                  ))}
                </div>
              </div>

              {/* Sample Responses */}
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-3">Sample Responses</h4>
                <div className="space-y-4">
                  <div className="bg-gray-50 rounded-lg p-4">
                    <p className="text-xs font-medium text-gray-500 mb-1">Greeting</p>
                    <p className="text-sm text-gray-800 italic">"{selectedPersonality.sample_responses.greeting}"</p>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <p className="text-xs font-medium text-gray-500 mb-1">Product Recommendation</p>
                    <p className="text-sm text-gray-800 italic">"{selectedPersonality.sample_responses.product_recommendation}"</p>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <p className="text-xs font-medium text-gray-500 mb-1">Out of Stock</p>
                    <p className="text-sm text-gray-800 italic">"{selectedPersonality.sample_responses.no_stock}"</p>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <p className="text-xs font-medium text-gray-500 mb-1">Closing</p>
                    <p className="text-sm text-gray-800 italic">"{selectedPersonality.sample_responses.closing}"</p>
                  </div>
                </div>
              </div>
            </>
          ) : isEditing && editForm ? (
            // Edit Form
            <div>
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-xl font-bold text-gray-900">Edit Personality</h3>
                <div className="flex space-x-2">
                  <button
                    onClick={cancelEdit}
                    className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={saveEdit}
                    className="px-4 py-2 bg-weed-green-500 text-white rounded-lg hover:bg-weed-green-600"
                  >
                    Save Changes
                  </button>
                </div>
              </div>

              <div className="space-y-4">
                {/* Avatar Section */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Avatar</label>
                  
                  {/* Avatar Type Selector */}
                  <div className="flex gap-2 mb-3">
                    <button
                      type="button"
                      onClick={() => setEditAvatarType('emoji')}
                      className={`px-4 py-2 rounded-lg border-2 transition-all ${
                        editAvatarType === 'emoji'
                          ? 'border-weed-green-500 bg-weed-green-50 text-weed-green-700'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      Select Emoji
                    </button>
                    <button
                      type="button"
                      onClick={() => setEditAvatarType('upload')}
                      className={`px-4 py-2 rounded-lg border-2 transition-all ${
                        editAvatarType === 'upload'
                          ? 'border-weed-green-500 bg-weed-green-50 text-weed-green-700'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      Upload Image
                    </button>
                  </div>

                  {/* Emoji Selection */}
                  {editAvatarType === 'emoji' ? (
                    <div className="grid grid-cols-8 gap-2 max-h-64 overflow-y-auto p-2 border border-gray-200 rounded-lg">
                      {[
                        // Light skin tone
                        '👨🏻', '👩🏻', '🧑🏻', '👴🏻', '👵🏻', '👨🏻‍🌾', '👩🏻‍⚕️', '🧑🏻‍🎤',
                        // Medium-light skin tone  
                        '👨🏼', '👩🏼', '🧑🏼', '👴🏼', '👵🏼', '👨🏼‍💼', '👩🏼‍🔬', '🧑🏼‍💻',
                        // Medium skin tone
                        '👨🏽', '👩🏽', '🧑🏽', '👴🏽', '👵🏽', '👨🏽‍🏫', '👩🏽‍🎓', '🧑🏽‍🍳',
                        // Medium-dark skin tone
                        '👨🏾', '👩🏾', '🧑🏾', '👴🏾', '👵🏾', '👨🏾‍🎨', '👩🏾‍💼', '🧑🏾‍🔧',
                        // Dark skin tone
                        '👨🏿', '👩🏿', '🧑🏿', '👴🏿', '👵🏿', '👨🏿‍🌾', '👩🏿‍⚕️', '🧑🏿‍🎤',
                        // Additional diverse options
                        '🧔🏻', '🧔🏼', '🧔🏽', '🧔🏾', '🧔🏿', '👳🏻‍♂️', '👳🏽‍♀️', '👳🏿‍♂️',
                        '🧕🏻', '🧕🏼', '🧕🏽', '🧕🏾', '🧕🏿', '👮🏻', '👮🏽', '👮🏿'
                      ].map((emoji) => (
                        <button
                          key={emoji}
                          type="button"
                          onClick={() => {
                            setEditForm({ ...editForm, emoji, avatar: undefined });
                            setEditUploadedAvatar(null);
                          }}
                          className={`w-12 h-12 rounded-lg border-2 flex items-center justify-center text-2xl transition-all ${
                            editForm.emoji === emoji 
                              ? 'border-weed-green-500 bg-weed-green-50' 
                              : 'border-gray-200 hover:border-gray-300'
                          }`}
                        >
                          {emoji}
                        </button>
                      ))}
                    </div>
                  ) : (
                    /* Upload Image */
                    <div className="space-y-3">
                      <input
                        ref={editFileInputRef}
                        type="file"
                        accept="image/*"
                        onChange={handleEditAvatarUpload}
                        className="hidden"
                      />
                      
                      <div className="flex items-center gap-4">
                        {editUploadedAvatar || editForm.avatar ? (
                          <div className="relative">
                            <img 
                              src={editUploadedAvatar || editForm.avatar} 
                              alt="Avatar preview" 
                              className="w-20 h-20 rounded-full object-cover border-2 border-gray-200"
                            />
                            <button
                              type="button"
                              onClick={() => {
                                setEditUploadedAvatar(null);
                                setEditForm({ ...editForm, avatar: undefined });
                              }}
                              className="absolute -top-1 -right-1 bg-red-500 text-white rounded-full p-1"
                            >
                              <X className="w-3 h-3" />
                            </button>
                          </div>
                        ) : (
                          <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center">
                            <Image className="w-8 h-8 text-gray-400" />
                          </div>
                        )}
                        
                        <button
                          type="button"
                          onClick={() => editFileInputRef.current?.click()}
                          className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 flex items-center gap-2"
                        >
                          <Upload className="w-4 h-4" />
                          {editUploadedAvatar || editForm.avatar ? 'Change' : 'Upload'} Avatar
                        </button>
                      </div>
                      
                      <p className="text-xs text-gray-500">
                        Recommended: Square image, max 5MB (JPG, PNG, GIF)
                      </p>
                    </div>
                  )}
                </div>

                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                    <input
                      type="text"
                      value={editForm.name}
                      onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Age</label>
                    <input
                      type="text"
                      value={editForm.age}
                      onChange={(e) => setEditForm({ ...editForm, age: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Gender</label>
                    <select
                      value={editForm.gender}
                      onChange={(e) => setEditForm({ ...editForm, gender: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    >
                      <option value="Male">Male</option>
                      <option value="Female">Female</option>
                      <option value="Non-binary">Non-binary</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                  <textarea
                    value={editForm.description}
                    onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Communication Style</label>
                    <input
                      type="text"
                      value={editForm.communication_style}
                      onChange={(e) => setEditForm({ ...editForm, communication_style: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                      placeholder="e.g., Professional yet approachable"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Knowledge Level</label>
                    <select
                      value={editForm.knowledge_level}
                      onChange={(e) => setEditForm({ ...editForm, knowledge_level: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    >
                      <option value="Beginner">Beginner</option>
                      <option value="Intermediate">Intermediate</option>
                      <option value="Expert">Expert</option>
                      <option value="Master">Master</option>
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Humor Level</label>
                    <select
                      value={editForm.humor_level}
                      onChange={(e) => setEditForm({ ...editForm, humor_level: e.target.value as any })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    >
                      <option value="none">None</option>
                      <option value="light">Light</option>
                      <option value="moderate">Moderate</option>
                      <option value="high">High</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Formality</label>
                    <select
                      value={editForm.formality}
                      onChange={(e) => setEditForm({ ...editForm, formality: e.target.value as any })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    >
                      <option value="very_casual">Very Casual</option>
                      <option value="casual">Casual</option>
                      <option value="balanced">Balanced</option>
                      <option value="formal">Formal</option>
                      <option value="very_formal">Very Formal</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Empathy Level</label>
                    <select
                      value={editForm.empathy_level}
                      onChange={(e) => setEditForm({ ...editForm, empathy_level: e.target.value as any })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    >
                      <option value="low">Low</option>
                      <option value="medium">Medium</option>
                      <option value="high">High</option>
                    </select>
                  </div>
                </div>

                {/* Traits Section */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Personality Traits</label>
                  <div className="flex flex-wrap gap-2 mb-2">
                    {Array.isArray(editForm.traits) && editForm.traits.map((trait, index) => (
                      <span key={index} className="px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-sm flex items-center gap-1">
                        {trait}
                        <button
                          type="button"
                          onClick={() => {
                            const newTraits = Array.isArray(editForm.traits) ? editForm.traits.filter((_, i) => i !== index) : [];
                            setEditForm({ ...editForm, traits: newTraits });
                          }}
                          className="ml-1 text-purple-500 hover:text-purple-700"
                        >
                          ×
                        </button>
                      </span>
                    ))}
                  </div>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      placeholder="Add a trait..."
                      onKeyPress={(e) => {
                        if (e.key === 'Enter' && e.currentTarget.value.trim()) {
                          e.preventDefault();
                          setEditForm({ 
                            ...editForm, 
                            traits: [...(Array.isArray(editForm.traits) ? editForm.traits : []), e.currentTarget.value.trim()] 
                          });
                          e.currentTarget.value = '';
                        }
                      }}
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-lg"
                    />
                  </div>
                </div>

                {/* Sample Responses */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Sample Responses</label>
                  <div className="space-y-3">
                    <div>
                      <label className="block text-xs text-gray-600 mb-1">Greeting</label>
                      <textarea
                        value={editForm.sample_responses.greeting}
                        onChange={(e) => setEditForm({ 
                          ...editForm, 
                          sample_responses: { ...editForm.sample_responses, greeting: e.target.value }
                        })}
                        rows={2}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                        placeholder="How this personality greets customers..."
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-gray-600 mb-1">Product Recommendation</label>
                      <textarea
                        value={editForm.sample_responses.product_recommendation}
                        onChange={(e) => setEditForm({ 
                          ...editForm, 
                          sample_responses: { ...editForm.sample_responses, product_recommendation: e.target.value }
                        })}
                        rows={2}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                        placeholder="How they recommend products..."
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-gray-600 mb-1">Out of Stock Response</label>
                      <textarea
                        value={editForm.sample_responses.no_stock}
                        onChange={(e) => setEditForm({ 
                          ...editForm, 
                          sample_responses: { ...editForm.sample_responses, no_stock: e.target.value }
                        })}
                        rows={2}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                        placeholder="Response when item is out of stock..."
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-gray-600 mb-1">Closing/Goodbye</label>
                      <textarea
                        value={editForm.sample_responses.closing}
                        onChange={(e) => setEditForm({ 
                          ...editForm, 
                          sample_responses: { ...editForm.sample_responses, closing: e.target.value }
                        })}
                        rows={2}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                        placeholder="How they say goodbye..."
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center text-gray-500 mt-20">
              <User className="w-16 h-16 mx-auto mb-4 text-gray-300" />
              <p>Select a personality to view details</p>
            </div>
          )}
        </div>
      </div>

      {/* New Personality Modal */}
      {showNewPersonalityModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-8 max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-2xl font-bold text-gray-900">Create New Personality</h3>
              <button
                onClick={() => {
                  setShowNewPersonalityModal(false);
                  resetNewPersonalityForm();
                }}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="w-6 h-6" />
              </button>
            </div>

            <div className="space-y-6">
              {/* Basic Information */}
              <div>
                <h4 className="text-lg font-semibold text-gray-900 mb-4">Basic Information</h4>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
                    <input
                      type="text"
                      value={newPersonalityForm.name}
                      onChange={(e) => setNewPersonalityForm({ ...newPersonalityForm, name: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                      placeholder="e.g., Alex"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Age</label>
                    <input
                      type="text"
                      value={newPersonalityForm.age}
                      onChange={(e) => setNewPersonalityForm({ ...newPersonalityForm, age: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                      placeholder="e.g., 28"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Gender</label>
                    <select
                      value={newPersonalityForm.gender}
                      onChange={(e) => setNewPersonalityForm({ ...newPersonalityForm, gender: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    >
                      <option value="Male">Male</option>
                      <option value="Female">Female</option>
                      <option value="Non-binary">Non-binary</option>
                    </select>
                  </div>
                </div>

                {/* Avatar Selection */}
                <div className="mt-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">Avatar</label>
                  
                  {/* Avatar Type Selector */}
                  <div className="flex gap-2 mb-3">
                    <button
                      type="button"
                      onClick={() => setAvatarType('emoji')}
                      className={`px-4 py-2 rounded-lg border-2 transition-all ${
                        avatarType === 'emoji'
                          ? 'border-weed-green-500 bg-weed-green-50 text-weed-green-700'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      Select Emoji
                    </button>
                    <button
                      type="button"
                      onClick={() => setAvatarType('upload')}
                      className={`px-4 py-2 rounded-lg border-2 transition-all ${
                        avatarType === 'upload'
                          ? 'border-weed-green-500 bg-weed-green-50 text-weed-green-700'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      Upload Image
                    </button>
                  </div>

                  {/* Emoji Selection */}
                  {avatarType === 'emoji' ? (
                    <div className="grid grid-cols-8 gap-2 max-h-64 overflow-y-auto p-2 border border-gray-200 rounded-lg">
                      {[
                        // Light skin tone
                        '👨🏻', '👩🏻', '🧑🏻', '👴🏻', '👵🏻', '👨🏻‍🌾', '👩🏻‍⚕️', '🧑🏻‍🎤',
                        // Medium-light skin tone  
                        '👨🏼', '👩🏼', '🧑🏼', '👴🏼', '👵🏼', '👨🏼‍💼', '👩🏼‍🔬', '🧑🏼‍💻',
                        // Medium skin tone
                        '👨🏽', '👩🏽', '🧑🏽', '👴🏽', '👵🏽', '👨🏽‍🏫', '👩🏽‍🎓', '🧑🏽‍🍳',
                        // Medium-dark skin tone
                        '👨🏾', '👩🏾', '🧑🏾', '👴🏾', '👵🏾', '👨🏾‍🎨', '👩🏾‍💼', '🧑🏾‍🔧',
                        // Dark skin tone
                        '👨🏿', '👩🏿', '🧑🏿', '👴🏿', '👵🏿', '👨🏿‍🌾', '👩🏿‍⚕️', '🧑🏿‍🎤',
                        // Additional diverse options
                        '🧔🏻', '🧔🏼', '🧔🏽', '🧔🏾', '🧔🏿', '👳🏻‍♂️', '👳🏽‍♀️', '👳🏿‍♂️',
                        '🧕🏻', '🧕🏼', '🧕🏽', '🧕🏾', '🧕🏿', '👮🏻', '👮🏽', '👮🏿'
                      ].map((emoji) => (
                        <button
                          key={emoji}
                          type="button"
                          onClick={() => {
                            setNewPersonalityForm({ ...newPersonalityForm, emoji, avatar: undefined });
                            setUploadedAvatar(null);
                          }}
                          className={`w-12 h-12 rounded-lg border-2 flex items-center justify-center text-2xl transition-all ${
                            newPersonalityForm.emoji === emoji 
                              ? 'border-weed-green-500 bg-weed-green-50' 
                              : 'border-gray-200 hover:border-gray-300'
                          }`}
                        >
                          {emoji}
                        </button>
                      ))}
                    </div>
                  ) : (
                    /* Upload Image */
                    <div className="space-y-3">
                      <input
                        ref={fileInputRef}
                        type="file"
                        accept="image/*"
                        onChange={handleAvatarUpload}
                        className="hidden"
                      />
                      
                      <div className="flex items-center gap-4">
                        {uploadedAvatar || newPersonalityForm.avatar ? (
                          <div className="relative">
                            <img 
                              src={uploadedAvatar || newPersonalityForm.avatar} 
                              alt="Avatar preview" 
                              className="w-20 h-20 rounded-full object-cover border-2 border-gray-200"
                            />
                            <button
                              type="button"
                              onClick={() => {
                                setUploadedAvatar(null);
                                setNewPersonalityForm({ ...newPersonalityForm, avatar: undefined });
                              }}
                              className="absolute -top-1 -right-1 bg-red-500 text-white rounded-full p-1"
                            >
                              <X className="w-3 h-3" />
                            </button>
                          </div>
                        ) : (
                          <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center">
                            <Image className="w-8 h-8 text-gray-400" />
                          </div>
                        )}
                        
                        <button
                          type="button"
                          onClick={() => fileInputRef.current?.click()}
                          className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 flex items-center gap-2"
                        >
                          <Upload className="w-4 h-4" />
                          {uploadedAvatar || newPersonalityForm.avatar ? 'Change' : 'Upload'} Avatar
                        </button>
                      </div>
                      
                      <p className="text-xs text-gray-500">
                        Recommended: Square image, max 5MB (JPG, PNG, GIF)
                      </p>
                    </div>
                  )}
                </div>

                <div className="mt-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Description *</label>
                  <textarea
                    value={newPersonalityForm.description}
                    onChange={(e) => setNewPersonalityForm({ ...newPersonalityForm, description: e.target.value })}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    placeholder="Describe the personality and approach of this budtender..."
                  />
                </div>

                <div className="mt-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Communication Style</label>
                  <input
                    type="text"
                    value={newPersonalityForm.communication_style}
                    onChange={(e) => setNewPersonalityForm({ ...newPersonalityForm, communication_style: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    placeholder="e.g., Professional yet approachable, with attention to detail"
                  />
                </div>
              </div>

              {/* Communication Settings */}
              <div>
                <h4 className="text-lg font-semibold text-gray-900 mb-4">Communication Settings</h4>
                <div className="grid grid-cols-4 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Knowledge Level</label>
                    <select
                      value={newPersonalityForm.knowledge_level}
                      onChange={(e) => setNewPersonalityForm({ ...newPersonalityForm, knowledge_level: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    >
                      <option value="Beginner">Beginner</option>
                      <option value="Intermediate">Intermediate</option>
                      <option value="Expert">Expert</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Humor Level</label>
                    <select
                      value={newPersonalityForm.humor_level}
                      onChange={(e) => setNewPersonalityForm({ ...newPersonalityForm, humor_level: e.target.value as any })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    >
                      <option value="none">None</option>
                      <option value="light">Light</option>
                      <option value="moderate">Moderate</option>
                      <option value="high">High</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Formality</label>
                    <select
                      value={newPersonalityForm.formality}
                      onChange={(e) => setNewPersonalityForm({ ...newPersonalityForm, formality: e.target.value as any })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    >
                      <option value="very_casual">Very Casual</option>
                      <option value="casual">Casual</option>
                      <option value="balanced">Balanced</option>
                      <option value="formal">Formal</option>
                      <option value="very_formal">Very Formal</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Empathy Level</label>
                    <select
                      value={newPersonalityForm.empathy_level}
                      onChange={(e) => setNewPersonalityForm({ ...newPersonalityForm, empathy_level: e.target.value as any })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    >
                      <option value="low">Low</option>
                      <option value="medium">Medium</option>
                      <option value="high">High</option>
                    </select>
                  </div>
                </div>
              </div>

              {/* Personality Traits */}
              <div>
                <h4 className="text-lg font-semibold text-gray-900 mb-4">Personality Traits</h4>
                <div className="flex items-center space-x-2 mb-3">
                  <input
                    type="text"
                    value={newTrait}
                    onChange={(e) => setNewTrait(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && addTraitToNewPersonality()}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-lg"
                    placeholder="Add a trait (e.g., Patient, Knowledgeable)"
                  />
                  <button
                    onClick={addTraitToNewPersonality}
                    className="px-4 py-2 bg-weed-green-500 text-white rounded-lg hover:bg-weed-green-600"
                  >
                    Add
                  </button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {newPersonalityForm.traits?.map((trait, index) => (
                    <span
                      key={index}
                      className="px-3 py-1 bg-purple-haze-100 text-purple-haze-700 rounded-full text-sm flex items-center space-x-1"
                    >
                      <span>{trait}</span>
                      <button
                        onClick={() => removeTraitFromNewPersonality(index)}
                        className="text-purple-haze-500 hover:text-purple-haze-700"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </span>
                  ))}
                </div>
              </div>

              {/* Sample Responses */}
              <div>
                <h4 className="text-lg font-semibold text-gray-900 mb-4">Sample Responses</h4>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Greeting</label>
                    <textarea
                      value={newPersonalityForm.sample_responses?.greeting}
                      onChange={(e) => setNewPersonalityForm({
                        ...newPersonalityForm,
                        sample_responses: {
                          ...newPersonalityForm.sample_responses!,
                          greeting: e.target.value
                        }
                      })}
                      rows={2}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                      placeholder="How this budtender greets customers..."
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Product Recommendation</label>
                    <textarea
                      value={newPersonalityForm.sample_responses?.product_recommendation}
                      onChange={(e) => setNewPersonalityForm({
                        ...newPersonalityForm,
                        sample_responses: {
                          ...newPersonalityForm.sample_responses!,
                          product_recommendation: e.target.value
                        }
                      })}
                      rows={2}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                      placeholder="How they recommend products..."
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Out of Stock Response</label>
                    <textarea
                      value={newPersonalityForm.sample_responses?.no_stock}
                      onChange={(e) => setNewPersonalityForm({
                        ...newPersonalityForm,
                        sample_responses: {
                          ...newPersonalityForm.sample_responses!,
                          no_stock: e.target.value
                        }
                      })}
                      rows={2}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                      placeholder="How they handle out of stock situations..."
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Closing Message</label>
                    <textarea
                      value={newPersonalityForm.sample_responses?.closing}
                      onChange={(e) => setNewPersonalityForm({
                        ...newPersonalityForm,
                        sample_responses: {
                          ...newPersonalityForm.sample_responses!,
                          closing: e.target.value
                        }
                      })}
                      rows={2}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                      placeholder="How they close conversations..."
                    />
                  </div>
                </div>
              </div>

              {/* Actions */}
              <div className="flex justify-end space-x-3 pt-4 border-t">
                <button
                  onClick={() => {
                    setShowNewPersonalityModal(false);
                    resetNewPersonalityForm();
                  }}
                  className="px-6 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
                >
                  Cancel
                </button>
                <button
                  onClick={createPersonality}
                  className="px-6 py-2 bg-weed-green-500 text-white rounded-lg hover:bg-weed-green-600"
                >
                  Create Personality
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}