"""
Multi-Agent Collaboration Protocol
Enables agents to work together on complex tasks
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from abc import ABC, abstractmethod
import json

from agi.core.interfaces import IAgent, ConversationContext, Message, MessageRole
from agi.agents.coordinator import CoordinatorAgent
from agi.agents.research import ResearchAgent
from agi.agents.analyst import AnalystAgent
from agi.agents.executor import ExecutorAgent
from agi.agents.validator import ValidatorAgent

logger = logging.getLogger(__name__)


class CollaborationMode(Enum):
    """Agent collaboration modes"""
    SEQUENTIAL = "sequential"      # Agents work in sequence
    PARALLEL = "parallel"          # Agents work in parallel
    HIERARCHICAL = "hierarchical"  # Lead agent delegates to others
    CONSENSUS = "consensus"        # All agents must agree
    COMPETITIVE = "competitive"    # Agents compete for best solution


class AgentRole(Enum):
    """Roles in collaboration"""
    LEADER = "leader"
    CONTRIBUTOR = "contributor"
    REVIEWER = "reviewer"
    OBSERVER = "observer"


@dataclass
class CollaborationTask:
    """Task for collaborative execution"""
    id: str
    description: str
    requirements: List[str]
    constraints: List[str]
    priority: int
    deadline: Optional[datetime] = None
    assigned_agents: List[str] = field(default_factory=list)
    subtasks: List['CollaborationTask'] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    status: str = "pending"
    results: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentMessage:
    """Message between agents"""
    sender: str
    recipient: str
    message_type: str
    content: Any
    timestamp: datetime = field(default_factory=datetime.utcnow)
    requires_response: bool = False
    correlation_id: Optional[str] = None


@dataclass
class CollaborationState:
    """State of ongoing collaboration"""
    task: CollaborationTask
    mode: CollaborationMode
    participants: Dict[str, AgentRole]
    messages: List[AgentMessage]
    decisions: List[Dict[str, Any]]
    start_time: datetime
    end_time: Optional[datetime] = None
    outcome: Optional[Dict[str, Any]] = None


class CollaborationProtocol(ABC):
    """Base class for collaboration protocols"""

    @abstractmethod
    async def execute(
        self,
        task: CollaborationTask,
        agents: Dict[str, IAgent],
        context: ConversationContext
    ) -> Dict[str, Any]:
        """Execute collaboration protocol"""
        pass

    @abstractmethod
    async def coordinate_agents(
        self,
        agents: Dict[str, IAgent],
        task: CollaborationTask
    ) -> List[Tuple[str, Any]]:
        """Coordinate agent activities"""
        pass


class SequentialCollaboration(CollaborationProtocol):
    """Sequential collaboration - agents work one after another"""

    async def execute(
        self,
        task: CollaborationTask,
        agents: Dict[str, IAgent],
        context: ConversationContext
    ) -> Dict[str, Any]:
        """Execute sequential collaboration"""
        results = {}
        previous_output = None

        for agent_id in task.assigned_agents:
            if agent_id not in agents:
                logger.warning(f"Agent {agent_id} not found")
                continue

            agent = agents[agent_id]

            # Prepare input with previous agent's output
            agent_input = {
                "task": task.description,
                "requirements": task.requirements,
                "previous_output": previous_output,
                "context": context
            }

            # Execute agent
            try:
                logger.info(f"Sequential execution: {agent_id} processing task")
                output = await agent.process(
                    task.description,
                    context
                )
                results[agent_id] = output
                previous_output = output

            except Exception as e:
                logger.error(f"Agent {agent_id} failed: {e}")
                results[agent_id] = {"error": str(e)}

        return {
            "mode": "sequential",
            "results": results,
            "final_output": previous_output
        }

    async def coordinate_agents(
        self,
        agents: Dict[str, IAgent],
        task: CollaborationTask
    ) -> List[Tuple[str, Any]]:
        """Coordinate sequential execution"""
        coordination = []

        for i, agent_id in enumerate(task.assigned_agents):
            coordination.append((
                agent_id,
                {
                    "order": i + 1,
                    "wait_for": task.assigned_agents[i-1] if i > 0 else None,
                    "pass_output_to": task.assigned_agents[i+1] if i < len(task.assigned_agents)-1 else None
                }
            ))

        return coordination


class ParallelCollaboration(CollaborationProtocol):
    """Parallel collaboration - agents work simultaneously"""

    async def execute(
        self,
        task: CollaborationTask,
        agents: Dict[str, IAgent],
        context: ConversationContext
    ) -> Dict[str, Any]:
        """Execute parallel collaboration"""
        tasks = []

        for agent_id in task.assigned_agents:
            if agent_id not in agents:
                logger.warning(f"Agent {agent_id} not found")
                continue

            agent = agents[agent_id]
            tasks.append(self._execute_agent(agent, agent_id, task, context))

        # Execute all agents in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        agent_results = {}
        for agent_id, result in zip(task.assigned_agents, results):
            if isinstance(result, Exception):
                agent_results[agent_id] = {"error": str(result)}
            else:
                agent_results[agent_id] = result

        # Aggregate results
        aggregated = self._aggregate_results(agent_results)

        return {
            "mode": "parallel",
            "results": agent_results,
            "aggregated": aggregated
        }

    async def _execute_agent(
        self,
        agent: IAgent,
        agent_id: str,
        task: CollaborationTask,
        context: ConversationContext
    ) -> Any:
        """Execute single agent"""
        logger.info(f"Parallel execution: {agent_id} processing task")
        return await agent.process(task.description, context)

    def _aggregate_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate parallel results"""
        # Simple aggregation - can be customized
        successful = [r for r in results.values() if "error" not in r]

        if not successful:
            return {"status": "all_failed", "results": results}

        return {
            "status": "completed",
            "successful_agents": len(successful),
            "total_agents": len(results),
            "combined_output": successful
        }

    async def coordinate_agents(
        self,
        agents: Dict[str, IAgent],
        task: CollaborationTask
    ) -> List[Tuple[str, Any]]:
        """Coordinate parallel execution"""
        coordination = []

        for agent_id in task.assigned_agents:
            coordination.append((
                agent_id,
                {
                    "execution": "parallel",
                    "can_start": "immediately",
                    "coordination": "independent"
                }
            ))

        return coordination


class HierarchicalCollaboration(CollaborationProtocol):
    """Hierarchical collaboration - lead agent delegates to others"""

    def __init__(self, leader_id: str):
        self.leader_id = leader_id

    async def execute(
        self,
        task: CollaborationTask,
        agents: Dict[str, IAgent],
        context: ConversationContext
    ) -> Dict[str, Any]:
        """Execute hierarchical collaboration"""
        if self.leader_id not in agents:
            raise ValueError(f"Leader agent {self.leader_id} not found")

        leader = agents[self.leader_id]
        subordinates = {
            aid: agent for aid, agent in agents.items()
            if aid != self.leader_id and aid in task.assigned_agents
        }

        # Leader analyzes task and creates delegation plan
        logger.info(f"Hierarchical: Leader {self.leader_id} analyzing task")
        delegation_plan = await self._create_delegation_plan(
            leader, task, list(subordinates.keys()), context
        )

        # Execute delegated tasks
        subordinate_results = {}
        for agent_id, delegated_task in delegation_plan.items():
            if agent_id in subordinates:
                logger.info(f"Hierarchical: Delegating to {agent_id}")
                result = await subordinates[agent_id].process(
                    delegated_task,
                    context
                )
                subordinate_results[agent_id] = result

        # Leader synthesizes results
        logger.info(f"Hierarchical: Leader synthesizing results")
        final_result = await leader.process(
            f"Synthesize these results for task '{task.description}': {json.dumps(subordinate_results)}",
            context
        )

        return {
            "mode": "hierarchical",
            "leader": self.leader_id,
            "delegation_plan": delegation_plan,
            "subordinate_results": subordinate_results,
            "final_result": final_result
        }

    async def _create_delegation_plan(
        self,
        leader: IAgent,
        task: CollaborationTask,
        subordinates: List[str],
        context: ConversationContext
    ) -> Dict[str, str]:
        """Create delegation plan"""
        prompt = f"""
        As the lead agent, create a delegation plan for this task:
        Task: {task.description}
        Requirements: {', '.join(task.requirements)}
        Available agents: {', '.join(subordinates)}

        Create specific subtasks for each agent.
        """

        response = await leader.process(prompt, context)

        # Parse response into delegation plan
        # Simple parsing - can be enhanced
        plan = {}
        for agent_id in subordinates:
            plan[agent_id] = f"Handle part of: {task.description}"

        return plan

    async def coordinate_agents(
        self,
        agents: Dict[str, IAgent],
        task: CollaborationTask
    ) -> List[Tuple[str, Any]]:
        """Coordinate hierarchical execution"""
        coordination = [(
            self.leader_id,
            {
                "role": "leader",
                "responsibilities": ["analyze", "delegate", "synthesize"]
            }
        )]

        for agent_id in task.assigned_agents:
            if agent_id != self.leader_id:
                coordination.append((
                    agent_id,
                    {
                        "role": "subordinate",
                        "reports_to": self.leader_id,
                        "awaits_delegation": True
                    }
                ))

        return coordination


class ConsensusCollaboration(CollaborationProtocol):
    """Consensus collaboration - all agents must agree"""

    def __init__(self, consensus_threshold: float = 0.7):
        self.consensus_threshold = consensus_threshold

    async def execute(
        self,
        task: CollaborationTask,
        agents: Dict[str, IAgent],
        context: ConversationContext
    ) -> Dict[str, Any]:
        """Execute consensus collaboration"""
        proposals = {}
        votes = {}

        # Phase 1: Generate proposals
        for agent_id in task.assigned_agents:
            if agent_id not in agents:
                continue

            agent = agents[agent_id]
            logger.info(f"Consensus: {agent_id} generating proposal")

            proposal = await agent.process(
                f"Propose a solution for: {task.description}",
                context
            )
            proposals[agent_id] = proposal

        # Phase 2: Vote on proposals
        for voter_id in task.assigned_agents:
            if voter_id not in agents:
                continue

            voter = agents[voter_id]
            votes[voter_id] = {}

            for proposer_id, proposal in proposals.items():
                if proposer_id == voter_id:
                    votes[voter_id][proposer_id] = 1.0  # Self vote
                else:
                    logger.info(f"Consensus: {voter_id} voting on {proposer_id}'s proposal")

                    vote_prompt = f"""
                    Evaluate this proposal for task '{task.description}':
                    {proposal}

                    Rate from 0 to 1 (0=reject, 1=fully support):
                    """

                    vote_response = await voter.process(vote_prompt, context)
                    # Parse vote (simplified)
                    try:
                        vote_value = 0.5  # Default neutral vote
                        votes[voter_id][proposer_id] = vote_value
                    except:
                        votes[voter_id][proposer_id] = 0.5

        # Phase 3: Determine consensus
        consensus_scores = {}
        for proposer_id in proposals:
            scores = [votes[v].get(proposer_id, 0) for v in votes]
            consensus_scores[proposer_id] = sum(scores) / len(scores) if scores else 0

        # Find best consensus
        best_proposal = max(consensus_scores.items(), key=lambda x: x[1])
        has_consensus = best_proposal[1] >= self.consensus_threshold

        return {
            "mode": "consensus",
            "proposals": proposals,
            "votes": votes,
            "consensus_scores": consensus_scores,
            "selected_proposal": best_proposal[0] if has_consensus else None,
            "consensus_reached": has_consensus,
            "final_result": proposals.get(best_proposal[0]) if has_consensus else None
        }

    async def coordinate_agents(
        self,
        agents: Dict[str, IAgent],
        task: CollaborationTask
    ) -> List[Tuple[str, Any]]:
        """Coordinate consensus execution"""
        coordination = []

        for agent_id in task.assigned_agents:
            coordination.append((
                agent_id,
                {
                    "phases": ["propose", "vote", "consensus"],
                    "equal_weight": True,
                    "consensus_threshold": self.consensus_threshold
                }
            ))

        return coordination


class CollaborationManager:
    """Manages multi-agent collaborations"""

    def __init__(self):
        self.protocols = {
            CollaborationMode.SEQUENTIAL: SequentialCollaboration(),
            CollaborationMode.PARALLEL: ParallelCollaboration(),
            CollaborationMode.HIERARCHICAL: HierarchicalCollaboration("coordinator"),
            CollaborationMode.CONSENSUS: ConsensusCollaboration()
        }
        self.active_collaborations: Dict[str, CollaborationState] = {}
        self.message_queue: List[AgentMessage] = []

    async def start_collaboration(
        self,
        task: CollaborationTask,
        mode: CollaborationMode,
        agents: Dict[str, IAgent],
        context: ConversationContext
    ) -> str:
        """Start a new collaboration"""
        collaboration_id = f"collab_{datetime.utcnow().timestamp()}"

        # Determine participants and roles
        participants = self._assign_roles(task.assigned_agents, mode)

        # Create collaboration state
        state = CollaborationState(
            task=task,
            mode=mode,
            participants=participants,
            messages=[],
            decisions=[],
            start_time=datetime.utcnow()
        )

        self.active_collaborations[collaboration_id] = state

        # Execute collaboration
        try:
            protocol = self.protocols[mode]
            result = await protocol.execute(task, agents, context)

            # Update state
            state.end_time = datetime.utcnow()
            state.outcome = result

            logger.info(f"Collaboration {collaboration_id} completed successfully")

        except Exception as e:
            logger.error(f"Collaboration {collaboration_id} failed: {e}")
            state.end_time = datetime.utcnow()
            state.outcome = {"error": str(e)}

        return collaboration_id

    def _assign_roles(
        self,
        agent_ids: List[str],
        mode: CollaborationMode
    ) -> Dict[str, AgentRole]:
        """Assign roles to agents based on collaboration mode"""
        roles = {}

        if mode == CollaborationMode.HIERARCHICAL:
            # First agent is leader, rest are contributors
            for i, agent_id in enumerate(agent_ids):
                if i == 0:
                    roles[agent_id] = AgentRole.LEADER
                else:
                    roles[agent_id] = AgentRole.CONTRIBUTOR

        elif mode == CollaborationMode.CONSENSUS:
            # All agents are equal contributors
            for agent_id in agent_ids:
                roles[agent_id] = AgentRole.CONTRIBUTOR

        else:
            # Default: all contributors
            for agent_id in agent_ids:
                roles[agent_id] = AgentRole.CONTRIBUTOR

        return roles

    async def send_message(
        self,
        sender: str,
        recipient: str,
        message_type: str,
        content: Any,
        requires_response: bool = False
    ) -> str:
        """Send message between agents"""
        message = AgentMessage(
            sender=sender,
            recipient=recipient,
            message_type=message_type,
            content=content,
            requires_response=requires_response,
            correlation_id=f"msg_{datetime.utcnow().timestamp()}"
        )

        self.message_queue.append(message)
        logger.debug(f"Message sent from {sender} to {recipient}: {message_type}")

        return message.correlation_id

    async def process_messages(self) -> int:
        """Process pending messages"""
        processed = 0

        while self.message_queue:
            message = self.message_queue.pop(0)

            # Route message to recipient
            # This would integrate with actual agent message handling
            logger.debug(f"Processing message {message.correlation_id}")
            processed += 1

        return processed

    def get_collaboration_status(self, collaboration_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a collaboration"""
        if collaboration_id not in self.active_collaborations:
            return None

        state = self.active_collaborations[collaboration_id]

        return {
            "id": collaboration_id,
            "task": state.task.description,
            "mode": state.mode.value,
            "participants": [
                {"agent": aid, "role": role.value}
                for aid, role in state.participants.items()
            ],
            "start_time": state.start_time.isoformat(),
            "end_time": state.end_time.isoformat() if state.end_time else None,
            "status": "completed" if state.end_time else "in_progress",
            "outcome": state.outcome
        }

    def get_active_collaborations(self) -> List[str]:
        """Get list of active collaboration IDs"""
        return [
            cid for cid, state in self.active_collaborations.items()
            if state.end_time is None
        ]


# Global collaboration manager
_collaboration_manager: Optional[CollaborationManager] = None


async def get_collaboration_manager() -> CollaborationManager:
    """Get singleton collaboration manager"""
    global _collaboration_manager
    if _collaboration_manager is None:
        _collaboration_manager = CollaborationManager()
    return _collaboration_manager