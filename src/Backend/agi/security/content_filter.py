"""
Content Filtering and Safety Module for AGI System
Ensures safe and responsible AI operations
"""

import re
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple
from enum import Enum
import hashlib
import json

from agi.core.database import get_db_manager
from agi.config.agi_config import get_config

logger = logging.getLogger(__name__)


class ContentCategory(Enum):
    """Categories of potentially harmful content"""
    VIOLENCE = "violence"
    HATE_SPEECH = "hate_speech"
    HARASSMENT = "harassment"
    SELF_HARM = "self_harm"
    SEXUAL = "sexual"
    ILLEGAL = "illegal"
    PII = "personal_information"
    MISINFORMATION = "misinformation"
    SPAM = "spam"
    MALICIOUS_CODE = "malicious_code"


class FilterAction(Enum):
    """Actions to take on filtered content"""
    ALLOW = "allow"
    BLOCK = "block"
    WARN = "warn"
    REDACT = "redact"
    REVIEW = "review"


class Severity(Enum):
    """Severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class FilterResult:
    """Result of content filtering"""
    safe: bool
    action: FilterAction
    categories_detected: List[ContentCategory]
    severity: Severity
    confidence: float
    redacted_content: Optional[str]
    warnings: List[str]
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'safe': self.safe,
            'action': self.action.value,
            'categories_detected': [c.value for c in self.categories_detected],
            'severity': self.severity.value,
            'confidence': self.confidence,
            'redacted_content': self.redacted_content,
            'warnings': self.warnings,
            'metadata': self.metadata
        }


class ContentFilter:
    """
    Filters and moderates content for safety
    """

    def __init__(self):
        """Initialize content filter"""
        self.config = get_config()
        self.db_manager = None

        # Pattern-based filters
        self._harmful_patterns: Dict[ContentCategory, List[re.Pattern]] = {}
        self._pii_patterns: List[re.Pattern] = []
        self._code_patterns: List[re.Pattern] = []

        # Whitelists and blacklists
        self._whitelist: Set[str] = set()
        self._blacklist: Set[str] = set()

        # Filter thresholds
        self._thresholds = {
            Severity.LOW: 0.3,
            Severity.MEDIUM: 0.5,
            Severity.HIGH: 0.7,
            Severity.CRITICAL: 0.9
        }

        self._initialize_patterns()

    def _initialize_patterns(self):
        """Initialize detection patterns"""
        # Violence patterns
        self._harmful_patterns[ContentCategory.VIOLENCE] = [
            re.compile(r'\b(kill|murder|assault|attack|hurt|harm|injure)\b', re.IGNORECASE),
            re.compile(r'\b(weapon|gun|knife|bomb|explosive)\b', re.IGNORECASE)
        ]

        # Hate speech patterns
        self._harmful_patterns[ContentCategory.HATE_SPEECH] = [
            re.compile(r'\b(hate|discriminat\w+|racist|sexist|bigot\w+)\b', re.IGNORECASE)
        ]

        # Harassment patterns
        self._harmful_patterns[ContentCategory.HARASSMENT] = [
            re.compile(r'\b(threaten|intimidat\w+|bully|harass)\b', re.IGNORECASE)
        ]

        # Self-harm patterns
        self._harmful_patterns[ContentCategory.SELF_HARM] = [
            re.compile(r'\b(suicide|self[\s-]?harm|cut[\s-]?myself)\b', re.IGNORECASE)
        ]

        # Illegal activity patterns
        self._harmful_patterns[ContentCategory.ILLEGAL] = [
            re.compile(r'\b(illegal|crime|fraud|steal|hack(?:ing)?)\b', re.IGNORECASE),
            re.compile(r'\b(drug[s]?|narcotic|controlled[\s-]?substance)\b', re.IGNORECASE)
        ]

        # PII patterns
        self._pii_patterns = [
            re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),  # SSN
            re.compile(r'\b(?:\d{4}[\s-]?){3}\d{4}\b'),  # Credit card
            re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),  # Email
            re.compile(r'\b(?:\+?1[\s-]?)?\(?[0-9]{3}\)?[\s-]?[0-9]{3}[\s-]?[0-9]{4}\b'),  # Phone
            re.compile(r'\b\d{1,5}\s+[\w\s]+(?:street|st|avenue|ave|road|rd|highway|hwy|lane|ln)\b', re.IGNORECASE)  # Address
        ]

        # Malicious code patterns
        self._code_patterns = [
            re.compile(r'<script[^>]*>.*?</script>', re.IGNORECASE | re.DOTALL),
            re.compile(r'javascript:', re.IGNORECASE),
            re.compile(r'on\w+\s*=\s*["\'].*?["\']', re.IGNORECASE),  # Event handlers
            re.compile(r'eval\s*\(.*?\)', re.IGNORECASE),
            re.compile(r'exec\s*\(.*?\)', re.IGNORECASE)
        ]

    async def initialize(self):
        """Initialize the content filter"""
        self.db_manager = await get_db_manager()
        await self._create_tables()
        await self._load_lists()

        logger.info("Content filter initialized")

    async def _create_tables(self):
        """Create necessary database tables"""
        conn = await self.db_manager.get_connection()
        try:
            # Filtered content log
            query = """
            CREATE TABLE IF NOT EXISTS agi.content_filter_log (
                id SERIAL PRIMARY KEY,
                session_id VARCHAR(255),
                content_hash VARCHAR(64),
                action VARCHAR(20) NOT NULL,
                categories JSONB,
                severity VARCHAR(20),
                confidence FLOAT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            await conn.execute(query)

            # Whitelist/blacklist
            query = """
            CREATE TABLE IF NOT EXISTS agi.content_lists (
                id SERIAL PRIMARY KEY,
                list_type VARCHAR(20) NOT NULL,
                pattern VARCHAR(500) NOT NULL,
                category VARCHAR(50),
                reason TEXT,
                added_by VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(list_type, pattern)
            )
            """
            await conn.execute(query)

            # Create indexes
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_filter_log_session ON agi.content_filter_log (session_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_filter_log_action ON agi.content_filter_log (action)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_content_lists_type ON agi.content_lists (list_type)")
        finally:
            await self.db_manager.release_connection(conn)

    async def _load_lists(self):
        """Load whitelist and blacklist from database"""
        conn = await self.db_manager.get_connection()
        try:
            # Load whitelist
            rows = await conn.fetch("SELECT pattern FROM agi.content_lists WHERE list_type = 'whitelist'")
            self._whitelist = {row['pattern'] for row in rows}

            # Load blacklist
            rows = await conn.fetch("SELECT pattern FROM agi.content_lists WHERE list_type = 'blacklist'")
            self._blacklist = {row['pattern'] for row in rows}

            logger.info(f"Loaded {len(self._whitelist)} whitelist and {len(self._blacklist)} blacklist patterns")
        finally:
            await self.db_manager.release_connection(conn)

    async def filter_content(
        self,
        content: str,
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> FilterResult:
        """Filter content for safety"""
        # Check whitelist first
        if self._is_whitelisted(content):
            return FilterResult(
                safe=True,
                action=FilterAction.ALLOW,
                categories_detected=[],
                severity=Severity.LOW,
                confidence=1.0,
                redacted_content=None,
                warnings=[],
                metadata={'whitelisted': True}
            )

        # Check blacklist
        if self._is_blacklisted(content):
            await self._log_filter_action(
                session_id, content, FilterAction.BLOCK,
                [ContentCategory.ILLEGAL], Severity.CRITICAL, 1.0
            )
            return FilterResult(
                safe=False,
                action=FilterAction.BLOCK,
                categories_detected=[ContentCategory.ILLEGAL],
                severity=Severity.CRITICAL,
                confidence=1.0,
                redacted_content="[BLOCKED CONTENT]",
                warnings=["Content matches blacklist"],
                metadata={'blacklisted': True}
            )

        # Detect harmful content
        detected_categories = []
        confidence_scores = []

        for category, patterns in self._harmful_patterns.items():
            score = self._check_patterns(content, patterns)
            if score > 0:
                detected_categories.append(category)
                confidence_scores.append(score)

        # Check for PII
        pii_detected = self._detect_pii(content)
        if pii_detected:
            detected_categories.append(ContentCategory.PII)
            confidence_scores.append(0.9)

        # Check for malicious code
        if self._detect_malicious_code(content):
            detected_categories.append(ContentCategory.MALICIOUS_CODE)
            confidence_scores.append(0.95)

        # Determine overall severity and action
        if not detected_categories:
            return FilterResult(
                safe=True,
                action=FilterAction.ALLOW,
                categories_detected=[],
                severity=Severity.LOW,
                confidence=1.0,
                redacted_content=None,
                warnings=[],
                metadata={}
            )

        # Calculate overall confidence and severity
        avg_confidence = sum(confidence_scores) / len(confidence_scores)
        severity = self._determine_severity(detected_categories, avg_confidence)
        action = self._determine_action(severity, detected_categories)

        # Redact content if needed
        redacted = None
        if action in [FilterAction.REDACT, FilterAction.BLOCK]:
            redacted = self._redact_content(content, detected_categories)

        # Generate warnings
        warnings = self._generate_warnings(detected_categories, severity)

        # Log the action
        await self._log_filter_action(
            session_id, content, action,
            detected_categories, severity, avg_confidence
        )

        return FilterResult(
            safe=action != FilterAction.BLOCK,
            action=action,
            categories_detected=detected_categories,
            severity=severity,
            confidence=avg_confidence,
            redacted_content=redacted,
            warnings=warnings,
            metadata={
                'patterns_matched': len(detected_categories),
                'context': context
            }
        )

    def _is_whitelisted(self, content: str) -> bool:
        """Check if content matches whitelist"""
        content_lower = content.lower()
        return any(pattern in content_lower for pattern in self._whitelist)

    def _is_blacklisted(self, content: str) -> bool:
        """Check if content matches blacklist"""
        content_lower = content.lower()
        return any(pattern in content_lower for pattern in self._blacklist)

    def _check_patterns(self, content: str, patterns: List[re.Pattern]) -> float:
        """Check content against patterns and return confidence score"""
        matches = 0
        for pattern in patterns:
            if pattern.search(content):
                matches += 1

        if matches == 0:
            return 0.0

        # Calculate confidence based on number of matches
        return min(matches * 0.3, 1.0)

    def _detect_pii(self, content: str) -> bool:
        """Detect personally identifiable information"""
        for pattern in self._pii_patterns:
            if pattern.search(content):
                return True
        return False

    def _detect_malicious_code(self, content: str) -> bool:
        """Detect potential malicious code"""
        for pattern in self._code_patterns:
            if pattern.search(content):
                return True
        return False

    def _determine_severity(
        self,
        categories: List[ContentCategory],
        confidence: float
    ) -> Severity:
        """Determine severity based on categories and confidence"""
        # Critical categories
        critical_categories = {
            ContentCategory.VIOLENCE,
            ContentCategory.SELF_HARM,
            ContentCategory.MALICIOUS_CODE,
            ContentCategory.ILLEGAL
        }

        if any(cat in critical_categories for cat in categories):
            if confidence > self._thresholds[Severity.HIGH]:
                return Severity.CRITICAL
            return Severity.HIGH

        # High severity categories
        high_categories = {
            ContentCategory.HATE_SPEECH,
            ContentCategory.HARASSMENT,
            ContentCategory.PII
        }

        if any(cat in high_categories for cat in categories):
            if confidence > self._thresholds[Severity.MEDIUM]:
                return Severity.HIGH
            return Severity.MEDIUM

        # Default to medium or low
        if confidence > self._thresholds[Severity.MEDIUM]:
            return Severity.MEDIUM
        return Severity.LOW

    def _determine_action(
        self,
        severity: Severity,
        categories: List[ContentCategory]
    ) -> FilterAction:
        """Determine action based on severity and categories"""
        if severity == Severity.CRITICAL:
            return FilterAction.BLOCK

        if severity == Severity.HIGH:
            if ContentCategory.PII in categories:
                return FilterAction.REDACT
            return FilterAction.REVIEW

        if severity == Severity.MEDIUM:
            return FilterAction.WARN

        return FilterAction.ALLOW

    def _redact_content(
        self,
        content: str,
        categories: List[ContentCategory]
    ) -> str:
        """Redact sensitive parts of content"""
        redacted = content

        # Redact PII
        if ContentCategory.PII in categories:
            for pattern in self._pii_patterns:
                redacted = pattern.sub("[REDACTED]", redacted)

        # Redact malicious code
        if ContentCategory.MALICIOUS_CODE in categories:
            for pattern in self._code_patterns:
                redacted = pattern.sub("[CODE REMOVED]", redacted)

        # Redact harmful content
        for category in categories:
            if category in self._harmful_patterns:
                for pattern in self._harmful_patterns[category]:
                    redacted = pattern.sub("[***]", redacted)

        return redacted

    def _generate_warnings(
        self,
        categories: List[ContentCategory],
        severity: Severity
    ) -> List[str]:
        """Generate appropriate warnings"""
        warnings = []

        if ContentCategory.PII in categories:
            warnings.append("Personal information detected and should be protected")

        if ContentCategory.MALICIOUS_CODE in categories:
            warnings.append("Potentially malicious code detected")

        if ContentCategory.VIOLENCE in categories:
            warnings.append("Content contains references to violence")

        if ContentCategory.HATE_SPEECH in categories:
            warnings.append("Content may contain hate speech")

        if severity in [Severity.HIGH, Severity.CRITICAL]:
            warnings.append(f"Content flagged as {severity.value} risk")

        return warnings

    async def _log_filter_action(
        self,
        session_id: Optional[str],
        content: str,
        action: FilterAction,
        categories: List[ContentCategory],
        severity: Severity,
        confidence: float
    ):
        """Log filter action to database"""
        conn = await self.db_manager.get_connection()
        try:
            # Hash content for privacy
            content_hash = hashlib.sha256(content.encode()).hexdigest()

            await conn.execute(
                """
                INSERT INTO agi.content_filter_log
                (session_id, content_hash, action, categories, severity, confidence)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                session_id,
                content_hash,
                action.value,
                json.dumps([c.value for c in categories]),
                severity.value,
                confidence
            )
        except Exception as e:
            logger.error(f"Failed to log filter action: {e}")
        finally:
            await self.db_manager.release_connection(conn)

    async def add_to_whitelist(
        self,
        pattern: str,
        reason: Optional[str] = None,
        added_by: Optional[str] = None
    ):
        """Add pattern to whitelist"""
        conn = await self.db_manager.get_connection()
        try:
            await conn.execute(
                """
                INSERT INTO agi.content_lists (list_type, pattern, reason, added_by)
                VALUES ('whitelist', $1, $2, $3)
                ON CONFLICT (list_type, pattern) DO NOTHING
                """,
                pattern, reason, added_by
            )
            self._whitelist.add(pattern)
            logger.info(f"Added '{pattern}' to whitelist")
        finally:
            await self.db_manager.release_connection(conn)

    async def add_to_blacklist(
        self,
        pattern: str,
        category: Optional[ContentCategory] = None,
        reason: Optional[str] = None,
        added_by: Optional[str] = None
    ):
        """Add pattern to blacklist"""
        conn = await self.db_manager.get_connection()
        try:
            await conn.execute(
                """
                INSERT INTO agi.content_lists
                (list_type, pattern, category, reason, added_by)
                VALUES ('blacklist', $1, $2, $3, $4)
                ON CONFLICT (list_type, pattern) DO NOTHING
                """,
                pattern,
                category.value if category else None,
                reason,
                added_by
            )
            self._blacklist.add(pattern)
            logger.info(f"Added '{pattern}' to blacklist")
        finally:
            await self.db_manager.release_connection(conn)

    async def get_filter_stats(
        self,
        time_window_hours: int = 24
    ) -> Dict[str, Any]:
        """Get filtering statistics"""
        conn = await self.db_manager.get_connection()
        try:
            query = """
            SELECT
                action,
                severity,
                COUNT(*) as count,
                AVG(confidence) as avg_confidence
            FROM agi.content_filter_log
            WHERE timestamp > NOW() - INTERVAL '%s hours'
            GROUP BY action, severity
            """

            rows = await conn.fetch(query, time_window_hours)

            stats = {
                'time_window_hours': time_window_hours,
                'actions': {},
                'severities': {},
                'total_filtered': 0
            }

            for row in rows:
                action = row['action']
                severity = row['severity']
                count = row['count']

                if action not in stats['actions']:
                    stats['actions'][action] = 0
                stats['actions'][action] += count

                if severity not in stats['severities']:
                    stats['severities'][severity] = 0
                stats['severities'][severity] += count

                stats['total_filtered'] += count

            return stats
        finally:
            await self.db_manager.release_connection(conn)

    async def cleanup(self):
        """Clean up resources"""
        logger.info("Content filter cleaned up")


# Singleton instance
_content_filter: Optional[ContentFilter] = None

async def get_content_filter() -> ContentFilter:
    """Get singleton content filter instance"""
    global _content_filter
    if _content_filter is None:
        _content_filter = ContentFilter()
        await _content_filter.initialize()
    return _content_filter