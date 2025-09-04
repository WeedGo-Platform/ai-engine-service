"""
Offline Multilingual Inference Engine using llama.cpp
Supports Qwen models with GGUF quantization
"""

import os
import json
import logging
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import asyncio
from concurrent.futures import ThreadPoolExecutor

try:
    from llama_cpp import Llama
except ImportError:
    print("Please install llama-cpp-python: pip install llama-cpp-python")
    Llama = None

logger = logging.getLogger(__name__)

class ModelSize(Enum):
    """Available model sizes"""
    TINY = "1.8B"     # Testing
    SMALL = "7B"      # Minimum production
    MEDIUM = "14B"    # Recommended
    LARGE = "72B"     # High-end

class QuantizationType(Enum):
    """Quantization types for GGUF models"""
    Q2_K = "q2_k"      # 2-bit, lowest quality
    Q3_K_M = "q3_k_m"  # 3-bit, low quality
    Q4_K_M = "q4_k_m"  # 4-bit, balanced (recommended)
    Q5_K_M = "q5_k_m"  # 5-bit, good quality
    Q6_K = "q6_k"      # 6-bit, high quality
    Q8_0 = "q8_0"      # 8-bit, near lossless

@dataclass
class InferenceConfig:
    """Configuration for inference engine"""
    model_path: str
    model_size: ModelSize = ModelSize.MEDIUM
    quantization: QuantizationType = QuantizationType.Q4_K_M
    
    # GPU settings
    n_gpu_layers: int = -1  # -1 for all layers on GPU
    use_mlock: bool = True  # Lock model in RAM
    use_mmap: bool = True   # Memory-mapped files
    
    # Context settings
    n_ctx: int = 8192       # Context window
    n_batch: int = 512      # Batch size
    
    # Generation settings
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    repeat_penalty: float = 1.1
    max_tokens: int = 512
    
    # Performance settings
    n_threads: int = 8      # CPU threads
    seed: int = -1          # Random seed (-1 for random)
    
    # Language-specific settings
    language_configs: Dict = field(default_factory=dict)

@dataclass
class GenerationResult:
    """Result from text generation"""
    text: str
    language: str
    tokens_generated: int
    time_taken: float
    tokens_per_second: float
    cache_hit: bool = False
    adapter_used: Optional[str] = None

class OfflineInferenceEngine:
    """
    Main inference engine for offline multilingual support
    Uses llama.cpp for efficient GGUF model inference
    """
    
    def __init__(self, config: InferenceConfig):
        """Initialize the inference engine"""
        
        self.config = config
        self.model = None
        self.executor = ThreadPoolExecutor(max_workers=2)
        
        # Language-specific configurations
        self.language_configs = self._initialize_language_configs()
        
        # Performance metrics
        self.metrics = {
            'total_requests': 0,
            'total_tokens': 0,
            'avg_tokens_per_second': 0,
            'cache_hits': 0
        }
        
        # Initialize model
        self._load_model()
    
    def _initialize_language_configs(self) -> Dict:
        """Initialize language-specific configurations"""
        
        return {
            'en': {
                'system_prompt': "You are a helpful cannabis dispensary assistant.",
                'temperature': 0.7,
                'max_tokens': 512
            },
            'es': {
                'system_prompt': "Eres un asistente útil de dispensario de cannabis.",
                'temperature': 0.75,
                'max_tokens': 550  # Spanish often needs more tokens
            },
            'fr': {
                'system_prompt': "Vous êtes un assistant utile de dispensaire de cannabis.",
                'temperature': 0.75,
                'max_tokens': 550
            },
            'pt': {
                'system_prompt': "Você é um assistente útil de dispensário de cannabis.",
                'temperature': 0.75,
                'max_tokens': 550
            },
            'zh': {
                'system_prompt': "你是一个有用的大麻药房助手。",
                'temperature': 0.65,  # Lower temperature for Chinese
                'max_tokens': 800     # Chinese needs more tokens
            },
            'ar': {
                'system_prompt': "أنت مساعد مفيد لمستوصف القنب.",
                'temperature': 0.65,
                'max_tokens': 700,    # Arabic needs more tokens
                'is_rtl': True
            }
        }
    
    def _load_model(self):
        """Load the GGUF model using llama.cpp"""
        
        if not os.path.exists(self.config.model_path):
            logger.error(f"Model not found at {self.config.model_path}")
            raise FileNotFoundError(f"Model not found: {self.config.model_path}")
        
        if Llama is None:
            raise ImportError("llama-cpp-python not installed")
        
        try:
            logger.info(f"Loading model from {self.config.model_path}")
            
            # Initialize Llama model
            self.model = Llama(
                model_path=self.config.model_path,
                n_ctx=self.config.n_ctx,
                n_batch=self.config.n_batch,
                n_gpu_layers=self.config.n_gpu_layers,
                n_threads=self.config.n_threads,
                use_mlock=self.config.use_mlock,
                use_mmap=self.config.use_mmap,
                seed=self.config.seed,
                verbose=False
            )
            
            logger.info(f"Model loaded successfully")
            
            # Warm up the model
            self._warmup()
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    def _warmup(self):
        """Warm up the model with a simple generation"""
        
        try:
            logger.info("Warming up model...")
            self.model("Hello", max_tokens=1, echo=False)
            logger.info("Model warmup complete")
        except Exception as e:
            logger.warning(f"Warmup failed: {e}")
    
    def generate(
        self,
        prompt: str,
        language: str = 'en',
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        system_prompt: Optional[str] = None,
        adapter_name: Optional[str] = None
    ) -> GenerationResult:
        """
        Generate text in specified language
        
        Args:
            prompt: Input prompt
            language: Target language code
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            system_prompt: System prompt override
            adapter_name: LoRA adapter to use
            
        Returns:
            GenerationResult with generated text
        """
        
        start_time = time.time()
        
        # Get language-specific config
        lang_config = self.language_configs.get(language, self.language_configs['en'])
        
        # Override with provided values
        if max_tokens is None:
            max_tokens = lang_config.get('max_tokens', self.config.max_tokens)
        if temperature is None:
            temperature = lang_config.get('temperature', self.config.temperature)
        if system_prompt is None:
            system_prompt = lang_config.get('system_prompt', '')
        
        # Build full prompt with system message
        full_prompt = self._build_prompt(prompt, language, system_prompt)
        
        # Adjust token count for non-Latin languages
        if language in ['zh', 'ar']:
            max_tokens = int(max_tokens * 1.5)  # Need more tokens
        
        try:
            # Generate response
            response = self.model(
                full_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=self.config.top_p,
                top_k=self.config.top_k,
                repeat_penalty=self.config.repeat_penalty,
                echo=False,
                stop=["User:", "用户:", "Usuario:", "Utilisateur:", "المستخدم:"]
            )
            
            # Extract generated text
            generated_text = response['choices'][0]['text'].strip()
            
            # Post-process for RTL languages
            if lang_config.get('is_rtl', False):
                generated_text = self._process_rtl_text(generated_text)
            
            # Calculate metrics
            time_taken = time.time() - start_time
            tokens_generated = response['usage']['completion_tokens']
            tokens_per_second = tokens_generated / time_taken if time_taken > 0 else 0
            
            # Update global metrics
            self.metrics['total_requests'] += 1
            self.metrics['total_tokens'] += tokens_generated
            self.metrics['avg_tokens_per_second'] = (
                (self.metrics['avg_tokens_per_second'] * (self.metrics['total_requests'] - 1) + tokens_per_second) 
                / self.metrics['total_requests']
            )
            
            return GenerationResult(
                text=generated_text,
                language=language,
                tokens_generated=tokens_generated,
                time_taken=time_taken,
                tokens_per_second=tokens_per_second,
                adapter_used=adapter_name
            )
            
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise
    
    def _build_prompt(self, user_input: str, language: str, system_prompt: str) -> str:
        """Build the full prompt with proper formatting"""
        
        # Qwen chat format
        if language == 'zh':
            return f"""<|im_start|>system
{system_prompt}<|im_end|>
<|im_start|>user
{user_input}<|im_end|>
<|im_start|>assistant
"""
        elif language == 'ar':
            return f"""<|im_start|>system
{system_prompt}<|im_end|>
<|im_start|>المستخدم
{user_input}<|im_end|>
<|im_start|>المساعد
"""
        else:
            # Default format for Latin languages
            return f"""<|im_start|>system
{system_prompt}<|im_end|>
<|im_start|>user
{user_input}<|im_end|>
<|im_start|>assistant
"""
    
    def _process_rtl_text(self, text: str) -> str:
        """Process right-to-left text (Arabic)"""
        # Add RTL markers if needed
        # This is simplified - proper RTL handling requires frontend support
        return text
    
    async def generate_async(
        self,
        prompt: str,
        language: str = 'en',
        **kwargs
    ) -> GenerationResult:
        """Async wrapper for generation"""
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self.generate,
            prompt,
            language,
            kwargs.get('max_tokens'),
            kwargs.get('temperature'),
            kwargs.get('system_prompt'),
            kwargs.get('adapter_name')
        )
    
    def batch_generate(
        self,
        prompts: List[Tuple[str, str]],  # List of (prompt, language) tuples
        **kwargs
    ) -> List[GenerationResult]:
        """Generate responses for multiple prompts"""
        
        results = []
        for prompt, language in prompts:
            try:
                result = self.generate(prompt, language, **kwargs)
                results.append(result)
            except Exception as e:
                logger.error(f"Batch generation failed for prompt: {e}")
                results.append(GenerationResult(
                    text=f"Error: {str(e)}",
                    language=language,
                    tokens_generated=0,
                    time_taken=0,
                    tokens_per_second=0
                ))
        
        return results
    
    def get_metrics(self) -> Dict:
        """Get performance metrics"""
        
        return {
            **self.metrics,
            'model_size': self.config.model_size.value,
            'quantization': self.config.quantization.value,
            'context_size': self.config.n_ctx,
            'gpu_layers': self.config.n_gpu_layers
        }
    
    def adjust_for_language(self, language: str) -> Dict:
        """Get adjusted parameters for specific language"""
        
        adjustments = {
            'en': {'token_multiplier': 1.0, 'temperature_offset': 0},
            'es': {'token_multiplier': 1.1, 'temperature_offset': 0.05},
            'fr': {'token_multiplier': 1.1, 'temperature_offset': 0.05},
            'pt': {'token_multiplier': 1.15, 'temperature_offset': 0.05},
            'zh': {'token_multiplier': 2.5, 'temperature_offset': -0.1},
            'ar': {'token_multiplier': 2.0, 'temperature_offset': -0.1}
        }
        
        return adjustments.get(language, adjustments['en'])
    
    def unload_model(self):
        """Unload model from memory"""
        
        if self.model:
            del self.model
            self.model = None
            logger.info("Model unloaded from memory")
    
    def __del__(self):
        """Cleanup on deletion"""
        self.unload_model()
        self.executor.shutdown(wait=False)