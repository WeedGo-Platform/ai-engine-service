"""
Multi-Model Orchestrator
Intelligently routes tasks to optimal models based on task type
Supports parallel processing and ensemble inference
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass
from functools import lru_cache
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import json
import psutil

from services.hot_swap_model_manager import get_hot_swap_manager
from services.intelligent_model_router import get_intelligent_router

logger = logging.getLogger(__name__)

class TaskType(Enum):
    """Task types for routing"""
    MATHEMATICAL = "mathematical"
    CODING = "coding"
    MULTILINGUAL = "multilingual"
    REASONING = "reasoning"
    CREATIVE = "creative"
    ANALYSIS = "analysis"
    GENERAL = "general"
    CANNABIS_SPECIFIC = "cannabis_specific"

@dataclass
class ModelCapability:
    """Model capability profile"""
    model_name: str
    strengths: List[TaskType]
    speed_score: float  # 0-1, higher is faster
    accuracy_score: float  # 0-1, higher is more accurate
    context_window: int
    memory_requirement_gb: float
    multilingual_score: float  # 0-1, higher is better

class MultiModelOrchestrator:
    """Orchestrates multiple models for optimal performance"""
    
    # Model capability profiles
    MODEL_PROFILES = {
        "llama33_70b": ModelCapability(
            model_name="llama33_70b",
            strengths=[TaskType.CODING, TaskType.REASONING, TaskType.GENERAL],
            speed_score=0.3,  # 3x faster than competitors but still large
            accuracy_score=0.95,
            context_window=131072,
            memory_requirement_gb=42.5,
            multilingual_score=0.7
        ),
        # Temporarily disabled - causing SIGABRT crashes
        # "qwq_32b": ModelCapability(
        #     model_name="qwq_32b",
        #     strengths=[TaskType.MATHEMATICAL, TaskType.REASONING, TaskType.ANALYSIS, TaskType.CODING],
        #     speed_score=0.5,
        #     accuracy_score=0.98,  # Best for math/reasoning
        #     context_window=32768,
        #     memory_requirement_gb=18.5,
        #     multilingual_score=0.6
        # ),
        "qwen_7b": ModelCapability(
            model_name="qwen_7b",
            strengths=[TaskType.MULTILINGUAL, TaskType.GENERAL],
            speed_score=0.8,
            accuracy_score=0.85,
            context_window=32768,
            memory_requirement_gb=4.4,
            multilingual_score=0.95  # Best multilingual
        ),
        # Temporarily disabled due to segmentation fault issue
        # "deepseek_coder": ModelCapability(
        #     model_name="deepseek_coder",
        #     strengths=[TaskType.CODING, TaskType.ANALYSIS],
        #     speed_score=0.85,
        #     accuracy_score=0.92,
        #     context_window=16384,
        #     memory_requirement_gb=4.0,
        #     multilingual_score=0.5
        # ),
        "mistral_7b_v3": ModelCapability(
            model_name="mistral_7b_v3",
            strengths=[TaskType.GENERAL, TaskType.CREATIVE, TaskType.CODING, TaskType.REASONING],
            speed_score=0.9,
            accuracy_score=0.82,
            context_window=32768,
            memory_requirement_gb=4.1,
            multilingual_score=0.6
        )
    }
    
    def __init__(self):
        self.hot_swap_manager = get_hot_swap_manager()
        self.intelligent_router = None  # Lazy load when needed
        self.executor = ThreadPoolExecutor(max_workers=3)
        self.task_history = []
        self.model_performance = {}
        self.use_intelligent_routing = False  # Can be enabled via config
        self._initialize_model_pool()
    
    def _initialize_model_pool(self):
        """Initialize model pool with available models"""
        available_models = self.hot_swap_manager.get_available_models()
        logger.info(f"Available models: {available_models}")
        
        # Verify which models are actually downloaded
        for model_name in available_models:
            if model_name in self.MODEL_PROFILES:
                config = self.hot_swap_manager.config["hot_swap"]["models"][model_name]
                model_path = config["path"]
                logger.info(f"Model {model_name} path: {model_path}")
    
    def detect_task_type(self, prompt: str) -> TaskType:
        """Detect task type from prompt"""
        prompt_lower = prompt.lower()
        
        # Mathematical indicators
        math_keywords = ["calculate", "solve", "equation", "integral", "derivative", 
                        "proof", "theorem", "mathematics", "algebra", "geometry"]
        if any(keyword in prompt_lower for keyword in math_keywords):
            return TaskType.MATHEMATICAL
        
        # Coding indicators
        code_keywords = ["code", "function", "implement", "debug", "program", 
                        "class", "method", "algorithm", "python", "javascript"]
        if any(keyword in prompt_lower for keyword in code_keywords):
            return TaskType.CODING
        
        # Multilingual indicators (non-English characters or language mentions)
        if any(ord(char) > 127 for char in prompt):
            return TaskType.MULTILINGUAL
        
        language_keywords = ["translate", "spanish", "french", "chinese", "arabic",
                           "japanese", "korean", "german", "portuguese"]
        if any(keyword in prompt_lower for keyword in language_keywords):
            return TaskType.MULTILINGUAL
        
        # Cannabis-specific
        cannabis_keywords = ["cannabis", "thc", "cbd", "strain", "terpene", 
                            "indica", "sativa", "dispensary", "budtender"]
        if any(keyword in prompt_lower for keyword in cannabis_keywords):
            return TaskType.CANNABIS_SPECIFIC
        
        # Reasoning indicators
        reasoning_keywords = ["explain", "why", "how", "analyze", "compare",
                            "evaluate", "assess", "logic", "reason"]
        if any(keyword in prompt_lower for keyword in reasoning_keywords):
            return TaskType.REASONING
        
        # Analysis indicators
        analysis_keywords = ["analyze", "review", "examine", "investigate",
                           "study", "research", "data", "statistics"]
        if any(keyword in prompt_lower for keyword in analysis_keywords):
            return TaskType.ANALYSIS
        
        # Creative indicators
        creative_keywords = ["write", "story", "poem", "creative", "imagine",
                           "design", "create", "artistic"]
        if any(keyword in prompt_lower for keyword in creative_keywords):
            return TaskType.CREATIVE
        
        return TaskType.GENERAL
    
    def is_model_available(self, model_name: str) -> bool:
        """Check if a model can be loaded without blocking"""
        # Check if model is currently loaded
        if self.hot_swap_manager.current_model_name == model_name:
            return True
        
        # Check memory requirements
        if model_name in self.MODEL_PROFILES:
            required_gb = self.MODEL_PROFILES[model_name].memory_requirement_gb
            available_gb = psutil.virtual_memory().available / (1024**3)
            
            # Add safety margin - don't attempt if less than required + 2GB buffer
            if available_gb < (required_gb + 2):
                logger.warning(f"Model {model_name} requires {required_gb}GB but only {available_gb:.1f}GB available")
                return False
        
        return True
    
    def select_optimal_model(self, task_type: TaskType, 
                            context_length: int = 0,
                            require_speed: bool = False,
                            prefer_current: bool = True) -> str:
        """Select optimal model for task with availability check"""
        
        current_model = self.hot_swap_manager.current_model_name
        
        # If prefer_current is True and current model can handle the task, use it
        if prefer_current and current_model and current_model in self.MODEL_PROFILES:
            profile = self.MODEL_PROFILES[current_model]
            if (task_type in profile.strengths or task_type == TaskType.GENERAL) and \
               context_length <= profile.context_window:
                logger.info(f"Using current model {current_model} for {task_type.value} task")
                return current_model
        
        candidates = []
        
        for model_name, profile in self.MODEL_PROFILES.items():
            # Skip if model is not available
            if not self.is_model_available(model_name):
                logger.debug(f"Skipping {model_name} - not available due to resource constraints")
                continue
            
            # Check if model handles this task type
            if task_type in profile.strengths or task_type == TaskType.GENERAL:
                # Check context window
                if context_length > profile.context_window:
                    continue
                
                # Calculate score
                score = 0
                
                # Task relevance score
                if task_type in profile.strengths:
                    score += 0.4
                
                # Accuracy score
                score += profile.accuracy_score * 0.3
                
                # Speed score (if required)
                if require_speed:
                    score += profile.speed_score * 0.3
                else:
                    score += profile.speed_score * 0.1
                
                # Multilingual bonus
                if task_type == TaskType.MULTILINGUAL:
                    score += profile.multilingual_score * 0.2
                
                # Bonus for already loaded model
                if model_name == current_model:
                    score += 0.2  # Prefer current model to avoid swapping
                
                candidates.append((model_name, score))
        
        if not candidates:
            # If no candidates and we have a current model, use it
            if current_model:
                return current_model
            return "mistral_7b_v3"  # Default fallback
        
        # Sort by score and return best available
        candidates.sort(key=lambda x: x[1], reverse=True)
        best_model = candidates[0][0]
        
        # Only log if we're changing models
        if best_model != current_model:
            logger.info(f"Selected {best_model} for {task_type.value} task (score: {candidates[0][1]:.2f})")
        
        return best_model
    
    def enable_intelligent_routing(self, enable: bool = True):
        """Enable or disable intelligent routing"""
        self.use_intelligent_routing = enable
        if enable and not self.intelligent_router:
            try:
                self.intelligent_router = get_intelligent_router()
                logger.info("Intelligent routing enabled")
            except Exception as e:
                logger.error(f"Failed to initialize intelligent router: {e}")
                self.use_intelligent_routing = False
    
    async def process_with_optimal_model(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Process prompt with optimal model selection"""
        
        # Use intelligent router if enabled
        if self.use_intelligent_routing and self.intelligent_router:
            return await self.intelligent_router.process_with_routing(prompt, **kwargs)
        
        # Otherwise use original logic
        start_time = time.time()
        
        # Detect task type
        task_type = self.detect_task_type(prompt)
        context_length = len(prompt.split())
        
        # Select optimal model
        optimal_model = self.select_optimal_model(
            task_type, 
            context_length,
            require_speed=kwargs.get("require_speed", False)
        )
        
        # Swap to optimal model if needed
        current_model = self.hot_swap_manager.current_model_name
        if current_model != optimal_model:
            logger.info(f"Swapping from {current_model} to {optimal_model}")
            success = self.hot_swap_manager.swap_model(optimal_model)
            if not success:
                logger.warning(f"Failed to swap to {optimal_model}, using current model")
                optimal_model = current_model
        
        # Generate response
        response = await self.hot_swap_manager.async_generate(prompt, **kwargs)
        
        # Track performance
        elapsed_time = time.time() - start_time
        self._track_performance(optimal_model, task_type, elapsed_time, response is not None)
        
        return {
            "response": response,
            "model_used": optimal_model,
            "task_type": task_type.value,
            "processing_time": elapsed_time
        }
    
    async def ensemble_inference(self, prompt: str, 
                                models: List[str] = None,
                                aggregation: str = "majority") -> Dict[str, Any]:
        """Run ensemble inference across multiple models"""
        
        if models is None:
            # Use top 3 models for the task
            task_type = self.detect_task_type(prompt)
            models = [
                self.select_optimal_model(task_type),
                "qwq_32b" if task_type == TaskType.MATHEMATICAL else "mistral_7b_v3",
                "qwen_7b" if task_type == TaskType.MULTILINGUAL else "mistral_7b_v2"
            ]
        
        logger.info(f"Running ensemble inference with models: {models}")
        
        # Run inference in parallel
        tasks = []
        for model in models:
            task = self._run_model_async(model, prompt)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter successful results
        successful_results = []
        for i, result in enumerate(results):
            if not isinstance(result, Exception) and result:
                successful_results.append({
                    "model": models[i],
                    "response": result
                })
        
        if not successful_results:
            return {"error": "All models failed"}
        
        # Aggregate results
        if aggregation == "majority":
            # For now, return the most common response pattern
            # In practice, this would be more sophisticated
            return {
                "ensemble_response": successful_results[0]["response"],
                "models_used": [r["model"] for r in successful_results],
                "aggregation_method": aggregation,
                "individual_responses": successful_results
            }
        elif aggregation == "best":
            # Return response from highest-scoring model
            best_model = self.MODEL_PROFILES[successful_results[0]["model"]]
            return {
                "ensemble_response": successful_results[0]["response"],
                "best_model": successful_results[0]["model"],
                "aggregation_method": aggregation
            }
        
        return {"ensemble_response": successful_results}
    
    async def _run_model_async(self, model_name: str, prompt: str) -> Optional[Dict]:
        """Run a specific model asynchronously with error recovery"""
        if not self.hot_swap_manager:
            return None
        
        # Skip models that have failed
        if hasattr(self, 'failed_models') and model_name in self.failed_models:
            logger.debug(f"Skipping failed model {model_name}")
            return None
        
        try:
            # Swap to model with error handling
            try:
                success = self.hot_swap_manager.swap_model(model_name)
                if not success:
                    if hasattr(self, 'failed_models'):
                        self.failed_models.add(model_name)
                    return None
            except Exception as swap_error:
                logger.error(f"Failed to swap to {model_name}: {swap_error}")
                if hasattr(self, 'failed_models'):
                    self.failed_models.add(model_name)
                return None
            
            # Generate response with timeout protection
            try:
                response = await asyncio.wait_for(
                    self.hot_swap_manager.async_generate(prompt),
                    timeout=30.0  # 30 second timeout
                )
                # Success - remove from failed list if exists
                if hasattr(self, 'failed_models'):
                    self.failed_models.discard(model_name)
                return response
            except asyncio.TimeoutError:
                logger.error(f"Model {model_name} timed out")
                if hasattr(self, 'failed_models'):
                    self.failed_models.add(model_name)
                return None
        except Exception as e:
            logger.error(f"Error running model {model_name}: {e}")
            if hasattr(self, 'failed_models'):
                self.failed_models.add(model_name)
            return None
    
    def _track_performance(self, model: str, task_type: TaskType, 
                          elapsed_time: float, success: bool):
        """Track model performance metrics"""
        if model not in self.model_performance:
            self.model_performance[model] = {
                "total_tasks": 0,
                "successful_tasks": 0,
                "total_time": 0,
                "task_types": {}
            }
        
        stats = self.model_performance[model]
        stats["total_tasks"] += 1
        if success:
            stats["successful_tasks"] += 1
        stats["total_time"] += elapsed_time
        
        # Track by task type
        task_key = task_type.value
        if task_key not in stats["task_types"]:
            stats["task_types"][task_key] = {
                "count": 0,
                "success": 0,
                "avg_time": 0
            }
        
        task_stats = stats["task_types"][task_key]
        task_stats["count"] += 1
        if success:
            task_stats["success"] += 1
        
        # Update average time
        prev_avg = task_stats["avg_time"]
        task_stats["avg_time"] = (prev_avg * (task_stats["count"] - 1) + elapsed_time) / task_stats["count"]
        
        # Add to history
        self.task_history.append({
            "timestamp": time.time(),
            "model": model,
            "task_type": task_type.value,
            "elapsed_time": elapsed_time,
            "success": success
        })
        
        # Keep only last 100 entries
        if len(self.task_history) > 100:
            self.task_history = self.task_history[-100:]
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get detailed performance report"""
        report = {
            "model_performance": self.model_performance,
            "recent_tasks": self.task_history[-10:],
            "model_rankings": {}
        }
        
        # Calculate rankings by task type
        for task_type in TaskType:
            rankings = []
            for model, stats in self.model_performance.items():
                if task_type.value in stats.get("task_types", {}):
                    task_stats = stats["task_types"][task_type.value]
                    if task_stats["count"] > 0:
                        success_rate = task_stats["success"] / task_stats["count"]
                        rankings.append({
                            "model": model,
                            "success_rate": success_rate,
                            "avg_time": task_stats["avg_time"],
                            "task_count": task_stats["count"]
                        })
            
            if rankings:
                rankings.sort(key=lambda x: x["success_rate"], reverse=True)
                report["model_rankings"][task_type.value] = rankings
        
        return report
    
    async def adaptive_routing(self, prompt: str, history: List[Dict] = None) -> Dict[str, Any]:
        """Adaptively route based on conversation history and context"""
        
        # Analyze conversation context
        if history:
            # Check if we're continuing a specific type of conversation
            recent_types = [self.detect_task_type(h.get("prompt", "")) for h in history[-3:]]
            most_common = max(set(recent_types), key=recent_types.count)
            
            # If consistent task type, optimize for it
            if recent_types.count(most_common) >= 2:
                logger.info(f"Detected consistent task type: {most_common.value}")
                return await self.process_with_optimal_model(
                    prompt,
                    task_type_hint=most_common
                )
        
        # Otherwise, use standard routing
        return await self.process_with_optimal_model(prompt)
    
    @lru_cache(maxsize=128)
    def estimate_token_count(self, text: str) -> int:
        """Estimate token count for text"""
        # Rough estimation: ~0.75 words per token
        return int(len(text.split()) / 0.75)
    
    async def chunked_processing(self, long_text: str, 
                                chunk_size: int = 2000) -> List[Dict[str, Any]]:
        """Process long text in chunks across multiple models"""
        
        # Split text into chunks
        words = long_text.split()
        chunks = []
        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i:i+chunk_size])
            chunks.append(chunk)
        
        logger.info(f"Processing {len(chunks)} chunks")
        
        # Process chunks in parallel with different models
        tasks = []
        for i, chunk in enumerate(chunks):
            # Rotate through fast models for chunks
            model = ["mistral_7b_v3", "qwen_7b", "deepseek_coder"][i % 3]
            task = self._process_chunk(chunk, model)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        return results
    
    async def _process_chunk(self, chunk: str, model: str) -> Dict[str, Any]:
        """Process a single chunk with specified model"""
        try:
            self.hot_swap_manager.swap_model(model)
            response = await self.hot_swap_manager.async_generate(chunk)
            return {
                "chunk": chunk[:100] + "...",
                "model": model,
                "response": response
            }
        except Exception as e:
            logger.error(f"Error processing chunk with {model}: {e}")
            return {"error": str(e), "model": model}

# Global instance
_orchestrator = None

def get_orchestrator() -> MultiModelOrchestrator:
    """Get or create orchestrator singleton"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = MultiModelOrchestrator()
    return _orchestrator