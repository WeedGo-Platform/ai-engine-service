"""
Core LLM Service with Advanced Model Management
Production-ready implementation with streaming, fallback, and multi-model support
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional, AsyncGenerator, Union
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import json

from llama_cpp import Llama
from langchain.llms import LlamaCpp
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.schema import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langchain.memory import ConversationBufferMemory, ConversationSummaryMemory
from langchain.chains import ConversationChain
from langchain.prompts import PromptTemplate

from services.interfaces import IModel, IModelManager
from config import settings
from utils.monitoring import MetricsCollector

logger = logging.getLogger(__name__)

class ModelType(Enum):
    """Supported model types"""
    LLAMA2_7B = "llama2-7b"
    MISTRAL_7B = "mistral-7b"
    LLAMA2_13B = "llama2-13b"
    MIXTRAL_8X7B = "mixtral-8x7b"
    CUSTOM = "custom"

@dataclass
class ModelConfig:
    """Model configuration"""
    name: str
    path: Path
    model_type: ModelType
    context_length: int = 4096
    n_threads: int = 8
    n_gpu_layers: int = 0
    temperature: float = 0.7
    top_p: float = 0.95
    top_k: int = 40
    max_tokens: int = 512
    repeat_penalty: float = 1.1
    seed: int = -1
    use_mmap: bool = True
    use_mlock: bool = False
    streaming: bool = True
    verbose: bool = False
    
    # Model-specific parameters
    rope_freq_base: float = 10000.0
    rope_freq_scale: float = 1.0
    
    # Performance settings
    n_batch: int = 512
    last_n_tokens_size: int = 64
    
    # Custom metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class GenerationResult:
    """Result from model generation"""
    text: str
    model: str
    tokens_generated: int
    generation_time: float
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    streaming: bool = False

class LLMModel(IModel):
    """Wrapper for individual LLM model"""
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self.model: Optional[Llama] = None
        self.langchain_llm: Optional[LlamaCpp] = None
        self.is_loaded = False
        self.metrics = MetricsCollector()
        
    async def load(self) -> bool:
        """Load model into memory"""
        try:
            start_time = time.time()
            logger.info(f"Loading model: {self.config.name}")
            
            # Check if model file exists
            if not self.config.path.exists():
                logger.error(f"Model file not found: {self.config.path}")
                return False
            
            # Initialize callback manager for streaming
            callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])
            
            # Load with LlamaCpp
            self.model = Llama(
                model_path=str(self.config.path),
                n_ctx=self.config.context_length,
                n_threads=self.config.n_threads,
                n_gpu_layers=self.config.n_gpu_layers,
                seed=self.config.seed,
                use_mmap=self.config.use_mmap,
                use_mlock=self.config.use_mlock,
                verbose=self.config.verbose,
                n_batch=self.config.n_batch,
                last_n_tokens_size=self.config.last_n_tokens_size,
                rope_freq_base=self.config.rope_freq_base,
                rope_freq_scale=self.config.rope_freq_scale
            )
            
            # Create LangChain wrapper
            self.langchain_llm = LlamaCpp(
                model_path=str(self.config.path),
                n_ctx=self.config.context_length,
                n_threads=self.config.n_threads,
                n_gpu_layers=self.config.n_gpu_layers,
                temperature=self.config.temperature,
                top_p=self.config.top_p,
                top_k=self.config.top_k,
                max_tokens=self.config.max_tokens,
                repeat_penalty=self.config.repeat_penalty,
                streaming=self.config.streaming,
                callback_manager=callback_manager if self.config.streaming else None,
                verbose=self.config.verbose
            )
            
            self.is_loaded = True
            load_time = time.time() - start_time
            
            logger.info(f"Model {self.config.name} loaded successfully in {load_time:.2f}s")
            self.metrics.record_model_load(self.config.name, load_time)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to load model {self.config.name}: {str(e)}", exc_info=True)
            self.is_loaded = False
            return False
    
    async def generate(
        self,
        prompt: str,
        stream: bool = False,
        **kwargs
    ) -> Union[GenerationResult, AsyncGenerator[str, None]]:
        """Generate response from prompt"""
        
        if not self.is_loaded:
            raise RuntimeError(f"Model {self.config.name} is not loaded")
        
        start_time = time.time()
        
        # Override config with kwargs
        temperature = kwargs.get('temperature', self.config.temperature)
        max_tokens = kwargs.get('max_tokens', self.config.max_tokens)
        top_p = kwargs.get('top_p', self.config.top_p)
        top_k = kwargs.get('top_k', self.config.top_k)
        repeat_penalty = kwargs.get('repeat_penalty', self.config.repeat_penalty)
        
        try:
            if stream:
                return self._stream_generation(
                    prompt, temperature, max_tokens, top_p, top_k, repeat_penalty
                )
            else:
                # Non-streaming generation
                response = self.model(
                    prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    top_k=top_k,
                    repeat_penalty=repeat_penalty,
                    echo=False
                )
                
                text = response['choices'][0]['text']
                tokens = response['usage']['completion_tokens']
                generation_time = time.time() - start_time
                
                # Calculate confidence based on generation metrics
                confidence = self._calculate_confidence(response)
                
                result = GenerationResult(
                    text=text,
                    model=self.config.name,
                    tokens_generated=tokens,
                    generation_time=generation_time,
                    confidence=confidence,
                    metadata={
                        'temperature': temperature,
                        'max_tokens': max_tokens,
                        'model_type': self.config.model_type.value
                    }
                )
                
                self.metrics.record_generation(
                    self.config.name,
                    tokens,
                    generation_time
                )
                
                return result
                
        except Exception as e:
            logger.error(f"Generation error with {self.config.name}: {str(e)}", exc_info=True)
            raise
    
    async def _stream_generation(
        self,
        prompt: str,
        temperature: float,
        max_tokens: int,
        top_p: float,
        top_k: int,
        repeat_penalty: float
    ) -> AsyncGenerator[str, None]:
        """Stream generation token by token"""
        
        try:
            stream = self.model(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                repeat_penalty=repeat_penalty,
                stream=True,
                echo=False
            )
            
            for output in stream:
                if output and 'choices' in output:
                    token = output['choices'][0].get('text', '')
                    if token:
                        yield token
                        
        except Exception as e:
            logger.error(f"Streaming error with {self.config.name}: {str(e)}")
            yield f"[Error: {str(e)}]"
    
    def _calculate_confidence(self, response: Dict) -> float:
        """Calculate confidence score from model response"""
        # Simple confidence calculation based on perplexity and generation metrics
        # This can be enhanced with more sophisticated metrics
        try:
            if 'choices' in response and response['choices']:
                # Base confidence on finish reason and token count
                finish_reason = response['choices'][0].get('finish_reason', 'length')
                tokens = response['usage']['completion_tokens']
                
                if finish_reason == 'stop':
                    base_confidence = 0.9
                else:
                    base_confidence = 0.7
                
                # Adjust based on token count (very short or very long responses may be less confident)
                if tokens < 10:
                    confidence = base_confidence * 0.8
                elif tokens > 400:
                    confidence = base_confidence * 0.9
                else:
                    confidence = base_confidence
                
                return min(max(confidence, 0.0), 1.0)
        except:
            return 0.5
    
    async def unload(self) -> None:
        """Unload model from memory"""
        try:
            if self.model:
                del self.model
                self.model = None
            if self.langchain_llm:
                del self.langchain_llm
                self.langchain_llm = None
            
            self.is_loaded = False
            logger.info(f"Model {self.config.name} unloaded")
            
        except Exception as e:
            logger.error(f"Error unloading model {self.config.name}: {str(e)}")

class LLMService(IModelManager):
    """
    Advanced LLM Service with multi-model management
    Handles model loading, routing, and generation with fallback support
    """
    
    def __init__(self):
        self.models: Dict[str, LLMModel] = {}
        self.model_configs: Dict[str, ModelConfig] = {}
        self.primary_model: Optional[str] = None
        self.fallback_model: Optional[str] = None
        self.metrics = MetricsCollector()
        self._initialized = False
        
    async def initialize(self) -> None:
        """Initialize LLM service with configured models"""
        
        logger.info("Initializing LLM Service")
        
        # Load model configurations
        self._load_model_configs()
        
        # Load primary models
        await self._load_primary_models()
        
        self._initialized = True
        logger.info("LLM Service initialized successfully")
    
    def _load_model_configs(self):
        """Load model configurations from settings"""
        
        # Llama 2 7B configuration
        if settings.llama_model_path.exists():
            self.model_configs['llama2-7b'] = ModelConfig(
                name='llama2-7b',
                path=settings.llama_model_path,
                model_type=ModelType.LLAMA2_7B,
                context_length=settings.MODEL_N_CTX,
                n_threads=settings.MODEL_N_THREADS,
                n_gpu_layers=settings.MODEL_N_GPU_LAYERS,
                temperature=settings.MODEL_TEMPERATURE,
                max_tokens=settings.MODEL_MAX_TOKENS,
                metadata={'specialty': 'general', 'languages': ['en', 'es', 'fr']}
            )
        
        # Mistral 7B configuration
        if settings.mistral_model_path.exists():
            self.model_configs['mistral-7b'] = ModelConfig(
                name='mistral-7b',
                path=settings.mistral_model_path,
                model_type=ModelType.MISTRAL_7B,
                context_length=8192,  # Mistral supports longer context
                n_threads=settings.MODEL_N_THREADS,
                n_gpu_layers=settings.MODEL_N_GPU_LAYERS,
                temperature=settings.MODEL_TEMPERATURE,
                max_tokens=settings.MODEL_MAX_TOKENS,
                metadata={'specialty': 'instruction', 'languages': ['en', 'fr', 'de', 'es', 'it']}
            )
    
    async def _load_primary_models(self):
        """Load primary and fallback models"""
        
        # Try to load Mistral as primary (better for instructions)
        if 'mistral-7b' in self.model_configs:
            model = LLMModel(self.model_configs['mistral-7b'])
            if await model.load():
                self.models['mistral-7b'] = model
                self.primary_model = 'mistral-7b'
                logger.info("Mistral-7B set as primary model")
        
        # Load Llama 2 as fallback or primary if Mistral failed
        if 'llama2-7b' in self.model_configs:
            model = LLMModel(self.model_configs['llama2-7b'])
            if await model.load():
                self.models['llama2-7b'] = model
                if not self.primary_model:
                    self.primary_model = 'llama2-7b'
                    logger.info("Llama2-7B set as primary model")
                else:
                    self.fallback_model = 'llama2-7b'
                    logger.info("Llama2-7B set as fallback model")
        
        if not self.primary_model:
            raise RuntimeError("No models could be loaded. Check model files.")
    
    async def generate(
        self,
        model: Optional[str] = None,
        prompt: str = "",
        stream: bool = False,
        **kwargs
    ) -> Union[GenerationResult, AsyncGenerator[str, None]]:
        """
        Generate response using specified or best available model
        
        Args:
            model: Model name to use (optional, will auto-select if not specified)
            prompt: Input prompt
            stream: Whether to stream the response
            **kwargs: Additional generation parameters
        
        Returns:
            GenerationResult or async generator for streaming
        """
        
        if not self._initialized:
            await self.initialize()
        
        # Select model
        model_name = model or self.primary_model
        if model_name not in self.models:
            logger.warning(f"Requested model {model_name} not available, using primary")
            model_name = self.primary_model
        
        selected_model = self.models[model_name]
        
        try:
            # Try primary model
            result = await selected_model.generate(prompt, stream, **kwargs)
            return result
            
        except Exception as e:
            logger.error(f"Primary model {model_name} failed: {str(e)}")
            
            # Try fallback model if available
            if self.fallback_model and self.fallback_model != model_name:
                logger.info(f"Attempting fallback to {self.fallback_model}")
                fallback = self.models[self.fallback_model]
                
                try:
                    result = await fallback.generate(prompt, stream, **kwargs)
                    return result
                except Exception as fallback_error:
                    logger.error(f"Fallback model also failed: {str(fallback_error)}")
                    raise
            else:
                raise
    
    def get_available_models(self) -> List[str]:
        """Get list of available loaded models"""
        return list(self.models.keys())
    
    def get_status(self) -> Dict[str, Any]:
        """Get detailed status of all models"""
        status = {
            'initialized': self._initialized,
            'primary_model': self.primary_model,
            'fallback_model': self.fallback_model,
            'models': {}
        }
        
        for name, model in self.models.items():
            status['models'][name] = {
                'loaded': model.is_loaded,
                'type': model.config.model_type.value,
                'context_length': model.config.context_length,
                'gpu_layers': model.config.n_gpu_layers,
                'metadata': model.config.metadata
            }
        
        return status
    
    async def load_model(self, model_name: str, config: Optional[ModelConfig] = None) -> bool:
        """
        Dynamically load a new model
        
        Args:
            model_name: Name for the model
            config: Model configuration (uses existing if not provided)
        
        Returns:
            Success status
        """
        
        if config:
            self.model_configs[model_name] = config
        elif model_name not in self.model_configs:
            logger.error(f"No configuration found for model {model_name}")
            return False
        
        model = LLMModel(self.model_configs[model_name])
        if await model.load():
            self.models[model_name] = model
            logger.info(f"Dynamically loaded model {model_name}")
            return True
        
        return False
    
    async def unload_model(self, model_name: str) -> bool:
        """
        Unload a model from memory
        
        Args:
            model_name: Name of model to unload
        
        Returns:
            Success status
        """
        
        if model_name not in self.models:
            logger.warning(f"Model {model_name} not loaded")
            return False
        
        # Don't unload primary or fallback without replacement
        if model_name == self.primary_model and len(self.models) > 1:
            # Find replacement primary
            for name in self.models:
                if name != model_name:
                    self.primary_model = name
                    logger.info(f"Primary model switched to {name}")
                    break
        
        await self.models[model_name].unload()
        del self.models[model_name]
        
        logger.info(f"Unloaded model {model_name}")
        return True
    
    async def cleanup(self) -> None:
        """Cleanup all resources"""
        
        logger.info("Cleaning up LLM Service")
        
        for model_name in list(self.models.keys()):
            await self.unload_model(model_name)
        
        self.models.clear()
        self.model_configs.clear()
        self.primary_model = None
        self.fallback_model = None
        self._initialized = False
        
        logger.info("LLM Service cleanup complete")

# Singleton instance
_llm_service: Optional[LLMService] = None

def get_llm_service() -> LLMService:
    """Get singleton LLM service instance"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service