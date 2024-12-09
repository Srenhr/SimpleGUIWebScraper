# tests/test_scraper_service.py
import pytest
import responses
from pathlib import Path
from bs4 import BeautifulSoup
from src.core.scraper_service import ScraperService
from src.core.browser_manager import BrowserManager
from src.config import AppConfig
from src.core.exceptions import ScraperError

@pytest.fixture
def config():
    return AppConfig()

@pytest.fixture
def browser_manager(config):
    return BrowserManager(config)

@pytest.fixture
def scraper_service(config, browser_manager):
    return ScraperService(config, browser_manager)

@pytest.fixture
def sample_html():
    return """
    <html>
        <body>
            <a href="file1.pdf">PDF 1</a>
            <a href="file2.pdf">PDF 2</a>
            <a href="file3.txt">Text File</a>
            <a href="http://example.com/file4.pdf">External PDF</a>
        </body>
    </html>
    """

class TestScraperService:
    @responses.activate
    def test_fetch_files_success(self, scraper_service, sample_html):
        # Setup
        url = "http://test.com"
        responses.add(
            responses.GET,
            url,
            body=sample_html,
            status=200
        )

        # Execute
        files = scraper_service.fetch_files(url, [".pdf"])

        # Assert
        assert len(files) == 3
        assert all(f.endswith('.pdf') for f in files)

    @responses.activate
    def test_fetch_files_invalid_url(self, scraper_service):
        # Execute & Assert
        with pytest.raises(ScraperError, match="Invalid URL format"):
            scraper_service.fetch_files("invalid-url", [".pdf"])

    @responses.activate
    def test_fetch_files_server_error(self, scraper_service):
        # Setup
        url = "http://test.com"
        responses.add(
            responses.GET,
            url,
            status=500
        )

        # Execute & Assert
        with pytest.raises(ScraperError, match="Failed to fetch URL"):
            scraper_service.fetch_files(url, [".pdf"])

    def test_extract_files(self, scraper_service, sample_html):
        # Setup
        soup = BeautifulSoup(sample_html, 'html.parser')
        base_url = "http://test.com"

        # Execute
        files = scraper_service._extract_files(soup, base_url, [".pdf"])

        # Assert
        assert len(files) == 3
        assert all(f.endswith('.pdf') for f in files)
        assert all(f.startswith('http://') for f in files)

    def test_is_valid_url(self, scraper_service):
        # Valid URLs
        assert scraper_service._is_valid_url("http://example.com")
        assert scraper_service._is_valid_url("https://example.com/file.pdf")

        # Invalid URLs
        assert not scraper_service._is_valid_url("invalid-url")
        assert not scraper_service._is_valid_url("ftp://example.com")
        assert not scraper_service._is_valid_url("http://example.com//")