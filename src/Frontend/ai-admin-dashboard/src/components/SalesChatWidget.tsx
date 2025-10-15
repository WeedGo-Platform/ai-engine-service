import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  MessageCircle,
  X,
  Send,
  Minimize2,
  Bot,
  User,
  Clock,
  Mic,
  MicOff,
  Volume2,
  VolumeX,
  Loader2,
  AlertCircle,
  PenLine
} from 'lucide-react';
import { voiceApi } from '../services/voiceApi';

type RecordingState = 'idle' | 'recording' | 'processing' | 'error';

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  responseTime?: number;
  tokens?: number;
  isVoice?: boolean;
}

interface SalesChatWidgetProps {
  wsUrl?: string;
  enableVoice?: boolean;
}

// Sales-focused busy activities
const busyActivities = [
  { icon: '💡', text: 'Analyzing your needs' },
  { icon: '📊', text: 'Checking pricing options' },
  { icon: '🎯', text: 'Finding the perfect fit' },
  { icon: '✨', text: 'Preparing recommendations' },
  { icon: '🚀', text: 'Finalizing details' }
];

// Simple markdown renderer for bold text
const renderMarkdown = (text: string): string => {
  // Convert **text** to <strong>text</strong>
  let rendered = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  // Convert newlines to <br/>
  rendered = rendered.replace(/\n/g, '<br/>');
  return rendered;
};

// Strip markdown for TTS - remove formatting but keep the text
const stripMarkdown = (text: string): string => {
  // Remove **bold** markers (keep the text inside)
  let cleaned = text.replace(/\*\*(.+?)\*\*/g, '$1');
  // Remove *italic* markers
  cleaned = cleaned.replace(/\*(.+?)\*/g, '$1');
  // Remove __bold__ markers
  cleaned = cleaned.replace(/__(.+?)__/g, '$1');
  // Remove _italic_ markers
  cleaned = cleaned.replace(/_(.+?)_/g, '$1');
  // Remove # headings
  cleaned = cleaned.replace(/^#{1,6}\s+/gm, '');
  // Remove [links](url) - keep just the link text
  cleaned = cleaned.replace(/\[(.+?)\]\(.+?\)/g, '$1');
  // Remove backticks for code
  cleaned = cleaned.replace(/`(.+?)`/g, '$1');
  return cleaned;
};

// Greeting translations for common languages
const GREETING_TRANSLATIONS: Record<string, string> = {
  en: "Hi! I'm Carlos, your WeedGo sales assistant. 👋\n\nI'm here to help you discover how WeedGo can transform your cannabis retail business. Whether you're curious about pricing, features, or just getting started - I'm here to answer any questions.\n\nWhat would you like to know about WeedGo?",
  
  es: "¡Hola! Soy Carlos, tu asistente de ventas de WeedGo. 👋\n\nEstoy aquí para ayudarte a descubrir cómo WeedGo puede transformar tu negocio de cannabis. Ya sea que tengas curiosidad sobre precios, características o estés comenzando - estoy aquí para responder cualquier pregunta.\n\n¿Qué te gustaría saber sobre WeedGo?",
  
  fr: "Bonjour ! Je suis Carlos, votre assistant commercial WeedGo. 👋\n\nJe suis là pour vous aider à découvrir comment WeedGo peut transformer votre entreprise de cannabis. Que vous soyez curieux des prix, des fonctionnalités ou que vous débutiez - je suis là pour répondre à toutes vos questions.\n\nQu'aimeriez-vous savoir sur WeedGo ?",
  
  de: "Hallo! Ich bin Carlos, Ihr WeedGo-Verkaufsassistent. 👋\n\nIch bin hier, um Ihnen zu helfen, herauszufinden, wie WeedGo Ihr Cannabis-Einzelhandelsgeschäft transformieren kann. Egal, ob Sie neugierig auf Preise, Funktionen oder den Einstieg sind - ich bin hier, um alle Fragen zu beantworten.\n\nWas möchten Sie über WeedGo erfahren?",
  
  zh: "你好！我是Carlos，您的WeedGo销售助手。👋\n\n我在这里帮助您了解WeedGo如何改变您的大麻零售业务。无论您对价格、功能感到好奇，还是刚刚开始 - 我都在这里回答任何问题。\n\n您想了解WeedGo的什么？",
  
  ja: "こんにちは！私はCarlosです、あなたのWeedGo販売アシスタントです。👋\n\nWeedGoがあなたの大麻小売ビジネスをどのように変革できるかをお手伝いします。価格、機能、または始め方について興味がある場合 - どんな質問にもお答えします。\n\nWeedGoについて何を知りたいですか？",
  
  ko: "안녕하세요! 저는 Carlos입니다, WeedGo 영업 어시스턴트입니다. 👋\n\nWeedGo가 귀하의 대마초 소매 비즈니스를 어떻게 변화시킬 수 있는지 알아보는 것을 도와드립니다. 가격, 기능 또는 시작하는 방법에 대해 궁금하신 경우 - 모든 질문에 답변해 드립니다.\n\nWeedGo에 대해 무엇을 알고 싶으신가요?",
  
  pt: "Olá! Sou Carlos, seu assistente de vendas WeedGo. 👋\n\nEstou aqui para ajudá-lo a descobrir como o WeedGo pode transformar seu negócio de varejo de cannabis. Seja curioso sobre preços, recursos ou apenas começando - estou aqui para responder a qualquer pergunta.\n\nO que você gostaria de saber sobre o WeedGo?",
  
  ru: "Привет! Я Carlos, ваш торговый помощник WeedGo. 👋\n\nЯ здесь, чтобы помочь вам узнать, как WeedGo может трансформировать ваш розничный бизнес каннабиса. Будь то цены, функции или только начало - я здесь, чтобы ответить на любые вопросы.\n\nЧто бы вы хотели узнать о WeedGo?",
  
  ar: "مرحبًا! أنا Carlos، مساعد مبيعات WeedGo الخاص بك. 👋\n\nأنا هنا لمساعدتك في اكتشاف كيف يمكن لـ WeedGo تحويل أعمال تجارة التجزئة الخاصة بك. سواء كنت فضوليًا بشأن الأسعار أو الميزات أو البدء فقط - أنا هنا للإجابة على أي أسئلة.\n\nماذا تريد أن تعرف عن WeedGo؟",
  
  it: "Ciao! Sono Carlos, il tuo assistente alle vendite WeedGo. 👋\n\nSono qui per aiutarti a scoprire come WeedGo può trasformare la tua attività al dettaglio di cannabis. Che tu sia curioso di prezzi, funzionalità o appena iniziato - sono qui per rispondere a qualsiasi domanda.\n\nCosa vorresti sapere su WeedGo?",
  
  nl: "Hallo! Ik ben Carlos, uw WeedGo-verkoopassistent. 👋\n\nIk ben hier om u te helpen ontdekken hoe WeedGo uw cannabisdetailhandel kan transformeren. Of u nu nieuwsgierig bent naar prijzen, functies of net begint - ik ben hier om elke vraag te beantwoorden.\n\nWat wilt u weten over WeedGo?",
  
  pl: "Cześć! Jestem Carlos, Twój asystent sprzedaży WeedGo. 👋\n\nJestem tutaj, aby pomóc Ci odkryć, jak WeedGo może przekształcić Twój biznes detaliczny z konopią. Czy jesteś ciekawy cen, funkcji czy dopiero zaczynasz - jestem tutaj, aby odpowiedzieć na wszystkie pytania.\n\nCo chciałbyś wiedzieć o WeedGo?",
  
  tr: "Merhaba! Ben Carlos, WeedGo satış asistanınızım. 👋\n\nWeedGo'nun esrar perakende işinizi nasıl dönüştürebileceğini keşfetmenize yardımcı olmak için buradayım. Fiyatlar, özellikler veya sadece başlama konusunda meraklıysanız - herhangi bir soruya cevap vermek için buradayım.\n\nWeedGo hakkında ne öğrenmek istersiniz?",
  
  vi: "Xin chào! Tôi là Carlos, trợ lý bán hàng WeedGo của bạn. 👋\n\nTôi ở đây để giúp bạn khám phá cách WeedGo có thể biến đổi doanh nghiệp bán lẻ cần sa của bạn. Cho dù bạn tò mò về giá cả, tính năng hay chỉ mới bắt đầu - tôi ở đây để trả lời bất kỳ câu hỏi nào.\n\nBạn muốn biết gì về WeedGo?"
};

// Default greeting message (English fallback)
const DEFAULT_GREETING = GREETING_TRANSLATIONS.en;

const SalesChatWidget: React.FC<SalesChatWidgetProps> = ({
  wsUrl = 'ws://localhost:5024/api/v1/chat/ws',
  enableVoice = true
}) => {
  // Fixed agent and personality for sales
  const AGENT = 'sales';
  const PERSONALITY = 'carlos';

  // UI State
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);

  // Chat State
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [currentActivity, setCurrentActivity] = useState(busyActivities[0]);
  const [isBusy, setIsBusy] = useState(false);

  // Translation State
  const [greetingMessage, setGreetingMessage] = useState<string>(DEFAULT_GREETING);

  const messageStartTimeRef = useRef<number | null>(null);
  const messageIdCounter = useRef<number>(0);

  // Generate unique message IDs
  const generateMessageId = () => {
    messageIdCounter.current += 1;
    return `msg-${Date.now()}-${messageIdCounter.current}`;
  };

  // Voice State
  const [voiceState, setVoiceState] = useState<RecordingState>('idle');
  const [voicePermission, setVoicePermission] = useState<boolean>(false);
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState<string>('');
  const [liveTranscript, setLiveTranscript] = useState<string>('');
  const silenceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pauseTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const lastSpeechTimeRef = useRef<number>(Date.now());
  const pendingTranscriptRef = useRef<string>('');
  const sendMessageRef = useRef<(text: string) => void>();

  // TTS State
  const [isSpeakerEnabled, setIsSpeakerEnabled] = useState<boolean>(() => {
    const saved = localStorage.getItem('salesChatWidgetTTSEnabled');
    return saved === 'true';
  });
  const [isSpeaking, setIsSpeaking] = useState<boolean>(false);
  const currentAudioRef = useRef<HTMLAudioElement | null>(null);

  // Typing Animation State
  const [typingMessages, setTypingMessages] = useState<Map<string, string>>(new Map());
  const typingAnimationsRef = useRef<Map<string, boolean>>(new Map());

  // Web Speech API Recognition
  const [recognition, setRecognition] = useState<any>(null);
  const [isTranscribing, setIsTranscribing] = useState<boolean>(false);

  // Refs
  const ws = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const activityInterval = useRef<NodeJS.Timeout | null>(null);

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

        for (let i = lastResultIndex; i < event.results.length; i++) {
          const result = event.results[i];
          if (!result || !result[0]) continue;

          const transcriptText = String(result[0].transcript);

          if (result.isFinal) {
            newFinalText += transcriptText + ' ';
            if (i >= lastResultIndex) {
              allFinalText += transcriptText + ' ';
              lastResultIndex = i + 1;
            }
          } else {
            interimText = transcriptText;
          }
        }

        const completeTranscript = allFinalText + interimText;
        setTranscript(completeTranscript);
        setLiveTranscript(interimText);
        pendingTranscriptRef.current = allFinalText;
        setIsTranscribing(interimText.length > 0 || allFinalText.length > 0);
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

        // Set new timers if we have text
        if (allFinalText && allFinalText.trim()) {
          pauseTimerRef.current = setTimeout(() => {
            const textToSend = allFinalText.trim();
            if (textToSend && textToSend !== lastSentText) {
              console.log('Sending transcript after pause:', textToSend);
              sendMessageRef.current?.(textToSend);
              lastSentText = textToSend;
              // Reset state for next recording
              allFinalText = '';
              lastResultIndex = event.results.length;
              setTranscript('');
              setLiveTranscript('');
              pendingTranscriptRef.current = '';
            }
          }, 2000);
        }

        silenceTimerRef.current = setTimeout(() => {
          console.log('Auto-stopping due to silence');
          const remainingText = allFinalText.trim();
          if (remainingText && remainingText !== lastSentText) {
            console.log('Sending remaining transcript before stop:', remainingText);
            sendMessageRef.current?.(remainingText);
            lastSentText = remainingText;
          }
          recognition.stop();
          // Reset state after stopping
          setTimeout(() => {
            setTranscript('');
            setLiveTranscript('');
            allFinalText = '';
            lastResultIndex = 0;
            lastSentText = '';
            pendingTranscriptRef.current = '';
          }, 500);
        }, 2000);
      };

      recognition.onend = () => {
        console.log('Speech recognition ended');
        setVoiceState('idle');
        setIsRecording(false);
        setIsTranscribing(false);

        // Clean up timers
        if (pauseTimerRef.current) {
          clearTimeout(pauseTimerRef.current);
          pauseTimerRef.current = null;
        }
        if (silenceTimerRef.current) {
          clearTimeout(silenceTimerRef.current);
          silenceTimerRef.current = null;
        }

        // Reset state variables for next use
        allFinalText = '';
        lastResultIndex = 0;
        lastSentText = '';
      };

      recognition.onerror = (event: any) => {
        console.error('Speech recognition error:', event.error);
        setVoiceState('error');
        setIsRecording(false);
        setIsTranscribing(false);
        if (pauseTimerRef.current) clearTimeout(pauseTimerRef.current);
        if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
      };

      recognition.onend = () => {
        console.log('Speech recognition ended');
        setVoiceState('idle');
        setIsRecording(false);
        setIsTranscribing(false);
        if (pauseTimerRef.current) clearTimeout(pauseTimerRef.current);
        if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
      };

      setRecognition(recognition);
      setVoicePermission(true);
    }
  }, [enableVoice]);

  // Detect browser language and set greeting
  useEffect(() => {
    const detectLanguageAndSetGreeting = () => {
      try {
        // Get browser language
        const browserLang = navigator.language || navigator.languages?.[0] || 'en';
        
        // Extract language code (e.g., 'en-US' -> 'en', 'zh-CN' -> 'zh')
        const langCode = browserLang.split('-')[0].toLowerCase();

        // Use pre-translated greeting if available, otherwise English
        const greeting = GREETING_TRANSLATIONS[langCode] || GREETING_TRANSLATIONS.en;
        setGreetingMessage(greeting);
        
        console.log(`[SalesChatWidget] Using ${langCode} greeting`);
      } catch (error) {
        // Fallback to English on any error
        console.error('[SalesChatWidget] Error detecting language:', error);
        setGreetingMessage(DEFAULT_GREETING);
      }
    };

    detectLanguageAndSetGreeting();
  }, []); // Run once on mount

  // Auto-scroll to bottom
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  // Scroll when messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // Scroll when typing/busy state changes (model thinking or responding)
  useEffect(() => {
    if (isTyping || isBusy) {
      scrollToBottom();
    }
  }, [isTyping, isBusy, scrollToBottom]);

  // Scroll during typing animation
  useEffect(() => {
    if (typingMessages.size > 0) {
      scrollToBottom();
    }
  }, [typingMessages, scrollToBottom]);

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
      console.log('Connected to sales chat service');

      // Send initial session configuration locked to sales/carlos
      if (ws.current?.readyState === WebSocket.OPEN) {
        ws.current.send(JSON.stringify({
          type: 'session_update',
          agent: AGENT,
          personality: PERSONALITY
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
      console.log('Disconnected from sales chat service');

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
        // Carlos's greeting - using translated version based on browser language
        setMessages([{
          id: generateMessageId(),
          role: 'assistant',
          content: greetingMessage,
          timestamp: new Date()
        }]);
        break;

      case 'typing':
        // Backend sends: {type: 'typing', typing: true/false}
        const isTypingNow = data.typing === true;
        setIsTyping(isTypingNow);
        setIsBusy(isTypingNow);
        if (isTypingNow) {
          messageStartTimeRef.current = Date.now();
          startActivityRotation();
        } else {
          stopActivityRotation();
        }
        break;

      case 'response':
      case 'message':
        handleIncomingMessage({ ...data, role: 'assistant' });
        break;

      case 'error':
        handleError(data.message || data.error || data.detail || 'An unknown error occurred');
        break;

      case 'session_updated':
        console.log('[SalesChatWidget] Session updated:', data);
        break;

      default:
        console.log('[SalesChatWidget] Unhandled message:', data.type);
    }
  };

  // Typing animation function - simulates human typing
  const animateTyping = async (messageId: string, fullText: string): Promise<void> => {
    return new Promise(async (resolve) => {
      // Mark this message as animating
      typingAnimationsRef.current.set(messageId, true);

      const words = fullText.split(' ');

      for (let i = 0; i <= words.length; i++) {
        // Check if animation was cancelled
        if (!typingAnimationsRef.current.get(messageId)) {
          break;
        }

        const partial = words.slice(0, i).join(' ');
        setTypingMessages(prev => {
          const newMap = new Map(prev);
          newMap.set(messageId, partial);
          return newMap;
        });

        // Don't delay after the last word
        if (i < words.length) {
          // Variable delay: 50-150ms per word (simulates human typing)
          const baseDelay = 50 + Math.random() * 100;

          // Add extra pause after punctuation for natural rhythm
          const extraPause = words[i - 1]?.match(/[.!?]$/) ? 300 : 0;

          await new Promise(resolve => setTimeout(resolve, baseDelay + extraPause));
        }
      }

      // Clean up - remove from typing state
      setTypingMessages(prev => {
        const newMap = new Map(prev);
        newMap.delete(messageId);
        return newMap;
      });
      typingAnimationsRef.current.delete(messageId);

      resolve();
    });
  };

  const handleIncomingMessage = async (data: any) => {
    setIsTyping(false);
    setIsBusy(false);
    stopActivityRotation();
    messageStartTimeRef.current = null;

    // Debug: Log the full data to see what backend sends
    console.log('[DEBUG] Incoming message data:', JSON.stringify(data, null, 2));

    const fullContent = data.content || data.message;
    if (!fullContent) {
      console.warn('[DEBUG] Message has no content:', data);
      return;
    }

    // Handle both assistant and system messages
    if (data.role === 'assistant' || data.role === 'system') {
      const responseTime = data.response_time;
      // Backend sends 'token_count' not 'tokens', also check metadata
      const tokens = data.token_count || data.tokens || data.metadata?.tokens_used || 0;

      console.log('[DEBUG] Extracted tokens:', tokens, 'from:', {
        token_count: data.token_count,
        tokens: data.tokens,
        'metadata.tokens_used': data.metadata?.tokens_used
      });

      const newMessage: Message = {
        id: data.id || generateMessageId(),
        role: data.role === 'system' ? 'system' : 'assistant',
        content: fullContent,
        timestamp: new Date(),
        responseTime,
        tokens
      };

      setMessages(prev => [...prev, newMessage]);
      messageStartTimeRef.current = null;

      // Only do typing animation and TTS for assistant messages, not system messages
      if (data.role === 'assistant') {
        // Start typing animation (don't await - let it run in background)
        animateTyping(newMessage.id, fullContent);

        // Handle TTS if enabled (start IMMEDIATELY, concurrent with typing)
        if (isSpeakerEnabled && fullContent) {
          // Run TTS synthesis and playback concurrently with typing animation
          (async () => {
            try {
              // Strip markdown before TTS to avoid reading "asterisk asterisk"
              const cleanContent = stripMarkdown(fullContent);
              console.log('[TTS] Synthesizing speech for:', cleanContent.substring(0, 50) + '...');
              const audioBlob = await voiceApi.synthesize(cleanContent);
              console.log('[TTS] Audio blob received:', audioBlob.size, 'bytes, type:', audioBlob.type);

              const audioUrl = URL.createObjectURL(audioBlob);
              console.log('[TTS] Audio URL created:', audioUrl);

              if (currentAudioRef.current) {
                currentAudioRef.current.pause();
                currentAudioRef.current = null;
              }

              const audio = new Audio(audioUrl);
              currentAudioRef.current = audio;

              setIsSpeaking(true);
              audio.onended = () => {
                setIsSpeaking(false);
                URL.revokeObjectURL(audioUrl);
                currentAudioRef.current = null;
                // Keep speaker enabled - let user control it manually
                console.log('🔊 Audio playback completed, speaker remains enabled');
              };

              audio.onerror = () => {
                setIsSpeaking(false);
                URL.revokeObjectURL(audioUrl);
                currentAudioRef.current = null;
              };

              // Play audio immediately (concurrent with typing animation)
              console.log('[TTS] Starting audio playback (concurrent with typing)...');
              await audio.play();
              console.log('[TTS] Audio playing successfully');
            } catch (error: any) {
              console.error('[TTS] Error:', error);
              console.error('[TTS] Error details:', {
                message: error.message,
                name: error.name,
                stack: error.stack
              });
              setIsSpeaking(false);
            }
          })();
        }
      }
    } else {
      console.warn('[DEBUG] Unhandled message role:', data.role);
    }
  };

  const handleError = (message: string | undefined) => {
    setIsTyping(false);
    setIsBusy(false);
    stopActivityRotation();

    const errorMessage = message || 'An unknown error occurred';
    console.error('[SalesChatWidget] Error:', errorMessage);
    
    setMessages(prev => [...prev, {
      id: generateMessageId(),
      role: 'system',
      content: `Error: ${errorMessage}`,
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

    const userMessage: Message = {
      id: generateMessageId(),
      role: 'user',
      content: messageToSend,
      timestamp: new Date(),
      isVoice: !!content
    };
    setMessages(prev => [...prev, userMessage]);

    setIsBusy(true);
    messageStartTimeRef.current = Date.now();

    const messagePayload = {
      type: 'message',
      message: messageToSend,
      session_id: sessionId,
      max_tokens: 2000  // Allow longer responses for sales conversations (default was 500)
    };

    if (ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(messagePayload));
    } else {
      console.error('[SalesChatWidget] WebSocket not ready');
      handleError('Connection not ready. Please wait a moment and try again.');
      return;
    }

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

  const sendTranscriptAsMessage = (text: string) => {
    if (!text.trim() || !ws.current || ws.current.readyState !== WebSocket.OPEN) return;

    const message: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: text,
      timestamp: new Date(),
      isVoice: true
    };

    setMessages(prev => [...prev, message]);
    setIsBusy(true);
    messageStartTimeRef.current = Date.now();

    ws.current.send(JSON.stringify({
      type: 'message',
      message: text,
      session_id: sessionId,
      max_tokens: 2000  // Allow longer responses for sales conversations (default was 500)
    }));
  };

  useEffect(() => {
    sendMessageRef.current = sendTranscriptAsMessage;
  }, [sessionId]);

  const startVoiceRecording = async () => {
    if (!recognition) return;

    if (isRecording) {
      console.log('Manually stopping recording');

      if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
      if (pauseTimerRef.current) clearTimeout(pauseTimerRef.current);

      if (pendingTranscriptRef.current && pendingTranscriptRef.current.trim()) {
        sendMessage(pendingTranscriptRef.current.trim());
      }

      recognition.stop();
    } else {
      console.log('Starting recording');

      // Auto-enable speaker when user starts voice input for better UX
      if (!isSpeakerEnabled) {
        setIsSpeakerEnabled(true);
        localStorage.setItem('salesChatWidgetTTSEnabled', 'true');
        console.log('🔊 Auto-enabled speaker for voice input');
      }

      if (currentAudioRef.current) {
        currentAudioRef.current.pause();
        currentAudioRef.current = null;
        setIsSpeaking(false);
      }
      if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }

      setTranscript('');
      setLiveTranscript('');
      pendingTranscriptRef.current = '';

      recognition.start();
      setIsRecording(true);
      setIsTranscribing(true);
      setVoiceState('recording');
      lastSpeechTimeRef.current = Date.now();
    }
  };

  const handleToggleSpeaker = () => {
    const newState = !isSpeakerEnabled;
    setIsSpeakerEnabled(newState);

    if (!newState) {
      // Stop any currently playing audio
      if (currentAudioRef.current) {
        currentAudioRef.current.pause();
        currentAudioRef.current = null;
        setIsSpeaking(false);
      }
      console.log('🔇 Speaker manually disabled');
    } else {
      console.log('🔊 Speaker manually enabled');
    }

    localStorage.setItem('salesChatWidgetTTSEnabled', newState.toString());
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <>
      {/* Floating Chat Button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white rounded-full p-4 shadow-lg hover:shadow-xl transition-all duration-300 group z-50"
          aria-label="Open sales chat"
        >
          <MessageCircle className="h-6 w-6 group-hover:scale-110 transition-transform" />
          <span className="absolute -top-2 -right-2 bg-red-500 text-white text-xs rounded-full px-2 py-0.5 animate-pulse">
            Questions?
          </span>
        </button>
      )}

      {/* Chat Window */}
      {isOpen && (
        <div
          className="fixed bottom-6 right-6 w-[520px] bg-white rounded-2xl shadow-2xl transition-all duration-300 flex flex-col z-50"
          style={{
            height: isMinimized ? '64px' : '650px'
          }}
        >
          {/* Header */}
          <div className="bg-gradient-to-r from-green-600 to-emerald-600 px-5 py-4 rounded-t-2xl flex items-center justify-between">
            <div className="flex items-center space-x-3">
              {/* Human-like avatar with initial */}
              <div className="relative">
                <div className="h-10 w-10 rounded-full bg-white/20 backdrop-blur-sm flex items-center justify-center text-white font-semibold text-lg border-2 border-white/30">
                  C
                </div>
                <span className={`absolute -bottom-0.5 -right-0.5 h-3 w-3 rounded-full border-2 border-green-600 ${
                  isConnected ? 'bg-green-300' : 'bg-gray-400'
                }`} />
              </div>
              <div>
                <h3 className="font-semibold text-white text-base">Carlos</h3>
                <p className="text-xs text-green-50 flex items-center gap-1.5">
                  {isBusy ? (
                    <>
                      <span className="inline-block w-1.5 h-1.5 bg-green-200 rounded-full animate-pulse" />
                      <span>typing...</span>
                    </>
                  ) : isConnected ? (
                    <>
                      <span className="inline-block w-1.5 h-1.5 bg-green-300 rounded-full" />
                      <span>Online</span>
                    </>
                  ) : (
                    'Connecting...'
                  )}
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-1">
              <button
                onClick={() => setIsMinimized(!isMinimized)}
                className="p-1.5 hover:bg-white/20 rounded-lg transition-colors"
                aria-label="Minimize"
              >
                <Minimize2 className="h-4 w-4 text-white" />
              </button>
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
              <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-gray-50">
                {messages.map((message) => (
                  <div key={message.id}>
                    <div className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                      <div
                        className={`max-w-[90%] rounded-2xl px-4 py-3 ${
                          message.role === 'user'
                            ? 'bg-gradient-to-r from-green-500 to-emerald-600 text-white'
                            : message.role === 'assistant'
                            ? 'bg-white text-gray-800 shadow-md border border-gray-100'
                            : 'bg-yellow-100 text-yellow-800'
                        }`}
                      >
                        <div className="flex flex-col gap-1">
                          {/* Remove bot icon for human feel - just show content */}
                          {message.role === 'user' && message.isVoice && (
                            <div className="flex items-center gap-1.5 mb-1 opacity-70">
                              <Volume2 className="h-3 w-3" />
                              <span className="text-xs">Voice message</span>
                            </div>
                          )}
                          <div>
                            {message.role === 'assistant' ? (
                              <div 
                                className="text-[15px] leading-relaxed"
                                dangerouslySetInnerHTML={{
                                  __html: renderMarkdown(
                                    typingMessages.has(message.id)
                                      ? typingMessages.get(message.id)!
                                      : message.content
                                  )
                                }}
                              />
                            ) : (
                              <p className="whitespace-pre-wrap text-[15px] leading-relaxed">
                                {message.content}
                              </p>
                            )}
                            {/* Show cursor during typing animation */}
                            {message.role === 'assistant' && typingMessages.has(message.id) && (
                              <span className="inline-block w-0.5 h-4 ml-1 bg-green-600 animate-pulse" />
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                    {/* Timestamp with Response Time and Tokens */}
                    <div className={`mt-1.5 px-2 flex items-center gap-1.5 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                      <Clock className="h-3 w-3 text-gray-400" />
                      <span className="text-xs text-gray-500">
                        {formatTime(message.timestamp)}
                      </span>

                      {/* Show response time for assistant messages */}
                      {message.role === 'assistant' && message.responseTime !== undefined && (
                        <>
                          <span className="text-gray-300">•</span>
                          <span className="text-xs text-green-600 font-medium">
                            {message.responseTime > 0 ? message.responseTime.toFixed(2) : '< 0.01'}s
                          </span>
                        </>
                      )}

                      {/* Show tokens for assistant messages */}
                      {message.role === 'assistant' && message.tokens !== undefined && message.tokens > 0 && (
                        <>
                          <span className="text-gray-300">•</span>
                          <span className="text-xs text-blue-600 font-medium">
                            {message.tokens} tokens
                          </span>
                        </>
                      )}
                    </div>
                  </div>
                ))}

                {/* Typing Indicator - Human-like */}
                {isTyping && (
                  <div className="flex justify-start">
                    <div className="bg-white rounded-2xl px-4 py-3 shadow-md border border-gray-100 max-w-[90%]">
                      <div className="flex items-center gap-3">
                        <span className="text-base">{currentActivity.icon}</span>
                        <span className="text-sm text-gray-600">{currentActivity.text}</span>
                        <div className="flex space-x-1">
                          <div className="w-2 h-2 bg-green-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                          <div className="w-2 h-2 bg-green-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                          <div className="w-2 h-2 bg-green-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </div>

              {/* Voice Status */}
              {isRecording && (transcript || liveTranscript) && (
                <div className="bg-gray-100 px-4 py-3 border-t border-gray-200">
                  <div className="p-2 bg-white rounded-lg border border-gray-200">
                    <div className="text-xs text-gray-500 mb-1 flex items-center gap-1">
                      <span className="animate-pulse text-red-500">●</span> Live Transcript
                    </div>
                    <div className="text-sm text-gray-800">{transcript || liveTranscript}</div>
                    <div className="text-xs text-gray-400 mt-1 italic">
                      (Pause 2s to send • 2s silence to stop)
                    </div>
                  </div>
                </div>
              )}

              {/* Input Area */}
              <div className="border-t border-gray-200 p-4 bg-white rounded-b-2xl">
                <div className="flex items-end space-x-2">
                  <div className="flex-1 relative">
                    <textarea
                      ref={inputRef}
                      value={inputMessage}
                      onChange={(e) => setInputMessage(e.target.value)}
                      onKeyPress={handleKeyPress}
                      placeholder={
                        isBusy
                          ? "Carlos is thinking..."
                          : isRecording
                          ? "Recording voice..."
                          : isConnected
                          ? "Ask about pricing, features, or getting started..."
                          : "Connecting..."
                      }
                      disabled={!isConnected || isBusy || isRecording}
                      rows={1}
                      className="w-full px-4 py-3 pr-12 border border-gray-300 rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed text-[15px] transition-colors"
                      style={{ maxHeight: '150px', minHeight: '44px' }}
                      onInput={(e) => {
                        const target = e.target as HTMLTextAreaElement;
                        target.style.height = 'auto';
                        target.style.height = Math.min(target.scrollHeight, 150) + 'px';
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
                          : 'bg-gray-100 hover:bg-gray-200 text-gray-600'
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
                        : 'bg-gray-100 hover:bg-gray-200 text-gray-600'
                    }`}
                    aria-label={isSpeakerEnabled ? 'Disable text-to-speech' : 'Enable text-to-speech'}
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
                    className="p-2.5 bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white rounded-xl disabled:opacity-30 disabled:cursor-not-allowed transition-all"
                    aria-label="Send message"
                  >
                    <Send className="h-5 w-5" />
                  </button>
                </div>

                {/* Status Bar */}
                <div className="flex items-center justify-between mt-2">
                  <div className="flex items-center gap-2">
                    {!isConnected && (
                      <span className="text-xs text-orange-600 flex items-center gap-1">
                        <AlertCircle className="h-3 w-3" />
                        Reconnecting...
                      </span>
                    )}
                    {isBusy && (
                      <span className="text-xs text-green-600 flex items-center gap-1">
                        <Loader2 className="h-3 w-3 animate-spin" />
                        Processing...
                      </span>
                    )}
                    {voiceState === 'error' && (
                      <span className="text-xs text-red-600">
                        Voice recognition error. Please try again.
                      </span>
                    )}
                  </div>
                  <span className="text-xs text-gray-500 italic">
                    Powered by WeedGo AI
                  </span>
                </div>
              </div>
            </>
          )}
        </div>
      )}
    </>
  );
};

export default SalesChatWidget;
