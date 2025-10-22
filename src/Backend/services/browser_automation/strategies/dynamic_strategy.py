"""
Dynamic Scraping Strategy - Full browser automation using Playwright

Best for: JavaScript-heavy sites with dynamic content
Performance: ~4000ms per request
Coverage: ~99% of websites
"""

import time
import json
import logging
from typing import Dict, Any, Optional
from playwright.async_api import async_playwright, Page, Browser, Error as PlaywrightError
from .base import AbstractScrapingStrategy
from ..domain.entities import ScrapingResult
from ..domain.value_objects import SelectorSet, ScrapingOptions, BrowserConfig
from ..domain.exceptions import (
    ScrapingTimeoutError,
    BrowserLaunchError,
    NavigationError
)

logger = logging.getLogger(__name__)


class DynamicScrapingStrategy(AbstractScrapingStrategy):
    """
    Full browser automation using Playwright

    Advantages:
    - Executes JavaScript
    - Sees fully-rendered content
    - Can interact with page elements
    - Handles SPAs, lazy loading, AJAX

    Limitations:
    - Slower (~4s vs ~300ms)
    - Higher resource usage (CPU, memory)
    - More complex error handling
    """

    def __init__(self, browser_config: Optional[BrowserConfig] = None):
        self.browser_config = browser_config or BrowserConfig()

    def get_name(self) -> str:
        return 'dynamic'

    async def scrape(
        self,
        url: str,
        selectors: SelectorSet,
        options: ScrapingOptions
    ) -> ScrapingResult:
        """Scrape using Playwright browser automation"""
        start_time = time.time()

        try:
            async with async_playwright() as p:
                # Launch browser
                browser = await self._launch_browser(p)

                try:
                    # Create page and navigate
                    page = await browser.new_page()
                    await self._navigate(page, url, options)

                    # Wait for content to load
                    if options.wait_for_selector:
                        await self._wait_for_content(page, options)

                    # Extract data
                    data = await self._extract_data(page, selectors, options)

                    # Take screenshot if requested
                    screenshot_path = None
                    if options.take_screenshot:
                        screenshot_path = await self._save_screenshot(page, url, options)

                    # Create result
                    return ScrapingResult(
                        url=url,
                        found=bool(data),
                        data=data,
                        strategy_used=self.get_name(),
                        latency_ms=(time.time() - start_time) * 1000,
                        screenshot_path=screenshot_path
                    )

                finally:
                    await browser.close()

        except PlaywrightError as e:
            logger.error(f"Playwright error for {url}: {e}")
            return self._create_error_result(url, str(e), time.time() - start_time)

        except Exception as e:
            logger.error(f"Unexpected error for {url}: {e}")
            return self._create_error_result(url, str(e), time.time() - start_time)

    async def _launch_browser(self, playwright) -> Browser:
        """Launch browser with configuration"""
        try:
            return await playwright.chromium.launch(
                headless=self.browser_config.headless,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
        except Exception as e:
            raise BrowserLaunchError(str(e))

    async def _navigate(
        self,
        page: Page,
        url: str,
        options: ScrapingOptions
    ) -> None:
        """Navigate to URL with proper wait conditions"""
        try:
            # Set viewport
            await page.set_viewport_size({
                'width': self.browser_config.viewport_width,
                'height': self.browser_config.viewport_height
            })

            # Set user agent if provided
            if self.browser_config.user_agent:
                await page.set_extra_http_headers({
                    'User-Agent': self.browser_config.user_agent
                })

            # Navigate
            wait_until = 'networkidle' if options.wait_for_network_idle else 'domcontentloaded'
            await page.goto(
                url,
                wait_until=wait_until,
                timeout=self.browser_config.timeout
            )

        except PlaywrightError as e:
            raise NavigationError(url, str(e))

    async def _wait_for_content(
        self,
        page: Page,
        options: ScrapingOptions
    ) -> None:
        """Wait for specific content to appear"""
        if options.wait_for_selector:
            try:
                await page.wait_for_selector(
                    options.wait_for_selector,
                    timeout=options.wait_for_timeout
                )
            except PlaywrightError:
                # Selector didn't appear - continue anyway
                logger.warning(
                    f"Wait selector '{options.wait_for_selector}' not found, continuing..."
                )

    async def _extract_data(
        self,
        page: Page,
        selectors: SelectorSet,
        options: ScrapingOptions
    ) -> Dict[str, Any]:
        """
        Extract data from page using selectors

        Args:
            page: Playwright page object
            selectors: CSS selectors for extraction
            options: Scraping options

        Returns:
            Dictionary of extracted data
        """
        data = {}

        # Extract product name
        if selectors.product_name:
            name = await self._extract_text_by_selectors(page, selectors.product_name)
            if name:
                data['name'] = name

        # Extract product price
        if selectors.product_price:
            price_text = await self._extract_text_by_selectors(page, selectors.product_price)
            if price_text:
                data['price'] = self._parse_price(price_text)
                data['price_text'] = price_text

        # Extract product image
        if selectors.product_image:
            img = await self._extract_image(page, selectors.product_image)
            if img:
                data['image_url'] = img

        # Extract brand
        if selectors.product_brand:
            brand = await self._extract_text_by_selectors(page, selectors.product_brand)
            if brand:
                data['brand'] = brand

        # Extract SKU
        if selectors.product_sku:
            sku = await self._extract_text_by_selectors(page, selectors.product_sku)
            if sku:
                data['sku'] = sku

        # Extract JSON-LD structured data if enabled
        if options.extract_json_ld:
            json_ld_data = await self._extract_json_ld(page)
            if json_ld_data:
                data.update(json_ld_data)

        # Extract custom selectors
        if selectors.custom:
            for key, selector_list in selectors.custom.items():
                value = await self._extract_text_by_selectors(page, selector_list)
                if value:
                    data[key] = value

        return data

    async def _extract_text_by_selectors(
        self,
        page: Page,
        selectors: list[str]
    ) -> str | None:
        """Try multiple selectors, return first match"""
        for selector in selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    text = await element.text_content()
                    if text:
                        return text.strip()
            except Exception:
                continue
        return None

    async def _extract_image(
        self,
        page: Page,
        selectors: list[str]
    ) -> str | None:
        """Extract image URL"""
        for selector in selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    # Try different attributes
                    for attr in ['src', 'data-src', 'data-lazy-src']:
                        url = await element.get_attribute(attr)
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
            return url  # Would need base URL
        return url

    def _parse_price(self, price_text: str) -> float | None:
        """Extract numeric price from text"""
        import re
        matches = re.findall(r'[\d,]+\.?\d*', price_text)
        if matches:
            try:
                return float(matches[0].replace(',', ''))
            except ValueError:
                pass
        return None

    async def _extract_json_ld(self, page: Page) -> Dict[str, Any]:
        """Extract JSON-LD structured data"""
        data = {}

        try:
            # Find all JSON-LD scripts
            scripts = await page.query_selector_all('script[type="application/ld+json"]')

            for script in scripts:
                try:
                    content = await script.text_content()
                    if not content:
                        continue

                    json_data = json.loads(content)
                    if isinstance(json_data, dict) and json_data.get('@type') == 'Product':
                        # Extract product data
                        data['name'] = json_data.get('name', data.get('name'))
                        data['brand'] = json_data.get('brand', {}).get('name', data.get('brand'))
                        data['sku'] = json_data.get('sku', data.get('sku'))

                        # Extract price
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

        except Exception as e:
            logger.warning(f"JSON-LD extraction failed: {e}")

        return data

    async def _save_screenshot(
        self,
        page: Page,
        url: str,
        options: ScrapingOptions
    ) -> str:
        """Save screenshot of page"""
        import hashlib
        from pathlib import Path

        # Generate filename from URL
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        filename = f"screenshot_{url_hash}_{int(time.time())}.png"

        # Use provided path or default
        if options.screenshot_path:
            path = Path(options.screenshot_path) / filename
        else:
            path = Path("/tmp/screenshots") / filename

        path.parent.mkdir(parents=True, exist_ok=True)

        # Take screenshot
        await page.screenshot(path=str(path), full_page=True)

        return str(path)

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
