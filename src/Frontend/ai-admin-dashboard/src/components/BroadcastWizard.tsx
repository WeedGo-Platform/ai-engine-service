import React, { useState, useEffect } from 'react';
import {
  X, ChevronRight, ChevronLeft, Send, Mail, Smartphone,
  Bell, Users, Calendar, DollarSign, AlertCircle, Check,
  Zap
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useStoreContext } from '../contexts/StoreContext';
import toast from 'react-hot-toast';

interface BroadcastWizardProps {
  isOpen: boolean;
  onClose: () => void;
  onComplete: (broadcastId: string) => void;
}

interface Segment {
  id: string;
  name: string;
  description: string;
  count: number;
  criteria: Record<string, any>;
}

interface Template {
  id: string;
  name: string;
  subject?: string;
  content: string;
  type: 'email' | 'sms' | 'push';
}

type WizardStep = 'details' | 'audience' | 'message' | 'schedule' | 'review';

const BroadcastWizard: React.FC<BroadcastWizardProps> = ({ isOpen, onClose, onComplete }) => {
  const { } = useAuth();
  const { currentStore } = useStoreContext();
  const [currentStep, setCurrentStep] = useState<WizardStep>('details');
  const [loading, setLoading] = useState(false);
  const [segments, setSegments] = useState<Segment[]>([]);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [estimatedCost, setEstimatedCost] = useState(0);

  // Form data
  const [broadcastData, setBroadcastData] = useState({
    name: '',
    description: '',
    channels: [] as string[],
    segmentId: '',
    customCriteria: {},
    messages: {
      email: { subject: '', content: '', templateId: '' },
      sms: { content: '', templateId: '' },
      push: { title: '', content: '', templateId: '' }
    },
    scheduled: false,
    scheduledAt: '',
    testMode: false,
    metadata: {}
  });

  const steps: WizardStep[] = ['details', 'audience', 'message', 'schedule', 'review'];
  const stepTitles = {
    details: 'Campaign Details',
    audience: 'Select Audience',
    message: 'Compose Message',
    schedule: 'Schedule Delivery',
    review: 'Review & Send'
  };

  useEffect(() => {
    if (isOpen) {
      fetchSegments();
      fetchTemplates();
    }
  }, [isOpen]);

  useEffect(() => {
    if (broadcastData.segmentId && broadcastData.channels.length > 0) {
      calculateCost();
    }
  }, [broadcastData.segmentId, broadcastData.channels]);

  const fetchSegments = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/communications/segments`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'X-Store-ID': currentStore?.id || ''
        }
      });
      if (response.ok) {
        const data = await response.json();
        setSegments(data.segments);
      }
    } catch (error) {
      console.error('Failed to fetch segments:', error);
    }
  };

  const fetchTemplates = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/communications/templates`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'X-Store-ID': currentStore?.id || ''
        }
      });
      if (response.ok) {
        const data = await response.json();
        setTemplates(data.templates);
      }
    } catch (error) {
      console.error('Failed to fetch templates:', error);
    }
  };

  const calculateCost = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/communications/broadcasts/estimate-cost`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
          'X-Store-ID': currentStore?.id || ''
        },
        body: JSON.stringify({
          segment_id: broadcastData.segmentId,
          channels: broadcastData.channels
        })
      });
      if (response.ok) {
        const data = await response.json();
        setEstimatedCost(data.estimated_cost);
      }
    } catch (error) {
      console.error('Failed to calculate cost:', error);
    }
  };

  const handleChannelToggle = (channel: string) => {
    setBroadcastData(prev => ({
      ...prev,
      channels: prev.channels.includes(channel)
        ? prev.channels.filter(c => c !== channel)
        : [...prev.channels, channel]
    }));
  };

  const handleTemplateSelect = (channel: 'email' | 'sms' | 'push', templateId: string) => {
    const template = templates.find(t => t.id === templateId && t.type === channel);
    if (template) {
      setBroadcastData(prev => ({
        ...prev,
        messages: {
          ...prev.messages,
          [channel]: {
            ...prev.messages[channel],
            templateId,
            content: template.content,
            ...(channel === 'email' && { subject: template.subject }),
            ...(channel === 'push' && { title: template.subject })
          }
        }
      }));
    }
  };

  const handleNext = () => {
    const stepIndex = steps.indexOf(currentStep);
    if (stepIndex < steps.length - 1) {
      setCurrentStep(steps[stepIndex + 1]);
    }
  };

  const handlePrevious = () => {
    const stepIndex = steps.indexOf(currentStep);
    if (stepIndex > 0) {
      setCurrentStep(steps[stepIndex - 1]);
    }
  };

  const handleSubmit = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const payload = {
        name: broadcastData.name,
        description: broadcastData.description,
        store_id: currentStore?.id,
        channels: broadcastData.channels,
        segment_id: broadcastData.segmentId,
        custom_criteria: broadcastData.customCriteria,
        messages: Object.fromEntries(
          broadcastData.channels.map(channel => [
            channel,
            broadcastData.messages[channel as keyof typeof broadcastData.messages]
          ])
        ),
        scheduled: broadcastData.scheduled,
        scheduled_at: broadcastData.scheduledAt || null,
        test_mode: broadcastData.testMode,
        metadata: broadcastData.metadata
      };

      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/communications/broadcasts`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
          'X-Store-ID': currentStore?.id || ''
        },
        body: JSON.stringify(payload)
      });

      if (response.ok) {
        const data = await response.json();
        toast.success('Broadcast created successfully!');
        onComplete(data.broadcast.id);
        onClose();
        resetForm();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to create broadcast');
      }
    } catch (error) {
      toast.error('Failed to create broadcast');
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setBroadcastData({
      name: '',
      description: '',
      channels: [],
      segmentId: '',
      customCriteria: {},
      messages: {
        email: { subject: '', content: '', templateId: '' },
        sms: { content: '', templateId: '' },
        push: { title: '', content: '', templateId: '' }
      },
      scheduled: false,
      scheduledAt: '',
      testMode: false,
      metadata: {}
    });
    setCurrentStep('details');
  };

  const isStepValid = () => {
    switch (currentStep) {
      case 'details':
        return broadcastData.name && broadcastData.channels.length > 0;
      case 'audience':
        return broadcastData.segmentId;
      case 'message':
        return broadcastData.channels.every(channel => {
          const msg = broadcastData.messages[channel as keyof typeof broadcastData.messages];
          return msg && msg.content;
        });
      case 'schedule':
        return !broadcastData.scheduled || broadcastData.scheduledAt;
      default:
        return true;
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-primary-600 to-primary-700 px-6 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Send className="h-6 w-6 text-white" />
            <h2 className="text-xl font-semibold text-white">Create Broadcast Campaign</h2>
          </div>
          <button onClick={onClose} className="text-white hover:text-gray-200">
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Progress Steps */}
        <div className="bg-gray-50 px-6 py-3 border-b">
          <div className="flex items-center justify-between">
            {steps.map((step, index) => (
              <div key={step} className="flex items-center">
                <div className={`flex items-center ${index > 0 ? 'flex-1' : ''}`}>
                  {index > 0 && (
                    <div className={`h-0.5 w-full mr-2 ${
                      steps.indexOf(currentStep) > index ? 'bg-primary-600' : 'bg-gray-300'
                    }`} />
                  )}
                  <div className={`flex items-center justify-center w-8 h-8 rounded-full ${
                    currentStep === step ? 'bg-primary-600 text-white' :
                    steps.indexOf(currentStep) > index ? 'bg-primary-100 text-primary-600' :
                    'bg-gray-200 text-gray-500'
                  }`}>
                    {steps.indexOf(currentStep) > index ? (
                      <Check className="h-4 w-4" />
                    ) : (
                      <span className="text-sm font-medium">{index + 1}</span>
                    )}
                  </div>
                  <span className={`ml-2 text-sm font-medium ${
                    currentStep === step ? 'text-primary-600' : 'text-gray-500'
                  }`}>
                    {stepTitles[step]}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto" style={{ maxHeight: 'calc(90vh - 200px)' }}>
          {/* Step 1: Details */}
          {currentStep === 'details' && (
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Campaign Name
                </label>
                <input
                  type="text"
                  value={broadcastData.name}
                  onChange={(e) => setBroadcastData(prev => ({ ...prev, name: e.target.value }))}
                  className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500"
                  placeholder="e.g., Weekend Sale Announcement"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Description
                </label>
                <textarea
                  value={broadcastData.description}
                  onChange={(e) => setBroadcastData(prev => ({ ...prev, description: e.target.value }))}
                  className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500"
                  rows={3}
                  placeholder="Brief description of this campaign..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Select Channels
                </label>
                <div className="grid grid-cols-3 gap-4">
                  <button
                    onClick={() => handleChannelToggle('email')}
                    className={`p-4 rounded-lg border-2 transition-all ${
                      broadcastData.channels.includes('email')
                        ? 'border-primary-500 bg-primary-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <Mail className={`h-8 w-8 mx-auto mb-2 ${
                      broadcastData.channels.includes('email') ? 'text-primary-600' : 'text-gray-400'
                    }`} />
                    <span className={`text-sm font-medium ${
                      broadcastData.channels.includes('email') ? 'text-primary-600' : 'text-gray-600'
                    }`}>Email</span>
                  </button>

                  <button
                    onClick={() => handleChannelToggle('sms')}
                    className={`p-4 rounded-lg border-2 transition-all ${
                      broadcastData.channels.includes('sms')
                        ? 'border-primary-500 bg-primary-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <Smartphone className={`h-8 w-8 mx-auto mb-2 ${
                      broadcastData.channels.includes('sms') ? 'text-primary-600' : 'text-gray-400'
                    }`} />
                    <span className={`text-sm font-medium ${
                      broadcastData.channels.includes('sms') ? 'text-primary-600' : 'text-gray-600'
                    }`}>SMS</span>
                  </button>

                  <button
                    onClick={() => handleChannelToggle('push')}
                    className={`p-4 rounded-lg border-2 transition-all ${
                      broadcastData.channels.includes('push')
                        ? 'border-primary-500 bg-primary-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <Bell className={`h-8 w-8 mx-auto mb-2 ${
                      broadcastData.channels.includes('push') ? 'text-primary-600' : 'text-gray-400'
                    }`} />
                    <span className={`text-sm font-medium ${
                      broadcastData.channels.includes('push') ? 'text-primary-600' : 'text-gray-600'
                    }`}>Push</span>
                  </button>
                </div>
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="testMode"
                  checked={broadcastData.testMode}
                  onChange={(e) => setBroadcastData(prev => ({ ...prev, testMode: e.target.checked }))}
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                />
                <label htmlFor="testMode" className="ml-2 text-sm text-gray-700">
                  Test Mode (Send to test group only)
                </label>
              </div>
            </div>
          )}

          {/* Step 2: Audience */}
          {currentStep === 'audience' && (
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Select Target Segment
                </label>
                <div className="space-y-3">
                  {segments.map(segment => (
                    <div
                      key={segment.id}
                      onClick={() => setBroadcastData(prev => ({ ...prev, segmentId: segment.id }))}
                      className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                        broadcastData.segmentId === segment.id
                          ? 'border-primary-500 bg-primary-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h4 className="font-medium text-gray-900">{segment.name}</h4>
                          <p className="text-sm text-gray-600 mt-1">{segment.description}</p>
                          <div className="flex items-center mt-2 text-sm text-gray-500">
                            <Users className="h-4 w-4 mr-1" />
                            <span>{segment.count.toLocaleString()} recipients</span>
                          </div>
                        </div>
                        {broadcastData.segmentId === segment.id && (
                          <div className="ml-4">
                            <div className="w-6 h-6 bg-primary-600 rounded-full flex items-center justify-center">
                              <Check className="h-4 w-4 text-white" />
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {broadcastData.segmentId && estimatedCost > 0 && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                  <div className="flex items-start">
                    <DollarSign className="h-5 w-5 text-yellow-600 mt-0.5" />
                    <div className="ml-3">
                      <h4 className="text-sm font-medium text-yellow-900">Estimated Cost</h4>
                      <p className="text-sm text-yellow-700 mt-1">
                        This broadcast will cost approximately ${estimatedCost.toFixed(2)}
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Step 3: Message */}
          {currentStep === 'message' && (
            <div className="space-y-6">
              {broadcastData.channels.includes('email') && (
                <div className="border rounded-lg p-4">
                  <div className="flex items-center mb-4">
                    <Mail className="h-5 w-5 text-gray-600 mr-2" />
                    <h4 className="font-medium text-gray-900">Email Message</h4>
                  </div>

                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Template
                      </label>
                      <select
                        value={broadcastData.messages.email.templateId}
                        onChange={(e) => handleTemplateSelect('email', e.target.value)}
                        className="w-full px-3 py-2 border rounded-lg"
                      >
                        <option value="">Custom Message</option>
                        {templates.filter(t => t.type === 'email').map(template => (
                          <option key={template.id} value={template.id}>{template.name}</option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Subject
                      </label>
                      <input
                        type="text"
                        value={broadcastData.messages.email.subject}
                        onChange={(e) => setBroadcastData(prev => ({
                          ...prev,
                          messages: {
                            ...prev.messages,
                            email: { ...prev.messages.email, subject: e.target.value }
                          }
                        }))}
                        className="w-full px-3 py-2 border rounded-lg"
                        placeholder="Email subject line..."
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Content
                      </label>
                      <textarea
                        value={broadcastData.messages.email.content}
                        onChange={(e) => setBroadcastData(prev => ({
                          ...prev,
                          messages: {
                            ...prev.messages,
                            email: { ...prev.messages.email, content: e.target.value }
                          }
                        }))}
                        className="w-full px-3 py-2 border rounded-lg"
                        rows={5}
                        placeholder="Email body content..."
                      />
                    </div>
                  </div>
                </div>
              )}

              {broadcastData.channels.includes('sms') && (
                <div className="border rounded-lg p-4">
                  <div className="flex items-center mb-4">
                    <Smartphone className="h-5 w-5 text-gray-600 mr-2" />
                    <h4 className="font-medium text-gray-900">SMS Message</h4>
                  </div>

                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Template
                      </label>
                      <select
                        value={broadcastData.messages.sms.templateId}
                        onChange={(e) => handleTemplateSelect('sms', e.target.value)}
                        className="w-full px-3 py-2 border rounded-lg"
                      >
                        <option value="">Custom Message</option>
                        {templates.filter(t => t.type === 'sms').map(template => (
                          <option key={template.id} value={template.id}>{template.name}</option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Message (160 characters)
                      </label>
                      <textarea
                        value={broadcastData.messages.sms.content}
                        onChange={(e) => setBroadcastData(prev => ({
                          ...prev,
                          messages: {
                            ...prev.messages,
                            sms: { ...prev.messages.sms, content: e.target.value }
                          }
                        }))}
                        className="w-full px-3 py-2 border rounded-lg"
                        rows={3}
                        maxLength={160}
                        placeholder="SMS message..."
                      />
                      <p className="text-xs text-gray-500 mt-1">
                        {broadcastData.messages.sms.content.length}/160 characters
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {broadcastData.channels.includes('push') && (
                <div className="border rounded-lg p-4">
                  <div className="flex items-center mb-4">
                    <Bell className="h-5 w-5 text-gray-600 mr-2" />
                    <h4 className="font-medium text-gray-900">Push Notification</h4>
                  </div>

                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Template
                      </label>
                      <select
                        value={broadcastData.messages.push.templateId}
                        onChange={(e) => handleTemplateSelect('push', e.target.value)}
                        className="w-full px-3 py-2 border rounded-lg"
                      >
                        <option value="">Custom Message</option>
                        {templates.filter(t => t.type === 'push').map(template => (
                          <option key={template.id} value={template.id}>{template.name}</option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Title
                      </label>
                      <input
                        type="text"
                        value={broadcastData.messages.push.title}
                        onChange={(e) => setBroadcastData(prev => ({
                          ...prev,
                          messages: {
                            ...prev.messages,
                            push: { ...prev.messages.push, title: e.target.value }
                          }
                        }))}
                        className="w-full px-3 py-2 border rounded-lg"
                        placeholder="Notification title..."
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Message
                      </label>
                      <textarea
                        value={broadcastData.messages.push.content}
                        onChange={(e) => setBroadcastData(prev => ({
                          ...prev,
                          messages: {
                            ...prev.messages,
                            push: { ...prev.messages.push, content: e.target.value }
                          }
                        }))}
                        className="w-full px-3 py-2 border rounded-lg"
                        rows={2}
                        placeholder="Push notification message..."
                      />
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Step 4: Schedule */}
          {currentStep === 'schedule' && (
            <div className="space-y-6">
              <div className="flex items-center space-x-4">
                <button
                  onClick={() => setBroadcastData(prev => ({ ...prev, scheduled: false }))}
                  className={`flex-1 p-4 rounded-lg border-2 transition-all ${
                    !broadcastData.scheduled
                      ? 'border-primary-500 bg-primary-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <Zap className={`h-6 w-6 mx-auto mb-2 ${
                    !broadcastData.scheduled ? 'text-primary-600' : 'text-gray-400'
                  }`} />
                  <span className={`text-sm font-medium ${
                    !broadcastData.scheduled ? 'text-primary-600' : 'text-gray-600'
                  }`}>Send Immediately</span>
                </button>

                <button
                  onClick={() => setBroadcastData(prev => ({ ...prev, scheduled: true }))}
                  className={`flex-1 p-4 rounded-lg border-2 transition-all ${
                    broadcastData.scheduled
                      ? 'border-primary-500 bg-primary-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <Calendar className={`h-6 w-6 mx-auto mb-2 ${
                    broadcastData.scheduled ? 'text-primary-600' : 'text-gray-400'
                  }`} />
                  <span className={`text-sm font-medium ${
                    broadcastData.scheduled ? 'text-primary-600' : 'text-gray-600'
                  }`}>Schedule for Later</span>
                </button>
              </div>

              {broadcastData.scheduled && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Schedule Date & Time
                  </label>
                  <input
                    type="datetime-local"
                    value={broadcastData.scheduledAt}
                    onChange={(e) => setBroadcastData(prev => ({ ...prev, scheduledAt: e.target.value }))}
                    className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500"
                    min={new Date().toISOString().slice(0, 16)}
                  />
                </div>
              )}

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-start">
                  <AlertCircle className="h-5 w-5 text-blue-600 mt-0.5" />
                  <div className="ml-3">
                    <h4 className="text-sm font-medium text-blue-900">Delivery Information</h4>
                    <p className="text-sm text-blue-700 mt-1">
                      {broadcastData.scheduled
                        ? `Your campaign will be sent on ${new Date(broadcastData.scheduledAt).toLocaleString()}`
                        : 'Your campaign will be sent immediately after creation'}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Step 5: Review */}
          {currentStep === 'review' && (
            <div className="space-y-6">
              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="font-medium text-gray-900 mb-4">Campaign Summary</h4>

                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Campaign Name:</span>
                    <span className="text-sm font-medium text-gray-900">{broadcastData.name}</span>
                  </div>

                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Channels:</span>
                    <span className="text-sm font-medium text-gray-900">
                      {broadcastData.channels.map(c => c.toUpperCase()).join(', ')}
                    </span>
                  </div>

                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Target Audience:</span>
                    <span className="text-sm font-medium text-gray-900">
                      {segments.find(s => s.id === broadcastData.segmentId)?.name}
                    </span>
                  </div>

                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Recipients:</span>
                    <span className="text-sm font-medium text-gray-900">
                      {segments.find(s => s.id === broadcastData.segmentId)?.count.toLocaleString()}
                    </span>
                  </div>

                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Delivery:</span>
                    <span className="text-sm font-medium text-gray-900">
                      {broadcastData.scheduled
                        ? `Scheduled for ${new Date(broadcastData.scheduledAt).toLocaleString()}`
                        : 'Immediate'}
                    </span>
                  </div>

                  {estimatedCost > 0 && (
                    <div className="flex justify-between pt-3 border-t">
                      <span className="text-sm font-medium text-gray-600">Estimated Cost:</span>
                      <span className="text-sm font-bold text-gray-900">${estimatedCost.toFixed(2)}</span>
                    </div>
                  )}
                </div>
              </div>

              {broadcastData.testMode && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                  <div className="flex items-start">
                    <AlertCircle className="h-5 w-5 text-yellow-600 mt-0.5" />
                    <div className="ml-3">
                      <h4 className="text-sm font-medium text-yellow-900">Test Mode Enabled</h4>
                      <p className="text-sm text-yellow-700 mt-1">
                        This campaign will only be sent to test recipients
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="bg-gray-50 px-6 py-4 border-t flex justify-between">
          <button
            onClick={currentStep === 'details' ? onClose : handlePrevious}
            className="px-4 py-2 text-gray-700 hover:text-gray-900 flex items-center"
            disabled={loading}
          >
            <ChevronLeft className="h-4 w-4 mr-1" />
            {currentStep === 'details' ? 'Cancel' : 'Previous'}
          </button>

          {currentStep === 'review' ? (
            <button
              onClick={handleSubmit}
              disabled={loading || !isStepValid()}
              className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                  Creating...
                </>
              ) : (
                <>
                  <Send className="h-4 w-4 mr-2" />
                  Create Campaign
                </>
              )}
            </button>
          ) : (
            <button
              onClick={handleNext}
              disabled={!isStepValid()}
              className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center"
            >
              Next
              <ChevronRight className="h-4 w-4 ml-1" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default BroadcastWizard;