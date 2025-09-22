/**
 * Streaming Voice Recording Service
 * Handles real-time voice recording with streaming transcription,
 * voice activity detection, and auto-send/stop functionality
 */

export interface AudioVisualizationData {
  waveform: Uint8Array;
  frequency: Uint8Array;
  volume: number;
}

export interface StreamingTranscriptData {
  text: string;
  isFinal: boolean;
  confidence?: number;
}

export interface VoiceActivityState {
  isSpeaking: boolean;
  silenceDuration: number;
  pauseDuration: number;
}

interface StreamingVoiceCallbacks {
  onTranscript?: (data: StreamingTranscriptData) => void;
  onVisualization?: (data: AudioVisualizationData) => void;
  onVoiceActivity?: (state: VoiceActivityState) => void;
  onAutoSend?: (transcript: string) => void;
  onAutoStop?: () => void;
  onError?: (error: Error) => void;
  onRecordingStateChange?: (isRecording: boolean) => void;
}

export class StreamingVoiceRecordingService {
  // Audio recording
  private mediaRecorder: MediaRecorder | null = null;
  private audioStream: MediaStream | null = null;
  private audioContext: AudioContext | null = null;
  private analyser: AnalyserNode | null = null;
  private scriptProcessor: ScriptProcessorNode | null = null;

  // WebSocket for streaming
  private ws: WebSocket | null = null;
  private wsUrl: string;

  // Recording state
  private isRecording = false;
  private currentTranscript = '';
  private lastSpeechTime = 0;
  private silenceCheckInterval: NodeJS.Timeout | null = null;

  // Configuration
  private readonly PAUSE_THRESHOLD_MS = 2000; // 2 seconds pause = auto-send
  private readonly SILENCE_THRESHOLD_MS = 3000; // 3 seconds silence = auto-stop
  private readonly VOICE_THRESHOLD = 0.01; // Volume threshold for voice detection
  private readonly CHUNK_SIZE = 4096; // Audio chunk size for streaming

  // Callbacks
  private callbacks: StreamingVoiceCallbacks = {};

  constructor(wsUrl: string = 'ws://localhost:5024/voice/stream') {
    this.wsUrl = wsUrl;
  }

  /**
   * Request microphone permission
   */
  async requestPermission(): Promise<boolean> {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 16000
        }
      });

      stream.getTracks().forEach(track => track.stop());
      return true;
    } catch (error) {
      console.error('Microphone permission denied:', error);
      return false;
    }
  }

  /**
   * Check if browser supports required features
   */
  isSupported(): boolean {
    return !!(
      navigator.mediaDevices &&
      navigator.mediaDevices.getUserMedia &&
      window.MediaRecorder &&
      window.WebSocket &&
      window.AudioContext
    );
  }

  /**
   * Start streaming voice recording
   */
  async startRecording(): Promise<void> {
    if (this.isRecording) {
      throw new Error('Already recording');
    }

    try {
      // Initialize WebSocket connection
      await this.connectWebSocket();

      // Get audio stream
      this.audioStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 16000,
          channelCount: 1
        }
      });

      // Setup audio processing
      this.audioContext = new AudioContext({ sampleRate: 16000 });
      const source = this.audioContext.createMediaStreamSource(this.audioStream);

      // Create analyser for visualization and VAD
      this.analyser = this.audioContext.createAnalyser();
      this.analyser.fftSize = 256;
      this.analyser.smoothingTimeConstant = 0.3;

      // Create script processor for streaming chunks
      this.scriptProcessor = this.audioContext.createScriptProcessor(this.CHUNK_SIZE, 1, 1);

      // Connect audio graph
      source.connect(this.analyser);
      source.connect(this.scriptProcessor);
      this.scriptProcessor.connect(this.audioContext.destination);

      // Handle audio processing
      this.scriptProcessor.onaudioprocess = (event) => {
        if (!this.isRecording) return;

        const inputData = event.inputBuffer.getChannelData(0);

        // Convert float32 to int16
        const int16Data = new Int16Array(inputData.length);
        for (let i = 0; i < inputData.length; i++) {
          const s = Math.max(-1, Math.min(1, inputData[i]));
          int16Data[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }

        // Send audio chunk via WebSocket
        if (this.ws?.readyState === WebSocket.OPEN) {
          this.ws.send(int16Data.buffer);
        }

        // Check for voice activity
        this.checkVoiceActivity(inputData);
      };

      // Start visualization
      this.startVisualization();

      // Start silence monitoring
      this.startSilenceMonitoring();

      this.isRecording = true;
      this.lastSpeechTime = Date.now();
      this.currentTranscript = '';
      this.callbacks.onRecordingStateChange?.(true);

    } catch (error) {
      this.callbacks.onError?.(error as Error);
      this.cleanup();
      throw error;
    }
  }

  /**
   * Stop recording and cleanup
   */
  stopRecording(): void {
    if (!this.isRecording) return;

    this.isRecording = false;
    this.callbacks.onRecordingStateChange?.(false);

    // Send final transcript if any
    if (this.currentTranscript.trim()) {
      this.callbacks.onAutoSend?.(this.currentTranscript);
    }

    this.cleanup();
  }

  /**
   * Connect to WebSocket for streaming
   */
  private async connectWebSocket(): Promise<void> {
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket(this.wsUrl);

      this.ws.onopen = () => {
        console.log('WebSocket connected for streaming voice');
        // Send initial configuration
        this.ws?.send(JSON.stringify({
          type: 'config',
          sampleRate: 16000,
          encoding: 'pcm16',
          language: 'en-US',
          streaming: true
        }));
        resolve();
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          if (data.type === 'transcript') {
            this.handleTranscript(data);
          } else if (data.type === 'error') {
            this.callbacks.onError?.(new Error(data.message));
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.callbacks.onError?.(new Error('WebSocket connection failed'));
        reject(error);
      };

      this.ws.onclose = () => {
        console.log('WebSocket closed');
        if (this.isRecording) {
          this.stopRecording();
        }
      };

      // Timeout for connection
      setTimeout(() => {
        if (this.ws?.readyState !== WebSocket.OPEN) {
          reject(new Error('WebSocket connection timeout'));
        }
      }, 5000);
    });
  }

  /**
   * Handle incoming transcript
   */
  private handleTranscript(data: any): void {
    const transcript: StreamingTranscriptData = {
      text: data.text || '',
      isFinal: data.isFinal || false,
      confidence: data.confidence
    };

    // Update current transcript
    if (transcript.isFinal) {
      this.currentTranscript = transcript.text;
    }

    // Notify callback with live transcript
    this.callbacks.onTranscript?.(transcript);

    // Reset speech timer when we get new speech
    if (transcript.text.trim()) {
      this.lastSpeechTime = Date.now();
    }
  }

  /**
   * Check for voice activity in audio data
   */
  private checkVoiceActivity(audioData: Float32Array): void {
    // Calculate RMS (volume)
    let sum = 0;
    for (let i = 0; i < audioData.length; i++) {
      sum += audioData[i] * audioData[i];
    }
    const volume = Math.sqrt(sum / audioData.length);

    // Determine if user is speaking
    const isSpeaking = volume > this.VOICE_THRESHOLD;

    if (isSpeaking) {
      this.lastSpeechTime = Date.now();
    }

    const now = Date.now();
    const silenceDuration = now - this.lastSpeechTime;

    // Notify voice activity state
    this.callbacks.onVoiceActivity?.({
      isSpeaking,
      silenceDuration,
      pauseDuration: isSpeaking ? 0 : silenceDuration
    });
  }

  /**
   * Monitor for silence and pauses
   */
  private startSilenceMonitoring(): void {
    this.silenceCheckInterval = setInterval(() => {
      if (!this.isRecording) return;

      const now = Date.now();
      const silenceDuration = now - this.lastSpeechTime;

      // Check for pause (2 seconds) - auto send
      if (silenceDuration >= this.PAUSE_THRESHOLD_MS &&
          silenceDuration < this.PAUSE_THRESHOLD_MS + 100 && // Only trigger once
          this.currentTranscript.trim()) {
        console.log('Auto-sending after 2 second pause');
        this.callbacks.onAutoSend?.(this.currentTranscript);
        this.currentTranscript = ''; // Clear after sending
      }

      // Check for complete silence (3 seconds) - auto stop
      if (silenceDuration >= this.SILENCE_THRESHOLD_MS) {
        console.log('Auto-stopping after 3 seconds of silence');
        this.callbacks.onAutoStop?.();
        this.stopRecording();
      }
    }, 100); // Check every 100ms
  }

  /**
   * Start audio visualization
   */
  private startVisualization(): void {
    if (!this.analyser) return;

    const bufferLength = this.analyser.frequencyBinCount;
    const waveformData = new Uint8Array(bufferLength);
    const frequencyData = new Uint8Array(bufferLength);

    const visualize = () => {
      if (!this.isRecording || !this.analyser) return;

      this.analyser.getByteTimeDomainData(waveformData);
      this.analyser.getByteFrequencyData(frequencyData);

      // Calculate volume
      let sum = 0;
      for (let i = 0; i < bufferLength; i++) {
        const normalized = (waveformData[i] - 128) / 128;
        sum += normalized * normalized;
      }
      const volume = Math.sqrt(sum / bufferLength);

      this.callbacks.onVisualization?.({
        waveform: waveformData,
        frequency: frequencyData,
        volume
      });

      requestAnimationFrame(visualize);
    };

    visualize();
  }

  /**
   * Clean up resources
   */
  private cleanup(): void {
    // Stop silence monitoring
    if (this.silenceCheckInterval) {
      clearInterval(this.silenceCheckInterval);
      this.silenceCheckInterval = null;
    }

    // Close WebSocket
    if (this.ws) {
      if (this.ws.readyState === WebSocket.OPEN) {
        this.ws.close();
      }
      this.ws = null;
    }

    // Stop audio stream
    if (this.audioStream) {
      this.audioStream.getTracks().forEach(track => track.stop());
      this.audioStream = null;
    }

    // Disconnect audio nodes
    if (this.scriptProcessor) {
      this.scriptProcessor.disconnect();
      this.scriptProcessor = null;
    }

    if (this.analyser) {
      this.analyser.disconnect();
      this.analyser = null;
    }

    // Close audio context
    if (this.audioContext) {
      this.audioContext.close();
      this.audioContext = null;
    }

    this.currentTranscript = '';
  }

  /**
   * Set callbacks
   */
  setCallbacks(callbacks: StreamingVoiceCallbacks): void {
    this.callbacks = { ...this.callbacks, ...callbacks };
  }

  /**
   * Get current recording state
   */
  getIsRecording(): boolean {
    return this.isRecording;
  }

  /**
   * Get current transcript
   */
  getCurrentTranscript(): string {
    return this.currentTranscript;
  }

  /**
   * Dispose of the service
   */
  dispose(): void {
    this.stopRecording();
    this.callbacks = {};
  }
}