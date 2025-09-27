"""
Audit Logging System for AGI Platform
Provides comprehensive logging of all system activities for security and compliance
"""

import asyncio
import logging
import json
import hashlib
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field, asdict
import traceback
import os
from pathlib import Path

from agi.core.database import get_db_manager
from agi.core.interfaces import IModel, ITool, IAgent

logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Types of audit events"""
    # Authentication events
    AUTH_LOGIN = "auth.login"
    AUTH_LOGOUT = "auth.logout"
    AUTH_FAILED = "auth.failed"
    AUTH_TOKEN_CREATED = "auth.token_created"
    AUTH_TOKEN_REVOKED = "auth.token_revoked"
    
    # Access control events
    ACCESS_GRANTED = "access.granted"
    ACCESS_DENIED = "access.denied"
    PERMISSION_CHANGED = "permission.changed"
    ROLE_ASSIGNED = "role.assigned"
    ROLE_REMOVED = "role.removed"
    
    # Model events
    MODEL_INVOKED = "model.invoked"
    MODEL_RESPONSE = "model.response"
    MODEL_ERROR = "model.error"
    MODEL_CREATED = "model.created"
    MODEL_UPDATED = "model.updated"
    MODEL_DELETED = "model.deleted"
    
    # Tool events
    TOOL_EXECUTED = "tool.executed"
    TOOL_FAILED = "tool.failed"
    TOOL_CREATED = "tool.created"
    TOOL_UPDATED = "tool.updated"
    TOOL_DELETED = "tool.deleted"
    
    # Agent events
    AGENT_STARTED = "agent.started"
    AGENT_COMPLETED = "agent.completed"
    AGENT_FAILED = "agent.failed"
    AGENT_DELEGATED = "agent.delegated"
    
    # Data events
    DATA_READ = "data.read"
    DATA_WRITTEN = "data.written"
    DATA_DELETED = "data.deleted"
    DATA_EXPORTED = "data.exported"
    DATA_IMPORTED = "data.imported"
    
    # Security events
    SECURITY_THREAT_DETECTED = "security.threat_detected"
    SECURITY_CONTENT_FILTERED = "security.content_filtered"
    SECURITY_RATE_LIMITED = "security.rate_limited"
    SECURITY_ENCRYPTION_APPLIED = "security.encryption_applied"
    SECURITY_DECRYPTION_PERFORMED = "security.decryption_performed"
    
    # System events
    SYSTEM_STARTED = "system.started"
    SYSTEM_STOPPED = "system.stopped"
    SYSTEM_ERROR = "system.error"
    SYSTEM_CONFIG_CHANGED = "system.config_changed"
    SYSTEM_MAINTENANCE = "system.maintenance"
    
    # Custom events
    CUSTOM = "custom"


class AuditSeverity(Enum):
    """Severity levels for audit events"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Represents an audit event"""
    event_type: AuditEventType
    severity: AuditSeverity
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    action: Optional[str] = None
    result: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['event_type'] = self.event_type.value
        data['severity'] = self.severity.value
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    def calculate_hash(self) -> str:
        """Calculate hash of the event for integrity"""
        # Create deterministic string representation
        event_str = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(event_str.encode()).hexdigest()


class AuditLogger:
    """
    Comprehensive audit logging system
    """
    
    _instance = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize audit logger"""
        if not hasattr(self, '_initialized'):
            self.db_manager = None
            self._buffer: List[AuditEvent] = []
            self._buffer_size = 100
            self._flush_interval = 5  # seconds
            self._file_logger = None
            self._retention_days = 90
            self._initialized = False
            self._flush_task = None
    
    async def initialize(self):
        """Initialize the audit logging system"""
        if self._initialized:
            return
        
        async with self._lock:
            if self._initialized:
                return
            
            try:
                # Get database manager
                self.db_manager = await get_db_manager()
                
                # Create tables
                await self._create_tables()
                
                # Setup file logging
                self._setup_file_logging()
                
                # Start background flush task
                self._flush_task = asyncio.create_task(self._flush_loop())
                
                # Log system start
                await self.log_event(AuditEvent(
                    event_type=AuditEventType.SYSTEM_STARTED,
                    severity=AuditSeverity.INFO,
                    metadata={"component": "audit_logger"}
                ))
                
                self._initialized = True
                logger.info("Audit logger initialized")
                
            except Exception as e:
                logger.error(f"Failed to initialize audit logger: {e}")
                raise
    
    async def _create_tables(self):
        """Create audit logging tables"""
        queries = [
            """
            CREATE TABLE IF NOT EXISTS agi_audit_logs (
                id BIGSERIAL PRIMARY KEY,
                event_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                user_id TEXT,
                session_id TEXT,
                resource_type TEXT,
                resource_id TEXT,
                action TEXT,
                result TEXT,
                ip_address TEXT,
                user_agent TEXT,
                error_message TEXT,
                stack_trace TEXT,
                metadata JSONB DEFAULT '{}',
                event_hash TEXT NOT NULL,
                timestamp TIMESTAMPTZ NOT NULL,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS agi_audit_aggregates (
                id SERIAL PRIMARY KEY,
                period_start TIMESTAMPTZ NOT NULL,
                period_end TIMESTAMPTZ NOT NULL,
                event_type TEXT NOT NULL,
                severity TEXT,
                count BIGINT NOT NULL DEFAULT 0,
                unique_users INTEGER DEFAULT 0,
                metadata JSONB DEFAULT '{}',
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(period_start, period_end, event_type, severity)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS agi_audit_alerts (
                id SERIAL PRIMARY KEY,
                alert_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                event_count INTEGER NOT NULL,
                time_window_minutes INTEGER NOT NULL,
                triggered_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                resolved_at TIMESTAMPTZ,
                alert_data JSONB DEFAULT '{}',
                acknowledged BOOLEAN DEFAULT FALSE,
                acknowledged_by TEXT,
                acknowledged_at TIMESTAMPTZ
            )
            """
        ]
        
        for query in queries:
            await self.db_manager.execute(query)
        
        # Create indexes
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_audit_logs_event_type ON agi_audit_logs(event_type)",
            "CREATE INDEX IF NOT EXISTS idx_audit_logs_severity ON agi_audit_logs(severity)",
            "CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON agi_audit_logs(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON agi_audit_logs(timestamp DESC)",
            "CREATE INDEX IF NOT EXISTS idx_audit_logs_resource ON agi_audit_logs(resource_type, resource_id)",
            "CREATE INDEX IF NOT EXISTS idx_audit_aggregates_period ON agi_audit_aggregates(period_start, period_end)",
            "CREATE INDEX IF NOT EXISTS idx_audit_alerts_triggered ON agi_audit_alerts(triggered_at DESC)"
        ]
        
        for index in indexes:
            await self.db_manager.execute(index)
    
    def _setup_file_logging(self):
        """Setup file-based audit logging as backup"""
        try:
            # Create audit logs directory
            log_dir = Path("logs/audit")
            log_dir.mkdir(parents=True, exist_ok=True)
            
            # Create rotating file handler
            from logging.handlers import RotatingFileHandler
            
            log_file = log_dir / f"audit_{datetime.now().strftime('%Y%m%d')}.log"
            handler = RotatingFileHandler(
                log_file,
                maxBytes=100 * 1024 * 1024,  # 100 MB
                backupCount=30
            )
            
            # Set format
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            
            # Create separate logger for audit
            self._file_logger = logging.getLogger("audit_file")
            self._file_logger.setLevel(logging.INFO)
            self._file_logger.addHandler(handler)
            
        except Exception as e:
            logger.error(f"Failed to setup file logging: {e}")
    
    async def log_event(self, event: AuditEvent) -> bool:
        """
        Log an audit event
        
        Args:
            event: The audit event to log
        
        Returns:
            Success status
        """
        try:
            # Add to buffer
            self._buffer.append(event)
            
            # Write to file immediately for critical events
            if event.severity in [AuditSeverity.ERROR, AuditSeverity.CRITICAL]:
                self._write_to_file(event)
                await self._flush_buffer()  # Flush immediately for critical events
            elif len(self._buffer) >= self._buffer_size:
                await self._flush_buffer()
            
            # Check for alerts
            await self._check_alerts(event)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
            # Try to write to file as fallback
            self._write_to_file(event)
            return False
    
    def _write_to_file(self, event: AuditEvent):
        """Write event to file"""
        if self._file_logger:
            try:
                self._file_logger.info(json.dumps(event.to_dict()))
            except Exception as e:
                logger.error(f"Failed to write to audit file: {e}")
    
    async def _flush_buffer(self):
        """Flush buffered events to database"""
        if not self._buffer:
            return
        
        events_to_flush = self._buffer[:]
        self._buffer = []
        
        try:
            # Batch insert events
            for event in events_to_flush:
                event_hash = event.calculate_hash()
                
                await self.db_manager.execute(
                    """
                    INSERT INTO agi_audit_logs (
                        event_type, severity, user_id, session_id,
                        resource_type, resource_id, action, result,
                        ip_address, user_agent, error_message, stack_trace,
                        metadata, event_hash, timestamp
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
                    """,
                    event.event_type.value,
                    event.severity.value,
                    event.user_id,
                    event.session_id,
                    event.resource_type,
                    event.resource_id,
                    event.action,
                    event.result,
                    event.ip_address,
                    event.user_agent,
                    event.error_message,
                    event.stack_trace,
                    json.dumps(event.metadata),
                    event_hash,
                    event.timestamp
                )
            
            # Update aggregates
            await self._update_aggregates(events_to_flush)
            
        except Exception as e:
            logger.error(f"Failed to flush audit buffer: {e}")
            # Re-add events to buffer for retry
            self._buffer = events_to_flush + self._buffer
    
    async def _flush_loop(self):
        """Background task to periodically flush buffer"""
        while True:
            try:
                await asyncio.sleep(self._flush_interval)
                await self._flush_buffer()
            except Exception as e:
                logger.error(f"Error in flush loop: {e}")
    
    async def _update_aggregates(self, events: List[AuditEvent]):
        """Update aggregate statistics"""
        try:
            # Group events by hour
            from collections import defaultdict
            hourly_stats = defaultdict(lambda: defaultdict(int))
            
            for event in events:
                hour_start = event.timestamp.replace(minute=0, second=0, microsecond=0)
                key = (hour_start, event.event_type.value, event.severity.value)
                hourly_stats[key]['count'] += 1
                if event.user_id:
                    hourly_stats[key]['users'].add(event.user_id)
            
            # Update database
            for (hour_start, event_type, severity), stats in hourly_stats.items():
                hour_end = hour_start + timedelta(hours=1)
                unique_users = len(stats.get('users', set()))
                
                await self.db_manager.execute(
                    """
                    INSERT INTO agi_audit_aggregates (
                        period_start, period_end, event_type, severity,
                        count, unique_users
                    )
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (period_start, period_end, event_type, severity)
                    DO UPDATE SET
                        count = agi_audit_aggregates.count + $5,
                        unique_users = GREATEST(agi_audit_aggregates.unique_users, $6)
                    """,
                    hour_start,
                    hour_end,
                    event_type,
                    severity,
                    stats['count'],
                    unique_users
                )
                
        except Exception as e:
            logger.error(f"Failed to update aggregates: {e}")
    
    async def _check_alerts(self, event: AuditEvent):
        """Check if event should trigger an alert"""
        # Define alert rules
        alert_rules = [
            # Multiple failed auth attempts
            {
                'event_type': AuditEventType.AUTH_FAILED,
                'threshold': 5,
                'window_minutes': 5,
                'severity': AuditSeverity.WARNING
            },
            # Access denied events
            {
                'event_type': AuditEventType.ACCESS_DENIED,
                'threshold': 10,
                'window_minutes': 10,
                'severity': AuditSeverity.WARNING
            },
            # Security threats
            {
                'event_type': AuditEventType.SECURITY_THREAT_DETECTED,
                'threshold': 1,
                'window_minutes': 1,
                'severity': AuditSeverity.CRITICAL
            },
            # System errors
            {
                'event_type': AuditEventType.SYSTEM_ERROR,
                'threshold': 3,
                'window_minutes': 5,
                'severity': AuditSeverity.ERROR
            }
        ]
        
        for rule in alert_rules:
            if event.event_type == rule['event_type']:
                # Check recent event count
                window_start = datetime.utcnow() - timedelta(minutes=rule['window_minutes'])
                
                count_result = await self.db_manager.fetchone(
                    """
                    SELECT COUNT(*) as count
                    FROM agi_audit_logs
                    WHERE event_type = $1
                      AND timestamp >= $2
                    """,
                    rule['event_type'].value,
                    window_start
                )
                
                if count_result and count_result['count'] >= rule['threshold']:
                    # Create alert
                    await self._create_alert(
                        event_type=rule['event_type'],
                        severity=rule['severity'],
                        count=count_result['count'],
                        window_minutes=rule['window_minutes']
                    )
    
    async def _create_alert(self, event_type: AuditEventType, severity: AuditSeverity, count: int, window_minutes: int):
        """Create an alert"""
        try:
            await self.db_manager.execute(
                """
                INSERT INTO agi_audit_alerts (
                    alert_type, severity, event_count, time_window_minutes,
                    alert_data
                )
                VALUES ($1, $2, $3, $4, $5)
                """,
                event_type.value,
                severity.value,
                count,
                window_minutes,
                json.dumps({
                    'triggered_at': datetime.utcnow().isoformat(),
                    'threshold_exceeded': True
                })
            )
            
            logger.warning(f"Alert triggered: {event_type.value} occurred {count} times in {window_minutes} minutes")
            
        except Exception as e:
            logger.error(f"Failed to create alert: {e}")
    
    async def query_logs(
        self,
        event_types: Optional[List[AuditEventType]] = None,
        severities: Optional[List[AuditSeverity]] = None,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Query audit logs"""
        query = "SELECT * FROM agi_audit_logs WHERE 1=1"
        params = []
        
        if event_types:
            params.append([e.value for e in event_types])
            query += f" AND event_type = ANY(${len(params)})"
        
        if severities:
            params.append([s.value for s in severities])
            query += f" AND severity = ANY(${len(params)})"
        
        if user_id:
            params.append(user_id)
            query += f" AND user_id = ${len(params)}"
        
        if resource_type:
            params.append(resource_type)
            query += f" AND resource_type = ${len(params)}"
        
        if resource_id:
            params.append(resource_id)
            query += f" AND resource_id = ${len(params)}"
        
        if start_time:
            params.append(start_time)
            query += f" AND timestamp >= ${len(params)}"
        
        if end_time:
            params.append(end_time)
            query += f" AND timestamp <= ${len(params)}"
        
        query += f" ORDER BY timestamp DESC LIMIT {limit}"
        
        rows = await self.db_manager.fetch(query, *params)
        return [dict(row) for row in rows]
    
    async def get_statistics(
        self,
        start_time: datetime,
        end_time: datetime,
        group_by: str = "event_type"
    ) -> Dict[str, Any]:
        """Get audit statistics"""
        stats = await self.db_manager.fetch(
            f"""
            SELECT 
                {group_by},
                COUNT(*) as count,
                COUNT(DISTINCT user_id) as unique_users
            FROM agi_audit_logs
            WHERE timestamp BETWEEN $1 AND $2
            GROUP BY {group_by}
            ORDER BY count DESC
            """,
            start_time,
            end_time
        )
        
        return {
            'period': {
                'start': start_time.isoformat(),
                'end': end_time.isoformat()
            },
            'statistics': [dict(row) for row in stats]
        }
    
    async def cleanup_old_logs(self):
        """Remove old audit logs based on retention policy"""
        cutoff_date = datetime.utcnow() - timedelta(days=self._retention_days)
        
        deleted = await self.db_manager.execute(
            "DELETE FROM agi_audit_logs WHERE timestamp < $1",
            cutoff_date
        )
        
        logger.info(f"Cleaned up audit logs older than {cutoff_date}")
        return deleted


# Singleton accessor
_logger_instance = None

async def get_audit_logger() -> AuditLogger:
    """Get or create the audit logger"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = AuditLogger()
        await _logger_instance.initialize()
    return _logger_instance


# Convenience functions for common logging
async def log_model_invocation(
    model: IModel,
    user_id: str,
    prompt: str,
    response: Optional[str] = None,
    error: Optional[str] = None
):
    """Log model invocation"""
    logger = await get_audit_logger()
    
    event = AuditEvent(
        event_type=AuditEventType.MODEL_INVOKED if not error else AuditEventType.MODEL_ERROR,
        severity=AuditSeverity.INFO if not error else AuditSeverity.ERROR,
        user_id=user_id,
        resource_type="model",
        resource_id=model.get_model_id() if hasattr(model, 'get_model_id') else None,
        action="invoke",
        result="success" if not error else "error",
        error_message=error,
        metadata={
            'prompt_length': len(prompt),
            'response_length': len(response) if response else 0,
            'model_type': str(type(model).__name__)
        }
    )
    
    await logger.log_event(event)


async def log_tool_execution(
    tool: ITool,
    user_id: str,
    parameters: Dict[str, Any],
    result: Optional[Any] = None,
    error: Optional[str] = None
):
    """Log tool execution"""
    logger = await get_audit_logger()
    
    event = AuditEvent(
        event_type=AuditEventType.TOOL_EXECUTED if not error else AuditEventType.TOOL_FAILED,
        severity=AuditSeverity.INFO if not error else AuditSeverity.ERROR,
        user_id=user_id,
        resource_type="tool",
        resource_id=tool.get_definition().name if hasattr(tool, 'get_definition') else None,
        action="execute",
        result="success" if not error else "error",
        error_message=error,
        metadata={
            'parameters': parameters,
            'tool_type': str(type(tool).__name__)
        }
    )
    
    await logger.log_event(event)


async def log_security_event(
    event_type: str,
    severity: AuditSeverity,
    user_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
):
    """Log security event"""
    logger = await get_audit_logger()
    
    event = AuditEvent(
        event_type=AuditEventType.SECURITY_THREAT_DETECTED,
        severity=severity,
        user_id=user_id,
        action="security_check",
        metadata=details or {}
    )
    
    await logger.log_event(event)
