"""
Abstract base class for scraping strategies

Following SRP: Each strategy knows HOW to scrape, not WHAT to scrape.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from ..domain.entities import ScrapingResult
from ..domain.value_objects import SelectorSet, ScrapingOptions


class AbstractScrapingStrategy(ABC):
    """
    Base class for all scraping strategies

    Defines the contract that all strategies must follow.
    Implements Template Method pattern for common scraping flow.
    """

    @abstractmethod
    async def scrape(
        self,
        url: str,
        selectors: SelectorSet,
        options: ScrapingOptions
    ) -> ScrapingResult:
        """
        Scrape a URL and return structured result

        Args:
            url: URL to scrape
            selectors: CSS selectors for data extraction
            options: Scraping options (timeout, wait conditions, etc.)

        Returns:
            ScrapingResult with extracted data

        Raises:
            BrowserAutomationError: On scraping failures
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """
        Get strategy name for logging and metrics

        Returns:
            Strategy name (e.g., 'static', 'dynamic')
        """
        pass

    def _extract_by_selectors(
        self,
        soup_or_page: Any,
        selectors: list[str]
    ) -> str | None:
        """
        Try multiple selectors in order, return first match

        Args:
            soup_or_page: BeautifulSoup or Playwright Page object
            selectors: List of CSS selectors to try

        Returns:
            Extracted text or None if no match
        """
        for selector in selectors:
            try:
                element = soup_or_page.select_one(selector)
                if element:
                    return element.text.strip() if hasattr(element, 'text') else element
            except Exception:
                continue
        return None

    def _calculate_initial_confidence(self, data: Dict[str, Any]) -> float:
        """
        Calculate initial confidence based on data completeness

        Args:
            data: Extracted data dictionary

        Returns:
            Confidence score 0.0-1.0
        """
        if not data:
            return 0.0

        # Count non-empty fields
        populated_fields = sum(1 for v in data.values() if v)

        # More fields = higher confidence
        if populated_fields >= 4:  # name, price, image, brand
            return 0.80
        elif populated_fields >= 2:
            return 0.60
        elif populated_fields >= 1:
            return 0.40
        else:
            return 0.0
