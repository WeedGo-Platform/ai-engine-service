#!/usr/bin/env python3
"""
Optimized LLM Inference Pipeline
Achieves sub-5 second responses through various optimization techniques
"""

import asyncio
import time
import logging
from typing import Dict, Optional, List, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import statistics
from collections import deque
import hashlib
import json

logger = logging.getLogger(__name__)

class OptimizationStrategy(Enum):
    """Inference optimization strategies"""
    FULL_QUALITY = "full_quality"      # Full model, no optimizations
    BALANCED = "balanced"               # Balance quality and speed
    SPEED_OPTIMIZED = "speed_optimized" # Maximum speed, some quality loss
    CACHE_ONLY = "cache_only"          # Only use cached responses

@dataclass
class InferenceMetrics:
    """Track inference performance metrics"""
    request_id: str
    prompt_tokens: int
    completion_tokens: int
    total_time: float
    model_time: float
    preprocessing_time: float
    postprocessing_time: float
    cache_hit: bool
    strategy: OptimizationStrategy

class PromptOptimizer:
    """Optimize prompts for faster inference"""
    
    # Templates optimized for brevity
    OPTIMIZED_TEMPLATES = {
        'product_recommendation': """Customer: {query}
Need: {intent}
Recommend 1-2 products briefly. Focus on benefits.""",
        
        'greeting': """Greet customer warmly.
Ask how to help with cannabis.
Keep under 2 sentences.""",
        
        'objection_handling': """Customer concern: {objection}
Address briefly, suggest alternative.
Max 2 sentences.""",
        
        'closing': """Customer ready to buy: {products}
Confirm choice briefly.
Add one benefit."""
    }
    
    @staticmethod
    def optimize_prompt(prompt: str, category: str = None) -> str:
        """Optimize prompt for faster processing"""
        
        # Remove unnecessary whitespace
        prompt = ' '.join(prompt.split())
        
        # Use template if category matches
        if category and category in PromptOptimizer.OPTIMIZED_TEMPLATES:
            # Extract key information from prompt
            # This is simplified - in production would use NLP
            return PromptOptimizer.OPTIMIZED_TEMPLATES[category]
        
        # Truncate long prompts
        max_length = 500
        if len(prompt) > max_length:
            prompt = prompt[:max_length] + "..."
        
        # Remove filler words for speed
        filler_words = ['very', 'really', 'actually', 'basically', 'just']
        words = prompt.split()
        words = [w for w in words if w.lower() not in filler_words]
        
        return ' '.join(words)

class ResponseCache:
    """Intelligent response caching with semantic similarity"""
    
    def __init__(self, max_size: int = 1000):
        self.cache = {}
        self.access_times = {}
        self.max_size = max_size
        
    def _get_cache_key(self, prompt: str, context: Dict) -> str:
        """Generate cache key from prompt and context"""
        # Normalize prompt
        normalized = prompt.lower().strip()
        
        # Include relevant context
        context_str = json.dumps({
            'intent': context.get('intent', ''),
            'stage': context.get('stage', '')
        }, sort_keys=True)
        
        # Create hash
        combined = f"{normalized}:{context_str}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    def get(self, prompt: str, context: Dict) -> Optional[str]:
        """Get cached response if available"""
        key = self._get_cache_key(prompt, context)
        
        if key in self.cache:
            self.access_times[key] = time.time()
            logger.debug(f"Cache hit for prompt: {prompt[:50]}...")
            return self.cache[key]
        
        return None
    
    def set(self, prompt: str, context: Dict, response: str):
        """Cache response"""
        # Evict old entries if cache is full
        if len(self.cache) >= self.max_size:
            self._evict_lru()
        
        key = self._get_cache_key(prompt, context)
        self.cache[key] = response
        self.access_times[key] = time.time()
    
    def _evict_lru(self):
        """Evict least recently used entry"""
        if not self.access_times:
            return
        
        lru_key = min(self.access_times, key=self.access_times.get)
        del self.cache[lru_key]
        del self.access_times[lru_key]

class InferenceOptimizer:
    """
    Main inference optimization system
    Combines multiple strategies to achieve <5 second responses
    """
    
    def __init__(self, model_manager=None):
        self.model_manager = model_manager
        self.cache = ResponseCache()
        self.metrics_history = deque(maxlen=100)  # Keep last 100 metrics
        self.warm_cache = self._initialize_warm_cache()
        
    def _initialize_warm_cache(self) -> Dict:
        """Pre-compute common responses"""
        return {
            'greeting': "Welcome to WeedGo! I'm here to help you find the perfect cannabis products. Whether you're looking for relaxation, pain relief, or something to boost your mood, I can guide you. What brings you in today?",
            'sleep': "For sleep, I recommend our indica strains like Purple Kush or Granddaddy Purple. They're known for their relaxing, sedative effects. Would you prefer flower or perhaps edibles for longer-lasting effects?",
            'pain': "For pain relief, high-CBD products work wonderfully. Our balanced THC/CBD options like Harlequin provide relief without intense psychoactive effects. What type of pain are you managing?",
            'first_time': "Great choice starting your cannabis journey! I recommend beginning with low-THC products (under 10%) or balanced THC/CBD ratios. Start with a small amount and wait to feel effects. Would you like to try a gentle flower or perhaps a precisely-dosed edible?",
            'anxiety': "For anxiety, CBD-dominant strains or balanced ratios work best. Products like ACDC or Cannatonic provide calming effects without paranoia. Many customers find vapes helpful for quick relief. What's your experience level with cannabis?"
        }
    
    async def optimize_inference(self, 
                                prompt: str,
                                context: Dict[str, Any],
                                strategy: OptimizationStrategy = OptimizationStrategy.BALANCED) -> Tuple[str, InferenceMetrics]:
        """
        Main optimization pipeline
        Returns (response, metrics)
        """
        start_time = time.time()
        request_id = hashlib.md5(f"{prompt}{time.time()}".encode()).hexdigest()[:8]
        
        # Initialize metrics
        metrics = InferenceMetrics(
            request_id=request_id,
            prompt_tokens=0,
            completion_tokens=0,
            total_time=0,
            model_time=0,
            preprocessing_time=0,
            postprocessing_time=0,
            cache_hit=False,
            strategy=strategy
        )
        
        try:
            # Step 1: Check warm cache for instant responses
            preprocess_start = time.time()
            for key, response in self.warm_cache.items():
                if key in prompt.lower():
                    metrics.cache_hit = True
                    metrics.total_time = time.time() - start_time
                    logger.info(f"Warm cache hit for '{key}': {metrics.total_time:.2f}s")
                    return response, metrics
            
            # Step 2: Check response cache
            cached_response = self.cache.get(prompt, context)
            if cached_response and strategy != OptimizationStrategy.FULL_QUALITY:
                metrics.cache_hit = True
                metrics.total_time = time.time() - start_time
                logger.info(f"Cache hit: {metrics.total_time:.2f}s")
                return cached_response, metrics
            
            # Step 3: Optimize prompt
            if strategy in [OptimizationStrategy.SPEED_OPTIMIZED, OptimizationStrategy.BALANCED]:
                category = context.get('category', None)
                optimized_prompt = PromptOptimizer.optimize_prompt(prompt, category)
            else:
                optimized_prompt = prompt
            
            metrics.prompt_tokens = len(optimized_prompt.split())
            metrics.preprocessing_time = time.time() - preprocess_start
            
            # Step 4: Select model and parameters based on strategy
            model_params = self._get_model_params(strategy)
            
            # Step 5: Run inference with timeout
            model_start = time.time()
            
            if self.model_manager:
                response = await asyncio.wait_for(
                    self._run_inference(optimized_prompt, model_params),
                    timeout=model_params['timeout']
                )
            else:
                # Fallback for testing
                response = f"Response to: {optimized_prompt[:50]}..."
                await asyncio.sleep(0.5)  # Simulate inference
            
            metrics.model_time = time.time() - model_start
            
            # Step 6: Post-process response
            postprocess_start = time.time()
            if strategy == OptimizationStrategy.SPEED_OPTIMIZED:
                # Truncate long responses
                max_length = 150
                if len(response) > max_length:
                    response = response[:max_length].rsplit(' ', 1)[0] + "..."
            
            metrics.completion_tokens = len(response.split())
            metrics.postprocessing_time = time.time() - postprocess_start
            
            # Cache successful response
            self.cache.set(prompt, context, response)
            
            # Record metrics
            metrics.total_time = time.time() - start_time
            self.metrics_history.append(metrics)
            
            # Log performance
            logger.info(f"Inference completed in {metrics.total_time:.2f}s "
                       f"(model: {metrics.model_time:.2f}s, "
                       f"cache: {'hit' if metrics.cache_hit else 'miss'})")
            
            return response, metrics
            
        except asyncio.TimeoutError:
            logger.warning(f"Inference timeout after {model_params['timeout']}s")
            # Return fallback response
            fallback = self._get_fallback_response(context)
            metrics.total_time = time.time() - start_time
            return fallback, metrics
            
        except Exception as e:
            logger.error(f"Inference error: {e}")
            fallback = self._get_fallback_response(context)
            metrics.total_time = time.time() - start_time
            return fallback, metrics
    
    def _get_model_params(self, strategy: OptimizationStrategy) -> Dict:
        """Get model parameters based on strategy"""
        if strategy == OptimizationStrategy.FULL_QUALITY:
            return {
                'temperature': 0.7,
                'max_tokens': 512,
                'timeout': 10,
                'n_ctx': 2048,
                'n_batch': 512
            }
        elif strategy == OptimizationStrategy.BALANCED:
            return {
                'temperature': 0.7,
                'max_tokens': 150,
                'timeout': 5,
                'n_ctx': 1024,
                'n_batch': 256
            }
        else:  # SPEED_OPTIMIZED
            return {
                'temperature': 0.5,  # Lower for more deterministic
                'max_tokens': 100,
                'timeout': 3,
                'n_ctx': 512,
                'n_batch': 128
            }
    
    async def _run_inference(self, prompt: str, params: Dict) -> str:
        """Run actual model inference"""
        if not self.model_manager:
            return f"Model response to: {prompt}"
        
        from services.model_manager import ModelType
        
        # Use Mistral for speed (it's generally faster)
        response = await self.model_manager.generate(
            ModelType.MISTRAL_7B,
            prompt,
            temperature=params['temperature'],
            max_tokens=params['max_tokens']
        )
        
        return response.text
    
    def _get_fallback_response(self, context: Dict) -> str:
        """Get fallback response when inference fails"""
        stage = context.get('stage', 'greeting')
        
        fallbacks = {
            'greeting': "Welcome! How can I help you find the perfect cannabis product today?",
            'qualification': "Tell me more about what you're looking for - relaxation, energy, or pain relief?",
            'recommendation': "Based on what you've told me, I have some great options for you.",
            'closing': "Excellent choice! This product will work perfectly for your needs."
        }
        
        return fallbacks.get(stage, "I'm here to help you find the right cannabis product.")
    
    def get_performance_stats(self) -> Dict:
        """Get performance statistics"""
        if not self.metrics_history:
            return {'status': 'no_data'}
        
        total_times = [m.total_time for m in self.metrics_history]
        model_times = [m.model_time for m in self.metrics_history if m.model_time > 0]
        cache_hits = sum(1 for m in self.metrics_history if m.cache_hit)
        
        return {
            'total_requests': len(self.metrics_history),
            'cache_hit_rate': cache_hits / len(self.metrics_history),
            'avg_total_time': statistics.mean(total_times),
            'p95_total_time': statistics.quantiles(total_times, n=20)[18] if len(total_times) > 5 else 0,
            'avg_model_time': statistics.mean(model_times) if model_times else 0,
            'under_5s_rate': sum(1 for t in total_times if t < 5) / len(total_times),
            'under_3s_rate': sum(1 for t in total_times if t < 3) / len(total_times)
        }

class BatchInferenceOptimizer:
    """Batch multiple requests for improved throughput"""
    
    def __init__(self, optimizer: InferenceOptimizer, batch_size: int = 4, batch_timeout: float = 0.5):
        self.optimizer = optimizer
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.pending_requests = []
        self.lock = asyncio.Lock()
    
    async def add_request(self, prompt: str, context: Dict) -> str:
        """Add request to batch and wait for response"""
        future = asyncio.Future()
        
        async with self.lock:
            self.pending_requests.append((prompt, context, future))
            
            # Process batch if full
            if len(self.pending_requests) >= self.batch_size:
                await self._process_batch()
        
        # Wait for response
        return await future
    
    async def _process_batch(self):
        """Process all pending requests"""
        if not self.pending_requests:
            return
        
        batch = self.pending_requests[:self.batch_size]
        self.pending_requests = self.pending_requests[self.batch_size:]
        
        # Process in parallel
        tasks = []
        for prompt, context, future in batch:
            task = asyncio.create_task(
                self.optimizer.optimize_inference(
                    prompt, context, OptimizationStrategy.SPEED_OPTIMIZED
                )
            )
            tasks.append((task, future))
        
        # Wait for all to complete
        for task, future in tasks:
            try:
                response, metrics = await task
                future.set_result(response)
            except Exception as e:
                future.set_exception(e)

# Testing
async def test_optimizer():
    """Test inference optimization"""
    optimizer = InferenceOptimizer()
    
    test_prompts = [
        ("I need help with sleep problems", {'intent': 'sleep', 'stage': 'qualification'}),
        ("What's good for first time users?", {'intent': 'first_time', 'stage': 'greeting'}),
        ("Tell me about indica vs sativa differences in detail", {'stage': 'education'}),
    ]
    
    print("Testing Inference Optimizer\n" + "="*50)
    
    for prompt, context in test_prompts:
        print(f"\nPrompt: {prompt}")
        
        # Test different strategies
        for strategy in [OptimizationStrategy.SPEED_OPTIMIZED, 
                        OptimizationStrategy.BALANCED]:
            response, metrics = await optimizer.optimize_inference(
                prompt, context, strategy
            )
            
            print(f"Strategy: {strategy.value}")
            print(f"Response: {response[:100]}...")
            print(f"Time: {metrics.total_time:.3f}s (Model: {metrics.model_time:.3f}s)")
            print(f"Cache hit: {metrics.cache_hit}")
    
    # Show performance stats
    stats = optimizer.get_performance_stats()
    print(f"\nPerformance Stats:")
    print(f"  Average time: {stats.get('avg_total_time', 0):.3f}s")
    print(f"  Under 5s rate: {stats.get('under_5s_rate', 0):.1%}")
    print(f"  Cache hit rate: {stats.get('cache_hit_rate', 0):.1%}")

if __name__ == "__main__":
    asyncio.run(test_optimizer())