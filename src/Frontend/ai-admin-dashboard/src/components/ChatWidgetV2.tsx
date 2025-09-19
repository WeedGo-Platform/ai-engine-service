import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  MessageCircle,
  X,
  Send,
  Minimize2,
  Maximize2,
  Bot,
  User,
  Hash,
  Clock,
  RotateCcw,
  Mic,
  MicOff,
  Volume2,
  Loader2,
  AlertCircle,
  Settings
} from 'lucide-react';
import { getVoiceRecordingService, AudioVisualizationData } from '../services/voiceRecording.service';
import VoiceVisualization from './chat/VoiceVisualization';

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
}

interface ChatWidgetV2Props {
  wsUrl?: string;
  defaultOpen?: boolean;
  position?: 'bottom-right' | 'bottom-left' | 'top-right' | 'top-left';
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

const ChatWidgetV2: React.FC<ChatWidgetV2Props> = ({
  wsUrl = 'ws://localhost:5024/chat/ws',
  defaultOpen = false,
  position = 'bottom-right',
  // theme = 'auto', // Reserved for future dark mode implementation
  enableVoice = true,
  maxMessages = 100
}) => {
  // UI State
  const [isOpen, setIsOpen] = useState(defaultOpen);
  const [isMinimized, setIsMinimized] = useState(false);
  const [isMaximized, setIsMaximized] = useState(false);
  const [showSettings, setShowSettings] = useState(false);

  // Chat State
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [currentActivity, setCurrentActivity] = useState(busyActivities[0]);
  const [messageStartTime, setMessageStartTime] = useState<number | null>(null);
  const [isBusy, setIsBusy] = useState(false);
  const [totalTokens, setTotalTokens] = useState(0);

  // Voice State
  const [voiceState, setVoiceState] = useState<RecordingState>('idle');
  const [voiceVisualization, setVoiceVisualization] = useState<AudioVisualizationData | null>(null);
  const [transcription, setTranscription] = useState<string>('');
  const [voicePermission, setVoicePermission] = useState<boolean>(false);

  // Responsive State
  const [isMobile, setIsMobile] = useState(false);
  const [dimensions, setDimensions] = useState({ width: 380, height: 600 });

  // Refs
  const ws = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const voiceService = useRef(getVoiceRecordingService());
  const activityInterval = useRef<NodeJS.Timeout | null>(null);

  // Initialize voice service
  useEffect(() => {
    if (enableVoice && voiceService.current.isSupported()) {
      // Set up callbacks
      voiceService.current.onData((blob) => {
        handleVoiceRecordingComplete(blob);
        setVoiceState('idle');
      });

      voiceService.current.onVisualization((data) => {
        setVoiceVisualization(data);
      });

      voiceService.current.onError((error) => {
        console.error('Voice recording error:', error);
        setVoiceState('error');
        setVoiceVisualization(null);
      });

      voiceService.current.onRecordingStateChange((isRecording) => {
        setVoiceState(isRecording ? 'recording' : 'idle');
        if (!isRecording) {
          setVoiceVisualization(null);
        }
      });

      // Request permission on mount
      voiceService.current.requestPermission().then(granted => {
        setVoicePermission(granted);
      });

      return () => {
        // Cleanup if needed
      };
    }
  }, [enableVoice]);

  // Handle responsive design
  useEffect(() => {
    const checkMobile = () => {
      const mobile = window.innerWidth < 768;
      setIsMobile(mobile);

      if (mobile) {
        setDimensions({ width: window.innerWidth - 32, height: window.innerHeight - 100 });
      } else {
        setDimensions({ width: 380, height: 600 });
      }
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Auto-scroll to bottom
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

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
          setMessageStartTime(Date.now());
          startActivityRotation();
        } else {
          stopActivityRotation();
        }
        break;

      case 'transcription':
        setTranscription(data.text);
        // Add transcribed message to chat
        const transcribedMessage: Message = {
          id: Date.now().toString(),
          role: 'user',
          content: data.text,
          timestamp: new Date(),
          isVoice: true,
          transcription: data.text
        };
        setMessages(prev => [...prev, transcribedMessage]);
        break;

      case 'response':
      case 'message':
        handleIncomingMessage(data);
        break;

      case 'error':
        handleError(data.message);
        break;
    }
  };

  const handleIncomingMessage = (data: any) => {
    setIsTyping(false);
    setIsBusy(false);
    stopActivityRotation();

    if (data.role === 'assistant') {
      const responseTime = messageStartTime ? (Date.now() - messageStartTime) / 1000 : undefined;
      const newMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: data.content || data.message,
        timestamp: new Date(),
        responseTime,
        tokenCount: data.token_count,
        promptTokens: data.prompt_tokens,
        completionTokens: data.completion_tokens
      };

      setMessages(prev => {
        const updated = [...prev, newMessage];
        // Limit messages if needed
        if (maxMessages && updated.length > maxMessages) {
          return updated.slice(-maxMessages);
        }
        return updated;
      });

      setMessageStartTime(null);

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

    // Set busy state
    setIsBusy(true);

    // Send message through WebSocket
    ws.current.send(JSON.stringify({
      type: 'message',
      message: messageToSend,
      session_id: sessionId
    }));

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

  // Voice handling
  const startVoiceRecording = async () => {
    if (voiceState === 'recording') {
      // Stop recording
      voiceService.current.stopRecording();
    } else {
      // Check permission first
      if (!voicePermission) {
        setVoiceState('requesting');
        const granted = await voiceService.current.requestPermission();
        setVoicePermission(granted);
        setVoiceState('idle');
        if (!granted) return;
      }
      // Start recording
      try {
        await voiceService.current.startRecording();
        setVoiceState('recording');
      } catch (error) {
        console.error('Failed to start recording:', error);
        setVoiceState('error');
      }
    }
  };

  const cancelVoiceRecording = () => {
    voiceService.current.stopRecording();
    setTranscription('');
    setVoiceState('idle');
  };

  const handleVoiceRecordingComplete = async (blob: Blob) => {
    if (!ws.current || !isConnected) return;

    // Convert blob to base64
    const base64Audio = await voiceService.current.blobToBase64(blob);

    // Send voice data through WebSocket
    ws.current.send(JSON.stringify({
      type: 'voice',
      audio: base64Audio,
      session_id: sessionId
    }));
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getPositionClasses = () => {
    const base = 'fixed z-50';
    switch (position) {
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
          className={`${getPositionClasses()} ${
            isMobile ? 'w-[calc(100vw-2rem)]' : ''
          } bg-white dark:bg-gray-900 rounded-2xl shadow-2xl transition-all duration-300 flex flex-col ${
            isMinimized ? 'h-16' : ''
          } ${isMaximized ? 'w-[calc(100vw-4rem)] h-[calc(100vh-4rem)]' : ''}`}
          style={{
            width: isMaximized ? undefined : (isMobile ? undefined : `${dimensions.width}px`),
            height: isMinimized ? '64px' : (isMaximized ? undefined : `${dimensions.height}px`)
          }}
        >
          {/* Header */}
          <div className="bg-gradient-to-r from-blue-600 to-purple-600 px-4 py-3 rounded-t-2xl flex items-center justify-between">
            <div className="flex items-center space-x-3 flex-1">
              <div className="relative">
                <Bot className="h-6 w-6 text-white" />
                <span className={`absolute -bottom-1 -right-1 h-2.5 w-2.5 rounded-full ${
                  isConnected ? 'bg-green-400' : 'bg-red-400'
                } ${isConnected ? 'animate-pulse' : ''}`} />
              </div>
              <div>
                <h3 className="font-semibold text-white text-sm">AI Assistant</h3>
                <p className="text-xs text-blue-100">
                  {isBusy ? 'Processing...' : isConnected ? 'Online' : 'Connecting...'}
                </p>
              </div>
              {totalTokens > 0 && !isMobile && (
                <div className="ml-auto mr-2 px-2 py-1 bg-white/20 backdrop-blur rounded-lg">
                  <span className="text-xs font-medium text-white flex items-center gap-1">
                    <Hash className="h-3 w-3" />
                    {totalTokens}
                  </span>
                </div>
              )}
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
              {/* Messages Area */}
              <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-gray-50 dark:bg-gray-800">
                {messages.map((message) => (
                  <div
                    key={message.id}
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
                          <div className="flex flex-wrap items-center gap-3 mt-2 text-xs opacity-60">
                            <span className="flex items-center gap-1">
                              <Clock className="h-3 w-3" />
                              {formatTime(message.timestamp)}
                            </span>
                            {message.responseTime !== undefined && (
                              <span>{message.responseTime.toFixed(2)}s</span>
                            )}
                            {message.tokenCount !== undefined && (
                              <span className="flex items-center gap-1">
                                <Hash className="h-3 w-3" />
                                {message.tokenCount}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
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
                {voiceState === 'processing' && transcription && (
                  <div className="flex justify-center">
                    <div className="bg-blue-100 dark:bg-blue-900/30 rounded-lg px-4 py-2">
                      <p className="text-sm text-blue-700 dark:text-blue-300">
                        Transcription: "{transcription}"
                      </p>
                    </div>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </div>

              {/* Voice Visualization */}
              {voiceState === 'recording' && (
                <div className="bg-gray-100 dark:bg-gray-800 px-4 py-2 border-t border-gray-200 dark:border-gray-700">
                  <VoiceVisualization
                    data={voiceVisualization}
                    isRecording={true}
                    mode="waveform"
                    height={60}
                  />
                  <div className="flex items-center justify-between mt-2">
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      Recording...
                    </span>
                    <button
                      onClick={cancelVoiceRecording}
                      className="text-xs text-red-600 hover:text-red-700 dark:text-red-400"
                    >
                      Cancel
                    </button>
                  </div>
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
                          : voiceState === 'recording'
                          ? "Recording voice..."
                          : isConnected
                          ? "Type a message or use voice..."
                          : "Connecting..."
                      }
                      disabled={!isConnected || isBusy || voiceState === 'recording'}
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
                        voiceState === 'recording'
                          ? 'bg-red-500 hover:bg-red-600 text-white animate-pulse'
                          : voiceState === 'processing'
                          ? 'bg-yellow-500 text-white'
                          : 'bg-gray-100 hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-400'
                      } disabled:opacity-30 disabled:cursor-not-allowed`}
                      aria-label={voiceState === 'recording' ? 'Stop recording' : 'Start voice recording'}
                    >
                      {voiceState === 'recording' ? (
                        <MicOff className="h-5 w-5" />
                      ) : voiceState === 'processing' ? (
                        <Loader2 className="h-5 w-5 animate-spin" />
                      ) : (
                        <Mic className="h-5 w-5" />
                      )}
                    </button>
                  )}

                  {/* Send Button */}
                  <button
                    onClick={() => sendMessage()}
                    disabled={!isConnected || !inputMessage.trim() || isBusy || voiceState === 'recording'}
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
                    {voiceState === 'requesting' && (
                      <span className="text-xs text-yellow-600 dark:text-yellow-400">
                        Requesting microphone access...
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
        </div>
      )}
    </>
  );
};

export default ChatWidgetV2;