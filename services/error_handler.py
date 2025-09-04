#!/usr/bin/env python3
"""
Comprehensive Error Handling and Fallback System
Ensures service resilience and graceful degradation
"""

import logging
import traceback
from typing import Dict, Optional, Any, Callable
from enum import Enum
from datetime import datetime
import json
from functools import wraps
import asyncio

logger = logging.getLogger(__name__)

class ErrorCategory(Enum):
    """Categories of errors for proper handling"""
    DATABASE = "database_error"
    MODEL = "model_error"
    COMPLIANCE = "compliance_error"
    VALIDATION = "validation_error"
    EXTERNAL_SERVICE = "external_service_error"
    RATE_LIMIT = "rate_limit_error"
    AUTHENTICATION = "authentication_error"
    BUSINESS_LOGIC = "business_logic_error"
    UNKNOWN = "unknown_error"

class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"        # Log only
    MEDIUM = "medium"  # Use fallback
    HIGH = "high"      # Alert and fallback
    CRITICAL = "critical"  # Service degradation

class ServiceError(Exception):
    """Base exception for service errors"""
    def __init__(self, message: str, category: ErrorCategory, 
                 severity: ErrorSeverity, details: Optional[Dict] = None):
        self.message = message
        self.category = category
        self.severity = severity
        self.details = details or {}
        self.timestamp = datetime.now()
        super().__init__(self.message)

class ErrorHandler:
    """
    Centralized error handling with fallback mechanisms
    """
    
    def __init__(self):
        self.error_counts = {}  # Track error frequencies
        self.circuit_breakers = {}  # Circuit breaker states
        self.fallback_responses = self._initialize_fallbacks()
        
    def _initialize_fallbacks(self) -> Dict:
        """Initialize fallback responses for different scenarios"""
        return {
            'chat_greeting': {
                'message': "Welcome to WeedGo! I'm here to help you find the perfect cannabis products. How can I assist you today?",
                'products': [],
                'quick_replies': [
                    "Help with sleep",
                    "Pain relief",
                    "First time user",
                    "Browse products"
                ],
                'confidence': 1.0,
                'stage': 'greeting'
            },
            'product_search_generic': [
                {
                    'id': 0,
                    'product_name': 'Popular Indica Strain',
                    'brand': 'Premium Brand',
                    'unit_price': 45.99,
                    'category': 'Flower',
                    'pitch': 'Our most popular strain for relaxation'
                },
                {
                    'id': 0,
                    'product_name': 'Balanced Hybrid',
                    'brand': 'Quality Cannabis',
                    'unit_price': 39.99,
                    'category': 'Flower',
                    'pitch': 'Perfect balance of effects'
                }
            ],
            'compliance_check': {
                'status': 'pending',
                'message': 'Compliance check temporarily unavailable. Please try again shortly.',
                'allow_proceed': False
            },
            'llm_unavailable': "I understand you're looking for cannabis products. While I process your request, you might be interested in our popular categories: Flower for traditional effects, Edibles for long-lasting relief, or Vapes for convenience. What interests you most?"
        }
    
    def handle_error(self, error: Exception, context: Dict[str, Any]) -> Dict:
        """
        Main error handling method
        Returns appropriate fallback response
        """
        # Categorize error
        category = self._categorize_error(error)
        severity = self._determine_severity(category, error)
        
        # Log error with context
        self._log_error(error, category, severity, context)
        
        # Track error frequency
        self._track_error(category)
        
        # Check circuit breaker
        if self._should_circuit_break(category):
            return self._get_circuit_breaker_response(category, context)
        
        # Get fallback response
        fallback = self._get_fallback_response(category, context)
        
        # Alert if necessary
        if severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            self._send_alert(error, category, severity, context)
        
        return fallback
    
    def _categorize_error(self, error: Exception) -> ErrorCategory:
        """Categorize error based on type and message"""
        error_str = str(error).lower()
        error_type = type(error).__name__
        
        # Database errors
        if 'psycopg2' in error_type or 'database' in error_str or 'connection' in error_str:
            return ErrorCategory.DATABASE
        
        # Model errors
        if 'model' in error_str or 'llm' in error_str or 'inference' in error_str:
            return ErrorCategory.MODEL
        
        # Compliance errors
        if 'compliance' in error_str or 'age' in error_str or 'verification' in error_str:
            return ErrorCategory.COMPLIANCE
        
        # Validation errors
        if 'validation' in error_str or 'invalid' in error_str or 'required' in error_str:
            return ErrorCategory.VALIDATION
        
        # Rate limiting
        if 'rate' in error_str or 'limit' in error_str or 'too many' in error_str:
            return ErrorCategory.RATE_LIMIT
        
        # Authentication
        if 'auth' in error_str or 'token' in error_str or 'permission' in error_str:
            return ErrorCategory.AUTHENTICATION
        
        return ErrorCategory.UNKNOWN
    
    def _determine_severity(self, category: ErrorCategory, error: Exception) -> ErrorSeverity:
        """Determine error severity"""
        # Critical errors
        if category == ErrorCategory.DATABASE:
            return ErrorSeverity.CRITICAL
        
        # High severity
        if category in [ErrorCategory.COMPLIANCE, ErrorCategory.AUTHENTICATION]:
            return ErrorSeverity.HIGH
        
        # Medium severity
        if category in [ErrorCategory.MODEL, ErrorCategory.EXTERNAL_SERVICE]:
            return ErrorSeverity.MEDIUM
        
        # Low severity
        if category in [ErrorCategory.VALIDATION, ErrorCategory.RATE_LIMIT]:
            return ErrorSeverity.LOW
        
        return ErrorSeverity.MEDIUM
    
    def _log_error(self, error: Exception, category: ErrorCategory, 
                   severity: ErrorSeverity, context: Dict):
        """Log error with appropriate level"""
        error_info = {
            'category': category.value,
            'severity': severity.value,
            'error_type': type(error).__name__,
            'message': str(error),
            'context': context,
            'traceback': traceback.format_exc()
        }
        
        if severity == ErrorSeverity.CRITICAL:
            logger.critical(f"Critical error: {json.dumps(error_info)}")
        elif severity == ErrorSeverity.HIGH:
            logger.error(f"High severity error: {json.dumps(error_info)}")
        elif severity == ErrorSeverity.MEDIUM:
            logger.warning(f"Medium severity error: {json.dumps(error_info)}")
        else:
            logger.info(f"Low severity error: {json.dumps(error_info)}")
    
    def _track_error(self, category: ErrorCategory):
        """Track error frequency for circuit breaking"""
        key = category.value
        if key not in self.error_counts:
            self.error_counts[key] = []
        
        self.error_counts[key].append(datetime.now())
        
        # Clean old entries (keep last 5 minutes)
        cutoff = datetime.now().timestamp() - 300
        self.error_counts[key] = [
            t for t in self.error_counts[key] 
            if t.timestamp() > cutoff
        ]
    
    def _should_circuit_break(self, category: ErrorCategory) -> bool:
        """Check if circuit breaker should activate"""
        key = category.value
        
        # Check if already broken
        if key in self.circuit_breakers:
            if self.circuit_breakers[key]['until'] > datetime.now():
                return True
            else:
                # Circuit breaker expired
                del self.circuit_breakers[key]
        
        # Check error frequency (>10 errors in 1 minute)
        if key in self.error_counts:
            recent_errors = len(self.error_counts[key])
            if recent_errors > 10:
                # Activate circuit breaker
                self.circuit_breakers[key] = {
                    'until': datetime.now().timestamp() + 60,  # 1 minute
                    'reason': f"{recent_errors} errors in last minute"
                }
                logger.warning(f"Circuit breaker activated for {key}")
                return True
        
        return False
    
    def _get_circuit_breaker_response(self, category: ErrorCategory, context: Dict) -> Dict:
        """Get response when circuit breaker is active"""
        if category == ErrorCategory.DATABASE:
            return {
                'error': True,
                'message': "Service temporarily unavailable. Please try again in a moment.",
                'fallback': True
            }
        
        # For other categories, return cached/fallback data
        return self._get_fallback_response(category, context)
    
    def _get_fallback_response(self, category: ErrorCategory, context: Dict) -> Dict:
        """Get appropriate fallback response"""
        endpoint = context.get('endpoint', '')
        
        if 'chat' in endpoint:
            # Determine conversation stage for appropriate fallback
            stage = context.get('stage', 'greeting')
            if stage == 'greeting':
                return self.fallback_responses['chat_greeting']
            else:
                return {
                    'message': self.fallback_responses['llm_unavailable'],
                    'products': [],
                    'confidence': 0.5,
                    'fallback': True
                }
        
        elif 'search' in endpoint or 'product' in endpoint:
            return self.fallback_responses['product_search_generic']
        
        elif 'compliance' in endpoint or 'verify' in endpoint:
            return self.fallback_responses['compliance_check']
        
        # Generic fallback
        return {
            'error': True,
            'message': "We're experiencing technical difficulties. Please try again.",
            'fallback': True
        }
    
    def _send_alert(self, error: Exception, category: ErrorCategory, 
                    severity: ErrorSeverity, context: Dict):
        """Send alerts for high severity errors"""
        # In production, this would send to monitoring service
        alert = {
            'timestamp': datetime.now().isoformat(),
            'severity': severity.value,
            'category': category.value,
            'error': str(error),
            'context': context
        }
        
        logger.critical(f"ALERT: {json.dumps(alert)}")
        
        # Would integrate with PagerDuty, Slack, etc.
    
    def get_health_status(self) -> Dict:
        """Get error handler health status"""
        return {
            'error_counts': {
                k: len(v) for k, v in self.error_counts.items()
            },
            'circuit_breakers': {
                k: {
                    'active': True,
                    'until': datetime.fromtimestamp(v['until']).isoformat(),
                    'reason': v['reason']
                }
                for k, v in self.circuit_breakers.items()
            },
            'status': 'healthy' if not self.circuit_breakers else 'degraded'
        }

# Decorator for automatic error handling
def with_error_handling(fallback_response=None):
    """
    Decorator to add error handling to async functions
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                # Get error handler instance (would be injected in production)
                handler = ErrorHandler()
                
                # Create context
                context = {
                    'function': func.__name__,
                    'args': str(args)[:100],  # Truncate for logging
                    'kwargs': str(kwargs)[:100]
                }
                
                # Handle error
                fallback = handler.handle_error(e, context)
                
                # Return fallback or raise
                if fallback_response:
                    return fallback_response
                return fallback
        
        return wrapper
    return decorator

# Retry decorator with exponential backoff
def retry_with_backoff(max_retries: int = 3, initial_delay: float = 1.0):
    """
    Decorator to retry failed operations with exponential backoff
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                        await asyncio.sleep(delay)
                        delay *= 2  # Exponential backoff
                    else:
                        logger.error(f"All {max_retries} attempts failed")
            
            raise last_exception
        
        return wrapper
    return decorator

# Example usage
class ResilientService:
    """Example of using error handling in a service"""
    
    def __init__(self):
        self.error_handler = ErrorHandler()
    
    @with_error_handling(fallback_response={'message': 'Fallback response'})
    @retry_with_backoff(max_retries=3)
    async def risky_operation(self):
        """Operation that might fail"""
        # Simulate potential failure
        import random
        if random.random() < 0.5:
            raise Exception("Random failure")
        return {'message': 'Success!'}
    
    async def safe_database_query(self, query: str):
        """Database query with fallback to cache"""
        try:
            # Attempt database query
            result = await self._execute_query(query)
            return result
        except Exception as e:
            # Use error handler
            context = {'endpoint': 'database', 'query': query}
            return self.error_handler.handle_error(e, context)
    
    async def _execute_query(self, query: str):
        """Simulate database query"""
        raise Exception("Database connection failed")

# Testing
async def test_error_handling():
    """Test error handling system"""
    handler = ErrorHandler()
    service = ResilientService()
    
    # Test different error categories
    errors = [
        Exception("Database connection failed"),
        Exception("Model inference timeout"),
        Exception("Age verification failed"),
        Exception("Rate limit exceeded"),
    ]
    
    for error in errors:
        context = {'endpoint': '/api/test', 'user': 'test_user'}
        response = handler.handle_error(error, context)
        print(f"Error: {error}")
        print(f"Response: {response}\n")
    
    # Test retry mechanism
    result = await service.risky_operation()
    print(f"Risky operation result: {result}")
    
    # Test health status
    health = handler.get_health_status()
    print(f"Health status: {health}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_error_handling())