# src/core/scraper_service.py
import logging
import requests
from typing import List, Set
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

from ..config import AppConfig
from .browser_manager import BrowserManager

class ScraperService:
    def __init__(self, config: AppConfig, browser_manager: BrowserManager):
        self.config = config
        self.browser_manager = browser_manager
        self.logger = logging.getLogger(__name__)
        self.seen_urls: Set[str] = set()

    def fetch_files(self, url: str, file_types: List[str]) -> List[str]:
        """Fetch files of specified types from URL"""
        self.logger.info(f"Fetching files from {url}")
        
        try:
            # Use requests instead of Selenium for initial fetch
            headers = {"User-Agent": self.config.USER_AGENT}
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            files = self._extract_files(soup, url, file_types)
            self.logger.info(f"Found {len(files)} files")
            return files
        except Exception as e:
            self.logger.error(f"Error fetching files: {e}")
            raise

    def _extract_files(self, soup: BeautifulSoup, base_url: str, file_types: List[str]) -> List[str]:
        """Extract files of specified types from parsed HTML"""
        valid_files = []
        links = soup.find_all('a', href=True)
        
        for link in links:
            href = link['href']
            if any(href.lower().endswith(ft.lower()) for ft in file_types):
                absolute_url = urljoin(base_url, href)
                if self._is_valid_url(absolute_url) and absolute_url not in self.seen_urls:
                    self.seen_urls.add(absolute_url)
                    valid_files.append(absolute_url)
                    
        if not valid_files:
            self.logger.warning(f"No files of types {file_types} found at {base_url}")
        
        return valid_files

    def _is_valid_url(self, url: str) -> bool:
        """Validate URL"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False