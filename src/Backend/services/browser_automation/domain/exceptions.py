"""
Domain-specific exceptions for browser automation

Following DRY principle: Define exceptions once, use everywhere.
"""


class BrowserAutomationError(Exception):
    """Base exception for all browser automation errors"""
    pass


class ScrapingTimeoutError(BrowserAutomationError):
    """Raised when scraping operation times out"""

    def __init__(self, url: str, timeout_ms: int):
        self.url = url
        self.timeout_ms = timeout_ms
        super().__init__(
            f"Scraping timeout after {timeout_ms}ms for URL: {url}"
        )


class BrowserNotAvailableError(BrowserAutomationError):
    """Raised when no browser instance is available"""

    def __init__(self, message: str = "No browser instances available in pool"):
        self.message = message
        super().__init__(message)


class InvalidSelectorError(BrowserAutomationError):
    """Raised when selector is invalid or produces no results"""

    def __init__(self, selector: str, url: str):
        self.selector = selector
        self.url = url
        super().__init__(
            f"Invalid or non-matching selector '{selector}' for URL: {url}"
        )


class StrategySelectionError(BrowserAutomationError):
    """Raised when strategy selection fails"""

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"Failed to select scraping strategy: {reason}")


class BrowserLaunchError(BrowserAutomationError):
    """Raised when browser fails to launch"""

    def __init__(self, error_message: str):
        self.error_message = error_message
        super().__init__(f"Failed to launch browser: {error_message}")


class NavigationError(BrowserAutomationError):
    """Raised when page navigation fails"""

    def __init__(self, url: str, error_message: str):
        self.url = url
        self.error_message = error_message
        super().__init__(f"Navigation failed for {url}: {error_message}")
