"""
Model Management Service
Implements IModelManager interface following SOLID principles
Handles model lifecycle management separately from the main engine
"""

import os
import time
import gc
import psutil
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from llama_cpp import Llama

# Import interface
import sys
sys.path.append(str(Path(__file__).parent.parent))
from core.interfaces import IModelManager

logger = logging.getLogger(__name__)


class ModelManager(IModelManager):
    """
    Model Manager implementation that handles model lifecycle
    Single Responsibility: Model loading, unloading, and management
    """
    
    def __init__(self, model_paths: Optional[List[str]] = None):
        """
        Initialize the Model Manager
        
        Args:
            model_paths: Optional list of paths to search for models
        """
        self.current_model = None
        self.current_model_name = None
        self.model_paths = model_paths or self._get_default_model_paths()
        self.available_models = self._scan_models()
        self.model_config = {}
        
        logger.info(f"ModelManager initialized with {len(self.available_models)} models")
        self._log_system_resources()
    
    def _get_default_model_paths(self) -> List[Path]:
        """Get default model search paths"""
        return [
            Path("models"),
            Path("../models"),
            Path("/Users/charrcy/projects/WeedGo/microservices/ai-engine-service/models")
        ]
    
    def _log_system_resources(self):
        """Log current system resource availability"""
        try:
            import multiprocessing
            cpu_count = multiprocessing.cpu_count()
            memory = psutil.virtual_memory()
            logger.info(f"System Resources:")
            logger.info(f"  - CPUs: {cpu_count}")
            logger.info(f"  - Memory: {memory.total / (1024**3):.1f} GB total, {memory.available / (1024**3):.1f} GB available")
            logger.info(f"  - Memory used: {memory.percent}%")
        except Exception as e:
            logger.warning(f"Could not get system resources: {e}")
    
    def _scan_models(self) -> Dict[str, str]:
        """Scan all available model files"""
        models = {}
        
        for base_path in self.model_paths:
            if not isinstance(base_path, Path):
                base_path = Path(base_path)
            
            if not base_path.exists():
                continue
                
            # Scan all subdirectories for .gguf files
            for model_file in base_path.rglob("*.gguf"):
                # Skip empty files (0 bytes = not downloaded)
                if model_file.stat().st_size == 0:
                    logger.info(f"Skipping empty model file: {model_file}")
                    continue
                
                # Get relative path from models directory
                rel_path = model_file.relative_to(base_path)
                # Create a simple name from the filename
                model_name = model_file.stem.replace('.Q4_K_M', '').replace('-', '_').lower()
                # Store full path
                models[model_name] = str(model_file)
        
        logger.info(f"Found {len(models)} downloaded models: {list(models.keys())}")
        return models
    
    def load_model(self, model_name: str, base_folder: Optional[str] = None) -> bool:
        """
        Load a specific model
        
        Args:
            model_name: Name of the model to load
            base_folder: Optional base folder for model search
            
        Returns:
            True if successful, False otherwise
        """
        # Add base folder to search paths if provided
        if base_folder:
            base_path = Path(base_folder)
            if base_path not in self.model_paths:
                self.model_paths.insert(0, base_path)
                # Rescan models with new path
                self.available_models = self._scan_models()
        
        if model_name not in self.available_models:
            logger.error(f"Model {model_name} not found in available models")
            return False
        
        # Check if already loaded
        if self.current_model_name == model_name:
            logger.info(f"Model {model_name} already loaded")
            return True
        
        try:
            # Unload current model first
            self.unload_model()
            
            model_path = self.available_models[model_name]
            logger.info(f"Loading model from {model_path}")
            
            # Memory monitoring
            memory_before = psutil.virtual_memory()
            logger.info(f"Memory before loading: {memory_before.available / (1024**3):.1f} GB available")
            
            # Determine optimal parameters based on model and system
            n_ctx = self._get_optimal_context_size(model_name)
            n_threads = self._get_optimal_thread_count()
            n_gpu_layers = self._get_gpu_layers(model_name)
            
            # Load the model with optimized parameters
            self.current_model = Llama(
                model_path=model_path,
                n_ctx=n_ctx,
                n_threads=n_threads,
                n_gpu_layers=n_gpu_layers,
                verbose=False,
                seed=-1,
                use_mmap=True,
                use_mlock=False
            )
            
            self.current_model_name = model_name
            
            # Store model configuration
            self.model_config = {
                'name': model_name,
                'path': model_path,
                'n_ctx': n_ctx,
                'n_threads': n_threads,
                'n_gpu_layers': n_gpu_layers
            }
            
            # Memory monitoring after load
            memory_after = psutil.virtual_memory()
            memory_used = (memory_before.available - memory_after.available) / (1024**3)
            logger.info(f"Model loaded successfully. Memory used: {memory_used:.1f} GB")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
            self.current_model = None
            self.current_model_name = None
            return False
    
    def unload_model(self) -> None:
        """Unload the current model and free resources"""
        if self.current_model:
            logger.info(f"Unloading model: {self.current_model_name}")
            
            try:
                # Try to explicitly free the model's memory if available
                if hasattr(self.current_model, '__del__'):
                    self.current_model.__del__()
            except:
                pass
            
            del self.current_model
            self.current_model = None
            self.current_model_name = None
            self.model_config = {}
            
            # Aggressive garbage collection
            gc.collect(2)  # Full collection
            gc.collect(1)
            gc.collect(0)
            
            # Give OS time to reclaim memory
            time.sleep(0.5)
            
            logger.info("Model unloaded and memory freed")
    
    def list_models(self) -> List[Dict[str, Any]]:
        """
        List available models with their information
        
        Returns:
            List of model information dictionaries
        """
        models = []
        for name, path in self.available_models.items():
            try:
                file_path = Path(path)
                size_gb = file_path.stat().st_size / (1024**3)
                
                models.append({
                    'name': name,
                    'path': path,
                    'size_gb': round(size_gb, 2),
                    'loaded': name == self.current_model_name
                })
            except Exception as e:
                logger.warning(f"Could not get info for model {name}: {e}")
                
        return sorted(models, key=lambda x: x['name'])
    
    def get_current_model(self) -> Optional[Any]:
        """
        Get the currently loaded model instance
        
        Returns:
            Current model instance or None
        """
        return self.current_model
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model
        
        Returns:
            Dictionary with model information
        """
        if not self.current_model:
            return {
                'loaded': False,
                'name': None,
                'config': {}
            }
        
        info = {
            'loaded': True,
            'name': self.current_model_name,
            'config': self.model_config.copy()
        }
        
        # Add runtime information
        try:
            memory = psutil.virtual_memory()
            process = psutil.Process()
            
            info['runtime'] = {
                'memory_used_mb': process.memory_info().rss / (1024**2),
                'system_memory_percent': memory.percent,
                'system_memory_available_gb': memory.available / (1024**3)
            }
        except:
            pass
        
        return info
    
    def _get_optimal_context_size(self, model_name: str) -> int:
        """
        Determine optimal context size based on model and available memory
        
        Args:
            model_name: Name of the model
            
        Returns:
            Optimal context size
        """
        memory = psutil.virtual_memory()
        available_gb = memory.available / (1024**3)
        
        # Base context sizes for different memory availability
        if available_gb > 16:
            base_ctx = 4096
        elif available_gb > 8:
            base_ctx = 2048
        else:
            base_ctx = 1024
        
        # Adjust for specific models
        if 'mistral' in model_name.lower() or 'llama' in model_name.lower():
            # These models can handle larger contexts efficiently
            return min(base_ctx * 2, 8192)
        elif 'tiny' in model_name.lower() or 'small' in model_name.lower():
            # Smaller models need less context
            return min(base_ctx, 2048)
        else:
            return base_ctx
    
    def _get_optimal_thread_count(self) -> int:
        """
        Determine optimal thread count for model inference
        
        Returns:
            Optimal thread count
        """
        try:
            import multiprocessing
            cpu_count = multiprocessing.cpu_count()
            
            # Use 75% of available cores for inference
            optimal = max(1, int(cpu_count * 0.75))
            
            # Cap at 8 threads to avoid diminishing returns
            return min(optimal, 8)
        except:
            return 4  # Safe default
    
    def _get_gpu_layers(self, model_name: str) -> int:
        """
        Determine number of GPU layers to use
        
        Args:
            model_name: Name of the model
            
        Returns:
            Number of GPU layers to offload
        """
        # Check if MPS (Metal Performance Shaders) is available for macOS
        try:
            import platform
            if platform.system() == 'Darwin':  # macOS
                # Use Metal acceleration if available
                return 1  # Enable GPU acceleration
        except:
            pass
        
        # For now, default to CPU-only
        # This can be enhanced to detect CUDA/ROCm availability
        return 0
    
    def get_resource_usage(self) -> Dict[str, Any]:
        """
        Get current resource usage for the model
        
        Returns:
            Resource usage statistics
        """
        try:
            memory = psutil.virtual_memory()
            process = psutil.Process()
            
            return {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": memory.percent,
                "memory_available_gb": memory.available / (1024**3),
                "process_memory_mb": process.memory_info().rss / (1024**2),
                "model_loaded": self.current_model_name is not None,
                "current_model": self.current_model_name
            }
        except Exception as e:
            logger.error(f"Failed to get resource usage: {e}")
            return {
                "error": str(e),
                "model_loaded": self.current_model_name is not None
            }
    
    def refresh_models(self) -> int:
        """
        Refresh the list of available models
        
        Returns:
            Number of models found
        """
        self.available_models = self._scan_models()
        return len(self.available_models)