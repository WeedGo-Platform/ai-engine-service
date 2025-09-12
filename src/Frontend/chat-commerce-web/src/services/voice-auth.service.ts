/**
 * Voice Authentication Service
 * Handles voice-based authentication with secure audio capture and transmission
 * Implements industry best practices for biometric authentication
 */

import { apiClient } from './api-client';
import { voiceLivenessService, LivenessCheckResult } from './voice-liveness.service';

export interface VoiceAuthResult {
  success: boolean;
  authenticated: boolean;
  user?: {
    id: string;
    email: string;
    name: string;
    age_verified: boolean;
  };
  confidence?: number;
  age_info?: {
    verified: boolean;
    estimated_age?: number;
    confidence?: number;
  };
  liveness?: LivenessCheckResult;
  message?: string;
}

export interface VoiceEnrollmentResult {
  success: boolean;
  message: string;
  user_id?: string;
  age_verification?: {
    verified: boolean;
    estimated_age?: number;
  };
}

export interface AudioRecordingOptions {
  duration?: number;
  sampleRate?: number;
  channelCount?: number;
  echoCancellation?: boolean;
  noiseSuppression?: boolean;
  autoGainControl?: boolean;
}

export class VoiceAuthService {
  private static instance: VoiceAuthService;
  private mediaRecorder: MediaRecorder | null = null;
  private audioContext: AudioContext | null = null;
  private analyser: AnalyserNode | null = null;
  private audioChunks: Blob[] = [];
  private isRecording = false;
  private stream: MediaStream | null = null;
  private enableLivenessDetection = true;
  private challengeMode = false;

  private readonly DEFAULT_OPTIONS: AudioRecordingOptions = {
    duration: 5000,
    sampleRate: 16000,
    channelCount: 1,
    echoCancellation: true,
    noiseSuppression: true,
    autoGainControl: true
  };

  private constructor() {
    this.initializeAudioContext();
  }

  public static getInstance(): VoiceAuthService {
    if (!VoiceAuthService.instance) {
      VoiceAuthService.instance = new VoiceAuthService();
    }
    return VoiceAuthService.instance;
  }

  private async initializeAudioContext(): Promise<void> {
    try {
      const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
      if (AudioContextClass) {
        this.audioContext = new AudioContextClass();
      }
    } catch (error) {
      console.error('Failed to initialize audio context:', error);
    }
  }

  /**
   * Check if voice authentication is supported in the current browser
   */
  public isSupported(): boolean {
    return !!(
      navigator.mediaDevices &&
      navigator.mediaDevices.getUserMedia &&
      window.MediaRecorder &&
      (window.AudioContext || (window as any).webkitAudioContext)
    );
  }

  /**
   * Request microphone permissions
   */
  public async requestMicrophonePermission(): Promise<boolean> {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach(track => track.stop());
      return true;
    } catch (error) {
      console.error('Microphone permission denied:', error);
      return false;
    }
  }

  /**
   * Start recording audio for authentication
   */
  public async startRecording(
    options: AudioRecordingOptions = {},
    onAudioData?: (data: Float32Array) => void
  ): Promise<void> {
    if (this.isRecording) {
      throw new Error('Recording already in progress');
    }

    const config = { ...this.DEFAULT_OPTIONS, ...options };

    try {
      // Get user media with specified constraints
      this.stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: config.channelCount,
          sampleRate: config.sampleRate,
          echoCancellation: config.echoCancellation,
          noiseSuppression: config.noiseSuppression,
          autoGainControl: config.autoGainControl
        }
      });

      // Setup audio analysis for visualization
      if (this.audioContext && onAudioData) {
        const source = this.audioContext.createMediaStreamSource(this.stream);
        this.analyser = this.audioContext.createAnalyser();
        this.analyser.fftSize = 256;
        source.connect(this.analyser);

        // Start animation loop for audio visualization
        this.startVisualization(onAudioData);
      }

      // Setup media recorder
      this.audioChunks = [];
      this.mediaRecorder = new MediaRecorder(this.stream, {
        mimeType: this.getSupportedMimeType()
      });

      this.mediaRecorder.addEventListener('dataavailable', (event) => {
        if (event.data.size > 0) {
          this.audioChunks.push(event.data);
        }
      });

      this.mediaRecorder.start();
      this.isRecording = true;

      // Auto-stop after duration if specified
      if (config.duration) {
        setTimeout(() => {
          if (this.isRecording) {
            this.stopRecording();
          }
        }, config.duration);
      }
    } catch (error) {
      this.cleanup();
      throw new Error(`Failed to start recording: ${error}`);
    }
  }

  /**
   * Stop recording and return the audio blob
   */
  public async stopRecording(): Promise<Blob> {
    if (!this.isRecording || !this.mediaRecorder) {
      // Clean up any resources even if no recording
      this.cleanup();
      throw new Error('No recording in progress');
    }

    return new Promise((resolve, reject) => {
      if (!this.mediaRecorder) {
        this.cleanup();
        reject(new Error('Media recorder not initialized'));
        return;
      }

      // Add timeout to prevent hanging
      const stopTimeout = setTimeout(() => {
        this.cleanup();
        reject(new Error('Recording stop timeout - please try again'));
      }, 5000);

      // Add error handler
      const errorHandler = (error: Event) => {
        clearTimeout(stopTimeout);
        this.cleanup();
        reject(new Error('Recording error: ' + (error as any).message));
      };

      // Add stop handler
      const stopHandler = () => {
        clearTimeout(stopTimeout);
        // Remove event listeners
        if (this.mediaRecorder) {
          this.mediaRecorder.removeEventListener('stop', stopHandler);
          this.mediaRecorder.removeEventListener('error', errorHandler);
        }
        
        const audioBlob = new Blob(this.audioChunks, {
          type: this.getSupportedMimeType()
        });
        this.cleanup();
        resolve(audioBlob);
      };

      this.mediaRecorder.addEventListener('stop', stopHandler);
      this.mediaRecorder.addEventListener('error', errorHandler);

      try {
        this.mediaRecorder.stop();
        this.isRecording = false;
      } catch (error) {
        clearTimeout(stopTimeout);
        this.cleanup();
        reject(new Error('Failed to stop recording: ' + (error as any).message));
      }
    });
  }

  /**
   * Cancel recording without saving
   */
  public cancelRecording(): void {
    try {
      if (this.isRecording && this.mediaRecorder) {
        this.mediaRecorder.stop();
        this.isRecording = false;
      }
    } catch (error) {
      console.error('Error stopping media recorder:', error);
    } finally {
      // Always cleanup, even if stop fails
      this.cleanup();
    }
  }

  /**
   * Authenticate user with voice
   */
  public async authenticateVoice(audioBlob: Blob, performLivenessCheck = true): Promise<VoiceAuthResult> {
    try {
      // Perform liveness detection if enabled
      let livenessResult: LivenessCheckResult | undefined;
      if (performLivenessCheck && this.enableLivenessDetection) {
        livenessResult = await voiceLivenessService.performLivenessCheck(audioBlob, this.stream || undefined);
        
        // If liveness check fails with high confidence, reject immediately
        if (!livenessResult.isLive && livenessResult.confidence > 0.8) {
          return {
            success: false,
            authenticated: false,
            liveness: livenessResult,
            message: 'Voice liveness check failed. Please use your live voice.'
          };
        }
      }

      // Convert blob to base64 for transmission
      const base64Audio = await this.blobToBase64(audioBlob);

      const formData = new FormData();
      formData.append('audio_base64', base64Audio.split(',')[1]);
      if (livenessResult) {
        formData.append('liveness_score', livenessResult.confidence.toString());
        formData.append('liveness_details', JSON.stringify(livenessResult.checks));
      }

      const response = await apiClient.post<VoiceAuthResult>(
        '/api/v1/auth/voice/login/base64',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        }
      );

      // Add liveness result to response
      if (livenessResult) {
        response.liveness = livenessResult;
      }
      return response;
    } catch (error: any) {
      console.error('Voice authentication failed:', error);
      return {
        success: false,
        authenticated: false,
        message: error.response?.data?.detail || 'Voice authentication failed'
      };
    }
  }

  /**
   * Generate a challenge for enhanced liveness detection
   */
  public generateChallenge(): {
    type: 'numeric' | 'word' | 'phrase';
    challenge: string;
    expectedDuration: number;
  } {
    return voiceLivenessService.generateRandomChallenge();
  }

  /**
   * Verify challenge response
   */
  public async verifyChallengeResponse(
    audioBlob: Blob,
    expectedChallenge: string,
    type: 'numeric' | 'word' | 'phrase'
  ): Promise<{ matches: boolean; confidence: number }> {
    return voiceLivenessService.verifyChallengeResponse(audioBlob, expectedChallenge, type);
  }

  /**
   * Enable or disable liveness detection
   */
  public setLivenessDetection(enabled: boolean): void {
    this.enableLivenessDetection = enabled;
  }

  /**
   * Enable or disable challenge mode for extra security
   */
  public setChallengeMode(enabled: boolean): void {
    this.challengeMode = enabled;
  }

  /**
   * Enroll voice profile for a user
   */
  public async enrollVoiceProfile(
    userId: string,
    audioBlob: Blob,
    metadata?: Record<string, any>
  ): Promise<VoiceEnrollmentResult> {
    try {
      // Perform liveness check for enrollment too
      if (this.enableLivenessDetection) {
        const livenessResult = await voiceLivenessService.performLivenessCheck(audioBlob, this.stream || undefined);
        if (!livenessResult.isLive && livenessResult.confidence > 0.8) {
          return {
            success: false,
            message: 'Liveness check failed during enrollment. Please use your live voice.'
          };
        }
        // Add liveness info to metadata
        if (!metadata) metadata = {};
        metadata.liveness_score = livenessResult.confidence;
        metadata.liveness_checks = livenessResult.checks;
      }

      const formData = new FormData();
      formData.append('user_id', userId);
      formData.append('audio', audioBlob, 'voice_sample.wav');
      if (metadata) {
        formData.append('metadata', JSON.stringify(metadata));
      }

      const response = await apiClient.post<VoiceEnrollmentResult>(
        '/api/v1/auth/voice/register',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        }
      );

      return response;
    } catch (error: any) {
      console.error('Voice enrollment failed:', error);
      return {
        success: false,
        message: error.response?.data?.detail || 'Voice enrollment failed'
      };
    }
  }

  /**
   * Verify age using voice (anonymous)
   */
  public async verifyAge(audioBlob: Blob): Promise<{
    success: boolean;
    verified: boolean;
    age_info?: {
      estimated_age?: number;
      confidence?: number;
    };
  }> {
    try {
      const formData = new FormData();
      formData.append('audio', audioBlob, 'voice_sample.wav');

      const response = await apiClient.post(
        '/api/v1/auth/voice/verify-age',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        }
      );

      return response;
    } catch (error: any) {
      console.error('Age verification failed:', error);
      return {
        success: false,
        verified: false
      };
    }
  }

  /**
   * Get voice profile for a user
   */
  public async getVoiceProfile(userId: string): Promise<any> {
    try {
      return await apiClient.get(`/api/v1/auth/voice/profile/${userId}`);
    } catch (error) {
      console.error('Failed to get voice profile:', error);
      return null;
    }
  }

  /**
   * Delete voice profile for a user
   */
  public async deleteVoiceProfile(userId: string): Promise<boolean> {
    try {
      const response = await apiClient.delete(`/api/v1/auth/voice/profile/${userId}`);
      return response.success;
    } catch (error) {
      console.error('Failed to delete voice profile:', error);
      return false;
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
      'audio/ogg',
      'audio/mp4',
      'audio/wav'
    ];

    for (const type of types) {
      if (MediaRecorder.isTypeSupported(type)) {
        return type;
      }
    }

    return 'audio/webm';
  }

  /**
   * Convert blob to base64
   */
  private blobToBase64(blob: Blob): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onloadend = () => {
        if (typeof reader.result === 'string') {
          resolve(reader.result);
        } else {
          reject(new Error('Failed to convert blob to base64'));
        }
      };
      reader.onerror = reject;
      reader.readAsDataURL(blob);
    });
  }

  /**
   * Start audio visualization
   */
  private startVisualization(onAudioData: (data: Float32Array) => void): void {
    if (!this.analyser) return;

    const bufferLength = this.analyser.frequencyBinCount;
    const dataArray = new Float32Array(bufferLength);

    const animate = () => {
      if (!this.isRecording || !this.analyser) return;

      // Use time domain data for better waveform visualization
      this.analyser.getFloatTimeDomainData(dataArray);
      onAudioData(dataArray);

      requestAnimationFrame(animate);
    };

    animate();
  }

  /**
   * Cleanup resources
   */
  private cleanup(): void {
    try {
      if (this.stream) {
        this.stream.getTracks().forEach(track => {
          try {
            track.stop();
          } catch (e) {
            console.error('Error stopping track:', e);
          }
        });
        this.stream = null;
      }

      if (this.analyser) {
        try {
          this.analyser.disconnect();
        } catch (e) {
          console.error('Error disconnecting analyser:', e);
        }
        this.analyser = null;
      }

      this.mediaRecorder = null;
      this.audioChunks = [];
      this.isRecording = false;
    } catch (error) {
      console.error('Error during cleanup:', error);
    }
  }

  /**
   * Calculate audio level for visualization
   */
  public calculateAudioLevel(dataArray: Float32Array): number {
    let sum = 0;
    for (let i = 0; i < dataArray.length; i++) {
      sum += Math.abs(dataArray[i]);
    }
    return sum / dataArray.length;
  }
}

// Export singleton instance
export const voiceAuthService = VoiceAuthService.getInstance();