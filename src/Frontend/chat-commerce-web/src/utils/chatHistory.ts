/**
 * Chat History Manager
 * Manages chat input history with localStorage persistence
 */

export class ChatHistory {
  private history: string[] = [];
  private position: number = -1;
  private tempInput: string = '';
  private readonly maxSize: number = 20;
  private readonly storageKey: string = 'chat_history';
  private readonly minLength: number = 3; // Minimum length to save

  constructor() {
    this.loadHistory();
  }

  /**
   * Load history from localStorage
   */
  private loadHistory(): void {
    try {
      const stored = localStorage.getItem(this.storageKey);
      if (stored) {
        const parsed = JSON.parse(stored);
        if (Array.isArray(parsed)) {
          this.history = parsed.slice(0, this.maxSize);
        }
      }
    } catch (error) {
      console.error('Failed to load chat history:', error);
      this.history = [];
    }
  }

  /**
   * Save history to localStorage
   */
  private saveHistory(): void {
    try {
      localStorage.setItem(this.storageKey, JSON.stringify(this.history));
    } catch (error) {
      console.error('Failed to save chat history:', error);
    }
  }

  /**
   * Add a new entry to history
   */
  add(entry: string): void {
    // Clean and validate entry
    const cleaned = entry.trim();
    
    // Skip if too short or empty
    if (cleaned.length < this.minLength) return;
    
    // Remove duplicates (case-insensitive)
    this.history = this.history.filter(
      h => h.toLowerCase() !== cleaned.toLowerCase()
    );
    
    // Add to front
    this.history.unshift(cleaned);
    
    // Trim to max size
    if (this.history.length > this.maxSize) {
      this.history = this.history.slice(0, this.maxSize);
    }
    
    // Reset position
    this.position = -1;
    this.tempInput = '';
    
    // Persist
    this.saveHistory();
  }

  /**
   * Navigate up in history (older entries)
   */
  navigateUp(currentInput: string): string | null {
    // Save current input if at start
    if (this.position === -1 && currentInput) {
      this.tempInput = currentInput;
    }
    
    // Check if we can go up
    if (this.position < this.history.length - 1) {
      this.position++;
      return this.history[this.position];
    }
    
    return null;
  }

  /**
   * Navigate down in history (newer entries)
   */
  navigateDown(): string | null {
    // Check if we can go down
    if (this.position > 0) {
      this.position--;
      return this.history[this.position];
    } else if (this.position === 0) {
      // Return to original input
      this.position = -1;
      return this.tempInput;
    }
    
    return null;
  }

  /**
   * Reset navigation position
   */
  resetPosition(): void {
    this.position = -1;
    this.tempInput = '';
  }

  /**
   * Search history with fuzzy matching
   */
  search(query: string, limit: number = 5): string[] {
    if (!query) return [];
    
    const lowerQuery = query.toLowerCase();
    
    return this.history
      .filter(entry => entry.toLowerCase().includes(lowerQuery))
      .slice(0, limit);
  }

  /**
   * Get recent unique entries
   */
  getRecent(count: number = 5): string[] {
    return this.history.slice(0, count);
  }

  /**
   * Clear all history
   */
  clear(): void {
    this.history = [];
    this.position = -1;
    this.tempInput = '';
    localStorage.removeItem(this.storageKey);
  }

  /**
   * Export history as JSON
   */
  export(): string {
    return JSON.stringify(this.history, null, 2);
  }

  /**
   * Import history from JSON
   */
  import(json: string): boolean {
    try {
      const parsed = JSON.parse(json);
      if (Array.isArray(parsed)) {
        this.history = parsed.slice(0, this.maxSize);
        this.saveHistory();
        return true;
      }
    } catch (error) {
      console.error('Failed to import history:', error);
    }
    return false;
  }
}

// Singleton instance
let historyInstance: ChatHistory | null = null;

export const getChatHistory = (): ChatHistory => {
  if (!historyInstance) {
    historyInstance = new ChatHistory();
  }
  return historyInstance;
};