# src/core/exceptions.py
from typing import Optional

class WebScraperError(Exception):
    """Base exception for web scraper errors"""
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.original_error = original_error

class ScraperError(WebScraperError):
    """Raised when scraping fails"""
    pass

class DownloaderError(WebScraperError):
    """Raised when download fails"""
    pass

class BrowserError(WebScraperError):
    """Raised when browser operations fail"""
    pass