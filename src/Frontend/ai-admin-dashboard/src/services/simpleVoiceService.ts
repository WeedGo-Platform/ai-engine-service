/**
 * Simple Voice Service using REST API
 * Uses the existing /api/voice endpoints for transcription and synthesis
 */

export class SimpleVoiceService {
  private mediaRecorder: MediaRecorder | null = null;
  private audioStream: MediaStream | null = null;
  private audioChunks: Blob[] = [];
  private isRecording = false;
  private onTranscriptCallback: ((text: string) => void) | null = null;
  private apiBase = 'http://localhost:5024';

  /**
   * Request microphone permission
   */
  async requestPermission(): Promise<boolean> {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
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
   * Start recording audio
   */
  async startRecording(): Promise<void> {
    if (this.isRecording) return;

    try {
      // Get audio stream
      this.audioStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      });

      // Create media recorder
      this.mediaRecorder = new MediaRecorder(this.audioStream);
      this.audioChunks = [];

      this.mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          this.audioChunks.push(event.data);
        }
      };

      this.mediaRecorder.onstop = async () => {
        // Create audio blob
        const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });

        // Transcribe the audio
        await this.transcribeAudio(audioBlob);
      };

      // Start recording
      this.mediaRecorder.start();
      this.isRecording = true;
    } catch (error) {
      console.error('Failed to start recording:', error);
      throw error;
    }
  }

  /**
   * Stop recording
   */
  stopRecording(): void {
    if (!this.isRecording) return;

    this.isRecording = false;

    if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
      this.mediaRecorder.stop();
    }

    if (this.audioStream) {
      this.audioStream.getTracks().forEach(track => track.stop());
      this.audioStream = null;
    }
  }

  /**
   * Transcribe audio using REST API
   */
  private async transcribeAudio(audioBlob: Blob): Promise<void> {
    try {
      const formData = new FormData();
      formData.append('audio', audioBlob, 'recording.webm');
      formData.append('language', 'en');
      formData.append('mode', 'auto_vad');

      const response = await fetch(`${this.apiBase}/api/voice/transcribe`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error('Transcription failed');
      }

      const result = await response.json();

      if (result.status === 'success' && result.result?.text) {
        const transcript = result.result.text.trim();
        if (transcript && this.onTranscriptCallback) {
          this.onTranscriptCallback(transcript);
        }
      }
    } catch (error) {
      console.error('Transcription error:', error);
      // Fallback to browser's Web Speech API if available
      await this.fallbackToWebSpeechAPI(audioBlob);
    }
  }

  /**
   * Fallback to browser's Web Speech API
   */
  private async fallbackToWebSpeechAPI(audioBlob: Blob): Promise<void> {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      console.error('Speech recognition not supported');
      return;
    }

    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    const recognition = new SpeechRecognition();

    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';

    recognition.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript;
      if (transcript && this.onTranscriptCallback) {
        this.onTranscriptCallback(transcript);
      }
    };

    recognition.onerror = (event: any) => {
      console.error('Speech recognition error:', event.error);
    };

    // Start a new recognition session
    recognition.start();

    // Since we can't directly feed the blob to Web Speech API,
    // we'll use it for the next recording session
    setTimeout(() => recognition.stop(), 5000); // Stop after 5 seconds
  }

  /**
   * Set transcript callback
   */
  onTranscript(callback: (text: string) => void): void {
    this.onTranscriptCallback = callback;
  }

  /**
   * Check if recording
   */
  getIsRecording(): boolean {
    return this.isRecording;
  }

  /**
   * Use Web Speech API for simple transcription
   */
  async startWebSpeechRecognition(): Promise<void> {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      // Fall back to regular recording
      await this.startRecording();
      return;
    }

    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    const recognition = new SpeechRecognition();

    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onresult = (event: any) => {
      let finalTranscript = '';
      let interimTranscript = '';

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          finalTranscript += transcript;
        } else {
          interimTranscript += transcript;
        }
      }

      const fullTranscript = finalTranscript || interimTranscript;
      if (fullTranscript && this.onTranscriptCallback) {
        this.onTranscriptCallback(fullTranscript);
      }

      // Auto-stop after 3 seconds of silence
      if (finalTranscript) {
        setTimeout(() => {
          if (this.isRecording) {
            recognition.stop();
            this.isRecording = false;
          }
        }, 3000);
      }
    };

    recognition.onerror = (event: any) => {
      console.error('Speech recognition error:', event.error);
      this.isRecording = false;
    };

    recognition.onend = () => {
      this.isRecording = false;
    };

    recognition.start();
    this.isRecording = true;
  }

  /**
   * Stop Web Speech Recognition
   */
  stopWebSpeechRecognition(): void {
    // The recognition will stop automatically
    this.isRecording = false;
  }
}