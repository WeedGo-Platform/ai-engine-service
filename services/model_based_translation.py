"""
Model-Based Translation Service
Uses LLMs for translation instead of placeholder code
"""
import logging
from typing import Tuple, Optional, Dict
from pathlib import Path

logger = logging.getLogger(__name__)

class ModelBasedTranslator:
    """
    Translation using the actual LLM models
    No external APIs, pure model-based translation
    """
    
    def __init__(self, llm_instance=None):
        self.llm = llm_instance
        self.translation_cache = {}
        
    def set_llm(self, llm_instance):
        """Set the LLM instance for translation"""
        self.llm = llm_instance
        
    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        context: Optional[str] = None
    ) -> Tuple[str, float]:
        """
        Translate text using the LLM model
        
        Returns: (translated_text, confidence_score)
        """
        
        # Check cache first
        cache_key = f"{source_lang}:{target_lang}:{text[:50]}"
        if cache_key in self.translation_cache:
            return self.translation_cache[cache_key], 0.95
        
        if not self.llm:
            logger.error("No LLM configured for translation")
            return text, 0.0
        
        # Build translation prompt
        lang_names = {
            "en": "English",
            "es": "Spanish", 
            "fr": "French",
            "pt": "Portuguese",
            "zh": "Chinese",
            "ar": "Arabic",
            "ja": "Japanese",
            "ko": "Korean"
        }
        
        source_name = lang_names.get(source_lang, source_lang)
        target_name = lang_names.get(target_lang, target_lang)
        
        # Create a robust translation prompt
        prompt = f"""You are a professional translator. Translate the following text from {source_name} to {target_name}.

Rules:
1. Maintain the original meaning and tone
2. Use natural, fluent {target_name}
3. Preserve any product names, brands, or technical terms
4. For cannabis-related terms, use appropriate {target_name} terminology
5. Output ONLY the translation, no explanations

{f'Context: {context}' if context else ''}

Original text ({source_name}):
{text}

Translation ({target_name}):"""
        
        try:
            # Use the model for translation
            response = self.llm(
                prompt,
                max_tokens=len(text) * 2,  # Allow for language expansion
                temperature=0.3,  # Low temperature for consistency
                echo=False
            )
            
            translated = response.get('choices', [{}])[0].get('text', '').strip()
            
            if translated and translated != text:
                # Cache the translation
                self.translation_cache[cache_key] = translated
                
                # Calculate confidence based on response
                confidence = 0.85 if len(translated) > 0 else 0.0
                
                logger.info(f"Translated '{text[:30]}...' from {source_lang} to {target_lang}")
                return translated, confidence
            else:
                logger.warning(f"Translation failed, returning original text")
                return text, 0.0
                
        except Exception as e:
            logger.error(f"Translation error: {e}")
            return text, 0.0
    
    async def translate_product_info(
        self,
        product: Dict,
        target_lang: str
    ) -> Dict:
        """Translate product information to target language"""
        
        if target_lang == "en":
            return product  # No translation needed
        
        translated_product = product.copy()
        
        # Fields to translate
        translate_fields = [
            'short_description',
            'long_description', 
            'effects',
            'flavors',
            'category',
            'sub_category'
        ]
        
        for field in translate_fields:
            if field in product and product[field]:
                if isinstance(product[field], list):
                    # Translate list items
                    translated_items = []
                    for item in product[field]:
                        translated, _ = await self.translate(item, "en", target_lang)
                        translated_items.append(translated)
                    translated_product[field] = translated_items
                else:
                    # Translate single value
                    translated, _ = await self.translate(
                        product[field], "en", target_lang
                    )
                    translated_product[field] = translated
        
        return translated_product
    
    def get_cannabis_terminology(self, term: str, target_lang: str) -> str:
        """Get cannabis-specific terminology in target language"""
        
        # Common cannabis terms translations
        terminology = {
            "es": {
                "strain": "cepa",
                "indica": "índica",
                "sativa": "sativa",
                "hybrid": "híbrida",
                "thc": "THC",
                "cbd": "CBD",
                "flower": "flor",
                "edibles": "comestibles",
                "vape": "vaporizador",
                "pre-roll": "pre-armado",
                "tincture": "tintura",
                "topical": "tópico",
                "concentrate": "concentrado",
                "relaxation": "relajación",
                "energy": "energía",
                "pain relief": "alivio del dolor",
                "sleep": "sueño",
                "focus": "concentración",
                "creativity": "creatividad"
            },
            "pt": {
                "strain": "variedade",
                "indica": "índica",
                "sativa": "sativa", 
                "hybrid": "híbrida",
                "thc": "THC",
                "cbd": "CBD",
                "flower": "flor",
                "edibles": "comestíveis",
                "vape": "vaporizador",
                "pre-roll": "pré-enrolado",
                "tincture": "tintura",
                "topical": "tópico",
                "concentrate": "concentrado",
                "relaxation": "relaxamento",
                "energy": "energia",
                "pain relief": "alívio da dor",
                "sleep": "sono",
                "focus": "foco",
                "creativity": "criatividade"
            },
            "fr": {
                "strain": "variété",
                "indica": "indica",
                "sativa": "sativa",
                "hybrid": "hybride",
                "thc": "THC",
                "cbd": "CBD",
                "flower": "fleur",
                "edibles": "comestibles",
                "vape": "vaporisateur",
                "pre-roll": "pré-roulé",
                "tincture": "teinture",
                "topical": "topique",
                "concentrate": "concentré",
                "relaxation": "relaxation",
                "energy": "énergie",
                "pain relief": "soulagement de la douleur",
                "sleep": "sommeil",
                "focus": "concentration",
                "creativity": "créativité"
            },
            "zh": {
                "strain": "品种",
                "indica": "印度大麻",
                "sativa": "苜蓿大麻",
                "hybrid": "混合品种",
                "thc": "四氢大麻酚",
                "cbd": "大麻二酚",
                "flower": "花",
                "edibles": "食用品",
                "vape": "电子烟",
                "pre-roll": "预卷",
                "tincture": "酊剂",
                "topical": "外用",
                "concentrate": "浓缩物",
                "relaxation": "放松",
                "energy": "能量",
                "pain relief": "止痛",
                "sleep": "睡眠",
                "focus": "专注",
                "creativity": "创造力"
            }
        }
        
        if target_lang in terminology and term.lower() in terminology[target_lang]:
            return terminology[target_lang][term.lower()]
        
        return term  # Return original if no translation found