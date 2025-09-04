"""
Domain Plugin Interface
Abstract base class for all domain-specific plugins
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class TaskType(Enum):
    """Common task types across domains"""
    GREETING = "greeting"
    SEARCH = "search"
    RECOMMENDATION = "recommendation"
    INFORMATION = "information"
    CONSULTATION = "consultation"
    TRANSACTION = "transaction"
    SUPPORT = "support"
    EDUCATION = "education"

@dataclass
class DomainConfig:
    """Configuration for a domain plugin"""
    name: str
    display_name: str
    description: str
    version: str
    author: str
    supported_languages: List[str]
    supported_tasks: List[TaskType]
    requires_auth: bool = False
    data_sources: List[str] = None
    knowledge_bases: List[str] = None

@dataclass
class DomainContext:
    """Context passed to domain plugins"""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    language: str = "en"
    location: Optional[str] = None
    preferences: Dict[str, Any] = None
    history: List[Dict] = None
    metadata: Dict[str, Any] = None

class DomainPlugin(ABC):
    """
    Abstract base class for domain-specific plugins
    Each domain (budtender, doctor, lawyer, etc.) implements this interface
    """
    
    @abstractmethod
    def __init__(self, config_path: str):
        """Initialize the domain plugin with configuration"""
        pass
    
    @abstractmethod
    def get_config(self) -> DomainConfig:
        """Get domain configuration"""
        pass
    
    @abstractmethod
    def get_prompt(self, task: TaskType, **kwargs) -> str:
        """
        Get a prompt template for a specific task
        
        Args:
            task: Type of task
            **kwargs: Variables to inject into prompt
            
        Returns:
            Formatted prompt string
        """
        pass
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get the system prompt that defines the domain's personality and rules"""
        pass
    
    @abstractmethod
    def search_knowledge(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Search domain-specific knowledge base
        
        Args:
            query: Search query
            limit: Maximum results
            
        Returns:
            List of relevant knowledge items
        """
        pass
    
    @abstractmethod
    def validate_input(self, input_text: str, task: TaskType) -> Tuple[bool, Optional[str]]:
        """
        Validate user input for domain-specific rules
        
        Args:
            input_text: User's input
            task: Current task type
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        pass
    
    @abstractmethod
    def validate_response(self, response: str, task: TaskType) -> Tuple[bool, Optional[str]]:
        """
        Validate AI response for domain-specific rules
        
        Args:
            response: AI's response
            task: Current task type
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        pass
    
    @abstractmethod
    def format_response(self, raw_response: str, task: TaskType, context: DomainContext) -> Dict:
        """
        Format raw AI response into domain-specific structure
        
        Args:
            raw_response: Raw text from AI
            task: Current task type
            context: Domain context
            
        Returns:
            Formatted response dictionary
        """
        pass
    
    @abstractmethod
    def get_tools(self) -> List[Dict]:
        """
        Get domain-specific tools/functions the AI can use
        
        Returns:
            List of tool definitions
        """
        pass
    
    @abstractmethod
    def get_data_schema(self) -> Dict:
        """
        Get the data schema mapping for this domain
        
        Returns:
            Schema definition dictionary
        """
        pass
    
    @abstractmethod
    def handle_error(self, error: Exception, task: TaskType, context: DomainContext) -> str:
        """
        Handle domain-specific errors
        
        Args:
            error: The exception that occurred
            task: Current task type
            context: Domain context
            
        Returns:
            User-friendly error message
        """
        pass
    
    @abstractmethod
    def get_fallback_response(self, task: TaskType, context: DomainContext) -> str:
        """
        Get a fallback response when AI fails
        
        Args:
            task: Current task type
            context: Domain context
            
        Returns:
            Fallback response text
        """
        pass
    
    # Optional methods with default implementations
    
    def pre_process(self, input_text: str, context: DomainContext) -> str:
        """Pre-process user input before sending to AI"""
        return input_text
    
    def post_process(self, response: str, context: DomainContext) -> str:
        """Post-process AI response before returning to user"""
        return response
    
    def get_examples(self, task: TaskType) -> List[Dict[str, str]]:
        """Get few-shot examples for a task"""
        return []
    
    def get_constraints(self, task: TaskType) -> List[str]:
        """Get constraints/rules for a task"""
        return []
    
    def should_escalate(self, input_text: str, context: DomainContext) -> bool:
        """Determine if the query should be escalated to a human"""
        return False
    
    def log_interaction(self, input_text: str, response: str, context: DomainContext) -> None:
        """Log the interaction for analytics/training"""
        pass