/**
 * Voice Liveness Detection Service
 * Implements anti-spoofing measures to detect replay attacks and ensure live voice
 * Uses multiple detection techniques for comprehensive security
 */

export interface LivenessCheckResult {
  isLive: boolean;
  confidence: number;
  checks: {
    ambientNoise: boolean;
    spectralAnalysis: boolean;
    microphoneResponse: boolean;
    challengeResponse?: boolean;
    behavioralPattern: boolean;
  };
  riskScore: number;
  details: string[];
}

export class VoiceLivenessService {
  private static instance: VoiceLivenessService;
  private audioContext: AudioContext | null = null;
  private analyser: AnalyserNode | null = null;
  
  // Detection thresholds
  private readonly NOISE_FLOOR_THRESHOLD = -60; // dB
  private readonly SPECTRAL_VARIANCE_THRESHOLD = 0.15;
  private readonly MICROPHONE_RESPONSE_THRESHOLD = 0.8;
  private readonly MINIMUM_CONFIDENCE = 0.7;

  private constructor() {
    this.initializeAudioContext();
  }

  public static getInstance(): VoiceLivenessService {
    if (!VoiceLivenessService.instance) {
      VoiceLivenessService.instance = new VoiceLivenessService();
    }
    return VoiceLivenessService.instance;
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
   * Perform comprehensive liveness detection on audio sample
   */
  public async performLivenessCheck(
    audioBlob: Blob,
    stream?: MediaStream
  ): Promise<LivenessCheckResult> {
    const checks = {
      ambientNoise: false,
      spectralAnalysis: false,
      microphoneResponse: false,
      challengeResponse: false,
      behavioralPattern: false
    };
    
    const details: string[] = [];
    let totalScore = 0;
    let checksPerformed = 0;

    try {
      // 1. Ambient Noise Detection
      const noiseCheck = await this.checkAmbientNoise(audioBlob);
      checks.ambientNoise = noiseCheck.isValid;
      if (noiseCheck.isValid) {
        totalScore += noiseCheck.score;
        details.push('Natural ambient noise detected');
      } else {
        details.push('Suspicious noise pattern (possible recording)');
      }
      checksPerformed++;

      // 2. Spectral Analysis for Recording Artifacts
      const spectralCheck = await this.analyzeSpectralCharacteristics(audioBlob);
      checks.spectralAnalysis = spectralCheck.isNatural;
      if (spectralCheck.isNatural) {
        totalScore += spectralCheck.score;
        details.push('Natural frequency spectrum');
      } else {
        details.push('Recording artifacts detected in spectrum');
      }
      checksPerformed++;

      // 3. Microphone Response Characteristics
      if (stream) {
        const micCheck = await this.checkMicrophoneResponse(stream);
        checks.microphoneResponse = micCheck.isLive;
        if (micCheck.isLive) {
          totalScore += micCheck.score;
          details.push('Live microphone characteristics confirmed');
        } else {
          details.push('Microphone response suggests playback');
        }
        checksPerformed++;
      }

      // 4. Behavioral Pattern Analysis
      const behaviorCheck = await this.analyzeBehavioralPatterns(audioBlob);
      checks.behavioralPattern = behaviorCheck.isNatural;
      if (behaviorCheck.isNatural) {
        totalScore += behaviorCheck.score;
        details.push('Natural speech patterns detected');
      } else {
        details.push('Unnatural speech patterns (possible synthesis)');
      }
      checksPerformed++;

      // Calculate overall confidence and risk score
      const confidence = checksPerformed > 0 ? totalScore / checksPerformed : 0;
      const riskScore = 1 - confidence;
      const isLive = confidence >= this.MINIMUM_CONFIDENCE;

      return {
        isLive,
        confidence,
        checks,
        riskScore,
        details
      };
    } catch (error) {
      console.error('Liveness detection error:', error);
      return {
        isLive: false,
        confidence: 0,
        checks,
        riskScore: 1,
        details: ['Liveness detection failed']
      };
    }
  }

  /**
   * Check for natural ambient noise patterns
   * Recordings often have consistent noise floors or complete silence
   */
  private async checkAmbientNoise(audioBlob: Blob): Promise<{
    isValid: boolean;
    score: number;
    noiseFloor: number;
    variance: number;
  }> {
    const audioBuffer = await this.blobToAudioBuffer(audioBlob);
    if (!audioBuffer) {
      return { isValid: false, score: 0, noiseFloor: 0, variance: 0 };
    }

    const channelData = audioBuffer.getChannelData(0);
    const sampleRate = audioBuffer.sampleRate;
    
    // Analyze silence periods
    const silenceSamples: number[] = [];
    const windowSize = Math.floor(sampleRate * 0.1); // 100ms windows
    
    for (let i = 0; i < channelData.length; i += windowSize) {
      const window = channelData.slice(i, Math.min(i + windowSize, channelData.length));
      const rms = this.calculateRMS(window);
      const db = 20 * Math.log10(rms);
      
      if (db < this.NOISE_FLOOR_THRESHOLD) {
        silenceSamples.push(db);
      }
    }

    // Check noise floor variance
    const variance = this.calculateVariance(silenceSamples);
    const avgNoiseFloor = silenceSamples.reduce((a, b) => a + b, 0) / silenceSamples.length;
    
    // Natural recordings have variable noise floors
    // Synthetic or played-back audio often has consistent noise
    const isValid = variance > 0.01 && avgNoiseFloor > -80;
    const score = isValid ? Math.min(variance * 10, 1) : 0;

    return {
      isValid,
      score,
      noiseFloor: avgNoiseFloor,
      variance
    };
  }

  /**
   * Analyze spectral characteristics for recording artifacts
   * Detects compression artifacts, band-limiting, and other signs of recording
   */
  private async analyzeSpectralCharacteristics(audioBlob: Blob): Promise<{
    isNatural: boolean;
    score: number;
    artifacts: string[];
  }> {
    const audioBuffer = await this.blobToAudioBuffer(audioBlob);
    if (!audioBuffer) {
      return { isNatural: false, score: 0, artifacts: ['Failed to analyze'] };
    }

    const channelData = audioBuffer.getChannelData(0);
    const artifacts: string[] = [];
    let score = 1.0;

    // 1. Check for frequency band limiting (common in compressed audio)
    const fft = this.performFFT(channelData);
    const highFreqEnergy = this.calculateHighFrequencyEnergy(fft);
    
    if (highFreqEnergy < 0.05) {
      artifacts.push('Band-limited audio detected');
      score -= 0.3;
    }

    // 2. Check for compression artifacts (MP3, AAC, etc.)
    const compressionArtifacts = this.detectCompressionArtifacts(fft);
    if (compressionArtifacts.detected) {
      artifacts.push(`Compression artifacts: ${compressionArtifacts.type}`);
      score -= 0.4;
    }

    // 3. Check for spectral consistency (recordings often have consistent spectra)
    const spectralVariance = this.calculateSpectralVariance(channelData, audioBuffer.sampleRate);
    if (spectralVariance < this.SPECTRAL_VARIANCE_THRESHOLD) {
      artifacts.push('Unnaturally consistent spectrum');
      score -= 0.3;
    }

    return {
      isNatural: score > 0.5,
      score: Math.max(0, score),
      artifacts
    };
  }

  /**
   * Check microphone response characteristics
   * Live microphones have specific response patterns different from speakers
   */
  private async checkMicrophoneResponse(stream: MediaStream): Promise<{
    isLive: boolean;
    score: number;
    characteristics: string[];
  }> {
    if (!this.audioContext) {
      return { isLive: false, score: 0, characteristics: ['No audio context'] };
    }

    const characteristics: string[] = [];
    let score = 1.0;

    try {
      const source = this.audioContext.createMediaStreamSource(stream);
      const analyser = this.audioContext.createAnalyser();
      analyser.fftSize = 2048;
      source.connect(analyser);

      // 1. Check for microphone proximity effect
      const proximityEffect = await this.detectProximityEffect(analyser);
      if (proximityEffect) {
        characteristics.push('Proximity effect detected');
        score += 0.2;
      }

      // 2. Check for natural transients
      const transients = await this.detectNaturalTransients(analyser);
      if (transients) {
        characteristics.push('Natural transients present');
      } else {
        characteristics.push('Suspicious transient response');
        score -= 0.3;
      }

      // 3. Check for feedback potential (only real mics can feedback)
      const feedbackPotential = this.checkFeedbackPotential(analyser);
      if (feedbackPotential) {
        characteristics.push('Microphone feedback characteristics');
        score += 0.1;
      }

      source.disconnect();
    } catch (error) {
      console.error('Microphone response check failed:', error);
      score = 0;
    }

    return {
      isLive: score >= this.MICROPHONE_RESPONSE_THRESHOLD,
      score: Math.min(1, Math.max(0, score)),
      characteristics
    };
  }

  /**
   * Analyze behavioral patterns in speech
   * Detects unnatural patterns that might indicate synthesis or manipulation
   */
  private async analyzeBehavioralPatterns(audioBlob: Blob): Promise<{
    isNatural: boolean;
    score: number;
    patterns: string[];
  }> {
    const audioBuffer = await this.blobToAudioBuffer(audioBlob);
    if (!audioBuffer) {
      return { isNatural: false, score: 0, patterns: ['Analysis failed'] };
    }

    const patterns: string[] = [];
    let score = 1.0;

    // 1. Check for natural pauses and breathing
    const breathingPattern = this.detectBreathingPatterns(audioBuffer);
    if (breathingPattern.natural) {
      patterns.push('Natural breathing detected');
    } else {
      patterns.push('No natural breathing patterns');
      score -= 0.3;
    }

    // 2. Check for micro-variations in pitch (humans can't maintain perfect pitch)
    const pitchVariation = this.analyzePitchVariation(audioBuffer);
    if (pitchVariation.natural) {
      patterns.push('Natural pitch variations');
    } else {
      patterns.push('Unnaturally consistent pitch');
      score -= 0.4;
    }

    // 3. Check for natural speech rhythm
    const rhythmAnalysis = this.analyzeSpeechRhythm(audioBuffer);
    if (rhythmAnalysis.natural) {
      patterns.push('Natural speech rhythm');
    } else {
      patterns.push('Mechanical speech rhythm');
      score -= 0.3;
    }

    return {
      isNatural: score > 0.5,
      score: Math.max(0, score),
      patterns
    };
  }

  /**
   * Generate a random challenge for enhanced liveness detection
   * User must speak specific words or numbers
   */
  public generateRandomChallenge(): {
    type: 'numeric' | 'word' | 'phrase';
    challenge: string;
    expectedDuration: number;
  } {
    const challengeTypes = ['numeric', 'word', 'phrase'] as const;
    const type = challengeTypes[Math.floor(Math.random() * challengeTypes.length)];
    
    let challenge: string;
    let expectedDuration: number;

    switch (type) {
      case 'numeric':
        // Generate random 6-digit number
        challenge = Math.floor(100000 + Math.random() * 900000).toString();
        expectedDuration = 3000; // 3 seconds
        break;
      
      case 'word':
        // Random words that are hard to pre-record
        const words = [
          'authentication', 'biometric', 'cannabis', 'verification',
          'security', 'identity', 'enrollment', 'recognition'
        ];
        challenge = words[Math.floor(Math.random() * words.length)];
        expectedDuration = 2000; // 2 seconds
        break;
      
      case 'phrase':
        // Random phrases
        const phrases = [
          'I am authenticating my identity',
          'This is my live voice',
          'Verify my biometric signature',
          'I consent to voice authentication'
        ];
        challenge = phrases[Math.floor(Math.random() * phrases.length)];
        expectedDuration = 4000; // 4 seconds
        break;
    }

    return { type, challenge, expectedDuration };
  }

  /**
   * Verify if the spoken audio matches the challenge
   */
  public async verifyChallengeResponse(
    audioBlob: Blob,
    expectedChallenge: string,
    type: 'numeric' | 'word' | 'phrase'
  ): Promise<{
    matches: boolean;
    confidence: number;
  }> {
    // In production, this would use speech-to-text API
    // For now, we'll implement a placeholder that checks audio characteristics
    
    const audioBuffer = await this.blobToAudioBuffer(audioBlob);
    if (!audioBuffer) {
      return { matches: false, confidence: 0 };
    }

    // Check if duration is reasonable for the challenge
    const duration = audioBuffer.duration * 1000; // Convert to ms
    const expectedDuration = this.getExpectedDuration(expectedChallenge, type);
    const durationMatch = Math.abs(duration - expectedDuration) < expectedDuration * 0.5;

    // Check if audio has speech characteristics
    const hasSpeech = await this.detectSpeechPresence(audioBuffer);

    // In production, add actual speech recognition here
    const matches = durationMatch && hasSpeech;
    const confidence = matches ? 0.8 : 0.2;

    return { matches, confidence };
  }

  // Helper methods

  private async blobToAudioBuffer(blob: Blob): Promise<AudioBuffer | null> {
    try {
      if (!this.audioContext) {
        await this.initializeAudioContext();
      }
      if (!this.audioContext) return null;

      const arrayBuffer = await blob.arrayBuffer();
      return await this.audioContext.decodeAudioData(arrayBuffer);
    } catch (error) {
      console.error('Failed to decode audio:', error);
      return null;
    }
  }

  private calculateRMS(samples: Float32Array): number {
    let sum = 0;
    for (let i = 0; i < samples.length; i++) {
      sum += samples[i] * samples[i];
    }
    return Math.sqrt(sum / samples.length);
  }

  private calculateVariance(values: number[]): number {
    if (values.length === 0) return 0;
    const mean = values.reduce((a, b) => a + b, 0) / values.length;
    const squaredDiffs = values.map(value => Math.pow(value - mean, 2));
    return squaredDiffs.reduce((a, b) => a + b, 0) / values.length;
  }

  private performFFT(samples: Float32Array): Float32Array {
    // Simplified FFT for demonstration
    // In production, use a proper FFT library
    const fftSize = 2048;
    const fft = new Float32Array(fftSize);
    
    for (let k = 0; k < fftSize / 2; k++) {
      let real = 0;
      let imag = 0;
      
      for (let n = 0; n < Math.min(samples.length, fftSize); n++) {
        const angle = -2 * Math.PI * k * n / fftSize;
        real += samples[n] * Math.cos(angle);
        imag += samples[n] * Math.sin(angle);
      }
      
      fft[k] = Math.sqrt(real * real + imag * imag);
    }
    
    return fft;
  }

  private calculateHighFrequencyEnergy(fft: Float32Array): number {
    const totalEnergy = fft.reduce((sum, val) => sum + val * val, 0);
    const highFreqStart = Math.floor(fft.length * 0.7);
    let highFreqEnergy = 0;
    
    for (let i = highFreqStart; i < fft.length; i++) {
      highFreqEnergy += fft[i] * fft[i];
    }
    
    return totalEnergy > 0 ? highFreqEnergy / totalEnergy : 0;
  }

  private detectCompressionArtifacts(fft: Float32Array): {
    detected: boolean;
    type: string;
  } {
    // Look for telltale signs of compression
    // MP3 creates specific artifacts at certain frequencies
    
    // Check for brick-wall filtering (common in MP3)
    const cutoffFreq = this.findCutoffFrequency(fft);
    if (cutoffFreq > 0 && cutoffFreq < fft.length * 0.9) {
      return { detected: true, type: 'MP3-like compression' };
    }
    
    return { detected: false, type: 'none' };
  }

  private findCutoffFrequency(fft: Float32Array): number {
    // Find sudden drop in high frequencies
    for (let i = fft.length - 2; i > fft.length / 2; i--) {
      if (fft[i] > fft[i + 1] * 10) {
        return i;
      }
    }
    return -1;
  }

  private calculateSpectralVariance(samples: Float32Array, sampleRate: number): number {
    // Calculate variance across multiple FFT windows
    const windowSize = 2048;
    const hopSize = 1024;
    const spectra: Float32Array[] = [];
    
    for (let i = 0; i + windowSize < samples.length; i += hopSize) {
      const window = samples.slice(i, i + windowSize);
      spectra.push(this.performFFT(window));
    }
    
    if (spectra.length < 2) return 0;
    
    // Calculate variance across time for each frequency bin
    let totalVariance = 0;
    for (let bin = 0; bin < windowSize / 2; bin++) {
      const binValues = spectra.map(spectrum => spectrum[bin]);
      totalVariance += this.calculateVariance(binValues);
    }
    
    return totalVariance / (windowSize / 2);
  }

  private async detectProximityEffect(analyser: AnalyserNode): Promise<boolean> {
    // Proximity effect causes low-frequency boost when close to mic
    const dataArray = new Float32Array(analyser.frequencyBinCount);
    analyser.getFloatFrequencyData(dataArray);
    
    // Check for enhanced low frequencies
    const lowFreqEnergy = dataArray.slice(0, 10).reduce((sum, val) => sum + Math.abs(val), 0);
    const midFreqEnergy = dataArray.slice(50, 60).reduce((sum, val) => sum + Math.abs(val), 0);
    
    return lowFreqEnergy > midFreqEnergy * 1.5;
  }

  private async detectNaturalTransients(analyser: AnalyserNode): Promise<boolean> {
    // Natural speech has specific transient characteristics
    const samples = 10;
    const transients: number[] = [];
    
    for (let i = 0; i < samples; i++) {
      const dataArray = new Float32Array(analyser.fftSize);
      analyser.getFloatTimeDomainData(dataArray);
      
      // Detect sudden changes
      for (let j = 1; j < dataArray.length; j++) {
        const diff = Math.abs(dataArray[j] - dataArray[j - 1]);
        if (diff > 0.1) {
          transients.push(diff);
        }
      }
      
      await new Promise(resolve => setTimeout(resolve, 10));
    }
    
    // Natural speech has varied transients
    const variance = this.calculateVariance(transients);
    return variance > 0.01;
  }

  private checkFeedbackPotential(analyser: AnalyserNode): boolean {
    // Real microphones can potentially feedback
    // This is a simplified check
    const dataArray = new Float32Array(analyser.frequencyBinCount);
    analyser.getFloatFrequencyData(dataArray);
    
    // Look for resonant peaks that could indicate feedback potential
    let peaks = 0;
    for (let i = 1; i < dataArray.length - 1; i++) {
      if (dataArray[i] > dataArray[i - 1] && dataArray[i] > dataArray[i + 1]) {
        if (dataArray[i] > -30) { // Strong peak
          peaks++;
        }
      }
    }
    
    return peaks > 3; // Multiple resonant frequencies
  }

  private detectBreathingPatterns(audioBuffer: AudioBuffer): {
    natural: boolean;
    breathCount: number;
  } {
    const channelData = audioBuffer.getChannelData(0);
    const sampleRate = audioBuffer.sampleRate;
    
    // Look for characteristic breathing sounds (low amplitude, specific frequency)
    let breathCount = 0;
    const windowSize = Math.floor(sampleRate * 0.5); // 500ms windows
    
    for (let i = 0; i < channelData.length - windowSize; i += windowSize / 2) {
      const window = channelData.slice(i, i + windowSize);
      const rms = this.calculateRMS(window);
      
      // Breathing is typically quiet but not silent
      if (rms > 0.001 && rms < 0.01) {
        const fft = this.performFFT(window);
        // Breathing has specific frequency characteristics (100-500 Hz)
        const breathFreqEnergy = fft.slice(2, 10).reduce((sum, val) => sum + val, 0);
        const totalEnergy = fft.reduce((sum, val) => sum + val, 0);
        
        if (totalEnergy > 0 && breathFreqEnergy / totalEnergy > 0.6) {
          breathCount++;
        }
      }
    }
    
    // Expect at least one breath in a 5-second recording
    const expectedBreaths = Math.floor(audioBuffer.duration / 5);
    return {
      natural: breathCount >= expectedBreaths,
      breathCount
    };
  }

  private analyzePitchVariation(audioBuffer: AudioBuffer): {
    natural: boolean;
    variationCoefficient: number;
  } {
    const channelData = audioBuffer.getChannelData(0);
    const sampleRate = audioBuffer.sampleRate;
    
    // Extract pitch using autocorrelation (simplified)
    const pitchValues: number[] = [];
    const windowSize = Math.floor(sampleRate * 0.02); // 20ms windows
    
    for (let i = 0; i < channelData.length - windowSize * 2; i += windowSize) {
      const window = channelData.slice(i, i + windowSize * 2);
      const pitch = this.estimatePitch(window, sampleRate);
      if (pitch > 0) {
        pitchValues.push(pitch);
      }
    }
    
    if (pitchValues.length < 2) {
      return { natural: false, variationCoefficient: 0 };
    }
    
    // Calculate coefficient of variation
    const mean = pitchValues.reduce((a, b) => a + b, 0) / pitchValues.length;
    const variance = this.calculateVariance(pitchValues);
    const coefficientOfVariation = Math.sqrt(variance) / mean;
    
    // Natural speech has pitch variation between 0.05 and 0.3
    const natural = coefficientOfVariation > 0.05 && coefficientOfVariation < 0.3;
    
    return {
      natural,
      variationCoefficient: coefficientOfVariation
    };
  }

  private estimatePitch(window: Float32Array, sampleRate: number): number {
    // Simplified pitch detection using autocorrelation
    const minPeriod = Math.floor(sampleRate / 500); // 500 Hz max
    const maxPeriod = Math.floor(sampleRate / 50);  // 50 Hz min
    
    let maxCorrelation = 0;
    let bestPeriod = 0;
    
    for (let period = minPeriod; period < Math.min(maxPeriod, window.length / 2); period++) {
      let correlation = 0;
      for (let i = 0; i < window.length - period; i++) {
        correlation += window[i] * window[i + period];
      }
      
      if (correlation > maxCorrelation) {
        maxCorrelation = correlation;
        bestPeriod = period;
      }
    }
    
    return bestPeriod > 0 ? sampleRate / bestPeriod : 0;
  }

  private analyzeSpeechRhythm(audioBuffer: AudioBuffer): {
    natural: boolean;
    rhythmScore: number;
  } {
    const channelData = audioBuffer.getChannelData(0);
    const sampleRate = audioBuffer.sampleRate;
    
    // Detect syllable boundaries
    const energy: number[] = [];
    const windowSize = Math.floor(sampleRate * 0.01); // 10ms windows
    
    for (let i = 0; i < channelData.length - windowSize; i += windowSize) {
      const window = channelData.slice(i, i + windowSize);
      energy.push(this.calculateRMS(window));
    }
    
    // Find peaks (syllables)
    const peaks: number[] = [];
    for (let i = 1; i < energy.length - 1; i++) {
      if (energy[i] > energy[i - 1] && energy[i] > energy[i + 1] && energy[i] > 0.01) {
        peaks.push(i * windowSize / sampleRate);
      }
    }
    
    if (peaks.length < 2) {
      return { natural: false, rhythmScore: 0 };
    }
    
    // Calculate inter-syllable intervals
    const intervals: number[] = [];
    for (let i = 1; i < peaks.length; i++) {
      intervals.push(peaks[i] - peaks[i - 1]);
    }
    
    // Natural speech has variable rhythm
    const rhythmVariance = this.calculateVariance(intervals);
    const natural = rhythmVariance > 0.01 && rhythmVariance < 0.5;
    
    return {
      natural,
      rhythmScore: natural ? 1 - Math.abs(rhythmVariance - 0.1) : 0
    };
  }

  private async detectSpeechPresence(audioBuffer: AudioBuffer): Promise<boolean> {
    const channelData = audioBuffer.getChannelData(0);
    
    // Check for speech-like energy patterns
    const rms = this.calculateRMS(channelData);
    const zeroCrossingRate = this.calculateZeroCrossingRate(channelData);
    
    // Speech typically has RMS > 0.01 and ZCR between 0.1 and 0.5
    return rms > 0.01 && zeroCrossingRate > 0.1 && zeroCrossingRate < 0.5;
  }

  private calculateZeroCrossingRate(samples: Float32Array): number {
    let crossings = 0;
    for (let i = 1; i < samples.length; i++) {
      if ((samples[i] >= 0 && samples[i - 1] < 0) || 
          (samples[i] < 0 && samples[i - 1] >= 0)) {
        crossings++;
      }
    }
    return crossings / samples.length;
  }

  private getExpectedDuration(challenge: string, type: 'numeric' | 'word' | 'phrase'): number {
    // Estimate based on challenge length and type
    const wordsPerMinute = 150;
    const words = challenge.split(' ').length;
    const baseTime = (words / wordsPerMinute) * 60 * 1000; // Convert to ms
    
    // Add padding based on type
    const padding = type === 'phrase' ? 1000 : 500;
    
    return baseTime + padding;
  }
}

// Export singleton instance
export const voiceLivenessService = VoiceLivenessService.getInstance();