"""
Dynamic Model Selector for Multilingual Support
Automatically selects the best available model for each language
"""
import os
import logging
from pathlib import Path
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ModelSize(Enum):
    TINY = "0.5B"
    SMALL = "1.8B"
    MEDIUM = "3B"
    STANDARD = "7B"
    LARGE = "14B"
    XLARGE = "32B"

@dataclass
class ModelInfo:
    """Information about an available model"""
    name: str
    path: Path
    size: ModelSize
    languages: List[str]
    performance_score: float  # 0-1, higher is better
    speed_score: float  # 0-1, higher is faster
    context_length: int
    quantization: str

class DynamicModelSelector:
    """
    Dynamically selects the best available model for a given language
    Falls back gracefully when preferred models aren't available
    """
    
    def __init__(self, models_base_path: str = "models"):
        self.base_path = Path(models_base_path)
        self.available_models = {}
        self.model_preferences = self._define_preferences()
        self.scan_available_models()
        
    def _define_preferences(self) -> Dict[str, List[str]]:
        """Define model preferences for each language in order of preference"""
        return {
            # Chinese - prefer Qwen models
            "zh": [
                "qwen2.5-7b-instruct",
                "qwen2.5-3b-instruct", 
                "qwen2.5-1.5b-instruct",
                "qwen2.5-0.5b-instruct",
                "deepseek-coder-6.7b",
                "yi-6b",
                "mistral-7b-instruct"  # Last resort
            ],
            # Arabic - Qwen has good Arabic support
            "ar": [
                "qwen2.5-7b-instruct",
                "qwen2.5-3b-instruct",
                "qwen2.5-0.5b-instruct",
                "jais-13b",  # Arabic-specific model
                "mistral-7b-instruct"
            ],
            # Spanish/French - Mistral is excellent
            "es": [
                "mistral-7b-instruct",
                "llama-3-8b-instruct",
                "phi-3-medium",
                "qwen2.5-7b-instruct"
            ],
            "fr": [
                "mistral-7b-instruct",  # French company, great French support
                "llama-3-8b-instruct",
                "croissantllm-1.3b",  # French-specific small model
                "qwen2.5-7b-instruct"
            ],
            # Portuguese - needs special attention
            "pt": [
                "sabia-7b",  # Brazilian Portuguese model
                "llama-3-8b-instruct",
                "mistral-7b-instruct",
                "qwen2.5-7b-instruct"
            ],
            # Japanese/Korean
            "ja": [
                "qwen2.5-7b-instruct",
                "llm-jp-13b",  # Japanese-specific
                "youri-7b-chat"  # Japanese model
            ],
            "ko": [
                "qwen2.5-7b-instruct",
                "solar-10.7b",  # Korean model
                "polyglot-ko-12.8b"  # Korean-specific
            ],
            # English - fastest/best for default
            "en": [
                "mistral-7b-instruct",
                "llama-3-8b-instruct",
                "phi-3-medium",
                "deepseek-coder-6.7b",
                "qwen2.5-7b-instruct"
            ]
        }
    
    def scan_available_models(self):
        """Scan filesystem for available models"""
        model_patterns = {
            # Pattern: (base_name, typical_sizes)
            "qwen": ["0.5b", "1.5b", "3b", "7b", "14b", "32b", "72b"],
            "mistral": ["7b"],
            "llama": ["7b", "8b", "13b", "70b"],
            "deepseek": ["1.3b", "6.7b", "33b"],
            "phi": ["2b", "3b", "3.8b"],
            "yi": ["6b", "34b"],
            "sabia": ["7b"],
            "solar": ["10.7b"],
            "croissantllm": ["1.3b"]
        }
        
        # Scan base and multilingual directories
        for directory in ["base", "multilingual", "models"]:
            model_dir = self.base_path / directory
            if not model_dir.exists():
                continue
                
            for model_file in model_dir.glob("*.gguf"):
                model_info = self._parse_model_file(model_file)
                if model_info:
                    self.available_models[model_info.name] = model_info
                    logger.info(f"Found model: {model_info.name} ({model_info.size.value}) at {model_info.path}")
    
    def _parse_model_file(self, file_path: Path) -> Optional[ModelInfo]:
        """Parse model information from filename"""
        filename = file_path.stem.lower()
        
        # Extract model family and size
        model_mappings = {
            "qwen2.5": ("qwen", ["zh", "ar", "ja", "ko", "en", "es", "fr", "pt"]),
            "mistral": ("mistral", ["en", "es", "fr", "pt", "it", "de"]),
            "llama-3": ("llama3", ["en", "es", "fr", "pt", "de", "it"]),
            "llama-2": ("llama2", ["en", "es", "fr"]),
            "deepseek": ("deepseek", ["zh", "en"]),
            "phi-3": ("phi", ["en"]),
            "yi": ("yi", ["zh", "en"]),
            "sabia": ("sabia", ["pt"]),
            "solar": ("solar", ["ko", "en"]),
            "croissantllm": ("croissant", ["fr"])
        }
        
        for model_key, (family, languages) in model_mappings.items():
            if model_key in filename:
                # Extract size
                size = ModelSize.STANDARD  # Default
                size_map = {
                    "0.5b": ModelSize.TINY,
                    "1.5b": ModelSize.SMALL,
                    "1.8b": ModelSize.SMALL,
                    "3b": ModelSize.MEDIUM,
                    "7b": ModelSize.STANDARD,
                    "8b": ModelSize.STANDARD,
                    "13b": ModelSize.LARGE,
                    "14b": ModelSize.LARGE
                }
                
                for size_str, size_enum in size_map.items():
                    if size_str in filename:
                        size = size_enum
                        break
                
                # Extract quantization
                quant = "q4_k_m"  # Default
                if "q8" in filename:
                    quant = "q8_0"
                elif "q5" in filename:
                    quant = "q5_k_m"
                elif "q4" in filename:
                    quant = "q4_k_m"
                elif "q3" in filename:
                    quant = "q3_k_m"
                
                # Calculate performance and speed scores
                perf_score = self._calculate_performance_score(size, quant)
                speed_score = self._calculate_speed_score(size, quant)
                
                return ModelInfo(
                    name=filename,
                    path=file_path,
                    size=size,
                    languages=languages,
                    performance_score=perf_score,
                    speed_score=speed_score,
                    context_length=4096,  # Default, could be parsed
                    quantization=quant
                )
        
        return None
    
    def _calculate_performance_score(self, size: ModelSize, quant: str) -> float:
        """Calculate performance score based on size and quantization"""
        size_scores = {
            ModelSize.TINY: 0.3,
            ModelSize.SMALL: 0.4,
            ModelSize.MEDIUM: 0.6,
            ModelSize.STANDARD: 0.8,
            ModelSize.LARGE: 0.9,
            ModelSize.XLARGE: 1.0
        }
        
        quant_penalty = {
            "q8_0": 0.95,
            "q5_k_m": 0.9,
            "q4_k_m": 0.85,
            "q3_k_m": 0.75
        }
        
        base_score = size_scores.get(size, 0.5)
        quant_factor = quant_penalty.get(quant, 0.85)
        
        return base_score * quant_factor
    
    def _calculate_speed_score(self, size: ModelSize, quant: str) -> float:
        """Calculate speed score (inverse of performance for size)"""
        size_scores = {
            ModelSize.TINY: 1.0,
            ModelSize.SMALL: 0.85,
            ModelSize.MEDIUM: 0.7,
            ModelSize.STANDARD: 0.5,
            ModelSize.LARGE: 0.3,
            ModelSize.XLARGE: 0.1
        }
        
        quant_boost = {
            "q3_k_m": 1.2,
            "q4_k_m": 1.0,
            "q5_k_m": 0.9,
            "q8_0": 0.8
        }
        
        base_score = size_scores.get(size, 0.5)
        quant_factor = quant_boost.get(quant, 1.0)
        
        return min(base_score * quant_factor, 1.0)
    
    def select_model_for_language(
        self, 
        language: str, 
        prefer_speed: bool = False,
        min_performance: float = 0.3
    ) -> Optional[Tuple[str, Path]]:
        """
        Select the best available model for a language
        
        Args:
            language: ISO language code
            prefer_speed: Prioritize speed over quality
            min_performance: Minimum acceptable performance score
            
        Returns:
            Tuple of (model_name, model_path) or None
        """
        preferences = self.model_preferences.get(language, self.model_preferences["en"])
        
        # Try each preferred model in order
        for preferred_name in preferences:
            # Find matching available models
            matches = [
                model for name, model in self.available_models.items()
                if preferred_name in name.lower() and 
                language in model.languages and
                model.performance_score >= min_performance
            ]
            
            if matches:
                # Sort by preference criteria
                if prefer_speed:
                    best_model = max(matches, key=lambda m: m.speed_score)
                else:
                    best_model = max(matches, key=lambda m: m.performance_score)
                
                logger.info(f"Selected {best_model.name} for {language} "
                          f"(perf: {best_model.performance_score:.2f}, "
                          f"speed: {best_model.speed_score:.2f})")
                return best_model.name, best_model.path
        
        # Fallback: any model that supports the language
        fallbacks = [
            model for model in self.available_models.values()
            if language in model.languages
        ]
        
        if fallbacks:
            best = max(fallbacks, key=lambda m: m.performance_score if not prefer_speed else m.speed_score)
            logger.warning(f"Using fallback model {best.name} for {language}")
            return best.name, best.path
        
        # Last resort: use default English model
        if language != "en":
            logger.warning(f"No model found for {language}, falling back to English")
            return self.select_model_for_language("en", prefer_speed, min_performance)
        
        return None
    
    def get_model_info(self, model_name: str) -> Optional[ModelInfo]:
        """Get information about a specific model"""
        return self.available_models.get(model_name)
    
    def list_available_models(self) -> Dict[str, List[str]]:
        """List all available models grouped by language"""
        language_models = {}
        for model in self.available_models.values():
            for lang in model.languages:
                if lang not in language_models:
                    language_models[lang] = []
                language_models[lang].append(f"{model.name} ({model.size.value})")
        return language_models