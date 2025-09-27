"""
Base Memory Implementation for AGI System
Provides abstract base and concrete implementations for different memory types
"""

import asyncio
import json
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
from collections import deque
import hashlib

from agi.core.interfaces import IMemory
from agi.config.agi_config import get_config
from agi.core.database import get_db_manager
import redis.asyncio as redis


class BaseMemory(IMemory):
    """
    Base implementation of memory interface
    Provides common functionality for all memory types
    """

    def __init__(self, memory_type: str, max_size: int = 1000):
        """
        Initialize base memory

        Args:
            memory_type: Type of memory (working, episodic, semantic)
            max_size: Maximum number of items to store
        """
        self.memory_type = memory_type
        self.max_size = max_size
        self.config = get_config()
        self._redis_client: Optional[redis.Redis] = None
        self._db_manager = None
        self._initialized = False

    async def initialize(self):
        """Initialize memory connections"""
        if self._initialized:
            return

        # Initialize Redis connection
        self._redis_client = await redis.Redis(
            host=self.config.redis.host,
            port=self.config.redis.port,
            db=self.config.redis.db,
            decode_responses=True
        )

        # Initialize database connection
        self._db_manager = await get_db_manager()

        self._initialized = True

    def _get_redis_key(self, key: str) -> str:
        """Get Redis key with proper prefix"""
        return f"{self.config.redis.key_prefix}memory:{self.memory_type}:{key}"

    async def store(
        self,
        key: str,
        value: Any,
        metadata: Optional[Dict[str, Any]] = None,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Store item in memory

        Args:
            key: Unique key for the item
            value: Value to store
            metadata: Optional metadata
            ttl: Time to live in seconds

        Returns:
            Success status
        """
        if not self._initialized:
            await self.initialize()

        try:
            # Prepare data for storage
            data = {
                "value": value,
                "metadata": metadata or {},
                "timestamp": datetime.utcnow().isoformat(),
                "memory_type": self.memory_type
            }

            # Store in Redis for fast access
            redis_key = self._get_redis_key(key)
            await self._redis_client.set(
                redis_key,
                json.dumps(data),
                ex=ttl
            )

            # Store in database for persistence
            await self._store_to_database(key, data)

            return True

        except Exception as e:
            print(f"Error storing to memory: {e}")
            return False

    async def retrieve(
        self,
        key: str
    ) -> Optional[Any]:
        """
        Retrieve item from memory

        Args:
            key: Key to retrieve

        Returns:
            Retrieved value or None
        """
        if not self._initialized:
            await self.initialize()

        try:
            # Try Redis first (faster)
            redis_key = self._get_redis_key(key)
            data = await self._redis_client.get(redis_key)

            if data:
                parsed = json.loads(data)
                return parsed.get("value")

            # Fallback to database
            result = await self._retrieve_from_database(key)
            if result:
                # Cache in Redis for future access
                await self._redis_client.set(
                    redis_key,
                    json.dumps(result),
                    ex=3600  # 1 hour cache
                )
                return result.get("value")

            return None

        except Exception as e:
            print(f"Error retrieving from memory: {e}")
            return None

    async def search(
        self,
        query: str,
        limit: int = 10
    ) -> List[Tuple[str, Any, float]]:
        """
        Search memory by query

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of (key, value, score) tuples
        """
        # This is a base implementation - override in specific memory types
        return []

    async def forget(
        self,
        key: str
    ) -> bool:
        """
        Remove item from memory

        Args:
            key: Key to remove

        Returns:
            Success status
        """
        if not self._initialized:
            await self.initialize()

        try:
            # Remove from Redis
            redis_key = self._get_redis_key(key)
            await self._redis_client.delete(redis_key)

            # Remove from database
            await self._remove_from_database(key)

            return True

        except Exception as e:
            print(f"Error forgetting from memory: {e}")
            return False

    async def clear(self) -> bool:
        """Clear all items from memory"""
        if not self._initialized:
            await self.initialize()

        try:
            # Clear Redis keys
            pattern = self._get_redis_key("*")
            keys = await self._redis_client.keys(pattern)
            if keys:
                await self._redis_client.delete(*keys)

            # Clear database
            await self._clear_database()

            return True

        except Exception as e:
            print(f"Error clearing memory: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete an item from memory - alias for forget"""
        return await self.forget(key)

    async def exists(self, key: str) -> bool:
        """Check if a key exists in memory"""
        if not self._initialized:
            await self.initialize()

        try:
            # Check Redis first
            redis_key = self._get_redis_key(key)
            if await self._redis_client.exists(redis_key):
                return True

            # Check database
            result = await self._retrieve_from_database(key)
            return result is not None

        except Exception as e:
            print(f"Error checking existence: {e}")
            return False

    async def _store_to_database(self, key: str, data: Dict[str, Any]):
        """Store to database - override in subclasses"""
        pass

    async def _retrieve_from_database(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve from database - override in subclasses"""
        return None

    async def _remove_from_database(self, key: str):
        """Remove from database - override in subclasses"""
        pass

    async def _clear_database(self):
        """Clear database - override in subclasses"""
        pass


class WorkingMemory(BaseMemory):
    """
    Working Memory: Short-term memory for current context
    Uses a circular buffer for efficiency
    """

    def __init__(self, max_size: int = 100):
        super().__init__("working", max_size)
        self.buffer = deque(maxlen=max_size)
        self.attention_weights = {}

    async def store(
        self,
        key: str,
        value: Any,
        metadata: Optional[Dict[str, Any]] = None,
        ttl: Optional[int] = 300  # 5 minutes default
    ) -> bool:
        """Store in working memory with short TTL"""
        # Add to buffer
        self.buffer.append({
            "key": key,
            "value": value,
            "metadata": metadata,
            "timestamp": time.time()
        })

        # Calculate attention weight based on recency and relevance
        self.attention_weights[key] = 1.0

        # Store with short TTL
        return await super().store(key, value, metadata, ttl)

    async def get_context(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent context from working memory

        Args:
            limit: Maximum items to return

        Returns:
            List of recent context items
        """
        # Return most recent items with high attention weights
        items = list(self.buffer)[-limit:]

        # Sort by attention weight if available
        if self.attention_weights:
            items.sort(
                key=lambda x: self.attention_weights.get(x["key"], 0),
                reverse=True
            )

        return items[:limit]

    async def update_attention(self, key: str, weight: float):
        """
        Update attention weight for an item

        Args:
            key: Item key
            weight: New attention weight (0-1)
        """
        self.attention_weights[key] = max(0.0, min(1.0, weight))

    async def decay_attention(self, decay_rate: float = 0.95):
        """
        Decay attention weights over time

        Args:
            decay_rate: Rate of decay (0-1)
        """
        for key in list(self.attention_weights.keys()):
            self.attention_weights[key] *= decay_rate

            # Remove if attention is too low
            if self.attention_weights[key] < 0.01:
                del self.attention_weights[key]


class EpisodicMemory(BaseMemory):
    """
    Episodic Memory: Stores specific experiences and events
    Organized by time and context
    """

    def __init__(self, max_size: int = 10000):
        super().__init__("episodic", max_size)
        self.episodes = {}
        self.timeline = []

    async def store_episode(
        self,
        episode_id: str,
        events: List[Dict[str, Any]],
        context: Dict[str, Any],
        outcome: Optional[str] = None
    ) -> bool:
        """
        Store a complete episode

        Args:
            episode_id: Unique episode identifier
            events: List of events in the episode
            context: Episode context
            outcome: Episode outcome (success/failure/neutral)

        Returns:
            Success status
        """
        episode_data = {
            "id": episode_id,
            "events": events,
            "context": context,
            "outcome": outcome,
            "timestamp": datetime.utcnow().isoformat(),
            "duration": self._calculate_duration(events)
        }

        # Store episode
        self.episodes[episode_id] = episode_data
        self.timeline.append(episode_id)

        # Keep timeline bounded
        if len(self.timeline) > self.max_size:
            oldest = self.timeline.pop(0)
            del self.episodes[oldest]

        # Store in persistent memory
        return await self.store(episode_id, episode_data)

    async def recall_similar(
        self,
        query_context: Dict[str, Any],
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Recall episodes similar to query context

        Args:
            query_context: Context to match
            limit: Maximum episodes to return

        Returns:
            List of similar episodes
        """
        similar_episodes = []

        for episode_id, episode in self.episodes.items():
            # Calculate similarity score
            score = self._calculate_similarity(
                query_context,
                episode["context"]
            )

            similar_episodes.append({
                "episode": episode,
                "similarity": score
            })

        # Sort by similarity and return top matches
        similar_episodes.sort(key=lambda x: x["similarity"], reverse=True)
        return similar_episodes[:limit]

    async def recall_by_timerange(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> List[Dict[str, Any]]:
        """
        Recall episodes within a time range

        Args:
            start_time: Start of time range
            end_time: End of time range

        Returns:
            Episodes within range
        """
        episodes_in_range = []

        for episode_id, episode in self.episodes.items():
            episode_time = datetime.fromisoformat(episode["timestamp"])

            if start_time <= episode_time <= end_time:
                episodes_in_range.append(episode)

        return episodes_in_range

    def _calculate_duration(self, events: List[Dict[str, Any]]) -> float:
        """Calculate episode duration from events"""
        if not events:
            return 0.0

        if len(events) < 2:
            return 0.0

        # Get first and last event timestamps
        first = events[0].get("timestamp", 0)
        last = events[-1].get("timestamp", 0)

        return last - first

    def _calculate_similarity(
        self,
        context1: Dict[str, Any],
        context2: Dict[str, Any]
    ) -> float:
        """Calculate similarity between two contexts"""
        # Simple Jaccard similarity for now
        keys1 = set(str(context1).split())
        keys2 = set(str(context2).split())

        if not keys1 or not keys2:
            return 0.0

        intersection = keys1.intersection(keys2)
        union = keys1.union(keys2)

        return len(intersection) / len(union)

    async def _store_to_database(self, key: str, data: Dict[str, Any]):
        """Store episode to database"""
        await self._db_manager.execute(
            f"""
            INSERT INTO {self.config.database.schema_prefix}.episodic_memory
            (episode_id, events, context, outcome, timestamp)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (episode_id) DO UPDATE SET
                events = EXCLUDED.events,
                context = EXCLUDED.context,
                outcome = EXCLUDED.outcome,
                timestamp = EXCLUDED.timestamp
            """,
            key,
            json.dumps(data.get("events", [])),
            json.dumps(data.get("context", {})),
            data.get("outcome"),
            data.get("timestamp")
        )


class SemanticMemory(BaseMemory):
    """
    Semantic Memory: Stores facts, concepts, and general knowledge
    Uses embeddings for semantic search
    """

    def __init__(self, max_size: int = 100000):
        super().__init__("semantic", max_size)
        self.knowledge_graph = {}
        self.concepts = {}
        self.embeddings_cache = {}

    async def store_fact(
        self,
        fact_id: str,
        subject: str,
        predicate: str,
        object: str,
        confidence: float = 1.0,
        source: Optional[str] = None
    ) -> bool:
        """
        Store a fact as a triple

        Args:
            fact_id: Unique fact identifier
            subject: Subject of the fact
            predicate: Relationship/predicate
            object: Object of the fact
            confidence: Confidence score (0-1)
            source: Source of the fact

        Returns:
            Success status
        """
        fact = {
            "id": fact_id,
            "subject": subject,
            "predicate": predicate,
            "object": object,
            "confidence": confidence,
            "source": source,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Update knowledge graph
        if subject not in self.knowledge_graph:
            self.knowledge_graph[subject] = {}

        if predicate not in self.knowledge_graph[subject]:
            self.knowledge_graph[subject][predicate] = []

        self.knowledge_graph[subject][predicate].append({
            "object": object,
            "confidence": confidence,
            "fact_id": fact_id
        })

        # Store fact
        return await self.store(fact_id, fact)

    async def store_concept(
        self,
        concept_id: str,
        name: str,
        definition: str,
        examples: List[str],
        related_concepts: List[str],
        embedding: Optional[List[float]] = None
    ) -> bool:
        """
        Store a concept with its definition and relationships

        Args:
            concept_id: Unique concept identifier
            name: Concept name
            definition: Concept definition
            examples: Example instances
            related_concepts: Related concept IDs
            embedding: Vector embedding for semantic search

        Returns:
            Success status
        """
        concept = {
            "id": concept_id,
            "name": name,
            "definition": definition,
            "examples": examples,
            "related": related_concepts,
            "embedding": embedding,
            "timestamp": datetime.utcnow().isoformat()
        }

        self.concepts[concept_id] = concept

        # Cache embedding if provided
        if embedding:
            self.embeddings_cache[concept_id] = np.array(embedding)

        return await self.store(concept_id, concept)

    async def query_facts(
        self,
        subject: Optional[str] = None,
        predicate: Optional[str] = None,
        object: Optional[str] = None,
        min_confidence: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Query facts by triple pattern

        Args:
            subject: Subject to match (optional)
            predicate: Predicate to match (optional)
            object: Object to match (optional)
            min_confidence: Minimum confidence threshold

        Returns:
            Matching facts
        """
        matching_facts = []

        # Search knowledge graph
        for subj, predicates in self.knowledge_graph.items():
            if subject and subj != subject:
                continue

            for pred, objects in predicates.items():
                if predicate and pred != predicate:
                    continue

                for obj_data in objects:
                    if object and obj_data["object"] != object:
                        continue

                    if obj_data["confidence"] >= min_confidence:
                        # Retrieve full fact
                        fact = await self.retrieve(obj_data["fact_id"])
                        if fact:
                            matching_facts.append(fact)

        return matching_facts

    async def find_related_concepts(
        self,
        concept_id: str,
        depth: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Find concepts related to a given concept

        Args:
            concept_id: Starting concept
            depth: How many levels of relationships to explore

        Returns:
            Related concepts
        """
        visited = set()
        related = []
        queue = [(concept_id, 0)]

        while queue:
            current_id, current_depth = queue.pop(0)

            if current_id in visited or current_depth > depth:
                continue

            visited.add(current_id)

            if current_id in self.concepts:
                concept = self.concepts[current_id]

                if current_id != concept_id:
                    related.append(concept)

                # Add related concepts to queue
                for related_id in concept.get("related", []):
                    if related_id not in visited:
                        queue.append((related_id, current_depth + 1))

        return related

    async def semantic_search(
        self,
        query_embedding: List[float],
        limit: int = 10,
        threshold: float = 0.7
    ) -> List[Tuple[str, float]]:
        """
        Search concepts by semantic similarity

        Args:
            query_embedding: Query vector embedding
            limit: Maximum results
            threshold: Similarity threshold

        Returns:
            List of (concept_id, similarity_score) tuples
        """
        query_vec = np.array(query_embedding)
        similarities = []

        for concept_id, embedding in self.embeddings_cache.items():
            # Cosine similarity
            similarity = np.dot(query_vec, embedding) / (
                np.linalg.norm(query_vec) * np.linalg.norm(embedding)
            )

            if similarity >= threshold:
                similarities.append((concept_id, float(similarity)))

        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:limit]


class MemoryManager:
    """
    Manages all memory types and coordinates between them
    """

    def __init__(self):
        self.working_memory = WorkingMemory()
        self.episodic_memory = EpisodicMemory()
        self.semantic_memory = SemanticMemory()
        self._initialized = False

    async def initialize(self):
        """Initialize all memory systems"""
        if self._initialized:
            return

        await self.working_memory.initialize()
        await self.episodic_memory.initialize()
        await self.semantic_memory.initialize()

        self._initialized = True

    async def consolidate(self):
        """
        Consolidate memories from working to long-term storage
        Simulates memory consolidation during sleep
        """
        # Get working memory content
        context = await self.working_memory.get_context(limit=50)

        # Extract episodes
        episodes = self._extract_episodes(context)
        for episode in episodes:
            await self.episodic_memory.store_episode(
                episode_id=episode["id"],
                events=episode["events"],
                context=episode["context"],
                outcome=episode.get("outcome")
            )

        # Extract facts
        facts = self._extract_facts(context)
        for fact in facts:
            await self.semantic_memory.store_fact(
                fact_id=fact["id"],
                subject=fact["subject"],
                predicate=fact["predicate"],
                object=fact["object"],
                confidence=fact.get("confidence", 0.8)
            )

        # Clear old working memory
        await self.working_memory.decay_attention(decay_rate=0.5)

    def _extract_episodes(self, context: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract episodic patterns from context"""
        episodes = []

        # Group related events into episodes
        current_episode = []
        episode_context = {}

        for item in context:
            # Simple heuristic: new episode if topic changes significantly
            if self._is_new_episode(item, current_episode):
                if current_episode:
                    episodes.append({
                        "id": hashlib.md5(
                            json.dumps(current_episode).encode()
                        ).hexdigest()[:8],
                        "events": current_episode,
                        "context": episode_context,
                        "outcome": "neutral"
                    })

                current_episode = [item]
                episode_context = item.get("metadata", {})
            else:
                current_episode.append(item)

        # Add final episode
        if current_episode:
            episodes.append({
                "id": hashlib.md5(
                    json.dumps(current_episode).encode()
                ).hexdigest()[:8],
                "events": current_episode,
                "context": episode_context,
                "outcome": "neutral"
            })

        return episodes

    def _extract_facts(self, context: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract semantic facts from context"""
        facts = []

        for item in context:
            # Simple fact extraction heuristic
            value = str(item.get("value", ""))

            # Look for "is" statements
            if " is " in value:
                parts = value.split(" is ", 1)
                if len(parts) == 2:
                    facts.append({
                        "id": hashlib.md5(value.encode()).hexdigest()[:8],
                        "subject": parts[0].strip(),
                        "predicate": "is",
                        "object": parts[1].strip(),
                        "confidence": 0.7
                    })

        return facts

    def _is_new_episode(
        self,
        item: Dict[str, Any],
        current_episode: List[Dict[str, Any]]
    ) -> bool:
        """Determine if item starts a new episode"""
        if not current_episode:
            return False

        # Check time gap (more than 5 minutes)
        last_time = current_episode[-1].get("timestamp", 0)
        current_time = item.get("timestamp", 0)

        if current_time - last_time > 300:
            return True

        # Check context change
        last_context = current_episode[-1].get("metadata", {})
        current_context = item.get("metadata", {})

        # Different session or user
        if last_context.get("session_id") != current_context.get("session_id"):
            return True

        return False


# Singleton instance
_memory_manager: Optional[MemoryManager] = None

async def get_memory_manager() -> MemoryManager:
    """Get singleton memory manager instance"""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager()
        await _memory_manager.initialize()
    return _memory_manager