/**
 * Enhanced Chat Input Hook
 * Combines history navigation and autocorrect features
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { getChatHistory } from '../utils/chatHistory';
import { getAutoCorrect } from '../utils/autoCorrect';

interface UseEnhancedChatInputProps {
  onSubmit?: (value: string) => void;
  enableAutoCorrect?: boolean;
  enableHistory?: boolean;
  autoCorrectDelay?: number;
}

interface AutoCorrectSuggestion {
  original: string;
  suggestion: string;
  confidence: number;
}

export const useEnhancedChatInput = ({
  onSubmit,
  enableAutoCorrect = true,
  enableHistory = true,
  autoCorrectDelay = 500
}: UseEnhancedChatInputProps = {}) => {
  const [value, setValue] = useState<string>('');
  const [suggestions, setSuggestions] = useState<AutoCorrectSuggestion[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedSuggestion, setSelectedSuggestion] = useState(-1);
  
  const history = useRef(enableHistory ? getChatHistory() : null);
  const autoCorrect = useRef(enableAutoCorrect ? getAutoCorrect() : null);
  const autoCorrectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const inputRef = useRef<HTMLInputElement | HTMLTextAreaElement | null>(null);

  /**
   * Handle autocorrect processing
   */
  const processAutoCorrect = useCallback((text: string) => {
    if (!autoCorrect.current || !enableAutoCorrect) return;

    // Clear existing timer
    if (autoCorrectTimer.current) {
      clearTimeout(autoCorrectTimer.current);
    }

    // Set new timer for debounced autocorrect
    autoCorrectTimer.current = setTimeout(() => {
      const result = autoCorrect.current!.processText(text);
      
      // Convert suggestions to array format
      const suggestionArray: AutoCorrectSuggestion[] = [];
      result.suggestions.forEach((suggs, word) => {
        suggs.forEach(sugg => {
          suggestionArray.push({
            original: word,
            suggestion: sugg.word,
            confidence: sugg.confidence
          });
        });
      });

      setSuggestions(suggestionArray);
      setShowSuggestions(suggestionArray.length > 0);
    }, autoCorrectDelay);
  }, [enableAutoCorrect, autoCorrectDelay]);

  /**
   * Handle input change
   */
  const handleChange = useCallback((newValue: string) => {
    setValue(newValue);
    
    // Reset history navigation when typing
    if (history.current) {
      history.current.resetPosition();
    }

    // Process autocorrect
    if (enableAutoCorrect && newValue.length > 2) {
      processAutoCorrect(newValue);
    } else {
      setSuggestions([]);
      setShowSuggestions(false);
    }
  }, [enableAutoCorrect, processAutoCorrect]);

  /**
   * Apply autocorrect suggestion
   */
  const applySuggestion = useCallback((suggestion: AutoCorrectSuggestion) => {
    const newValue = value.replace(
      new RegExp(`\\b${suggestion.original}\\b`, 'gi'),
      suggestion.suggestion
    );
    setValue(newValue);
    setShowSuggestions(false);
    setSuggestions([]);
    
    // Add corrected word to user dictionary if needed
    if (autoCorrect.current && suggestion.confidence < 0.8) {
      autoCorrect.current.addToUserDictionary(suggestion.suggestion);
    }
  }, [value]);

  /**
   * Handle form submission
   */
  const handleSubmit = useCallback(() => {
    const trimmed = value.trim();
    if (!trimmed) return;

    // Add to history
    if (enableHistory && history.current) {
      history.current.add(trimmed);
    }

    // Clear input
    setValue('');
    setSuggestions([]);
    setShowSuggestions(false);

    // Call parent submit handler
    if (onSubmit) {
      onSubmit(trimmed);
    }
  }, [value, enableHistory, onSubmit]);

  /**
   * Handle key down events
   */
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    // Handle history navigation
    if (enableHistory && history.current) {
      if (e.key === 'ArrowUp') {
        e.preventDefault();
        const historicalValue = history.current.navigateUp(value);
        if (historicalValue !== null) {
          setValue(historicalValue);
          // Move cursor to end
          setTimeout(() => {
            if (inputRef.current) {
              const len = historicalValue.length;
              inputRef.current.setSelectionRange(len, len);
            }
          }, 0);
        }
        return;
      }
      
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        const historicalValue = history.current.navigateDown();
        if (historicalValue !== null) {
          setValue(historicalValue);
          // Move cursor to end
          setTimeout(() => {
            if (inputRef.current) {
              const len = historicalValue.length;
              inputRef.current.setSelectionRange(len, len);
            }
          }, 0);
        }
        return;
      }
    }

    // Handle suggestion navigation
    if (showSuggestions && suggestions.length > 0) {
      if (e.key === 'Tab') {
        e.preventDefault();
        // Apply first suggestion
        if (suggestions.length > 0) {
          applySuggestion(suggestions[0]);
        }
        return;
      }

      if (e.key === 'Escape') {
        setShowSuggestions(false);
        setSelectedSuggestion(-1);
        return;
      }
    }

    // Handle submit
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  }, [value, enableHistory, showSuggestions, suggestions, applySuggestion, handleSubmit]);

  /**
   * Get search suggestions from history
   */
  const getHistorySuggestions = useCallback((query: string) => {
    if (!history.current || !query) return [];
    return history.current.search(query, 5);
  }, []);

  /**
   * Clear history
   */
  const clearHistory = useCallback(() => {
    if (history.current) {
      history.current.clear();
    }
  }, []);

  /**
   * Add word to dictionary
   */
  const addToDictionary = useCallback((word: string) => {
    if (autoCorrect.current) {
      autoCorrect.current.addToUserDictionary(word);
    }
  }, []);

  /**
   * Cleanup on unmount
   */
  useEffect(() => {
    return () => {
      if (autoCorrectTimer.current) {
        clearTimeout(autoCorrectTimer.current);
      }
    };
  }, []);

  return {
    // State
    value,
    suggestions,
    showSuggestions,
    selectedSuggestion,
    
    // Methods
    setValue: handleChange,
    handleKeyDown,
    handleSubmit,
    applySuggestion,
    getHistorySuggestions,
    clearHistory,
    addToDictionary,
    
    // Refs
    inputRef,
    
    // Utilities
    dismissSuggestions: () => setShowSuggestions(false),
  };
};