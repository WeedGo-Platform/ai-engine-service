"""
Fast Extraction Model Manager
Optimized for sub-500ms extraction responses
"""

import os
import time
import logging
from pathlib import Path
from typing import Dict, Optional
from threading import Lock
from llama_cpp import Llama

logger = logging.getLogger(__name__)

class FastExtractorModel:
    """
    Optimized model manager specifically for fast extraction tasks
    Uses minimal context, optimized threading, and cached model
    """
    
    def __init__(self):
        self.model = None
        self.model_lock = Lock()
        # Use phi3_mini - it's smaller and faster for extraction
        self.model_path = "models/base/Phi-3-mini-4k-instruct.Q4_K_M.gguf"
        self.performance_metrics = {
            "count": 0,
            "total_time": 0,
            "avg_time": 0,
            "last_time": 0
        }
        self._initialize_fast_model()
    
    def _initialize_fast_model(self):
        """Initialize model with speed-optimized parameters"""
        model_file = Path(self.model_path)
        
        if not model_file.exists():
            logger.error(f"Model not found: {self.model_path}")
            return False
        
        try:
            logger.info("Loading FastExtractor model with optimized settings...")
            
            # Detect optimal thread count (use all available cores for speed)
            cpu_count = os.cpu_count() or 4
            n_threads = min(cpu_count, 16)  # Cap at 16 for stability
            
            logger.info(f"Using {n_threads} threads for maximum speed")
            
            # Load with speed-optimized parameters
            self.model = Llama(
                model_path=str(model_file),
                n_ctx=256,  # Even smaller context for faster processing
                n_batch=256,  # Match batch to context
                n_threads=n_threads,  # Use all available threads
                n_threads_batch=n_threads,  # Batch processing threads
                n_gpu_layers=0,  # CPU mode for now
                seed=42,  # Fixed seed for consistency
                f16_kv=True,  # 16-bit cache for speed
                logits_all=False,  # Only last token
                vocab_only=False,
                use_mmap=True,  # Memory mapping
                use_mlock=False,  # No memory locking
                embedding=False,
                rope_freq_base=10000.0,  # Standard RoPE
                rope_freq_scale=1.0,
                verbose=False
            )
            
            # Warm up the model with a test prompt
            logger.info("Warming up model...")
            warmup_start = time.time()
            
            test_prompt = "Extract: product"
            for i in range(3):  # Multiple warmup runs
                response = self.model(
                    test_prompt,
                    max_tokens=10,
                    temperature=0.1,
                    top_p=0.9,
                    echo=False,
                    stop=[]
                )
            
            warmup_time = time.time() - warmup_start
            logger.info(f"Model warmed up in {warmup_time:.2f}s")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize FastExtractor: {e}")
            return False
    
    def extract(self, prompt: str, max_tokens: int = 150) -> Optional[str]:
        """
        Fast extraction with minimal overhead
        Target: <500ms response time
        """
        if not self.model:
            logger.error("Model not initialized")
            return None
        
        with self.model_lock:
            try:
                start_time = time.time()
                
                # Generate with speed-optimized parameters
                response = self.model(
                    prompt,
                    max_tokens=max_tokens,
                    temperature=0.01,  # Near-deterministic for speed
                    top_p=0.5,  # Reduce search space
                    top_k=5,  # Very limited vocabulary for maximum speed
                    repeat_penalty=1.0,
                    echo=False,
                    stop=["\n", "}", "User:", "Human:"],  # Stop early
                    stream=False
                )
                
                # Extract text from response
                if response and response.get("choices"):
                    text = response["choices"][0].get("text", "")
                    
                    # Track metrics
                    elapsed = time.time() - start_time
                    self.performance_metrics["count"] += 1
                    self.performance_metrics["total_time"] += elapsed
                    self.performance_metrics["avg_time"] = (
                        self.performance_metrics["total_time"] / 
                        self.performance_metrics["count"]
                    )
                    self.performance_metrics["last_time"] = elapsed
                    
                    if elapsed < 0.5:
                        logger.info(f"✅ Fast extraction in {elapsed*1000:.0f}ms")
                    else:
                        logger.warning(f"⚠️ Slow extraction: {elapsed*1000:.0f}ms")
                    
                    return text
                
                return None
                
            except Exception as e:
                logger.error(f"Extraction error: {e}")
                return None
    
    def get_metrics(self) -> Dict:
        """Get performance metrics"""
        return {
            "avg_response_ms": self.performance_metrics["avg_time"] * 1000,
            "last_response_ms": self.performance_metrics["last_time"] * 1000,
            "total_requests": self.performance_metrics["count"],
            "model": "qwen_0.5b_fast"
        }

# Global instance for reuse
_fast_extractor = None

def get_fast_extractor() -> FastExtractorModel:
    """Get or create fast extractor singleton"""
    global _fast_extractor
    if _fast_extractor is None:
        _fast_extractor = FastExtractorModel()
    return _fast_extractor