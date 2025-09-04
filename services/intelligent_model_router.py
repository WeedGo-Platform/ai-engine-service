"""
Intelligent Model Router
Uses a lightweight model to intelligently route tasks to appropriate models
Bootstrap approach: Start with smallest/fastest model as router
"""

import logging
import time
import json
import psutil
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum

from services.hot_swap_model_manager import get_hot_swap_manager

logger = logging.getLogger(__name__)

class ModelSize(Enum):
    """Model size categories"""
    TINY = "tiny"      # < 2GB
    SMALL = "small"    # 2-4GB  
    MEDIUM = "medium"  # 4-8GB
    LARGE = "large"    # 8-20GB
    XLARGE = "xlarge"  # > 20GB

@dataclass
class ModelProfile:
    """Lightweight model profile for routing decisions"""
    name: str
    size: ModelSize
    speed_ms: int  # Average response time in ms
    capabilities: List[str]
    memory_gb: float

class IntelligentModelRouter:
    """
    Intelligent router that uses a lightweight model to make routing decisions
    """
    
    # Model profiles ordered by size (smallest first for bootstrapping)
    MODEL_HIERARCHY = {
        "qwen_0.5b": ModelProfile(
            name="qwen_0.5b",
            size=ModelSize.TINY,
            speed_ms=100,  # Ultra fast
            capabilities=["router", "simple", "classification"],
            memory_gb=0.5
        ),
        "phi3_mini": ModelProfile(
            name="phi3_mini",
            size=ModelSize.TINY,
            speed_ms=200,
            capabilities=["simple", "general", "lightweight"],
            memory_gb=1.0
        ),
        "qwen_3b": ModelProfile(
            name="qwen_3b",
            size=ModelSize.SMALL,
            speed_ms=500,
            capabilities=["general", "multilingual", "moderate"],
            memory_gb=2.0
        ),
        "llama2_7b": ModelProfile(
            name="llama2_7b",
            size=ModelSize.SMALL,
            speed_ms=2000,
            capabilities=["general", "simple"],
            memory_gb=3.8
        ),
        "mistral_7b_v2": ModelProfile(
            name="mistral_7b_v2", 
            size=ModelSize.SMALL,
            speed_ms=2500,
            capabilities=["general", "reasoning"],
            memory_gb=4.1
        ),
        "mistral_7b_v3": ModelProfile(
            name="mistral_7b_v3",
            size=ModelSize.SMALL,
            speed_ms=2500,
            capabilities=["general", "coding", "reasoning", "creative"],
            memory_gb=4.1
        ),
        "qwen_7b": ModelProfile(
            name="qwen_7b",
            size=ModelSize.SMALL,
            speed_ms=2200,
            capabilities=["multilingual", "general"],
            memory_gb=4.4
        ),
        # Disabled problematic models
        # "deepseek_coder": ModelProfile(...),  # Causes segfaults
        # "qwq_32b": ModelProfile(...),  # Causes SIGABRT
        "llama33_70b": ModelProfile(
            name="llama33_70b",
            size=ModelSize.XLARGE,
            speed_ms=120000,  # Very slow on CPU
            capabilities=["coding", "reasoning", "general", "complex"],
            memory_gb=42.5
        )
    }
    
    ROUTER_PROMPT_TEMPLATE = """Task: {query}

Choose model:
- phi3_mini: simple chat
- qwen_3b: moderate tasks  
- mistral_7b_v3: coding/complex
- qwen_7b: multilingual

Reply with model name only:"""
    
    def __init__(self):
        self.hot_swap_manager = get_hot_swap_manager()
        self.router_model = None
        self.router_model_name = None
        self.performance_history = {}
        self._bootstrap_router()
    
    def _bootstrap_router(self):
        """Bootstrap with the smallest available model as router"""
        available_gb = psutil.virtual_memory().available / (1024**3)
        
        # Find smallest model that fits in memory
        for model_name, profile in self.MODEL_HIERARCHY.items():
            if profile.memory_gb + 2 < available_gb:  # 2GB buffer
                logger.info(f"Bootstrapping router with {model_name} ({profile.memory_gb}GB)")
                
                # Check if already loaded
                if self.hot_swap_manager.current_model_name == model_name:
                    self.router_model_name = model_name
                    logger.info(f"Router using existing model: {model_name}")
                    return True
                
                # Try to load as router
                success = self.hot_swap_manager.swap_model(model_name)
                if success:
                    self.router_model_name = model_name
                    logger.info(f"✅ Router bootstrapped with {model_name}")
                    return True
        
        logger.error("Failed to bootstrap router model")
        return False
    
    def analyze_query_complexity(self, query: str) -> str:
        """Analyze query complexity using simple heuristics"""
        query_lower = query.lower()
        word_count = len(query.split())
        
        # Simple heuristics for fast routing without model inference
        complexity_indicators = {
            "simple": ["hello", "hi", "hey", "thanks", "bye", "yes", "no"],
            "coding": ["function", "code", "implement", "debug", "class", "algorithm"],
            "math": ["calculate", "solve", "equation", "integral", "derivative"],
            "multilingual": any(ord(c) > 127 for c in query),
            "complex": ["explain", "analyze", "compare", "design", "architect"]
        }
        
        # Quick routing decisions
        if any(word in query_lower for word in complexity_indicators["simple"]):
            return "simple"
        elif any(word in query_lower for word in complexity_indicators["coding"]):
            return "coding"
        elif any(word in query_lower for word in complexity_indicators["math"]):
            return "math"
        elif complexity_indicators["multilingual"]:
            return "multilingual"
        elif any(word in query_lower for word in complexity_indicators["complex"]) or word_count > 50:
            return "complex"
        else:
            return "general"
    
    def select_model_for_task(self, query: str, require_speed: bool = False) -> str:
        """Select optimal model for task using intelligent routing"""
        
        available_gb = psutil.virtual_memory().available / (1024**3)
        complexity = self.analyze_query_complexity(query)
        
        logger.info(f"Query complexity: {complexity}, Available memory: {available_gb:.1f}GB")
        
        # Fast path: Use heuristics for common cases
        if complexity == "simple" or require_speed:
            # Use smallest available model
            for model_name, profile in self.MODEL_HIERARCHY.items():
                if profile.memory_gb + 2 < available_gb:
                    return model_name
        
        elif complexity == "multilingual":
            # Prefer Qwen for multilingual
            if "qwen_7b" in self.MODEL_HIERARCHY and \
               self.MODEL_HIERARCHY["qwen_7b"].memory_gb + 2 < available_gb:
                return "qwen_7b"
        
        elif complexity in ["coding", "math", "complex"]:
            # Prefer Mistral v3 for these tasks (good balance)
            if "mistral_7b_v3" in self.MODEL_HIERARCHY and \
               self.MODEL_HIERARCHY["mistral_7b_v3"].memory_gb + 2 < available_gb:
                return "mistral_7b_v3"
        
        # Default: Use current model if it can handle the task
        current = self.hot_swap_manager.current_model_name
        if current and current in self.MODEL_HIERARCHY:
            return current
        
        # Fallback to smallest available
        for model_name, profile in self.MODEL_HIERARCHY.items():
            if profile.memory_gb + 2 < available_gb:
                return model_name
        
        return "mistral_7b_v3"  # Ultimate fallback
    
    def route_with_model(self, query: str) -> str:
        """Use the router model itself to decide routing (advanced mode)"""
        if not self.router_model_name:
            # Fallback to heuristic routing
            return self.select_model_for_task(query)
        
        try:
            # Prepare routing prompt
            available_gb = psutil.virtual_memory().available / (1024**3)
            prompt = self.ROUTER_PROMPT_TEMPLATE.format(
                query=query,
                available_gb=available_gb
            )
            
            # Get routing decision from model
            response = self.hot_swap_manager.generate(
                prompt,
                max_tokens=20,
                temperature=0.1
            )
            
            if response and response.get("choices"):
                model_name = response["choices"][0]["text"].strip().lower()
                
                # Validate model name
                for key in self.MODEL_HIERARCHY.keys():
                    if key.lower() in model_name:
                        logger.info(f"Router selected: {key} for query")
                        return key
            
        except Exception as e:
            logger.error(f"Router model failed: {e}")
        
        # Fallback to heuristic
        return self.select_model_for_task(query)
    
    async def process_with_routing(self, query: str, **kwargs) -> Dict:
        """Process query with intelligent routing"""
        
        start_time = time.time()
        
        # Get routing decision
        if kwargs.get("use_model_routing", False):
            target_model = self.route_with_model(query)
        else:
            target_model = self.select_model_for_task(
                query, 
                require_speed=kwargs.get("require_speed", False)
            )
        
        logger.info(f"Routing to model: {target_model}")
        
        # Check if we need to swap
        current = self.hot_swap_manager.current_model_name
        if current != target_model:
            # Check if target model can be loaded
            available_gb = psutil.virtual_memory().available / (1024**3)
            required_gb = self.MODEL_HIERARCHY.get(target_model, 
                ModelProfile("unknown", ModelSize.MEDIUM, 5000, [], 5.0)).memory_gb
            
            if required_gb + 2 > available_gb:
                logger.warning(f"Cannot load {target_model} ({required_gb}GB), using {current}")
                target_model = current
            else:
                success = self.hot_swap_manager.swap_model(target_model)
                if not success:
                    logger.warning(f"Failed to swap to {target_model}, using {current}")
                    target_model = current
        
        # Generate response
        response = await self.hot_swap_manager.async_generate(query, **kwargs)
        
        # Track performance
        elapsed = time.time() - start_time
        self._track_performance(target_model, elapsed, bool(response))
        
        return {
            "response": response,
            "model_used": target_model,
            "routing_method": "model" if kwargs.get("use_model_routing") else "heuristic",
            "processing_time": elapsed
        }
    
    def _track_performance(self, model: str, time_sec: float, success: bool):
        """Track model performance for adaptive routing"""
        if model not in self.performance_history:
            self.performance_history[model] = {
                "total_requests": 0,
                "successful": 0,
                "total_time": 0,
                "avg_time": 0
            }
        
        stats = self.performance_history[model]
        stats["total_requests"] += 1
        if success:
            stats["successful"] += 1
        stats["total_time"] += time_sec
        stats["avg_time"] = stats["total_time"] / stats["total_requests"]
    
    def get_router_status(self) -> Dict:
        """Get current router status"""
        return {
            "router_model": self.router_model_name,
            "current_model": self.hot_swap_manager.current_model_name,
            "available_models": list(self.MODEL_HIERARCHY.keys()),
            "performance_history": self.performance_history,
            "memory_available_gb": psutil.virtual_memory().available / (1024**3)
        }

# Singleton instance
_router = None

def get_intelligent_router() -> IntelligentModelRouter:
    """Get or create router singleton"""
    global _router
    if _router is None:
        _router = IntelligentModelRouter()
    return _router