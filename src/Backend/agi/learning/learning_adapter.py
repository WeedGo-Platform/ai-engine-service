"""
Learning Adapter for AGI System
Integrates feedback and patterns to improve model responses
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
import json

from agi.learning.feedback_collector import get_feedback_collector, FeedbackType
from agi.learning.pattern_recognition import get_pattern_engine, PatternType
from agi.knowledge.rag_system import get_rag_system
from agi.prompts import get_persona_manager, get_template_engine
from agi.core.database import get_db_manager
from agi.config.agi_config import get_config

logger = logging.getLogger(__name__)


class AdaptationType(Enum):
    """Types of adaptations"""
    PROMPT_ADJUSTMENT = "prompt_adjustment"
    RESPONSE_STYLE = "response_style"
    KNOWLEDGE_UPDATE = "knowledge_update"
    TOOL_PREFERENCE = "tool_preference"
    ERROR_HANDLING = "error_handling"
    CONVERSATION_FLOW = "conversation_flow"


@dataclass
class Adaptation:
    """Represents a learning adaptation"""
    type: AdaptationType
    description: str
    parameters: Dict[str, Any]
    confidence: float
    source: str  # feedback or pattern
    timestamp: datetime
    applied: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'type': self.type.value,
            'description': self.description,
            'parameters': self.parameters,
            'confidence': self.confidence,
            'source': self.source,
            'timestamp': self.timestamp.isoformat(),
            'applied': self.applied
        }


@dataclass
class LearningInsight:
    """Insight derived from learning"""
    title: str
    description: str
    impact_score: float  # 0.0 to 1.0
    recommendations: List[str]
    evidence: Dict[str, Any]
    timestamp: datetime


class LearningAdapter:
    """
    Adapts the AGI system based on feedback and patterns
    """

    def __init__(self):
        """Initialize learning adapter"""
        self.config = get_config()
        self.db_manager = None
        self.feedback_collector = None
        self.pattern_engine = None
        self.rag_system = None
        self.persona_manager = None
        self.template_engine = None
        self._adaptations_buffer: List[Adaptation] = []
        self._learning_task = None

    async def initialize(self):
        """Initialize the learning adapter"""
        self.db_manager = await get_db_manager()
        self.feedback_collector = await get_feedback_collector()
        self.pattern_engine = await get_pattern_engine()
        self.rag_system = await get_rag_system()
        self.persona_manager = await get_persona_manager()
        self.template_engine = await get_template_engine()

        await self._create_tables()

        # Start background learning task
        self._learning_task = asyncio.create_task(self._learning_loop())

        logger.info("Learning adapter initialized")

    async def _create_tables(self):
        """Create necessary database tables"""
        conn = await self.db_manager.get_connection()
        try:
            # Adaptations table
            query = """
            CREATE TABLE IF NOT EXISTS agi.learning_adaptations (
                id SERIAL PRIMARY KEY,
                adaptation_type VARCHAR(50) NOT NULL,
                description TEXT,
                parameters JSONB,
                confidence FLOAT,
                source VARCHAR(50),
                applied BOOLEAN DEFAULT FALSE,
                timestamp TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            await conn.execute(query)

            # Learning insights table
            query = """
            CREATE TABLE IF NOT EXISTS agi.learning_insights (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                impact_score FLOAT,
                recommendations JSONB,
                evidence JSONB,
                timestamp TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            await conn.execute(query)

            # Create indexes
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_adaptations_type ON agi.learning_adaptations (adaptation_type)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_adaptations_applied ON agi.learning_adaptations (applied)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_insights_impact ON agi.learning_insights (impact_score)")
        finally:
            await self.db_manager.release_connection(conn)

    async def learn_from_session(
        self,
        session_id: str,
        context: Dict[str, Any]
    ) -> List[Adaptation]:
        """Learn from a specific session"""
        adaptations = []

        # Analyze feedback for the session
        feedback_adaptations = await self._learn_from_feedback(session_id)
        adaptations.extend(feedback_adaptations)

        # Analyze patterns from the session
        pattern_adaptations = await self._learn_from_patterns(context)
        adaptations.extend(pattern_adaptations)

        # Store adaptations
        for adaptation in adaptations:
            await self._store_adaptation(adaptation)

        return adaptations

    async def _learn_from_feedback(
        self,
        session_id: str
    ) -> List[Adaptation]:
        """Learn from feedback data"""
        adaptations = []

        # Get feedback analysis
        analysis = await self.feedback_collector.analyze_feedback(time_window_hours=1)

        # Generate adaptations based on feedback
        if analysis.negative_ratio > 0.3:
            # High negative feedback - adjust response style
            adaptation = Adaptation(
                type=AdaptationType.RESPONSE_STYLE,
                description="Adjust response style due to negative feedback",
                parameters={
                    'tone': 'more_helpful',
                    'detail_level': 'increase',
                    'empathy': 'increase'
                },
                confidence=analysis.negative_ratio,
                source='feedback',
                timestamp=datetime.now()
            )
            adaptations.append(adaptation)

        # Learn from common issues
        if analysis.common_issues:
            for issue in analysis.common_issues[:3]:
                adaptation = Adaptation(
                    type=AdaptationType.ERROR_HANDLING,
                    description=f"Improve handling of issue: {issue[:100]}",
                    parameters={
                        'issue': issue,
                        'priority': 'high'
                    },
                    confidence=0.7,
                    source='feedback',
                    timestamp=datetime.now()
                )
                adaptations.append(adaptation)

        # Learn from strengths
        if analysis.strengths:
            adaptation = Adaptation(
                type=AdaptationType.RESPONSE_STYLE,
                description="Reinforce successful patterns",
                parameters={
                    'strengths': analysis.strengths,
                    'action': 'reinforce'
                },
                confidence=analysis.positive_ratio,
                source='feedback',
                timestamp=datetime.now()
            )
            adaptations.append(adaptation)

        return adaptations

    async def _learn_from_patterns(
        self,
        context: Dict[str, Any]
    ) -> List[Adaptation]:
        """Learn from recognized patterns"""
        adaptations = []

        # Get high-confidence patterns
        patterns = await self.pattern_engine.get_learned_patterns(min_confidence=0.6)

        for pattern in patterns[:5]:  # Top 5 patterns
            if pattern.type == PatternType.QUERY_STRUCTURE:
                # Adapt prompt templates for common query types
                adaptation = Adaptation(
                    type=AdaptationType.PROMPT_ADJUSTMENT,
                    description=f"Optimize prompts for {pattern.description}",
                    parameters={
                        'pattern_id': pattern.pattern_id,
                        'query_type': pattern.metadata.get('query_type')
                    },
                    confidence=pattern.confidence,
                    source='pattern',
                    timestamp=datetime.now()
                )
                adaptations.append(adaptation)

            elif pattern.type == PatternType.RESPONSE_PREFERENCE:
                # Adapt response style based on preferences
                prefs = pattern.metadata.get('preferences', {})
                adaptation = Adaptation(
                    type=AdaptationType.RESPONSE_STYLE,
                    description="Adapt to user response preferences",
                    parameters=prefs,
                    confidence=pattern.confidence,
                    source='pattern',
                    timestamp=datetime.now()
                )
                adaptations.append(adaptation)

            elif pattern.type == PatternType.TOOL_USAGE:
                # Optimize tool selection
                tool_counts = pattern.metadata.get('tool_counts', {})
                adaptation = Adaptation(
                    type=AdaptationType.TOOL_PREFERENCE,
                    description="Optimize tool usage patterns",
                    parameters={
                        'preferred_tools': tool_counts,
                        'optimization': 'prioritize_frequent'
                    },
                    confidence=pattern.confidence,
                    source='pattern',
                    timestamp=datetime.now()
                )
                adaptations.append(adaptation)

            elif pattern.type == PatternType.CONVERSATION_FLOW:
                # Adapt conversation flow
                adaptation = Adaptation(
                    type=AdaptationType.CONVERSATION_FLOW,
                    description="Optimize conversation flow pattern",
                    parameters={
                        'flow_pattern': pattern.metadata.get('flow_patterns', []),
                        'optimization': 'streamline'
                    },
                    confidence=pattern.confidence,
                    source='pattern',
                    timestamp=datetime.now()
                )
                adaptations.append(adaptation)

        return adaptations

    async def _store_adaptation(self, adaptation: Adaptation):
        """Store adaptation in database"""
        conn = await self.db_manager.get_connection()
        try:
            await conn.execute(
                """
                INSERT INTO agi.learning_adaptations
                (adaptation_type, description, parameters, confidence, source, applied, timestamp)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                adaptation.type.value,
                adaptation.description,
                adaptation.parameters,
                adaptation.confidence,
                adaptation.source,
                adaptation.applied,
                adaptation.timestamp
            )
        finally:
            await self.db_manager.release_connection(conn)

    async def apply_adaptations(
        self,
        adaptations: List[Adaptation]
    ) -> Dict[str, Any]:
        """Apply adaptations to the system"""
        results = {
            'applied': [],
            'failed': [],
            'skipped': []
        }

        for adaptation in adaptations:
            if adaptation.confidence < 0.5:
                results['skipped'].append({
                    'adaptation': adaptation.description,
                    'reason': 'Low confidence'
                })
                continue

            try:
                if adaptation.type == AdaptationType.PROMPT_ADJUSTMENT:
                    await self._apply_prompt_adjustment(adaptation)
                    results['applied'].append(adaptation.description)

                elif adaptation.type == AdaptationType.RESPONSE_STYLE:
                    await self._apply_response_style(adaptation)
                    results['applied'].append(adaptation.description)

                elif adaptation.type == AdaptationType.KNOWLEDGE_UPDATE:
                    await self._apply_knowledge_update(adaptation)
                    results['applied'].append(adaptation.description)

                elif adaptation.type == AdaptationType.TOOL_PREFERENCE:
                    # Tool preferences would be applied in orchestrator
                    results['applied'].append(adaptation.description)

                elif adaptation.type == AdaptationType.ERROR_HANDLING:
                    # Error handling improvements would be logged for manual review
                    results['applied'].append(adaptation.description)

                elif adaptation.type == AdaptationType.CONVERSATION_FLOW:
                    # Conversation flow optimizations would be applied in orchestrator
                    results['applied'].append(adaptation.description)

                # Mark as applied
                adaptation.applied = True
                await self._mark_adaptation_applied(adaptation)

            except Exception as e:
                logger.error(f"Failed to apply adaptation: {e}")
                results['failed'].append({
                    'adaptation': adaptation.description,
                    'error': str(e)
                })

        return results

    async def _apply_prompt_adjustment(self, adaptation: Adaptation):
        """Apply prompt adjustment adaptation"""
        params = adaptation.parameters
        query_type = params.get('query_type')

        if query_type:
            # Create or update template for this query type
            template_name = f"optimized_{query_type}"
            template_content = self._generate_optimized_template(query_type)

            from agi.prompts.template_engine import PromptTemplate
            template = PromptTemplate(
                name=template_name,
                template=template_content,
                description=f"Optimized template for {query_type} queries",
                variables=['query', 'context'],
                metadata={'query_type': query_type, 'optimized': True}
            )

            await self.template_engine.save_template(template)

    async def _apply_response_style(self, adaptation: Adaptation):
        """Apply response style adaptation"""
        params = adaptation.parameters

        # Update default persona with learned preferences
        default_persona = await self.persona_manager.get_persona('default')
        if default_persona:
            # Merge learned parameters with existing
            if params.get('tone'):
                default_persona.language_style['tone'] = params['tone']
            if params.get('detail_level'):
                default_persona.characteristics['detail_level'] = params['detail_level']

            await self.persona_manager.save_persona(default_persona)

    async def _apply_knowledge_update(self, adaptation: Adaptation):
        """Apply knowledge update adaptation"""
        params = adaptation.parameters
        content = params.get('content')
        metadata = params.get('metadata', {})

        if content:
            # Add learned knowledge to RAG system
            await self.rag_system.add_document(
                content=content,
                metadata={
                    **metadata,
                    'source': 'learning',
                    'learned_at': datetime.now().isoformat()
                }
            )

    def _generate_optimized_template(self, query_type: str) -> str:
        """Generate optimized template for query type"""
        templates = {
            'how_to': """
You are helping with a how-to question.
Query: {{ query }}
Context: {{ context }}

Provide step-by-step instructions that are:
1. Clear and actionable
2. Properly sequenced
3. Include any prerequisites
4. Mention common pitfalls to avoid
            """,
            'what_is': """
You are explaining a concept.
Query: {{ query }}
Context: {{ context }}

Provide an explanation that:
1. Starts with a concise definition
2. Includes relevant context
3. Uses appropriate examples
4. Clarifies common misconceptions
            """,
            'implementation': """
You are helping with implementation.
Query: {{ query }}
Context: {{ context }}

Provide implementation guidance that:
1. Includes working code examples
2. Explains key design decisions
3. Mentions best practices
4. Addresses edge cases
            """
        }

        return templates.get(query_type, "Query: {{ query }}\nContext: {{ context }}")

    async def _mark_adaptation_applied(self, adaptation: Adaptation):
        """Mark adaptation as applied in database"""
        conn = await self.db_manager.get_connection()
        try:
            await conn.execute(
                """
                UPDATE agi.learning_adaptations
                SET applied = TRUE
                WHERE adaptation_type = $1
                AND timestamp = $2
                """,
                adaptation.type.value,
                adaptation.timestamp
            )
        finally:
            await self.db_manager.release_connection(conn)

    async def _learning_loop(self):
        """Background task for continuous learning"""
        while True:
            try:
                await asyncio.sleep(600)  # Run every 10 minutes
                await self._perform_batch_learning()
                await self._generate_insights()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in learning loop: {e}")

    async def _perform_batch_learning(self):
        """Perform batch learning from recent data"""
        # Get recent unapplied adaptations
        conn = await self.db_manager.get_connection()
        try:
            query = """
            SELECT * FROM agi.learning_adaptations
            WHERE applied = FALSE
            AND confidence > 0.6
            AND timestamp > NOW() - INTERVAL '1 hour'
            ORDER BY confidence DESC
            LIMIT 10
            """

            rows = await conn.fetch(query)

            adaptations = []
            for row in rows:
                adaptation = Adaptation(
                    type=AdaptationType(row['adaptation_type']),
                    description=row['description'],
                    parameters=row['parameters'],
                    confidence=row['confidence'],
                    source=row['source'],
                    timestamp=row['timestamp']
                )
                adaptations.append(adaptation)

            if adaptations:
                # Apply high-confidence adaptations
                results = await self.apply_adaptations(adaptations)
                logger.info(f"Batch learning results: {results}")

        finally:
            await self.db_manager.release_connection(conn)

    async def _generate_insights(self):
        """Generate learning insights"""
        # Analyze recent adaptations and patterns
        conn = await self.db_manager.get_connection()
        try:
            # Get adaptation statistics
            query = """
            SELECT
                adaptation_type,
                COUNT(*) as count,
                AVG(confidence) as avg_confidence,
                SUM(CASE WHEN applied THEN 1 ELSE 0 END) as applied_count
            FROM agi.learning_adaptations
            WHERE timestamp > NOW() - INTERVAL '24 hours'
            GROUP BY adaptation_type
            """

            stats = await conn.fetch(query)

            for stat in stats:
                if stat['count'] > 5 and stat['avg_confidence'] > 0.6:
                    # Generate insight
                    insight = LearningInsight(
                        title=f"High frequency {stat['adaptation_type']} adaptations",
                        description=f"System is frequently adapting {stat['adaptation_type']} with {stat['avg_confidence']:.2f} confidence",
                        impact_score=stat['avg_confidence'],
                        recommendations=[
                            f"Review {stat['adaptation_type']} configurations",
                            "Consider permanent system adjustments",
                            "Analyze root causes of frequent adaptations"
                        ],
                        evidence={
                            'adaptation_count': stat['count'],
                            'applied_count': stat['applied_count'],
                            'confidence': stat['avg_confidence']
                        },
                        timestamp=datetime.now()
                    )

                    await self._store_insight(insight)

        finally:
            await self.db_manager.release_connection(conn)

    async def _store_insight(self, insight: LearningInsight):
        """Store learning insight"""
        conn = await self.db_manager.get_connection()
        try:
            await conn.execute(
                """
                INSERT INTO agi.learning_insights
                (title, description, impact_score, recommendations, evidence, timestamp)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                insight.title,
                insight.description,
                insight.impact_score,
                insight.recommendations,
                insight.evidence,
                insight.timestamp
            )
        finally:
            await self.db_manager.release_connection(conn)

    async def get_learning_insights(
        self,
        time_window_hours: int = 24,
        min_impact: float = 0.5
    ) -> List[LearningInsight]:
        """Get recent learning insights"""
        conn = await self.db_manager.get_connection()
        try:
            query = """
            SELECT * FROM agi.learning_insights
            WHERE timestamp > NOW() - INTERVAL '%s hours'
            AND impact_score >= $1
            ORDER BY impact_score DESC, timestamp DESC
            """

            rows = await conn.fetch(query, min_impact)

            insights = []
            for row in rows:
                insight = LearningInsight(
                    title=row['title'],
                    description=row['description'],
                    impact_score=row['impact_score'],
                    recommendations=row['recommendations'],
                    evidence=row['evidence'],
                    timestamp=row['timestamp']
                )
                insights.append(insight)

            return insights

        finally:
            await self.db_manager.release_connection(conn)

    async def get_adaptation_history(
        self,
        adaptation_type: Optional[AdaptationType] = None,
        limit: int = 100
    ) -> List[Adaptation]:
        """Get adaptation history"""
        conn = await self.db_manager.get_connection()
        try:
            if adaptation_type:
                query = """
                SELECT * FROM agi.learning_adaptations
                WHERE adaptation_type = $1
                ORDER BY timestamp DESC
                LIMIT $2
                """
                rows = await conn.fetch(query, adaptation_type.value, limit)
            else:
                query = """
                SELECT * FROM agi.learning_adaptations
                ORDER BY timestamp DESC
                LIMIT $1
                """
                rows = await conn.fetch(query, limit)

            adaptations = []
            for row in rows:
                adaptation = Adaptation(
                    type=AdaptationType(row['adaptation_type']),
                    description=row['description'],
                    parameters=row['parameters'],
                    confidence=row['confidence'],
                    source=row['source'],
                    timestamp=row['timestamp'],
                    applied=row['applied']
                )
                adaptations.append(adaptation)

            return adaptations

        finally:
            await self.db_manager.release_connection(conn)

    async def cleanup(self):
        """Clean up resources"""
        if self._learning_task:
            self._learning_task.cancel()
            try:
                await self._learning_task
            except asyncio.CancelledError:
                pass

        logger.info("Learning adapter cleaned up")


# Singleton instance
_learning_adapter: Optional[LearningAdapter] = None

async def get_learning_adapter() -> LearningAdapter:
    """Get singleton learning adapter instance"""
    global _learning_adapter
    if _learning_adapter is None:
        _learning_adapter = LearningAdapter()
        await _learning_adapter.initialize()
    return _learning_adapter