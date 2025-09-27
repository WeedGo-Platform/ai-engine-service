"""
Insights Generator for AGI
Generates actionable insights from analytics data
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from enum import Enum

from agi.analytics.metrics import MetricsCollector, MetricType, get_metrics_collector
from agi.analytics.analyzer import (
    ConversationAnalyzer, AnalysisResult, ConversationType,
    Sentiment, ComplexityLevel, get_conversation_analyzer
)
from agi.core.database import get_db_manager
from agi.config.agi_config import get_config

logger = logging.getLogger(__name__)


class InsightType(Enum):
    """Types of insights"""
    PERFORMANCE = "performance"
    USAGE_PATTERN = "usage_pattern"
    QUALITY = "quality"
    OPTIMIZATION = "optimization"
    ANOMALY = "anomaly"
    TREND = "trend"
    RECOMMENDATION = "recommendation"


class InsightPriority(Enum):
    """Priority levels for insights"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Insight:
    """Represents a generated insight"""
    id: str
    type: InsightType
    priority: InsightPriority
    title: str
    description: str
    evidence: Dict[str, Any]
    impact: str
    recommendations: List[str]
    timestamp: datetime
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None


class InsightsGenerator:
    """
    Generates insights from metrics and analysis data
    """

    def __init__(self):
        """Initialize insights generator"""
        self.config = get_config()
        self.db_manager = None
        self.metrics_collector = None
        self.conversation_analyzer = None
        self._insight_cache: Dict[str, Insight] = {}

    async def initialize(self):
        """Initialize the insights generator"""
        self.db_manager = await get_db_manager()
        self.metrics_collector = await get_metrics_collector()
        self.conversation_analyzer = await get_conversation_analyzer()
        await self._create_tables()
        logger.info("Insights generator initialized")

    async def _create_tables(self):
        """Create necessary database tables"""
        conn = await self.db_manager.get_connection()
        try:
            query = """
            CREATE TABLE IF NOT EXISTS agi.insights (
                id VARCHAR(255) PRIMARY KEY,
                type VARCHAR(50) NOT NULL,
                priority VARCHAR(20) NOT NULL,
                title VARCHAR(500) NOT NULL,
                description TEXT,
                evidence JSONB,
                impact TEXT,
                recommendations JSONB,
                timestamp TIMESTAMP NOT NULL,
                expires_at TIMESTAMP,
                metadata JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            await conn.execute(query)
            
            # Create index
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_insights_timestamp ON agi.insights (timestamp)"
            )
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_insights_type ON agi.insights (type)"
            )
        finally:
            await self.db_manager.release_connection(conn)

    async def generate_insights(
        self,
        time_window_hours: int = 24
    ) -> List[Insight]:
        """
        Generate insights for a time window
        
        Args:
            time_window_hours: Hours to look back
            
        Returns:
            List of generated insights
        """
        insights = []
        
        # Performance insights
        performance_insights = await self._generate_performance_insights(time_window_hours)
        insights.extend(performance_insights)
        
        # Usage pattern insights
        usage_insights = await self._generate_usage_insights(time_window_hours)
        insights.extend(usage_insights)
        
        # Quality insights
        quality_insights = await self._generate_quality_insights(time_window_hours)
        insights.extend(quality_insights)
        
        # Optimization insights
        optimization_insights = await self._generate_optimization_insights(time_window_hours)
        insights.extend(optimization_insights)
        
        # Anomaly detection
        anomaly_insights = await self._detect_anomalies(time_window_hours)
        insights.extend(anomaly_insights)
        
        # Store insights
        for insight in insights:
            await self._store_insight(insight)
        
        return insights

    async def _generate_performance_insights(
        self,
        time_window_hours: int
    ) -> List[Insight]:
        """Generate performance-related insights"""
        insights = []
        
        # Get performance metrics
        system_stats = await self.metrics_collector.get_system_stats(time_window_hours)
        
        # Response time insight
        if 'response_time' in system_stats:
            rt_data = system_stats['response_time']
            if rt_data['p95_seconds'] > 5.0:
                insight = Insight(
                    id=f"perf_slow_response_{datetime.now().timestamp()}",
                    type=InsightType.PERFORMANCE,
                    priority=InsightPriority.HIGH,
                    title="High Response Times Detected",
                    description=f"95th percentile response time is {rt_data['p95_seconds']:.2f}s, which exceeds acceptable threshold",
                    evidence={'response_time_p95': rt_data['p95_seconds'], 'mean': rt_data['mean_seconds']},
                    impact="Users experiencing slow responses, potential abandonment",
                    recommendations=[
                        "Optimize model selection for faster responses",
                        "Consider caching frequent queries",
                        "Review and optimize agent task complexity"
                    ],
                    timestamp=datetime.now(),
                    expires_at=datetime.now() + timedelta(hours=48)
                )
                insights.append(insight)
            elif rt_data['mean_seconds'] < 1.0:
                insight = Insight(
                    id=f"perf_excellent_{datetime.now().timestamp()}",
                    type=InsightType.PERFORMANCE,
                    priority=InsightPriority.LOW,
                    title="Excellent Performance",
                    description=f"Average response time is {rt_data['mean_seconds']:.2f}s",
                    evidence={'mean_response_time': rt_data['mean_seconds']},
                    impact="Users experiencing fast, responsive interactions",
                    recommendations=["Maintain current performance levels"],
                    timestamp=datetime.now()
                )
                insights.append(insight)
        
        # Token usage insight
        if 'token_usage' in system_stats:
            token_data = system_stats['token_usage']
            if token_data['mean_per_request'] > 2000:
                insight = Insight(
                    id=f"perf_high_tokens_{datetime.now().timestamp()}",
                    type=InsightType.OPTIMIZATION,
                    priority=InsightPriority.MEDIUM,
                    title="High Token Usage Per Request",
                    description=f"Average {token_data['mean_per_request']:.0f} tokens per request",
                    evidence=token_data,
                    impact="Higher costs and potential context limit issues",
                    recommendations=[
                        "Review prompt engineering for efficiency",
                        "Implement response summarization",
                        "Consider using smaller models for simple tasks"
                    ],
                    timestamp=datetime.now()
                )
                insights.append(insight)
        
        return insights

    async def _generate_usage_insights(
        self,
        time_window_hours: int
    ) -> List[Insight]:
        """Generate usage pattern insights"""
        insights = []
        
        # Analyze tool usage patterns
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=time_window_hours)
        
        tool_metrics = await self.metrics_collector.get_metrics(
            metric_type=MetricType.TOOL_USAGE,
            start_time=start_time,
            end_time=end_time
        )
        
        if tool_metrics:
            # Count tool usage
            tool_counts = {}
            for metric in tool_metrics:
                if metric.metadata and 'tool_name' in metric.metadata:
                    tool_name = metric.metadata['tool_name']
                    tool_counts[tool_name] = tool_counts.get(tool_name, 0) + 1
            
            # Find most used tools
            if tool_counts:
                sorted_tools = sorted(tool_counts.items(), key=lambda x: x[1], reverse=True)
                top_tools = sorted_tools[:3]
                
                insight = Insight(
                    id=f"usage_top_tools_{datetime.now().timestamp()}",
                    type=InsightType.USAGE_PATTERN,
                    priority=InsightPriority.LOW,
                    title="Most Used Tools",
                    description=f"Top tools: {', '.join([f'{t[0]} ({t[1]} uses)' for t in top_tools])}",
                    evidence={'tool_usage': dict(top_tools)},
                    impact="Understanding tool usage helps optimize system",
                    recommendations=[
                        "Ensure frequently used tools are optimized",
                        "Consider caching results from popular tools"
                    ],
                    timestamp=datetime.now()
                )
                insights.append(insight)
        
        # Analyze conversation types
        model_metrics = await self.metrics_collector.get_metrics(
            metric_type=MetricType.MODEL_SELECTION,
            start_time=start_time,
            end_time=end_time
        )
        
        if model_metrics:
            model_counts = {}
            for metric in model_metrics:
                if metric.metadata and 'model_id' in metric.metadata:
                    model_id = metric.metadata['model_id']
                    model_counts[model_id] = model_counts.get(model_id, 0) + 1
            
            if model_counts:
                sorted_models = sorted(model_counts.items(), key=lambda x: x[1], reverse=True)
                
                # Check for model usage imbalance
                if len(sorted_models) > 1:
                    top_usage = sorted_models[0][1]
                    total_usage = sum(count for _, count in sorted_models)
                    
                    if top_usage / total_usage > 0.8:
                        insight = Insight(
                            id=f"usage_model_imbalance_{datetime.now().timestamp()}",
                            type=InsightType.OPTIMIZATION,
                            priority=InsightPriority.MEDIUM,
                            title="Model Usage Imbalance",
                            description=f"{sorted_models[0][0]} handling {top_usage/total_usage*100:.0f}% of requests",
                            evidence={'model_distribution': dict(sorted_models)},
                            impact="Potential underutilization of model capabilities",
                            recommendations=[
                                "Review model routing logic",
                                "Consider task complexity in model selection",
                                "Ensure appropriate models for different tasks"
                            ],
                            timestamp=datetime.now()
                        )
                        insights.append(insight)
        
        return insights

    async def _generate_quality_insights(
        self,
        time_window_hours: int
    ) -> List[Insight]:
        """Generate quality-related insights"""
        insights = []
        
        # Get error metrics
        system_stats = await self.metrics_collector.get_system_stats(time_window_hours)
        
        if 'errors' in system_stats:
            error_data = system_stats['errors']
            if error_data['error_rate'] > 0.1:
                insight = Insight(
                    id=f"quality_high_errors_{datetime.now().timestamp()}",
                    type=InsightType.QUALITY,
                    priority=InsightPriority.CRITICAL,
                    title="High Error Rate",
                    description=f"Error rate is {error_data['error_rate']*100:.1f}%",
                    evidence=error_data,
                    impact="Poor user experience, potential data loss",
                    recommendations=[
                        "Investigate error patterns",
                        "Improve error handling and recovery",
                        "Add monitoring for specific error types",
                        "Review recent system changes"
                    ],
                    timestamp=datetime.now(),
                    expires_at=datetime.now() + timedelta(hours=24)
                )
                insights.append(insight)
        
        # Analyze conversation quality scores
        quality_metrics = await self.metrics_collector.get_metrics(
            metric_type=MetricType.CUSTOM,
            start_time=datetime.now() - timedelta(hours=time_window_hours),
            end_time=datetime.now()
        )
        
        quality_scores = []
        for metric in quality_metrics:
            if metric.metadata and metric.metadata.get('metric_name') == 'conversation_quality':
                quality_scores.append(metric.value)
        
        if quality_scores:
            avg_quality = sum(quality_scores) / len(quality_scores)
            
            if avg_quality < 0.5:
                insight = Insight(
                    id=f"quality_low_satisfaction_{datetime.now().timestamp()}",
                    type=InsightType.QUALITY,
                    priority=InsightPriority.HIGH,
                    title="Low Conversation Quality",
                    description=f"Average quality score is {avg_quality:.2f}/1.0",
                    evidence={'average_quality': avg_quality, 'sample_count': len(quality_scores)},
                    impact="Users may be dissatisfied with interactions",
                    recommendations=[
                        "Review conversation patterns for issues",
                        "Improve response relevance and completeness",
                        "Enhance error messages and recovery flows",
                        "Consider user feedback collection"
                    ],
                    timestamp=datetime.now()
                )
                insights.append(insight)
            elif avg_quality > 0.8:
                insight = Insight(
                    id=f"quality_high_satisfaction_{datetime.now().timestamp()}",
                    type=InsightType.QUALITY,
                    priority=InsightPriority.LOW,
                    title="High Conversation Quality",
                    description=f"Average quality score is {avg_quality:.2f}/1.0",
                    evidence={'average_quality': avg_quality},
                    impact="Users satisfied with interactions",
                    recommendations=["Maintain current quality standards"],
                    timestamp=datetime.now()
                )
                insights.append(insight)
        
        return insights

    async def _generate_optimization_insights(
        self,
        time_window_hours: int
    ) -> List[Insight]:
        """Generate optimization recommendations"""
        insights = []
        
        # Analyze agent efficiency
        agent_metrics = await self.metrics_collector.get_metrics(
            metric_type=MetricType.AGENT_STEPS,
            start_time=datetime.now() - timedelta(hours=time_window_hours),
            end_time=datetime.now()
        )
        
        if agent_metrics:
            step_counts = [m.value for m in agent_metrics]
            if step_counts:
                avg_steps = sum(step_counts) / len(step_counts)
                
                if avg_steps > 7:
                    insight = Insight(
                        id=f"opt_agent_efficiency_{datetime.now().timestamp()}",
                        type=InsightType.OPTIMIZATION,
                        priority=InsightPriority.MEDIUM,
                        title="Agent Task Complexity",
                        description=f"Agents averaging {avg_steps:.1f} steps per task",
                        evidence={'average_steps': avg_steps, 'sample_count': len(step_counts)},
                        impact="Longer processing times and higher resource usage",
                        recommendations=[
                            "Review agent planning strategies",
                            "Optimize tool selection logic",
                            "Consider task decomposition approaches",
                            "Cache intermediate results"
                        ],
                        timestamp=datetime.now()
                    )
                    insights.append(insight)
        
        # Memory usage optimization
        memory_metrics = await self.metrics_collector.get_metrics(
            metric_type=MetricType.MEMORY_USAGE,
            start_time=datetime.now() - timedelta(hours=time_window_hours),
            end_time=datetime.now()
        )
        
        if memory_metrics:
            memory_values = [m.value for m in memory_metrics]
            if memory_values:
                max_memory = max(memory_values)
                
                if max_memory > 1000:  # MB
                    insight = Insight(
                        id=f"opt_memory_usage_{datetime.now().timestamp()}",
                        type=InsightType.OPTIMIZATION,
                        priority=InsightPriority.MEDIUM,
                        title="High Memory Usage",
                        description=f"Peak memory usage: {max_memory:.0f}MB",
                        evidence={'peak_memory_mb': max_memory},
                        impact="Potential performance degradation and scaling issues",
                        recommendations=[
                            "Implement memory cleanup routines",
                            "Optimize data structures",
                            "Review caching strategies",
                            "Consider memory-efficient models"
                        ],
                        timestamp=datetime.now()
                    )
                    insights.append(insight)
        
        return insights

    async def _detect_anomalies(
        self,
        time_window_hours: int
    ) -> List[Insight]:
        """Detect anomalies in metrics"""
        insights = []
        
        # Get recent metrics for comparison
        current_end = datetime.now()
        current_start = current_end - timedelta(hours=time_window_hours)
        previous_start = current_start - timedelta(hours=time_window_hours)
        
        # Compare response times
        current_rt = await self.metrics_collector.aggregate_metrics(
            MetricType.RESPONSE_TIME,
            current_start,
            current_end
        )
        
        previous_rt = await self.metrics_collector.aggregate_metrics(
            MetricType.RESPONSE_TIME,
            previous_start,
            current_start
        )
        
        if current_rt and previous_rt:
            # Check for significant changes
            change_ratio = current_rt.mean / previous_rt.mean if previous_rt.mean > 0 else 1
            
            if change_ratio > 2.0:
                insight = Insight(
                    id=f"anomaly_response_spike_{datetime.now().timestamp()}",
                    type=InsightType.ANOMALY,
                    priority=InsightPriority.HIGH,
                    title="Response Time Spike Detected",
                    description=f"Response times increased {(change_ratio-1)*100:.0f}% compared to previous period",
                    evidence={
                        'current_mean': current_rt.mean,
                        'previous_mean': previous_rt.mean,
                        'change_ratio': change_ratio
                    },
                    impact="Degraded user experience",
                    recommendations=[
                        "Check for system resource constraints",
                        "Review recent deployments",
                        "Monitor for traffic spikes",
                        "Check external service dependencies"
                    ],
                    timestamp=datetime.now(),
                    expires_at=datetime.now() + timedelta(hours=12)
                )
                insights.append(insight)
            elif change_ratio < 0.5:
                insight = Insight(
                    id=f"anomaly_response_improvement_{datetime.now().timestamp()}",
                    type=InsightType.ANOMALY,
                    priority=InsightPriority.LOW,
                    title="Significant Performance Improvement",
                    description=f"Response times decreased {(1-change_ratio)*100:.0f}%",
                    evidence={
                        'current_mean': current_rt.mean,
                        'previous_mean': previous_rt.mean
                    },
                    impact="Improved user experience",
                    recommendations=["Document changes that led to improvement"],
                    timestamp=datetime.now()
                )
                insights.append(insight)
        
        # Check for error spikes
        current_errors = await self.metrics_collector.get_metrics(
            metric_type=MetricType.ERROR_RATE,
            start_time=current_start,
            end_time=current_end
        )
        
        if len(current_errors) > 10:
            # Group errors by hour
            hourly_errors = {}
            for error in current_errors:
                hour_key = error.timestamp.replace(minute=0, second=0, microsecond=0)
                hourly_errors[hour_key] = hourly_errors.get(hour_key, 0) + 1
            
            if hourly_errors:
                max_errors_hour = max(hourly_errors.values())
                avg_errors_hour = sum(hourly_errors.values()) / len(hourly_errors)
                
                if max_errors_hour > avg_errors_hour * 3:
                    insight = Insight(
                        id=f"anomaly_error_spike_{datetime.now().timestamp()}",
                        type=InsightType.ANOMALY,
                        priority=InsightPriority.CRITICAL,
                        title="Error Spike Detected",
                        description=f"Peak of {max_errors_hour} errors in one hour, {max_errors_hour/avg_errors_hour:.1f}x average",
                        evidence={
                            'peak_errors': max_errors_hour,
                            'average_errors': avg_errors_hour
                        },
                        impact="Service disruption for affected users",
                        recommendations=[
                            "Investigate error logs immediately",
                            "Check for cascading failures",
                            "Review error handling and circuit breakers",
                            "Consider rolling back recent changes"
                        ],
                        timestamp=datetime.now(),
                        expires_at=datetime.now() + timedelta(hours=6)
                    )
                    insights.append(insight)
        
        return insights

    async def _store_insight(self, insight: Insight):
        """Store insight in database"""
        conn = await self.db_manager.get_connection()
        try:
            query = """
            INSERT INTO agi.insights (
                id, type, priority, title, description,
                evidence, impact, recommendations, timestamp,
                expires_at, metadata
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            ON CONFLICT (id) DO UPDATE SET
                priority = EXCLUDED.priority,
                description = EXCLUDED.description,
                evidence = EXCLUDED.evidence,
                timestamp = EXCLUDED.timestamp
            """
            
            import json
            await conn.execute(
                query,
                insight.id,
                insight.type.value,
                insight.priority.value,
                insight.title,
                insight.description,
                json.dumps(insight.evidence),
                insight.impact,
                json.dumps(insight.recommendations),
                insight.timestamp,
                insight.expires_at,
                json.dumps(insight.metadata) if insight.metadata else None
            )
        finally:
            await self.db_manager.release_connection(conn)

    async def get_active_insights(
        self,
        priority_filter: Optional[InsightPriority] = None
    ) -> List[Insight]:
        """Get active (non-expired) insights"""
        conn = await self.db_manager.get_connection()
        try:
            query = """
            SELECT * FROM agi.insights
            WHERE (expires_at IS NULL OR expires_at > NOW())
            """
            params = []
            
            if priority_filter:
                query += " AND priority = $1"
                params.append(priority_filter.value)
            
            query += " ORDER BY timestamp DESC"
            
            rows = await conn.fetch(query, *params)
            
            insights = []
            for row in rows:
                import json
                insight = Insight(
                    id=row['id'],
                    type=InsightType(row['type']),
                    priority=InsightPriority(row['priority']),
                    title=row['title'],
                    description=row['description'],
                    evidence=json.loads(row['evidence']) if row['evidence'] else {},
                    impact=row['impact'],
                    recommendations=json.loads(row['recommendations']) if row['recommendations'] else [],
                    timestamp=row['timestamp'],
                    expires_at=row['expires_at'],
                    metadata=json.loads(row['metadata']) if row['metadata'] else None
                )
                insights.append(insight)
            
            return insights
        finally:
            await self.db_manager.release_connection(conn)


# Singleton instance
_insights_generator: Optional[InsightsGenerator] = None

async def get_insights_generator() -> InsightsGenerator:
    """Get singleton insights generator instance"""
    global _insights_generator
    if _insights_generator is None:
        _insights_generator = InsightsGenerator()
        await _insights_generator.initialize()
    return _insights_generator