"""
Configuration settings for the AI ML Service
"""

import os
from typing import Optional, List
from pydantic import BaseSettings, Field


class DatabaseSettings(BaseSettings):
    """Database configuration"""
    host: str = Field(default="localhost", env="POSTGRES_HOST")
    port: int = Field(default=5432, env="POSTGRES_PORT")
    database: str = Field(default="weedgo_ai", env="POSTGRES_DB")
    username: str = Field(default="weedgo", env="POSTGRES_USER")
    password: str = Field(default="your_password_here", env="POSTGRES_PASSWORD")
    
    @property
    def url(self) -> str:
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"


class RedisSettings(BaseSettings):
    """Redis configuration"""
    host: str = Field(default="localhost", env="REDIS_HOST")
    port: int = Field(default=6379, env="REDIS_PORT")
    db: int = Field(default=0, env="REDIS_DB")
    password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    
    @property
    def url(self) -> str:
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"


class MilvusSettings(BaseSettings):
    """Milvus vector database configuration"""
    host: str = Field(default="localhost", env="MILVUS_HOST")
    port: int = Field(default=19530, env="MILVUS_PORT")
    username: Optional[str] = Field(default=None, env="MILVUS_USER")
    password: Optional[str] = Field(default=None, env="MILVUS_PASSWORD")


class ModelSettings(BaseSettings):
    """ML Model configuration"""
    model_path: str = Field(default="/models", env="MODEL_PATH")
    
    # Face Recognition Models
    face_model_name: str = Field(default="buffalo_l", env="FACE_MODEL_NAME")
    face_threshold: float = Field(default=0.85, env="FACE_THRESHOLD")
    
    # NLP Models
    nlp_model_name: str = Field(default="sentence-transformers/all-MiniLM-L6-v2", env="NLP_MODEL_NAME")
    llm_model_name: str = Field(default="microsoft/DialoGPT-medium", env="LLM_MODEL_NAME")
    
    # OCR Models
    ocr_engines: List[str] = Field(default=["easyocr", "paddleocr"], env="OCR_ENGINES")
    
    # Pricing Models
    pricing_model_type: str = Field(default="xgboost", env="PRICING_MODEL_TYPE")
    
    # Model serving
    batch_size: int = Field(default=32, env="MODEL_BATCH_SIZE")
    max_sequence_length: int = Field(default=512, env="MAX_SEQUENCE_LENGTH")


class ScrapingSettings(BaseSettings):
    """Web scraping configuration"""
    user_agents: List[str] = Field(default=[
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ])
    
    request_delay: float = Field(default=1.0, env="SCRAPING_DELAY")
    timeout: int = Field(default=30, env="SCRAPING_TIMEOUT")
    max_retries: int = Field(default=3, env="SCRAPING_MAX_RETRIES")
    use_proxy: bool = Field(default=False, env="USE_PROXY")
    proxy_list: List[str] = Field(default=[], env="PROXY_LIST")


class LanguageSettings(BaseSettings):
    """Multi-language configuration"""
    supported_languages: List[str] = Field(default=[
        "en",  # English
        "fr",  # French
        "pt",  # Portuguese
        "es",  # Spanish
        "ar",  # Arabic
        "zh"   # Chinese
    ])
    
    default_language: str = Field(default="en", env="DEFAULT_LANGUAGE")
    
    # Translation models
    translation_model: str = Field(default="facebook/m2m100_418M", env="TRANSLATION_MODEL")
    
    # Language detection
    language_detection_threshold: float = Field(default=0.8, env="LANG_DETECTION_THRESHOLD")


class SecuritySettings(BaseSettings):
    """Security and privacy configuration"""
    encryption_key: str = Field(default="changeme", env="ENCRYPTION_KEY")
    jwt_secret: str = Field(default="changeme", env="JWT_SECRET")
    
    # Biometric privacy
    use_cancelable_biometrics: bool = Field(default=True, env="USE_CANCELABLE_BIOMETRICS")
    biometric_salt_rotation_days: int = Field(default=90, env="BIOMETRIC_SALT_ROTATION_DAYS")
    
    # Data retention
    face_template_retention_days: int = Field(default=365, env="FACE_TEMPLATE_RETENTION_DAYS")
    chat_history_retention_days: int = Field(default=30, env="CHAT_HISTORY_RETENTION_DAYS")
    
    # Rate limiting
    rate_limit_requests_per_minute: int = Field(default=60, env="RATE_LIMIT_RPM")


class MonitoringSettings(BaseSettings):
    """Monitoring and observability configuration"""
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    metrics_port: int = Field(default=8501, env="METRICS_PORT")
    
    # Performance monitoring
    slow_request_threshold_ms: int = Field(default=1000, env="SLOW_REQUEST_THRESHOLD_MS")
    
    # Model monitoring
    model_drift_threshold: float = Field(default=0.05, env="MODEL_DRIFT_THRESHOLD")
    accuracy_monitoring_interval_hours: int = Field(default=24, env="ACCURACY_MONITORING_INTERVAL")


class Settings(BaseSettings):
    """Main configuration class"""
    
    # Service configuration
    grpc_port: int = Field(default=50051, env="GRPC_PORT")
    max_workers: int = Field(default=10, env="MAX_WORKERS")
    environment: str = Field(default="development", env="ENVIRONMENT")
    
    # Component settings
    database: DatabaseSettings = DatabaseSettings()
    redis: RedisSettings = RedisSettings()
    milvus: MilvusSettings = MilvusSettings()
    models: ModelSettings = ModelSettings()
    scraping: ScrapingSettings = ScrapingSettings()
    languages: LanguageSettings = LanguageSettings()
    security: SecuritySettings = SecuritySettings()
    monitoring: MonitoringSettings = MonitoringSettings()
    
    # Canadian Cannabis specific
    enable_age_verification: bool = Field(default=True, env="ENABLE_AGE_VERIFICATION")
    minimum_age: int = Field(default=19, env="MINIMUM_AGE")  # Most provinces are 19, Alberta is 18
    enable_medical_verification: bool = Field(default=True, env="ENABLE_MEDICAL_VERIFICATION")
    
    # Cannabis knowledge base
    strain_database_path: str = Field(default="/datasets/canadian_strains.json", env="STRAIN_DATABASE_PATH")
    terpene_database_path: str = Field(default="/datasets/terpene_profiles.json", env="TERPENE_DATABASE_PATH")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        return self.environment.lower() == "development"
    
    def get_model_path(self, model_name: str) -> str:
        """Get full path to a model file"""
        return os.path.join(self.models.model_path, model_name)
    
    def get_dataset_path(self, dataset_name: str) -> str:
        """Get full path to a dataset file"""
        return os.path.join("/datasets", dataset_name)