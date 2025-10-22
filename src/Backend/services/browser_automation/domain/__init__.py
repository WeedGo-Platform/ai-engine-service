"""Domain layer for browser automation"""

from .entities import ScrapingResult
from .value_objects import BrowserConfig, ScrapingOptions, SelectorSet
from .exceptions import (
    BrowserAutomationError,
    ScrapingTimeoutError,
    BrowserNotAvailableError,
    InvalidSelectorError
)

__all__ = [
    'ScrapingResult',
    'BrowserConfig',
    'ScrapingOptions',
    'SelectorSet',
    'BrowserAutomationError',
    'ScrapingTimeoutError',
    'BrowserNotAvailableError',
    'InvalidSelectorError',
]
