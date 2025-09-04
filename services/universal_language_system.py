"""
Universal Language System
Automatically detects and handles ANY language based on available model capabilities
No hardcoded restrictions - fully dynamic and extensible
"""
import logging
import json
from typing import Dict, List, Optional, Tuple, Set, Any
from dataclasses import dataclass, field
from pathlib import Path
import re
from collections import defaultdict

logger = logging.getLogger(__name__)

@dataclass
class LanguageProfile:
    """Profile for a detected language"""
    code: str  # ISO 639-1/3 code (e.g., 'en', 'es', 'hin', 'swa')
    name: str  # English name
    native_name: str  # Native name
    script: str  # Writing system (latin, cyrillic, arabic, devanagari, etc.)
    direction: str  # ltr or rtl
    confidence: float  # Detection confidence
    detected_by: str  # Which model/method detected it
    sample_text: str  # Sample for verification

@dataclass
class ModelLanguageCapability:
    """Language capability of a specific model"""
    model_id: str
    language_code: str
    proficiency_score: float  # 0-1, how well it handles this language
    verified: bool  # Has this been tested?
    supports_generation: bool
    supports_understanding: bool
    special_instructions: Optional[str] = None  # Special prompting needed

class UniversalLanguageSystem:
    """
    Detects and routes ANY language to capable models
    No hardcoded language lists - learns from model capabilities
    """
    
    def __init__(self, model_manager=None):
        self.model_manager = model_manager
        self.language_capabilities: Dict[str, List[ModelLanguageCapability]] = defaultdict(list)
        self.detected_languages: Set[str] = set()
        self.language_profiles: Dict[str, LanguageProfile] = {}
        self.session_languages: Dict[str, str] = {}  # session_id -> language
        
        # Load comprehensive language data
        self.language_database = self._load_language_database()
        
        # Discover capabilities from models
        if model_manager:
            self._discover_model_capabilities()
    
    def _load_language_database(self) -> Dict:
        """Load comprehensive language information"""
        # This would ideally load from a file, but for now we'll include essentials
        return {
            # Major languages
            "en": {"name": "English", "native": "English", "script": "latin", "dir": "ltr"},
            "zh": {"name": "Chinese", "native": "中文", "script": "chinese", "dir": "ltr"},
            "es": {"name": "Spanish", "native": "Español", "script": "latin", "dir": "ltr"},
            "hi": {"name": "Hindi", "native": "हिन्दी", "script": "devanagari", "dir": "ltr"},
            "ar": {"name": "Arabic", "native": "العربية", "script": "arabic", "dir": "rtl"},
            "bn": {"name": "Bengali", "native": "বাংলা", "script": "bengali", "dir": "ltr"},
            "pt": {"name": "Portuguese", "native": "Português", "script": "latin", "dir": "ltr"},
            "ru": {"name": "Russian", "native": "Русский", "script": "cyrillic", "dir": "ltr"},
            "ja": {"name": "Japanese", "native": "日本語", "script": "japanese", "dir": "ltr"},
            "pa": {"name": "Punjabi", "native": "ਪੰਜਾਬੀ", "script": "gurmukhi", "dir": "ltr"},
            "de": {"name": "German", "native": "Deutsch", "script": "latin", "dir": "ltr"},
            "jv": {"name": "Javanese", "native": "Basa Jawa", "script": "latin", "dir": "ltr"},
            "ko": {"name": "Korean", "native": "한국어", "script": "korean", "dir": "ltr"},
            "fr": {"name": "French", "native": "Français", "script": "latin", "dir": "ltr"},
            "te": {"name": "Telugu", "native": "తెలుగు", "script": "telugu", "dir": "ltr"},
            "mr": {"name": "Marathi", "native": "मराठी", "script": "devanagari", "dir": "ltr"},
            "tr": {"name": "Turkish", "native": "Türkçe", "script": "latin", "dir": "ltr"},
            "ta": {"name": "Tamil", "native": "தமிழ்", "script": "tamil", "dir": "ltr"},
            "vi": {"name": "Vietnamese", "native": "Tiếng Việt", "script": "latin", "dir": "ltr"},
            "ur": {"name": "Urdu", "native": "اردو", "script": "arabic", "dir": "rtl"},
            "it": {"name": "Italian", "native": "Italiano", "script": "latin", "dir": "ltr"},
            "th": {"name": "Thai", "native": "ไทย", "script": "thai", "dir": "ltr"},
            "gu": {"name": "Gujarati", "native": "ગુજરાતી", "script": "gujarati", "dir": "ltr"},
            "fa": {"name": "Persian", "native": "فارسی", "script": "arabic", "dir": "rtl"},
            "pl": {"name": "Polish", "native": "Polski", "script": "latin", "dir": "ltr"},
            "uk": {"name": "Ukrainian", "native": "Українська", "script": "cyrillic", "dir": "ltr"},
            "ml": {"name": "Malayalam", "native": "മലയാളം", "script": "malayalam", "dir": "ltr"},
            "kn": {"name": "Kannada", "native": "ಕನ್ನಡ", "script": "kannada", "dir": "ltr"},
            "or": {"name": "Odia", "native": "ଓଡ଼ିଆ", "script": "odia", "dir": "ltr"},
            "my": {"name": "Burmese", "native": "မြန်မာ", "script": "myanmar", "dir": "ltr"},
            "ne": {"name": "Nepali", "native": "नेपाली", "script": "devanagari", "dir": "ltr"},
            "si": {"name": "Sinhala", "native": "සිංහල", "script": "sinhala", "dir": "ltr"},
            "km": {"name": "Khmer", "native": "ខ្មែរ", "script": "khmer", "dir": "ltr"},
            "lo": {"name": "Lao", "native": "ລາວ", "script": "lao", "dir": "ltr"},
            "sv": {"name": "Swedish", "native": "Svenska", "script": "latin", "dir": "ltr"},
            "nl": {"name": "Dutch", "native": "Nederlands", "script": "latin", "dir": "ltr"},
            "el": {"name": "Greek", "native": "Ελληνικά", "script": "greek", "dir": "ltr"},
            "he": {"name": "Hebrew", "native": "עברית", "script": "hebrew", "dir": "rtl"},
            "cs": {"name": "Czech", "native": "Čeština", "script": "latin", "dir": "ltr"},
            "ro": {"name": "Romanian", "native": "Română", "script": "latin", "dir": "ltr"},
            "hu": {"name": "Hungarian", "native": "Magyar", "script": "latin", "dir": "ltr"},
            "da": {"name": "Danish", "native": "Dansk", "script": "latin", "dir": "ltr"},
            "fi": {"name": "Finnish", "native": "Suomi", "script": "latin", "dir": "ltr"},
            "no": {"name": "Norwegian", "native": "Norsk", "script": "latin", "dir": "ltr"},
            "id": {"name": "Indonesian", "native": "Bahasa Indonesia", "script": "latin", "dir": "ltr"},
            "ms": {"name": "Malay", "native": "Bahasa Melayu", "script": "latin", "dir": "ltr"},
            "tl": {"name": "Tagalog", "native": "Tagalog", "script": "latin", "dir": "ltr"},
            "sw": {"name": "Swahili", "native": "Kiswahili", "script": "latin", "dir": "ltr"},
            "ha": {"name": "Hausa", "native": "Hausa", "script": "latin", "dir": "ltr"},
            "yo": {"name": "Yoruba", "native": "Yorùbá", "script": "latin", "dir": "ltr"},
            "ig": {"name": "Igbo", "native": "Igbo", "script": "latin", "dir": "ltr"},
            "am": {"name": "Amharic", "native": "አማርኛ", "script": "ethiopic", "dir": "ltr"},
            "zu": {"name": "Zulu", "native": "isiZulu", "script": "latin", "dir": "ltr"},
            "xh": {"name": "Xhosa", "native": "isiXhosa", "script": "latin", "dir": "ltr"},
            "af": {"name": "Afrikaans", "native": "Afrikaans", "script": "latin", "dir": "ltr"},
            "sq": {"name": "Albanian", "native": "Shqip", "script": "latin", "dir": "ltr"},
            "eu": {"name": "Basque", "native": "Euskara", "script": "latin", "dir": "ltr"},
            "be": {"name": "Belarusian", "native": "Беларуская", "script": "cyrillic", "dir": "ltr"},
            "bg": {"name": "Bulgarian", "native": "Български", "script": "cyrillic", "dir": "ltr"},
            "ca": {"name": "Catalan", "native": "Català", "script": "latin", "dir": "ltr"},
            "hr": {"name": "Croatian", "native": "Hrvatski", "script": "latin", "dir": "ltr"},
            "et": {"name": "Estonian", "native": "Eesti", "script": "latin", "dir": "ltr"},
            "gl": {"name": "Galician", "native": "Galego", "script": "latin", "dir": "ltr"},
            "ka": {"name": "Georgian", "native": "ქართული", "script": "georgian", "dir": "ltr"},
            "is": {"name": "Icelandic", "native": "Íslenska", "script": "latin", "dir": "ltr"},
            "ga": {"name": "Irish", "native": "Gaeilge", "script": "latin", "dir": "ltr"},
            "kk": {"name": "Kazakh", "native": "Қазақ", "script": "cyrillic", "dir": "ltr"},
            "ky": {"name": "Kyrgyz", "native": "Кыргызча", "script": "cyrillic", "dir": "ltr"},
            "la": {"name": "Latin", "native": "Latina", "script": "latin", "dir": "ltr"},
            "lv": {"name": "Latvian", "native": "Latviešu", "script": "latin", "dir": "ltr"},
            "lt": {"name": "Lithuanian", "native": "Lietuvių", "script": "latin", "dir": "ltr"},
            "lb": {"name": "Luxembourgish", "native": "Lëtzebuergesch", "script": "latin", "dir": "ltr"},
            "mk": {"name": "Macedonian", "native": "Македонски", "script": "cyrillic", "dir": "ltr"},
            "mt": {"name": "Maltese", "native": "Malti", "script": "latin", "dir": "ltr"},
            "mn": {"name": "Mongolian", "native": "Монгол", "script": "cyrillic", "dir": "ltr"},
            "ps": {"name": "Pashto", "native": "پښتو", "script": "arabic", "dir": "rtl"},
            "sr": {"name": "Serbian", "native": "Српски", "script": "cyrillic", "dir": "ltr"},
            "sk": {"name": "Slovak", "native": "Slovenčina", "script": "latin", "dir": "ltr"},
            "sl": {"name": "Slovenian", "native": "Slovenščina", "script": "latin", "dir": "ltr"},
            "so": {"name": "Somali", "native": "Soomaali", "script": "latin", "dir": "ltr"},
            "tg": {"name": "Tajik", "native": "Тоҷикӣ", "script": "cyrillic", "dir": "ltr"},
            "tt": {"name": "Tatar", "native": "Татар", "script": "cyrillic", "dir": "ltr"},
            "tk": {"name": "Turkmen", "native": "Türkmen", "script": "latin", "dir": "ltr"},
            "uz": {"name": "Uzbek", "native": "Oʻzbek", "script": "latin", "dir": "ltr"},
            "cy": {"name": "Welsh", "native": "Cymraeg", "script": "latin", "dir": "ltr"},
            "yi": {"name": "Yiddish", "native": "ייִדיש", "script": "hebrew", "dir": "rtl"},
            "eo": {"name": "Esperanto", "native": "Esperanto", "script": "latin", "dir": "ltr"}
        }
    
    def _discover_model_capabilities(self):
        """Discover language capabilities from available models"""
        
        if not self.model_manager:
            return
        
        # Check each model's declared capabilities
        for model_id, model in self.model_manager.models.items():
            profile = model.get_profile()
            
            # Get declared languages
            for lang_code in profile.supported_languages:
                capability = ModelLanguageCapability(
                    model_id=model_id,
                    language_code=lang_code,
                    proficiency_score=0.8,  # Default score
                    verified=False,
                    supports_generation=True,
                    supports_understanding=True
                )
                
                self.language_capabilities[lang_code].append(capability)
                self.detected_languages.add(lang_code)
            
            # Infer additional capabilities from model name/type
            self._infer_language_capabilities(model_id, profile)
    
    def _infer_language_capabilities(self, model_id: str, profile):
        """Infer language capabilities from model characteristics"""
        
        model_name = profile.name.lower()
        
        # Multilingual model patterns
        multilingual_indicators = {
            "qwen": ["zh", "en", "ja", "ko", "es", "fr", "de", "ru", "ar", "pt", "it", "nl", "vi", "th", "id"],
            "aya": ["en", "es", "fr", "de", "it", "pt", "ru", "zh", "ja", "ko", "ar", "hi", "tr", "vi", "th", "id", "ms", "sw", "yo", "ha"],
            "bloom": ["en", "es", "fr", "ar", "zh", "hi", "ur", "id", "pt", "vi", "sw", "yo", "ig", "ha", "am"],
            "xlm": ["en", "es", "fr", "de", "it", "pt", "nl", "ru", "ar", "zh", "ja", "ko", "hi", "tr"],
            "m2m": ["en", "es", "fr", "de", "it", "pt", "nl", "ru", "ar", "zh", "ja", "ko", "hi", "tr", "vi", "th", "id"],
            "mbart": ["en", "es", "fr", "de", "it", "pt", "nl", "ru", "ar", "zh", "ja", "ko", "hi", "tr", "vi", "th"],
            "mt5": ["en", "es", "fr", "de", "it", "pt", "nl", "ru", "ar", "zh", "ja", "ko", "hi", "tr", "vi", "th", "id", "ms", "sw"],
            "nllb": ["en", "es", "fr", "de", "it", "pt", "nl", "ru", "ar", "zh", "ja", "ko", "hi", "tr", "vi", "th", "id", "ms", "sw", "yo", "ig", "ha"],
            "madlad": ["en", "es", "fr", "de", "it", "pt", "nl", "ru", "ar", "zh", "ja", "ko", "hi", "tr", "vi", "th", "id", "ms"],
            "llama3": ["en", "es", "fr", "de", "it", "pt", "ru", "zh", "ja"],
            "llama2": ["en", "es", "fr", "de", "it", "pt"],
            "mistral": ["en", "es", "fr", "de", "it", "pt"],
            "gemma": ["en", "es", "fr", "de", "it", "ja", "ko", "pt", "ru", "zh"],
            "command": ["en", "es", "fr", "de", "it", "pt", "ja", "ko"],
            "claude": ["en", "es", "fr", "de", "it", "pt", "ja", "ko", "zh", "ru"],
            "gpt": ["en", "es", "fr", "de", "it", "pt", "ja", "ko", "zh", "ru", "ar", "hi"]
        }
        
        # Check if model name contains multilingual indicators
        for pattern, languages in multilingual_indicators.items():
            if pattern in model_name:
                for lang in languages:
                    if lang not in [cap.language_code for cap in self.language_capabilities[lang]]:
                        capability = ModelLanguageCapability(
                            model_id=model_id,
                            language_code=lang,
                            proficiency_score=0.6,  # Lower score for inferred
                            verified=False,
                            supports_generation=True,
                            supports_understanding=True,
                            special_instructions=f"Inferred from {pattern} model family"
                        )
                        self.language_capabilities[lang].append(capability)
                        self.detected_languages.add(lang)
    
    async def detect_language(
        self, 
        text: str,
        session_id: Optional[str] = None,
        use_context: bool = True
    ) -> LanguageProfile:
        """
        Detect language using multiple methods
        
        Args:
            text: Text to analyze
            session_id: Session for context
            use_context: Whether to use session context
        """
        
        # Check session context first
        if use_context and session_id and session_id in self.session_languages:
            cached_lang = self.session_languages[session_id]
            if cached_lang in self.language_profiles:
                # Verify it's still the same language
                if self._quick_verify_language(text, cached_lang):
                    return self.language_profiles[cached_lang]
        
        # Try multiple detection methods
        detections = []
        
        # 1. Script-based detection (most reliable)
        script_lang = self._detect_by_script(text)
        if script_lang:
            detections.append((script_lang, 0.9, "script"))
        
        # 2. Pattern-based detection
        pattern_lang = self._detect_by_patterns(text)
        if pattern_lang:
            detections.append((pattern_lang, 0.8, "pattern"))
        
        # 3. Model-based detection (if available)
        if self.model_manager:
            model_lang = await self._detect_by_model(text)
            if model_lang:
                detections.append((model_lang[0], model_lang[1], "model"))
        
        # 4. Statistical detection as fallback
        stat_lang = self._detect_by_statistics(text)
        if stat_lang:
            detections.append((stat_lang, 0.6, "statistics"))
        
        # Combine detections
        if detections:
            # Sort by confidence
            detections.sort(key=lambda x: x[1], reverse=True)
            best_detection = detections[0]
            
            lang_code = best_detection[0]
            confidence = best_detection[1]
            detected_by = best_detection[2]
            
            # Create language profile
            lang_info = self.language_database.get(lang_code, {})
            profile = LanguageProfile(
                code=lang_code,
                name=lang_info.get("name", lang_code),
                native_name=lang_info.get("native", lang_code),
                script=lang_info.get("script", "unknown"),
                direction=lang_info.get("dir", "ltr"),
                confidence=confidence,
                detected_by=detected_by,
                sample_text=text[:100]
            )
            
            # Cache for session
            if session_id:
                self.session_languages[session_id] = lang_code
            self.language_profiles[lang_code] = profile
            
            logger.info(f"Detected language: {lang_code} ({profile.name}) with confidence {confidence:.2f}")
            return profile
        
        # Default to English
        return LanguageProfile(
            code="en",
            name="English",
            native_name="English",
            script="latin",
            direction="ltr",
            confidence=0.5,
            detected_by="default",
            sample_text=text[:100]
        )
    
    def _detect_by_script(self, text: str) -> Optional[str]:
        """Detect language by writing script"""
        
        # Unicode ranges for different scripts
        script_ranges = {
            'chinese': (0x4E00, 0x9FFF, ['zh']),
            'japanese_hiragana': (0x3040, 0x309F, ['ja']),
            'japanese_katakana': (0x30A0, 0x30FF, ['ja']),
            'korean': (0xAC00, 0xD7AF, ['ko']),
            'arabic': (0x0600, 0x06FF, ['ar', 'ur', 'fa', 'ps']),
            'hebrew': (0x0590, 0x05FF, ['he', 'yi']),
            'cyrillic': (0x0400, 0x04FF, ['ru', 'uk', 'bg', 'sr', 'mk', 'be', 'kk', 'ky', 'tg', 'tt']),
            'devanagari': (0x0900, 0x097F, ['hi', 'ne', 'mr']),
            'bengali': (0x0980, 0x09FF, ['bn']),
            'tamil': (0x0B80, 0x0BFF, ['ta']),
            'telugu': (0x0C00, 0x0C7F, ['te']),
            'thai': (0x0E00, 0x0E7F, ['th']),
            'greek': (0x0370, 0x03FF, ['el']),
            'georgian': (0x10A0, 0x10FF, ['ka']),
            'ethiopic': (0x1200, 0x137F, ['am']),
            'kannada': (0x0C80, 0x0CFF, ['kn']),
            'malayalam': (0x0D00, 0x0D7F, ['ml']),
            'sinhala': (0x0D80, 0x0DFF, ['si']),
            'gujarati': (0x0A80, 0x0AFF, ['gu']),
            'gurmukhi': (0x0A00, 0x0A7F, ['pa']),
            'myanmar': (0x1000, 0x109F, ['my']),
            'khmer': (0x1780, 0x17FF, ['km']),
            'lao': (0x0E80, 0x0EFF, ['lo']),
            'odia': (0x0B00, 0x0B7F, ['or'])
        }
        
        # Count characters in each script
        script_counts = defaultdict(int)
        
        for char in text:
            char_code = ord(char)
            for script_name, (start, end, languages) in script_ranges.items():
                if start <= char_code <= end:
                    for lang in languages:
                        script_counts[lang] += 1
        
        if script_counts:
            # Return language with most characters
            return max(script_counts.items(), key=lambda x: x[1])[0]
        
        return None
    
    def _detect_by_patterns(self, text: str) -> Optional[str]:
        """Detect language by characteristic patterns"""
        
        # Language-specific patterns
        patterns = {
            'es': [r'\b(el|la|los|las|un|una|de|en|y|que|es|por|para)\b', r'[áéíóúñ]'],
            'fr': [r'\b(le|la|les|un|une|de|et|est|pour|que|dans|sur)\b', r'[àâçèéêëîïôùûü]'],
            'de': [r'\b(der|die|das|ein|eine|und|ist|von|mit|für|auf)\b', r'[äöüß]'],
            'it': [r'\b(il|la|le|un|una|di|e|è|per|che|in|con)\b', r'[àèéìòù]'],
            'pt': [r'\b(o|a|os|as|um|uma|de|e|é|para|por|em)\b', r'[ãõáéíóúâêô]'],
            'nl': [r'\b(de|het|een|van|en|is|in|op|aan|met|voor)\b', r'[ëï]'],
            'ru': [r'[а-яА-Я]', r'\b(и|в|не|на|с|что|это|как|но|по)\b'],
            'ja': [r'[ぁ-ん]|[ァ-ヴ]|[一-龯]', r'(です|ます|ました|ません|でした)'],
            'ar': [r'[\u0600-\u06FF]', r'(ال|في|من|على|إلى|هذا|ذلك)'],
            'hi': [r'[\u0900-\u097F]', r'(है|हैं|का|की|के|में|से|को|पर)'],
            'ko': [r'[가-힣]', r'(습니다|입니다|에서|으로|에게|이다|한다)'],
            'vi': [r'[àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ]'],
            'th': [r'[\u0E00-\u0E7F]', r'(และ|ที่|ใน|ของ|เป็น|มี|ได้|การ)'],
            'pl': [r'[ąćęłńóśźż]', r'\b(i|w|na|z|do|że|to|jest|się|nie)\b'],
            'tr': [r'[çğıöşü]', r'\b(ve|bir|bu|da|için|ile|olan|olarak)\b'],
            'id': [r'\b(dan|yang|di|ke|dari|untuk|pada|dengan|ini|itu)\b'],
            'sv': [r'[åäö]', r'\b(och|i|att|det|som|på|av|för|med|till)\b'],
            'no': [r'[æøå]', r'\b(og|i|er|på|til|av|for|med|som|det)\b'],
            'da': [r'[æøå]', r'\b(og|i|at|er|på|til|af|for|med|som)\b'],
            'fi': [r'[äö]', r'\b(ja|on|ei|se|että|olla|hän|kun|mutta)\b'],
            'el': [r'[α-ωΑ-Ω]', r'\b(και|το|τα|του|της|στο|στη|με|για)\b'],
            'he': [r'[\u0590-\u05FF]', r'(של|את|על|עם|אל|מן|בין)'],
            'hu': [r'[áéíóöőúüű]', r'\b(és|a|az|egy|hogy|van|nem|meg|el)\b'],
            'cs': [r'[áčďéěíňóřšťúůýž]', r'\b(a|v|na|je|se|že|to|s|z)\b'],
            'ro': [r'[ăâîșț]', r'\b(și|de|la|în|cu|pe|un|o|că)\b']
        }
        
        # Score each language
        scores = {}
        for lang, lang_patterns in patterns.items():
            score = 0
            for pattern in lang_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    score += 1
            if score > 0:
                scores[lang] = score
        
        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]
        
        return None
    
    async def _detect_by_model(self, text: str) -> Optional[Tuple[str, float]]:
        """Use a model to detect language"""
        
        # Find a model with language detection capability
        detection_model = None
        for model_id, model in self.model_manager.models.items():
            profile = model.get_profile()
            # Prefer multilingual models for detection
            if "multilingual" in [c.value for c in profile.capabilities]:
                detection_model = model
                break
        
        if not detection_model:
            # Use any available model
            detection_model = next(iter(self.model_manager.models.values()), None)
        
        if detection_model:
            prompt = f"""Detect the language of this text. Respond with ONLY the ISO 639-1 language code (e.g., en, es, fr, zh, ar, hi, etc.)

Text: {text}

Language code:"""
            
            try:
                response = await detection_model.generate(
                    prompt,
                    max_tokens=10,
                    temperature=0.1
                )
                
                lang_code = response.get('choices', [{}])[0].get('text', '').strip().lower()
                
                # Validate it's a real language code
                if len(lang_code) == 2 and lang_code.isalpha():
                    return (lang_code, 0.85)
            except Exception as e:
                logger.error(f"Model language detection failed: {e}")
        
        return None
    
    def _detect_by_statistics(self, text: str) -> Optional[str]:
        """Simple statistical detection based on character frequencies"""
        
        # This is a fallback method
        # Count Latin vs non-Latin characters
        latin_count = sum(1 for c in text if ord(c) < 256)
        total_count = len(text)
        
        if total_count == 0:
            return None
        
        latin_ratio = latin_count / total_count
        
        # If mostly Latin, likely a European language
        if latin_ratio > 0.9:
            # Check for English common words
            english_words = ['the', 'is', 'and', 'to', 'a', 'of', 'in', 'that', 'have', 'it']
            text_lower = text.lower()
            english_score = sum(1 for word in english_words if word in text_lower)
            
            if english_score >= 3:
                return 'en'
            
            # Could be any European language
            return None
        
        # If mostly non-Latin, need script detection
        return None
    
    def _quick_verify_language(self, text: str, expected_lang: str) -> bool:
        """Quick verification that text matches expected language"""
        
        # For cached session language, do a quick check
        if expected_lang in ['zh', 'ja', 'ko', 'ar', 'he', 'th', 'hi', 'bn', 'ta', 'te']:
            # Non-Latin scripts are easy to verify
            detected_script = self._detect_by_script(text)
            return detected_script == expected_lang
        
        # For Latin script languages, harder to verify quickly
        # Just return True to trust the cache
        return True
    
    async def select_best_model_for_language(
        self,
        language_code: str,
        task_type: Optional[str] = None,
        prefer_speed: bool = False
    ) -> Optional[str]:
        """
        Select the best model for a specific language
        
        Args:
            language_code: ISO language code
            task_type: Optional task type for better selection
            prefer_speed: Whether to prioritize speed
        """
        
        # Get all models that support this language
        capable_models = self.language_capabilities.get(language_code, [])
        
        if not capable_models:
            # No model explicitly supports this language
            # Try to find a multilingual model
            for model_id, model in self.model_manager.models.items():
                profile = model.get_profile()
                if "multilingual" in [c.value for c in profile.capabilities]:
                    # Multilingual model might work
                    logger.warning(f"No specific support for {language_code}, trying multilingual model {model_id}")
                    return model_id
            
            logger.error(f"No model available for language {language_code}")
            return None
        
        # Sort by proficiency and select best
        if prefer_speed:
            # Get the fastest model that supports the language
            sorted_models = sorted(capable_models, key=lambda x: (
                -x.proficiency_score,  # Higher proficiency first
                self.model_manager.models[x.model_id].get_profile().size_gb  # Smaller size (faster)
            ))
        else:
            # Get the best quality model
            sorted_models = sorted(capable_models, key=lambda x: -x.proficiency_score)
        
        best_model = sorted_models[0]
        logger.info(f"Selected model {best_model.model_id} for language {language_code}")
        
        return best_model.model_id
    
    async def generate_in_language(
        self,
        prompt: str,
        language_code: str,
        model_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate response in a specific language
        
        Args:
            prompt: The prompt (can be in any language)
            language_code: Target language for response
            model_id: Optional specific model to use
        """
        
        # Select model if not specified
        if not model_id:
            model_id = await self.select_best_model_for_language(language_code)
        
        if not model_id or model_id not in self.model_manager.models:
            return {"error": f"No model available for language {language_code}"}
        
        model = self.model_manager.models[model_id]
        
        # Get language info
        lang_info = self.language_database.get(language_code, {})
        lang_name = lang_info.get("name", language_code)
        lang_native = lang_info.get("native", language_code)
        
        # Enhance prompt with language instruction
        enhanced_prompt = f"""Please respond in {lang_name} ({lang_native}).

{prompt}

Response in {lang_name}:"""
        
        # Generate response
        response = await model.generate(enhanced_prompt, **kwargs)
        
        # Add language metadata
        if "error" not in response:
            response["language"] = language_code
            response["model_used"] = model_id
        
        return response
    
    async def translate_if_needed(
        self,
        text: str,
        source_lang: str,
        target_lang: str
    ) -> str:
        """
        Translate text if source and target languages differ
        """
        
        if source_lang == target_lang:
            return text
        
        # Find a model that can handle both languages
        translation_model = None
        
        # Check for models that support both languages
        for model_id in self.language_capabilities.get(source_lang, []):
            if model_id.model_id in [m.model_id for m in self.language_capabilities.get(target_lang, [])]:
                translation_model = self.model_manager.models.get(model_id.model_id)
                break
        
        if not translation_model:
            # Use any multilingual model
            for model_id, model in self.model_manager.models.items():
                profile = model.get_profile()
                if "multilingual" in [c.value for c in profile.capabilities]:
                    translation_model = model
                    break
        
        if translation_model:
            source_name = self.language_database.get(source_lang, {}).get("name", source_lang)
            target_name = self.language_database.get(target_lang, {}).get("name", target_lang)
            
            prompt = f"""Translate from {source_name} to {target_name}:

{text}

Translation:"""
            
            response = await translation_model.generate(prompt, temperature=0.3)
            if "error" not in response:
                return response.get("choices", [{}])[0].get("text", text)
        
        return text
    
    def get_supported_languages(self) -> List[Dict[str, Any]]:
        """Get list of all languages supported by available models"""
        
        supported = []
        
        for lang_code in self.detected_languages:
            lang_info = self.language_database.get(lang_code, {})
            models = self.language_capabilities.get(lang_code, [])
            
            supported.append({
                "code": lang_code,
                "name": lang_info.get("name", lang_code),
                "native_name": lang_info.get("native", lang_code),
                "script": lang_info.get("script", "unknown"),
                "direction": lang_info.get("dir", "ltr"),
                "num_models": len(models),
                "best_model": models[0].model_id if models else None,
                "verified": any(m.verified for m in models)
            })
        
        # Sort by number of supporting models
        supported.sort(key=lambda x: x["num_models"], reverse=True)
        
        return supported
    
    async def maintain_language_continuity(
        self,
        session_id: str,
        detected_language: str,
        response: str
    ) -> str:
        """
        Ensure response maintains language continuity
        """
        
        # Store session language
        self.session_languages[session_id] = detected_language
        
        # Verify response is in correct language
        response_lang = await self.detect_language(response, use_context=False)
        
        if response_lang.code != detected_language:
            logger.warning(f"Response language mismatch: expected {detected_language}, got {response_lang.code}")
            # Translate if needed
            response = await self.translate_if_needed(response, response_lang.code, detected_language)
        
        return response
    
    async def handle_code_switching(
        self,
        text: str,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Handle code-switching (mixing languages) in text
        """
        
        # Detect all languages in text
        languages = []
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            if sentence.strip():
                lang = await self.detect_language(sentence.strip(), use_context=False)
                languages.append({
                    "text": sentence.strip(),
                    "language": lang.code,
                    "confidence": lang.confidence
                })
        
        # Determine primary language
        lang_counts = defaultdict(int)
        for item in languages:
            lang_counts[item["language"]] += 1
        
        primary_language = max(lang_counts.items(), key=lambda x: x[1])[0] if lang_counts else "en"
        
        return {
            "primary_language": primary_language,
            "segments": languages,
            "is_code_switching": len(set(lang_counts.keys())) > 1
        }
    
    def get_language_stats(self) -> Dict[str, Any]:
        """Get statistics about language usage"""
        
        stats = {
            "total_languages_supported": len(self.detected_languages),
            "languages_by_model_count": {},
            "session_languages": dict(self.session_languages),
            "top_languages": []
        }
        
        # Count models per language
        for lang_code in self.detected_languages:
            models = self.language_capabilities.get(lang_code, [])
            stats["languages_by_model_count"][lang_code] = len(models)
        
        # Get top languages
        top_langs = sorted(
            stats["languages_by_model_count"].items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        for lang_code, count in top_langs:
            lang_info = self.language_database.get(lang_code, {})
            stats["top_languages"].append({
                "code": lang_code,
                "name": lang_info.get("name", lang_code),
                "model_count": count
            })
        
        return stats