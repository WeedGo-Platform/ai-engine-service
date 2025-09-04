import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { format } from 'date-fns';
import { useQuery, useMutation } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { 
  MessageSquare, 
  Send,
  MessageCircle, 
  Clock, 
  User, 
  Bot, 
  Play,
  Pause,
  SkipForward,
  RotateCcw,
  History,
  Save,
  Download,
  ChevronRight,
  Calendar,
  Filter,
  TrendingUp,
  AlertCircle,
  CheckCircle,
  XCircle,
  Zap,
  BarChart3,
  GitBranch,
  Eye,
  EyeOff,
  RefreshCw,
  Layers,
  Settings,
  Loader2,
  Brain,
  Copy,
  Check
} from 'lucide-react';
import AILearningComparison from './AILearningComparison';
import GitStyleDiff from './GitStyleDiff';

interface QuickAction {
  id: string;
  label: string;
  value: string;
  icon?: string;
  type?: 'primary' | 'secondary' | 'info';
}

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

interface HistoricalConversation {
  id: string;
  session_id: string;
  customer_id?: string;
  messages: Array<{
    role: 'user' | 'assistant';
    content?: string;
    message?: string; // API might return 'message' instead of 'content'
    timestamp: string;
    confidence?: number;
    processing_time_ms?: number;
    quick_actions?: QuickAction[];
    quickActions?: QuickAction[];
  }>;
  start_time: string;
  end_time?: string;
  metadata?: {
    personality?: string;
    model_version?: string;
    total_messages?: number;
    avg_response_time?: number;
    satisfaction_score?: number;
  };
}

interface ReplayResult {
  message_id: string;
  original_response: string;
  new_response: string;
  confidence: number;
  processing_time_ms: number;
  differences?: string[];
  improvement_score?: number;
  model_version: string;
  timestamp: string;
}

interface ModelVersion {
  id: string;
  name: string;
  version: string;
  created_at: string;
  is_active: boolean;
  description?: string;
}

type ViewMode = 'live' | 'history' | 'replay' | 'comparison';

import { endpoints } from '../config/endpoints';
const API_BASE_URL = endpoints.base;

export default function UnifiedChatTestingHistory() {
  const [viewMode, setViewMode] = useState<ViewMode>('live');
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [selectedPersonality, setSelectedPersonality] = useState('friendly-budtender');
  const [sessionId, setSessionId] = useState<string>(`session_${Date.now()}`);
  
  // History state
  const [selectedConversation, setSelectedConversation] = useState<HistoricalConversation | null>(null);
  const [dateRange, setDateRange] = useState({
    start: format(new Date(Date.now() - 7 * 24 * 60 * 60 * 1000), 'yyyy-MM-dd'),
    end: format(new Date(), 'yyyy-MM-dd')
  });
  
  // Replay state
  const [isReplaying, setIsReplaying] = useState(false);
  const [replayIndex, setReplayIndex] = useState(0);
  const [replaySpeed, setReplaySpeed] = useState(1);
  const [replayResults, setReplayResults] = useState<ReplayResult[]>([]);
  const [compareMode, setCompareMode] = useState(false);
  
  // Model versions
  const [selectedVersions, setSelectedVersions] = useState<string[]>([]);
  const [isCopied, setIsCopied] = useState(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const replayIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const currentMessagesRef = useRef<Message[]>([]);
  const isReplayingRef = useRef<boolean>(false);
  const inputRef = useRef<HTMLInputElement>(null);

  // Fetch available personalities
  const { data: personalitiesData, isError: personalitiesError, isLoading: personalitiesLoading } = useQuery({
    queryKey: ['personalities'],
    queryFn: async () => {
      const response = await fetch(endpoints.ai.personalities);
      if (!response.ok) {
        throw new Error('Failed to fetch personalities');
      }
      const data = await response.json();
      return data;
    },
    retry: 1,
    retryDelay: 1000
  });
  
  const personalities = personalitiesData?.personalities || [];

  // Fetch conversation history
  const { data: conversationsData, refetch: refetchConversations } = useQuery({
    queryKey: ['conversations', dateRange],
    queryFn: async () => {
      const response = await fetch(
        `${endpoints.base}/conversations/history?start_date=${dateRange.start}&end_date=${dateRange.end}`
      );
      if (!response.ok) throw new Error('Failed to fetch conversations');
      const data = await response.json();
      // Handle both array and object response formats
      return data;
    }
  });
  
  // Extract conversations array from response
  const conversations = conversationsData?.conversations || [];

  // Fetch model versions
  const { data: modelVersions = [], isError: modelVersionsError } = useQuery({
    queryKey: ['model-versions'],
    queryFn: async () => {
      try {
        const response = await fetch(endpoints.models.versions);
        if (!response.ok) {
          console.warn('Model versions endpoint not available');
          return [];
        }
        const data = await response.json();
        return Array.isArray(data) ? data : [];
      } catch (error) {
        console.error('Error fetching model versions:', error);
        return [];
      }
    },
    retry: 1,
    retryDelay: 1000
  });

  // Send message mutation
  const sendMessageMutation = useMutation({
    mutationFn: async (message: string) => {
      // Get full personality data to send to API
      const fullPersonality = personalities.find(p => p.id === selectedPersonality);
      
      const response = await fetch(endpoints.chat.base, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message,
          session_id: sessionId,
          customer_id: `test_user_${Date.now()}`,
          budtender_personality: selectedPersonality,  // Send personality ID directly
          // Remove context wrapper - API expects flat structure
          mode: viewMode === 'replay' ? 'replay' : 'live',
          previous_messages: messages.slice(-5).map(m => ({
            role: m.sender,
            content: m.content
          }))
        })
      });
      
      if (!response.ok) throw new Error('Failed to send message');
      return response.json();
    },
    onSuccess: (data) => {
      const aiMessage: Message = {
        id: Date.now().toString(),
        content: data.message || data.response || 'I understand. How can I help you further?',
        sender: 'assistant',
        timestamp: new Date(),
        personality: selectedPersonality,
        confidence: data.confidence,
        processingTime: data.response_time_ms || data.processing_time_ms,
        version: data.model_version,
        metadata: data.metadata,
        quickActions: data.quick_actions || data.quickActions || [],
        products: data.products || []
      };
      setMessages(prev => [...prev, aiMessage]);
      
      // If we have products in the response, we could display them
      if (data.products && data.products.length > 0) {
        console.log('Products found:', data.products);
      }
    },
    onError: (error: any) => {
      const errorMessage = error?.message || 'Failed to get AI response';
      toast.error(errorMessage);
      console.error('Chat error:', error);
      
      // Add a system message about the error
      const errorMsg: Message = {
        id: Date.now().toString(),
        content: 'Sorry, I encountered an error processing your message. Please ensure the AI service is running and try again.',
        sender: 'assistant',
        timestamp: new Date(),
        personality: selectedPersonality,
        confidence: 0,
        metadata: { error: true }
      };
      setMessages(prev => [...prev, errorMsg]);
    }
  });

  // Replay conversation mutation - Feed exact historical messages to AI engine
  const replayConversationMutation = useMutation({
    mutationFn: async (userMessage: string) => {
      // Feed exact historical message from database to AI engine for comparison
      const response = await fetch(endpoints.chat.send, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMessage,
          session_id: `replay_${selectedConversation?.session_id}_${Date.now()}`,
          customer_id: `replay_${selectedConversation?.customer_id || 'user'}`,
          personality: selectedConversation?.metadata?.personality || selectedPersonality,
          context: {
            mode: 'replay',
            original_session_id: selectedConversation?.session_id,
            model_version: modelVersions.find(v => v.is_active)?.version || 'latest',
            comparison_enabled: true,
            // Include exact conversation context from database
            conversation_history: selectedConversation?.messages || []
          }
        })
      });
      
      if (!response.ok) throw new Error('Failed to replay message');
      return response.json();
    },
    onSuccess: (data, variables) => {
      console.log('=== REPLAY API SUCCESS ===');
      console.log('Response data:', data);
      console.log('Input message was:', variables);
      console.log('Current messages count before adding AI response:', currentMessagesRef.current.length);
      
      // Find the original response from the database conversation
      const originalResponse = findOriginalResponse(variables);
      console.log('Original response found:', originalResponse ? 'Yes' : 'No');
      
      // Create detailed comparison result for AI learning tracking
      const result: ReplayResult = {
        message_id: Date.now().toString(),
        original_response: originalResponse || '',
        new_response: data.message || data.response || '',
        confidence: data.confidence || 0,
        processing_time_ms: data.response_time_ms || data.processing_time_ms || 0,
        differences: analyzeDifferences(
          originalResponse || '',
          data.message || data.response || ''
        ),
        improvement_score: calculateImprovementScore(data, originalResponse),
        model_version: data.model_version || modelVersions.find(v => v.is_active)?.version || 'current',
        timestamp: new Date().toISOString()
      };
      
      setReplayResults(prev => [...prev, result]);
      
      // Remove loading indicator and add real AI response
      setMessages(prev => {
        console.log('Updating messages after AI response, current count:', prev.length);
        // Remove any loading messages
        const filtered = prev.filter(m => !m.metadata?.isLoading);
        console.log('After removing loading messages:', filtered.length);
        
        // Add the actual AI response with replay metadata
        const aiReplayMessage: Message = {
          id: `ai_replay_${Date.now()}`,
          content: data.message || data.response || '',
          sender: 'assistant',
          timestamp: new Date(),
          confidence: data.confidence,
          processingTime: data.response_time_ms,
          metadata: { 
            isReplay: true,
            replayVersion: 'v2',
            originalResponse: originalResponse,
            modelVersion: result.model_version
          },
          quickActions: data.quick_actions || [],
          products: data.products || []
        };
        
        const finalMessages = [...filtered, aiReplayMessage];
        console.log('Final messages after adding AI response:', finalMessages.length);
        console.log('AI response added:', aiReplayMessage.content.substring(0, 50) + '...');
        return finalMessages;
      });
      
      // Log the comparison for learning tracking
      console.log('AI Learning Comparison:', {
        userMessage: variables,
        originalResponse,
        newResponse: data.message || data.response,
        confidenceChange: data.confidence - (selectedConversation?.messages.find((m: any) => m.message === originalResponse)?.confidence || 0),
        modelVersion: result.model_version
      });
    },
    onError: (error, variables) => {
      console.error('=== REPLAY API ERROR ===');
      console.error('Error:', error);
      console.error('Failed message:', variables);
      
      // Remove loading indicator
      setMessages(prev => {
        // Remove any loading messages
        const filtered = prev.filter(m => !m.metadata?.isLoading);
        
        // Add error message in chat as AI would normally do
        const errorMessage: Message = {
          id: `error_${Date.now()}`,
          content: 'Sorry, I encountered an error processing your message. Please ensure the AI service is running and try again.',
          sender: 'assistant',
          timestamp: new Date(),
          confidence: 0,
          metadata: { 
            isReplay: true,
            error: true,
            errorDetails: error.message || 'AI service unavailable'
          }
        };
        
        return [...filtered, errorMessage];
      });
      
      // Log the error
      console.error('Replay error for message:', variables);
      console.error('Error details:', error);
      
      // Don't show toast for each message, error is shown in chat
      // Only show toast if it's a critical error
      if (error.message?.includes('network') || error.message?.includes('Network')) {
        toast.error('Network error: Cannot connect to AI service');
      }
    }
  });

  // Helper functions
  const findOriginalResponse = (userMessage: string): string | undefined => {
    if (!selectedConversation) return undefined;
    
    // Find the user message in the conversation using correct field names
    const userMsgIndex = selectedConversation.messages.findIndex(
      (m: any) => m.sender === 'customer' && (m.message === userMessage || m.content === userMessage)
    );
    
    if (userMsgIndex >= 0 && userMsgIndex < selectedConversation.messages.length - 1) {
      const nextMsg = selectedConversation.messages[userMsgIndex + 1];
      // Check if next message is from budtender (AI)
      if (nextMsg.sender === 'budtender') {
        return nextMsg.message || nextMsg.content;
      }
    }
    
    return undefined;
  };

  const analyzeDifferences = (original: string, new_response: string): string[] => {
    const differences: string[] = [];
    
    // Simple difference analysis - in production, use a proper diff algorithm
    if (original.length !== new_response.length) {
      differences.push(`Length changed: ${original.length} → ${new_response.length} characters`);
    }
    
    // Check for new keywords
    const originalWords = new Set(original.toLowerCase().split(/\s+/));
    const newWords = new Set(new_response.toLowerCase().split(/\s+/));
    
    const addedWords = [...newWords].filter(w => !originalWords.has(w));
    const removedWords = [...originalWords].filter(w => !newWords.has(w));
    
    if (addedWords.length > 0) {
      differences.push(`Added keywords: ${addedWords.slice(0, 5).join(', ')}`);
    }
    if (removedWords.length > 0) {
      differences.push(`Removed keywords: ${removedWords.slice(0, 5).join(', ')}`);
    }
    
    return differences;
  };

  const calculateImprovementScore = (data: any, originalResponse?: string): number => {
    // Calculate improvement score based on confidence, response time, and response quality
    const baseScore = (data.confidence || 0) * 100;
    const timeBonus = data.processing_time_ms < 1000 ? 10 : 0;
    
    // Additional scoring based on response comparison if original exists
    let qualityBonus = 0;
    if (originalResponse && data.response) {
      // Check if new response is more comprehensive
      const newLength = (data.response || data.message || '').length;
      const oldLength = originalResponse.length;
      if (newLength > oldLength * 1.1) qualityBonus += 5; // More detailed response
      
      // Check for product recommendations
      if (data.products && data.products.length > 0) qualityBonus += 10;
    }
    
    return Math.min(100, baseScore + timeBonus + qualityBonus);
  };

  const scrollToBottom = () => {
    if (messagesEndRef.current && messages.length > 0) {
      console.log('Scrolling to bottom with', messages.length, 'messages');
      // Use a small delay to ensure DOM has updated
      setTimeout(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
      }, 100);
    }
  };

  useEffect(() => {
    // Keep ref in sync with messages state
    currentMessagesRef.current = messages;
    console.log('=== MESSAGES STATE UPDATED ===');
    console.log('Count:', messages.length);
    console.log('First message:', messages[0]);
    console.log('View mode:', viewMode);
    console.log('Is replaying:', isReplaying);
    console.log('Stack trace:', new Error().stack);
    
    // Only scroll if we have messages
    if (messages.length > 0) {
      scrollToBottom();
    }
  }, [messages]);

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // Handle sending a message (either from input or quick action)
  const handleSendMessage = async (messageText: string) => {
    if (!messageText.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: messageText,
      sender: 'user',
      timestamp: new Date(),
      version: modelVersions.find(v => v.is_active)?.version
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      await sendMessageMutation.mutateAsync(messageText);
    } catch (error) {
      console.error('Error sending message:', error);
    } finally {
      setIsLoading(false);
      // Focus input after quick action sends message
      setTimeout(() => {
        inputRef.current?.focus();
      }, 100);
    }
  };

  const copyChat = () => {
    const chatText = messages.map(msg => {
      const timestamp = format(msg.timestamp, 'HH:mm:ss');
      const sender = msg.sender === 'user' ? 'User' : 'Assistant';
      return `[${timestamp}] ${sender}: ${msg.content}`;
    }).join('\n');
    
    navigator.clipboard.writeText(chatText).then(() => {
      setIsCopied(true);
      toast.success('Chat copied to clipboard!');
      setTimeout(() => setIsCopied(false), 2000);
    }).catch(() => {
      toast.error('Failed to copy chat');
    });
  };

  const sendMessage = async () => {
    if (!inputMessage.trim()) return;
    
    await handleSendMessage(inputMessage);
    setInputMessage(''); // Clear input only for manual messages
    
    // Keep focus on input after sending
    setTimeout(() => {
      inputRef.current?.focus();
    }, 100);
  };

  const startReplay = async () => {
    try {
      console.log('=== START REPLAY FUNCTION CALLED ===');
      console.log('selectedConversation:', selectedConversation);
      console.log('viewMode:', viewMode);
      console.log('isReplaying:', isReplaying);
      console.log('messages.length:', messages.length);
      
      if (!selectedConversation) {
        console.log('ERROR: No conversation selected');
        toast.error('Please select a conversation from the left sidebar');
        return;
      }
    
    console.log('Selected conversation ID:', selectedConversation.session_id);
    console.log('Conversation messages:', selectedConversation.messages);
    
    // Clear the message window completely for replay
    console.log('Clearing messages for replay');
    console.log('Previous messages count:', messages.length);
    
    // Add a status message before clearing
    toast('Starting replay - clearing conversation and replaying messages sequentially...', {
      icon: '🔄',
      duration: 3000
    });
    
    setMessages([]);
    setIsReplaying(true);
    isReplayingRef.current = true; // Set ref to track replaying state
    setReplayJustFinished(false); // Reset the flag
    setReplayIndex(0);
    setReplayResults([]);
    
    // Add a slight delay to ensure state is updated
    await new Promise(resolve => setTimeout(resolve, 50));
    
    // Force update to ensure clean state
    await new Promise(resolve => setTimeout(resolve, 100));
    
    // Extract all messages from the conversation in order
    const allMessages = selectedConversation.messages;
    console.log('All messages:', allMessages);
    
    const userMessages = allMessages.filter((m: any) => m.sender === 'customer');
    console.log('Filtered customer messages:', userMessages);
    
    if (userMessages.length === 0) {
      console.log('ERROR: No customer messages found');
      toast.error('No customer messages found in selected conversation');
      setIsReplaying(false);
      return;
    }
    
    console.log(`Starting replay of conversation ${selectedConversation.session_id}`);
    console.log(`Total messages to replay: ${userMessages.length}`);
    
    // Process messages sequentially - mimicking real chat behavior
    console.log('STARTING FOR LOOP - userMessages:', userMessages.length);
    
    for (let i = 0; i < userMessages.length; i++) {
      console.log(`\n=== REPLAYING MESSAGE ${i + 1}/${userMessages.length} ===`);
      console.log('isReplayingRef.current:', isReplayingRef.current);
      
      // Check if still replaying using ref instead of state
      if (!isReplayingRef.current) {
        console.log('Replay stopped by user');
        break;
      }
      
      setReplayIndex(i);
      const userMsg = userMessages[i];
      const messageContent = userMsg.message || userMsg.content || '';
      
      console.log('User message to replay:', messageContent);
      console.log('Original message object:', userMsg);
      
      if (!messageContent || messageContent.trim() === '') {
        console.warn(`Skipping empty message at index ${i}`);
        continue;
      }
      
      try {
        console.log('Creating user replay message...');
        // Add the user message to the chat window with replay indicator
        const userReplayMessage: Message = {
          id: `replay_user_${Date.now()}_${i}`,
          content: messageContent,
          sender: 'user',
          timestamp: new Date(),
          metadata: { 
            isReplay: true,
            replayVersion: 'v2',
            originalMessageId: userMsg.id,
            replayIndex: i + 1,
            totalReplays: userMessages.length
          }
        };
        
        // Add user message immediately
        console.log('Adding user message to UI, current messages count:', currentMessagesRef.current.length);
        console.log('Messages state value:', messages.length);
        setMessages(prev => {
          console.log('Previous messages:', prev.length);
          const updated = [...prev, userReplayMessage];
          console.log('Updated messages:', updated.length);
          return updated;
        });
        
        // Show loading indicator for AI processing
        const loadingMessageId = `loading_${i}_${Date.now()}`;
        const loadingMessage: Message = {
          id: loadingMessageId,
          content: '🤖 Processing...',
          sender: 'assistant',
          timestamp: new Date(),
          metadata: { 
            isLoading: true,
            isReplay: true 
          }
        };
        console.log('Adding loading message');
        setMessages(prev => {
          const withLoading = [...prev, loadingMessage];
          console.log('Messages with loading:', withLoading.length);
          return withLoading;
        });
        
        // Small delay to show the user message before processing
        await new Promise(resolve => setTimeout(resolve, 500));
        
        console.log(`Replaying message ${i + 1}/${userMessages.length}: "${messageContent.substring(0, 50)}..."`);
        
        // Send to AI and wait for response
        console.log('Sending message to AI API...');
        await replayConversationMutation.mutateAsync(messageContent);
        console.log('AI response processed successfully');
        
        // Natural pause between messages based on replay speed
        await new Promise(resolve => setTimeout(resolve, 2000 / replaySpeed));
        
      } catch (error) {
        console.error(`Error replaying message ${i + 1}:`, error);
        // Error is handled in mutation's onError, which removes loading and adds error message
        // Continue to next message after a pause
        await new Promise(resolve => setTimeout(resolve, 2000 / replaySpeed));
      }
    }
    
    console.log('=== REPLAY COMPLETED ===');
    console.log('Final messages count:', messages.length);
    console.log('Messages in ref:', currentMessagesRef.current.length);
    
    setIsReplaying(false);
    isReplayingRef.current = false; // Update ref
    setReplayJustFinished(true); // Set flag to prevent clearing
    toast.success(`Replay completed! Processed ${userMessages.length} messages`);
    
    // Reset the flag after a short delay to allow future operations
    setTimeout(() => {
      setReplayJustFinished(false);
    }, 1000);
    
    // Log summary of learning comparison
    if (replayResults.length > 0) {
      const avgImprovement = replayResults.reduce((acc, r) => acc + (r.improvement_score || 0), 0) / replayResults.length;
      console.log('AI Learning Summary:', {
        totalMessages: userMessages.length,
        successfulReplays: replayResults.length,
        averageImprovement: avgImprovement.toFixed(1) + '%'
      });
    }
    } catch (error) {
      console.error('=== ERROR IN START REPLAY ===');
      console.error('Error details:', error);
      console.error('Stack trace:', (error as any).stack);
      toast.error('Failed to start replay: ' + (error as any).message);
      setIsReplaying(false);
      isReplayingRef.current = false;
    }
  };

  const stopReplay = () => {
    setIsReplaying(false);
    isReplayingRef.current = false; // Update ref
    if (replayIntervalRef.current) {
      clearInterval(replayIntervalRef.current);
      replayIntervalRef.current = null;
    }
  };

  const exportResults = () => {
    const exportData = {
      conversation: selectedConversation,
      replay_results: replayResults,
      model_versions: modelVersions.filter(v => selectedVersions.includes(v.id)),
      timestamp: new Date().toISOString(),
      metadata: {
        total_messages: replayResults.length,
        avg_confidence: replayResults.reduce((acc, r) => acc + r.confidence, 0) / replayResults.length,
        avg_processing_time: replayResults.reduce((acc, r) => acc + r.processing_time_ms, 0) / replayResults.length
      }
    };
    
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `replay-results-${selectedConversation?.session_id}-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Track if we've just finished replaying to prevent clearing
  const [replayJustFinished, setReplayJustFinished] = useState(false);

  // Convert API conversation to display messages
  useEffect(() => {
    console.log('=== VIEWMODE/CONVERSATION EFFECT RUNNING ===');
    console.log('View mode:', viewMode);
    console.log('Selected conversation:', selectedConversation?.session_id);
    console.log('Current messages count:', messages.length);
    console.log('Is replaying?', isReplaying);
    console.log('isReplayingRef.current?', isReplayingRef.current);
    console.log('Replay just finished?', replayJustFinished);
    
    // SKIP ONLY if actively replaying (not just in replay mode)
    if (isReplaying || isReplayingRef.current) {
      console.log('SKIPPING - currently replaying');
      return;
    }
    
    // Populate messages in both history AND replay mode (when not actively replaying)
    if ((viewMode === 'history' || viewMode === 'replay') && selectedConversation) {
      console.log('Populating view with conversation:', selectedConversation);
      console.log('First message:', selectedConversation.messages[0]);
      
      const convertedMessages: Message[] = selectedConversation.messages.map((msg: any, idx: number) => ({
        id: `${selectedConversation.session_id}_${idx}`,
        content: msg.message || msg.content || '', // Use 'message' field from API
        sender: msg.sender === 'customer' ? 'user' : 'assistant', // Map 'customer' to 'user' and 'budtender' to 'assistant'
        timestamp: new Date(msg.timestamp),
        confidence: msg.confidence,
        processingTime: msg.processing_time_ms,
        version: selectedConversation.metadata?.model_version,
        quickActions: msg.quick_actions || msg.quickActions || [],
        products: msg.products || [], // Include products from API
        // Add a flag to indicate these are historical messages
        metadata: { isHistorical: true }
      }));
      setMessages(convertedMessages);
    } else if (viewMode === 'live' && !isReplaying && !isReplayingRef.current) {
      // Clear messages when switching to live mode ONLY if not replaying
      setMessages([]);
    }
  }, [selectedConversation, viewMode, isReplaying]);

  return (
    <div className="bg-gradient-to-br from-purple-900 via-pink-800 to-orange-700 rounded-3xl shadow-2xl h-[calc(100vh-200px)] flex flex-col overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-pink-400 via-purple-400 to-indigo-400 p-5 shadow-lg backdrop-blur-sm">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-white/30 backdrop-blur-sm rounded-full flex items-center justify-center shadow-xl">
              <MessageSquare className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white drop-shadow-lg">Unified Chat Testing & History</h2>
              <p className="text-sm text-white/90">Test, replay, and analyze conversation evolution</p>
            </div>
            
            {/* Selected Personality Avatar - Only show in live mode */}
            {viewMode === 'live' && personalities.length > 0 && (
              <div className="flex items-center gap-3 ml-auto mr-4">
                <div className="text-right">
                  <p className="text-xs text-white/70">Active Budtender</p>
                  <p className="text-sm font-medium text-white">
                    {personalities.find(p => p.id === selectedPersonality)?.name || 'Select'}
                  </p>
                </div>
                <div className="w-12 h-12 bg-white rounded-full flex items-center justify-center overflow-hidden shadow-xl">
                  {(() => {
                    const selectedP = personalities.find(p => p.id === selectedPersonality);
                    if (selectedP?.avatar) {
                      return <img src={selectedP.avatar} alt={selectedP.name} className="w-full h-full object-cover" />;
                    } else if (selectedP?.emoji) {
                      return <span className="text-2xl">{selectedP.emoji}</span>;
                    } else {
                      return <User className="w-6 h-6 text-gray-400" />;
                    }
                  })()}
                </div>
              </div>
            )}
          </div>
          
          {/* Action Buttons and View Mode Selector */}
          <div className="flex items-center gap-3">
            {/* Copy Chat Button */}
            <button
              onClick={copyChat}
              disabled={messages.length === 0}
              className={`
                px-3 py-2 rounded-xl flex items-center gap-2 transition-all
                ${messages.length > 0 
                  ? 'bg-white/20 backdrop-blur-sm hover:bg-white/30 text-white' 
                  : 'bg-white/10 text-white/50 cursor-not-allowed'}
              `}
              title="Copy chat to clipboard"
            >
              {isCopied ? (
                <>
                  <Check className="w-4 h-4" />
                  <span className="text-sm font-medium">Copied!</span>
                </>
              ) : (
                <>
                  <Copy className="w-4 h-4" />
                  <span className="text-sm font-medium">Copy Chat</span>
                </>
              )}
            </button>
            
            {/* View Mode Selector */}
            <div className="flex bg-white/20 backdrop-blur-sm rounded-xl p-1">
            {(['live', 'history', 'replay', 'comparison'] as ViewMode[]).map((mode) => (
              <button
                key={mode}
                onClick={() => setViewMode(mode)}
                className={`
                  px-4 py-2 rounded-lg text-sm font-medium capitalize transition-all
                  ${viewMode === mode 
                    ? 'bg-white text-purple-700 shadow-lg' 
                    : 'text-white/90 hover:text-white hover:bg-white/10'
                  }
                `}
              >
                {mode === 'live' && <Zap className="w-4 h-4 inline mr-1" />}
                {mode === 'history' && <History className="w-4 h-4 inline mr-1" />}
                {mode === 'replay' && <RefreshCw className="w-4 h-4 inline mr-1" />}
                {mode === 'comparison' && <GitBranch className="w-4 h-4 inline mr-1" />}
                {mode}
              </button>
            ))}
            </div>
          </div>
        </div>

        {/* Mode-specific Controls */}
        {viewMode === 'replay' && (
          <div className="mt-4">
            {/* Show selected conversation info */}
            {selectedConversation && !isReplaying && (
              <div className="mb-3 p-3 bg-white/30 backdrop-blur-sm rounded-xl">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-sm font-medium text-white">
                      Selected: {selectedConversation.session_id}
                    </div>
                    <div className="text-xs text-white/80 mt-1">
                      {selectedConversation.messages?.length || 0} messages • 
                      {' '}{selectedConversation.messages?.filter((m: any) => m.sender === 'customer').length || 0} from customer
                    </div>
                  </div>
                  {messages.length > 0 && messages[0].metadata?.isHistorical && (
                    <div className="text-xs text-white/90">
                      <span className="px-2 py-1 bg-purple-600/30 rounded-full">
                        ✓ Viewing full conversation
                      </span>
                    </div>
                  )}
                </div>
              </div>
            )}
            
            <div className="flex items-center justify-between p-3 bg-white/20 backdrop-blur-sm rounded-xl">
              <div className="flex items-center gap-3">
                {!isReplaying ? (
                  <button
                    onClick={() => {
                      console.log('=== BUTTON CLICKED ===');
                      console.log('selectedConversation:', selectedConversation);
                      console.log('isReplaying:', isReplaying);
                      console.log('viewMode:', viewMode);
                      console.log('Calling startReplay...');
                      startReplay().then(() => {
                        console.log('StartReplay promise resolved');
                      }).catch((err) => {
                        console.error('StartReplay promise rejected:', err);
                      });
                    }}
                    disabled={!selectedConversation}
                    className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed transition-all transform hover:scale-105"
                  >
                    <Play className="w-4 h-4" />
                    {selectedConversation ? 'Start Replay' : 'Select a Conversation'}
                  </button>
                ) : (
                  <button
                    onClick={stopReplay}
                    className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                  >
                    <Pause className="w-4 h-4" />
                    Stop
                  </button>
                )}
              
              <div className="flex items-center gap-2">
                <span className="text-sm text-zinc-600">Speed:</span>
                <select 
                  value={replaySpeed}
                  onChange={(e) => setReplaySpeed(Number(e.target.value))}
                  className="px-2 py-1 border border-zinc-200 rounded text-sm"
                  disabled={isReplaying}
                >
                  <option value={0.5}>0.5x</option>
                  <option value={1}>1x</option>
                  <option value={2}>2x</option>
                </select>
              </div>

              {isReplaying && (
                <div className="flex items-center gap-2">
                  <Loader2 className="w-4 h-4 text-purple-600 animate-spin" />
                  <span className="text-sm text-purple-700">
                    Replaying message {replayIndex + 1} of {selectedConversation?.messages.filter((m: any) => m.sender === 'customer').length || 0}
                  </span>
                </div>
              )}
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => setCompareMode(!compareMode)}
                className={`
                  flex items-center gap-2 px-3 py-1.5 rounded-lg transition-colors
                  ${compareMode 
                    ? 'bg-purple-600 text-white' 
                    : 'bg-white text-purple-600 border border-purple-300 hover:bg-purple-50'
                  }
                `}
              >
                {compareMode ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                {compareMode ? 'Hide' : 'Show'} Comparison
              </button>
              
              <button
                onClick={exportResults}
                disabled={replayResults.length === 0}
                className="flex items-center gap-2 px-3 py-1.5 bg-white text-zinc-700 border border-zinc-300 rounded-lg hover:bg-zinc-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <Download className="w-4 h-4" />
                Export
              </button>
            </div>
          </div>
          </div>
        )}

        {viewMode === 'comparison' && (
          <div className="mt-4 p-3 bg-blue-50 rounded-lg">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="text-sm font-medium text-blue-900">Select Model Versions:</span>
                <div className="flex gap-2">
                  {modelVersions.map((version) => (
                    <label key={version.id} className="flex items-center gap-1">
                      <input
                        type="checkbox"
                        checked={selectedVersions.includes(version.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedVersions([...selectedVersions, version.id]);
                          } else {
                            setSelectedVersions(selectedVersions.filter(v => v !== version.id));
                          }
                        }}
                        className="rounded text-blue-600"
                      />
                      <span className="text-sm text-zinc-700">{version.version}</span>
                      {version.is_active && (
                        <span className="text-xs text-green-600">(active)</span>
                      )}
                    </label>
                  ))}
                </div>
              </div>
              <button className="text-sm text-blue-600 hover:text-blue-700">
                <Settings className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar for History/Conversations */}
        {(viewMode === 'history' || viewMode === 'replay') && (
          <div className="w-80 border-r border-zinc-200 overflow-y-auto">
            <div className="p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-medium text-zinc-900">Conversations</h3>
                <button 
                  onClick={() => refetchConversations()}
                  className="text-zinc-500 hover:text-zinc-700"
                >
                  <RefreshCw className="w-4 h-4" />
                </button>
              </div>
              
              {/* Date Range Filter */}
              <div className="flex gap-2 mb-4">
                <input
                  type="date"
                  value={dateRange.start}
                  onChange={(e) => setDateRange(prev => ({ ...prev, start: e.target.value }))}
                  className="flex-1 px-2 py-1 text-sm border border-zinc-200 rounded"
                />
                <input
                  type="date"
                  value={dateRange.end}
                  onChange={(e) => setDateRange(prev => ({ ...prev, end: e.target.value }))}
                  className="flex-1 px-2 py-1 text-sm border border-zinc-200 rounded"
                />
              </div>
              
              <div className="space-y-2">
                {conversations.length === 0 ? (
                  <div className="text-center py-8 text-zinc-500">
                    No conversations found
                  </div>
                ) : (
                  conversations.map((conv: HistoricalConversation) => (
                    <motion.div
                      key={conv.id}
                      whileHover={{ scale: 1.02 }}
                      onClick={() => {
                        console.log('=== CONVERSATION SELECTED ===');
                        console.log('Selected conversation:', conv);
                        console.log('Session ID:', conv.session_id);
                        console.log('Messages count:', conv.messages?.length);
                        console.log('Current viewMode:', viewMode);
                        setSelectedConversation(conv);
                        
                        // DON'T clear messages when selecting conversation in replay mode
                        // Let the Start Replay button handle clearing
                        if (viewMode === 'replay') {
                          console.log('In replay mode - conversation selected');
                          console.log('Is currently replaying?', isReplaying);
                          // Don't clear messages here
                        }
                      }}
                      className={`
                        p-3 rounded-lg cursor-pointer transition-all
                        ${selectedConversation?.id === conv.id 
                          ? 'bg-blue-50 border border-blue-200' 
                          : 'bg-zinc-50 hover:bg-zinc-100'
                        }
                      `}
                    >
                      <div className="flex items-start justify-between mb-1">
                        <div className="flex items-center gap-2">
                          <User className="w-4 h-4 text-zinc-500" />
                          <span className="text-sm font-medium text-zinc-900">
                            {conv.customer_id || 'Anonymous'}
                          </span>
                        </div>
                        <span className="text-xs text-zinc-500">
                          {format(new Date(conv.start_time), 'MMM d')}
                        </span>
                      </div>
                      <div className="text-xs text-zinc-600 mb-2">
                        {format(new Date(conv.start_time), 'HH:mm')}
                        {conv.end_time && ` - ${format(new Date(conv.end_time), 'HH:mm')}`}
                      </div>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3 text-xs">
                          <span className="flex items-center gap-1">
                            <MessageSquare className="w-3 h-3" />
                            {conv.messages.length}
                          </span>
                          {conv.metadata?.avg_response_time && (
                            <span className="flex items-center gap-1">
                              <Clock className="w-3 h-3" />
                              {(conv.metadata.avg_response_time / 1000).toFixed(1)}s
                            </span>
                          )}
                        </div>
                        {conv.metadata?.satisfaction_score && (
                          <div className="flex items-center gap-1">
                            <span className="text-xs text-yellow-600">★</span>
                            <span className="text-xs text-zinc-600">
                              {conv.metadata.satisfaction_score.toFixed(1)}
                            </span>
                          </div>
                        )}
                      </div>
                    </motion.div>
                  ))
                )}
              </div>
            </div>
          </div>
        )}

        {/* Chat Area */}
        <div className="flex-1 flex flex-col bg-gradient-to-b from-gray-900/95 to-indigo-900/95 backdrop-blur-sm">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-6">
            {messages.length === 0 ? (
              <div className="text-center py-12 text-white/70">
                {viewMode === 'live' 
                  ? 'Start a conversation to test the AI'
                  : 'Select a conversation to view messages'}
              </div>
            ) : (
              messages.map((message, index) => (
                <div key={message.id}>
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'} mb-4`}
                  >
                    <div className={`
                      max-w-2xl px-5 py-3 rounded-2xl shadow-xl backdrop-blur-sm
                      ${message.sender === 'user' 
                        ? 'bg-gradient-to-r from-pink-500 to-purple-600 text-white rounded-br-sm' 
                        : 'bg-white/95 text-gray-800 rounded-bl-sm'
                      }
                    `}>
                      <div className="flex items-start gap-3">
                        {message.sender === 'assistant' && (
                          <div className="w-8 h-8 bg-white/20 backdrop-blur-sm rounded-full flex items-center justify-center overflow-hidden">
                            {(() => {
                              const personality = personalities?.find(p => p.id === selectedPersonality);
                              if (personality?.avatar) {
                                return <img src={personality.avatar} alt={personality.name} className="w-full h-full object-cover" />;
                              } else if (personality?.emoji) {
                                return <span className="text-xl">{personality.emoji}</span>;
                              } else {
                                return <span className="text-xl">🤖</span>;
                              }
                            })()}
                          </div>
                        )}
                        <div className="flex-1">
                          {/* Replay indicator */}
                          {message.metadata?.isReplay && (
                            <div className="mb-2">
                              <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-purple-600/20 text-purple-300 text-xs rounded-full">
                                <RefreshCw className="w-3 h-3" />
                                Replay {message.metadata.replayIndex && message.metadata.totalReplays && 
                                  `${message.metadata.replayIndex}/${message.metadata.totalReplays}`}
                                {message.metadata.replayVersion && ` • ${message.metadata.replayVersion}`}
                              </span>
                            </div>
                          )}
                          
                          {/* Loading indicator for AI processing */}
                          {message.metadata?.isLoading ? (
                            <div className="flex items-center gap-2">
                              <Loader2 className="w-4 h-4 animate-spin" />
                              <span className="text-sm opacity-70">AI is thinking...</span>
                            </div>
                          ) : (
                            <p className="text-base leading-relaxed">{message.content}</p>
                          )}
                          
                          {/* Product Cards */}
                          {message.products && message.products.length > 0 && (
                            <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-3">
                              {message.products.map((product: any, idx: number) => (
                                <div key={product.id || idx} className="bg-zinc-800 border border-zinc-700 rounded-lg overflow-hidden hover:border-zinc-600 transition-colors">
                                  {/* Product Image */}
                                  {(product.image || product.image_url) && (
                                    <div className="h-32 bg-zinc-900 relative">
                                      <img 
                                        src={product.image || product.image_url}
                                        alt={product.product_name}
                                        className="w-full h-full object-cover"
                                        onError={(e) => {
                                          e.currentTarget.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 24 24" fill="none" stroke="%23a1a1aa" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"%3E%3Crect x="3" y="3" width="18" height="18" rx="2" ry="2"%3E%3C/rect%3E%3Ccircle cx="8.5" cy="8.5" r="1.5"%3E%3C/circle%3E%3Cpolyline points="21 15 16 10 5 21"%3E%3C/polyline%3E%3C/svg%3E';
                                        }}
                                      />
                                      {product.category && (
                                        <span className="absolute top-2 left-2 px-2 py-1 bg-black/70 text-white text-xs rounded">
                                          {product.category}
                                        </span>
                                      )}
                                    </div>
                                  )}
                                  
                                  {/* Product Details */}
                                  <div className="p-3">
                                    <h4 className="font-medium text-zinc-100 text-sm mb-1">
                                      {product.product_name}
                                    </h4>
                                    {product.brand && (
                                      <p className="text-xs text-zinc-400 mb-2">{product.brand}</p>
                                    )}
                                    
                                    {/* Product Info Grid */}
                                    <div className="grid grid-cols-2 gap-2 mb-2 text-xs">
                                      {product.size && (
                                        <div>
                                          <span className="text-zinc-500">Size:</span>
                                          <span className="ml-1 text-zinc-300">{product.size}</span>
                                        </div>
                                      )}
                                      {product.thc !== undefined && (
                                        <div>
                                          <span className="text-zinc-500">THC:</span>
                                          <span className="ml-1 text-zinc-300">{product.thc}%</span>
                                        </div>
                                      )}
                                      {product.cbd !== undefined && (
                                        <div>
                                          <span className="text-zinc-500">CBD:</span>
                                          <span className="ml-1 text-zinc-300">{product.cbd}%</span>
                                        </div>
                                      )}
                                    </div>
                                    
                                    {/* Price */}
                                    <div className="flex items-center justify-between">
                                      <span className="text-base font-bold text-emerald-400">
                                        ${product.price?.toFixed(2) || '0.00'}
                                      </span>
                                    </div>
                                  </div>
                                </div>
                              ))}
                            </div>
                          )}
                          
                          {/* Timestamp */}
                          <div className="text-xs mt-2 opacity-60">
                            {format(message.timestamp, 'hh:mm a')}
                          </div>
                          
                          {/* Metadata for AI responses */}
                          {message.sender === 'assistant' && !message.metadata?.isLoading && (
                            <div className="flex items-center gap-3 mt-2 text-xs opacity-70">
                              {message.confidence && (
                                <span>Confidence: {(message.confidence * 100).toFixed(0)}%</span>
                              )}
                              {message.processingTime && (
                                <span>{(message.processingTime / 1000).toFixed(1)}s</span>
                              )}
                              {message.metadata?.modelVersion && message.metadata.modelVersion !== 'unavailable' && (
                                <span>Model: {message.metadata.modelVersion}</span>
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </motion.div>

                  {/* Quick Actions */}
                  {message.sender === 'assistant' && message.quickActions && message.quickActions.length > 0 && (
                    <motion.div
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="flex justify-start mt-2 ml-8"
                    >
                      <div className="flex flex-wrap gap-2">
                        {message.quickActions.map((action) => (
                          <button
                            key={action.id}
                            onClick={() => {
                              // Send message directly without populating input
                              handleSendMessage(action.value);
                            }}
                            className={`
                              px-3 py-1.5 rounded-full text-xs font-medium
                              transition-all duration-200 hover:scale-105
                              ${action.type === 'primary' 
                                ? 'bg-blue-100 text-blue-700 hover:bg-blue-200 border border-blue-300' 
                                : action.type === 'info'
                                ? 'bg-purple-100 text-purple-700 hover:bg-purple-200 border border-purple-300'
                                : 'bg-zinc-100 text-zinc-700 hover:bg-zinc-200 border border-zinc-300'
                              }
                            `}
                          >
                            {action.icon && <span className="mr-1">{action.icon}</span>}
                            {action.label}
                          </button>
                        ))}
                      </div>
                    </motion.div>
                  )}

                  {/* Replay Comparison */}
                  {viewMode === 'replay' && compareMode && (
                    <>
                      {replayResults.map((result) => {
                        // Match replay result to original message
                        const originalMsg = selectedConversation?.messages.find(
                          (m, idx) => 
                            m.role === 'user' && 
                            m.content === message.content &&
                            idx < selectedConversation.messages.length - 1
                        );
                        
                        if (originalMsg && result.original_response) {
                          const improvement = result.improvement_score || 0;
                          return (
                            <motion.div 
                              key={result.message_id}
                              initial={{ opacity: 0, height: 0 }}
                              animate={{ opacity: 1, height: 'auto' }}
                              className="mt-3 ml-12 p-3 bg-purple-50 rounded-lg border border-purple-200"
                            >
                              <div className="text-xs font-medium text-purple-900 mb-2">
                                Replay Result {result.model_version !== 'unavailable' ? `(v${result.model_version})` : ''}
                              </div>
                              <div className="space-y-2">
                                <div className="text-sm text-zinc-700">
                                  {result.new_response}
                                </div>
                                <div className="flex items-center gap-3 text-xs">
                                  <span className={`
                                    px-2 py-0.5 rounded-full
                                    ${improvement > 70 
                                      ? 'bg-green-100 text-green-700' 
                                      : improvement > 40
                                      ? 'bg-yellow-100 text-yellow-700'
                                      : 'bg-red-100 text-red-700'
                                    }
                                  `}>
                                    {improvement > 70 && <TrendingUp className="w-3 h-3 inline" />}
                                    Score: {improvement.toFixed(0)}%
                                  </span>
                                  <span>
                                    Confidence: {(result.confidence * 100).toFixed(0)}%
                                  </span>
                                  <span>
                                    {(result.processing_time_ms / 1000).toFixed(1)}s
                                  </span>
                                </div>
                                {result.differences && result.differences.length > 0 && (
                                  <div className="text-xs text-zinc-600 mt-2">
                                    <div className="font-medium mb-1">Changes:</div>
                                    <ul className="list-disc list-inside space-y-0.5">
                                      {result.differences.map((diff, i) => (
                                        <li key={i}>{diff}</li>
                                      ))}
                                    </ul>
                                  </div>
                                )}
                              </div>
                            </motion.div>
                          );
                        }
                        return null;
                      })}
                    </>
                  )}
                </div>
              ))
            )}
            
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-zinc-100 px-4 py-3 rounded-lg">
                  <div className="flex items-center gap-2">
                    <Loader2 className="w-4 h-4 text-zinc-600 animate-spin" />
                    <span className="text-sm text-zinc-600">AI is thinking...</span>
                  </div>
                </div>
              </div>
            )}
            
            {/* Scroll anchor - MUST be inside the scrollable container */}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area (only for live mode) */}
          {viewMode === 'live' && (
            <div className="border-t border-zinc-200 p-4">
              {personalitiesError ? (
                <div className="flex items-center justify-center p-4 bg-red-50 rounded-lg border border-red-200 mb-3">
                  <AlertCircle className="w-5 h-5 text-red-500 mr-2" />
                  <span className="text-red-700">Unable to load AI personalities. Please check your database connection and refresh the page.</span>
                </div>
              ) : personalitiesLoading ? (
                <div className="flex items-center justify-center p-4">
                  <Loader2 className="w-5 h-5 animate-spin text-purple-600 mr-2" />
                  <span className="text-zinc-600">Loading personalities...</span>
                </div>
              ) : personalities.length === 0 ? (
                <div className="flex items-center justify-center p-4 bg-amber-50 rounded-lg border border-amber-200 mb-3">
                  <AlertCircle className="w-5 h-5 text-amber-500 mr-2" />
                  <span className="text-amber-700">No AI personalities configured. Please add personalities in the AI Personality section.</span>
                </div>
              ) : (
                <div className="flex items-center gap-3">
                  <div className="relative">
                    <select
                      value={selectedPersonality}
                      onChange={(e) => setSelectedPersonality(e.target.value)}
                      className="px-3 py-2 pl-10 border border-purple-300 bg-white/90 rounded-lg text-sm appearance-none cursor-pointer hover:border-purple-400 transition-colors"
                    >
                      {personalities.map((p: any) => (
                        <option key={p.id} value={p.id}>
                          {p.emoji ? `${p.emoji} ` : ''}{p.name}
                        </option>
                      ))}
                    </select>
                    <div className="absolute left-2 top-1/2 -translate-y-1/2 pointer-events-none">
                      {(() => {
                        const selectedP = personalities?.find(p => p.id === selectedPersonality);
                        if (selectedP?.avatar) {
                          return (
                            <img 
                              src={selectedP.avatar} 
                              alt={selectedP.name} 
                              className="w-6 h-6 rounded-full object-cover"
                            />
                          );
                        } else if (selectedP?.emoji) {
                          return <span className="text-xl">{selectedP.emoji}</span>;
                        } else {
                          return <span className="text-xl">🤖</span>;
                        }
                      })()}
                    </div>
                  </div>
                  
                  <input
                  ref={inputRef}
                  type="text"
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && !isLoading && personalities.length > 0 && sendMessage()}
                  placeholder={personalities.length === 0 ? "No personalities available" : "Type your message..."}
                  className="flex-1 px-5 py-3 bg-gray-800/70 text-white placeholder-gray-400 rounded-2xl focus:outline-none focus:ring-2 focus:ring-purple-500 backdrop-blur-sm"
                  disabled={isLoading || personalities.length === 0}
                />
                
                <button
                  onClick={sendMessage}
                  disabled={!inputMessage.trim() || isLoading || personalities.length === 0}
                  className="px-5 py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-2xl hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed transition-all transform hover:scale-105 flex items-center gap-2"
                >
                  {isLoading ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    <MessageCircle className="w-5 h-5" />
                  )}
                </button>
                </div>
              )}
            </div>
          )}
        </div>

        {/* AI Learning Comparison Panel with Git-style Diff */}
        {viewMode === 'comparison' && selectedConversation && (
          <div className="flex-1 p-6 overflow-y-auto">
            <div className="max-w-6xl mx-auto space-y-6">
              {/* Comparison Header */}
              <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-xl font-bold text-white">AI Response Comparison</h3>
                  {replayResults.length === 0 && (
                    <button
                      onClick={startReplay}
                      disabled={!selectedConversation}
                      className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                    >
                      <RefreshCw className="w-4 h-4" />
                      Run Comparison
                    </button>
                  )}
                </div>
                
                {replayResults.length === 0 ? (
                  <div className="text-center py-12">
                    <GitBranch className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                    <p className="text-white/70">No comparison data available</p>
                    <p className="text-white/50 text-sm mt-2">
                      Run a replay to compare original and new AI responses
                    </p>
                  </div>
                ) : (
                  <div className="space-y-6">
                    {/* Display git-style diff for each replayed message */}
                    {replayResults.map((result, idx) => {
                      // Find the corresponding user message
                      const userMessages = selectedConversation.messages.filter((m: any) => m.sender === 'customer');
                      const userMessage = userMessages[idx]?.message || userMessages[idx]?.content || 'User message';
                      
                      return (
                        <div key={result.message_id} className="space-y-4">
                          {/* User Message Context */}
                          <div className="bg-blue-900/30 border-l-4 border-blue-500 p-3 rounded">
                            <div className="text-blue-300 text-sm font-medium mb-1">User Query #{idx + 1}</div>
                            <div className="text-white/90">{userMessage}</div>
                          </div>
                          
                          {/* Git-style Diff */}
                          <GitStyleDiff
                            original={result.original_response || 'No original response'}
                            modified={result.new_response || 'No new response'}
                            title={result.model_version !== 'unavailable' ? `Response Comparison - v${result.model_version}` : 'Response Comparison'}
                            mode="words"
                          />
                          
                          {/* Metrics */}
                          <div className="grid grid-cols-4 gap-4">
                            <div className="bg-gray-800/50 rounded-lg p-3">
                              <div className="text-xs text-gray-400">Confidence</div>
                              <div className="text-lg font-bold text-white">
                                {(result.confidence * 100).toFixed(1)}%
                                {result.confidence > 0.8 && <span className="text-green-400 text-xs ml-1">↑</span>}
                              </div>
                            </div>
                            <div className="bg-gray-800/50 rounded-lg p-3">
                              <div className="text-xs text-gray-400">Response Time</div>
                              <div className="text-lg font-bold text-white">
                                {(result.processing_time_ms / 1000).toFixed(2)}s
                              </div>
                            </div>
                            <div className="bg-gray-800/50 rounded-lg p-3">
                              <div className="text-xs text-gray-400">Improvement</div>
                              <div className={`text-lg font-bold ${
                                (result.improvement_score || 0) > 70 ? 'text-green-400' :
                                (result.improvement_score || 0) > 40 ? 'text-yellow-400' : 'text-red-400'
                              }`}>
                                {(result.improvement_score || 0).toFixed(0)}%
                              </div>
                            </div>
                            <div className="bg-gray-800/50 rounded-lg p-3">
                              <div className="text-xs text-gray-400">Model Version</div>
                              <div className="text-lg font-bold text-white">
                                {result.model_version === 'unavailable' ? 'N/A' : result.model_version}
                              </div>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Replay Progress Bar */}
      {viewMode === 'replay' && isReplaying && selectedConversation && (
        <div className="border-t border-zinc-200 p-2">
          <div className="w-full bg-zinc-200 rounded-full h-2">
            <motion.div 
              className="bg-purple-600 h-2 rounded-full"
              initial={{ width: 0 }}
              animate={{ 
                width: `${(replayIndex / selectedConversation.messages.filter(m => m.role === 'user').length) * 100}%` 
              }}
              transition={{ duration: 0.5 }}
            />
          </div>
        </div>
      )}
    </div>
  );
}