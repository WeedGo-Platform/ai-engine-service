"""
Scraping Strategy Selector - Domain Service

Responsible for selecting the optimal scraping strategy based on:
- Known site characteristics
- URL patterns
- Previous scraping history
- Performance requirements
"""

import logging
from typing import Dict, Set
from urllib.parse import urlparse
from ..strategies.base import AbstractScrapingStrategy
from ..strategies.static_strategy import StaticScrapingStrategy
from ..strategies.dynamic_strategy import DynamicScrapingStrategy
from ..strategies.hybrid_strategy import HybridScrapingStrategy
from ..domain.value_objects import BrowserConfig, ScrapingOptions

logger = logging.getLogger(__name__)


class ScrapingStrategySelector:
    """
    Domain Service: Selects optimal scraping strategy

    This service encapsulates the business logic for strategy selection.
    It knows WHEN to use each strategy, but delegates HOW to the strategies themselves.
    """

    # Sites known to require browser automation (JavaScript-heavy)
    KNOWN_DYNAMIC_SITES: Set[str] = {
        'onewholesale.ca',
        'shopify.com',
        'squarespace.com',
        'wix.com',
        'webflow.com',
        'weebly.com',
        # Add more as discovered through usage
    }

    # Sites known to work well with static scraping
    KNOWN_STATIC_SITES: Set[str] = {
        'upcitemdb.com',
        'barcodelookup.com',
        'ean-search.org',
        'wikipedia.org',
        # Traditional server-rendered sites
    }

    def __init__(self, browser_config: BrowserConfig | None = None):
        """
        Initialize strategy selector

        Args:
            browser_config: Configuration for browser-based strategies
        """
        self.browser_config = browser_config or BrowserConfig()
        self._strategy_cache: Dict[str, str] = {}  # domain -> strategy_name

    def select(
        self,
        url: str,
        options: ScrapingOptions
    ) -> AbstractScrapingStrategy:
        """
        Select the optimal scraping strategy for a URL

        Decision tree:
        1. If user specified strategy → use that
        2. If URL in known dynamic sites → use dynamic or hybrid
        3. If URL in known static sites → use static
        4. Otherwise → use hybrid (smart fallback)

        Args:
            url: URL to scrape
            options: Scraping options (may specify strategy)

        Returns:
            Strategy instance to use
        """
        # Check if user specified strategy
        if options.strategy and options.strategy != 'auto':
            return self._create_strategy(options.strategy)

        # Extract domain from URL
        domain = self._extract_domain(url)

        # Check cache (learn from previous scrapes)
        if domain in self._strategy_cache:
            cached_strategy = self._strategy_cache[domain]
            logger.debug(f"Using cached strategy '{cached_strategy}' for {domain}")
            return self._create_strategy(cached_strategy)

        # Check known dynamic sites
        if self._is_known_dynamic_site(domain):
            logger.info(f"Known dynamic site detected: {domain}")
            # Use hybrid instead of pure dynamic for better performance
            # (hybrid will try static first, fallback to dynamic)
            return HybridScrapingStrategy(self.browser_config)

        # Check known static sites
        if self._is_known_static_site(domain):
            logger.info(f"Known static site detected: {domain}")
            return StaticScrapingStrategy()

        # Default: Use hybrid strategy (intelligent fallback)
        logger.info(f"Unknown site, using hybrid strategy: {domain}")
        return HybridScrapingStrategy(self.browser_config)

    def learn_from_result(
        self,
        url: str,
        strategy_used: str,
        success: bool
    ) -> None:
        """
        Learn from scraping result to improve future selections

        If hybrid strategy ended up using dynamic, remember that
        this site needs browser automation.

        Args:
            url: URL that was scraped
            strategy_used: Strategy that was actually used
            success: Whether scraping was successful
        """
        if not success:
            return  # Don't learn from failures

        domain = self._extract_domain(url)

        # If hybrid used dynamic, cache as dynamic site
        if strategy_used == 'hybrid':
            # Hybrid internally uses either static or dynamic
            # We'd need to track which one was actually used
            # For now, just cache as hybrid
            self._strategy_cache[domain] = 'hybrid'
            logger.debug(f"Learned: {domain} works with hybrid strategy")

    def _create_strategy(self, strategy_name: str) -> AbstractScrapingStrategy:
        """
        Factory method to create strategy instances

        Args:
            strategy_name: Name of strategy ('static', 'dynamic', 'hybrid')

        Returns:
            Strategy instance
        """
        strategies = {
            'static': lambda: StaticScrapingStrategy(),
            'dynamic': lambda: DynamicScrapingStrategy(self.browser_config),
            'hybrid': lambda: HybridScrapingStrategy(self.browser_config),
        }

        factory = strategies.get(strategy_name)
        if not factory:
            logger.warning(f"Unknown strategy '{strategy_name}', defaulting to hybrid")
            return HybridScrapingStrategy(self.browser_config)

        return factory()

    def _extract_domain(self, url: str) -> str:
        """
        Extract domain from URL

        Args:
            url: Full URL

        Returns:
            Domain (e.g., 'onewholesale.ca')
        """
        try:
            parsed = urlparse(url)
            # Remove 'www.' prefix if present
            domain = parsed.netloc.lower()
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except Exception:
            return ''

    def _is_known_dynamic_site(self, domain: str) -> bool:
        """
        Check if domain is known to require browser automation

        Args:
            domain: Domain to check

        Returns:
            True if site is known to be JavaScript-heavy
        """
        # Check exact match
        if domain in self.KNOWN_DYNAMIC_SITES:
            return True

        # Check if domain ends with known dynamic platform
        # (e.g., 'mystore.shopify.com' contains 'shopify.com')
        return any(
            known_site in domain
            for known_site in self.KNOWN_DYNAMIC_SITES
        )

    def _is_known_static_site(self, domain: str) -> bool:
        """
        Check if domain is known to work with static scraping

        Args:
            domain: Domain to check

        Returns:
            True if site is known to be server-rendered
        """
        return domain in self.KNOWN_STATIC_SITES

    def add_dynamic_site(self, domain: str) -> None:
        """
        Add a site to the known dynamic sites list

        Use this when you discover a site requires browser automation.

        Args:
            domain: Domain to add (e.g., 'example.com')
        """
        self.KNOWN_DYNAMIC_SITES.add(domain.lower())
        logger.info(f"Added {domain} to known dynamic sites")

    def add_static_site(self, domain: str) -> None:
        """
        Add a site to the known static sites list

        Args:
            domain: Domain to add
        """
        self.KNOWN_STATIC_SITES.add(domain.lower())
        logger.info(f"Added {domain} to known static sites")
