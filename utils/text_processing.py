"""
Text Processing Utilities
NLP helpers for message processing and keyword extraction
"""

import re
import string
import hashlib
from typing import List, Set

class TextProcessor:
    """
    Text processing utilities for NLP tasks
    Handles cleaning, normalization, and keyword extraction
    """
    
    def __init__(self):
        """Initialize text processor"""
        # Common stop words for multiple languages
        self.stop_words = {
            "en": {"the", "is", "at", "which", "on", "a", "an", "and", "or", "but", "in", "with", "to", "for", "of", "i", "you", "me", "my", "your"},
            "fr": {"le", "de", "un", "une", "et", "à", "que", "dans", "pour", "avec", "sur", "par", "je", "tu", "il", "elle"},
            "es": {"el", "la", "de", "que", "y", "a", "en", "un", "una", "para", "con", "por", "yo", "tu"},
            "pt": {"o", "a", "de", "que", "e", "em", "um", "uma", "para", "com", "por", "eu", "tu"},
        }
        
        # Cannabis-specific terms to preserve
        self.cannabis_terms = {
            "thc", "cbd", "indica", "sativa", "hybrid", "strain", "terpene",
            "edible", "flower", "oil", "vape", "preroll", "pre-roll",
            "joint", "bud", "cannabis", "marijuana", "weed", "pot"
        }
        
        # Common misspellings
        self.corrections = {
            "prerols": "pre-rolls",
            "prerolls": "pre-rolls",
            "cannibis": "cannabis",
            "marajuana": "marijuana",
            "sative": "sativa",
            "indaca": "indica",
            "hybred": "hybrid",
            "ediable": "edible",
            "vapour": "vape",
            "terps": "terpenes"
        }
    
    def clean_message(self, message: str) -> str:
        """Clean and normalize message text"""
        
        # Apply spelling corrections
        message_lower = message.lower()
        for wrong, correct in self.corrections.items():
            message_lower = message_lower.replace(wrong, correct)
        
        # Remove extra whitespace
        message = " ".join(message_lower.split())
        
        # Remove URLs
        message = re.sub(r'http[s]?://\S+', '', message)
        
        # Remove email addresses
        message = re.sub(r'\S+@\S+', '', message)
        
        # Remove special characters but keep spaces and basic punctuation
        message = re.sub(r'[^\w\s.,!?-]', '', message)
        
        return message.strip()
    
    def extract_keywords(
        self,
        text: str,
        language: str = "en",
        max_keywords: int = 10
    ) -> List[str]:
        """Extract keywords from text"""
        
        # Clean text
        text = self.clean_message(text)
        
        # Tokenize
        words = text.lower().split()
        
        # Get stop words for language
        stop_words = self.stop_words.get(language, self.stop_words["en"])
        
        # Extract keywords
        keywords = []
        keyword_set = set()
        
        for word in words:
            # Remove punctuation
            word = word.strip(string.punctuation)
            
            # Skip if too short or stop word
            if len(word) < 2 or word in stop_words:
                continue
            
            # Preserve cannabis terms
            if word in self.cannabis_terms:
                if word not in keyword_set:
                    keywords.append(word)
                    keyword_set.add(word)
            # Add other meaningful words
            elif len(word) > 3 and word not in keyword_set:
                keywords.append(word)
                keyword_set.add(word)
        
        return keywords[:max_keywords]
    
    def normalize_for_cache(self, text: str) -> str:
        """Normalize text for cache key generation"""
        
        # Clean and lowercase
        text = self.clean_message(text).lower()
        
        # Remove all punctuation
        text = text.translate(str.maketrans('', '', string.punctuation))
        
        # Sort words for consistent hashing
        words = sorted(text.split())
        
        # Create normalized string
        normalized = " ".join(words)
        
        # Return first 100 chars of hash for shorter keys
        return hashlib.md5(normalized.encode()).hexdigest()[:100]
    
    def detect_intent(self, message: str) -> str:
        """Detect user intent from message"""
        
        message_lower = message.lower()
        
        # Greeting intents
        if any(greeting in message_lower for greeting in 
               ["hello", "hi", "hey", "greetings", "good morning", "good afternoon",
                "bonjour", "hola", "olá", "مرحبا", "你好"]):
            return "greeting"
        
        # Product search intent
        if any(term in message_lower for term in 
               ["looking for", "search", "find", "show me", "recommend",
                "suggest", "what do you have", "options", "available"]):
            return "product_search"
        
        # Medical/health intent
        if any(term in message_lower for term in 
               ["pain", "anxiety", "sleep", "medical", "condition", "symptom",
                "relief", "treatment", "help with", "suffering"]):
            return "medical_query"
        
        # Price inquiry
        if any(term in message_lower for term in 
               ["price", "cost", "how much", "expensive", "cheap", "budget",
                "afford", "deal", "discount", "sale"]):
            return "price_inquiry"
        
        # Information request
        if any(term in message_lower for term in 
               ["what is", "tell me about", "explain", "how does",
                "difference between", "vs", "versus"]):
            return "information_request"
        
        return "general"
    
    def extract_quantities(self, text: str) -> List[float]:
        """Extract quantity values from text (grams, ounces, etc.)"""
        
        quantities = []
        
        # Pattern for numbers with units
        pattern = r'(\d+(?:\.\d+)?)\s*(?:g|gram|grams|oz|ounce|ounces|eighth|quarter|half|full)'
        
        matches = re.findall(pattern, text.lower())
        
        for match in matches:
            try:
                value = float(match)
                quantities.append(value)
            except ValueError:
                continue
        
        # Handle text representations
        if "eighth" in text.lower():
            quantities.append(3.5)
        if "quarter" in text.lower():
            quantities.append(7)
        if "half" in text.lower() and "ounce" in text.lower():
            quantities.append(14)
        if "ounce" in text.lower() and "half" not in text.lower():
            quantities.append(28)
        
        return quantities