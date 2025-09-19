import React, { useState, useEffect, useRef } from 'react';
import { MessageCircle, X, Send, Minimize2, Maximize2, Bot, User, Zap, Hash, Clock, RotateCcw } from 'lucide-react';

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  responseTime?: number; // in seconds
  tokenCount?: number;
  promptTokens?: number;
  completionTokens?: number;
}

// Busy animation activities
const busyActivities = [
  { icon: '🔍', text: 'Analyzing your request' },
  { icon: '🧠', text: 'Processing information' },
  { icon: '📊', text: 'Evaluating options' },
  { icon: '💭', text: 'Formulating response' },
  { icon: '⚡', text: 'Optimizing answer' },
  { icon: '🎯', text: 'Finalizing details' }
];

// Custom scrollbar styles
const scrollbarStyles = `
  .custom-scrollbar::-webkit-scrollbar {
    width: 6px;
  }
  .custom-scrollbar::-webkit-scrollbar-track {
    background: transparent;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb {
    background-color: rgba(156, 163, 175, 0.5);
    border-radius: 3px;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb:hover {
    background-color: rgba(156, 163, 175, 0.8);
  }
  .dark .custom-scrollbar::-webkit-scrollbar-thumb {
    background-color: rgba(75, 85, 99, 0.5);
  }
  .dark .custom-scrollbar::-webkit-scrollbar-thumb:hover {
    background-color: rgba(75, 85, 99, 0.8);
  }
`;

const ChatWidget: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [isMaximized, setIsMaximized] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [currentActivity, setCurrentActivity] = useState(busyActivities[0]);
  const [messageStartTime, setMessageStartTime] = useState<number | null>(null);
  const [isBusy, setIsBusy] = useState(false);
  const [totalTokens, setTotalTokens] = useState(0);

  // Drag state
  const [isDragging, setIsDragging] = useState(false);
  const [position, setPosition] = useState({ x: window.innerWidth - 420, y: window.innerHeight - 700 });
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  // Resize state
  const [isResizing, setIsResizing] = useState(false);
  const [size, setSize] = useState({ width: 380, height: 600 });
  const [resizeStart, setResizeStart] = useState({ x: 0, y: 0, width: 380, height: 600 });

  const ws = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // WebSocket connection management
  useEffect(() => {
    if (isOpen && !ws.current) {
      connectWebSocket();
    }

    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [isOpen]);

  // Handle dragging
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (isDragging) {
        const newX = e.clientX - dragStart.x;
        const newY = e.clientY - dragStart.y;

        // Keep window within viewport
        const maxX = window.innerWidth - size.width - 20;
        const maxY = window.innerHeight - 60;

        setPosition({
          x: Math.min(Math.max(20, newX), maxX),
          y: Math.min(Math.max(20, newY), maxY)
        });
      }

      if (isResizing) {
        const newWidth = resizeStart.width + (e.clientX - resizeStart.x);
        const newHeight = resizeStart.height + (e.clientY - resizeStart.y);

        setSize({
          width: Math.min(Math.max(320, newWidth), window.innerWidth - 40),
          height: Math.min(Math.max(400, newHeight), window.innerHeight - 100)
        });
      }
    };

    const handleMouseUp = () => {
      setIsDragging(false);
      setIsResizing(false);
    };

    if (isDragging || isResizing) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging, isResizing, dragStart, resizeStart, size.width]);

  const connectWebSocket = () => {
    // Connect to the chat WebSocket endpoint
    const wsUrl = 'ws://localhost:5024/chat/ws';
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
    };
  };

  const handleWebSocketMessage = (data: any) => {
    switch (data.type) {
      case 'connection':
        setSessionId(data.session_id);
        setMessages([{
          id: Date.now().toString(),
          role: 'system',
          content: 'Welcome! How can I assist you today?',
          timestamp: new Date()
        }]);
        break;

      case 'typing':
        setIsTyping(data.status === 'start');
        setIsBusy(data.status === 'start');
        if (data.status === 'start') {
          setMessageStartTime(Date.now());
          // Start rotating through activities
          const intervalId = setInterval(() => {
            setCurrentActivity(busyActivities[Math.floor(Math.random() * busyActivities.length)]);
          }, 1500);
          // Store interval ID to clear later
          (window as any).typingIntervalId = intervalId;
        } else {
          // Clear the interval when typing stops
          if ((window as any).typingIntervalId) {
            clearInterval((window as any).typingIntervalId);
            delete (window as any).typingIntervalId;
          }
        }
        break;

      case 'response':
      case 'message':  // Handle both 'response' and 'message' types
        setIsTyping(false);
        setIsBusy(false);
        // Clear typing interval
        if ((window as any).typingIntervalId) {
          clearInterval((window as any).typingIntervalId);
          delete (window as any).typingIntervalId;
        }
        // Only add assistant messages, skip echoing user messages
        if (data.role === 'assistant') {
          const responseTime = messageStartTime ? (Date.now() - messageStartTime) / 1000 : undefined;
          setMessages(prev => [...prev, {
            id: Date.now().toString(),
            role: 'assistant',
            content: data.content || data.message,  // Handle both content and message fields
            timestamp: new Date(),
            responseTime,
            tokenCount: data.token_count,
            promptTokens: data.prompt_tokens,
            completionTokens: data.completion_tokens
          }]);
          setMessageStartTime(null);
          // Update total token count
          if (data.token_count) {
            setTotalTokens(prev => prev + data.token_count);
          }
        }
        break;

      case 'error':
        setIsTyping(false);
        setIsBusy(false);
        setMessages(prev => [...prev, {
          id: Date.now().toString(),
          role: 'system',
          content: `Error: ${data.message}`,
          timestamp: new Date()
        }]);
        break;
    }
  };

  const sendMessage = () => {
    if (!inputMessage.trim() || !ws.current || !isConnected || isBusy) return;

    // Add user message to chat
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputMessage,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMessage]);

    // Set busy state
    setIsBusy(true);

    // Send message through WebSocket
    ws.current.send(JSON.stringify({
      type: 'message',
      message: inputMessage,
      session_id: sessionId
    }));

    // Clear input
    setInputMessage('');
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const handleStartDrag = (e: React.MouseEvent) => {
    if ((e.target as HTMLElement).classList.contains('chat-header')) {
      setIsDragging(true);
      setDragStart({
        x: e.clientX - position.x,
        y: e.clientY - position.y
      });
    }
  };

  const handleStartResize = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsResizing(true);
    setResizeStart({
      x: e.clientX,
      y: e.clientY,
      width: size.width,
      height: size.height
    });
  };

  const toggleMaximize = () => {
    if (isMaximized) {
      setSize({ width: 380, height: 600 });
      setPosition({ x: window.innerWidth - 420, y: window.innerHeight - 700 });
    } else {
      setSize({ width: window.innerWidth - 100, height: window.innerHeight - 100 });
      setPosition({ x: 50, y: 50 });
    }
    setIsMaximized(!isMaximized);
  };

  return (
    <>
      <style dangerouslySetInnerHTML={{ __html: scrollbarStyles }} />
      {/* Floating Chat Button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 bg-gray-900 hover:bg-gray-800 text-white rounded-full p-4 shadow-lg hover:shadow-xl transition-all duration-200 z-50 group"
          aria-label="Open chat"
        >
          <MessageCircle className="h-6 w-6 group-hover:scale-110 transition-transform" />
          {messages.filter(m => m.role === 'assistant').length > 0 && (
            <span className="absolute -top-1 -right-1 bg-blue-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center animate-pulse">
              {messages.filter(m => m.role === 'assistant').length}
            </span>
          )}
        </button>
      )}

      {/* Chat Window */}
      {isOpen && (
        <div
          ref={chatRef}
          className={`fixed bg-white dark:bg-gray-900 rounded-xl shadow-2xl transition-all duration-300 z-50 flex flex-col border border-gray-200 dark:border-gray-700 ${
            isMinimized ? 'h-14' : ''
          }`}
          style={{
            left: `${position.x}px`,
            top: `${position.y}px`,
            width: isMinimized ? '320px' : `${size.width}px`,
            height: isMinimized ? '56px' : `${size.height}px`,
          }}
        >
          {/* Header */}
          <div
            className="chat-header bg-gray-50 dark:bg-gray-800 px-4 py-3 rounded-t-xl flex items-center justify-between cursor-move border-b border-gray-200 dark:border-gray-700"
            onMouseDown={handleStartDrag}
          >
            <div className="flex items-center space-x-3">
              <div className="relative">
                <Bot className="h-5 w-5 text-gray-700 dark:text-gray-300" />
                {isConnected ? (
                  <span className="absolute -bottom-1 -right-1 h-2 w-2 bg-green-500 rounded-full" />
                ) : (
                  <span className="absolute -bottom-1 -right-1 h-2 w-2 bg-red-500 rounded-full" />
                )}
              </div>
              <div className="flex-1">
                <h3 className="font-medium text-gray-900 dark:text-gray-100 text-sm">AI Assistant</h3>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  {isBusy ? '🤖 Processing...' : isConnected ? 'Online' : 'Connecting...'}
                </p>
              </div>
              {totalTokens > 0 && (
                <div className="px-2 py-1 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
                  <span className="text-xs font-medium text-purple-700 dark:text-purple-300">
                    {totalTokens} tokens
                  </span>
                </div>
              )}
            </div>
            <div className="flex items-center space-x-1">
              {totalTokens > 0 && (
                <button
                  onClick={() => {
                    setMessages([]);
                    setTotalTokens(0);
                  }}
                  className="p-1.5 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg transition-colors"
                  aria-label="Clear chat"
                  title="Clear chat and reset tokens"
                >
                  <RotateCcw className="h-4 w-4 text-gray-600 dark:text-gray-400" />
                </button>
              )}
              <button
                onClick={() => setIsMinimized(!isMinimized)}
                className="p-1.5 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg transition-colors"
                aria-label="Minimize chat"
              >
                <Minimize2 className="h-4 w-4 text-gray-600 dark:text-gray-400" />
              </button>
              <button
                onClick={toggleMaximize}
                className="p-1.5 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg transition-colors"
                aria-label="Maximize chat"
              >
                <Maximize2 className="h-4 w-4 text-gray-600 dark:text-gray-400" />
              </button>
              <button
                onClick={() => {
                  setIsOpen(false);
                  if (ws.current) {
                    ws.current.close();
                  }
                }}
                className="p-1.5 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg transition-colors"
                aria-label="Close chat"
              >
                <X className="h-4 w-4 text-gray-600 dark:text-gray-400" />
              </button>
            </div>
          </div>

          {!isMinimized && (
            <>
              {/* Messages Area */}
              <div className="flex-1 overflow-y-auto p-4 space-y-3 custom-scrollbar" style={{
                scrollbarWidth: 'thin',
                scrollbarColor: 'rgb(156 163 175) transparent'
              }}>
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex ${
                      message.role === 'user' ? 'justify-end' : 'justify-start'
                    }`}
                  >
                    <div
                      className={`max-w-[85%] rounded-2xl px-4 py-2.5 ${
                        message.role === 'user'
                          ? 'bg-gray-700 text-yellow-400 dark:bg-gray-700 dark:text-yellow-400'
                          : message.role === 'assistant'
                          ? 'bg-gray-100 dark:bg-gray-800 text-green-600 dark:text-green-400'
                          : 'bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 text-sm'
                      }`}
                    >
                      <div className="flex items-start gap-2">
                        {message.role === 'assistant' && (
                          <Bot className="h-4 w-4 mt-0.5 flex-shrink-0 opacity-70" />
                        )}
                        {message.role === 'user' && (
                          <User className="h-4 w-4 mt-0.5 flex-shrink-0 opacity-70" />
                        )}
                        <div className="flex-1">
                          <p className="whitespace-pre-wrap text-sm leading-relaxed">{message.content}</p>
                          <div className="flex flex-wrap items-center gap-3 mt-2 text-xs opacity-60">
                            <span className="flex items-center gap-1">
                              <Clock className="h-3 w-3" />
                              {formatTime(message.timestamp)}
                            </span>
                            {message.responseTime !== undefined && (
                              <span>
                                Duration: {message.responseTime.toFixed(2)}s
                              </span>
                            )}
                            {message.tokenCount !== undefined && (
                              <span className="text-purple-500 dark:text-purple-400">
                                Tokens: {message.tokenCount}
                                {message.promptTokens && message.completionTokens && (
                                  <span className="opacity-75">
                                    {' '}({message.promptTokens}+{message.completionTokens})
                                  </span>
                                )}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}

                {isTyping && (
                  <div className="flex justify-start">
                    <div className="bg-gray-100 dark:bg-gray-800 rounded-2xl px-4 py-3 max-w-[85%]">
                      <div className="flex items-center space-x-3">
                        <Bot className="h-4 w-4 text-gray-500 dark:text-gray-400" />
                        <div className="flex items-center gap-2">
                          <span className="text-lg">{currentActivity.icon}</span>
                          <span className="text-sm text-gray-600 dark:text-gray-400">
                            {currentActivity.text}
                          </span>
                          <div className="flex space-x-1">
                            <div className="w-1.5 h-1.5 bg-gray-400 dark:bg-gray-600 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                            <div className="w-1.5 h-1.5 bg-gray-400 dark:bg-gray-600 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                            <div className="w-1.5 h-1.5 bg-gray-400 dark:bg-gray-600 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </div>

              {/* Input Area */}
              <div className="border-t border-gray-200 dark:border-gray-700 p-4">
                <div className="flex items-end space-x-2">
                  <div className="flex-1 relative">
                    <textarea
                      value={inputMessage}
                      onChange={(e) => setInputMessage(e.target.value)}
                      onKeyPress={handleKeyPress}
                      placeholder={isBusy ? "AI is processing..." : isConnected ? "Type your message..." : "Connecting..."}
                      disabled={!isConnected || isBusy}
                      rows={1}
                      className="w-full px-4 py-2.5 pr-12 border border-gray-300 dark:border-gray-600 rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-gray-400 dark:focus:ring-gray-600 dark:bg-gray-800 dark:text-white disabled:opacity-50 disabled:cursor-not-allowed text-sm"
                      style={{ maxHeight: '120px' }}
                      onInput={(e) => {
                        const target = e.target as HTMLTextAreaElement;
                        target.style.height = 'auto';
                        target.style.height = Math.min(target.scrollHeight, 120) + 'px';
                      }}
                    />
                    <button
                      onClick={sendMessage}
                      disabled={!isConnected || !inputMessage.trim() || isBusy}
                      className="absolute right-2 bottom-2 p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                      aria-label="Send message"
                    >
                      <MessageCircle className="h-4 w-4" />
                    </button>
                  </div>
                </div>
                <div className="flex items-center justify-between mt-2">
                  {!isConnected ? (
                    <p className="text-xs text-orange-600 dark:text-orange-400">
                      Reconnecting to chat service...
                    </p>
                  ) : isBusy ? (
                    <p className="text-xs text-blue-600 dark:text-blue-400 animate-pulse flex items-center gap-1">
                      <span className="inline-block w-2 h-2 bg-blue-600 dark:bg-blue-400 rounded-full animate-ping"></span>
                      AI model is processing your request...
                    </p>
                  ) : (
                    <div></div>
                  )}
                  {totalTokens > 0 && (
                    <span className="text-xs text-purple-500 dark:text-purple-400 font-medium">
                      Total: {totalTokens} tokens
                    </span>
                  )}
                </div>
              </div>

              {/* Resize Handle */}
              <div
                className="absolute bottom-0 right-0 w-4 h-4 cursor-nwse-resize"
                onMouseDown={handleStartResize}
              >
                <svg className="w-4 h-4 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" />
                </svg>
              </div>
            </>
          )}
        </div>
      )}
    </>
  );
};

export default ChatWidget;