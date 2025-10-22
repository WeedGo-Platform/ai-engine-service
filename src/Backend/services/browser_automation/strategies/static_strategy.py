"""
Static Scraping Strategy - Fast, lightweight scraping using aiohttp

Best for: Server-rendered HTML without JavaScript
Performance: ~300ms per request
Coverage: ~90-95% of websites
"""

import aiohttp
import time
import json
import logging
from bs4 import BeautifulSoup
from typing import Dict, Any
from .base import AbstractScrapingStrategy
from ..domain.entities import ScrapingResult
from ..domain.value_objects import SelectorSet, ScrapingOptions
from ..domain.exceptions import ScrapingTimeoutError, NavigationError

logger = logging.getLogger(__name__)


class StaticScrapingStrategy(AbstractScrapingStrategy):
    """
    Fast scraping using aiohttp + BeautifulSoup

    Advantages:
    - Very fast (~300ms)
    - Low resource usage
    - No browser overhead
    - Simple and reliable

    Limitations:
    - Cannot execute JavaScript
    - Misses dynamically-loaded content
    - No interaction with page elements
    """

    def get_name(self) -> str:
        return 'static'

    async def scrape(
        self,
        url: str,
        selectors: SelectorSet,
        options: ScrapingOptions
    ) -> ScrapingResult:
        """Scrape using static HTML parsing"""
        start_time = time.time()

        try:
            # Fetch HTML
            html, status_code = await self._fetch_html(url, options)

            if status_code != 200:
                return self._create_error_result(
                    url,
                    f"HTTP {status_code}",
                    time.time() - start_time
                )

            # Parse HTML
            soup = BeautifulSoup(html, 'html.parser')

            # Extract data using selectors
            data = self._extract_data(soup, selectors, options)

            # Create result
            return ScrapingResult(
                url=url,
                found=bool(data),
                data=data,
                strategy_used=self.get_name(),
                latency_ms=(time.time() - start_time) * 1000,
                html_snapshot=html[:5000] if options.take_screenshot else None  # First 5KB
            )

        except aiohttp.ClientError as e:
            logger.error(f"Static scraping failed for {url}: {e}")
            return self._create_error_result(
                url,
                str(e),
                time.time() - start_time
            )

    async def _fetch_html(
        self,
        url: str,
        options: ScrapingOptions
    ) -> tuple[str, int]:
        """
        Fetch HTML using aiohttp

        Returns:
            Tuple of (html_content, status_code)
        """
        timeout = aiohttp.ClientTimeout(
            total=options.wait_for_timeout / 1000  # Convert ms to seconds
        )

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, headers=headers) as response:
                html = await response.text()
                return html, response.status

    def _extract_data(
        self,
        soup: BeautifulSoup,
        selectors: SelectorSet,
        options: ScrapingOptions
    ) -> Dict[str, Any]:
        """
        Extract data from BeautifulSoup object using selectors

        Args:
            soup: Parsed HTML
            selectors: CSS selectors for extraction
            options: Scraping options

        Returns:
            Dictionary of extracted data
        """
        data = {}

        # Extract product name
        if selectors.product_name:
            name = self._extract_by_selectors(soup, selectors.product_name)
            if name:
                data['name'] = name

        # Extract product price
        if selectors.product_price:
            price_text = self._extract_by_selectors(soup, selectors.product_price)
            if price_text:
                data['price'] = self._parse_price(price_text)
                data['price_text'] = price_text

        # Extract product image
        if selectors.product_image:
            img = self._extract_image(soup, selectors.product_image)
            if img:
                data['image_url'] = img

        # Extract brand
        if selectors.product_brand:
            brand = self._extract_by_selectors(soup, selectors.product_brand)
            if brand:
                data['brand'] = brand

        # Extract SKU
        if selectors.product_sku:
            sku = self._extract_by_selectors(soup, selectors.product_sku)
            if sku:
                data['sku'] = sku

        # Extract JSON-LD structured data if enabled
        if options.extract_json_ld:
            json_ld_data = self._extract_json_ld(soup)
            if json_ld_data:
                data.update(json_ld_data)

        # Extract custom selectors
        if selectors.custom:
            for key, selector_list in selectors.custom.items():
                value = self._extract_by_selectors(soup, selector_list)
                if value:
                    data[key] = value

        return data

    def _extract_image(self, soup: BeautifulSoup, selectors: list[str]) -> str | None:
        """Extract image URL from img tags"""
        for selector in selectors:
            try:
                img = soup.select_one(selector)
                if img:
                    # Try different attribute names
                    for attr in ['src', 'data-src', 'data-lazy-src']:
                        url = img.get(attr)
                        if url:
                            return self._normalize_url(url)
            except Exception:
                continue
        return None

    def _normalize_url(self, url: str) -> str:
        """Normalize relative URLs to absolute"""
        if url.startswith('//'):
            return 'https:' + url
        elif url.startswith('/'):
            # Would need base URL to make absolute - just return as-is
            return url
        return url

    def _parse_price(self, price_text: str) -> float | None:
        """Extract numeric price from text"""
        import re
        # Remove currency symbols and extract first number
        matches = re.findall(r'[\d,]+\.?\d*', price_text)
        if matches:
            try:
                # Remove commas and convert to float
                return float(matches[0].replace(',', ''))
            except ValueError:
                pass
        return None

    def _extract_json_ld(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Extract JSON-LD structured data (common in Shopify, WooCommerce, etc.)

        Returns:
            Dictionary with extracted fields
        """
        data = {}
        scripts = soup.find_all('script', type='application/ld+json')

        for script in scripts:
            try:
                json_data = json.loads(script.string)
                if isinstance(json_data, dict):
                    if json_data.get('@type') == 'Product':
                        # Extract product data from JSON-LD
                        data['name'] = json_data.get('name', data.get('name'))
                        data['brand'] = json_data.get('brand', {}).get('name', data.get('brand'))
                        data['sku'] = json_data.get('sku', data.get('sku'))

                        # Extract price from offers
                        offers = json_data.get('offers', {})
                        if isinstance(offers, dict):
                            price = offers.get('price')
                            if price:
                                data['price'] = float(price)
                        elif isinstance(offers, list) and offers:
                            price = offers[0].get('price')
                            if price:
                                data['price'] = float(price)

                        # Extract image
                        image = json_data.get('image')
                        if isinstance(image, list):
                            data['image_url'] = image[0]
                        elif isinstance(image, str):
                            data['image_url'] = image

            except (json.JSONDecodeError, AttributeError, ValueError):
                continue

        return data

    def _create_error_result(
        self,
        url: str,
        error: str,
        elapsed_time: float
    ) -> ScrapingResult:
        """Create ScrapingResult for error case"""
        return ScrapingResult(
            url=url,
            found=False,
            data={},
            strategy_used=self.get_name(),
            latency_ms=elapsed_time * 1000,
            error=error
        )
