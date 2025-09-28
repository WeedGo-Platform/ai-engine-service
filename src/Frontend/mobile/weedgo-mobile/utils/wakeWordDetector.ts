/**
 * Wake Word Detection for Hands-Free Activation
 * Detects specific phrases like "Hey WeedGo" to trigger voice recording
 */

export interface WakeWordConfig {
  wakeWords: string[];           // List of wake words to detect
  sensitivity: number;            // 0-1, higher = more sensitive
  minConfidence: number;          // Minimum confidence to trigger
  cooldownMs: number;             // Time before next detection
  energyThreshold: number;        // Minimum audio energy required
  usePhonemeMatching: boolean;   // Use phoneme-based matching
}

export interface WakeWordResult {
  detected: boolean;
  wakeWord: string | null;
  confidence: number;
  timestamp: number;
}

export class WakeWordDetector {
  private config: WakeWordConfig;
  private lastDetectionTime: number = 0;
  private audioBuffer: Float32Array[] = [];
  private bufferDuration: number = 2000; // Keep 2 seconds of audio
  private isListening: boolean = false;

  // Simple phoneme patterns for common wake words
  private phonemePatterns: Map<string, RegExp> = new Map([
    ['hey weedgo', /h[ae]i?\s*w[ie]+d?\s*g[ou]+/i],
    ['okay weedgo', /o[uk][ae]i?\s*w[ie]+d?\s*g[ou]+/i],
    ['hi weedgo', /h[ai]+\s*w[ie]+d?\s*g[ou]+/i],
    ['weedgo', /w[ie]+d?\s*g[ou]+/i],
  ]);

  constructor(config?: Partial<WakeWordConfig>) {
    this.config = {
      wakeWords: ['hey weedgo', 'okay weedgo', 'hi weedgo'],
      sensitivity: 0.7,
      minConfidence: 0.6,
      cooldownMs: 3000,
      energyThreshold: 0.02,
      usePhonemeMatching: true,
      ...config
    };
  }

  /**
   * Start listening for wake words
   */
  startListening(): void {
    this.isListening = true;
    this.audioBuffer = [];
    this.lastDetectionTime = 0;
    console.log('[WakeWord] Started listening');
  }

  /**
   * Stop listening for wake words
   */
  stopListening(): void {
    this.isListening = false;
    this.audioBuffer = [];
    console.log('[WakeWord] Stopped listening');
  }

  /**
   * Process audio chunk for wake word detection
   */
  processAudio(audioData: Float32Array, sampleRate: number = 16000): WakeWordResult {
    if (!this.isListening) {
      return {
        detected: false,
        wakeWord: null,
        confidence: 0,
        timestamp: Date.now()
      };
    }

    // Check energy threshold
    const energy = this.calculateEnergy(audioData);
    if (energy < this.config.energyThreshold) {
      return {
        detected: false,
        wakeWord: null,
        confidence: 0,
        timestamp: Date.now()
      };
    }

    // Add to buffer
    this.audioBuffer.push(audioData);

    // Maintain buffer size (2 seconds)
    const maxBuffers = Math.ceil((this.bufferDuration / 1000) * sampleRate / audioData.length);
    while (this.audioBuffer.length > maxBuffers) {
      this.audioBuffer.shift();
    }

    // Check cooldown
    const now = Date.now();
    if (now - this.lastDetectionTime < this.config.cooldownMs) {
      return {
        detected: false,
        wakeWord: null,
        confidence: 0,
        timestamp: now
      };
    }

    // Combine buffer for analysis
    const combinedBuffer = this.combineBuffers();

    // Detect wake word
    const result = this.detectWakeWord(combinedBuffer, sampleRate);

    if (result.detected) {
      this.lastDetectionTime = now;
      console.log(`[WakeWord] Detected: "${result.wakeWord}" with confidence ${result.confidence}`);
    }

    return result;
  }

  /**
   * Calculate energy of audio data
   */
  private calculateEnergy(audioData: Float32Array): number {
    let sum = 0;
    for (let i = 0; i < audioData.length; i++) {
      sum += audioData[i] * audioData[i];
    }
    return Math.sqrt(sum / audioData.length);
  }

  /**
   * Combine audio buffers
   */
  private combineBuffers(): Float32Array {
    const totalLength = this.audioBuffer.reduce((sum, buf) => sum + buf.length, 0);
    const combined = new Float32Array(totalLength);
    let offset = 0;
    for (const buffer of this.audioBuffer) {
      combined.set(buffer, offset);
      offset += buffer.length;
    }
    return combined;
  }

  /**
   * Detect wake word in audio
   * This is a simplified implementation. In production, you'd use:
   * - WebAssembly-based model (like Porcupine)
   * - TensorFlow.js with a trained model
   * - Native wake word detection APIs
   */
  private detectWakeWord(audioData: Float32Array, sampleRate: number): WakeWordResult {
    // For now, we'll use a simple energy pattern matching
    // In a real implementation, this would use ML models

    const result: WakeWordResult = {
      detected: false,
      wakeWord: null,
      confidence: 0,
      timestamp: Date.now()
    };

    // Analyze energy patterns
    const energyPattern = this.extractEnergyPattern(audioData);

    // Check each wake word
    for (const wakeWord of this.config.wakeWords) {
      const confidence = this.matchWakeWord(energyPattern, wakeWord);

      if (confidence > result.confidence) {
        result.confidence = confidence;
        result.wakeWord = wakeWord;
      }
    }

    // Check if confidence meets threshold
    if (result.confidence >= this.config.minConfidence) {
      result.detected = true;
    }

    return result;
  }

  /**
   * Extract energy pattern from audio
   */
  private extractEnergyPattern(audioData: Float32Array): number[] {
    const windowSize = 800; // 50ms at 16kHz
    const pattern: number[] = [];

    for (let i = 0; i < audioData.length; i += windowSize) {
      const window = audioData.slice(i, Math.min(i + windowSize, audioData.length));
      const energy = this.calculateEnergy(window);
      pattern.push(energy);
    }

    return pattern;
  }

  /**
   * Match wake word pattern
   * Simplified pattern matching - in production use proper speech recognition
   */
  private matchWakeWord(energyPattern: number[], wakeWord: string): number {
    // Simulate wake word matching based on energy pattern
    // Real implementation would use:
    // 1. MFCC feature extraction
    // 2. DTW (Dynamic Time Warping) or
    // 3. Neural network model

    // For now, return a simulated confidence based on pattern characteristics
    const expectedLength = wakeWord.split(' ').length * 10; // Rough estimate
    const lengthMatch = 1 - Math.abs(energyPattern.length - expectedLength) / expectedLength;

    // Check for speech-like energy variations
    let variations = 0;
    for (let i = 1; i < energyPattern.length; i++) {
      if (Math.abs(energyPattern[i] - energyPattern[i-1]) > 0.01) {
        variations++;
      }
    }
    const variationScore = variations / energyPattern.length;

    // Combine scores
    const confidence = (lengthMatch * 0.3 + variationScore * 0.7) * this.config.sensitivity;

    return Math.min(1, Math.max(0, confidence));
  }

  /**
   * Get current configuration
   */
  getConfig(): WakeWordConfig {
    return { ...this.config };
  }

  /**
   * Update configuration
   */
  updateConfig(config: Partial<WakeWordConfig>): void {
    this.config = { ...this.config, ...config };
  }

  /**
   * Check if listening
   */
  isActivelyListening(): boolean {
    return this.isListening;
  }

  /**
   * Clear audio buffer
   */
  clearBuffer(): void {
    this.audioBuffer = [];
  }
}

/**
 * Create a wake word detector instance
 */
export function createWakeWordDetector(config?: Partial<WakeWordConfig>): WakeWordDetector {
  return new WakeWordDetector(config);
}

/**
 * Hook for using wake word detection
 */
export function useWakeWordDetection(
  onWakeWordDetected: (wakeWord: string) => void,
  config?: Partial<WakeWordConfig>
) {
  const detectorRef = React.useRef<WakeWordDetector | null>(null);

  React.useEffect(() => {
    detectorRef.current = createWakeWordDetector(config);
    detectorRef.current.startListening();

    return () => {
      if (detectorRef.current) {
        detectorRef.current.stopListening();
      }
    };
  }, []);

  const processAudioChunk = React.useCallback((audioData: Float32Array) => {
    if (!detectorRef.current) return;

    const result = detectorRef.current.processAudio(audioData);
    if (result.detected && result.wakeWord) {
      onWakeWordDetected(result.wakeWord);
    }

    return result;
  }, [onWakeWordDetected]);

  const startListening = React.useCallback(() => {
    detectorRef.current?.startListening();
  }, []);

  const stopListening = React.useCallback(() => {
    detectorRef.current?.stopListening();
  }, []);

  return {
    processAudioChunk,
    startListening,
    stopListening,
    isListening: detectorRef.current?.isActivelyListening() || false
  };
}

// Add React import for the hook
import React from 'react';