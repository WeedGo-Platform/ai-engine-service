"""
Configuration management for WeedGo AI Engine
Centralized settings with environment variable support
"""

import os
from typing import List, Optional
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field, validator

class Settings(BaseSettings):
    """Application settings with validation"""
    
    # API Configuration
    HOST: str = Field(default="0.0.0.0", env="AI_ENGINE_HOST")
    PORT: int = Field(default=8000, env="AI_ENGINE_PORT")
    DEBUG: bool = Field(default=False, env="AI_ENGINE_DEBUG")
    
    # CORS
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        env="ALLOWED_ORIGINS"
    )
    
    # Database
    DB_HOST: str = Field(default="localhost", env="DB_HOST")
    DB_PORT: int = Field(default=5434, env="DB_PORT")
    DB_NAME: str = Field(default="ai_engine", env="DB_NAME")
    DB_USER: str = Field(default="weedgo", env="DB_USER")
    DB_PASSWORD: str = Field(default="your_password_here", env="DB_PASSWORD")
    
    # Redis
    REDIS_HOST: str = Field(default="localhost", env="REDIS_HOST")
    REDIS_PORT: int = Field(default=6381, env="REDIS_PORT")
    REDIS_PASSWORD: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    REDIS_DB: int = Field(default=0, env="REDIS_DB")
    
    # Model Configuration
    MODELS_DIR: Path = Field(
        default=Path(__file__).parent / "models",
        env="MODELS_DIR"
    )
    LLAMA_MODEL: str = Field(
        default="llama-2-7b-chat.Q4_K_M.gguf",
        env="LLAMA_MODEL"
    )
    MISTRAL_MODEL: str = Field(
        default="mistral-7b-instruct-v0.2.Q4_K_M.gguf",
        env="MISTRAL_MODEL"
    )
    
    # Model Parameters - Optimized for M3 Max Performance
    MODEL_N_CTX: int = Field(default=1024, env="MODEL_N_CTX")  # Reduced for speed
    MODEL_N_THREADS: int = Field(default=16, env="MODEL_N_THREADS")  # M3 Max cores
    MODEL_N_GPU_LAYERS: int = Field(default=32, env="MODEL_N_GPU_LAYERS")  # Full Metal
    MODEL_TEMPERATURE: float = Field(default=0.7, env="MODEL_TEMPERATURE")
    MODEL_MAX_TOKENS: int = Field(default=150, env="MODEL_MAX_TOKENS")  # Shorter responses
    MODEL_TIMEOUT: int = Field(default=5, env="MODEL_TIMEOUT")  # 5 second timeout
    MODEL_TOP_P: float = Field(default=0.95, env="MODEL_TOP_P")
    MODEL_TOP_K: int = Field(default=40, env="MODEL_TOP_K")
    MODEL_REPEAT_PENALTY: float = Field(default=1.1, env="MODEL_REPEAT_PENALTY")
    MODEL_SEED: int = Field(default=-1, env="MODEL_SEED")
    
    # RAG Configuration
    MILVUS_HOST: str = Field(default="localhost", env="MILVUS_HOST")
    MILVUS_PORT: int = Field(default=19530, env="MILVUS_PORT")
    EMBEDDING_MODEL: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        env="EMBEDDING_MODEL"
    )
    EMBEDDING_DIM: int = Field(default=384, env="EMBEDDING_DIM")
    RERANKER_MODEL: str = Field(
        default="cross-encoder/ms-marco-MiniLM-L-6-v2",
        env="RERANKER_MODEL"
    )
    RAG_TOP_K: int = Field(default=10, env="RAG_TOP_K")
    RAG_SIMILARITY_THRESHOLD: float = Field(default=0.7, env="RAG_SIMILARITY_THRESHOLD")
    RAG_CHUNK_SIZE: int = Field(default=500, env="RAG_CHUNK_SIZE")
    RAG_CHUNK_OVERLAP: int = Field(default=50, env="RAG_CHUNK_OVERLAP")
    
    # Context Management
    CONTEXT_WINDOW_SIZE: int = Field(default=20, env="CONTEXT_WINDOW_SIZE")
    CONTEXT_MAX_TOKENS: int = Field(default=2000, env="CONTEXT_MAX_TOKENS")
    MEMORY_STRATEGY: str = Field(default="summary_buffer", env="MEMORY_STRATEGY")
    SESSION_TIMEOUT_HOURS: int = Field(default=24, env="SESSION_TIMEOUT_HOURS")
    
    # Features
    ENABLE_AB_TESTING: bool = Field(default=False, env="ENABLE_AB_TESTING")
    ENABLE_CACHING: bool = Field(default=True, env="ENABLE_CACHING")
    CACHE_TTL: int = Field(default=3600, env="CACHE_TTL")
    ENABLE_METRICS: bool = Field(default=True, env="ENABLE_METRICS")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FILE: Path = Field(
        default=Path(__file__).parent / "logs" / "ai_engine.log",
        env="LOG_FILE"
    )
    
    # Security
    API_KEY: Optional[str] = Field(default=None, env="AI_ENGINE_API_KEY")
    ENABLE_AUTH: bool = Field(default=False, env="ENABLE_AUTH")
    JWT_SECRET: Optional[str] = Field(default=None, env="JWT_SECRET")
    JWT_ALGORITHM: str = Field(default="HS256", env="JWT_ALGORITHM")
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    RATE_LIMIT_REQUESTS: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    RATE_LIMIT_PERIOD: int = Field(default=60, env="RATE_LIMIT_PERIOD")
    
    # Business Logic
    SUPPORTED_LANGUAGES: List[str] = Field(
        default=["en", "fr", "es", "pt", "ar", "zh"],
        env="SUPPORTED_LANGUAGES"
    )
    DEFAULT_LANGUAGE: str = Field(default="en", env="DEFAULT_LANGUAGE")
    MIN_AGE: int = Field(default=19, env="MIN_AGE")  # Ontario requirement
    
    # Training Data
    TRAINING_DATA_DIR: Path = Field(
        default=Path(__file__).parent / "data" / "training",
        env="TRAINING_DATA_DIR"
    )
    OCS_DATA_FILE: Path = Field(
        default=Path(__file__).parent / "data" / "ocs_products.xlsx",
        env="OCS_DATA_FILE"
    )
    
    # Neo4j Graph Database
    NEO4J_URI: str = Field(default="bolt://localhost:7687", env="NEO4J_URI")
    NEO4J_USER: str = Field(default="neo4j", env="NEO4J_USER")
    NEO4J_PASSWORD: str = Field(default="password", env="NEO4J_PASSWORD")
    NEO4J_DATABASE: str = Field(default="neo4j", env="NEO4J_DATABASE")
    
    # Elasticsearch
    ELASTICSEARCH_HOST: str = Field(default="localhost", env="ELASTICSEARCH_HOST")
    ELASTICSEARCH_PORT: int = Field(default=9200, env="ELASTICSEARCH_PORT")
    ELASTICSEARCH_USER: Optional[str] = Field(default=None, env="ELASTICSEARCH_USER")
    ELASTICSEARCH_PASSWORD: Optional[str] = Field(default=None, env="ELASTICSEARCH_PASSWORD")
    ELASTICSEARCH_INDEX: str = Field(default="cannabis_products", env="ELASTICSEARCH_INDEX")
    
    @validator("MODELS_DIR", "LOG_FILE", "TRAINING_DATA_DIR")
    def create_directories(cls, v):
        """Ensure directories exist"""
        if isinstance(v, Path):
            v.parent.mkdir(parents=True, exist_ok=True)
        return v
    
    @validator("LOG_LEVEL")
    def validate_log_level(cls, v):
        """Validate log level"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v.upper()
    
    @property
    def database_url(self) -> str:
        """Generate database URL"""
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    @property
    def redis_url(self) -> str:
        """Generate Redis URL"""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    @property
    def llama_model_path(self) -> Path:
        """Get full path to Llama model"""
        return self.MODELS_DIR / self.LLAMA_MODEL
    
    @property
    def mistral_model_path(self) -> Path:
        """Get full path to Mistral model"""
        return self.MODELS_DIR / self.MISTRAL_MODEL
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

# Create settings instance
settings = Settings()

# Environment-specific configurations
class DevelopmentSettings(Settings):
    """Development environment settings"""
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    ENABLE_AUTH: bool = False
    RATE_LIMIT_ENABLED: bool = False

class ProductionSettings(Settings):
    """Production environment settings"""
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    ENABLE_AUTH: bool = True
    RATE_LIMIT_ENABLED: bool = True
    MODEL_N_GPU_LAYERS: int = 32  # Use GPU in production

class TestSettings(Settings):
    """Test environment settings"""
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    DB_NAME: str = "ai_engine_test"
    REDIS_DB: int = 1
    ENABLE_AUTH: bool = False

# Select configuration based on environment
def get_settings() -> Settings:
    """Get settings based on environment"""
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    if env == "production":
        return ProductionSettings()
    elif env == "test":
        return TestSettings()
    else:
        return DevelopmentSettings()

# Export configured settings
if __name__ != "__main__":
    settings = get_settings()