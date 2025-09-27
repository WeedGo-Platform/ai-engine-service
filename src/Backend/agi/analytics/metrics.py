"""
Metrics Collection System for AGI
Tracks performance, usage, and quality metrics
"""

import asyncio
import logging
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
import time
import statistics

from agi.core.database import get_db_manager
from agi.config.agi_config import get_config

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics to track"""
    # Performance metrics
    RESPONSE_TIME = "response_time"
    TOKEN_USAGE = "token_usage"
    MODEL_LATENCY = "model_latency"
    MEMORY_USAGE = "memory_usage"
    
    # Usage metrics
    REQUESTS_PER_SESSION = "requests_per_session"
    SESSION_DURATION = "session_duration"
    TOOL_USAGE = "tool_usage"
    MODEL_SELECTION = "model_selection"
    
    # Quality metrics
    ERROR_RATE = "error_rate"
    FALLBACK_RATE = "fallback_rate"
    USER_SATISFACTION = "user_satisfaction"
    TASK_COMPLETION = "task_completion"
    
    # Agent metrics
    AGENT_STEPS = "agent_steps"
    AGENT_SUCCESS_RATE = "agent_success_rate"
    TOOL_SUCCESS_RATE = "tool_success_rate"
    
    # RAG metrics
    RAG_RETRIEVAL_COUNT = "rag_retrieval_count"
    RAG_RELEVANCE_SCORE = "rag_relevance_score"
    
    # Custom
    CUSTOM = "custom"


@dataclass
class Metric:
    """Represents a single metric measurement"""
    type: MetricType
    value: float
    timestamp: datetime
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = {
            'type': self.type.value,
            'value': self.value,
            'timestamp': self.timestamp.isoformat(),
        }
        if self.session_id:
            data['session_id'] = self.session_id
        if self.metadata:
            data['metadata'] = self.metadata
        return data


@dataclass
class AggregatedMetric:
    """Aggregated metric statistics"""
    type: MetricType
    count: int
    mean: float
    median: float
    std_dev: float
    min_value: float
    max_value: float
    percentile_95: float
    time_window: Tuple[datetime, datetime]


class MetricsCollector:
    """
    Collects and manages metrics for the AGI system
    """

    def __init__(self):
        """Initialize metrics collector"""
        self.config = get_config()
        self.db_manager = None
        self._metrics_buffer: List[Metric] = []
        self._buffer_lock = asyncio.Lock()
        self._flush_interval = 30  # seconds
        self._flush_task = None
        self._session_metrics: Dict[str, Dict[str, Any]] = {}

    async def initialize(self):
        """Initialize the metrics collector"""
        self.db_manager = await get_db_manager()
        await self._create_tables()
        
        # Start background flush task
        self._flush_task = asyncio.create_task(self._periodic_flush())
        
        logger.info("Metrics collector initialized")

    async def _create_tables(self):
        """Create necessary database tables"""
        conn = await self.db_manager.get_connection()
        try:
            # Metrics table
            query = """
            CREATE TABLE IF NOT EXISTS agi.metrics (
                id SERIAL PRIMARY KEY,
                metric_type VARCHAR(50) NOT NULL,
                value FLOAT NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                session_id VARCHAR(255),
                metadata JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            await conn.execute(query)

            # Create indexes
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_metrics_type ON agi.metrics (metric_type)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON agi.metrics (timestamp)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_metrics_session ON agi.metrics (session_id)")

            # Aggregated metrics table
            query = """
            CREATE TABLE IF NOT EXISTS agi.aggregated_metrics (
                id SERIAL PRIMARY KEY,
                metric_type VARCHAR(50) NOT NULL,
                time_window_start TIMESTAMP NOT NULL,
                time_window_end TIMESTAMP NOT NULL,
                count INTEGER NOT NULL,
                mean FLOAT NOT NULL,
                median FLOAT NOT NULL,
                std_dev FLOAT NOT NULL,
                min_value FLOAT NOT NULL,
                max_value FLOAT NOT NULL,
                percentile_95 FLOAT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (metric_type, time_window_start, time_window_end)
            )
            """
            await conn.execute(query)
        finally:
            await self.db_manager.release_connection(conn)

    async def record(
        self,
        metric_type: MetricType,
        value: float,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Record a metric"""
        metric = Metric(
            type=metric_type,
            value=value,
            timestamp=datetime.now(),
            session_id=session_id,
            metadata=metadata
        )
        
        async with self._buffer_lock:
            self._metrics_buffer.append(metric)
            
            # Update session metrics
            if session_id:
                if session_id not in self._session_metrics:
                    self._session_metrics[session_id] = {
                        'start_time': datetime.now(),
                        'request_count': 0,
                        'total_tokens': 0,
                        'error_count': 0,
                        'tool_usage': {}
                    }
                
                session_data = self._session_metrics[session_id]
                
                if metric_type == MetricType.REQUESTS_PER_SESSION:
                    session_data['request_count'] += 1
                elif metric_type == MetricType.TOKEN_USAGE:
                    session_data['total_tokens'] += value
                elif metric_type == MetricType.ERROR_RATE:
                    session_data['error_count'] += 1
                elif metric_type == MetricType.TOOL_USAGE and metadata:
                    tool_name = metadata.get('tool_name')
                    if tool_name:
                        session_data['tool_usage'][tool_name] = \
                            session_data['tool_usage'].get(tool_name, 0) + 1
        
        # Flush if buffer is large
        if len(self._metrics_buffer) >= 100:
            await self.flush()

    async def record_timing(
        self,
        metric_type: MetricType,
        start_time: float,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Record a timing metric"""
        elapsed = time.time() - start_time
        await self.record(metric_type, elapsed, session_id, metadata)

    async def flush(self):
        """Flush metrics buffer to database"""
        async with self._buffer_lock:
            if not self._metrics_buffer:
                return
            
            metrics_to_flush = self._metrics_buffer.copy()
            self._metrics_buffer.clear()
        
        conn = await self.db_manager.get_connection()
        try:
            # Batch insert metrics
            for metric in metrics_to_flush:
                await conn.execute(
                    """
                    INSERT INTO agi.metrics 
                    (metric_type, value, timestamp, session_id, metadata)
                    VALUES ($1, $2, $3, $4, $5)
                    """,
                    metric.type.value,
                    metric.value,
                    metric.timestamp,
                    metric.session_id,
                    metric.metadata
                )
            
            logger.debug(f"Flushed {len(metrics_to_flush)} metrics to database")
        except Exception as e:
            logger.error(f"Failed to flush metrics: {e}")
            # Re-add metrics to buffer on failure
            async with self._buffer_lock:
                self._metrics_buffer.extend(metrics_to_flush)
        finally:
            await self.db_manager.release_connection(conn)

    async def _periodic_flush(self):
        """Periodically flush metrics buffer"""
        while True:
            try:
                await asyncio.sleep(self._flush_interval)
                await self.flush()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic flush: {e}")

    async def get_metrics(
        self,
        metric_type: Optional[MetricType] = None,
        session_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[Metric]:
        """Get metrics from database"""
        conn = await self.db_manager.get_connection()
        try:
            query = "SELECT * FROM agi.metrics WHERE 1=1"
            params = []
            param_count = 0
            
            if metric_type:
                param_count += 1
                query += f" AND metric_type = ${param_count}"
                params.append(metric_type.value)
            
            if session_id:
                param_count += 1
                query += f" AND session_id = ${param_count}"
                params.append(session_id)
            
            if start_time:
                param_count += 1
                query += f" AND timestamp >= ${param_count}"
                params.append(start_time)
            
            if end_time:
                param_count += 1
                query += f" AND timestamp <= ${param_count}"
                params.append(end_time)
            
            query += f" ORDER BY timestamp DESC LIMIT {limit}"
            
            rows = await conn.fetch(query, *params)
            
            metrics = []
            for row in rows:
                metric = Metric(
                    type=MetricType(row['metric_type']),
                    value=row['value'],
                    timestamp=row['timestamp'],
                    session_id=row['session_id'],
                    metadata=row['metadata']
                )
                metrics.append(metric)
            
            return metrics
        finally:
            await self.db_manager.release_connection(conn)

    async def aggregate_metrics(
        self,
        metric_type: MetricType,
        start_time: datetime,
        end_time: datetime
    ) -> Optional[AggregatedMetric]:
        """Aggregate metrics for a time window"""
        metrics = await self.get_metrics(
            metric_type=metric_type,
            start_time=start_time,
            end_time=end_time,
            limit=10000
        )
        
        if not metrics:
            return None
        
        values = [m.value for m in metrics]
        
        return AggregatedMetric(
            type=metric_type,
            count=len(values),
            mean=statistics.mean(values),
            median=statistics.median(values),
            std_dev=statistics.stdev(values) if len(values) > 1 else 0,
            min_value=min(values),
            max_value=max(values),
            percentile_95=self._calculate_percentile(values, 95),
            time_window=(start_time, end_time)
        )

    def _calculate_percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile value"""
        if not values:
            return 0
        
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        
        if index >= len(sorted_values):
            return sorted_values[-1]
        
        return sorted_values[index]

    async def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get summary metrics for a session"""
        # Get from cache if available
        if session_id in self._session_metrics:
            session_data = self._session_metrics[session_id]
            duration = (datetime.now() - session_data['start_time']).total_seconds()
            
            return {
                'session_id': session_id,
                'duration_seconds': duration,
                'request_count': session_data['request_count'],
                'total_tokens': session_data['total_tokens'],
                'error_count': session_data['error_count'],
                'error_rate': session_data['error_count'] / max(session_data['request_count'], 1),
                'tool_usage': session_data['tool_usage'],
                'avg_tokens_per_request': session_data['total_tokens'] / max(session_data['request_count'], 1)
            }
        
        # Get from database
        metrics = await self.get_metrics(session_id=session_id)
        
        if not metrics:
            return {'session_id': session_id, 'no_data': True}
        
        # Calculate summary
        request_count = sum(1 for m in metrics if m.type == MetricType.REQUESTS_PER_SESSION)
        total_tokens = sum(m.value for m in metrics if m.type == MetricType.TOKEN_USAGE)
        error_count = sum(1 for m in metrics if m.type == MetricType.ERROR_RATE)
        
        # Get tool usage
        tool_usage = {}
        for m in metrics:
            if m.type == MetricType.TOOL_USAGE and m.metadata:
                tool_name = m.metadata.get('tool_name')
                if tool_name:
                    tool_usage[tool_name] = tool_usage.get(tool_name, 0) + 1
        
        # Calculate duration
        timestamps = [m.timestamp for m in metrics]
        duration = (max(timestamps) - min(timestamps)).total_seconds() if timestamps else 0
        
        return {
            'session_id': session_id,
            'duration_seconds': duration,
            'request_count': request_count,
            'total_tokens': total_tokens,
            'error_count': error_count,
            'error_rate': error_count / max(request_count, 1),
            'tool_usage': tool_usage,
            'avg_tokens_per_request': total_tokens / max(request_count, 1)
        }

    async def get_system_stats(
        self,
        time_window_hours: int = 24
    ) -> Dict[str, Any]:
        """Get overall system statistics"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=time_window_hours)
        
        # Aggregate key metrics
        response_time = await self.aggregate_metrics(
            MetricType.RESPONSE_TIME, start_time, end_time
        )
        token_usage = await self.aggregate_metrics(
            MetricType.TOKEN_USAGE, start_time, end_time
        )
        error_rate = await self.aggregate_metrics(
            MetricType.ERROR_RATE, start_time, end_time
        )
        
        stats = {
            'time_window': {
                'start': start_time.isoformat(),
                'end': end_time.isoformat(),
                'hours': time_window_hours
            }
        }
        
        if response_time:
            stats['response_time'] = {
                'mean_seconds': response_time.mean,
                'median_seconds': response_time.median,
                'p95_seconds': response_time.percentile_95,
                'request_count': response_time.count
            }
        
        if token_usage:
            stats['token_usage'] = {
                'total': int(sum([token_usage.mean * token_usage.count])),
                'mean_per_request': token_usage.mean,
                'max_per_request': token_usage.max_value
            }
        
        if error_rate:
            stats['errors'] = {
                'total_errors': error_rate.count,
                'error_rate': error_rate.mean
            }
        
        return stats

    async def cleanup(self):
        """Clean up resources"""
        # Cancel flush task
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
        
        # Final flush
        await self.flush()
        
        logger.info("Metrics collector cleaned up")


# Singleton instance
_metrics_collector: Optional[MetricsCollector] = None

async def get_metrics_collector() -> MetricsCollector:
    """Get singleton metrics collector instance"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
        await _metrics_collector.initialize()
    return _metrics_collector