/**
 * Utility to clean up repetitive transcript text
 */

/**
 * Remove duplicate sentences from transcript
 * @param transcript - The raw transcript text
 * @returns Cleaned transcript with duplicates removed
 */
export function cleanTranscript(transcript: string): string {
  if (!transcript) return '';

  // Split into sentences (basic splitting on . ! ?)
  const sentences = transcript
    .split(/([.!?]+)/)
    .filter(s => s.trim())
    .reduce((acc: string[], curr, idx, arr) => {
      // Combine sentence with its punctuation
      if (idx % 2 === 0 && arr[idx + 1]) {
        acc.push(curr.trim() + arr[idx + 1]);
      } else if (idx % 2 === 0) {
        acc.push(curr.trim());
      }
      return acc;
    }, []);

  // Remove exact duplicates while preserving order
  const seen = new Set<string>();
  const unique: string[] = [];

  for (const sentence of sentences) {
    const normalized = sentence.toLowerCase().trim();
    if (!seen.has(normalized) && normalized.length > 0) {
      seen.add(normalized);
      unique.push(sentence);
    }
  }

  // Join back together
  return unique.join(' ').trim();
}

/**
 * Remove repeated phrases within a transcript
 * @param transcript - The raw transcript text
 * @returns Cleaned transcript
 */
export function removeRepeatedPhrases(transcript: string): string {
  if (!transcript) return '';

  // Common patterns like "Hello, hello." repeated multiple times
  let cleaned = transcript;

  // Pattern 1: Remove exact consecutive duplicates
  // e.g., "Hello. Hello." -> "Hello."
  cleaned = cleaned.replace(/(\b\w+[.,!?]?\s+)\1+/gi, '$1');

  // Pattern 2: Remove repeated short phrases
  // e.g., "Testing, testing. Testing, testing." -> "Testing, testing."
  const phrases = cleaned.match(/[^.!?]+[.!?]*/g) || [];
  const uniquePhrases: string[] = [];
  const recentPhrases: string[] = [];

  for (const phrase of phrases) {
    const normalized = phrase.toLowerCase().trim();

    // Keep track of recent phrases (last 3)
    if (!recentPhrases.includes(normalized)) {
      uniquePhrases.push(phrase.trim());
      recentPhrases.push(normalized);
      if (recentPhrases.length > 3) {
        recentPhrases.shift();
      }
    }
  }

  return uniquePhrases.join(' ').trim();
}

/**
 * Check if transcript appears to be nonsense or background noise
 */
export function isNonsenseTranscript(transcript: string): boolean {
  if (!transcript) return true;

  // Check for excessive repetition of the same question/phrase
  const normalizedText = transcript.toLowerCase();

  // Common patterns from background audio/music
  const nonsensePatterns = [
    /^(hello[,.]?\s*){3,}/i,  // "Hello, hello, hello..." repeatedly
    /(hello[,.]?\s*testing[,.]?\s*){2,}/i,  // "Hello, testing" repeated
    /^(testing[,.]?\s*){3,}/i,  // "testing, testing, testing"
    /(testing.*?what['']?s going on[,.]?\s*){2,}/i,  // Pattern from screenshot
    /^(what['']?s going on\?\s*){2,}/i,  // Same question repeated
    /^(do you have.*?\?\s*){3,}/i,  // Same question repeated multiple times
    /(\w+[,.]?\s*)\1{4,}/gi,  // Any word repeated 5+ times
    /(hello.*?testing.*?){3,}/i,  // Hello testing pattern repeated
  ];

  for (const pattern of nonsensePatterns) {
    if (pattern.test(normalizedText)) {
      return true;
    }
  }

  // Check if it's mostly the same sentence repeated
  const sentences = transcript.split(/[.!?]+/).filter(s => s.trim());
  if (sentences.length > 2) {
    const uniqueSentences = new Set(sentences.map(s => s.toLowerCase().trim()));
    if (uniqueSentences.size === 1) {
      return true;  // All sentences are the same
    }
  }

  // Check word diversity - if very few unique words, likely nonsense
  const words = normalizedText.split(/\s+/).filter(w => w.length > 2);
  const uniqueWords = new Set(words);
  if (words.length > 10 && uniqueWords.size < words.length / 3) {
    return true;  // Less than 1/3 unique words
  }

  return false;
}

/**
 * Main function to clean transcript
 */
export function cleanupTranscript(transcript: string): string {
  // First check if it's nonsense
  if (isNonsenseTranscript(transcript)) {
    console.log('[TRANSCRIPT] Detected nonsense/background audio, filtering out');
    return '';  // Return empty string for nonsense
  }

  // First remove repeated phrases
  let cleaned = removeRepeatedPhrases(transcript);

  // Then remove any remaining duplicate sentences
  cleaned = cleanTranscript(cleaned);

  // Final cleanup
  cleaned = cleaned
    .replace(/\s+/g, ' ')  // Multiple spaces to single
    .replace(/\s+([.,!?])/g, '$1')  // Remove space before punctuation
    .trim();

  // Final check - if the cleaned version is still repetitive, return empty
  if (isNonsenseTranscript(cleaned)) {
    return '';
  }

  return cleaned;
}