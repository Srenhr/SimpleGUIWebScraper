# src/core/scraper_service.py
import logging
import requests
import requests.adapters
import aiohttp
from typing import List, Set, Optional
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from urllib3.util.retry import Retry
from requests.exceptions import RequestException

from ..config import AppConfig
from .browser_manager import BrowserManager
from .exceptions import ScraperError
from ..utils.performance import measure_performance

class ScraperService:
    def __init__(self, config: AppConfig, browser_manager: BrowserManager):
        self.config = config
        self.browser_manager = browser_manager
        self.logger = logging.getLogger(__name__)
        self.seen_urls: Set[str] = set()
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create session with retries and connection pooling"""
        session = requests.Session()
        retries = Retry(
            total=self.config.RETRY_ATTEMPTS,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504]
        )
        adapter = requests.adapters.HTTPAdapter(
            max_retries=retries,
            pool_connections=10,
            pool_maxsize=10
        )
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        return session

    @measure_performance
    async def fetch_files(self, url: str, file_types: List[str]) -> List[str]:
        """Fetch files of specified types from URL with performance monitoring"""
        self.logger.info(f"Fetching files from {url}")
        
        # Clear seen_urls cache for new search
        self.seen_urls.clear()
        
        try:
            if not self._is_valid_url(url):
                raise ScraperError(f"Invalid URL format: {url}")

            headers = {
                "User-Agent": self.config.USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1"
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    response.raise_for_status()
                    content = await response.text()
                    
                    soup = BeautifulSoup(content, 'html.parser')
                    files = self._extract_files(soup, url, file_types)
                    self.logger.info(f"Found {len(files)} files")
                    return files

        except aiohttp.ClientError as e:
            error_msg = f"Failed to fetch URL {url}"
            self.logger.error(f"{error_msg}: {e}")
            raise ScraperError(error_msg, e)
        except Exception as e:
            error_msg = f"Unexpected error fetching files from {url}"
            self.logger.error(f"{error_msg}: {e}")
            raise ScraperError(error_msg, e)

    def _extract_files(self, soup: BeautifulSoup, base_url: str, file_types: List[str]) -> List[str]:
        """Extract files of specified types from parsed HTML"""
        valid_files = []
        links = soup.find_all('a', href=True)
        
        for link in links:
            href = link['href']
            if any(href.lower().endswith(ft.lower()) for ft in file_types):
                try:
                    absolute_url = urljoin(base_url, href)
                    if self._is_valid_url(absolute_url) and absolute_url not in self.seen_urls:
                        self.seen_urls.add(absolute_url)
                        valid_files.append(absolute_url)
                except Exception as e:
                    self.logger.warning(f"Error processing URL {href}: {e}")
                    continue
                    
        if not valid_files:
            self.logger.warning(f"No files of types {file_types} found at {base_url}")
        
        return valid_files

    def _is_valid_url(self, url: str) -> bool:
        """Validate URL format"""
        try:
            result = urlparse(url)
            return all([
                result.scheme in ('http', 'https'),
                result.netloc,
                not result.path.endswith(('//', '\\'))
            ])
        except Exception as e:
            self.logger.warning(f"URL validation failed for {url}: {e}")
            return False

    def __del__(self):
        """Cleanup session on object destruction"""
        if hasattr(self, 'session'):
            try:
                self.session.close()
            except Exception as e:
                self.logger.error(f"Error closing session: {e}")