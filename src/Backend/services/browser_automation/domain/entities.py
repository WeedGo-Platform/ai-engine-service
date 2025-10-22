"""
Entities for Browser Automation Domain

Entities have identity and lifecycle. They are compared by ID, not by value.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from datetime import datetime
import hashlib


@dataclass
class ScrapingResult:
    """
    Result of a scraping operation

    Entity with identity (url + timestamp).
    Mutable because we may enrich it after creation (e.g., add metadata).
    """
    url: str
    found: bool
    data: Dict[str, Any]
    strategy_used: str
    latency_ms: float

    # Optional metadata
    timestamp: datetime = field(default_factory=datetime.utcnow)
    screenshot_path: Optional[str] = None
    error: Optional[str] = None
    html_snapshot: Optional[str] = None

    # Performance metrics
    network_requests: int = 0
    bytes_downloaded: int = 0

    def __post_init__(self):
        """Generate unique ID for this scraping result"""
        self._id = self._generate_id()

    def _generate_id(self) -> str:
        """Generate unique ID from URL + timestamp"""
        key = f"{self.url}_{self.timestamp.isoformat()}"
        return hashlib.md5(key.encode()).hexdigest()

    @property
    def id(self) -> str:
        """Unique identifier for this result"""
        return self._id

    def is_successful(self) -> bool:
        """Check if scraping was successful"""
        return self.found and not self.error and bool(self.data)

    def get_confidence(self) -> float:
        """
        Calculate confidence score for this result

        Confidence based on:
        - Strategy used (dynamic > static)
        - Data completeness
        - Source reliability
        """
        if not self.found:
            return 0.0

        base_confidence = {
            'cached': 1.0,  # Cached results are verified
            'dynamic': 0.85,  # Browser automation is thorough
            'static': 0.70,  # Static scraping may miss JS-rendered content
        }.get(self.strategy_used, 0.5)

        # Boost confidence if we have rich data
        data_boost = 0.0
        if self.data:
            field_count = len([v for v in self.data.values() if v])
            if field_count >= 4:  # name, price, image, brand
                data_boost = 0.10
            elif field_count >= 2:
                data_boost = 0.05

        return min(base_confidence + data_boost, 1.0)

    def add_metadata(self, key: str, value: Any) -> None:
        """Add custom metadata to result"""
        if 'metadata' not in self.data:
            self.data['metadata'] = {}
        self.data['metadata'][key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get custom metadata from result"""
        return self.data.get('metadata', {}).get(key, default)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for serialization"""
        return {
            'id': self.id,
            'url': self.url,
            'found': self.found,
            'data': self.data,
            'strategy_used': self.strategy_used,
            'latency_ms': self.latency_ms,
            'timestamp': self.timestamp.isoformat(),
            'confidence': self.get_confidence(),
            'screenshot_path': self.screenshot_path,
            'error': self.error,
            'network_requests': self.network_requests,
            'bytes_downloaded': self.bytes_downloaded,
        }

    def __repr__(self) -> str:
        status = "✓" if self.is_successful() else "✗"
        return (
            f"ScrapingResult({status} {self.url}, "
            f"strategy={self.strategy_used}, "
            f"latency={self.latency_ms:.0f}ms, "
            f"confidence={self.get_confidence():.2f})"
        )
