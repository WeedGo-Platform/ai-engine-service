"""
True Learning System
Implements real learning that improves the AI over time
"""
import json
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, field
import logging
from collections import defaultdict
import yaml

logger = logging.getLogger(__name__)

@dataclass
class LearnedPattern:
    """A pattern learned from user interactions"""
    pattern_id: str
    pattern_type: str  # success, failure, preference, behavior
    context: Dict[str, Any]
    occurrences: int
    success_rate: float
    last_seen: datetime
    
    # What triggered this pattern
    triggers: List[str]
    
    # What response/action was taken
    responses: List[str]
    
    # Outcome metrics
    outcomes: Dict[str, float]
    
    # Confidence in this pattern
    confidence: float

@dataclass
class PromptEvolution:
    """Evolution of prompts based on success"""
    prompt_id: str
    base_prompt: str
    current_prompt: str
    mutations: List[Dict[str, Any]]
    performance_history: List[float]
    success_rate: float
    usage_count: int

class TrueLearningSystem:
    """
    Implements true learning through:
    1. Pattern recognition from interactions
    2. Prompt evolution based on outcomes
    3. Behavioral adaptation
    4. Knowledge accumulation
    """
    
    def __init__(self, learning_dir: str = "data/learning"):
        self.learning_dir = Path(learning_dir)
        self.learning_dir.mkdir(parents=True, exist_ok=True)
        
        # Learning components
        self.patterns: Dict[str, LearnedPattern] = {}
        self.prompt_evolution: Dict[str, PromptEvolution] = {}
        self.knowledge_graph = KnowledgeGraph()
        self.behavioral_model = BehavioralModel()
        
        # Learning configuration
        self.config = self._load_learning_config()
        
        # Load existing learnings
        self._load_learned_data()
        
    def _load_learning_config(self) -> Dict:
        """Load learning configuration"""
        config_path = self.learning_dir / "learning_config.yaml"
        
        if config_path.exists():
            with open(config_path) as f:
                return yaml.safe_load(f)
        
        # Default configuration
        return {
            "pattern_threshold": 3,  # Min occurrences to establish pattern
            "confidence_threshold": 0.7,  # Min confidence to apply learning
            "prompt_mutation_rate": 0.1,  # Rate of prompt experimentation
            "learning_rate": 0.1,  # How fast to adapt
            "memory_window": 1000,  # Number of interactions to remember
            "success_metrics": {
                "user_satisfaction": 0.4,
                "task_completion": 0.3,
                "response_time": 0.1,
                "engagement_level": 0.2
            }
        }
    
    def learn_from_interaction(
        self,
        input_data: Dict[str, Any],
        ai_response: Dict[str, Any],
        outcome: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Core learning function - learns from every interaction
        
        Args:
            input_data: User input (text, voice, context)
            ai_response: What the AI said/did
            outcome: Measured outcomes (satisfaction, purchase, etc.)
        """
        
        # 1. Extract patterns from this interaction
        patterns = self._extract_patterns(input_data, ai_response, outcome)
        
        # 2. Update or create patterns
        for pattern in patterns:
            self._update_pattern(pattern)
        
        # 3. Evolve prompts based on outcome
        prompt_updates = self._evolve_prompts(input_data, ai_response, outcome)
        
        # 4. Update behavioral model
        behavioral_learning = self.behavioral_model.update(input_data, outcome)
        
        # 5. Expand knowledge graph
        knowledge_updates = self.knowledge_graph.add_knowledge(input_data, ai_response)
        
        # 6. Generate learning insights
        insights = self._generate_insights()
        
        # 7. Save learnings
        self._save_learned_data()
        
        return {
            "patterns_learned": len(patterns),
            "prompt_updates": prompt_updates,
            "behavioral_updates": behavioral_learning,
            "knowledge_added": knowledge_updates,
            "insights": insights,
            "learning_applied": True
        }
    
    def _extract_patterns(
        self,
        input_data: Dict,
        response: Dict,
        outcome: Dict
    ) -> List[LearnedPattern]:
        """Extract patterns from interaction"""
        patterns = []
        
        # Pattern 1: Successful interaction patterns
        if outcome.get("satisfaction", 0) > 0.7:
            pattern = LearnedPattern(
                pattern_id=f"success_{datetime.now().timestamp()}",
                pattern_type="success",
                context={
                    "user_intent": input_data.get("intent"),
                    "domain": input_data.get("domain"),
                    "time_of_day": datetime.now().hour,
                    "user_type": input_data.get("user_type")
                },
                occurrences=1,
                success_rate=1.0,
                last_seen=datetime.now(),
                triggers=[
                    input_data.get("text", ""),
                    input_data.get("intent", "")
                ],
                responses=[response.get("message", "")],
                outcomes={
                    "satisfaction": outcome.get("satisfaction", 0),
                    "task_completed": outcome.get("task_completed", False),
                    "purchase_made": outcome.get("purchase_made", False)
                },
                confidence=0.5  # Initial confidence
            )
            patterns.append(pattern)
        
        # Pattern 2: User preference patterns
        if input_data.get("user_id"):
            pref_pattern = LearnedPattern(
                pattern_id=f"pref_{input_data['user_id']}_{datetime.now().timestamp()}",
                pattern_type="preference",
                context={
                    "user_id": input_data["user_id"],
                    "products_mentioned": input_data.get("entities", {}).get("products", []),
                    "effects_desired": input_data.get("entities", {}).get("effects", [])
                },
                occurrences=1,
                success_rate=outcome.get("satisfaction", 0.5),
                last_seen=datetime.now(),
                triggers=input_data.get("entities", {}).get("products", []),
                responses=[response.get("recommendations", [])],
                outcomes=outcome,
                confidence=0.6
            )
            patterns.append(pref_pattern)
        
        # Pattern 3: Failure patterns (to avoid)
        if outcome.get("satisfaction", 1.0) < 0.3:
            failure_pattern = LearnedPattern(
                pattern_id=f"failure_{datetime.now().timestamp()}",
                pattern_type="failure",
                context=input_data,
                occurrences=1,
                success_rate=0.0,
                last_seen=datetime.now(),
                triggers=[input_data.get("text", "")],
                responses=[response.get("message", "")],
                outcomes=outcome,
                confidence=0.7  # High confidence to avoid
            )
            patterns.append(failure_pattern)
        
        return patterns
    
    def _update_pattern(self, new_pattern: LearnedPattern):
        """Update or merge pattern with existing patterns"""
        
        # Find similar existing patterns
        similar_pattern = self._find_similar_pattern(new_pattern)
        
        if similar_pattern:
            # Merge patterns
            similar_pattern.occurrences += 1
            similar_pattern.last_seen = datetime.now()
            
            # Update success rate (moving average)
            alpha = self.config["learning_rate"]
            similar_pattern.success_rate = (
                (1 - alpha) * similar_pattern.success_rate +
                alpha * new_pattern.success_rate
            )
            
            # Increase confidence if pattern is consistent
            if similar_pattern.occurrences >= self.config["pattern_threshold"]:
                similar_pattern.confidence = min(0.95, similar_pattern.confidence + 0.05)
            
            # Add new triggers/responses if unique
            for trigger in new_pattern.triggers:
                if trigger not in similar_pattern.triggers:
                    similar_pattern.triggers.append(trigger)
            
            for response in new_pattern.responses:
                if response not in similar_pattern.responses:
                    similar_pattern.responses.append(response)
        else:
            # Store new pattern
            self.patterns[new_pattern.pattern_id] = new_pattern
    
    def _find_similar_pattern(self, pattern: LearnedPattern) -> Optional[LearnedPattern]:
        """Find similar existing pattern"""
        for existing_pattern in self.patterns.values():
            if existing_pattern.pattern_type != pattern.pattern_type:
                continue
            
            # Calculate similarity based on context
            similarity = self._calculate_pattern_similarity(
                existing_pattern.context,
                pattern.context
            )
            
            if similarity > 0.8:
                return existing_pattern
        
        return None
    
    def _calculate_pattern_similarity(self, context1: Dict, context2: Dict) -> float:
        """Calculate similarity between two contexts"""
        if not context1 or not context2:
            return 0.0
        
        common_keys = set(context1.keys()) & set(context2.keys())
        if not common_keys:
            return 0.0
        
        matches = sum(1 for k in common_keys if context1[k] == context2[k])
        return matches / len(common_keys)
    
    def _evolve_prompts(
        self,
        input_data: Dict,
        response: Dict,
        outcome: Dict
    ) -> Dict[str, Any]:
        """Evolve prompts based on success/failure"""
        
        prompt_id = f"{input_data.get('domain', 'default')}_{input_data.get('intent', 'general')}"
        
        # Get or create prompt evolution
        if prompt_id not in self.prompt_evolution:
            base_prompt = self._get_base_prompt(prompt_id)
            self.prompt_evolution[prompt_id] = PromptEvolution(
                prompt_id=prompt_id,
                base_prompt=base_prompt,
                current_prompt=base_prompt,
                mutations=[],
                performance_history=[],
                success_rate=0.5,
                usage_count=0
            )
        
        evolution = self.prompt_evolution[prompt_id]
        evolution.usage_count += 1
        
        # Calculate success score
        success_score = self._calculate_success_score(outcome)
        evolution.performance_history.append(success_score)
        
        # Update success rate
        if len(evolution.performance_history) > 10:
            evolution.success_rate = np.mean(evolution.performance_history[-10:])
        
        # Evolve prompt if needed
        updates = {}
        
        if success_score > 0.8:
            # This worked well, reinforce
            updates["action"] = "reinforce"
            updates["confidence"] = min(1.0, evolution.success_rate + 0.05)
            
        elif success_score < 0.3:
            # This failed, try mutation
            if np.random.random() < self.config["prompt_mutation_rate"]:
                mutation = self._generate_prompt_mutation(evolution, input_data, outcome)
                evolution.mutations.append({
                    "timestamp": datetime.now().isoformat(),
                    "mutation": mutation,
                    "reason": "poor_performance",
                    "success_score": success_score
                })
                evolution.current_prompt = mutation
                updates["action"] = "mutate"
                updates["new_prompt"] = mutation
        
        return updates
    
    def _calculate_success_score(self, outcome: Dict) -> float:
        """Calculate overall success score from outcome"""
        metrics = self.config["success_metrics"]
        score = 0.0
        
        for metric, weight in metrics.items():
            value = outcome.get(metric, 0.5)
            score += value * weight
        
        return score
    
    def _generate_prompt_mutation(
        self,
        evolution: PromptEvolution,
        input_data: Dict,
        outcome: Dict
    ) -> str:
        """Generate a mutation of the prompt"""
        
        base = evolution.current_prompt
        
        # Mutation strategies based on failure reason
        if outcome.get("user_confusion", False):
            # Make clearer
            mutation = f"{base}\n\nBe very clear and specific. Avoid jargon."
        elif outcome.get("too_long", False):
            # Make more concise
            mutation = f"{base}\n\nBe concise. Maximum 2 sentences."
        elif outcome.get("wrong_tone", False):
            # Adjust tone
            mutation = f"{base}\n\nUse a {input_data.get('preferred_tone', 'friendly')} tone."
        else:
            # General improvement
            mutation = f"{base}\n\nFocus on user satisfaction and clear communication."
        
        return mutation
    
    def _get_base_prompt(self, prompt_id: str) -> str:
        """Get base prompt for ID"""
        # This would load from prompt files
        return f"Base prompt for {prompt_id}"
    
    def _generate_insights(self) -> List[str]:
        """Generate insights from learned patterns"""
        insights = []
        
        # Insight 1: Most successful patterns
        successful_patterns = [
            p for p in self.patterns.values()
            if p.pattern_type == "success" and p.confidence > 0.8
        ]
        
        if successful_patterns:
            best_pattern = max(successful_patterns, key=lambda p: p.success_rate)
            insights.append(
                f"Most successful pattern: {best_pattern.context} "
                f"with {best_pattern.success_rate:.0%} success rate"
            )
        
        # Insight 2: Common failures to avoid
        failure_patterns = [
            p for p in self.patterns.values()
            if p.pattern_type == "failure" and p.occurrences > 3
        ]
        
        if failure_patterns:
            insights.append(
                f"Identified {len(failure_patterns)} failure patterns to avoid"
            )
        
        # Insight 3: Prompt performance
        for prompt_id, evolution in self.prompt_evolution.items():
            if evolution.usage_count > 10:
                trend = "improving" if evolution.success_rate > 0.7 else "needs work"
                insights.append(
                    f"Prompt '{prompt_id}': {evolution.success_rate:.0%} success, {trend}"
                )
        
        return insights
    
    def _save_learned_data(self):
        """Save learned patterns and evolutions"""
        # Save patterns
        patterns_file = self.learning_dir / "patterns.json"
        patterns_data = {
            pid: {
                "pattern_type": p.pattern_type,
                "context": p.context,
                "occurrences": p.occurrences,
                "success_rate": p.success_rate,
                "confidence": p.confidence,
                "last_seen": p.last_seen.isoformat()
            }
            for pid, p in self.patterns.items()
        }
        
        with open(patterns_file, 'w') as f:
            json.dump(patterns_data, f, indent=2)
        
        # Save prompt evolutions
        prompts_file = self.learning_dir / "prompt_evolutions.json"
        prompts_data = {
            pid: {
                "current_prompt": e.current_prompt,
                "success_rate": e.success_rate,
                "usage_count": e.usage_count,
                "mutations": e.mutations
            }
            for pid, e in self.prompt_evolution.items()
        }
        
        with open(prompts_file, 'w') as f:
            json.dump(prompts_data, f, indent=2)
    
    def _load_learned_data(self):
        """Load previously learned data"""
        # Load patterns
        patterns_file = self.learning_dir / "patterns.json"
        if patterns_file.exists():
            with open(patterns_file) as f:
                patterns_data = json.load(f)
                # Reconstruct pattern objects
                # ... (implementation)
        
        # Load prompt evolutions
        prompts_file = self.learning_dir / "prompt_evolutions.json"
        if prompts_file.exists():
            with open(prompts_file) as f:
                prompts_data = json.load(f)
                # Reconstruct evolution objects
                # ... (implementation)
    
    def get_learned_context(self, input_data: Dict) -> Dict[str, Any]:
        """
        Get learned context to enhance AI response
        """
        context = {
            "patterns": [],
            "prompt_adjustments": "",
            "behavioral_predictions": {},
            "knowledge_relevant": []
        }
        
        # Find relevant patterns
        for pattern in self.patterns.values():
            if pattern.confidence > self.config["confidence_threshold"]:
                # Check if pattern matches current context
                similarity = self._calculate_pattern_similarity(
                    pattern.context,
                    input_data
                )
                
                if similarity > 0.6:
                    context["patterns"].append({
                        "type": pattern.pattern_type,
                        "success_rate": pattern.success_rate,
                        "suggested_responses": pattern.responses[:3]
                    })
        
        # Get evolved prompt
        prompt_id = f"{input_data.get('domain', 'default')}_{input_data.get('intent', 'general')}"
        if prompt_id in self.prompt_evolution:
            evolution = self.prompt_evolution[prompt_id]
            if evolution.success_rate > 0.7:
                context["prompt_adjustments"] = evolution.current_prompt
        
        # Get behavioral predictions
        context["behavioral_predictions"] = self.behavioral_model.predict(input_data)
        
        # Get relevant knowledge
        context["knowledge_relevant"] = self.knowledge_graph.query(input_data)
        
        return context


class KnowledgeGraph:
    """Knowledge graph that grows from interactions"""
    
    def __init__(self):
        self.nodes = {}  # Concepts
        self.edges = []  # Relationships
        self.facts = []  # Learned facts
    
    def add_knowledge(self, input_data: Dict, response: Dict) -> int:
        """Add knowledge from interaction"""
        added = 0
        
        # Extract entities
        entities = input_data.get("entities", {})
        
        for entity_type, entity_values in entities.items():
            for value in entity_values:
                if value not in self.nodes:
                    self.nodes[value] = {
                        "type": entity_type,
                        "mentions": 1,
                        "contexts": [input_data.get("intent")]
                    }
                    added += 1
                else:
                    self.nodes[value]["mentions"] += 1
        
        # Learn relationships
        if len(entities) > 1:
            # Create edges between co-occurring entities
            entity_list = []
            for values in entities.values():
                entity_list.extend(values)
            
            for i, entity1 in enumerate(entity_list):
                for entity2 in entity_list[i+1:]:
                    self.edges.append({
                        "from": entity1,
                        "to": entity2,
                        "context": input_data.get("intent"),
                        "strength": 1.0
                    })
                    added += 1
        
        return added
    
    def query(self, input_data: Dict) -> List[Dict]:
        """Query knowledge graph for relevant information"""
        relevant = []
        
        # Find mentioned entities
        for entity_type, values in input_data.get("entities", {}).items():
            for value in values:
                if value in self.nodes:
                    relevant.append({
                        "entity": value,
                        "info": self.nodes[value],
                        "related": self._find_related(value)
                    })
        
        return relevant
    
    def _find_related(self, entity: str) -> List[str]:
        """Find related entities"""
        related = []
        
        for edge in self.edges:
            if edge["from"] == entity:
                related.append(edge["to"])
            elif edge["to"] == entity:
                related.append(edge["from"])
        
        return list(set(related))[:5]


class BehavioralModel:
    """Model of user behavior patterns"""
    
    def __init__(self):
        self.behavior_patterns = defaultdict(list)
        self.predictions = {}
    
    def update(self, input_data: Dict, outcome: Dict) -> Dict:
        """Update behavioral model"""
        
        user_id = input_data.get("user_id", "anonymous")
        
        # Track behavior sequence
        behavior = {
            "timestamp": datetime.now(),
            "intent": input_data.get("intent"),
            "time_of_day": datetime.now().hour,
            "day_of_week": datetime.now().weekday(),
            "outcome": outcome
        }
        
        self.behavior_patterns[user_id].append(behavior)
        
        # Keep only recent behaviors
        max_behaviors = 100
        if len(self.behavior_patterns[user_id]) > max_behaviors:
            self.behavior_patterns[user_id] = self.behavior_patterns[user_id][-max_behaviors:]
        
        # Update predictions
        self._update_predictions(user_id)
        
        return {
            "patterns_tracked": len(self.behavior_patterns[user_id]),
            "predictions_updated": True
        }
    
    def _update_predictions(self, user_id: str):
        """Update behavior predictions"""
        behaviors = self.behavior_patterns[user_id]
        
        if len(behaviors) < 5:
            return
        
        # Predict next likely intent
        intents = [b["intent"] for b in behaviors]
        intent_counts = defaultdict(int)
        
        for i in range(len(intents) - 1):
            current = intents[i]
            next_intent = intents[i + 1]
            key = f"{current}->{next_intent}"
            intent_counts[key] += 1
        
        # Find most likely next intent
        if intents:
            current_intent = intents[-1]
            next_intents = {
                k.split("->")[1]: v
                for k, v in intent_counts.items()
                if k.startswith(f"{current_intent}->")
            }
            
            if next_intents:
                most_likely = max(next_intents.items(), key=lambda x: x[1])
                self.predictions[user_id] = {
                    "next_intent": most_likely[0],
                    "confidence": most_likely[1] / sum(next_intents.values())
                }
    
    def predict(self, input_data: Dict) -> Dict:
        """Predict user behavior"""
        user_id = input_data.get("user_id", "anonymous")
        
        if user_id in self.predictions:
            return self.predictions[user_id]
        
        return {"next_intent": None, "confidence": 0.0}