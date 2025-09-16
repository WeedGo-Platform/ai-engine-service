"""
Comprehensive Audit Logging System
Provides detailed logging of all security-relevant events and API access
"""

import json
import time
import hashlib
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, asdict
from enum import Enum
import asyncpg
import redis.asyncio as redis
from fastapi import Request, Response
import logging
import os
import gzip
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Types of audit events"""
    # Authentication events
    AUTH_LOGIN_SUCCESS = "auth.login.success"
    AUTH_LOGIN_FAILED = "auth.login.failed"
    AUTH_LOGOUT = "auth.logout"
    AUTH_TOKEN_CREATED = "auth.token.created"
    AUTH_TOKEN_REVOKED = "auth.token.revoked"
    AUTH_PASSWORD_CHANGED = "auth.password.changed"
    AUTH_MFA_ENABLED = "auth.mfa.enabled"
    AUTH_MFA_DISABLED = "auth.mfa.disabled"

    # API access events
    API_REQUEST = "api.request"
    API_RESPONSE = "api.response"
    API_ERROR = "api.error"
    API_RATE_LIMITED = "api.rate_limited"

    # Data access events
    DATA_READ = "data.read"
    DATA_CREATED = "data.created"
    DATA_UPDATED = "data.updated"
    DATA_DELETED = "data.deleted"
    DATA_EXPORTED = "data.exported"

    # Security events
    SECURITY_VIOLATION = "security.violation"
    SECURITY_PERMISSION_DENIED = "security.permission_denied"
    SECURITY_SUSPICIOUS_ACTIVITY = "security.suspicious_activity"
    SECURITY_BREACH_ATTEMPT = "security.breach_attempt"

    # Configuration changes
    CONFIG_CHANGED = "config.changed"
    CONFIG_PERMISSION_GRANTED = "config.permission.granted"
    CONFIG_PERMISSION_REVOKED = "config.permission.revoked"

    # Payment events (PCI DSS)
    PAYMENT_INITIATED = "payment.initiated"
    PAYMENT_COMPLETED = "payment.completed"
    PAYMENT_FAILED = "payment.failed"
    PAYMENT_REFUNDED = "payment.refunded"

    # Compliance events
    COMPLIANCE_DATA_REQUEST = "compliance.data_request"
    COMPLIANCE_DATA_DELETION = "compliance.data_deletion"
    COMPLIANCE_CONSENT_GRANTED = "compliance.consent_granted"
    COMPLIANCE_CONSENT_REVOKED = "compliance.consent_revoked"


class AuditSeverity(Enum):
    """Severity levels for audit events"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Audit event structure"""
    event_id: str
    timestamp: datetime
    event_type: AuditEventType
    severity: AuditSeverity
    actor_id: Optional[str]  # User or service ID
    actor_type: str  # user, service, system
    actor_ip: Optional[str]
    actor_user_agent: Optional[str]
    resource_type: Optional[str]  # Type of resource accessed
    resource_id: Optional[str]  # ID of resource accessed
    action: str  # Action performed
    result: str  # success, failure, error
    details: Dict[str, Any]  # Additional details
    request_id: Optional[str]  # Correlation ID
    session_id: Optional[str]
    api_endpoint: Optional[str]
    http_method: Optional[str]
    response_code: Optional[int]
    response_time_ms: Optional[int]
    data_hash: Optional[str]  # Hash of sensitive data for integrity


class AuditLogger:
    """
    Comprehensive audit logging system

    Features:
    - Structured logging with event types and severity
    - Multiple storage backends (database, file, syslog)
    - Real-time streaming to SIEM systems
    - Tamper-proof logging with cryptographic signatures
    - Automatic PII redaction
    - Log rotation and archival
    - Query and search capabilities
    - Compliance reporting (GDPR, CCPA, PCI DSS)
    """

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize audit logger"""
        self.config = config or {}

        # Storage configuration
        self.enable_database = self.config.get('enable_database', True)
        self.enable_file = self.config.get('enable_file', True)
        self.enable_syslog = self.config.get('enable_syslog', False)
        self.enable_streaming = self.config.get('enable_streaming', False)

        # File storage settings
        self.log_dir = Path(self.config.get('log_dir', '/var/log/weedgo/audit'))
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.max_file_size = self.config.get('max_file_size', 100 * 1024 * 1024)  # 100MB
        self.compress_logs = self.config.get('compress_logs', True)
        self.retention_days = self.config.get('retention_days', 90)

        # Security settings
        self.sign_logs = self.config.get('sign_logs', True)
        self.signing_key = os.environ.get('AUDIT_SIGNING_KEY', self._generate_signing_key())
        self.redact_pii = self.config.get('redact_pii', True)

        # Performance settings
        self.batch_size = self.config.get('batch_size', 100)
        self.flush_interval = self.config.get('flush_interval', 5)  # seconds
        self.buffer: List[AuditEvent] = []

        # Storage backends
        self.db_pool: Optional[asyncpg.Pool] = None
        self.redis_client: Optional[redis.Redis] = None

        # PII patterns to redact
        self.pii_patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
            'credit_card': r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
            'ip_address': r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        }

    def _generate_signing_key(self) -> str:
        """Generate signing key for log integrity"""
        return hashlib.sha256(os.urandom(32)).hexdigest()

    async def initialize(self, db_pool: asyncpg.Pool = None, redis_client: redis.Redis = None):
        """Initialize storage backends"""
        self.db_pool = db_pool
        self.redis_client = redis_client

        if self.db_pool and self.enable_database:
            await self._create_tables()

        # Start background flush task
        asyncio.create_task(self._flush_buffer_task())

    async def _create_tables(self):
        """Create audit log tables"""
        if not self.db_pool:
            return

        async with self.db_pool.acquire() as conn:
            # Main audit log table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    event_id UUID PRIMARY KEY,
                    timestamp TIMESTAMPTZ NOT NULL,
                    event_type VARCHAR(100) NOT NULL,
                    severity VARCHAR(20) NOT NULL,
                    actor_id VARCHAR(255),
                    actor_type VARCHAR(50) NOT NULL,
                    actor_ip INET,
                    actor_user_agent TEXT,
                    resource_type VARCHAR(100),
                    resource_id VARCHAR(255),
                    action VARCHAR(100) NOT NULL,
                    result VARCHAR(50) NOT NULL,
                    details JSONB,
                    request_id UUID,
                    session_id VARCHAR(255),
                    api_endpoint VARCHAR(255),
                    http_method VARCHAR(10),
                    response_code INTEGER,
                    response_time_ms INTEGER,
                    data_hash VARCHAR(64),
                    signature VARCHAR(128),

                    -- Indexes for common queries
                    INDEX idx_audit_timestamp (timestamp DESC),
                    INDEX idx_audit_actor (actor_id),
                    INDEX idx_audit_event_type (event_type),
                    INDEX idx_audit_severity (severity),
                    INDEX idx_audit_resource (resource_type, resource_id),
                    INDEX idx_audit_session (session_id),
                    INDEX idx_audit_request (request_id)
                ) PARTITION BY RANGE (timestamp);
            """)

            # Create monthly partitions
            current_month = datetime.now(timezone.utc).strftime('%Y_%m')
            await conn.execute(f"""
                CREATE TABLE IF NOT EXISTS audit_log_{current_month}
                PARTITION OF audit_log
                FOR VALUES FROM ('{datetime.now(timezone.utc).replace(day=1).isoformat()}')
                TO ('{(datetime.now(timezone.utc).replace(day=1) + timedelta(days=32)).replace(day=1).isoformat()}')
            """)

            # Summary statistics table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_statistics (
                    date DATE PRIMARY KEY,
                    event_counts JSONB NOT NULL,
                    unique_actors INTEGER,
                    total_events INTEGER,
                    error_count INTEGER,
                    avg_response_time_ms FLOAT,
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)

    async def log_event(
        self,
        event_type: AuditEventType,
        action: str,
        result: str = "success",
        severity: AuditSeverity = AuditSeverity.INFO,
        actor_id: Optional[str] = None,
        actor_type: str = "system",
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None,
        response: Optional[Response] = None,
        response_time_ms: Optional[int] = None
    ) -> str:
        """
        Log an audit event

        Args:
            event_type: Type of event
            action: Action performed
            result: Result of action (success, failure, error)
            severity: Event severity
            actor_id: ID of actor (user/service)
            actor_type: Type of actor
            resource_type: Type of resource accessed
            resource_id: ID of resource
            details: Additional event details
            request: FastAPI request object
            response: FastAPI response object
            response_time_ms: Response time in milliseconds

        Returns:
            Event ID
        """
        # Generate event ID
        event_id = str(uuid.uuid4())

        # Extract request information
        actor_ip = None
        actor_user_agent = None
        api_endpoint = None
        http_method = None
        request_id = None
        session_id = None

        if request:
            actor_ip = request.client.host if request.client else None
            actor_user_agent = request.headers.get('user-agent')
            api_endpoint = str(request.url.path)
            http_method = request.method
            request_id = request.headers.get('x-request-id')
            session_id = request.headers.get('x-session-id')

        # Extract response information
        response_code = None
        if response:
            response_code = response.status_code

        # Redact PII from details if enabled
        if self.redact_pii and details:
            details = self._redact_pii_from_dict(details)

        # Create audit event
        event = AuditEvent(
            event_id=event_id,
            timestamp=datetime.now(timezone.utc),
            event_type=event_type,
            severity=severity,
            actor_id=actor_id,
            actor_type=actor_type,
            actor_ip=actor_ip,
            actor_user_agent=actor_user_agent,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            result=result,
            details=details or {},
            request_id=request_id,
            session_id=session_id,
            api_endpoint=api_endpoint,
            http_method=http_method,
            response_code=response_code,
            response_time_ms=response_time_ms,
            data_hash=self._compute_data_hash(details) if details else None
        )

        # Add to buffer
        self.buffer.append(event)

        # Flush if buffer is full
        if len(self.buffer) >= self.batch_size:
            await self._flush_buffer()

        # Log critical events immediately
        if severity == AuditSeverity.CRITICAL:
            await self._flush_buffer()
            await self._alert_critical_event(event)

        return event_id

    def _redact_pii_from_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Redact PII from dictionary"""
        import re
        import copy

        redacted = copy.deepcopy(data)

        def redact_value(value: Any) -> Any:
            if isinstance(value, str):
                for pattern_name, pattern in self.pii_patterns.items():
                    value = re.sub(pattern, f"[REDACTED_{pattern_name.upper()}]", value)
            elif isinstance(value, dict):
                return {k: redact_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [redact_value(item) for item in value]
            return value

        return {k: redact_value(v) for k, v in redacted.items()}

    def _compute_data_hash(self, data: Dict[str, Any]) -> str:
        """Compute hash of data for integrity verification"""
        json_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()

    def _sign_event(self, event: AuditEvent) -> str:
        """Sign event for tamper detection"""
        if not self.sign_logs:
            return ""

        # Create canonical representation
        event_str = json.dumps(asdict(event), sort_keys=True, default=str)

        # Compute signature
        signature = hashlib.sha512(
            f"{self.signing_key}{event_str}".encode()
        ).hexdigest()

        return signature

    async def _flush_buffer(self):
        """Flush buffered events to storage"""
        if not self.buffer:
            return

        events_to_flush = self.buffer[:]
        self.buffer.clear()

        # Write to different backends
        tasks = []

        if self.enable_database and self.db_pool:
            tasks.append(self._write_to_database(events_to_flush))

        if self.enable_file:
            tasks.append(self._write_to_file(events_to_flush))

        if self.enable_streaming and self.redis_client:
            tasks.append(self._stream_events(events_to_flush))

        # Execute all writes concurrently
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _write_to_database(self, events: List[AuditEvent]):
        """Write events to database"""
        if not self.db_pool:
            return

        try:
            async with self.db_pool.acquire() as conn:
                # Batch insert
                values = []
                for event in events:
                    signature = self._sign_event(event)
                    values.append((
                        event.event_id,
                        event.timestamp,
                        event.event_type.value,
                        event.severity.value,
                        event.actor_id,
                        event.actor_type,
                        event.actor_ip,
                        event.actor_user_agent,
                        event.resource_type,
                        event.resource_id,
                        event.action,
                        event.result,
                        json.dumps(event.details) if event.details else None,
                        event.request_id,
                        event.session_id,
                        event.api_endpoint,
                        event.http_method,
                        event.response_code,
                        event.response_time_ms,
                        event.data_hash,
                        signature
                    ))

                await conn.executemany("""
                    INSERT INTO audit_log (
                        event_id, timestamp, event_type, severity,
                        actor_id, actor_type, actor_ip, actor_user_agent,
                        resource_type, resource_id, action, result,
                        details, request_id, session_id, api_endpoint,
                        http_method, response_code, response_time_ms,
                        data_hash, signature
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                             $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21)
                """, values)

                # Update statistics
                await self._update_statistics(events)

        except Exception as e:
            logger.error(f"Failed to write audit events to database: {e}")

    async def _write_to_file(self, events: List[AuditEvent]):
        """Write events to file"""
        try:
            # Generate filename with date
            date_str = datetime.now(timezone.utc).strftime('%Y%m%d')
            log_file = self.log_dir / f"audit_{date_str}.jsonl"

            # Check file size and rotate if needed
            if log_file.exists() and log_file.stat().st_size > self.max_file_size:
                await self._rotate_log_file(log_file)

            # Write events
            with open(log_file, 'a') as f:
                for event in events:
                    event_dict = asdict(event)
                    event_dict['signature'] = self._sign_event(event)
                    f.write(json.dumps(event_dict, default=str) + '\n')

            # Set secure permissions
            os.chmod(log_file, 0o640)

        except Exception as e:
            logger.error(f"Failed to write audit events to file: {e}")

    async def _rotate_log_file(self, log_file: Path):
        """Rotate log file when it reaches max size"""
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        rotated_file = log_file.with_suffix(f'.{timestamp}.jsonl')

        # Rename current file
        log_file.rename(rotated_file)

        # Compress if enabled
        if self.compress_logs:
            with open(rotated_file, 'rb') as f_in:
                with gzip.open(f"{rotated_file}.gz", 'wb') as f_out:
                    f_out.writelines(f_in)
            rotated_file.unlink()

    async def _stream_events(self, events: List[AuditEvent]):
        """Stream events to real-time consumers (SIEM)"""
        if not self.redis_client:
            return

        try:
            for event in events:
                # Publish to Redis stream
                await self.redis_client.xadd(
                    'audit:stream',
                    {
                        'event': json.dumps(asdict(event), default=str),
                        'signature': self._sign_event(event)
                    }
                )

                # Also publish to pub/sub for real-time alerts
                if event.severity in [AuditSeverity.ERROR, AuditSeverity.CRITICAL]:
                    await self.redis_client.publish(
                        f'audit:alerts:{event.severity.value}',
                        json.dumps(asdict(event), default=str)
                    )

        except Exception as e:
            logger.error(f"Failed to stream audit events: {e}")

    async def _alert_critical_event(self, event: AuditEvent):
        """Send immediate alert for critical events"""
        # In production, integrate with alerting system (PagerDuty, etc.)
        logger.critical(f"CRITICAL AUDIT EVENT: {event.event_type.value} - {event.action}")

        # Send to monitoring system
        if self.redis_client:
            await self.redis_client.publish(
                'audit:critical',
                json.dumps(asdict(event), default=str)
            )

    async def _update_statistics(self, events: List[AuditEvent]):
        """Update audit statistics"""
        if not self.db_pool:
            return

        try:
            # Group events by date
            from collections import defaultdict
            by_date = defaultdict(list)
            for event in events:
                date = event.timestamp.date()
                by_date[date].append(event)

            async with self.db_pool.acquire() as conn:
                for date, date_events in by_date.items():
                    # Calculate statistics
                    event_counts = {}
                    for event in date_events:
                        event_type = event.event_type.value
                        event_counts[event_type] = event_counts.get(event_type, 0) + 1

                    unique_actors = len(set(e.actor_id for e in date_events if e.actor_id))
                    total_events = len(date_events)
                    error_count = sum(1 for e in date_events if e.result == 'error')

                    response_times = [e.response_time_ms for e in date_events if e.response_time_ms]
                    avg_response_time = sum(response_times) / len(response_times) if response_times else None

                    # Upsert statistics
                    await conn.execute("""
                        INSERT INTO audit_statistics (
                            date, event_counts, unique_actors, total_events,
                            error_count, avg_response_time_ms
                        ) VALUES ($1, $2, $3, $4, $5, $6)
                        ON CONFLICT (date) DO UPDATE SET
                            event_counts = audit_statistics.event_counts || $2,
                            unique_actors = audit_statistics.unique_actors + $3,
                            total_events = audit_statistics.total_events + $4,
                            error_count = audit_statistics.error_count + $5,
                            avg_response_time_ms = COALESCE(
                                (audit_statistics.avg_response_time_ms * audit_statistics.total_events + $6 * $4) /
                                (audit_statistics.total_events + $4),
                                $6
                            ),
                            updated_at = NOW()
                    """, date, json.dumps(event_counts), unique_actors, total_events, error_count, avg_response_time)

        except Exception as e:
            logger.error(f"Failed to update audit statistics: {e}")

    async def _flush_buffer_task(self):
        """Background task to periodically flush buffer"""
        while True:
            await asyncio.sleep(self.flush_interval)
            await self._flush_buffer()

    async def query_events(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        event_types: Optional[List[AuditEventType]] = None,
        actor_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        severity: Optional[AuditSeverity] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Query audit events

        Returns:
            List of audit events matching criteria
        """
        if not self.db_pool:
            return []

        # Build query
        query = "SELECT * FROM audit_log WHERE 1=1"
        params = []

        if start_time:
            params.append(start_time)
            query += f" AND timestamp >= ${len(params)}"

        if end_time:
            params.append(end_time)
            query += f" AND timestamp <= ${len(params)}"

        if event_types:
            params.append([e.value for e in event_types])
            query += f" AND event_type = ANY(${len(params)})"

        if actor_id:
            params.append(actor_id)
            query += f" AND actor_id = ${len(params)}"

        if resource_type:
            params.append(resource_type)
            query += f" AND resource_type = ${len(params)}"

        if resource_id:
            params.append(resource_id)
            query += f" AND resource_id = ${len(params)}"

        if severity:
            params.append(severity.value)
            query += f" AND severity = ${len(params)}"

        query += f" ORDER BY timestamp DESC LIMIT {limit} OFFSET {offset}"

        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(query, *params)

        return [dict(row) for row in rows]

    async def generate_compliance_report(
        self,
        user_id: str,
        report_type: str = "gdpr"
    ) -> Dict[str, Any]:
        """
        Generate compliance report for user

        Args:
            user_id: User ID
            report_type: Type of report (gdpr, ccpa)

        Returns:
            Compliance report data
        """
        if report_type == "gdpr":
            # GDPR data access request
            events = await self.query_events(
                actor_id=user_id,
                limit=10000
            )

            return {
                "user_id": user_id,
                "report_type": "GDPR Data Access",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "total_events": len(events),
                "events": events,
                "data_categories": self._categorize_gdpr_data(events)
            }

        elif report_type == "ccpa":
            # CCPA data request
            events = await self.query_events(
                actor_id=user_id,
                limit=10000
            )

            return {
                "user_id": user_id,
                "report_type": "CCPA Consumer Request",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "total_events": len(events),
                "events": events,
                "data_categories": self._categorize_ccpa_data(events)
            }

        return {}

    def _categorize_gdpr_data(self, events: List[Dict]) -> Dict[str, List]:
        """Categorize data for GDPR report"""
        categories = {
            "personal_data": [],
            "activity_data": [],
            "consent_records": [],
            "data_processing": []
        }

        for event in events:
            event_type = event.get('event_type', '')
            if 'auth' in event_type:
                categories['personal_data'].append(event)
            elif 'api' in event_type:
                categories['activity_data'].append(event)
            elif 'consent' in event_type:
                categories['consent_records'].append(event)
            elif 'data' in event_type:
                categories['data_processing'].append(event)

        return categories

    def _categorize_ccpa_data(self, events: List[Dict]) -> Dict[str, List]:
        """Categorize data for CCPA report"""
        categories = {
            "personal_information": [],
            "commercial_information": [],
            "internet_activity": [],
            "inferences": []
        }

        for event in events:
            event_type = event.get('event_type', '')
            if 'auth' in event_type or 'user' in event_type:
                categories['personal_information'].append(event)
            elif 'payment' in event_type or 'order' in event_type:
                categories['commercial_information'].append(event)
            elif 'api' in event_type:
                categories['internet_activity'].append(event)

        return categories

    async def cleanup_old_logs(self):
        """Clean up logs older than retention period"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.retention_days)

        # Clean database
        if self.db_pool:
            async with self.db_pool.acquire() as conn:
                result = await conn.execute("""
                    DELETE FROM audit_log
                    WHERE timestamp < $1
                """, cutoff_date)
                logger.info(f"Deleted {result} old audit log entries")

        # Clean files
        for log_file in self.log_dir.glob("audit_*.jsonl*"):
            if log_file.stat().st_mtime < cutoff_date.timestamp():
                log_file.unlink()
                logger.info(f"Deleted old audit log file: {log_file}")


# FastAPI middleware for automatic audit logging
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import timedelta


class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to automatically log API requests"""

    def __init__(self, app, audit_logger: AuditLogger, excluded_paths: List[str] = None):
        super().__init__(app)
        self.audit_logger = audit_logger
        self.excluded_paths = excluded_paths or ['/health', '/metrics']

    async def dispatch(self, request: Request, call_next):
        """Process request and log audit event"""
        # Skip excluded paths
        if any(request.url.path.startswith(path) for path in self.excluded_paths):
            return await call_next(request)

        # Track timing
        start_time = time.time()

        # Process request
        response = await call_next(request)

        # Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)

        # Determine severity based on response code
        severity = AuditSeverity.INFO
        if response.status_code >= 500:
            severity = AuditSeverity.ERROR
        elif response.status_code >= 400:
            severity = AuditSeverity.WARNING

        # Log audit event
        await self.audit_logger.log_event(
            event_type=AuditEventType.API_REQUEST,
            action=f"{request.method} {request.url.path}",
            result="success" if response.status_code < 400 else "failure",
            severity=severity,
            request=request,
            response=response,
            response_time_ms=response_time_ms
        )

        return response


# Global instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get global audit logger instance"""
    global _audit_logger
    if _audit_logger is None:
        from core.config_loader import get_config
        config = get_config()
        _audit_logger = AuditLogger(config.get_security_config())
    return _audit_logger


# Background task for cleanup
async def audit_cleanup_task():
    """Background task to clean up old audit logs"""
    logger = get_audit_logger()
    while True:
        try:
            await logger.cleanup_old_logs()
            await asyncio.sleep(86400)  # Run daily
        except Exception as e:
            logger.error(f"Audit cleanup error: {e}")
            await asyncio.sleep(3600)  # Retry in an hour