"""
Main Orchestrator for AGI System
Handles model routing, agent selection, and request processing
"""

import asyncio
import logging
import time
from typing import Any, Optional, Dict, List, AsyncIterator
import json
from datetime import datetime

from agi.core.interfaces import (
    IOrchestrator, IAgent, IModel, ITool,
    ConversationContext, AgentTask, MessageRole, Message
)
from agi.config.agi_config import get_config, ModelSize
from agi.models.registry import get_model_registry
from agi.agents.base_agent import BaseAgent
from agi.core.database import get_db_manager
from agi.memory import get_memory_manager
from agi.tools import get_tool_registry
from agi.knowledge import get_rag_system
from agi.prompts import get_persona_manager, get_template_engine
from agi.analytics import get_metrics_collector, get_conversation_analyzer
from agi.analytics.metrics import MetricType

logger = logging.getLogger(__name__)

class AGIOrchestrator(IOrchestrator):
    """
    Main orchestrator that routes requests to appropriate models and agents

    Responsibilities:
    - Analyze incoming requests
    - Select appropriate model based on complexity
    - Route to agents when needed
    - Handle streaming responses
    - Manage fallbacks
    """

    def __init__(self):
        """Initialize orchestrator"""
        self.config = get_config()
        self.registry = None
        self.db_manager = None
        self.memory_manager = None
        self.tool_registry = None
        self.rag_system = None
        self.persona_manager = None
        self.template_engine = None
        self.metrics_collector = None
        self.conversation_analyzer = None
        self._agents: Dict[str, IAgent] = {}
        self._initialized = False

    async def initialize(self):
        """Initialize orchestrator components"""
        if self._initialized:
            return

        try:
            # Initialize model registry
            self.registry = await get_model_registry()

            # Initialize database
            self.db_manager = await get_db_manager()

            # Initialize memory manager
            self.memory_manager = await get_memory_manager()

            # Initialize tool registry
            self.tool_registry = await get_tool_registry()

            # Initialize RAG system
            try:
                self.rag_system = await get_rag_system()
                logger.info("RAG system initialized")
            except Exception as e:
                logger.warning(f"RAG system initialization failed: {e}")
                self.rag_system = None

            # Initialize persona manager
            try:
                self.persona_manager = await get_persona_manager()
                logger.info("Persona manager initialized")
            except Exception as e:
                logger.warning(f"Persona manager initialization failed: {e}")
                self.persona_manager = None

            # Initialize template engine
            try:
                self.template_engine = await get_template_engine()
                logger.info("Template engine initialized")
            except Exception as e:
                logger.warning(f"Template engine initialization failed: {e}")
                self.template_engine = None

            # Initialize analytics
            try:
                self.metrics_collector = await get_metrics_collector()
                logger.info("Metrics collector initialized")
            except Exception as e:
                logger.warning(f"Metrics collector initialization failed: {e}")
                self.metrics_collector = None

            try:
                self.conversation_analyzer = await get_conversation_analyzer()
                logger.info("Conversation analyzer initialized")
            except Exception as e:
                logger.warning(f"Conversation analyzer initialization failed: {e}")
                self.conversation_analyzer = None

            # Initialize default agents
            await self._initialize_agents()

            self._initialized = True
            logger.info("AGI Orchestrator initialized")

        except Exception as e:
            logger.error(f"Failed to initialize orchestrator: {e}")
            raise

    async def _initialize_agents(self):
        """Initialize default agents"""
        # Get relevant tools for general agent
        tools = []
        if self.tool_registry:
            # Load essential tools
            tool_names = ["calculator", "web_search", "python_code"]
            for name in tool_names:
                tool = self.tool_registry.get_tool(name)
                if tool:
                    tools.append(tool)

        # Create a general purpose agent with tools
        general_agent = BaseAgent(
            name="general",
            model_id=None,  # Will use task-based selection
            tools=tools,
            memory=self.memory_manager,
            auto_load_tools=False  # We're providing tools explicitly
        )
        self._agents["general"] = general_agent

        logger.info(f"Initialized {len(self._agents)} agents with {len(tools)} tools")

    async def process_request(
        self,
        request: str,
        context: ConversationContext,
        stream: bool = False
    ) -> Any:
        """
        Process a request

        Args:
            request: User request
            context: Conversation context
            stream: Whether to stream response

        Returns:
            Response (string or async generator)
        """
        if not self._initialized:
            await self.initialize()

        try:
            # Record request metrics
            if self.metrics_collector:
                start_time = time.time()
                await self.metrics_collector.record(
                    MetricType.REQUESTS_PER_SESSION,
                    1,
                    session_id=context.session_id
                )

            # Analyze request complexity
            task_type = await self._analyze_request(request)

            # Check if agent is needed
            if self._requires_agent(task_type, request):
                return await self._process_with_agent(request, context)

            # Select model for direct response
            model_id = await self.select_model(task_type)
            model = await self.registry.get_model(model_id)

            if not model:
                raise RuntimeError(f"Failed to load model {model_id}")

            # Record model selection
            if self.metrics_collector:
                await self.metrics_collector.record(
                    MetricType.MODEL_SELECTION,
                    1,
                    session_id=context.session_id,
                    metadata={'model_id': model_id, 'task_type': task_type}
                )

            # Store request in database and memory
            await self._store_conversation(context, "user", request)

            # Add to working memory
            await self.memory_manager.working_memory.store(
                f"{context.session_id}_{datetime.now().timestamp()}",
                request,
                {"role": "user", "session_id": context.session_id}
            )

            # Generate response
            if stream:
                # Return the async generator directly
                return self._stream_response(model, request, context)
            else:
                response = await self._generate_response(model, request, context)

                # Store response
                await self._store_conversation(context, "assistant", response)

                # Add to working memory
                await self.memory_manager.working_memory.store(
                    f"{context.session_id}_{datetime.now().timestamp()}_response",
                    response,
                    {"role": "assistant", "session_id": context.session_id}
                )

                # Record metrics
                if self.metrics_collector:
                    await self.metrics_collector.record_timing(
                        MetricType.RESPONSE_TIME,
                        start_time,
                        session_id=context.session_id
                    )

                    # Estimate token usage (rough estimate)
                    token_count = len(request.split()) + len(response.split())
                    await self.metrics_collector.record(
                        MetricType.TOKEN_USAGE,
                        token_count * 1.3,  # Rough tokenization factor
                        session_id=context.session_id
                    )

                # Analyze conversation if analyzer is available
                if self.conversation_analyzer:
                    try:
                        messages = [
                            {'role': 'user', 'content': request},
                            {'role': 'assistant', 'content': response}
                        ]
                        analysis = await self.conversation_analyzer.analyze_conversation(
                            context.session_id,
                            messages
                        )
                        logger.debug(f"Conversation analysis: quality={analysis.quality_score:.2f}")
                    except Exception as e:
                        logger.warning(f"Conversation analysis failed: {e}")

                return response

        except Exception as e:
            logger.error(f"Request processing failed: {e}")

            # Record error metrics
            if self.metrics_collector:
                await self.metrics_collector.record(
                    MetricType.ERROR_RATE,
                    1,
                    session_id=context.session_id,
                    metadata={'error': str(e)}
                )

            return await self.handle_failure(e, context)

    async def _analyze_request(self, request: str) -> str:
        """
        Analyze request to determine task type

        Args:
            request: User request

        Returns:
            Task type
        """
        request_lower = request.lower()

        # Simple heuristics for task classification
        if any(word in request_lower for word in ["explain", "what is", "define", "tell me"]):
            return "simple_qa"

        elif any(word in request_lower for word in ["analyze", "compare", "evaluate"]):
            return "analysis"

        elif any(word in request_lower for word in ["create", "generate", "write"]):
            return "creative"

        elif any(word in request_lower for word in ["solve", "calculate", "reason"]):
            return "reasoning"

        elif any(word in request_lower for word in ["code", "program", "function", "debug"]):
            return "code"

        else:
            return "conversation"

    def _requires_agent(self, task_type: str, request: str) -> bool:
        """
        Determine if request requires an agent

        Args:
            task_type: Type of task
            request: User request

        Returns:
            Whether agent is needed
        """
        # Complex tasks that benefit from planning
        agent_tasks = ["complex_reasoning", "multi_step", "research"]

        # Check for multi-step indicators
        multi_step_words = ["then", "after that", "next", "finally", "step by step"]

        # Check for tool-related keywords
        tool_words = ["calculate", "search", "find", "web", "python", "code", "file", "database"]

        if task_type in agent_tasks:
            return True

        if any(word in request.lower() for word in multi_step_words):
            return True

        # If request mentions tools, use agent
        if any(word in request.lower() for word in tool_words):
            return True

        # Check request length (complex requests tend to be longer)
        if len(request.split()) > 50:
            return True

        return False

    async def _process_with_agent(
        self,
        request: str,
        context: ConversationContext
    ) -> str:
        """
        Process request using an agent

        Args:
            request: User request
            context: Conversation context

        Returns:
            Agent response
        """
        # Analyze request to determine needed tools
        needed_tools = await self._select_tools_for_request(request)

        # Create task for agent
        task = AgentTask(
            id=f"task_{datetime.now().timestamp()}",
            description=request,
            context=context,
            tools=needed_tools,
            constraints={"max_steps": 10, "timeout": 60}
        )

        # Select agent and provide tools if needed
        agent = await self.select_agent(task)
        if needed_tools and not agent.tools:
            agent.tools = needed_tools

        # Execute task
        result = await agent.execute(task)

        if result.success:
            # Format agent result as response
            response = self._format_agent_result(result)
            await self._store_conversation(context, "assistant", response)
            return response
        else:
            error_msg = f"Agent execution failed: {result.error}"
            logger.error(error_msg)
            return error_msg

    async def _generate_response(
        self,
        model: IModel,
        request: str,
        context: ConversationContext
    ) -> str:
        """
        Generate response using model

        Args:
            model: Model to use
            request: User request
            context: Conversation context

        Returns:
            Generated response
        """
        # Build prompt with context
        prompt = await self._build_prompt(request, context)

        # Generate response
        response = await model.generate(
            prompt=prompt,
            temperature=self.config.models.temperature_default,
            max_tokens=self.config.models.max_tokens_default
        )

        return response

    async def _stream_response(
        self,
        model: IModel,
        request: str,
        context: ConversationContext
    ) -> AsyncIterator[str]:
        """
        Stream response from model

        Args:
            model: Model to use
            request: User request
            context: Conversation context

        Yields:
            Response chunks
        """
        # Build prompt with context
        prompt = await self._build_prompt(request, context)

        # Store request
        await self._store_conversation(context, "user", request)

        # Stream response
        full_response = ""
        async for chunk in model.generate_stream(
            prompt=prompt,
            temperature=self.config.models.temperature_default,
            max_tokens=self.config.models.max_tokens_default
        ):
            full_response += chunk
            yield chunk

        # Store complete response
        await self._store_conversation(context, "assistant", full_response)

    async def _build_prompt(self, request: str, context: ConversationContext) -> str:
        """
        Build prompt with conversation context, memory, RAG, and persona

        Args:
            request: User request
            context: Conversation context

        Returns:
            Complete prompt
        """
        # Start with system message - check for persona
        prompt_parts = []

        # Use persona if available
        if self.persona_manager and context.metadata and "persona_id" in context.metadata:
            persona = await self.persona_manager.get_persona(context.metadata["persona_id"])
            if persona:
                system_prompt = self.persona_manager.build_system_prompt(
                    persona,
                    {"request": request, "session_id": context.session_id}
                )
                prompt_parts.append(f"System: {system_prompt}")
        elif context.metadata and "persona" in context.metadata:
            prompt_parts.append(f"System: {context.metadata['persona']}")

        # Get RAG context if available
        if self.rag_system and self._should_use_rag(request):
            try:
                rag_results = await self.rag_system.search(
                    query=request,
                    limit=3,
                    threshold=0.6
                )
                if rag_results:
                    prompt_parts.append("Knowledge Base Context:")
                    for result in rag_results[:2]:  # Use top 2 results
                        prompt_parts.append(f"- {result['content'][:300]}... (from: {result['document_title']})")
            except Exception as e:
                logger.warning(f"RAG search failed: {e}")

        # Get relevant memories
        if self.memory_manager:
            # Get working memory context
            working_context = await self.memory_manager.working_memory.get_context(limit=5)
            if working_context:
                prompt_parts.append("Recent Context:")
                for item in working_context:
                    prompt_parts.append(f"- {item['value']}")

            # Check for relevant episodic memories
            similar_episodes = await self.memory_manager.episodic_memory.recall_similar(
                {"request": request}, limit=2
            )
            if similar_episodes:
                prompt_parts.append("\nRelevant Past Experiences:")
                for episode_data in similar_episodes[:2]:
                    episode = episode_data["episode"]
                    prompt_parts.append(f"- {episode.get('context', {})}")

        # Add conversation history
        for message in context.messages[-10:]:  # Last 10 messages
            role = message.role.value if hasattr(message.role, 'value') else message.role
            prompt_parts.append(f"{role.capitalize()}: {message.content}")

        # Add current request
        prompt_parts.append(f"User: {request}")
        prompt_parts.append("Assistant:")

        # Use template engine if available and template specified
        if self.template_engine and context.metadata and "template_id" in context.metadata:
            template = await self.template_engine.get_template(context.metadata["template_id"])
            if template:
                # Prepare variables for template
                template_vars = {
                    "question": request,
                    "context": "\n\n".join(prompt_parts[:-2]) if len(prompt_parts) > 2 else "",
                    "conversation_history": [
                        {"role": msg.role.value if hasattr(msg.role, 'value') else msg.role,
                         "content": msg.content}
                        for msg in context.messages[-10:]
                    ],
                    "session_id": context.session_id
                }

                # Add any custom variables from metadata
                if "template_vars" in context.metadata:
                    template_vars.update(context.metadata["template_vars"])

                # Render template
                rendered = self.template_engine.render(template, template_vars)
                return rendered

        return "\n\n".join(prompt_parts)

    def _should_use_rag(self, request: str) -> bool:
        """Determine if RAG should be used for this request"""
        # Check for knowledge-seeking patterns
        rag_indicators = [
            "what is", "what are", "explain", "describe", "tell me about",
            "how does", "how do", "why", "when", "where", "who",
            "define", "definition", "meaning", "information about"
        ]

        request_lower = request.lower()
        return any(indicator in request_lower for indicator in rag_indicators)

    async def _store_conversation(
        self,
        context: ConversationContext,
        role: str,
        content: str
    ):
        """Store conversation message in database"""
        try:
            await self.db_manager.add_conversation_message(
                session_id=context.session_id,
                role=role,
                content=content,
                metadata=context.metadata
            )
        except Exception as e:
            logger.error(f"Failed to store conversation: {e}")

    def _format_agent_result(self, result: Any) -> str:
        """Format agent result as human-readable response"""
        if isinstance(result.result, list):
            # Format step results
            response_parts = []
            for step_result in result.result:
                if step_result.get("type") == "think":
                    response_parts.append(step_result.get("thought", ""))
                elif step_result.get("type") == "tool":
                    response_parts.append(f"Used tool: {step_result.get('tool', 'unknown')}")
                    if step_result.get("result"):
                        response_parts.append(str(step_result["result"]))

            return "\n\n".join(filter(None, response_parts))
        else:
            return str(result.result)

    async def select_model(self, task_type: str) -> str:
        """
        Select appropriate model for task

        Args:
            task_type: Type of task

        Returns:
            Model ID
        """
        # Get recommended model size
        routing_rules = self.config.models.routing_rules
        recommended_size = routing_rules.get(task_type, ModelSize.SMALL)

        # Get available models
        models = await self.registry.list_models()

        if not models:
            raise RuntimeError("No models available")

        # Try to get model by size
        size_to_models = self.config.models.size_to_models
        candidates = []

        # Map actual model files to size categories
        for model_id in models:
            model_name = model_id.lower()
            if "0.5b" in model_name or "0_5b" in model_name:
                if recommended_size == ModelSize.TINY:
                    candidates.append(model_id)
            elif "1b" in model_name:
                if recommended_size == ModelSize.TINY:
                    candidates.append(model_id)
            elif "3b" in model_name:
                if recommended_size == ModelSize.SMALL:
                    candidates.append(model_id)
            elif "7b" in model_name or "8b" in model_name:
                if recommended_size == ModelSize.MEDIUM:
                    candidates.append(model_id)
            elif "32b" in model_name:
                if recommended_size == ModelSize.LARGE:
                    candidates.append(model_id)
            elif "70b" in model_name:
                if recommended_size == ModelSize.XLARGE:
                    candidates.append(model_id)

        # Return first candidate or default to first available model
        if candidates:
            return candidates[0]
        else:
            # Fallback to smallest available model
            return models[0]

    async def _select_tools_for_request(self, request: str) -> List[ITool]:
        """
        Select appropriate tools based on request

        Args:
            request: User request

        Returns:
            List of relevant tools
        """
        if not self.tool_registry:
            return []

        # Use tool registry's built-in selection
        tools = self.tool_registry.get_tools_for_task(request)

        # If no specific tools found, provide general tools
        if not tools:
            default_tools = ["calculator", "web_search"]
            tools = [self.tool_registry.get_tool(name) for name in default_tools]
            tools = [t for t in tools if t is not None]

        return tools

    async def select_agent(self, task: AgentTask) -> IAgent:
        """
        Select appropriate agent for task

        Args:
            task: Task to execute

        Returns:
            Selected agent
        """
        # For now, return general agent
        # In future, can select based on task requirements
        agent = self._agents.get("general")
        if not agent:
            # Create default agent if not found
            agent = BaseAgent(
                name="default",
                model_id=None,
                tools=task.tools or [],
                memory=self.memory_manager
            )
        return agent

    async def handle_failure(
        self,
        error: Exception,
        context: ConversationContext
    ) -> Any:
        """
        Handle failure with fallback

        Args:
            error: Exception that occurred
            context: Conversation context

        Returns:
            Fallback response
        """
        error_message = f"I encountered an error: {str(error)}. Please try rephrasing your request."

        # Log error
        logger.error(f"Orchestrator error: {error}", exc_info=True)

        # Store error in conversation
        await self._store_conversation(
            context,
            "system",
            f"Error: {str(error)}"
        )

        return error_message

# Singleton instance
_orchestrator: Optional[AGIOrchestrator] = None

async def get_orchestrator() -> AGIOrchestrator:
    """Get singleton orchestrator instance"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AGIOrchestrator()
        await _orchestrator.initialize()
    return _orchestrator