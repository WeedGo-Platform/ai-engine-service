"""
Intelligent Model Selector for Voice
Automatically selects optimal models based on context
"""
import time
import logging
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass
from enum import Enum
import numpy as np
from pathlib import Path

logger = logging.getLogger(__name__)

class ModelPriority(Enum):
    """Model selection priorities"""
    SPEED = "speed"
    ACCURACY = "accuracy"
    BALANCED = "balanced"
    MEMORY = "memory"

@dataclass
class ModelProfile:
    """Profile for a voice model"""
    name: str
    type: str  # stt, tts, vad
    size_mb: float
    speed_factor: float  # Relative speed (1.0 = baseline)
    accuracy: float  # 0-1 score
    languages: List[str]
    memory_mb: int
    cpu_cores: int
    supports_streaming: bool
    supports_gpu: bool

@dataclass
class ContextMetrics:
    """Current context metrics"""
    audio_length_ms: float
    noise_level: float
    language: str
    domain: str
    urgency: float  # 0-1 (1 = very urgent)
    available_memory_mb: int
    available_cpu_cores: int
    has_gpu: bool
    network_quality: float  # 0-1 (for future cloud fallback)

class IntelligentModelSelector:
    """
    Selects optimal models based on context and requirements
    """
    
    def __init__(self):
        self.model_profiles = self._load_model_profiles()
        self.performance_history = {}
        self.current_models = {}
        
    def _load_model_profiles(self) -> Dict[str, ModelProfile]:
        """Load profiles for all available models"""
        profiles = {
            # STT Models
            "whisper-tiny": ModelProfile(
                name="whisper-tiny",
                type="stt",
                size_mb=39,
                speed_factor=3.0,
                accuracy=0.85,
                languages=["all"],
                memory_mb=150,
                cpu_cores=2,
                supports_streaming=True,
                supports_gpu=True
            ),
            "whisper-base": ModelProfile(
                name="whisper-base",
                type="stt",
                size_mb=74,
                speed_factor=2.0,
                accuracy=0.92,
                languages=["all"],
                memory_mb=250,
                cpu_cores=2,
                supports_streaming=True,
                supports_gpu=True
            ),
            "whisper-small": ModelProfile(
                name="whisper-small",
                type="stt",
                size_mb=244,
                speed_factor=1.0,
                accuracy=0.95,
                languages=["all"],
                memory_mb=500,
                cpu_cores=4,
                supports_streaming=True,
                supports_gpu=True
            ),
            
            # TTS Models
            "piper-fast": ModelProfile(
                name="piper-fast",
                type="tts",
                size_mb=30,
                speed_factor=15.0,
                accuracy=0.85,
                languages=["en"],
                memory_mb=100,
                cpu_cores=1,
                supports_streaming=True,
                supports_gpu=False
            ),
            "piper-quality": ModelProfile(
                name="piper-quality",
                type="tts",
                size_mb=63,
                speed_factor=10.0,
                accuracy=0.93,
                languages=["en", "es", "fr", "de"],
                memory_mb=150,
                cpu_cores=2,
                supports_streaming=True,
                supports_gpu=False
            ),
            
            # VAD Models
            "silero-vad": ModelProfile(
                name="silero-vad",
                type="vad",
                size_mb=1.5,
                speed_factor=100.0,
                accuracy=0.99,
                languages=["all"],
                memory_mb=50,
                cpu_cores=1,
                supports_streaming=True,
                supports_gpu=False
            ),
            "webrtc-vad": ModelProfile(
                name="webrtc-vad",
                type="vad",
                size_mb=0.5,
                speed_factor=200.0,
                accuracy=0.95,
                languages=["all"],
                memory_mb=20,
                cpu_cores=1,
                supports_streaming=True,
                supports_gpu=False
            )
        }
        
        return profiles
    
    def select_optimal_models(
        self,
        context: ContextMetrics,
        priority: ModelPriority = ModelPriority.BALANCED
    ) -> Dict[str, str]:
        """
        Select optimal models for current context
        
        Returns:
            Dict mapping model type to selected model name
        """
        selected = {}
        
        # Select STT model
        selected["stt"] = self._select_stt_model(context, priority)
        
        # Select TTS model
        selected["tts"] = self._select_tts_model(context, priority)
        
        # Select VAD model
        selected["vad"] = self._select_vad_model(context, priority)
        
        logger.info(f"Selected models: {selected} for priority: {priority.value}")
        
        return selected
    
    def _select_stt_model(
        self,
        context: ContextMetrics,
        priority: ModelPriority
    ) -> str:
        """Select optimal STT model"""
        
        stt_models = {
            name: profile 
            for name, profile in self.model_profiles.items()
            if profile.type == "stt"
        }
        
        # Filter by language support
        compatible_models = {
            name: profile
            for name, profile in stt_models.items()
            if "all" in profile.languages or context.language in profile.languages
        }
        
        if not compatible_models:
            return "whisper-base"  # Fallback
        
        # Score models based on priority
        scores = {}
        for name, profile in compatible_models.items():
            score = self._calculate_model_score(profile, context, priority)
            scores[name] = score
        
        # Select best scoring model
        best_model = max(scores.items(), key=lambda x: x[1])[0]
        
        # Apply intelligent rules
        
        # Rule 1: Use tiny model for very short audio
        if context.audio_length_ms < 1000 and priority == ModelPriority.SPEED:
            if "whisper-tiny" in compatible_models:
                best_model = "whisper-tiny"
        
        # Rule 2: Use small model for noisy environments
        if context.noise_level > 0.7:
            if "whisper-small" in compatible_models:
                best_model = "whisper-small"
        
        # Rule 3: Use faster model for urgent responses
        if context.urgency > 0.8:
            # Pick fastest available
            fastest = min(
                compatible_models.items(),
                key=lambda x: 1.0 / x[1].speed_factor
            )[0]
            best_model = fastest
        
        # Rule 4: Speculative decoding combo
        if priority == ModelPriority.BALANCED:
            # Use tiny for draft, base for verification
            self.current_models["stt_draft"] = "whisper-tiny"
            self.current_models["stt_verify"] = "whisper-base"
            return "whisper-base"  # Primary model
        
        return best_model
    
    def _select_tts_model(
        self,
        context: ContextMetrics,
        priority: ModelPriority
    ) -> str:
        """Select optimal TTS model"""
        
        tts_models = {
            name: profile
            for name, profile in self.model_profiles.items()
            if profile.type == "tts"
        }
        
        # Domain-specific voice selection
        domain_voices = {
            "budtender": "piper-quality",  # More natural
            "healthcare": "piper-quality",  # Clear and professional
            "legal": "piper-quality"  # Authoritative
        }
        
        if context.domain in domain_voices:
            preferred = domain_voices[context.domain]
            if preferred in tts_models:
                return preferred
        
        # Speed vs quality tradeoff
        if priority == ModelPriority.SPEED:
            return "piper-fast"
        elif priority == ModelPriority.ACCURACY:
            return "piper-quality"
        else:
            # Balanced: use quality for important responses
            return "piper-quality"
    
    def _select_vad_model(
        self,
        context: ContextMetrics,
        priority: ModelPriority
    ) -> str:
        """Select optimal VAD model"""
        
        # Silero is more accurate, WebRTC is faster
        if context.noise_level > 0.5:
            return "silero-vad"  # Better noise handling
        elif priority == ModelPriority.SPEED:
            return "webrtc-vad"  # Faster
        else:
            return "silero-vad"  # Default to more accurate
    
    def _calculate_model_score(
        self,
        profile: ModelProfile,
        context: ContextMetrics,
        priority: ModelPriority
    ) -> float:
        """Calculate model score based on context and priority"""
        
        score = 0.0
        
        # Base scores by priority
        if priority == ModelPriority.SPEED:
            score += profile.speed_factor * 0.6
            score += (1.0 - profile.size_mb / 300) * 0.2
            score += profile.accuracy * 0.2
            
        elif priority == ModelPriority.ACCURACY:
            score += profile.accuracy * 0.6
            score += profile.speed_factor * 0.2
            score += (1.0 - profile.size_mb / 300) * 0.2
            
        elif priority == ModelPriority.BALANCED:
            score += profile.accuracy * 0.4
            score += profile.speed_factor * 0.4
            score += (1.0 - profile.size_mb / 300) * 0.2
            
        elif priority == ModelPriority.MEMORY:
            score += (1.0 - profile.memory_mb / 500) * 0.6
            score += profile.speed_factor * 0.2
            score += profile.accuracy * 0.2
        
        # Context adjustments
        
        # Memory constraints
        if context.available_memory_mb < profile.memory_mb:
            score *= 0.1  # Heavily penalize
        
        # CPU constraints
        if context.available_cpu_cores < profile.cpu_cores:
            score *= 0.7
        
        # GPU availability
        if context.has_gpu and profile.supports_gpu:
            score *= 1.2
        
        # Urgency adjustment
        if context.urgency > 0.7:
            score *= (1.0 + profile.speed_factor * 0.1)
        
        return score
    
    def get_pipeline_configuration(
        self,
        context: ContextMetrics
    ) -> Dict[str, Any]:
        """
        Get complete pipeline configuration for context
        """
        
        # Determine priority based on context
        if context.urgency > 0.8:
            priority = ModelPriority.SPEED
        elif context.noise_level > 0.6:
            priority = ModelPriority.ACCURACY
        elif context.available_memory_mb < 500:
            priority = ModelPriority.MEMORY
        else:
            priority = ModelPriority.BALANCED
        
        # Select models
        models = self.select_optimal_models(context, priority)
        
        # Configure pipeline
        config = {
            "models": models,
            "priority": priority.value,
            "optimizations": self._get_optimizations(context, priority),
            "parameters": self._get_parameters(context, models)
        }
        
        return config
    
    def _get_optimizations(
        self,
        context: ContextMetrics,
        priority: ModelPriority
    ) -> Dict[str, bool]:
        """Get optimization settings"""
        
        optimizations = {
            "quantization": True,  # Always use quantization
            "speculative_decoding": False,
            "parallel_pipeline": False,
            "caching": True,
            "streaming": False,
            "batch_processing": False
        }
        
        # Enable speculative decoding for balanced priority
        if priority == ModelPriority.BALANCED:
            optimizations["speculative_decoding"] = True
        
        # Enable parallel pipeline if enough cores
        if context.available_cpu_cores >= 4:
            optimizations["parallel_pipeline"] = True
        
        # Enable streaming for long audio
        if context.audio_length_ms > 5000:
            optimizations["streaming"] = True
        
        # Enable batch processing if not urgent
        if context.urgency < 0.5:
            optimizations["batch_processing"] = True
        
        return optimizations
    
    def _get_parameters(
        self,
        context: ContextMetrics,
        models: Dict[str, str]
    ) -> Dict[str, Any]:
        """Get model-specific parameters"""
        
        params = {
            "stt": {
                "beam_size": 1 if context.urgency > 0.7 else 5,
                "best_of": 1 if context.urgency > 0.7 else 3,
                "temperature": 0.0,  # Deterministic
                "compression_ratio_threshold": 2.4,
                "no_speech_threshold": 0.6
            },
            "tts": {
                "speed": 1.0,
                "pitch": 0.0,
                "energy": 1.0,
                "speaker_id": 0
            },
            "vad": {
                "threshold": max(0.5, context.noise_level * 0.8),
                "min_speech_duration_ms": 250,
                "max_speech_duration_ms": 30000,
                "speech_pad_ms": 300
            }
        }
        
        # Adjust TTS speed for urgency
        if context.urgency > 0.7:
            params["tts"]["speed"] = 1.1
        
        # Adjust VAD for noise
        if context.noise_level > 0.5:
            params["vad"]["min_speech_duration_ms"] = 400
            params["vad"]["speech_pad_ms"] = 500
        
        return params
    
    def update_performance_history(
        self,
        model: str,
        latency_ms: float,
        accuracy: float
    ):
        """Update model performance history"""
        
        if model not in self.performance_history:
            self.performance_history[model] = {
                "uses": 0,
                "avg_latency_ms": 0,
                "avg_accuracy": 0
            }
        
        history = self.performance_history[model]
        n = history["uses"]
        
        # Update running averages
        history["avg_latency_ms"] = (history["avg_latency_ms"] * n + latency_ms) / (n + 1)
        history["avg_accuracy"] = (history["avg_accuracy"] * n + accuracy) / (n + 1)
        history["uses"] += 1
    
    def get_performance_report(self) -> Dict:
        """Get performance report for all models"""
        
        report = {
            "model_performance": self.performance_history,
            "current_models": self.current_models,
            "recommendations": []
        }
        
        # Generate recommendations
        for model, history in self.performance_history.items():
            if history["uses"] > 10:
                if history["avg_latency_ms"] > 500:
                    report["recommendations"].append(
                        f"Consider replacing {model} with faster alternative"
                    )
                if history["avg_accuracy"] < 0.8:
                    report["recommendations"].append(
                        f"Model {model} showing low accuracy, consider upgrade"
                    )
        
        return report

class AdaptiveOptimizer:
    """
    Adaptive optimization based on real-time performance
    """
    
    def __init__(self, model_selector: IntelligentModelSelector):
        self.selector = model_selector
        self.performance_window = []  # Recent performance metrics
        self.optimization_state = {}
        
    def adapt_to_performance(
        self,
        latency_ms: float,
        target_latency_ms: float = 200
    ) -> Dict[str, Any]:
        """Adapt optimization based on performance"""
        
        # Add to performance window
        self.performance_window.append(latency_ms)
        if len(self.performance_window) > 10:
            self.performance_window.pop(0)
        
        avg_latency = np.mean(self.performance_window)
        
        adjustments = {}
        
        if avg_latency > target_latency_ms * 1.5:
            # Too slow - increase optimization
            adjustments["action"] = "increase_speed"
            adjustments["changes"] = {
                "switch_to_faster_model": True,
                "reduce_beam_size": True,
                "enable_more_quantization": True
            }
        elif avg_latency > target_latency_ms:
            # Slightly slow - minor adjustments
            adjustments["action"] = "minor_speedup"
            adjustments["changes"] = {
                "reduce_beam_size": True
            }
        elif avg_latency < target_latency_ms * 0.5:
            # Very fast - can improve quality
            adjustments["action"] = "improve_quality"
            adjustments["changes"] = {
                "switch_to_better_model": True,
                "increase_beam_size": True
            }
        else:
            # On target
            adjustments["action"] = "maintain"
            adjustments["changes"] = {}
        
        return adjustments