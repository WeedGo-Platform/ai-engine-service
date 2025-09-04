"""
Unified Model Interface - Model Agnostic System
Supports any model, automatic capability detection, and A/B testing
"""
import asyncio
import json
import logging
import time
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set
from collections import defaultdict
import hashlib

logger = logging.getLogger(__name__)

class ModelCapability(Enum):
    """Model capabilities that can be auto-detected or configured"""
    CHAT = "chat"
    COMPLETION = "completion"
    TRANSLATION = "translation"
    CODE_GENERATION = "code_generation"
    REASONING = "reasoning"
    MULTILINGUAL = "multilingual"
    FUNCTION_CALLING = "function_calling"
    VISION = "vision"
    EMBEDDING = "embedding"
    SUMMARIZATION = "summarization"
    CLASSIFICATION = "classification"
    ENTITY_EXTRACTION = "entity_extraction"
    SENTIMENT_ANALYSIS = "sentiment_analysis"

class TaskType(Enum):
    """Types of tasks the system handles"""
    GREETING = "greeting"
    PRODUCT_SEARCH = "product_search"
    PRODUCT_INFO = "product_info"
    RECOMMENDATION = "recommendation"
    TRANSLATION = "translation"
    INTENT_DETECTION = "intent_detection"
    ENTITY_EXTRACTION = "entity_extraction"
    CONVERSATION = "conversation"
    SUMMARY = "summary"
    CLASSIFICATION = "classification"

@dataclass
class ModelProfile:
    """Complete profile of a model's capabilities and performance"""
    model_id: str
    name: str
    path: Path
    size_gb: float
    
    # Capabilities
    capabilities: Set[ModelCapability] = field(default_factory=set)
    supported_languages: Set[str] = field(default_factory=set)
    max_context_length: int = 4096
    
    # Performance metrics (auto-measured)
    avg_tokens_per_second: float = 0.0
    avg_latency_ms: float = 0.0
    memory_usage_mb: float = 0.0
    
    # Quality metrics (from testing)
    accuracy_scores: Dict[TaskType, float] = field(default_factory=dict)
    language_scores: Dict[str, float] = field(default_factory=dict)
    
    # Usage statistics
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_tokens_generated: int = 0
    
    # A/B testing
    ab_test_group: Optional[str] = None
    ab_test_weight: float = 1.0  # Weight for selection probability
    
    def get_success_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests
    
    def get_task_score(self, task: TaskType) -> float:
        """Get model's score for a specific task"""
        return self.accuracy_scores.get(task, 0.5)
    
    def get_language_score(self, language: str) -> float:
        """Get model's score for a specific language"""
        return self.language_scores.get(language, 0.5)

class ModelInterface(ABC):
    """Abstract interface that all models must implement"""
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        stop: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate text from prompt"""
        pass
    
    @abstractmethod
    async def get_embedding(self, text: str) -> List[float]:
        """Get embedding for text (if supported)"""
        pass
    
    @abstractmethod
    def supports_capability(self, capability: ModelCapability) -> bool:
        """Check if model supports a capability"""
        pass
    
    @abstractmethod
    def get_profile(self) -> ModelProfile:
        """Get model profile"""
        pass

class LlamaCppModel(ModelInterface):
    """Wrapper for llama.cpp models (GGUF format)"""
    
    def __init__(self, model_path: Path, profile: ModelProfile):
        self.model_path = model_path
        self.profile = profile
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the actual model"""
        try:
            from llama_cpp import Llama
            self.model = Llama(
                model_path=str(self.model_path),
                n_ctx=self.profile.max_context_length,
                n_gpu_layers=35,  # Auto-detect available GPU layers
                verbose=False
            )
            logger.info(f"Loaded {self.profile.name} successfully")
        except Exception as e:
            logger.error(f"Failed to load {self.profile.name}: {e}")
    
    async def generate(self, prompt: str, max_tokens: int = 512, 
                       temperature: float = 0.7, stop: Optional[List[str]] = None,
                       **kwargs) -> Dict[str, Any]:
        """Generate text using llama.cpp"""
        if not self.model:
            return {"error": "Model not loaded"}
        
        start_time = time.time()
        
        try:
            response = self.model(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stop=stop or [],
                echo=False,
                **kwargs
            )
            
            # Update metrics
            elapsed_ms = (time.time() - start_time) * 1000
            self.profile.avg_latency_ms = (
                self.profile.avg_latency_ms * 0.9 + elapsed_ms * 0.1
            )  # Exponential moving average
            
            tokens = response.get('usage', {}).get('completion_tokens', 0)
            if tokens > 0 and elapsed_ms > 0:
                tps = (tokens / elapsed_ms) * 1000
                self.profile.avg_tokens_per_second = (
                    self.profile.avg_tokens_per_second * 0.9 + tps * 0.1
                )
            
            self.profile.successful_requests += 1
            self.profile.total_requests += 1
            self.profile.total_tokens_generated += tokens
            
            return response
            
        except Exception as e:
            logger.error(f"Generation failed for {self.profile.name}: {e}")
            self.profile.failed_requests += 1
            self.profile.total_requests += 1
            return {"error": str(e)}
    
    async def get_embedding(self, text: str) -> List[float]:
        """Get embedding (if model supports it)"""
        if not self.supports_capability(ModelCapability.EMBEDDING):
            raise NotImplementedError(f"{self.profile.name} doesn't support embeddings")
        
        # Use model's embedding function if available
        if hasattr(self.model, 'embed'):
            return self.model.embed(text)
        
        raise NotImplementedError("Embedding not implemented")
    
    def supports_capability(self, capability: ModelCapability) -> bool:
        """Check capability support"""
        return capability in self.profile.capabilities
    
    def get_profile(self) -> ModelProfile:
        """Get model profile"""
        return self.profile

class UnifiedModelManager:
    """
    Manages all available models, routes tasks, and handles A/B testing
    """
    
    def __init__(self, models_base_path: str = "models"):
        self.base_path = Path(models_base_path)
        self.models: Dict[str, ModelInterface] = {}
        self.task_routing: Dict[TaskType, List[str]] = defaultdict(list)
        self.ab_tests: Dict[str, Dict] = {}
        self.performance_history: Dict[str, List[Dict]] = defaultdict(list)
        
        # Auto-discovery configuration
        self.model_detection_patterns = self._load_detection_patterns()
        
    def _load_detection_patterns(self) -> Dict:
        """Load patterns for auto-detecting model capabilities"""
        return {
            "qwen": {
                "capabilities": {ModelCapability.MULTILINGUAL, ModelCapability.CHAT, 
                               ModelCapability.REASONING, ModelCapability.CODE_GENERATION},
                "languages": ["zh", "ar", "ja", "ko", "en", "es", "fr", "pt", "ru", "de"],
                "pattern": r"qwen.*\.gguf"
            },
            "mistral": {
                "capabilities": {ModelCapability.CHAT, ModelCapability.REASONING,
                               ModelCapability.FUNCTION_CALLING},
                "languages": ["en", "es", "fr", "de", "it", "pt"],
                "pattern": r"mistral.*\.gguf"
            },
            "llama3": {
                "capabilities": {ModelCapability.CHAT, ModelCapability.REASONING,
                               ModelCapability.MULTILINGUAL},
                "languages": ["en", "es", "fr", "pt", "de", "it", "nl", "pl"],
                "pattern": r"llama-?3.*\.gguf"
            },
            "phi3": {
                "capabilities": {ModelCapability.CHAT, ModelCapability.CODE_GENERATION},
                "languages": ["en"],
                "pattern": r"phi-?3.*\.gguf"
            },
            "deepseek": {
                "capabilities": {ModelCapability.CODE_GENERATION, ModelCapability.REASONING,
                               ModelCapability.CHAT},
                "languages": ["zh", "en"],
                "pattern": r"deepseek.*\.gguf"
            },
            "gemma2": {
                "capabilities": {ModelCapability.CHAT, ModelCapability.REASONING},
                "languages": ["en", "es", "fr", "de", "it", "pt", "nl"],
                "pattern": r"gemma-?2.*\.gguf"
            },
            "claude": {
                "capabilities": {ModelCapability.CHAT, ModelCapability.REASONING,
                               ModelCapability.FUNCTION_CALLING, ModelCapability.VISION},
                "languages": ["en", "es", "fr", "de", "it", "pt", "ja", "ko", "zh"],
                "pattern": r"claude.*\.gguf"
            }
        }
    
    async def discover_and_load_models(self):
        """Auto-discover and load all available models"""
        logger.info("Starting model discovery...")
        
        for directory in ["base", "multilingual", "specialized"]:
            model_dir = self.base_path / directory
            if not model_dir.exists():
                continue
            
            for model_file in model_dir.glob("*.gguf"):
                profile = self._create_model_profile(model_file)
                if profile:
                    try:
                        model = LlamaCppModel(model_file, profile)
                        self.models[profile.model_id] = model
                        
                        # Auto-assign to task types based on capabilities
                        self._auto_assign_tasks(profile)
                        
                        logger.info(f"Loaded: {profile.name} with capabilities: {profile.capabilities}")
                    except Exception as e:
                        logger.error(f"Failed to load {model_file}: {e}")
        
        logger.info(f"Discovery complete. Loaded {len(self.models)} models")
    
    def _create_model_profile(self, model_path: Path) -> Optional[ModelProfile]:
        """Create a model profile from file path and patterns"""
        filename = model_path.name.lower()
        file_size_gb = model_path.stat().st_size / (1024**3)
        
        # Generate unique model ID
        model_id = hashlib.md5(str(model_path).encode()).hexdigest()[:8]
        
        profile = ModelProfile(
            model_id=model_id,
            name=model_path.stem,
            path=model_path,
            size_gb=file_size_gb
        )
        
        # Auto-detect capabilities and languages
        for model_type, config in self.model_detection_patterns.items():
            if model_type in filename:
                profile.capabilities = config["capabilities"]
                profile.supported_languages = set(config["languages"])
                
                # Estimate context length from filename
                if "32k" in filename:
                    profile.max_context_length = 32768
                elif "16k" in filename:
                    profile.max_context_length = 16384
                elif "8k" in filename:
                    profile.max_context_length = 8192
                else:
                    profile.max_context_length = 4096
                
                break
        
        # If no pattern matched, use defaults
        if not profile.capabilities:
            profile.capabilities = {ModelCapability.CHAT, ModelCapability.COMPLETION}
            profile.supported_languages = {"en"}
        
        return profile
    
    def _auto_assign_tasks(self, profile: ModelProfile):
        """Auto-assign model to task types based on capabilities"""
        capability_to_tasks = {
            ModelCapability.CHAT: [TaskType.CONVERSATION, TaskType.GREETING],
            ModelCapability.MULTILINGUAL: [TaskType.TRANSLATION],
            ModelCapability.REASONING: [TaskType.RECOMMENDATION, TaskType.PRODUCT_INFO],
            ModelCapability.CLASSIFICATION: [TaskType.INTENT_DETECTION, TaskType.CLASSIFICATION],
            ModelCapability.ENTITY_EXTRACTION: [TaskType.ENTITY_EXTRACTION],
            ModelCapability.SUMMARIZATION: [TaskType.SUMMARY]
        }
        
        for capability in profile.capabilities:
            if capability in capability_to_tasks:
                for task in capability_to_tasks[capability]:
                    self.task_routing[task].append(profile.model_id)
        
        # Always add to product search if multilingual
        if ModelCapability.MULTILINGUAL in profile.capabilities:
            self.task_routing[TaskType.PRODUCT_SEARCH].append(profile.model_id)
    
    async def select_model(
        self,
        task: TaskType,
        language: str = "en",
        prefer_speed: bool = False,
        session_id: Optional[str] = None
    ) -> Optional[ModelInterface]:
        """
        Select the best model for a task
        
        Args:
            task: Type of task to perform
            language: Language required
            prefer_speed: Prioritize speed over quality
            session_id: Session ID for A/B test consistency
        """
        
        # Get candidate models for this task
        candidate_ids = self.task_routing.get(task, [])
        if not candidate_ids:
            # No specific models for task, use any chat model
            candidate_ids = [
                mid for mid, model in self.models.items()
                if model.supports_capability(ModelCapability.CHAT)
            ]
        
        # Filter by language support
        candidates = []
        for model_id in candidate_ids:
            model = self.models[model_id]
            profile = model.get_profile()
            if language in profile.supported_languages:
                candidates.append(model)
        
        if not candidates:
            # Fallback to English-capable models
            candidates = [
                model for model in self.models.values()
                if "en" in model.get_profile().supported_languages
            ]
        
        if not candidates:
            logger.error(f"No models available for task {task} in language {language}")
            return None
        
        # Apply A/B testing if configured
        if session_id and session_id in self.ab_tests:
            return self._apply_ab_test(candidates, session_id)
        
        # Score and rank models
        scored_models = []
        for model in candidates:
            score = self._calculate_model_score(model, task, language, prefer_speed)
            scored_models.append((score, model))
        
        # Sort by score (highest first)
        scored_models.sort(key=lambda x: x[0], reverse=True)
        
        # Return best model
        best_model = scored_models[0][1]
        logger.info(f"Selected {best_model.get_profile().name} for {task} in {language}")
        
        return best_model
    
    def _calculate_model_score(
        self,
        model: ModelInterface,
        task: TaskType,
        language: str,
        prefer_speed: bool
    ) -> float:
        """Calculate a model's score for a specific task and language"""
        profile = model.get_profile()
        
        # Base score from task performance
        task_score = profile.get_task_score(task)
        
        # Language score
        lang_score = profile.get_language_score(language)
        
        # Success rate score
        success_score = profile.get_success_rate()
        
        # Speed score (inverse of latency)
        if profile.avg_latency_ms > 0:
            speed_score = 1000 / profile.avg_latency_ms
        else:
            speed_score = 0.5
        
        # Size penalty (smaller is better for speed)
        size_penalty = 1.0 / (1 + profile.size_gb * 0.1)
        
        # Calculate weighted score
        if prefer_speed:
            # Prioritize speed and size
            score = (
                task_score * 0.2 +
                lang_score * 0.2 +
                success_score * 0.1 +
                speed_score * 0.3 +
                size_penalty * 0.2
            )
        else:
            # Prioritize quality
            score = (
                task_score * 0.3 +
                lang_score * 0.3 +
                success_score * 0.2 +
                speed_score * 0.1 +
                size_penalty * 0.1
            )
        
        return score
    
    def _apply_ab_test(
        self,
        candidates: List[ModelInterface],
        session_id: str
    ) -> ModelInterface:
        """Apply A/B testing logic"""
        test_config = self.ab_tests[session_id]
        
        # Check if session already assigned to a group
        if "assigned_model" in test_config:
            model_id = test_config["assigned_model"]
            if model_id in self.models:
                return self.models[model_id]
        
        # Assign to a model based on weights
        weights = []
        for model in candidates:
            profile = model.get_profile()
            weights.append(profile.ab_test_weight)
        
        # Weighted random selection
        selected = random.choices(candidates, weights=weights)[0]
        
        # Store assignment
        test_config["assigned_model"] = selected.get_profile().model_id
        
        return selected
    
    def create_ab_test(
        self,
        test_name: str,
        model_weights: Dict[str, float],
        task_types: List[TaskType]
    ):
        """Create an A/B test configuration"""
        self.ab_tests[test_name] = {
            "model_weights": model_weights,
            "task_types": task_types,
            "created_at": time.time(),
            "sessions": {}
        }
        
        # Update model weights
        for model_id, weight in model_weights.items():
            if model_id in self.models:
                self.models[model_id].get_profile().ab_test_weight = weight
    
    async def benchmark_model(
        self,
        model_id: str,
        test_suite: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Benchmark a model's performance"""
        if model_id not in self.models:
            return {"error": "Model not found"}
        
        model = self.models[model_id]
        profile = model.get_profile()
        
        if not test_suite:
            # Default test suite
            test_suite = {
                TaskType.GREETING: [
                    "Hello!", "Hola!", "你好", "Bonjour!"
                ],
                TaskType.PRODUCT_SEARCH: [
                    "Show me indica strains",
                    "I need something for sleep",
                    "What's your strongest THC?"
                ],
                TaskType.TRANSLATION: [
                    ("Hello, how are you?", "es"),
                    ("I need help", "fr"),
                    ("Show me products", "zh")
                ]
            }
        
        results = {}
        
        for task_type, tests in test_suite.items():
            task_results = []
            
            for test in tests:
                start_time = time.time()
                
                if task_type == TaskType.TRANSLATION:
                    prompt = f"Translate to {test[1]}: {test[0]}"
                else:
                    prompt = test
                
                response = await model.generate(prompt, max_tokens=100)
                
                elapsed = time.time() - start_time
                
                task_results.append({
                    "prompt": prompt,
                    "response_time": elapsed,
                    "success": "error" not in response,
                    "tokens": response.get("usage", {}).get("completion_tokens", 0)
                })
            
            # Calculate task metrics
            successful = [r for r in task_results if r["success"]]
            if successful:
                avg_time = sum(r["response_time"] for r in successful) / len(successful)
                avg_tokens = sum(r["tokens"] for r in successful) / len(successful)
                success_rate = len(successful) / len(task_results)
                
                # Update profile
                profile.accuracy_scores[task_type] = success_rate
                
                results[task_type.value] = {
                    "success_rate": success_rate,
                    "avg_response_time": avg_time,
                    "avg_tokens": avg_tokens
                }
        
        return results
    
    def get_model_stats(self) -> Dict[str, Any]:
        """Get statistics for all models"""
        stats = {}
        
        for model_id, model in self.models.items():
            profile = model.get_profile()
            stats[model_id] = {
                "name": profile.name,
                "size_gb": profile.size_gb,
                "capabilities": [c.value for c in profile.capabilities],
                "languages": list(profile.supported_languages),
                "performance": {
                    "tokens_per_second": profile.avg_tokens_per_second,
                    "avg_latency_ms": profile.avg_latency_ms,
                    "success_rate": profile.get_success_rate(),
                    "total_requests": profile.total_requests
                },
                "task_scores": {
                    task.value: score 
                    for task, score in profile.accuracy_scores.items()
                }
            }
        
        return stats
    
    async def hot_swap_model(self, old_model_id: str, new_model_path: Path):
        """Hot-swap a model without downtime"""
        logger.info(f"Hot-swapping {old_model_id} with {new_model_path}")
        
        # Load new model
        new_profile = self._create_model_profile(new_model_path)
        if not new_profile:
            return {"error": "Failed to create profile for new model"}
        
        new_model = LlamaCppModel(new_model_path, new_profile)
        
        # Copy statistics from old model if exists
        if old_model_id in self.models:
            old_profile = self.models[old_model_id].get_profile()
            new_profile.accuracy_scores = old_profile.accuracy_scores.copy()
            new_profile.language_scores = old_profile.language_scores.copy()
        
        # Replace in registry
        self.models[new_profile.model_id] = new_model
        
        # Update task routing
        for task, model_ids in self.task_routing.items():
            if old_model_id in model_ids:
                model_ids.remove(old_model_id)
                model_ids.append(new_profile.model_id)
        
        # Remove old model
        if old_model_id in self.models:
            del self.models[old_model_id]
        
        logger.info(f"Successfully hot-swapped to {new_profile.name}")
        return {"success": True, "new_model_id": new_profile.model_id}