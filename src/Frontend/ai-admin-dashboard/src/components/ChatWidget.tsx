import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  MessageCircle,
  X,
  Send,
  Minimize2,
  Maximize2,
  Bot,
  User,
  Clock,
  RotateCcw,
  Mic,
  MicOff,
  Volume2,
  VolumeX,
  Loader2,
  AlertCircle,
  Settings,
  Copy,
  Check,
  GripVertical
} from 'lucide-react';
// Voice Visualization (optional - can be removed if not needed)
// import VoiceVisualization from './chat/VoiceVisualization';
import { useAuth } from '../contexts/AuthContext';
import { voiceApi } from '../services/voiceApi';
import { getApiUrl } from '../config/app.config';

type RecordingState = 'idle' | 'recording' | 'processing' | 'error' | 'requesting';

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  responseTime?: number;
  tokenCount?: number;
  promptTokens?: number;
  completionTokens?: number;
  isVoice?: boolean;
  transcription?: string;
  products?: any[];
  quick_actions?: any[];
}

interface ChatWidgetProps {
  wsUrl?: string;
  defaultOpen?: boolean;
  initialPosition?: 'bottom-right' | 'bottom-left' | 'top-right' | 'top-left';
  theme?: 'light' | 'dark' | 'auto';
  enableVoice?: boolean;
  maxMessages?: number;
}

// Enhanced busy animation activities
const busyActivities = [
  { icon: '🔍', text: 'Analyzing your request' },
  { icon: '🧠', text: 'Processing information' },
  { icon: '📊', text: 'Evaluating options' },
  { icon: '💭', text: 'Formulating response' },
  { icon: '⚡', text: 'Optimizing answer' },
  { icon: '🎯', text: 'Finalizing details' }
];

const ChatWidget: React.FC<ChatWidgetProps> = ({
  wsUrl = 'ws://localhost:5024/api/v1/chat/ws',
  defaultOpen = false,
  initialPosition = 'bottom-right',
  // theme = 'auto', // Reserved for future dark mode implementation
  enableVoice = true,
  maxMessages = 100
}) => {
  // Get user context from AuthContext
  const { user } = useAuth();

  // UI State
  const [isOpen, setIsOpen] = useState(defaultOpen);
  const [isMinimized, setIsMinimized] = useState(false);
  const [isMaximized, setIsMaximized] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [isCopied, setIsCopied] = useState(false);

  // Chat State
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [currentActivity, setCurrentActivity] = useState(busyActivities[0]);
  const [isBusy, setIsBusy] = useState(false);
  const [totalTokens, setTotalTokens] = useState(0);

  // Agent and Personality State
  const [selectedAgent, setSelectedAgent] = useState('assistant');
  const [selectedPersonality, setSelectedPersonality] = useState('');
  const [availableAgents, setAvailableAgents] = useState<any[]>([]);
  const [availablePersonalities, setAvailablePersonalities] = useState<any[]>([]);
  const [loadingAgents, setLoadingAgents] = useState(false);
  const [loadingPersonalities, setLoadingPersonalities] = useState(false);

  // Use ref for timing to avoid stale closure issues
  const messageStartTimeRef = useRef<number | null>(null);

  // Voice State
  const [voiceState, setVoiceState] = useState<RecordingState>('idle');
  const [voicePermission, setVoicePermission] = useState<boolean>(false);
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState<string>('');
  const [liveTranscript, setLiveTranscript] = useState<string>('');
  // const [finalizedTranscript, setFinalizedTranscript] = useState<string>(''); // Removed - not being read
  const silenceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pauseTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const lastSpeechTimeRef = useRef<number>(Date.now());
  const pendingTranscriptRef = useRef<string>('');
  const sendMessageRef = useRef<(text: string) => void>();

  // TTS State - restore preference from localStorage
  const [isSpeakerEnabled, setIsSpeakerEnabled] = useState<boolean>(() => {
    const saved = localStorage.getItem('chatWidgetTTSEnabled');
    return saved === 'true';
  });
  const [isSpeaking, setIsSpeaking] = useState<boolean>(false);
  const currentAudioRef = useRef<HTMLAudioElement | null>(null);

  // Web Speech API Recognition
  const [recognition, setRecognition] = useState<any>(null);
  const [isTranscribing, setIsTranscribing] = useState<boolean>(false);

  // Responsive State
  const [isMobile, setIsMobile] = useState(false);
  const [dimensions, setDimensions] = useState(() => {
    const saved = localStorage.getItem('chatWidgetDimensions');
    return saved ? JSON.parse(saved) : { width: 380, height: 600 };
  });

  // Dragging and Position State
  const [position, setPosition] = useState(() => {
    const saved = localStorage.getItem('chatWidgetPosition');
    return saved ? JSON.parse(saved) : { x: window.innerWidth - 420, y: window.innerHeight - 650 };
  });
  const [isDragging, setIsDragging] = useState(false);
  const [isResizing, setIsResizing] = useState(false);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const [resizeStart, setResizeStart] = useState({ width: 0, height: 0, x: 0, y: 0 });

  // Refs
  const ws = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  // Remove voiceService - we'll use Web Speech API directly
  const activityInterval = useRef<NodeJS.Timeout | null>(null);
  const chatWindowRef = useRef<HTMLDivElement>(null);

  // Fetch available agents
  useEffect(() => {
    const fetchAgents = async () => {
      setLoadingAgents(true);
      try {
        const token = localStorage.getItem('weedgo_auth_access_token');
        const response = await fetch(getApiUrl('/api/admin/agents'), {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });
        if (response.ok) {
          const data = await response.json();
          setAvailableAgents(data.agents || []);

          // If we have agents and assistant is available, fetch its personalities
          const assistantAgent = data.agents?.find((a: any) => a.id === 'assistant');
          if (assistantAgent) {
            fetchPersonalities('assistant');
          }
        }
      } catch (error) {
        console.error('Failed to fetch agents:', error);
      } finally {
        setLoadingAgents(false);
      }
    };

    fetchAgents();
  }, []);

  // Fetch personalities for selected agent
  const fetchPersonalities = async (agentId: string) => {
    setLoadingPersonalities(true);
    try {
      const token = localStorage.getItem('weedgo_auth_access_token');
      const response = await fetch(getApiUrl(`/api/admin/agents/${agentId}/personalities`), {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      if (response.ok) {
        const data = await response.json();
        setAvailablePersonalities(data.personalities || []);

        // Always select the first available personality
        if (data.personalities?.length > 0) {
          setSelectedPersonality(data.personalities[0].id);
        }
      }
    } catch (error) {
      console.error('Failed to fetch personalities:', error);
    } finally {
      setLoadingPersonalities(false);
    }
  };

  // Initialize Web Speech API
  useEffect(() => {
    if (enableVoice && ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      const recognition = new SpeechRecognition();

      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'en-US';
      recognition.maxAlternatives = 1;

      let allFinalText = '';
      let lastResultIndex = 0;
      let lastSentText = '';

      recognition.onstart = () => {
        console.log('Speech recognition started');
        setVoiceState('recording');
        setIsRecording(true);
        setIsTranscribing(true);
        lastSpeechTimeRef.current = Date.now();
      };

      recognition.onresult = (event: any) => {
        let interimText = '';
        let newFinalText = '';

        // Process all results from the last processed index
        for (let i = lastResultIndex; i < event.results.length; i++) {
          const result = event.results[i];

          if (!result || !result[0]) {
            continue;
          }

          const transcriptText = String(result[0].transcript);

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

        // Update all transcript states immediately for live display
        setTranscript(completeTranscript);
        setLiveTranscript(interimText);
        // setFinalizedTranscript(allFinalText); // Removed - not being read
        pendingTranscriptRef.current = allFinalText; // Store for pause detection

        // Keep transcribing state active
        setIsTranscribing(interimText.length > 0 || allFinalText.length > 0);

        // Reset timers on any speech activity
        lastSpeechTimeRef.current = Date.now();

        // Clear existing timers
        if (pauseTimerRef.current) {
          clearTimeout(pauseTimerRef.current);
          pauseTimerRef.current = null;
        }
        if (silenceTimerRef.current) {
          clearTimeout(silenceTimerRef.current);
          silenceTimerRef.current = null;
        }

        // Set pause timer (2 seconds) - sends accumulated text as a chunk
        if (allFinalText && allFinalText.trim()) {
          pauseTimerRef.current = setTimeout(() => {
            const textToSend = allFinalText.trim();
            if (textToSend && textToSend !== lastSentText) {
              console.log('Sending transcript after pause:', textToSend);
              // Send this chunk as a message
              sendMessageRef.current?.(textToSend);
              lastSentText = textToSend;

              // Clear the pending transcript since we've sent it
              allFinalText = '';
              lastResultIndex = event.results.length;
              setTranscript(''); // Clear the display after sending
              setLiveTranscript('');
              pendingTranscriptRef.current = '';
            }
          }, 2000); // 2 seconds pause = send chunk
        }

        // Set silence timer (2 seconds) - stops recording completely
        silenceTimerRef.current = setTimeout(() => {
          console.log('Auto-stopping due to silence');

          // Send any remaining transcript before stopping
          const remainingText = allFinalText.trim();
          if (remainingText && remainingText !== lastSentText) {
            console.log('Sending remaining transcript before stop:', remainingText);
            sendMessageRef.current?.(remainingText);
          }

          recognition.stop();
          // Keep the transcript visible for a moment to show it was sent
          setTimeout(() => {
            setTranscript('');
            setLiveTranscript('');
          }, 500);
        }, 2000); // 2 seconds of silence = stop
      };

      recognition.onerror = (event: any) => {
        console.error('Speech recognition error:', event.error);
        setVoiceState('error');
        setIsRecording(false);
        setIsTranscribing(false);

        // Clear timers
        if (pauseTimerRef.current) {
          clearTimeout(pauseTimerRef.current);
          pauseTimerRef.current = null;
        }
        if (silenceTimerRef.current) {
          clearTimeout(silenceTimerRef.current);
          silenceTimerRef.current = null;
        }
      };

      recognition.onend = () => {
        console.log('Speech recognition ended');
        setVoiceState('idle');
        setIsRecording(false);
        setIsTranscribing(false);

        // Clear timers
        if (pauseTimerRef.current) {
          clearTimeout(pauseTimerRef.current);
          pauseTimerRef.current = null;
        }
        if (silenceTimerRef.current) {
          clearTimeout(silenceTimerRef.current);
          silenceTimerRef.current = null;
        }
      };

      setRecognition(recognition);
      setVoicePermission(true);
    }
  }, [enableVoice]);

  // Handle responsive design
  useEffect(() => {
    const checkMobile = () => {
      const mobile = window.innerWidth < 768;
      setIsMobile(mobile);

      if (mobile) {
        setDimensions({ width: window.innerWidth - 32, height: window.innerHeight - 100 });
      }
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Persist dimensions and position
  useEffect(() => {
    if (!isMobile) {
      localStorage.setItem('chatWidgetDimensions', JSON.stringify(dimensions));
    }
  }, [dimensions, isMobile]);

  useEffect(() => {
    if (!isMobile && !isMaximized) {
      localStorage.setItem('chatWidgetPosition', JSON.stringify(position));
    }
  }, [position, isMobile, isMaximized]);

  // Auto-scroll to bottom
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // Copy chat functionality
  const copyChat = () => {
    // Format the chat messages for copying
    const chatText = messages.map(msg => {
      const timestamp = msg.timestamp ? new Date(msg.timestamp).toLocaleString() : '';
      const role = msg.role === 'user' ? 'You' : 'AI Assistant';
      return `[${timestamp}] ${role}: ${msg.content}`;
    }).join('\n\n');

    // Add header information
    const header = `Chat Export - ${new Date().toLocaleString()}\nAgent: ${availableAgents.find(a => a.id === selectedAgent)?.name || 'AI Assistant'}\nPersonality: ${selectedPersonality || 'Default'}\n${'='.repeat(50)}\n\n`;

    const fullText = header + chatText;

    // Copy to clipboard
    navigator.clipboard.writeText(fullText).then(() => {
      setIsCopied(true);
      setTimeout(() => setIsCopied(false), 2000);
    }).catch(err => {
      console.error('Failed to copy chat:', err);
      handleError('Failed to copy chat to clipboard');
    });
  };

  // Drag handlers
  const handleDragStart = (e: React.MouseEvent) => {
    if (isMaximized || isMobile) return;

    const rect = chatWindowRef.current?.getBoundingClientRect();
    if (rect) {
      setDragOffset({
        x: e.clientX - rect.left,
        y: e.clientY - rect.top
      });
      setIsDragging(true);
    }
  };

  const handleDrag = useCallback((e: MouseEvent) => {
    if (!isDragging) return;

    const newX = e.clientX - dragOffset.x;
    const newY = e.clientY - dragOffset.y;

    // Keep window within viewport bounds
    const maxX = window.innerWidth - dimensions.width;
    const maxY = window.innerHeight - dimensions.height;

    setPosition({
      x: Math.max(0, Math.min(newX, maxX)),
      y: Math.max(0, Math.min(newY, maxY))
    });
  }, [isDragging, dragOffset, dimensions]);

  const handleDragEnd = useCallback(() => {
    setIsDragging(false);
  }, []);

  // Resize handlers
  const handleResizeStart = (e: React.MouseEvent) => {
    if (isMaximized || isMobile) return;

    e.stopPropagation();
    setResizeStart({
      width: dimensions.width,
      height: dimensions.height,
      x: e.clientX,
      y: e.clientY
    });
    setIsResizing(true);
  };

  const handleResize = useCallback((e: MouseEvent) => {
    if (!isResizing) return;

    const deltaX = e.clientX - resizeStart.x;
    const deltaY = e.clientY - resizeStart.y;

    const newWidth = Math.max(320, Math.min(resizeStart.width + deltaX, window.innerWidth - position.x));
    const newHeight = Math.max(400, Math.min(resizeStart.height + deltaY, window.innerHeight - position.y));

    setDimensions({
      width: newWidth,
      height: newHeight
    });
  }, [isResizing, resizeStart, position]);

  const handleResizeEnd = useCallback(() => {
    setIsResizing(false);
  }, []);

  // Add mouse event listeners for drag and resize
  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleDrag);
      document.addEventListener('mouseup', handleDragEnd);
      return () => {
        document.removeEventListener('mousemove', handleDrag);
        document.removeEventListener('mouseup', handleDragEnd);
      };
    }
  }, [isDragging, handleDrag, handleDragEnd]);

  useEffect(() => {
    if (isResizing) {
      document.addEventListener('mousemove', handleResize);
      document.addEventListener('mouseup', handleResizeEnd);
      return () => {
        document.removeEventListener('mousemove', handleResize);
        document.removeEventListener('mouseup', handleResizeEnd);
      };
    }
  }, [isResizing, handleResize, handleResizeEnd]);

  // Load chat history when component opens
  useEffect(() => {
    const loadChatHistory = async () => {
      if (isOpen && user?.user_id && messages.length === 0) {
        try {
          console.log('Loading chat history for user:', user.user_id);
          const response = await fetch(`http://localhost:5024/api/v1/chat/history/${user.user_id}?limit=20`);

          if (response.ok) {
            const history = await response.json();
            console.log('Chat history loaded:', history);

            if (history.messages && history.messages.length > 0) {
              // Convert history messages to our Message format
              const historicalMessages: Message[] = history.messages.map((msg: any) => ({
                id: `history-${Date.now()}-${Math.random()}`,
                role: msg.role || (msg.user_message ? 'user' : 'assistant'),
                content: msg.user_message || msg.ai_response || msg.content || '',
                timestamp: new Date(msg.created_at || msg.timestamp),
                isVoice: false,
                responseTime: msg.response_time
              }));

              // Sort messages by timestamp (oldest first)
              historicalMessages.sort((a, b) => a.timestamp.getTime() - b.timestamp.getTime());

              // Add a separator message
              const separatorMessage: Message = {
                id: `separator-${Date.now()}`,
                role: 'system',
                content: '--- Previous Conversations ---',
                timestamp: new Date()
              };

              setMessages([...historicalMessages, separatorMessage]);
            }
          } else {
            console.error('Failed to load chat history:', response.statusText);
          }
        } catch (error) {
          console.error('Error loading chat history:', error);
        }
      }
    };

    loadChatHistory();
  }, [isOpen, user?.user_id]); // Only depend on isOpen and user.user_id, not messages

  // WebSocket connection management
  useEffect(() => {
    if (isOpen && !ws.current) {
      connectWebSocket();
    }

    return () => {
      if (ws.current) {
        ws.current.close();
        ws.current = null;
      }
      if (activityInterval.current) {
        clearInterval(activityInterval.current);
      }
    };
  }, [isOpen]);

  const connectWebSocket = () => {
    ws.current = new WebSocket(wsUrl);

    ws.current.onopen = () => {
      setIsConnected(true);
      console.log('Connected to chat service');

      // Send initial session configuration with agent and personality
      if (ws.current?.readyState === WebSocket.OPEN) {
        ws.current.send(JSON.stringify({
          type: 'session_update',
          agent: selectedAgent,
          personality: selectedPersonality
        }));
      }
    };

    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleWebSocketMessage(data);
    };

    ws.current.onerror = (error) => {
      console.error('WebSocket error:', error);
      setIsConnected(false);
    };

    ws.current.onclose = () => {
      setIsConnected(false);
      ws.current = null;
      console.log('Disconnected from chat service');

      // Attempt to reconnect after 3 seconds
      setTimeout(() => {
        if (isOpen) {
          connectWebSocket();
        }
      }, 3000);
    };
  };

  const handleWebSocketMessage = (data: any) => {
    switch (data.type) {
      case 'connection':
        setSessionId(data.session_id);
        setMessages([{
          id: Date.now().toString(),
          role: 'system',
          content: 'Welcome! How can I assist you today? You can type or use voice input.',
          timestamp: new Date()
        }]);
        break;

      case 'typing':
        setIsTyping(data.status === 'start');
        setIsBusy(data.status === 'start');
        if (data.status === 'start') {
          messageStartTimeRef.current = Date.now();
          startActivityRotation();
        } else {
          stopActivityRotation();
        }
        break;

      case 'transcription':
        // Handle streaming transcription
        if (data.isFinal) {
          // Final transcription
          setTranscript(data.text);
          setLiveTranscript('');
          pendingTranscriptRef.current = data.text;

          if (data.text && data.text.trim()) {
            const transcribedMessage: Message = {
              id: Date.now().toString(),
              role: 'user',
              content: data.text,
              timestamp: new Date(),
              isVoice: true,
              transcription: data.text
            };
            setMessages(prev => [...prev, transcribedMessage]);
          }
        } else {
          // Live/partial transcription update
          setLiveTranscript(data.text || '');
        }
        break;

      case 'response':
      case 'message':
        // Log what we received
        console.log('[ChatWidget] Received message:', {
          type: data.type,
          hasProducts: !!data.products,
          productCount: data.products?.length || 0,
          hasQuickActions: !!data.quick_actions,
          messageKeys: Object.keys(data)
        });

        // Ensure we set the role to 'assistant' for responses
        handleIncomingMessage({
          ...data,
          role: 'assistant',
          products: data.products,
          quick_actions: data.quick_actions
        });
        break;

      case 'error':
        handleError(data.message || data.error || 'An unknown error occurred');
        break;

      case 'session_updated':
        // Handle session update confirmation from backend
        console.log('[ChatWidget] Session update confirmed from backend:', {
          agent: data.agent,
          personality: data.personality,
          message: data.message
        });
        // Optionally show a system message to confirm the change
        setMessages(prev => [...prev, {
          id: Date.now().toString(),
          role: 'system',
          content: data.message || `Agent changed to ${data.agent} with personality ${data.personality}`,
          timestamp: new Date()
        }]);
        break;

      default:
        console.log('[ChatWidget] Unhandled message type:', data.type, data);
    }
  };

  const handleIncomingMessage = async (data: any) => {
    setIsTyping(false);
    setIsBusy(false);
    stopActivityRotation();

    if (data.role === 'assistant') {
      // Use response_time from backend only
      const responseTime = data.response_time;
      const newMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: data.content || data.message,
        timestamp: new Date(),
        responseTime,
        tokenCount: data.token_count,
        promptTokens: data.prompt_tokens,
        completionTokens: data.completion_tokens,
        products: data.products,
        quick_actions: data.quick_actions
      };

      setMessages(prev => {
        const updated = [...prev, newMessage];
        // Limit messages if needed
        if (maxMessages && updated.length > maxMessages) {
          return updated.slice(-maxMessages);
        }
        return updated;
      });

      messageStartTimeRef.current = null;

      // Handle Text-to-Speech if enabled
      if (isSpeakerEnabled && (data.content || data.message)) {
        try {
          const audioBlob = await voiceApi.synthesize(data.content || data.message);
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
          audio.onended = () => {
            setIsSpeaking(false);
            URL.revokeObjectURL(audioUrl);
            currentAudioRef.current = null;
          };

          audio.onerror = () => {
            setIsSpeaking(false);
            URL.revokeObjectURL(audioUrl);
            currentAudioRef.current = null;
          };

          await audio.play();
        } catch (error) {
          console.error('TTS Error:', error);
          setIsSpeaking(false);
        }
      }

      if (data.token_count) {
        setTotalTokens(prev => prev + data.token_count);
      }
    }
  };

  const handleError = (message: string) => {
    setIsTyping(false);
    setIsBusy(false);
    stopActivityRotation();

    setMessages(prev => [...prev, {
      id: Date.now().toString(),
      role: 'system',
      content: `Error: ${message}`,
      timestamp: new Date()
    }]);
  };

  const startActivityRotation = () => {
    if (activityInterval.current) return;

    activityInterval.current = setInterval(() => {
      setCurrentActivity(busyActivities[Math.floor(Math.random() * busyActivities.length)]);
    }, 1500);
  };

  const stopActivityRotation = () => {
    if (activityInterval.current) {
      clearInterval(activityInterval.current);
      activityInterval.current = null;
    }
  };

  const sendMessage = (content?: string) => {
    const messageToSend = content || inputMessage.trim();
    if (!messageToSend || !ws.current || !isConnected || isBusy) return;

    // Add user message to chat
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: messageToSend,
      timestamp: new Date(),
      isVoice: !!content
    };
    setMessages(prev => [...prev, userMessage]);

    // Set busy state and start timing
    setIsBusy(true);
    messageStartTimeRef.current = Date.now();

    // Log user context status
    console.log('[ChatWidget] Sending message with user context:', {
      has_user: !!user,
      user_id: user?.user_id,
      user_email: user?.email,
      message_length: messageToSend.length,
      session_id: sessionId
    });

    // Send message through WebSocket with user_id if available
    const messagePayload = {
      type: 'message',
      message: messageToSend,
      session_id: sessionId,
      ...(user?.user_id && { user_id: user.user_id })
    };

    console.log('[ChatWidget] WebSocket message payload:', messagePayload);

    // Check WebSocket is ready before sending
    if (ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(messagePayload));
    } else {
      console.error('[ChatWidget] WebSocket not ready. State:', ws.current.readyState);
      // Optionally queue the message or show an error
      handleError('Connection not ready. Please wait a moment and try again.');
      return;
    }

    // Clear input
    if (!content) {
      setInputMessage('');
      if (inputRef.current) {
        inputRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  // Monitor voice activity for auto-send and auto-stop
  // Voice activity monitoring is now handled by the Web Speech API

  // Clear voice-related timers
  // Timer clearing is now handled in the Web Speech API event handlers

  // Send transcript as message
  const sendTranscriptAsMessage = (text: string) => {
    if (!text.trim() || !ws.current || ws.current.readyState !== WebSocket.OPEN) return;

    const message: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: text,
      timestamp: new Date(),
      isVoice: true,
      transcription: text
    };

    setMessages(prev => [...prev, message]);
    setIsBusy(true);
    messageStartTimeRef.current = Date.now();

    // Send via WebSocket
    ws.current.send(JSON.stringify({
      type: 'message',
      message: text,
      session_id: sessionId,
      ...(user?.user_id && { user_id: user.user_id })
    }));
  };

  // Voice streaming is now handled by Web Speech API

  // Voice recording stop is now handled in startVoiceRecording function

  // Update sendMessageRef whenever sendTranscriptAsMessage changes
  useEffect(() => {
    sendMessageRef.current = sendTranscriptAsMessage;
  }, [sessionId, user]);

  // Voice handling
  const startVoiceRecording = async () => {
    if (!recognition) return;

    if (isRecording) {
      console.log('Manually stopping recording');

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
        sendMessage(pendingTranscriptRef.current.trim());
      }

      recognition.stop();
    } else {
      console.log('Starting recording');

      // Stop any currently playing audio when starting to record
      if (currentAudioRef.current) {
        currentAudioRef.current.pause();
        currentAudioRef.current = null;
        setIsSpeaking(false);
      }
      // Also stop browser's speech synthesis if active
      if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }

      // Clear any previous transcripts
      setTranscript('');
      setLiveTranscript('');
      // setFinalizedTranscript(''); // Removed - not being read
      pendingTranscriptRef.current = '';

      // Start recognition
      recognition.start();
      setIsRecording(true);
      setIsTranscribing(true);
      setVoiceState('recording');

      // Update activity time
      lastSpeechTimeRef.current = Date.now();
    }
  };

  const cancelVoiceRecording = () => {
    if (recognition && isRecording) {
      recognition.stop();
    }
    setTranscript('');
    setLiveTranscript('');
    // setFinalizedTranscript(''); // Removed - not being read
    setVoiceState('idle');
    setIsRecording(false);
    setIsTranscribing(false);
  };

  // Toggle speaker/TTS
  const handleToggleSpeaker = () => {
    const newState = !isSpeakerEnabled;
    setIsSpeakerEnabled(newState);

    // If turning off, stop any currently playing audio
    if (!newState && currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current = null;
      setIsSpeaking(false);
    }

    // Store preference
    localStorage.setItem('chatWidgetTTSEnabled', newState.toString());
  };

  // Voice recording completion is now handled by Web Speech API

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getPositionClasses = () => {
    const base = 'fixed z-50';
    switch (initialPosition) {
      case 'bottom-left':
        return `${base} bottom-6 left-6`;
      case 'top-right':
        return `${base} top-6 right-6`;
      case 'top-left':
        return `${base} top-6 left-6`;
      case 'bottom-right':
      default:
        return `${base} bottom-6 right-6`;
    }
  };

  return (
    <>
      {/* Floating Chat Button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className={`${getPositionClasses()} bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white rounded-full p-4 shadow-lg hover:shadow-xl transition-all duration-300 group`}
          aria-label="Open chat"
        >
          <MessageCircle className="h-6 w-6 group-hover:scale-110 transition-transform" />
          {messages.filter(m => m.role === 'assistant').length > 0 && (
            <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center animate-pulse">
              {messages.filter(m => m.role === 'assistant').length}
            </span>
          )}
        </button>
      )}

      {/* Chat Window */}
      {isOpen && (
        <div
          ref={chatWindowRef}
          className={`${
            isMobile || isMaximized ? getPositionClasses() : 'fixed'
          } ${
            isMobile ? 'w-[calc(100vw-2rem)]' : ''
          } bg-white dark:bg-gray-900 rounded-2xl shadow-2xl transition-all duration-300 flex flex-col ${
            isMinimized ? 'h-16' : ''
          } ${isMaximized ? 'w-[calc(100vw-4rem)] h-[calc(100vh-4rem)]' : ''} ${
            isDragging || isResizing ? 'select-none' : ''
          } z-50`}
          style={{
            width: isMaximized ? undefined : (isMobile ? undefined : `${dimensions.width}px`),
            height: isMinimized ? '64px' : (isMaximized ? undefined : `${dimensions.height}px`),
            left: !isMobile && !isMaximized ? `${position.x}px` : undefined,
            top: !isMobile && !isMaximized ? `${position.y}px` : undefined,
            cursor: isDragging ? 'grabbing' : undefined
          }}
        >
          {/* Header */}
          <div
            className="bg-gradient-to-r from-blue-600 to-purple-600 px-4 py-3 rounded-t-2xl flex items-center justify-between"
            onMouseDown={handleDragStart}
            style={{ cursor: !isMaximized && !isMobile ? (isDragging ? 'grabbing' : 'grab') : 'default' }}
          >
            <div className="flex items-center space-x-3">
              <div className="relative">
                <Bot className="h-6 w-6 text-white" />
                <span className={`absolute -bottom-1 -right-1 h-2.5 w-2.5 rounded-full ${
                  isConnected ? 'bg-green-400' : 'bg-red-400'
                } ${isConnected ? 'animate-pulse' : ''}`} />
              </div>
              <div>
                <h3 className="font-semibold text-white text-sm">
                  {availableAgents.find(a => a.id === selectedAgent)?.name || 'AI Assistant'}
                </h3>
                <p className="text-xs text-blue-100">
                  {selectedPersonality ? `${selectedPersonality} • ` : ''}{isBusy ? 'Processing...' : isConnected ? 'Online' : 'Connecting...'}
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-1">
              {!isMobile && (
                <>
                  <button
                    onClick={() => setShowSettings(!showSettings)}
                    className="p-1.5 hover:bg-white/20 rounded-lg transition-colors"
                    aria-label="Settings"
                  >
                    <Settings className="h-4 w-4 text-white" />
                  </button>
                  {totalTokens > 0 && (
                    <button
                      onClick={() => {
                        setMessages([]);
                        setTotalTokens(0);
                      }}
                      className="p-1.5 hover:bg-white/20 rounded-lg transition-colors"
                      aria-label="Clear chat"
                    >
                      <RotateCcw className="h-4 w-4 text-white" />
                    </button>
                  )}
                </>
              )}
              {messages.length > 0 && (
                <button
                  onClick={copyChat}
                  className="p-1.5 hover:bg-white/20 rounded-lg transition-colors"
                  aria-label="Copy chat"
                >
                  {isCopied ? (
                    <Check className="h-4 w-4 text-green-300" />
                  ) : (
                    <Copy className="h-4 w-4 text-white" />
                  )}
                </button>
              )}
              <button
                onClick={() => setIsMinimized(!isMinimized)}
                className="p-1.5 hover:bg-white/20 rounded-lg transition-colors"
                aria-label="Minimize"
              >
                <Minimize2 className="h-4 w-4 text-white" />
              </button>
              {!isMobile && (
                <button
                  onClick={() => setIsMaximized(!isMaximized)}
                  className="p-1.5 hover:bg-white/20 rounded-lg transition-colors"
                  aria-label="Maximize"
                >
                  <Maximize2 className="h-4 w-4 text-white" />
                </button>
              )}
              <button
                onClick={() => {
                  setIsOpen(false);
                  if (ws.current) {
                    ws.current.close();
                  }
                }}
                className="p-1.5 hover:bg-white/20 rounded-lg transition-colors"
                aria-label="Close"
              >
                <X className="h-4 w-4 text-white" />
              </button>
            </div>
          </div>

          {!isMinimized && (
            <>
              {/* Settings Panel */}
              {showSettings && (
                <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-4">
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Select Agent
                      </label>
                      <select
                        value={selectedAgent}
                        onChange={async (e) => {
                          const newAgent = e.target.value;
                          console.log('[ChatWidget] Agent changed to:', newAgent);
                          setSelectedAgent(newAgent);
                          setSelectedPersonality(''); // Clear personality while loading

                          // Fetch personalities for the new agent
                          await fetchPersonalities(newAgent);

                          // Send update to backend when agent changes
                          console.log('[ChatWidget] Sending agent update to backend:', newAgent);
                          if (ws.current?.readyState === WebSocket.OPEN) {
                            ws.current.send(JSON.stringify({
                              type: 'session_update',
                              agent: newAgent,
                              personality: '' // Clear personality on agent change
                            }));
                          }
                        }}
                        disabled={loadingAgents}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
                      >
                        {loadingAgents ? (
                          <option>Loading agents...</option>
                        ) : (
                          availableAgents.map(agent => (
                            <option key={agent.id} value={agent.id}>
                              {agent.name}
                            </option>
                          ))
                        )}
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Select Personality
                      </label>
                      <select
                        value={selectedPersonality}
                        onChange={(e) => {
                          const newPersonality = e.target.value;
                          console.log('[ChatWidget] Personality changed to:', newPersonality);
                          setSelectedPersonality(newPersonality);
                          // Update session if connected
                          console.log('[ChatWidget] Sending personality update to backend:', {
                            agent: selectedAgent,
                            personality: newPersonality
                          });
                          if (ws.current?.readyState === WebSocket.OPEN) {
                            ws.current.send(JSON.stringify({
                              type: 'session_update',
                              agent: selectedAgent,
                              personality: newPersonality
                            }));
                          }
                        }}
                        disabled={loadingPersonalities || !selectedAgent}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
                      >
                        {loadingPersonalities ? (
                          <option>Loading personalities...</option>
                        ) : availablePersonalities.length === 0 ? (
                          <option>No personalities available</option>
                        ) : (
                          availablePersonalities.map(personality => (
                            <option key={personality.id} value={personality.id}>
                              {personality.name}
                            </option>
                          ))
                        )}
                      </select>
                    </div>

                    <div className="flex justify-end">
                      <button
                        onClick={() => setShowSettings(false)}
                        className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
                      >
                        Apply Settings
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* Messages Area */}
              <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-gray-50 dark:bg-gray-800">
                {messages.map((message) => (
                  <div key={message.id}>
                    {/* Special rendering for system separator messages */}
                    {message.role === 'system' && message.content.includes('Previous Conversations') ? (
                      <div className="flex items-center my-4">
                        <div className="flex-1 border-t border-gray-300 dark:border-gray-600"></div>
                        <div className="px-3 text-xs text-gray-500 dark:text-gray-400 italic">
                          {message.content.replace(/^-+\s*|\s*-+$/g, '')}
                        </div>
                        <div className="flex-1 border-t border-gray-300 dark:border-gray-600"></div>
                      </div>
                    ) : (
                    <div
                      className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                      <div
                        className={`max-w-[85%] rounded-2xl px-4 py-2.5 ${
                          message.role === 'user'
                            ? 'bg-gradient-to-r from-blue-500 to-blue-600 text-white'
                            : message.role === 'assistant'
                            ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-md'
                            : 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-200'
                        }`}
                      >
                        <div className="flex items-start gap-2">
                          {message.role === 'assistant' && (
                            <Bot className="h-4 w-4 mt-0.5 flex-shrink-0 opacity-70" />
                          )}
                          {message.role === 'user' && (
                            <>
                              {message.isVoice && (
                                <Volume2 className="h-4 w-4 mt-0.5 flex-shrink-0 opacity-70" />
                              )}
                              <User className="h-4 w-4 mt-0.5 flex-shrink-0 opacity-70" />
                            </>
                          )}
                          <div className="flex-1">
                            <p className="whitespace-pre-wrap text-sm leading-relaxed">
                              {message.content}
                            </p>

                            {/* Product Cards */}
                            {message.products && message.products.length > 0 && (
                              <div className="mt-3 space-y-2">
                                <div className="text-xs font-semibold text-gray-500 dark:text-gray-400 mb-2">
                                  {message.products.length} Products Found
                                </div>
                                <div className="grid grid-cols-1 gap-2 max-h-96 overflow-y-auto">
                                  {message.products.map((product: any, idx: number) => (
                                    <div key={idx} className="bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-3 hover:shadow-md transition-shadow">
                                      <div className="flex gap-3">
                                        {product.image && (
                                          <img
                                            src={product.image}
                                            alt={product.name}
                                            className="w-16 h-16 object-cover rounded-lg flex-shrink-0"
                                            onError={(e) => {
                                              (e.target as HTMLImageElement).src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64"><rect fill="%23ddd" width="64" height="64"/></svg>';
                                            }}
                                          />
                                        )}
                                        <div className="flex-1 min-w-0">
                                          <div className="text-xs font-semibold text-gray-900 dark:text-gray-100 truncate">
                                            {idx + 1}. {product.name}
                                          </div>
                                          {product.brand && (
                                            <div className="text-xs text-gray-600 dark:text-gray-400">
                                              {product.brand}
                                            </div>
                                          )}
                                          <div className="flex items-center gap-2 mt-1 text-xs">
                                            {product.thcContent?.display && (
                                              <span className="px-1.5 py-0.5 bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300 rounded">
                                                THC: {product.thcContent.display}
                                              </span>
                                            )}
                                            {product.cbdContent?.display && (
                                              <span className="px-1.5 py-0.5 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 rounded">
                                                CBD: {product.cbdContent.display}
                                              </span>
                                            )}
                                          </div>
                                          <div className="flex items-center justify-between mt-1">
                                            <span className="text-sm font-bold text-gray-900 dark:text-gray-100">
                                              ${product.price?.toFixed(2)}
                                            </span>
                                            {product.plantType && (
                                              <span className="text-xs text-gray-500 dark:text-gray-400 capitalize">
                                                {product.plantType}
                                              </span>
                                            )}
                                          </div>
                                        </div>
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}

                            {/* Quick Actions */}
                            {message.quick_actions && message.quick_actions.length > 0 && (
                              <div className="mt-3">
                                <div className="text-xs font-semibold text-gray-500 dark:text-gray-400 mb-2">
                                  What would you like to see?
                                </div>
                                <div className="flex flex-wrap gap-2">
                                  {message.quick_actions.map((action: any, idx: number) => (
                                    <button
                                      key={idx}
                                      onClick={() => {
                                        // Send the action value as a new message
                                        const messageToSend = action.value || action.label;
                                        setInputMessage(messageToSend);
                                        // Automatically send the message
                                        setTimeout(() => {
                                          const form = document.querySelector('form');
                                          if (form) {
                                            form.dispatchEvent(new Event('submit', { bubbles: true }));
                                          }
                                        }, 50);
                                      }}
                                      className="inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-700 rounded-full hover:from-blue-100 hover:to-indigo-100 dark:hover:from-blue-900/30 dark:hover:to-indigo-900/30 hover:border-blue-300 dark:hover:border-blue-600 transition-all duration-200 shadow-sm hover:shadow-md"
                                    >
                                      {action.icon && <span className="text-base">{action.icon}</span>}
                                      <span>{action.label}</span>
                                    </button>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                    )}
                    {/* Metadata outside bubble - timestamp, duration, tokens */}
                    {(message.timestamp || message.responseTime !== undefined || message.tokenCount !== undefined) && (
                      <div className={`mt-1.5 px-2 ${
                        message.role === 'user' ? 'text-right' : 'text-left'
                      }`}>
                        <div className={`inline-flex flex-wrap items-center gap-2 text-xs italic text-gray-400 dark:text-gray-500`}>
                          <span className="flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            {formatTime(message.timestamp)}
                          </span>
                          {message.role === 'assistant' && message.responseTime !== undefined && (
                            <>
                              <span className="text-gray-300 dark:text-gray-600">•</span>
                              <span>{message.responseTime > 0 ? message.responseTime.toFixed(2) : '< 0.01'}s</span>
                            </>
                          )}
                          {message.tokenCount !== undefined && (
                            <>
                              <span className="text-gray-300 dark:text-gray-600">•</span>
                              <span>{message.tokenCount} tokens</span>
                            </>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                ))}

                {/* Typing Indicator */}
                {isTyping && (
                  <div className="flex justify-start">
                    <div className="bg-white dark:bg-gray-700 rounded-2xl px-4 py-3 shadow-md max-w-[85%]">
                      <div className="flex items-center space-x-3">
                        <Bot className="h-4 w-4 text-gray-500 dark:text-gray-400" />
                        <div className="flex items-center gap-2">
                          <span className="text-lg">{currentActivity.icon}</span>
                          <span className="text-sm text-gray-600 dark:text-gray-400">
                            {currentActivity.text}
                          </span>
                          <div className="flex space-x-1">
                            <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                            <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                            <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Voice Transcription */}
                {(isRecording || isTranscribing || transcript) && (
                  <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
                    <div className="flex items-center gap-3">
                      {isRecording && (
                        <div className="flex items-center gap-2">
                          <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
                          <span className="text-sm font-medium text-red-600 dark:text-red-400">Recording...</span>
                        </div>
                      )}
                      {isTranscribing && !isRecording && (
                        <div className="flex items-center gap-2">
                          <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
                          <span className="text-sm font-medium text-blue-600 dark:text-blue-400">Transcribing...</span>
                        </div>
                      )}
                      {transcript && (
                        <div className="flex-1 px-3 py-1 bg-white dark:bg-gray-700 rounded-lg border border-gray-300 dark:border-gray-600">
                          <p className="text-sm text-gray-800 dark:text-gray-200">
                            <span className="font-medium text-blue-600 dark:text-blue-400">Transcript:</span> {transcript}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </div>

              {/* Voice Status and Live Transcript */}
              {isRecording && (
                <div className="bg-gray-100 dark:bg-gray-800 px-4 py-3 border-t border-gray-200 dark:border-gray-700">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <div className="flex gap-1">
                        <span className="w-1 h-4 bg-blue-500 rounded-full animate-pulse" />
                        <span className="w-1 h-4 bg-blue-500 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }} />
                        <span className="w-1 h-4 bg-blue-500 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }} />
                      </div>
                      <span className="text-xs text-gray-600 dark:text-gray-400">Listening...</span>
                    </div>
                    <button
                      onClick={cancelVoiceRecording}
                      className="text-xs text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
                    >
                      Cancel
                    </button>
                  </div>

                  {/* Live Transcript Display */}
                  {(transcript || liveTranscript) && (
                    <div className="p-2 bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700">
                      <div className="text-xs text-gray-500 dark:text-gray-400 mb-1 flex items-center gap-1">
                        <span className="animate-pulse text-red-500">●</span> Live Transcript
                      </div>
                      <div className="text-sm text-gray-800 dark:text-gray-200">
                        {transcript || liveTranscript}
                      </div>
                      <div className="text-xs text-gray-400 dark:text-gray-500 mt-1 italic">
                        (Pause 1.5s to send • 3s silence to stop)
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Input Area */}
              <div className="border-t border-gray-200 dark:border-gray-700 p-4 bg-white dark:bg-gray-900">
                <div className="flex items-end space-x-2">
                  <div className="flex-1 relative">
                    <textarea
                      ref={inputRef}
                      value={inputMessage}
                      onChange={(e) => setInputMessage(e.target.value)}
                      onKeyPress={handleKeyPress}
                      placeholder={
                        isBusy
                          ? "AI is processing..."
                          : isRecording
                          ? "Recording voice..."
                          : isConnected
                          ? "Type a message or use voice..."
                          : "Connecting..."
                      }
                      disabled={!isConnected || isBusy || isRecording}
                      rows={1}
                      className="w-full px-4 py-2.5 pr-12 border border-gray-300 dark:border-gray-600 rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-white disabled:opacity-50 disabled:cursor-not-allowed text-sm transition-colors"
                      style={{ maxHeight: '120px' }}
                      onInput={(e) => {
                        const target = e.target as HTMLTextAreaElement;
                        target.style.height = 'auto';
                        target.style.height = Math.min(target.scrollHeight, 120) + 'px';
                      }}
                    />
                  </div>

                  {/* Voice Button */}
                  {enableVoice && voicePermission && (
                    <button
                      onClick={startVoiceRecording}
                      disabled={!isConnected || isBusy}
                      className={`p-2.5 rounded-xl transition-all ${
                        isRecording
                          ? 'bg-red-500 hover:bg-red-600 text-white animate-pulse'
                          : isTranscribing
                          ? 'bg-yellow-500 text-white'
                          : 'bg-gray-100 hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-400'
                      } disabled:opacity-30 disabled:cursor-not-allowed`}
                      aria-label={isRecording ? 'Stop recording' : 'Start voice recording'}
                    >
                      {isRecording ? (
                        <MicOff className="h-5 w-5" />
                      ) : isTranscribing ? (
                        <Loader2 className="h-5 w-5 animate-spin" />
                      ) : (
                        <Mic className="h-5 w-5" />
                      )}
                    </button>
                  )}

                  {/* Speaker Button */}
                  <button
                    onClick={handleToggleSpeaker}
                    className={`p-2.5 rounded-xl transition-all ${
                      isSpeakerEnabled
                        ? isSpeaking
                          ? 'bg-green-500 text-white animate-pulse'
                          : 'bg-green-500 hover:bg-green-600 text-white'
                        : 'bg-gray-100 hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-400'
                    }`}
                    aria-label={isSpeakerEnabled ? 'Disable text-to-speech' : 'Enable text-to-speech'}
                    title={isSpeakerEnabled ? 'Text-to-speech enabled' : 'Enable text-to-speech'}
                  >
                    {isSpeakerEnabled ? (
                      <Volume2 className="h-5 w-5" />
                    ) : (
                      <VolumeX className="h-5 w-5" />
                    )}
                  </button>

                  {/* Send Button */}
                  <button
                    onClick={() => sendMessage()}
                    disabled={!isConnected || !inputMessage.trim() || isBusy || isRecording}
                    className="p-2.5 bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white rounded-xl disabled:opacity-30 disabled:cursor-not-allowed transition-all"
                    aria-label="Send message"
                  >
                    <Send className="h-5 w-5" />
                  </button>
                </div>

                {/* Status Bar */}
                <div className="flex items-center justify-between mt-2">
                  <div className="flex items-center gap-2">
                    {!isConnected && (
                      <span className="text-xs text-orange-600 dark:text-orange-400 flex items-center gap-1">
                        <AlertCircle className="h-3 w-3" />
                        Reconnecting...
                      </span>
                    )}
                    {isBusy && (
                      <span className="text-xs text-blue-600 dark:text-blue-400 flex items-center gap-1">
                        <Loader2 className="h-3 w-3 animate-spin" />
                        Processing...
                      </span>
                    )}
                    {voiceState === 'error' && (
                      <span className="text-xs text-red-600 dark:text-red-400">
                        Voice recognition error. Please try again.
                      </span>
                    )}
                  </div>
                  {totalTokens > 0 && (
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      Session: {totalTokens} tokens
                    </span>
                  )}
                </div>
              </div>
            </>
          )}

          {/* Resize Handle */}
          {!isMobile && !isMaximized && !isMinimized && (
            <div
              className="absolute bottom-0 right-0 w-4 h-4 cursor-se-resize"
              onMouseDown={handleResizeStart}
              style={{
                background: 'linear-gradient(135deg, transparent 50%, rgba(156, 163, 175, 0.5) 50%)'
              }}
            >
              <div className="absolute bottom-1 right-1">
                <GripVertical className="h-3 w-3 text-gray-400 rotate-45" />
              </div>
            </div>
          )}
        </div>
      )}
    </>
  );
};

export default ChatWidget;