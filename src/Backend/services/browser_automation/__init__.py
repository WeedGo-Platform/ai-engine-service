"""
Browser Automation Service
A reusable, DDD-based web scraping system with intelligent strategy selection

Public API:
- BrowserAutomationService: Main service for web scraping
- BarcodeProductScraper: Application-level barcode scraping
- ScrapingResult: Result entity
- BrowserConfig, ScrapingOptions, SelectorSet: Value objects
"""

from .domain.entities import ScrapingResult
from .domain.value_objects import BrowserConfig, ScrapingOptions, SelectorSet
from .services.browser_service import BrowserAutomationService
from .scrapers.barcode_scraper import BarcodeProductScraper

__all__ = [
    'BrowserAutomationService',
    'BarcodeProductScraper',
    'ScrapingResult',
    'BrowserConfig',
    'ScrapingOptions',
    'SelectorSet',
]
