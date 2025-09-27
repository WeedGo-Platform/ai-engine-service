"""
Specialized Agent Types for Multi-Agent System
Different agent roles with specific capabilities
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import re

from agi.agents.base_agent import BaseAgent
from agi.core.interfaces import AgentTask, AgentResult, AgentState
from agi.knowledge.rag_system import get_rag_system
from agi.tools import get_tool_registry
from agi.learning import get_pattern_engine, get_feedback_collector

logger = logging.getLogger(__name__)


class ResearchAgent(BaseAgent):
    """
    Agent specialized in research and information gathering
    """

    def __init__(self, name: str = "ResearchAgent"):
        """Initialize research agent"""
        super().__init__(
            name=name,
            model_id="claude-3-sonnet",  # Good for research tasks
            auto_load_tools=True
        )
        self.rag_system = None
        self._research_history = []

    async def initialize(self):
        """Initialize research-specific components"""
        await self._initialize_tools()
        self.rag_system = await get_rag_system()

        # Add research-specific tools
        tool_registry = await get_tool_registry()
        web_search = tool_registry.get_tool("web_search")
        if web_search:
            self.tools.append(web_search)

    async def plan(self, task: AgentTask) -> List[Dict[str, Any]]:
        """Create research-specific plan"""
        # Analyze task for research needs
        research_keywords = self._extract_research_keywords(task.description)

        plan = [
            {
                "type": "think",
                "description": "Identify research objectives",
                "prompt": f"What are the key research questions for: {task.description}",
                "critical": True
            },
            {
                "type": "tool",
                "description": "Search existing knowledge base",
                "tool": "rag_search",
                "parameters": {"query": " ".join(research_keywords)},
                "critical": False
            }
        ]

        # Add web search steps if needed
        if any(keyword in task.description.lower() for keyword in ["latest", "current", "recent", "news"]):
            plan.append({
                "type": "tool",
                "description": "Search web for current information",
                "tool": "web_search",
                "parameters": {"query": task.description},
                "critical": False
            })

        # Add analysis steps
        plan.extend([
            {
                "type": "think",
                "description": "Analyze gathered information",
                "prompt": "Synthesize the research findings",
                "critical": True
            },
            {
                "type": "think",
                "description": "Identify gaps and contradictions",
                "prompt": "What information is missing or contradictory?",
                "critical": False
            },
            {
                "type": "decide",
                "description": "Determine if more research is needed",
                "options": ["sufficient", "need_more"],
                "critical": False
            }
        ])

        return plan

    def _extract_research_keywords(self, text: str) -> List[str]:
        """Extract key research terms from text"""
        # Remove common words
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}

        # Extract important words
        words = re.findall(r'\b\w+\b', text.lower())
        keywords = [w for w in words if w not in stop_words and len(w) > 3]

        return keywords[:10]  # Top 10 keywords

    async def _execute_tool_step(self, step: Dict[str, Any], task: AgentTask) -> Dict[str, Any]:
        """Execute research-specific tools"""
        tool_name = step.get("tool")

        if tool_name == "rag_search" and self.rag_system:
            # Use RAG system for knowledge retrieval
            query = step.get("parameters", {}).get("query", task.description)
            results = await self.rag_system.search(query, top_k=5)

            self._research_history.append({
                "source": "knowledge_base",
                "query": query,
                "results": results,
                "timestamp": datetime.utcnow().isoformat()
            })

            return {
                "success": True,
                "type": "tool",
                "tool": "rag_search",
                "result": results
            }

        return await super()._execute_tool_step(step, task)

    def get_capabilities(self) -> Dict[str, Any]:
        """Get research agent capabilities"""
        capabilities = super().get_capabilities()
        capabilities.update({
            "specialization": "research",
            "skills": ["information_gathering", "knowledge_retrieval", "web_search", "analysis"],
            "has_rag": self.rag_system is not None
        })
        return capabilities


class AnalystAgent(BaseAgent):
    """
    Agent specialized in data analysis and pattern recognition
    """

    def __init__(self, name: str = "AnalystAgent"):
        """Initialize analyst agent"""
        super().__init__(
            name=name,
            model_id="claude-3-opus",  # Best for complex analysis
            auto_load_tools=True
        )
        self.pattern_engine = None
        self._analysis_cache = {}

    async def initialize(self):
        """Initialize analysis-specific components"""
        await self._initialize_tools()
        self.pattern_engine = await get_pattern_engine()

        # Add analysis tools
        tool_registry = await get_tool_registry()
        calculator = tool_registry.get_tool("calculator")
        if calculator:
            self.tools.append(calculator)

    async def plan(self, task: AgentTask) -> List[Dict[str, Any]]:
        """Create analysis-specific plan"""
        plan = [
            {
                "type": "observe",
                "description": "Examine input data",
                "critical": True
            },
            {
                "type": "think",
                "description": "Identify patterns and anomalies",
                "prompt": "What patterns or anomalies exist in this data?",
                "critical": True
            }
        ]

        # Add calculation steps if needed
        if any(keyword in task.description.lower() for keyword in ["calculate", "compute", "sum", "average"]):
            plan.append({
                "type": "tool",
                "description": "Perform calculations",
                "tool": "calculator",
                "parameters": {},  # Will be filled during execution
                "critical": True
            })

        plan.extend([
            {
                "type": "think",
                "description": "Statistical analysis",
                "prompt": "What are the statistical insights?",
                "critical": False
            },
            {
                "type": "think",
                "description": "Draw conclusions",
                "prompt": "What conclusions can we draw from this analysis?",
                "critical": True
            },
            {
                "type": "decide",
                "description": "Determine confidence level",
                "options": ["high_confidence", "medium_confidence", "low_confidence"],
                "critical": False
            }
        ])

        return plan

    async def analyze_patterns(self, data: Any) -> Dict[str, Any]:
        """Analyze patterns in data"""
        if self.pattern_engine:
            # Use pattern recognition engine
            from agi.core.interfaces import ConversationContext, Message

            # Create context from data
            context = ConversationContext(
                session_id="analysis_session",
                messages=[Message(role="user", content=str(data))]
            )

            patterns = await self.pattern_engine.recognize_patterns(context)

            return {
                "patterns_found": len(patterns),
                "patterns": [p.pattern.to_dict() for p in patterns[:5]],
                "confidence": sum(p.match_confidence for p in patterns) / max(len(patterns), 1)
            }

        return {"patterns_found": 0, "patterns": [], "confidence": 0.0}


class ExecutorAgent(BaseAgent):
    """
    Agent specialized in executing actions and using tools
    """

    def __init__(self, name: str = "ExecutorAgent"):
        """Initialize executor agent"""
        super().__init__(
            name=name,
            model_id="gpt-4",  # Good for tool use
            auto_load_tools=True
        )
        self._execution_log = []

    async def initialize(self):
        """Initialize executor-specific components"""
        await self._initialize_tools()

        # Load all available tools
        tool_registry = await get_tool_registry()
        all_tools = tool_registry.list_tools()

        # Add tools not already loaded
        for tool_def in all_tools:
            tool = tool_registry.get_tool(tool_def.name)
            if tool and tool not in self.tools:
                self.tools.append(tool)

    async def plan(self, task: AgentTask) -> List[Dict[str, Any]]:
        """Create execution-specific plan"""
        # Identify required tools
        required_tools = self._identify_required_tools(task.description)

        plan = [
            {
                "type": "think",
                "description": "Prepare execution strategy",
                "prompt": "What is the best execution order?",
                "critical": True
            }
        ]

        # Add tool execution steps
        for tool_name in required_tools:
            plan.append({
                "type": "tool",
                "description": f"Execute {tool_name}",
                "tool": tool_name,
                "parameters": {},  # Will be determined during execution
                "critical": True
            })

        plan.extend([
            {
                "type": "observe",
                "description": "Verify execution results",
                "critical": True
            },
            {
                "type": "decide",
                "description": "Determine if retry is needed",
                "options": ["success", "retry", "fail"],
                "critical": False
            }
        ])

        return plan

    def _identify_required_tools(self, description: str) -> List[str]:
        """Identify which tools are needed"""
        required = []

        # Map keywords to tools
        tool_keywords = {
            "calculator": ["calculate", "compute", "math", "sum", "average"],
            "web_search": ["search", "find", "lookup", "google"],
            "python_code": ["code", "script", "program", "python"],
            "file_system": ["file", "read", "write", "save"],
            "database": ["query", "database", "sql", "table"]
        }

        description_lower = description.lower()

        for tool_name, keywords in tool_keywords.items():
            if any(keyword in description_lower for keyword in keywords):
                # Check if we have this tool
                if any(t.get_definition().name == tool_name for t in self.tools):
                    required.append(tool_name)

        return required


class ValidatorAgent(BaseAgent):
    """
    Agent specialized in validation and quality assurance
    """

    def __init__(self, name: str = "ValidatorAgent"):
        """Initialize validator agent"""
        super().__init__(
            name=name,
            model_id="claude-3-sonnet",
            auto_load_tools=False  # Validators focus on checking, not executing
        )
        self.feedback_collector = None
        self._validation_criteria = {}

    async def initialize(self):
        """Initialize validator-specific components"""
        self.feedback_collector = await get_feedback_collector()

    async def plan(self, task: AgentTask) -> List[Dict[str, Any]]:
        """Create validation-specific plan"""
        plan = [
            {
                "type": "think",
                "description": "Define validation criteria",
                "prompt": "What are the success criteria for this task?",
                "critical": True
            },
            {
                "type": "observe",
                "description": "Examine results to validate",
                "critical": True
            },
            {
                "type": "think",
                "description": "Check correctness",
                "prompt": "Are the results correct and complete?",
                "critical": True
            },
            {
                "type": "think",
                "description": "Check quality",
                "prompt": "Does the quality meet standards?",
                "critical": False
            },
            {
                "type": "think",
                "description": "Identify issues",
                "prompt": "What issues or improvements are needed?",
                "critical": False
            },
            {
                "type": "decide",
                "description": "Validation decision",
                "options": ["approved", "needs_revision", "rejected"],
                "critical": True
            }
        ]

        return plan

    async def validate_result(
        self,
        result: Any,
        criteria: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Validate a result against criteria"""
        validation = {
            "valid": True,
            "score": 1.0,
            "issues": [],
            "suggestions": []
        }

        # Apply validation criteria
        if criteria:
            for criterion, requirement in criteria.items():
                if not self._check_criterion(result, criterion, requirement):
                    validation["valid"] = False
                    validation["score"] *= 0.8
                    validation["issues"].append(f"Failed {criterion}: {requirement}")

        # Record feedback if collector available
        if self.feedback_collector and validation["valid"]:
            await self.feedback_collector.collect_reinforcement(
                session_id="validation_session",
                message_id=str(result),
                success=validation["valid"],
                metric="validation_score",
                value=validation["score"]
            )

        return validation

    def _check_criterion(self, result: Any, criterion: str, requirement: Any) -> bool:
        """Check if result meets a specific criterion"""
        # Implement specific validation logic
        if criterion == "length" and isinstance(result, str):
            return len(result) >= requirement
        elif criterion == "contains" and isinstance(result, str):
            return requirement in result
        elif criterion == "type":
            return isinstance(result, requirement)

        return True


class CoordinatorAgent(BaseAgent):
    """
    Agent that coordinates other agents
    """

    def __init__(self, name: str = "CoordinatorAgent"):
        """Initialize coordinator agent"""
        super().__init__(
            name=name,
            model_id="claude-3-opus",  # Best for complex coordination
            auto_load_tools=False
        )
        self.sub_agents: Dict[str, BaseAgent] = {}
        self._delegation_history = []

    async def initialize(self):
        """Initialize coordinator-specific components"""
        # Create specialized sub-agents
        self.sub_agents = {
            "research": ResearchAgent("research_sub"),
            "analyst": AnalystAgent("analyst_sub"),
            "executor": ExecutorAgent("executor_sub"),
            "validator": ValidatorAgent("validator_sub")
        }

        # Initialize all sub-agents
        for agent in self.sub_agents.values():
            await agent.initialize()

    async def plan(self, task: AgentTask) -> List[Dict[str, Any]]:
        """Create coordination plan"""
        # Analyze task to determine which agents are needed
        required_agents = self._identify_required_agents(task)

        plan = [
            {
                "type": "think",
                "description": "Decompose task into subtasks",
                "prompt": f"How should we break down: {task.description}",
                "critical": True
            }
        ]

        # Add delegation steps
        for agent_type in required_agents:
            plan.append({
                "type": "delegate",
                "description": f"Delegate to {agent_type} agent",
                "agent": agent_type,
                "critical": True
            })

        plan.extend([
            {
                "type": "observe",
                "description": "Collect results from agents",
                "critical": True
            },
            {
                "type": "think",
                "description": "Integrate results",
                "prompt": "How do we combine the agent results?",
                "critical": True
            },
            {
                "type": "delegate",
                "description": "Validate final result",
                "agent": "validator",
                "critical": False
            }
        ])

        return plan

    def _identify_required_agents(self, task: AgentTask) -> List[str]:
        """Identify which agents are needed for a task"""
        required = []
        description_lower = task.description.lower()

        # Map task keywords to agent types
        agent_triggers = {
            "research": ["research", "find", "search", "investigate", "explore"],
            "analyst": ["analyze", "pattern", "statistics", "trends", "insights"],
            "executor": ["execute", "run", "perform", "implement", "create"],
            "validator": ["validate", "check", "verify", "test", "quality"]
        }

        for agent_type, keywords in agent_triggers.items():
            if any(keyword in description_lower for keyword in keywords):
                required.append(agent_type)

        # Default to research and executor if nothing specific
        if not required:
            required = ["research", "executor"]

        return required

    async def _execute_step(self, step: Dict[str, Any], task: AgentTask) -> Dict[str, Any]:
        """Execute coordination-specific steps"""
        if step.get("type") == "delegate":
            return await self._execute_delegation_step(step, task)

        return await super()._execute_step(step, task)

    async def _execute_delegation_step(
        self,
        step: Dict[str, Any],
        task: AgentTask
    ) -> Dict[str, Any]:
        """Delegate to a sub-agent"""
        agent_type = step.get("agent")
        agent = self.sub_agents.get(agent_type)

        if not agent:
            return {
                "success": False,
                "type": "delegate",
                "error": f"Agent {agent_type} not found"
            }

        try:
            # Create subtask for the agent
            subtask = AgentTask(
                id=f"{task.id}_{agent_type}",
                description=task.description,
                context=task.context,
                constraints=task.constraints
            )

            # Execute with the sub-agent
            result = await agent.execute(subtask)

            self._delegation_history.append({
                "agent": agent_type,
                "task": subtask.id,
                "result": result,
                "timestamp": datetime.utcnow().isoformat()
            })

            return {
                "success": result.success,
                "type": "delegate",
                "agent": agent_type,
                "result": result
            }

        except Exception as e:
            return {
                "success": False,
                "type": "delegate",
                "agent": agent_type,
                "error": str(e)
            }

    def get_capabilities(self) -> Dict[str, Any]:
        """Get coordinator capabilities"""
        capabilities = super().get_capabilities()
        capabilities.update({
            "specialization": "coordination",
            "sub_agents": list(self.sub_agents.keys()),
            "delegation": True,
            "orchestration": True
        })
        return capabilities