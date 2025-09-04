#!/usr/bin/env python3
"""
Multilingual Handler Integration
Shows how language detection and handling flows through the system
"""

import logging
from typing import Dict, Optional
from services.language_manager import language_manager, Language, LanguageContext
from services.model_manager import ModelManager, ModelType

logger = logging.getLogger(__name__)

class MultilingualSmartEngine:
    """
    Enhanced SmartAIEngine with full multilingual support
    """
    
    def __init__(self, model_manager: ModelManager):
        self.model_manager = model_manager
        self.language_manager = language_manager
    
    async def process_multilingual_message(self,
                                          customer_id: str,
                                          session_id: str,
                                          message: str,
                                          api_language: Optional[str] = None) -> Dict:
        """
        Process message with full language support
        
        Flow:
        1. Detect/determine language
        2. Adapt AI prompts to target language
        3. Search products (language-agnostic)
        4. Format response in target language
        """
        
        # Step 1: Determine language context
        lang_context = self.language_manager.process_request(
            message=message,
            api_language=api_language,
            customer_id=customer_id
        )
        
        target_language = lang_context.get_effective_language()
        logger.info(f"Processing in {target_language.value} for customer {customer_id}")
        
        # Step 2: Generate language-aware AI prompt
        ai_prompt = self._build_language_aware_prompt(message, target_language)
        
        # Step 3: Get AI response in target language
        ai_response = await self._get_ai_response(ai_prompt, target_language)
        
        # Step 4: Search products (this part remains language-agnostic)
        products = await self._search_products_for_language(message, target_language)
        
        # Step 5: Format response with translations
        response = self._format_multilingual_response(
            ai_response=ai_response,
            products=products,
            language=target_language,
            session_id=session_id
        )
        
        return response
    
    def _build_language_aware_prompt(self, message: str, language: Language) -> str:
        """Build AI prompt in target language"""
        
        # Get language-specific system prompt
        system_prompt = self.language_manager.get_ai_prompt_prefix(language)
        
        # Language-specific instructions
        language_instructions = {
            Language.SPANISH: "Responde siempre en español. Sé amigable y profesional.",
            Language.FRENCH: "Répondez toujours en français. Soyez amical et professionnel.",
            Language.CHINESE: "请始终用中文回答。要友好和专业。",
            Language.JAPANESE: "常に日本語で答えてください。親切でプロフェッショナルに。",
            Language.KOREAN: "항상 한국어로 대답하세요. 친절하고 전문적으로.",
            Language.PORTUGUESE: "Responda sempre em português. Seja amigável e profissional.",
            Language.GERMAN: "Antworten Sie immer auf Deutsch. Seien Sie freundlich und professionell.",
            Language.ITALIAN: "Rispondi sempre in italiano. Sii amichevole e professionale.",
            Language.RUSSIAN: "Всегда отвечайте на русском языке. Будьте дружелюбны и профессиональны.",
            Language.ENGLISH: "Respond in clear, friendly English.",
        }
        
        instruction = language_instructions.get(language, language_instructions[Language.ENGLISH])
        
        # Build complete prompt
        if language == Language.ENGLISH:
            prompt = f"""[INST] {system_prompt}
Customer says: {message}
{instruction}
Respond naturally as a knowledgeable budtender. [/INST]"""
        else:
            # For non-English, include translation hint
            prompt = f"""[INST] {system_prompt}
Customer says: {message}
{instruction}
Language: {language.value}
Respond naturally as a knowledgeable budtender in {language.name}. [/INST]"""
        
        return prompt
    
    async def _get_ai_response(self, prompt: str, language: Language) -> str:
        """Get AI response in target language"""
        
        try:
            # Adjust temperature based on language
            # Higher for creative languages, lower for precise ones
            temperature = 0.7
            if language in [Language.SPANISH, Language.ITALIAN, Language.PORTUGUESE]:
                temperature = 0.8  # More expressive languages
            elif language in [Language.JAPANESE, Language.GERMAN]:
                temperature = 0.6  # More formal languages
            
            response = await self.model_manager.generate(
                ModelType.LLAMA2_7B,
                prompt,
                temperature=temperature,
                max_tokens=200
            )
            
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"AI response generation failed: {e}")
            # Fallback to template
            return self.language_manager.templates.get_template(
                "GREETINGS", language
            )
    
    async def _search_products_for_language(self, message: str, language: Language) -> list:
        """
        Search products (language-agnostic but can translate queries)
        """
        
        # Translate common product terms if needed
        query_translations = {
            Language.SPANISH: {
                "flor": "flower",
                "comestibles": "edibles",
                "vaporizadores": "vapes",
                "extractos": "extracts",
            },
            Language.FRENCH: {
                "fleur": "flower",
                "comestibles": "edibles",
                "vaporisateurs": "vapes",
                "extraits": "extracts",
            },
            Language.CHINESE: {
                "花": "flower",
                "食用": "edibles",
                "电子烟": "vapes",
                "提取物": "extracts",
            },
        }
        
        # Translate query if needed
        search_query = message.lower()
        if language in query_translations:
            for local_term, english_term in query_translations[language].items():
                if local_term in search_query:
                    search_query = search_query.replace(local_term, english_term)
        
        # Perform search (mock for example)
        # In real implementation, this would call the search API
        products = []  # Would be actual search results
        
        return products
    
    def _format_multilingual_response(self,
                                     ai_response: str,
                                     products: list,
                                     language: Language,
                                     session_id: str) -> Dict:
        """Format response with language-appropriate elements"""
        
        # Get translated quick replies
        quick_replies = self.language_manager.templates.QUICK_REPLIES.get(
            language,
            self.language_manager.templates.QUICK_REPLIES[Language.ENGLISH]
        )
        
        # Format product message if products found
        if products:
            product_message = self.language_manager.templates.get_template(
                "PRODUCT_FOUND",
                language,
                count=len(products)
            )
            full_message = f"{ai_response}\n\n{product_message}"
        else:
            full_message = ai_response
        
        # Translate product categories in results
        for product in products:
            if 'category' in product:
                product['category_translated'] = self.language_manager.translate_product_category(
                    product['category'],
                    language
                )
        
        return {
            "message": full_message,
            "products": products,
            "quick_replies": quick_replies,
            "confidence": 0.95,
            "session_id": session_id,
            "language": language.value,
            "stage": "multilingual_response"
        }


class LanguageFlowExample:
    """
    Example showing complete language flow
    """
    
    @staticmethod
    async def demonstrate_language_flow():
        """Show how language detection works in practice"""
        
        examples = [
            # Example 1: Spanish auto-detection
            {
                "customer_id": "customer_001",
                "message": "Hola, quiero ver productos de flores",
                "api_language": None,
                "expected_language": Language.SPANISH,
                "description": "Spanish auto-detected from message"
            },
            
            # Example 2: API language override
            {
                "customer_id": "customer_002",
                "message": "Show me flower products",  # English message
                "api_language": "fr",  # But API requests French
                "expected_language": Language.FRENCH,
                "description": "API language overrides detection"
            },
            
            # Example 3: User preference remembered
            {
                "customer_id": "customer_001",  # Same customer as example 1
                "message": "show me edibles",  # English message
                "api_language": None,
                "expected_language": Language.SPANISH,  # Remembered preference
                "description": "User preference remembered from previous interaction"
            },
            
            # Example 4: Character-based detection (Chinese)
            {
                "customer_id": "customer_003",
                "message": "我想买大麻花",
                "api_language": None,
                "expected_language": Language.CHINESE,
                "description": "Chinese detected from characters"
            },
        ]
        
        for example in examples:
            print(f"\n{example['description']}")
            print(f"  Message: {example['message']}")
            print(f"  API Language: {example['api_language']}")
            print(f"  Expected: {example['expected_language'].value}")
            
            # Process through language manager
            context = language_manager.process_request(
                message=example['message'],
                api_language=example['api_language'],
                customer_id=example['customer_id']
            )
            
            actual_language = context.get_effective_language()
            print(f"  Actual: {actual_language.value}")
            print(f"  ✅ PASS" if actual_language == example['expected_language'] else f"  ❌ FAIL")


# Database Considerations for Production
class MultilingualDatabase:
    """
    Database schema considerations for multilingual support
    """
    
    @staticmethod
    def get_schema_additions():
        """SQL schema additions for multilingual support"""
        
        return """
        -- Add language preference to customers table
        ALTER TABLE customers ADD COLUMN IF NOT EXISTS 
            preferred_language VARCHAR(2) DEFAULT 'en';
        
        -- Add multilingual product descriptions
        ALTER TABLE products ADD COLUMN IF NOT EXISTS 
            name_translations JSONB DEFAULT '{}';
        -- Example: {"es": "Flor de Pink Kush", "fr": "Fleur de Pink Kush"}
        
        ALTER TABLE products ADD COLUMN IF NOT EXISTS 
            description_translations JSONB DEFAULT '{}';
        
        -- Track language usage for analytics
        CREATE TABLE IF NOT EXISTS language_usage (
            id SERIAL PRIMARY KEY,
            customer_id VARCHAR(255),
            language_code VARCHAR(2),
            detection_method VARCHAR(50), -- 'api', 'auto', 'preference'
            confidence FLOAT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Index for fast language preference lookup
        CREATE INDEX IF NOT EXISTS idx_customer_language 
            ON customers(customer_id, preferred_language);
        """