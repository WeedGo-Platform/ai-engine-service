"""
Base Agent Implementation for AGI System
Implements the planner-executor pattern for autonomous agents
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from abc import abstractmethod
from datetime import datetime
import json

from agi.core.interfaces import (
    IAgent, AgentState, AgentTask, AgentResult,
    IModel, ITool, IMemory, MessageRole, Message
)
from agi.models.registry import get_model_registry
from agi.core.database import get_db_manager
from agi.tools import get_tool_registry

logger = logging.getLogger(__name__)

class BaseAgent(IAgent):
    """
    Base implementation of an autonomous agent with planner-executor pattern

    The agent follows a cycle:
    1. Plan - Decompose task into steps
    2. Execute - Execute each step
    3. Observe - Check results
    4. Reflect - Learn from execution
    """

    def __init__(
        self,
        name: str,
        model_id: Optional[str] = None,
        tools: Optional[List[ITool]] = None,
        memory: Optional[IMemory] = None,
        auto_load_tools: bool = True
    ):
        """
        Initialize base agent

        Args:
            name: Agent name
            model_id: Model to use for reasoning
            tools: Available tools
            memory: Memory system
        """
        self.name = name
        self.model_id = model_id
        self.tools = tools or []
        self.memory = memory
        self.state = AgentState.IDLE
        self.auto_load_tools = auto_load_tools
        self._model: Optional[IModel] = None
        self._current_task: Optional[AgentTask] = None
        self._execution_history: List[Dict[str, Any]] = []
        self._tools_initialized = False

    async def _get_model(self) -> IModel:
        """Get or load the model"""
        if not self._model:
            registry = await get_model_registry()
            if self.model_id:
                self._model = await registry.get_model(self.model_id)
            else:
                # Get default model for reasoning
                self._model = await registry.get_model_for_task("reasoning")
        return self._model

    async def _initialize_tools(self):
        """Initialize tools from registry if needed"""
        if self._tools_initialized:
            return

        if self.auto_load_tools and not self.tools:
            # Load default tools from registry
            tool_registry = await get_tool_registry()
            # Get relevant tools for general tasks
            self.tools = [
                tool_registry.get_tool("calculator"),
                tool_registry.get_tool("web_search"),
                tool_registry.get_tool("python_code")
            ]
            # Remove None values
            self.tools = [t for t in self.tools if t is not None]
            logger.info(f"Agent {self.name} loaded {len(self.tools)} default tools")

        self._tools_initialized = True

    async def plan(self, task: AgentTask) -> List[Dict[str, Any]]:
        """
        Plan how to execute the task

        Args:
            task: Task to plan

        Returns:
            List of planned steps
        """
        self.state = AgentState.PLANNING
        self._current_task = task

        # Initialize tools if needed
        await self._initialize_tools()

        try:
            model = await self._get_model()

            # Create planning prompt
            planning_prompt = self._create_planning_prompt(task)

            # Generate plan using the model
            response = await model.generate(
                prompt=planning_prompt,
                temperature=0.7,
                max_tokens=1024
            )

            # Parse the plan
            plan = self._parse_plan(response)

            # Store plan in memory if available
            if self.memory:
                await self.memory.store(
                    f"plan_{task.id}",
                    json.dumps(plan),
                    ttl=3600  # 1 hour TTL
                )

            logger.info(f"Agent {self.name} created plan with {len(plan)} steps for task {task.id}")
            return plan

        except Exception as e:
            logger.error(f"Planning failed for agent {self.name}: {e}")
            self.state = AgentState.FAILED
            raise

    async def execute(self, task: AgentTask) -> AgentResult:
        """
        Execute the task

        Args:
            task: Task to execute

        Returns:
            Execution result
        """
        self.state = AgentState.EXECUTING
        self._current_task = task
        self._execution_history = []

        try:
            # Get or create plan
            if self.memory:
                stored_plan = await self.memory.retrieve(f"plan_{task.id}")
                if stored_plan:
                    plan = json.loads(stored_plan)
                else:
                    plan = await self.plan(task)
            else:
                plan = await self.plan(task)

            # Execute each step
            results = []
            for step_idx, step in enumerate(plan):
                logger.info(f"Agent {self.name} executing step {step_idx + 1}/{len(plan)}: {step.get('description', 'Unknown')}")

                step_result = await self._execute_step(step, task)
                results.append(step_result)

                self._execution_history.append({
                    "step": step,
                    "result": step_result,
                    "timestamp": datetime.utcnow().isoformat()
                })

                # Check if we should continue
                if not step_result.get("success", False):
                    if step.get("critical", True):
                        logger.warning(f"Critical step failed, stopping execution")
                        break

            # Compile final result
            success = all(r.get("success", False) for r in results)

            self.state = AgentState.COMPLETED if success else AgentState.FAILED

            return AgentResult(
                task_id=task.id,
                success=success,
                result=results,
                steps_taken=self._execution_history,
                metadata={
                    "agent": self.name,
                    "model": self.model_id,
                    "plan_steps": len(plan),
                    "executed_steps": len(results)
                }
            )

        except Exception as e:
            logger.error(f"Execution failed for agent {self.name}: {e}")
            self.state = AgentState.FAILED

            return AgentResult(
                task_id=task.id,
                success=False,
                result=None,
                steps_taken=self._execution_history,
                error=str(e)
            )

    async def _execute_step(
        self,
        step: Dict[str, Any],
        task: AgentTask
    ) -> Dict[str, Any]:
        """
        Execute a single step

        Args:
            step: Step to execute
            task: Parent task

        Returns:
            Step result
        """
        step_type = step.get("type", "think")

        if step_type == "think":
            # Use model to reason about something
            return await self._execute_think_step(step, task)

        elif step_type == "tool":
            # Execute a tool
            return await self._execute_tool_step(step, task)

        elif step_type == "observe":
            # Check current state
            return await self._execute_observe_step(step, task)

        elif step_type == "decide":
            # Make a decision
            return await self._execute_decide_step(step, task)

        else:
            logger.warning(f"Unknown step type: {step_type}")
            return {"success": False, "error": f"Unknown step type: {step_type}"}

    async def _execute_think_step(
        self,
        step: Dict[str, Any],
        task: AgentTask
    ) -> Dict[str, Any]:
        """Execute a thinking/reasoning step"""
        try:
            model = await self._get_model()

            # Create reasoning prompt with context
            prompt = self._create_reasoning_prompt(step, task)

            # Generate response
            response = await model.generate(
                prompt=prompt,
                temperature=0.7,
                max_tokens=512
            )

            return {
                "success": True,
                "type": "think",
                "thought": response,
                "step_description": step.get("description", "Reasoning")
            }

        except Exception as e:
            return {
                "success": False,
                "type": "think",
                "error": str(e)
            }

    async def _execute_tool_step(
        self,
        step: Dict[str, Any],
        task: AgentTask
    ) -> Dict[str, Any]:
        """Execute a tool step"""
        tool_name = step.get("tool")
        tool_params = step.get("parameters", {})

        # Find the tool
        tool = next((t for t in self.tools if t.get_definition().name == tool_name), None)

        if not tool:
            return {
                "success": False,
                "type": "tool",
                "error": f"Tool {tool_name} not found"
            }

        try:
            # Validate input
            valid, error = await tool.validate_input(**tool_params)
            if not valid:
                return {
                    "success": False,
                    "type": "tool",
                    "error": f"Invalid tool parameters: {error}"
                }

            # Execute tool
            result = await tool.execute(**tool_params)

            return {
                "success": result.success,
                "type": "tool",
                "tool": tool_name,
                "result": result.result,
                "error": result.error
            }

        except Exception as e:
            return {
                "success": False,
                "type": "tool",
                "tool": tool_name,
                "error": str(e)
            }

    async def _execute_observe_step(
        self,
        step: Dict[str, Any],
        task: AgentTask
    ) -> Dict[str, Any]:
        """Execute an observation step"""
        # Check execution history and current state
        observation = {
            "steps_completed": len(self._execution_history),
            "last_step": self._execution_history[-1] if self._execution_history else None,
            "current_state": self.state.value
        }

        return {
            "success": True,
            "type": "observe",
            "observation": observation
        }

    async def _execute_decide_step(
        self,
        step: Dict[str, Any],
        task: AgentTask
    ) -> Dict[str, Any]:
        """Execute a decision step"""
        try:
            model = await self._get_model()

            # Create decision prompt
            prompt = self._create_decision_prompt(step, task)

            # Generate decision
            response = await model.generate(
                prompt=prompt,
                temperature=0.3,  # Lower temperature for decisions
                max_tokens=256
            )

            # Parse decision
            decision = self._parse_decision(response)

            return {
                "success": True,
                "type": "decide",
                "decision": decision,
                "reasoning": response
            }

        except Exception as e:
            return {
                "success": False,
                "type": "decide",
                "error": str(e)
            }

    def _create_planning_prompt(self, task: AgentTask) -> str:
        """Create prompt for planning"""
        tools_description = "\n".join([
            f"- {t.get_definition().name}: {t.get_definition().description}"
            for t in self.tools
        ])

        return f"""You are an AI agent that needs to create a plan to complete the following task.

Task: {task.description}

Context:
{json.dumps(task.context.__dict__, default=str, indent=2)}

Available Tools:
{tools_description if tools_description else "No tools available"}

Constraints:
{json.dumps(task.constraints) if task.constraints else "None"}

Create a step-by-step plan to complete this task. For each step, specify:
1. Type: (think/tool/observe/decide)
2. Description: What this step does
3. Tool (if applicable): Which tool to use
4. Parameters (if applicable): Tool parameters
5. Critical: Whether failure should stop execution

Return your plan as a JSON array of steps."""

    def _create_reasoning_prompt(
        self,
        step: Dict[str, Any],
        task: AgentTask
    ) -> str:
        """Create prompt for reasoning"""
        context = ""
        if self._execution_history:
            context = "Previous steps:\n" + "\n".join([
                f"- {h['step'].get('description', 'Unknown')}: {h['result'].get('success', False)}"
                for h in self._execution_history[-3:]  # Last 3 steps
            ])

        return f"""You are an AI agent executing a task.

Current Task: {task.description}

Current Step: {step.get('description', 'Reasoning')}

{context}

Question: {step.get('prompt', 'What should we consider or analyze for this step?')}

Provide your reasoning:"""

    def _create_decision_prompt(
        self,
        step: Dict[str, Any],
        task: AgentTask
    ) -> str:
        """Create prompt for decision making"""
        return f"""You are an AI agent that needs to make a decision.

Task Context: {task.description}

Decision Required: {step.get('description', 'Make a decision')}

Options: {json.dumps(step.get('options', []))}

Execution History:
{json.dumps(self._execution_history[-5:], default=str, indent=2)}

Based on the context and history, what is the best decision? Explain your reasoning and provide a clear decision."""

    def _parse_plan(self, response: str) -> List[Dict[str, Any]]:
        """Parse plan from model response"""
        try:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())

            # Fallback: Create basic plan
            return [
                {
                    "type": "think",
                    "description": "Analyze the task",
                    "critical": True
                },
                {
                    "type": "execute",
                    "description": "Execute the main task",
                    "critical": True
                },
                {
                    "type": "observe",
                    "description": "Check results",
                    "critical": False
                }
            ]
        except Exception as e:
            logger.error(f"Failed to parse plan: {e}")
            return [{
                "type": "think",
                "description": "Execute task",
                "critical": True
            }]

    def _parse_decision(self, response: str) -> str:
        """Parse decision from model response"""
        # Extract key decision phrases
        decision_keywords = ["decide", "choose", "select", "option", "best"]

        lines = response.split('\n')
        for line in lines:
            if any(keyword in line.lower() for keyword in decision_keywords):
                return line.strip()

        # Return first non-empty line as fallback
        return next((line.strip() for line in lines if line.strip()), "Continue")

    def get_capabilities(self) -> Dict[str, Any]:
        """Get agent capabilities"""
        return {
            "name": self.name,
            "model": self.model_id,
            "tools": [t.get_definition().name for t in self.tools],
            "has_memory": self.memory is not None,
            "planning": True,
            "execution": True,
            "reflection": True
        }

    def get_state(self) -> AgentState:
        """Get current agent state"""
        return self.state