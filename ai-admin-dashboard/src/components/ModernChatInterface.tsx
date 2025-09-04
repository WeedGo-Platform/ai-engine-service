import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { format } from 'date-fns';
import { useMutation } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { 
  Send, 
  X,
  Mic,
  MoreVertical,
  ChevronLeft
} from 'lucide-react';

interface Message {
  id: string;
  content: string;
  sender: 'user' | 'assistant';
  timestamp: Date;
  personality?: string;
  confidence?: number;
  processingTime?: number;
  version?: string;
  metadata?: any;
  quickActions?: QuickAction[];
  products?: any[];
}

interface QuickAction {
  id: string;
  label: string;
  value: string;
  icon?: string;
  type?: 'primary' | 'secondary' | 'info';
}

interface BudtenderPersonality {
  id: string;
  name: string;
  emoji: string;
  status: string;
  greeting: string;
  gradient: string;
}

const budtenders: BudtenderPersonality[] = [
  {
    id: 'bob',
    name: 'Bob',
    emoji: '👨‍🌾',
    status: 'Ready to help!',
    greeting: "Hey there! I'm Bob, your friendly cannabis guide! 🌿 I'm here to help you find exactly what you're looking for. What brings you in today?",
    gradient: 'from-pink-400 via-purple-400 to-indigo-400'
  },
  {
    id: 'sarah',
    name: 'Sarah',
    emoji: '👩‍⚕️',
    status: 'Medical expert',
    greeting: "Welcome! I'm Sarah, your medical cannabis specialist. I'm here to help you find the perfect products for your wellness needs. How can I assist you today?",
    gradient: 'from-blue-400 via-teal-400 to-green-400'
  },
  {
    id: 'alex',
    name: 'Alex',
    emoji: '🧑‍🎤',
    status: 'Vibe curator',
    greeting: "What's good! I'm Alex, here to help you find the perfect vibe. Whether you're looking to chill or get creative, I got you! What kind of experience are you after?",
    gradient: 'from-purple-400 via-pink-400 to-red-400'
  }
];

import { endpoints } from '../config/endpoints';
const API_BASE_URL = endpoints.base;

export default function ModernChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [selectedBudtender, setSelectedBudtender] = useState(budtenders[0]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);

  // Load messages from localStorage
  useEffect(() => {
    const savedMessages = localStorage.getItem('modern_chat_messages');
    const savedBudtender = localStorage.getItem('modern_chat_budtender');
    
    if (savedBudtender) {
      const budtender = budtenders.find(b => b.id === savedBudtender);
      if (budtender) setSelectedBudtender(budtender);
    }
    
    if (savedMessages) {
      try {
        const parsed = JSON.parse(savedMessages, (key, value) => {
          if (key === 'timestamp') return new Date(value);
          return value;
        });
        setMessages(parsed);
      } catch (error) {
        console.error('Error loading messages:', error);
      }
    }
    
    // Add initial greeting if no messages
    if (!savedMessages || JSON.parse(savedMessages).length === 0) {
      const greeting: Message = {
        id: Date.now().toString(),
        content: selectedBudtender.greeting,
        sender: 'assistant',
        timestamp: new Date(),
        personality: selectedBudtender.id
      };
      setMessages([greeting]);
    }
  }, []);

  // Save messages to localStorage
  useEffect(() => {
    if (messages.length > 0) {
      localStorage.setItem('modern_chat_messages', JSON.stringify(messages));
    }
    localStorage.setItem('modern_chat_budtender', selectedBudtender.id);
  }, [messages, selectedBudtender]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Send message mutation
  const sendMessageMutation = useMutation({
    mutationFn: async (message: string) => {
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message,
          session_id: `session_${Date.now()}`,
          personality: selectedBudtender.id,
          context: {
            mode: 'live',
            previous_messages: messages.slice(-5).map(m => ({
              role: m.sender,
              content: m.content
            }))
          }
        })
      });
      
      if (!response.ok) throw new Error('Failed to send message');
      return response.json();
    },
    onSuccess: (data) => {
      const aiMessage: Message = {
        id: Date.now().toString(),
        content: data.response || data.message || "Excellent! Based on what you're telling me, I have some ideas already. Let's dive deeper.",
        sender: 'assistant',
        timestamp: new Date(),
        personality: selectedBudtender.id,
        confidence: data.confidence,
        processingTime: data.processing_time_ms,
        version: data.model_version,
        metadata: data.metadata,
        quickActions: data.quick_actions || data.quickActions || [],
        products: data.products || []
      };
      setMessages(prev => [...prev, aiMessage]);
      setIsLoading(false);
    },
    onError: (error: any) => {
      setIsLoading(false);
      // Still provide a contextual response even on error
      const fallbackMessage: Message = {
        id: Date.now().toString(),
        content: "I understand what you're looking for! While I'm having a small connection issue, I'd recommend checking out our indica strains for relaxation or our sativa options for energy. What sounds better to you?",
        sender: 'assistant',
        timestamp: new Date(),
        personality: selectedBudtender.id,
        quickActions: [
          { id: '1', label: 'Show Indica Strains', value: 'Show me indica strains for relaxation', type: 'primary' },
          { id: '2', label: 'Show Sativa Options', value: 'Show me sativa strains for energy', type: 'primary' },
          { id: '3', label: 'Tell Me More', value: 'Tell me more about the differences', type: 'secondary' }
        ]
      };
      setMessages(prev => [...prev, fallbackMessage]);
    }
  });

  const handleSendMessage = (messageText?: string) => {
    const message = messageText || inputMessage.trim();
    if (!message) return;

    // Add user message
    const userMessage: Message = {
      id: `user_${Date.now()}`,
      content: message,
      sender: 'user',
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    // Send to AI
    sendMessageMutation.mutate(message);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const clearChat = () => {
    const greeting: Message = {
      id: Date.now().toString(),
      content: selectedBudtender.greeting,
      sender: 'assistant',
      timestamp: new Date(),
      personality: selectedBudtender.id
    };
    setMessages([greeting]);
    localStorage.removeItem('modern_chat_messages');
  };

  return (
    <div className="h-[calc(100vh-200px)] flex flex-col bg-gradient-to-br from-purple-900 via-pink-800 to-orange-700 rounded-3xl overflow-hidden shadow-2xl">
      {/* Header */}
      <div className={`bg-gradient-to-r ${selectedBudtender.gradient} p-5 shadow-lg relative overflow-hidden`}>
        {/* Background decoration */}
        <div className="absolute inset-0 bg-white/10 backdrop-blur-sm"></div>
        
        <div className="relative flex items-center justify-between">
          <button className="p-2 hover:bg-white/20 rounded-xl transition-colors text-white">
            <ChevronLeft className="w-5 h-5" />
          </button>
          
          <div className="flex flex-col items-center flex-1">
            {/* Avatar */}
            <div className="relative mb-2">
              <div className="w-20 h-20 bg-white/30 backdrop-blur-md rounded-full flex items-center justify-center text-4xl shadow-xl ring-4 ring-white/40">
                {selectedBudtender.emoji}
              </div>
              <div className="absolute bottom-1 right-1 w-5 h-5 bg-green-400 rounded-full border-3 border-white shadow-md"></div>
            </div>
            
            {/* Name and Status */}
            <h2 className="text-2xl font-bold text-white drop-shadow-lg">
              {selectedBudtender.name}
            </h2>
            <p className="text-sm text-white/90 flex items-center gap-2">
              <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
              {selectedBudtender.status}
            </p>
          </div>
          
          <button
            onClick={clearChat}
            className="p-2 hover:bg-white/20 rounded-xl transition-colors text-white"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Messages Container */}
      <div 
        ref={chatContainerRef}
        className="flex-1 overflow-y-auto px-4 py-6 space-y-4"
        style={{
          background: 'linear-gradient(to bottom, rgba(31, 29, 71, 0.95), rgba(31, 29, 71, 0.98))'
        }}
      >
        <AnimatePresence>
          {messages.map((message) => (
            <motion.div
              key={message.id}
              initial={{ opacity: 0, y: 20, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              transition={{ duration: 0.3 }}
              className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'} mb-4`}
            >
              <div className={`flex items-end gap-2 max-w-[85%] ${message.sender === 'user' ? 'flex-row-reverse' : ''}`}>
                {/* Avatar for assistant */}
                {message.sender === 'assistant' && (
                  <div className="w-8 h-8 bg-white/20 backdrop-blur-sm rounded-full flex items-center justify-center text-xl flex-shrink-0 mb-1">
                    {selectedBudtender.emoji}
                  </div>
                )}
                
                {/* Message Bubble */}
                <div>
                  <div className={`
                    px-5 py-3 rounded-2xl shadow-xl backdrop-blur-sm
                    ${message.sender === 'user' 
                      ? 'bg-gradient-to-r from-pink-500 to-purple-600 text-white rounded-br-sm' 
                      : 'bg-white/95 text-gray-800 rounded-bl-sm'
                    }
                  `}>
                    <p className="text-base leading-relaxed whitespace-pre-wrap">
                      {message.content}
                    </p>
                  </div>
                  
                  {/* Timestamp */}
                  <div className={`text-xs mt-1 px-2 ${message.sender === 'user' ? 'text-right' : 'text-left'}`}>
                    <span className="text-white/50">
                      {format(message.timestamp, 'hh:mm a')}
                    </span>
                  </div>
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Quick Actions */}
        {messages.length > 0 && messages[messages.length - 1].sender === 'assistant' && messages[messages.length - 1].quickActions && messages[messages.length - 1].quickActions!.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="flex flex-wrap gap-2 ml-10"
          >
            {messages[messages.length - 1].quickActions!.map((action) => (
              <button
                key={action.id}
                onClick={() => handleSendMessage(action.value)}
                className="px-4 py-2.5 bg-white/20 backdrop-blur-md text-white rounded-2xl text-sm font-medium hover:bg-white/30 transition-all transform hover:scale-105 border border-white/30 shadow-lg"
              >
                {action.icon && <span className="mr-2">{action.icon}</span>}
                {action.label}
              </button>
            ))}
          </motion.div>
        )}
        
        {/* Loading Indicator */}
        {isLoading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex justify-start"
          >
            <div className="flex items-end gap-2">
              <div className="w-8 h-8 bg-white/20 backdrop-blur-sm rounded-full flex items-center justify-center text-xl">
                {selectedBudtender.emoji}
              </div>
              <div className="px-5 py-3 bg-white/95 rounded-2xl rounded-bl-sm shadow-xl">
                <div className="flex gap-1.5">
                  <div className="w-2.5 h-2.5 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                  <div className="w-2.5 h-2.5 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                  <div className="w-2.5 h-2.5 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                </div>
              </div>
            </div>
          </motion.div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 bg-gray-900/95 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          {/* Input Field */}
          <div className="flex-1 relative">
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your message..."
              className="w-full px-5 py-3.5 bg-gray-800/70 text-white placeholder-gray-400 rounded-2xl focus:outline-none focus:ring-2 focus:ring-purple-500 transition-all backdrop-blur-sm"
              disabled={isLoading}
            />
          </div>
          
          {/* Voice Button */}
          <button
            onClick={() => toast.success('Voice input coming soon!')}
            className="p-3.5 bg-gray-800/70 hover:bg-gray-700/70 rounded-2xl transition-colors text-gray-400 backdrop-blur-sm"
          >
            <Mic className="w-5 h-5" />
          </button>
          
          {/* Send Button */}
          <button
            onClick={() => handleSendMessage()}
            disabled={!inputMessage.trim() || isLoading}
            className={`
              p-3.5 rounded-2xl transition-all transform
              ${inputMessage.trim() && !isLoading
                ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white hover:scale-105 shadow-xl'
                : 'bg-gray-800/50 text-gray-500 cursor-not-allowed'
              }
            `}
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
        
        {/* Budtender Switcher */}
        <div className="flex items-center justify-center gap-4 mt-3">
          {budtenders.map((budtender) => (
            <button
              key={budtender.id}
              onClick={() => {
                setSelectedBudtender(budtender);
                const switchMessage: Message = {
                  id: Date.now().toString(),
                  content: `Hey! ${budtender.name} here! ${budtender.emoji} How can I help you today?`,
                  sender: 'assistant',
                  timestamp: new Date(),
                  personality: budtender.id
                };
                setMessages(prev => [...prev, switchMessage]);
              }}
              className={`
                p-2 rounded-xl transition-all
                ${selectedBudtender.id === budtender.id 
                  ? 'bg-white/20 scale-110' 
                  : 'hover:bg-white/10'
                }
              `}
              title={budtender.name}
            >
              <span className="text-2xl">{budtender.emoji}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}