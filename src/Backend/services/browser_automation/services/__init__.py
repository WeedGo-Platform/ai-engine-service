"""Domain services for browser automation orchestration"""

from .strategy_selector import ScrapingStrategySelector
from .browser_service import BrowserAutomationService

__all__ = [
    'ScrapingStrategySelector',
    'BrowserAutomationService',
]
