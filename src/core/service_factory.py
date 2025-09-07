"""
Service Factory and Dependency Injection Container
Implements IServiceFactory interface following SOLID principles
Creates and manages service instances with proper dependency injection
"""

import logging
from typing import Dict, Any, Optional
from pathlib import Path

# Import interfaces
from core.interfaces import (
    IServiceFactory,
    IModelManager,
    IPromptManager,
    IIntentDetector,
    IContextManager,
    IGenerationEngine,
    IToolManager,
    IConfigurationService,
    ISafetyService,
    IAgentManager,
    IBenchmarkService
)

# Import implementations
from services.model_manager import ModelManager
from services.prompt_manager import PromptManager
from services.context_manager import ContextManager, MemoryContextStore
from services.generation_engine import GenerationEngine

# Import intent detector with fallback
try:
    from services.intent_detector import LLMIntentDetector, PatternIntentDetector
    INTENT_DETECTOR_AVAILABLE = True
except ImportError:
    INTENT_DETECTOR_AVAILABLE = False

logger = logging.getLogger(__name__)


class ServiceContainer:
    """
    Dependency Injection Container
    Manages service instances and their lifecycles
    """
    
    def __init__(self):
        """Initialize the service container"""
        self._services = {}
        self._singletons = {}
        self._factories = {}
        
        logger.info("ServiceContainer initialized")
    
    def register_singleton(self, interface_name: str, instance: Any):
        """
        Register a singleton service instance
        
        Args:
            interface_name: Name of the interface
            instance: Service instance
        """
        self._singletons[interface_name] = instance
        logger.debug(f"Registered singleton: {interface_name}")
    
    def register_factory(self, interface_name: str, factory_func: callable):
        """
        Register a factory function for creating service instances
        
        Args:
            interface_name: Name of the interface
            factory_func: Factory function that creates instances
        """
        self._factories[interface_name] = factory_func
        logger.debug(f"Registered factory: {interface_name}")
    
    def get(self, interface_name: str) -> Any:
        """
        Get a service instance
        
        Args:
            interface_name: Name of the interface
            
        Returns:
            Service instance
        """
        # Check singletons first
        if interface_name in self._singletons:
            return self._singletons[interface_name]
        
        # Check if we have a factory
        if interface_name in self._factories:
            instance = self._factories[interface_name]()
            # Store as singleton for future use
            self._singletons[interface_name] = instance
            return instance
        
        # Check regular services
        if interface_name in self._services:
            return self._services[interface_name]
        
        raise ValueError(f"Service not registered: {interface_name}")
    
    def has(self, interface_name: str) -> bool:
        """
        Check if a service is registered
        
        Args:
            interface_name: Name of the interface
            
        Returns:
            True if registered
        """
        return (interface_name in self._singletons or 
                interface_name in self._factories or 
                interface_name in self._services)
    
    def clear(self):
        """Clear all registered services"""
        self._services.clear()
        self._singletons.clear()
        self._factories.clear()
        logger.info("Service container cleared")


class ServiceFactory(IServiceFactory):
    """
    Service Factory implementation
    Creates service instances with proper dependency injection
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Service Factory
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.container = ServiceContainer()
        
        # Register factories for lazy initialization
        self._register_default_factories()
        
        logger.info("ServiceFactory initialized")
    
    def _register_default_factories(self):
        """Register default factory functions"""
        self.container.register_factory('IModelManager', self.create_model_manager)
        self.container.register_factory('IPromptManager', self.create_prompt_manager)
        self.container.register_factory('IIntentDetector', self.create_intent_detector)
        self.container.register_factory('IContextManager', self.create_context_manager)
        self.container.register_factory('IGenerationEngine', 
                                       lambda: self.create_generation_engine(
                                           self.container.get('IModelManager')))
    
    def create_model_manager(self) -> IModelManager:
        """
        Create model manager instance
        
        Returns:
            IModelManager implementation
        """
        model_paths = self.config.get('model_paths', None)
        return ModelManager(model_paths)
    
    def create_prompt_manager(self) -> IPromptManager:
        """
        Create prompt manager instance
        
        Returns:
            IPromptManager implementation
        """
        return PromptManager()
    
    def create_intent_detector(self) -> IIntentDetector:
        """
        Create intent detector instance
        
        Returns:
            IIntentDetector implementation
        """
        if not INTENT_DETECTOR_AVAILABLE:
            logger.warning("Intent detector not available, returning None")
            return None
        
        detector_type = self.config.get('intent_detector_type', 'llm')
        
        if detector_type == 'pattern':
            return PatternIntentDetector()
        else:
            # LLM detector needs reference to V5 engine
            # This will be set later when engine is initialized
            return LLMIntentDetector(v5_engine=None)
    
    def create_context_manager(self) -> IContextManager:
        """
        Create context manager instance
        
        Returns:
            IContextManager implementation
        """
        context_config = self.config.get('context', {})
        
        # Create appropriate storage backend
        storage_type = context_config.get('storage_type', 'memory')
        
        if storage_type == 'memory':
            max_entries = context_config.get('max_entries_per_session', 100)
            store = MemoryContextStore(max_entries)
        else:
            # Default to memory store
            store = MemoryContextStore()
        
        return ContextManager(store, context_config)
    
    def create_generation_engine(self, model_manager: IModelManager) -> IGenerationEngine:
        """
        Create generation engine instance
        
        Args:
            model_manager: Model manager instance
            
        Returns:
            IGenerationEngine implementation
        """
        return GenerationEngine(model_manager)
    
    def create_tool_manager(self) -> IToolManager:
        """
        Create tool manager instance
        
        Returns:
            IToolManager implementation (placeholder)
        """
        # Tool manager would be implemented separately
        # For now, return None as it's optional
        logger.debug("Tool manager not implemented yet")
        return None
    
    def create_configuration_service(self) -> IConfigurationService:
        """
        Create configuration service instance
        
        Returns:
            IConfigurationService implementation (placeholder)
        """
        # Configuration service would be implemented separately
        logger.debug("Configuration service not implemented yet")
        return None
    
    def create_safety_service(self) -> ISafetyService:
        """
        Create safety service instance
        
        Returns:
            ISafetyService implementation (placeholder)
        """
        # Safety service would be implemented separately
        logger.debug("Safety service not implemented yet")
        return None
    
    def create_agent_manager(self) -> IAgentManager:
        """
        Create agent manager instance
        
        Returns:
            IAgentManager implementation (placeholder)
        """
        # Agent manager would be implemented separately
        logger.debug("Agent manager not implemented yet")
        return None
    
    def create_benchmark_service(self) -> IBenchmarkService:
        """
        Create benchmark service instance
        
        Returns:
            IBenchmarkService implementation (placeholder)
        """
        # Benchmark service would be implemented separately
        logger.debug("Benchmark service not implemented yet")
        return None
    
    def get_container(self) -> ServiceContainer:
        """
        Get the service container
        
        Returns:
            ServiceContainer instance
        """
        return self.container
    
    def create_all_services(self) -> Dict[str, Any]:
        """
        Create all core services
        
        Returns:
            Dictionary of service instances
        """
        services = {}
        
        # Create core services
        services['model_manager'] = self.container.get('IModelManager')
        services['prompt_manager'] = self.container.get('IPromptManager')
        services['context_manager'] = self.container.get('IContextManager')
        services['generation_engine'] = self.container.get('IGenerationEngine')
        
        # Optional services
        if self.container.has('IIntentDetector'):
            services['intent_detector'] = self.container.get('IIntentDetector')
        
        logger.info(f"Created {len(services)} core services")
        
        return services