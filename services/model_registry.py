"""
Model Registry Service for managing AI model versions and deployments.
Handles model loading, versioning, and fallback to base models.
"""
import os
import json
import hashlib
import shutil
import asyncio
import asyncpg
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

# Import llama-cpp-python for model loading
try:
    from llama_cpp import Llama
    LLAMA_CPP_AVAILABLE = True
except ImportError:
    LLAMA_CPP_AVAILABLE = False
    logging.warning("llama-cpp-python not installed. Model loading will be simulated.")

logger = logging.getLogger(__name__)

class ModelStatus(Enum):
    """Model status enum"""
    TRAINING = "training"
    READY = "ready"
    DEPLOYED = "deployed"
    ARCHIVED = "archived"
    FAILED = "failed"

class DeploymentEnvironment(Enum):
    """Deployment environment enum"""
    DEV = "dev"
    STAGING = "staging"
    PRODUCTION = "production"

@dataclass
class ModelConfig:
    """Configuration for a model version"""
    version_id: str
    model_name: str
    base_model: str
    version_number: str
    model_type: str = "llama"
    model_size: str = "7B"
    quantization: str = "Q4_K_M"
    context_length: int = 4096
    n_gpu_layers: int = -1  # -1 means use all available GPU layers
    n_threads: int = 4
    temperature: float = 0.7
    max_tokens: int = 512
    top_p: float = 0.95
    top_k: int = 40
    repeat_penalty: float = 1.1
    stop_sequences: List[str] = None
    
    def __post_init__(self):
        if self.stop_sequences is None:
            self.stop_sequences = ["</s>", "[/INST]", "Human:", "Assistant:"]

class ModelRegistry:
    """
    Manages model versions, loading, and deployments.
    Ensures base model fallback when no trained model exists.
    """
    
    def __init__(self, db_pool: Optional[asyncpg.Pool] = None):
        self.db_pool = db_pool
        self.models_dir = Path("/Users/charrcy/projects/WeedGo/microservices/ai-engine-service/models")
        self.base_models_dir = self.models_dir / "base"
        self.trained_models_dir = self.models_dir / "trained"
        self.checkpoints_dir = self.models_dir / "checkpoints"
        self.temp_dir = self.models_dir / "temp"
        self.exports_dir = self.models_dir / "exports"
        
        # Model cache
        self._loaded_models: Dict[str, Any] = {}
        self._active_model = None
        self._active_model_config = None
        
        # Ensure directories exist
        for dir_path in [self.base_models_dir, self.trained_models_dir, 
                         self.checkpoints_dir, self.temp_dir, self.exports_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    async def initialize_db(self):
        """Initialize database connection"""
        if not self.db_pool:
            try:
                self.db_pool = await asyncpg.create_pool(
                    host='localhost',
                    port=5434,
                    database='ai_engine',
                    user='weedgo',
                    password='your_password_here',
                    min_size=2,
                    max_size=10
                )
                logger.info("ModelRegistry database pool initialized")
            except Exception as db_error:
                logger.warning(f"ModelRegistry database pool creation failed (running without DB): {db_error}")
                self.db_pool = None
    
    async def get_active_model(self) -> Optional[Dict[str, Any]]:
        """
        Get the currently active model.
        Falls back to base model if no trained model exists.
        """
        if not self.db_pool:
            await self.initialize_db()
        
        if not self.db_pool:
            # Return a default model config if no database
            logger.info("No database available, returning default model config")
            return {
                'model_name': 'llama3.2:1b',
                'model_type': 'base',
                'version': '1.0.0',
                'is_active': True,
                'status': 'deployed'
            }
        
        async with self.db_pool.acquire() as conn:
            # First, try to get the active deployed model
            active_model = await conn.fetchrow("""
                SELECT mv.*, md.environment, md.traffic_percentage
                FROM model_versions mv
                LEFT JOIN model_deployments md ON mv.id = md.model_version_id
                WHERE mv.is_active = true 
                AND mv.status = 'deployed'
                AND (md.status = 'active' OR md.status IS NULL)
                ORDER BY mv.created_at DESC
                LIMIT 1
            """)
            
            if active_model:
                return dict(active_model)
            
            # If no active model, try to get the default base model
            base_model = await conn.fetchrow("""
                SELECT * FROM base_models
                WHERE is_default = true AND is_available = true
                LIMIT 1
            """)
            
            if base_model:
                logger.info(f"No active trained model found. Using base model: {base_model['model_name']}")
                return dict(base_model)
            
            # If no default base model, get any available base model
            any_base = await conn.fetchrow("""
                SELECT * FROM base_models
                WHERE is_available = true
                LIMIT 1
            """)
            
            if any_base:
                logger.warning(f"No default base model. Using available model: {any_base['model_name']}")
                return dict(any_base)
            
            return None
    
    async def load_model(self, model_config: Optional[ModelConfig] = None) -> Any:
        """
        Load a model with the specified configuration.
        Falls back to base model if specific model not found.
        """
        if model_config is None:
            # Load the active model
            active_model_data = await self.get_active_model()
            if not active_model_data:
                # Check for local base models
                base_models = list(self.base_models_dir.glob("*.gguf"))
                if base_models:
                    logger.info(f"Loading local base model: {base_models[0].name}")
                    model_config = ModelConfig(
                        version_id="base_local_fallback",
                        model_name=base_models[0].stem,
                        base_model=base_models[0].stem,
                        version_number="1.0.0"
                    )
                    model_path = str(base_models[0])
                else:
                    raise ValueError("No models available. Please download a base model first.")
            else:
                model_config = self._create_config_from_db(active_model_data)
                model_path = self._resolve_model_path(active_model_data)
        else:
            model_path = self._resolve_model_path_from_config(model_config)
        
        # Check if model is already loaded
        if model_config.version_id in self._loaded_models:
            logger.info(f"Using cached model: {model_config.model_name}")
            self._active_model = self._loaded_models[model_config.version_id]
            self._active_model_config = model_config
            return self._active_model
        
        # Load the model
        logger.info(f"Loading model: {model_config.model_name} from {model_path}")
        
        if not os.path.exists(model_path):
            # Try to find an alternative model
            logger.warning(f"Model file not found: {model_path}")
            model_path = await self._find_alternative_model()
            if not model_path:
                raise FileNotFoundError(f"No model file found. Please download a base model.")
        
        if LLAMA_CPP_AVAILABLE:
            try:
                model = Llama(
                    model_path=model_path,
                    n_ctx=model_config.context_length,
                    n_gpu_layers=model_config.n_gpu_layers,
                    n_threads=model_config.n_threads,
                    verbose=False
                )
                
                # Cache the loaded model
                self._loaded_models[model_config.version_id] = model
                self._active_model = model
                self._active_model_config = model_config
                
                logger.info(f"Successfully loaded model: {model_config.model_name}")
                
                # Update database to mark as active
                await self._update_model_status(model_config.version_id, "deployed", is_active=True)
                
                return model
                
            except Exception as e:
                logger.error(f"Failed to load model: {e}")
                # Try to load a fallback base model
                return await self._load_fallback_model()
        else:
            # Simulate model loading for development
            logger.warning("llama-cpp-python not available. Simulating model load.")
            mock_model = {
                "model_path": model_path,
                "config": asdict(model_config),
                "loaded_at": datetime.utcnow().isoformat()
            }
            self._loaded_models[model_config.version_id] = mock_model
            self._active_model = mock_model
            self._active_model_config = model_config
            return mock_model
    
    async def _find_alternative_model(self) -> Optional[str]:
        """Find an alternative model file when the specified one is not found"""
        # Check base models directory
        base_models = list(self.base_models_dir.glob("*.gguf"))
        if base_models:
            logger.info(f"Found alternative base model: {base_models[0]}")
            return str(base_models[0])
        
        # Check trained models directory
        trained_models = list(self.trained_models_dir.glob("*.gguf"))
        if trained_models:
            logger.info(f"Found alternative trained model: {trained_models[0]}")
            return str(trained_models[0])
        
        return None
    
    async def _load_fallback_model(self) -> Any:
        """Load a fallback base model when primary model fails"""
        logger.info("Loading fallback base model...")
        
        # Find first available base model
        base_models = list(self.base_models_dir.glob("*.gguf"))
        if not base_models:
            raise FileNotFoundError("No base models available for fallback")
        
        fallback_path = str(base_models[0])
        fallback_config = ModelConfig(
            version_id="fallback_base",
            model_name=base_models[0].stem,
            base_model=base_models[0].stem,
            version_number="1.0.0"
        )
        
        if LLAMA_CPP_AVAILABLE:
            try:
                model = Llama(
                    model_path=fallback_path,
                    n_ctx=fallback_config.context_length,
                    n_gpu_layers=0,  # Use CPU for fallback
                    n_threads=fallback_config.n_threads,
                    verbose=False
                )
                
                self._loaded_models[fallback_config.version_id] = model
                self._active_model = model
                self._active_model_config = fallback_config
                
                logger.info(f"Successfully loaded fallback model: {fallback_config.model_name}")
                return model
                
            except Exception as e:
                logger.error(f"Failed to load fallback model: {e}")
                raise
        else:
            # Return mock model for development
            mock_model = {
                "model_path": fallback_path,
                "config": asdict(fallback_config),
                "is_fallback": True
            }
            self._active_model = mock_model
            self._active_model_config = fallback_config
            return mock_model
    
    def _create_config_from_db(self, model_data: Dict[str, Any]) -> ModelConfig:
        """Create ModelConfig from database record"""
        return ModelConfig(
            version_id=model_data.get('version_id', model_data.get('model_id', 'unknown')),
            model_name=model_data.get('model_name', 'Unknown Model'),
            base_model=model_data.get('base_model', model_data.get('model_family', 'llama')),
            version_number=model_data.get('version_number', '1.0.0'),
            model_type=model_data.get('model_type', 'llama'),
            model_size=model_data.get('model_size', '7B'),
            quantization=model_data.get('quantization', 'Q4_K_M'),
            context_length=model_data.get('context_length', 4096)
        )
    
    def _resolve_model_path(self, model_data: Dict[str, Any]) -> str:
        """Resolve the actual file path for a model"""
        if 'model_path' in model_data:
            return model_data['model_path']
        elif 'file_path' in model_data:
            return model_data['file_path']
        else:
            # Try to construct path from model name
            model_name = model_data.get('model_name', 'unknown')
            # Check trained models first
            trained_path = self.trained_models_dir / f"{model_name}.gguf"
            if trained_path.exists():
                return str(trained_path)
            # Check base models
            base_path = self.base_models_dir / f"{model_name}.gguf"
            if base_path.exists():
                return str(base_path)
            # Return expected path even if it doesn't exist
            return str(base_path)
    
    def _resolve_model_path_from_config(self, config: ModelConfig) -> str:
        """Resolve model path from ModelConfig"""
        # Check trained models first
        trained_path = self.trained_models_dir / f"{config.model_name}.gguf"
        if trained_path.exists():
            return str(trained_path)
        
        # Check base models
        base_path = self.base_models_dir / f"{config.base_model}.gguf"
        if base_path.exists():
            return str(base_path)
        
        # Return expected path
        return str(trained_path)
    
    async def _update_model_status(self, version_id: str, status: str, is_active: bool = False):
        """Update model status in database"""
        if not self.db_pool:
            return
        
        try:
            async with self.db_pool.acquire() as conn:
                # Check if it's a model version
                await conn.execute("""
                    UPDATE model_versions
                    SET status = $1, is_active = $2, updated_at = CURRENT_TIMESTAMP
                    WHERE version_id = $3
                """, status, is_active, version_id)
                
                if is_active:
                    # Deactivate other models
                    await conn.execute("""
                        UPDATE model_versions
                        SET is_active = false
                        WHERE version_id != $1
                    """, version_id)
        except Exception as e:
            logger.error(f"Failed to update model status: {e}")
    
    async def register_model(self, 
                            model_name: str,
                            base_model: str,
                            model_path: str,
                            version_number: Optional[str] = None,
                            **kwargs) -> str:
        """Register a new model version in the registry"""
        if not self.db_pool:
            await self.initialize_db()
        
        version_id = f"{model_name}_{uuid.uuid4().hex[:8]}"
        if version_number is None:
            version_number = await self._get_next_version_number(model_name)
        
        # Calculate file size
        file_size_mb = 0
        if os.path.exists(model_path):
            file_size_mb = os.path.getsize(model_path) / (1024 * 1024)
        
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO model_versions (
                    version_id, model_name, base_model, version_number,
                    model_type, model_size, quantization, model_path,
                    file_size_mb, status, training_method, training_params,
                    datasets_used, created_by
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
            """, version_id, model_name, base_model, version_number,
                kwargs.get('model_type', 'llama'),
                kwargs.get('model_size', '7B'),
                kwargs.get('quantization', 'Q4_K_M'),
                model_path, file_size_mb, 'ready',
                kwargs.get('training_method', 'base'),
                json.dumps(kwargs.get('training_params', {})),
                json.dumps(kwargs.get('datasets_used', [])),
                kwargs.get('created_by', 'system'))
        
        logger.info(f"Registered model: {model_name} version {version_number}")
        return version_id
    
    async def _get_next_version_number(self, model_name: str) -> str:
        """Generate next version number for a model"""
        if not self.db_pool:
            await self.initialize_db()
        
        async with self.db_pool.acquire() as conn:
            result = await conn.fetchval("""
                SELECT MAX(version_number) FROM model_versions
                WHERE model_name = $1
            """, model_name)
            
            if result:
                # Parse version and increment
                parts = result.split('.')
                if len(parts) == 3:
                    major, minor, patch = parts
                    return f"{major}.{minor}.{int(patch) + 1}"
            
            return "1.0.0"
    
    async def list_models(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all registered models"""
        if not self.db_pool:
            await self.initialize_db()
        
        query = "SELECT * FROM model_versions"
        params = []
        
        if status:
            query += " WHERE status = $1"
            params.append(status)
        
        query += " ORDER BY created_at DESC"
        
        async with self.db_pool.acquire() as conn:
            results = await conn.fetch(query, *params)
            return [dict(r) for r in results]
    
    async def list_base_models(self) -> List[Dict[str, Any]]:
        """List all available base models"""
        if not self.db_pool:
            await self.initialize_db()
        
        async with self.db_pool.acquire() as conn:
            results = await conn.fetch("""
                SELECT * FROM base_models
                WHERE is_available = true
                ORDER BY is_default DESC, model_family, model_size
            """)
            
            models = [dict(r) for r in results]
            
            # Also check for local files not in database
            local_models = list(self.base_models_dir.glob("*.gguf"))
            registered_paths = {m['file_path'] for m in models}
            
            for model_file in local_models:
                model_path = str(model_file)
                if model_path not in registered_paths:
                    # Add unregistered local model
                    models.append({
                        'model_id': f"local_{model_file.stem}",
                        'model_name': model_file.stem,
                        'file_path': model_path,
                        'file_size_gb': model_file.stat().st_size / (1024**3),
                        'is_available': True,
                        'source': 'local',
                        'download_status': 'downloaded'
                    })
            
            return models
    
    async def deploy_model(self, version_id: str, environment: str = "production") -> bool:
        """Deploy a model version to specified environment"""
        if not self.db_pool:
            await self.initialize_db()
        
        deployment_id = f"deploy_{uuid.uuid4().hex[:8]}"
        
        async with self.db_pool.acquire() as conn:
            # Get model version
            model = await conn.fetchrow("""
                SELECT id, status FROM model_versions
                WHERE version_id = $1
            """, version_id)
            
            if not model or model['status'] != 'ready':
                logger.error(f"Model {version_id} not ready for deployment")
                return False
            
            # Deactivate current deployment in this environment
            await conn.execute("""
                UPDATE model_deployments
                SET status = 'inactive', undeployed_at = CURRENT_TIMESTAMP
                WHERE environment = $1 AND status = 'active'
            """, environment)
            
            # Create new deployment
            await conn.execute("""
                INSERT INTO model_deployments (
                    deployment_id, model_version_id, environment,
                    deployment_type, status, deployed_at, deployed_by
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, deployment_id, model['id'], environment,
                'replace', 'active', datetime.utcnow(), 'system')
            
            # Update model version status
            await conn.execute("""
                UPDATE model_versions
                SET status = 'deployed', is_active = true
                WHERE id = $1
            """, model['id'])
            
            # Deactivate other models
            await conn.execute("""
                UPDATE model_versions
                SET is_active = false
                WHERE id != $1
            """, model['id'])
        
        logger.info(f"Deployed model {version_id} to {environment}")
        
        # Reload the model if it's being deployed to production
        if environment == "production":
            await self.load_model()
        
        return True
    
    async def get_or_create_base_model(self) -> Dict[str, Any]:
        """
        Ensure a base model is available, downloading if necessary.
        This is the main entry point to ensure base model availability.
        """
        # Check for active model first
        active_model = await self.get_active_model()
        if active_model:
            return active_model
        
        # Check for any local base model files
        local_models = list(self.base_models_dir.glob("*.gguf"))
        if local_models:
            # Register the first local model as default
            model_file = local_models[0]
            logger.info(f"Found local base model: {model_file.name}")
            
            if self.db_pool:
                async with self.db_pool.acquire() as conn:
                    # Register in database
                    model_id = f"local_{model_file.stem}"
                    await conn.execute("""
                        INSERT INTO base_models (
                            model_id, model_name, file_path, file_format,
                            file_size_gb, is_available, is_default,
                            download_status, source
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                        ON CONFLICT (model_id) DO UPDATE
                        SET is_available = true, is_default = true
                    """, model_id, model_file.stem, str(model_file), 'gguf',
                        model_file.stat().st_size / (1024**3),
                        True, True, 'downloaded', 'local')
                    
                    return {
                        'model_id': model_id,
                        'model_name': model_file.stem,
                        'file_path': str(model_file),
                        'is_available': True
                    }
            else:
                return {
                    'model_id': f"local_{model_file.stem}",
                    'model_name': model_file.stem,
                    'file_path': str(model_file),
                    'is_available': True
                }
        
        # No local models found
        logger.warning("No base models found. Please download a model to continue.")
        return None
    
    def get_active_model_config(self) -> Optional[ModelConfig]:
        """Get the configuration of the currently active model"""
        return self._active_model_config
    
    def is_model_loaded(self) -> bool:
        """Check if a model is currently loaded"""
        return self._active_model is not None
    
    async def unload_model(self, version_id: Optional[str] = None):
        """Unload a model from memory"""
        if version_id:
            if version_id in self._loaded_models:
                del self._loaded_models[version_id]
                logger.info(f"Unloaded model: {version_id}")
        else:
            # Unload all models
            self._loaded_models.clear()
            self._active_model = None
            self._active_model_config = None
            logger.info("Unloaded all models")
    
    async def cleanup(self):
        """Cleanup resources"""
        await self.unload_model()
        if self.db_pool:
            await self.db_pool.close()
            logger.info("ModelRegistry database pool closed")