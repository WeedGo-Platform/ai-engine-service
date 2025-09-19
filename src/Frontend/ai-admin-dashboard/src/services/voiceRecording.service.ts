/**
 * Voice Recording Service
 * Handles microphone permissions, audio recording, and WebRTC API integration
 */

export interface AudioVisualizationData {
  waveform: Uint8Array;
  frequency: Uint8Array;
  volume: number;
}

export class VoiceRecordingService {
  private mediaRecorder: MediaRecorder | null = null;
  private audioStream: MediaStream | null = null;
  private audioContext: AudioContext | null = null;
  private analyser: AnalyserNode | null = null;
  private audioChunks: Blob[] = [];
  private isRecording = false;
  private maxRecordingTime = 60000; // 60 seconds max
  private recordingTimer: NodeJS.Timeout | null = null;

  // Callbacks
  private onDataCallback: ((data: Blob) => void) | null = null;
  private onVisualizationCallback: ((data: AudioVisualizationData) => void) | null = null;
  private onErrorCallback: ((error: Error) => void) | null = null;
  private onRecordingStateChangeCallback: ((isRecording: boolean) => void) | null = null;

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

      // Stop the stream immediately after getting permission
      stream.getTracks().forEach(track => track.stop());
      return true;
    } catch (error) {
      console.error('Microphone permission denied:', error);
      return false;
    }
  }

  /**
   * Check if browser supports audio recording
   */
  isSupported(): boolean {
    return !!(
      navigator.mediaDevices &&
      navigator.mediaDevices.getUserMedia &&
      window.MediaRecorder
    );
  }

  /**
   * Start recording audio
   */
  async startRecording(): Promise<void> {
    if (this.isRecording) {
      throw new Error('Already recording');
    }

    try {
      // Get audio stream
      this.audioStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 16000
        }
      });

      // Setup audio context for visualization
      this.audioContext = new AudioContext();
      const source = this.audioContext.createMediaStreamSource(this.audioStream);
      this.analyser = this.audioContext.createAnalyser();
      this.analyser.fftSize = 256;
      source.connect(this.analyser);

      // Start visualization
      this.startVisualization();

      // Setup MediaRecorder
      const mimeType = this.getSupportedMimeType();
      this.mediaRecorder = new MediaRecorder(this.audioStream, { mimeType });

      this.audioChunks = [];

      this.mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          this.audioChunks.push(event.data);
        }
      };

      this.mediaRecorder.onstop = () => {
        const audioBlob = new Blob(this.audioChunks, { type: mimeType });
        this.onDataCallback?.(audioBlob);
        this.cleanup();
      };

      this.mediaRecorder.onerror = (event: any) => {
        this.onErrorCallback?.(new Error(event.error || 'Recording error'));
        this.stopRecording();
      };

      // Start recording
      this.mediaRecorder.start(1000); // Collect data every second
      this.isRecording = true;
      this.onRecordingStateChangeCallback?.(true);

      // Set max recording time
      this.recordingTimer = setTimeout(() => {
        this.stopRecording();
      }, this.maxRecordingTime);

    } catch (error) {
      this.onErrorCallback?.(error as Error);
      this.cleanup();
      throw error;
    }
  }

  /**
   * Stop recording audio
   */
  stopRecording(): void {
    if (!this.isRecording || !this.mediaRecorder) {
      return;
    }

    if (this.recordingTimer) {
      clearTimeout(this.recordingTimer);
      this.recordingTimer = null;
    }

    this.isRecording = false;
    this.onRecordingStateChangeCallback?.(false);

    if (this.mediaRecorder.state !== 'inactive') {
      this.mediaRecorder.stop();
    }
  }

  /**
   * Get supported MIME type for recording
   */
  private getSupportedMimeType(): string {
    const types = [
      'audio/webm;codecs=opus',
      'audio/webm',
      'audio/ogg;codecs=opus',
      'audio/mp4',
      'audio/mpeg'
    ];

    for (const type of types) {
      if (MediaRecorder.isTypeSupported(type)) {
        return type;
      }
    }

    return 'audio/webm'; // Fallback
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

      // Calculate volume (RMS)
      let sum = 0;
      for (let i = 0; i < bufferLength; i++) {
        const normalized = (waveformData[i] - 128) / 128;
        sum += normalized * normalized;
      }
      const volume = Math.sqrt(sum / bufferLength);

      this.onVisualizationCallback?.({
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
    // Stop all tracks
    if (this.audioStream) {
      this.audioStream.getTracks().forEach(track => track.stop());
      this.audioStream = null;
    }

    // Close audio context
    if (this.audioContext) {
      this.audioContext.close();
      this.audioContext = null;
    }

    this.analyser = null;
    this.mediaRecorder = null;
    this.audioChunks = [];
  }

  /**
   * Convert blob to base64
   */
  async blobToBase64(blob: Blob): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onloadend = () => {
        const base64 = reader.result as string;
        // Remove data URL prefix
        const base64Data = base64.split(',')[1];
        resolve(base64Data);
      };
      reader.onerror = reject;
      reader.readAsDataURL(blob);
    });
  }

  /**
   * Set callback handlers
   */
  onData(callback: (data: Blob) => void): void {
    this.onDataCallback = callback;
  }

  onVisualization(callback: (data: AudioVisualizationData) => void): void {
    this.onVisualizationCallback = callback;
  }

  onError(callback: (error: Error) => void): void {
    this.onErrorCallback = callback;
  }

  onRecordingStateChange(callback: (isRecording: boolean) => void): void {
    this.onRecordingStateChangeCallback = callback;
  }

  /**
   * Get current recording state
   */
  getIsRecording(): boolean {
    return this.isRecording;
  }

  /**
   * Dispose of the service
   */
  dispose(): void {
    this.stopRecording();
    this.cleanup();
    this.onDataCallback = null;
    this.onVisualizationCallback = null;
    this.onErrorCallback = null;
    this.onRecordingStateChangeCallback = null;
  }
}

// Singleton instance
let voiceRecordingServiceInstance: VoiceRecordingService | null = null;

export const getVoiceRecordingService = (): VoiceRecordingService => {
  if (!voiceRecordingServiceInstance) {
    voiceRecordingServiceInstance = new VoiceRecordingService();
  }
  return voiceRecordingServiceInstance;
};