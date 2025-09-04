"""
Smart AI Engine V5 with Tools and Context Persistence
Advanced AI engine with tool calling capabilities and conversation memory
Supports modular agents with custom tools and context storage
"""

import os
import time
import json
import logging
import psutil
import multiprocessing
import gc
import re
import uuid
import asyncio
from pathlib import Path
from typing import Dict, Optional, List, Any, Tuple
from llama_cpp import Llama

# Import tool and context interfaces
try:
    from services.tools.base import ToolManager, ITool, ToolResult
    from services.tools.dispensary_tools import DispensarySearchTool, DosageCalculatorTool, StrainComparisonTool
    from services.tools.dispensary_tools_db import DispensarySearchToolDB, DispensaryStatsToolDB
    from services.context.base import ContextManager, MemoryContextStore, DatabaseContextStore, IContextStore
    TOOLS_AVAILABLE = True
except ImportError:
    TOOLS_AVAILABLE = False
    logging.warning("Tool and context modules not available")

logger = logging.getLogger(__name__)

class SmartAIEngineV5:
    _instance = None
    
    def __new__(cls):
        """Singleton pattern to ensure only one engine instance"""
        if cls._instance is None:
            cls._instance = super(SmartAIEngineV5, cls).__new__(cls)
        return cls._instance
    
    """
    Smart AI Engine V5 with advanced capabilities:
    - Tool calling for function execution
    - Context persistence across conversations
    - Modular agent system with custom tools
    """
    
    def __init__(self):
        self.current_model = None
        self.current_model_name = None
        self.available_models = self._scan_models()
        self.loaded_prompts = {}
        self.base_prompts = {}
        self.role_prompts = {}
        self.personality_prompts = {}
        self.prompt_folder = None
        self.role_folder = None
        self.personality_folder = None
        self.use_prompts = False
        self.current_personality = None
        
        # New modular architecture support
        self.current_agent = None
        self.current_personality_type = None
        self.agent_prompts = {}
        self.personality_traits = {}
        self.system_config = self._load_system_config()
        
        # Initialize tools and context systems
        self.tool_manager = None
        self.context_manager = None
        self.session_id = None
        self._initialize_tools_and_context()
        
        logger.info(f"SmartAIEngineV5 initialized with {len(self.available_models)} models")
        self._log_system_resources()
    
    def _log_system_resources(self):
        """Log current system resource availability"""
        try:
            cpu_count = multiprocessing.cpu_count()
            memory = psutil.virtual_memory()
            logger.info(f"System Resources:")
            logger.info(f"  - CPUs: {cpu_count}")
            logger.info(f"  - Memory: {memory.total / (1024**3):.1f} GB total, {memory.available / (1024**3):.1f} GB available")
            logger.info(f"  - Memory used: {memory.percent}%")
        except Exception as e:
            logger.warning(f"Could not get system resources: {e}")
    
    def _initialize_tools_and_context(self):
        """Initialize tool manager and context storage based on config"""
        if not TOOLS_AVAILABLE:
            logger.warning("Tools and context modules not available, skipping initialization")
            return
            
        try:
            # Initialize tools if enabled in config
            if self.system_config and self.system_config.get('system', {}).get('tools', {}).get('enabled'):
                self.tool_manager = ToolManager()
                
                # Load agent-specific tools if configured
                if self.current_agent:
                    self._load_agent_tools(self.current_agent)
                    
                logger.info(f"Tool manager initialized with {len(self.tool_manager.list_tools())} tools")
            
            # Initialize context storage if enabled
            if self.system_config and self.system_config.get('system', {}).get('context', {}).get('enabled'):
                context_config = self.system_config['system']['context']
                storage_type = context_config.get('storage_type', 'memory')
                
                if storage_type == 'memory':
                    max_entries = context_config.get('memory_config', {}).get('max_entries_per_session', 100)
                    store = MemoryContextStore(max_entries)
                elif storage_type == 'database':
                    conn_string = context_config.get('database_config', {}).get('connection_string')
                    store = DatabaseContextStore(conn_string)
                    # Note: Would need to await store.initialize() in async context
                else:
                    store = MemoryContextStore()
                
                self.context_manager = ContextManager(store, context_config.get('settings', {}))
                self.session_id = str(uuid.uuid4())
                logger.info(f"Context manager initialized with {storage_type} storage")
                
        except Exception as e:
            logger.error(f"Failed to initialize tools/context: {e}")
    
    def _load_agent_tools(self, agent_id: str):
        """Load tools specific to an agent"""
        if not self.tool_manager or not self.system_config:
            return
            
        try:
            # Get agent-specific tools from config
            agent_tools = self.system_config.get('system', {}).get('tools', {}).get('agent_tools', {}).get(agent_id, [])
            
            # Check if database tools should be used
            use_db_tools = self.system_config.get('system', {}).get('tools', {}).get('use_database', True)
            db_config = self.system_config.get('system', {}).get('context', {}).get('database_config', {})
            
            # Load dispensary-specific tools
            if agent_id == 'dispensary':
                if 'dispensary_search' in agent_tools:
                    if use_db_tools and db_config:
                        # Use database-connected search tool
                        self.tool_manager.register_tool(DispensarySearchToolDB(db_config))
                        logger.info("Loaded database-connected DispensarySearchTool")
                    else:
                        # Use mock search tool
                        self.tool_manager.register_tool(DispensarySearchTool())
                        logger.info("Loaded mock DispensarySearchTool")
                
                if 'dosage_calculator' in agent_tools:
                    self.tool_manager.register_tool(DosageCalculatorTool())
                
                if 'compare_strains' in agent_tools:
                    self.tool_manager.register_tool(StrainComparisonTool())
                
                if 'product_stats' in agent_tools and use_db_tools and db_config:
                    self.tool_manager.register_tool(DispensaryStatsToolDB(db_config))
                    logger.info("Loaded database-connected StatsToolDB")
                
            logger.info(f"Loaded {len(self.tool_manager.list_tools())} tools for agent '{agent_id}'")
        except Exception as e:
            logger.error(f"Failed to load agent tools: {e}")
    
    def get_resource_usage(self) -> Dict[str, Any]:
        """Get current resource usage"""
        try:
            memory = psutil.virtual_memory()
            process = psutil.Process()
            return {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": memory.percent,
                "memory_available_gb": memory.available / (1024**3),
                "process_memory_mb": process.memory_info().rss / (1024**2),
                "model_loaded": self.current_model_name is not None
            }
        except:
            return {}
    
    def _scan_models(self) -> Dict[str, str]:
        """Scan all available model files"""
        models = {}
        base_path = Path("models")
        
        # Scan all subdirectories for .gguf files
        for model_file in base_path.rglob("*.gguf"):
            # Skip empty files (0 bytes = not downloaded)
            if model_file.stat().st_size == 0:
                logger.info(f"Skipping empty model file: {model_file}")
                continue
                
            # Get relative path from models directory
            rel_path = model_file.relative_to(base_path)
            # Create a simple name from the filename
            model_name = model_file.stem.replace('.Q4_K_M', '').replace('-', '_').lower()
            # Store full path
            models[model_name] = str(model_file)
            
        logger.info(f"Found {len(models)} downloaded models: {list(models.keys())}")
        return models
    
    def _load_system_config(self) -> Dict:
        """Load system configuration for modular architecture"""
        try:
            config_path = Path("prompts/system/config.json")
            if config_path.exists():
                with open(config_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load system config: {e}")
        return {}
    
    def load_agent_personality(self, agent_id: str = None, personality_id: str = None) -> bool:
        """Load agent and personality combination for modular system"""
        try:
            # Reset current configuration
            self.agent_prompts = {}
            self.personality_traits = {}
            self.current_agent = agent_id
            self.current_personality_type = personality_id
            
            # Load agent prompts
            if agent_id:
                agent_path = Path(f"prompts/agents/{agent_id}/prompts.json")
                if agent_path.exists():
                    with open(agent_path, 'r') as f:
                        agent_data = json.load(f)
                        self.agent_prompts = agent_data.get('prompts', {})
                        logger.info(f"Loaded agent '{agent_id}' with {len(self.agent_prompts)} prompts")
            
            # Load personality traits
            if personality_id:
                personality_path = Path(f"prompts/personality/{personality_id}/traits.json")
                if personality_path.exists():
                    with open(personality_path, 'r') as f:
                        personality_data = json.load(f)
                        self.personality_traits = personality_data.get('personality', {})
                        logger.info(f"Loaded personality '{personality_id}' - {self.personality_traits.get('name')}")
            
            self.use_prompts = bool(self.agent_prompts or self.personality_traits)
            return True
            
        except Exception as e:
            logger.error(f"Failed to load agent/personality: {e}")
            return False
    
    def load_prompts(self, prompt_folder: str = None, role_folder: str = None, personality_file: str = None) -> Dict[str, Dict]:
        """Load prompts from base, role, and personality layers"""
        self.loaded_prompts = {}
        self.base_prompts = {}
        self.role_prompts = {}
        self.personality_prompts = {}
        
        # Load base prompts (or system configuration)
        if prompt_folder:
            self.prompt_folder = prompt_folder
            prompt_path = Path(prompt_folder)
            if prompt_path.exists():
                # Special handling for system folder
                if prompt_folder == "prompts/system":
                    config_file = prompt_path / "config.json"
                    if config_file.exists():
                        with open(config_file, 'r') as f:
                            config_data = json.load(f)
                            # Apply system configuration
                            if 'system' in config_data:
                                self.system_config = config_data
                                system_cfg = config_data['system']
                                # Apply default behavior settings if available
                                if 'default_behavior' in system_cfg:
                                    defaults = system_cfg['default_behavior']
                                    # These can be used to override temperature, etc.
                                    logger.info(f"Applied system configuration: {defaults.get('response_style', 'default')} style")
                                # Apply safety guidelines
                                if 'safety_guidelines' in system_cfg and system_cfg['safety_guidelines'].get('enabled'):
                                    logger.info(f"Safety guidelines enabled with {len(system_cfg['safety_guidelines'].get('rules', []))} rules")
                        logger.info(f"Loaded system configuration from {config_file.name}")
                else:
                    # Normal prompt loading for non-system folders
                    for json_file in prompt_path.glob("*.json"):
                        # Skip config.json in any folder
                        if json_file.stem == "config":
                            continue
                        try:
                            with open(json_file, 'r') as f:
                                prompts = json.load(f)
                                file_name = json_file.stem
                                self.base_prompts[file_name] = prompts
                                logger.info(f"Loaded {len(prompts)} base prompts from {json_file.name}")
                        except Exception as e:
                            logger.error(f"Failed to load prompts from {json_file}: {e}")
        
        # Load role/agent prompts
        if role_folder:
            self.role_folder = role_folder
            role_path = Path(role_folder)
            if role_path.exists():
                for json_file in role_path.glob("*.json"):
                    try:
                        with open(json_file, 'r') as f:
                            data = json.load(f)
                            file_name = json_file.stem
                            
                            # Check if this is an agent prompt file with nested structure
                            if 'prompts' in data and isinstance(data['prompts'], dict):
                                # Extract the prompts from the nested structure
                                self.role_prompts[file_name] = data['prompts']
                                # Also set agent_prompts for compatibility
                                self.agent_prompts = data['prompts']
                                logger.info(f"Loaded {len(data['prompts'])} agent prompts from {json_file.name}")
                            else:
                                # Regular prompt file structure
                                self.role_prompts[file_name] = data
                                logger.info(f"Loaded role prompts from {json_file.name}")
                    except Exception as e:
                        logger.error(f"Failed to load role prompts from {json_file}: {e}")
        
        # Load personality
        if personality_file:
            self.personality_folder = personality_file
            personality_path = Path(personality_file)
            if personality_path.exists():
                try:
                    with open(personality_path, 'r') as f:
                        personality_data = json.load(f)
                        if 'personality' in personality_data:
                            self.current_personality = personality_data['personality']
                            self.personality_prompts = personality_data
                            # Set personality traits for template replacement
                            self.personality_traits = personality_data['personality']
                            logger.info(f"Loaded personality: {self.current_personality.get('name', 'Unknown')}")
                except Exception as e:
                    logger.error(f"Failed to load personality from {personality_file}: {e}")
        
        # Merge all prompts (base takes priority, then role, then personality)
        self.loaded_prompts = {**self.personality_prompts, **self.role_prompts, **self.base_prompts}
        
        # Set use_prompts flag - True if we have prompts OR system config
        self.use_prompts = len(self.loaded_prompts) > 0 or bool(self.system_config) or bool(self.role_prompts) or bool(self.base_prompts)
        
        total_prompts = sum(len(p) if isinstance(p, dict) else 1 for p in self.loaded_prompts.values())
        if self.system_config:
            logger.info(f"System configuration loaded, prompts enabled")
        logger.info(f"Loaded total {total_prompts} prompts from all sources")
        return self.loaded_prompts
    
    def get_prompt_template(self, prompt_type: str) -> Optional[Dict]:
        """Get a specific prompt template by type"""
        if not self.use_prompts:
            return None
        
        # Search through all loaded prompt files
        for file_prompts in self.loaded_prompts.values():
            if prompt_type in file_prompts:
                return file_prompts[prompt_type]
        
        return None
    
    def apply_agent_template(self, user_input: str, prompt_type: str) -> str:
        """Apply agent-based prompt template with personality modifiers"""
        if not self.agent_prompts or prompt_type not in self.agent_prompts:
            return self.apply_prompt_template(user_input, prompt_type)
        
        template_data = self.agent_prompts[prompt_type]
        template_str = template_data.get('template', '')
        
        if not template_str:
            return user_input
        
        # Check if this should be used as a system message
        use_system_format = template_data.get('system_format', False)
        
        # Replace personality variables - also check self.current_personality for backward compatibility
        personality_data = self.personality_traits or self.current_personality
        
        if personality_data:
            personality_name = personality_data.get('name', 'Assistant')
            logger.info(f"Replacing {{personality_name}} with '{personality_name}'")
            template_str = template_str.replace('{personality_name}', personality_name)
            
            # Format traits as a descriptive string
            traits_dict = personality_data.get('traits', {})
            if traits_dict and isinstance(traits_dict, dict):
                # Create a readable traits description
                traits_desc = f"who is {traits_dict.get('communication_style', 'friendly')} and {traits_dict.get('sales_approach', 'helpful')}"
                template_str = template_str.replace('{personality_traits}', traits_desc)
            else:
                template_str = template_str.replace('{personality_traits}', '')
        else:
            # Default replacements when no personality loaded
            logger.warning("No personality data loaded, using default 'Assistant'")
            template_str = template_str.replace('{personality_name}', 'Assistant')
            template_str = template_str.replace('{personality_traits}', '')
        
        # Replace other common variables with defaults
        variables = template_data.get('variables', [])
        for var in variables:
            if var == 'message':
                # Don't replace message in system format
                if not use_system_format:
                    template_str = template_str.replace('{message}', user_input)
            elif var == 'effects':
                template_str = template_str.replace('{effects}', 'relaxation')
            elif var == 'budget':
                template_str = template_str.replace('{budget}', '50')
            elif var == 'experience':
                template_str = template_str.replace('{experience}', 'intermediate')
            else:
                template_str = template_str.replace(f'{{{var}}}', '')
        
        # If system format, create a system-user prompt structure
        if use_system_format:
            return f"System: {template_str}\n\nUser: {user_input}\nAssistant:"
        
        return template_str
    
    def apply_prompt_template_with_config(self, user_input: str, prompt_type: str) -> tuple:
        """Apply prompt template and return both result and config"""
        # First check if we're using agent templates
        if self.agent_prompts and prompt_type in self.agent_prompts:
            template_result = self.apply_agent_template(user_input, prompt_type)
            template = self.agent_prompts[prompt_type]
        else:
            template_result = self.apply_prompt_template(user_input, prompt_type)
            template = self.get_prompt_template(prompt_type)
        
        # Get template config with better defaults
        if template:
            # Extract max_tokens from template or constraints
            max_tokens = template.get('max_tokens')
            if not max_tokens and 'constraints' in template:
                max_tokens = template['constraints'].get('max_words', 30) * 2  # Rough conversion
            
            # Get stop sequences from template, constraints, or use defaults
            stop_sequences = template.get('stop_sequences', [])
            if not stop_sequences and 'constraints' in template:
                stop_sequences = template['constraints'].get('stop_sequences', [])
            if not stop_sequences:
                # Default stop sequences for cannabis dispensary context
                stop_sequences = ["\nCustomer:", "\nBudtender:", "\n\n", "\\n4.", "\\n\\n"]
            
            config = {
                'max_tokens': max_tokens or 50,  # Default to 50 if not specified
                'stop_sequences': stop_sequences
            }
        else:
            config = {'max_tokens': 50, 'stop_sequences': []}
            
        return template_result, config
    
    def apply_prompt_template(self, user_input: str, prompt_type: str) -> str:
        """Apply a prompt template to user input (legacy support)"""
        # Try agent-based templates first
        if self.agent_prompts and prompt_type in self.agent_prompts:
            return self.apply_agent_template(user_input, prompt_type)
        
        if not self.use_prompts:
            return user_input
        
        template = self.get_prompt_template(prompt_type)
        if not template:
            logger.info(f"No template found for {prompt_type}, using raw input")
            return user_input
        
        # Get the template string
        template_str = template.get('template', '')
        if not template_str:
            return user_input
        
        # Check if this should be used as a system message
        use_system_format = template.get('system_format', False)
        
        # Replace variables in template
        variables = template.get('variables', [])
        formatted_prompt = template_str
        
        # Common variable replacements
        if 'message' in variables:
            formatted_prompt = formatted_prompt.replace('{message}', user_input)
        if 'query' in variables:
            formatted_prompt = formatted_prompt.replace('{query}', user_input)
        if 'input' in variables:
            formatted_prompt = formatted_prompt.replace('{input}', user_input)
        if 'text' in variables:
            formatted_prompt = formatted_prompt.replace('{text}', user_input)
        
        # Replace personality placeholder if exists
        if 'personality' in variables:
            if self.current_personality:
                # Use loaded personality data
                personality_str = f"You are {self.current_personality.get('name', 'a budtender')}, {self.current_personality.get('description', 'a helpful cannabis budtender')}. "
                if self.current_personality.get('traits'):
                    traits = self.current_personality['traits']
                    personality_str += f"You are {traits.get('age', '')} years old with {traits.get('communication_style', 'friendly')} communication style. "
                    personality_str += f"Your approach is {traits.get('sales_approach', 'helpful')} and {traits.get('formality', 'professional')}."
                formatted_prompt = formatted_prompt.replace('{personality}', personality_str)
            else:
                formatted_prompt = formatted_prompt.replace('{personality}', 
                    "You are a helpful cannabis budtender assistant. Be friendly and knowledgeable about cannabis products.")
        
        # Replace other common placeholders with defaults
        if 'conversation_text' in variables:
            formatted_prompt = formatted_prompt.replace('{conversation_text}', '')
        if 'customer_context' in variables:
            formatted_prompt = formatted_prompt.replace('{customer_context}', '')
        if 'customer_profile' in variables:
            formatted_prompt = formatted_prompt.replace('{customer_profile}', 'General customer')
        if 'available_products' in variables:
            formatted_prompt = formatted_prompt.replace('{available_products}', 'Various cannabis products')
        if 'product_data' in variables:
            formatted_prompt = formatted_prompt.replace('{product_data}', 'Product information')
        if 'products_shown' in variables:
            formatted_prompt = formatted_prompt.replace('{products_shown}', 'No products shown yet')
        
        # If system format, create a system-user prompt structure
        if use_system_format:
            formatted_prompt = f"System: {formatted_prompt}\n\nUser: {user_input}\nAssistant:"
        
        logger.info(f"Applied template '{prompt_type}' to user input")
        return formatted_prompt
    
    def list_models(self) -> List[Dict[str, Any]]:
        """List all available models with info"""
        model_list = []
        for name, path in self.available_models.items():
            # Get file size
            try:
                size_bytes = os.path.getsize(path)
                # Skip empty files
                if size_bytes == 0:
                    continue
                    
                size_gb = size_bytes / (1024**3)  # Size in GB
                model_list.append({
                    "name": name,
                    "path": path,
                    "size_gb": round(size_gb, 2),
                    "loaded": name == self.current_model_name,
                    "prompts_loaded": self.use_prompts,
                    "prompt_folder": self.prompt_folder
                })
            except:
                continue
        
        # Sort by size
        model_list.sort(key=lambda x: x['size_gb'])
        return model_list
    
    def list_loaded_prompts(self) -> Dict[str, List[str]]:
        """List all loaded prompt templates"""
        result = {}
        for file_name, prompts in self.loaded_prompts.items():
            result[file_name] = list(prompts.keys())
        return result
    
    def list_available_agents(self) -> List[Dict[str, Any]]:
        """List all available agents from the modular system"""
        agents = []
        agents_path = Path("prompts/agents")
        if agents_path.exists():
            for agent_dir in agents_path.iterdir():
                if agent_dir.is_dir():
                    prompts_file = agent_dir / "prompts.json"
                    if prompts_file.exists():
                        try:
                            with open(prompts_file, 'r') as f:
                                agent_data = json.load(f)
                                agent_info = agent_data.get('agent', {})
                                agents.append({
                                    "id": agent_info.get('id', agent_dir.name),
                                    "name": agent_info.get('name', agent_dir.name),
                                    "loaded": self.current_agent == agent_info.get('id')
                                })
                        except:
                            continue
        
        # Add agents from system config if available
        if self.system_config and 'system' in self.system_config:
            for agent in self.system_config['system'].get('agents', []):
                if not any(a['id'] == agent['id'] for a in agents):
                    agent['loaded'] = self.current_agent == agent['id']
                    agents.append(agent)
        
        return agents
    
    def list_available_personalities(self) -> List[Dict[str, Any]]:
        """List all available personalities from the modular system"""
        personalities = []
        personality_path = Path("prompts/personality")
        if personality_path.exists():
            for pers_dir in personality_path.iterdir():
                if pers_dir.is_dir():
                    traits_file = pers_dir / "traits.json"
                    if traits_file.exists():
                        try:
                            with open(traits_file, 'r') as f:
                                pers_data = json.load(f)
                                pers_info = pers_data.get('personality', {})
                                personalities.append({
                                    "id": pers_info.get('id', pers_dir.name),
                                    "name": pers_info.get('name', pers_dir.name),
                                    "emoji": pers_info.get('emoji', ''),
                                    "loaded": self.current_personality_type == pers_info.get('id')
                                })
                        except:
                            continue
        
        # Add personalities from system config if available
        if self.system_config and 'system' in self.system_config:
            for pers in self.system_config['system'].get('personalities', []):
                if not any(p['id'] == pers['id'] for p in personalities):
                    pers['loaded'] = self.current_personality_type == pers['id']
                    personalities.append(pers)
        
        return personalities
    
    def load_model(self, model_name: str, base_folder: Optional[str] = None, 
                   role_folder: Optional[str] = None, personality_file: Optional[str] = None,
                   agent_id: Optional[str] = None, personality_id: Optional[str] = None) -> bool:
        """Load a specific model with optional multi-layer prompts or agent/personality"""
        if model_name not in self.available_models:
            logger.error(f"Model {model_name} not found")
            return False
        
        # Check if using new modular system
        if agent_id is not None or personality_id is not None:
            self.load_agent_personality(agent_id, personality_id)
        # Load prompts if specified (legacy support)
        elif base_folder is not None or role_folder is not None or personality_file is not None:
            self.load_prompts(base_folder, role_folder, personality_file)
        else:
            # Clear prompts if none specified
            self.loaded_prompts = {}
            self.base_prompts = {}
            self.role_prompts = {}
            self.personality_prompts = {}
            self.current_personality = None
            self.use_prompts = False
        
        if self.current_model_name == model_name and not any([base_folder, role_folder, personality_file]):
            logger.info(f"Model {model_name} already loaded")
            return True
        
        try:
            # Unload current model with aggressive cleanup
            if self.current_model:
                logger.info(f"Unloading {self.current_model_name}")
                try:
                    # Try to explicitly free the model's memory if available
                    if hasattr(self.current_model, '__del__'):
                        self.current_model.__del__()
                except:
                    pass
                
                del self.current_model
                self.current_model = None
                self.current_model_name = None
                
                # Aggressive garbage collection
                import gc
                gc.collect(2)  # Full collection
                gc.collect(1)
                gc.collect(0)
                
                # Give OS time to reclaim memory
                time.sleep(1.0)
            
            # Load new model
            model_path = self.available_models[model_name]
            logger.info(f"Loading {model_name} from {model_path}")
            if self.use_prompts:
                logger.info(f"With prompts from: {self.prompt_folder}")
            else:
                logger.info("Without prompts (raw model)")
            
            # Determine optimal parameters based on model size and available CPU
            import multiprocessing
            cpu_count = multiprocessing.cpu_count()
            file_size_gb = os.path.getsize(model_path) / (1024**3)
            
            # Get max context from system config if available
            config_max_ctx = self.get_config_max_context() if hasattr(self, 'get_config_max_context') else 4096
            
            # Use more aggressive resource allocation
            if file_size_gb < 1:  # Small models (< 1GB)
                n_ctx = min(config_max_ctx, 4096)  # Use config or default
                n_threads = min(cpu_count - 1, 16)  # Use almost all CPUs
                n_batch = 1024  # Larger batch for faster processing
                n_gpu_layers = 0
            elif file_size_gb < 5:  # Medium models (1-5GB)
                n_ctx = min(config_max_ctx, 8192)  # Use config or higher limit
                n_threads = min(cpu_count - 2, 12)  # Still use most CPUs
                n_batch = 512
                n_gpu_layers = 0
            else:  # Large models (> 5GB)
                n_ctx = min(config_max_ctx, 8192)  # Use config or maximum
                n_threads = min(cpu_count - 2, 8)  # Balance threads
                n_batch = 256
                n_gpu_layers = 0
            
            logger.info(f"Allocating {n_threads} threads (of {cpu_count} available) for {model_name}")
            logger.info(f"Context size: {n_ctx}, Batch size: {n_batch}")
            
            self.current_model = Llama(
                model_path=model_path,
                n_ctx=n_ctx,
                n_threads=n_threads,
                n_batch=n_batch,
                n_gpu_layers=n_gpu_layers,
                seed=42,
                f16_kv=True,  # Use 16-bit for faster computation
                logits_all=False,
                vocab_only=False,
                use_mmap=True,  # Memory-mapped files for efficiency
                use_mlock=True,  # Lock model in RAM if possible
                embedding=False,  # Disable embeddings if not needed
                low_vram=False,  # We're using CPU anyway
                mul_mat_q=True,  # Enable quantized matrix multiplication
                verbose=False
            )
            
            self.current_model_name = model_name
            logger.info(f"✅ Successfully loaded {model_name}")
            if self.use_prompts:
                logger.info(f"✅ With {sum(len(p) for p in self.loaded_prompts.values())} prompts")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load {model_name}: {e}")
            return False
    
    def _get_system_instruction(self) -> str:
        """Get system instruction from config to prepend to prompts"""
        if not self.system_config or 'system' not in self.system_config:
            return ""
        
        system_cfg = self.system_config['system']
        instruction_parts = []
        
        # Add safety guidelines
        if system_cfg.get('safety_guidelines', {}).get('enabled'):
            rules = system_cfg['safety_guidelines'].get('rules', [])
            if rules:
                instruction_parts.append("Follow these guidelines:\n" + "\n".join(f"- {rule}" for rule in rules[:2]))
        
        # Add response style
        if system_cfg.get('default_behavior', {}).get('response_style'):
            style = system_cfg['default_behavior']['response_style']
            if style == 'conversational':
                instruction_parts.append("Respond in a friendly, conversational manner.")
            elif style == 'formal':
                instruction_parts.append("Respond in a professional, formal manner.")
        
        return "\n".join(instruction_parts) if instruction_parts else ""
    
    def apply_safety_guidelines(self, prompt: str, response: str) -> str:
        """Apply safety guidelines from system config to filter response"""
        if not self.system_config or 'system' not in self.system_config:
            return response
        
        guidelines = self.system_config['system'].get('safety_guidelines', {})
        if not guidelines.get('enabled', False):
            return response
        
        # Check if response violates any safety rules
        rules = guidelines.get('rules', [])
        
        # Basic safety checks (could be expanded)
        harmful_keywords = ['illegal', 'harm', 'unethical', 'medical diagnosis', 'prescription']
        response_lower = response.lower()
        
        for keyword in harmful_keywords:
            if keyword in response_lower:
                # Add disclaimer or filter response
                if 'medical' in keyword:
                    response += "\n\n*Disclaimer: This is general information only. Please consult a healthcare professional for medical advice.*"
                break
        
        return response
    
    def get_config_temperature(self) -> float:
        """Get temperature setting from system config"""
        if self.system_config and 'system' in self.system_config:
            default_behavior = self.system_config['system'].get('default_behavior', {})
            return default_behavior.get('temperature_default', 0.7)
        return 0.7
    
    def get_config_max_context(self) -> int:
        """Get max context length from system config"""
        if self.system_config and 'system' in self.system_config:
            default_behavior = self.system_config['system'].get('default_behavior', {})
            return default_behavior.get('max_context_length', 4096)
        return 4096
    
    def _extract_tool_calls(self, response: str) -> List[Dict]:
        """Extract tool calls from LLM response"""
        tool_calls = []
        
        # Look for tool call patterns in response
        # Pattern 1: [TOOL: search_products(query="blue dream")]
        tool_pattern = r'\[TOOL:\s*(\w+)\((.*?)\)\]'
        matches = re.findall(tool_pattern, response)
        
        for tool_name, params_str in matches:
            try:
                # Parse parameters
                params = {}
                if params_str:
                    # Simple parameter parsing (could be enhanced)
                    param_pairs = re.findall(r'(\w+)=["\'](.*?)["\']', params_str)
                    for key, value in param_pairs:
                        params[key] = value
                
                tool_calls.append({
                    'tool': tool_name,
                    'parameters': params
                })
            except Exception as e:
                logger.warning(f"Failed to parse tool call: {e}")
        
        return tool_calls
    
    async def _execute_tool_calls(self, tool_calls: List[Dict]) -> str:
        """Execute tool calls and format results"""
        if not self.tool_manager:
            return ""
        
        results = []
        for call in tool_calls:
            tool_name = call['tool']
            params = call['parameters']
            
            result = await self.tool_manager.execute_tool(tool_name, params)
            
            if result.success:
                results.append(f"[TOOL_RESULT: {tool_name}]\n{json.dumps(result.data, indent=2)}")
            else:
                results.append(f"[TOOL_ERROR: {tool_name}]\n{result.error}")
        
        return "\n".join(results)
    
    def _add_context_to_prompt(self, prompt: str, session_id: Optional[str] = None) -> str:
        """Add conversation context to prompt"""
        if not self.context_manager or not session_id:
            return prompt
        
        try:
            # Get conversation context synchronously (would need async in production)
            # For now, just return prompt
            return prompt
        except Exception as e:
            logger.warning(f"Failed to add context: {e}")
            return prompt
    
    def generate(self, 
                 prompt: str, 
                 prompt_type: Optional[str] = None,
                 max_tokens: int = 512,
                 temperature: float = None,  # Changed to None to allow config override
                 top_p: float = 0.95,
                 top_k: int = 40,
                 use_tools: bool = False,
                 use_context: bool = False,
                 session_id: Optional[str] = None) -> Dict:
        """Generate response with optional prompt template, tools, and context"""
        
        if not self.current_model:
            return {
                "error": "No model loaded",
                "text": "",
                "model": None,
                "time_ms": 0,
                "used_prompt": False
            }
        
        # Apply system config temperature if not explicitly provided
        if temperature is None:
            temperature = self.get_config_temperature()
        
        try:
            start_time = time.time()
            
            # Apply prompt template if specified
            final_prompt = prompt
            used_template = None
            
            # Add debug prompt listing if asked
            if "list prompts" in prompt.lower() or "show prompts" in prompt.lower():
                if self.use_prompts:
                    prompts_list = []
                    for file_name, prompts in self.loaded_prompts.items():
                        prompts_list.append(f"File: {file_name}")
                        for prompt_key in prompts.keys():
                            prompts_list.append(f"  - {prompt_key}")
                    return {
                        "text": f"Loaded prompts from {self.prompt_folder}:\n" + "\n".join(prompts_list),
                        "model": self.current_model_name,
                        "time_ms": 0,
                        "used_prompt": False,
                        "loaded_prompts": self.list_loaded_prompts(),
                        "error": None
                    }
                else:
                    return {
                        "text": "No prompts loaded. Model is in raw mode.",
                        "model": self.current_model_name,
                        "time_ms": 0,
                        "used_prompt": False,
                        "error": None
                    }
            
            # Apply prompts if available
            template_max_tokens = None
            template_stop_sequences = None
            if prompt_type and self.use_prompts:
                template_applied, template_config = self.apply_prompt_template_with_config(prompt, prompt_type)
                if template_applied and template_applied != prompt:  # Only use if template was actually applied
                    final_prompt = template_applied
                    used_template = prompt_type
                    template_max_tokens = template_config.get('max_tokens', 50)  # Default to 50 if not specified
                    template_stop_sequences = template_config.get('stop_sequences', [])
                    logger.info(f"Applied template '{prompt_type}' with max_tokens={template_max_tokens}")
            elif self.use_prompts and not prompt_type:
                # Auto-detect prompt type based on content and available prompts
                detected_type = None
                if any(word in prompt.lower() for word in ['hello', 'hi', 'hey', 'greetings', 'hola', 'bonjour']):
                    # Try different greeting prompts
                    if self.get_prompt_template('greeting_response'):
                        detected_type = 'greeting_response'
                    elif self.get_prompt_template('greeting_detection'):
                        detected_type = 'greeting_detection'
                    elif self.get_prompt_template('greeting'):
                        detected_type = 'greeting'
                elif any(word in prompt.lower() for word in ['want', 'need', 'looking for', 'show me', 'find', 'offer']):
                    # Try search/product prompts
                    if self.get_prompt_template('product_search'):
                        detected_type = 'product_search'
                    elif self.get_prompt_template('search_extraction_enhanced'):
                        detected_type = 'search_extraction_enhanced'
                
                # Use detected type or fall back to default
                if detected_type:
                    template_applied, template_config = self.apply_prompt_template_with_config(prompt, detected_type)
                    if template_applied and template_applied != prompt:
                        final_prompt = template_applied
                        used_template = detected_type
                        template_max_tokens = template_config.get('max_tokens', 50)
                        template_stop_sequences = template_config.get('stop_sequences', [])
                        logger.info(f"Auto-detected and applied template '{detected_type}'")
                elif self.get_prompt_template('default'):
                    # Use default template for any unmatched input
                    template_applied, template_config = self.apply_prompt_template_with_config(prompt, 'default')
                    if template_applied and template_applied != prompt:
                        final_prompt = template_applied
                        used_template = 'default'
                        template_max_tokens = template_config.get('max_tokens', 50)
                        template_stop_sequences = template_config.get('stop_sequences', [])
                        logger.info(f"Applied default template for unmatched input")
                else:
                    # Default to general conversation if available
                    if self.get_prompt_template('general_conversation'):
                        final_prompt = self.apply_prompt_template(prompt, 'general_conversation')
                        used_template = 'general_conversation'
            
            # If system config is loaded but no prompts applied, add system instruction
            if self.system_config and not used_template:
                system_instruction = self._get_system_instruction()
                if system_instruction:
                    final_prompt = f"{system_instruction}\n\nUser: {prompt}\nAssistant:"
            
            # Apply system config for response style
            response_style = None
            if self.system_config and 'system' in self.system_config:
                response_style = self.system_config['system'].get('default_behavior', {}).get('response_style', 'conversational')
            
            # Adjust parameters based on response style
            if response_style == 'conversational':
                # More natural, flowing responses
                actual_temperature = min(temperature + 0.1, 1.0)
                actual_top_p = top_p
            elif response_style == 'formal':
                # More precise, formal responses
                actual_temperature = max(temperature - 0.2, 0.1)
                actual_top_p = max(top_p - 0.1, 0.8)
            else:
                # Default
                actual_temperature = temperature
                actual_top_p = top_p
            
            # Use template max_tokens if specified, otherwise use provided
            final_max_tokens = template_max_tokens if template_max_tokens else max_tokens
            
            # Combine stop sequences from template and defaults
            stop_sequences = []
            if template_stop_sequences:
                stop_sequences = template_stop_sequences
                logger.info(f"Using template stop sequences: {stop_sequences[:3]}")
            else:
                stop_sequences = ["Human:", "User:", "\n\n\n", "\nCustomer:", "\nBudtender:"]
            
            # Log generation parameters for debugging
            logger.info(f"Generating with max_tokens={final_max_tokens}, temp={actual_temperature:.2f}, stops={len(stop_sequences)}")
            logger.debug(f"Final prompt preview: {final_prompt[:100]}...")
            
            # Optimize sampling parameters for faster generation
            response = self.current_model(
                final_prompt,
                max_tokens=final_max_tokens,
                temperature=actual_temperature,
                top_p=actual_top_p,
                top_k=top_k,
                echo=False,
                stop=stop_sequences[:8],  # Allow more stop sequences for better control
                stream=False,
                repeat_penalty=1.1  # Prevent repetition
            )
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            if response and response.get("choices"):
                text = response["choices"][0].get("text", "")
                
                # Apply safety guidelines if configured
                text = self.apply_safety_guidelines(prompt, text)
                
                # Calculate tokens per second
                completion_tokens = response.get("usage", {}).get("completion_tokens", 0)
                tokens_per_sec = completion_tokens / (elapsed_ms / 1000) if elapsed_ms > 0 else 0
                
                # Include system config info in response
                system_info = {}
                if self.system_config:
                    system_info = {
                        "system_config_loaded": True,
                        "response_style": response_style,
                        "applied_temperature": actual_temperature,
                        "safety_guidelines_enabled": self.system_config.get('system', {}).get('safety_guidelines', {}).get('enabled', False)
                    }
                
                return {
                    "text": text,
                    "model": self.current_model_name,
                    "time_ms": round(elapsed_ms),
                    "tokens": completion_tokens,
                    "tokens_per_sec": round(tokens_per_sec, 1),
                    "used_prompt": self.use_prompts,
                    "prompt_template": used_template,
                    "prompt_folder": self.prompt_folder,
                    "loaded_prompts_count": sum(len(p) for p in self.loaded_prompts.values()) if self.use_prompts else 0,
                    "loaded_files": list(self.loaded_prompts.keys()) if self.use_prompts else [],
                    "final_prompt": final_prompt if used_template else None,
                    "error": None,
                    **system_info  # Add system config info
                }
            else:
                return {
                    "error": "No response from model",
                    "text": "",
                    "model": self.current_model_name,
                    "time_ms": round(elapsed_ms),
                    "used_prompt": self.use_prompts
                }
                
        except Exception as e:
            logger.error(f"Generation error: {e}")
            return {
                "error": str(e),
                "text": "",
                "model": self.current_model_name,
                "time_ms": 0,
                "used_prompt": self.use_prompts
            }
    
    def compare_with_without_prompts(self, user_input: str, prompt_type: str = None) -> Dict:
        """Generate responses with and without prompts for comparison"""
        
        if not self.current_model:
            return {"error": "No model loaded"}
        
        results = {
            "model": self.current_model_name,
            "user_input": user_input,
            "prompt_type": prompt_type
        }
        
        # Generate without prompts
        original_use_prompts = self.use_prompts
        self.use_prompts = False
        results["without_prompts"] = self.generate(user_input, prompt_type)
        
        # Generate with prompts
        self.use_prompts = original_use_prompts
        if self.use_prompts:
            results["with_prompts"] = self.generate(user_input, prompt_type)
        else:
            results["with_prompts"] = {"error": "No prompts loaded"}
        
        # Calculate differences
        if "error" not in results["without_prompts"] and "error" not in results["with_prompts"]:
            time_diff = results["with_prompts"]["time_ms"] - results["without_prompts"]["time_ms"]
            results["time_difference_ms"] = time_diff
            results["time_difference_pct"] = round((time_diff / results["without_prompts"]["time_ms"]) * 100, 1) if results["without_prompts"]["time_ms"] > 0 else 0
        
        return results
    
    def benchmark_model(self, model_name: str, with_prompts: bool = False, test_prompts: List[str] = None) -> Dict:
        """Benchmark a model with or without prompts"""
        
        if not test_prompts:
            test_prompts = [
                "What is 2+2?",
                "hello",
                "I want to find cannabis products",
                "show me sativa flowers",
                "Explain quantum computing in simple terms"
            ]
        
        # Load the model
        prompt_folder = self.prompt_folder if with_prompts else None
        if not self.load_model(model_name, prompt_folder):
            return {"error": f"Failed to load {model_name}"}
        
        results = {
            "model": model_name,
            "with_prompts": with_prompts,
            "prompt_folder": prompt_folder,
            "tests": [],
            "avg_time_ms": 0,
            "avg_tokens_per_sec": 0
        }
        
        total_time = 0
        total_tps = 0
        
        for prompt in test_prompts:
            # Auto-detect prompt type for benchmarking
            prompt_type = None
            if with_prompts:
                if 'hello' in prompt.lower():
                    prompt_type = 'greeting_detection'
                elif 'want' in prompt.lower() or 'show' in prompt.lower():
                    prompt_type = 'search_extraction_enhanced'
            
            result = self.generate(prompt, prompt_type=prompt_type, max_tokens=100)
            results["tests"].append({
                "prompt": prompt[:50] + "..." if len(prompt) > 50 else prompt,
                "prompt_type": prompt_type,
                "response": result["text"][:100] + "..." if len(result["text"]) > 100 else result["text"],
                "time_ms": result.get("time_ms", 0),
                "tokens_per_sec": result.get("tokens_per_sec", 0),
                "used_template": result.get("prompt_template")
            })
            total_time += result.get("time_ms", 0)
            total_tps += result.get("tokens_per_sec", 0)
        
        if test_prompts:
            results["avg_time_ms"] = round(total_time / len(test_prompts))
            results["avg_tokens_per_sec"] = round(total_tps / len(test_prompts), 1)
        
        return results

# Global instance
_engine_v5 = None

def get_smart_engine_v5() -> SmartAIEngineV5:
    """Get or create Smart AI Engine V5 singleton"""
    global _engine_v5
    if _engine_v5 is None:
        _engine_v5 = SmartAIEngineV5()
    return _engine_v5

# Backward compatibility
def get_test_engine() -> SmartAIEngineV5:
    """Backward compatibility alias"""
    return get_smart_engine_v5()