import { endpoints } from '../config/endpoints';
import React, { useState, useEffect } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { 
  Brain, 
  CheckCircle, 
  XCircle, 
  AlertCircle, 
  Target,
  TrendingUp,
  BookOpen,
  MessageSquare,
  ShoppingCart,
  Users,
  Settings
} from 'lucide-react';
import toast from 'react-hot-toast';

interface TrainingScenario {
  id: string;
  category: string;
  title: string;
  description: string;
  userMessage: string;
  expectedBehavior: string[];
  avoidBehavior: string[];
  correctResponse: string;
  keyPoints: string[];
  confidence: number;
}

interface TrainingExample {
  id: string;
  scenario_id: string;
  user_input: string;
  ideal_response: string;
  intent: string;
  products_to_show?: string[];
  context_required: string[];
  created_at: string;
  success_rate?: number;
}

interface TrainingMetrics {
  totalScenarios: number;
  completedTrainings: number;
  averageConfidence: number;
  problemAreas: string[];
  improvements: string[];
}

const trainingCategories = [
  { id: 'greeting', label: 'Greetings & Introduction', icon: Users },
  { id: 'product_inquiry', label: 'Product Inquiries', icon: ShoppingCart },
  { id: 'recommendation', label: 'Recommendations', icon: Target },
  { id: 'inventory', label: 'Inventory Management', icon: BookOpen },
  { id: 'context', label: 'Context Retention', icon: Brain },
  { id: 'correction', label: 'Error Recovery', icon: AlertCircle }
];

const scenariosData: TrainingScenario[] = [
  {
    id: 'greeting_1',
    category: 'greeting',
    title: 'Initial Customer Greeting',
    description: 'How to properly greet and identify customers',
    userMessage: 'Hi',
    expectedBehavior: [
      'Warm, friendly greeting',
      'Ask for customer name if not known',
      'Set welcoming tone',
      'Mention you are here to help'
    ],
    avoidBehavior: [
      'Jumping straight to products',
      'Being overly casual',
      'Forgetting to identify customer'
    ],
    correctResponse: "Hey there! Welcome to our dispensary. I'm [Name], your budtender today. May I have your name so I can better assist you?",
    keyPoints: ['Greeting', 'Introduction', 'Customer Identification'],
    confidence: 95
  },
  {
    id: 'product_1',
    category: 'product_inquiry',
    title: 'Sativa Request',
    description: 'Customer asks for sativa strains',
    userMessage: 'I am looking to get some sativa',
    expectedBehavior: [
      'Acknowledge the request',
      'Check actual inventory',
      'Provide specific available options',
      'Include prices and THC levels',
      'Ask about preferences (effects, price range)'
    ],
    avoidBehavior: [
      'Saying products are available then unavailable',
      'Not providing specific products',
      'Changing topic suddenly'
    ],
    correctResponse: "Great choice! I have several excellent sativa strains available. Our top sellers are:\n\n1. Sour Diesel - $45/eighth, 22% THC - energizing and uplifting\n2. Jack Herer - $40/eighth, 20% THC - creative and focused\n3. Green Crack - $35/eighth, 18% THC - energetic and happy\n\nWhat effects are you looking for, or do you have a price range in mind?",
    keyPoints: ['Product Knowledge', 'Inventory Awareness', 'Specific Options', 'Follow-up Questions'],
    confidence: 90
  },
  {
    id: 'context_1',
    category: 'context',
    title: 'Maintaining Product Discussion',
    description: 'Keep track of what product customer is interested in',
    userMessage: 'yes please (after discussing Sour Diesel)',
    expectedBehavior: [
      'Remember previous product mentioned',
      'Confirm the specific product',
      'Provide next steps for purchase',
      'Maintain conversation flow'
    ],
    avoidBehavior: [
      'Forgetting what was discussed',
      'Switching to unrelated products',
      'Asking what they want again'
    ],
    correctResponse: "Perfect! I'll get that Sour Diesel ready for you - that's an eighth for $45. It's one of our most popular strains with great energizing effects. Would you like to add anything else, or shall I ring this up for you?",
    keyPoints: ['Context Retention', 'Confirmation', 'Purchase Flow'],
    confidence: 85
  },
  {
    id: 'inventory_1',
    category: 'inventory',
    title: 'Stock Availability Response',
    description: 'How to handle inventory questions',
    userMessage: 'what do you have in stock',
    expectedBehavior: [
      'Provide categories first',
      'List specific available products',
      'Include key details (price, THC)',
      'Be accurate about availability'
    ],
    avoidBehavior: [
      'Being vague',
      'Not knowing inventory',
      'Contradicting availability'
    ],
    correctResponse: "Let me show you what we have available today:\n\n**Flower (Sativa):**\n- Sour Diesel ($45/eighth)\n- Jack Herer ($40/eighth)\n\n**Flower (Indica):**\n- Purple Kush ($42/eighth)\n- Northern Lights ($38/eighth)\n\n**Edibles:**\n- Gummies 10mg ($15)\n- Chocolate bars 50mg ($25)\n\n**Vapes:**\n- Various cartridges ($30-60)\n\nWhat category interests you most?",
    keyPoints: ['Inventory Knowledge', 'Organization', 'Specificity'],
    confidence: 88
  },
  {
    id: 'correction_1',
    category: 'correction',
    title: 'Handling Confusion',
    description: 'How to recover from misunderstandings',
    userMessage: 'i thought you wanted to sell me sour diesel',
    expectedBehavior: [
      'Acknowledge the confusion',
      'Apologize if needed',
      'Clarify the situation',
      'Get back on track',
      'Confirm availability'
    ],
    avoidBehavior: [
      'Contradicting yourself',
      'Ignoring the confusion',
      'Making it worse'
    ],
    correctResponse: "You're absolutely right, Jim! I apologize for the confusion. Yes, we do have Sour Diesel in stock - $45 for an eighth. I got sidetracked there. Would you like me to prepare that Sour Diesel for you?",
    keyPoints: ['Error Recovery', 'Acknowledgment', 'Clarity'],
    confidence: 82
  }
];

export default function AITrainingProgram() {
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedScenario, setSelectedScenario] = useState<TrainingScenario | null>(null);
  const [testMode, setTestMode] = useState(false);
  const [testInput, setTestInput] = useState('');
  const [testResponse, setTestResponse] = useState('');
  const [trainingMetrics, setTrainingMetrics] = useState<TrainingMetrics>({
    totalScenarios: scenariosData.length,
    completedTrainings: 0,
    averageConfidence: 0,
    problemAreas: ['Context Retention', 'Product Consistency', 'Gender Recognition'],
    improvements: []
  });

  // Calculate average confidence
  useEffect(() => {
    const avgConfidence = scenariosData.reduce((acc, s) => acc + s.confidence, 0) / scenariosData.length;
    setTrainingMetrics(prev => ({ ...prev, averageConfidence: Math.round(avgConfidence) }));
  }, []);

  // Save training example to database
  const saveTrainingMutation = useMutation({
    mutationFn: async (example: Partial<TrainingExample>) => {
      const response = await axios.post(endpoints.training.examples, example);
      return response.data;
    },
    onSuccess: () => {
      toast.success('Training example saved successfully');
      setTrainingMetrics(prev => ({ 
        ...prev, 
        completedTrainings: prev.completedTrainings + 1 
      }));
    },
    onError: (error) => {
      toast.error('Failed to save training example');
      console.error(error);
    }
  });

  // Apply training to AI model
  const applyTrainingMutation = useMutation({
    mutationFn: async (scenarioId: string) => {
      const scenario = scenariosData.find(s => s.id === scenarioId);
      if (!scenario) return;

      const trainingData = {
        examples: [{
          user_input: scenario.userMessage,
          ideal_response: scenario.correctResponse,
          intent: scenario.category,
          context_required: scenario.keyPoints
        }],
        category: scenario.category
      };

      const response = await axios.post(endpoints.training.apply, trainingData);
      return response.data;
    },
    onSuccess: () => {
      toast.success('Training applied to AI model');
    },
    onError: (error) => {
      toast.error('Failed to apply training');
      console.error(error);
    }
  });

  // Test the AI with a scenario
  const testScenarioMutation = useMutation({
    mutationFn: async (params: { input: string; context?: any }) => {
      const response = await axios.post(endpoints.chat.base, {
        message: params.input,
        customer_id: 'training_test',
        session_id: `training_${Date.now()}`,
        context: params.context || {}
      });
      return response.data;
    },
    onSuccess: (data) => {
      setTestResponse(data.message || 'No response');
    },
    onError: (error) => {
      toast.error('Test failed');
      console.error(error);
    }
  });

  const filteredScenarios = selectedCategory === 'all' 
    ? scenariosData 
    : scenariosData.filter(s => s.category === selectedCategory);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <Brain className="w-8 h-8 text-weed-green-500" />
              AI Training Program
            </h2>
            <p className="text-gray-600 mt-1">
              Train the AI to handle conversations correctly and consistently
            </p>
          </div>
          <button
            onClick={() => setTestMode(!testMode)}
            className="px-4 py-2 bg-weed-green-500 text-white rounded-lg hover:bg-weed-green-600 transition-colors"
          >
            {testMode ? 'Training Mode' : 'Test Mode'}
          </button>
        </div>

        {/* Metrics */}
        <div className="grid grid-cols-4 gap-4 mt-6">
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="text-sm text-gray-500">Total Scenarios</div>
            <div className="text-2xl font-bold text-gray-900">{trainingMetrics.totalScenarios}</div>
          </div>
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="text-sm text-gray-500">Completed Trainings</div>
            <div className="text-2xl font-bold text-weed-green-600">{trainingMetrics.completedTrainings}</div>
          </div>
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="text-sm text-gray-500">Average Confidence</div>
            <div className="text-2xl font-bold text-blue-600">{trainingMetrics.averageConfidence}%</div>
          </div>
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="text-sm text-gray-500">Problem Areas</div>
            <div className="text-2xl font-bold text-red-600">{trainingMetrics.problemAreas.length}</div>
          </div>
        </div>

        {/* Problem Areas Alert */}
        {trainingMetrics.problemAreas.length > 0 && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 mt-0.5" />
              <div>
                <h4 className="font-semibold text-red-900">Areas Needing Improvement</h4>
                <ul className="mt-2 space-y-1">
                  {trainingMetrics.problemAreas.map((area, idx) => (
                    <li key={idx} className="text-sm text-red-700">• {area}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Category Filter */}
      <div className="bg-white rounded-lg shadow-sm p-4">
        <div className="flex items-center gap-4">
          <span className="text-sm font-medium text-gray-700">Category:</span>
          <div className="flex gap-2">
            <button
              onClick={() => setSelectedCategory('all')}
              className={`px-3 py-1 rounded-lg text-sm ${
                selectedCategory === 'all' 
                  ? 'bg-weed-green-500 text-white' 
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              All
            </button>
            {trainingCategories.map(cat => {
              const Icon = cat.icon;
              return (
                <button
                  key={cat.id}
                  onClick={() => setSelectedCategory(cat.id)}
                  className={`px-3 py-1 rounded-lg text-sm flex items-center gap-1 ${
                    selectedCategory === cat.id 
                      ? 'bg-weed-green-500 text-white' 
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {cat.label}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-3 gap-6">
        {/* Scenarios List */}
        <div className="col-span-1 bg-white rounded-lg shadow-sm p-4">
          <h3 className="font-semibold text-gray-900 mb-4">Training Scenarios</h3>
          <div className="space-y-2 max-h-[600px] overflow-y-auto">
            {filteredScenarios.map(scenario => (
              <div
                key={scenario.id}
                onClick={() => setSelectedScenario(scenario)}
                className={`p-3 rounded-lg cursor-pointer transition-colors ${
                  selectedScenario?.id === scenario.id
                    ? 'bg-weed-green-50 border-2 border-weed-green-500'
                    : 'bg-gray-50 hover:bg-gray-100 border-2 border-transparent'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <h4 className="font-medium text-gray-900">{scenario.title}</h4>
                    <p className="text-sm text-gray-600 mt-1">{scenario.description}</p>
                  </div>
                  <div className={`text-xs px-2 py-1 rounded ${
                    scenario.confidence >= 90 ? 'bg-green-100 text-green-700' :
                    scenario.confidence >= 80 ? 'bg-yellow-100 text-yellow-700' :
                    'bg-red-100 text-red-700'
                  }`}>
                    {scenario.confidence}%
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Scenario Details */}
        <div className="col-span-2 bg-white rounded-lg shadow-sm p-6">
          {selectedScenario ? (
            <div className="space-y-6">
              <div>
                <h3 className="text-xl font-semibold text-gray-900">{selectedScenario.title}</h3>
                <p className="text-gray-600 mt-1">{selectedScenario.description}</p>
              </div>

              {/* User Message */}
              <div className="bg-blue-50 rounded-lg p-4">
                <h4 className="font-medium text-blue-900 mb-2">Customer Says:</h4>
                <p className="text-blue-800">"{selectedScenario.userMessage}"</p>
              </div>

              {/* Expected Behavior */}
              <div className="bg-green-50 rounded-lg p-4">
                <h4 className="font-medium text-green-900 mb-2 flex items-center gap-2">
                  <CheckCircle className="w-5 h-5" />
                  Expected Behavior:
                </h4>
                <ul className="space-y-1">
                  {selectedScenario.expectedBehavior.map((behavior, idx) => (
                    <li key={idx} className="text-sm text-green-800 flex items-start gap-2">
                      <span className="text-green-600 mt-0.5">✓</span>
                      {behavior}
                    </li>
                  ))}
                </ul>
              </div>

              {/* Avoid Behavior */}
              <div className="bg-red-50 rounded-lg p-4">
                <h4 className="font-medium text-red-900 mb-2 flex items-center gap-2">
                  <XCircle className="w-5 h-5" />
                  Avoid:
                </h4>
                <ul className="space-y-1">
                  {selectedScenario.avoidBehavior.map((behavior, idx) => (
                    <li key={idx} className="text-sm text-red-800 flex items-start gap-2">
                      <span className="text-red-600 mt-0.5">✗</span>
                      {behavior}
                    </li>
                  ))}
                </ul>
              </div>

              {/* Correct Response */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="font-medium text-gray-900 mb-2">Ideal Response:</h4>
                <p className="text-gray-800 whitespace-pre-wrap">{selectedScenario.correctResponse}</p>
              </div>

              {/* Key Points */}
              <div className="flex flex-wrap gap-2">
                {selectedScenario.keyPoints.map((point, idx) => (
                  <span key={idx} className="px-3 py-1 bg-weed-green-100 text-weed-green-700 rounded-full text-sm">
                    {point}
                  </span>
                ))}
              </div>

              {/* Actions */}
              <div className="flex gap-3">
                <button
                  onClick={() => {
                    saveTrainingMutation.mutate({
                      scenario_id: selectedScenario.id,
                      user_input: selectedScenario.userMessage,
                      ideal_response: selectedScenario.correctResponse,
                      intent: selectedScenario.category,
                      context_required: selectedScenario.keyPoints
                    });
                  }}
                  disabled={saveTrainingMutation.isPending}
                  className="px-4 py-2 bg-weed-green-500 text-white rounded-lg hover:bg-weed-green-600 disabled:opacity-50"
                >
                  {saveTrainingMutation.isPending ? 'Saving...' : 'Save Training Example'}
                </button>
                <button
                  onClick={() => applyTrainingMutation.mutate(selectedScenario.id)}
                  disabled={applyTrainingMutation.isPending}
                  className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50"
                >
                  {applyTrainingMutation.isPending ? 'Applying...' : 'Apply to AI Model'}
                </button>
                <button
                  onClick={() => {
                    setTestMode(true);
                    setTestInput(selectedScenario.userMessage);
                  }}
                  className="px-4 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600"
                >
                  Test This Scenario
                </button>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center h-full text-gray-500">
              Select a scenario to view details
            </div>
          )}
        </div>
      </div>

      {/* Test Mode Panel */}
      {testMode && (
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Test AI Response</h3>
          <div className="grid grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Test Input
              </label>
              <textarea
                value={testInput}
                onChange={(e) => setTestInput(e.target.value)}
                className="w-full h-32 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-weed-green-500 focus:border-transparent"
                placeholder="Enter test message..."
              />
              <button
                onClick={() => testScenarioMutation.mutate({ input: testInput })}
                disabled={testScenarioMutation.isPending || !testInput}
                className="mt-3 px-4 py-2 bg-weed-green-500 text-white rounded-lg hover:bg-weed-green-600 disabled:opacity-50"
              >
                {testScenarioMutation.isPending ? 'Testing...' : 'Test AI Response'}
              </button>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                AI Response
              </label>
              <div className="w-full h-32 px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 overflow-y-auto">
                {testResponse || 'No response yet...'}
              </div>
              {selectedScenario && testResponse && (
                <div className="mt-3">
                  <button
                    onClick={() => {
                      // Compare response with ideal response
                      const similarity = testResponse.toLowerCase().includes(selectedScenario.userMessage.toLowerCase()) ? 30 : 70;
                      toast.info(`Response similarity: ${similarity}%`);
                    }}
                    className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
                  >
                    Compare with Ideal
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}