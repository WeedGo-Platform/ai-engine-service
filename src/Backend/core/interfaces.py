"""
Core interfaces for the AI Engine Service following SOLID principles.
Each interface represents a single responsibility.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path


# Model Management Interface (SRP: Model lifecycle management)
class IModelManager(ABC):
    """Interface for model management operations"""
    
    @abstractmethod
    def load_model(self, model_name: str, base_folder: Optional[str] = None) -> bool:
        """Load a specific model"""
        pass
    
    @abstractmethod
    def unload_model(self) -> None:
        """Unload the current model"""
        pass
    
    @abstractmethod
    def list_models(self) -> List[Dict[str, Any]]:
        """List available models"""
        pass
    
    @abstractmethod
    def get_current_model(self) -> Optional[Any]:
        """Get the currently loaded model"""
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model"""
        pass


# Prompt Management Interface (SRP: Prompt template management)
class IPromptManager(ABC):
    """Interface for prompt template management"""
    
    @abstractmethod
    def load_prompts(self, prompt_folder: str) -> bool:
        """Load prompts from a folder"""
        pass
    
    @abstractmethod
    def get_prompt_template(self, prompt_type: str) -> Optional[Dict]:
        """Get a specific prompt template"""
        pass
    
    @abstractmethod
    def apply_prompt_template(self, user_input: str, prompt_type: str) -> str:
        """Apply a prompt template to user input"""
        pass
    
    @abstractmethod
    def list_loaded_prompts(self) -> Dict[str, List[str]]:
        """List all loaded prompts"""
        pass


# Intent Detection Interface (SRP: Intent classification)
class IIntentDetector(ABC):
    """Interface for intent detection"""
    
    @abstractmethod
    def detect(self, message: str, language: str = "auto") -> Dict[str, Any]:
        """Detect intent from a message"""
        pass
    
    @abstractmethod
    def load_intents(self, agent_id: str) -> bool:
        """Load intent configuration for an agent"""
        pass
    
    @abstractmethod
    def clear_cache(self) -> None:
        """Clear any cached results"""
        pass


# Context Management Interface (SRP: Session and context management)
class IContextManager(ABC):
    """Interface for context and session management"""
    
    @abstractmethod
    def get_context(self, session_id: str) -> Dict[str, Any]:
        """Get context for a session"""
        pass
    
    @abstractmethod
    def update_context(self, session_id: str, context: Dict[str, Any]) -> None:
        """Update context for a session"""
        pass
    
    @abstractmethod
    def add_to_history(self, session_id: str, user_message: Dict, assistant_message: Dict) -> None:
        """Add messages to conversation history"""
        pass
    
    @abstractmethod
    def get_history(self, session_id: str, limit: int = 10) -> List[Dict]:
        """Get conversation history"""
        pass
    
    @abstractmethod
    def clear_context(self, session_id: str) -> None:
        """Clear context for a session"""
        pass


# Generation Interface (SRP: Text generation)
class IGenerationEngine(ABC):
    """Interface for text generation"""
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate text from a prompt"""
        pass
    
    @abstractmethod
    def stream_generate(self, prompt: str, **kwargs):
        """Stream generation for real-time output"""
        pass


# Tool Management Interface (SRP: Tool execution)
class IToolManager(ABC):
    """Interface for tool management and execution"""
    
    @abstractmethod
    def register_tool(self, tool_name: str, tool_function: callable) -> bool:
        """Register a new tool"""
        pass
    
    @abstractmethod
    def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Execute a tool with given parameters"""
        pass
    
    @abstractmethod
    def list_tools(self) -> List[str]:
        """List available tools"""
        pass
    
    @abstractmethod
    def extract_tool_calls(self, response: str) -> List[Dict]:
        """Extract tool calls from a response"""
        pass


# Configuration Interface (SRP: Configuration management)
class IConfigurationService(ABC):
    """Interface for configuration management"""
    
    @abstractmethod
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get a configuration value"""
        pass
    
    @abstractmethod
    def set_config(self, key: str, value: Any) -> None:
        """Set a configuration value"""
        pass
    
    @abstractmethod
    def load_config(self, config_path: str) -> bool:
        """Load configuration from file"""
        pass
    
    @abstractmethod
    def get_model_config(self) -> Dict[str, Any]:
        """Get model-specific configuration"""
        pass


# Safety Interface (SRP: Content safety and moderation)
class ISafetyService(ABC):
    """Interface for safety and content moderation"""
    
    @abstractmethod
    def apply_safety_guidelines(self, prompt: str, response: str) -> str:
        """Apply safety guidelines to a response"""
        pass
    
    @abstractmethod
    def check_content_safety(self, content: str) -> Dict[str, Any]:
        """Check content for safety violations"""
        pass
    
    @abstractmethod
    def get_system_instruction(self) -> str:
        """Get system safety instructions"""
        pass


# Agent Management Interface (SRP: Agent configuration)
class IAgentManager(ABC):
    """Interface for agent management"""
    
    @abstractmethod
    def load_agent(self, agent_id: str) -> bool:
        """Load an agent configuration"""
        pass
    
    @abstractmethod
    def get_agent_config(self) -> Dict[str, Any]:
        """Get current agent configuration"""
        pass
    
    @abstractmethod
    def list_agents(self) -> List[Dict[str, Any]]:
        """List available agents"""
        pass
    
    @abstractmethod
    def load_personality(self, personality_id: str) -> bool:
        """Load an agent personality"""
        pass
    
    @abstractmethod
    def list_personalities(self) -> List[Dict[str, Any]]:
        """List available personalities"""
        pass


# Benchmarking Interface (SRP: Performance measurement)
class IBenchmarkService(ABC):
    """Interface for benchmarking and performance measurement"""
    
    @abstractmethod
    def benchmark_model(self, model_name: str, test_prompts: List[str]) -> Dict[str, Any]:
        """Benchmark a model"""
        pass
    
    @abstractmethod
    def compare_configurations(self, config1: Dict, config2: Dict) -> Dict[str, Any]:
        """Compare two configurations"""
        pass
    
    @abstractmethod
    def get_resource_usage(self) -> Dict[str, Any]:
        """Get current resource usage"""
        pass


# Main Engine Interface (Facade pattern - coordinates all services)
class IAIEngine(ABC):
    """Main AI Engine interface that coordinates all services"""
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the engine with configuration"""
        pass
    
    @abstractmethod
    def process_message(self, message: str, session_id: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Process a user message and return response"""
        pass
    
    @abstractmethod
    def stream_response(self, message: str, session_id: Optional[str] = None, **kwargs):
        """Stream response for real-time output"""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Cleanup resources"""
        pass
    
    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """Get engine status"""
        pass


# Factory Interface (Factory pattern for creating services)
class IServiceFactory(ABC):
    """Interface for creating service instances"""
    
    @abstractmethod
    def create_model_manager(self) -> IModelManager:
        """Create model manager instance"""
        pass
    
    @abstractmethod
    def create_prompt_manager(self) -> IPromptManager:
        """Create prompt manager instance"""
        pass
    
    @abstractmethod
    def create_intent_detector(self) -> IIntentDetector:
        """Create intent detector instance"""
        pass
    
    @abstractmethod
    def create_context_manager(self) -> IContextManager:
        """Create context manager instance"""
        pass
    
    @abstractmethod
    def create_generation_engine(self, model_manager: IModelManager) -> IGenerationEngine:
        """Create generation engine instance"""
        pass
    
    @abstractmethod
    def create_tool_manager(self) -> IToolManager:
        """Create tool manager instance"""
        pass
    
    @abstractmethod
    def create_configuration_service(self) -> IConfigurationService:
        """Create configuration service instance"""
        pass
    
    @abstractmethod
    def create_safety_service(self) -> ISafetyService:
        """Create safety service instance"""
        pass
    
    @abstractmethod
    def create_agent_manager(self) -> IAgentManager:
        """Create agent manager instance"""
        pass
    
    @abstractmethod
    def create_benchmark_service(self) -> IBenchmarkService:
        """Create benchmark service instance"""
        pass


# Database Tool Interface (SRP: Database search operations)
class IDatabaseSearchTool(ABC):
    """Interface for database search tool"""
    
    @abstractmethod
    def connect(self, connection_params: Dict[str, Any]) -> bool:
        """Establish database connection"""
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Close database connection"""
        pass
    
    @abstractmethod
    def search(self, query_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute search query with parameters"""
        pass
    
    @abstractmethod
    def search_products(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search for products with specific filters"""
        pass
    
    @abstractmethod
    def search_by_category(self, category: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search products by category"""
        pass
    
    @abstractmethod
    def search_by_effects(self, effects: List[str], limit: int = 10) -> List[Dict[str, Any]]:
        """Search products by effects"""
        pass
    
    @abstractmethod
    def get_product_details(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific product"""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if database is connected"""
        pass


# Database Connection Manager Interface (SRP: Connection lifecycle)  
class IDatabaseConnectionManager(ABC):
    """Interface for database connection management"""
    
    @abstractmethod
    def get_connection(self, connection_name: str = "default") -> Any:
        """Get a database connection by name"""
        pass
    
    @abstractmethod
    def create_connection(self, connection_name: str, config: Dict[str, Any]) -> bool:
        """Create a new database connection"""
        pass
    
    @abstractmethod
    def close_connection(self, connection_name: str) -> None:
        """Close a specific connection"""
        pass
    
    @abstractmethod
    def close_all_connections(self) -> None:
        """Close all connections"""
        pass
    
    @abstractmethod
    def get_connection_status(self, connection_name: str) -> Dict[str, Any]:
        """Get status of a specific connection"""
        pass
    
    @abstractmethod
    def list_connections(self) -> List[str]:
        """List all active connections"""
        pass