"""
Agent Pool Manager - Hybrid Architecture for Multiple Agents/Personalities
Implements shared model with multiple personality configurations
"""

import os
import json
import logging
import asyncio
import re
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from collections import OrderedDict
import psutil

# Import intent detection and tools
from services.intent_detector import LLMIntentDetector
from services.tools.product_search_tool import ProductSearchTool
from services.tool_manager import ToolManager

logger = logging.getLogger(__name__)


@dataclass
class PersonalityConfig:
    """Lightweight personality configuration"""
    agent_id: str
    personality_id: str
    name: str
    traits: Dict[str, Any] = field(default_factory=dict)
    prompts: Dict[str, str] = field(default_factory=dict)
    system_prompt: str = ""
    greeting: str = ""
    style: Dict[str, Any] = field(default_factory=dict)
    knowledge_domains: List[str] = field(default_factory=list)
    behavioral_rules: List[str] = field(default_factory=list)
    loaded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def get_context(self) -> Dict[str, Any]:
        """Get personality context for model inference"""
        return {
            "system_prompt": self.system_prompt,
            "traits": self.traits,
            "style": self.style,
            "greeting": self.greeting,
            "knowledge_domains": self.knowledge_domains,
            "behavioral_rules": self.behavioral_rules
        }


@dataclass
class AgentConfig:
    """Agent configuration with multiple personalities"""
    agent_id: str
    name: str
    description: str
    capabilities: List[str] = field(default_factory=list)
    personalities: Dict[str, PersonalityConfig] = field(default_factory=dict)
    default_personality: str = ""
    intent_patterns: Dict[str, Any] = field(default_factory=dict)
    tools: List[str] = field(default_factory=list)

    # Intent detection and prompt templates
    intent_detector: Optional[Any] = None
    prompt_templates: Dict[str, Any] = field(default_factory=dict)
    intent_config: Dict[str, Any] = field(default_factory=dict)

    # Tools
    tool_manager: Optional[Any] = None
    product_search_tool: Optional[Any] = None

    def add_personality(self, personality: PersonalityConfig):
        """Add a personality to this agent"""
        self.personalities[personality.personality_id] = personality
        if not self.default_personality:
            self.default_personality = personality.personality_id


@dataclass
class SessionState:
    """Active session state"""
    session_id: str
    agent_id: str
    personality_id: str
    user_id: Optional[str] = None
    context_history: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_activity: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)
    signup_state: Dict[str, Any] = field(default_factory=dict)  # Track signup flow state

    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.now(timezone.utc)


class AgentPoolManager:
    """
    Manages multiple agents with shared model and personality switching
    Implements industry best practices for resource management
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the agent pool manager"""
        self.config = config or {}

        # Resource management
        self.max_memory_gb = self.config.get("max_memory_gb", 4)
        self.enable_hot_swap = self.config.get("enable_hot_swap", True)
        self.cache_personalities = self.config.get("cache_personalities", True)

        # Agent and personality storage
        self.agents: Dict[str, AgentConfig] = {}
        self.personality_cache: OrderedDict[Tuple[str, str], PersonalityConfig] = OrderedDict()
        self.max_cache_size = self.config.get("max_cache_size", 20)

        # Session management
        self.sessions: Dict[str, SessionState] = {}
        self.max_sessions = self.config.get("max_sessions", 1000)

        # Shared model reference (will be set by SmartAIEngine)
        self.shared_model = None

        # Tool manager reference (will be set by SmartAIEngine)
        self.tool_manager = None

        # Performance metrics
        self.metrics = {
            "total_requests": 0,
            "personality_switches": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "active_sessions": 0
        }

        # Load configurations
        self._load_agent_configs()

    def _load_agent_configs(self):
        """Load all agent and personality configurations"""
        base_path = Path("prompts/agents")

        if not base_path.exists():
            logger.warning(f"Agents directory not found: {base_path}")
            return

        # Scan for agents
        for agent_dir in base_path.iterdir():
            if agent_dir.is_dir():
                agent_id = agent_dir.name
                logger.info(f"Loading agent: {agent_id}")

                # Load agent config
                agent_config = self._load_agent_config(agent_dir)
                if agent_config:
                    self.agents[agent_id] = agent_config

                    # Load personalities for this agent from personality/ folder (not personalities/)
                    personality_dir = agent_dir / "personality"
                    if personality_dir.exists():
                        # Load each .json file as a personality
                        for personality_file in personality_dir.glob("*.json"):
                            personality_id = personality_file.stem  # filename without extension
                            personality = self._load_personality_from_file(
                                agent_id, personality_id, personality_file
                            )
                            if personality:
                                agent_config.add_personality(personality)
                                logger.info(f"  - Loaded personality: {personality_id}")

        logger.info(f"Loaded {len(self.agents)} agents with personalities")

    def _load_agent_config(self, agent_dir: Path) -> Optional[AgentConfig]:
        """Load agent configuration from directory"""
        config_file = agent_dir / "config.json"
        if not config_file.exists():
            logger.warning(f"❌ config.json not found for agent {agent_dir.name}")
            return None

        try:
            logger.info(f"📁 Loading config.json for agent {agent_dir.name}")
            with open(config_file, 'r') as f:
                data = json.load(f)
            logger.info(f"  ✅ config.json loaded successfully")

            # Load intent patterns if available
            intent_file = agent_dir / "intent.json"
            intent_patterns = {}
            if intent_file.exists():
                logger.info(f"📁 Loading intent.json for agent {agent_dir.name}")
                with open(intent_file, 'r') as f:
                    intent_patterns = json.load(f)
                logger.info(f"  ✅ intent.json loaded: {len(intent_patterns.get('intents', {}))} intents defined")
                logger.info(f"     Available intents: {list(intent_patterns.get('intents', {}).keys())}")
            else:
                logger.warning(f"  ❌ intent.json not found at {intent_file}")

            agent_config = AgentConfig(
                agent_id=agent_dir.name,
                name=data.get("agent_name", agent_dir.name),
                description=data.get("description", ""),
                capabilities=data.get("capabilities", []),
                intent_patterns=intent_patterns,
                tools=data.get("enrolled_tools", []),
                default_personality=data.get("default_personality", "")
            )

            # Initialize intent detection system
            try:
                agent_config.intent_detector = LLMIntentDetector(cache_size=1000)
                success = agent_config.intent_detector.load_intents(agent_dir.name)
                if success:
                    logger.info(f"  ✅ Intent detector initialized successfully for {agent_dir.name}")
                else:
                    logger.warning(f"  ⚠️ Intent detector initialized but intent.json may not have loaded properly")
            except Exception as e:
                logger.error(f"  ❌ Failed to initialize intent detector: {e}")
                agent_config.intent_detector = None

            # Load prompt templates
            prompts_file = agent_dir / "prompts.json"
            if prompts_file.exists():
                try:
                    logger.info(f"📁 Loading prompts.json for agent {agent_dir.name}")
                    with open(prompts_file, 'r') as f:
                        prompts_data = json.load(f)
                        agent_config.prompt_templates = prompts_data.get('prompts', {})
                        logger.info(f"  ✅ prompts.json loaded: {len(agent_config.prompt_templates)} templates")
                        logger.info(f"     Available templates: {list(agent_config.prompt_templates.keys())}")
                except Exception as e:
                    logger.error(f"  ❌ Failed to load prompt templates: {e}")
            else:
                logger.warning(f"  ❌ prompts.json not found at {prompts_file}")

            # Initialize tools for dispensary agent
            if agent_dir.name == "dispensary":
                try:
                    agent_config.product_search_tool = ProductSearchTool()
                    logger.info(f"  - Initialized ProductSearchTool")
                except Exception as e:
                    logger.warning(f"  - Failed to initialize ProductSearchTool: {e}")

            return agent_config
        except Exception as e:
            logger.error(f"Failed to load agent config: {e}")
            return None

    def _load_personality_from_file(
        self,
        agent_id: str,
        personality_id: str,
        personality_file: Path
    ) -> Optional[PersonalityConfig]:
        """Load personality configuration from a single JSON file"""
        if not personality_file.exists():
            return None

        try:
            with open(personality_file, 'r') as f:
                data = json.load(f)

            # Handle nested personality structure (like in zac.json)
            if "personality" in data and isinstance(data["personality"], dict):
                personality_data = data["personality"]
                # Build a comprehensive system prompt from the personality data
                system_prompt = personality_data.get("greeting_prompt", "")
                if not system_prompt and "description" in personality_data:
                    system_prompt = f"You are {personality_data.get('name', personality_id)}, {personality_data.get('description', '')}."

                return PersonalityConfig(
                    agent_id=agent_id,
                    personality_id=personality_id,
                    name=personality_data.get("name", personality_id),
                    traits=personality_data.get("traits", {}),
                    prompts={
                        "greeting": personality_data.get("greeting_prompt", ""),
                        "product_search": personality_data.get("product_search_prompt", ""),
                        "recommendation": personality_data.get("recommendation_prompt", "")
                    },
                    system_prompt=system_prompt,
                    greeting=personality_data.get("conversation_style", {}).get("opening_phrases", ["Hello!"])[0] if personality_data.get("conversation_style", {}).get("opening_phrases") else "Hello! How can I help you today?",
                    style={
                        "temperature": 0.7,
                        "max_tokens": 512,
                        "verbosity": personality_data.get("traits", {}).get("response_length", "moderate"),
                        "tone": personality_data.get("traits", {}).get("communication_style", "friendly")
                    },
                    knowledge_domains=[personality_data.get("role", "assistant")],
                    behavioral_rules=[]
                )
            else:
                # Original flat structure
                return PersonalityConfig(
                    agent_id=agent_id,
                    personality_id=personality_id,
                    name=data.get("name", personality_id),
                    traits=data.get("traits", {}),
                    prompts=data.get("prompts", {}),
                    system_prompt=data.get("system_prompt", data.get("personality", "")),
                    greeting=data.get("greeting", data.get("default_greeting", "Hello! How can I help you today?")),
                    style=data.get("style", {
                        "temperature": data.get("temperature", 0.7),
                        "max_tokens": data.get("max_tokens", 512),
                        "verbosity": data.get("verbosity", "moderate"),
                        "tone": data.get("tone", "friendly")
                    }),
                    knowledge_domains=data.get("knowledge_domains", []),
                    behavioral_rules=data.get("behavioral_rules", data.get("rules", []))
                )
        except Exception as e:
            logger.error(f"Failed to load personality from {personality_file}: {e}")
            return None

    def get_agent(self, agent_id: str) -> Optional[AgentConfig]:
        """Get agent configuration"""
        return self.agents.get(agent_id)

    def get_personality(
        self,
        agent_id: str,
        personality_id: str
    ) -> Optional[PersonalityConfig]:
        """Get personality configuration with caching"""
        cache_key = (agent_id, personality_id)

        # Check cache first
        if self.cache_personalities and cache_key in self.personality_cache:
            # Move to end (LRU)
            self.personality_cache.move_to_end(cache_key)
            self.metrics["cache_hits"] += 1
            return self.personality_cache[cache_key]

        # Load from agent config
        agent = self.agents.get(agent_id)
        if not agent:
            return None

        personality = agent.personalities.get(personality_id)
        if personality and self.cache_personalities:
            # Add to cache
            self._add_to_cache(cache_key, personality)
            self.metrics["cache_misses"] += 1

        return personality

    def _add_to_cache(
        self,
        key: Tuple[str, str],
        personality: PersonalityConfig
    ):
        """Add personality to LRU cache"""
        if len(self.personality_cache) >= self.max_cache_size:
            # Remove least recently used
            self.personality_cache.popitem(last=False)

        self.personality_cache[key] = personality

    async def create_session(
        self,
        session_id: str,
        agent_id: str,
        personality_id: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> SessionState:
        """Create a new session with specified agent/personality"""

        # Validate agent exists
        agent = self.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent not found: {agent_id}")

        # Use default personality if not specified
        if not personality_id:
            personality_id = agent.default_personality or list(agent.personalities.keys())[0]

        # Validate personality exists
        personality = self.get_personality(agent_id, personality_id)
        if not personality:
            raise ValueError(f"Personality not found: {agent_id}/{personality_id}")

        # Check session limit
        if len(self.sessions) >= self.max_sessions:
            # Remove oldest inactive session
            await self._cleanup_old_sessions()

        # Create session
        session = SessionState(
            session_id=session_id,
            agent_id=agent_id,
            personality_id=personality_id,
            user_id=user_id,
            metadata=metadata or {}
        )

        self.sessions[session_id] = session
        self.metrics["active_sessions"] = len(self.sessions)

        logger.info(f"Created session {session_id}: {agent_id}/{personality_id}")
        return session

    async def switch_personality(
        self,
        session_id: str,
        new_personality_id: str,
        preserve_context: bool = True
    ) -> bool:
        """Hot-swap personality for an active session"""

        if not self.enable_hot_swap:
            return False

        session = self.sessions.get(session_id)
        if not session:
            return False

        # Validate new personality exists
        personality = self.get_personality(session.agent_id, new_personality_id)
        if not personality:
            return False

        # Update session
        old_personality = session.personality_id
        session.personality_id = new_personality_id
        session.update_activity()

        if not preserve_context:
            # Clear context if requested
            session.context_history = []

        self.metrics["personality_switches"] += 1
        logger.info(f"Session {session_id}: Switched {old_personality} -> {new_personality_id}")

        return True

    async def switch_agent(
        self,
        session_id: str,
        new_agent_id: str,
        personality_id: Optional[str] = None
    ) -> bool:
        """Switch to a different agent (more resource intensive)"""

        session = self.sessions.get(session_id)
        if not session:
            return False

        # Validate new agent exists
        agent = self.get_agent(new_agent_id)
        if not agent:
            return False

        # Use default personality if not specified
        if not personality_id:
            personality_id = agent.default_personality or list(agent.personalities.keys())[0]

        # Validate personality
        personality = self.get_personality(new_agent_id, personality_id)
        if not personality:
            return False

        # Update session
        session.agent_id = new_agent_id
        session.personality_id = personality_id
        session.context_history = []  # Clear context when switching agents
        session.update_activity()

        logger.info(f"Session {session_id}: Switched to {new_agent_id}/{personality_id}")
        return True

    def get_session(self, session_id: str) -> Optional[SessionState]:
        """Get active session"""
        session = self.sessions.get(session_id)
        if session:
            session.update_activity()
        return session

    async def process_message(
        self,
        session_id: str,
        message: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Process a message for a session using intent-based routing"""

        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        # Get personality configuration
        personality = self.get_personality(session.agent_id, session.personality_id)
        if not personality:
            raise ValueError("Personality configuration not found")

        # Get the agent configuration
        agent_config = self.agents.get(session.agent_id)
        if not agent_config:
            raise ValueError(f"Agent configuration not found: {session.agent_id}")

        # Step 1: Detect intent
        intent_result = None
        detected_intent = "general"

        if hasattr(agent_config, 'intent_detector') and agent_config.intent_detector:
            try:
                intent_result = agent_config.intent_detector.detect(message, language="auto")
                detected_intent = intent_result.get("intent", "general")
                logger.info(f"Intent detected: {detected_intent} (confidence: {intent_result.get('confidence', 0):.2f})")
                
                # Override intent if there's an active signup session
                if session.agent_id == "sales" and session.signup_state:
                    current_step = session.signup_state.get('current_step', 'not_started')
                    if current_step not in ["not_started", "completed", ""]:
                        logger.info(f"🔧 Active signup session detected (step: {current_step}), overriding intent to signup_help")
                        detected_intent = "signup_help"
                    
            except Exception as e:
                logger.warning(f"Intent detection failed: {e}")

        # Step 2: Execute tools for product_search intent
        tool_results = None
        logger.debug(f"Checking for product_search: detected_intent={detected_intent}, has_tool={hasattr(agent_config, 'product_search_tool')}, tool={agent_config.product_search_tool if hasattr(agent_config, 'product_search_tool') else 'None'}")

        if detected_intent == "product_search" and hasattr(agent_config, 'product_search_tool') and agent_config.product_search_tool:
            logger.info(f"Executing ProductSearchTool for query: {message}")
            try:
                tool_results = agent_config.product_search_tool.search_products(
                    query=message,
                    limit=5
                )
                logger.info(f"Product search returned {len(tool_results.get('products', []))} products")
            except Exception as e:
                logger.error(f"Product search failed: {e}")
        elif detected_intent == "product_search":
            logger.warning(f"Product search intent detected but tool not available. Agent: {session.agent_id}")

        # Step 2b: Execute tools for signup intents (sales agent)
        signup_tool_result = None
        if session.agent_id == "sales" and detected_intent in ["signup_help", "closing_request"]:
            logger.info(f"🔧 Signup intent detected: {detected_intent}")
            logger.info(f"🔧 Available tools: {agent_config.tools if hasattr(agent_config, 'tools') else 'None'}")
            logger.info(f"🔧 Tool manager: {self.tool_manager is not None}")
            
            # Initialize signup state if not already started
            if not session.signup_state.get('current_step'):
                logger.info(f"🔧 Initializing signup flow - setting step to 'collecting_info'")
                session.signup_state['current_step'] = 'collecting_info'
            
            if self.tool_manager and hasattr(agent_config, 'tools') and agent_config.tools:
                logger.info(f"🔧 Processing signup flow for session {session_id}")
                
                # Try to extract signup information from message
                signup_info = await self._extract_signup_info(message, session)
                logger.info(f"🔧 Extracted signup info: {list(signup_info.keys())}")
                
                # Determine which tool to call based on state and available info
                signup_tool_result = await self._handle_signup_tools(
                    session=session,
                    message=message,
                    signup_info=signup_info,
                    agent_config=agent_config
                )
                
                if signup_tool_result:
                    logger.info(f"🔧 Signup tool executed successfully: {signup_tool_result.get('tool_called')}")
                    # Update session signup state
                    session.signup_state.update(signup_tool_result.get('state_updates', {}))
            else:
                logger.warning(f"⚠️ Signup tools not available. tool_manager={self.tool_manager is not None}, has_tools={hasattr(agent_config, 'tools')}, tools={agent_config.tools if hasattr(agent_config, 'tools') else None}")

        # Step 3: Select appropriate prompt template
        prompt_template = None
        max_tokens = 500

        if hasattr(agent_config, 'prompt_templates') and agent_config.prompt_templates:
            # Map intent to prompt template key
            template_key = detected_intent
            if detected_intent == "general":
                template_key = "general_chat"

            prompt_template = agent_config.prompt_templates.get(template_key)
            if prompt_template:
                logger.info(f"Using prompt template: {template_key}")

        # Step 4: Build prompt with template or fallback
        if prompt_template:
            template_str = prompt_template.get('template', '')
            output_format = prompt_template.get('output_format', '')

            # Check if this is a knowledge template (sales agent style) vs a prompt template
            is_knowledge_template = (
                "{message}" not in template_str and
                len(template_str) > 50 and
                output_format == "text"
            )

            if is_knowledge_template:
                logger.info(f"📚 Using knowledge template as context for personalized response")
                # Use template as KNOWLEDGE/CONTEXT, not verbatim response
                # Load system prompt if available
                system_prompt = ""
                if hasattr(agent_config, 'prompt_templates') and 'system_prompt' in agent_config.prompt_templates:
                    system_template = agent_config.prompt_templates['system_prompt']
                    system_prompt = system_template.get('template', '')

                # Build conversational prompt with template as knowledge base
                prompt_parts = []

                if system_prompt:
                    prompt_parts.append(system_prompt)

                # Add template as reference knowledge
                prompt_parts.append(f"REFERENCE INFORMATION:\n{template_str}")

                # Detect language FIRST before building instructions
                detected_language = intent_result.get("language", "en") if intent_result else "en"
                language_map = {
                    "es": "Spanish (Español)",
                    "fr": "French (Français)",
                    "zh": "Chinese (中文)",
                    "ja": "Japanese (日本語)",
                    "ko": "Korean (한국어)",
                    "de": "German (Deutsch)",
                    "pt": "Portuguese (Português)"
                }
                
                # Build instructions with language requirement if needed
                instructions = (
                    "\nINSTRUCTIONS: "
                    "1. Answer ONLY what the customer asked - don't include unrelated information\n"
                    "2. Keep response focused and concise (2-3 short paragraphs maximum)\n"
                    "3. Be conversational and friendly, not formal\n"
                    "4. End with a specific follow-up question to learn more about their needs\n"
                    "5. Do NOT include all pricing tiers unless specifically asked for a comparison"
                )
                
                # Add language instruction to the INSTRUCTIONS section, not at the end
                if detected_language != "en" and detected_language in language_map:
                    instructions += f"\n6. CRITICAL: You MUST respond ENTIRELY in {language_map[detected_language]}. The customer wrote in {language_map[detected_language]}, so all your text must be in {language_map[detected_language]}."
                    logger.info(f"🌐 Multilingual: Detected {language_map[detected_language]}, adding language requirement to instructions")
                
                prompt_parts.append(instructions)

                # Add the actual user message
                prompt_parts.append(f"\nCustomer: {message}\nCarlos:")

                prompt_with_context = "\n\n".join(prompt_parts)
                # Get max tokens from template constraints - reduce significantly for concise responses
                constraints = prompt_template.get('constraints', {})
                # For knowledge templates, use much lower token count for concise responses (max 150 tokens)
                max_tokens = 150  # Fixed at 150 for all knowledge template responses
            else:
                # Original logic for prompt templates
                # Load system prompt if available
                system_prompt = ""
                if hasattr(agent_config, 'prompt_templates') and 'system_prompt' in agent_config.prompt_templates:
                    system_template = agent_config.prompt_templates['system_prompt']
                    system_prompt = system_template.get('template', '')

                # Replace variables in template
                template_with_vars = template_str.replace(
                    "{personality_name}", personality.name
                ).replace(
                    "{message}", message
                )

                # Build the complete prompt
                # Structure: [System Prompt] + [Template Context] + User: {message} + Assistant:
                prompt_parts = []

                if system_prompt:
                    prompt_parts.append(system_prompt)

                # Detect language FIRST
                detected_language = intent_result.get("language", "en") if intent_result else "en"
                language_map = {
                    "es": "Spanish (Español)",
                    "fr": "French (Français)",
                    "zh": "Chinese (中文)",
                    "ja": "Japanese (日本語)",
                    "ko": "Korean (한국어)",
                    "de": "German (Deutsch)",
                    "pt": "Portuguese (Português)",
                    "it": "Italian (Italiano)",
                    "ru": "Russian (Русский)",
                    "ar": "Arabic (العربية)"
                }
                
                # Add language instruction to system prompt if needed
                if detected_language != "en" and detected_language in language_map:
                    language_instruction = f"\n\nCRITICAL LANGUAGE REQUIREMENT: You MUST respond entirely in {language_map[detected_language]}. The user wrote their message in {language_map[detected_language]}, so your entire response must be in {language_map[detected_language]}."
                    if system_prompt:
                        system_prompt += language_instruction
                    else:
                        prompt_parts.insert(0, f"[System Instruction]{language_instruction}")
                    logger.info(f"🌐 Multilingual: Detected {language_map[detected_language]}, added language requirement to system prompt")
                
                # If template doesn't contain the user message (no {message} placeholder), add it conversationally
                if "{message}" not in template_str:
                    # Template is guidance/context, append user message
                    prompt_parts.append(template_with_vars)
                    prompt_parts.append(f"\nUser: {message}\nAssistant:")
                else:
                    # Template already has message integrated
                    prompt_parts.append(template_with_vars)
                    prompt_parts.append("\nAssistant:")

                prompt_with_context = "\n\n".join(prompt_parts)
            # Add tool results for product search
            if tool_results and tool_results.get('products'):
                products_info = "\n\nAvailable products based on your search:\n"
                for i, product in enumerate(tool_results['products'][:5], 1):
                    products_info += f"{i}. **{product.get('name', 'Unknown')}** "
                    if product.get('brand'):
                        products_info += f"by {product['brand']} "
                    if product.get('strain_type'):
                        products_info += f"({product['strain_type']})\n"
                    else:
                        products_info += "\n"
                    if product.get('thc_content'):
                        products_info += f"   THC: {product['thc_content']}%"
                    if product.get('cbd_content'):
                        products_info += f", CBD: {product['cbd_content']}%"
                    if product.get('price'):
                        products_info += f"   Price: ${product['price']}"
                    if product.get('size'):
                        products_info += f" ({product['size']})"
                    products_info += "\n"
                    if product.get('short_description'):
                        products_info += f"   {product['short_description'][:100]}\n"
                prompt_with_context += products_info

            # Get max tokens from template constraints - limit to 150 for concise responses
            constraints = prompt_template.get('constraints', {})
            max_tokens = min(150, constraints.get('max_words', 75))  # Max 150 tokens
        else:
            # Fallback to personality system prompt
            system_prompt = personality.system_prompt or "You are a helpful assistant."
            prompt_with_context = f"{system_prompt}\n\nUser: {message}\nAssistant:"
            max_tokens = 150  # Set default for fallback path

        # Step 5: Add conversation history to the prompt for context
        # Keep last 6 exchanges (12 messages) to maintain context without exceeding token limits
        if session.context_history and len(session.context_history) > 0:
            history_text = "\n\nPREVIOUS CONVERSATION:\n"
            # Get last 6 exchanges (user + assistant pairs)
            recent_history = session.context_history[-6:]
            for exchange in recent_history:
                history_text += f"Customer: {exchange.get('user', '')}\n"
                history_text += f"Assistant: {exchange.get('assistant', '')}\n"
            
            logger.info(f"💬 Session has {len(session.context_history)} total exchanges, using last {len(recent_history)}")
            
            # Insert conversation history before the current message
            # Find where the current user message starts in the prompt
            if "\nCustomer: " in prompt_with_context or "\nUser: " in prompt_with_context:
                # Insert history before the last user message
                parts = prompt_with_context.rsplit("\nCustomer: ", 1) if "\nCustomer: " in prompt_with_context else prompt_with_context.rsplit("\nUser: ", 1)
                if len(parts) == 2:
                    separator = "\nCustomer: " if "\nCustomer: " in prompt_with_context else "\nUser: "
                    prompt_with_context = parts[0] + history_text + separator + parts[1]
                    logger.info(f"💬 Added {len(recent_history)} previous exchanges to context")
                else:
                    logger.warning(f"⚠️ Could not split prompt to insert history (parts={len(parts)})")
            else:
                logger.warning(f"⚠️ No Customer:/User: marker found in prompt to insert history")
        else:
            logger.info(f"ℹ️ No conversation history to add (history length: {len(session.context_history) if session.context_history else 0})")

        # Step 6: Generate response using shared model
        # Pass the pre-built prompt directly and skip V5's intent detection
        if self.shared_model:
            # Force max_tokens to be reasonable - override kwargs if needed
            final_max_tokens = min(150, kwargs.get('max_tokens', max_tokens))

            # Tell V5 to use our prompt directly by setting prompt_type
            result = await self.shared_model.generate(
                prompt=prompt_with_context,
                prompt_type="direct",  # Skip V5's intent detection
                session_id=session_id,
                max_tokens=final_max_tokens,
                temperature=personality.style.get('temperature', 0.7) if personality.style else 0.7,
                use_tools=kwargs.get('use_tools', False),
                use_context=False  # We're managing context ourselves
            )

            logger.info(f"📝 Raw result from shared_model.generate: type={type(result)}, keys={result.keys() if isinstance(result, dict) else 'N/A'}")

            # Ensure result is a dict
            if isinstance(result, str):
                response = {
                    "text": result,
                    "intent": detected_intent,
                    "confidence": intent_result.get("confidence", 0) if intent_result else 0
                }
            else:
                response = result
                # Ensure there's a text field in the response
                if "text" not in response:
                    response["text"] = response.get("response", response.get("message", ""))
                response["intent"] = detected_intent
                response["confidence"] = intent_result.get("confidence", 0) if intent_result else 0

            # Add product data if available for frontend display
            if tool_results and tool_results.get('products') and detected_intent == "product_search":
                response["products"] = tool_results['products'][:5]  # Limit to 5 products for display
                response["products_found"] = len(tool_results['products'])
                logger.info(f"✅ Added {response['products_found']} products to response for display")
            elif detected_intent == "product_search":
                logger.warning(f"⚠️ Product search intent but no products found. tool_results: {bool(tool_results)}, has products: {tool_results.get('products') if tool_results else None}")
            
            # Add signup tool results if available
            if signup_tool_result:
                response["signup_tool_result"] = signup_tool_result
                response["signup_state"] = session.signup_state
                logger.info(f"✅ Added signup tool result to response: {signup_tool_result.get('tool_called')}")
                
                # Inject tool result into response text if successful
                if signup_tool_result.get('success'):
                    tool_name = signup_tool_result.get('tool_called')
                    if tool_name == 'validate_crsa_signup':
                        store_info = signup_tool_result['data'].get('store_info', {})
                        tier = signup_tool_result['data'].get('verification_tier')
                        response["text"] += f"\n\n✅ License verified for {store_info.get('store_name')}! "
                        if tier == 'auto_approved':
                            response["text"] += "Your email matches your business website, so we can activate your account immediately."
                        else:
                            response["text"] += "Your account will be reviewed within 24 hours."
                    elif tool_name == 'send_verification_code':
                        response["text"] += "\n\n📧 Verification code sent! Please check your email and provide the 6-digit code."
                    elif tool_name == 'verify_signup_code':
                        response["text"] += "\n\n✅ Code verified! Creating your account now..."
                    elif tool_name == 'create_tenant_signup':
                        tenant_code = signup_tool_result['data'].get('tenant_code')
                        response["text"] += f"\n\n🎉 Account created! Tenant code: {tenant_code}. Check your email for the password setup link!"
        else:
            response = {
                "text": "Model not loaded",
                "error": "No shared model available",
                "intent": detected_intent
            }

        # Update session history with intent info
        session.context_history.append({
            "user": message,
            "assistant": response.get("text", ""),
            "intent": detected_intent,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        self.metrics["total_requests"] += 1
        return response

    async def _extract_verification_code(self, message: str) -> Optional[str]:
        """Extract 6-digit verification code from message using LLM"""
        import re
        
        # First try simple regex (fast path for "123456")
        code_match = re.search(r'\b\d{6}\b', message)
        if code_match:
            return code_match.group(0)
        
        # Use LLM for complex cases (spelled out, spaces, non-English)
        if self.shared_model:
            logger.info(f"🤖 Using LLM to extract verification code")
            
            extraction_prompt = f"""Extract the 6-digit verification code from this message. Reply with ONLY the 6 digits, nothing else.

Message: "{message}"

Examples:
- "123456" → 123456
- "one two three four five six" → 123456
- "the code is 1 2 3 4 5 6" → 123456
- "my code: 987654" → 987654
- "código: 111222" → 111222

Reply with only the 6 digits:"""

            try:
                result = await self._safe_llm_call(
                    prompt=extraction_prompt,
                    max_tokens=20,
                    temperature=0.1
                )
                
                response_text = result.get('text', '').strip()
                logger.info(f"🤖 Code extraction response: {response_text}")
                
                # Extract 6 digits from response
                code_match = re.search(r'\b\d{6}\b', response_text)
                if code_match:
                    return code_match.group(0)
                
            except Exception as e:
                logger.warning(f"⚠️ LLM code extraction failed: {e}")
        
        return None

    async def _safe_llm_call(self, prompt: str, max_tokens: int, temperature: float) -> Dict[str, Any]:
        """Safely call LLM with error handling"""
        try:
            if not self.shared_model:
                return {"text": "", "error": "No model available"}
            
            result = await self.shared_model.generate(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                prompt_type="direct"
            )
            return result
        except Exception as e:
            logger.error(f"❌ LLM call failed: {e}")
            return {"text": "", "error": str(e)}

    async def generate_message(
        self,
        session_id: str,
        message: str,
        user_id: Optional[str] = None,
        **kwargs
    ) -> str:
        """Generate a message response for compatibility with chat_endpoints"""
        # Update user_id if provided
        if user_id and session_id in self.sessions:
            self.sessions[session_id].user_id = user_id

        # Process the message
        result = await self.process_message(session_id, message, **kwargs)

        # Return just the text response for compatibility
        return result.get("text", "")

    async def generate_message_with_products(
        self,
        session_id: str,
        message: str,
        user_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate a message response with full product data"""
        # Update user_id if provided
        if user_id and session_id in self.sessions:
            self.sessions[session_id].user_id = user_id

        # Process the message
        result = await self.process_message(session_id, message, **kwargs)

        # Return the full response object including products
        return result

    async def _cleanup_old_sessions(self, max_age_minutes: int = 30):
        """Clean up inactive sessions"""
        now = datetime.now(timezone.utc)
        to_remove = []

        for session_id, session in self.sessions.items():
            age = (now - session.last_activity).total_seconds() / 60
            if age > max_age_minutes:
                to_remove.append(session_id)

        for session_id in to_remove:
            del self.sessions[session_id]
            logger.info(f"Cleaned up inactive session: {session_id}")

        self.metrics["active_sessions"] = len(self.sessions)

    def get_available_agents(self) -> List[Dict[str, Any]]:
        """Get list of available agents with their personalities"""
        agents_list = []

        for agent_id, agent in self.agents.items():
            personalities = [
                {
                    "id": p_id,
                    "name": p.name,
                    "traits": p.traits
                }
                for p_id, p in agent.personalities.items()
            ]

            agents_list.append({
                "agent_id": agent_id,
                "name": agent.name,
                "description": agent.description,
                "capabilities": agent.capabilities,
                "personalities": personalities,
                "default_personality": agent.default_personality
            })

        return agents_list

    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        memory_usage = psutil.Process().memory_info().rss / 1024 / 1024 / 1024  # GB

        return {
            **self.metrics,
            "memory_usage_gb": round(memory_usage, 2),
            "loaded_agents": len(self.agents),
            "cached_personalities": len(self.personality_cache),
            "cache_hit_rate": (
                self.metrics["cache_hits"] /
                max(1, self.metrics["cache_hits"] + self.metrics["cache_misses"])
            )
        }

    def set_shared_model(self, model):
        """Set the shared model reference and propagate to intent detectors"""
        self.shared_model = model
        logger.info("Shared model reference set")

        # Propagate v5_engine reference to all intent detectors
        for agent_id, agent_config in self.agents.items():
            if hasattr(agent_config, 'intent_detector') and agent_config.intent_detector:
                agent_config.intent_detector.v5_engine = model
                logger.info(f"  ✅ Updated intent detector for agent {agent_id} with v5_engine reference")

    async def _extract_signup_info(self, message: str, session: SessionState) -> Dict[str, Any]:
        """Extract signup information from message using LLM"""
        import re
        
        info = {}
        
        # First try simple regex for obvious patterns (fast path)
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        email_match = re.search(email_pattern, message)
        if email_match:
            info['email'] = email_match.group(0)
        
        crsa_pattern = r'CRSA\s*\d{7}'
        crsa_match = re.search(crsa_pattern, message, re.IGNORECASE)
        if crsa_match:
            info['license_number'] = crsa_match.group(0).replace(' ', '').upper()
        elif re.search(r'\b\d{7}\b', message):
            digit_match = re.search(r'\b\d{7}\b', message)
            info['license_number'] = f"CRSA{digit_match.group(0)}"
        
        # Check if we need LLM extraction (for non-English or complex cases)
        needs_llm_extraction = (
            len(info) == 0 or  # Regex found nothing
            not email_match or  # No email found
            any(ord(c) > 127 for c in message)  # Non-ASCII characters (non-English)
        )
        
        if needs_llm_extraction and self.shared_model:
            logger.info(f"🤖 Using LLM to extract signup info (multilingual/complex)")
            
            extraction_prompt = f"""Extract signup information from this message. Reply ONLY with JSON, no explanation.

Message: "{message}"

Extract these fields if present (leave empty string if not found):
{{
  "contact_name": "person's full name",
  "contact_role": "their job title (owner/manager/director/ceo/president/operator)",
  "email": "email address",
  "phone": "phone number",
  "license_number": "CRSA license number (7 digits, add CRSA prefix if missing)"
}}

Rules:
- If a 7-digit number appears, treat it as CRSA license and add "CRSA" prefix
- For role, use one of: Owner, Manager, Director, CEO, President, Operator
- Return empty string "" for fields not found
- Output ONLY valid JSON, nothing else

JSON:"""

            try:
                # Wrap call to handle errors gracefully
                result = await self._safe_llm_call(
                    prompt=extraction_prompt,
                    max_tokens=150,
                    temperature=0.1
                )
                
                response_text = result.get('text', '').strip()
                logger.info(f"🤖 LLM extraction response: {response_text[:200]}")
                
                # Parse JSON response
                import json
                # Try to find JSON in response (in case model adds explanation)
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = response_text[json_start:json_end]
                    extracted = json.loads(json_str)
                    
                    # Merge LLM-extracted info (only non-empty values)
                    for key, value in extracted.items():
                        if value and value.strip():
                            info[key] = value.strip()
                            logger.info(f"  ✅ Extracted {key}: {value}")
                
            except Exception as e:
                logger.warning(f"⚠️ LLM extraction failed: {e}, falling back to regex")
        
        # Check session state for previously collected info
        if session.signup_state:
            for key in ['email', 'contact_name', 'contact_role', 'phone', 'license_number']:
                if key not in info and key in session.signup_state:
                    info[key] = session.signup_state[key]
        
        return info

    async def _handle_signup_tools(
        self,
        session: SessionState,
        message: str,
        signup_info: Dict[str, Any],
        agent_config: AgentConfig
    ) -> Optional[Dict[str, Any]]:
        """Handle signup tool execution based on collected information"""
        
        try:
            current_step = session.signup_state.get('current_step', 'not_started')
            logger.info(f"🔧 Current signup step: {current_step}")
            
            # Step 1: Validate CRSA if we have license and email
            if signup_info.get('license_number') and signup_info.get('email'):
                if current_step in ['not_started', 'collecting_info']:
                    logger.info(f"🔧 Calling validate_crsa_signup tool")
                    logger.info(f"🔧   License: {signup_info['license_number']}")
                    logger.info(f"🔧   Email: {signup_info['email']}")
                    
                    result = await self.tool_manager.execute_tool(
                        'validate_crsa_signup',
                        license_number=signup_info['license_number'],
                        email=signup_info['email'],
                        phone=signup_info.get('phone'),
                        session_id=session.session_id
                    )
                    
                    if result.get('success') and result['result'].get('success'):
                        logger.info(f"✅ CRSA validation successful")
                        tool_data = result['result'].get('data', {})
                        
                        return {
                            'tool_called': 'validate_crsa_signup',
                            'success': True,
                            'state_updates': {
                                'current_step': 'validating_crsa',
                                'store_info': tool_data.get('store_info'),
                                'verification_tier': tool_data.get('verification_tier'),
                                'domain_match': tool_data.get('domain_match'),
                                'email': signup_info['email'],
                                'phone': signup_info.get('phone'),
                                'license_number': signup_info['license_number']
                            },
                            'data': tool_data
                        }
                    else:
                        logger.error(f"❌ CRSA validation failed: {result}")
                        return {
                            'tool_called': 'validate_crsa_signup',
                            'success': False,
                            'error': result.get('result', {}).get('error', 'Unknown error')
                        }
            
            # Step 2: Send verification code if CRSA validated
            if current_step == 'validating_crsa' and session.signup_state.get('store_info'):
                logger.info(f"🔧 Calling send_verification_code tool")
                
                result = await self.tool_manager.execute_tool(
                    'send_verification_code',
                    email=session.signup_state['email'],
                    phone=session.signup_state.get('phone'),
                    verification_tier=session.signup_state['verification_tier'],
                    store_name=session.signup_state['store_info']['store_name'],
                    store_info=session.signup_state['store_info'],
                    session_id=session.session_id
                )
                
                if result.get('success') and result['result'].get('success'):
                    logger.info(f"✅ Verification code sent")
                    tool_data = result['result'].get('data', {})
                    
                    return {
                        'tool_called': 'send_verification_code',
                        'success': True,
                        'state_updates': {
                            'current_step': 'verifying_code',
                            'verification_id': tool_data.get('verification_id')
                        },
                        'data': tool_data
                    }
            
            # Step 3: Verify code if user provides it
            if current_step == 'verifying_code':
                # Use LLM to extract 6-digit code (handles "one two three four five six" etc)
                code = await self._extract_verification_code(message)
                
                if code:
                    logger.info(f"🔧 Calling verify_signup_code tool with code: {code}")
                    
                    result = await self.tool_manager.execute_tool(
                        'verify_signup_code',
                        verification_id=session.signup_state['verification_id'],
                        code=code,
                        email=session.signup_state['email'],
                        session_id=session.session_id
                    )
                    
                    if result.get('success') and result['result'].get('success'):
                        logger.info(f"✅ Code verified")
                        
                        return {
                            'tool_called': 'verify_signup_code',
                            'success': True,
                            'state_updates': {
                                'current_step': 'creating_tenant',
                                'code_verified': True
                            },
                            'data': result['result'].get('data', {})
                        }
                    else:
                        logger.error(f"❌ Code verification failed")
                        return {
                            'tool_called': 'verify_signup_code',
                            'success': False,
                            'error': result.get('result', {}).get('error', 'Invalid code')
                        }
                else:
                    logger.info(f"⚠️ No verification code found in message")
                    return None
            
            # Step 4: Create tenant if code verified
            if current_step == 'creating_tenant' and session.signup_state.get('code_verified'):
                logger.info(f"🔧 Calling create_tenant_signup tool")
                
                result = await self.tool_manager.execute_tool(
                    'create_tenant_signup',
                    verification_id=session.signup_state['verification_id'],
                    email=session.signup_state['email'],
                    phone=session.signup_state.get('phone'),
                    contact_name=signup_info.get('contact_name', 'Unknown'),
                    contact_role=signup_info.get('contact_role', 'Manager'),
                    session_id=session.session_id
                )
                
                if result.get('success') and result['result'].get('success'):
                    logger.info(f"✅ Tenant created successfully")
                    tool_data = result['result'].get('data', {})
                    
                    return {
                        'tool_called': 'create_tenant_signup',
                        'success': True,
                        'state_updates': {
                            'current_step': 'completed',
                            'tenant_id': tool_data.get('tenant_id'),
                            'tenant_code': tool_data.get('tenant_code')
                        },
                        'data': tool_data
                    }
            
            logger.info(f"🔧 No tool action taken for current state")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error handling signup tools: {e}", exc_info=True)
            return {
                'tool_called': 'error',
                'success': False,
                'error': str(e)
            }

    def set_tool_manager(self, tool_manager):
        """Set the tool manager reference and enroll agent tools"""
        self.tool_manager = tool_manager
        logger.info("Tool manager reference set")

        # Enroll tools for each agent
        for agent_id, agent_config in self.agents.items():
            if agent_config.tools:
                enrolled = self.tool_manager.enroll_agent_tools(agent_id, agent_config.tools)
                if enrolled:
                    logger.info(f"  ✅ Enrolled {len(agent_config.tools)} tools for agent {agent_id}: {agent_config.tools}")
                    agent_config.tool_manager = tool_manager
                else:
                    logger.warning(f"  ⚠️ Failed to enroll tools for agent {agent_id}")
            else:
                logger.info(f"  ℹ️ No tools configured for agent {agent_id}")


# Singleton instance
_agent_pool = None

def get_agent_pool() -> AgentPoolManager:
    """Get or create the agent pool manager singleton"""
    global _agent_pool
    if _agent_pool is None:
        from core.config_loader import get_config
        config = get_config()

        pool_config = {
            "max_memory_gb": config.get("performance", {}).get("max_memory_gb", 4),
            "enable_hot_swap": True,
            "cache_personalities": True,
            "max_cache_size": 20,
            "max_sessions": 1000
        }

        _agent_pool = AgentPoolManager(pool_config)

    return _agent_pool