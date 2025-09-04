"""
Hot-Swap Model Manager
Allows runtime switching between different LLM models without restarting
"""

import os
import gc
import time
import json
import logging
import psutil
from pathlib import Path
from typing import Dict, Optional, Any, List
from threading import Lock
import asyncio
from llama_cpp import Llama

logger = logging.getLogger(__name__)

class HotSwapModelManager:
    """
    Manages multiple LLM models with hot-swapping capability
    """
    
    def __init__(self, config_path: str = "config/model_hot_swap.json"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.models: Dict[str, Optional[Llama]] = {}
        self.current_model_name: Optional[str] = None
        self.current_model: Optional[Llama] = None
        self.model_lock = Lock()
        self.performance_metrics = {}
        self.error_counts = {}
        
        # Initialize with default model
        self._initialize_default_model()
    
    def _load_config(self) -> Dict:
        """Load hot-swap configuration"""
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                return json.load(f)
        else:
            # Default configuration
            return {
                "hot_swap": {
                    "enabled": True,
                    "default_model": "mistral_7b",
                    "fallback_model": "mistral_7b_v3",
                    "models": {
                        "mistral_7b": {
                            "path": "models/base/mistral-7b-instruct-v0.2.Q4_K_M.gguf",
                            "context_size": 4096,
                            "gpu_layers": 35,
                            "temperature": 0.7
                        }
                    }
                }
            }
    
    def _initialize_default_model(self):
        """Initialize the default model on startup"""
        default_name = self.config["hot_swap"]["default_model"]
        logger.info(f"Initializing default model: {default_name}")
        
        try:
            self.swap_model(default_name)
            logger.info(f"✅ Default model {default_name} loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load default model {default_name}: {e}")
            # Try fallback
            fallback_name = self.config["hot_swap"]["fallback_model"]
            if fallback_name and fallback_name != default_name:
                logger.info(f"Attempting fallback model: {fallback_name}")
                try:
                    self.swap_model(fallback_name)
                    logger.info(f"✅ Fallback model {fallback_name} loaded")
                except Exception as e2:
                    logger.error(f"Failed to load fallback model: {e2}")
    
    def get_available_models(self) -> List[str]:
        """Get list of available models"""
        return list(self.config["hot_swap"]["models"].keys())
    
    def get_current_model_info(self) -> Dict:
        """Get information about current model"""
        if not self.current_model_name:
            return {"status": "no_model_loaded"}
        
        return {
            "name": self.current_model_name,
            "config": self.config["hot_swap"]["models"][self.current_model_name],
            "metrics": self.performance_metrics.get(self.current_model_name, {}),
            "error_count": self.error_counts.get(self.current_model_name, 0)
        }
    
    def swap_model(self, model_name: str, force: bool = False) -> bool:
        """
        Hot-swap to a different model
        
        Args:
            model_name: Name of model to swap to
            force: Force swap even if model is already loaded
        
        Returns:
            Success status
        """
        with self.model_lock:
            try:
                # Check if model is already loaded
                if not force and self.current_model_name == model_name:
                    logger.info(f"Model {model_name} is already loaded")
                    return True
                
                # Check if model config exists
                if model_name not in self.config["hot_swap"]["models"]:
                    logger.error(f"Model {model_name} not found in configuration")
                    return False
                
                model_config = self.config["hot_swap"]["models"][model_name]
                model_path = Path(model_config["path"])
                
                # Check if model file exists
                if not model_path.exists():
                    logger.error(f"Model file not found: {model_path}")
                    return False
                
                logger.info(f"Hot-swapping from {self.current_model_name} to {model_name}")
                
                # Track swap start time
                swap_start = time.time()
                
                # Unload current model with proper cleanup
                if self.current_model:
                    logger.info("Unloading current model...")
                    try:
                        # Properly close the model if it has a close method
                        if hasattr(self.current_model, 'close'):
                            self.current_model.close()
                    except Exception as e:
                        logger.warning(f"Error closing model: {e}")
                    
                    # Clear the reference
                    self.current_model = None
                    
                    # Force garbage collection multiple times for thorough cleanup
                    for _ in range(3):
                        gc.collect()
                    
                    # Give more time for cleanup to prevent buffer issues
                    time.sleep(1.0)
                
                # Check available memory
                memory_gb = psutil.virtual_memory().available / (1024**3)
                logger.info(f"Available memory: {memory_gb:.2f}GB")
                
                if memory_gb < self.config["hot_swap"].get("swap_conditions", {}).get("memory_threshold_gb", 4):
                    logger.warning(f"Low memory warning: {memory_gb:.2f}GB available")
                
                # Load new model
                logger.info(f"Loading model from {model_path}")
                
                try:
                    # Determine GPU layers based on available VRAM
                    n_gpu_layers = model_config.get("gpu_layers", 0)
                    
                    # Try to detect if GPU is available
                    try:
                        import torch
                        if torch.cuda.is_available():
                            vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
                            logger.info(f"GPU detected with {vram_gb:.2f}GB VRAM")
                        else:
                            n_gpu_layers = 0
                            logger.info("No GPU detected, using CPU")
                    except ImportError:
                        logger.info("PyTorch not available, assuming CPU mode")
                        n_gpu_layers = 0
                    
                    # Add safety checks for problematic models
                    problematic_models = ["deepseek_coder", "qwq_32b", "qwen_0.5b"]
                    if model_name in problematic_models:
                        logger.warning(f"Model {model_name} has known stability issues, loading with extra safety measures")
                        # Force CPU mode for problematic models
                        n_gpu_layers = 0
                        # Reduce context size for stability
                        model_config["context_size"] = min(model_config.get("context_size", 2048), 2048)
                    
                    # Create model with extra safety parameters
                    try:
                        self.current_model = Llama(
                            model_path=str(model_path),
                            n_ctx=model_config.get("context_size", 4096),
                            n_gpu_layers=n_gpu_layers,
                            n_threads=max(1, min(os.cpu_count() // 2, 8)),  # Cap threads at 8 for stability
                            use_mlock=False,  # Disable mlock to avoid memory issues
                            verbose=False,
                            seed=-1,  # Random seed
                            n_batch=256,  # Even smaller batch size for better stability
                            f16_kv=True,  # Use 16-bit key-value cache for memory efficiency
                            logits_all=False,  # Only compute logits for the last token
                            vocab_only=False,  # Load full model, not just vocabulary
                            use_mmap=True,  # Use memory mapping for better memory management
                            embedding=False  # Disable embeddings if not needed
                        )
                    except Exception as load_error:
                        logger.error(f"Failed to create Llama instance: {load_error}")
                        # Try with minimal parameters as fallback
                        logger.info("Attempting to load with minimal parameters...")
                        self.current_model = Llama(
                            model_path=str(model_path),
                            n_ctx=2048,  # Minimal context
                            n_gpu_layers=0,  # CPU only
                            n_threads=1,  # Single thread
                            use_mlock=False,
                            verbose=False
                        )
                    
                    self.current_model_name = model_name
                    
                    # Test the model with multiple attempts
                    test_passed = False
                    for attempt in range(3):
                        try:
                            logger.info(f"Testing model (attempt {attempt + 1}/3)...")
                            test_response = self.current_model(
                                "Hello",
                                max_tokens=10,
                                echo=False,
                                temperature=0.1,
                                top_p=0.95,
                                top_k=40
                            )
                            
                            if test_response and test_response.get("choices"):
                                test_passed = True
                                logger.info("Model test passed")
                                break
                            else:
                                logger.warning(f"Model test attempt {attempt + 1} returned empty response")
                                time.sleep(0.5)  # Brief pause before retry
                        except Exception as test_error:
                            logger.warning(f"Model test attempt {attempt + 1} failed: {test_error}")
                            time.sleep(0.5)
                    
                    if not test_passed:
                        raise Exception("Model test failed after 3 attempts")
                    
                    # Track swap time
                    swap_time = time.time() - swap_start
                    
                    # Update metrics
                    self.performance_metrics[model_name] = {
                        "load_time": swap_time,
                        "last_swap": time.time(),
                        "swap_count": self.performance_metrics.get(model_name, {}).get("swap_count", 0) + 1
                    }
                    
                    logger.info(f"✅ Successfully swapped to {model_name} in {swap_time:.2f}s")
                    
                    # Reset error count on successful swap
                    self.error_counts[model_name] = 0
                    
                    return True
                    
                except Exception as e:
                    logger.error(f"Failed to load model {model_name}: {e}")
                    self.error_counts[model_name] = self.error_counts.get(model_name, 0) + 1
                    
                    # Try fallback if this wasn't already a fallback attempt
                    fallback = self.config["hot_swap"]["fallback_model"]
                    if fallback and fallback != model_name:
                        logger.info(f"Attempting fallback to {fallback}")
                        return self.swap_model(fallback, force=True)
                    
                    return False
                    
            except Exception as e:
                logger.error(f"Critical error during model swap: {e}")
                return False
    
    def generate(self, prompt: str, **kwargs) -> Optional[Dict]:
        """
        Generate response using current model with automatic fallback
        """
        if not self.current_model:
            logger.error("No model loaded")
            # Try to load fallback model
            fallback = self.config["hot_swap"].get("fallback_model")
            if fallback:
                logger.info(f"Attempting to load fallback model: {fallback}")
                if self.swap_model(fallback):
                    logger.info("Fallback model loaded successfully")
                else:
                    return None
            else:
                return None
        
        # Ensure thread safety
        with self.model_lock:
            try:
                # Track generation start
                gen_start = time.time()
                
                # Set default parameters
                params = {
                    "max_tokens": kwargs.get("max_tokens", 512),
                    "temperature": kwargs.get("temperature", 
                        self.config["hot_swap"]["models"][self.current_model_name].get("temperature", 0.7)),
                    "echo": kwargs.get("echo", False),
                    "stop": kwargs.get("stop", ["\n\n", "Human:", "User:"])
                }
                
                # Generate response with timeout protection
                try:
                    response = self.current_model(prompt, **params)
                except Exception as gen_error:
                    logger.error(f"Generation error: {gen_error}")
                    # If generation fails, it might be a buffer issue - try reloading
                    if "GGML_ASSERT" in str(gen_error) or "buffer" in str(gen_error).lower():
                        logger.warning("Detected buffer issue, attempting model reload...")
                        if self.swap_model(self.current_model_name, force=True):
                            # Retry generation once after reload
                            response = self.current_model(prompt, **params)
                        else:
                            raise gen_error
                    else:
                        raise gen_error
                
                # Track generation time
                gen_time = time.time() - gen_start
                
                # Update performance metrics
                if self.current_model_name:
                    metrics = self.performance_metrics.setdefault(self.current_model_name, {})
                    metrics["last_generation"] = gen_time
                    metrics["avg_generation_time"] = (
                        metrics.get("avg_generation_time", gen_time) * 0.9 + gen_time * 0.1
                    )
                    metrics["generation_count"] = metrics.get("generation_count", 0) + 1
                
                # Check if we should swap based on performance
                self._check_auto_swap(gen_time)
                
                return response
                
            except Exception as e:
                logger.error(f"Generation failed with {self.current_model_name}: {e}")
                
                # Track error
                self.error_counts[self.current_model_name] = self.error_counts.get(self.current_model_name, 0) + 1
                
                # Check if we should swap due to errors
                if self.error_counts[self.current_model_name] >= self.config["hot_swap"]["swap_conditions"].get("error_threshold", 3):
                    logger.warning(f"Error threshold reached for {self.current_model_name}, attempting swap")
                    fallback = self.config["hot_swap"]["fallback_model"]
                    if fallback and fallback != self.current_model_name:
                        if self.swap_model(fallback):
                            # Retry with new model
                            return self.generate(prompt, **kwargs)
                
                return None
    
    def _check_auto_swap(self, last_gen_time: float):
        """Check if automatic swap should occur based on performance"""
        if not self.config["hot_swap"].get("enabled", True):
            return
        
        # Check latency threshold
        latency_threshold = self.config["hot_swap"]["swap_conditions"].get("latency_threshold_ms", 1000) / 1000
        
        if last_gen_time > latency_threshold:
            logger.warning(f"Generation took {last_gen_time:.2f}s, exceeding threshold of {latency_threshold}s")
            
            # Disabled auto-swap to avoid problematic models
            # # Find a faster model
            # current_size = self._estimate_model_size(self.current_model_name)
            # for model_name in self.get_available_models():
            #     if model_name != self.current_model_name:
            #         model_size = self._estimate_model_size(model_name)
            #         if model_size < current_size:
            #             logger.info(f"Attempting swap to smaller/faster model: {model_name}")
            #             self.swap_model(model_name)
            #             break
    
    def _estimate_model_size(self, model_name: str) -> float:
        """Estimate model size from filename"""
        if not model_name or model_name not in self.config["hot_swap"]["models"]:
            return float('inf')
        
        path = self.config["hot_swap"]["models"][model_name]["path"]
        
        # Extract size from common naming patterns
        if "70b" in path.lower():
            return 70
        elif "14b" in path.lower():
            return 14
        elif "8b" in path.lower():
            return 8
        elif "7b" in path.lower():
            return 7
        elif "3b" in path.lower():
            return 3
        elif "mini" in path.lower():
            return 2
        
        return 10  # Default medium size
    
    async def async_generate(self, prompt: str, **kwargs) -> Optional[Dict]:
        """Async wrapper for generation"""
        loop = asyncio.get_event_loop()
        # Use a lambda to properly pass kwargs
        return await loop.run_in_executor(
            None, 
            lambda: self.generate(prompt, **kwargs)
        )
    
    def get_performance_report(self) -> Dict:
        """Get performance report for all models"""
        report = {
            "current_model": self.current_model_name,
            "models": {}
        }
        
        for model_name in self.get_available_models():
            metrics = self.performance_metrics.get(model_name, {})
            errors = self.error_counts.get(model_name, 0)
            
            report["models"][model_name] = {
                "loaded": model_name == self.current_model_name,
                "metrics": metrics,
                "error_count": errors,
                "health": "healthy" if errors < 3 else "unhealthy"
            }
        
        return report

# Global instance
_hot_swap_manager = None

def get_hot_swap_manager() -> HotSwapModelManager:
    """Get or create hot swap manager singleton"""
    global _hot_swap_manager
    if _hot_swap_manager is None:
        _hot_swap_manager = HotSwapModelManager()
    return _hot_swap_manager