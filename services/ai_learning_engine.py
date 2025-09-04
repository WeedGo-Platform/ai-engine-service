#!/usr/bin/env python3
"""
AI Learning Engine - Pure AI with continuous learning
No hardcoded logic - everything is learned from training data
"""

import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from dataclasses import dataclass, asdict
import asyncio
import numpy as np
from collections import defaultdict
import asyncpg
import os
import uuid

logger = logging.getLogger(__name__)

@dataclass
class TrainingExample:
    """A single training example for the AI"""
    query: str
    context: Dict[str, Any]
    expected_intent: str
    expected_entities: Dict[str, Any]
    expected_products: List[str]
    expected_response_qualities: List[str]  # e.g., ["welcoming", "mentions_indica", "suggests_alternatives"]
    feedback_score: float = 0.0  # 0-1, how good was the actual response
    timestamp: datetime = None

@dataclass
class LearningSession:
    """A complete learning session with results"""
    examples_trained: int
    accuracy_before: float
    accuracy_after: float
    improvements: Dict[str, float]
    timestamp: datetime

class AILearningEngine:
    """
    Pure AI engine that learns everything from training data
    No hardcoded rules - just learned patterns
    """
    
    def __init__(self, model_manager=None):
        self.model_manager = model_manager
        
        # Training data storage
        self.training_data: List[TrainingExample] = []
        self.knowledge_base = defaultdict(list)  # Pattern -> Examples
        
        # Performance tracking
        self.performance_history = []
        self.current_accuracy = 0.0
        
        # Learning configuration
        self.learning_config = {
            "min_confidence_threshold": 0.3,
            "learning_rate": 0.1,
            "batch_size": 10,
            "memory_size": 1000  # Keep last N examples
        }
        
        # Dynamic prompt templates learned from examples
        self.learned_prompts = {}
        
        # Database connection pool
        self.db_pool = None
        
    async def initialize_db(self):
        """Initialize database connection pool"""
        if not self.db_pool:
            try:
                self.db_pool = await asyncpg.create_pool(
                    host=os.getenv('DB_HOST', 'localhost'),
                    port=int(os.getenv('DB_PORT', 5434)),
                    database=os.getenv('DB_NAME', 'ai_engine'),
                    user=os.getenv('DB_USER', 'weedgo'),
                    password=os.getenv('DB_PASSWORD', 'your_password_here'),
                    min_size=1,
                    max_size=10
                )
                logger.info("Database pool initialized for AI Learning Engine")
                
                # Create tables if they don't exist
                await self._ensure_tables_exist()
                
                # Load existing training examples from database
                await self._load_training_data_from_db()
                
            except Exception as e:
                logger.error(f"Failed to initialize database: {e}")
                
    async def _ensure_tables_exist(self):
        """Ensure training tables exist in the database"""
        if not self.db_pool:
            return
            
        async with self.db_pool.acquire() as conn:
            # Create training_examples table if it doesn't exist
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS training_examples (
                    id SERIAL PRIMARY KEY,
                    query TEXT NOT NULL,
                    expected_intent VARCHAR(100) NOT NULL,
                    expected_response TEXT,
                    entities JSONB DEFAULT '{}',
                    expected_products JSONB DEFAULT '[]',
                    expected_response_qualities JSONB DEFAULT '[]',
                    context JSONB DEFAULT '{}',
                    feedback_score FLOAT DEFAULT 0.5,
                    dataset_id VARCHAR(255),
                    dataset_name VARCHAR(255),
                    added_by VARCHAR(100) DEFAULT 'admin',
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create training_sessions table if it doesn't exist
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS training_sessions (
                    id SERIAL PRIMARY KEY,
                    session_id VARCHAR(255) UNIQUE NOT NULL,
                    examples_trained INTEGER DEFAULT 0,
                    accuracy_before FLOAT DEFAULT 0,
                    accuracy_after FLOAT DEFAULT 0,
                    improvements JSONB DEFAULT '{}',
                    dataset_id VARCHAR(255),
                    status VARCHAR(50) DEFAULT 'in_progress',
                    error_message TEXT,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP
                )
            ''')
            
    async def _load_training_data_from_db(self):
        """Load existing training data from database"""
        if not self.db_pool:
            return
            
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT query, expected_intent, expected_response, entities, 
                       expected_products, expected_response_qualities, context, 
                       feedback_score, created_at
                FROM training_examples
                WHERE is_active = TRUE
                ORDER BY created_at DESC
                LIMIT 1000
            ''')
            
            for row in rows:
                example = TrainingExample(
                    query=row['query'],
                    context=json.loads(row['context']) if row['context'] else {},
                    expected_intent=row['expected_intent'],
                    expected_entities=json.loads(row['entities']) if row['entities'] else {},
                    expected_products=json.loads(row['expected_products']) if row['expected_products'] else [],
                    expected_response_qualities=json.loads(row['expected_response_qualities']) if row['expected_response_qualities'] else [],
                    feedback_score=row['feedback_score'] or 0.5,
                    timestamp=row['created_at']
                )
                self.training_data.append(example)
                
                # Also populate knowledge base
                patterns = self._extract_patterns(example)
                for pattern in patterns:
                    self.knowledge_base[pattern].append(example)
                    
            logger.info(f"Loaded {len(rows)} training examples from database")
            
    async def _save_training_example_to_db(self, example: TrainingExample, dataset_id: str = None, dataset_name: str = None):
        """Save a single training example to the database"""
        if not self.db_pool:
            await self.initialize_db()
            
        if not self.db_pool:
            logger.warning("Could not save training example - no database connection")
            return
            
        async with self.db_pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO training_examples 
                (query, expected_intent, expected_response, entities, expected_products, 
                 expected_response_qualities, context, feedback_score, dataset_id, dataset_name)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            ''',
                example.query,
                example.expected_intent,
                example.context.get('expected_response', ''),
                json.dumps(example.expected_entities),
                json.dumps(example.expected_products),
                json.dumps(example.expected_response_qualities),
                json.dumps(example.context),
                example.feedback_score,
                dataset_id or example.context.get('dataset_id'),
                dataset_name or example.context.get('dataset_name')
            )
            
    async def _save_training_session_to_db(self, session: LearningSession, dataset_id: str = None):
        """Save a training session to the database"""
        if not self.db_pool:
            await self.initialize_db()
            
        if not self.db_pool:
            logger.warning("Could not save training session - no database connection")
            return
            
        session_id = str(uuid.uuid4())
        
        async with self.db_pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO training_sessions 
                (session_id, examples_trained, accuracy_before, accuracy_after, 
                 improvements, dataset_id, status, completed_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            ''',
                session_id,
                session.examples_trained,
                session.accuracy_before,
                session.accuracy_after,
                json.dumps(session.improvements),
                dataset_id,
                'completed',
                session.timestamp
            )
        
    async def train(self, examples: List[TrainingExample]) -> LearningSession:
        """
        Train the AI with a batch of examples
        This is where the magic happens - the AI learns patterns
        """
        
        # Measure accuracy before training
        accuracy_before = await self._measure_accuracy()
        
        trained_count = 0
        improvements = defaultdict(float)
        
        for example in examples:
            # Store the training example
            self.training_data.append(example)
            
            # Save to database
            dataset_id = example.context.get('dataset_id') if hasattr(example, 'context') and example.context else None
            dataset_name = example.context.get('dataset_name') if hasattr(example, 'context') and example.context else None
            await self._save_training_example_to_db(example, dataset_id, dataset_name)
            
            # Extract patterns from the example
            patterns = self._extract_patterns(example)
            
            # Store patterns in knowledge base
            for pattern in patterns:
                self.knowledge_base[pattern].append(example)
            
            # Generate training prompt for the model
            training_prompt = self._generate_training_prompt(example)
            
            # Train the model (in production, this would fine-tune the model)
            if self.model_manager:
                await self._train_model_with_example(training_prompt, example)
            
            trained_count += 1
            
            # Track what we learned
            if example.expected_intent:
                improvements[f"intent_{example.expected_intent}"] += 0.1
        
        # Measure accuracy after training
        accuracy_after = await self._measure_accuracy()
        
        # Update current accuracy
        self.current_accuracy = accuracy_after
        
        # Create learning session record
        session = LearningSession(
            examples_trained=trained_count,
            accuracy_before=accuracy_before,
            accuracy_after=accuracy_after,
            improvements=dict(improvements),
            timestamp=datetime.now()
        )
        
        self.performance_history.append(session)
        
        # Save session to database
        dataset_id = examples[0].context.get('dataset_id') if examples and hasattr(examples[0], 'context') and examples[0].context else None
        await self._save_training_session_to_db(session, dataset_id)
        
        # Cleanup old training data if needed
        if len(self.training_data) > self.learning_config["memory_size"]:
            self.training_data = self.training_data[-self.learning_config["memory_size"]:]
        
        logger.info(f"Training complete: {trained_count} examples, accuracy {accuracy_before:.2%} -> {accuracy_after:.2%}")
        
        return session
    
    def _extract_patterns(self, example: TrainingExample) -> List[str]:
        """Extract learnable patterns from an example"""
        patterns = []
        
        # Query patterns
        query_lower = example.query.lower()
        
        # Intent patterns
        if example.expected_intent:
            patterns.append(f"intent:{example.expected_intent}:{query_lower}")
        
        # Entity patterns
        for entity_type, entity_value in example.expected_entities.items():
            if entity_value:
                patterns.append(f"entity:{entity_type}:{entity_value}:{query_lower}")
        
        # Context patterns
        if example.context:
            for key, value in example.context.items():
                patterns.append(f"context:{key}:{value}")
        
        # Response quality patterns
        for quality in example.expected_response_qualities:
            patterns.append(f"quality:{quality}:{query_lower}")
        
        return patterns
    
    def _generate_training_prompt(self, example: TrainingExample) -> str:
        """Generate a training prompt from an example"""
        
        prompt = f"""Learn from this example:

Customer Query: "{example.query}"

Context:
{json.dumps(example.context, indent=2) if example.context else "No previous context"}

Expected Understanding:
- Intent: {example.expected_intent}
- Entities: {json.dumps(example.expected_entities, indent=2)}
- Products to recommend: {', '.join(example.expected_products) if example.expected_products else "Based on query"}

Response should have these qualities:
{chr(10).join(f"- {q}" for q in example.expected_response_qualities)}

Learn this pattern and apply it to similar queries."""
        
        return prompt
    
    async def _train_model_with_example(self, prompt: str, example: TrainingExample):
        """Train the model with a single example"""
        
        if not self.model_manager:
            return
        
        # In production, this would fine-tune the model
        # For now, we store the prompt as a learned pattern
        pattern_key = f"{example.expected_intent}:{example.query[:30]}"
        self.learned_prompts[pattern_key] = prompt
        
        # We could also call a fine-tuning API here
        # await self.model_manager.fine_tune(prompt, example)
    
    async def _measure_accuracy(self) -> float:
        """Measure current accuracy on known examples"""
        
        if not self.training_data:
            return 0.0
        
        # Sample some training examples to test
        test_size = min(10, len(self.training_data))
        test_examples = self.training_data[-test_size:]
        
        correct = 0
        total = 0
        
        for example in test_examples:
            # Test if we can correctly identify intent and entities
            result = await self.process_query(
                example.query,
                example.context
            )
            
            # Check if intent matches
            if result.get('intent') == example.expected_intent:
                correct += 0.5
            
            # Check if key entities were found
            if result.get('entities'):
                for key, expected_value in example.expected_entities.items():
                    if result['entities'].get(key) == expected_value:
                        correct += 0.5 / len(example.expected_entities)
            
            total += 1
        
        return correct / total if total > 0 else 0.0
    
    async def process_query(self, query: str, context: Dict[str, Any] = None) -> Dict:
        """
        Process a query using only learned patterns
        No hardcoded logic - pure AI
        """
        
        # Find similar examples from training data
        similar_examples = self._find_similar_examples(query, context)
        
        # Build prompt using learned patterns
        prompt = self._build_inference_prompt(query, context, similar_examples)
        
        # Get AI response
        if self.model_manager:
            from services.model_manager import ModelType
            response = await self.model_manager.generate(
                model=ModelType.LLAMA2_7B,
                prompt=prompt,
                max_length=200
            )
            
            # Parse AI response
            return self._parse_ai_response(response.text)
        
        # Fallback if no model
        return {
            "intent": "unknown",
            "entities": {},
            "confidence": 0.0,
            "response": "I'm still learning. Please teach me more about this."
        }
    
    def _find_similar_examples(self, query: str, context: Dict = None) -> List[TrainingExample]:
        """Find similar examples from training data"""
        
        similar = []
        query_lower = query.lower()
        
        for example in self.training_data:
            similarity = self._calculate_similarity(query_lower, example.query.lower())
            
            # Add context similarity
            if context and example.context:
                for key in context:
                    if key in example.context and context[key] == example.context[key]:
                        similarity += 0.1
            
            if similarity > 0.3:  # Threshold for similarity
                similar.append((example, similarity))
        
        # Sort by similarity and return top 5
        similar.sort(key=lambda x: x[1], reverse=True)
        return [ex for ex, _ in similar[:5]]
    
    def _calculate_similarity(self, query1: str, query2: str) -> float:
        """Calculate similarity between two queries"""
        
        # Simple word overlap similarity
        words1 = set(query1.split())
        words2 = set(query2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def _build_inference_prompt(self, query: str, context: Dict, similar_examples: List[TrainingExample]) -> str:
        """Build inference prompt using learned examples"""
        
        examples_text = ""
        if similar_examples:
            examples_text = "Here are similar examples I've learned:\n\n"
            for ex in similar_examples[:3]:
                examples_text += f"Query: {ex.query}\n"
                examples_text += f"Intent: {ex.expected_intent}\n"
                examples_text += f"Entities: {json.dumps(ex.expected_entities)}\n\n"
        
        prompt = f"""Based on my training, analyze this query:

{examples_text}

Current Query: "{query}"
Context: {json.dumps(context) if context else "No context"}

Identify:
1. Intent (greeting, product_search, cart_action, information_request)
2. Entities (product, size, category, strain_type, effects, price)
3. Appropriate response

Respond in JSON format:
{{"intent": "", "entities": {{}}, "response": ""}}"""
        
        return prompt
    
    def _parse_ai_response(self, response: str) -> Dict:
        """Parse AI response into structured data"""
        
        try:
            # Try to parse as JSON
            if '{' in response and '}' in response:
                start = response.index('{')
                end = response.rindex('}') + 1
                json_str = response[start:end]
                return json.loads(json_str)
        except:
            pass
        
        # Fallback parsing
        result = {
            "intent": "unknown",
            "entities": {},
            "response": response,
            "confidence": 0.5
        }
        
        # Simple intent detection from response
        response_lower = response.lower()
        if any(word in response_lower for word in ['welcome', 'hello', 'hi']):
            result["intent"] = "greeting"
        elif any(word in response_lower for word in ['product', 'found', 'recommend']):
            result["intent"] = "product_search"
        
        return result
    
    def get_learning_stats(self) -> Dict:
        """Get current learning statistics"""
        
        stats = {
            "total_examples_trained": len(self.training_data),
            "current_accuracy": self.current_accuracy,
            "unique_patterns": len(self.knowledge_base),
            "sessions_completed": len(self.performance_history),
            "improvement_rate": 0.0
        }
        
        # Calculate improvement rate
        if len(self.performance_history) >= 2:
            first = self.performance_history[0].accuracy_after
            last = self.performance_history[-1].accuracy_after
            stats["improvement_rate"] = (last - first) / max(first, 0.01)
        
        return stats
    
    def export_knowledge(self) -> Dict:
        """Export learned knowledge for persistence"""
        
        return {
            "training_data": [asdict(ex) for ex in self.training_data[-100:]],  # Last 100
            "patterns": {k: len(v) for k, v in self.knowledge_base.items()},
            "learned_prompts": self.learned_prompts,
            "stats": self.get_learning_stats()
        }
    
    def import_knowledge(self, knowledge: Dict):
        """Import previously learned knowledge"""
        
        if "training_data" in knowledge:
            for ex_dict in knowledge["training_data"]:
                ex = TrainingExample(**ex_dict)
                self.training_data.append(ex)
        
        if "learned_prompts" in knowledge:
            self.learned_prompts.update(knowledge["learned_prompts"])
        
        logger.info(f"Imported {len(self.training_data)} training examples")


# Global instance
ai_learning_engine = AILearningEngine()