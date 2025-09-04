"""
Offline Language Detection System
No external API calls - uses FastText and Lingua for detection
"""

import os
import re
import logging
from typing import Tuple, List, Dict, Optional
from dataclasses import dataclass
import fasttext
from lingua import Language, LanguageDetectorBuilder
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class LanguageDetectionResult:
    """Result from language detection"""
    primary_language: str
    confidence: float
    all_candidates: List[Tuple[str, float]]
    script_type: str  # latin, arabic, chinese, etc.
    is_mixed: bool

class OfflineLanguageDetector:
    """
    Completely offline language detection supporting 6 languages:
    English, Spanish, French, Portuguese, Chinese, Arabic
    """
    
    def __init__(self, model_path: str = "models/lid.176.bin"):
        """Initialize offline language detector"""
        
        # Primary detector - FastText
        if os.path.exists(model_path):
            self.fasttext_model = fasttext.load_model(model_path)
            logger.info(f"Loaded FastText model from {model_path}")
        else:
            self.fasttext_model = None
            logger.warning(f"FastText model not found at {model_path}")
        
        # Secondary detector - Lingua (more accurate for short texts)
        self.lingua_detector = LanguageDetectorBuilder.from_languages(
            Language.ENGLISH,
            Language.SPANISH, 
            Language.FRENCH,
            Language.PORTUGUESE,
            Language.CHINESE,
            Language.ARABIC
        ).build()
        
        # Language code mappings
        self.language_codes = {
            'en': 'English',
            'es': 'Spanish',
            'fr': 'French',
            'pt': 'Portuguese',
            'zh': 'Chinese',
            'ar': 'Arabic',
            # Alternative codes
            'eng': 'en',
            'spa': 'es',
            'fra': 'fr',
            'por': 'pt',
            'chi': 'zh',
            'ara': 'ar',
            'zho': 'zh',
            'cmn': 'zh',  # Mandarin
            'zh-cn': 'zh',
            'zh-tw': 'zh'
        }
        
        # Script detection patterns
        self.script_patterns = {
            'chinese': re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf]'),
            'arabic': re.compile(r'[\u0600-\u06ff\u0750-\u077f\u08a0-\u08ff]'),
            'cyrillic': re.compile(r'[\u0400-\u04ff]'),
            'hebrew': re.compile(r'[\u0590-\u05ff]'),
            'devanagari': re.compile(r'[\u0900-\u097f]'),
            'latin': re.compile(r'[a-zA-Z]')
        }
        
        # Cannabis-specific terms that indicate English
        self.cannabis_terms = {
            'thc', 'cbd', 'indica', 'sativa', 'hybrid',
            'flower', 'edibles', 'vape', 'pre-roll',
            'gram', 'ounce', 'eighth', 'quarter'
        }
    
    def detect(self, text: str, hint: Optional[str] = None) -> LanguageDetectionResult:
        """
        Detect language of input text
        
        Args:
            text: Text to analyze
            hint: Optional language hint from user preference
            
        Returns:
            LanguageDetectionResult with detection details
        """
        
        if not text or len(text.strip()) < 2:
            return LanguageDetectionResult(
                primary_language='en',
                confidence=0.5,
                all_candidates=[('en', 0.5)],
                script_type='unknown',
                is_mixed=False
            )
        
        # Detect script type first
        script_type = self._detect_script(text)
        
        # Fast path for obvious scripts
        if script_type == 'chinese':
            return LanguageDetectionResult(
                primary_language='zh',
                confidence=0.95,
                all_candidates=[('zh', 0.95)],
                script_type='chinese',
                is_mixed=False
            )
        elif script_type == 'arabic':
            return LanguageDetectionResult(
                primary_language='ar',
                confidence=0.95,
                all_candidates=[('ar', 0.95)],
                script_type='arabic',
                is_mixed=False
            )
        
        # Get predictions from both detectors
        fasttext_result = self._detect_fasttext(text) if self.fasttext_model else None
        lingua_result = self._detect_lingua(text)
        
        # Check for cannabis terms (strong indicator of English)
        has_cannabis_terms = self._check_cannabis_terms(text)
        
        # Combine results
        combined_result = self._combine_results(
            fasttext_result, 
            lingua_result,
            script_type,
            has_cannabis_terms,
            hint
        )
        
        return combined_result
    
    def _detect_script(self, text: str) -> str:
        """Detect the script type of the text"""
        
        script_counts = {}
        total_chars = 0
        
        for script_name, pattern in self.script_patterns.items():
            matches = pattern.findall(text)
            if matches:
                script_counts[script_name] = len(matches)
                total_chars += len(matches)
        
        if total_chars == 0:
            return 'unknown'
        
        # Get dominant script
        dominant_script = max(script_counts, key=script_counts.get)
        dominant_ratio = script_counts[dominant_script] / total_chars
        
        # Check if mixed script
        if dominant_ratio < 0.8 and len(script_counts) > 1:
            return 'mixed'
        
        return dominant_script
    
    def _detect_fasttext(self, text: str) -> Optional[List[Tuple[str, float]]]:
        """Detect language using FastText"""
        
        if not self.fasttext_model:
            return None
        
        try:
            # Clean text for FastText
            clean_text = text.replace('\n', ' ').strip()
            
            # Get predictions (top 3)
            predictions = self.fasttext_model.predict(clean_text, k=3)
            
            results = []
            for lang, score in zip(predictions[0], predictions[1]):
                # Remove __label__ prefix
                lang_code = lang.replace('__label__', '')
                
                # Map to our language codes
                if lang_code in self.language_codes:
                    mapped_code = self.language_codes.get(lang_code, lang_code)
                    if mapped_code in ['en', 'es', 'fr', 'pt', 'zh', 'ar']:
                        results.append((mapped_code, float(score)))
                    else:
                        results.append((self.language_codes.get(mapped_code, 'en'), float(score)))
            
            return results
            
        except Exception as e:
            logger.error(f"FastText detection failed: {e}")
            return None
    
    def _detect_lingua(self, text: str) -> List[Tuple[str, float]]:
        """Detect language using Lingua"""
        
        try:
            # Get confidence values for all languages
            confidence_values = self.lingua_detector.compute_language_confidence_values(text)
            
            results = []
            for lang, confidence in confidence_values:
                # Map Lingua language to our codes
                lang_map = {
                    Language.ENGLISH: 'en',
                    Language.SPANISH: 'es',
                    Language.FRENCH: 'fr',
                    Language.PORTUGUESE: 'pt',
                    Language.CHINESE: 'zh',
                    Language.ARABIC: 'ar'
                }
                
                if lang in lang_map:
                    results.append((lang_map[lang], confidence))
            
            # Sort by confidence
            results.sort(key=lambda x: x[1], reverse=True)
            return results[:3]  # Top 3
            
        except Exception as e:
            logger.error(f"Lingua detection failed: {e}")
            return [('en', 0.5)]  # Default fallback
    
    def _check_cannabis_terms(self, text: str) -> bool:
        """Check if text contains cannabis-specific terms"""
        
        text_lower = text.lower()
        for term in self.cannabis_terms:
            if term in text_lower:
                return True
        return False
    
    def _combine_results(
        self,
        fasttext_result: Optional[List[Tuple[str, float]]],
        lingua_result: List[Tuple[str, float]],
        script_type: str,
        has_cannabis_terms: bool,
        hint: Optional[str]
    ) -> LanguageDetectionResult:
        """Combine results from multiple detection methods"""
        
        # Weight factors
        weights = {
            'fasttext': 0.4,
            'lingua': 0.4,
            'script': 0.1,
            'cannabis': 0.05,
            'hint': 0.05
        }
        
        # Aggregate scores
        language_scores = {}
        
        # Add FastText scores
        if fasttext_result:
            for lang, score in fasttext_result:
                language_scores[lang] = language_scores.get(lang, 0) + score * weights['fasttext']
        
        # Add Lingua scores
        for lang, score in lingua_result:
            language_scores[lang] = language_scores.get(lang, 0) + score * weights['lingua']
        
        # Boost based on script type
        if script_type == 'chinese':
            language_scores['zh'] = language_scores.get('zh', 0) + weights['script']
        elif script_type == 'arabic':
            language_scores['ar'] = language_scores.get('ar', 0) + weights['script']
        elif script_type == 'latin':
            # Could be any Latin script language
            for lang in ['en', 'es', 'fr', 'pt']:
                language_scores[lang] = language_scores.get(lang, 0) + weights['script'] / 4
        
        # Boost English if cannabis terms found
        if has_cannabis_terms:
            language_scores['en'] = language_scores.get('en', 0) + weights['cannabis']
        
        # Apply hint if provided
        if hint and hint in ['en', 'es', 'fr', 'pt', 'zh', 'ar']:
            language_scores[hint] = language_scores.get(hint, 0) + weights['hint']
        
        # Normalize scores
        total_score = sum(language_scores.values())
        if total_score > 0:
            for lang in language_scores:
                language_scores[lang] /= total_score
        
        # Sort by score
        sorted_langs = sorted(language_scores.items(), key=lambda x: x[1], reverse=True)
        
        if not sorted_langs:
            # Fallback to English
            sorted_langs = [('en', 0.5)]
        
        # Determine if mixed language
        is_mixed = False
        if len(sorted_langs) > 1:
            if sorted_langs[0][1] < 0.6 and sorted_langs[1][1] > 0.3:
                is_mixed = True
        
        return LanguageDetectionResult(
            primary_language=sorted_langs[0][0],
            confidence=sorted_langs[0][1],
            all_candidates=sorted_langs,
            script_type=script_type,
            is_mixed=is_mixed
        )
    
    def detect_batch(self, texts: List[str]) -> List[LanguageDetectionResult]:
        """Detect languages for multiple texts efficiently"""
        
        results = []
        for text in texts:
            results.append(self.detect(text))
        return results
    
    def get_language_name(self, code: str) -> str:
        """Get full language name from code"""
        
        names = {
            'en': 'English',
            'es': 'Spanish',
            'fr': 'French',
            'pt': 'Portuguese',
            'zh': 'Chinese',
            'ar': 'Arabic'
        }
        return names.get(code, 'Unknown')
    
    def is_supported(self, language_code: str) -> bool:
        """Check if language is supported"""
        
        return language_code in ['en', 'es', 'fr', 'pt', 'zh', 'ar']