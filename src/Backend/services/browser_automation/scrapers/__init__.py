"""
Application-level scrapers

These scrapers know WHAT to scrape but delegate HOW to the domain layer.
"""

from .barcode_scraper import BarcodeProductScraper

__all__ = [
    'BarcodeProductScraper',
]
