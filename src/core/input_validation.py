"""
Comprehensive Input Validation System
Prevents XSS, injection attacks, and validates all user input
"""

import re
import html
import urllib.parse
import json
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass
from enum import Enum
from pydantic import BaseModel, Field, validator, model_validator
from fastapi import HTTPException, status
import logging
import hashlib

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom validation error"""
    pass


class InputType(Enum):
    """Types of input to validate"""
    TEXT = "text"
    EMAIL = "email"
    URL = "url"
    JSON = "json"
    SQL = "sql"
    SCRIPT = "script"
    HTML = "html"
    NUMBER = "number"
    ALPHANUMERIC = "alphanumeric"
    PATH = "path"
    COMMAND = "command"


@dataclass
class ValidationRule:
    """Validation rule definition"""
    name: str
    pattern: Optional[str] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    allowed_chars: Optional[str] = None
    forbidden_patterns: Optional[List[str]] = None
    custom_validator: Optional[Callable] = None
    sanitizer: Optional[Callable] = None


class InputValidator:
    """
    Comprehensive input validation with multiple security layers
    """
    
    # Dangerous patterns for different attack types
    DANGEROUS_PATTERNS = {
        'sql_injection': [
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|CREATE|ALTER|EXEC|EXECUTE|SCRIPT|TRUNCATE)\b)",
            r"(--|#|\/\*|\*\/)",
            r"(\bOR\b.*=.*)",
            r"(\bAND\b.*=.*)",
            r"(\'|\"|;|\\x00|\\n|\\r|\\x1a)",
            r"(\bxp_\w+)",
            r"(\bsp_\w+)",
        ],
        'xss': [
            r"(<script[^>]*>.*?</script>)",
            r"(javascript:|data:text/html)",
            r"(\bon\w+\s*=\s*[\"'])",  # More specific: only match HTML event handlers with quotes
            r"(<iframe[^>]*>)",
            r"(<object[^>]*>)",
            r"(<embed[^>]*>)",
            r"(<img[^>]*on\w+[^>]*>)",
            r"(eval\s*\()",
            r"(expression\s*\()",
        ],
        'command_injection': [
            r"([;&|`$])",
            r"(\$\(.*\))",
            r"(`.*`)",
            r"(\|.*)",
            r"(>.*)",
            r"(<.*)",
            r"(\\x00)",
        ],
        'path_traversal': [
            r"(\.\.\/|\.\.\\)",
            r"(\/etc\/passwd)",
            r"(C:\\)",
            r"(\/proc\/)",
            r"(\\x00)",
        ],
        'ldap_injection': [
            r"([()&|!])",
            r"(\*)",
        ],
        'xml_injection': [
            r"(<!DOCTYPE[^>]*>)",
            r"(<!ENTITY[^>]*>)",
            r"(<!\[CDATA\[)",
        ],
    }
    
    # Email validation pattern (RFC 5322)
    EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    # URL validation pattern
    URL_PATTERN = r'^(https?|ftp)://[^\s/$.?#].[^\s]*$'
    
    # Alphanumeric pattern
    ALPHANUMERIC_PATTERN = r'^[a-zA-Z0-9]+$'
    
    # Safe path pattern
    SAFE_PATH_PATTERN = r'^[a-zA-Z0-9_\-./]+$'
    
    def __init__(self):
        """Initialize validator"""
        self.validation_rules = {}
        self._setup_default_rules()
    
    def _setup_default_rules(self):
        """Setup default validation rules"""
        self.validation_rules = {
            'username': ValidationRule(
                name='username',
                pattern=r'^[a-zA-Z0-9_]{3,30}$',
                min_length=3,
                max_length=30
            ),
            'password': ValidationRule(
                name='password',
                min_length=8,
                max_length=128,
                custom_validator=self._validate_password_strength
            ),
            'email': ValidationRule(
                name='email',
                pattern=self.EMAIL_PATTERN,
                max_length=254
            ),
            'message': ValidationRule(
                name='message',
                max_length=1000,
                sanitizer=self._sanitize_text,
                forbidden_patterns=[]  # Chat messages are text-only, not rendered as HTML
            ),
            'chat_message': ValidationRule(
                name='chat_message',
                max_length=1000,
                sanitizer=self._sanitize_chat_text,
                forbidden_patterns=[]  # Chat messages don't need XSS protection
            ),
            'product_name': ValidationRule(
                name='product_name',
                pattern=r'^[a-zA-Z0-9\s\-\.\,\']+$',
                max_length=100
            ),
            'search_query': ValidationRule(
                name='search_query',
                max_length=200,
                sanitizer=self._sanitize_search_query
            ),
        }
    
    def validate(
        self,
        value: Any,
        input_type: InputType,
        rule_name: Optional[str] = None,
        custom_rule: Optional[ValidationRule] = None
    ) -> Any:
        """
        Main validation method
        
        Args:
            value: Value to validate
            input_type: Type of input
            rule_name: Name of predefined rule
            custom_rule: Custom validation rule
        
        Returns:
            Validated and sanitized value
        
        Raises:
            ValidationError: If validation fails
        """
        if value is None:
            return None
        
        # Convert to string for validation
        str_value = str(value)
        
        # Skip dangerous pattern check for chat messages
        if rule_name not in ['chat_message', 'message']:
            # Check for dangerous patterns first
            self._check_dangerous_patterns(str_value, input_type)
        
        # Apply rule-based validation first if provided
        if rule_name and rule_name in self.validation_rules:
            rule = self.validation_rules[rule_name]
            return self._apply_rule(str_value, rule)
        
        if custom_rule:
            return self._apply_rule(str_value, custom_rule)
        
        # Apply specific validation
        if input_type == InputType.EMAIL:
            return self._validate_email(str_value)
        elif input_type == InputType.URL:
            return self._validate_url(str_value)
        elif input_type == InputType.JSON:
            return self._validate_json(str_value)
        elif input_type == InputType.NUMBER:
            return self._validate_number(str_value)
        elif input_type == InputType.ALPHANUMERIC:
            return self._validate_alphanumeric(str_value)
        elif input_type == InputType.PATH:
            return self._validate_path(str_value)
        elif input_type == InputType.HTML:
            return self._sanitize_html(str_value)
        elif input_type == InputType.TEXT:
            return self._sanitize_text(str_value)
        
        # Default sanitization
        return self._sanitize_text(str_value)
    
    def _check_dangerous_patterns(self, value: str, input_type: InputType):
        """Check for dangerous patterns based on input type"""
        patterns_to_check = []
        
        # Select patterns based on input type
        if input_type in [InputType.TEXT, InputType.HTML]:
            patterns_to_check.extend(self.DANGEROUS_PATTERNS['xss'])
        
        if input_type in [InputType.SQL, InputType.TEXT]:
            patterns_to_check.extend(self.DANGEROUS_PATTERNS['sql_injection'])
        
        if input_type == InputType.COMMAND:
            patterns_to_check.extend(self.DANGEROUS_PATTERNS['command_injection'])
        
        if input_type == InputType.PATH:
            patterns_to_check.extend(self.DANGEROUS_PATTERNS['path_traversal'])
        
        # Check patterns
        for pattern in patterns_to_check:
            if re.search(pattern, value, re.IGNORECASE):
                logger.warning(f"Dangerous pattern detected: {pattern} in value")
                raise ValidationError(f"Invalid input: contains forbidden characters or patterns")
    
    def _apply_rule(self, value: str, rule: ValidationRule) -> str:
        """Apply validation rule"""
        # Length validation
        if rule.min_length and len(value) < rule.min_length:
            raise ValidationError(f"Value too short (min {rule.min_length} characters)")
        
        if rule.max_length and len(value) > rule.max_length:
            raise ValidationError(f"Value too long (max {rule.max_length} characters)")
        
        # Pattern validation
        if rule.pattern and not re.match(rule.pattern, value):
            raise ValidationError(f"Value does not match required pattern")
        
        # Forbidden patterns
        if rule.forbidden_patterns:
            for pattern in rule.forbidden_patterns:
                if re.search(pattern, value, re.IGNORECASE):
                    raise ValidationError(f"Value contains forbidden content")
        
        # Custom validator
        if rule.custom_validator:
            if not rule.custom_validator(value):
                raise ValidationError(f"Value failed custom validation")
        
        # Sanitizer
        if rule.sanitizer:
            value = rule.sanitizer(value)
        
        return value
    
    def _validate_email(self, email: str) -> str:
        """Validate email address"""
        if not re.match(self.EMAIL_PATTERN, email):
            raise ValidationError("Invalid email address")
        
        # Additional checks
        if '..' in email:
            raise ValidationError("Invalid email: consecutive dots")
        
        if email.count('@') != 1:
            raise ValidationError("Invalid email: multiple @ symbols")
        
        return email.lower()
    
    def _validate_url(self, url: str) -> str:
        """Validate URL"""
        if not re.match(self.URL_PATTERN, url):
            raise ValidationError("Invalid URL")
        
        # Parse URL for additional validation
        try:
            parsed = urllib.parse.urlparse(url)
            
            # Check for javascript: or data: schemes
            if parsed.scheme in ['javascript', 'data', 'vbscript']:
                raise ValidationError("Invalid URL scheme")
            
            # Check for localhost in production
            if parsed.hostname in ['localhost', '127.0.0.1', '0.0.0.0']:
                logger.warning("Localhost URL detected")
            
            return url
        except Exception as e:
            raise ValidationError(f"Invalid URL: {e}")
    
    def _validate_json(self, json_str: str) -> Dict:
        """Validate JSON string"""
        try:
            data = json.loads(json_str)
            
            # Recursively validate nested data
            self._validate_json_data(data)
            
            return data
        except json.JSONDecodeError as e:
            raise ValidationError(f"Invalid JSON: {e}")
    
    def _validate_json_data(self, data: Any, depth: int = 0):
        """Recursively validate JSON data"""
        MAX_DEPTH = 10
        
        if depth > MAX_DEPTH:
            raise ValidationError("JSON nesting too deep")
        
        if isinstance(data, dict):
            for key, value in data.items():
                # Validate key
                if not isinstance(key, str):
                    raise ValidationError("JSON keys must be strings")
                
                if len(key) > 100:
                    raise ValidationError("JSON key too long")
                
                # Recursively validate value
                self._validate_json_data(value, depth + 1)
        
        elif isinstance(data, list):
            if len(data) > 1000:
                raise ValidationError("JSON array too large")
            
            for item in data:
                self._validate_json_data(item, depth + 1)
        
        elif isinstance(data, str):
            if len(data) > 10000:
                raise ValidationError("JSON string value too long")
    
    def _validate_number(self, value: str) -> Union[int, float]:
        """Validate number"""
        try:
            # Try integer first
            if '.' not in value:
                return int(value)
            else:
                return float(value)
        except ValueError:
            raise ValidationError("Invalid number")
    
    def _validate_alphanumeric(self, value: str) -> str:
        """Validate alphanumeric string"""
        if not re.match(self.ALPHANUMERIC_PATTERN, value):
            raise ValidationError("Value must be alphanumeric")
        return value
    
    def _validate_path(self, path: str) -> str:
        """Validate file path"""
        # Check for path traversal
        if '..' in path or path.startswith('/etc/') or path.startswith('C:\\'):
            raise ValidationError("Invalid path: potential path traversal")
        
        # Check for null bytes
        if '\x00' in path:
            raise ValidationError("Invalid path: contains null bytes")
        
        # Check pattern
        if not re.match(self.SAFE_PATH_PATTERN, path):
            raise ValidationError("Invalid path: contains forbidden characters")
        
        return path
    
    def _validate_password_strength(self, password: str) -> bool:
        """Validate password strength"""
        if len(password) < 8:
            return False
        
        # Check for at least one of each
        has_upper = bool(re.search(r'[A-Z]', password))
        has_lower = bool(re.search(r'[a-z]', password))
        has_digit = bool(re.search(r'\d', password))
        has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))
        
        # Require at least 3 out of 4
        strength = sum([has_upper, has_lower, has_digit, has_special])
        return strength >= 3
    
    def _sanitize_text(self, text: str) -> str:
        """Sanitize plain text"""
        # Remove null bytes
        text = text.replace('\x00', '')
        
        # HTML encode special characters
        text = html.escape(text)
        
        # Limit consecutive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove control characters
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
        
        return text.strip()
    
    def _sanitize_chat_text(self, text: str) -> str:
        """Sanitize chat text - minimal sanitization for conversational messages"""
        # Remove null bytes
        text = text.replace('\x00', '')
        
        # Limit consecutive whitespace but preserve single spaces
        text = re.sub(r'\s{3,}', '  ', text)  # Replace 3+ spaces with 2
        text = re.sub(r'\n{3,}', '\n\n', text)  # Replace 3+ newlines with 2
        
        # Remove control characters except newline, return, tab
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
        
        # Don't HTML escape - this is plain text chat, not HTML
        # Preserve apostrophes, quotes, question marks for natural conversation
        
        return text.strip()
    
    def _sanitize_html(self, html_str: str) -> str:
        """Sanitize HTML (remove dangerous tags)"""
        # Remove script tags
        html_str = re.sub(r'<script[^>]*>.*?</script>', '', html_str, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove style tags
        html_str = re.sub(r'<style[^>]*>.*?</style>', '', html_str, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove on* attributes
        html_str = re.sub(r'\s*on\w+\s*=\s*["\'][^"\']*["\']', '', html_str, flags=re.IGNORECASE)
        
        # Remove javascript: and data: URLs
        html_str = re.sub(r'(javascript|data):[^"\'\s]*', '', html_str, flags=re.IGNORECASE)
        
        return html_str
    
    def _sanitize_search_query(self, query: str) -> str:
        """Sanitize search query"""
        # Remove SQL operators
        sql_operators = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DROP', 'UNION', 'OR', 'AND']
        for op in sql_operators:
            query = re.sub(r'\b' + op + r'\b', '', query, flags=re.IGNORECASE)
        
        # Remove special characters except spaces and basic punctuation
        query = re.sub(r'[^a-zA-Z0-9\s\-\.\,]', '', query)
        
        # Limit length
        return query[:200].strip()


# Pydantic models for request validation
class ChatRequestModel(BaseModel):
    """Validated chat request model"""
    message: str = Field(..., min_length=1, max_length=1000)
    session_id: str = Field(..., pattern='^[a-zA-Z0-9_-]{1,64}$')
    agent_id: Optional[str] = Field(None, pattern='^[a-zA-Z0-9_-]{1,32}$')
    
    @validator('message')
    def validate_message(cls, v):
        validator = InputValidator()
        try:
            # Use chat_message rule for conversational text
            return validator.validate(v, InputType.TEXT, 'chat_message')
        except ValidationError as e:
            raise ValueError(str(e))
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Show me indica strains under $50",
                "session_id": "abc123",
                "agent_id": "dispensary"
            }
        }


class ProductSearchModel(BaseModel):
    """Validated product search model"""
    query: Optional[str] = Field(None, max_length=200)
    category: Optional[str] = Field(None, pattern='^[a-zA-Z]+$')
    min_price: Optional[float] = Field(None, ge=0, le=10000)
    max_price: Optional[float] = Field(None, ge=0, le=10000)
    strain_type: Optional[str] = Field(None, pattern='^(indica|sativa|hybrid)$')
    limit: Optional[int] = Field(10, ge=1, le=100)
    
    @validator('query')
    def validate_query(cls, v):
        if v:
            validator = InputValidator()
            try:
                return validator.validate(v, InputType.TEXT, 'search_query')
            except ValidationError as e:
                raise ValueError(str(e))
        return v
    
    @model_validator(mode='after')
    def validate_price_range(self):
        if self.min_price and self.max_price and self.min_price > self.max_price:
            raise ValueError('min_price must be less than max_price')
        return self


class OrderCreateModel(BaseModel):
    """Validated order creation model"""
    items: List[Dict[str, Any]]
    delivery_address: Optional[str] = Field(None, max_length=500)
    payment_method: str = Field(..., pattern='^(cash|debit|credit)$')
    notes: Optional[str] = Field(None, max_length=500)
    
    @validator('items')
    def validate_items(cls, v):
        if not v:
            raise ValueError('Order must contain at least one item')
        
        if len(v) > 50:
            raise ValueError('Too many items in order')
        
        for item in v:
            if 'product_id' not in item or 'quantity' not in item:
                raise ValueError('Each item must have product_id and quantity')
            
            if not isinstance(item['quantity'], int) or item['quantity'] < 1:
                raise ValueError('Quantity must be a positive integer')
        
        return v
    
    @validator('delivery_address')
    def validate_address(cls, v):
        if v:
            validator = InputValidator()
            try:
                return validator.validate(v, InputType.TEXT)
            except ValidationError as e:
                raise ValueError(str(e))
        return v


# Global validator instance
_validator_instance = None

def get_validator() -> InputValidator:
    """Get or create global validator instance"""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = InputValidator()
    return _validator_instance