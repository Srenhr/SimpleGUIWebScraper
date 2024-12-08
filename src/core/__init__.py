from .browser import BrowserManager, highlight_element, get_webdriver,ensure_driver
from .scraper import fetch_files
from .downloader import download_files_with_progress

__all__ = ['BrowserManager', 'fetch_files', 'download_files_with_progress','highlight_element','get_webdriver','ensure_driver']
__version__ = '0.1.0'