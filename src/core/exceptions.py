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

class URLError(ScraperError):
    """Raised when URL is invalid or unreachable"""
    pass

class ParsingError(ScraperError):
    """Raised when HTML parsing fails"""
    pass

class DownloaderError(WebScraperError):
    """Raised when download fails"""
    pass

class DownloadTimeout(DownloaderError):
    """Raised when download times out"""
    pass

class BrowserError(WebScraperError):
    """Raised when browser operations fail"""
    pass

class BrowserConnectionError(BrowserError):
    """Raised when browser connection fails"""
    pass

class BrowserSessionError(BrowserError):
    """Raised when browser session becomes invalid"""
    pass