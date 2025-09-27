"""
Feedback Collection System for AGI Learning
Collects and processes user feedback for continuous improvement
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
import json

from agi.core.database import get_db_manager
from agi.config.agi_config import get_config

logger = logging.getLogger(__name__)


class FeedbackType(Enum):
    """Types of feedback"""
    EXPLICIT_RATING = "explicit_rating"  # User gives a rating
    IMPLICIT_POSITIVE = "implicit_positive"  # User accepts/uses response
    IMPLICIT_NEGATIVE = "implicit_negative"  # User rejects/rephrases
    CORRECTION = "correction"  # User corrects the response
    PREFERENCE = "preference"  # User expresses preference between options
    REPORT = "report"  # User reports an issue
    REINFORCEMENT = "reinforcement"  # System-detected success/failure


class FeedbackSentiment(Enum):
    """Sentiment of feedback"""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


@dataclass
class Feedback:
    """Represents a single feedback item"""
    session_id: str
    message_id: Optional[str]
    type: FeedbackType
    sentiment: FeedbackSentiment
    value: float  # -1.0 to 1.0 scale
    content: Optional[str]  # Text content if applicable
    metadata: Dict[str, Any]
    timestamp: datetime
    processed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'session_id': self.session_id,
            'message_id': self.message_id,
            'type': self.type.value,
            'sentiment': self.sentiment.value,
            'value': self.value,
            'content': self.content,
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat(),
            'processed': self.processed
        }


@dataclass
class FeedbackAnalysis:
    """Analysis of collected feedback"""
    total_feedback: int
    positive_ratio: float
    negative_ratio: float
    neutral_ratio: float
    average_rating: float
    common_issues: List[str]
    improvement_areas: List[str]
    strengths: List[str]
    time_period: Tuple[datetime, datetime]


class FeedbackCollector:
    """
    Collects and manages feedback for learning and improvement
    """

    def __init__(self):
        """Initialize feedback collector"""
        self.config = get_config()
        self.db_manager = None
        self._feedback_buffer: List[Feedback] = []
        self._buffer_lock = asyncio.Lock()
        self._processing_task = None

    async def initialize(self):
        """Initialize the feedback collector"""
        self.db_manager = await get_db_manager()
        await self._create_tables()

        # Start background processing
        self._processing_task = asyncio.create_task(self._process_feedback_loop())

        logger.info("Feedback collector initialized")

    async def _create_tables(self):
        """Create necessary database tables"""
        conn = await self.db_manager.get_connection()
        try:
            # Feedback table
            query = """
            CREATE TABLE IF NOT EXISTS agi.feedback (
                id SERIAL PRIMARY KEY,
                session_id VARCHAR(255) NOT NULL,
                message_id VARCHAR(255),
                feedback_type VARCHAR(50) NOT NULL,
                sentiment VARCHAR(20) NOT NULL,
                value FLOAT NOT NULL,
                content TEXT,
                metadata JSONB,
                timestamp TIMESTAMP NOT NULL,
                processed BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            await conn.execute(query)

            # Create indexes
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_feedback_session ON agi.feedback (session_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_feedback_type ON agi.feedback (feedback_type)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_feedback_sentiment ON agi.feedback (sentiment)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_feedback_processed ON agi.feedback (processed)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_feedback_timestamp ON agi.feedback (timestamp)")

            # Feedback patterns table
            query = """
            CREATE TABLE IF NOT EXISTS agi.feedback_patterns (
                id SERIAL PRIMARY KEY,
                pattern_type VARCHAR(50) NOT NULL,
                pattern_description TEXT,
                frequency INTEGER DEFAULT 0,
                confidence FLOAT DEFAULT 0.0,
                actions_taken JSONB,
                first_seen TIMESTAMP,
                last_seen TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            await conn.execute(query)
        finally:
            await self.db_manager.release_connection(conn)

    async def collect_explicit_rating(
        self,
        session_id: str,
        message_id: str,
        rating: float,
        comment: Optional[str] = None
    ):
        """Collect explicit rating from user"""
        # Normalize rating to -1.0 to 1.0 scale
        normalized_value = (rating - 3) / 2  # Assuming 1-5 scale

        sentiment = FeedbackSentiment.POSITIVE if normalized_value > 0.2 else \
                   FeedbackSentiment.NEGATIVE if normalized_value < -0.2 else \
                   FeedbackSentiment.NEUTRAL

        feedback = Feedback(
            session_id=session_id,
            message_id=message_id,
            type=FeedbackType.EXPLICIT_RATING,
            sentiment=sentiment,
            value=normalized_value,
            content=comment,
            metadata={'original_rating': rating},
            timestamp=datetime.now()
        )

        await self._add_feedback(feedback)

    async def collect_implicit_feedback(
        self,
        session_id: str,
        message_id: str,
        action: str,
        context: Dict[str, Any]
    ):
        """Collect implicit feedback from user actions"""
        # Determine feedback type and value based on action
        if action in ['accept', 'use', 'copy', 'save']:
            feedback_type = FeedbackType.IMPLICIT_POSITIVE
            value = 0.5
            sentiment = FeedbackSentiment.POSITIVE
        elif action in ['reject', 'regenerate', 'rephrase']:
            feedback_type = FeedbackType.IMPLICIT_NEGATIVE
            value = -0.3
            sentiment = FeedbackSentiment.NEGATIVE
        else:
            feedback_type = FeedbackType.IMPLICIT_POSITIVE
            value = 0.1
            sentiment = FeedbackSentiment.NEUTRAL

        feedback = Feedback(
            session_id=session_id,
            message_id=message_id,
            type=feedback_type,
            sentiment=sentiment,
            value=value,
            content=None,
            metadata={'action': action, 'context': context},
            timestamp=datetime.now()
        )

        await self._add_feedback(feedback)

    async def collect_correction(
        self,
        session_id: str,
        message_id: str,
        original_response: str,
        corrected_response: str,
        correction_type: Optional[str] = None
    ):
        """Collect correction feedback"""
        feedback = Feedback(
            session_id=session_id,
            message_id=message_id,
            type=FeedbackType.CORRECTION,
            sentiment=FeedbackSentiment.NEGATIVE,
            value=-0.5,  # Corrections indicate issues
            content=corrected_response,
            metadata={
                'original': original_response,
                'corrected': corrected_response,
                'correction_type': correction_type
            },
            timestamp=datetime.now()
        )

        await self._add_feedback(feedback)

    async def collect_preference(
        self,
        session_id: str,
        preferred_option: str,
        rejected_option: str,
        reason: Optional[str] = None
    ):
        """Collect preference feedback between options"""
        feedback = Feedback(
            session_id=session_id,
            message_id=None,
            type=FeedbackType.PREFERENCE,
            sentiment=FeedbackSentiment.NEUTRAL,
            value=0.0,  # Preferences are neutral
            content=reason,
            metadata={
                'preferred': preferred_option,
                'rejected': rejected_option
            },
            timestamp=datetime.now()
        )

        await self._add_feedback(feedback)

    async def collect_reinforcement(
        self,
        session_id: str,
        message_id: str,
        success: bool,
        metric: str,
        value: float
    ):
        """Collect system-detected reinforcement signals"""
        feedback = Feedback(
            session_id=session_id,
            message_id=message_id,
            type=FeedbackType.REINFORCEMENT,
            sentiment=FeedbackSentiment.POSITIVE if success else FeedbackSentiment.NEGATIVE,
            value=value if success else -value,
            content=None,
            metadata={
                'metric': metric,
                'success': success,
                'metric_value': value
            },
            timestamp=datetime.now()
        )

        await self._add_feedback(feedback)

    async def _add_feedback(self, feedback: Feedback):
        """Add feedback to buffer"""
        async with self._buffer_lock:
            self._feedback_buffer.append(feedback)

            # Flush if buffer is large
            if len(self._feedback_buffer) >= 50:
                await self._flush_feedback()

    async def _flush_feedback(self):
        """Flush feedback buffer to database"""
        async with self._buffer_lock:
            if not self._feedback_buffer:
                return

            feedback_to_flush = self._feedback_buffer.copy()
            self._feedback_buffer.clear()

        conn = await self.db_manager.get_connection()
        try:
            for fb in feedback_to_flush:
                await conn.execute(
                    """
                    INSERT INTO agi.feedback
                    (session_id, message_id, feedback_type, sentiment, value,
                     content, metadata, timestamp, processed)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    """,
                    fb.session_id,
                    fb.message_id,
                    fb.type.value,
                    fb.sentiment.value,
                    fb.value,
                    fb.content,
                    fb.metadata,
                    fb.timestamp,
                    fb.processed
                )

            logger.debug(f"Flushed {len(feedback_to_flush)} feedback items to database")
        except Exception as e:
            logger.error(f"Failed to flush feedback: {e}")
            # Re-add feedback to buffer on failure
            async with self._buffer_lock:
                self._feedback_buffer.extend(feedback_to_flush)
        finally:
            await self.db_manager.release_connection(conn)

    async def _process_feedback_loop(self):
        """Background task to process feedback"""
        while True:
            try:
                await asyncio.sleep(60)  # Process every minute
                await self._flush_feedback()
                await self._identify_patterns()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in feedback processing loop: {e}")

    async def _identify_patterns(self):
        """Identify patterns in feedback"""
        conn = await self.db_manager.get_connection()
        try:
            # Find common negative feedback patterns
            query = """
            SELECT feedback_type, sentiment, COUNT(*) as count,
                   AVG(value) as avg_value
            FROM agi.feedback
            WHERE processed = FALSE
            AND timestamp > NOW() - INTERVAL '1 hour'
            GROUP BY feedback_type, sentiment
            HAVING COUNT(*) > 5
            """

            patterns = await conn.fetch(query)

            for pattern in patterns:
                if pattern['sentiment'] == 'negative' and pattern['avg_value'] < -0.3:
                    # Record significant negative pattern
                    await self._record_pattern(
                        pattern_type=pattern['feedback_type'],
                        description=f"High frequency negative feedback detected",
                        frequency=pattern['count'],
                        confidence=abs(pattern['avg_value'])
                    )

            # Mark feedback as processed
            await conn.execute(
                """
                UPDATE agi.feedback
                SET processed = TRUE
                WHERE processed = FALSE
                AND timestamp < NOW() - INTERVAL '1 hour'
                """
            )
        finally:
            await self.db_manager.release_connection(conn)

    async def _record_pattern(
        self,
        pattern_type: str,
        description: str,
        frequency: int,
        confidence: float
    ):
        """Record identified pattern"""
        conn = await self.db_manager.get_connection()
        try:
            await conn.execute(
                """
                INSERT INTO agi.feedback_patterns
                (pattern_type, pattern_description, frequency, confidence,
                 first_seen, last_seen)
                VALUES ($1, $2, $3, $4, NOW(), NOW())
                ON CONFLICT (pattern_type) DO UPDATE SET
                    frequency = agi.feedback_patterns.frequency + EXCLUDED.frequency,
                    confidence = (agi.feedback_patterns.confidence + EXCLUDED.confidence) / 2,
                    last_seen = NOW()
                """,
                pattern_type,
                description,
                frequency,
                confidence
            )
        finally:
            await self.db_manager.release_connection(conn)

    async def analyze_feedback(
        self,
        time_window_hours: int = 24
    ) -> FeedbackAnalysis:
        """Analyze collected feedback"""
        conn = await self.db_manager.get_connection()
        try:
            # Get feedback statistics
            query = """
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN sentiment = 'positive' THEN 1 ELSE 0 END) as positive,
                SUM(CASE WHEN sentiment = 'negative' THEN 1 ELSE 0 END) as negative,
                SUM(CASE WHEN sentiment = 'neutral' THEN 1 ELSE 0 END) as neutral,
                AVG(value) as avg_value
            FROM agi.feedback
            WHERE timestamp > NOW() - INTERVAL '%s hours'
            """

            stats = await conn.fetchrow(query, time_window_hours)

            total = stats['total'] or 1  # Avoid division by zero

            # Get common issues (negative feedback content)
            issues_query = """
            SELECT content, COUNT(*) as count
            FROM agi.feedback
            WHERE sentiment = 'negative'
            AND content IS NOT NULL
            AND timestamp > NOW() - INTERVAL '%s hours'
            GROUP BY content
            ORDER BY count DESC
            LIMIT 5
            """

            issues = await conn.fetch(issues_query, time_window_hours)
            common_issues = [issue['content'] for issue in issues]

            # Get improvement areas from patterns
            patterns_query = """
            SELECT pattern_description
            FROM agi.feedback_patterns
            WHERE confidence > 0.5
            ORDER BY frequency DESC
            LIMIT 5
            """

            patterns = await conn.fetch(patterns_query)
            improvement_areas = [p['pattern_description'] for p in patterns]

            # Get strengths (positive feedback patterns)
            strengths_query = """
            SELECT metadata->>'action' as action, COUNT(*) as count
            FROM agi.feedback
            WHERE sentiment = 'positive'
            AND metadata IS NOT NULL
            AND timestamp > NOW() - INTERVAL '%s hours'
            GROUP BY metadata->>'action'
            ORDER BY count DESC
            LIMIT 5
            """

            strength_data = await conn.fetch(strengths_query, time_window_hours)
            strengths = [f"{s['action']} (used {s['count']} times)" for s in strength_data]

            return FeedbackAnalysis(
                total_feedback=stats['total'] or 0,
                positive_ratio=(stats['positive'] or 0) / total,
                negative_ratio=(stats['negative'] or 0) / total,
                neutral_ratio=(stats['neutral'] or 0) / total,
                average_rating=stats['avg_value'] or 0.0,
                common_issues=common_issues,
                improvement_areas=improvement_areas,
                strengths=strengths,
                time_period=(
                    datetime.now() - timedelta(hours=time_window_hours),
                    datetime.now()
                )
            )
        finally:
            await self.db_manager.release_connection(conn)

    async def get_feedback_for_learning(
        self,
        limit: int = 1000,
        min_confidence: float = 0.3
    ) -> List[Dict[str, Any]]:
        """Get processed feedback for learning algorithms"""
        conn = await self.db_manager.get_connection()
        try:
            query = """
            SELECT
                session_id,
                message_id,
                feedback_type,
                sentiment,
                value,
                content,
                metadata
            FROM agi.feedback
            WHERE ABS(value) > $1
            AND processed = TRUE
            ORDER BY timestamp DESC
            LIMIT $2
            """

            rows = await conn.fetch(query, min_confidence, limit)

            return [dict(row) for row in rows]
        finally:
            await self.db_manager.release_connection(conn)

    async def cleanup(self):
        """Clean up resources"""
        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass

        await self._flush_feedback()

        logger.info("Feedback collector cleaned up")


# Singleton instance
_feedback_collector: Optional[FeedbackCollector] = None

async def get_feedback_collector() -> FeedbackCollector:
    """Get singleton feedback collector instance"""
    global _feedback_collector
    if _feedback_collector is None:
        _feedback_collector = FeedbackCollector()
        await _feedback_collector.initialize()
    return _feedback_collector