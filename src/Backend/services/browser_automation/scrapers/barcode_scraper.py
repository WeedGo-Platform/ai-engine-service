"""
Barcode Product Scraper - Application Service

Application-level scraper that knows WHAT to scrape for barcode lookups.
Uses BrowserAutomationService for HOW to scrape.

Following SRP: This class knows about barcode-specific logic, not scraping mechanics.
"""

import logging
from typing import Dict, Any
from ..services.browser_service import BrowserAutomationService
from ..domain.value_objects import SelectorSet, ScrapingOptions

logger = logging.getLogger(__name__)


class BarcodeProductScraper:
    """
    Application Service: Scrapes product data from barcode search results

    This class contains barcode-specific business logic:
    - Which sites to check
    - What selectors to use
    - How to format results

    It delegates the actual scraping to BrowserAutomationService.
    """

    # Site-specific selector configurations
    SITE_CONFIGS = {
        'onewholesale.ca': {
            'selectors': SelectorSet(
                product_name=[
                    # Mega-menu classes (used in search results)
                    '.mm-featured-title',
                    '.mm-title',
                    '.mm-product-name',
                    # Product page classes (fallback)
                    'h1.product-title',
                    'h2.product-title',
                    'h3.product-name',
                    '.product-single__title',
                    '[class*="product"][class*="title"]',
                    'h1',  # Last resort fallback
                ],
                product_price=[
                    # Mega-menu price classes
                    '.mega-menu-price',
                    '.mega-menu-compare_at_price',
                    'span.money',
                    # Standard product page prices (fallback)
                    'span.price',
                    '.product-price',
                    '[class*="price"]',
                ],
                product_image=[
                    # Mega-menu image classes
                    '.mm-image-container img',
                    '.mm-image img',
                    '.get-product-image',
                    # Product page images (fallback)
                    '.product-single__photo img',
                    '.product-featured-img',
                    '.product-image img',
                    'img[class*="product"]',
                ],
                product_brand=[
                    '.product-vendor',
                    '.brand-name',
                    '[class*="vendor"]',
                ],
            ),
            'options': ScrapingOptions(
                wait_for_selector='.mega-menu-item-container, .product-card, .product-single',
                wait_for_timeout=5000,
                wait_for_network_idle=True,  # Wait for all network requests to complete
                extract_json_ld=True,
                strategy='dynamic',  # Force browser automation for JavaScript-heavy site
            ),
        },
        'upcitemdb.com': {
            'selectors': SelectorSet(
                product_name=[
                    'p.detailtitle b',
                    '.product-name',
                ],
                product_image=[
                    '.EANimage img',
                    '#EANimage img',
                ],
            ),
            'options': ScrapingOptions(
                strategy='static',  # Known to work with static
                extract_json_ld=False,
            ),
        },
        # Add more sites as needed
    }

    def __init__(self, browser_service: BrowserAutomationService):
        """
        Initialize barcode product scraper

        Args:
            browser_service: Browser automation service to use for scraping
        """
        self.browser_service = browser_service

    async def scrape_one_wholesale(self, barcode: str) -> Dict[str, Any]:
        """
        Scrape ONE Wholesale for barcode product data

        This is the method that replaces the old _scrape_one_wholesale
        in BarcodeLookupService, now using browser automation.

        Args:
            barcode: Barcode to search for

        Returns:
            Dictionary with product data and metadata

        Example:
            >>> scraper = BarcodeProductScraper(browser_service)
            >>> result = await scraper.scrape_one_wholesale('841562004743')
            >>> print(result['data']['name'])
            'Evolve - Pipe Cleaners Pack of 50'
        """
        url = f"https://www.onewholesale.ca/search?q={barcode}"
        config = self.SITE_CONFIGS['onewholesale.ca']

        logger.info(f"Scraping ONE Wholesale for barcode: {barcode}")

        # Use browser automation service
        result = await self.browser_service.scrape(
            url=url,
            selectors=config['selectors'],
            options=config['options']
        )

        # Format result for barcode lookup service
        return {
            'found': result.found,
            'data': result.data,
            'source': 'ONE Wholesale',
            'confidence': result.get_confidence(),
            'strategy_used': result.strategy_used,
            'latency_ms': result.latency_ms,
            'barcode': barcode,
        }

    async def scrape_upcitemdb(self, barcode: str) -> Dict[str, Any]:
        """
        Scrape UPCItemDB for barcode data

        Args:
            barcode: Barcode to search for

        Returns:
            Dictionary with product data
        """
        url = f"https://www.upcitemdb.com/upc/{barcode}"
        config = self.SITE_CONFIGS.get('upcitemdb.com', {
            'selectors': SelectorSet(
                product_name=['p.detailtitle b'],
                product_image=['.EANimage img'],
            ),
            'options': ScrapingOptions(strategy='static'),
        })

        logger.info(f"Scraping UPCItemDB for barcode: {barcode}")

        result = await self.browser_service.scrape(
            url=url,
            selectors=config['selectors'],
            options=config.get('options', ScrapingOptions())
        )

        return {
            'found': result.found,
            'data': result.data,
            'source': 'UPCItemDB',
            'confidence': result.get_confidence(),
            'strategy_used': result.strategy_used,
            'latency_ms': result.latency_ms,
            'barcode': barcode,
        }

    async def scrape_multiple_sites(
        self,
        barcode: str,
        sites: list[str] | None = None
    ) -> list[Dict[str, Any]]:
        """
        Scrape multiple sites in parallel for a barcode

        Args:
            barcode: Barcode to search for
            sites: List of sites to check (defaults to all configured sites)

        Returns:
            List of results from all sites

        Example:
            >>> results = await scraper.scrape_multiple_sites('841562004743')
            >>> for r in results:
            ...     if r['found']:
            ...         print(f"{r['source']}: {r['data']['name']}")
        """
        import asyncio

        sites = sites or ['onewholesale.ca', 'upcitemdb.com']

        # Create scraping tasks
        tasks = []
        for site in sites:
            if site == 'onewholesale.ca':
                tasks.append(self.scrape_one_wholesale(barcode))
            elif site == 'upcitemdb.com':
                tasks.append(self.scrape_upcitemdb(barcode))
            # Add more sites as needed

        # Execute in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions
        valid_results = []
        for result in results:
            if isinstance(result, dict):
                valid_results.append(result)
            elif isinstance(result, Exception):
                logger.error(f"Scraping error: {result}")

        return valid_results

    def add_site_config(
        self,
        site: str,
        selectors: SelectorSet,
        options: ScrapingOptions
    ) -> None:
        """
        Add or update configuration for a site

        This allows dynamic addition of new sites without code changes.

        Args:
            site: Site domain (e.g., 'example.com')
            selectors: Selectors for the site
            options: Scraping options for the site

        Example:
            >>> scraper.add_site_config(
            ...     'newsite.com',
            ...     SelectorSet(product_name=['h1.title']),
            ...     ScrapingOptions(strategy='hybrid')
            ... )
        """
        self.SITE_CONFIGS[site] = {
            'selectors': selectors,
            'options': options,
        }
        logger.info(f"Added configuration for site: {site}")
