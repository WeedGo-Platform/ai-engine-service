import React, { useState, useEffect, useRef, useCallback, RefObject } from 'react';
import { TemplateContextProvider, useTemplateContext } from './contexts/TemplateContext';
import { AuthProvider } from './contexts/AuthContext';
import { ComplianceProvider } from './contexts/ComplianceContext';
import { FloatingChatProvider } from './contexts/FloatingChatContext';
import { CartProvider } from './contexts/CartContext';
import { PageProvider, usePageContext } from './contexts/PageContext';
import { DynamicComponent, TemplateLayout } from './core/providers/template.provider';
import FloatingChatContainer from './components/floating-chat/FloatingChatContainer';
import { modelApi, chatApi, voiceApi } from './services/api';
import { Product } from './services/productSearch';
import { useClickOutside } from './hooks/useClickOutside';
import { useEnhancedChatInput } from './hooks/useEnhancedChatInput';
import { getChatHistory } from './utils/chatHistory';

// Types
import { 
  Personality, 
  Tool, 
  Message, 
  Preset, 
  ConversationTemplate, 
  Voice, 
  User,
  AIConfig,
  VoiceSettings
} from './types';

// Utils
import { formatTime, formatResponseTime } from './utils/formatters';
import { extractMessageContent, formatMessageContent, createProductDetailsMessage } from './utils/messageParser';

import LandingPage from './components/pages/LandingPage';
import PageSlider from './components/common/PageSlider';

function AppContent() {
  // Get template context
  const { currentTemplate, availableTemplates, switchTemplate } = useTemplateContext();
  
  // Get page context
  const { currentPage } = usePageContext();
  
  // State
  const [personalities, setPersonalities] = useState<Personality[]>([]);
  const [activeTools, setActiveTools] = useState<Tool[]>([]);
  const [presets, setPresets] = useState<Preset[]>([]);
  
  const [selectedModel, setSelectedModel] = useState<string>('');
  const [selectedAgent, setSelectedAgent] = useState<string>('');
  const [selectedPersonality, setSelectedPersonality] = useState<string>('');
  
  const [messages, setMessages] = useState<Message[]>([]);
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
  
  // Mic mode: 'off' | 'wake' | 'active'
  type MicMode = 'off' | 'wake' | 'active';
  const [micMode, setMicMode] = useState<MicMode>('off');
  const [isRecording, setIsRecording] = useState(false);
  const [recognition, setRecognition] = useState<any>(null);
  const [transcript, setTranscript] = useState<string>('');
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [sessionLoaded, setSessionLoaded] = useState(false);
  const [isSpeakerEnabled, setIsSpeakerEnabled] = useState(false); // Default OFF
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isConversationMode, setIsConversationMode] = useState(false);
  const currentAudioRef = useRef<HTMLAudioElement | null>(null);
  
  // New state for real-time transcript
  const [liveTranscript, setLiveTranscript] = useState<string>('');
  const [finalizedTranscript, setFinalizedTranscript] = useState<string>('');
  const silenceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pauseTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const conversationSilenceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const lastSpeechTimeRef = useRef<number>(Date.now());
  const pendingTranscriptRef = useRef<string>('');
  
  const [isPanelOpen, setIsPanelOpen] = useState(false);
  const [showTemplates, setShowTemplates] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  
  // Voice settings state
  const [availableVoices, setAvailableVoices] = useState<Voice[]>([]);
  const [selectedVoice, setSelectedVoice] = useState<string>('');
  const [showNotification, setShowNotification] = useState(false);
  const [notificationMessage, setNotificationMessage] = useState('');
  
  // Auth modal state
  const [showLogin, setShowLogin] = useState(false);
  const [showRegister, setShowRegister] = useState(false);
  
  // Age verification state
  const [isAgeVerified, setIsAgeVerified] = useState(() => {
    // Check if age was already verified in this session
    return localStorage.getItem('age_verified') === 'true';
  });
  
  // Forward declare the send message ref
  const sendMessageRef = useRef<(text?: string) => Promise<void>>(null);
  
  // Enhanced chat input with history and autocorrect
  const enhancedInput = useEnhancedChatInput({
    onSubmit: (text: string) => {
      if (sendMessageRef.current) {
        sendMessageRef.current(text);
      }
    },
    enableAutoCorrect: true,
    enableHistory: true,
    autoCorrectDelay: 500
  });
  
  const inputMessage = enhancedInput.value || '';
  const setInputMessage = enhancedInput.setValue;
  const handleInputKeyDown = enhancedInput.handleKeyDown;
  const suggestions = enhancedInput.suggestions;
  const showSuggestions = enhancedInput.showSuggestions;
  const applySuggestion = enhancedInput.applySuggestion;
  const dismissSuggestions = enhancedInput.dismissSuggestions;
  const enhancedInputRef = enhancedInput.inputRef;
  
  const inputRef = useRef<HTMLInputElement>(null);
  const shouldAutoSend = useRef(false);
  const messagesEndRef = useRef<HTMLDivElement>(null!);
  const hamburgerRef = useRef<HTMLDivElement>(null);
  const panelRef = useClickOutside<HTMLDivElement>(() => {
    if (isPanelOpen) {
      setIsPanelOpen(false);
    }
  }, [hamburgerRef as RefObject<HTMLElement>]);

  // Load saved configuration and session on mount
  useEffect(() => {
    // First load saved session
    loadSavedSession();
    // Then check model status (which will append to existing messages)
    checkModelStatus();
    // Load other resources
    loadDispensaryPresets();
    loadAvailableVoices();
    
    // Initialize speech recognition
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition;
      const recognitionInstance = new SpeechRecognition();
      recognitionInstance.continuous = true;
      recognitionInstance.interimResults = true;
      recognitionInstance.lang = 'en-US';
      
      let allFinalText = '';
      let lastResultIndex = 0;
      let lastSentText = '';
      
      recognitionInstance.onresult = (event: any) => {
        console.log('[Mic] Speech result event, resultIndex:', event.resultIndex, 'results length:', event.results.length);
        
        let interimText = '';
        let newFinalText = '';
        
        // Process only new results (from resultIndex onwards)
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const result = event.results[i];
          
          if (!result || !result[0]) {
            continue;
          }
          
          const transcriptText = String(result[0].transcript);
          console.log(`[Mic] Result ${i}: "${transcriptText}" (final: ${result.isFinal})`);
          
          // Wake word detection in wake mode
          if (micMode === 'wake') {
            const lowerText = transcriptText.toLowerCase();
            if (lowerText.includes('hey assistant') || lowerText.includes('hey ai') || lowerText.includes('hey there')) {
              console.log('[WakeWord] Detected! Switching to active mode');
              setMicMode('active');
              recognitionInstance.stop();
              setTimeout(() => startActiveRecording(), 300);
              showNotificationMessage('✅ Wake word detected!');
              return;
            }
            setTranscript(transcriptText);
            return; // Don't process further in wake mode
          }
          
          if (result.isFinal) {
            newFinalText += transcriptText + ' ';
            // Add to accumulated final text
            if (i >= lastResultIndex) {
              allFinalText += transcriptText + ' ';
              lastResultIndex = i + 1;
            }
          } else {
            // This is interim/live text
            interimText = transcriptText;
          }
        }
        
        // Show complete transcript immediately (accumulated final + current interim)
        const completeTranscript = allFinalText + interimText;
        console.log('[Mic] Setting transcript to:', completeTranscript);
        
        // Update all transcript states immediately for live display
        setTranscript(completeTranscript);
        setLiveTranscript(interimText);
        setFinalizedTranscript(allFinalText);
        pendingTranscriptRef.current = allFinalText; // Store for pause detection
        
        // Keep transcribing state active
        setIsTranscribing(interimText.length > 0 || allFinalText.length > 0);
        
        // Reset timers on any speech activity
        lastSpeechTimeRef.current = Date.now();
        
        // Clear ALL existing timers to prevent stale timers
        if (pauseTimerRef.current) {
          clearTimeout(pauseTimerRef.current);
          pauseTimerRef.current = null;
        }
        
        if (silenceTimerRef.current) {
          clearTimeout(silenceTimerRef.current);
          silenceTimerRef.current = null;
        }
        
        if (conversationSilenceTimerRef.current) {
          clearTimeout(conversationSilenceTimerRef.current);
          conversationSilenceTimerRef.current = null;
        }
        
        // Set pause timer (1.5 seconds) - sends text but keeps recording
        if (allFinalText.trim() && allFinalText.trim() !== lastSentText) {
          pauseTimerRef.current = setTimeout(() => {
            console.log('[Mic] Pause detected, sending chunk:', allFinalText);
            
            const textToSend = allFinalText.trim();
            if (textToSend && textToSend !== lastSentText) {
              // Send this chunk as a message
              sendMessageRef.current?.(textToSend);
              lastSentText = textToSend;
              
              // Clear the pending transcript since we've sent it
              allFinalText = '';
              lastResultIndex = event.results.length;
              setFinalizedTranscript('');
              setTranscript(interimText); // Keep showing any interim text
              pendingTranscriptRef.current = '';
            }
          }, 1500); // 1.5 seconds pause = send chunk
        }
        
        // Set long silence timer (5 seconds) - stops recording completely
        // In conversation mode, use shorter timeout (4 seconds)
        const silenceTimeout = isConversationMode ? 4000 : 5000;
        silenceTimerRef.current = setTimeout(() => {
          console.log(`[Mic] ${silenceTimeout/1000} seconds of silence detected, stopping recording`);
          
          // Send any remaining unsent text
          const remainingText = allFinalText.trim();
          if (remainingText && remainingText !== lastSentText) {
            sendMessageRef.current?.(remainingText);
          }
          
          // Exit conversation mode
          if (isConversationMode) {
            console.log('[ConversationMode] Ending conversation due to silence');
            setIsConversationMode(false);
          }
          
          // Stop recording
          if (recognitionInstance) {
            recognitionInstance.stop();
          }
          
          // Reset for next recording session
          allFinalText = '';
          lastResultIndex = 0;
          lastSentText = '';
        }, silenceTimeout);
      };
      
      recognitionInstance.onerror = (event: any) => {
        console.error('[Mic] Speech recognition error:', event.error);
        
        // Don't stop recording on "no-speech" error - it's normal during pauses
        if (event.error === 'no-speech') {
          console.log('[Mic] No speech detected, but continuing to listen...');
          return; // Keep recording active
        }
        
        // For other errors, stop recording
        setIsRecording(false);
        setIsTranscribing(false);
        
        // Show user-friendly error message
        const errorMessages: Record<string, string> = {
          'not-allowed': 'Microphone access denied. Please allow microphone access in your browser settings.',
          'audio-capture': 'Microphone not found. Please check your microphone connection.',
          'network': 'Network error. Please check your internet connection.',
          'aborted': 'Recording was aborted.',
          'service-not-allowed': 'Speech recognition service not allowed.'
        };
        
        const message = errorMessages[event.error] || `Recording error: ${event.error}`;
        showNotificationMessage(message);
      };
      
      recognitionInstance.onend = () => {
        console.log('[Mic] Speech recognition ended');
        
        // If we're still supposed to be recording, restart it
        if (isRecording) {
          console.log('[Mic] Auto-restarting recognition...');
          try {
            recognitionInstance.start();
          } catch (e) {
            console.error('[Mic] Failed to restart recognition:', e);
            setIsRecording(false);
            setIsTranscribing(false);
          }
          return;
        }
        
        // Otherwise, clean up
        console.log('[Mic] Cleaning up recognition state');
        
        // Clear both timers
        if (silenceTimerRef.current) {
          clearTimeout(silenceTimerRef.current);
          silenceTimerRef.current = null;
        }
        if (pauseTimerRef.current) {
          clearTimeout(pauseTimerRef.current);
          pauseTimerRef.current = null;
        }
        
        // Clean up states
        setIsRecording(false);
        setIsTranscribing(false);
        setTranscript('');
        setLiveTranscript('');
        setFinalizedTranscript('');
        pendingTranscriptRef.current = '';
      };
      
      setRecognition(recognitionInstance);
      console.log('[Mic] Speech recognition initialized successfully');
    } else {
      console.warn('[Mic] Speech recognition not supported in this browser');
      showNotificationMessage('Speech recognition is not supported in your browser. Try Chrome or Edge.');
    }
  }, []);

  // Load saved session function
  const loadSavedSession = () => {
    try {
      const savedMessages = localStorage.getItem(`potpalace_messages_${sessionId}`);
      const savedConfig = localStorage.getItem(`potpalace_config_${sessionId}`);
      
      if (savedMessages) {
        const parsedMessages = JSON.parse(savedMessages);
        setMessages(parsedMessages);
      }
      
      if (savedConfig) {
        const parsedConfig = JSON.parse(savedConfig);
        setSelectedModel(parsedConfig.model || '');
        setSelectedAgent(parsedConfig.agent || '');
        setSelectedPersonality(parsedConfig.personality || '');
        setActiveTools(parsedConfig.tools || []);
        setIsSpeakerEnabled(parsedConfig.speakerEnabled || false);
      }
      
      setSessionLoaded(true);
    } catch (error) {
      console.error('Error loading saved session:', error);
      setSessionLoaded(true);
    }
  };

  // Load presets function
  const loadDispensaryPresets = async () => {
    // Default presets data
    const defaultPresets: Preset[] = [
      {
        id: 'budtender',
        name: 'Budtender',
        icon: '🌿',
        personality: 'friendly_budtender',
        agent: 'dispensary_assistant',
        tools: []
      },
      {
        id: 'medical',
        name: 'Medical Advisor',
        icon: '🏥',
        personality: 'medical_consultant',
        agent: 'medical_assistant',
        tools: []
      },
      {
        id: 'sommelier',
        name: 'Cannabis Sommelier',
        icon: '🍷',
        personality: 'cannabis_sommelier',
        agent: 'product_specialist',
        tools: []
      }
    ];
    setPresets(defaultPresets);
  };

  // Load available voices
  const loadAvailableVoices = async () => {
    try {
      console.log('[Voice] Loading available voices...');
      const voices = await voiceApi.getVoices();
      console.log('[Voice] Loaded voices:', voices);
      setAvailableVoices(voices);
      if (voices.length > 0 && !selectedVoice) {
        setSelectedVoice(voices[0].id);
        console.log('[Voice] Auto-selected first voice:', voices[0].id);
      }
    } catch (error) {
      console.error('[Voice] Error loading voices:', error);
      showNotificationMessage('Failed to load voices');
    }
  };

  // Check model status
  const checkModelStatus = async () => {
    try {
      const response = await modelApi.getModelStatus();
      setIsModelLoaded(response.loaded || response.model_loaded);
      // Add other model loading logic here
    } catch (error) {
      console.error('Error checking model status:', error);
    }
  };

  // Handle sending message
  const handleSendMessage = async (messageText?: string) => {
    // Ensure we have a string value
    const textToSend = String(messageText || inputMessage || '');
    if (!textToSend || !textToSend.trim() || !isModelLoaded || isSending) return;
    
    // Add to history
    const trimmedText = textToSend.trim();
    if (enhancedInput && enhancedInput.value === trimmedText) {
      // This came from the input, add to history
      const history = getChatHistory();
      history.add(trimmedText);
    }
    
    const userMessage: Message = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: trimmedText,
      text: trimmedText, // Add for template compatibility
      timestamp: new Date()
    } as Message;
    
    console.log('Creating user message:', userMessage);
    console.log('User message content type:', typeof userMessage.content);
    console.log('User message content value:', userMessage.content);
    
    setMessages(prev => {
      console.log('Previous messages:', prev);
      const newMessages = [...prev, userMessage];
      console.log('New messages array:', newMessages);
      return newMessages;
    });
    setInputMessage('');
    setIsSending(true);
    
    try {
      const startTime = Date.now();
      // Get user_id from localStorage if user is logged in
      let userId: string | undefined;
      const userStr = localStorage.getItem('user');
      if (userStr) {
        try {
          const user = JSON.parse(userStr);
          userId = user?.id;
        } catch (e) {
          console.error('Failed to parse user from localStorage:', e);
        }
      }
      
      const response = await chatApi.sendMessage(trimmedText, sessionId, selectedAgent, userId);
      const responseTime = (Date.now() - startTime) / 1000; // Convert to seconds
      
      // Debug log to see the structure
      if (typeof window !== 'undefined' && window.location.hostname === 'localhost') {
        console.log('Chat API Response:', response);
        console.log('Response type:', typeof response);
        if (response && typeof response === 'object') {
          console.log('Response keys:', Object.keys(response));
        }
      }
      
      // Use the robust message parser to extract content
      const messageContent = formatMessageContent(response);
      
      // Validate the extracted content
      if (!messageContent || messageContent === '[object Object]') {
        console.error('Failed to extract valid message content from response:', response);
        // Provide a fallback message
        const fallbackMessage = 'I received your message but encountered an issue processing the response.';
        
        const errorMessage: Message = {
          id: `msg-${Date.now()}-assistant`,
          role: 'assistant',
          content: fallbackMessage,
          text: fallbackMessage, // Add for template compatibility
          timestamp: new Date(),
          responseTime: responseTime,
          tokens: 0,
          agent: selectedAgent || 'default',
          personality: selectedPersonality || 'default',
          metadata: { error: 'Failed to parse response', originalResponse: response }
        } as Message;
        
        setMessages(prev => [...prev, errorMessage]);
        setIsSending(false);
        return;
      }
      
      const assistantMessage: Message = {
        id: `msg-${Date.now()}-assistant`,
        role: 'assistant',
        content: messageContent,
        text: messageContent, // Add for template compatibility
        timestamp: new Date(),
        responseTime: responseTime,
        tokens: response?.metadata?.tokens || 0,
        agent: selectedAgent || 'default',
        personality: selectedPersonality || 'default',
        metadata: response?.metadata
      } as Message;
      
      setMessages(prev => [...prev, assistantMessage]);
      
      // Handle voice synthesis if enabled
      if (isSpeakerEnabled && selectedVoice) {
        try {
          console.log('[Voice] Synthesizing speech with voice:', selectedVoice);
          console.log('[Voice] Text to synthesize:', messageContent.substring(0, 100) + '...');
          const audioBlob = await voiceApi.synthesize(messageContent, selectedVoice);
          console.log('[Voice] Received audio blob:', audioBlob.size, 'bytes');
          const audioUrl = URL.createObjectURL(audioBlob);
          
          // Stop any currently playing audio
          if (currentAudioRef.current) {
            currentAudioRef.current.pause();
            currentAudioRef.current = null;
          }
          
          // Create and play new audio
          const audio = new Audio(audioUrl);
          currentAudioRef.current = audio;
          
          setIsSpeaking(true);
          
          audio.addEventListener('ended', () => {
            console.log('[Voice] Audio playback ended');
            setIsSpeaking(false);
            URL.revokeObjectURL(audioUrl);
            currentAudioRef.current = null;

            // Auto-start mic after voice finishes (conversation mode)
            if (isSpeakerEnabled && micMode === 'off') {
              console.log('[ConversationMode] Voice finished, auto-starting mic in 500ms...');
              setIsConversationMode(true);
              // Small delay to feel more natural
              setTimeout(() => {
                setMicMode('active');
                startActiveRecording();
              }, 500);
            }
          });
          
          audio.addEventListener('error', (e) => {
            console.error('[Voice] Audio playback error:', e);
            showNotificationMessage('Failed to play voice audio');
            setIsSpeaking(false);
            URL.revokeObjectURL(audioUrl);
            currentAudioRef.current = null;
          });
          
          console.log('[Voice] Starting audio playback...');
          await audio.play();
          console.log('[Voice] Audio playing successfully');
        } catch (error) {
          console.error('[Voice] Error synthesizing speech:', error);
          showNotificationMessage('Voice synthesis failed: ' + (error as Error).message);
          setIsSpeaking(false);
        }
      } else if (isSpeakerEnabled && !selectedVoice) {
        console.warn('[Voice] Speaker enabled but no voice selected');
        showNotificationMessage('No voice selected. Please select a voice in settings.');
      }
    } catch (error) {
      console.error('Error sending message:', error);
    } finally {
      setIsSending(false);
    }
  };
  
  // Assign the send message function to the ref
  sendMessageRef.current = handleSendMessage;

  // Handle viewing product details in chat
  const handleViewProductDetails = (product: Product) => {
    const detailsMessage: Message = {
      id: `product-${Date.now()}`,
      role: 'assistant',
      content: createProductDetailsMessage(product), // Don't stringify - pass object directly
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, detailsMessage]);
    
    // Save to localStorage
    const updatedMessages = [...messages, detailsMessage];
    localStorage.setItem(`potpalace_messages_${sessionId}`, JSON.stringify(updatedMessages));
  };

  // Handle new conversation
  const handleNewConversation = () => {
    setMessages([]);
    localStorage.removeItem(`potpalace_messages_${sessionId}`);
  };

  // Handle voice recording
  const handleVoiceRecord = () => {
    if (!recognition) {
      console.error('[Mic] Speech recognition not initialized');
      showNotificationMessage('Speech recognition not available in your browser');
      return;
    }
    
    if (isRecording) {
      console.log('[Mic] Manually stopping recording');
      
      // Set flag to prevent auto-restart
      setIsRecording(false);
      setIsTranscribing(false);
      
      // Exit conversation mode if manually stopped
      if (isConversationMode) {
        console.log('[ConversationMode] Manually stopped, exiting conversation mode');
        setIsConversationMode(false);
      }
      
      // Clear both timers if active
      if (silenceTimerRef.current) {
        clearTimeout(silenceTimerRef.current);
        silenceTimerRef.current = null;
      }
      if (pauseTimerRef.current) {
        clearTimeout(pauseTimerRef.current);
        pauseTimerRef.current = null;
      }
      
      // Send any pending transcript before stopping
      if (pendingTranscriptRef.current && pendingTranscriptRef.current.trim()) {
        console.log('[Mic] Sending pending transcript:', pendingTranscriptRef.current.trim());
        sendMessageRef.current?.(pendingTranscriptRef.current.trim());
      }
      
      // Stop recognition (this will trigger onend, but isRecording is now false)
      recognition.stop();
      showNotificationMessage('Recording stopped');
      return;
    }
  };
  
  const startWakeWordListening = () => {
    if (!recognition) return;
    
    console.log('[WakeWord] Starting wake word detection');
    setTranscript('');
    setLiveTranscript('');
    
    try {
      recognition.start();
      showNotificationMessage('🎤 Listening for "Hey Assistant"...');
    } catch (error) {
      console.error('[WakeWord] Failed to start:', error);
      setMicMode('off');
    }
  };
  
  const startActiveRecording = () => {
    if (!recognition) return;
    
    console.log('[Mic] Starting active recording');
    
    // Clear any previous transcripts
    setTranscript('');
    setLiveTranscript('');
    setFinalizedTranscript('');
    pendingTranscriptRef.current = '';
    
    // Set recording state BEFORE starting
    setIsRecording(true);
    setIsTranscribing(true);
    
    try {
      // Start recognition
      recognition.start();
      
      // Initialize speech time
      lastSpeechTimeRef.current = Date.now();
      
      console.log('[Mic] Recording started successfully');
      showNotificationMessage('Recording... Speak now');
    } catch (error) {
      console.error('[Mic] Failed to start recording:', error);
      setIsRecording(false);
      setIsTranscribing(false);
      setMicMode('off');
      showNotificationMessage('Failed to start recording. Check microphone permissions.');
    }
  };

  // Create AI config object
  const aiConfig: AIConfig = {
    model: selectedModel,
    agent: selectedAgent,
    personality: selectedPersonality,
    tools: activeTools,
    temperature: 0.7,
    maxTokens: 2000
  };

  // Create voice settings object
  const voiceSettings: VoiceSettings = {
    enabled: isSpeakerEnabled,
    voiceId: selectedVoice,
    speed: 1.0,
    pitch: 1.0
  };

  // Handle config change
  const handleConfigChange = (updates: Partial<AIConfig>) => {
    if (updates.model) setSelectedModel(updates.model);
    if (updates.agent) setSelectedAgent(updates.agent);
    if (updates.personality) setSelectedPersonality(updates.personality);
    if (updates.tools) setActiveTools(updates.tools);
  };

  // Handle voice change
  const handleVoiceChange = (updates: Partial<VoiceSettings>) => {
    if (updates.enabled !== undefined) setIsSpeakerEnabled(updates.enabled);
    if (updates.voiceId) setSelectedVoice(updates.voiceId);
  };

  // Handle test voice
  const handleTestVoice = async () => {
    if (!selectedVoice) return;
    try {
      const audioBlob = await voiceApi.synthesize("This is a test of the voice synthesis system.", selectedVoice);
      const audioUrl = URL.createObjectURL(audioBlob);
      
      // Stop any currently playing audio
      if (currentAudioRef.current) {
        currentAudioRef.current.pause();
        currentAudioRef.current = null;
      }
      
      const audio = new Audio(audioUrl);
      currentAudioRef.current = audio;
      
      setIsSpeaking(true);
      
      audio.addEventListener('ended', () => {
        setIsSpeaking(false);
        URL.revokeObjectURL(audioUrl);
        currentAudioRef.current = null;
        showNotificationMessage("Voice test completed!");
      });
      
      audio.addEventListener('error', (e) => {
        console.error('Audio playback error:', e);
        setIsSpeaking(false);
        URL.revokeObjectURL(audioUrl);
        currentAudioRef.current = null;
        showNotificationMessage("Voice test failed!");
      });
      
      await audio.play();
    } catch (error) {
      console.error('Error testing voice:', error);
      showNotificationMessage("Voice test failed!");
      setIsSpeaking(false);
    }
  };

  // Toggle speaker function
  const handleToggleSpeaker = () => {
    const newState = !isSpeakerEnabled;
    setIsSpeakerEnabled(newState);
    
    console.log('[Voice] Speaker toggled:', newState ? 'ON' : 'OFF');
    console.log('[Voice] Selected voice:', selectedVoice);
    console.log('[Voice] Available voices:', availableVoices.length);
    
    if (newState) {
      // Turning on - check if voice is available
      if (!selectedVoice && availableVoices.length > 0) {
        setSelectedVoice(availableVoices[0].id);
        console.log('[Voice] Auto-selected voice:', availableVoices[0].id);
        showNotificationMessage(`Voice enabled: ${availableVoices[0].name}`);
      } else if (selectedVoice) {
        const voice = availableVoices.find(v => v.id === selectedVoice);
        showNotificationMessage(`Voice enabled: ${voice?.name || selectedVoice}`);
      } else {
        showNotificationMessage('Voice enabled but no voices available');
      }
    } else {
      // Turning off - stop any currently playing audio
      if (currentAudioRef.current) {
        currentAudioRef.current.pause();
        currentAudioRef.current = null;
        setIsSpeaking(false);
      }
      showNotificationMessage('Voice disabled');
    }
  };

  // Show notification
  const showNotificationMessage = (message: string) => {
    setNotificationMessage(message);
    setShowNotification(true);
    setTimeout(() => setShowNotification(false), 3000);
  };

  // Handle login success
  const handleLoginSuccess = () => {
    setShowLogin(false);
    showNotificationMessage('Successfully logged in!');
  };

  // Handle register success
  const handleRegisterSuccess = () => {
    setShowRegister(false);
    showNotificationMessage('Successfully registered!');
  };

  // Usage stats (mock data - replace with actual tracking)
  const usageStats = {
    inputTokens: 0,
    outputTokens: 0,
    totalCost: 0
  };

  // Render both pages with slider transition
  return (
    <TemplateLayout>
      {/* Legal Components */}
      {!isAgeVerified && (
        <DynamicComponent 
          component="AgeGate" 
          onVerified={() => {
            // Handle age verification
            setIsAgeVerified(true);
            localStorage.setItem('age_verified', 'true');
            console.log('Age verified');
          }} 
        />
      )}
      <DynamicComponent component="CookieDisclaimer" />
      
      <div className="h-screen flex flex-col">
        {/* Top Menu Bar - Persistent across pages */}
        <div className="relative z-50">
          <DynamicComponent
            component="TopMenuBar"
            onShowLogin={() => setShowLogin(true)}
            onShowRegister={() => setShowRegister(true)}
            onViewProductDetails={handleViewProductDetails}
          />
        </div>
        
        {/* Page Content with Slider */}
        <div className="flex-1 relative overflow-hidden">
          <PageSlider>
            {/* Landing Page */}
            <LandingPage />
            
            {/* Chat Page */}
            <div className="h-full flex relative overflow-hidden">
          {/* Hamburger Menu Button */}
          <div ref={hamburgerRef} className="fixed top-16 sm:top-20 left-2 sm:left-4 z-50">
            <DynamicComponent
              component="HamburgerMenu"
              isOpen={isPanelOpen}
              onClick={() => setIsPanelOpen(!isPanelOpen)}
            />
          </div>

          {/* Configuration Panel */}
          <div ref={panelRef}>
            <DynamicComponent
              component="ConfigurationPanel"
              isOpen={isPanelOpen}
              onClose={() => setIsPanelOpen(false)}
              presets={presets}
            selectedPersonality={selectedPersonality}
            isModelLoaded={isModelLoaded}
            onPresetLoad={(preset: Preset) => {
              setSelectedPersonality(preset.personality);
              setSelectedAgent(preset.agent);
              setActiveTools(preset.tools || []);
            }}
            configDetails={configDetails}
            availableVoices={availableVoices}
            selectedVoice={selectedVoice}
            onVoiceChange={(voiceId: string) => setSelectedVoice(voiceId)}
            isSpeakerEnabled={isSpeakerEnabled}
            onToggleSpeaker={handleToggleSpeaker}
            activeTools={activeTools}
            currentTemplate={currentTemplate}
            availableTemplates={availableTemplates}
            onTemplateChange={switchTemplate}
          />
          </div>

          {/* Main Chat Area with Floating Container */}
          <FloatingChatContainer 
            className={`flex-1 transition-all duration-300 ${isPanelOpen ? 'sm:ml-80' : ''}`}
            isPanelOpen={isPanelOpen}>
            <div className="flex-1 flex flex-col bg-white/95 backdrop-blur-sm h-full">
              {/* Chat Header */}
              <DynamicComponent
                component="ChatHeader"
                isModelLoaded={isModelLoaded}
                selectedModel={selectedModel}
                selectedPersonality={selectedPersonality}
                presets={presets}
                isSpeaking={isSpeaking}
                isFullscreen={isFullscreen}
                onToggleFullscreen={() => setIsFullscreen(!isFullscreen)}
                onCopyChat={() => {
                  const chatText = messages.map(m => `${m.role}: ${m.content}`).join('\n');
                  navigator.clipboard.writeText(chatText);
                  showNotificationMessage('Chat copied to clipboard!');
                }}
                onClearSession={handleNewConversation}
                messages={messages}
                sessionId={sessionId}
                isPanelOpen={isPanelOpen}
              />

              {/* Chat Messages */}
              <DynamicComponent
                component="ChatMessages"
                messages={messages}
                isTyping={isSending}
                messagesEndRef={messagesEndRef}
                isModelLoaded={isModelLoaded}
              />

              {/* Chat Input Area */}
              <DynamicComponent
                component="ChatInputArea"
                inputMessage={inputMessage}
                onInputChange={setInputMessage}
                onSendMessage={handleSendMessage}
                onKeyDown={(e: React.KeyboardEvent) => {
                  // Use enhanced input key handler for history and autocorrect
                  handleInputKeyDown(e);
                }}
                isModelLoaded={isModelLoaded}
                isSending={isSending}
                isRecording={isRecording}
                isTranscribing={isTranscribing}
                transcript={transcript}
                micMode={micMode}
                onToggleVoiceRecording={handleVoiceRecord}
                isSpeakerEnabled={isSpeakerEnabled}
                onToggleSpeaker={handleToggleSpeaker}
                isSpeaking={isSpeaking}
                showTemplates={showTemplates}
                onToggleTemplates={() => setShowTemplates(!showTemplates)}
                // Enhanced features
                inputRef={enhancedInputRef}
                autoCorrectSuggestions={suggestions}
                showAutoCorrectSuggestions={showSuggestions}
                onApplySuggestion={applySuggestion}
                onDismissSuggestions={dismissSuggestions}
                onUseTemplate={(template: ConversationTemplate) => {
                  setInputMessage(template.message);
                  setShowTemplates(false);
                }}
              />
            </div>
          </FloatingChatContainer>
        </div>

          </PageSlider>
        </div>
        
        {/* Notification */}
        <DynamicComponent
          component="Notification"
          show={showNotification}
          message={notificationMessage}
        />

        {/* Login Modal */}
        {showLogin && (
          <DynamicComponent
            component="Login"
            onClose={() => setShowLogin(false)}
            onSubmit={handleLoginSuccess}
            onRegister={() => {
              setShowLogin(false);
              setShowRegister(true);
            }}
          />
        )}
        
        {/* Register Modal */}
        {showRegister && (
          <DynamicComponent
            component="Register"
            onClose={() => setShowRegister(false)}
            onSubmit={handleRegisterSuccess}
            onLogin={() => {
              setShowRegister(false);
              setShowLogin(true);
            }}
          />
        )}
      </div>
    </TemplateLayout>
  );
}

function App() {
  return (
    <AuthProvider>
      <ComplianceProvider>
        <TemplateContextProvider>
          <PageProvider>
            <CartProvider>
              <FloatingChatProvider>
                <AppContent />
              </FloatingChatProvider>
            </CartProvider>
          </PageProvider>
        </TemplateContextProvider>
      </ComplianceProvider>
    </AuthProvider>
  );
}

export default App;