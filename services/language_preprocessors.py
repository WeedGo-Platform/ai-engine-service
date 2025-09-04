"""
Language-Specific Preprocessors for Multilingual AI
Handles text normalization, tokenization, and preparation for each language
"""

import re
import unicodedata
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import json

try:
    import jieba  # Chinese tokenization
except ImportError:
    jieba = None

try:
    import pyarabic.araby as araby  # Arabic text processing
except ImportError:
    araby = None

logger = logging.getLogger(__name__)

class TextDirection(Enum):
    """Text direction for languages"""
    LTR = "left-to-right"
    RTL = "right-to-left"
    VERTICAL = "vertical"  # Traditional Chinese/Japanese

@dataclass
class ProcessedText:
    """Result of text preprocessing"""
    original: str
    normalized: str
    tokens: List[str]
    language: str
    direction: TextDirection
    char_count: int
    token_count: int
    has_special_chars: bool
    metadata: Dict = None

class LanguagePreprocessor:
    """Base class for language-specific preprocessing"""
    
    def __init__(self, language: str):
        self.language = language
        self.direction = TextDirection.LTR
        
    def preprocess(self, text: str) -> ProcessedText:
        """Main preprocessing pipeline"""
        
        # Normalize unicode
        normalized = self.normalize_unicode(text)
        
        # Language-specific normalization
        normalized = self.normalize_text(normalized)
        
        # Tokenization
        tokens = self.tokenize(normalized)
        
        # Clean tokens
        tokens = self.clean_tokens(tokens)
        
        return ProcessedText(
            original=text,
            normalized=normalized,
            tokens=tokens,
            language=self.language,
            direction=self.direction,
            char_count=len(normalized),
            token_count=len(tokens),
            has_special_chars=self.has_special_characters(text),
            metadata=self.get_metadata(text)
        )
    
    def normalize_unicode(self, text: str) -> str:
        """Normalize unicode characters"""
        return unicodedata.normalize('NFC', text)
    
    def normalize_text(self, text: str) -> str:
        """Language-specific text normalization"""
        return text.strip()
    
    def tokenize(self, text: str) -> List[str]:
        """Basic tokenization"""
        return text.split()
    
    def clean_tokens(self, tokens: List[str]) -> List[str]:
        """Clean and filter tokens"""
        return [t for t in tokens if t and len(t) > 0]
    
    def has_special_characters(self, text: str) -> bool:
        """Check for special characters"""
        return bool(re.search(r'[^\w\s]', text))
    
    def get_metadata(self, text: str) -> Dict:
        """Extract metadata from text"""
        return {}

class EnglishPreprocessor(LanguagePreprocessor):
    """English text preprocessor"""
    
    def __init__(self):
        super().__init__('en')
        
        # Common contractions
        self.contractions = {
            "won't": "will not",
            "can't": "cannot",
            "n't": " not",
            "'re": " are",
            "'ve": " have",
            "'ll": " will",
            "'d": " would",
            "'m": " am"
        }
        
        # Cannabis-specific abbreviations
        self.cannabis_abbrev = {
            'thc': 'THC',
            'cbd': 'CBD',
            'cbg': 'CBG',
            'cbn': 'CBN',
            'mg': 'milligrams',
            'g': 'grams',
            'oz': 'ounce'
        }
    
    def normalize_text(self, text: str) -> str:
        """Normalize English text"""
        
        # Expand contractions
        for contraction, expansion in self.contractions.items():
            text = re.sub(r'\b' + contraction + r'\b', expansion, text, flags=re.IGNORECASE)
        
        # Standardize cannabis terms
        for abbrev, full in self.cannabis_abbrev.items():
            text = re.sub(r'\b' + abbrev + r'\b', full, text, flags=re.IGNORECASE)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text
    
    def tokenize(self, text: str) -> List[str]:
        """Tokenize English text"""
        
        # Simple word tokenization
        tokens = re.findall(r'\b\w+\b|[^\w\s]', text.lower())
        return tokens

class SpanishPreprocessor(LanguagePreprocessor):
    """Spanish text preprocessor"""
    
    def __init__(self):
        super().__init__('es')
        
        # Spanish-specific character handling
        self.special_chars = {'ñ', 'á', 'é', 'í', 'ó', 'ú', 'ü', '¿', '¡'}
        
    def normalize_text(self, text: str) -> str:
        """Normalize Spanish text"""
        
        # Handle inverted punctuation
        text = re.sub(r'\s+([¿¡])', r'\1', text)
        text = re.sub(r'([?!])\s+', r'\1 ', text)
        
        # Normalize quotes
        text = re.sub(r'[«»]', '"', text)
        
        return text.strip()
    
    def tokenize(self, text: str) -> List[str]:
        """Tokenize Spanish text"""
        
        # Preserve Spanish characters in tokenization
        tokens = re.findall(r'\b[\w\u00C0-\u024F]+\b|[^\w\s]', text.lower())
        return tokens

class FrenchPreprocessor(LanguagePreprocessor):
    """French text preprocessor"""
    
    def __init__(self):
        super().__init__('fr')
        
        # French elisions
        self.elisions = {
            "l'": "le ",
            "d'": "de ",
            "n'": "ne ",
            "s'": "se ",
            "j'": "je ",
            "m'": "me ",
            "t'": "te ",
            "qu'": "que ",
            "c'": "ce "
        }
    
    def normalize_text(self, text: str) -> str:
        """Normalize French text"""
        
        # Handle elisions
        for elision, expansion in self.elisions.items():
            text = re.sub(r'\b' + elision, expansion, text, flags=re.IGNORECASE)
        
        # Normalize French quotes
        text = re.sub(r'[«»]', '"', text)
        
        # Handle French spaces before punctuation
        text = re.sub(r'\s+([;:!?])', r'\1', text)
        
        return text.strip()
    
    def tokenize(self, text: str) -> List[str]:
        """Tokenize French text"""
        
        # Preserve French accented characters
        tokens = re.findall(r'\b[\w\u00C0-\u024F]+\b|[^\w\s]', text.lower())
        return tokens

class PortuguesePreprocessor(LanguagePreprocessor):
    """Portuguese text preprocessor"""
    
    def __init__(self):
        super().__init__('pt')
        
        # Portuguese contractions
        self.contractions = {
            'do': 'de o',
            'da': 'de a',
            'dos': 'de os',
            'das': 'de as',
            'no': 'em o',
            'na': 'em a',
            'nos': 'em os',
            'nas': 'em as',
            'pelo': 'por o',
            'pela': 'por a'
        }
    
    def normalize_text(self, text: str) -> str:
        """Normalize Portuguese text"""
        
        # Expand contractions
        for contraction, expansion in self.contractions.items():
            text = re.sub(r'\b' + contraction + r'\b', expansion, text, flags=re.IGNORECASE)
        
        # Handle Portuguese-specific punctuation
        text = re.sub(r'[«»]', '"', text)
        
        return text.strip()
    
    def tokenize(self, text: str) -> List[str]:
        """Tokenize Portuguese text"""
        
        # Preserve Portuguese characters
        tokens = re.findall(r'\b[\w\u00C0-\u024F]+\b|[^\w\s]', text.lower())
        return tokens

class ChinesePreprocessor(LanguagePreprocessor):
    """Chinese text preprocessor"""
    
    def __init__(self):
        super().__init__('zh')
        self.direction = TextDirection.LTR  # Modern Chinese is LTR
        
        # Initialize jieba if available
        if jieba:
            jieba.initialize()
            # Add cannabis terms to dictionary
            self.add_cannabis_terms()
    
    def add_cannabis_terms(self):
        """Add cannabis terms to Chinese tokenizer"""
        
        if not jieba:
            return
            
        cannabis_terms = [
            '大麻', '印度大麻', '医用大麻',
            '四氢大麻酚', '大麻二酚',
            '花', '食用品', '浓缩物',
            '混合型', '苜蓿', '籼稻'
        ]
        
        for term in cannabis_terms:
            jieba.add_word(term)
    
    def normalize_text(self, text: str) -> str:
        """Normalize Chinese text"""
        
        # Convert traditional to simplified (basic)
        text = self.traditional_to_simplified(text)
        
        # Normalize punctuation
        text = re.sub(r'[，]', ',', text)
        text = re.sub(r'[。]', '.', text)
        text = re.sub(r'[！]', '!', text)
        text = re.sub(r'[？]', '?', text)
        text = re.sub(r'[；]', ';', text)
        text = re.sub(r'[：]', ':', text)
        text = re.sub(r'[（]', '(', text)
        text = re.sub(r'[）]', ')', text)
        text = re.sub(r'[【]', '[', text)
        text = re.sub(r'[】]', ']', text)
        text = re.sub(r'[《]', '"', text)
        text = re.sub(r'[》]', '"', text)
        
        # Remove extra spaces (Chinese doesn't use spaces between words)
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def traditional_to_simplified(self, text: str) -> str:
        """Convert traditional Chinese to simplified (basic mapping)"""
        
        # Basic character mappings (subset)
        mappings = {
            '醫': '医', '藥': '药', '療': '疗',
            '濃': '浓', '縮': '缩', '產': '产',
            '質': '质', '體': '体', '種': '种'
        }
        
        for trad, simp in mappings.items():
            text = text.replace(trad, simp)
        
        return text
    
    def tokenize(self, text: str) -> List[str]:
        """Tokenize Chinese text"""
        
        if jieba:
            # Use jieba for accurate segmentation
            tokens = list(jieba.cut(text))
        else:
            # Fallback: character-level tokenization
            tokens = list(text)
        
        # Filter out spaces
        tokens = [t for t in tokens if t.strip()]
        
        return tokens
    
    def get_metadata(self, text: str) -> Dict:
        """Extract Chinese-specific metadata"""
        
        # Count Chinese characters
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        
        return {
            'chinese_char_count': chinese_chars,
            'has_traditional': self.has_traditional_chars(text)
        }
    
    def has_traditional_chars(self, text: str) -> bool:
        """Check if text contains traditional Chinese characters"""
        
        traditional_chars = '繁體字醫藥療濃縮產質體種'
        return any(char in text for char in traditional_chars)

class ArabicPreprocessor(LanguagePreprocessor):
    """Arabic text preprocessor"""
    
    def __init__(self):
        super().__init__('ar')
        self.direction = TextDirection.RTL
        
        # Arabic letter forms
        self.arabic_letters = set('ابتثجحخدذرزسشصضطظعغفقكلمنهوي')
        
    def normalize_text(self, text: str) -> str:
        """Normalize Arabic text"""
        
        if araby:
            # Remove Arabic diacritics (tashkeel)
            text = araby.strip_tashkeel(text)
            
            # Normalize hamza
            text = araby.normalize_hamza(text)
            
            # Normalize ligatures
            text = araby.normalize_ligature(text)
        else:
            # Basic normalization without pyarabic
            # Remove common diacritics
            text = re.sub(r'[\u064B-\u065F\u0670\u06D6-\u06DC\u06DF-\u06E4\u06E7\u06E8\u06EA-\u06ED]', '', text)
            
            # Normalize different forms of alef
            text = re.sub(r'[آأإ]', 'ا', text)
            
            # Normalize different forms of yaa
            text = re.sub(r'[ىئ]', 'ي', text)
            
            # Normalize taa marbuta
            text = text.replace('ة', 'ه')
        
        # Normalize punctuation
        text = re.sub(r'[،]', ',', text)
        text = re.sub(r'[؛]', ';', text)
        text = re.sub(r'[؟]', '?', text)
        
        return text.strip()
    
    def tokenize(self, text: str) -> List[str]:
        """Tokenize Arabic text"""
        
        if araby:
            # Use pyarabic tokenization
            tokens = araby.tokenize(text)
        else:
            # Basic tokenization
            # Arabic words are separated by spaces
            tokens = text.split()
        
        return tokens
    
    def clean_tokens(self, tokens: List[str]) -> List[str]:
        """Clean Arabic tokens"""
        
        cleaned = []
        for token in tokens:
            # Remove non-Arabic characters except numbers
            token = re.sub(r'[^\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\s\d]', '', token)
            if token.strip():
                cleaned.append(token.strip())
        
        return cleaned
    
    def get_metadata(self, text: str) -> Dict:
        """Extract Arabic-specific metadata"""
        
        # Count Arabic characters
        arabic_chars = len(re.findall(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]', text))
        
        # Check for mixed direction text
        has_latin = bool(re.search(r'[a-zA-Z]', text))
        
        return {
            'arabic_char_count': arabic_chars,
            'has_mixed_direction': has_latin,
            'is_rtl': True
        }

class MultilingualPreprocessor:
    """Main preprocessor that handles all languages"""
    
    def __init__(self):
        """Initialize preprocessors for all languages"""
        
        self.preprocessors = {
            'en': EnglishPreprocessor(),
            'es': SpanishPreprocessor(),
            'fr': FrenchPreprocessor(),
            'pt': PortuguesePreprocessor(),
            'zh': ChinesePreprocessor(),
            'ar': ArabicPreprocessor()
        }
        
        # Metrics
        self.metrics = {
            'total_processed': 0,
            'languages_processed': {lang: 0 for lang in self.preprocessors.keys()}
        }
    
    def preprocess(
        self,
        text: str,
        language: str,
        detect_language: bool = False
    ) -> ProcessedText:
        """
        Preprocess text for specified language
        
        Args:
            text: Input text
            language: Language code
            detect_language: Whether to auto-detect if not specified
            
        Returns:
            ProcessedText object
        """
        
        # Get appropriate preprocessor
        if language not in self.preprocessors:
            logger.warning(f"Unsupported language: {language}, using English")
            language = 'en'
        
        preprocessor = self.preprocessors[language]
        
        # Preprocess
        result = preprocessor.preprocess(text)
        
        # Update metrics
        self.metrics['total_processed'] += 1
        self.metrics['languages_processed'][language] += 1
        
        return result
    
    def batch_preprocess(
        self,
        texts: List[Tuple[str, str]]
    ) -> List[ProcessedText]:
        """
        Preprocess multiple texts
        
        Args:
            texts: List of (text, language) tuples
            
        Returns:
            List of ProcessedText objects
        """
        
        results = []
        for text, language in texts:
            results.append(self.preprocess(text, language))
        
        return results
    
    def prepare_for_model(
        self,
        processed: ProcessedText,
        max_length: int = 512
    ) -> Dict:
        """
        Prepare processed text for model input
        
        Args:
            processed: ProcessedText object
            max_length: Maximum sequence length
            
        Returns:
            Model-ready input dictionary
        """
        
        # Truncate if needed
        tokens = processed.tokens[:max_length]
        
        # Adjust for language-specific needs
        if processed.language == 'zh':
            # Chinese needs more tokens
            max_length = int(max_length * 1.5)
        elif processed.language == 'ar':
            # Arabic needs RTL handling
            if processed.direction == TextDirection.RTL:
                tokens = tokens[::-1]  # Reverse for RTL
        
        return {
            'text': processed.normalized,
            'tokens': tokens,
            'language': processed.language,
            'direction': processed.direction.value,
            'metadata': processed.metadata
        }
    
    def get_metrics(self) -> Dict:
        """Get preprocessing metrics"""
        
        return {
            **self.metrics,
            'most_processed_language': max(
                self.metrics['languages_processed'],
                key=self.metrics['languages_processed'].get
            ) if self.metrics['total_processed'] > 0 else None
        }