# src/core/scraper_service.py
import aiohttp
import asyncio
import logging
from typing import List, Set, Optional
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from .exceptions import WebScraperError, ScraperError, URLError, ParsingError
from .browser_manager import BrowserManager
from ..config import AppConfig

class ScraperService:
    def __init__(self, config: AppConfig, browser_manager: BrowserManager):
        self.config = config
        self.browser_manager = browser_manager
        self.logger = logging.getLogger(__name__)
        self.seen_urls: Set[str] = set()
        self._session: Optional[aiohttp.ClientSession] = None
        self.timeout = aiohttp.ClientTimeout(total=30, connect=10)

    async def ensure_session(self) -> None:
        """Ensure session is active"""
        if not self._session or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=self.timeout,
                headers=self._get_headers()
            )

    def _get_headers(self) -> dict:
        """Get request headers"""
        return {
            "User-Agent": self.config.USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "DNT": "1"
        }

    def _is_valid_url(self, url: str) -> bool:
        """Validate URL with improved checks"""
        try:
            result = urlparse(url)
            return all([
                result.scheme in ('http', 'https'),
                result.netloc,
                not result.path.endswith(('//', '\\')),
                len(url) < 2048,  # Common URL length limit
                not any(c in url for c in '<>"{}|\\^[]`')  # Invalid URL characters
            ])
        except Exception as e:
            self.logger.warning(f"URL validation failed for {url}: {e}")
            return False

    async def fetch_files(self, url: str, file_types: List[str]) -> List[str]:
        """Fetch files with comprehensive error handling"""
        self.logger.info(f"Fetching files from {url}")
        self.seen_urls.clear()
        
        try:
            if not self._is_valid_url(url):
                raise URLError(f"Invalid URL format: {url}")

            await self.ensure_session()
            
            for attempt in range(self.config.RETRY_ATTEMPTS):
                try:
                    async with self._session.get(url) as response:
                        response.raise_for_status()
                        content = await response.text()
                        
                        try:
                            soup = BeautifulSoup(content, 'html.parser', from_encoding=response.charset)
                        except Exception as e:
                            raise ParsingError(f"Failed to parse HTML from {url}", e)

                        files = self._extract_files(soup, url, file_types)
                        self.logger.info(f"Found {len(files)} files")
                        return files

                except aiohttp.ClientError as e:
                    delay = min(2 ** attempt, 30)  # Exponential backoff, max 30s
                    self.logger.warning(
                        f"Attempt {attempt + 1}/{self.config.RETRY_ATTEMPTS} "
                        f"failed, retrying in {delay}s: {e}"
                    )
                    if attempt == self.config.RETRY_ATTEMPTS - 1:
                        raise URLError(f"Failed to fetch URL {url}", e)
                    await asyncio.sleep(delay)
                    
                except asyncio.TimeoutError as e:
                    delay = min(2 ** attempt, 30)
                    self.logger.warning(
                        f"Timeout on attempt {attempt + 1}/{self.config.RETRY_ATTEMPTS}, "
                        f"retrying in {delay}s: {e}"
                    )
                    if attempt == self.config.RETRY_ATTEMPTS - 1:
                        raise URLError(f"Timeout fetching URL {url}", e)
                    await asyncio.sleep(delay)

        except WebScraperError:
            raise
        except Exception as e:
            raise ScraperError(f"Unexpected error scraping {url}", e)

    def _extract_files(self, soup: BeautifulSoup, base_url: str, file_types: List[str]) -> List[str]:
        """Extract files with validation"""
        valid_files = []
        seen_this_page = set()
        
        try:
            links = soup.find_all('a', href=True)
            for link in links:
                href = link['href']
                if any(href.lower().endswith(ft.lower()) for ft in file_types):
                    try:
                        absolute_url = urljoin(base_url, href)
                        if (self._is_valid_url(absolute_url) and 
                            absolute_url not in self.seen_urls and
                            absolute_url not in seen_this_page):
                            
                            self.seen_urls.add(absolute_url)
                            seen_this_page.add(absolute_url)
                            valid_files.append(absolute_url)
                            
                    except Exception as e:
                        self.logger.warning(
                            f"Error processing URL {href}: {e}",
                            exc_info=self.logger.isEnabledFor(logging.DEBUG)
                        )
                        continue

        except Exception as e:
            raise ParsingError(f"Error extracting files from HTML", e)

        return valid_files

    async def cleanup(self) -> None:
        """Clean up resources"""
        if self._session and not self._session.closed:
            try:
                await self._session.close()
            except Exception as e:
                self.logger.error(f"Error closing session: {e}")

    async def __aenter__(self):
        """Async context manager entry"""
        await self.ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.cleanup()