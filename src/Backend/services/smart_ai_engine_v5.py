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
    from services.tool_manager import ToolManager
    from services.tools.base import ITool, ToolResult
    from services.tools.dispensary_tools import DispensarySearchTool, DosageCalculatorTool, StrainComparisonTool
    from services.tools.dispensary_tools_db import DispensarySearchToolDB, DispensaryStatsToolDB
    from services.context.base import ContextManager, MemoryContextStore, DatabaseContextStore, IContextStore
    TOOLS_AVAILABLE = True
except ImportError as e:
    TOOLS_AVAILABLE = False
    logging.warning(f"Tool and context modules not available: {e}")

# Import intent detector
try:
    from services.intent_detector import IntentDetectorInterface, LLMIntentDetector, PatternIntentDetector
    INTENT_DETECTOR_AVAILABLE = True
except ImportError:
    INTENT_DETECTOR_AVAILABLE = False
    logging.warning("Intent detector module not available")

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

        # Initialize agent pool manager for multi-agent support (BEFORE tools/context)
        self.agent_pool = None
        self._initialize_agent_pool()

        # Initialize tools and context systems (needs agent_pool to be set)
        self.tool_manager = None
        self.context_manager = None
        self.session_id = None
        self._initialize_tools_and_context()

        # Initialize intent detector
        self.intent_detector = None
        self._detecting_intent = False  # Flag to prevent recursion during intent detection
        self._initialize_intent_detector()

        # Initialize LLM Router for cloud inference (hot-swappable backend)
        self.llm_router = None
        self.use_cloud_inference = False  # Flag to switch between local and cloud
        self._initialize_llm_router()

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
    
    def _initialize_agent_pool(self):
        """Initialize agent pool manager for multi-agent support"""
        try:
            from services.agent_pool_manager import get_agent_pool
            self.agent_pool = get_agent_pool()
            # Set this engine as the shared model
            self.agent_pool.set_shared_model(self)
            logger.info(f"Agent pool initialized with {len(self.agent_pool.agents)} agents")
        except Exception as e:
            logger.error(f"Failed to initialize agent pool: {e}")
            self.agent_pool = None

    def _initialize_intent_detector(self):
        """Initialize intent detector based on configuration"""
        if not INTENT_DETECTOR_AVAILABLE:
            logger.warning("Intent detector not available")
            return

        try:
            # Check config for detector type
            detector_type = "llm"  # default
            if self.system_config:
                detector_type = self.system_config.get('intent_detection', {}).get('type', 'llm')

            # Initialize appropriate detector
            if detector_type == 'llm':
                self.intent_detector = LLMIntentDetector(v5_engine=self)
                logger.info("Initialized LLM-based intent detector")
            elif detector_type == 'pattern':
                self.intent_detector = PatternIntentDetector()
                logger.info("Initialized pattern-based intent detector")
            else:
                self.intent_detector = LLMIntentDetector(v5_engine=self)
                logger.info(f"Unknown detector type '{detector_type}', using LLM detector")

        except Exception as e:
            logger.error(f"Failed to initialize intent detector: {e}")
            self.intent_detector = None

    def _initialize_llm_router(self):
        """Initialize LLM Router for cloud inference hot-swap"""
        try:
            from services.llm_gateway import (
                LLMRouter,
                RequestContext,
                TaskType,
                GroqProvider,
                OpenRouterProvider,
                LLM7GPT4Mini
            )

            # Create router
            self.llm_router = LLMRouter()

            # Register cloud providers (automatically skip if no API key)
            self.llm_router.register_provider(GroqProvider())           # Ultra-fast
            self.llm_router.register_provider(OpenRouterProvider())     # Reasoning
            self.llm_router.register_provider(LLM7GPT4Mini())          # Fallback (no auth)

            provider_count = len(self.llm_router.list_providers())
            logger.info(f"✅ LLM Router initialized with {provider_count} cloud providers")
            logger.info(f"   Providers: {', '.join(self.llm_router.list_providers())}")

            # Check config for default inference backend
            if self.system_config:
                self.use_cloud_inference = self.system_config.get('inference', {}).get('use_cloud', False)
                if self.use_cloud_inference:
                    logger.info("🌐 Cloud inference ENABLED by default (hot-swap active)")
                else:
                    logger.info("💻 Local inference default (cloud available for hot-swap)")

        except ImportError as e:
            logger.warning(f"LLM Router not available: {e}")
            self.llm_router = None
        except Exception as e:
            logger.error(f"Failed to initialize LLM Router: {e}")
            self.llm_router = None
    
    def detect_intent(self, message: str, language: str = "auto") -> Dict[str, Any]:
        """Detect intent using the configured detector"""
        if not self.intent_detector:
            # Fallback to basic detection
            return self._basic_intent_detection(message)
        
        try:
            # Detect intent
            result = self.intent_detector.detect(message, language)
            
            # Ensure result is a dictionary
            if not isinstance(result, dict):
                logger.warning(f"Intent detector returned non-dict: {type(result)} - {result}")
                return self._basic_intent_detection(message)
            
            # Log detection result
            logger.info(f"Intent detected: {result.get('intent')} (confidence: {result.get('confidence')})")
            
            return result
            
        except AttributeError as e:
            # Handle the specific case where we get a string instead of dict
            logger.error(f"Intent detection returned invalid type (likely string): {e}")
            return self._basic_intent_detection(message)
        except Exception as e:
            logger.error(f"Intent detection failed: {e}")
            return self._basic_intent_detection(message)
    
    async def detect_intent_async(self, message: str, language: str = "auto") -> Dict[str, Any]:
        """Async version of detect intent using the configured detector"""
        if not self.intent_detector:
            # Fallback to basic detection
            return self._basic_intent_detection(message)

        try:
            # Run intent detection in executor to avoid blocking
            import asyncio
            loop = asyncio.get_event_loop()

            # Run the blocking detect call in a thread pool
            result = await loop.run_in_executor(
                None,  # Use default executor
                self.intent_detector.detect,
                message,
                language
            )

            # Ensure result is a dictionary
            if not isinstance(result, dict):
                logger.warning(f"Intent detector returned non-dict: {type(result)} - {result}")
                return self._basic_intent_detection(message)

            # Log detection result
            logger.info(f"Intent detected (async): {result.get('intent')} (confidence: {result.get('confidence')})")

            return result

        except AttributeError as e:
            # Handle the specific case where we get a string instead of dict
            logger.error(f"Intent detection returned invalid type (likely string): {e}")
            return self._basic_intent_detection(message)
        except Exception as e:
            logger.error(f"Async intent detection failed: {e}")
            return self._basic_intent_detection(message)

    def _basic_intent_detection(self, message: str) -> Dict[str, Any]:
        """Basic fallback when intent detector is not available"""
        # No pattern matching - just return general intent
        return {"intent": "general", "confidence": 0.3, "method": "no_detector"}
    
    def _initialize_tools_and_context(self):
        """Initialize tool manager and context storage based on config"""
        if not TOOLS_AVAILABLE:
            logger.warning("Tools and context modules not available, skipping initialization")
            return
            
        try:
            # Initialize tools if enabled in config
            if self.system_config and self.system_config.get('system', {}).get('tools', {}).get('enabled'):
                self.tool_manager = ToolManager(agent_pool=self.agent_pool)

                # Set tool manager reference in agent pool and enroll agent-specific tools
                if self.agent_pool:
                    self.agent_pool.set_tool_manager(self.tool_manager)

                # Load agent-specific tools if configured
                if self.current_agent:
                    self._load_agent_tools(self.current_agent)

                logger.info(f"Tool manager initialized with {len(self.tool_manager.list_tools())} tools, agent_pool: {self.agent_pool is not None}")
            
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
                
                self.context_manager = ContextManager(store)
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
            
            # Dynamically load all tools based on configuration
            for tool_name in agent_tools:
                try:
                    # Product Search - Now uses API gateway instead of database
                    if tool_name == 'product_search':
                        # Product search is now handled via read_api tool
                        logger.info("Product search will use API gateway via read_api tool")
                        continue
                    
                    # Dosage Calculator (local logic, no external data needed)
                    elif tool_name == 'dosage_calculator':
                        self.tool_manager.register_tool(DosageCalculatorTool())
                        logger.info("Loaded DosageCalculatorTool")
                    
                    # Strain Comparison (uses API data)
                    elif tool_name == 'compare_strains':
                        # Strain comparison now fetches data via API
                        logger.info("Strain comparison will use API gateway via read_api tool")
                        continue
                    
                    # Product Statistics (uses API analytics endpoints)
                    elif tool_name == 'product_stats':
                        # Statistics now come from API analytics endpoints
                        logger.info("Product statistics will use API gateway analytics endpoints")
                        continue
                    
                    # Smart API Orchestration Tool (for WRITE operations)
                    elif tool_name == 'api_orchestrator':
                        from tools.api_tool_integration import register_api_tool_with_v5
                        # Pass full configuration to the tool
                        register_api_tool_with_v5(self.tool_manager, config=self.system_config)
                        logger.info("Loaded Smart API Orchestration Tool with configuration-driven endpoints")
                    
                    # Stateless Read API Tool (for READ operations)
                    elif tool_name == 'read_api':
                        from tools.stateless_read_api_tool import register_conversation_read_tool_with_v5
                        # Pass full configuration to the tool
                        register_conversation_read_tool_with_v5(self.tool_manager, config=self.system_config)
                        logger.info("Loaded Stateless Read API Tool with configuration-driven endpoints")
                    
                    # Unknown tool warning
                    else:
                        logger.warning(f"Unknown tool '{tool_name}' in configuration for agent '{agent_id}'")
                        
                except ImportError as e:
                    logger.warning(f"Tool '{tool_name}' not available - missing dependencies: {e}")
                except Exception as e:
                    logger.error(f"Failed to load tool '{tool_name}': {e}")
                
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
        # Check both V5/models and ai-engine-service/models
        base_paths = [
            Path("models"),
            Path("../models"),
            Path("/Users/charrcy/projects/WeedGo/microservices/ai-engine-service/models")
        ]
        
        for base_path in base_paths:
            if not base_path.exists():
                continue
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
        # Try multiple config locations in order of preference
        config_paths = [
            Path("config/system_config.json"),  # Primary config location
            Path("prompts/system/config.json"),  # Legacy location
            Path("system_config.json"),  # Root directory fallback
        ]
        
        for config_path in config_paths:
            try:
                if config_path.exists():
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                        logger.info(f"Loaded system config from {config_path}")
                        return config
            except Exception as e:
                logger.warning(f"Could not load config from {config_path}: {e}")
        
        logger.warning("No system config found, using defaults")
        return {}
    
    def update_personality(self, personality_id: str) -> bool:
        """Update personality without reloading model or agent configuration"""
        try:
            if not self.current_agent:
                logger.error("No agent loaded - cannot update personality")
                return False
            
            logger.info(f"=== UPDATING PERSONALITY ===")
            logger.info(f"Current agent: {self.current_agent}, New personality: {personality_id}")
            
            # Load new personality traits
            agent_personality_path = Path(f"prompts/agents/{self.current_agent}/personality/{personality_id}.json")
            
            if agent_personality_path.exists():
                with open(agent_personality_path, 'r') as f:
                    personality_data = json.load(f)
                    self.personality_traits = personality_data.get('personality', {})
                    self.current_personality_type = personality_id
                    logger.info(f"✅ UPDATED PERSONALITY to '{personality_id}' for agent '{self.current_agent}'")
                    logger.info(f"  Personality name: {self.personality_traits.get('name')}")
                    
                    # Update use_prompts flag
                    self.use_prompts = bool(self.agent_prompts or self.personality_traits or self.system_config)
                    return True
            else:
                logger.error(f"❌ PERSONALITY NOT FOUND at {agent_personality_path}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to update personality: {e}")
            return False
    
    def load_agent_personality(self, agent_id: str = None, personality_id: str = None) -> bool:
        """Load agent and personality combination for modular system"""
        try:
            logger.info(f"=== LOADING AGENT PERSONALITY ===")
            logger.info(f"Agent ID: {agent_id}, Personality ID: {personality_id}")
            
            # Reset current configuration
            self.agent_prompts = {}
            self.personality_traits = {}
            self.system_config = {}
            self.current_agent = agent_id
            self.current_personality_type = personality_id
            
            # Load agent configuration and prompts
            if agent_id:
                # First load the config.json if it exists
                config_path = Path(f"prompts/agents/{agent_id}/config.json")
                if config_path.exists():
                    with open(config_path, 'r') as f:
                        config_data = json.load(f)
                        # Store the entire config including system_behavior settings
                        self.system_config = config_data
                        # Extract system behavior settings specifically
                        if 'system_behavior' in config_data:
                            self.system_config.update(config_data['system_behavior'])
                        if 'default_behavior' in config_data:
                            self.system_config.update(config_data['default_behavior'])
                        if 'safety_guidelines' in config_data:
                            self.system_config['safety_guidelines'] = config_data['safety_guidelines']
                        logger.info(f"✅ LOADED CONFIG.JSON for '{agent_id}' - Keys: {list(config_data.keys())}")
                        if 'model_settings' in config_data:
                            logger.info(f"  Model settings: {config_data['model_settings']}")
                else:
                    logger.warning(f"❌ CONFIG.JSON NOT FOUND at {config_path}")
                
                # Load intent configuration for this agent
                if self.intent_detector:
                    loaded = self.intent_detector.load_intents(agent_id)
                    logger.info(f"✅ LOADED INTENT.JSON for agent {agent_id}: {loaded}")
                else:
                    logger.warning(f"❌ Intent detector not initialized")
                
                # Then load the prompts.json
                agent_path = Path(f"prompts/agents/{agent_id}/prompts.json")
                if agent_path.exists():
                    with open(agent_path, 'r') as f:
                        agent_data = json.load(f)
                        self.agent_prompts = agent_data.get('prompts', {})
                        logger.info(f"✅ LOADED PROMPTS.JSON for '{agent_id}' - {len(self.agent_prompts)} prompts")
                        logger.info(f"  Available prompts: {list(self.agent_prompts.keys())}")
                else:
                    logger.warning(f"❌ PROMPTS.JSON NOT FOUND at {agent_path}")
            
            # Load personality traits
            if personality_id:
                # First check for personality in agent's personality folder (note: singular 'personality')
                agent_personality_path = Path(f"prompts/agents/{agent_id}/personality/{personality_id}.json") if agent_id else None
                personality_path = Path(f"prompts/personality/{personality_id}/traits.json")
                
                if agent_personality_path and agent_personality_path.exists():
                    # Load from agent-specific personality
                    with open(agent_personality_path, 'r') as f:
                        personality_data = json.load(f)
                        self.personality_traits = personality_data.get('personality', {})
                        logger.info(f"✅ LOADED PERSONALITY '{personality_id}' for agent '{agent_id}'")
                        logger.info(f"  Personality name: {self.personality_traits.get('name')}")
                        logger.info(f"  Traits: {self.personality_traits.get('traits', {})}")
                elif personality_path.exists():
                    # Load from global personality folder
                    with open(personality_path, 'r') as f:
                        personality_data = json.load(f)
                        self.personality_traits = personality_data.get('personality', {})
                        logger.info(f"Loaded global personality '{personality_id}' - {self.personality_traits.get('name')}")
            
            self.use_prompts = bool(self.agent_prompts or self.personality_traits or self.system_config)
            
            # Log summary of what was loaded
            logger.info(f"=== LOADING COMPLETE ===")
            logger.info(f"  use_prompts: {self.use_prompts}")
            logger.info(f"  agent_prompts loaded: {len(self.agent_prompts)} prompts")
            logger.info(f"  personality loaded: {self.personality_traits.get('name', 'None')}")
            logger.info(f"  system_config loaded: {bool(self.system_config)}")
            
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

        # First check agent-specific prompts
        if self.agent_prompts and prompt_type in self.agent_prompts:
            return self.agent_prompts[prompt_type]

        # Then search through all loaded prompt files
        for file_prompts in self.loaded_prompts.values():
            if prompt_type in file_prompts:
                return file_prompts[prompt_type]

        return None
    
    def apply_agent_template(self, user_input: str, prompt_type: str) -> str:
        """Apply agent-based prompt template with personality modifiers"""
        if not self.agent_prompts or prompt_type not in self.agent_prompts:
            return self.apply_prompt_template(user_input, prompt_type)
        
        template_data = self.agent_prompts[prompt_type]
        
        # Handle both string and dict formats
        if isinstance(template_data, str):
            # If template_data is a string, use it directly as the template
            template_str = template_data
            use_system_format = False
        elif isinstance(template_data, dict):
            template_str = template_data.get('template', '')
        else:
            # Fallback for unexpected types
            logger.warning(f"Unexpected template_data type: {type(template_data)}")
            return user_input
        
        if not template_str:
            return user_input
        
        # Check if this should be used as a system message (only for dict format)
        if not isinstance(template_data, dict):
            use_system_format = False
        else:
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
        
        # Replace other common variables with defaults (only for dict format)
        if isinstance(template_data, dict):
            variables = template_data.get('variables', [])
        else:
            # For string templates, check for common variables in the template itself
            variables = []
            if '{message}' in template_str:
                variables.append('message')
        
        # Get list of tool result variables that should NOT be replaced yet
        tool_result_vars = set()
        if isinstance(template_data, dict) and 'tools' in template_data:
            tool_config = template_data['tools']
            if 'result_injection' in tool_config:
                tool_result_vars = set(tool_config['result_injection'].values())

        for var in variables:
            # Skip tool result variables - they will be injected after tool execution
            if var in tool_result_vars:
                logger.info(f"Skipping variable '{var}' - will be injected after tool execution")
                continue

            if var == 'message':
                # Don't replace message in system format
                if not use_system_format:
                    template_str = template_str.replace('{message}', user_input)
            elif var == 'effects':
                template_str = template_str.replace('{effects}', '')
            elif var == 'budget':
                template_str = template_str.replace('{budget}', '')
            elif var == 'experience':
                template_str = template_str.replace('{experience}', '')
            else:
                template_str = template_str.replace(f'{{{var}}}', '')
        
        # If system format, create a system-user prompt structure
        if use_system_format:
            # Get format from config or return empty
            if self.system_config and 'prompt_format' in self.system_config:
                return self.system_config['prompt_format'].format(system=template_str, user=user_input)
            return user_input
        
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
        
        # Handle case where template is a string (backward compatibility)
        if isinstance(template, str):
            # If template is just a string, wrap it in a dict format
            template = {'template': template}
        
        # Get template config with better defaults
        if template and isinstance(template, dict):
            # Extract max_tokens from template or constraints
            max_tokens = template.get('max_tokens')
            if not max_tokens and 'constraints' in template:
                max_tokens = template['constraints'].get('max_words', 30) * 2  # Rough conversion
            
            # Get stop sequences from template, constraints, or use defaults
            stop_sequences = template.get('stop_sequences', [])
            if not stop_sequences and 'constraints' in template:
                stop_sequences = template['constraints'].get('stop_sequences', [])
            if not stop_sequences:
                # Get stop sequences from config only
                stop_sequences = self.system_config.get('default_stop_sequences', []) if self.system_config else []
            
            config = {
                'max_tokens': max_tokens or (self.system_config.get('default_max_tokens') if self.system_config else None),
                'stop_sequences': stop_sequences,
                'tools': template.get('tools')  # Include tools configuration
            }
        else:
            config = {'max_tokens': self.system_config.get('default_max_tokens') if self.system_config else None, 'stop_sequences': []}
            
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
                personality_str = f"You are {self.current_personality.get('name', '')}, {self.current_personality.get('description', '')}. "
                if self.current_personality.get('traits'):
                    traits = self.current_personality['traits']
                    personality_str += f"You are {traits.get('age', '')} years old with {traits.get('communication_style', '')} communication style. "
                    personality_str += f"Your approach is {traits.get('sales_approach', '')} and {traits.get('formality', '')}."
                formatted_prompt = formatted_prompt.replace('{personality}', personality_str)
            else:
                formatted_prompt = formatted_prompt.replace('{personality}', '')
        
        # Replace other common placeholders with defaults
        if 'conversation_text' in variables:
            formatted_prompt = formatted_prompt.replace('{conversation_text}', '')
        if 'customer_context' in variables:
            formatted_prompt = formatted_prompt.replace('{customer_context}', '')
        if 'customer_profile' in variables:
            formatted_prompt = formatted_prompt.replace('{customer_profile}', '')
        if 'available_products' in variables:
            formatted_prompt = formatted_prompt.replace('{available_products}', '')
        if 'product_data' in variables:
            formatted_prompt = formatted_prompt.replace('{product_data}', '')
        if 'products_shown' in variables:
            formatted_prompt = formatted_prompt.replace('{products_shown}', '')
        
        # If system format, create a system-user prompt structure
        if use_system_format:
            # Get format from config or return as-is
            if self.system_config and 'prompt_format' in self.system_config:
                formatted_prompt = self.system_config['prompt_format'].format(system=formatted_prompt, user=user_input)
            else:
                formatted_prompt = user_input
        
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
                # Count prompts from either agent system or legacy system
                prompt_count = len(self.agent_prompts) if self.agent_prompts else sum(len(p) for p in self.loaded_prompts.values())
                logger.info(f"✅ With {prompt_count} prompts loaded")
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
        
        # Add response style from config
        if system_cfg.get('default_behavior', {}).get('response_style'):
            style = system_cfg['default_behavior']['response_style']
            # Get style descriptions from config
            style_descriptions = system_cfg.get('response_style_descriptions', {})
            if style in style_descriptions:
                instruction_parts.append(style_descriptions[style])
        
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
        """Get temperature setting from agent config or system config"""
        # First check if we have agent config with model settings
        if hasattr(self, 'agent_config') and self.agent_config:
            model_settings = self.agent_config.get('model_settings', {})
            if 'temperature' in model_settings:
                return model_settings['temperature']
        
        # Fall back to system config
        if self.system_config and 'system' in self.system_config:
            default_behavior = self.system_config['system'].get('default_behavior', {})
            return default_behavior.get('temperature_default', 0.7)
        return 0.7
    
    def get_config_max_context(self) -> int:
        """Get max context length from agent config or system config"""
        # First check agent config
        if hasattr(self, 'agent_config') and self.agent_config:
            model_settings = self.agent_config.get('model_settings', {})
            if 'context_window' in model_settings:
                return model_settings['context_window']
        
        # Fall back to system config
        if self.system_config and 'system' in self.system_config:
            default_behavior = self.system_config['system'].get('default_behavior', {})
            return default_behavior.get('max_context_length', 4096)
        return 4096
    
    def get_config_max_tokens(self) -> int:
        """Get max tokens from agent config"""
        if hasattr(self, 'agent_config') and self.agent_config:
            model_settings = self.agent_config.get('model_settings', {})
            if 'max_tokens' in model_settings:
                return model_settings['max_tokens']
        return 512  # Default
    
    def get_config_top_p(self) -> float:
        """Get top_p from agent config"""
        if hasattr(self, 'agent_config') and self.agent_config:
            model_settings = self.agent_config.get('model_settings', {})
            if 'top_p' in model_settings:
                return model_settings['top_p']
        return 0.95  # Default
    
    def get_config_repeat_penalty(self) -> float:
        """Get repeat penalty from agent config"""
        if hasattr(self, 'agent_config') and self.agent_config:
            model_settings = self.agent_config.get('model_settings', {})
            if 'repeat_penalty' in model_settings:
                return model_settings['repeat_penalty']
        return 1.1  # Default
    
    def _generate_internal(self, prompt: str, max_tokens: int = 20, temperature: float = 0.1, top_p: float = 0.9) -> Dict[str, Any]:
        """Internal generation method for intent detection to avoid recursion"""
        if not self.current_model:
            return {"text": "general", "error": "No model loaded"}
        
        try:
            # Direct model call without any prompt processing or intent detection
            response = self.current_model(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                stop=["\n", ".", ","],
                echo=False,
                stream=False
            )
            
            # Handle different response types
            if isinstance(response, str):
                return {"text": response.strip() if response else "general"}
            elif isinstance(response, dict) and response.get("choices"):
                text = response["choices"][0].get("text", "")
                return {"text": text.strip() if text else "general"}
            else:
                return {"text": "general"}
                
        except Exception as e:
            logger.error(f"Internal generation failed: {e}")
            return {"text": "general", "error": str(e)}
    
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

    def _generate_quick_actions(self, products: List[Dict]) -> List[Dict]:
        """Generate quick action buttons based on product analysis"""
        if not products:
            return []

        from collections import defaultdict

        # Analyze products to generate relevant quick actions
        categories = defaultdict(int)
        price_ranges = []
        thc_ranges = []

        for product in products:
            # Count categories
            subcategory = product.get('subcategory', product.get('category', ''))
            if subcategory:
                categories[subcategory] += 1

            # Collect price data
            price = product.get('price', 0)
            if price:
                price_ranges.append(price)

            # Collect THC data
            thc_content = product.get('thcContent', {})
            if isinstance(thc_content, dict):
                thc_max = thc_content.get('max', 0)
                if thc_max:
                    thc_ranges.append(thc_max)

        quick_actions = []

        # Generate category filters (top 3 categories)
        sorted_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:3]
        for category, count in sorted_categories:
            quick_actions.append({
                "type": "filter",
                "label": f"{category} ({count})",
                "action": "filter_category",
                "value": category
            })

        # Generate price range filters
        if price_ranges:
            min_price = min(price_ranges)
            max_price = max(price_ranges)
            mid_price = (min_price + max_price) / 2

            quick_actions.append({
                "type": "filter",
                "label": f"Under ${mid_price:.0f}",
                "action": "filter_price",
                "value": {"max": mid_price}
            })

            quick_actions.append({
                "type": "filter",
                "label": f"Over ${mid_price:.0f}",
                "action": "filter_price",
                "value": {"min": mid_price}
            })

        # Generate THC filters
        if thc_ranges:
            avg_thc = sum(thc_ranges) / len(thc_ranges)

            quick_actions.append({
                "type": "filter",
                "label": f"High THC (>{avg_thc:.0f}%)",
                "action": "filter_thc",
                "value": {"min": avg_thc}
            })

            quick_actions.append({
                "type": "filter",
                "label": f"Low THC (<{avg_thc:.0f}%)",
                "action": "filter_thc",
                "value": {"max": avg_thc}
            })

        # Add "Show All" action
        quick_actions.append({
            "type": "action",
            "label": "Show All Products",
            "action": "show_all",
            "value": None
        })

        return quick_actions

    def _format_products_for_template(self, products: List[Dict]) -> str:
        """Format product results for template injection with categorization"""
        if not products:
            return "No products found matching your criteria."

        # Categorize products
        from collections import defaultdict
        categories = defaultdict(list)

        for product in products:
            # Map API response fields
            name = product.get('name', 'Unknown Product')
            brand = product.get('brand', '')
            sku = product.get('sku', 'N/A')

            # Extract THC/CBD from nested content objects
            thc_content = product.get('thcContent', {})
            cbd_content = product.get('cbdContent', {})
            thc = thc_content.get('display', 'N/A') if isinstance(thc_content, dict) else 'N/A'
            cbd = cbd_content.get('display', 'N/A') if isinstance(cbd_content, dict) else 'N/A'

            # Extract numeric THC for sorting
            try:
                thc_num = float(thc_content.get('max', 0)) if isinstance(thc_content, dict) else 0
            except:
                thc_num = 0

            price = product.get('price', 0)
            category = product.get('category', 'Unknown')
            subcategory = product.get('subcategory', category)
            plant_type = product.get('plantType', product.get('strainType', ''))

            # Build product display
            product_display = f"{brand} {name}" if brand else name

            # Store product with metadata
            categories[subcategory].append({
                'display': product_display,
                'thc': thc,
                'thc_num': thc_num,
                'cbd': cbd,
                'price': price,
                'plant_type': plant_type,
                'category': category
            })

        # Build categorized summary
        formatted_lines = []
        formatted_lines.append(f"Found {len(products)} products across {len(categories)} categories:\n")

        for subcategory, items in categories.items():
            # Calculate ranges for this category
            prices = [p['price'] for p in items if p['price']]
            thc_values = [p['thc_num'] for p in items if p['thc_num']]

            price_range = f"${min(prices):.2f}-${max(prices):.2f}" if prices else "N/A"
            thc_range = f"{min(thc_values):.1f}%-{max(thc_values):.1f}%" if thc_values else "N/A"

            formatted_lines.append(
                f"\n{subcategory} ({len(items)} items):\n"
                f"  Price range: {price_range} | THC range: {thc_range}\n"
            )

            # List top 3 items from this category
            for i, item in enumerate(items[:3], 1):
                formatted_lines.append(
                    f"  {i}. {item['display']} - {item['plant_type']}\n"
                    f"     THC: {item['thc']} | CBD: {item['cbd']} | ${item['price']}\n"
                )

        return "".join(formatted_lines)
    
    async def generate(self,
                 prompt: str,
                 prompt_type: Optional[str] = None,
                 max_tokens: int = None,
                 temperature: float = None,  # Changed to None to allow config override
                 top_p: float = None,
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
        
        # Apply config values if not explicitly provided
        if temperature is None:
            temperature = self.get_config_temperature()
        if max_tokens is None:
            max_tokens = self.get_config_max_tokens()
        if top_p is None:
            top_p = self.get_config_top_p()
        
        try:
            start_time = time.time()
            timing_breakdown = {}

            # Save original user message for tool parameter substitution
            original_user_message = prompt

            # Apply prompt template if specified
            final_prompt = prompt
            used_template = None
            intent_result = None  # Initialize to avoid UnboundLocalError

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
                try:
                    template_applied, template_config = self.apply_prompt_template_with_config(prompt, prompt_type)
                except ValueError as e:
                    # Handle unpacking error
                    logger.error(f"Failed to unpack template result: {e}")
                    template_applied = prompt
                    template_config = {}
                if template_applied and template_applied != prompt:  # Only use if template was actually applied
                    final_prompt = template_applied
                    used_template = prompt_type
                    # Ensure template_config is a dict before calling .get()
                    if not isinstance(template_config, dict):
                        template_config = {}
                    template_max_tokens = template_config.get('max_tokens') or (self.system_config.get('default_max_tokens') if self.system_config else None)
                    template_stop_sequences = template_config.get('stop_sequences', [])
                    logger.info(f"Applied template '{prompt_type}' with max_tokens={template_max_tokens}")
            elif self.use_prompts and not prompt_type:
                # SERIAL EXECUTION: Detect intent first, then apply template
                detected_type = None
                logger.info(f"Intent detection path: use_prompts={self.use_prompts}, intent_detector={self.intent_detector is not None}")

                # Run intent detection serially if available
                if self.intent_detector:
                    intent_detect_start = time.time()
                    try:
                        intent_result = self.detect_intent(prompt)
                        timing_breakdown['intent_detection'] = time.time() - intent_detect_start
                        logger.info(f"Serial intent detection completed: {intent_result} (took {timing_breakdown['intent_detection']:.2f}s)")
                        # Extract the prompt_type from the intent result
                        if isinstance(intent_result, dict):
                            detected_type = intent_result.get('prompt_type') or intent_result.get('intent')
                        else:
                            detected_type = intent_result
                    except Exception as e:
                        logger.warning(f"Intent detection failed: {e}")
                        detected_type = None
                else:
                    logger.warning("Intent detector not available, skipping intent detection")

                # Apply template based on detected intent or use default
                if detected_type and self.get_prompt_template(detected_type):
                    try:
                        logger.info(f"[V5-INTENT] 🎯 Applying template for detected type: '{detected_type}'")
                        template_applied, template_config = self.apply_prompt_template_with_config(prompt, detected_type)
                        logger.info(f"[V5-INTENT] Template config keys: {list(template_config.keys()) if isinstance(template_config, dict) else 'Not a dict'}")

                        if template_applied and template_applied != prompt:
                            final_prompt = template_applied
                            used_template = detected_type
                            if isinstance(template_config, dict):
                                template_max_tokens = template_config.get('max_tokens') or (self.system_config.get('default_max_tokens') if self.system_config else None)
                                template_stop_sequences = template_config.get('stop_sequences', [])

                                # Check if template specifies tools to execute
                                if 'tools' in template_config:
                                    tool_config = template_config['tools']
                                    logger.info(f"[V5-TEMPLATE] 📋 Template '{detected_type}' specifies tools: {tool_config}")

                                    # Execute tools before prompt generation (check if tool_config is not None)
                                    if tool_config and tool_config.get('execution') == 'before_prompt':
                                        tool_results = {}
                                        required_tools = tool_config.get('required', [])
                                        logger.info(f"[V5-TEMPLATE] 🔧 Required tools to execute: {required_tools}")

                                        # Get session context for store_id if needed
                                        session_context = {}
                                        if session_id and self.context_manager:
                                            try:
                                                session_context = await self.context_manager.get_context(session_id)
                                            except Exception as e:
                                                logger.warning(f"Failed to get session context: {e}")

                                        for tool_name in required_tools:
                                            if tool_name in tool_config.get('parameters', {}):
                                                # Get tool parameters and substitute variables
                                                tool_params = tool_config['parameters'][tool_name]
                                                substituted_params = {}

                                                for param_key, param_value in tool_params.items():
                                                    # Substitute {message} with original user message (not the template)
                                                    if isinstance(param_value, str) and '{message}' in param_value:
                                                        substituted_value = param_value.replace('{message}', original_user_message)
                                                        substituted_params[param_key] = substituted_value
                                                        logger.debug(f"Substituted param '{param_key}': '{param_value}' -> '{substituted_value}' (original_user_message='{original_user_message}')")
                                                    else:
                                                        substituted_params[param_key] = param_value

                                                # Add store_id from context for smart_product_search
                                                if tool_name == 'smart_product_search' and 'store_id' in session_context:
                                                    substituted_params['store_id'] = session_context['store_id']
                                                    logger.info(f"Added store_id from context: {session_context['store_id']}")

                                                # Execute the tool
                                                logger.info(f"[V5-TOOL] 🚀 Executing tool '{tool_name}' with params: {substituted_params}")
                                                tool_result = await self.tool_manager.execute_tool(tool_name, **substituted_params)
                                                logger.info(f"[V5-TOOL] Tool '{tool_name}' execution complete. Success: {tool_result.get('success')}")

                                                # RECURSION PREVENTION: Check if smart_product_search needs clarification
                                                if tool_name == 'smart_product_search' and tool_result.get("success"):
                                                    result_data = tool_result.get("result", {})
                                                    if result_data.get("needs_clarification") and result_data.get("quick_actions"):
                                                        logger.info(f"SmartProductSearch needs clarification, returning quick actions to user")
                                                        # Return quick actions immediately without generating prompt
                                                        # This prevents the clarification prompt from being treated as a new user message
                                                        return {
                                                            "response": result_data.get("quick_actions", {}).get("message", "What would you like?"),
                                                            "quick_actions": result_data.get("quick_actions", {}).get("quick_actions", []),
                                                            "needs_clarification": True
                                                        }

                                                if tool_result.get("success"):
                                                    tool_results[tool_name] = tool_result.get("result", {})
                                                    product_count = len(tool_result.get("result", {}).get('products', [])) if isinstance(tool_result.get("result"), dict) else 0
                                                    logger.info(f"Tool '{tool_name}' returned {product_count} products")
                                                else:
                                                    logger.error(f"Tool '{tool_name}' failed: {tool_result.get('error')}")
                                                    tool_results[tool_name] = {"products": [], "error": tool_result.get("error")}

                                        # Inject tool results into template variables
                                        if 'result_injection' in tool_config and tool_results:
                                            for tool_name, variable_name in tool_config['result_injection'].items():
                                                if tool_name in tool_results:
                                                    # Format tool results for template injection
                                                    result_data = tool_results[tool_name]
                                                    if 'products' in result_data:
                                                        formatted_results = self._format_products_for_template(result_data['products'])

                                                        # Debug: Check before replacement
                                                        placeholder = f"{{{variable_name}}}"
                                                        before_exists = placeholder in final_prompt
                                                        logger.info(f"BEFORE replacement: placeholder '{placeholder}' exists in prompt: {before_exists}")
                                                        logger.info(f"Formatted results to inject ({len(formatted_results)} chars): {formatted_results[:300]}...")

                                                        # Re-apply template with tool results
                                                        final_prompt = final_prompt.replace(placeholder, formatted_results)

                                                        # Debug: Check after replacement
                                                        after_exists = placeholder in final_prompt
                                                        logger.info(f"AFTER replacement: placeholder '{placeholder}' still exists: {after_exists}")
                                                        logger.info(f"Injected {len(result_data['products'])} products into template variable '{variable_name}'")
                                                        logger.info(f"Final prompt after injection (first 1500 chars): {final_prompt[:1500]}")
                                else:
                                    logger.info(f"Template '{detected_type}' has no tools")

                                logger.info(f"Applied detected template '{detected_type}'")
                    except ValueError as e:
                        logger.error(f"Failed to apply detected template: {e}")
                elif self.get_prompt_template('default'):
                    # Use default template for unmatched or failed detection
                    try:
                        template_applied, template_config = self.apply_prompt_template_with_config(prompt, 'default')
                        if template_applied and template_applied != prompt:
                            final_prompt = template_applied
                            used_template = 'default'
                            if isinstance(template_config, dict):
                                template_max_tokens = template_config.get('max_tokens') or (self.system_config.get('default_max_tokens') if self.system_config else None)
                                template_stop_sequences = template_config.get('stop_sequences', [])
                            logger.info(f"Applied default template")
                    except ValueError as e:
                        logger.error(f"Failed to apply default template: {e}")
                else:
                    # Default to general conversation if available
                    if self.get_prompt_template('general_conversation'):
                        final_prompt = self.apply_prompt_template(prompt, 'general_conversation')
                        used_template = 'general_conversation'
            
            # If system config is loaded but no prompts applied, add system instruction
            if self.system_config and not used_template:
                system_instruction = self._get_system_instruction()
                if system_instruction:
                    # Get format from config
                    if self.system_config and 'prompt_format' in self.system_config:
                        final_prompt = self.system_config['prompt_format'].format(system=system_instruction, user=prompt)
                    else:
                        final_prompt = prompt
            
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
                # Get stop sequences from config
                stop_sequences = self.system_config.get('default_stop_sequences', []) if self.system_config else []
            
            # Log generation parameters for debugging
            logger.info(f"Generating with max_tokens={final_max_tokens}, temp={actual_temperature:.2f}, stops={len(stop_sequences)}")
            logger.debug(f"Final prompt preview: {final_prompt[:100]}...")
            
            # Debug timing for model inference
            inference_start = time.time()

            # Check if model is loaded
            if not self.current_model:
                logger.error("No model loaded! Cannot generate response.")
                return {
                    "text": "I apologize, but the AI model is not currently loaded. Please try again later.",
                    "model": "none",
                    "error": "Model not loaded"
                }

            logger.info(f"Starting model inference with {self.current_model_name or 'cloud provider'}")

            # HOT-SWAP: Choose between local and cloud inference
            if self.use_cloud_inference and self.llm_router:
                # Cloud inference via LLM Router
                logger.info("🌐 Using cloud inference (LLM Router)")

                try:
                    # Import types for cloud routing
                    from services.llm_gateway import RequestContext, TaskType

                    # Map detected intent to task type
                    task_type = TaskType.CHAT  # default
                    if 'intent_result' in locals() and isinstance(intent_result, dict):
                        intent = intent_result.get('intent', 'general')
                        if intent in ['product_search', 'product_recommendation']:
                            task_type = TaskType.REASONING
                        elif intent in ['dosage', 'medical_advice']:
                            task_type = TaskType.REASONING
                        else:
                            task_type = TaskType.CHAT

                    # Create routing context
                    context = RequestContext(
                        task_type=task_type,
                        estimated_tokens=final_max_tokens,
                        requires_speed=(response_style == 'conversational')
                    )

                    # Route to cloud provider
                    # Convert to OpenAI message format with system prompt if available
                    messages = []

                    # Build comprehensive system message
                    system_content_parts = []

                    # 1. Add system prompt from agent configuration if available
                    if self.agent_prompts and 'system_prompt' in self.agent_prompts:
                        system_prompt_config = self.agent_prompts['system_prompt']
                        system_prompt_text = system_prompt_config.get('template', '') if isinstance(system_prompt_config, dict) else system_prompt_config
                        if system_prompt_text:
                            system_content_parts.append(system_prompt_text)
                            logger.info(f"Added agent system prompt ({len(system_prompt_text)} chars)")

                    # 2. Add template context if a specific prompt type was used
                    if used_template and used_template in self.agent_prompts:
                        template_config = self.agent_prompts[used_template]
                        template_text = template_config.get('template', '') if isinstance(template_config, dict) else template_config
                        if template_text and used_template != 'system_prompt':
                            # Add template as reference/guidance, not as the response
                            system_content_parts.append(f"\nWhen responding to this type of query ({used_template}), use this information as reference:\n{template_text}")
                            logger.info(f"Added template guidance for '{used_template}' ({len(template_text)} chars)")

                    # Combine system content
                    if system_content_parts:
                        messages.append({"role": "system", "content": "\n\n".join(system_content_parts)})

                    # Add user message (use original prompt, not template-applied)
                    # For cloud inference, we want the actual user question, not the template
                    user_message = original_user_message if 'original_user_message' in locals() else prompt
                    messages.append({"role": "user", "content": user_message})
                    
                    # Log message sizes safely
                    system_msg_len = len(messages[0]['content']) if messages and messages[0]['role'] == 'system' else 0
                    logger.info(f"Cloud inference: System message {system_msg_len} chars, User message: {len(user_message)} chars")

                    result = await self.llm_router.complete(messages, context)

                    # Convert router response to V5 format
                    response = {
                        "choices": [{
                            "text": result.content,
                            "finish_reason": result.finish_reason
                        }],
                        "usage": {
                            "prompt_tokens": result.tokens_input,
                            "completion_tokens": result.tokens_output,
                            "total_tokens": result.tokens_input + result.tokens_output
                        },
                        "model": result.model,
                        "provider": result.provider,
                        "cloud_inference": True
                    }

                    logger.info(f"✅ Cloud inference complete: {result.provider} ({result.latency:.2f}s)")

                except Exception as e:
                    logger.error(f"Cloud inference failed: {e}, falling back to local")
                    # Fallback to local if cloud fails
                    if not self.current_model:
                        raise Exception("No local model loaded and cloud inference failed")

                    response = self.current_model(
                        final_prompt,
                        max_tokens=final_max_tokens,
                        temperature=actual_temperature,
                        top_p=actual_top_p,
                        top_k=top_k,
                        echo=False,
                        stop=stop_sequences[:8],
                        stream=False,
                        repeat_penalty=self.get_config_repeat_penalty()
                    )

            else:
                # Local inference via llama-cpp
                logger.info("💻 Using local inference (llama-cpp)")

                if not self.current_model:
                    logger.error("No model loaded! Cannot generate response.")
                    return {
                        "text": "I apologize, but the AI model is not currently loaded. Please try again later.",
                        "model": "none",
                        "error": "Model not loaded"
                    }

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
                    repeat_penalty=self.get_config_repeat_penalty()  # Use config value
                )

            inference_time = time.time() - inference_start
            timing_breakdown['model_inference'] = inference_time
            logger.info(f"Model inference completed in {inference_time:.2f}s")

            elapsed_ms = (time.time() - start_time) * 1000

            # Log complete timing breakdown
            parallel_note = " (PARALLEL)" if timing_breakdown.get('intent_detection_started', False) else ""
            logger.info(f"generate() timing breakdown - Total: {elapsed_ms:.0f}ms | Intent{parallel_note}: {timing_breakdown.get('intent_detection', 0)*1000:.0f}ms | Inference: {timing_breakdown.get('model_inference', 0)*1000:.0f}ms")
            
            # Ensure response is a dict
            if isinstance(response, str):
                # If response is a string, wrap it in proper dict format
                response = {
                    "choices": [{"text": response}]
                }
            
            if response and isinstance(response, dict) and response.get("choices"):
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

                # Extract products and generate quick actions if tool results exist
                products_array = []
                quick_actions = []

                if 'tool_results' in locals() and tool_results:
                    # Extract products from smart_product_search results
                    for tool_name, result_data in tool_results.items():
                        if tool_name == 'smart_product_search' and isinstance(result_data, dict):
                            products_array = result_data.get('products', [])
                            logger.info(f"Adding {len(products_array)} products to response")

                            # Generate quick actions based on product categories
                            quick_actions = self._generate_quick_actions(products_array)
                            logger.info(f"Generated {len(quick_actions)} quick actions")
                            break

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
                    "products": products_array,
                    "quick_actions": quick_actions,
                    "detected_intent": intent_result.get('intent') if isinstance(intent_result, dict) and 'intent_result' in locals() else None,
                    "intent_confidence": intent_result.get('confidence') if isinstance(intent_result, dict) and 'intent_result' in locals() else None,
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
            import traceback
            logger.error(f"Generation error: {e}")
            logger.error(f"Error traceback: {traceback.format_exc()}")
            return {
                "error": str(e),
                "text": "",
                "model": self.current_model_name,
                "time_ms": 0,
                "used_prompt": self.use_prompts
            }
    
    async def generate_async(self,
                 prompt: str,
                 prompt_type: Optional[str] = None,
                 max_tokens: int = None,
                 temperature: float = None,
                 top_p: float = None,
                 top_k: int = 40,
                 use_tools: bool = False,
                 use_context: bool = False,
                 session_id: Optional[str] = None) -> Dict:
        """Async version of generate with proper parallel intent detection"""
        start_time = time.time()
        timing_breakdown = {}

        if not self.current_model:
            return {"error": "No model loaded", "text": "", "model": "none"}

        try:
            # Get config values if not specified
            if temperature is None:
                temperature = self.get_config_temperature()
            if top_p is None:
                top_p = self.get_config_top_p()
            if max_tokens is None:
                max_tokens = self.get_config_max_tokens()

            # Initialize variables
            final_prompt = prompt
            used_template = None
            template_max_tokens = None
            template_stop_sequences = []
            detected_intent = None

            # Add context if requested
            if use_context:
                context_start = time.time()
                final_prompt = self._add_context_to_prompt(prompt, session_id)
                timing_breakdown['add_context'] = time.time() - context_start

            # Handle prompt templates
            if prompt_type and self.use_prompts:
                # User specified a prompt type - use it directly
                try:
                    template_applied, template_config = self.apply_prompt_template_with_config(prompt, prompt_type)
                    if template_applied and template_applied != prompt:
                        final_prompt = template_applied
                        used_template = prompt_type
                        if isinstance(template_config, dict):
                            template_max_tokens = template_config.get('max_tokens')
                            template_stop_sequences = template_config.get('stop_sequences', [])
                except ValueError as e:
                    logger.error(f"Failed to apply template: {e}")

            elif self.use_prompts and not prompt_type:
                # SERIAL ASYNC EXECUTION: Detect intent first, then apply template
                detected_type = None
                logger.info(f"Async intent detection path: use_prompts={self.use_prompts}, intent_detector={self.intent_detector is not None}")

                # Run intent detection serially if available
                if self.intent_detector:
                    intent_detect_start = time.time()
                    try:
                        # Run async intent detection serially
                        intent_result = await self.detect_intent_async(prompt)
                        timing_breakdown['intent_detection'] = time.time() - intent_detect_start
                        logger.info(f"Serial async intent detection completed: {intent_result} (took {timing_breakdown['intent_detection']:.2f}s)")
                        # Extract the prompt_type from the intent result
                        if isinstance(intent_result, dict):
                            detected_type = intent_result.get('prompt_type') or intent_result.get('intent')
                        else:
                            detected_type = intent_result
                    except Exception as e:
                        logger.warning(f"Async intent detection failed: {e}")
                        detected_type = None
                else:
                    logger.warning("Intent detector not available in async, skipping intent detection")

                # Apply template based on detected intent or use default
                if detected_type and self.get_prompt_template(detected_type):
                    try:
                        template_applied, template_config = self.apply_prompt_template_with_config(prompt, detected_type)
                        logger.info(f"🔍 Template result - Original: '{prompt[:50]}...' Applied: '{template_applied[:100]}...'")
                        if template_applied and template_applied != prompt:
                            final_prompt = template_applied
                            used_template = detected_type
                            if isinstance(template_config, dict):
                                template_max_tokens = template_config.get('max_tokens')
                                template_stop_sequences = template_config.get('stop_sequences', [])
                            logger.info(f"Applied detected template '{detected_type}'")
                        else:
                            logger.warning(f"⚠️ Template not applied or same as original - detected_type: {detected_type}")
                    except Exception as e:
                        logger.error(f"Failed to apply detected template: {e}")
                elif self.get_prompt_template('default'):
                    # Use default template for unmatched or failed detection
                    try:
                        template_applied, template_config = self.apply_prompt_template_with_config(prompt, 'default')
                        if template_applied and template_applied != prompt:
                            final_prompt = template_applied
                            used_template = 'default'
                            if isinstance(template_config, dict):
                                template_max_tokens = template_config.get('max_tokens')
                                template_stop_sequences = template_config.get('stop_sequences', [])
                            logger.info("Applied default template")
                    except Exception as e:
                        logger.error(f"Failed to apply default template: {e}")

            # Apply system config if no template used
            if self.system_config and not used_template:
                system_instruction = self._get_system_instruction()
                if system_instruction and 'prompt_format' in self.system_config:
                    final_prompt = self.system_config['prompt_format'].format(
                        system=system_instruction, user=prompt
                    )

            # Determine response style
            response_style = None
            if self.system_config and 'system' in self.system_config:
                response_style = self.system_config['system'].get('default_behavior', {}).get('response_style', 'conversational')

            # Adjust parameters based on response style
            if response_style == 'conversational':
                actual_temperature = min(temperature + 0.1, 1.0)
                actual_top_p = top_p
            elif response_style == 'formal':
                actual_temperature = max(temperature - 0.2, 0.1)
                actual_top_p = max(top_p - 0.1, 0.8)
            else:
                actual_temperature = temperature
                actual_top_p = top_p

            # Use template max_tokens if specified
            final_max_tokens = template_max_tokens if template_max_tokens else max_tokens

            # Get stop sequences
            stop_sequences = template_stop_sequences if template_stop_sequences else \
                            self.system_config.get('default_stop_sequences', []) if self.system_config else []

            # Log parameters
            logger.info(f"Generating async with max_tokens={final_max_tokens}, temp={actual_temperature:.2f}")

            # Run model inference in executor to avoid blocking
            inference_start = time.time()
            loop = asyncio.get_event_loop()

            # Run the blocking model call in executor
            response = await loop.run_in_executor(
                None,
                lambda: self.current_model(
                    final_prompt,
                    max_tokens=final_max_tokens,
                    temperature=actual_temperature,
                    top_p=actual_top_p,
                    top_k=top_k,
                    echo=False,
                    stop=stop_sequences[:8],
                    stream=False,
                    repeat_penalty=self.get_config_repeat_penalty()
                )
            )

            inference_time = time.time() - inference_start
            timing_breakdown['model_inference'] = inference_time
            logger.info(f"Async model inference completed in {inference_time:.2f}s")

            elapsed_ms = (time.time() - start_time) * 1000

            # Log timing breakdown
            parallel_note = " (ASYNC)" if timing_breakdown.get('intent_detection_started', False) else ""
            logger.info(f"generate_async() timing - Total: {elapsed_ms:.0f}ms | Intent{parallel_note}: {timing_breakdown.get('intent_detection', 0)*1000:.0f}ms | Inference: {timing_breakdown.get('model_inference', 0)*1000:.0f}ms")

            # Process response
            if isinstance(response, str):
                response = {"choices": [{"text": response}]}

            if response and isinstance(response, dict) and response.get("choices"):
                text = response["choices"][0].get("text", "")

                # Apply safety guidelines
                text = self.apply_safety_guidelines(prompt, text)

                # Calculate metrics
                completion_tokens = response.get("usage", {}).get("completion_tokens", 0)
                tokens_per_sec = completion_tokens / (elapsed_ms / 1000) if elapsed_ms > 0 else 0

                return {
                    "text": text,
                    "model": self.current_model_name,
                    "time_ms": round(elapsed_ms),
                    "tokens": completion_tokens,
                    "tokens_per_sec": round(tokens_per_sec, 1),
                    "used_prompt": self.use_prompts,
                    "prompt_template": used_template,
                    "detected_intent": detected_intent.get('intent') if detected_intent else None,
                    "async_generation": True,
                    "error": None
                }
            else:
                return {
                    "error": "No response from model",
                    "text": "",
                    "model": self.current_model_name,
                    "time_ms": round(elapsed_ms),
                    "async_generation": True
                }

        except Exception as e:
            logger.error(f"Async generation error: {e}")
            return {
                "error": str(e),
                "text": "",
                "model": self.current_model_name,
                "time_ms": 0,
                "async_generation": True
            }

    async def generate_with_context(
        self,
        message: str,
        context: Dict[str, Any],
        max_tokens: int = None,
        temperature: float = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate response with specific context (used by agent pool)"""
        if not self.current_model:
            return {
                "error": "No model loaded",
                "text": "",
                "model": None
            }

        try:
            # Prepare prompt with context
            system_prompt = context.get("system_prompt", "")
            traits = context.get("traits", {})
            style = context.get("style", {})
            history = context.get("history", [])

            # Build full prompt with personality context
            full_prompt = ""
            if system_prompt:
                full_prompt = f"System: {system_prompt}\n\n"

            # Add conversation history
            if history:
                full_prompt += "Previous conversation:\n"
                for h in history[-5:]:  # Last 5 exchanges
                    if "user" in h:
                        full_prompt += f"User: {h['user']}\n"
                    if "assistant" in h:
                        full_prompt += f"Assistant: {h['assistant']}\n"
                full_prompt += "\n"

            # Add current message
            full_prompt += f"User: {message}\nAssistant:"

            # Apply style settings
            if temperature is None:
                temperature = style.get("temperature", 0.7)
            if max_tokens is None:
                max_tokens = style.get("max_tokens", 512)

            # Generate response
            response = self.generate(
                prompt=full_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )

            return response

        except Exception as e:
            logger.error(f"Error in generate_with_context: {e}")
            return {
                "error": str(e),
                "text": "",
                "model": self.current_model_name
            }

    async def get_user_context(self, user_id: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Fetch user context from the UserContextService"""
        try:
            logger.info(f"[SmartAIEngineV5] get_user_context starting - User ID: {user_id}, Session ID: {session_id}")

            # Import here to avoid circular dependencies
            from services.user_context_service import UserContextService
            import asyncpg
            import os

            # Create a database connection
            db_config = {
                'host': os.getenv('DB_HOST', 'localhost'),
                'port': int(os.getenv('DB_PORT', 5434)),
                'database': os.getenv('DB_NAME', 'ai_engine'),
                'user': os.getenv('DB_USER', 'weedgo'),
                'password': os.getenv('DB_PASSWORD', 'weedgo123')
            }
            logger.info(f"[SmartAIEngineV5] Connecting to database at {db_config['host']}:{db_config['port']}/{db_config['database']}")

            conn = await asyncpg.connect(**db_config)
            
            try:
                logger.info(f"[SmartAIEngineV5] Database connected, creating UserContextService")
                context_service = UserContextService(conn)

                logger.info(f"[SmartAIEngineV5] Fetching complete user context")
                user_context = await context_service.get_complete_user_context(user_id, session_id)

                logger.info(f"[SmartAIEngineV5] User context retrieved - Has profile: {bool(user_context.get('user_profile'))}, "
                           f"Purchase count: {len(user_context.get('recent_purchases', []))}, "
                           f"Chat history count: {len(user_context.get('conversation_context', {}).get('messages', []))}")

                return user_context
            finally:
                await conn.close()
                logger.info(f"[SmartAIEngineV5] Database connection closed")
                
        except Exception as e:
            logger.error(f"[SmartAIEngineV5] Error getting user context: {str(e)}")
            logger.exception("[SmartAIEngineV5] Full stack trace:")
            return {}
    
    async def get_response_async(self, message: str, session_id: Optional[str] = None,
                    user_id: Optional[str] = None, max_tokens: int = 500,
                    include_context: bool = True) -> str:
        """
        Async version of get_response for better performance
        """
        try:
            # Debug timing
            timing_start = time.time()
            timing_points = {}

            # Build context-aware prompt if user_id is provided
            context_prompt = message

            if include_context and user_id:
                # Use proper async call
                context_start = time.time()
                user_context = await self.get_user_context(user_id, session_id)
                timing_points['user_context'] = time.time() - context_start

                if user_context and user_context.get('user_profile'):
                    # Build context-aware prompt (same as before)
                    context_parts = []

                    # Add user profile info
                    profile = user_context['user_profile']
                    if profile:
                        context_parts.append(f"User: {profile.get('first_name', '')} {profile.get('last_name', '')}")
                        if profile.get('age_verified'):
                            context_parts.append("Age verified: 21+")

                    # Add order history if available
                    if user_context.get('order_history'):
                        context_parts.append(f"Previous orders: {len(user_context['order_history'])}")

                    # Add preferences if available
                    if user_context.get('preferences'):
                        prefs = user_context['preferences']
                        if prefs:
                            context_parts.append(f"Preferences: {prefs}")

                    # Build final context prompt
                    context_prompt = f"""
User Context:
{chr(10).join(context_parts)}

Current message: {message}

Please provide a personalized response based on the user's history and preferences."""

            # Generate response using the async generate method
            generate_start = time.time()
            result = await self.generate_async(
                prompt=context_prompt,
                max_tokens=max_tokens,
                use_context=True,
                session_id=session_id
            )
            timing_points['generate'] = time.time() - generate_start

            # Log timing breakdown
            total_time = time.time() - timing_start
            logger.info(f"get_response_async timing - Total: {total_time:.3f}s | Context: {timing_points.get('user_context', 0):.3f}s | Generate: {timing_points.get('generate', 0):.3f}s")

            # Extract just the text from the result
            if isinstance(result, dict):
                return result.get('text', 'I apologize, but I encountered an error processing your request.')
            else:
                return str(result)

        except Exception as e:
            logger.error(f"Error in get_response_async: {str(e)}")
            return "I apologize, but I'm having trouble processing your request. Please try again."

    def get_response(self, message: str, session_id: Optional[str] = None,
                    user_id: Optional[str] = None, max_tokens: int = 500,
                    include_context: bool = True) -> str:
        """
        Simple wrapper around generate() for backward compatibility
        This is the method called by chat endpoints
        """
        try:
            # Log entry point
            logger.info(f"[SmartAIEngineV5] get_response called - User ID: {user_id}, Session ID: {session_id}, Include context: {include_context}")

            # Debug timing
            timing_start = time.time()
            timing_points = {}

            # Build context-aware prompt if user_id is provided
            context_prompt = message

            if include_context and user_id:
                logger.info(f"[SmartAIEngineV5] Fetching user context for user_id: {user_id}")
                # Try to get user context (sync wrapper for async function)
                context_start = time.time()
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                user_context = loop.run_until_complete(self.get_user_context(user_id, session_id))
                timing_points['user_context'] = time.time() - context_start

                logger.info(f"[SmartAIEngineV5] User context fetched in {timing_points['user_context']:.3f}s - Has profile: {bool(user_context and user_context.get('user_profile'))}")

                if user_context and user_context.get('user_profile'):
                    # Build context-aware prompt
                    context_parts = []
                    
                    # Add user profile info
                    profile = user_context['user_profile']
                    if profile:
                        context_parts.append(f"User: {profile.get('first_name', '')} {profile.get('last_name', '')}")
                        if profile.get('age_verified'):
                            context_parts.append("Age verified: Yes")
                        if profile.get('loyalty_points'):
                            context_parts.append(f"Loyalty points: {profile['loyalty_points']}")
                    
                    # Add recent purchase context
                    if user_context.get('recent_purchases'):
                        recent_items = []
                        for order in user_context['recent_purchases'][:3]:
                            if order.get('items'):
                                for item in order['items'][:2]:
                                    recent_items.append(item.get('product_name', 'Unknown'))
                        if recent_items:
                            context_parts.append(f"Recent purchases: {', '.join(recent_items[:5])}")
                    
                    # Add preferences
                    if user_context.get('preferences', {}).get('frequent_items'):
                        fav_products = [item['product_name'] for item in user_context['preferences']['frequent_items'][:3]]
                        if fav_products:
                            context_parts.append(f"Favorite products: {', '.join(fav_products)}")
                    
                    # Add conversation context
                    if user_context.get('conversation_context', {}).get('messages'):
                        # Include last few messages for context continuity
                        recent_msgs = user_context['conversation_context']['messages'][-4:]
                        if recent_msgs:
                            context_parts.append("Recent conversation:")
                            for msg in recent_msgs:
                                role = msg.get('role', 'user')
                                content = msg.get('content', '')[:100]
                                context_parts.append(f"{role}: {content}")
                    
                    if context_parts:
                        context_info = "\n".join(context_parts)
                        logger.info(f"[SmartAIEngineV5] Context built with {len(context_parts)} parts")
                        logger.debug(f"[SmartAIEngineV5] Context details: {context_info[:200]}...")
                        context_prompt = f"""Context about the user:
{context_info}

Current message: {message}

Please provide a personalized response based on the user's history and preferences."""
            
            # Generate response using the existing generate method
            logger.info(f"[SmartAIEngineV5] Sending prompt to LLM with context: {bool(user_id and include_context)}")
            logger.debug(f"[SmartAIEngineV5] Full prompt being sent to LLM:\n{context_prompt[:500]}...")

            generate_start = time.time()
            result = self.generate(
                prompt=context_prompt,
                max_tokens=max_tokens,
                use_context=True,
                session_id=session_id
            )
            timing_points['generate'] = time.time() - generate_start

            # Log timing breakdown
            total_time = time.time() - timing_start
            logger.info(f"get_response timing - Total: {total_time:.3f}s | Context: {timing_points.get('user_context', 0):.3f}s | Generate: {timing_points.get('generate', 0):.3f}s")

            # Extract just the text from the result
            if isinstance(result, dict):
                return result.get('text', 'I apologize, but I encountered an error processing your request.')
            else:
                return str(result)
                
        except Exception as e:
            logger.error(f"Error in get_response: {str(e)}")
            return "I apologize, but I'm having trouble processing your request. Please try again."
    
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
            # Get test prompts from config or use minimal defaults
            test_prompts = []
            if self.system_config and 'test_prompts' in self.system_config:
                test_prompts = self.system_config['test_prompts']
            else:
                # No fallback - tests require config
                test_prompts = []
        
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
                # Check configured greeting keywords for benchmarking
                greeting_keywords = self.system_config.get('greeting_keywords', []) if self.system_config else []
                if greeting_keywords and any(word in prompt.lower() for word in greeting_keywords):
                    prompt_type = 'greeting_detection'
                search_keywords = self.system_config.get('search_keywords', []) if self.system_config else []
                if search_keywords and any(word in prompt.lower() for word in search_keywords):
                    prompt_type = 'search_extraction_enhanced'
            
            # Get max tokens from config
            max_tokens = self.system_config.get('benchmark_max_tokens') if self.system_config else None
            result = self.generate(prompt, prompt_type=prompt_type, max_tokens=max_tokens)
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
    
    async def process_message(
        self, 
        message: str, 
        context: Dict[str, Any] = None,
        session_id: str = None
    ) -> Dict[str, Any]:
        """
        Process a message with full V5 features
        
        Args:
            message: The user message
            context: Additional context (user_id, role, etc.)
            session_id: Session identifier
            
        Returns:
            Response dict with response, tools_used, confidence, metadata
        """
        try:
            # Apply agent personality and context
            prompt = self.apply_prompt_template(message, "chat")
            
            # Add session context if available
            if session_id and self.context_manager:
                prompt = self._add_context_to_prompt(prompt, session_id)
            
            # Generate response
            result = self.generate(
                prompt,
                max_tokens=500,
                temperature=0.7,
                session_id=session_id
            )
            
            # Extract tool calls and execute them
            tool_calls = self._extract_tool_calls(result['text'])
            tools_used = []
            
            if tool_calls and self.tool_manager:
                tool_results = await self._execute_tool_calls(tool_calls)
                result['text'] = tool_results
                tools_used = [tc.get('tool') for tc in tool_calls]
            
            # Apply safety guidelines
            final_response = self.apply_safety_guidelines(prompt, result['text'])
            
            # Store in conversation history if context manager available
            if session_id and self.context_manager:
                self.context_manager.add_to_history(
                    session_id,
                    {"role": "user", "content": message},
                    {"role": "assistant", "content": final_response}
                )
            
            return {
                'response': final_response,
                'tools_used': tools_used,
                'confidence': result.get('confidence'),
                'metadata': {
                    'tokens_generated': result.get('num_tokens'),
                    'time_ms': result.get('time_ms'),
                    'session_id': session_id
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {
                'response': "I apologize, I encountered an error processing your request.",
                'error': str(e)
            }
    
    async def stream_response(
        self,
        message: str,
        context: Dict[str, Any] = None,
        session_id: str = None
    ):
        """
        Stream response tokens for real-time output
        
        Args:
            message: User message
            context: Additional context
            session_id: Session identifier
            
        Yields:
            Response tokens as they're generated
        """
        try:
            # Apply prompt template
            prompt = self.apply_prompt_template(message, "chat")
            
            # Add session context
            if session_id and self.context_manager:
                prompt = self._add_context_to_prompt(prompt, session_id)
            
            # Stream tokens from model
            if hasattr(self.current_model, 'create_completion'):
                # For llama.cpp models
                stream = self.current_model.create_completion(
                    prompt,
                    max_tokens=500,
                    temperature=0.7,
                    stream=True
                )
                
                full_response = ""
                for output in stream:
                    token = output.get('choices', [{}])[0].get('text', '')
                    if token:
                        full_response += token
                        yield token
                
                # Store in history
                if session_id and self.context_manager:
                    self.context_manager.add_to_history(
                        session_id,
                        {"role": "user", "content": message},
                        {"role": "assistant", "content": full_response}
                    )
            else:
                # Fallback for non-streaming models
                result = await self.process_message(message, context, session_id)
                for char in result['response']:
                    yield char
                    await asyncio.sleep(0.01)  # Simulate streaming
                    
        except Exception as e:
            logger.error(f"Error in stream_response: {e}")
            yield f"Error: {str(e)}"
    
    def enable_cloud_inference(self):
        """Enable cloud inference (hot-swap to cloud providers)"""
        if not self.llm_router:
            logger.warning("LLM Router not initialized, cannot enable cloud inference")
            return False

        self.use_cloud_inference = True
        provider_count = len(self.llm_router.list_providers())
        logger.info(f"🌐 Cloud inference ENABLED (hot-swap active, {provider_count} providers)")
        return True

    def disable_cloud_inference(self):
        """Disable cloud inference (hot-swap back to local)"""
        self.use_cloud_inference = False
        logger.info("💻 Cloud inference DISABLED (using local model)")
        return True

    def toggle_cloud_inference(self):
        """Toggle between cloud and local inference"""
        if self.use_cloud_inference:
            return self.disable_cloud_inference()
        else:
            return self.enable_cloud_inference()

    def get_router_stats(self) -> Dict[str, Any]:
        """Get LLM Router statistics"""
        if not self.llm_router:
            return {
                "enabled": False,
                "error": "LLM Router not initialized"
            }

        stats = self.llm_router.get_stats()
        return {
            "enabled": True,
            "active": self.use_cloud_inference,
            "providers": self.llm_router.list_providers(),
            "stats": stats
        }

    def cleanup(self):
        """Cleanup resources on shutdown"""
        try:
            # Clear model from memory if needed
            if hasattr(self, 'current_model'):
                del self.current_model
                self.current_model = None
            
            # Clear tool manager
            if hasattr(self, 'tool_manager'):
                self.tool_manager = None
            
            # Clear context manager  
            if hasattr(self, 'context_manager'):
                self.context_manager = None
                
            logger.info("V5 engine cleaned up successfully")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

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