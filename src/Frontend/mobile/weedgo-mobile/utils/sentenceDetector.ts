/**
 * Sentence Completion Detection
 * Automatically detects when a sentence is complete to trigger auto-send
 */

export interface SentenceDetectorConfig {
  // Punctuation that ends sentences
  sentenceEnders: string[];

  // Minimum length for a valid sentence
  minSentenceLength: number;

  // Time to wait after sentence end before auto-stopping (ms)
  autoStopDelay: number;

  // Whether to detect questions as complete sentences
  detectQuestions: boolean;

  // Whether to require capitalization at start
  requireCapitalization: boolean;

  // Common incomplete patterns to ignore
  incompletePatterns: RegExp[];
}

export interface SentenceResult {
  isComplete: boolean;
  sentenceType: 'statement' | 'question' | 'exclamation' | 'incomplete';
  confidence: number;
  shouldAutoSend: boolean;
  reason?: string;
}

export class SentenceDetector {
  private config: SentenceDetectorConfig;
  private lastTranscript: string = '';
  private sentenceEndTime: number = 0;
  private pendingAutoStop: NodeJS.Timeout | null = null;

  constructor(config?: Partial<SentenceDetectorConfig>) {
    this.config = {
      sentenceEnders: ['.', '?', '!', '。', '？', '！'], // Include Chinese/Japanese
      minSentenceLength: 10,
      autoStopDelay: 1500, // 1.5 seconds after sentence ends
      detectQuestions: true,
      requireCapitalization: false, // ASR often doesn't capitalize
      incompletePatterns: [
        /\b(um|uh|er|ah|oh|hmm)\s*$/i,
        /\b(and|but|or|so|then)\s*$/i,
        /\b(the|a|an)\s*$/i,
        /\b(i|you|we|they|he|she|it)\s*$/i,
        /\b(is|are|was|were|am)\s*$/i,
        /\b(like|just|really|very)\s*$/i,
      ],
      ...config
    };
  }

  /**
   * Analyze transcript for sentence completion
   */
  analyzeTranscript(
    transcript: string,
    isPartial: boolean = false
  ): SentenceResult {
    if (!transcript || transcript.trim().length === 0) {
      return {
        isComplete: false,
        sentenceType: 'incomplete',
        confidence: 0,
        shouldAutoSend: false,
        reason: 'Empty transcript'
      };
    }

    const trimmed = transcript.trim();

    // Check minimum length
    if (trimmed.length < this.config.minSentenceLength) {
      return {
        isComplete: false,
        sentenceType: 'incomplete',
        confidence: 0.2,
        shouldAutoSend: false,
        reason: 'Too short'
      };
    }

    // Check for sentence-ending punctuation
    const lastChar = trimmed[trimmed.length - 1];
    const hasEndPunctuation = this.config.sentenceEnders.includes(lastChar);

    // Determine sentence type
    let sentenceType: 'statement' | 'question' | 'exclamation' | 'incomplete' = 'incomplete';
    if (lastChar === '?' || lastChar === '？') {
      sentenceType = 'question';
    } else if (lastChar === '!' || lastChar === '！') {
      sentenceType = 'exclamation';
    } else if (lastChar === '.' || lastChar === '。') {
      sentenceType = 'statement';
    }

    // Check for incomplete patterns at the end
    const endsWithIncomplete = this.config.incompletePatterns.some(
      pattern => pattern.test(trimmed)
    );

    // Calculate confidence
    let confidence = 0;

    if (hasEndPunctuation) {
      confidence += 0.5;
    }

    // Check for question words without punctuation
    if (!hasEndPunctuation && this.detectsQuestion(trimmed)) {
      sentenceType = 'question';
      confidence += 0.3;
    }

    // Check for complete thought patterns
    if (this.isCompleteSentenceStructure(trimmed)) {
      confidence += 0.3;
    }

    if (endsWithIncomplete) {
      confidence -= 0.4;
    }

    // Length factor
    if (trimmed.length > 30) {
      confidence += 0.1;
    }
    if (trimmed.length > 50) {
      confidence += 0.1;
    }

    // Clamp confidence
    confidence = Math.max(0, Math.min(1, confidence));

    // Determine if complete
    const isComplete = hasEndPunctuation ||
                      (confidence > 0.6 && !isPartial && !endsWithIncomplete);

    // Determine if should auto-send
    const shouldAutoSend = isComplete &&
                          confidence > 0.7 &&
                          (sentenceType !== 'incomplete');

    return {
      isComplete,
      sentenceType,
      confidence,
      shouldAutoSend,
      reason: this.getCompletionReason(isComplete, hasEndPunctuation, endsWithIncomplete)
    };
  }

  /**
   * Check if transcript contains question patterns
   */
  private detectsQuestion(text: string): boolean {
    const questionPatterns = [
      /^(what|when|where|who|why|how|which|whose|whom)\b/i,
      /^(is|are|was|were|am|do|does|did|can|could|will|would|should|shall|may|might)\s+\w+/i,
      /\b(right|okay|correct|yes|no)\s*$/i, // Tag questions
    ];

    return questionPatterns.some(pattern => pattern.test(text));
  }

  /**
   * Check for complete sentence structure
   */
  private isCompleteSentenceStructure(text: string): boolean {
    // Simple heuristic: has subject and verb
    const words = text.toLowerCase().split(/\s+/);

    // Common subjects
    const subjects = ['i', 'you', 'we', 'they', 'he', 'she', 'it', 'this', 'that'];
    const hasSubject = subjects.some(subj => words.includes(subj));

    // Common verbs
    const verbs = ['is', 'are', 'was', 'were', 'am', 'have', 'has', 'had',
                   'do', 'does', 'did', 'will', 'would', 'can', 'could',
                   'want', 'need', 'like', 'think', 'know', 'see', 'get'];
    const hasVerb = verbs.some(verb => words.includes(verb));

    // Commands are complete without subject
    const isCommand = /^(please|show|give|tell|find|search|look|get|make|send)\b/i.test(text);

    return isCommand || (hasSubject && hasVerb);
  }

  /**
   * Get reason for completion status
   */
  private getCompletionReason(
    isComplete: boolean,
    hasEndPunctuation: boolean,
    endsWithIncomplete: boolean
  ): string {
    if (isComplete && hasEndPunctuation) {
      return 'Has sentence-ending punctuation';
    }
    if (isComplete && !hasEndPunctuation) {
      return 'Appears to be a complete thought';
    }
    if (!isComplete && endsWithIncomplete) {
      return 'Ends with incomplete phrase';
    }
    if (!isComplete) {
      return 'Sentence appears incomplete';
    }
    return 'Unknown';
  }

  /**
   * Track transcript changes and manage auto-stop
   */
  trackTranscript(
    transcript: string,
    isPartial: boolean,
    onAutoStop: () => void
  ): SentenceResult {
    const result = this.analyzeTranscript(transcript, isPartial);

    // Clear any pending auto-stop if transcript changed significantly
    if (transcript !== this.lastTranscript && this.pendingAutoStop) {
      clearTimeout(this.pendingAutoStop);
      this.pendingAutoStop = null;
    }

    this.lastTranscript = transcript;

    // Schedule auto-stop if sentence is complete
    if (result.shouldAutoSend && !isPartial && !this.pendingAutoStop) {
      console.log(`[SentenceDetector] Scheduling auto-stop in ${this.config.autoStopDelay}ms`);

      this.pendingAutoStop = setTimeout(() => {
        console.log('[SentenceDetector] Auto-stopping due to sentence completion');
        onAutoStop();
        this.pendingAutoStop = null;
      }, this.config.autoStopDelay);

      this.sentenceEndTime = Date.now();
    }

    return result;
  }

  /**
   * Cancel any pending auto-stop
   */
  cancelAutoStop(): void {
    if (this.pendingAutoStop) {
      clearTimeout(this.pendingAutoStop);
      this.pendingAutoStop = null;
      console.log('[SentenceDetector] Cancelled auto-stop');
    }
  }

  /**
   * Reset detector state
   */
  reset(): void {
    this.lastTranscript = '';
    this.sentenceEndTime = 0;
    this.cancelAutoStop();
  }

  /**
   * Update configuration
   */
  updateConfig(config: Partial<SentenceDetectorConfig>): void {
    this.config = { ...this.config, ...config };
  }
}

/**
 * Create sentence detector instance
 */
export function createSentenceDetector(
  config?: Partial<SentenceDetectorConfig>
): SentenceDetector {
  return new SentenceDetector(config);
}

/**
 * React hook for sentence detection
 */
export function useSentenceDetection(
  onAutoStop: () => void,
  config?: Partial<SentenceDetectorConfig>
) {
  const detectorRef = React.useRef<SentenceDetector | null>(null);

  React.useEffect(() => {
    detectorRef.current = createSentenceDetector(config);

    return () => {
      detectorRef.current?.reset();
    };
  }, []);

  const analyzeTranscript = React.useCallback(
    (transcript: string, isPartial: boolean = false) => {
      if (!detectorRef.current) {
        detectorRef.current = createSentenceDetector(config);
      }

      return detectorRef.current.trackTranscript(transcript, isPartial, onAutoStop);
    },
    [onAutoStop, config]
  );

  const cancelAutoStop = React.useCallback(() => {
    detectorRef.current?.cancelAutoStop();
  }, []);

  const reset = React.useCallback(() => {
    detectorRef.current?.reset();
  }, []);

  return {
    analyzeTranscript,
    cancelAutoStop,
    reset
  };
}

// Add React import for the hook
import React from 'react';