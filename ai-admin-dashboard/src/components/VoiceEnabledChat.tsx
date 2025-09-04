import React, { useState, useEffect, useRef, useCallback } from 'react';
import { 
  Mic, MicOff, Volume2, VolumeX, Send, Loader2, 
  Globe, User, Activity, Headphones, AlertCircle 
} from 'lucide-react';
import toast from 'react-hot-toast';
import { endpoints } from '../config/endpoints';

interface VoiceConfig {
  enabled: boolean;
  autoDetectLanguage: boolean;
  language: string;
  microphonePermission: 'granted' | 'denied' | 'prompt';
  speakerEnabled: boolean;
  noiseLevel: number;
  domain: string;
}

interface TranscriptionResult {
  text: string;
  language: string;
  confidence: number;
  userId?: string;
  isFinal: boolean;
}

interface ChatMessage {
  id: string;
  text: string;
  sender: 'user' | 'assistant';
  timestamp: Date;
  language?: string;
  voiceId?: string;
  products?: any[];
  audioUrl?: string;
}

const LANGUAGES = [
  { code: 'en', name: 'English', flag: '🇺🇸' },
  { code: 'es', name: 'Español', flag: '🇪🇸' },
  { code: 'fr', name: 'Français', flag: '🇫🇷' },
  { code: 'pt', name: 'Português', flag: '🇵🇹' },
  { code: 'zh', name: '中文', flag: '🇨🇳' },
  { code: 'ar', name: 'العربية', flag: '🇸🇦' }
];

export const VoiceEnabledChat: React.FC = () => {
  // State
  const [voiceConfig, setVoiceConfig] = useState<VoiceConfig>({
    enabled: false,
    autoDetectLanguage: true,
    language: 'en',
    microphonePermission: 'prompt',
    speakerEnabled: true,
    noiseLevel: 0,
    domain: 'budtender'
  });

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [currentTranscription, setCurrentTranscription] = useState<TranscriptionResult | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  const [detectedUser, setDetectedUser] = useState<string | null>(null);
  const [sessionId] = useState(`voice_session_${Date.now()}`);
  const [retryCount, setRetryCount] = useState(0);

  // Refs
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const lastAudioTimestampRef = useRef<number>(0);

  // Initialize WebSocket connection
  useEffect(() => {
    if (voiceConfig.enabled) {
      connectWebSocket();
    }
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      // Stop any playing audio when component unmounts
      if (currentAudioRef.current) {
        currentAudioRef.current.pause();
        currentAudioRef.current = null;
      }
    };
  }, [voiceConfig.enabled]);

  const connectWebSocket = () => {
    // Check if voice is enabled before attempting connection
    if (!voiceConfig.enabled) return;
    
    try {
      const ws = new WebSocket(endpoints.voiceEndpoints.stream);
      
      ws.onopen = () => {
        console.log('WebSocket connected');
        setRetryCount(0); // Reset retry count on successful connection
        // Send initial configuration
        ws.send(JSON.stringify({
          type: 'config',
          session_id: sessionId,
          domain: voiceConfig.domain,
          language: voiceConfig.language
        }));
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        // Only show error on first attempt
        if (retryCount === 0) {
          toast.warning('Voice features are currently unavailable');
          // Disable voice after first failure
          setVoiceConfig(prev => ({ ...prev, enabled: false }));
        }
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        // Only retry if voice is still enabled and retry count is low
        if (voiceConfig.enabled && retryCount < 3) {
          setRetryCount(prev => prev + 1);
          setTimeout(() => {
            connectWebSocket();
          }, 3000);
        }
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
      toast.error('Failed to connect to voice service');
    }
  };

  const handleWebSocketMessage = (data: any) => {
    switch (data.type) {
      case 'transcription':
        setCurrentTranscription({
          text: data.text,
          language: data.language,
          confidence: data.confidence,
          userId: data.user_id,
          isFinal: data.is_final
        });
        if (data.user_id) {
          setDetectedUser(data.user_id);
        }
        break;

      case 'audio_response':
        // Play audio response
        console.log('[Voice] Received audio_response message from WebSocket');
        if (voiceConfig.speakerEnabled && data.audio) {
          // Prevent duplicate audio within 1 second
          const now = Date.now();
          if (now - lastAudioTimestampRef.current < 1000) {
            console.log('[Voice] Skipping duplicate audio (too soon after last)');
            return;
          }
          
          // Add debounce to prevent rapid repeated playback
          if (currentAudioRef.current) {
            console.log('[Voice] Skipping audio - already playing');
            return;
          }
          
          lastAudioTimestampRef.current = now;
          playAudioResponse(data.audio);
        }
        break;

      case 'processing':
        setIsProcessing(true);
        break;

      case 'error':
        toast.error(data.message);
        setIsProcessing(false);
        break;
    }
  };

  // Request microphone permission
  const requestMicrophonePermission = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      setVoiceConfig(prev => ({
        ...prev,
        microphonePermission: 'granted'
      }));
      
      // Set up audio context for visualization
      audioContextRef.current = new AudioContext();
      analyserRef.current = audioContextRef.current.createAnalyser();
      const source = audioContextRef.current.createMediaStreamSource(stream);
      source.connect(analyserRef.current);
      
      streamRef.current = stream;
      
      // Start audio level monitoring
      monitorAudioLevel();
      
      toast.success('Microphone access granted');
      
      // Calibrate for environment
      calibrateEnvironment();
      
    } catch (error) {
      console.error('Microphone permission denied:', error);
      setVoiceConfig(prev => ({
        ...prev,
        microphonePermission: 'denied'
      }));
      toast.error('Microphone access denied. Please enable it in browser settings.');
    }
  };

  // Monitor audio level for visualization
  const monitorAudioLevel = () => {
    if (!analyserRef.current) return;

    const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
    
    const checkLevel = () => {
      if (!analyserRef.current || !isRecording) return;
      
      analyserRef.current.getByteFrequencyData(dataArray);
      const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
      setAudioLevel(average / 255);
      
      requestAnimationFrame(checkLevel);
    };
    
    checkLevel();
  };

  // Calibrate for environment noise
  const calibrateEnvironment = async () => {
    try {
      const response = await fetch(endpoints.voiceEndpoints.calibrate, {
        method: 'POST'
      });
      
      if (response.ok) {
        const data = await response.json();
        setVoiceConfig(prev => ({
          ...prev,
          noiseLevel: data.calibration.noise_level
        }));
        
        if (data.recommendations.noise_reduction) {
          toast.info('High noise detected. Noise reduction enabled.');
        }
      }
    } catch (error) {
      console.error('Calibration failed:', error);
    }
  };

  // Start/stop recording
  const toggleRecording = async () => {
    if (!isRecording) {
      if (voiceConfig.microphonePermission !== 'granted') {
        await requestMicrophonePermission();
        if (voiceConfig.microphonePermission !== 'granted') {
          return;
        }
      }
      startRecording();
    } else {
      stopRecording();
    }
  };

  const startRecording = () => {
    if (!streamRef.current) return;

    audioChunksRef.current = [];
    
    // Try to use WAV format if supported, otherwise fall back to webm
    const mimeType = MediaRecorder.isTypeSupported('audio/wav') ? 'audio/wav' : 'audio/webm';
    console.log('[Voice] Recording with mime type:', mimeType);
    
    const mediaRecorder = new MediaRecorder(streamRef.current, {
      mimeType: mimeType
    });
    
    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        audioChunksRef.current.push(event.data);
        
        // For now, skip WebSocket streaming until we can convert format properly
        // Will process complete audio on stop
      }
    };

    mediaRecorder.onstop = async () => {
      const audioBlob = new Blob(audioChunksRef.current, { type: mimeType });
      console.log('[Voice] Recording stopped, blob size:', audioBlob.size, 'type:', audioBlob.type);
      await processAudioBlob(audioBlob);
    };

    mediaRecorder.onerror = (event: any) => {
      console.error('[Voice] MediaRecorder error:', event);
      toast.error('Recording error occurred');
    };

    mediaRecorder.start(1000); // Larger chunks, less frequent
    mediaRecorderRef.current = mediaRecorder;
    setIsRecording(true);
    setIsListening(true);
    
    toast.success('Recording started');
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setIsListening(false);
      setAudioLevel(0);
    }
  };

  // Convert audio blob to WAV format
  const convertToWav = async (audioBlob: Blob): Promise<ArrayBuffer> => {
    const audioContext = new AudioContext({ sampleRate: 16000 });
    const arrayBuffer = await audioBlob.arrayBuffer();
    const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
    
    // Resample to 16kHz mono
    const channelData = audioBuffer.getChannelData(0); // Get first channel
    const length = channelData.length;
    
    // Convert float32 to int16
    const int16Buffer = new Int16Array(length);
    for (let i = 0; i < length; i++) {
      const s = Math.max(-1, Math.min(1, channelData[i]));
      int16Buffer[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
    }
    
    return int16Buffer.buffer;
  };

  // Process recorded audio
  const processAudioBlob = async (audioBlob: Blob) => {
    setIsProcessing(true);
    
    try {
      let audioData: string;
      
      // If the blob is WebM, convert to WAV
      if (audioBlob.type.includes('webm')) {
        console.log('[Voice] Converting WebM to WAV format...');
        try {
          const wavBuffer = await convertToWav(audioBlob);
          // Convert ArrayBuffer to base64
          const uint8Array = new Uint8Array(wavBuffer);
          const binaryString = Array.from(uint8Array)
            .map(byte => String.fromCharCode(byte))
            .join('');
          audioData = btoa(binaryString);
          console.log('[Voice] Conversion successful, size:', audioData.length);
        } catch (convError) {
          console.error('[Voice] Conversion failed:', convError);
          toast.error('Audio format conversion failed');
          return;
        }
      } else {
        // If already WAV or other format, use as-is
        const reader = new FileReader();
        const result = await new Promise<string>((resolve) => {
          reader.onload = () => {
            const base64 = reader.result?.toString().split(',')[1];
            resolve(base64 || '');
          };
          reader.readAsDataURL(audioBlob);
        });
        audioData = result;
      }
        
      if (!audioData) {
        console.error('[Voice] No audio data to send');
        return;
      }

      // Send to conversation endpoint
      console.log('[Voice] Sending audio to server...');
      const response = await fetch(endpoints.voiceEndpoints.conversation, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          audio_data: audioData,
          session_id: sessionId,
          domain: voiceConfig.domain,
          metadata: {
            user_id: detectedUser,
            language: voiceConfig.language,
            auto_detect_language: voiceConfig.autoDetectLanguage
          }
        })
      });

      if (response.ok) {
        const data = await response.json();
        
        // Add user message
        if (data.user_text) {
          addMessage({
            id: `msg_${Date.now()}`,
            text: data.user_text,
            sender: 'user',
            timestamp: new Date(),
            language: data.metadata?.language,
            voiceId: data.metadata?.user_profile?.voice_id
          });
        }

        // Add AI response
        if (data.ai_text) {
          addMessage({
            id: `msg_${Date.now() + 1}`,
            text: data.ai_text,
            sender: 'assistant',
            timestamp: new Date(),
            products: data.products,
            audioUrl: data.audio_response
          });

          // Play audio response if enabled
          if (voiceConfig.speakerEnabled && data.audio_response) {
            playAudioResponse(data.audio_response);
          }
        }
      } else {
        console.error('[Voice] Server response error:', response.status, response.statusText);
        toast.error('Failed to process voice request');
      }
      
    } catch (error) {
      console.error('Processing failed:', error);
      toast.error('Failed to process audio');
    } finally {
      setIsProcessing(false);
      setCurrentTranscription(null);
    }
  };

  // Reference to current audio to prevent multiple plays
  const currentAudioRef = useRef<HTMLAudioElement | null>(null);

  // Play audio response
  const playAudioResponse = (audioData: string) => {
    try {
      // Stop and clean up any currently playing audio
      if (currentAudioRef.current) {
        console.log('[Voice] Stopping previous audio');
        currentAudioRef.current.pause();
        currentAudioRef.current.src = ''; // Clear source
        currentAudioRef.current.load(); // Reset the element
        currentAudioRef.current = null;
      }

      // If already a data URL, use as-is, otherwise add prefix
      const audioUrl = audioData.startsWith('data:') 
        ? audioData 
        : `data:audio/wav;base64,${audioData}`;
      
      // Validate data URL format
      if (!audioUrl.startsWith('data:audio/')) {
        console.error('[Voice] Invalid audio URL format');
        toast.error('Invalid audio format received');
        return;
      }
      
      // Check if base64 data exists
      const base64Index = audioUrl.indexOf(',');
      if (base64Index === -1 || base64Index === audioUrl.length - 1) {
        console.error('[Voice] No audio data in URL');
        toast.error('No audio data received');
        return;
      }
      
      console.log('[Voice] Creating new audio element');
      console.log('[Voice] Audio URL length:', audioUrl.length);
      console.log('[Voice] Audio URL preview:', audioUrl.substring(0, 100) + '...');
      
      const audio = new Audio(audioUrl);
      audio.loop = false; // Explicitly disable looping
      audio.autoplay = false; // Explicitly disable autoplay
      
      // Track play count to detect loops
      let playCount = 0;
      
      audio.addEventListener('play', () => {
        playCount++;
        console.log(`[Voice] Audio play event #${playCount}`);
        if (playCount > 1) {
          console.warn('[Voice] Audio played multiple times - possible loop detected');
        }
      });
      
      // Clean up when audio finishes
      audio.addEventListener('ended', () => {
        console.log('[Voice] Audio ended naturally');
        if (currentAudioRef.current === audio) {
          currentAudioRef.current = null;
        }
      });
      
      // Handle errors
      audio.addEventListener('error', (e: Event) => {
        const audioElement = e.target as HTMLAudioElement;
        const error = audioElement.error;
        console.error('[Voice] Audio error details:', {
          code: error?.code,
          message: error?.message,
          mediaError: error,
          networkState: audioElement.networkState,
          readyState: audioElement.readyState,
          src: audioElement.src?.substring(0, 100) + '...'
        });
        
        // Clear reference on error
        if (currentAudioRef.current === audio) {
          currentAudioRef.current = null;
        }
        
        // Don't retry on error - just notify user
        toast.error('Audio playback failed. Please try again.');
      });
      
      // Store reference and play
      currentAudioRef.current = audio;
      audio.play().then(() => {
        console.log('[Voice] Audio playback started successfully');
      }).catch(error => {
        console.error('[Voice] Failed to play audio:', error);
        currentAudioRef.current = null;
      });
    } catch (error) {
      console.error('[Voice] Failed to create audio:', error);
    }
  };

  // Send text message
  const sendTextMessage = async () => {
    if (!inputText.trim()) return;

    const userMessage: ChatMessage = {
      id: `msg_${Date.now()}`,
      text: inputText,
      sender: 'user',
      timestamp: new Date()
    };

    addMessage(userMessage);
    setInputText('');
    setIsProcessing(true);

    try {
      const response = await fetch(endpoints.chat.send, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: inputText,
          session_id: sessionId,
          language: voiceConfig.language,
          customer_id: detectedUser
        })
      });

      if (response.ok) {
        const data = await response.json();
        
        const aiMessage: ChatMessage = {
          id: `msg_${Date.now()}`,
          text: data.message,
          sender: 'assistant',
          timestamp: new Date(),
          products: data.products
        };

        addMessage(aiMessage);

        // Generate and play voice response if enabled
        if (voiceConfig.speakerEnabled) {
          const ttsResponse = await fetch(endpoints.voiceEndpoints.synthesize, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              text: data.message,
              domain: voiceConfig.domain,
              emotion: 'friendly'
            })
          });

          if (ttsResponse.ok) {
            const audioBlob = await ttsResponse.blob();
            const audioUrl = URL.createObjectURL(audioBlob);
            const audio = new Audio(audioUrl);
            audio.play();
          }
        }
      }
    } catch (error) {
      console.error('Failed to send message:', error);
      toast.error('Failed to send message');
    } finally {
      setIsProcessing(false);
    }
  };

  const addMessage = (message: ChatMessage) => {
    setMessages(prev => [...prev, message]);
    setTimeout(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, 100);
  };

  // Voice indicator animation
  const VoiceIndicator: React.FC<{ level: number; isActive: boolean }> = ({ level, isActive }) => (
    <div className="flex items-center space-x-1">
      {[...Array(5)].map((_, i) => (
        <div
          key={i}
          className={`w-1 transition-all duration-100 ${
            isActive ? 'bg-green-500' : 'bg-gray-300'
          }`}
          style={{
            height: isActive ? `${Math.max(8, level * 100 * (i + 1) / 5)}px` : '8px'
          }}
        />
      ))}
    </div>
  );

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Header with voice controls */}
      <div className="bg-white border-b p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <h2 className="text-xl font-semibold">Voice-Enabled Chat</h2>
            
            {/* Language selector */}
            <div className="flex items-center space-x-2">
              <Globe className="w-4 h-4 text-gray-500" />
              <select
                value={voiceConfig.language}
                onChange={(e) => setVoiceConfig(prev => ({ ...prev, language: e.target.value }))}
                className="text-sm border rounded px-2 py-1"
                disabled={voiceConfig.autoDetectLanguage}
              >
                {LANGUAGES.map(lang => (
                  <option key={lang.code} value={lang.code}>
                    {lang.flag} {lang.name}
                  </option>
                ))}
              </select>
              
              <label className="flex items-center space-x-1 text-sm">
                <input
                  type="checkbox"
                  checked={voiceConfig.autoDetectLanguage}
                  onChange={(e) => setVoiceConfig(prev => ({ 
                    ...prev, 
                    autoDetectLanguage: e.target.checked 
                  }))}
                  className="rounded"
                />
                <span>Auto-detect</span>
              </label>
            </div>

            {/* Voice status */}
            {detectedUser && (
              <div className="flex items-center space-x-2 text-sm">
                <User className="w-4 h-4 text-blue-500" />
                <span className="text-blue-600">User: {detectedUser}</span>
              </div>
            )}
          </div>

          {/* Voice controls */}
          <div className="flex items-center space-x-3">
            {/* Microphone permission status */}
            {voiceConfig.microphonePermission === 'denied' && (
              <div className="flex items-center space-x-1 text-red-500 text-sm">
                <AlertCircle className="w-4 h-4" />
                <span>Mic access denied</span>
              </div>
            )}

            {/* Speaker toggle */}
            <button
              onClick={() => setVoiceConfig(prev => ({ 
                ...prev, 
                speakerEnabled: !prev.speakerEnabled 
              }))}
              className={`p-2 rounded ${
                voiceConfig.speakerEnabled 
                  ? 'bg-blue-100 text-blue-600' 
                  : 'bg-gray-100 text-gray-400'
              }`}
              title={voiceConfig.speakerEnabled ? 'Speaker enabled' : 'Speaker disabled'}
            >
              {voiceConfig.speakerEnabled ? <Volume2 /> : <VolumeX />}
            </button>

            {/* Voice toggle */}
            <button
              onClick={() => setVoiceConfig(prev => ({ ...prev, enabled: !prev.enabled }))}
              className={`px-4 py-2 rounded flex items-center space-x-2 ${
                voiceConfig.enabled 
                  ? 'bg-green-500 text-white' 
                  : 'bg-gray-200 text-gray-600'
              }`}
            >
              <Headphones className="w-4 h-4" />
              <span>{voiceConfig.enabled ? 'Voice ON' : 'Voice OFF'}</span>
            </button>
          </div>
        </div>

        {/* Live transcription display */}
        {currentTranscription && (
          <div className="mt-3 p-2 bg-blue-50 rounded border border-blue-200">
            <div className="flex items-center space-x-2">
              <Activity className="w-4 h-4 text-blue-500 animate-pulse" />
              <span className="text-sm text-blue-700">
                {currentTranscription.isFinal ? 'Transcribed' : 'Listening'}: 
              </span>
              <span className="text-sm font-medium text-blue-900">
                {currentTranscription.text}
              </span>
              {currentTranscription.language && (
                <span className="text-xs bg-blue-200 px-2 py-1 rounded">
                  {LANGUAGES.find(l => l.code === currentTranscription.language)?.flag} 
                  {currentTranscription.language.toUpperCase()}
                </span>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 mt-10">
            <Mic className="w-12 h-12 mx-auto mb-3 text-gray-300" />
            <p>Start a conversation by speaking or typing</p>
            <p className="text-sm mt-2">
              {voiceConfig.enabled 
                ? 'Click the microphone button to start speaking' 
                : 'Enable voice mode for hands-free interaction'}
            </p>
          </div>
        )}

        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-2xl rounded-lg p-4 ${
                message.sender === 'user'
                  ? 'bg-blue-500 text-white'
                  : 'bg-white border'
              }`}
            >
              <div className="flex items-start space-x-2">
                <div className="flex-1">
                  <p className="whitespace-pre-wrap">{message.text}</p>
                  
                  {/* Voice ID indicator */}
                  {message.voiceId && (
                    <div className="mt-2 text-xs opacity-75">
                      <User className="w-3 h-3 inline mr-1" />
                      Voice ID: {message.voiceId}
                    </div>
                  )}

                  {/* Language indicator */}
                  {message.language && (
                    <div className="mt-1 text-xs opacity-75">
                      {LANGUAGES.find(l => l.code === message.language)?.flag} 
                      {message.language.toUpperCase()}
                    </div>
                  )}
                </div>
              </div>

              {/* Products */}
              {message.products && message.products.length > 0 && (
                <div className="mt-3 space-y-2">
                  {message.products.map((product: any) => (
                    <div key={product.id} className="bg-gray-50 p-3 rounded">
                      <div className="font-medium">{product.product_name}</div>
                      <div className="text-sm text-gray-600">
                        {product.brand} • ${product.price}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {isProcessing && (
          <div className="flex justify-start">
            <div className="bg-white border rounded-lg p-4">
              <Loader2 className="w-5 h-5 animate-spin text-blue-500" />
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <div className="bg-white border-t p-4">
        <div className="flex items-center space-x-3">
          {/* Voice recording button */}
          {voiceConfig.enabled && (
            <button
              onClick={toggleRecording}
              disabled={isProcessing}
              className={`p-3 rounded-full transition-all ${
                isRecording
                  ? 'bg-red-500 text-white animate-pulse'
                  : voiceConfig.microphonePermission === 'granted'
                  ? 'bg-blue-500 text-white hover:bg-blue-600'
                  : 'bg-gray-200 text-gray-500'
              }`}
              title={isRecording ? 'Stop recording' : 'Start recording'}
            >
              {isRecording ? <MicOff /> : <Mic />}
            </button>
          )}

          {/* Voice level indicator */}
          {isRecording && (
            <VoiceIndicator level={audioLevel} isActive={isListening} />
          )}

          {/* Text input */}
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && sendTextMessage()}
            placeholder={isRecording ? "Speaking..." : "Type a message..."}
            disabled={isRecording || isProcessing}
            className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:border-blue-500"
          />

          {/* Send button */}
          <button
            onClick={sendTextMessage}
            disabled={!inputText.trim() || isProcessing || isRecording}
            className="p-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isProcessing ? <Loader2 className="animate-spin" /> : <Send />}
          </button>
        </div>

        {/* Environment info */}
        {voiceConfig.noiseLevel > 0 && (
          <div className="mt-2 text-xs text-gray-500">
            Noise level: {(voiceConfig.noiseLevel * 100).toFixed(0)}% 
            {voiceConfig.noiseLevel > 0.3 && ' (High noise detected)'}
          </div>
        )}
      </div>
    </div>
  );
};

export default VoiceEnabledChat;