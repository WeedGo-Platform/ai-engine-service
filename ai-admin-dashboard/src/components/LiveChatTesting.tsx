import { endpoints } from '../config/endpoints';
import { useState, useRef, useEffect } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import axios from 'axios';
import apiService from '../services/api';
import { MessageCircle, User, Clock, Hash, Search, Brain, Loader2, ChevronDown, Cannabis, ShoppingBag } from 'lucide-react';
import ProductCard from './chat/ProductCard';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  products?: Product[];
  quickReplies?: string[];
  metadata?: {
    processingTime?: number;
    confidence?: number;
    intent?: string;
    budtender?: string;
  };
}

interface Product {
  id: string;
  name: string;
  brand: string;
  category: string;
  thc_content?: string;
  cbd_content?: string;
  price: number;
  image_url?: string;
  description?: string;
  effects?: string[];
  in_stock?: boolean;
}

interface TestProfile {
  name: string;
  customerId: string;
  context: string;
  preferences: Record<string, any>;
}

interface BudtenderPersonality {
  id: string;
  name: string;
  avatar: string;
  tagline: string;
  style: string;
  greeting: string;
}

// Fetch personalities from the same source as AI Personality page
// This ensures consistency across the application

const testProfiles: TestProfile[] = [
  {
    name: 'New Customer',
    customerId: 'test_new_001',
    context: 'First time cannabis user, anxious about trying',
    preferences: { experience_level: 'beginner', concerns: ['anxiety', 'dosage'] }
  },
  {
    name: 'Medical Patient',
    customerId: 'test_med_001',
    context: 'Chronic pain patient, prefers CBD products',
    preferences: { medical: true, conditions: ['chronic_pain'], prefers_cbd: true }
  },
  {
    name: 'Experienced User',
    customerId: 'test_exp_001',
    context: 'Daily user, high tolerance, likes concentrates',
    preferences: { experience_level: 'expert', preferred_category: 'concentrates', tolerance: 'high' }
  },
  {
    name: 'Budget Conscious',
    customerId: 'test_budget_001',
    context: 'Looking for best value, bulk purchases',
    preferences: { budget_conscious: true, prefers_bulk: true, price_sensitive: true }
  }
];

const quickQueries = [
  "What's good for anxiety?",
  "Got any fire?",
  "I need something for sleep",
  "Show me your strongest edibles",
  "What's on sale today?",
  "I want something fruity",
  "First time, what should I try?",
  "Gimme a half of pink kush"
];

// Product Card Component
function ProductCard({ product }: { product: Product }) {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden hover:shadow-md transition-shadow">
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
        <div className="flex justify-between items-start mb-1">
          <div>
            <h4 className="font-semibold text-sm text-gray-900">{product.name}</h4>
            <p className="text-xs text-gray-500">{product.brand}</p>
          </div>
          <span className="text-lg font-bold text-weed-green-600">${product.price}</span>
        </div>
        
        <div className="flex items-center space-x-2 mb-2">
          {product.thc_content && (
            <span className="px-2 py-0.5 bg-purple-haze-100 text-purple-haze-700 text-xs rounded">
              THC: {product.thc_content}
            </span>
          )}
          {product.cbd_content && (
            <span className="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded">
              CBD: {product.cbd_content}
            </span>
          )}
        </div>

        {product.effects && product.effects.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {product.effects.slice(0, 3).map((effect, idx) => (
              <span key={idx} className="text-xs text-gray-600">
                {effect}{idx < 2 && idx < product.effects!.length - 1 ? ' •' : ''}
              </span>
            ))}
          </div>
        )}

        <div className="flex items-center justify-between mt-2">
          <span className={`text-xs ${product.in_stock ? 'text-green-600' : 'text-red-600'}`}>
            {product.in_stock ? '✓ In Stock' : '✗ Out of Stock'}
          </span>
          <button className="text-xs text-weed-green-600 hover:text-weed-green-700 font-medium">
            View Details →
          </button>
        </div>
      </div>
    </div>
  );
}

export default function LiveChatTesting() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [selectedProfile, setSelectedProfile] = useState<TestProfile>(testProfiles[0]);
  const [selectedBudtender, setSelectedBudtender] = useState<BudtenderPersonality | null>(null);
  const [showBudtenderMenu, setShowBudtenderMenu] = useState(false);
  const [sessionId] = useState(`test_session_${Date.now()}`);
  const [isTyping, setIsTyping] = useState(false);
  const [aiState, setAiState] = useState<'idle' | 'thinking' | 'searching' | 'writing'>('idle');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Fetch personalities from API (same source as AI Personality page)
  const { data: personalitiesData, isLoading: loadingPersonalities } = useQuery({
    queryKey: ['personalities'],
    queryFn: () => apiService.getPersonalities(),
  });

  // Transform API personalities to match BudtenderPersonality interface
  const budtenderPersonalities: BudtenderPersonality[] = personalitiesData?.personalities?.map((p: any) => ({
    id: p.id,
    name: p.name,
    avatar: p.gender === 'female' ? '👩' : p.gender === 'male' ? '👨' : '🧑',
    tagline: p.description?.substring(0, 50) || 'Your cannabis expert',
    style: p.communication_style,
    greeting: p.sample_responses?.greeting || `Hi! I'm ${p.name}. How can I help you today?`
  })) || [];

  // Set initial budtender when personalities load
  useEffect(() => {
    if (budtenderPersonalities.length > 0 && !selectedBudtender) {
      // Find active personality or use first one
      const activePersonality = budtenderPersonalities.find((p: any) => p.active) || budtenderPersonalities[0];
      setSelectedBudtender(activePersonality);
    }
  }, [budtenderPersonalities, selectedBudtender]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Send initial greeting when budtender changes
  useEffect(() => {
    if (messages.length === 0 || messages[messages.length - 1]?.metadata?.budtender !== selectedBudtender.id) {
      const greetingMessage: Message = {
        id: `greeting_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        role: 'assistant',
        content: selectedBudtender.greeting,
        timestamp: new Date(),
        metadata: {
          budtender: selectedBudtender.id
        }
      };
      setMessages(prev => [...prev, greetingMessage]);
    }
  }, [selectedBudtender]);

  const sendMessage = useMutation({
    mutationFn: async (message: string) => {
      const response = await axios.post(endpoints.chat.base, {
        message,
        customer_id: selectedProfile.customerId,
        session_id: sessionId,
        budtender_personality: selectedBudtender
      });
      return response.data;
    },
    onMutate: (message) => {
      // Add user message immediately
      const userMessage: Message = {
        id: `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        role: 'user',
        content: message,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, userMessage]);
      setIsTyping(true);
      setAiState('thinking');
      // Simulate different AI states
      setTimeout(() => setAiState('searching'), 500);
      setTimeout(() => setAiState('writing'), 1500);
    },
    onSuccess: (data) => {
      // Generate context-aware quick replies
      const quickReplies = generateQuickReplies(data, messages[messages.length - 1]?.content || '');
      
      // Add AI response with products if available
      const aiMessage: Message = {
        id: `ai_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        role: 'assistant',
        content: data.message || data.response || 'I understand. Let me help you find what you need.',
        timestamp: new Date(),
        products: data.products || [],
        quickReplies: data.quick_replies || quickReplies,
        metadata: {
          processingTime: data.response_time_ms || data.processing_time,
          confidence: data.confidence,
          intent: data.intent,
          budtender: selectedBudtender.id
        }
      };
      setMessages(prev => [...prev, aiMessage]);
      setIsTyping(false);
      setAiState('idle');
    },
    onError: (error) => {
      console.error('Chat error:', error);
      setIsTyping(false);
      setAiState('idle');
      // Add error message
      const errorMessage: Message = {
        id: `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your request. Please try again.',
        timestamp: new Date(),
        metadata: {
          budtender: selectedBudtender.id
        }
      };
      setMessages(prev => [...prev, errorMessage]);
    }
  });

  const handleSend = () => {
    if (input.trim() && !sendMessage.isPending) {
      sendMessage.mutate(input);
      setInput('');
    }
  };

  const handleQuickQuery = (query: string) => {
    setInput(query);
    sendMessage.mutate(query);
  };

  // Generate context-aware quick reply suggestions
  const generateQuickReplies = (response: any, lastUserMessage: string): string[] => {
    const replies: string[] = [];
    
    // If products were shown
    if (response.products && response.products.length > 0) {
      replies.push('Show me similar products');
      replies.push('Tell me more about effects');
      replies.push('Compare these products');
      
      // If multiple products, offer to see more
      if (response.products.length >= 3) {
        replies.push('Show me more options');
      }
    }
    
    // Context-based suggestions
    const lowerMessage = lastUserMessage.toLowerCase();
    if (lowerMessage.includes('pain') || lowerMessage.includes('relief')) {
      if (!replies.includes('Show me CBD products')) {
        replies.push('Show me CBD products');
      }
      replies.push('What about topicals?');
    } else if (lowerMessage.includes('sleep') || lowerMessage.includes('insomnia')) {
      replies.push('Show me indica strains');
      replies.push('What about edibles?');
    } else if (lowerMessage.includes('energy') || lowerMessage.includes('focus')) {
      replies.push('Show me sativa strains');
      replies.push('Any pre-rolls available?');
    }
    
    // General navigation options
    if (replies.length === 0) {
      replies.push('Show me popular products');
      replies.push('I need help choosing');
      replies.push('What\'s on sale?');
      replies.push('Tell me about effects');
    }
    
    // Limit to 4 suggestions
    return replies.slice(0, 4);
  };

  const clearChat = () => {
    setMessages([]);
    // Add greeting after clearing
    setTimeout(() => {
      const greetingMessage: Message = {
        id: `greeting_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        role: 'assistant',
        content: selectedBudtender.greeting,
        timestamp: new Date(),
        metadata: {
          budtender: selectedBudtender.id
        }
      };
      setMessages([greetingMessage]);
    }, 100);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-xl shadow-sm p-6">
        <div className="flex justify-between items-center mb-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Live Testing Console</h2>
            <p className="text-gray-600 mt-1">Test the AI budtender with different customer profiles and scenarios</p>
          </div>
          <div className="flex items-center space-x-4">
            <span className="text-sm text-gray-500">Session: {sessionId.slice(-8)}</span>
            <button
              onClick={clearChat}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
            >
              Clear Chat
            </button>
          </div>
        </div>

        {/* Budtender Selection */}
        <div className="border-t pt-4 mb-4">
          <h3 className="text-sm font-medium text-gray-700 mb-3">AI Budtender:</h3>
          <div className="relative">
            <button
              onClick={() => setShowBudtenderMenu(!showBudtenderMenu)}
              className="w-full md:w-auto px-4 py-3 bg-gradient-to-r from-weed-green-500 to-weed-green-600 text-white rounded-lg hover:from-weed-green-600 hover:to-weed-green-700 transition-all flex items-center justify-between space-x-3"
            >
              <div className="flex items-center space-x-3">
                <span className="text-2xl">{selectedBudtender.avatar}</span>
                <div className="text-left">
                  <div className="font-semibold">{selectedBudtender.name}</div>
                  <div className="text-xs opacity-90">{selectedBudtender.tagline}</div>
                </div>
              </div>
              <ChevronDown className={`w-5 h-5 transition-transform ${showBudtenderMenu ? 'rotate-180' : ''}`} />
            </button>
            
            {showBudtenderMenu && (
              <div className="absolute z-10 mt-2 w-full md:w-96 bg-white rounded-lg shadow-lg border border-gray-200 overflow-hidden">
                {budtenderPersonalities.map((personality) => (
                  <button
                    key={personality.id}
                    onClick={() => {
                      setSelectedBudtender(personality);
                      setShowBudtenderMenu(false);
                    }}
                    className={`w-full px-4 py-3 hover:bg-gray-50 flex items-center space-x-3 transition-colors ${
                      selectedBudtender.id === personality.id ? 'bg-weed-green-50' : ''
                    }`}
                  >
                    <span className="text-2xl">{personality.avatar}</span>
                    <div className="text-left flex-1">
                      <div className="font-medium text-gray-900">{personality.name}</div>
                      <div className="text-xs text-gray-600">{personality.tagline}</div>
                    </div>
                    {selectedBudtender.id === personality.id && (
                      <div className="w-2 h-2 bg-weed-green-500 rounded-full"></div>
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Test Profiles */}
        <div className="border-t pt-4">
          <h3 className="text-sm font-medium text-gray-700 mb-3">Test Profile:</h3>
          <div className="grid grid-cols-4 gap-3">
            {testProfiles.map((profile) => (
              <button
                key={profile.customerId}
                onClick={() => setSelectedProfile(profile)}
                className={`p-3 rounded-lg border-2 transition-all ${
                  selectedProfile.customerId === profile.customerId
                    ? 'border-weed-green-500 bg-weed-green-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="font-medium text-sm">{profile.name}</div>
                <div className="text-xs text-gray-500 mt-1">{profile.context}</div>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Chat Interface */}
      <div className="bg-white rounded-xl shadow-sm">
        {/* Messages */}
        <div className="h-[600px] overflow-y-auto p-6 space-y-4">
          {messages.length === 0 ? (
            <div className="text-center text-gray-500 mt-20">
              <div className="text-6xl mb-4">{selectedBudtender.avatar}</div>
              <p className="text-lg font-medium">{selectedBudtender.name} is ready to help!</p>
              <p className="text-sm mt-2">Try one of the quick queries below</p>
            </div>
          ) : (
            messages.map((message) => (
              <div key={message.id}>
                <div className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`flex max-w-3xl ${
                    message.role === 'user' ? 'flex-row-reverse' : 'flex-row'
                  }`}>
                    <div className={`flex-shrink-0 ${
                      message.role === 'user' ? 'ml-3' : 'mr-3'
                    }`}>
                      {message.role === 'user' ? (
                        <div className="w-10 h-10 bg-purple-haze-500 rounded-full flex items-center justify-center">
                          <User className="w-6 h-6 text-white" />
                        </div>
                      ) : (
                        <div className="text-3xl">{selectedBudtender.avatar}</div>
                      )}
                    </div>
                    <div>
                      <div className={`${
                        message.role === 'user'
                          ? 'bg-purple-haze-100 text-purple-haze-900'
                          : 'bg-gray-100 text-gray-900'
                      } rounded-lg px-4 py-3 inline-block`}>
                        <p className="text-sm">{message.content}</p>
                        {message.metadata && (
                          <div className="mt-2 pt-2 border-t border-gray-200 flex items-center space-x-4 text-xs text-gray-500">
                            {message.metadata.processingTime && (
                              <span className="flex items-center">
                                <Clock className="w-3 h-3 mr-1" />
                                {message.metadata.processingTime}ms
                              </span>
                            )}
                            {message.metadata.confidence && (
                              <span className="flex items-center">
                                <Hash className="w-3 h-3 mr-1" />
                                {(message.metadata.confidence * 100).toFixed(0)}% confidence
                              </span>
                            )}
                          </div>
                        )}
                      </div>
                      
                      {/* Product Cards */}
                      {message.products && message.products.length > 0 && (
                        <div className="mt-3 space-y-2 max-w-2xl">
                          {message.products.map((product: any) => (
                            <ProductCard 
                              key={product.id || product.product_name} 
                              product={product}
                              compact={true}
                              onAddToCart={(product, quantity) => {
                                // Handle add to cart
                                console.log(`Adding ${quantity} of ${product.product_name} to cart`);
                                // Show success message
                                const successMessage = `Added ${quantity} x ${product.product_name} to cart`;
                                // You could trigger a toast notification here
                                alert(successMessage);
                              }}
                              onShowDetails={(product) => {
                                // Handle show details
                                console.log(`Showing details for ${product.product_name}`);
                              }}
                            />
                          ))}
                        </div>
                      )}
                      
                      {/* Quick Reply Suggestions */}
                      {message.quickReplies && message.quickReplies.length > 0 && 
                       message.id === messages[messages.length - 1]?.id && 
                       message.role === 'assistant' && (
                        <div className="mt-3 flex flex-wrap gap-2">
                          {message.quickReplies.map((reply, idx) => (
                            <button
                              key={idx}
                              onClick={() => {
                                setInput(reply);
                                sendMessage.mutate(reply);
                              }}
                              className="px-3 py-1.5 bg-white border border-weed-green-300 rounded-full text-sm text-weed-green-700 hover:bg-weed-green-50 hover:border-weed-green-400 transition-colors flex items-center gap-1.5"
                            >
                              <span className="text-weed-green-500">➜</span>
                              {reply}
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
          {isTyping && (
            <div className="flex justify-start">
              <div className="flex items-center space-x-3">
                <div className="text-3xl">{selectedBudtender.avatar}</div>
                <div className="bg-gray-100 rounded-lg px-4 py-3 max-w-md">
                  <div className="flex items-center space-x-2">
                    {aiState === 'thinking' && (
                      <>
                        <Brain className="w-4 h-4 text-purple-haze-500 animate-pulse" />
                        <span className="text-sm text-gray-600">{selectedBudtender.name} is thinking...</span>
                      </>
                    )}
                    {aiState === 'searching' && (
                      <>
                        <Search className="w-4 h-4 text-blue-500 animate-spin" />
                        <span className="text-sm text-gray-600">Searching products...</span>
                      </>
                    )}
                    {aiState === 'writing' && (
                      <>
                        <Loader2 className="w-4 h-4 text-weed-green-500 animate-spin" />
                        <span className="text-sm text-gray-600">Writing response...</span>
                      </>
                    )}
                  </div>
                  <div className="flex space-x-1 mt-2">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                  </div>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Quick Queries */}
        <div className="border-t px-6 py-3">
          <div className="flex items-center space-x-2 overflow-x-auto">
            <span className="text-xs text-gray-500 flex-shrink-0">Quick:</span>
            {quickQueries.map((query) => (
              <button
                key={query}
                onClick={() => handleQuickQuery(query)}
                className="flex-shrink-0 px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-xs hover:bg-gray-200"
              >
                {query}
              </button>
            ))}
          </div>
        </div>

        {/* Input */}
        <div className="border-t p-6">
          <div className="flex space-x-4">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSend()}
              placeholder={`Ask ${selectedBudtender.name} anything...`}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-weed-green-500"
              disabled={sendMessage.isPending}
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || sendMessage.isPending}
              className="px-6 py-2 bg-weed-green-500 text-white rounded-lg hover:bg-weed-green-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
            >
              <MessageCircle className="w-5 h-5" />
              <span>Chat</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}