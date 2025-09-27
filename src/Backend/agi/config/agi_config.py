"""
AGI System Configuration
Central configuration for the general-purpose AI platform
"""

import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent.parent
MODELS_DIR = Path("/Users/charrcy/projects/WeedGo/microservices/ai-engine-service/models")
KNOWLEDGE_DIR = BASE_DIR / "knowledge" / "stores"
CACHE_DIR = BASE_DIR / "cache"

# Ensure directories exist
KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)

class ModelSize(Enum):
    """Model size categories for routing decisions"""
    TINY = "tiny"      # < 1B parameters
    SMALL = "small"    # 1-3B parameters
    MEDIUM = "medium"  # 7-13B parameters
    LARGE = "large"    # 30-70B parameters
    XLARGE = "xlarge"  # > 70B parameters

class AgentRole(Enum):
    """Standard agent roles in the system"""
    CONVERSATIONAL = "conversational"
    TASK = "task"
    RESEARCH = "research"
    DECISION = "decision"
    MONITOR = "monitor"
    ORCHESTRATOR = "orchestrator"

@dataclass
class DatabaseConfig:
    """Database configuration with agi prefix"""
    host: str = os.getenv('DB_HOST', 'localhost')
    port: int = int(os.getenv('DB_PORT', 5434))
    user: str = os.getenv('DB_USER', 'weedgo')
    password: str = os.getenv('DB_PASSWORD', 'your_password_here')
    database: str = os.getenv('DB_NAME', 'ai_engine')
    schema_prefix: str = "agi"
    pool_min_size: int = 5
    pool_max_size: int = 20

    @property
    def connection_string(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

@dataclass
class RedisConfig:
    """Redis configuration with agi prefix"""
    host: str = os.getenv('REDIS_HOST', 'localhost')
    port: int = int(os.getenv('REDIS_PORT', 6379))
    password: Optional[str] = os.getenv('REDIS_PASSWORD', None)
    db: int = int(os.getenv('REDIS_DB', 0))
    key_prefix: str = "agi:"
    ttl_default: int = 3600  # 1 hour default TTL

    @property
    def connection_string(self) -> str:
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"

@dataclass
class ModelConfig:
    """Model configuration and registry"""
    default_model: str = "qwen2.5_0.5b_instruct_q4_k_m"
    model_timeout: int = 30  # seconds
    max_context_length: int = 8192
    temperature_default: float = 0.7
    max_tokens_default: int = 2048

    # Model routing rules based on complexity
    routing_rules: Dict[str, ModelSize] = field(default_factory=lambda: {
        "simple_qa": ModelSize.TINY,
        "conversation": ModelSize.SMALL,
        "analysis": ModelSize.MEDIUM,
        "reasoning": ModelSize.LARGE,
        "creative": ModelSize.LARGE,
    })

    # Model registry mapping
    size_to_models: Dict[ModelSize, List[str]] = field(default_factory=lambda: {
        ModelSize.TINY: ["qwen2.5_0.5b_instruct_q4_k_m"],
        ModelSize.SMALL: ["phi_3_mini_4k_instruct_q4", "stablelm_zephyr_3b_q4"],
        ModelSize.MEDIUM: ["llama_3_8b_instruct_q4", "mistral_7b_instruct_v0_2_q4"],
        ModelSize.LARGE: ["llama_3_70b_instruct_q4"],
        ModelSize.XLARGE: [],
    })

@dataclass
class MemoryConfig:
    """Memory system configuration"""
    working_memory_size: int = 10  # Number of recent messages
    episodic_memory_days: int = 30  # Days to retain episodic memory
    semantic_embedding_model: str = "all-MiniLM-L6-v2"  # Sentence transformer model
    vector_dimension: int = 384
    similarity_threshold: float = 0.7

    # Memory backends
    working_backend: str = "redis"  # Fast access
    episodic_backend: str = "postgres"  # Structured storage
    semantic_backend: str = "chromadb"  # Vector storage

@dataclass
class OrchestrationConfig:
    """Orchestration and routing configuration"""
    max_retries: int = 3
    retry_delay: float = 1.0
    timeout_per_step: int = 60
    max_planning_steps: int = 10
    parallel_execution: bool = True
    fallback_enabled: bool = True

    # Load balancing
    load_balance_strategy: str = "round_robin"  # or "least_loaded", "random"
    health_check_interval: int = 30  # seconds

@dataclass
class KnowledgeConfig:
    """Knowledge and RAG system configuration"""
    chunk_size: int = 512
    chunk_overlap: int = 50
    embedding_batch_size: int = 32
    max_search_results: int = 5
    rerank_enabled: bool = True

    # ChromaDB settings
    chroma_persist_dir: str = str(KNOWLEDGE_DIR / "chromadb")
    collection_prefix: str = "agi_"

@dataclass
class APIConfig:
    """API configuration"""
    host: str = "0.0.0.0"
    port: int = 5024
    base_path: str = "/api/agi"
    cors_origins: List[str] = field(default_factory=lambda: ["*"])
    max_request_size: int = 10 * 1024 * 1024  # 10MB
    rate_limit_per_minute: int = 60

    # WebSocket settings
    ws_ping_interval: int = 30
    ws_ping_timeout: int = 10
    ws_max_connections: int = 100

@dataclass
class MonitoringConfig:
    """Monitoring and metrics configuration"""
    metrics_enabled: bool = True
    metrics_port: int = 9090
    log_level: str = "INFO"
    log_format: str = "json"

    # Performance tracking
    track_latency: bool = True
    track_token_usage: bool = True
    track_errors: bool = True

    # Alerts
    alert_on_error_rate: float = 0.1  # 10% error rate
    alert_on_latency_ms: int = 5000  # 5 seconds

@dataclass
class SecurityConfig:
    """Security configuration"""
    jwt_secret: str = os.getenv('JWT_SECRET', 'change-me-in-production')
    jwt_algorithm: str = "HS256"
    jwt_expiry_hours: int = 24

    # Rate limiting
    rate_limit_enabled: bool = True
    rate_limit_per_ip: int = 100  # per minute

    # Input validation
    max_input_length: int = 10000
    sanitize_inputs: bool = True

    # Multi-tenancy
    tenant_isolation: bool = True
    require_api_key: bool = False  # Set to True in production

@dataclass
class AGIConfig:
    """Main AGI system configuration"""
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)
    models: ModelConfig = field(default_factory=ModelConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    orchestration: OrchestrationConfig = field(default_factory=OrchestrationConfig)
    knowledge: KnowledgeConfig = field(default_factory=KnowledgeConfig)
    api: APIConfig = field(default_factory=APIConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)

    # System settings
    environment: str = os.getenv('AGI_ENV', 'development')
    debug: bool = environment == 'development'
    version: str = "1.0.0"

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            'database': self.database.__dict__,
            'redis': self.redis.__dict__,
            'models': self.models.__dict__,
            'memory': self.memory.__dict__,
            'orchestration': self.orchestration.__dict__,
            'knowledge': self.knowledge.__dict__,
            'api': self.api.__dict__,
            'monitoring': self.monitoring.__dict__,
            'security': self.security.__dict__,
            'environment': self.environment,
            'debug': self.debug,
            'version': self.version,
        }

# Singleton configuration instance
_config: Optional[AGIConfig] = None

def get_config() -> AGIConfig:
    """Get the singleton configuration instance"""
    global _config
    if _config is None:
        _config = AGIConfig()
    return _config

def reset_config():
    """Reset configuration (mainly for testing)"""
    global _config
    _config = None