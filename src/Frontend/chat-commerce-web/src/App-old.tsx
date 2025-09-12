import React, { useState, useEffect, useRef, useCallback } from 'react';
import { modelApi, chatApi, voiceApi, authApi } from './services/api';
import potPalaceLogo from './assets/pot-palace-logo.png';
import Login from './components/Login';
import Register from './components/Register';

// Types

interface Personality {
  id: string;
  name: string;
  filename: string;
  path: string;
}

interface Tool {
  name: string;
  enabled: boolean;
}

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  responseTime?: number;
  tokens?: number;
  tokensPerSec?: number;
  promptUsed?: string;
  toolsUsed?: string[];
  model?: string;
  agent?: string;
  personality?: string;
  metadata?: any;
}

interface Preset {
  id: string;
  name: string;
  icon: string;
  agent: string;
  personality: string;
  description: string;
}

interface ConversationTemplate {
  id: string;
  category: string;
  icon: string;
  title: string;
  message: string;
}

interface Voice {
  id: string;
  name: string;
  language?: string;
  gender?: string;
}

// Conversation templates
const CONVERSATION_TEMPLATES: ConversationTemplate[] = [
  {
    id: 'first-time',
    category: 'General',
    icon: '🌱',
    title: 'First Time Customer',
    message: "I'm new to cannabis. What would you recommend for a beginner?"
  },
  {
    id: 'pain',
    category: 'Medical',
    icon: '💊',
    title: 'Pain Relief',
    message: "I'm looking for something to help with chronic pain. What strains work best?"
  },
  {
    id: 'sleep',
    category: 'Medical',
    icon: '😴',
    title: 'Sleep Aid',
    message: "I have trouble sleeping. What products can help with insomnia?"
  },
  {
    id: 'anxiety',
    category: 'Medical',
    icon: '😰',
    title: 'Anxiety Relief',
    message: "I need something for anxiety that won't make me too drowsy. Any recommendations?"
  },
  {
    id: 'creative',
    category: 'Effects',
    icon: '🎨',
    title: 'Creative Boost',
    message: "I want something that enhances creativity and focus. What do you suggest?"
  },
  {
    id: 'social',
    category: 'Effects',
    icon: '🎉',
    title: 'Social Enhancement',
    message: "What's good for social situations? I want to feel relaxed but still engaged."
  },
  {
    id: 'indica-sativa',
    category: 'Education',
    icon: '📚',
    title: 'Indica vs Sativa',
    message: "Can you explain the difference between indica and sativa?"
  },
  {
    id: 'edibles',
    category: 'Products',
    icon: '🍪',
    title: 'Edibles Info',
    message: "How do edibles work differently than smoking? What should I know?"
  },
  {
    id: 'dosing',
    category: 'Education',
    icon: '⚖️',
    title: 'Proper Dosing',
    message: "How do I find the right dose for me? I don't want to overdo it."
  },
  {
    id: 'terpenes',
    category: 'Advanced',
    icon: '🧪',
    title: 'Terpene Effects',
    message: "Can you explain how different terpenes affect the cannabis experience?"
  }
];

function App() {
  // State
  const [personalities, setPersonalities] = useState<Personality[]>([]);
  const [activeTools, setActiveTools] = useState<Tool[]>([]);
  const [presets, setPresets] = useState<Preset[]>([]);
  
  const [selectedModel, setSelectedModel] = useState<string>('');
  const [selectedAgent, setSelectedAgent] = useState<string>('');
  const [selectedPersonality, setSelectedPersonality] = useState<string>('');
  
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isModelLoaded, setIsModelLoaded] = useState(false);
  const [configDetails, setConfigDetails] = useState<any>(null);
  const [isSending, setIsSending] = useState(false);
  const [sessionId] = useState(() => {
    // Try to restore previous session or create new one
    const savedSession = localStorage.getItem('potpalace_session_id');
    const savedTimestamp = localStorage.getItem('potpalace_session_timestamp');
    
    // Check if saved session is less than 24 hours old
    if (savedSession && savedTimestamp) {
      const age = Date.now() - parseInt(savedTimestamp);
      if (age < 24 * 60 * 60 * 1000) { // 24 hours
        return savedSession;
      }
    }
    
    // Create new session
    const newSessionId = `session-${Date.now()}`;
    localStorage.setItem('potpalace_session_id', newSessionId);
    localStorage.setItem('potpalace_session_timestamp', Date.now().toString());
    return newSessionId;
  });
  const [expandedMessages, setExpandedMessages] = useState<Set<string>>(new Set());
  
  const [isRecording, setIsRecording] = useState(false);
  const [recognition, setRecognition] = useState<any>(null);
  const [transcript, setTranscript] = useState<string>('');
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [sessionLoaded, setSessionLoaded] = useState(false);
  const [isSpeakerEnabled, setIsSpeakerEnabled] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const currentAudioRef = useRef<HTMLAudioElement | null>(null);
  
  const [isPanelOpen, setIsPanelOpen] = useState(false);
  const [showTemplates, setShowTemplates] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  
  // Voice settings state
  const [availableVoices, setAvailableVoices] = useState<Voice[]>([]);
  const [selectedVoice, setSelectedVoice] = useState<string>('');
  const [showNotification, setShowNotification] = useState(false);
  const [notificationMessage, setNotificationMessage] = useState('');
  
  // Auth state
  const [showLogin, setShowLogin] = useState(false);
  const [showRegister, setShowRegister] = useState(false);
  const [currentUser, setCurrentUser] = useState<any>(null);
  
  const chatEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const shouldAutoSend = useRef(false);

  // Load saved configuration and session on mount
  useEffect(() => {
    // First load saved session
    loadSavedSession();
    // Then check model status (which will append to existing messages)
    checkModelStatus();
    // Load other resources
    loadDispensaryPresets();
    loadAvailableVoices();
    setupVoiceRecognition();
    
    // Keyboard shortcuts
    const handleKeyboard = (e: KeyboardEvent) => {
      if (e.metaKey || e.ctrlKey) {
        if (e.key === 'k') {
          e.preventDefault();
          inputRef.current?.focus();
        } else if (e.key === '/') {
          e.preventDefault();
          setIsPanelOpen(prev => !prev);
        } else if (e.key === 'f') {
          e.preventDefault();
          setIsFullscreen(prev => !prev);
        }
      } else if (e.key === 'Escape') {
        setIsPanelOpen(false);
        setShowTemplates(false);
      }
    };
    
    window.addEventListener('keydown', handleKeyboard);
    return () => window.removeEventListener('keydown', handleKeyboard);
  }, []);


  // Auto-scroll chat and save messages
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    // Save messages to localStorage whenever they change
    if (messages.length > 0) {
      saveSession();
    }
  }, [messages]);
  
  // Auto-send transcript when shouldAutoSend flag is set
  useEffect(() => {
    if (shouldAutoSend.current && inputMessage && !isRecording && !isTranscribing) {
      shouldAutoSend.current = false; // Reset the flag
      // Small delay to ensure state is updated
      const timer = setTimeout(() => {
        sendMessage();
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [inputMessage, isRecording, isTranscribing]);


  // Load saved configuration
  const checkModelStatus = async () => {
    try {
      // Try the new endpoint first
      const status = await modelApi.getCurrentModel();
      if (status.ready && status.loaded) {
        setIsModelLoaded(true);
        setSelectedModel(status.model || '');
        setSelectedAgent(status.agent || '');
        setSelectedPersonality(status.personality || '');
        
        // If config was applied, store the details
        if (status.config_applied && status.config_details) {
          setConfigDetails(status.config_details);
        }
        
        // Load active tools
        loadActiveTools();
        
        // Add a system message showing the model is already loaded
        const modelName = status.model || 'AI Model';
        const agentName = status.agent === 'dispensary' ? 'Pot Palace Budtender' : status.agent || '';
        const personalityText = status.personality === 'pot_palace' ? 'Expert Mode' : status.personality || '';
        
        // Only add model loaded message if we don't already have messages
        setMessages(prev => {
          // Check if we already have a "Model loaded" message
          const hasModelLoadedMsg = prev.some(msg => msg.content?.includes('Model loaded:'));
          if (hasModelLoadedMsg) {
            return prev; // Don't add duplicate
          }
          
          const systemMsg: Message = {
            id: `msg-model-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
            role: 'system',
            content: `Model loaded: ${agentName || modelName}${personalityText ? ` (${personalityText})` : ''}`,
            timestamp: new Date(),
            model: status.model,
            agent: status.agent,
            personality: status.personality
          };
          
          return prev.length === 0 ? [systemMsg] : [...prev, systemMsg];
        });
        
        // Auto-focus the chat input when model is loaded
        setTimeout(() => {
          inputRef.current?.focus();
        }, 100);
      }
    } catch (error) {
      console.error('Failed to check model status:', error);
    }
  };

  const saveSession = useCallback(() => {
    try {
      const sessionData = {
        sessionId,
        messages: messages
          .filter(msg => !msg.content?.startsWith('personality-change:')) // Don't save personality changes
          .map(msg => ({
            ...msg,
            timestamp: msg.timestamp.toISOString() // Convert Date to string
          })),
        savedAt: Date.now()
      };
      localStorage.setItem('potpalace_chat_session', JSON.stringify(sessionData));
    } catch (error) {
      console.error('Failed to save session:', error);
    }
  }, [messages, sessionId]);

  const loadSavedSession = () => {
    // Only load session once
    if (sessionLoaded) return;
    
    try {
      const saved = localStorage.getItem('potpalace_chat_session');
      if (saved) {
        const sessionData = JSON.parse(saved);
        
        // Check if this is the same session and less than 24 hours old
        if (sessionData.sessionId === sessionId && 
            Date.now() - sessionData.savedAt < 24 * 60 * 60 * 1000) {
          
          // Restore messages with Date objects, but filter out system messages about restoration
          const seenIds = new Set<string>();
          const restoredMessages = sessionData.messages
            .filter((msg: any) => {
              // Filter out restoration messages and duplicate model loaded messages
              return !msg.content?.includes('Previous session restored') &&
                     !msg.content?.includes('Session restored');
            })
            .map((msg: any, index: number) => {
              let messageId = msg.id;
              // If we've seen this ID before, generate a new unique one
              if (seenIds.has(messageId)) {
                messageId = `${msg.id}-dedup-${index}-${Math.random().toString(36).substr(2, 9)}`;
              }
              seenIds.add(messageId);
              
              return {
                ...msg,
                id: messageId,
                timestamp: new Date(msg.timestamp)
              };
            });
          
          if (restoredMessages.length > 0) {
            // Set the restored messages directly
            setMessages(restoredMessages);
            setSessionLoaded(true);
            
            // Show notification
            setTimeout(() => {
              showNotificationMessage(`Session restored (${restoredMessages.length} messages) 💾`);
            }, 500);
          }
        }
      }
    } catch (error) {
      console.error('Failed to load saved session:', error);
    }
  };

  const clearSession = () => {
    setMessages([]);
    localStorage.removeItem('potpalace_chat_session');
    // Create new session ID
    const newSessionId = `session-${Date.now()}`;
    localStorage.setItem('potpalace_session_id', newSessionId);
    localStorage.setItem('potpalace_session_timestamp', Date.now().toString());
    window.location.reload(); // Reload to get new session ID
  };

  const showNotificationMessage = (message: string) => {
    setNotificationMessage(message);
    setShowNotification(true);
    setTimeout(() => setShowNotification(false), 3000);
  };


  const loadDispensaryPresets = async () => {
    try {
      // Load personalities for dispensary agent
      const data = await modelApi.getPersonalities('dispensary');
      const dispensaryPersonalities = data.personalities || [];
      
      // Create presets from actual personalities
      const generatedPresets: Preset[] = dispensaryPersonalities.map((personality: any, index: number) => {
        // Choose icon based on personality name or use default
        let icon = '🌿';
        const lowerName = personality.name.toLowerCase();
        if (lowerName.includes('medical') || lowerName.includes('health')) {
          icon = '⚕️';
        } else if (lowerName.includes('chill') || lowerName.includes('casual') || lowerName.includes('relax')) {
          icon = '✌️';
        } else if (lowerName.includes('expert') || lowerName.includes('professional')) {
          icon = '🎓';
        } else if (lowerName.includes('friend')) {
          icon = '😊';
        }
        
        return {
          id: personality.id,
          name: personality.name,
          icon: icon,
          agent: 'dispensary',
          personality: personality.id,
          description: `${personality.name} - Dispensary ${personality.id} mode`
        };
      });
      
      setPresets(generatedPresets);
    } catch (error) {
      console.error('Failed to load dispensary presets:', error);
      // No fallback - just set empty presets
      setPresets([]);
    }
  };


  const loadActiveTools = async () => {
    try {
      const data = await modelApi.getActiveTools();
      setActiveTools(data.tools);
    } catch (error) {
      console.error('Failed to load active tools:', error);
    }
  };

  const loadAvailableVoices = async () => {
    try {
      const data = await voiceApi.getVoices();
      setAvailableVoices(data.voices || []);
      // Set the current voice if provided
      if (data.current_voice) {
        setSelectedVoice(data.current_voice);
      }
    } catch (error) {
      console.error('Failed to load voices:', error);
    }
  };

  const handleVoiceChange = async (voiceId: string) => {
    try {
      await voiceApi.changeVoice(voiceId);
      setSelectedVoice(voiceId);
      showNotificationMessage(`Voice changed to ${availableVoices.find(v => v.id === voiceId)?.name || voiceId}`);
    } catch (error) {
      console.error('Failed to change voice:', error);
      showNotificationMessage('Failed to change voice. Please try again.');
    }
  };


  const handlePresetLoad = async (preset: Preset) => {
    // Check if model is loaded first
    if (!isModelLoaded) {
      showNotificationMessage('Please wait for a model to be loaded first');
      return;
    }
    
    try {
      // Use the personality change endpoint instead of reloading the model
      const response = await modelApi.changePersonality(preset.agent, preset.personality);
      
      if (response.success) {
        // Update local state
        setSelectedAgent(preset.agent);
        setSelectedPersonality(preset.personality);
        
        // Add a metadata message for personality change
        const metadataMsg: Message = {
          id: `msg-meta-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
          role: 'system',
          content: `personality-change:${preset.name}`, // Special format for metadata
          timestamp: new Date(),
          model: selectedModel,
          agent: preset.agent,
          personality: preset.personality
        };
        setMessages(prev => [...prev, metadataMsg]);
        
        // Show success notification
        showNotificationMessage(`Switched to ${preset.name} mode 🌿`);
        
        // Close the panel after successful change
        setIsPanelOpen(false);
        
        // Focus on input
        setTimeout(() => {
          inputRef.current?.focus();
        }, 100);
      }
    } catch (error) {
      console.error('Failed to change personality:', error);
      showNotificationMessage('Failed to change personality. Please try again.');
    }
  };

  const setupVoiceRecognition = () => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition;
      const recognition = new SpeechRecognition();
      
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = 'en-US';
      
      recognition.onresult = (event: any) => {
        const finalTranscript = event.results[0][0].transcript;
        setTranscript(finalTranscript);
        setIsRecording(false);
        setIsTranscribing(false);
        // Set the input message and mark for auto-send
        setInputMessage(finalTranscript);
        shouldAutoSend.current = true;
      };
      
      recognition.onerror = (event: any) => {
        console.error('Speech recognition error', event.error);
        setIsRecording(false);
        setIsTranscribing(false);
        showNotificationMessage('Voice recognition error. Please try again.');
      };
      
      setRecognition(recognition);
    }
  };

  const toggleVoiceRecording = () => {
    if (!recognition) return;
    
    if (isRecording) {
      recognition.stop();
      setIsTranscribing(true);
    } else {
      recognition.start();
      setIsRecording(true);
      setTranscript('');
    }
  };

  const speakText = async (text: string) => {
    if (isSpeakerEnabled) {
      try {
        setIsSpeaking(true);
        
        // Stop any currently playing audio
        if (currentAudioRef.current) {
          currentAudioRef.current.pause();
          currentAudioRef.current = null;
        }
        
        // Use backend Piper TTS instead of browser speech synthesis
        const audioBlob = await voiceApi.synthesize(text, selectedVoice || undefined);
        
        // Create audio element and play
        const audioUrl = URL.createObjectURL(audioBlob);
        const audio = new Audio(audioUrl);
        currentAudioRef.current = audio;
        
        audio.onended = () => {
          setIsSpeaking(false);
          URL.revokeObjectURL(audioUrl);
          currentAudioRef.current = null;
        };
        
        audio.onerror = () => {
          setIsSpeaking(false);
          URL.revokeObjectURL(audioUrl);
          currentAudioRef.current = null;
          console.error('Failed to play synthesized audio');
        };
        
        await audio.play();
      } catch (error) {
        console.error('Failed to synthesize speech:', error);
        setIsSpeaking(false);
        // Fallback to browser speech synthesis if backend fails
        if ('speechSynthesis' in window) {
          const utterance = new SpeechSynthesisUtterance(text);
          utterance.onstart = () => setIsSpeaking(true);
          utterance.onend = () => setIsSpeaking(false);
          window.speechSynthesis.speak(utterance);
        }
      }
    }
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || !isModelLoaded || isSending) return;

    const userMsg: Message = {
      id: `msg-user-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      role: 'user',
      content: inputMessage,
      timestamp: new Date(),
      model: selectedModel,
      agent: selectedAgent,
      personality: selectedPersonality
    };

    setMessages(prev => [...prev, userMsg]);
    const messageSent = inputMessage; // Store for later use
    setInputMessage('');
    setTranscript('');
    setIsSending(true);
    
    // Keep focus on input after sending
    inputRef.current?.focus();
    
    const startTime = Date.now();

    try {
      const response = await chatApi.sendMessage(
        messageSent,
        sessionId,
        selectedAgent
      );
      
      const responseTime = Date.now() - startTime;

      const assistantMsg: Message = {
        id: `msg-assistant-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        role: 'assistant',
        content: response.response || 'No response',
        timestamp: new Date(),
        responseTime,
        toolsUsed: response.tools_used,
        tokens: response.metadata?.tokens,
        tokensPerSec: response.metadata?.tokens_per_sec,
        promptUsed: response.metadata?.prompt_template,
        model: selectedModel,
        agent: selectedAgent,
        personality: selectedPersonality,
        metadata: response.metadata
      };

      setMessages(prev => [...prev, assistantMsg]);
      
      // Speak the response if speaker is enabled
      if (isSpeakerEnabled) {
        speakText(response.response || 'No response');
      }
    } catch (error) {
      console.error('Failed to send message:', error);
      showNotificationMessage('Failed to send message. Please try again.');
    } finally {
      setIsSending(false);
      // Restore focus to input after response
      inputRef.current?.focus();
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const useTemplate = (template: ConversationTemplate) => {
    setInputMessage(template.message);
    setShowTemplates(false);
    inputRef.current?.focus();
  };

  const toggleMessageDetails = (messageId: string) => {
    setExpandedMessages(prev => {
      const newSet = new Set(prev);
      if (newSet.has(messageId)) {
        newSet.delete(messageId);
      } else {
        newSet.add(messageId);
      }
      return newSet;
    });
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit', 
      second: '2-digit' 
    });
  };

  const formatResponseTime = (ms: number) => {
    return `${(ms / 1000).toFixed(1)}s`;
  };

  const copyChatHistory = () => {
    const chatHistory = messages.map(msg => {
      let text = `[${formatTime(msg.timestamp)}] ${msg.role.toUpperCase()}: ${msg.content}`;
      
      if (msg.role !== 'user') {
        const details = [];
        if (msg.responseTime) details.push(`Response: ${formatResponseTime(msg.responseTime)}`);
        if (msg.tokens) details.push(`Tokens: ${msg.tokens}`);
        if (msg.tokensPerSec) details.push(`Speed: ${msg.tokensPerSec} t/s`);
        if (details.length > 0) {
          text += '\n  ' + details.join(' | ');
        }
      }
      
      return text;
    }).join('\n\n');
    
    const header = `=== Pot Palace AI Chat History ===
Session: ${sessionId}
Model: ${selectedModel || 'None'}
Agent: ${selectedAgent || 'None'}
Personality: ${selectedPersonality || 'None'}
Exported: ${new Date().toLocaleString()}
==================\n\n`;
    
    const fullText = header + chatHistory;
    
    navigator.clipboard.writeText(fullText).then(() => {
      showNotificationMessage('Chat history copied! 📋');
    }).catch(err => {
      console.error('Failed to copy:', err);
      showNotificationMessage('Failed to copy chat history');
    });
  };

  const handleLoginSuccess = (user: any) => {
    setCurrentUser(user);
    setShowLogin(false);
    showNotificationMessage(`Welcome back, ${user.name || user.email}! 🌿`);
    // Store user in localStorage
    localStorage.setItem('potpalace_user', JSON.stringify(user));
  };

  const handleRegisterSuccess = (user: any) => {
    setCurrentUser(user);
    setShowRegister(false);
    showNotificationMessage(`Welcome to Pot Palace, ${user.name || user.email}! 🎉`);
    // Store user in localStorage
    localStorage.setItem('potpalace_user', JSON.stringify(user));
  };

  const handleLogout = async () => {
    try {
      await authApi.logout();
    } catch (error) {
      console.error('Logout error:', error);
    }
    setCurrentUser(null);
    localStorage.removeItem('potpalace_user');
    showNotificationMessage('You have been logged out. See you soon! 👋');
  };

  // Check for saved user on mount
  useEffect(() => {
    const savedUser = localStorage.getItem('potpalace_user');
    if (savedUser) {
      try {
        setCurrentUser(JSON.parse(savedUser));
      } catch (error) {
        console.error('Failed to parse saved user:', error);
      }
    }
  }, []);

  return (
    <div className={`min-h-screen bg-gradient-to-br from-purple-950 via-purple-900 to-purple-800 ${isFullscreen ? 'fixed inset-0 z-50' : ''}`}>
      {/* Pot Palace Top Bar */}
      <div className="w-full bg-gradient-to-r from-[#E91ED4] via-[#FF006E] via-[#FF6B35] to-[#FFA500] px-6 py-4 flex items-center justify-between shadow-lg relative overflow-hidden z-40 h-[72px]">
        {/* Animated gradient overlay */}
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent animate-shimmer"></div>
        
        <div className="flex items-center gap-4 relative z-10">
          {/* Logo */}
          <div className="flex items-center gap-3">
            <img src={potPalaceLogo} alt="Pot Palace" className="h-10 w-auto" />
          </div>
        </div>

        {/* Search Bar */}
        <div className="flex-1 max-w-2xl mx-8 relative z-10">
          <div className="relative">
            <input
              type="text"
              placeholder="Search for products..."
              className="w-full px-5 py-2.5 bg-white/95 backdrop-blur-sm rounded-full text-gray-800 placeholder-gray-500 pr-12 focus:outline-none focus:ring-2 focus:ring-white/50 shadow-md"
            />
            <button className="absolute right-2 top-1/2 -translate-y-1/2 p-2 hover:bg-gray-100 rounded-full transition-colors">
              <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </button>
          </div>
        </div>

        {/* Right Actions - Transparent Cylinder with Icons */}
        <div className="relative z-10">
          <div className="flex items-center gap-4 px-6 py-1.5 bg-white/30 backdrop-blur-md rounded-full border border-white/30 shadow-lg">
            {/* Language Icon */}
            <button className="p-2.5 rounded-full hover:bg-white/20 transition-all group" title="Language">
              <svg className="w-5 h-5 text-white group-hover:text-yellow-400 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" />
              </svg>
            </button>
            
            {/* Cart Icon */}
            <button className="p-2.5 rounded-full hover:bg-white/20 transition-all group" title="Cart">
              <svg className="w-5 h-5 text-white group-hover:text-yellow-400 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
              </svg>
            </button>
            
            {/* Login/Logout Icon */}
            {currentUser ? (
              <button 
                onClick={handleLogout} 
                className="p-2.5 rounded-full hover:bg-white/20 transition-all group" 
                title="Logout"
              >
                <svg className="w-5 h-5 text-white group-hover:text-yellow-400 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
                </svg>
              </button>
            ) : (
              <button 
                onClick={() => {
                  console.log('Login button clicked');
                  setShowLogin(true);
                }} 
                className="p-2.5 rounded-full hover:bg-white/20 transition-all group" 
                title="Login"
              >
                <svg className="w-5 h-5 text-white group-hover:text-yellow-400 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
                </svg>
              </button>
            )}
            
            {/* Sign Up Icon - Only show when not logged in */}
            {!currentUser && (
              <button 
                onClick={() => setShowRegister(true)} 
                className="p-2.5 rounded-full hover:bg-white/20 transition-all group" 
                title="Sign Up"
              >
                <svg className="w-5 h-5 text-white group-hover:text-yellow-400 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
                </svg>
              </button>
            )}
            
            {/* User Profile - Show when logged in */}
            {currentUser && (
              <div className="flex items-center gap-2 px-3 py-1 bg-white/20 rounded-full">
                <span className="text-white text-sm font-medium">{currentUser.name || currentUser.email}</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Notification */}
      {showNotification && (
        <div className="fixed top-20 right-4 z-50 animate-float">
          <div className="bg-gradient-to-r from-purple-600 to-purple-500 text-white px-6 py-3 rounded-xl shadow-2xl font-medium flex items-center gap-2">
            <span className="text-pink-300">✨</span>
            {notificationMessage}
          </div>
        </div>
      )}

      <div className="relative h-[calc(100vh-72px)]">
        {/* Floating Configuration Panel */}
        <div className={`fixed left-0 top-[72px] h-[calc(100vh-72px)] w-80 bg-white shadow-2xl border-r border-gray-200 transform transition-transform duration-300 z-30 ${
          isPanelOpen ? 'translate-x-0' : '-translate-x-full'
        }`}>
          <div className="p-6 h-full overflow-y-auto">
            {/* Header */}
            <div className="mb-8">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div>
                    <h2 className="text-2xl font-bold bg-gradient-to-r from-[#3b82f6] via-[#9333ea] to-[#ec4899] bg-clip-text text-transparent">
                      AI Configuration
                    </h2>
                  </div>
                </div>
                <button
                  onClick={() => setIsPanelOpen(false)}
                  className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>

            {/* Quick Presets */}
            <div className="mb-6">
              <h3 className="text-sm font-semibold text-[#E91ED4] mb-3 uppercase tracking-wider">Quick Presets</h3>
              <div className="space-y-2">
                {presets.map(preset => (
                  <button
                    key={preset.id}
                    onClick={() => handlePresetLoad(preset)}
                    disabled={!isModelLoaded}
                    className={`w-full p-3 bg-gradient-to-r from-purple-50 to-pink-50 hover:from-purple-100 hover:to-pink-100 border border-purple-200 rounded-xl transition-all group shadow-sm hover:shadow-md ${
                      !isModelLoaded ? 'opacity-50 cursor-not-allowed' : ''
                    } ${
                      selectedPersonality === preset.personality ? 'ring-2 ring-[#E91ED4] bg-gradient-to-r from-purple-100 to-pink-100' : ''
                    }`}
                    title={isModelLoaded ? `Switch to ${preset.name}` : 'Load a model first'}
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-2xl">{preset.icon}</span>
                      <div className="text-left flex-1">
                        <div className="font-medium text-gray-800">{preset.name}</div>
                        <div className="text-xs text-gray-600">{preset.description}</div>
                      </div>
                      {selectedPersonality === preset.personality ? (
                        <svg className="w-4 h-4 text-[#E91ED4]" fill="currentColor" viewBox="0 0 24 24">
                          <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z" />
                        </svg>
                      ) : (
                        <svg className="w-4 h-4 text-purple-400 group-hover:text-[#E91ED4] transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" />
                        </svg>
                      )}
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Configuration Status */}
            {configDetails && (
              <div className="mt-6 p-4 bg-gradient-to-br from-purple-900/40 to-pink-900/40 rounded-xl border border-pink-600/20">
                <h3 className="text-sm font-semibold text-pink-400 mb-3 uppercase tracking-wider">Applied Configuration</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-purple-400">Name:</span>
                    <span className="text-purple-200 font-medium">{configDetails.name || 'Custom Config'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-purple-400">Version:</span>
                    <span className="text-purple-200">{configDetails.version || '1.0.0'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-purple-400">Temperature:</span>
                    <span className="text-purple-200">{configDetails.temperature || 'Default'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-purple-400">Max Tokens:</span>
                    <span className="text-purple-200">{configDetails.max_tokens || 'Default'}</span>
                  </div>
                </div>
              </div>
            )}
            
            {/* Voice Settings */}
            <div className="mt-6 p-4 bg-gradient-to-br from-indigo-900/40 to-purple-900/40 rounded-xl border border-purple-600/20">
              <h3 className="text-sm font-semibold text-purple-400 mb-3 uppercase tracking-wider">Voice Settings</h3>
              <div className="space-y-3">
                <div>
                  <label className="text-xs text-purple-400 block mb-1">Voice Selection</label>
                  <select
                    value={selectedVoice}
                    onChange={(e) => handleVoiceChange(e.target.value)}
                    className="w-full px-3 py-2 bg-purple-900/50 text-purple-200 border border-purple-600/30 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 text-sm"
                  >
                    <option value="">Default Voice</option>
                    {availableVoices.map(voice => (
                      <option key={voice.id} value={voice.id}>
                        {voice.name} {voice.language ? `(${voice.language})` : ''} {voice.gender ? `- ${voice.gender}` : ''}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-purple-400">Text-to-Speech</span>
                  <button
                    onClick={() => setIsSpeakerEnabled(!isSpeakerEnabled)}
                    className={`p-1.5 rounded-lg transition-colors ${
                      isSpeakerEnabled 
                        ? 'bg-purple-600 text-white' 
                        : 'bg-purple-900/50 text-purple-400 hover:bg-purple-800/50'
                    }`}
                    title={isSpeakerEnabled ? 'Disable TTS' : 'Enable TTS'}
                  >
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                      {isSpeakerEnabled ? (
                        <path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z"/>
                      ) : (
                        <path d="M16.5 12c0-1.77-1.02-3.29-2.5-4.03v2.21l2.45 2.45c.03-.2.05-.41.05-.63zm2.5 0c0 .94-.2 1.82-.54 2.64l1.51 1.51C20.63 14.91 21 13.5 21 12c0-4.28-2.99-7.86-7-8.77v2.06c2.89.86 5 3.54 5 6.71zM4.27 3L3 4.27 7.73 9H3v6h4l5 5v-6.73l4.25 4.25c-.67.52-1.42.93-2.25 1.18v2.06c1.38-.31 2.63-.95 3.69-1.81L19.73 21 21 19.73l-9-9L4.27 3zM12 4L9.91 6.09 12 8.18V4z"/>
                      )}
                    </svg>
                  </button>
                </div>
              </div>
            </div>
            
            {/* Active Tools */}
            {activeTools.length > 0 && (
              <div className="mt-6 p-4 bg-purple-900/30 rounded-xl">
                <h3 className="text-sm font-semibold text-pink-400 mb-3 uppercase tracking-wider">Active Tools</h3>
                <div className="space-y-2">
                  {activeTools.map(tool => (
                    <div key={tool.name} className="flex items-center gap-2 text-sm">
                      <div className={`w-2 h-2 rounded-full ${
                        tool.enabled ? 'bg-purple-400 animate-pulse' : 'bg-purple-700'
                      }`} />
                      <span className="text-purple-300">{tool.name}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Main Chat Interface */}
        <div className={`absolute inset-0 flex flex-col z-20 transition-all duration-300 ${
          isPanelOpen ? 'ml-80' : 'ml-0'
        }`}>
        
        {/* Toggle Panel Button */}
        {!isPanelOpen && (
          <button
            onClick={() => setIsPanelOpen(true)}
            className="fixed left-4 top-[92px] z-30 p-3 bg-white hover:bg-gray-50 border border-gray-200 rounded-xl transition-all group shadow-lg"
          >
            <svg className="w-5 h-5 text-[#E91ED4] group-hover:text-[#FF006E]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
        )}
          {/* Chat Header */}
          <div className="bg-white border-b border-gray-200 px-6 py-4 shadow-sm">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4 ml-16">
                <div className={`flex items-center gap-2 px-4 py-2 rounded-full ${
                  isModelLoaded 
                    ? 'bg-gradient-to-r from-[#3b82f6] via-[#9333ea] to-[#ec4899] text-white' 
                    : 'bg-gray-100 border border-gray-300 text-gray-600'
                }`}>
                  <div className={`w-2 h-2 rounded-full ${
                    isModelLoaded ? 'bg-white animate-pulse' : 'bg-gray-400'
                  }`}></div>
                  <span className="text-sm font-medium">
                    {isModelLoaded ? 'Online' : 'Offline'}
                  </span>
                </div>
                {selectedModel && (
                  <span className="text-sm text-gray-600">
                    {selectedModel}
                  </span>
                )}
                {selectedPersonality && (
                  <span className="text-sm text-gray-500 italic">
                    • {presets.find(p => p.personality === selectedPersonality)?.name || selectedPersonality}
                  </span>
                )}
                {isSpeaking && (
                  <span className="text-sm text-green-500 flex items-center gap-1 animate-pulse">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                    </svg>
                    Speaking...
                  </span>
                )}
              </div>

              <div className="flex items-center gap-2">
                {/* Fullscreen Toggle */}
                <button
                  onClick={() => setIsFullscreen(!isFullscreen)}
                  className="p-2 rounded-xl bg-gray-100 hover:bg-gray-200 text-gray-600 hover:text-[#E91ED4] transition-all"
                  title="Toggle fullscreen"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    {isFullscreen ? (
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                    ) : (
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 8V4m0 0h4M4 4l5 5m11-5h-4m4 0v4m0 0l-5-5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5h-4m4 0v-4" />
                    )}
                  </svg>
                </button>

                {/* Copy Chat */}
                <button
                  onClick={copyChatHistory}
                  disabled={messages.length === 0}
                  className="p-2 rounded-xl bg-gray-100 hover:bg-gray-200 text-gray-600 hover:text-[#E91ED4] transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                  title="Copy chat history"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                </button>

                {/* Clear Chat */}
                <button
                  onClick={clearSession}
                  disabled={messages.length === 0}
                  className="p-2 rounded-xl bg-gray-100 hover:bg-gray-200 text-gray-600 hover:text-red-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                  title="Clear chat and start new session"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>

                <div className="flex items-center gap-2">
                  {messages.length > 0 && (
                    <div className="px-2 py-1 bg-green-100 border border-green-300 rounded-lg text-xs text-green-700 font-medium">
                      {messages.length} msgs
                    </div>
                  )}
                  <div className="px-3 py-1.5 bg-gradient-to-r from-purple-50 to-pink-50 border border-purple-200 rounded-xl text-xs font-mono text-purple-600" title={`Session ID: ${sessionId}`}>
                    {sessionId.slice(-8)}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Chat Messages */}
          <div className="flex-1 overflow-y-auto p-6 bg-black/50 backdrop-blur-sm relative">
            {/* Offline Overlay */}
            {!isModelLoaded && (
              <div className="absolute inset-0 bg-white/80 backdrop-blur-sm z-10 flex items-center justify-center">
                <div className="text-center p-8 bg-white rounded-2xl border border-gray-200 shadow-xl">
                  <div className="text-4xl mb-3">🔌</div>
                  <p className="text-[#E91ED4] text-lg font-semibold">Model Offline</p>
                  <p className="text-gray-600 text-sm mt-2">Waiting for model to be loaded...</p>
                  <p className="text-gray-500 text-xs mt-1">Model must be loaded via API</p>
                </div>
              </div>
            )}
            
            {messages.length === 0 && (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <div className="text-6xl mb-4 animate-float">🌿</div>
                  <p className="text-purple-400 text-lg">Welcome to Pot Palace AI</p>
                  <p className="text-purple-500 text-sm mt-2">Select a personality preset when model is ready</p>
                </div>
              </div>
            )}

            <div className="space-y-4 max-w-6xl mx-auto">
              {messages.map(message => {
                // Check if this is a personality change metadata message
                if (message.role === 'system' && message.content.startsWith('personality-change:')) {
                  const personalityName = message.content.replace('personality-change:', '');
                  return (
                    <div key={message.id} className="flex justify-center py-2">
                      <p className="text-sm text-white/60 italic">
                        Personality changed to {personalityName}
                      </p>
                    </div>
                  );
                }
                
                return (
                  <div
                    key={message.id}
                    className={`flex ${
                      message.role === 'user' ? 'justify-end' : 
                      message.role === 'system' ? 'justify-center' : 'justify-start'
                    }`}
                  >
                    <div className={`max-w-4xl ${
                      message.role === 'system' ? 'w-full' : ''
                    }`}>
                      <div className={`px-5 py-3 rounded-2xl ${
                        message.role === 'user'
                          ? 'bg-black/75 border border-yellow-600/40 text-yellow-400 shadow-lg backdrop-blur-sm'
                          : message.role === 'system'
                          ? 'bg-black/75 text-pink-400 border border-purple-600/50 backdrop-blur-sm'
                          : 'bg-black/75 text-green-400 border border-green-700/40 backdrop-blur-sm'
                      }`}>
                        <div className="text-base font-medium">{message.content}</div>
                      </div>
                    
                    {/* Metadata */}
                    {message.role === 'assistant' && (
                      <div className="mt-1 px-2 text-xs text-white flex items-center gap-2 justify-start">
                        <span>{formatTime(message.timestamp)}</span>
                        
                        {message.responseTime && (
                          <>
                            <span>•</span>
                            <span>{formatResponseTime(message.responseTime)}</span>
                          </>
                        )}
                        
                        {message.tokens && (
                          <>
                            <span>•</span>
                            <span>{message.tokens} tokens</span>
                          </>
                        )}
                        
                        {message.agent && (
                          <>
                            <span>•</span>
                            <span>Agent: {message.agent}</span>
                          </>
                        )}
                        
                        {message.personality && (
                          <>
                            <span>•</span>
                            <span>Personality: {message.personality}</span>
                          </>
                        )}
                        
                        {message.toolsUsed && message.toolsUsed.length > 0 && (
                          <>
                            <span>•</span>
                            <span>Tools: {message.toolsUsed.join(', ')}</span>
                          </>
                        )}
                      </div>
                    )}
                  </div>
                </div>
                );
              })}
              
              {isSending && (
                <div className="flex justify-start">
                  <div className="px-4 py-3 rounded-2xl bg-black/75 border border-purple-700/30 backdrop-blur-sm">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 bg-pink-400 rounded-full animate-ping"></div>
                      <div className="w-2 h-2 bg-pink-400 rounded-full animate-ping" style={{ animationDelay: '0.2s' }}></div>
                      <div className="w-2 h-2 bg-pink-400 rounded-full animate-ping" style={{ animationDelay: '0.4s' }}></div>
                    </div>
                  </div>
                </div>
              )}
            </div>
            <div ref={chatEndRef} />
          </div>

          {/* Input Area */}
          <div className="border-t border-pink-600/20 bg-purple-900/80 backdrop-blur-sm">
            {/* Voice Transcription */}
            {(isRecording || isTranscribing || transcript) && (
              <div className="px-6 py-3 border-b border-purple-700/30">
                <div className="flex items-center gap-3">
                  {isRecording && (
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
                      <span className="text-sm font-medium text-red-400">Recording...</span>
                    </div>
                  )}
                  {isTranscribing && (
                    <div className="flex items-center gap-2">
                      <svg className="animate-spin h-4 w-4 text-pink-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      <span className="text-sm font-medium text-pink-400">Transcribing...</span>
                    </div>
                  )}
                  {transcript && !isRecording && !isTranscribing && (
                    <div className="flex-1 px-4 py-2 bg-purple-800/50 rounded-xl border border-purple-600/30">
                      <p className="text-sm text-purple-200">
                        <span className="font-medium text-pink-400">Transcript:</span> {transcript}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            )}
            
            {/* Input Controls */}
            <div className="p-4">
              <div className="flex items-center gap-3 max-w-6xl mx-auto">
                {/* Templates Button */}
                <button
                  onClick={() => setShowTemplates(!showTemplates)}
                  disabled={!isModelLoaded}
                  className="p-3 rounded-xl bg-purple-800/50 hover:bg-purple-700/50 text-purple-300 hover:text-pink-400 transition-all disabled:opacity-50 disabled:cursor-not-allowed relative"
                  title="Conversation templates"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </button>

                {/* Voice Button */}
                <button
                  onClick={toggleVoiceRecording}
                  disabled={!isModelLoaded || isSending}
                  className={`p-3 rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed ${
                    isRecording 
                      ? 'bg-gradient-to-r from-red-600 to-red-500 text-white animate-pulse shadow-lg' 
                      : 'bg-purple-800/50 hover:bg-purple-700/50 text-purple-300 hover:text-pink-400'
                  }`}
                  title={isRecording ? "Stop recording" : "Start voice recording"}
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                  </svg>
                </button>
                
                {/* Text Input */}
                <input
                  ref={inputRef}
                  type="text"
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder={isModelLoaded ? "Type your question here... (Cmd+K to focus)" : "Load a model to start chatting"}
                  disabled={!isModelLoaded}
                  className={`flex-1 px-5 py-3 bg-purple-900/50 border border-purple-600/30 rounded-xl text-purple-100 placeholder-purple-500 focus:outline-none focus:ring-2 focus:ring-pink-500/50 focus:border-transparent transition-all ${isModelLoaded && messages.length === 1 ? 'animate-pulse ring-2 ring-green-400/50' : ''}`}
                />
                
                {/* Speaker Button */}
                <button
                  onClick={() => {
                    setIsSpeakerEnabled(!isSpeakerEnabled);
                    // Stop any currently playing audio
                    if (currentAudioRef.current) {
                      currentAudioRef.current.pause();
                      currentAudioRef.current = null;
                      setIsSpeaking(false);
                    }
                    // Also stop browser speech synthesis if any
                    if ('speechSynthesis' in window) {
                      window.speechSynthesis.cancel();
                    }
                  }}
                  className={`p-3 rounded-xl transition-all ${
                    isSpeakerEnabled 
                      ? 'bg-gradient-to-r from-green-600 to-green-500 text-white shadow-lg' 
                      : 'bg-purple-800/50 hover:bg-purple-700/50 text-purple-300 hover:text-pink-400'
                  } ${isSpeaking ? 'animate-pulse' : ''}`}
                  title={isSpeakerEnabled ? "Disable text-to-speech" : "Enable text-to-speech"}
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    {isSpeakerEnabled ? (
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                    ) : (
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                    )}
                  </svg>
                </button>
                
                {/* Chat Button */}
                <button
                  id="send-button"
                  onClick={sendMessage}
                  disabled={!isModelLoaded || !inputMessage.trim() || isSending}
                  className="px-6 py-3 bg-gradient-to-r from-pink-600 to-pink-500 hover:from-pink-500 hover:to-pink-400 text-purple-950 font-bold rounded-xl transition-all transform hover:scale-105 active:scale-95 shadow-lg disabled:from-purple-700 disabled:to-purple-600 disabled:text-purple-400 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  {isSending ? (
                    <>
                      <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      <span>Chatting...</span>
                    </>
                  ) : (
                    <>
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                      </svg>
                      <span>Chat</span>
                    </>
                  )}
                </button>
              </div>

              {/* Templates Dropdown */}
              {showTemplates && (
                <div className="absolute bottom-20 left-4 right-4 max-w-6xl mx-auto bg-purple-900/95 backdrop-blur-xl border border-pink-600/20 rounded-2xl shadow-2xl p-4 z-50">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-sm font-semibold text-pink-400 uppercase tracking-wider">Quick Questions</h3>
                    <button
                      onClick={() => setShowTemplates(false)}
                      className="p-1 hover:bg-purple-800 rounded-lg transition-colors"
                    >
                      <svg className="w-4 h-4 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                  <div className="grid grid-cols-2 gap-2 max-h-60 overflow-y-auto">
                    {CONVERSATION_TEMPLATES.map(template => (
                      <button
                        key={template.id}
                        onClick={() => useTemplate(template)}
                        className="text-left p-3 bg-purple-800/50 hover:bg-purple-700/50 border border-purple-600/30 rounded-xl transition-all group"
                      >
                        <div className="flex items-start gap-2">
                          <span className="text-lg">{template.icon}</span>
                          <div className="flex-1">
                            <div className="text-xs font-medium text-pink-300 group-hover:text-pink-200">{template.title}</div>
                            <div className="text-xs text-purple-400 mt-1 line-clamp-2">{template.message}</div>
                          </div>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
      
      {/* Login Modal */}
      {showLogin && (
        <Login 
          onClose={() => setShowLogin(false)}
          onLoginSuccess={handleLoginSuccess}
          onSwitchToRegister={() => {
            setShowLogin(false);
            setShowRegister(true);
          }}
        />
      )}
      
      {/* Register Modal */}
      {showRegister && (
        <Register
          onClose={() => setShowRegister(false)}
          onRegisterSuccess={handleRegisterSuccess}
          onSwitchToLogin={() => {
            setShowRegister(false);
            setShowLogin(true);
          }}
        />
      )}
    </div>
  );
}

export default App;