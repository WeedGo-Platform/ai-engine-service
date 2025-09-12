import React, { useState, useEffect, useRef, useCallback } from 'react';
import { modelApi, chatApi, voiceApi, authApi } from './services/api';

// Components
import TopMenuBar from './components/layout/TopMenuBar';
import ConfigurationPanel from './components/panels/ConfigurationPanel';
import ChatHeader from './components/chat/ChatHeader';
import ChatMessages from './components/chat/ChatMessages';
import ChatInputArea from './components/chat/ChatInputArea';
import Notification from './components/common/Notification';
import ConfigToggleButton from './components/common/ConfigToggleButton';
import Login from './components/Login';
import Register from './components/Register';

// Types
import { 
  Personality, 
  Tool, 
  Message, 
  Preset, 
  ConversationTemplate, 
  Voice, 
  User 
} from './types';

// Utils
import { formatTime, formatResponseTime } from './utils/formatters';

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
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  
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

  const handleToggleSpeaker = () => {
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
  };

  return (
    <div className={`min-h-screen bg-gradient-to-br from-purple-950 via-purple-900 to-purple-800 ${isFullscreen ? 'fixed inset-0 z-50' : ''}`}>
      {/* Pot Palace Top Bar */}
      <TopMenuBar
        currentUser={currentUser}
        onLogout={handleLogout}
        onShowLogin={() => setShowLogin(true)}
        onShowRegister={() => setShowRegister(true)}
      />

      {/* Notification */}
      <Notification show={showNotification} message={notificationMessage} />

      <div className="relative h-[calc(100vh-72px)]">
        {/* Floating Configuration Panel */}
        <ConfigurationPanel
          isOpen={isPanelOpen}
          onClose={() => setIsPanelOpen(false)}
          presets={presets}
          selectedPersonality={selectedPersonality}
          isModelLoaded={isModelLoaded}
          onPresetLoad={handlePresetLoad}
          configDetails={configDetails}
          availableVoices={availableVoices}
          selectedVoice={selectedVoice}
          onVoiceChange={handleVoiceChange}
          isSpeakerEnabled={isSpeakerEnabled}
          onToggleSpeaker={handleToggleSpeaker}
          activeTools={activeTools}
        />

        {/* Main Chat Interface */}
        <div className={`absolute inset-0 flex flex-col z-20 transition-all duration-300 ${
          isPanelOpen ? 'ml-80' : 'ml-0'
        }`}>
        
          {/* Toggle Panel Button */}
          <ConfigToggleButton isPanelOpen={isPanelOpen} onClick={() => setIsPanelOpen(true)} />
          
          {/* Chat Header */}
          <ChatHeader
            isModelLoaded={isModelLoaded}
            selectedModel={selectedModel}
            selectedPersonality={selectedPersonality}
            presets={presets}
            isSpeaking={isSpeaking}
            isFullscreen={isFullscreen}
            onToggleFullscreen={() => setIsFullscreen(!isFullscreen)}
            onCopyChat={copyChatHistory}
            onClearSession={clearSession}
            messages={messages}
            sessionId={sessionId}
            isPanelOpen={isPanelOpen}
          />

          {/* Chat Messages */}
          <ChatMessages
            messages={messages}
            isSending={isSending}
            isModelLoaded={isModelLoaded}
          />

          {/* Input Area */}
          <ChatInputArea
            ref={inputRef}
            inputMessage={inputMessage}
            onInputChange={setInputMessage}
            onSendMessage={sendMessage}
            onKeyPress={handleKeyPress}
            isModelLoaded={isModelLoaded}
            isSending={isSending}
            isRecording={isRecording}
            isTranscribing={isTranscribing}
            transcript={transcript}
            onToggleVoiceRecording={toggleVoiceRecording}
            isSpeakerEnabled={isSpeakerEnabled}
            onToggleSpeaker={handleToggleSpeaker}
            isSpeaking={isSpeaking}
            showTemplates={showTemplates}
            onToggleTemplates={() => setShowTemplates(!showTemplates)}
            onUseTemplate={useTemplate}
          />
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