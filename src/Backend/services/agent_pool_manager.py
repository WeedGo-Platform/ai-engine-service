"""
Agent Pool Manager - Hybrid Architecture for Multiple Agents/Personalities
Implements shared model with multiple personality configurations
"""

import os
import json
import logging
import asyncio
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
            # Use intent-specific template
            template_str = prompt_template.get('template', '')

            # Replace variables in template
            prompt_with_context = template_str.replace(
                "{personality_name}", personality.name
            ).replace(
                "{message}", message
            )

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

            # Get max tokens from template constraints
            constraints = prompt_template.get('constraints', {})
            max_tokens = constraints.get('max_words', 100) * 2
        else:
            # Fallback to personality system prompt
            system_prompt = personality.system_prompt or "You are a helpful assistant."
            prompt_with_context = f"{system_prompt}\n\nUser: {message}\nAssistant:"

        # Step 5: Generate response using shared model
        if self.shared_model:
            result = await self.shared_model.generate(
                prompt=prompt_with_context,
                session_id=session_id,
                max_tokens=kwargs.get('max_tokens', max_tokens),
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