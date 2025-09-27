/**
 * Chat Interface Component
 * Interactive chat with AGI system featuring streaming support
 * Following SOLID principles and real-time communication patterns
 */

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useChat } from '../hooks/useAGI';
import { agiApi } from '../services/agiApi';
import {
  Card, CardHeader, CardContent,
  Button, IconButton,
  Badge, StatusDot,
  Alert,
  LoadingState, Spinner,
  Modal
} from './ui';
import { IChatMessage, IChatSession, IChatRequest } from '../types';

/**
 * Main Chat Interface Component
 */
export const ChatInterface: React.FC = () => {
  const {
    messages,
    isStreaming,
    streamingContent,
    error,
    sendMessage,
    stopStreaming,
    clearMessages
  } = useChat();

  const [inputMessage, setInputMessage] = useState('');
  const [selectedModel, setSelectedModel] = useState('gpt-4');
  const [temperature, setTemperature] = useState(0.7);
  const [maxTokens, setMaxTokens] = useState(1000);
  const [showSettings, setShowSettings] = useState(false);
  const [chatHistory, setChatHistory] = useState<IChatMessage[]>([]);
  const [isTyping, setIsTyping] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingContent, chatHistory]);

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // Handle message submission
  const handleSubmit = async (e?: React.FormEvent) => {
    e?.preventDefault();

    if (!inputMessage.trim() || isStreaming) return;

    const userMessage: IChatMessage = {
      id: Date.now().toString(),
      session_id: 'default',
      role: 'user',
      content: inputMessage,
      timestamp: new Date().toISOString()
    };

    // Add user message to history
    setChatHistory(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsTyping(true);

    try {
      await sendMessage(inputMessage, {
        model_id: selectedModel,
        temperature,
        max_tokens: maxTokens,
        stream: true
      });

      // Add AI response to history after streaming completes
      if (!isStreaming && !streamingContent) {
        const lastMessage = messages[messages.length - 1];
        if (lastMessage) {
          const aiMessage: IChatMessage = {
            id: (Date.now() + 1).toString(),
            session_id: 'default',
            role: 'assistant',
            content: lastMessage.response,
            timestamp: new Date().toISOString(),
            model: selectedModel
          };
          setChatHistory(prev => [...prev, aiMessage]);
        }
      }
    } catch (err) {
      console.error('Failed to send message:', err);
    } finally {
      setIsTyping(false);
    }
  };

  // Handle Enter key press
  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  // Clear chat history
  const handleClearChat = () => {
    if (window.confirm('Are you sure you want to clear the chat history?')) {
      clearMessages();
      setChatHistory([]);
    }
  };

  // Export chat history
  const handleExportChat = () => {
    const exportData = {
      session: 'default',
      model: selectedModel,
      messages: chatHistory,
      exported_at: new Date().toISOString()
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: 'application/json'
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `chat-export-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex flex-col h-full max-h-screen">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <h2 className="text-xl font-semibold text-gray-900">AGI Chat Interface</h2>
            <StatusDot
              status={isStreaming ? 'busy' : 'online'}
              label={isStreaming ? 'Responding' : 'Ready'}
            />
          </div>

          <div className="flex items-center space-x-2">
            <Badge variant="info">{selectedModel}</Badge>
            <IconButton
              icon={<SettingsIcon />}
              onClick={() => setShowSettings(true)}
            />
            <IconButton
              icon={<ExportIcon />}
              onClick={handleExportChat}
            />
            <IconButton
              icon={<ClearIcon />}
              onClick={handleClearChat}
              variant="danger"
            />
          </div>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto bg-gray-50 px-6 py-4">
        {chatHistory.length === 0 && !streamingContent ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="p-8 bg-white rounded-lg shadow-sm">
              <ChatIcon className="w-16 h-16 mx-auto text-gray-400 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Start a Conversation
              </h3>
              <p className="text-gray-600 max-w-md">
                Begin chatting with the AGI system. Your messages will appear here.
              </p>

              <div className="mt-6 space-y-2">
                <SuggestedPrompt
                  prompt="Explain how neural networks work"
                  onClick={() => setInputMessage("Explain how neural networks work")}
                />
                <SuggestedPrompt
                  prompt="What are the latest AI trends?"
                  onClick={() => setInputMessage("What are the latest AI trends?")}
                />
                <SuggestedPrompt
                  prompt="Help me optimize my code"
                  onClick={() => setInputMessage("Help me optimize my code")}
                />
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {chatHistory.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}

            {/* Streaming content */}
            {streamingContent && (
              <MessageBubble
                message={{
                  id: 'streaming',
                  session_id: 'default',
                  role: 'assistant',
                  content: streamingContent,
                  timestamp: new Date().toISOString(),
                  model: selectedModel
                }}
                isStreaming
              />
            )}

            {/* Typing indicator */}
            {isTyping && !streamingContent && (
              <div className="flex items-center space-x-2 text-gray-500">
                <Spinner size="sm" />
                <span className="text-sm">AI is thinking...</span>
              </div>
            )}

            {/* Error message */}
            {error && (
              <Alert
                type="error"
                title="Error"
                message={error.message}
                onClose={() => {}}
              />
            )}

            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="bg-white border-t border-gray-200 px-6 py-4">
        <form onSubmit={handleSubmit}>
          <div className="flex items-end space-x-4">
            <div className="flex-1">
              <textarea
                ref={inputRef}
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Type your message here... (Shift+Enter for new line)"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                rows={3}
                disabled={isStreaming}
              />
              <div className="flex items-center justify-between mt-2">
                <div className="text-xs text-gray-500">
                  {inputMessage.length > 0 && `${inputMessage.length} characters`}
                </div>
                <div className="flex items-center space-x-2 text-xs text-gray-500">
                  <span>Temp: {temperature}</span>
                  <span>•</span>
                  <span>Max tokens: {maxTokens}</span>
                </div>
              </div>
            </div>

            <div className="flex flex-col space-y-2">
              {isStreaming ? (
                <Button
                  variant="danger"
                  onClick={stopStreaming}
                >
                  <StopIcon className="w-4 h-4 mr-2" />
                  Stop
                </Button>
              ) : (
                <Button
                  type="submit"
                  variant="primary"
                  disabled={!inputMessage.trim()}
                >
                  <SendIcon className="w-4 h-4 mr-2" />
                  Send
                </Button>
              )}
            </div>
          </div>
        </form>
      </div>

      {/* Settings Modal */}
      {showSettings && (
        <ChatSettingsModal
          selectedModel={selectedModel}
          temperature={temperature}
          maxTokens={maxTokens}
          onModelChange={setSelectedModel}
          onTemperatureChange={setTemperature}
          onMaxTokensChange={setMaxTokens}
          onClose={() => setShowSettings(false)}
        />
      )}
    </div>
  );
};

/**
 * Message Bubble Component
 */
const MessageBubble: React.FC<{
  message: IChatMessage;
  isStreaming?: boolean;
}> = ({ message, isStreaming }) => {
  const isUser = message.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`
          max-w-3xl px-4 py-3 rounded-lg
          ${isUser
            ? 'bg-blue-600 text-white'
            : 'bg-white border border-gray-200 text-gray-900'
          }
          ${isStreaming ? 'animate-pulse' : ''}
        `}
      >
        {!isUser && (
          <div className="flex items-center space-x-2 mb-2">
            <Badge variant="info" size="sm">
              {message.model || 'AI'}
            </Badge>
            {isStreaming && (
              <Badge variant="warning" size="sm">
                Streaming...
              </Badge>
            )}
          </div>
        )}

        <div className="whitespace-pre-wrap break-words">
          {message.content}
          {isStreaming && <span className="inline-block w-2 h-4 ml-1 bg-gray-400 animate-pulse" />}
        </div>

        <div className={`text-xs mt-2 ${isUser ? 'text-blue-100' : 'text-gray-500'}`}>
          {new Date(message.timestamp).toLocaleTimeString()}
          {message.tokens_used && (
            <span className="ml-2">
              • {message.tokens_used.prompt + message.tokens_used.completion} tokens
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

/**
 * Suggested Prompt Component
 */
const SuggestedPrompt: React.FC<{
  prompt: string;
  onClick: () => void;
}> = ({ prompt, onClick }) => {
  return (
    <button
      onClick={onClick}
      className="w-full text-left px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
    >
      <span className="text-sm text-gray-700">{prompt}</span>
    </button>
  );
};

/**
 * Chat Settings Modal
 */
const ChatSettingsModal: React.FC<{
  selectedModel: string;
  temperature: number;
  maxTokens: number;
  onModelChange: (model: string) => void;
  onTemperatureChange: (temp: number) => void;
  onMaxTokensChange: (tokens: number) => void;
  onClose: () => void;
}> = ({
  selectedModel,
  temperature,
  maxTokens,
  onModelChange,
  onTemperatureChange,
  onMaxTokensChange,
  onClose
}) => {
  return (
    <Modal
      isOpen
      onClose={onClose}
      title="Chat Settings"
      size="md"
    >
      <div className="space-y-6">
        {/* Model Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            AI Model
          </label>
          <select
            value={selectedModel}
            onChange={(e) => onModelChange(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="gpt-4">GPT-4</option>
            <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
            <option value="claude-2">Claude 2</option>
            <option value="palm-2">PaLM 2</option>
            <option value="llama-2">Llama 2</option>
          </select>
          <p className="text-xs text-gray-500 mt-1">
            Choose the AI model for conversations
          </p>
        </div>

        {/* Temperature Slider */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Temperature: {temperature}
          </label>
          <input
            type="range"
            min="0"
            max="2"
            step="0.1"
            value={temperature}
            onChange={(e) => onTemperatureChange(parseFloat(e.target.value))}
            className="w-full"
          />
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>Focused</span>
            <span>Balanced</span>
            <span>Creative</span>
          </div>
          <p className="text-xs text-gray-500 mt-2">
            Controls randomness in responses (0 = focused, 2 = creative)
          </p>
        </div>

        {/* Max Tokens */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Max Tokens: {maxTokens}
          </label>
          <input
            type="range"
            min="100"
            max="4000"
            step="100"
            value={maxTokens}
            onChange={(e) => onMaxTokensChange(parseInt(e.target.value))}
            className="w-full"
          />
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>100</span>
            <span>2000</span>
            <span>4000</span>
          </div>
          <p className="text-xs text-gray-500 mt-2">
            Maximum length of the response
          </p>
        </div>

        {/* System Prompt */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            System Prompt (Optional)
          </label>
          <textarea
            placeholder="You are a helpful AI assistant..."
            className="w-full px-3 py-2 border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
            rows={3}
          />
          <p className="text-xs text-gray-500 mt-1">
            Set a custom system prompt for the AI
          </p>
        </div>
      </div>

      <div className="flex justify-end space-x-3 mt-6">
        <Button variant="ghost" onClick={onClose}>
          Cancel
        </Button>
        <Button variant="primary" onClick={onClose}>
          Save Settings
        </Button>
      </div>
    </Modal>
  );
};

// Icon Components
const ChatIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
  </svg>
);

const SendIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
  </svg>
);

const StopIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z" />
  </svg>
);

const SettingsIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
  </svg>
);

const ExportIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
  </svg>
);

const ClearIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
  </svg>
);

export default ChatInterface;