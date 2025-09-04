"""
Model-based Translation Service
All translations should go through the model, not hardcoded strings
"""
import logging
from typing import Dict, List, Optional, Any
from services.multilingual_llm_service import MultilingualLLMService

logger = logging.getLogger(__name__)

class ModelTranslationService:
    """Service that handles all translations through AI models"""
    
    def __init__(self, llm_service: Optional[MultilingualLLMService] = None):
        self.llm_service = llm_service
        self._greeting_cache = {}
        self._ui_element_cache = {}
        
    async def translate_text(self, text: str, target_language: str, context: str = "general") -> str:
        """Translate any text using the model"""
        if target_language == "en":
            return text
            
        # Use the multilingual LLM service for translation
        if self.llm_service:
            try:
                response = await self.llm_service.translate(text, "en", target_language, context)
                return response.get("text", text)
            except Exception as e:
                logger.error(f"Translation failed: {e}")
                return text
        
        # Fallback to original text if no service available
        return text
    
    async def get_greeting(self, language: str) -> str:
        """Get greeting in specified language using model"""
        if language in self._greeting_cache:
            return self._greeting_cache[language]
            
        # Generate greeting using model
        prompt = f"Generate a friendly greeting for a cannabis dispensary in {language}. Keep it brief and welcoming."
        
        if self.llm_service:
            response = await self.llm_service.generate_response(
                prompt, 
                language,
                {"context": "greeting", "role": "budtender"}
            )
            greeting = response[0] if isinstance(response, tuple) else response
            self._greeting_cache[language] = greeting
            return greeting
        
        # Simple fallback
        return "Hello! Welcome to our dispensary. How can I help you today?"
    
    async def translate_ui_elements(self, elements: Dict[str, str], target_language: str) -> Dict[str, str]:
        """Translate UI elements like buttons, labels, etc."""
        if target_language == "en":
            return elements
            
        translated = {}
        for key, value in elements.items():
            translated[key] = await self.translate_text(value, target_language, "ui")
        
        return translated
    
    async def translate_product_info(self, product: Dict[str, Any], target_language: str) -> Dict[str, Any]:
        """Translate product information"""
        if target_language == "en":
            return product
            
        translated = product.copy()
        
        # Translate description and effects
        if "description" in product:
            translated["description"] = await self.translate_text(
                product["description"], target_language, "product"
            )
        
        if "effects" in product and isinstance(product["effects"], list):
            translated["effects"] = [
                await self.translate_text(effect, target_language, "effects")
                for effect in product["effects"]
            ]
        
        return translated
    
    def detect_greeting(self, message: str) -> Optional[str]:
        """Detect if message is a greeting and return the language"""
        message_lower = message.lower().strip()
        
        # Use pattern matching for common greetings
        greeting_patterns = {
            "en": ["hello", "hi", "hey", "howdy", "greetings"],
            "es": ["hola", "buenos días", "buenas tardes", "buenas noches", "saludos"],
            "fr": ["bonjour", "bonsoir", "salut", "coucou"],
            "zh": ["你好", "您好", "嗨", "早上好", "晚上好"],
            "pt": ["olá", "oi", "bom dia", "boa tarde", "boa noite"],
            "ar": ["مرحبا", "أهلا", "السلام عليكم", "صباح الخير", "مساء الخير"]
        }
        
        for lang, greetings in greeting_patterns.items():
            if any(greeting in message_lower for greeting in greetings):
                return lang
        
        return None
    
    async def get_system_prompt(self, language: str, role: str = "budtender") -> str:
        """Generate system prompt in specified language"""
        if language == "en":
            base_prompt = f"You are a knowledgeable {role} at a licensed cannabis dispensary."
        else:
            # Use model to translate and adapt the system prompt
            base_prompt = await self.translate_text(
                f"You are a knowledgeable {role} at a licensed cannabis dispensary.",
                language,
                "system"
            )
        
        return base_prompt
    
    async def translate_quick_action(self, action: Dict[str, str], target_language: str) -> Dict[str, str]:
        """Translate quick action dynamically"""
        if target_language == "en":
            return action
            
        translated = action.copy()
        
        # Translate both label and value
        if "label" in action:
            translated["label"] = await self.translate_text(action["label"], target_language, "ui")
        
        if "value" in action:
            translated["value"] = await self.translate_text(action["value"], target_language, "action")
        
        return translated