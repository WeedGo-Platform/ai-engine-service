#!/usr/bin/env python3
"""
Language Detection and Management System
Handles multilingual support for the AI budtender
"""

import logging
import re
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class Language(Enum):
    """Supported languages"""
    ENGLISH = "en"
    SPANISH = "es"
    FRENCH = "fr"
    CHINESE = "zh"
    JAPANESE = "ja"
    KOREAN = "ko"
    PORTUGUESE = "pt"
    GERMAN = "de"
    ITALIAN = "it"
    RUSSIAN = "ru"
    
    @classmethod
    def from_code(cls, code: str) -> 'Language':
        """Get language from ISO code"""
        code = code.lower()[:2]  # Take first 2 chars (en-US -> en)
        for lang in cls:
            if lang.value == code:
                return lang
        return cls.ENGLISH  # Default to English

@dataclass
class LanguageContext:
    """Context for language handling"""
    detected_language: Language
    confidence: float
    api_language: Optional[Language] = None
    user_preference: Optional[Language] = None
    
    def get_effective_language(self) -> Language:
        """Get the language to use based on priority"""
        # Priority: API request > User preference > Detected
        if self.api_language:
            return self.api_language
        if self.user_preference:
            return self.user_preference
        return self.detected_language


class LanguageDetector:
    """Detects language from text"""
    
    # Character patterns for language detection
    LANGUAGE_PATTERNS = {
        Language.CHINESE: re.compile(r'[\u4e00-\u9fff]+'),
        Language.JAPANESE: re.compile(r'[\u3040-\u309f\u30a0-\u30ff]+'),
        Language.KOREAN: re.compile(r'[\uac00-\ud7af]+'),
        Language.RUSSIAN: re.compile(r'[\u0400-\u04ff]+'),
    }
    
    # Common words/phrases for language detection
    LANGUAGE_INDICATORS = {
        Language.ENGLISH: ['the', 'is', 'what', 'how', 'want', 'need', 'show', 'hello', 'hi'],
        Language.SPANISH: ['hola', 'quiero', 'necesito', 'por favor', 'gracias', 'qué', 'cómo', 'muéstrame'],
        Language.FRENCH: ['bonjour', 'je veux', 'merci', 'comment', 'quoi', 's\'il vous plaît', 'montrez-moi'],
        Language.PORTUGUESE: ['olá', 'eu quero', 'obrigado', 'por favor', 'como', 'o que', 'mostre-me'],
        Language.GERMAN: ['hallo', 'ich möchte', 'bitte', 'danke', 'was', 'wie', 'zeigen sie mir'],
        Language.ITALIAN: ['ciao', 'voglio', 'grazie', 'per favore', 'cosa', 'come', 'mostrami'],
    }
    
    @classmethod
    def detect_language(cls, text: str) -> Tuple[Language, float]:
        """
        Detect language from text
        Returns: (Language, confidence_score)
        """
        text_lower = text.lower()
        
        # First check character-based patterns (very reliable)
        for lang, pattern in cls.LANGUAGE_PATTERNS.items():
            if pattern.search(text):
                return lang, 0.95  # High confidence for character-based detection
        
        # Then check word indicators
        language_scores = {}
        for lang, indicators in cls.LANGUAGE_INDICATORS.items():
            score = sum(1 for word in indicators if word in text_lower)
            if score > 0:
                language_scores[lang] = score
        
        if language_scores:
            # Get language with highest score
            best_lang = max(language_scores, key=language_scores.get)
            max_score = language_scores[best_lang]
            # Calculate confidence based on number of matches
            confidence = min(0.9, max_score * 0.2)
            return best_lang, confidence
        
        # Default to English with low confidence
        return Language.ENGLISH, 0.3


class TranslationTemplates:
    """Translation templates for common responses"""
    
    GREETINGS = {
        Language.ENGLISH: "Welcome to our dispensary! 🌿 How can I help you today?",
        Language.SPANISH: "¡Bienvenido a nuestro dispensario! 🌿 ¿Cómo puedo ayudarte hoy?",
        Language.FRENCH: "Bienvenue dans notre dispensaire! 🌿 Comment puis-je vous aider aujourd'hui?",
        Language.CHINESE: "欢迎来到我们的药房！🌿 今天我能为您做什么？",
        Language.JAPANESE: "私たちのディスペンサリーへようこそ！🌿 今日はどのようにお手伝いできますか？",
        Language.KOREAN: "우리 약국에 오신 것을 환영합니다! 🌿 오늘 어떻게 도와드릴까요?",
        Language.PORTUGUESE: "Bem-vindo ao nosso dispensário! 🌿 Como posso ajudá-lo hoje?",
        Language.GERMAN: "Willkommen in unserer Apotheke! 🌿 Wie kann ich Ihnen heute helfen?",
        Language.ITALIAN: "Benvenuto nel nostro dispensario! 🌿 Come posso aiutarti oggi?",
        Language.RUSSIAN: "Добро пожаловать в наш диспансер! 🌿 Чем я могу помочь вам сегодня?",
    }
    
    PRODUCT_FOUND = {
        Language.ENGLISH: "I found {count} products for you:",
        Language.SPANISH: "Encontré {count} productos para ti:",
        Language.FRENCH: "J'ai trouvé {count} produits pour vous:",
        Language.CHINESE: "我为您找到了{count}个产品：",
        Language.JAPANESE: "あなたのために{count}個の製品を見つけました：",
        Language.KOREAN: "당신을 위해 {count}개의 제품을 찾았습니다:",
        Language.PORTUGUESE: "Encontrei {count} produtos para você:",
        Language.GERMAN: "Ich habe {count} Produkte für Sie gefunden:",
        Language.ITALIAN: "Ho trovato {count} prodotti per te:",
        Language.RUSSIAN: "Я нашел {count} продуктов для вас:",
    }
    
    NO_PRODUCTS = {
        Language.ENGLISH: "Sorry, I couldn't find any products matching your request.",
        Language.SPANISH: "Lo siento, no pude encontrar productos que coincidan con tu solicitud.",
        Language.FRENCH: "Désolé, je n'ai trouvé aucun produit correspondant à votre demande.",
        Language.CHINESE: "抱歉，我找不到符合您要求的产品。",
        Language.JAPANESE: "申し訳ありませんが、ご要望に合う製品が見つかりませんでした。",
        Language.KOREAN: "죄송합니다. 요청하신 제품을 찾을 수 없습니다.",
        Language.PORTUGUESE: "Desculpe, não consegui encontrar produtos que correspondam ao seu pedido.",
        Language.GERMAN: "Entschuldigung, ich konnte keine Produkte finden, die Ihrer Anfrage entsprechen.",
        Language.ITALIAN: "Mi dispiace, non sono riuscito a trovare prodotti che corrispondono alla tua richiesta.",
        Language.RUSSIAN: "Извините, я не смог найти продукты, соответствующие вашему запросу.",
    }
    
    CART_ADDED = {
        Language.ENGLISH: "Added {product} to your cart!",
        Language.SPANISH: "¡Añadido {product} a tu carrito!",
        Language.FRENCH: "Ajouté {product} à votre panier!",
        Language.CHINESE: "已将{product}添加到您的购物车！",
        Language.JAPANESE: "{product}をカートに追加しました！",
        Language.KOREAN: "{product}을(를) 장바구니에 추가했습니다!",
        Language.PORTUGUESE: "Adicionado {product} ao seu carrinho!",
        Language.GERMAN: "{product} wurde Ihrem Warenkorb hinzugefügt!",
        Language.ITALIAN: "Aggiunto {product} al tuo carrello!",
        Language.RUSSIAN: "Добавлено {product} в вашу корзину!",
    }
    
    QUICK_REPLIES = {
        Language.ENGLISH: ["Show more", "Add to cart", "Different category"],
        Language.SPANISH: ["Mostrar más", "Añadir al carrito", "Categoría diferente"],
        Language.FRENCH: ["Voir plus", "Ajouter au panier", "Catégorie différente"],
        Language.CHINESE: ["显示更多", "加入购物车", "不同类别"],
        Language.JAPANESE: ["もっと見る", "カートに追加", "別のカテゴリー"],
        Language.KOREAN: ["더 보기", "장바구니에 추가", "다른 카테고리"],
        Language.PORTUGUESE: ["Mostrar mais", "Adicionar ao carrinho", "Categoria diferente"],
        Language.GERMAN: ["Mehr anzeigen", "In den Warenkorb", "Andere Kategorie"],
        Language.ITALIAN: ["Mostra di più", "Aggiungi al carrello", "Categoria diversa"],
        Language.RUSSIAN: ["Показать больше", "Добавить в корзину", "Другая категория"],
    }
    
    @classmethod
    def get_template(cls, template_type: str, language: Language, **kwargs) -> str:
        """Get translated template with parameters"""
        templates = getattr(cls, template_type, {})
        template = templates.get(language, templates.get(Language.ENGLISH, ""))
        
        # Format with provided parameters
        try:
            return template.format(**kwargs)
        except:
            return template


class LanguageManager:
    """Main language management system"""
    
    def __init__(self):
        self.detector = LanguageDetector()
        self.templates = TranslationTemplates()
        self.user_language_preferences = {}  # customer_id -> Language
    
    def process_request(self, 
                        message: str, 
                        api_language: Optional[str] = None,
                        customer_id: Optional[str] = None) -> LanguageContext:
        """
        Process language for a request
        
        Priority:
        1. API request language (if specified)
        2. User saved preference (if exists)
        3. Auto-detected from message
        """
        
        # Detect language from message
        detected_lang, confidence = self.detector.detect_language(message)
        
        context = LanguageContext(
            detected_language=detected_lang,
            confidence=confidence
        )
        
        # Check API language
        if api_language:
            context.api_language = Language.from_code(api_language)
        
        # Check user preference
        if customer_id and customer_id in self.user_language_preferences:
            context.user_preference = self.user_language_preferences[customer_id]
        
        # If high confidence detection and no API language, save as preference
        if confidence > 0.8 and customer_id and not api_language:
            self.user_language_preferences[customer_id] = detected_lang
        
        logger.info(f"Language context: Effective={context.get_effective_language().value}, "
                   f"Detected={detected_lang.value} ({confidence:.2f}), "
                   f"API={api_language}, Customer={customer_id}")
        
        return context
    
    def get_ai_prompt_prefix(self, language: Language) -> str:
        """Get language-specific prompt prefix for AI"""
        
        prompts = {
            Language.ENGLISH: "You are a helpful cannabis dispensary assistant.",
            Language.SPANISH: "Eres un asistente útil de dispensario de cannabis. Responde en español.",
            Language.FRENCH: "Vous êtes un assistant utile de dispensaire de cannabis. Répondez en français.",
            Language.CHINESE: "你是一个有用的大麻药房助手。请用中文回答。",
            Language.JAPANESE: "あなたは親切な大麻薬局のアシスタントです。日本語で答えてください。",
            Language.KOREAN: "당신은 도움이 되는 대마초 약국 도우미입니다. 한국어로 대답해주세요.",
            Language.PORTUGUESE: "Você é um assistente útil de dispensário de cannabis. Responda em português.",
            Language.GERMAN: "Sie sind ein hilfreicher Cannabis-Apotheken-Assistent. Antworten Sie auf Deutsch.",
            Language.ITALIAN: "Sei un assistente utile del dispensario di cannabis. Rispondi in italiano.",
            Language.RUSSIAN: "Вы полезный помощник в диспансере каннабиса. Отвечайте на русском языке.",
        }
        
        return prompts.get(language, prompts[Language.ENGLISH])
    
    def translate_product_category(self, category: str, language: Language) -> str:
        """Translate product category names"""
        
        translations = {
            "Flower": {
                Language.SPANISH: "Flor",
                Language.FRENCH: "Fleur",
                Language.CHINESE: "花",
                Language.JAPANESE: "フラワー",
                Language.KOREAN: "꽃",
                Language.PORTUGUESE: "Flor",
                Language.GERMAN: "Blüte",
                Language.ITALIAN: "Fiore",
                Language.RUSSIAN: "Цветок",
            },
            "Edibles": {
                Language.SPANISH: "Comestibles",
                Language.FRENCH: "Comestibles",
                Language.CHINESE: "食用品",
                Language.JAPANESE: "エディブル",
                Language.KOREAN: "식용품",
                Language.PORTUGUESE: "Comestíveis",
                Language.GERMAN: "Essbare",
                Language.ITALIAN: "Commestibili",
                Language.RUSSIAN: "Съедобные",
            },
            "Vapes": {
                Language.SPANISH: "Vaporizadores",
                Language.FRENCH: "Vaporisateurs",
                Language.CHINESE: "电子烟",
                Language.JAPANESE: "ベイプ",
                Language.KOREAN: "베이프",
                Language.PORTUGUESE: "Vaporizadores",
                Language.GERMAN: "Verdampfer",
                Language.ITALIAN: "Vaporizzatori",
                Language.RUSSIAN: "Вейпы",
            },
            "Extracts": {
                Language.SPANISH: "Extractos",
                Language.FRENCH: "Extraits",
                Language.CHINESE: "提取物",
                Language.JAPANESE: "エキストラクト",
                Language.KOREAN: "추출물",
                Language.PORTUGUESE: "Extratos",
                Language.GERMAN: "Extrakte",
                Language.ITALIAN: "Estratti",
                Language.RUSSIAN: "Экстракты",
            },
        }
        
        if language == Language.ENGLISH:
            return category
        
        category_translations = translations.get(category, {})
        return category_translations.get(language, category)


# Global instance
language_manager = LanguageManager()