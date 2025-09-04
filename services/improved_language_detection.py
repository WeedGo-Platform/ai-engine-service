"""
Improved Language Detection Service
Handles context-aware language detection with better accuracy
"""
import logging
from typing import Optional, Dict, List
from langdetect import detect, detect_langs, LangDetectException
import re

logger = logging.getLogger(__name__)

class ImprovedLanguageDetection:
    """Context-aware language detection service"""
    
    def __init__(self):
        # Common greetings by language
        self.greetings = {
            'es': [
                'hola', 'buenos días', 'buenas tardes', 'buenas noches', 
                'qué tal', 'cómo estás', 'saludos', 'buenas'
            ],
            'fr': [
                'bonjour', 'bonsoir', 'salut', 'coucou', 
                'bonne journée', 'comment allez-vous'
            ],
            'zh': [
                '你好', '您好', '早上好', '晚上好', '下午好',
                '嗨', '喂', '哈罗'
            ],
            'pt': [
                'olá', 'oi', 'bom dia', 'boa tarde', 'boa noite',
                'como vai', 'tudo bem'
            ],
            'ar': [
                'مرحبا', 'أهلا', 'السلام عليكم', 'صباح الخير',
                'مساء الخير', 'كيف حالك'
            ]
        }
        
        # Common Spanish patterns that langdetect might miss
        self.spanish_patterns = [
            r'\b(yo|tú|él|ella|nosotros|ustedes|ellos|ellas)\b',
            r'\b(soy|eres|es|somos|son)\b',
            r'\b(estoy|estás|está|estamos|están)\b',
            r'\b(tengo|tienes|tiene|tenemos|tienen)\b',
            r'\b(quiero|quieres|quiere|queremos|quieren)\b',
            r'\b(puedo|puedes|puede|podemos|pueden)\b',
            r'\b(me|te|le|nos|les|se)\b',
            r'\b(mi|tu|su|nuestro|vuestro)\b',
            r'\b(qué|cómo|dónde|cuándo|por qué|cuál)\b',
            r'\b(para|por|con|sin|sobre|entre)\b'
        ]
        
        # Session language memory (in production, use Redis)
        self.session_languages = {}
    
    def detect_language(self, 
                        message: str, 
                        session_id: Optional[str] = None,
                        previous_language: Optional[str] = None) -> tuple[str, float]:
        """
        Detect language with context awareness
        
        Returns:
            tuple: (detected_language, confidence)
        """
        message_lower = message.lower().strip()
        
        # 1. Check session memory first
        if session_id and session_id in self.session_languages:
            session_lang = self.session_languages[session_id]
            logger.info(f"Using session language: {session_lang}")
            return session_lang, 0.95
        
        # 2. Check for greetings (highest confidence)
        for lang, greetings in self.greetings.items():
            if any(greeting in message_lower for greeting in greetings):
                logger.info(f"Detected {lang} from greeting: {message}")
                if session_id:
                    self.session_languages[session_id] = lang
                return lang, 1.0
        
        # 3. Check Spanish patterns (common misdetection)
        spanish_score = sum(1 for pattern in self.spanish_patterns 
                          if re.search(pattern, message_lower, re.IGNORECASE))
        if spanish_score >= 2:  # At least 2 Spanish patterns
            logger.info(f"Detected Spanish from patterns (score: {spanish_score}): {message}")
            if session_id:
                self.session_languages[session_id] = 'es'
            return 'es', 0.9
        
        # 4. Use langdetect with confidence scoring
        try:
            # Get probabilities for all detected languages
            langs = detect_langs(message)
            
            if langs:
                best_lang = langs[0]
                lang_code = best_lang.lang
                confidence = best_lang.prob
                
                # Map language codes
                if lang_code in ['zh-cn', 'zh-tw']:
                    lang_code = 'zh'
                elif lang_code == 'cy':  # Welsh often misdetected for Spanish
                    # Double-check if it might be Spanish
                    if spanish_score >= 1 or any(word in message_lower for word in ['si', 'no', 'que', 'es']):
                        lang_code = 'es'
                        confidence = 0.7
                elif lang_code == 'it' and spanish_score >= 1:
                    # Italian often confused with Spanish
                    lang_code = 'es'
                    confidence = 0.7
                
                # Only accept detection if confidence is reasonable
                if confidence > 0.5:
                    logger.info(f"Langdetect: {lang_code} (confidence: {confidence:.2f})")
                    if session_id and confidence > 0.7:
                        self.session_languages[session_id] = lang_code
                    return lang_code, confidence
                    
        except LangDetectException as e:
            logger.warning(f"Language detection failed: {e}")
        
        # 5. Fall back to previous language or English
        if previous_language and previous_language != 'en':
            logger.info(f"Falling back to previous language: {previous_language}")
            return previous_language, 0.6
        
        return 'en', 0.5
    
    def update_session_language(self, session_id: str, language: str):
        """Update the session's detected language"""
        self.session_languages[session_id] = language
        logger.info(f"Updated session {session_id} language to: {language}")
    
    def get_session_language(self, session_id: str) -> Optional[str]:
        """Get the stored language for a session"""
        return self.session_languages.get(session_id)