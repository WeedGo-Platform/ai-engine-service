"""
Domain Manager
Manages loading, switching, and lifecycle of domain plugins
"""
import os
import sys
import importlib
import logging
from pathlib import Path
from typing import Dict, Optional, List, Any
import yaml
import json

from core.interfaces.domain_plugin import DomainPlugin, DomainConfig, DomainContext, TaskType
from core.interfaces.data_adapter import DataAdapter, DataAdapterFactory

# Import and register the PostgreSQL adapter
try:
    from data.adapters.postgresql import PostgreSQLAdapter
    DataAdapterFactory.register('postgresql', PostgreSQLAdapter)
except ImportError:
    # Try alternative location
    try:
        from core.adapters.postgresql_adapter import PostgreSQLAdapter
        DataAdapterFactory.register('postgresql', PostgreSQLAdapter)
    except ImportError:
        pass

logger = logging.getLogger(__name__)

class DomainManager:
    """
    Manages domain plugins and provides a unified interface
    """
    
    def __init__(self, domains_path: str = "domains", config_path: str = "config/domains.yaml"):
        self.domains_path = Path(domains_path)
        self.config_path = Path(config_path)
        self.domains: Dict[str, DomainPlugin] = {}
        self.active_domain: Optional[str] = None
        self.data_adapters: Dict[str, DataAdapter] = {}
        self._load_config()
        
    def _load_config(self):
        """Load domain configuration"""
        if self.config_path.exists():
            with open(self.config_path) as f:
                self.config = yaml.safe_load(f)
        else:
            self.config = {
                "enabled_domains": [],
                "default_domain": None,
                "auto_discover": True
            }
    
    async def initialize(self):
        """Initialize the domain manager"""
        logger.info("Initializing Domain Manager...")
        
        # Auto-discover domains if enabled
        if self.config.get("auto_discover", True):
            await self.discover_domains()
        
        # Load enabled domains
        for domain_name in self.config.get("enabled_domains", []):
            await self.load_domain(domain_name)
        
        # Set default domain
        default = self.config.get("default_domain")
        if default and default in self.domains:
            self.active_domain = default
            logger.info(f"Set default domain: {default}")
        
        logger.info(f"Initialized with {len(self.domains)} domains")
    
    async def discover_domains(self) -> List[str]:
        """
        Discover available domain plugins
        
        Returns:
            List of discovered domain names
        """
        discovered = []
        
        if not self.domains_path.exists():
            logger.warning(f"Domains path does not exist: {self.domains_path}")
            return discovered
        
        for domain_dir in self.domains_path.iterdir():
            if not domain_dir.is_dir() or domain_dir.name.startswith('_'):
                continue
            
            plugin_file = domain_dir / "plugin.py"
            config_file = domain_dir / "config.yaml"
            
            if plugin_file.exists() and config_file.exists():
                discovered.append(domain_dir.name)
                logger.info(f"Discovered domain: {domain_dir.name}")
        
        return discovered
    
    async def load_domain(self, domain_name: str) -> bool:
        """
        Load a domain plugin
        
        Args:
            domain_name: Name of the domain to load
            
        Returns:
            Success status
        """
        try:
            domain_path = self.domains_path / domain_name
            
            if not domain_path.exists():
                logger.error(f"Domain path not found: {domain_path}")
                return False
            
            # Add domain path to Python path
            if str(domain_path) not in sys.path:
                sys.path.insert(0, str(domain_path))
            
            # Import the plugin module
            module = importlib.import_module(f"domains.{domain_name}.plugin")
            
            # Find the plugin class (should be named XxxPlugin)
            plugin_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    issubclass(attr, DomainPlugin) and 
                    attr != DomainPlugin):
                    plugin_class = attr
                    break
            
            if not plugin_class:
                logger.error(f"No DomainPlugin class found in {domain_name}")
                return False
            
            # Instantiate the plugin
            config_path = str(domain_path / "config.yaml")
            plugin = plugin_class(config_path)
            
            # Load data adapter if specified
            config = plugin.get_config()
            if config.data_sources:
                await self._load_data_adapters(domain_name, config.data_sources)
            
            # Register the domain
            self.domains[domain_name] = plugin
            logger.info(f"Loaded domain: {domain_name} ({config.display_name})")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to load domain {domain_name}: {e}")
            return False
    
    async def _load_data_adapters(self, domain_name: str, data_sources: List[str]):
        """Load data adapters for a domain"""
        for source in data_sources:
            if source not in self.data_adapters:
                try:
                    # Load adapter configuration
                    adapter_config = self.config.get("data_adapters", {}).get(source, {})
                    adapter_type = adapter_config.get("type", "postgresql")
                    
                    # Create adapter
                    adapter = DataAdapterFactory.create(adapter_type, adapter_config)
                    await adapter.connect()
                    
                    self.data_adapters[source] = adapter
                    logger.info(f"Loaded data adapter: {source} for domain {domain_name}")
                except Exception as e:
                    logger.warning(f"Could not load data adapter {source}: {e}")
                    # Continue without the adapter - domain can still work without database
    
    def switch_domain(self, domain_name: str) -> bool:
        """
        Switch to a different domain
        
        Args:
            domain_name: Name of domain to switch to
            
        Returns:
            Success status
        """
        if domain_name not in self.domains:
            logger.error(f"Domain not loaded: {domain_name}")
            return False
        
        self.active_domain = domain_name
        logger.info(f"Switched to domain: {domain_name}")
        return True
    
    def get_active_domain(self) -> Optional[DomainPlugin]:
        """Get the currently active domain plugin"""
        if self.active_domain:
            return self.domains.get(self.active_domain)
        return None
    
    def get_domain(self, domain_name: str) -> Optional[DomainPlugin]:
        """Get a specific domain plugin"""
        return self.domains.get(domain_name)
    
    def list_domains(self) -> List[DomainConfig]:
        """List all loaded domains"""
        return [domain.get_config() for domain in self.domains.values()]
    
    def get_domain_capabilities(self, domain_name: str = None) -> Dict:
        """Get capabilities of a domain"""
        domain = self.get_domain(domain_name) if domain_name else self.get_active_domain()
        
        if not domain:
            return {}
        
        config = domain.get_config()
        tools = domain.get_tools()
        
        return {
            "name": config.name,
            "display_name": config.display_name,
            "supported_tasks": [task.value for task in config.supported_tasks],
            "supported_languages": config.supported_languages,
            "tools": [tool.get("name") for tool in tools],
            "requires_auth": config.requires_auth
        }
    
    async def process_request(
        self,
        input_text: str,
        task: TaskType,
        context: DomainContext = None,
        domain_name: str = None
    ) -> Dict[str, Any]:
        """
        Process a request using the appropriate domain
        
        Args:
            input_text: User input
            task: Task type
            context: Domain context
            domain_name: Specific domain to use (or active domain)
            
        Returns:
            Processed response
        """
        # Get the domain to use
        domain = self.get_domain(domain_name) if domain_name else self.get_active_domain()
        
        if not domain:
            return {
                "error": "No domain available",
                "message": "Please select a domain first"
            }
        
        # Create context if not provided
        if context is None:
            context = DomainContext()
        
        try:
            # Validate input
            is_valid, error = domain.validate_input(input_text, task)
            if not is_valid:
                return {
                    "error": "Invalid input",
                    "message": error
                }
            
            # Pre-process input
            processed_input = domain.pre_process(input_text, context)
            
            # Get prompt
            prompt = domain.get_prompt(task, input=processed_input, context=context)
            
            # This is where we would call the AI model
            # For now, returning a placeholder
            raw_response = f"[AI Response for {task.value} in {domain.get_config().name}]"
            
            # Validate response
            is_valid, error = domain.validate_response(raw_response, task)
            if not is_valid:
                raw_response = domain.get_fallback_response(task, context)
            
            # Post-process response
            processed_response = domain.post_process(raw_response, context)
            
            # Format response
            formatted = domain.format_response(processed_response, task, context)
            
            # Log interaction
            domain.log_interaction(input_text, processed_response, context)
            
            return formatted
            
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            error_message = domain.handle_error(e, task, context)
            return {
                "error": "Processing failed",
                "message": error_message
            }
    
    async def search_knowledge(
        self,
        query: str,
        domain_name: str = None,
        limit: int = 10
    ) -> List[Dict]:
        """
        Search knowledge base of a domain
        
        Args:
            query: Search query
            domain_name: Specific domain (or active domain)
            limit: Maximum results
            
        Returns:
            Search results
        """
        domain = self.get_domain(domain_name) if domain_name else self.get_active_domain()
        
        if not domain:
            return []
        
        return domain.search_knowledge(query, limit)
    
    def get_data_adapter(self, adapter_name: str) -> Optional[DataAdapter]:
        """Get a data adapter by name"""
        return self.data_adapters.get(adapter_name)
    
    async def cleanup(self):
        """Clean up resources"""
        # Disconnect data adapters
        for adapter in self.data_adapters.values():
            await adapter.disconnect()
        
        logger.info("Domain Manager cleaned up")