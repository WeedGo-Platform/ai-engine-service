/**
 * Context-Aware AutoCorrect System
 * Provides intelligent spelling suggestions based on language and context
 */

interface CorrectionSuggestion {
  word: string;
  confidence: number;
  reason?: string;
}

interface LanguageContext {
  language: string;
  confidence: number;
}

export class AutoCorrect {
  private userDictionary: Set<string> = new Set();
  private commonMisspellings: Map<string, string> = new Map();
  private cannabisTerms: Set<string> = new Set();
  private contextPatterns: Map<string, string[]> = new Map();
  private readonly storageKey = 'autocorrect_dictionary';
  private languageCache: Map<string, LanguageContext> = new Map();

  constructor() {
    this.initializeDictionaries();
    this.loadUserDictionary();
  }

  /**
   * Initialize built-in dictionaries
   */
  private initializeDictionaries(): void {
    // Common misspellings and corrections
    this.commonMisspellings = new Map([
      ['recieve', 'receive'],
      ['definately', 'definitely'],
      ['occured', 'occurred'],
      ['seperate', 'separate'],
      ['untill', 'until'],
      ['wich', 'which'],
      ['doesnt', "doesn't"],
      ['cant', "can't"],
      ['wont', "won't"],
      ['thier', 'their'],
      ['teh', 'the'],
      ['taht', 'that'],
      ['jsut', 'just'],
      ['waht', 'what'],
      ['hte', 'the'],
    ]);

    // Cannabis-specific terms (won't be "corrected")
    this.cannabisTerms = new Set([
      'indica', 'sativa', 'hybrid', 'cbd', 'thc', 'cbg', 'cbn',
      'terpene', 'terpenes', 'cannabinoid', 'cannabinoids',
      'edible', 'edibles', 'tincture', 'topical', 'vape',
      'flower', 'bud', 'nugs', 'eighths', 'quarters',
      'dispensary', 'budtender', 'strain', 'cultivar',
      'kush', 'haze', 'diesel', 'cookies', 'gelato',
      'dab', 'dabbing', 'concentrates', 'shatter', 'wax',
      'rosin', 'resin', 'distillate', 'isolate',
      'entourage', 'bioavailability', 'decarboxylation'
    ]);

    // Context patterns for better detection
    this.contextPatterns = new Map([
      ['cannabis', ['weed', 'marijuana', 'bud', 'flower', 'strain']],
      ['effects', ['high', 'relaxed', 'euphoric', 'sleepy', 'hungry', 'creative']],
      ['medical', ['pain', 'anxiety', 'depression', 'insomnia', 'inflammation']],
      ['products', ['gummies', 'brownies', 'cookies', 'chocolate', 'drinks']]
    ]);
  }

  /**
   * Load user's personal dictionary from localStorage
   */
  private loadUserDictionary(): void {
    try {
      const stored = localStorage.getItem(this.storageKey);
      if (stored) {
        const words = JSON.parse(stored);
        if (Array.isArray(words)) {
          this.userDictionary = new Set(words);
        }
      }
    } catch (error) {
      console.error('Failed to load user dictionary:', error);
    }
  }

  /**
   * Save user dictionary to localStorage
   */
  private saveUserDictionary(): void {
    try {
      const words = Array.from(this.userDictionary);
      localStorage.setItem(this.storageKey, JSON.stringify(words));
    } catch (error) {
      console.error('Failed to save user dictionary:', error);
    }
  }

  /**
   * Detect language from text
   */
  private detectLanguage(text: string): LanguageContext {
    // Check cache first
    const cached = this.languageCache.get(text);
    if (cached) return cached;

    // Simple language detection based on character sets and patterns
    const languages: { [key: string]: RegExp[] } = {
      'en': [/\b(the|and|or|is|are|was|were|been|have|has|had)\b/gi],
      'es': [/\b(el|la|los|las|un|una|es|son|está|están)\b/gi],
      'fr': [/\b(le|la|les|un|une|est|sont|avec|dans)\b/gi],
      'de': [/\b(der|die|das|ein|eine|ist|sind|mit|von)\b/gi],
      'pt': [/\b(o|a|os|as|um|uma|é|são|com|para)\b/gi],
      'it': [/\b(il|la|gli|le|un|una|è|sono|con|per)\b/gi],
      'nl': [/\b(de|het|een|is|zijn|was|waren|met|van)\b/gi],
    };

    let detectedLang = 'en';
    let maxMatches = 0;

    for (const [lang, patterns] of Object.entries(languages)) {
      let matches = 0;
      for (const pattern of patterns) {
        const found = text.match(pattern);
        if (found) matches += found.length;
      }
      if (matches > maxMatches) {
        maxMatches = matches;
        detectedLang = lang;
      }
    }

    const confidence = Math.min(maxMatches / 10, 1); // Normalize confidence
    const result = { language: detectedLang, confidence };
    
    // Cache result
    this.languageCache.set(text, result);
    
    return result;
  }

  /**
   * Check if a word is in cannabis context
   */
  private isInCannabisContext(word: string, context: string): boolean {
    const lowerWord = word.toLowerCase();
    const lowerContext = context.toLowerCase();

    // Check if it's a known cannabis term
    if (this.cannabisTerms.has(lowerWord)) return true;

    // Check context for cannabis-related words
    for (const [category, terms] of this.contextPatterns) {
      for (const term of terms) {
        if (lowerContext.includes(term)) {
          return true;
        }
      }
    }

    return false;
  }

  /**
   * Calculate Levenshtein distance between two strings
   */
  private levenshteinDistance(str1: string, str2: string): number {
    const matrix: number[][] = [];

    for (let i = 0; i <= str2.length; i++) {
      matrix[i] = [i];
    }

    for (let j = 0; j <= str1.length; j++) {
      matrix[0][j] = j;
    }

    for (let i = 1; i <= str2.length; i++) {
      for (let j = 1; j <= str1.length; j++) {
        if (str2.charAt(i - 1) === str1.charAt(j - 1)) {
          matrix[i][j] = matrix[i - 1][j - 1];
        } else {
          matrix[i][j] = Math.min(
            matrix[i - 1][j - 1] + 1, // substitution
            matrix[i][j - 1] + 1,     // insertion
            matrix[i - 1][j] + 1      // deletion
          );
        }
      }
    }

    return matrix[str2.length][str1.length];
  }

  /**
   * Get correction suggestions for a word
   */
  getSuggestions(word: string, context: string = ''): CorrectionSuggestion[] {
    const suggestions: CorrectionSuggestion[] = [];
    const lowerWord = word.toLowerCase();

    // Skip if word is too short
    if (word.length < 3) return suggestions;

    // Skip if it's a number or contains numbers
    if (/\d/.test(word)) return suggestions;

    // Skip if in user dictionary
    if (this.userDictionary.has(lowerWord)) return suggestions;

    // Skip if in cannabis context
    if (this.isInCannabisContext(word, context)) return suggestions;

    // Check common misspellings first
    if (this.commonMisspellings.has(lowerWord)) {
      suggestions.push({
        word: this.commonMisspellings.get(lowerWord)!,
        confidence: 0.95,
        reason: 'Common misspelling'
      });
    }

    // Use browser's spellcheck API if available
    if ('spellcheck' in document.createElement('input')) {
      // Browser will handle this automatically
    }

    return suggestions;
  }

  /**
   * Add word to user dictionary
   */
  addToUserDictionary(word: string): void {
    this.userDictionary.add(word.toLowerCase());
    this.saveUserDictionary();
  }

  /**
   * Remove word from user dictionary
   */
  removeFromUserDictionary(word: string): void {
    this.userDictionary.delete(word.toLowerCase());
    this.saveUserDictionary();
  }

  /**
   * Process text for autocorrect
   */
  processText(text: string): { original: string; corrected: string; suggestions: Map<string, CorrectionSuggestion[]> } {
    const words = text.split(/\s+/);
    const suggestions = new Map<string, CorrectionSuggestion[]>();
    let corrected = text;

    // Detect language context
    const langContext = this.detectLanguage(text);

    for (const word of words) {
      const wordSuggestions = this.getSuggestions(word, text);
      if (wordSuggestions.length > 0) {
        suggestions.set(word, wordSuggestions);
        
        // Auto-apply high confidence corrections
        const highConfidence = wordSuggestions.find(s => s.confidence > 0.9);
        if (highConfidence) {
          corrected = corrected.replace(new RegExp(`\\b${word}\\b`, 'gi'), highConfidence.word);
        }
      }
    }

    return { original: text, corrected, suggestions };
  }

  /**
   * Clear all cached data
   */
  clearCache(): void {
    this.languageCache.clear();
  }

  /**
   * Export user dictionary
   */
  exportUserDictionary(): string {
    return JSON.stringify(Array.from(this.userDictionary), null, 2);
  }

  /**
   * Import user dictionary
   */
  importUserDictionary(json: string): boolean {
    try {
      const words = JSON.parse(json);
      if (Array.isArray(words)) {
        this.userDictionary = new Set(words);
        this.saveUserDictionary();
        return true;
      }
    } catch (error) {
      console.error('Failed to import dictionary:', error);
    }
    return false;
  }
}

// Singleton instance
let autoCorrectInstance: AutoCorrect | null = null;

export const getAutoCorrect = (): AutoCorrect => {
  if (!autoCorrectInstance) {
    autoCorrectInstance = new AutoCorrect();
  }
  return autoCorrectInstance;
};