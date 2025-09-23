import React, { useState, useRef, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
  XMarkIcon as XIcon,
  MicrophoneIcon,
  PaperAirplaneIcon,
  SpeakerWaveIcon as VolumeUpIcon,
  ArrowPathIcon as RefreshIcon,
  UserIcon,
  SparklesIcon
} from '@heroicons/react/24/outline';
import { MicrophoneIcon as MicrophoneSolidIcon } from '@heroicons/react/24/solid';
import { chatService } from '@services/chatService';
import { voiceService } from '@services/voiceService';
import toast from 'react-hot-toast';

interface ChatInterfaceProps {
  onClose: () => void;
}

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'assistant';
  timestamp: Date;
  products?: any[];
  isLoading?: boolean;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ onClose }) => {
  const { t } = useTranslation();
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      text: t('chat.welcome'),
      sender: 'assistant',
      timestamp: new Date()
    }
  ]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const recognitionRef = useRef<any>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Initialize speech recognition
  useEffect(() => {
    if (typeof window !== 'undefined' && 'webkitSpeechRecognition' in window) {
      const SpeechRecognition = (window as any).webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = true;
      recognitionRef.current.lang = 'en-US';

      recognitionRef.current.onresult = (event: any) => {
        const transcript = Array.from(event.results)
          .map((result: any) => result[0])
          .map((result: any) => result.transcript)
          .join('');

        setInputText(transcript);
      };

      recognitionRef.current.onerror = (event: any) => {
        console.error('Speech recognition error:', event.error);
        setIsListening(false);
        toast.error(t('chat.voiceError'));
      };

      recognitionRef.current.onend = () => {
        setIsListening(false);
      };
    }

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, []);

  const handleSendMessage = async () => {
    if (!inputText.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text: inputText,
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setIsLoading(true);

    try {
      // Send message to chat API
      const response = await chatService.sendMessage(inputText);

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: response.message,
        sender: 'assistant',
        timestamp: new Date(),
        products: response.products
      };

      setMessages(prev => [...prev, assistantMessage]);

      // Auto-speak response if voice was used for input
      if (isListening) {
        handleSpeak(response.message);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      toast.error(t('chat.sendError'));

      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: t('chat.errorMessage'),
        sender: 'assistant',
        timestamp: new Date()
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleVoiceInput = () => {
    if (!recognitionRef.current) {
      toast.error(t('chat.voiceNotSupported'));
      return;
    }

    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    } else {
      recognitionRef.current.start();
      setIsListening(true);
    }
  };

  const handleSpeak = (text: string) => {
    if ('speechSynthesis' in window) {
      // Cancel any ongoing speech
      window.speechSynthesis.cancel();

      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 0.9;
      utterance.pitch = 1.0;

      utterance.onstart = () => setIsSpeaking(true);
      utterance.onend = () => setIsSpeaking(false);

      window.speechSynthesis.speak(utterance);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const clearChat = () => {
    setMessages([
      {
        id: '1',
        text: t('chat.welcome'),
        sender: 'assistant',
        timestamp: new Date()
      }
    ]);
  };

  // Suggested prompts
  const suggestedPrompts = [
    t('chat.prompts.findSativa'),
    t('chat.prompts.bestEdibles'),
    t('chat.prompts.helpSleep'),
    t('chat.prompts.firstTime')
  ];

  const handleSuggestedPrompt = (prompt: string) => {
    setInputText(prompt);
    inputRef.current?.focus();
  };

  return (
    <div className="fixed bottom-4 right-4 w-96 h-[600px] bg-white rounded-lg shadow-2xl flex flex-col z-50 animate-slide-in">
      {/* Header */}
      <div className="bg-gradient-to-r from-primary-500 to-primary-600 text-white p-4 rounded-t-lg flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <SparklesIcon className="h-6 w-6" />
          <div>
            <h3 className="font-bold text-lg">WeedGo AI Assistant</h3>
            <p className="text-xs text-primary-100">{t('chat.subtitle')}</p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={clearChat}
            className="p-1 hover:bg-primary-400 rounded-full transition-colors"
            title={t('chat.clear')}
          >
            <RefreshIcon className="h-5 w-5" />
          </button>
          <button
            onClick={onClose}
            className="p-1 hover:bg-primary-400 rounded-full transition-colors"
          >
            <XIcon className="h-5 w-5" />
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] ${
                message.sender === 'user'
                  ? 'bg-primary-500 text-white rounded-l-lg rounded-br-lg'
                  : 'bg-white text-gray-800 rounded-r-lg rounded-bl-lg shadow-md'
              } p-3`}
            >
              <div className="flex items-start space-x-2">
                {message.sender === 'assistant' && (
                  <SparklesIcon className="h-5 w-5 text-primary-500 flex-shrink-0 mt-0.5" />
                )}
                <div className="flex-1">
                  <p className="text-sm">{message.text}</p>

                  {/* Product Cards */}
                  {message.products && message.products.length > 0 && (
                    <div className="mt-3 space-y-2">
                      {message.products.slice(0, 3).map((product) => (
                        <div
                          key={product.sku}
                          className="bg-gray-50 rounded-lg p-2 cursor-pointer hover:bg-gray-100 transition-colors"
                          onClick={() => window.location.href = `/products/${product.sku}`}
                        >
                          <div className="flex items-center space-x-2">
                            <img
                              src={product.image || '/placeholder.jpg'}
                              alt={product.name}
                              className="w-12 h-12 object-cover rounded"
                            />
                            <div className="flex-1">
                              <h4 className="text-xs font-semibold text-gray-800">{product.name}</h4>
                              <p className="text-xs text-gray-600">{product.brand}</p>
                              <p className="text-xs font-bold text-primary-600">${product.price}</p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
                {message.sender === 'user' && (
                  <UserIcon className="h-5 w-5 flex-shrink-0 mt-0.5" />
                )}
              </div>
              {message.sender === 'assistant' && !message.isLoading && (
                <button
                  onClick={() => handleSpeak(message.text)}
                  className="mt-2 text-xs text-primary-500 hover:text-primary-600 flex items-center space-x-1"
                >
                  <VolumeUpIcon className="h-3 w-3" />
                  <span>{isSpeaking ? t('chat.stopSpeaking') : t('chat.speak')}</span>
                </button>
              )}
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-white rounded-r-lg rounded-bl-lg shadow-md p-3">
              <div className="flex items-center space-x-2">
                <SparklesIcon className="h-5 w-5 text-primary-500 animate-pulse" />
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                </div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Prompts */}
      {messages.length === 1 && (
        <div className="px-4 py-2 border-t border-gray-200 bg-gray-50">
          <p className="text-xs text-gray-500 mb-2">{t('chat.suggestions')}</p>
          <div className="flex flex-wrap gap-2">
            {suggestedPrompts.map((prompt, index) => (
              <button
                key={index}
                onClick={() => handleSuggestedPrompt(prompt)}
                className="text-xs px-2 py-1 bg-white border border-gray-300 rounded-full hover:bg-primary-50 hover:border-primary-300 transition-colors"
              >
                {prompt}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <div className="p-4 border-t border-gray-200 bg-white rounded-b-lg">
        <div className="flex items-center space-x-2">
          <button
            onClick={handleVoiceInput}
            className={`p-2 rounded-full transition-all ${
              isListening
                ? 'bg-red-500 text-white animate-pulse'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
            title={t('chat.voiceInput')}
          >
            {isListening ? (
              <MicrophoneSolidIcon className="h-5 w-5" />
            ) : (
              <MicrophoneIcon className="h-5 w-5" />
            )}
          </button>
          <input
            ref={inputRef}
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={isListening ? t('chat.listening') : t('chat.placeholder')}
            className="flex-1 px-3 py-2 border border-gray-300 rounded-full focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm"
            disabled={isLoading || isListening}
          />
          <button
            onClick={handleSendMessage}
            disabled={!inputText.trim() || isLoading}
            className={`p-2 rounded-full transition-all ${
              inputText.trim() && !isLoading
                ? 'bg-primary-500 text-white hover:bg-primary-600'
                : 'bg-gray-100 text-gray-400'
            }`}
          >
            <PaperAirplaneIcon className="h-5 w-5 transform rotate-90" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;