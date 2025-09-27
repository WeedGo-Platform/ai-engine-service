"""
Pattern Recognition Engine for AGI Learning
Identifies patterns in conversations and interactions for improvement
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple
from enum import Enum
from collections import defaultdict, Counter
import re
import statistics

from agi.core.database import get_db_manager
from agi.core.interfaces import ConversationContext, Message
from agi.config.agi_config import get_config

logger = logging.getLogger(__name__)


class PatternType(Enum):
    """Types of patterns to recognize"""
    CONVERSATION_FLOW = "conversation_flow"  # How conversations typically progress
    QUERY_STRUCTURE = "query_structure"  # Common query patterns
    RESPONSE_PREFERENCE = "response_preference"  # Preferred response styles
    ERROR_PATTERN = "error_pattern"  # Common error scenarios
    TOOL_USAGE = "tool_usage"  # Tool usage patterns
    TOPIC_CLUSTER = "topic_cluster"  # Topic clustering
    INTERACTION_SEQUENCE = "interaction_sequence"  # Interaction sequences
    FEEDBACK_CORRELATION = "feedback_correlation"  # Feedback patterns


@dataclass
class Pattern:
    """Represents a recognized pattern"""
    type: PatternType
    pattern_id: str
    description: str
    confidence: float  # 0.0 to 1.0
    frequency: int
    examples: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    first_seen: datetime
    last_seen: datetime

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'type': self.type.value,
            'pattern_id': self.pattern_id,
            'description': self.description,
            'confidence': self.confidence,
            'frequency': self.frequency,
            'examples': self.examples,
            'metadata': self.metadata,
            'first_seen': self.first_seen.isoformat(),
            'last_seen': self.last_seen.isoformat()
        }


@dataclass
class PatternMatch:
    """Represents a pattern match in data"""
    pattern: Pattern
    match_confidence: float
    matched_data: Dict[str, Any]
    suggestions: List[str]


class PatternRecognitionEngine:
    """
    Recognizes patterns in AGI interactions for learning
    """

    def __init__(self):
        """Initialize pattern recognition engine"""
        self.config = get_config()
        self.db_manager = None
        self._patterns_cache: Dict[str, Pattern] = {}
        self._pattern_matchers: Dict[PatternType, callable] = {}
        self._recognition_task = None
        self._initialize_matchers()

    def _initialize_matchers(self):
        """Initialize pattern matchers"""
        self._pattern_matchers = {
            PatternType.CONVERSATION_FLOW: self._match_conversation_flow,
            PatternType.QUERY_STRUCTURE: self._match_query_structure,
            PatternType.RESPONSE_PREFERENCE: self._match_response_preference,
            PatternType.ERROR_PATTERN: self._match_error_pattern,
            PatternType.TOOL_USAGE: self._match_tool_usage,
            PatternType.TOPIC_CLUSTER: self._match_topic_cluster,
            PatternType.INTERACTION_SEQUENCE: self._match_interaction_sequence,
            PatternType.FEEDBACK_CORRELATION: self._match_feedback_correlation
        }

    async def initialize(self):
        """Initialize the pattern recognition engine"""
        self.db_manager = await get_db_manager()
        await self._create_tables()
        await self._load_patterns()

        # Start background recognition task
        self._recognition_task = asyncio.create_task(self._recognition_loop())

        logger.info("Pattern recognition engine initialized")

    async def _create_tables(self):
        """Create necessary database tables"""
        conn = await self.db_manager.get_connection()
        try:
            # Patterns table
            query = """
            CREATE TABLE IF NOT EXISTS agi.learned_patterns (
                id SERIAL PRIMARY KEY,
                pattern_type VARCHAR(50) NOT NULL,
                pattern_id VARCHAR(255) UNIQUE NOT NULL,
                description TEXT,
                confidence FLOAT DEFAULT 0.0,
                frequency INTEGER DEFAULT 0,
                examples JSONB,
                metadata JSONB,
                first_seen TIMESTAMP,
                last_seen TIMESTAMP,
                active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            await conn.execute(query)

            # Create indexes
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_patterns_type ON agi.learned_patterns (pattern_type)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_patterns_confidence ON agi.learned_patterns (confidence)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_patterns_active ON agi.learned_patterns (active)")

            # Pattern matches table
            query = """
            CREATE TABLE IF NOT EXISTS agi.pattern_matches (
                id SERIAL PRIMARY KEY,
                pattern_id VARCHAR(255) REFERENCES agi.learned_patterns(pattern_id),
                session_id VARCHAR(255),
                match_confidence FLOAT,
                matched_data JSONB,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            await conn.execute(query)

            # Create index
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_matches_pattern ON agi.pattern_matches (pattern_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_matches_session ON agi.pattern_matches (session_id)")
        finally:
            await self.db_manager.release_connection(conn)

    async def _load_patterns(self):
        """Load patterns from database into cache"""
        conn = await self.db_manager.get_connection()
        try:
            query = """
            SELECT * FROM agi.learned_patterns
            WHERE active = TRUE
            AND confidence > 0.3
            """
            rows = await conn.fetch(query)

            for row in rows:
                pattern = Pattern(
                    type=PatternType(row['pattern_type']),
                    pattern_id=row['pattern_id'],
                    description=row['description'],
                    confidence=row['confidence'],
                    frequency=row['frequency'],
                    examples=row['examples'] or [],
                    metadata=row['metadata'] or {},
                    first_seen=row['first_seen'],
                    last_seen=row['last_seen']
                )
                self._patterns_cache[pattern.pattern_id] = pattern

            logger.info(f"Loaded {len(self._patterns_cache)} patterns into cache")
        finally:
            await self.db_manager.release_connection(conn)

    async def recognize_patterns(
        self,
        context: ConversationContext
    ) -> List[PatternMatch]:
        """Recognize patterns in conversation context"""
        matches = []

        for pattern_type, matcher in self._pattern_matchers.items():
            try:
                pattern_matches = await matcher(context)
                matches.extend(pattern_matches)
            except Exception as e:
                logger.error(f"Error in {pattern_type} matcher: {e}")

        # Sort by confidence
        matches.sort(key=lambda x: x.match_confidence, reverse=True)

        # Record matches
        for match in matches[:5]:  # Top 5 matches
            await self._record_match(match, context.session_id)

        return matches

    async def _match_conversation_flow(
        self,
        context: ConversationContext
    ) -> List[PatternMatch]:
        """Match conversation flow patterns"""
        matches = []

        if len(context.messages) < 3:
            return matches

        # Analyze message sequence
        message_types = []
        for msg in context.messages[-10:]:  # Last 10 messages
            if msg.role == "user":
                # Classify user message type
                if "?" in msg.content:
                    message_types.append("question")
                elif any(cmd in msg.content.lower() for cmd in ["please", "can you", "could you"]):
                    message_types.append("request")
                else:
                    message_types.append("statement")
            else:
                message_types.append("response")

        # Look for patterns
        flow_pattern = "->".join(message_types[-4:])

        # Check against known patterns
        for pattern_id, pattern in self._patterns_cache.items():
            if pattern.type != PatternType.CONVERSATION_FLOW:
                continue

            if flow_pattern in pattern.metadata.get('flow_patterns', []):
                match = PatternMatch(
                    pattern=pattern,
                    match_confidence=0.8,
                    matched_data={'flow': flow_pattern},
                    suggestions=["Consider this conversation flow pattern"]
                )
                matches.append(match)

        return matches

    async def _match_query_structure(
        self,
        context: ConversationContext
    ) -> List[PatternMatch]:
        """Match query structure patterns"""
        matches = []

        if not context.messages:
            return matches

        last_user_msg = None
        for msg in reversed(context.messages):
            if msg.role == "user":
                last_user_msg = msg
                break

        if not last_user_msg:
            return matches

        # Analyze query structure
        query = last_user_msg.content

        # Check for common patterns
        patterns = {
            'how_to': r'^how (do|can|should|to)',
            'what_is': r'^what (is|are|was|were)',
            'why_question': r'^why (do|does|did|is|are)',
            'comparison': r'(better|worse|vs|versus|compared to)',
            'list_request': r'(list|enumerate|give me|show me)',
            'explanation': r'(explain|describe|tell me about)',
            'implementation': r'(implement|create|build|make|develop)'
        }

        for pattern_name, regex in patterns.items():
            if re.search(regex, query.lower()):
                # Create or update pattern
                pattern_id = f"query_{pattern_name}"
                pattern = self._patterns_cache.get(pattern_id)

                if pattern:
                    match = PatternMatch(
                        pattern=pattern,
                        match_confidence=0.7,
                        matched_data={'query_type': pattern_name, 'query': query},
                        suggestions=[f"Query matches {pattern_name} pattern"]
                    )
                    matches.append(match)

        return matches

    async def _match_response_preference(
        self,
        context: ConversationContext
    ) -> List[PatternMatch]:
        """Match response preference patterns"""
        matches = []

        # Analyze user's implicit preferences from conversation
        preferences = {
            'detail_level': 'normal',
            'code_examples': False,
            'step_by_step': False,
            'technical_depth': 'medium'
        }

        for msg in context.messages:
            if msg.role == "user":
                content_lower = msg.content.lower()

                # Check for detail preferences
                if any(word in content_lower for word in ['detailed', 'comprehensive', 'thorough']):
                    preferences['detail_level'] = 'high'
                elif any(word in content_lower for word in ['brief', 'summary', 'quick']):
                    preferences['detail_level'] = 'low'

                # Check for code preferences
                if any(word in content_lower for word in ['code', 'example', 'snippet']):
                    preferences['code_examples'] = True

                # Check for step-by-step preference
                if 'step by step' in content_lower or 'steps' in content_lower:
                    preferences['step_by_step'] = True

                # Check technical depth
                if any(word in content_lower for word in ['technical', 'advanced', 'expert']):
                    preferences['technical_depth'] = 'high'
                elif any(word in content_lower for word in ['simple', 'basic', 'beginner']):
                    preferences['technical_depth'] = 'low'

        # Match against known preference patterns
        for pattern_id, pattern in self._patterns_cache.items():
            if pattern.type != PatternType.RESPONSE_PREFERENCE:
                continue

            pattern_prefs = pattern.metadata.get('preferences', {})
            similarity = sum(1 for k, v in preferences.items() if pattern_prefs.get(k) == v)

            if similarity >= 2:  # At least 2 matching preferences
                match = PatternMatch(
                    pattern=pattern,
                    match_confidence=similarity / len(preferences),
                    matched_data={'preferences': preferences},
                    suggestions=["Adjust response style based on user preferences"]
                )
                matches.append(match)

        return matches

    async def _match_error_pattern(
        self,
        context: ConversationContext
    ) -> List[PatternMatch]:
        """Match error patterns"""
        matches = []

        # Look for error indicators in conversation
        error_indicators = [
            'error', 'failed', 'not working', 'broken', 'issue', 'problem',
            'wrong', 'incorrect', 'bug', "doesn't work", "can't"
        ]

        error_messages = []
        for msg in context.messages:
            if any(indicator in msg.content.lower() for indicator in error_indicators):
                error_messages.append(msg)

        if error_messages:
            # Identify error pattern
            pattern_id = "error_encountered"
            pattern = self._patterns_cache.get(pattern_id)

            if not pattern:
                pattern = Pattern(
                    type=PatternType.ERROR_PATTERN,
                    pattern_id=pattern_id,
                    description="User encountered an error",
                    confidence=0.7,
                    frequency=1,
                    examples=[],
                    metadata={'error_count': len(error_messages)},
                    first_seen=datetime.now(),
                    last_seen=datetime.now()
                )

            match = PatternMatch(
                pattern=pattern,
                match_confidence=0.8,
                matched_data={'error_messages': [m.content for m in error_messages]},
                suggestions=["Provide error resolution guidance", "Ask for specific error details"]
            )
            matches.append(match)

        return matches

    async def _match_tool_usage(
        self,
        context: ConversationContext
    ) -> List[PatternMatch]:
        """Match tool usage patterns"""
        matches = []

        # Analyze tool usage from metadata
        tools_used = []
        for msg in context.messages:
            if msg.metadata and 'tools_used' in msg.metadata:
                tools_used.extend(msg.metadata['tools_used'])

        if tools_used:
            # Count tool frequency
            tool_counts = Counter(tools_used)

            # Identify pattern
            pattern_id = f"tool_usage_{len(set(tools_used))}"
            pattern = Pattern(
                type=PatternType.TOOL_USAGE,
                pattern_id=pattern_id,
                description=f"Tool usage pattern with {len(set(tools_used))} unique tools",
                confidence=0.6,
                frequency=len(tools_used),
                examples=[dict(tool_counts)],
                metadata={'tool_counts': dict(tool_counts)},
                first_seen=datetime.now(),
                last_seen=datetime.now()
            )

            match = PatternMatch(
                pattern=pattern,
                match_confidence=0.7,
                matched_data={'tools': tools_used},
                suggestions=["Optimize tool selection", "Consider tool combinations"]
            )
            matches.append(match)

        return matches

    async def _match_topic_cluster(
        self,
        context: ConversationContext
    ) -> List[PatternMatch]:
        """Match topic clustering patterns"""
        matches = []

        # Extract topics from conversation
        topics = set()
        topic_keywords = {
            'programming': ['code', 'function', 'variable', 'class', 'method'],
            'data': ['database', 'query', 'table', 'data', 'sql'],
            'ai': ['model', 'training', 'neural', 'machine learning', 'ai'],
            'web': ['api', 'http', 'rest', 'endpoint', 'server'],
            'system': ['file', 'process', 'memory', 'cpu', 'disk']
        }

        for msg in context.messages:
            content_lower = msg.content.lower()
            for topic, keywords in topic_keywords.items():
                if any(keyword in content_lower for keyword in keywords):
                    topics.add(topic)

        if topics:
            # Create topic cluster pattern
            pattern_id = f"topics_{'_'.join(sorted(topics))}"
            pattern = Pattern(
                type=PatternType.TOPIC_CLUSTER,
                pattern_id=pattern_id,
                description=f"Topic cluster: {', '.join(topics)}",
                confidence=0.7,
                frequency=1,
                examples=[],
                metadata={'topics': list(topics)},
                first_seen=datetime.now(),
                last_seen=datetime.now()
            )

            match = PatternMatch(
                pattern=pattern,
                match_confidence=0.6,
                matched_data={'topics': list(topics)},
                suggestions=[f"Consider {topic}-specific optimizations" for topic in topics]
            )
            matches.append(match)

        return matches

    async def _match_interaction_sequence(
        self,
        context: ConversationContext
    ) -> List[PatternMatch]:
        """Match interaction sequence patterns"""
        matches = []

        if len(context.messages) < 4:
            return matches

        # Analyze interaction sequences
        sequences = []
        for i in range(len(context.messages) - 3):
            sequence = []
            for j in range(4):
                msg = context.messages[i + j]
                if msg.role == "user":
                    sequence.append("U")
                else:
                    sequence.append("A")
            sequences.append("".join(sequence))

        # Look for common sequences
        sequence_counts = Counter(sequences)
        most_common = sequence_counts.most_common(1)

        if most_common:
            seq, count = most_common[0]
            if count >= 2:  # Repeated sequence
                pattern_id = f"sequence_{seq}"
                pattern = Pattern(
                    type=PatternType.INTERACTION_SEQUENCE,
                    pattern_id=pattern_id,
                    description=f"Interaction sequence: {seq}",
                    confidence=count / len(sequences),
                    frequency=count,
                    examples=[seq],
                    metadata={'sequence': seq},
                    first_seen=datetime.now(),
                    last_seen=datetime.now()
                )

                match = PatternMatch(
                    pattern=pattern,
                    match_confidence=0.6,
                    matched_data={'sequences': sequences},
                    suggestions=["Optimize for this interaction pattern"]
                )
                matches.append(match)

        return matches

    async def _match_feedback_correlation(
        self,
        context: ConversationContext
    ) -> List[PatternMatch]:
        """Match feedback correlation patterns"""
        matches = []

        # Look for feedback signals in metadata
        feedback_signals = []
        for msg in context.messages:
            if msg.metadata and 'feedback' in msg.metadata:
                feedback_signals.append(msg.metadata['feedback'])

        if feedback_signals:
            # Analyze feedback patterns
            positive = sum(1 for f in feedback_signals if f.get('sentiment') == 'positive')
            negative = sum(1 for f in feedback_signals if f.get('sentiment') == 'negative')

            if negative > positive:
                pattern_id = "negative_feedback_trend"
                pattern = Pattern(
                    type=PatternType.FEEDBACK_CORRELATION,
                    pattern_id=pattern_id,
                    description="Negative feedback trend detected",
                    confidence=negative / len(feedback_signals),
                    frequency=negative,
                    examples=feedback_signals,
                    metadata={'positive': positive, 'negative': negative},
                    first_seen=datetime.now(),
                    last_seen=datetime.now()
                )

                match = PatternMatch(
                    pattern=pattern,
                    match_confidence=0.8,
                    matched_data={'feedback': feedback_signals},
                    suggestions=["Adjust response strategy", "Review recent changes"]
                )
                matches.append(match)

        return matches

    async def _record_match(
        self,
        match: PatternMatch,
        session_id: str
    ):
        """Record a pattern match"""
        conn = await self.db_manager.get_connection()
        try:
            # Update or insert pattern
            await conn.execute(
                """
                INSERT INTO agi.learned_patterns
                (pattern_type, pattern_id, description, confidence, frequency,
                 examples, metadata, first_seen, last_seen)
                VALUES ($1, $2, $3, $4, $5, $6, $7, NOW(), NOW())
                ON CONFLICT (pattern_id) DO UPDATE SET
                    confidence = (agi.learned_patterns.confidence + EXCLUDED.confidence) / 2,
                    frequency = agi.learned_patterns.frequency + 1,
                    last_seen = NOW()
                """,
                match.pattern.type.value,
                match.pattern.pattern_id,
                match.pattern.description,
                match.pattern.confidence,
                match.pattern.frequency,
                match.pattern.examples[:10],  # Keep only last 10 examples
                match.pattern.metadata
            )

            # Record match
            await conn.execute(
                """
                INSERT INTO agi.pattern_matches
                (pattern_id, session_id, match_confidence, matched_data)
                VALUES ($1, $2, $3, $4)
                """,
                match.pattern.pattern_id,
                session_id,
                match.match_confidence,
                match.matched_data
            )
        finally:
            await self.db_manager.release_connection(conn)

    async def _recognition_loop(self):
        """Background task for pattern recognition"""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                await self._analyze_recent_patterns()
                await self._consolidate_patterns()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in recognition loop: {e}")

    async def _analyze_recent_patterns(self):
        """Analyze recent patterns for insights"""
        conn = await self.db_manager.get_connection()
        try:
            # Get recent high-confidence patterns
            query = """
            SELECT pattern_id, COUNT(*) as match_count, AVG(match_confidence) as avg_confidence
            FROM agi.pattern_matches
            WHERE timestamp > NOW() - INTERVAL '1 hour'
            GROUP BY pattern_id
            HAVING COUNT(*) > 5
            ORDER BY match_count DESC
            LIMIT 10
            """

            patterns = await conn.fetch(query)

            for pattern_row in patterns:
                pattern_id = pattern_row['pattern_id']

                # Update pattern confidence
                await conn.execute(
                    """
                    UPDATE agi.learned_patterns
                    SET confidence = $1,
                        frequency = frequency + $2
                    WHERE pattern_id = $3
                    """,
                    pattern_row['avg_confidence'],
                    pattern_row['match_count'],
                    pattern_id
                )

                # Reload into cache if high confidence
                if pattern_row['avg_confidence'] > 0.7:
                    await self._load_pattern_to_cache(pattern_id)

        finally:
            await self.db_manager.release_connection(conn)

    async def _consolidate_patterns(self):
        """Consolidate similar patterns"""
        # This would implement pattern merging logic
        # For now, just clean up low-confidence patterns
        conn = await self.db_manager.get_connection()
        try:
            # Deactivate low-confidence, low-frequency patterns
            await conn.execute(
                """
                UPDATE agi.learned_patterns
                SET active = FALSE
                WHERE confidence < 0.2
                AND frequency < 3
                AND last_seen < NOW() - INTERVAL '7 days'
                """
            )
        finally:
            await self.db_manager.release_connection(conn)

    async def _load_pattern_to_cache(self, pattern_id: str):
        """Load a specific pattern into cache"""
        conn = await self.db_manager.get_connection()
        try:
            row = await conn.fetchrow(
                "SELECT * FROM agi.learned_patterns WHERE pattern_id = $1",
                pattern_id
            )

            if row:
                pattern = Pattern(
                    type=PatternType(row['pattern_type']),
                    pattern_id=row['pattern_id'],
                    description=row['description'],
                    confidence=row['confidence'],
                    frequency=row['frequency'],
                    examples=row['examples'] or [],
                    metadata=row['metadata'] or {},
                    first_seen=row['first_seen'],
                    last_seen=row['last_seen']
                )
                self._patterns_cache[pattern_id] = pattern
        finally:
            await self.db_manager.release_connection(conn)

    async def get_learned_patterns(
        self,
        pattern_type: Optional[PatternType] = None,
        min_confidence: float = 0.5
    ) -> List[Pattern]:
        """Get learned patterns"""
        patterns = []

        for pattern in self._patterns_cache.values():
            if pattern_type and pattern.type != pattern_type:
                continue
            if pattern.confidence < min_confidence:
                continue
            patterns.append(pattern)

        # Sort by confidence and frequency
        patterns.sort(key=lambda p: (p.confidence, p.frequency), reverse=True)

        return patterns

    async def cleanup(self):
        """Clean up resources"""
        if self._recognition_task:
            self._recognition_task.cancel()
            try:
                await self._recognition_task
            except asyncio.CancelledError:
                pass

        logger.info("Pattern recognition engine cleaned up")


# Singleton instance
_pattern_engine: Optional[PatternRecognitionEngine] = None

async def get_pattern_engine() -> PatternRecognitionEngine:
    """Get singleton pattern recognition engine instance"""
    global _pattern_engine
    if _pattern_engine is None:
        _pattern_engine = PatternRecognitionEngine()
        await _pattern_engine.initialize()
    return _pattern_engine