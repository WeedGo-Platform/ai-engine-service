/**
 * Voice Activity Detection (VAD) for Frontend
 * Detects speech in audio to reduce bandwidth and improve accuracy
 */

export interface VADConfig {
  // Energy thresholds
  silenceThreshold: number;      // Below this = silence
  speechThreshold: number;        // Above this = speech

  // Timing parameters (in ms)
  minSpeechDuration: number;      // Minimum speech to be valid
  maxSilenceDuration: number;     // Max silence before cutting
  preSpeechPadding: number;       // Audio to include before speech
  postSpeechPadding: number;      // Audio to include after speech

  // Smoothing
  smoothingFactor: number;        // For energy averaging

  // Adaptive threshold
  adaptiveThreshold: boolean;     // Dynamically adjust thresholds
  noiseFloor: number;            // Baseline noise level
}

export interface VADResult {
  isSpeech: boolean;
  energy: number;
  confidence: number;
  shouldSend: boolean;
  audioToSend?: Float32Array;
}

export class VoiceActivityDetector {
  private config: VADConfig;
  private energyHistory: number[] = [];
  private speechBuffer: Float32Array[] = [];
  private silenceBuffer: Float32Array[] = [];
  private preSpeechBuffer: Float32Array[] = [];

  private isSpeaking: boolean = false;
  private speechStartTime: number = 0;
  private silenceStartTime: number = 0;
  private lastSpeechTime: number = 0;

  private noiseFloor: number = 0;
  private adaptiveThreshold: number = 0;

  // Statistics for debugging
  private stats = {
    totalChunks: 0,
    speechChunks: 0,
    silenceChunks: 0,
    segmentsSent: 0,
  };

  constructor(config?: Partial<VADConfig>) {
    this.config = {
      silenceThreshold: 0.01,
      speechThreshold: 0.02,
      minSpeechDuration: 250,      // 250ms minimum speech
      maxSilenceDuration: 1500,     // 1.5 seconds max silence
      preSpeechPadding: 200,        // 200ms before speech
      postSpeechPadding: 300,       // 300ms after speech
      smoothingFactor: 0.95,
      adaptiveThreshold: true,
      noiseFloor: 0.005,
      ...config
    };

    this.adaptiveThreshold = this.config.speechThreshold;
  }

  /**
   * Process an audio chunk and determine if it contains speech
   */
  processAudioChunk(
    audioData: Float32Array,
    sampleRate: number = 16000
  ): VADResult {
    this.stats.totalChunks++;

    // Calculate energy (RMS - Root Mean Square)
    const energy = this.calculateEnergy(audioData);

    // Update energy history for smoothing
    this.energyHistory.push(energy);
    if (this.energyHistory.length > 10) {
      this.energyHistory.shift();
    }

    // Calculate smoothed energy
    const smoothedEnergy = this.getSmoothedEnergy();

    // Update adaptive threshold if enabled
    if (this.config.adaptiveThreshold) {
      this.updateAdaptiveThreshold(smoothedEnergy);
    }

    // Determine if this is speech
    const isSpeech = this.detectSpeech(smoothedEnergy);
    const confidence = this.calculateConfidence(smoothedEnergy);

    // Handle the audio based on speech detection
    const result = this.handleAudioChunk(
      audioData,
      isSpeech,
      smoothedEnergy,
      sampleRate
    );

    return {
      isSpeech,
      energy: smoothedEnergy,
      confidence,
      ...result
    };
  }

  /**
   * Calculate energy (RMS) of audio data
   */
  private calculateEnergy(audioData: Float32Array): number {
    let sum = 0;
    for (let i = 0; i < audioData.length; i++) {
      sum += audioData[i] * audioData[i];
    }
    return Math.sqrt(sum / audioData.length);
  }

  /**
   * Get smoothed energy using exponential moving average
   */
  private getSmoothedEnergy(): number {
    if (this.energyHistory.length === 0) return 0;

    let weightedSum = 0;
    let weightSum = 0;
    const factor = this.config.smoothingFactor;

    for (let i = this.energyHistory.length - 1; i >= 0; i--) {
      const weight = Math.pow(factor, this.energyHistory.length - 1 - i);
      weightedSum += this.energyHistory[i] * weight;
      weightSum += weight;
    }

    return weightSum > 0 ? weightedSum / weightSum : 0;
  }

  /**
   * Update adaptive threshold based on noise floor
   */
  private updateAdaptiveThreshold(energy: number): void {
    if (!this.isSpeaking) {
      // Update noise floor estimate during silence
      this.noiseFloor = this.noiseFloor * 0.95 + energy * 0.05;

      // Set threshold above noise floor
      this.adaptiveThreshold = Math.max(
        this.noiseFloor * 3, // 3x noise floor
        this.config.speechThreshold
      );
    }
  }

  /**
   * Detect if audio contains speech
   */
  private detectSpeech(energy: number): boolean {
    const threshold = this.config.adaptiveThreshold
      ? this.adaptiveThreshold
      : this.config.speechThreshold;

    return energy > threshold;
  }

  /**
   * Calculate confidence score for speech detection
   */
  private calculateConfidence(energy: number): number {
    const threshold = this.config.adaptiveThreshold
      ? this.adaptiveThreshold
      : this.config.speechThreshold;

    if (energy <= this.config.silenceThreshold) return 0;
    if (energy >= threshold * 2) return 1;

    // Linear interpolation between silence and 2x threshold
    const range = threshold * 2 - this.config.silenceThreshold;
    const position = energy - this.config.silenceThreshold;
    return Math.min(1, Math.max(0, position / range));
  }

  /**
   * Handle audio chunk based on speech detection
   */
  private handleAudioChunk(
    audioData: Float32Array,
    isSpeech: boolean,
    energy: number,
    sampleRate: number
  ): { shouldSend: boolean; audioToSend?: Float32Array } {
    const chunkDuration = (audioData.length / sampleRate) * 1000; // ms
    const now = Date.now();

    if (isSpeech) {
      this.stats.speechChunks++;

      if (!this.isSpeaking) {
        // Speech just started
        console.log('[VAD] Speech started');
        this.isSpeaking = true;
        this.speechStartTime = now;

        // Include pre-speech buffer for context
        this.speechBuffer = [...this.preSpeechBuffer];
        this.preSpeechBuffer = [];
      }

      // Add to speech buffer
      this.speechBuffer.push(audioData);
      this.lastSpeechTime = now;

      // Clear silence buffer when speech is detected
      this.silenceBuffer = [];
      this.silenceStartTime = 0;

    } else {
      this.stats.silenceChunks++;

      // Add to pre-speech buffer (circular buffer)
      this.preSpeechBuffer.push(audioData);
      const maxPreBufferSize = Math.ceil(
        (this.config.preSpeechPadding / 1000) * sampleRate / audioData.length
      );
      if (this.preSpeechBuffer.length > maxPreBufferSize) {
        this.preSpeechBuffer.shift();
      }

      if (this.isSpeaking) {
        // Silence during speech - might be a pause
        if (this.silenceStartTime === 0) {
          this.silenceStartTime = now;
        }

        this.silenceBuffer.push(audioData);

        const silenceDuration = now - this.silenceStartTime;

        if (silenceDuration >= this.config.maxSilenceDuration) {
          // Too much silence - end the speech segment
          console.log('[VAD] Speech ended (silence timeout)');
          return this.endSpeechSegment(sampleRate);
        }
      }
    }

    // Check if we should send accumulated speech
    if (this.isSpeaking) {
      const speechDuration = now - this.speechStartTime;

      // Send periodically during long speech (every 5 seconds)
      if (speechDuration > 5000 && this.speechBuffer.length > 50) {
        console.log('[VAD] Sending ongoing speech segment');
        return this.sendSpeechSegment(sampleRate, false);
      }
    }

    return { shouldSend: false };
  }

  /**
   * End speech segment and prepare audio for sending
   */
  private endSpeechSegment(sampleRate: number): { shouldSend: boolean; audioToSend?: Float32Array } {
    this.isSpeaking = false;
    const speechDuration = this.lastSpeechTime - this.speechStartTime;

    // Check if speech was long enough
    if (speechDuration < this.config.minSpeechDuration) {
      console.log(`[VAD] Speech too short (${speechDuration}ms), discarding`);
      this.speechBuffer = [];
      this.silenceBuffer = [];
      return { shouldSend: false };
    }

    return this.sendSpeechSegment(sampleRate, true);
  }

  /**
   * Prepare and send speech segment
   */
  private sendSpeechSegment(
    sampleRate: number,
    isFinal: boolean
  ): { shouldSend: boolean; audioToSend?: Float32Array } {
    if (this.speechBuffer.length === 0) {
      return { shouldSend: false };
    }

    // Include post-speech padding (but not all silence)
    const maxPostBufferSize = Math.ceil(
      (this.config.postSpeechPadding / 1000) * sampleRate / this.speechBuffer[0].length
    );
    const postBuffer = this.silenceBuffer.slice(0, maxPostBufferSize);

    // Combine all audio
    const allBuffers = [...this.speechBuffer, ...postBuffer];
    const totalLength = allBuffers.reduce((sum, buf) => sum + buf.length, 0);
    const combinedAudio = new Float32Array(totalLength);

    let offset = 0;
    for (const buffer of allBuffers) {
      combinedAudio.set(buffer, offset);
      offset += buffer.length;
    }

    console.log(`[VAD] Sending speech segment: ${combinedAudio.length} samples, final=${isFinal}`);
    this.stats.segmentsSent++;

    // Clear buffers if final
    if (isFinal) {
      this.speechBuffer = [];
      this.silenceBuffer = [];
      this.speechStartTime = 0;
      this.silenceStartTime = 0;
    } else {
      // Keep last part for continuity
      this.speechBuffer = this.speechBuffer.slice(-5);
    }

    return {
      shouldSend: true,
      audioToSend: combinedAudio
    };
  }

  /**
   * Force end any ongoing speech segment
   */
  forceEndSegment(sampleRate: number = 16000): { shouldSend: boolean; audioToSend?: Float32Array } {
    if (this.isSpeaking || this.speechBuffer.length > 0) {
      console.log('[VAD] Force ending segment');
      return this.endSpeechSegment(sampleRate);
    }
    return { shouldSend: false };
  }

  /**
   * Reset VAD state
   */
  reset(): void {
    this.energyHistory = [];
    this.speechBuffer = [];
    this.silenceBuffer = [];
    this.preSpeechBuffer = [];
    this.isSpeaking = false;
    this.speechStartTime = 0;
    this.silenceStartTime = 0;
    this.lastSpeechTime = 0;
    this.noiseFloor = this.config.noiseFloor;
    this.adaptiveThreshold = this.config.speechThreshold;
    console.log('[VAD] Reset');
  }

  /**
   * Get statistics for debugging
   */
  getStats() {
    return {
      ...this.stats,
      isSpeaking: this.isSpeaking,
      noiseFloor: this.noiseFloor,
      adaptiveThreshold: this.adaptiveThreshold,
      speechBufferSize: this.speechBuffer.length,
      silenceBufferSize: this.silenceBuffer.length,
    };
  }

  /**
   * Update configuration
   */
  updateConfig(config: Partial<VADConfig>): void {
    this.config = { ...this.config, ...config };
    if (config.speechThreshold !== undefined) {
      this.adaptiveThreshold = config.speechThreshold;
    }
  }
}

/**
 * Create a default VAD instance
 */
export function createVAD(config?: Partial<VADConfig>): VoiceActivityDetector {
  return new VoiceActivityDetector(config);
}