"""
Browser Automation Service - Main Domain Service

Orchestrates web scraping operations using intelligent strategy selection.
This is the main entry point for all scraping operations.
"""

import logging
from typing import Optional, Dict, Any
from ..domain.entities import ScrapingResult
from ..domain.value_objects import BrowserConfig, SelectorSet, ScrapingOptions
from .strategy_selector import ScrapingStrategySelector

logger = logging.getLogger(__name__)


class BrowserAutomationService:
    """
    Main domain service for browser automation

    Responsibilities:
    - Strategy selection and execution
    - Result caching (optional)
    - Error handling and retries
    - Performance monitoring

    Does NOT:
    - Know about specific sites (that's scrapers' job)
    - Contain business logic (that's application layer)
    - Parse domain-specific data (that's scrapers' job)

    Usage:
        service = BrowserAutomationService()
        result = await service.scrape(url, selectors, options)
    """

    def __init__(
        self,
        browser_config: Optional[BrowserConfig] = None,
        strategy_selector: Optional[ScrapingStrategySelector] = None,
        cache: Optional[Any] = None  # Simple dict cache for now
    ):
        """
        Initialize browser automation service

        Args:
            browser_config: Browser configuration
            strategy_selector: Strategy selector (will create default if not provided)
            cache: Optional cache for results
        """
        self.browser_config = browser_config or BrowserConfig()
        self.strategy_selector = strategy_selector or ScrapingStrategySelector(self.browser_config)
        self.cache = cache or {}  # Simple in-memory cache

        # Metrics
        self.total_requests = 0
        self.cache_hits = 0
        self.strategy_usage: Dict[str, int] = {}

    async def scrape(
        self,
        url: str,
        selectors: SelectorSet,
        options: Optional[ScrapingOptions] = None
    ) -> ScrapingResult:
        """
        Scrape a URL using the optimal strategy

        This is the main entry point for scraping operations.

        Algorithm:
        1. Check cache (if enabled)
        2. Select appropriate strategy
        3. Execute scraping
        4. Cache result (if successful and caching enabled)
        5. Learn from result for future optimizations
        6. Return standardized result

        Args:
            url: URL to scrape
            selectors: CSS selectors for data extraction
            options: Scraping options (optional, sensible defaults)

        Returns:
            ScrapingResult with extracted data and metadata

        Example:
            >>> service = BrowserAutomationService()
            >>> selectors = SelectorSet(
            ...     product_name=['h1.title', '.product-name'],
            ...     product_price=['span.price', '.cost']
            ... )
            >>> result = await service.scrape(
            ...     'https://example.com/product/123',
            ...     selectors
            ... )
            >>> print(result.data['name'])
        """
        self.total_requests += 1
        options = options or ScrapingOptions()

        # Step 1: Check cache
        if options.enable_cache:
            cached_result = self._get_from_cache(url)
            if cached_result:
                logger.info(f"Cache hit for {url}")
                self.cache_hits += 1
                return cached_result

        # Step 2: Select strategy
        strategy = self.strategy_selector.select(url, options)
        logger.info(f"Selected strategy: {strategy.get_name()} for {url}")

        # Step 3: Execute scraping with retry logic
        result = await self._execute_with_retry(
            strategy,
            url,
            selectors,
            options
        )

        # Step 4: Update metrics
        self._update_metrics(strategy.get_name())

        # Step 5: Cache result if successful
        if result.is_successful() and options.enable_cache:
            self._add_to_cache(url, result, options)

        # Step 6: Learn from result
        self.strategy_selector.learn_from_result(
            url,
            result.strategy_used,
            result.is_successful()
        )

        return result

    async def _execute_with_retry(
        self,
        strategy,
        url: str,
        selectors: SelectorSet,
        options: ScrapingOptions
    ) -> ScrapingResult:
        """
        Execute scraping with retry logic

        Args:
            strategy: Strategy to use
            url: URL to scrape
            selectors: Selectors for extraction
            options: Scraping options (includes max_retries)

        Returns:
            ScrapingResult
        """
        last_error = None

        for attempt in range(options.max_retries):
            try:
                result = await strategy.scrape(url, selectors, options)

                # If successful, return immediately
                if result.is_successful():
                    if attempt > 0:
                        logger.info(f"Scraping succeeded on attempt {attempt + 1}")
                    return result

                # If not successful but no error, don't retry (legitimate not found)
                if not result.error:
                    return result

                last_error = result.error

            except Exception as e:
                last_error = str(e)
                logger.warning(f"Scraping attempt {attempt + 1} failed: {e}")

                # Wait before retry (exponential backoff)
                if attempt < options.max_retries - 1:
                    import asyncio
                    wait_time = options.retry_delay * (2 ** attempt) / 1000  # Convert ms to seconds
                    await asyncio.sleep(wait_time)

        # All retries failed
        logger.error(f"Scraping failed after {options.max_retries} attempts for {url}")
        return ScrapingResult(
            url=url,
            found=False,
            data={},
            strategy_used=strategy.get_name(),
            latency_ms=0,
            error=f"Failed after {options.max_retries} attempts: {last_error}"
        )

    def _get_from_cache(self, url: str) -> Optional[ScrapingResult]:
        """Get result from cache"""
        return self.cache.get(url)

    def _add_to_cache(
        self,
        url: str,
        result: ScrapingResult,
        options: ScrapingOptions
    ) -> None:
        """Add result to cache"""
        # Simple in-memory cache (production would use Redis)
        self.cache[url] = result
        logger.debug(f"Cached result for {url}")

        # TODO: Implement TTL-based cache eviction
        # For now, cache grows indefinitely (acceptable for prototype)

    def _update_metrics(self, strategy_name: str) -> None:
        """Update usage metrics"""
        if strategy_name not in self.strategy_usage:
            self.strategy_usage[strategy_name] = 0
        self.strategy_usage[strategy_name] += 1

    def get_stats(self) -> Dict[str, Any]:
        """
        Get service statistics

        Returns:
            Dictionary with metrics:
            - total_requests
            - cache_hit_rate
            - strategy_distribution
        """
        cache_hit_rate = (
            self.cache_hits / self.total_requests
            if self.total_requests > 0
            else 0.0
        )

        return {
            'total_requests': self.total_requests,
            'cache_hits': self.cache_hits,
            'cache_hit_rate': cache_hit_rate,
            'strategy_usage': self.strategy_usage,
            'known_dynamic_sites': list(self.strategy_selector.KNOWN_DYNAMIC_SITES),
            'known_static_sites': list(self.strategy_selector.KNOWN_STATIC_SITES),
        }

    def clear_cache(self) -> None:
        """Clear the result cache"""
        self.cache.clear()
        logger.info("Cache cleared")

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        # Could implement cleanup here (e.g., close browser pools)
        pass
