"""
Value Objects for Browser Automation Domain

Value Objects are immutable and compared by value, not identity.
They represent concepts in the domain that have no identity.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass(frozen=True)
class BrowserConfig:
    """
    Browser configuration settings

    Immutable configuration for browser instances.
    All scrapers using the same config will get consistent behavior.
    """
    headless: bool = True
    timeout: int = 30000  # milliseconds
    viewport_width: int = 1920
    viewport_height: int = 1080
    user_agent: Optional[str] = None
    ignore_https_errors: bool = True

    def __post_init__(self):
        """Validate configuration"""
        if self.timeout < 1000:
            raise ValueError("Timeout must be at least 1000ms")
        if self.viewport_width < 320 or self.viewport_height < 240:
            raise ValueError("Viewport dimensions too small")


@dataclass(frozen=True)
class SelectorSet:
    """
    Set of CSS selectors for extracting data

    Each field contains a list of selectors to try in order.
    First matching selector wins (fallback pattern).

    Example:
        selectors = SelectorSet(
            product_name=['h1.title', 'h2.product-name', '.name'],
            product_price=['span.price', '.cost', '[data-price]']
        )
    """
    product_name: List[str] = field(default_factory=list)
    product_price: List[str] = field(default_factory=list)
    product_image: List[str] = field(default_factory=list)
    product_brand: Optional[List[str]] = None
    product_sku: Optional[List[str]] = None
    product_description: Optional[List[str]] = None

    # Custom selectors (extensible)
    custom: Optional[Dict[str, List[str]]] = None

    def __post_init__(self):
        """Validate at least one selector provided"""
        has_selectors = (
            self.product_name or
            self.product_price or
            self.product_image or
            self.custom
        )
        if not has_selectors:
            raise ValueError("SelectorSet must have at least one selector")


@dataclass(frozen=True)
class ScrapingOptions:
    """
    Options for a single scraping operation

    Configures behavior for a specific scrape request.
    Immutable to ensure thread-safety and predictability.
    """
    # Strategy selection
    strategy: Optional[str] = 'auto'  # 'static', 'dynamic', 'auto'

    # Waiting behavior
    wait_for_selector: Optional[str] = None
    wait_for_timeout: int = 5000  # milliseconds
    wait_for_network_idle: bool = False

    # Extraction options
    extract_json_ld: bool = True  # Extract JSON-LD structured data
    extract_meta_tags: bool = True  # Extract meta tags

    # Performance options
    enable_cache: bool = True
    cache_ttl: Optional[int] = None  # seconds, None = use default

    # Debugging options
    take_screenshot: bool = False
    screenshot_path: Optional[str] = None

    # Retry configuration
    max_retries: int = 3
    retry_delay: int = 1000  # milliseconds

    def __post_init__(self):
        """Validate options"""
        valid_strategies = ['static', 'dynamic', 'auto', None]
        if self.strategy not in valid_strategies:
            raise ValueError(f"Invalid strategy: {self.strategy}. Must be one of {valid_strategies}")

        if self.wait_for_timeout < 0:
            raise ValueError("wait_for_timeout must be non-negative")


@dataclass(frozen=True)
class ScrapeRequest:
    """
    Complete scraping request

    Encapsulates all information needed for a scraping operation.
    """
    url: str
    selectors: SelectorSet
    options: ScrapingOptions = field(default_factory=ScrapingOptions)

    def __post_init__(self):
        """Validate URL"""
        if not self.url or not self.url.startswith(('http://', 'https://')):
            raise ValueError(f"Invalid URL: {self.url}")
