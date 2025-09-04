"""
Model Manager - Handles loading and management of AI models
Implements strategy pattern for different model types
"""

import os
import logging
import asyncio
from typing import Dict, List, Optional, Any
from enum import Enum
from pathlib import Path
from dataclasses import dataclass

from llama_cpp import Llama
from config import settings
from services.interfaces import IModelManager, IModel

logger = logging.getLogger(__name__)

class ModelType(Enum):
    """Available model types"""
    LLAMA2_7B = "llama2-7b"
    MISTRAL_7B = "mistral-7b"
    FALLBACK = "fallback"

@dataclass
class ModelResponse:
    """Model response container"""
    text: str
    confidence: float
    tokens_used: int
    model_type: ModelType

class BaseModel(IModel):
    """Base model implementation"""
    
    def __init__(self, model_type: ModelType):
        self.model_type = model_type
        self.model = None
        self.loaded = False
    
    async def load(self) -> bool:
        """Load model (to be implemented by subclasses)"""
        raise NotImplementedError
    
    async def generate(self, prompt: str, **kwargs) -> ModelResponse:
        """Generate response (to be implemented by subclasses)"""
        raise NotImplementedError
    
    async def unload(self) -> None:
        """Unload model from memory"""
        self.model = None
        self.loaded = False

class Llama2Model(BaseModel):
    """Llama 2 7B model implementation"""
    
    def __init__(self):
        super().__init__(ModelType.LLAMA2_7B)
        self.model_path = settings.llama_model_path
    
    async def load(self) -> bool:
        """Load Llama 2 model"""
        try:
            if not self.model_path.exists():
                logger.error(f"Llama 2 model not found at {self.model_path}")
                return False
            
            logger.info(f"Loading Llama 2 model from {self.model_path}")
            
            # Load model in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            self.model = await loop.run_in_executor(
                None,
                lambda: Llama(
                    model_path=str(self.model_path),
                    n_ctx=settings.MODEL_N_CTX,
                    n_threads=settings.MODEL_N_THREADS,
                    n_gpu_layers=settings.MODEL_N_GPU_LAYERS,
                    verbose=False
                )
            )
            
            self.loaded = True
            logger.info("Llama 2 model loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load Llama 2: {str(e)}")
            return False
    
    async def generate(self, prompt: str, **kwargs) -> ModelResponse:
        """Generate response using Llama 2"""
        if not self.loaded:
            raise RuntimeError("Model not loaded")
        
        try:
            temperature = kwargs.get("temperature", settings.MODEL_TEMPERATURE)
            max_tokens = kwargs.get("max_tokens", settings.MODEL_MAX_TOKENS)
            
            # Generate in thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.model(
                    prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    stop=["Customer:", "User:", "\n\n"]
                )
            )
            
            text = result["choices"][0]["text"].strip()
            tokens = result["usage"]["total_tokens"]
            
            # Calculate confidence based on response characteristics
            confidence = self._calculate_confidence(text, tokens)
            
            return ModelResponse(
                text=text,
                confidence=confidence,
                tokens_used=tokens,
                model_type=self.model_type
            )
            
        except Exception as e:
            logger.error(f"Llama 2 generation error: {str(e)}")
            raise
    
    def _calculate_confidence(self, text: str, tokens: int) -> float:
        """Calculate confidence score for response"""
        # Simple heuristic - can be improved
        base_confidence = 0.7
        
        # Longer, more detailed responses = higher confidence
        if len(text) > 100:
            base_confidence += 0.1
        if tokens > 50:
            base_confidence += 0.1
        
        # Cap at 0.95
        return min(base_confidence, 0.95)

class MistralModel(BaseModel):
    """Mistral 7B model implementation"""
    
    def __init__(self):
        super().__init__(ModelType.MISTRAL_7B)
        self.model_path = settings.mistral_model_path
    
    async def load(self) -> bool:
        """Load Mistral model"""
        try:
            if not self.model_path.exists():
                logger.warning(f"Mistral model not found at {self.model_path}")
                return False
            
            logger.info(f"Loading Mistral model from {self.model_path}")
            
            loop = asyncio.get_event_loop()
            self.model = await loop.run_in_executor(
                None,
                lambda: Llama(
                    model_path=str(self.model_path),
                    n_ctx=settings.MODEL_N_CTX,
                    n_threads=settings.MODEL_N_THREADS,
                    n_gpu_layers=settings.MODEL_N_GPU_LAYERS,
                    verbose=False
                )
            )
            
            self.loaded = True
            logger.info("Mistral model loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load Mistral: {str(e)}")
            return False
    
    async def generate(self, prompt: str, **kwargs) -> ModelResponse:
        """Generate response using Mistral"""
        if not self.loaded:
            raise RuntimeError("Model not loaded")
        
        try:
            # Mistral prefers lower temperature for medical/technical
            temperature = kwargs.get("temperature", 0.5)
            max_tokens = kwargs.get("max_tokens", settings.MODEL_MAX_TOKENS)
            
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.model(
                    prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    stop=["Customer:", "User:", "\n\n"]
                )
            )
            
            text = result["choices"][0]["text"].strip()
            tokens = result["usage"]["total_tokens"]
            
            # Mistral typically has higher confidence for technical content
            confidence = self._calculate_confidence(text, tokens) + 0.05
            
            return ModelResponse(
                text=text,
                confidence=min(confidence, 0.98),
                tokens_used=tokens,
                model_type=self.model_type
            )
            
        except Exception as e:
            logger.error(f"Mistral generation error: {str(e)}")
            raise
    
    def _calculate_confidence(self, text: str, tokens: int) -> float:
        """Calculate confidence score for Mistral response"""
        base_confidence = 0.75  # Higher base for Mistral
        
        if len(text) > 100:
            base_confidence += 0.1
        if tokens > 50:
            base_confidence += 0.05
        
        return base_confidence

class FallbackModel(BaseModel):
    """Fallback model for when LLMs are unavailable"""
    
    def __init__(self):
        super().__init__(ModelType.FALLBACK)
        self.loaded = True  # Always "loaded"
    
    async def load(self) -> bool:
        """Fallback is always ready"""
        return True
    
    async def generate(self, prompt: str, **kwargs) -> ModelResponse:
        """Generate basic fallback response"""
        # Extract language from prompt if possible
        language = "en"
        if "français" in prompt.lower() or "french" in prompt.lower():
            language = "fr"
        elif "español" in prompt.lower() or "spanish" in prompt.lower():
            language = "es"
        
        responses = {
            "en": "I'm here to help you find the right cannabis products. Could you tell me more about what you're looking for?",
            "fr": "Je suis là pour vous aider à trouver les bons produits de cannabis. Pouvez-vous m'en dire plus sur ce que vous recherchez?",
            "es": "Estoy aquí para ayudarte a encontrar los productos de cannabis adecuados. ¿Podrías decirme más sobre lo que buscas?"
        }
        
        return ModelResponse(
            text=responses.get(language, responses["en"]),
            confidence=0.3,
            tokens_used=0,
            model_type=self.model_type
        )

class ModelManager(IModelManager):
    """
    Manages multiple AI models with lazy loading and failover
    Open/Closed Principle: Easy to add new models without modifying existing code
    """
    
    def __init__(self):
        self.models: Dict[ModelType, IModel] = {}
        self.loaded_models: List[ModelType] = []
        self.primary_model: Optional[ModelType] = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize and load models"""
        if self._initialized:
            return
        
        logger.info("Initializing Model Manager...")
        
        # Create model instances
        self.models[ModelType.LLAMA2_7B] = Llama2Model()
        self.models[ModelType.MISTRAL_7B] = MistralModel()
        self.models[ModelType.FALLBACK] = FallbackModel()
        
        # Load models based on configuration
        load_tasks = []
        
        if settings.llama_model_path.exists():
            load_tasks.append(self._load_model(ModelType.LLAMA2_7B))
        
        # Skip Mistral for now - it's loading too slowly
        # if settings.mistral_model_path.exists():
        #     load_tasks.append(self._load_model(ModelType.MISTRAL_7B))
        
        # Always load fallback
        load_tasks.append(self._load_model(ModelType.FALLBACK))
        
        # Load models concurrently
        results = await asyncio.gather(*load_tasks, return_exceptions=True)
        
        # Check results
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Model load error: {result}")
        
        # Set primary model
        if ModelType.MISTRAL_7B in self.loaded_models:
            self.primary_model = ModelType.MISTRAL_7B
        elif ModelType.LLAMA2_7B in self.loaded_models:
            self.primary_model = ModelType.LLAMA2_7B
        else:
            self.primary_model = ModelType.FALLBACK
        
        self._initialized = True
        logger.info(
            f"Model Manager initialized. "
            f"Loaded models: {[m.value for m in self.loaded_models]}"
        )
    
    async def _load_model(self, model_type: ModelType) -> bool:
        """Load a specific model"""
        try:
            model = self.models[model_type]
            success = await model.load()
            
            if success:
                self.loaded_models.append(model_type)
                logger.info(f"Loaded {model_type.value}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to load {model_type.value}: {str(e)}")
            return False
    
    async def generate(
        self,
        model: ModelType,
        prompt: str,
        **kwargs
    ) -> ModelResponse:
        """Generate response using specified model with fallback"""
        
        # Try requested model first
        if model in self.loaded_models:
            try:
                return await self.models[model].generate(prompt, **kwargs)
            except Exception as e:
                logger.error(f"Generation failed for {model.value}: {str(e)}")
        
        # Fallback to primary model
        if self.primary_model and self.primary_model != model:
            try:
                logger.info(f"Falling back to {self.primary_model.value}")
                return await self.models[self.primary_model].generate(prompt, **kwargs)
            except Exception as e:
                logger.error(f"Primary model failed: {str(e)}")
        
        # Last resort: fallback model
        logger.warning("Using fallback model")
        return await self.models[ModelType.FALLBACK].generate(prompt, **kwargs)
    
    def get_available_models(self) -> List[ModelType]:
        """Get list of available models"""
        return self.loaded_models
    
    def get_status(self) -> Dict[str, bool]:
        """Get status of all models"""
        return {
            model_type.value: model_type in self.loaded_models
            for model_type in ModelType
        }
    
    def get_detailed_status(self) -> Dict[str, Any]:
        """Get detailed status including metrics"""
        status = {
            "models": {},
            "primary_model": self.primary_model.value if self.primary_model else None,
            "total_loaded": len(self.loaded_models)
        }
        
        for model_type, model in self.models.items():
            status["models"][model_type.value] = {
                "loaded": model_type in self.loaded_models,
                "type": model_type.value,
                "path": str(getattr(model, "model_path", "N/A"))
            }
        
        return status
    
    async def reload(self) -> None:
        """Reload all models"""
        logger.info("Reloading models...")
        
        # Unload existing models
        await self.cleanup()
        
        # Reset state
        self.loaded_models = []
        self.primary_model = None
        self._initialized = False
        
        # Reinitialize
        await self.initialize()
    
    async def cleanup(self) -> None:
        """Clean up and unload models"""
        logger.info("Cleaning up models...")
        
        for model_type, model in self.models.items():
            if model_type in self.loaded_models:
                await model.unload()
        
        self.loaded_models = []
        self.primary_model = None