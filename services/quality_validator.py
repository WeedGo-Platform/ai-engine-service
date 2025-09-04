"""
Quality Validation System for Multilingual AI Responses
Ensures response quality across all supported languages
"""

import re
import logging
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import json
import numpy as np
from collections import Counter

try:
    from textstat import flesch_reading_ease, flesch_kincaid_grade
except ImportError:
    flesch_reading_ease = None
    flesch_kincaid_grade = None

try:
    from langdetect import detect_langs, LangDetectException
except ImportError:
    detect_langs = None

logger = logging.getLogger(__name__)

class QualityLevel(Enum):
    """Quality levels for responses"""
    EXCELLENT = "excellent"    # Score >= 0.9
    GOOD = "good"              # Score >= 0.75
    ACCEPTABLE = "acceptable"  # Score >= 0.6
    POOR = "poor"              # Score >= 0.4
    UNACCEPTABLE = "unacceptable"  # Score < 0.4

class ValidationCategory(Enum):
    """Categories of validation checks"""
    LANGUAGE = "language_consistency"
    COHERENCE = "coherence"
    COMPLETENESS = "completeness"
    ACCURACY = "accuracy"
    SAFETY = "safety"
    FORMATTING = "formatting"
    RELEVANCE = "relevance"

@dataclass
class ValidationResult:
    """Result of quality validation"""
    overall_score: float
    quality_level: QualityLevel
    language: str
    passed: bool
    category_scores: Dict[str, float]
    issues: List[str]
    suggestions: List[str]
    metadata: Dict = field(default_factory=dict)

@dataclass
class ValidationConfig:
    """Configuration for validation"""
    min_score: float = 0.6
    strict_mode: bool = False
    check_language_consistency: bool = True
    check_coherence: bool = True
    check_completeness: bool = True
    check_safety: bool = True
    check_formatting: bool = True
    check_relevance: bool = True
    language_specific_rules: Dict = field(default_factory=dict)

class QualityValidator:
    """
    Validates quality of AI responses across multiple languages
    """
    
    def __init__(self, config: ValidationConfig = None):
        """
        Initialize quality validator
        
        Args:
            config: Validation configuration
        """
        
        self.config = config or ValidationConfig()
        
        # Language-specific validation rules
        self.language_rules = self._initialize_language_rules()
        
        # Safety patterns
        self.safety_patterns = self._initialize_safety_patterns()
        
        # Quality thresholds
        self.thresholds = {
            QualityLevel.EXCELLENT: 0.9,
            QualityLevel.GOOD: 0.75,
            QualityLevel.ACCEPTABLE: 0.6,
            QualityLevel.POOR: 0.4,
            QualityLevel.UNACCEPTABLE: 0.0
        }
        
        # Metrics
        self.metrics = {
            'total_validated': 0,
            'passed': 0,
            'failed': 0,
            'avg_score': 0.0,
            'language_scores': {}
        }
    
    def _initialize_language_rules(self) -> Dict:
        """Initialize language-specific validation rules"""
        
        return {
            'en': {
                'min_words': 5,
                'max_words': 1000,
                'sentence_endings': r'[.!?]',
                'common_words': {'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i'},
                'readability_target': 60  # Flesch reading ease
            },
            'es': {
                'min_words': 5,
                'max_words': 1100,
                'sentence_endings': r'[.!?¿¡]',
                'common_words': {'el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'ser', 'se'},
                'special_chars': 'ñáéíóúü¿¡'
            },
            'fr': {
                'min_words': 5,
                'max_words': 1100,
                'sentence_endings': r'[.!?]',
                'common_words': {'le', 'de', 'un', 'être', 'et', 'à', 'il', 'avoir', 'ne', 'je'},
                'special_chars': 'àâéèêëîïôùûüç'
            },
            'pt': {
                'min_words': 5,
                'max_words': 1100,
                'sentence_endings': r'[.!?]',
                'common_words': {'o', 'a', 'de', 'que', 'e', 'do', 'da', 'em', 'um', 'para'},
                'special_chars': 'àáâãéêíóôõúç'
            },
            'zh': {
                'min_chars': 10,
                'max_chars': 2000,
                'sentence_endings': r'[。！？!?]',
                'common_chars': {'的', '是', '在', '了', '有', '和', '人', '这', '中', '大'},
                'char_range': (0x4e00, 0x9fff)  # Chinese character range
            },
            'ar': {
                'min_words': 5,
                'max_words': 1200,
                'sentence_endings': r'[.؟!?]',
                'common_words': {'في', 'من', 'إلى', 'أن', 'على', 'هذا', 'كان', 'ذلك'},
                'char_range': (0x0600, 0x06ff),  # Arabic character range
                'is_rtl': True
            }
        }
    
    def _initialize_safety_patterns(self) -> Dict:
        """Initialize safety check patterns"""
        
        return {
            'medical_claims': [
                r'\bcure\s+\w+',
                r'\btreat\s+\w+\s+disease',
                r'\bFDA\s+approved',
                r'\bclinically\s+proven',
                r'\bguaranteed\s+to\s+work'
            ],
            'inappropriate_content': [
                r'\b(?:illegal|illicit)\s+(?:drug|substance)',
                r'\b(?:black|dark)\s+market',
                r'\bhow\s+to\s+(?:make|grow|produce)\s+\w+\s+at\s+home'
            ],
            'personal_info': [
                r'\b\d{3}-\d{2}-\d{4}\b',  # SSN pattern
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
                r'\b\d{16}\b',  # Credit card
                r'\b\d{3}-\d{3}-\d{4}\b'  # Phone
            ]
        }
    
    def validate(
        self,
        response: str,
        language: str,
        prompt: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> ValidationResult:
        """
        Validate response quality
        
        Args:
            response: Generated response text
            language: Language code
            prompt: Original prompt (for relevance check)
            context: Additional context
            
        Returns:
            ValidationResult with scores and issues
        """
        
        issues = []
        suggestions = []
        category_scores = {}
        
        # Language consistency check
        if self.config.check_language_consistency:
            lang_score, lang_issues = self._check_language_consistency(response, language)
            category_scores[ValidationCategory.LANGUAGE.value] = lang_score
            issues.extend(lang_issues)
        
        # Coherence check
        if self.config.check_coherence:
            coh_score, coh_issues = self._check_coherence(response, language)
            category_scores[ValidationCategory.COHERENCE.value] = coh_score
            issues.extend(coh_issues)
        
        # Completeness check
        if self.config.check_completeness:
            comp_score, comp_issues = self._check_completeness(response, language)
            category_scores[ValidationCategory.COMPLETENESS.value] = comp_score
            issues.extend(comp_issues)
        
        # Safety check
        if self.config.check_safety:
            safe_score, safe_issues = self._check_safety(response)
            category_scores[ValidationCategory.SAFETY.value] = safe_score
            issues.extend(safe_issues)
        
        # Formatting check
        if self.config.check_formatting:
            fmt_score, fmt_issues = self._check_formatting(response, language)
            category_scores[ValidationCategory.FORMATTING.value] = fmt_score
            issues.extend(fmt_issues)
        
        # Relevance check (if prompt provided)
        if self.config.check_relevance and prompt:
            rel_score, rel_issues = self._check_relevance(response, prompt, language)
            category_scores[ValidationCategory.RELEVANCE.value] = rel_score
            issues.extend(rel_issues)
        
        # Calculate overall score
        if category_scores:
            overall_score = np.mean(list(category_scores.values()))
        else:
            overall_score = 0.5
        
        # Apply strict mode if enabled
        if self.config.strict_mode:
            # In strict mode, any category below threshold fails
            min_category_score = min(category_scores.values()) if category_scores else 0
            if min_category_score < self.config.min_score:
                overall_score = min_category_score
        
        # Determine quality level
        quality_level = self._get_quality_level(overall_score)
        
        # Generate suggestions based on issues
        suggestions = self._generate_suggestions(issues, language, category_scores)
        
        # Update metrics
        self._update_metrics(overall_score, language, overall_score >= self.config.min_score)
        
        return ValidationResult(
            overall_score=overall_score,
            quality_level=quality_level,
            language=language,
            passed=overall_score >= self.config.min_score,
            category_scores=category_scores,
            issues=issues,
            suggestions=suggestions,
            metadata={
                'response_length': len(response),
                'validation_time': time.time(),
                'strict_mode': self.config.strict_mode
            }
        )
    
    def _check_language_consistency(self, text: str, expected_lang: str) -> Tuple[float, List[str]]:
        """Check if response is in expected language"""
        
        issues = []
        score = 1.0
        
        if not detect_langs:
            return score, issues
        
        try:
            # Detect languages in text
            detected = detect_langs(text)
            
            if detected:
                primary_lang = detected[0]
                
                # Map detected language to our codes
                lang_map = {
                    'en': 'en', 'es': 'es', 'fr': 'fr',
                    'pt': 'pt', 'zh-cn': 'zh', 'zh-tw': 'zh',
                    'ar': 'ar'
                }
                
                detected_code = lang_map.get(primary_lang.lang, primary_lang.lang)
                
                if detected_code != expected_lang:
                    score = primary_lang.prob if primary_lang.lang == expected_lang else 0.5
                    issues.append(f"Language mismatch: expected {expected_lang}, detected {detected_code}")
                else:
                    score = primary_lang.prob
                
                # Check for mixed languages
                if len(detected) > 1 and detected[1].prob > 0.2:
                    score *= 0.8
                    issues.append(f"Mixed languages detected: {', '.join([d.lang for d in detected[:3]])}")
        
        except (LangDetectException, Exception) as e:
            logger.warning(f"Language detection failed: {e}")
        
        return score, issues
    
    def _check_coherence(self, text: str, language: str) -> Tuple[float, List[str]]:
        """Check text coherence and structure"""
        
        issues = []
        score = 1.0
        
        rules = self.language_rules.get(language, self.language_rules['en'])
        
        # Check sentence structure
        if 'sentence_endings' in rules:
            sentences = re.split(rules['sentence_endings'], text)
            sentences = [s.strip() for s in sentences if s.strip()]
            
            if not sentences:
                score *= 0.5
                issues.append("No complete sentences found")
            else:
                # Check for very short or very long sentences
                for i, sentence in enumerate(sentences):
                    word_count = len(sentence.split())
                    if word_count < 3:
                        score *= 0.9
                        issues.append(f"Very short sentence at position {i+1}")
                    elif word_count > 50:
                        score *= 0.95
                        issues.append(f"Very long sentence at position {i+1}")
        
        # Check for repetition
        words = text.lower().split()
        if len(words) > 10:
            word_freq = Counter(words)
            top_word, top_count = word_freq.most_common(1)[0]
            
            # Exclude common words
            common_words = rules.get('common_words', set()) | rules.get('common_chars', set())
            if top_word not in common_words:
                repetition_ratio = top_count / len(words)
                if repetition_ratio > 0.1:  # More than 10% repetition
                    score *= (1 - repetition_ratio)
                    issues.append(f"High repetition of word '{top_word}' ({top_count} times)")
        
        # Check for proper capitalization (Latin scripts only)
        if language in ['en', 'es', 'fr', 'pt']:
            sentences = re.split(r'[.!?]+', text)
            for sentence in sentences:
                sentence = sentence.strip()
                if sentence and not sentence[0].isupper():
                    score *= 0.95
                    issues.append("Sentence doesn't start with capital letter")
                    break
        
        return score, issues
    
    def _check_completeness(self, text: str, language: str) -> Tuple[float, List[str]]:
        """Check if response is complete"""
        
        issues = []
        score = 1.0
        
        rules = self.language_rules.get(language, self.language_rules['en'])
        
        # Check length
        if language == 'zh':
            # Chinese uses character count
            char_count = len(text)
            min_chars = rules.get('min_chars', 10)
            max_chars = rules.get('max_chars', 2000)
            
            if char_count < min_chars:
                score *= 0.5
                issues.append(f"Response too short: {char_count} characters (min: {min_chars})")
            elif char_count > max_chars:
                score *= 0.8
                issues.append(f"Response too long: {char_count} characters (max: {max_chars})")
        else:
            # Other languages use word count
            word_count = len(text.split())
            min_words = rules.get('min_words', 5)
            max_words = rules.get('max_words', 1000)
            
            if word_count < min_words:
                score *= 0.5
                issues.append(f"Response too short: {word_count} words (min: {min_words})")
            elif word_count > max_words:
                score *= 0.8
                issues.append(f"Response too long: {word_count} words (max: {max_words})")
        
        # Check for incomplete sentences
        if text and not re.search(r'[.!?。؟！？]$', text.strip()):
            score *= 0.85
            issues.append("Response doesn't end with proper punctuation")
        
        # Check for truncation indicators
        truncation_patterns = ['...', '…', '[truncated]', '[cut off]', '[incomplete]']
        for pattern in truncation_patterns:
            if pattern in text.lower():
                score *= 0.7
                issues.append("Response appears to be truncated")
                break
        
        return score, issues
    
    def _check_safety(self, text: str) -> Tuple[float, List[str]]:
        """Check for safety issues"""
        
        issues = []
        score = 1.0
        
        # Check medical claims
        for pattern in self.safety_patterns['medical_claims']:
            if re.search(pattern, text, re.IGNORECASE):
                score *= 0.5
                issues.append("Contains unverified medical claims")
                break
        
        # Check inappropriate content
        for pattern in self.safety_patterns['inappropriate_content']:
            if re.search(pattern, text, re.IGNORECASE):
                score *= 0.3
                issues.append("Contains potentially inappropriate content")
                break
        
        # Check personal information
        for pattern in self.safety_patterns['personal_info']:
            if re.search(pattern, text):
                score *= 0.2
                issues.append("Contains potential personal information")
                break
        
        return score, issues
    
    def _check_formatting(self, text: str, language: str) -> Tuple[float, List[str]]:
        """Check text formatting"""
        
        issues = []
        score = 1.0
        
        # Check for excessive whitespace
        if '  ' in text or '\n\n\n' in text:
            score *= 0.95
            issues.append("Contains excessive whitespace")
        
        # Check for proper encoding
        try:
            _ = text.encode('utf-8')
        except UnicodeEncodeError:
            score *= 0.7
            issues.append("Contains encoding issues")
        
        # Language-specific formatting
        rules = self.language_rules.get(language, {})
        
        if language == 'ar' and rules.get('is_rtl'):
            # Check for RTL marks if needed
            if not any(char in text for char in '\u200F\u202B\u202E'):
                # RTL marks not required but noted
                pass
        
        return score, issues
    
    def _check_relevance(self, response: str, prompt: str, language: str) -> Tuple[float, List[str]]:
        """Check if response is relevant to prompt"""
        
        issues = []
        score = 1.0
        
        # Simple keyword overlap check
        prompt_words = set(prompt.lower().split())
        response_words = set(response.lower().split())
        
        # Remove common words
        rules = self.language_rules.get(language, self.language_rules['en'])
        common_words = rules.get('common_words', set()) | rules.get('common_chars', set())
        
        prompt_words -= common_words
        response_words -= common_words
        
        if prompt_words:
            overlap = len(prompt_words & response_words) / len(prompt_words)
            
            if overlap < 0.1:
                score *= 0.6
                issues.append("Response seems unrelated to prompt")
            elif overlap < 0.3:
                score *= 0.8
                issues.append("Limited relevance to prompt")
        
        return score, issues
    
    def _get_quality_level(self, score: float) -> QualityLevel:
        """Determine quality level from score"""
        
        for level, threshold in self.thresholds.items():
            if score >= threshold:
                return level
        
        return QualityLevel.UNACCEPTABLE
    
    def _generate_suggestions(self, issues: List[str], language: str, scores: Dict) -> List[str]:
        """Generate improvement suggestions based on issues"""
        
        suggestions = []
        
        # Analyze category scores
        if scores:
            worst_category = min(scores, key=scores.get)
            worst_score = scores[worst_category]
            
            if worst_score < 0.6:
                if worst_category == ValidationCategory.LANGUAGE.value:
                    suggestions.append(f"Ensure response is fully in {language}")
                elif worst_category == ValidationCategory.COHERENCE.value:
                    suggestions.append("Improve sentence structure and flow")
                elif worst_category == ValidationCategory.COMPLETENESS.value:
                    suggestions.append("Provide more complete response")
                elif worst_category == ValidationCategory.SAFETY.value:
                    suggestions.append("Review for compliance and safety")
                elif worst_category == ValidationCategory.RELEVANCE.value:
                    suggestions.append("Better address the user's question")
        
        # Specific issue-based suggestions
        if "too short" in ' '.join(issues).lower():
            suggestions.append("Expand response with more details")
        
        if "repetition" in ' '.join(issues).lower():
            suggestions.append("Reduce word repetition for better flow")
        
        if "truncated" in ' '.join(issues).lower():
            suggestions.append("Complete the response fully")
        
        return suggestions
    
    def _update_metrics(self, score: float, language: str, passed: bool):
        """Update validation metrics"""
        
        self.metrics['total_validated'] += 1
        
        if passed:
            self.metrics['passed'] += 1
        else:
            self.metrics['failed'] += 1
        
        # Update average score
        prev_avg = self.metrics['avg_score']
        self.metrics['avg_score'] = (
            (prev_avg * (self.metrics['total_validated'] - 1) + score)
            / self.metrics['total_validated']
        )
        
        # Update language-specific scores
        if language not in self.metrics['language_scores']:
            self.metrics['language_scores'][language] = {
                'total': 0,
                'avg_score': 0,
                'passed': 0
            }
        
        lang_metrics = self.metrics['language_scores'][language]
        lang_metrics['total'] += 1
        
        if passed:
            lang_metrics['passed'] += 1
        
        lang_metrics['avg_score'] = (
            (lang_metrics['avg_score'] * (lang_metrics['total'] - 1) + score)
            / lang_metrics['total']
        )
    
    def batch_validate(
        self,
        responses: List[Tuple[str, str]],
        prompts: Optional[List[str]] = None
    ) -> List[ValidationResult]:
        """
        Validate multiple responses
        
        Args:
            responses: List of (response, language) tuples
            prompts: Optional list of original prompts
            
        Returns:
            List of ValidationResults
        """
        
        results = []
        
        for i, (response, language) in enumerate(responses):
            prompt = prompts[i] if prompts and i < len(prompts) else None
            result = self.validate(response, language, prompt)
            results.append(result)
        
        return results
    
    def get_metrics(self) -> Dict:
        """Get validation metrics"""
        
        pass_rate = (
            self.metrics['passed'] / self.metrics['total_validated']
            if self.metrics['total_validated'] > 0 else 0
        )
        
        return {
            **self.metrics,
            'pass_rate': pass_rate,
            'quality_distribution': self._get_quality_distribution()
        }
    
    def _get_quality_distribution(self) -> Dict:
        """Get distribution of quality levels"""
        
        # This would track actual distribution in production
        return {
            level.value: 0 for level in QualityLevel
        }