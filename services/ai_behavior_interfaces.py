"""
AI Behavior Interfaces
Complete abstraction of all AI behaviors for different roles
Following Single Responsibility Principle
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# Intent Types
class Intent(Enum):
    """Universal intent types"""
    GREETING = "greeting"
    PRODUCT_SEARCH = "product_search"
    RECOMMENDATION = "recommendation"
    INFORMATION = "information"
    COMPLAINT = "complaint"
    CHECKOUT = "checkout"
    MEDICAL_CONSULTATION = "medical_consultation"
    EDUCATION = "education"
    SMALL_TALK = "small_talk"
    UNKNOWN = "unknown"

# Core Interfaces

class IIntentDetector(ABC):
    """Interface for detecting user intent"""
    
    @abstractmethod
    def detect_intent(self, message: str, context: Optional[Dict] = None) -> Tuple[Intent, float]:
        """
        Detect intent from message
        Returns: (Intent, confidence_score)
        """
        pass
    
    @abstractmethod
    def get_intent_keywords(self) -> Dict[Intent, List[str]]:
        """Get keywords that trigger each intent"""
        pass
    
    @abstractmethod
    def requires_context(self, intent: Intent) -> bool:
        """Check if intent requires conversation context"""
        pass

class ILanguageDetector(ABC):
    """Interface for detecting language"""
    
    @abstractmethod
    def detect_language(self, message: str) -> Tuple[str, float]:
        """
        Detect language of message
        Returns: (language_code, confidence)
        """
        pass
    
    @abstractmethod
    def get_supported_languages(self) -> List[str]:
        """Get list of supported language codes"""
        pass

class IConversationManager(ABC):
    """Interface for managing conversation flow"""
    
    @abstractmethod
    def should_remember_context(self, message: str) -> bool:
        """Determine if context should be remembered"""
        pass
    
    @abstractmethod
    def extract_entities(self, message: str) -> Dict[str, Any]:
        """Extract named entities from message"""
        pass
    
    @abstractmethod
    def generate_followup_questions(self, context: Dict) -> List[str]:
        """Generate appropriate follow-up questions"""
        pass
    
    @abstractmethod
    def handle_conversation_state(self, state: str, message: str) -> str:
        """Handle conversation based on current state"""
        pass

class IResponseGenerator(ABC):
    """Interface for generating responses"""
    
    @abstractmethod
    def generate_response(self, intent: Intent, context: Dict) -> str:
        """Generate response based on intent and context"""
        pass
    
    @abstractmethod
    def add_personality(self, response: str, personality: Dict) -> str:
        """Add personality traits to response"""
        pass
    
    @abstractmethod
    def localize_response(self, response: str, language: str) -> str:
        """Localize response to target language"""
        pass

class ISentimentAnalyzer(ABC):
    """Interface for analyzing sentiment"""
    
    @abstractmethod
    def analyze_sentiment(self, message: str) -> Dict[str, float]:
        """
        Analyze sentiment of message
        Returns: {"positive": 0.8, "negative": 0.1, "neutral": 0.1}
        """
        pass
    
    @abstractmethod
    def detect_urgency(self, message: str) -> float:
        """Detect urgency level (0-1)"""
        pass
    
    @abstractmethod
    def detect_frustration(self, messages: List[str]) -> float:
        """Detect frustration from conversation history"""
        pass

class IKnowledgeBase(ABC):
    """Interface for knowledge base access"""
    
    @abstractmethod
    def search_knowledge(self, query: str, category: Optional[str] = None) -> List[Dict]:
        """Search knowledge base"""
        pass
    
    @abstractmethod
    def get_faq_answer(self, question: str) -> Optional[str]:
        """Get answer from FAQ"""
        pass
    
    @abstractmethod
    def update_knowledge(self, key: str, value: Any) -> bool:
        """Update knowledge base"""
        pass

# Budtender-specific implementations

class BudtenderIntentDetector(IIntentDetector):
    """Cannabis budtender intent detection"""
    
    def __init__(self, llm_function):
        self.llm = llm_function
        self.intent_keywords = {
            Intent.GREETING: ["hello", "hi", "hey", "sup", "what's up"],
            Intent.PRODUCT_SEARCH: ["looking for", "need", "want", "show me", "do you have"],
            Intent.RECOMMENDATION: ["recommend", "suggest", "what's good", "help me choose"],
            Intent.INFORMATION: ["what is", "tell me about", "explain", "how does"],
            Intent.MEDICAL_CONSULTATION: ["pain", "anxiety", "insomnia", "medical", "condition"],
            Intent.CHECKOUT: ["buy", "purchase", "checkout", "order"],
            Intent.COMPLAINT: ["problem", "issue", "wrong", "bad", "complaint"],
            Intent.SMALL_TALK: ["how are you", "what's your name", "weather"],
        }
    
    def detect_intent(self, message: str, context: Optional[Dict] = None) -> Tuple[Intent, float]:
        """Detect intent with cannabis context"""
        
        message_lower = message.lower()
        
        # Quick keyword matching first
        for intent, keywords in self.intent_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                # Use LLM to confirm and get confidence
                prompt = f"""As a cannabis budtender, classify this customer message intent:
                Message: "{message}"
                
                Possible intents:
                - greeting: Customer is greeting
                - product_search: Looking for specific products
                - recommendation: Wants suggestions
                - information: Asking about cannabis info
                - medical_consultation: Medical/health related
                - checkout: Ready to purchase
                - complaint: Has an issue
                - small_talk: Casual conversation
                
                Respond with: intent_name|confidence (e.g., "product_search|0.95")
                """
                
                response = self.llm(prompt, max_tokens=20)
                result = response.get('choices', [{}])[0].get('text', 'unknown|0.5')
                
                try:
                    intent_str, confidence_str = result.strip().split('|')
                    return Intent(intent_str.strip()), float(confidence_str)
                except:
                    return intent, 0.8  # Fallback to keyword match
        
        return Intent.UNKNOWN, 0.5
    
    def get_intent_keywords(self) -> Dict[Intent, List[str]]:
        """Get cannabis-specific intent keywords"""
        return self.intent_keywords
    
    def requires_context(self, intent: Intent) -> bool:
        """Check if intent needs context"""
        context_required = [
            Intent.RECOMMENDATION,
            Intent.MEDICAL_CONSULTATION,
            Intent.CHECKOUT
        ]
        return intent in context_required

class BudtenderLanguageDetector(ILanguageDetector):
    """Language detection for cannabis context"""
    
    def __init__(self, llm_function):
        self.llm = llm_function
        self.supported = ["en", "es", "fr", "zh", "pt"]
    
    def detect_language(self, message: str) -> Tuple[str, float]:
        """Detect language with cannabis terminology awareness"""
        
        # Quick detection for obvious cases
        if any(word in message.lower() for word in ["hola", "como", "estas", "quiero"]):
            return "es", 0.9
        if any(word in message.lower() for word in ["bonjour", "cherche", "acheter"]):
            return "fr", 0.9
        
        # Use LLM for complex detection
        prompt = f"""Detect the language of this message (cannabis context):
        Message: "{message}"
        
        Consider cannabis slang in different languages.
        Respond with: language_code|confidence (e.g., "en|0.95")
        Codes: en=English, es=Spanish, fr=French, zh=Chinese, pt=Portuguese
        """
        
        response = self.llm(prompt, max_tokens=10)
        result = response.get('choices', [{}])[0].get('text', 'en|0.7')
        
        try:
            lang, conf = result.strip().split('|')
            return lang.strip(), float(conf)
        except:
            return "en", 0.7
    
    def get_supported_languages(self) -> List[str]:
        return self.supported

class BudtenderConversationManager(IConversationManager):
    """Cannabis-specific conversation management"""
    
    def __init__(self, llm_function):
        self.llm = llm_function
    
    def should_remember_context(self, message: str) -> bool:
        """Determine if cannabis context should be remembered"""
        remember_triggers = [
            "i usually", "last time", "before", "again",
            "my favorite", "i prefer", "allergic", "medical"
        ]
        return any(trigger in message.lower() for trigger in remember_triggers)
    
    def extract_entities(self, message: str) -> Dict[str, Any]:
        """Extract cannabis-related entities"""
        entities = {
            "strains": [],
            "products": [],
            "effects": [],
            "conditions": [],
            "quantities": []
        }
        
        # Extract strain names
        strain_keywords = ["kush", "haze", "dream", "cookies", "gelato"]
        for keyword in strain_keywords:
            if keyword in message.lower():
                entities["strains"].append(keyword)
        
        # Extract effects
        effect_keywords = ["relaxing", "energizing", "creative", "focus", "sleep"]
        for keyword in effect_keywords:
            if keyword in message.lower():
                entities["effects"].append(keyword)
        
        # Extract quantities
        import re
        quantity_patterns = [
            r'\d+\s*(?:by|x)\s*\d+(?:\.\d+)?g',  # 2 by 1g, 3x0.5g
            r'\d+(?:\.\d+)?g',  # 3.5g, 14g
            r'\d+/\d+\s*(?:oz|ounce)',  # 1/2 oz
        ]
        for pattern in quantity_patterns:
            matches = re.findall(pattern, message.lower())
            entities["quantities"].extend(matches)
        
        return entities
    
    def generate_followup_questions(self, context: Dict) -> List[str]:
        """Generate cannabis-specific follow-ups"""
        
        intent = context.get("intent", Intent.UNKNOWN)
        
        followups = {
            Intent.PRODUCT_SEARCH: [
                "What effects are you looking for?",
                "Do you prefer Sativa, Indica, or Hybrid?",
                "What's your tolerance level?"
            ],
            Intent.RECOMMENDATION: [
                "Are you using this for daytime or nighttime?",
                "Any specific effects you want to achieve?",
                "What's your experience level with cannabis?"
            ],
            Intent.MEDICAL_CONSULTATION: [
                "What symptoms are you trying to address?",
                "Do you prefer high CBD options?",
                "Have you used cannabis medically before?"
            ]
        }
        
        return followups.get(intent, ["How else can I help you?"])
    
    def handle_conversation_state(self, state: str, message: str) -> str:
        """Handle conversation based on state"""
        
        states = {
            "greeting": "Welcome! What can I help you find today?",
            "searching": "Let me search our inventory for you...",
            "recommending": "Based on what you've told me, I'd suggest...",
            "educating": "Let me explain how this works...",
            "closing": "Thanks for visiting! Enjoy your products!"
        }
        
        return states.get(state, "How can I assist you?")

class BudtenderResponseGenerator(IResponseGenerator):
    """Cannabis budtender response generation"""
    
    def __init__(self, llm_function):
        self.llm = llm_function
    
    def generate_response(self, intent: Intent, context: Dict) -> str:
        """Generate cannabis-appropriate response"""
        
        templates = {
            Intent.GREETING: "Hey there! Welcome to our dispensary. What brings you in today?",
            Intent.PRODUCT_SEARCH: "Let me find those products for you...",
            Intent.RECOMMENDATION: "Based on what you're looking for, I'd recommend...",
            Intent.INFORMATION: "Great question! Let me explain...",
            Intent.MEDICAL_CONSULTATION: "I understand you're looking for relief. Let me show you some options...",
            Intent.CHECKOUT: "Excellent choices! Let's get you checked out...",
            Intent.COMPLAINT: "I'm sorry to hear that. Let me help resolve this...",
            Intent.SMALL_TALK: "I'm doing great! Always happy to help with cannabis questions!"
        }
        
        base_response = templates.get(intent, "How can I help you?")
        
        # Enhance with context
        if context.get("products"):
            base_response += f"\n\nI found {len(context['products'])} products for you."
        
        return base_response
    
    def add_personality(self, response: str, personality: Dict) -> str:
        """Add budtender personality"""
        
        style = personality.get("style", "friendly")
        
        if style == "enthusiastic":
            response = response.replace(".", "! 🌿")
            response = "Awesome! " + response
        elif style == "professional":
            response = response.replace("Hey", "Hello")
            response = response.replace("stuff", "products")
        elif style == "casual":
            response = response.replace("Hello", "Yo")
            response += " Feel me?"
        
        return response
    
    def localize_response(self, response: str, language: str) -> str:
        """Localize cannabis responses"""
        
        if language == "es":
            # Spanish cannabis terms
            response = response.replace("dispensary", "dispensario")
            response = response.replace("strain", "cepa")
            response = response.replace("high", "colocado")
        elif language == "fr":
            # French cannabis terms
            response = response.replace("dispensary", "dispensaire")
            response = response.replace("strain", "variété")
        
        return response

# AI Behavior Orchestrator

class AIBehaviorOrchestrator:
    """Orchestrates all AI behaviors based on role"""
    
    def __init__(self, role: str, llm_function, db_pool):
        self.role = role
        self.llm = llm_function
        self.db_pool = db_pool
        
        # Initialize role-specific implementations
        if role == "budtender":
            self.intent_detector = BudtenderIntentDetector(llm_function)
            self.language_detector = BudtenderLanguageDetector(llm_function)
            self.conversation_manager = BudtenderConversationManager(llm_function)
            self.response_generator = BudtenderResponseGenerator(llm_function)
        # Add other roles here (medical, recreational, etc.)
    
    async def process_message(self, message: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Process message through all AI behaviors"""
        
        result = {}
        
        # 1. Detect language
        language, lang_confidence = self.language_detector.detect_language(message)
        result["language"] = language
        result["language_confidence"] = lang_confidence
        
        # 2. Detect intent
        intent, intent_confidence = self.intent_detector.detect_intent(message, context)
        result["intent"] = intent.value
        result["intent_confidence"] = intent_confidence
        
        # 3. Extract entities
        entities = self.conversation_manager.extract_entities(message)
        result["entities"] = entities
        
        # 4. Determine if context should be remembered
        remember = self.conversation_manager.should_remember_context(message)
        result["remember_context"] = remember
        
        # 5. Generate follow-up questions
        followups = self.conversation_manager.generate_followup_questions({"intent": intent})
        result["followup_questions"] = followups
        
        # 6. Generate base response
        response = self.response_generator.generate_response(intent, entities)
        
        # 7. Add personality
        personality = context.get("personality", {"style": "friendly"}) if context else {"style": "friendly"}
        response = self.response_generator.add_personality(response, personality)
        
        # 8. Localize if needed
        if language != "en":
            response = self.response_generator.localize_response(response, language)
        
        result["response"] = response
        result["role"] = self.role
        
        return result