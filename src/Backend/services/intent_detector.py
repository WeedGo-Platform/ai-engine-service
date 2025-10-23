"""
Intent Detection System for V5 AI Engine
Pluggable, LLM-agnostic intent classification with caching
"""

import json
import logging
import hashlib
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from collections import OrderedDict
import time

logger = logging.getLogger(__name__)


class IntentDetectorInterface(ABC):
    """Abstract interface for intent detection implementations"""
    
    @abstractmethod
    def detect(self, message: str, language: str = "auto") -> Dict[str, Any]:
        """
        Detect intent from a message
        
        Args:
            message: User input message
            language: Language code or "auto" for auto-detection
            
        Returns:
            Dict containing:
                - intent: Detected intent name
                - confidence: Confidence score (0-1)
                - language: Detected/specified language
                - metadata: Additional detection metadata
        """
        pass
    
    @abstractmethod
    def load_intents(self, agent_id: str) -> bool:
        """Load intent configuration for an agent"""
        pass
    
    @abstractmethod
    def clear_cache(self) -> None:
        """Clear any cached results"""
        pass


class LLMIntentDetector(IntentDetectorInterface):
    """LLM-based intent detector with intelligent caching"""
    
    def __init__(self, v5_engine=None, cache_size: int = 1000):
        """
        Initialize the LLM Intent Detector
        
        Args:
            v5_engine: Reference to V5 engine for LLM generation
            cache_size: Maximum number of cached intent results
        """
        self.v5_engine = v5_engine
        self.cache_size = cache_size
        self.cache = OrderedDict()  # LRU cache
        self.intent_config = {}
        self.current_agent = None
        self.stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "total_requests": 0,
            "avg_latency_ms": 0
        }
    
    def load_intents(self, agent_id: str) -> bool:
        """
        Load intent configuration from agent's intent.json
        
        Args:
            agent_id: The agent identifier
            
        Returns:
            True if successfully loaded, False otherwise
        """
        try:
            # Load intent configuration
            intent_path = Path(f"prompts/agents/{agent_id}/intent.json")
            if not intent_path.exists():
                # Try legacy path or create default
                logger.warning(f"❌ INTENT.JSON NOT FOUND at {intent_path}, using defaults")
                self.intent_config = self._get_default_intents()
                self.current_agent = agent_id
                return False
            
            with open(intent_path, 'r') as f:
                self.intent_config = json.load(f)
            
            self.current_agent = agent_id
            logger.info(f"✅ LOADED INTENT.JSON for agent {agent_id}")
            logger.info(f"  {len(self.intent_config.get('intents', {}))} intents available: {list(self.intent_config.get('intents', {}).keys())}")
            
            # Clear cache when loading new intents
            self.clear_cache()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to load intents for {agent_id}: {e}")
            self.intent_config = self._get_default_intents()
            return False
    
    def detect(self, message: str, language: str = "auto") -> Dict[str, Any]:
        """
        Detect intent using LLM with intelligent caching
        
        Args:
            message: User input message
            language: Language code or "auto"
            
        Returns:
            Detection result dictionary
        """
        start_time = time.time()
        self.stats["total_requests"] += 1
        
        # Generate cache key
        cache_key = self._get_cache_key(message, language)
        
        # Check cache first
        if cache_key in self.cache:
            self.stats["cache_hits"] += 1
            self._move_to_end(cache_key)  # LRU update
            result = self.cache[cache_key].copy()
            result["from_cache"] = True
            result["latency_ms"] = 0
            return result
        
        self.stats["cache_misses"] += 1
        
        # Perform detection
        result = self._detect_with_llm(message, language)
        
        # Update cache
        self._add_to_cache(cache_key, result)
        
        # Calculate latency
        latency_ms = (time.time() - start_time) * 1000
        result["latency_ms"] = round(latency_ms, 2)
        
        # Update average latency
        self._update_avg_latency(latency_ms)
        
        return result
    
    def _detect_with_llm(self, message: str, language: str) -> Dict[str, Any]:
        """
        Perform actual LLM-based intent detection

        Args:
            message: User input
            language: Language code

        Returns:
            Detection result
        """
        if not self.v5_engine or not self.v5_engine.current_model:
            # Fallback to pattern-based detection
            logger.warning(f"⚠️ Intent detector falling back - v5_engine: {self.v5_engine is not None}, current_model: {self.v5_engine.current_model if self.v5_engine else None}")
            return self._fallback_detection(message, language)
        
        # Prevent recursion - if we're already detecting intent, return fallback
        if hasattr(self.v5_engine, '_detecting_intent') and self.v5_engine._detecting_intent:
            return self._fallback_detection(message, language)
        
        # Get available intents
        intents = self.intent_config.get("intents", {})
        intent_list = list(intents.keys())
        
        # Build classification prompt
        prompt = self._build_classification_prompt(message, intent_list, language)
        
        try:
            # Mark that we're detecting intent to prevent recursion
            self.v5_engine._detecting_intent = True

            # Use V5 engine for generation - call internal method to avoid recursion
            if hasattr(self.v5_engine, '_generate_internal'):
                result = self.v5_engine._generate_internal(
                    prompt=prompt,
                    max_tokens=20,  # We only need the intent name
                    temperature=0.1,  # Low temperature for consistency
                    top_p=0.9
                )
                # Ensure result is properly formatted
                if not isinstance(result, dict):
                    logger.warning(f"_generate_internal returned non-dict: {type(result)}")
                    result = {"text": str(result) if result else "general"}
            else:
                # Direct model call to avoid recursion
                result = self._direct_model_call(prompt)
            
            # Ensure result is a dictionary
            if not isinstance(result, dict):
                logger.warning(f"Model returned non-dict result: {type(result)}")
                result = {"text": str(result) if result else "general"}
            
            # Parse the response
            response_text = result.get("text", "").strip().lower()
            
            # Extract intent and confidence
            intent, confidence = self._parse_llm_response(response_text, intent_list)
            
            # Get prompt_type from intent configuration
            prompt_type = None
            if intent in intents:
                prompt_type = intents[intent].get('prompt_type', None)
            
            return {
                "intent": intent,
                "confidence": confidence,
                "prompt_type": prompt_type,  # Include prompt_type in result
                "language": language if language != "auto" else self._detect_language(message),
                "method": "llm",
                "from_cache": False,
                "metadata": {
                    "model": self.v5_engine.current_model_name if self.v5_engine else "unknown",
                    "prompt_tokens": len(prompt.split()),
                    "intents_available": len(intent_list)
                }
            }
            
        except Exception as e:
            logger.error(f"LLM detection failed: {e}")
            return self._fallback_detection(message, language)
        finally:
            # Clear the recursion flag
            if self.v5_engine and hasattr(self.v5_engine, '_detecting_intent'):
                self.v5_engine._detecting_intent = False
    
    def _direct_model_call(self, prompt: str) -> Dict[str, Any]:
        """
        Direct model call to avoid recursion

        Args:
            prompt: The prompt to send to the model

        Returns:
            Model response dictionary
        """
        try:
            if self.v5_engine and self.v5_engine.current_model:
                # Direct call to model
                response = self.v5_engine.current_model(
                    prompt,
                    max_tokens=20,
                    temperature=0.1,
                    top_p=0.9,
                    stop=["\n", ".", ","],
                    echo=False
                )

                # Handle different response types robustly
                if response is None:
                    logger.warning("Model returned None response")
                    return {"text": "general", "model": self.v5_engine.current_model_name}

                if isinstance(response, str):
                    # If model returns a string directly, use it as the text
                    text = response.strip() if response else "general"
                    return {
                        "text": text,
                        "model": self.v5_engine.current_model_name
                    }
                elif isinstance(response, dict):
                    # Handle different dict structures
                    text = None

                    # Try to extract text from various possible structures
                    if "text" in response:
                        text = response["text"]
                    elif "choices" in response and isinstance(response["choices"], list) and len(response["choices"]) > 0:
                        choice = response["choices"][0]
                        if isinstance(choice, dict):
                            text = choice.get("text", choice.get("message", {}).get("content"))
                        elif isinstance(choice, str):
                            text = choice
                    elif "content" in response:
                        text = response["content"]
                    elif "output" in response:
                        text = response["output"]

                    # Ensure we have valid text
                    if text is None or (isinstance(text, str) and not text.strip()):
                        text = "general"
                    elif not isinstance(text, str):
                        text = str(text)

                    return {
                        "text": text.strip(),
                        "model": self.v5_engine.current_model_name
                    }
                else:
                    # Fallback for unexpected types - try to convert to string
                    logger.warning(f"Unexpected response type from model: {type(response)}")
                    try:
                        text = str(response).strip()
                        if not text:
                            text = "general"
                    except:
                        text = "general"
                    return {"text": text, "model": self.v5_engine.current_model_name}

        except Exception as e:
            logger.error(f"Direct model call failed: {e}")
            import traceback
            logger.error(traceback.format_exc())

        return {"text": "general", "model": "fallback"}
    
    def _build_classification_prompt(self, message: str, intents: List[str], language: str) -> str:
        """
        Build the classification prompt for the LLM
        
        Args:
            message: User message
            intents: List of available intents
            language: Language code
            
        Returns:
            Formatted prompt string
        """
        # Get prompt template from config or use default
        template = self.intent_config.get("classification_prompt", {}).get("template", None)
        
        if template:
            # Use configured template
            return template.format(
                message=message,
                intents=", ".join(intents),
                language=language
            )
        
        # Default optimized prompt
        intent_str = ", ".join(intents)
        
        if language != "auto":
            prompt = f"""Classify this {language} message into ONE intent.
Message: "{message}"
Available intents: {intent_str}
Intent:"""
        else:
            prompt = f"""Classify this message into ONE intent.
Message: "{message}"
Available intents: {intent_str}
Intent:"""
        
        return prompt
    
    def _parse_llm_response(self, response: str, valid_intents: List[str]) -> Tuple[str, float]:
        """
        Parse LLM response to extract intent and confidence

        Args:
            response: LLM response text
            valid_intents: List of valid intent names

        Returns:
            Tuple of (intent, confidence)
        """
        # Handle None or non-string responses
        if not response:
            return "general", 0.3

        if not isinstance(response, str):
            try:
                response = str(response)
            except:
                return "general", 0.3

        response = response.lower().strip()

        # Remove common prefixes that LLM might add
        prefixes_to_remove = ["intent:", "the intent is:", "intent is", "classified as:", "classification:"]
        for prefix in prefixes_to_remove:
            if response.startswith(prefix):
                response = response[len(prefix):].strip()

        # Direct match
        if response in valid_intents:
            return response, 0.95

        # Check if response contains an intent (but avoid partial matches)
        for intent in valid_intents:
            # Word boundary check to avoid matching "product" in "production"
            import re
            pattern = r'\b' + re.escape(intent) + r'\b'
            if re.search(pattern, response):
                return intent, 0.85

        # Fuzzy match for close matches
        for intent in valid_intents:
            if self._fuzzy_match(response, intent):
                return intent, 0.75

        # Default fallback
        return "general", 0.5
    
    def _fuzzy_match(self, text1: str, text2: str, threshold: float = 0.8) -> bool:
        """
        Simple fuzzy matching based on character overlap
        
        Args:
            text1: First text
            text2: Second text
            threshold: Match threshold (0-1)
            
        Returns:
            True if texts match above threshold
        """
        # Simple character-based similarity
        set1 = set(text1.lower())
        set2 = set(text2.lower())
        
        if not set1 or not set2:
            return False
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        similarity = intersection / union if union > 0 else 0
        return similarity >= threshold
    
    def _fallback_detection(self, message: str, language: str) -> Dict[str, Any]:
        """
        Fallback when LLM is unavailable - no pattern matching
        
        Args:
            message: User message
            language: Language code
            
        Returns:
            Detection result with general intent only
        """
        # No pattern matching - just return general intent
        return {
            "intent": "general",
            "confidence": 0.3,
            "language": language if language != "auto" else self._detect_language(message),
            "method": "fallback",
            "from_cache": False,
            "metadata": {"reason": "LLM unavailable, no pattern matching"}
        }
    
    def _detect_language(self, message: str) -> str:
        """
        Enhanced language detection using keyword matching
        
        Args:
            message: Input message
            
        Returns:
            Language code
        """
        message_lower = message.lower().strip()
        
        # Spanish keywords (most common words and greetings)
        spanish_keywords = [
            'hola', 'adios', 'gracias', 'por favor', 'buenos', 'dias', 'buenas', 'noches', 'tardes',
            'como', 'cómo', 'estas', 'estás', 'que', 'qué', 'si', 'sí', 'no', 'bien', 'mal',
            'mucho', 'poco', 'donde', 'dónde', 'cuando', 'cuándo', 'quien', 'quién',
            'amigo', 'amiga', 'señor', 'señora', 'necesito', 'quiero', 'tengo', 'tienes',
            'puedo', 'puede', 'ayuda', 'aqui', 'aquí', 'alli', 'allí', 'ahora', 'despues', 'después'
        ]
        
        # French keywords
        french_keywords = [
            'bonjour', 'salut', 'merci', 'oui', 'non', 'comment', 'ça', 'va', 'bien',
            'je', 'tu', 'il', 'elle', 'nous', 'vous', 'ils', 'elles', 'est', 'sont',
            'avoir', 'être', 'faire', 'aller', 'venir', 'voir', 'dire', 'pouvoir',
            'vouloir', 'avec', 'dans', 'pour', 'sur', 'mais', 'aussi', 'très', 'alors'
        ]
        
        # German keywords
        german_keywords = [
            'hallo', 'guten', 'tag', 'morgen', 'abend', 'danke', 'bitte', 'ja', 'nein',
            'wie', 'was', 'wo', 'wann', 'warum', 'wer', 'ich', 'du', 'er', 'sie', 'es',
            'wir', 'ihr', 'ist', 'sind', 'haben', 'sein', 'werden', 'können', 'müssen',
            'möchten', 'mit', 'für', 'auf', 'in', 'zu', 'auch', 'nicht', 'und', 'oder'
        ]
        
        # Portuguese keywords
        portuguese_keywords = [
            'olá', 'oi', 'obrigado', 'obrigada', 'sim', 'não', 'como', 'está', 'vai',
            'bom', 'boa', 'dia', 'noite', 'tarde', 'eu', 'você', 'ele', 'ela', 'nós',
            'vocês', 'eles', 'elas', 'é', 'são', 'estar', 'ter', 'fazer', 'ir', 'vir',
            'ver', 'poder', 'querer', 'com', 'em', 'para', 'por', 'mas', 'também', 'muito'
        ]
        
        # Italian keywords
        italian_keywords = [
            'ciao', 'buongiorno', 'buonasera', 'grazie', 'prego', 'scusa', 'si', 'sì', 'no',
            'come', 'cosa', 'dove', 'quando', 'perché', 'chi', 'io', 'tu', 'lui', 'lei',
            'noi', 'voi', 'loro', 'è', 'sono', 'essere', 'avere', 'fare', 'andare', 'venire',
            'vedere', 'dire', 'potere', 'volere', 'con', 'in', 'per', 'su', 'ma', 'anche', 'molto'
        ]
        
        # Split message into words
        words = message_lower.split()
        
        # Count matches for each language
        language_scores = {
            'es': sum(1 for word in words if word in spanish_keywords),
            'fr': sum(1 for word in words if word in french_keywords),
            'de': sum(1 for word in words if word in german_keywords),
            'pt': sum(1 for word in words if word in portuguese_keywords),
            'it': sum(1 for word in words if word in italian_keywords)
        }
        
        # Check character-based detection for non-Latin scripts
        if any(ord(char) > 0x4E00 for char in message):
            return "zh"  # Chinese
        elif any(ord(char) in range(0x0600, 0x06FF) for char in message):
            return "ar"  # Arabic
        elif any(ord(char) in range(0x3040, 0x30FF) for char in message):
            return "ja"  # Japanese
        elif any(ord(char) in range(0xAC00, 0xD7AF) for char in message):
            return "ko"  # Korean
        
        # Get language with highest score
        max_score = max(language_scores.values())
        if max_score > 0:
            detected = max(language_scores, key=language_scores.get)
            logger.info(f"🌐 Language detection: '{message}' → {detected} (score: {max_score})")
            return detected
        
        # Default to English
        return "en"
    
    def _get_cache_key(self, message: str, language: str) -> str:
        """
        Generate cache key for message and language
        
        Args:
            message: User message
            language: Language code
            
        Returns:
            Cache key string
        """
        # Create normalized key
        normalized = message.lower().strip()
        key_string = f"{self.current_agent}:{language}:{normalized}"
        
        # Use hash for consistent key length
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _add_to_cache(self, key: str, value: Dict[str, Any]) -> None:
        """
        Add result to cache with LRU eviction
        
        Args:
            key: Cache key
            value: Result to cache
        """
        # Remove oldest if cache is full
        if len(self.cache) >= self.cache_size:
            self.cache.popitem(last=False)  # Remove oldest
        
        # Add new entry
        self.cache[key] = value.copy()
    
    def _move_to_end(self, key: str) -> None:
        """
        Move cache entry to end (most recently used)
        
        Args:
            key: Cache key to move
        """
        self.cache.move_to_end(key)
    
    def _update_avg_latency(self, latency_ms: float) -> None:
        """
        Update average latency statistics
        
        Args:
            latency_ms: Latest latency measurement
        """
        current_avg = self.stats["avg_latency_ms"]
        total_requests = self.stats["cache_misses"]  # Only count non-cached
        
        if total_requests > 0:
            # Running average
            self.stats["avg_latency_ms"] = round(
                (current_avg * (total_requests - 1) + latency_ms) / total_requests,
                2
            )
    
    def clear_cache(self) -> None:
        """Clear the intent cache"""
        self.cache.clear()
        logger.info("Intent cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get detector statistics
        
        Returns:
            Statistics dictionary
        """
        hit_rate = 0
        if self.stats["total_requests"] > 0:
            hit_rate = round(
                self.stats["cache_hits"] / self.stats["total_requests"] * 100,
                2
            )
        
        return {
            **self.stats,
            "cache_hit_rate": f"{hit_rate}%",
            "cache_size": len(self.cache),
            "cache_capacity": self.cache_size,
            "current_agent": self.current_agent
        }
    
    def _get_default_intents(self) -> Dict[str, Any]:
        """
        Get default intent configuration
        
        Returns:
            Default intent configuration dictionary
        """
        return {
            "version": "1.0.0",
            "intents": {
                "greeting": {
                    "description": "User greetings and hellos",
                    "keywords": ["hello", "hi", "hey", "greetings", "good morning", "good evening"],
                    "patterns": ["how are you", "what's up", "howdy"]
                },
                "product_search": {
                    "description": "Looking for products",
                    "keywords": ["want", "need", "looking for", "show me", "find", "search", "get"],
                    "patterns": ["do you have", "can I get", "I'd like"]
                },
                "recommendation": {
                    "description": "Asking for recommendations",
                    "keywords": ["recommend", "suggest", "advice", "best", "good for"],
                    "patterns": ["what do you recommend", "help me choose", "what should I"]
                },
                "yes_no": {
                    "description": "Yes/no questions",
                    "keywords": ["is", "are", "do", "does", "can", "should", "will", "would"],
                    "patterns": ["is it", "are there", "do you"]
                },
                "product_info": {
                    "description": "Asking about product details",
                    "keywords": ["tell me about", "what is", "how much", "price", "cost", "thc", "cbd"],
                    "patterns": ["information about", "details on", "what's the"]
                },
                "general": {
                    "description": "General conversation",
                    "keywords": [],
                    "patterns": []
                }
            },
            "classification_prompt": {
                "template": None  # Use default
            }
        }


class PatternIntentDetector(IntentDetectorInterface):
    """Minimal intent detector without pattern matching - returns general intent only"""
    
    def __init__(self):
        """Initialize the minimal detector"""
        self.intent_config = {}
        self.current_agent = None
    
    def load_intents(self, agent_id: str) -> bool:
        """Load intent configuration"""
        try:
            intent_path = Path(f"prompts/agents/{agent_id}/intent.json")
            if intent_path.exists():
                with open(intent_path, 'r') as f:
                    self.intent_config = json.load(f)
            else:
                self.intent_config = LLMIntentDetector()._get_default_intents()
            
            self.current_agent = agent_id
            return True
            
        except Exception as e:
            logger.error(f"Failed to load intents: {e}")
            return False
    
    def detect(self, message: str, language: str = "auto") -> Dict[str, Any]:
        """Minimal detection - no pattern matching, always returns general intent"""
        # No pattern matching - always return general intent
        return {
            "intent": "general",
            "confidence": 0.3,
            "language": language if language != "auto" else "en",
            "method": "minimal",
            "from_cache": False,
            "metadata": {"reason": "Pattern matching disabled"}
        }
    
    def clear_cache(self) -> None:
        """No cache for minimal detector"""
        pass