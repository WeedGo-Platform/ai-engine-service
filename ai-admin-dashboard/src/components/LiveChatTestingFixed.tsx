import { endpoints } from '../config/endpoints';
import { useState, useEffect, useRef } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { motion } from 'framer-motion';
import { Loader, User, Bot, MessageSquare, Cannabis, UserCircle, History, LogOut, X } from 'lucide-react';
import toast from 'react-hot-toast';
import { useChat } from '../contexts/ChatContext';
import { type QuickAction, QuickActionGroup } from './QuickActionButton';

interface BudtenderPersonality {
  id: string;
  name: string;
  avatar: string;
  tagline: string;
  style: string;
  greeting: string;
  active?: boolean;
}

interface CustomerProfile {
  customerId: string;
  name: string;
  phone?: string;
  email?: string;
  preferences: {
    strainType?: string;
    effects?: string[];
    priceRange?: string;
  };
  context: string;
}

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  products?: Product[];
  quickActions?: QuickAction[];
  metadata?: {
    processingTime?: number;
    confidence?: number;
    intent?: string;
    budtender?: string;
  };
}

interface Product {
  id: number;
  name: string;
  brand: string;
  category: string;
  price: number;
  thc?: number;
  cbd?: number;
  image_url?: string;
}

interface ConversationFlow {
  id: string;
  name: string;
  steps: FlowStep[];
}

interface FlowStep {
  id: string;
  type: 'question' | 'action' | 'condition';
  content: string;
  nextStep?: string;
  options?: string[];
  field?: string; // Field to store response (e.g., 'name', 'email')
}

// Avatar options based on age and gender
const getAvatar = (age: string, gender: string): string => {
  const avatars = {
    'young_male': '👨🏽‍🦱',
    'young_female': '👩🏾‍🦰',
    'young_non-binary': '🧑‍🦱',
    'middle-aged_male': '👨‍💼',
    'middle-aged_female': '👩‍💼',
    'middle-aged_non-binary': '🧑‍💼',
    'senior_male': '👨🏿‍🦲',
    'senior_female': '👵',
    'senior_non-binary': '🧓'
  };
  const key = `${age}_${gender}` as keyof typeof avatars;
  return avatars[key] || '🧑‍🦱';
};

// Generate greeting based on personality traits
const generateGreeting = (personality: any): string => {
  const name = personality.name;
  const style = personality.communication_style;
  
  if (style === 'casual') {
    return `Hey there! I'm ${name}, your friendly budtender! What brings you in today?`;
  } else if (style === 'professional') {
    return `Welcome! I'm ${name}, and I'm delighted to help you today. How may I assist you?`;
  } else if (style === 'enthusiastic') {
    return `What's good! I'm ${name}, ready to help you find something amazing! What are you looking for?`;
  } else {
    return `Hello! I'm ${name}, your cannabis consultant. Let's find the perfect product for you!`;
  }
};

// Customer identification flow
const customerIdentificationFlow: ConversationFlow = {
  id: 'customer_id',
  name: 'Customer Identification',
  steps: [
    {
      id: 'ask_name',
      type: 'question',
      content: "Before we get started, may I have your name?",
      field: 'name',
      nextStep: 'ask_contact'
    },
    {
      id: 'ask_contact',
      type: 'question',
      content: "Great! And could I get your phone number or email for our records?",
      field: 'contact',
      nextStep: 'complete'
    },
    {
      id: 'complete',
      type: 'action',
      content: "Perfect! Now, what can I help you find today?"
    }
  ]
};

function ProductCard({ product }: { product: Product }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden hover:shadow-md transition-shadow"
    >
      {product.image_url ? (
        <img
          src={product.image_url}
          alt={product.name}
          className="w-full h-32 object-cover"
        />
      ) : (
        <div className="w-full h-32 bg-gradient-to-br from-weed-green-400 to-weed-green-600 flex items-center justify-center">
          <Cannabis className="w-12 h-12 text-white/50" />
        </div>
      )}
      <div className="p-3">
        <h4 className="font-semibold text-gray-900 text-sm">{product.name}</h4>
        <p className="text-xs text-gray-600">{product.brand}</p>
        <div className="flex justify-between items-center mt-2">
          <span className="text-lg font-bold text-weed-green-600">${product.price}</span>
          <div className="flex gap-2 text-xs">
            {product.thc && <span className="bg-purple-100 text-purple-700 px-2 py-1 rounded">THC: {product.thc}%</span>}
            {product.cbd && <span className="bg-blue-100 text-blue-700 px-2 py-1 rounded">CBD: {product.cbd}%</span>}
          </div>
        </div>
      </div>
    </motion.div>
  );
}

export default function LiveChatTestingFixed() {
  // Use context for persistent state
  const {
    messages,
    setMessages,
    selectedBudtender,
    setSelectedBudtender,
    customerProfile,
    setCustomerProfile,
    isIdentified,
    setIsIdentified,
    sessionId,
    clearConversation
  } = useChat();
  
  // Local state for UI-specific things
  const [budtenders, setBudtenders] = useState<BudtenderPersonality[]>([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [aiState, setAiState] = useState<'idle' | 'thinking' | 'searching' | 'writing'>('idle');
  const [showHistory, setShowHistory] = useState(false);
  const [currentFlow, setCurrentFlow] = useState<ConversationFlow | null>(null);
  const [currentFlowStep, setCurrentFlowStep] = useState<FlowStep | null>(null);
  const [showCloseSessionModal, setShowCloseSessionModal] = useState(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  // Fetch personalities from database
  const { data: personalitiesData, isLoading: personalitiesLoading } = useQuery({
    queryKey: ['ai-personalities'],
    queryFn: async () => {
      const response = await axios.get(endpoints.ai.personalities);
      return response.data;
    }
  });
  
  // Transform database personalities to budtender format
  useEffect(() => {
    if (personalitiesData?.personalities) {
      // For testing, show ALL personalities, not just active ones
      const allBudtenders = personalitiesData.personalities
        // Remove the filter to show all personalities for testing
        // .filter((p: any) => p.active)
        .map((p: any) => ({
          id: p.id.toString(),
          name: p.name,
          avatar: getAvatar(p.age, p.gender),
          tagline: p.description || `Your ${p.communication_style} cannabis guide`,
          style: `${p.age}, ${p.communication_style}, ${p.humor_style}`,
          greeting: generateGreeting(p),
          active: p.active // Keep track of active status
        }));
      
      setBudtenders(allBudtenders);
      
      // Set first budtender as default (prefer active ones)
      if (allBudtenders.length > 0 && !selectedBudtender) {
        const activeBudtender = allBudtenders.find((b: any) => b.active);
        setSelectedBudtender(activeBudtender || allBudtenders[0]);
      }
    }
  }, [personalitiesData, selectedBudtender]);
  
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
  
  useEffect(() => {
    scrollToBottom();
  }, [messages]);
  
  // Initialize with greeting when first budtender is selected
  useEffect(() => {
    if (!selectedBudtender) return;
    
    // Only set initial greeting if there are no messages yet
    if (messages.length === 0) {
      const greetingMessage: Message = {
        id: `greeting_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        role: 'assistant',
        content: selectedBudtender?.greeting || 'Hello! How can I help you today?',
        timestamp: new Date(),
        metadata: {
          budtender: selectedBudtender?.id || 'default'
        }
      };
      setMessages([greetingMessage]);
      
      // Start customer identification flow if not identified
      if (!isIdentified) {
        setTimeout(() => {
          startIdentificationFlow();
        }, 2000);
      }
    }
  }, [selectedBudtender, messages.length, isIdentified]); // Re-run when selectedBudtender changes
  
  // Start customer identification flow
  const startIdentificationFlow = () => {
    if (!selectedBudtender) return;
    
    setCurrentFlow(customerIdentificationFlow);
    setCurrentFlowStep(customerIdentificationFlow.steps[0]);
    
    // Add a slight delay to ensure proper timestamp ordering
    const flowTimestamp = new Date(Date.now() + 100); // Add 100ms to ensure it's after greeting
    const flowMessage: Message = {
      id: `flow_${flowTimestamp.getTime()}_${Math.random().toString(36).substr(2, 9)}`,
      role: 'assistant',
      content: customerIdentificationFlow.steps[0].content,
      timestamp: flowTimestamp,
      metadata: {
        budtender: selectedBudtender?.id || 'default'
      }
    };
    setMessages(prev => [...prev, flowMessage]);
  };
  
  // Handle flow progression
  const handleFlowResponse = (response: string) => {
    if (!currentFlowStep) return;
    
    // Store the response in customer profile
    if (currentFlowStep.field === 'name') {
      setCustomerProfile(prev => ({ ...prev, name: response }));
    } else if (currentFlowStep.field === 'contact') {
      // Determine if it's email or phone
      if (response.includes('@')) {
        setCustomerProfile(prev => ({ ...prev, email: response }));
      } else {
        setCustomerProfile(prev => ({ ...prev, phone: response }));
      }
    }
    
    // Move to next step
    if (currentFlowStep.nextStep) {
      const nextStep = currentFlow?.steps.find(s => s.id === currentFlowStep.nextStep);
      if (nextStep) {
        setCurrentFlowStep(nextStep);
        
        const flowMessage: Message = {
          id: `flow_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
          role: 'assistant',
          content: nextStep.content,
          timestamp: new Date(),
          metadata: {
            budtender: selectedBudtender?.id
          }
        };
        setMessages(prev => [...prev, flowMessage]);
        
        // If this is the complete step, mark as identified
        if (nextStep.id === 'complete') {
          setIsIdentified(true);
          setCurrentFlow(null);
          setCurrentFlowStep(null);
          
          // Generate customer ID
          setCustomerProfile(prev => ({
            ...prev,
            customerId: `CUST_${Date.now().toString(36).toUpperCase()}`
          }));
          
          toast.success(`Welcome ${customerProfile.name}! You're all set.`);
        }
      }
    }
  };
  
  // Handle budtender switch
  const handleBudtenderChange = (newBudtender: BudtenderPersonality) => {
    if (newBudtender.id === selectedBudtender?.id) return;
    
    // Add transition message
    const transitionMessage: Message = {
      id: `transition_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      role: 'system',
      content: `Switching to ${newBudtender.name}...`,
      timestamp: new Date()
    };
    
    // New budtender greeting with context
    const contextualGreeting = isIdentified
      ? `Hi ${customerProfile.name}! I'm ${newBudtender.name}, taking over from ${selectedBudtender?.name || 'your previous budtender'}. ${newBudtender.tagline}. How can I continue helping you?`
      : `Hi! I'm ${newBudtender.name}. ${newBudtender.greeting}`;
    
    const newGreeting: Message = {
      id: `greeting_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      role: 'assistant',
      content: contextualGreeting,
      timestamp: new Date(),
      metadata: {
        budtender: newBudtender.id
      }
    };
    
    setMessages(prev => [...prev, transitionMessage, newGreeting]);
    setSelectedBudtender(newBudtender);
  };
  
  // Fetch conversation history
  const { data: conversationHistory } = useQuery({
    queryKey: ['conversation-history', sessionId],
    queryFn: async () => {
      const response = await axios.get(endpoints.conversations.get(sessionId));
      return response.data;
    },
    enabled: showHistory
  });
  
  // Send message mutation
  const sendMessage = useMutation({
    mutationFn: async (message: string) => {
      const response = await axios.post(endpoints.chat.base, {
        message,
        customer_id: customerProfile.customerId || 'guest',
        session_id: sessionId,
        context: {
          customer_name: customerProfile.name,
          customer_phone: customerProfile.phone,
          customer_email: customerProfile.email,
          preferences: customerProfile.preferences,
          budtender_personality: selectedBudtender?.name || 'default',
          budtender_style: selectedBudtender?.style || 'professional',
          is_identified: isIdentified
        }
      });
      return response.data;
    },
    onMutate: (message) => {
      // Add user message
      const userMessage: Message = {
        id: `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        role: 'user',
        content: message,
        timestamp: new Date()
      };
      console.log('Adding user message:', userMessage); // Debug log
      setMessages(prev => {
        const newMessages = [...prev, userMessage];
        console.log('All messages after adding user message:', newMessages); // Debug log
        return newMessages;
      });
      setIsTyping(true);
      setAiState('thinking');
      
      // Simulate AI state changes
      setTimeout(() => setAiState('searching'), 500);
      setTimeout(() => setAiState('writing'), 1500);
    },
    onSuccess: (data) => {
      console.log('API Response:', data); // Debug log to see what we're getting
      
      // Check if the response indicates an error stage (LLM unavailable)
      if (data.stage === 'error' || data.error === 'LLM_NOT_AVAILABLE') {
        setIsTyping(false);
        setAiState('idle');
        
        const errorMessage: Message = {
          id: `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
          role: 'assistant',
          content: '🚫 AI Service Unavailable: The AI engine is currently offline. Our intelligent budtender service requires the AI model to be running. Please contact support or try again later.',
          timestamp: new Date(),
          metadata: {
            budtender: selectedBudtender?.id || 'default',
            errorType: 'ai_unavailable'
          }
        };
        setMessages(prev => [...prev, errorMessage]);
        
        toast.error('AI Service Unavailable - Cannot process conversations without the AI model');
        return;
      }
      
      // Add AI response
      const aiMessage: Message = {
        id: `ai_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        role: 'assistant',
        content: data.message || data.response || 'I understand. Let me help you find what you need.',
        timestamp: new Date(),
        products: data.products || [],
        quickActions: data.quick_actions || [],  // Add quick actions from response
        metadata: {
          processingTime: data.response_time_ms || data.processing_time,
          confidence: data.confidence,
          intent: data.intent,
          budtender: selectedBudtender?.id || 'default'
        }
      };
      console.log('Adding AI message:', aiMessage); // Debug log to see the message being added
      setMessages(prev => {
        const newMessages = [...prev, aiMessage];
        console.log('All messages after adding AI response:', newMessages); // Debug log to see all messages
        return newMessages;
      });
      setIsTyping(false);
      setAiState('idle');
    },
    onError: (error: any) => {
      console.error('Chat error:', error);
      setIsTyping(false);
      setAiState('idle');
      
      // Check if this is an AI availability error
      const isAIUnavailable = error?.response?.data?.error === 'LLM_NOT_AVAILABLE' ||
                             error?.response?.data?.stage === 'error' ||
                             error?.response?.data?.message?.includes('AI service') ||
                             error?.response?.data?.message?.includes('AI model not available');
      
      const errorContent = isAIUnavailable 
        ? '🚫 AI Service Unavailable: The AI engine is currently offline. Our intelligent budtender service requires the AI model to be running. Please contact support or try again later.'
        : 'Sorry, I encountered an error. Please try again.';
      
      const errorMessage: Message = {
        id: `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        role: 'assistant',
        content: errorContent,
        timestamp: new Date(),
        metadata: {
          budtender: selectedBudtender?.id || 'default',
          errorType: isAIUnavailable ? 'ai_unavailable' : 'general_error'
        }
      };
      setMessages(prev => [...prev, errorMessage]);
      
      // Show toast notification for AI unavailability
      if (isAIUnavailable) {
        toast.error('AI Service Unavailable - Cannot process conversations without the AI model');
      }
    }
  });
  
  const handleSendMessage = (message: string) => {
    if (message.trim() && !sendMessage.isPending) {
      // Check if we're in a flow
      if (currentFlowStep) {
        handleFlowResponse(message);
        // Add user's response to messages
        const userMessage: Message = {
          id: `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
          role: 'user',
          content: message,
          timestamp: new Date()
        };
        setMessages(prev => [...prev, userMessage]);
      } else {
        // Normal message handling
        sendMessage.mutate(message);
      }
    }
  };

  const handleSend = () => {
    if (input.trim()) {
      handleSendMessage(input.trim());
      setInput('');
    }
  };
  
  const clearChat = () => {
    clearConversation(); // Use the context method to clear everything
    
    // If we have a selected budtender, re-add the greeting
    if (selectedBudtender) {
      const greetingMessage: Message = {
        id: `greeting_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        role: 'assistant',
        content: selectedBudtender?.greeting || 'Hello! How can I help you today?',
        timestamp: new Date(),
        metadata: {
          budtender: selectedBudtender?.id || 'default'
        }
      };
      console.log('Clearing chat and setting greeting:', greetingMessage);
      setMessages([greetingMessage]);
    }
  };

  const closeSession = async () => {
    try {
      // Add a closing message to the chat
      const closingMessage: Message = {
        id: `closing_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        role: 'system',
        content: `Session ended. Thank you ${customerProfile.name || 'for visiting'}! Have a great day! 🌿`,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, closingMessage]);

      // Log session end to the backend
      await axios.post(endpoints.sessions.close, {
        session_id: sessionId,
        customer_id: customerProfile.customerId,
        ended_at: new Date().toISOString(),
        total_messages: messages.length,
        customer_satisfied: true // Could be determined from conversation
      }).catch(err => {
        console.log('Session close tracking failed:', err);
        // Don't block the UI if tracking fails
      });

      // Show success toast
      toast.success(`Session closed for ${customerProfile.name || 'customer'}`);

      // Wait a moment to show the closing message
      setTimeout(() => {
        // Reset everything for a new session
        clearConversation();
        setIsIdentified(false);
        setCurrentFlow(null);
        setCurrentFlowStep(null);
        
        // Generate new session ID
        const newSessionId = `session_${Date.now()}`;
        // Note: We'd need to update the context's sessionId here
        // For now, we'll just clear and let the user start fresh
        
        // Reset to initial state with greeting
        if (selectedBudtender) {
          const greetingMessage: Message = {
            id: `greeting_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            role: 'assistant',
            content: selectedBudtender?.greeting || 'Hello! How can I help you today?',
            timestamp: new Date(),
            metadata: {
              budtender: selectedBudtender?.id || 'default'
            }
          };
          setMessages([greetingMessage]);
        }
      }, 2000);

      // Close the modal
      setShowCloseSessionModal(false);
    } catch (error) {
      console.error('Error closing session:', error);
      toast.error('Failed to close session properly');
    }
  };
  
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-xl shadow-sm p-6">
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Live Chat Testing</h2>
            <p className="text-gray-600 mt-1">Test AI responses with different customer scenarios</p>
          </div>
          <div className="flex items-center gap-4">
            {/* Customer Info Display */}
            {isIdentified && (
              <div className="bg-gray-50 px-4 py-2 rounded-lg">
                <div className="flex items-center gap-2">
                  <UserCircle className="w-5 h-5 text-gray-600" />
                  <div>
                    <p className="text-sm font-semibold text-gray-900">{customerProfile.name}</p>
                    <p className="text-xs text-gray-600">
                      {customerProfile.email || customerProfile.phone || 'No contact'}
                    </p>
                  </div>
                </div>
              </div>
            )}
            
            {/* History Button */}
            <button
              onClick={() => setShowHistory(!showHistory)}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 flex items-center gap-2"
            >
              <History className="w-4 h-4" />
              History
            </button>
            
            {/* Close Session Button - Only show when customer is identified */}
            {isIdentified && (
              <button
                onClick={() => setShowCloseSessionModal(true)}
                className="px-4 py-2 bg-purple-100 text-purple-700 rounded-lg hover:bg-purple-200 flex items-center gap-2"
              >
                <LogOut className="w-4 h-4" />
                Close Session
              </button>
            )}
            
            {/* Clear Chat */}
            <button
              onClick={clearChat}
              className="px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200"
            >
              Clear Chat
            </button>
          </div>
        </div>
      </div>
      
      {/* Main Chat Area */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Chat Window */}
        <div className="lg:col-span-3 bg-white rounded-xl shadow-sm">
          {/* Budtender Selection Bar */}
          <div className="p-4 border-b border-gray-200 bg-gradient-to-r from-weed-green-50 to-purple-haze-50">
            {personalitiesLoading ? (
              <div className="flex items-center justify-center py-2">
                <Loader className="w-5 h-5 animate-spin text-weed-green-600" />
                <span className="ml-2 text-gray-600">Loading personalities...</span>
              </div>
            ) : selectedBudtender ? (
              <div className="flex justify-between items-center">
                <div className="flex items-center gap-3">
                  <span className="text-3xl">{selectedBudtender?.avatar || '🤖'}</span>
                  <div>
                    <h3 className="font-semibold text-gray-900">{selectedBudtender?.name || 'Select a Budtender'}</h3>
                    <p className="text-sm text-gray-600">{selectedBudtender?.tagline || 'Choose your AI assistant'}</p>
                  </div>
                </div>
                <select
                  value={selectedBudtender?.id || ''}
                  onChange={(e) => {
                    const budtender = budtenders.find(b => b.id === e.target.value);
                    if (budtender) handleBudtenderChange(budtender);
                  }}
                  className="px-4 py-2 bg-gradient-to-r from-weed-green-500 to-weed-green-600 text-white rounded-lg font-medium shadow-sm hover:shadow-md transition-all"
                >
                  {budtenders.map(budtender => (
                    <option key={budtender.id} value={budtender.id}>
                      {budtender.avatar} {budtender.name} {budtender.active ? '✅' : '⚪'}
                    </option>
                  ))}
                </select>
              </div>
            ) : (
              <div className="text-center py-2 text-gray-500">
                No personalities found. Please create some in the AI Personality page.
              </div>
            )}
          </div>
          
          {/* Messages */}
          <div className="h-[500px] overflow-y-auto p-6 space-y-4">
            {console.log('Rendering messages:', messages) /* Debug log to see what we're rendering */}
            {/* Sort messages by timestamp to ensure chronological order */}
            {[...messages]
              .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
              .map((message) => {
              console.log(`Rendering message - Role: ${message.role}, Content: ${message.content.substring(0, 50)}...`);
              return (
              <motion.div
                key={message.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {message.role === 'system' ? (
                  <div className="bg-gray-100 text-gray-600 px-4 py-2 rounded-lg text-sm italic max-w-md">
                    {message.content}
                  </div>
                ) : (
                  <div className={`flex gap-3 max-w-lg ${message.role === 'user' ? 'flex-row-reverse' : ''}`}>
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                      message.role === 'user' 
                        ? 'bg-blue-500 text-white' 
                        : 'bg-weed-green-500 text-white'
                    }`}>
                      {message.role === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                    </div>
                    <div>
                      <div className={`px-4 py-3 rounded-lg ${
                        message.role === 'user'
                          ? 'bg-blue-500 text-white'
                          : 'bg-gray-100 text-gray-900'
                      }`}>
                        {message.content}
                      </div>
                      
                      {/* Product Cards */}
                      {message.products && message.products.length > 0 && (
                        <div className="grid grid-cols-2 gap-3 mt-3">
                          {message.products.map(product => (
                            <ProductCard key={product.id} product={product} />
                          ))}
                        </div>
                      )}
                      
                      {/* Quick Actions */}
                      {message.quickActions && message.quickActions.length > 0 && message.role === 'assistant' && (
                        <QuickActionGroup
                          actions={message.quickActions}
                          onActionClick={(action) => {
                            // Send the quick action value as a message
                            handleSendMessage(action.value);
                            // Track the action
                            console.log('Quick action clicked:', action);
                          }}
                          title="Quick responses:"
                        />
                      )}
                      
                      {/* Metadata */}
                      {message.metadata && (
                        <div className="mt-2 text-xs text-gray-500">
                          {message.metadata.processingTime && (
                            <span>Response time: {message.metadata.processingTime}ms</span>
                          )}
                          {message.metadata.confidence && (
                            <span className="ml-3">Confidence: {(message.metadata.confidence * 100).toFixed(0)}%</span>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </motion.div>
            );
            })}
            
            {/* Typing Indicator */}
            {isTyping && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex items-center gap-2 text-gray-500"
              >
                <div className="flex items-center gap-1">
                  <Bot className="w-4 h-4" />
                  <span className="text-sm">{selectedBudtender?.name || 'AI'} is {aiState}...</span>
                </div>
                <div className="flex gap-1">
                  <motion.div
                    animate={{ y: [0, -5, 0] }}
                    transition={{ repeat: Infinity, duration: 0.6, delay: 0 }}
                    className="w-2 h-2 bg-weed-green-500 rounded-full"
                  />
                  <motion.div
                    animate={{ y: [0, -5, 0] }}
                    transition={{ repeat: Infinity, duration: 0.6, delay: 0.1 }}
                    className="w-2 h-2 bg-weed-green-500 rounded-full"
                  />
                  <motion.div
                    animate={{ y: [0, -5, 0] }}
                    transition={{ repeat: Infinity, duration: 0.6, delay: 0.2 }}
                    className="w-2 h-2 bg-weed-green-500 rounded-full"
                  />
                </div>
              </motion.div>
            )}
            
            <div ref={messagesEndRef} />
          </div>
          
          {/* Input Area */}
          <div className="p-4 border-t border-gray-200">
            <div className="flex gap-3">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                placeholder={
                  currentFlowStep
                    ? "Please answer the question above..."
                    : selectedBudtender 
                      ? `Ask ${selectedBudtender?.name || 'the budtender'} anything...`
                      : "Select a budtender to start chatting..."
                }
                className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-weed-green-500"
                disabled={sendMessage.isPending}
              />
              <button
                onClick={handleSend}
                disabled={!input.trim() || sendMessage.isPending}
                className="px-6 py-3 bg-weed-green-500 text-white rounded-lg hover:bg-weed-green-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {sendMessage.isPending ? (
                  <Loader className="w-5 h-5 animate-spin" />
                ) : (
                  <MessageSquare className="w-5 h-5" />
                )}
                Chat
              </button>
            </div>
          </div>
        </div>
        
        {/* Conversation History Sidebar */}
        {showHistory && (
          <div className="bg-white rounded-xl shadow-sm p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Conversation History</h3>
            {conversationHistory ? (
              <div className="space-y-3">
                {conversationHistory.sessions?.map((session: any) => (
                  <div key={session.id} className="p-3 bg-gray-50 rounded-lg cursor-pointer hover:bg-gray-100">
                    <p className="text-sm font-medium text-gray-900">
                      {new Date(session.created_at).toLocaleDateString()}
                    </p>
                    <p className="text-xs text-gray-600">
                      {session.message_count} messages
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-500">No history available</p>
            )}
          </div>
        )}
      </div>

      {/* Close Session Confirmation Modal */}
      {showCloseSessionModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white rounded-xl shadow-xl p-6 max-w-md w-full mx-4"
          >
            <div className="flex justify-between items-start mb-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <LogOut className="w-6 h-6 text-purple-600" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">Close Customer Session?</h3>
                  <p className="text-sm text-gray-600 mt-1">
                    {customerProfile.name ? `End session for ${customerProfile.name}` : 'End current session'}
                  </p>
                </div>
              </div>
              <button
                onClick={() => setShowCloseSessionModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 mb-6">
              <p className="text-sm text-purple-800">
                This will end the current chat session with the customer. The conversation will be saved and the customer will need to start a new session for future interactions.
              </p>
              {messages.length > 0 && (
                <div className="mt-3 pt-3 border-t border-purple-200">
                  <p className="text-xs text-purple-700">
                    Session Statistics:
                  </p>
                  <ul className="text-xs text-purple-600 mt-1 space-y-1">
                    <li>• Total Messages: {messages.length}</li>
                    <li>• Session Duration: {Math.round((Date.now() - parseInt(sessionId.split('_')[1] || '0')) / 60000)} minutes</li>
                    <li>• Budtender: {selectedBudtender?.name || 'Default'}</li>
                  </ul>
                </div>
              )}
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => setShowCloseSessionModal(false)}
                className="flex-1 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={closeSession}
                className="flex-1 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors flex items-center justify-center gap-2"
              >
                <LogOut className="w-4 h-4" />
                Close Session
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  );
}