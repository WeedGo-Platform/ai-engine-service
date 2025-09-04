"""
Model-Driven Language Detection Service
NO hardcoded patterns - everything through the model
"""
import logging
import json
from typing import Optional, Dict, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

class ModelDrivenLanguageService:
    """
    Pure model-driven language detection and routing
    NO hardcoded patterns or rules
    """
    
    def __init__(self, llm_instance=None, prompt_path: str = "prompts"):
        self.llm = llm_instance
        self.prompt_path = Path(prompt_path)
        self.language_prompt = self._load_prompt("language_detection.json")
        
    def _load_prompt(self, filename: str) -> Dict:
        """Load prompt from JSON file"""
        prompt_file = self.prompt_path / filename
        if prompt_file.exists():
            with open(prompt_file, 'r') as f:
                return json.load(f)
        return {}
    
    async def detect_language(self, text: str, session_context: Optional[Dict] = None) -> Tuple[str, float]:
        """
        Detect language using ONLY the model - no patterns
        
        Args:
            text: Input text to analyze
            session_context: Optional session history for context
            
        Returns:
            Tuple of (language_code, confidence)
        """
        if not self.llm:
            logger.warning("No LLM configured, defaulting to English")
            return "en", 0.5
        
        # Build prompt from template
        detection_prompt = self.language_prompt.get("language_detection_prompt", {})
        prompt_template = detection_prompt.get("template", "")
        
        if not prompt_template:
            # Fallback prompt if file not loaded
            prompt_template = """Detect the language of this text and respond with only the 2-letter ISO code (en, es, fr, zh, pt, ar):

Text: {text}

Language code:"""
        
        prompt = prompt_template.format(text=text)
        
        # Add context if available
        if session_context and session_context.get("previous_language"):
            prompt += f"\nNote: Previous conversation was in {session_context['previous_language']}"
        
        try:
            # Get language detection from model
            response = self.llm(
                prompt,
                max_tokens=10,
                temperature=0.1,  # Low temperature for consistent detection
                echo=False
            )
            
            # Extract language code from response
            raw_response = response.get('choices', [{}])[0].get('text', '').strip().lower()
            
            # Clean up the response to get just the language code
            # Remove any extra text, quotes, periods, etc.
            detected_lang = raw_response.replace('.', '').replace('"', '').replace("'", '').strip()
            
            # If response contains multiple words, try to extract a 2-letter code
            if len(detected_lang) > 3:
                # Look for common 2-letter ISO codes anywhere in the response
                import re
                match = re.search(r'\b([a-z]{2})\b', detected_lang)
                if match:
                    detected_lang = match.group(1)
            
            # Trust the model's language detection - no artificial restrictions
            if detected_lang and len(detected_lang) == 2:
                logger.info(f"Model detected language: {detected_lang} for text: '{text[:50]}...'")
                return detected_lang, 0.9
            else:
                # Log for debugging but still try to use what model detected
                logger.warning(f"Model returned unexpected format: '{raw_response}', using as-is")
                # If we at least got something that looks like a language code, use it
                if detected_lang and len(detected_lang) <= 3:
                    return detected_lang, 0.7
                return "en", 0.5
                
        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            return "en", 0.5
    
    async def route_to_model(self, language: str) -> str:
        """
        Determine which model to use based on language
        Pure configuration-driven, no hardcoded rules
        """
        # Load routing configuration from prompt file
        routing_config = self.language_prompt.get("language_routing", {})
        
        # This would be expanded to route to different models
        # For now, return the language for the multilingual engine
        return language
    
    async def get_language_specific_prompt(self, language: str, prompt_type: str) -> str:
        """
        Load language-specific prompts from files
        No hardcoded translations
        """
        # Try to load language-specific prompt file
        lang_prompt_file = self.prompt_path / f"{language}_{prompt_type}.json"
        
        if lang_prompt_file.exists():
            with open(lang_prompt_file, 'r') as f:
                lang_prompts = json.load(f)
                return lang_prompts.get(prompt_type, "")
        
        # Fallback to English
        eng_prompt_file = self.prompt_path / f"en_{prompt_type}.json"
        if eng_prompt_file.exists():
            with open(eng_prompt_file, 'r') as f:
                eng_prompts = json.load(f)
                return eng_prompts.get(prompt_type, "")
        
        return ""