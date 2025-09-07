import React, { useState, useEffect, useRef, useCallback } from 'react';
import { TemplateContextProvider, useTemplateContext } from './contexts/TemplateContext';
import { AuthProvider } from './contexts/AuthContext';
import { ComplianceProvider } from './contexts/ComplianceContext';
import { DynamicComponent, TemplateLayout } from './core/providers/template.provider';
import { modelApi, chatApi, voiceApi } from './services/api';
import { useClickOutside } from './hooks/useClickOutside';

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

function AppContent() {
  // Get template context
  const { currentTemplate, availableTemplates, switchTemplate } = useTemplateContext();
  
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
  
  // Auth modal state
  const [showLogin, setShowLogin] = useState(false);
  const [showRegister, setShowRegister] = useState(false);
  
  const inputRef = useRef<HTMLInputElement>(null);
  const shouldAutoSend = useRef(false);
  const messagesEndRef = useRef<HTMLDivElement>(null!);
  const hamburgerRef = useRef<HTMLDivElement>(null);
  const panelRef = useClickOutside<HTMLDivElement>(() => {
    if (isPanelOpen) {
      setIsPanelOpen(false);
    }
  }, [hamburgerRef]);

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
      
      recognitionInstance.onresult = (event: any) => {
        let interimTranscript = '';
        let finalTranscript = '';
        
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += transcript + ' ';
          } else {
            interimTranscript += transcript;
          }
        }
        
        setTranscript(finalTranscript || interimTranscript);
        
        if (finalTranscript) {
          setInputMessage(prev => prev + finalTranscript);
        }
      };
      
      recognitionInstance.onerror = (event: any) => {
        console.error('Speech recognition error:', event.error);
        setIsRecording(false);
        setIsTranscribing(false);
      };
      
      recognitionInstance.onend = () => {
        setIsRecording(false);
        setIsTranscribing(false);
      };
      
      setRecognition(recognitionInstance);
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
      const voices = await voiceApi.getVoices();
      setAvailableVoices(voices);
      if (voices.length > 0 && !selectedVoice) {
        setSelectedVoice(voices[0].id);
      }
    } catch (error) {
      console.error('Error loading voices:', error);
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
  const handleSendMessage = async () => {
    if (!inputMessage.trim() || !isModelLoaded || isSending) return;
    
    const userMessage: Message = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: inputMessage,
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsSending(true);
    
    try {
      const startTime = Date.now();
      const response = await chatApi.sendMessage(inputMessage, sessionId, selectedAgent);
      const responseTime = (Date.now() - startTime) / 1000; // Convert to seconds
      
      const assistantMessage: Message = {
        id: `msg-${Date.now()}-assistant`,
        role: 'assistant',
        content: response.response || response.message || '',
        timestamp: new Date(),
        responseTime: responseTime,
        tokens: response.metadata?.tokens || 0,
        agent: selectedAgent || 'default',
        personality: selectedPersonality || 'default',
        metadata: response.metadata
      };
      
      setMessages(prev => [...prev, assistantMessage]);
      
      // Handle voice synthesis if enabled
      if (isSpeakerEnabled && selectedVoice) {
        try {
          const audioBlob = await voiceApi.synthesize(response.response || response.message || '', selectedVoice);
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
            setIsSpeaking(false);
            URL.revokeObjectURL(audioUrl);
            currentAudioRef.current = null;
          });
          
          audio.addEventListener('error', (e) => {
            console.error('Audio playback error:', e);
            setIsSpeaking(false);
            URL.revokeObjectURL(audioUrl);
            currentAudioRef.current = null;
          });
          
          await audio.play();
        } catch (error) {
          console.error('Error synthesizing speech:', error);
          setIsSpeaking(false);
        }
      }
    } catch (error) {
      console.error('Error sending message:', error);
    } finally {
      setIsSending(false);
    }
  };

  // Handle new conversation
  const handleNewConversation = () => {
    setMessages([]);
    localStorage.removeItem(`potpalace_messages_${sessionId}`);
  };

  // Handle voice recording
  const handleVoiceRecord = () => {
    if (!recognition) return;
    
    if (isRecording) {
      recognition.stop();
    } else {
      recognition.start();
      setIsRecording(true);
      setIsTranscribing(true);
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
    
    // If turning off speaker, stop any currently playing audio
    if (!newState && currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current = null;
      setIsSpeaking(false);
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

  return (
    <TemplateLayout>
      {/* Legal Components */}
      <DynamicComponent component="AgeGate" />
      <DynamicComponent component="CookieDisclaimer" />
      
      <div className="h-screen flex flex-col">
        {/* Top Menu Bar with Template Switcher */}
        <div className="relative">
          <DynamicComponent
            component="TopMenuBar"
            onShowLogin={() => setShowLogin(true)}
            onShowRegister={() => setShowRegister(true)}
          />
          
        </div>

        {/* Main Chat Container */}
        <div className="flex-1 flex relative overflow-hidden">
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

          {/* Main Chat Area */}
          <div className="flex-1 flex flex-col bg-white/95 backdrop-blur-sm">
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
              onKeyPress={(e: React.KeyboardEvent) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage();
                }
              }}
              isModelLoaded={isModelLoaded}
              isSending={isSending}
              isRecording={isRecording}
              isTranscribing={isTranscribing}
              transcript={transcript}
              onToggleVoiceRecording={handleVoiceRecord}
              isSpeakerEnabled={isSpeakerEnabled}
              onToggleSpeaker={handleToggleSpeaker}
              isSpeaking={isSpeaking}
              showTemplates={showTemplates}
              onToggleTemplates={() => setShowTemplates(!showTemplates)}
              onUseTemplate={(template: ConversationTemplate) => {
                setInputMessage(template.message);
                setShowTemplates(false);
              }}
            />
          </div>
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
          <AppContent />
        </TemplateContextProvider>
      </ComplianceProvider>
    </AuthProvider>
  );
}

export default App;