"""
Secure Configuration Loader
Loads configuration from environment variables with validation
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv
import hashlib
import secrets

logger = logging.getLogger(__name__)

class SecureConfigLoader:
    """
    Secure configuration loader that:
    - Loads from environment variables
    - Validates configuration
    - Masks sensitive values in logs
    - Provides defaults for non-sensitive values
    """
    
    # List of sensitive keys that should never be logged
    SENSITIVE_KEYS = {
        'password', 'secret', 'key', 'token', 'credential',
        'api_key', 'private_key', 'auth', 'jwt'
    }
    
    def __init__(self, env_file: Optional[str] = None):
        """Initialize config loader with optional env file"""
        # Load environment variables
        if env_file and Path(env_file).exists():
            load_dotenv(env_file)
        else:
            # Try to load from default locations
            for env_path in ['.env', '../.env', '../../.env']:
                if Path(env_path).exists():
                    load_dotenv(env_path)
                    break

        self.config = {}
        # Generate consistent secrets once at initialization
        self._jwt_secret = None
        self._api_key_salt = None
        self._load_configuration()
        self._validate_required()
    
    def _load_configuration(self):
        """Load configuration from environment and files"""
        # Load base configuration from JSON
        config_paths = [
            'config/system_config.json',
            '../config/system_config.json',
            'system_config.json'
        ]
        
        base_config = {}
        for path in config_paths:
            if Path(path).exists():
                with open(path, 'r') as f:
                    base_config = json.load(f)
                    break
        
        # Override with environment variables
        self.config = self._override_with_env(base_config)
    
    def _override_with_env(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively override configuration with environment variables
        """
        result = {}
        for key, value in config.items():
            if isinstance(value, dict):
                result[key] = self._override_with_env(value)
            else:
                # Skip environment variable override for certain keys that conflict with system variables
                # Specifically avoid overriding "path" keys with system PATH variable
                if key.lower() in ['path', 'home', 'user', 'shell', 'term']:
                    # Only check for placeholders, not environment variables
                    if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
                        var_name = value[2:-1]
                        result[key] = os.environ.get(var_name, value)
                    else:
                        result[key] = value
                else:
                    # Check for environment variable
                    env_key = self._get_env_key(key)
                    env_value = os.environ.get(env_key)

                    if env_value is not None:
                        # Type conversion based on original value
                        if isinstance(value, bool):
                            result[key] = env_value.lower() in ('true', '1', 'yes')
                        elif isinstance(value, int):
                            try:
                                result[key] = int(env_value)
                            except ValueError:
                                result[key] = value
                        elif isinstance(value, float):
                            try:
                                result[key] = float(env_value)
                            except ValueError:
                                result[key] = value
                        else:
                            result[key] = env_value
                    else:
                        # Check if it's a placeholder like ${VAR_NAME}
                        if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
                            var_name = value[2:-1]
                            result[key] = os.environ.get(var_name, value)
                        else:
                            result[key] = value

        return result
    
    def _get_env_key(self, key: str) -> str:
        """Convert config key to environment variable name"""
        # Convert camelCase or snake_case to UPPER_SNAKE_CASE
        return key.upper().replace('.', '_')
    
    def _validate_required(self):
        """Validate that all required configurations are present"""
        required = {
            'DB_PASSWORD': 'Database password is required',
            'JWT_SECRET': 'JWT secret is required for authentication',
        }
        
        missing = []
        for key, message in required.items():
            if not os.environ.get(key):
                missing.append(f"  - {key}: {message}")
        
        if missing and os.environ.get('ENABLE_AUTH', 'false').lower() == 'true':
            raise ValueError(
                "Missing required environment variables:\n" + "\n".join(missing) +
                "\n\nPlease set these in your .env file or environment"
            )
    
    def get(self, path: str, default: Any = None) -> Any:
        """
        Get configuration value by path (dot notation)
        Example: config.get('api.gateway.base_url')
        """
        keys = path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration with secure defaults"""
        return {
            'host': os.environ.get('DB_HOST', 'localhost'),
            'port': int(os.environ.get('DB_PORT', 5434)),
            'database': os.environ.get('DB_NAME', 'ai_engine'),
            'user': os.environ.get('DB_USER', 'weedgo'),
            'password': os.environ.get('DB_PASSWORD', ''),
            'pool_size': int(os.environ.get('DB_POOL_SIZE', 10)),
            'max_overflow': int(os.environ.get('DB_MAX_OVERFLOW', 20)),
        }
    
    def get_redis_config(self) -> Dict[str, Any]:
        """Get Redis configuration for caching and rate limiting"""
        return {
            'host': os.environ.get('REDIS_HOST', 'localhost'),
            'port': int(os.environ.get('REDIS_PORT', 6379)),
            'password': os.environ.get('REDIS_PASSWORD', None),
            'db': int(os.environ.get('REDIS_DB', 0)),
            'decode_responses': True,
        }
    
    def get_api_gateway_config(self) -> Dict[str, Any]:
        """Get API gateway configuration"""
        return {
            'base_url': os.environ.get('API_GATEWAY_URL', 'http://localhost:8000'),
            'timeout': int(os.environ.get('API_GATEWAY_TIMEOUT', 30)),
            'retry_attempts': int(os.environ.get('API_RETRY_ATTEMPTS', 3)),
            'rate_limit_per_minute': int(os.environ.get('API_RATE_LIMIT', 60)),
        }
    
    def get_security_config(self) -> Dict[str, Any]:
        """Get security configuration"""
        # Use consistent secrets - generate once on first access, then reuse
        if self._jwt_secret is None:
            self._jwt_secret = os.environ.get('JWT_SECRET') or self._generate_secret()
        if self._api_key_salt is None:
            self._api_key_salt = os.environ.get('API_KEY_SALT') or self._generate_secret()

        return {
            'jwt_secret': self._jwt_secret,
            'jwt_algorithm': os.environ.get('JWT_ALGORITHM', 'HS256'),
            'jwt_expiry_hours': int(os.environ.get('JWT_EXPIRY_HOURS', 24)),
            'api_key_salt': self._api_key_salt,
            'enable_auth': os.environ.get('ENABLE_AUTH', 'false').lower() == 'true',
            'enable_rate_limit': os.environ.get('RATE_LIMIT_ENABLED', 'true').lower() == 'true',
            'rate_limit_per_minute': int(os.environ.get('RATE_LIMIT_PER_MINUTE', 60)),
            'rate_limit_burst': int(os.environ.get('RATE_LIMIT_BURST', 10)),
        }
    
    def _generate_secret(self) -> str:
        """Generate a secure random secret"""
        return secrets.token_urlsafe(32)
    
    def mask_sensitive(self, value: Any, key: str = '') -> Any:
        """Mask sensitive values for logging"""
        key_lower = key.lower()
        
        # Check if key contains sensitive words
        for sensitive_word in self.SENSITIVE_KEYS:
            if sensitive_word in key_lower:
                if isinstance(value, str) and value:
                    # Show first 2 and last 2 characters only
                    if len(value) > 4:
                        return f"{value[:2]}...{value[-2:]}"
                    else:
                        return "***"
                return "***"
        
        # Recursively mask nested dictionaries
        if isinstance(value, dict):
            return {k: self.mask_sensitive(v, k) for k, v in value.items()}
        elif isinstance(value, list):
            return [self.mask_sensitive(item) for item in value]
        
        return value
    
    def log_config(self):
        """Log configuration with sensitive values masked"""
        masked_config = self.mask_sensitive(self.config)
        logger.info(f"Configuration loaded: {json.dumps(masked_config, indent=2)}")
    
    def validate_database_connection(self) -> bool:
        """Validate database configuration"""
        db_config = self.get_database_config()
        if not db_config.get('password'):
            logger.error("Database password not configured")
            return False
        return True
    
    def get_feature_flags(self) -> Dict[str, bool]:
        """Get feature flags configuration"""
        return {
            'streaming': os.environ.get('ENABLE_STREAMING', 'true').lower() == 'true',
            'function_schemas': os.environ.get('ENABLE_FUNCTION_SCHEMAS', 'true').lower() == 'true',
            'tool_validation': os.environ.get('ENABLE_TOOL_VALIDATION', 'true').lower() == 'true',
            'result_caching': os.environ.get('ENABLE_RESULT_CACHING', 'true').lower() == 'true',
            'cost_tracking': os.environ.get('ENABLE_COST_TRACKING', 'true').lower() == 'true',
            'observability': os.environ.get('OTEL_ENABLED', 'false').lower() == 'true',
        }

# Global config instance
_config_instance = None

def get_config() -> SecureConfigLoader:
    """Get or create global config instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = SecureConfigLoader()
    return _config_instance

def reload_config():
    """Reload configuration from environment"""
    global _config_instance
    _config_instance = SecureConfigLoader()
    return _config_instance