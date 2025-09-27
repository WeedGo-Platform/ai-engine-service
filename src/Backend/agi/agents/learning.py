"""
Agent Learning and Adaptation System
Enables agents to learn from experiences and improve over time
"""

import asyncio
import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import pickle

from agi.core.database import get_db_manager
from agi.core.interfaces import IAgent, ConversationContext
from agi.analytics import get_metrics_collector

logger = logging.getLogger(__name__)


class LearningStrategy(Enum):
    """Learning strategies for agents"""
    REINFORCEMENT = "reinforcement"      # Learn from rewards/penalties
    SUPERVISED = "supervised"            # Learn from examples
    UNSUPERVISED = "unsupervised"       # Learn patterns
    TRANSFER = "transfer"                # Transfer knowledge between domains
    CONTINUAL = "continual"              # Learn continuously without forgetting


class AdaptationType(Enum):
    """Types of adaptation"""
    BEHAVIORAL = "behavioral"            # Change behavior patterns
    STRATEGIC = "strategic"              # Adjust strategies
    PARAMETRIC = "parametric"            # Tune parameters
    STRUCTURAL = "structural"            # Modify structure


@dataclass
class Experience:
    """Single learning experience"""
    id: str
    agent_id: str
    task: str
    action: str
    outcome: Any
    reward: float
    context: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LearningEpisode:
    """Collection of related experiences"""
    id: str
    agent_id: str
    experiences: List[Experience]
    total_reward: float
    start_time: datetime
    end_time: Optional[datetime] = None
    success: bool = False
    insights: List[str] = field(default_factory=list)


@dataclass
class AgentKnowledge:
    """Agent's learned knowledge"""
    agent_id: str
    domain: str
    patterns: Dict[str, List[Dict[str, Any]]]
    strategies: Dict[str, float]  # Strategy -> effectiveness score
    parameters: Dict[str, Any]
    examples: List[Dict[str, Any]]
    last_updated: datetime = field(default_factory=datetime.utcnow)


class ReinforcementLearner:
    """Reinforcement learning for agents"""

    def __init__(self, learning_rate: float = 0.1, discount_factor: float = 0.9):
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.q_table: Dict[Tuple[str, str], float] = {}  # (state, action) -> Q-value
        self.experience_buffer: List[Experience] = []
        self.epsilon = 0.1  # Exploration rate

    async def learn_from_experience(self, experience: Experience) -> Dict[str, Any]:
        """Learn from a single experience"""
        self.experience_buffer.append(experience)

        # Extract state and action
        state = self._extract_state(experience.context)
        action = experience.action

        # Update Q-value
        current_q = self.q_table.get((state, action), 0.0)

        # Calculate new Q-value using Bellman equation
        new_q = current_q + self.learning_rate * (
            experience.reward - current_q
        )

        self.q_table[(state, action)] = new_q

        logger.debug(f"Updated Q-value for ({state}, {action}): {current_q:.3f} -> {new_q:.3f}")

        return {
            "state": state,
            "action": action,
            "old_q": current_q,
            "new_q": new_q,
            "reward": experience.reward
        }

    async def learn_from_episode(self, episode: LearningEpisode) -> Dict[str, Any]:
        """Learn from complete episode"""
        updates = []

        # Process experiences in reverse for temporal difference learning
        experiences = list(reversed(episode.experiences))

        for i, exp in enumerate(experiences):
            state = self._extract_state(exp.context)
            action = exp.action

            # Calculate discounted future reward
            future_reward = 0
            for j in range(i):
                future_reward += (self.discount_factor ** j) * experiences[j].reward

            # Update Q-value
            current_q = self.q_table.get((state, action), 0.0)
            target = exp.reward + self.discount_factor * future_reward
            new_q = current_q + self.learning_rate * (target - current_q)

            self.q_table[(state, action)] = new_q
            updates.append({
                "state": state,
                "action": action,
                "q_value": new_q
            })

        return {
            "episode_id": episode.id,
            "total_reward": episode.total_reward,
            "updates": len(updates),
            "success": episode.success
        }

    def select_action(self, state: str, available_actions: List[str]) -> str:
        """Select action using epsilon-greedy strategy"""
        import random

        if random.random() < self.epsilon:
            # Explore: random action
            return random.choice(available_actions)

        # Exploit: best known action
        q_values = {
            action: self.q_table.get((state, action), 0.0)
            for action in available_actions
        }

        if not q_values:
            return random.choice(available_actions)

        return max(q_values, key=q_values.get)

    def _extract_state(self, context: Dict[str, Any]) -> str:
        """Extract state representation from context"""
        # Simplified state extraction - can be enhanced
        key_features = []

        for key in ["task_type", "complexity", "domain"]:
            if key in context:
                key_features.append(f"{key}:{context[key]}")

        return "|".join(key_features) if key_features else "default"

    def decay_epsilon(self, decay_rate: float = 0.995):
        """Decay exploration rate"""
        self.epsilon *= decay_rate
        self.epsilon = max(0.01, self.epsilon)  # Minimum exploration


class PatternLearner:
    """Learn patterns from agent behavior"""

    def __init__(self):
        self.patterns: Dict[str, List[Dict[str, Any]]] = {}
        self.pattern_scores: Dict[str, float] = {}

    async def learn_patterns(
        self,
        experiences: List[Experience]
    ) -> Dict[str, Any]:
        """Learn patterns from experiences"""
        # Group experiences by task type
        task_groups = {}
        for exp in experiences:
            task_type = exp.metadata.get("task_type", "unknown")
            if task_type not in task_groups:
                task_groups[task_type] = []
            task_groups[task_type].append(exp)

        discovered_patterns = []

        for task_type, exps in task_groups.items():
            # Find successful patterns
            successful = [e for e in exps if e.reward > 0.5]

            if len(successful) >= 3:  # Minimum experiences for pattern
                pattern = self._extract_pattern(successful)
                if pattern:
                    pattern_id = f"{task_type}_{len(self.patterns)}"
                    self.patterns[pattern_id] = pattern
                    self.pattern_scores[pattern_id] = np.mean([e.reward for e in successful])
                    discovered_patterns.append(pattern_id)

        return {
            "discovered": len(discovered_patterns),
            "patterns": discovered_patterns,
            "total_patterns": len(self.patterns)
        }

    def _extract_pattern(self, experiences: List[Experience]) -> List[Dict[str, Any]]:
        """Extract common pattern from experiences"""
        if not experiences:
            return []

        # Find common action sequences
        patterns = []

        for exp in experiences:
            pattern = {
                "action": exp.action,
                "context_features": self._extract_features(exp.context),
                "reward": exp.reward
            }
            patterns.append(pattern)

        # Filter for consistency
        if len(patterns) >= 3:
            return patterns

        return []

    def _extract_features(self, context: Dict[str, Any]) -> List[str]:
        """Extract key features from context"""
        features = []

        for key, value in context.items():
            if isinstance(value, (str, int, float, bool)):
                features.append(f"{key}={value}")

        return features

    def apply_pattern(self, context: Dict[str, Any]) -> Optional[str]:
        """Apply learned pattern to new context"""
        context_features = set(self._extract_features(context))

        best_match = None
        best_score = 0

        for pattern_id, pattern_list in self.patterns.items():
            for pattern in pattern_list:
                pattern_features = set(pattern.get("context_features", []))

                # Calculate similarity
                similarity = len(context_features & pattern_features) / max(
                    len(context_features | pattern_features), 1
                )

                score = similarity * self.pattern_scores.get(pattern_id, 0)

                if score > best_score:
                    best_score = score
                    best_match = pattern.get("action")

        return best_match if best_score > 0.5 else None


class AdaptationEngine:
    """Engine for agent adaptation"""

    def __init__(self):
        self.adaptation_rules: Dict[str, Any] = {}
        self.performance_history: List[Dict[str, Any]] = []
        self.adaptation_threshold = 0.3  # Performance drop threshold

    async def evaluate_performance(
        self,
        agent_id: str,
        recent_episodes: List[LearningEpisode]
    ) -> Dict[str, float]:
        """Evaluate agent performance"""
        if not recent_episodes:
            return {"overall": 0.5}

        # Calculate metrics
        success_rate = sum(1 for e in recent_episodes if e.success) / len(recent_episodes)
        avg_reward = np.mean([e.total_reward for e in recent_episodes])

        # Time-based efficiency
        durations = [
            (e.end_time - e.start_time).total_seconds()
            for e in recent_episodes
            if e.end_time
        ]
        avg_duration = np.mean(durations) if durations else float('inf')

        performance = {
            "success_rate": success_rate,
            "average_reward": avg_reward,
            "efficiency": 1.0 / (1.0 + avg_duration / 60),  # Normalize to 0-1
            "overall": (success_rate + avg_reward) / 2
        }

        self.performance_history.append({
            "agent_id": agent_id,
            "timestamp": datetime.utcnow(),
            "metrics": performance
        })

        return performance

    async def determine_adaptation(
        self,
        current_performance: Dict[str, float],
        historical_performance: List[Dict[str, float]]
    ) -> Optional[AdaptationType]:
        """Determine if adaptation is needed"""
        if len(historical_performance) < 2:
            return None

        # Compare with recent history
        recent_avg = np.mean([p["overall"] for p in historical_performance[-5:]])
        current = current_performance["overall"]

        performance_drop = recent_avg - current

        if performance_drop > self.adaptation_threshold:
            # Significant performance drop - need adaptation
            if current_performance["success_rate"] < 0.3:
                return AdaptationType.STRATEGIC  # Change strategies
            elif current_performance["efficiency"] < 0.3:
                return AdaptationType.BEHAVIORAL  # Change behaviors
            else:
                return AdaptationType.PARAMETRIC  # Tune parameters

        return None

    async def apply_adaptation(
        self,
        agent_id: str,
        adaptation_type: AdaptationType,
        knowledge: AgentKnowledge
    ) -> Dict[str, Any]:
        """Apply adaptation to agent"""
        changes = {}

        if adaptation_type == AdaptationType.BEHAVIORAL:
            # Adjust behavior patterns
            changes["behaviors"] = self._adapt_behaviors(knowledge)

        elif adaptation_type == AdaptationType.STRATEGIC:
            # Change strategies
            changes["strategies"] = self._adapt_strategies(knowledge)

        elif adaptation_type == AdaptationType.PARAMETRIC:
            # Tune parameters
            changes["parameters"] = self._adapt_parameters(knowledge)

        elif adaptation_type == AdaptationType.STRUCTURAL:
            # Modify structure (advanced)
            changes["structure"] = self._adapt_structure(knowledge)

        # Update knowledge
        knowledge.last_updated = datetime.utcnow()

        logger.info(f"Applied {adaptation_type.value} adaptation to agent {agent_id}")

        return {
            "agent_id": agent_id,
            "adaptation_type": adaptation_type.value,
            "changes": changes,
            "timestamp": datetime.utcnow().isoformat()
        }

    def _adapt_behaviors(self, knowledge: AgentKnowledge) -> Dict[str, Any]:
        """Adapt behavioral patterns"""
        # Analyze patterns and adjust
        successful_patterns = [
            p for p in knowledge.patterns.values()
            if any(item.get("reward", 0) > 0.7 for pattern in p for item in pattern)
        ]

        return {
            "reinforced_patterns": len(successful_patterns),
            "pruned_patterns": len(knowledge.patterns) - len(successful_patterns)
        }

    def _adapt_strategies(self, knowledge: AgentKnowledge) -> Dict[str, Any]:
        """Adapt strategies"""
        # Reweight strategies based on effectiveness
        total_score = sum(knowledge.strategies.values())

        if total_score > 0:
            for strategy in knowledge.strategies:
                knowledge.strategies[strategy] /= total_score

        return {
            "reweighted": list(knowledge.strategies.keys()),
            "top_strategy": max(knowledge.strategies, key=knowledge.strategies.get)
        }

    def _adapt_parameters(self, knowledge: AgentKnowledge) -> Dict[str, Any]:
        """Adapt parameters"""
        changes = {}

        # Adjust learning rate
        if "learning_rate" in knowledge.parameters:
            old_lr = knowledge.parameters["learning_rate"]
            new_lr = old_lr * 0.95  # Decay
            knowledge.parameters["learning_rate"] = new_lr
            changes["learning_rate"] = {"old": old_lr, "new": new_lr}

        # Adjust exploration
        if "epsilon" in knowledge.parameters:
            old_eps = knowledge.parameters["epsilon"]
            new_eps = max(0.01, old_eps * 0.99)
            knowledge.parameters["epsilon"] = new_eps
            changes["epsilon"] = {"old": old_eps, "new": new_eps}

        return changes

    def _adapt_structure(self, knowledge: AgentKnowledge) -> Dict[str, Any]:
        """Adapt structural components"""
        # Advanced structural changes
        return {
            "components_modified": 0,
            "new_connections": 0
        }


class LearningManager:
    """Manages learning for all agents"""

    def __init__(self):
        self.learners: Dict[str, ReinforcementLearner] = {}
        self.pattern_learners: Dict[str, PatternLearner] = {}
        self.adaptation_engine = AdaptationEngine()
        self.knowledge_base: Dict[str, AgentKnowledge] = {}

    async def initialize_agent_learning(
        self,
        agent_id: str,
        domain: str = "general"
    ) -> None:
        """Initialize learning for an agent"""
        if agent_id not in self.learners:
            self.learners[agent_id] = ReinforcementLearner()
            self.pattern_learners[agent_id] = PatternLearner()
            self.knowledge_base[agent_id] = AgentKnowledge(
                agent_id=agent_id,
                domain=domain,
                patterns={},
                strategies={},
                parameters={
                    "learning_rate": 0.1,
                    "epsilon": 0.1
                },
                examples=[]
            )

            logger.info(f"Initialized learning for agent {agent_id}")

    async def record_experience(
        self,
        agent_id: str,
        task: str,
        action: str,
        outcome: Any,
        reward: float,
        context: Dict[str, Any]
    ) -> str:
        """Record learning experience"""
        experience = Experience(
            id=f"exp_{datetime.utcnow().timestamp()}",
            agent_id=agent_id,
            task=task,
            action=action,
            outcome=outcome,
            reward=reward,
            context=context
        )

        # Store in database
        db = await get_db_manager()
        await db.execute(
            """
            INSERT INTO agi.learning_feedback
            (id, agent_id, task, action, outcome, reward, context, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
            experience.id,
            agent_id,
            task,
            action,
            json.dumps(outcome),
            reward,
            json.dumps(context),
            experience.timestamp
        )

        # Learn from experience
        if agent_id in self.learners:
            await self.learners[agent_id].learn_from_experience(experience)

        return experience.id

    async def complete_episode(
        self,
        agent_id: str,
        episode_id: str,
        success: bool
    ) -> Dict[str, Any]:
        """Complete learning episode"""
        # Retrieve episode experiences
        db = await get_db_manager()
        experiences_data = await db.fetch(
            """
            SELECT * FROM agi.learning_feedback
            WHERE agent_id = $1 AND created_at > NOW() - INTERVAL '1 hour'
            ORDER BY created_at
            """,
            agent_id
        )

        if not experiences_data:
            return {"status": "no_experiences"}

        # Create episode
        experiences = [
            Experience(
                id=row['id'],
                agent_id=row['agent_id'],
                task=row['task'],
                action=row['action'],
                outcome=json.loads(row['outcome']),
                reward=row['reward'],
                context=json.loads(row['context']),
                timestamp=row['created_at']
            )
            for row in experiences_data
        ]

        episode = LearningEpisode(
            id=episode_id,
            agent_id=agent_id,
            experiences=experiences,
            total_reward=sum(e.reward for e in experiences),
            start_time=experiences[0].timestamp,
            end_time=datetime.utcnow(),
            success=success
        )

        # Learn from episode
        if agent_id in self.learners:
            rl_result = await self.learners[agent_id].learn_from_episode(episode)

            # Learn patterns
            pattern_result = await self.pattern_learners[agent_id].learn_patterns(experiences)

            # Evaluate performance
            performance = await self.adaptation_engine.evaluate_performance(
                agent_id,
                [episode]  # In practice, would use more episodes
            )

            # Check if adaptation needed
            adaptation_type = await self.adaptation_engine.determine_adaptation(
                performance,
                self.adaptation_engine.performance_history[-10:]
            )

            adaptation_result = None
            if adaptation_type:
                adaptation_result = await self.adaptation_engine.apply_adaptation(
                    agent_id,
                    adaptation_type,
                    self.knowledge_base[agent_id]
                )

            return {
                "episode_id": episode_id,
                "learning": rl_result,
                "patterns": pattern_result,
                "performance": performance,
                "adaptation": adaptation_result
            }

        return {"status": "agent_not_initialized"}

    async def get_agent_knowledge(self, agent_id: str) -> Optional[AgentKnowledge]:
        """Get agent's learned knowledge"""
        return self.knowledge_base.get(agent_id)

    async def save_knowledge(self, agent_id: str) -> bool:
        """Save agent knowledge to database"""
        if agent_id not in self.knowledge_base:
            return False

        knowledge = self.knowledge_base[agent_id]

        db = await get_db_manager()
        await db.execute(
            """
            INSERT INTO agi.agent_knowledge
            (agent_id, domain, patterns, strategies, parameters, examples, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (agent_id) DO UPDATE SET
                patterns = $3,
                strategies = $4,
                parameters = $5,
                examples = $6,
                updated_at = $7
            """,
            agent_id,
            knowledge.domain,
            json.dumps(knowledge.patterns),
            json.dumps(knowledge.strategies),
            json.dumps(knowledge.parameters),
            json.dumps(knowledge.examples),
            knowledge.last_updated
        )

        return True

    async def load_knowledge(self, agent_id: str) -> bool:
        """Load agent knowledge from database"""
        db = await get_db_manager()
        row = await db.fetchone(
            """
            SELECT * FROM agi.agent_knowledge
            WHERE agent_id = $1
            """,
            agent_id
        )

        if row:
            self.knowledge_base[agent_id] = AgentKnowledge(
                agent_id=agent_id,
                domain=row['domain'],
                patterns=json.loads(row['patterns']),
                strategies=json.loads(row['strategies']),
                parameters=json.loads(row['parameters']),
                examples=json.loads(row['examples']),
                last_updated=row['updated_at']
            )
            return True

        return False


# Global learning manager
_learning_manager: Optional[LearningManager] = None


async def get_learning_manager() -> LearningManager:
    """Get singleton learning manager"""
    global _learning_manager
    if _learning_manager is None:
        _learning_manager = LearningManager()
    return _learning_manager