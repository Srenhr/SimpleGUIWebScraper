# src/core/browser_manager.py
import logging
import platform
import winreg
import time
from pathlib import Path
from typing import Optional
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from .exceptions import BrowserConnectionError

from ..config import AppConfig

class BrowserManager:
    def __init__(self, config: AppConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.driver: Optional[WebDriver] = None
        self.browser_type = self._detect_default_browser()

    def _detect_default_browser(self) -> str:
        """Detect system default browser"""
        try:
            if platform.system() == "Windows":
                with winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"SOFTWARE\Microsoft\Windows\Shell\Associations\URLAssociations\http\UserChoice"
                ) as key:
                    prog_id = winreg.QueryValueEx(key, "ProgId")[0].lower()
                    if "chrome" in prog_id:
                        self.logger.info("Using Chrome")
                        return "chrome"
                    elif "firefox" in prog_id:
                        self.logger.info("Using Firefox")
                        return "firefox"
        except Exception as e:
            self.logger.error(f"Browser detection failed: {e}")
        return "firefox"

    def get_driver(self) -> WebDriver:
        """Get or create WebDriver instance"""
        if not self.driver:
            try:
                self.driver = self._create_driver()
            except Exception as e:
                self.logger.error(f"Driver creation failed: {e}")
                raise
        return self._ensure_driver()

    def _create_driver(self) -> WebDriver:
        """Create new WebDriver instance"""
        options = webdriver.ChromeOptions() if self.browser_type == "chrome" else webdriver.FirefoxOptions()
        if self.config.USER_AGENT:
            if self.browser_type == "chrome":
                options.add_argument(f'user-agent={self.config.USER_AGENT}')
            else:
                options.set_preference("general.useragent.override", self.config.USER_AGENT)

        if self.browser_type == "chrome":
            service = ChromeService(ChromeDriverManager().install())
            return webdriver.Chrome(service=service, options=options)
        else:
            service = FirefoxService(GeckoDriverManager().install())
            return webdriver.Firefox(service=service, options=options)

    def _ensure_driver(self) -> WebDriver:
        """Ensure driver is working with exponential backoff"""
        max_retries = self.config.RETRY_ATTEMPTS
        for attempt in range(max_retries):
            try:
                if not self.driver:
                    self.driver = self._create_driver()
                self.driver.current_url
                return self.driver
            except WebDriverException as e:
                delay = min(2 ** attempt, 30)  # Exponential backoff, max 30s
                self.logger.warning(
                    f"Driver check failed (attempt {attempt + 1}/{max_retries})"
                    f" waiting {delay}s: {e}"
                )
                self.cleanup()
                if attempt < max_retries - 1:
                    time.sleep(delay)
                    self.driver = self._create_driver()
                else:
                    raise BrowserConnectionError(
                        f"Failed to initialize browser after {max_retries} attempts",
                        original_error=e
                    )
        return self.driver

    def cleanup(self) -> None:
        """Clean up browser resources with proper error handling"""
        if self.driver:
            try:
                self.driver.quit()
                time.sleep(1)  # Allow cleanup to complete
            except Exception as e:
                self.logger.error(
                    f"Browser cleanup failed: {e}. "
                    "Process may need manual termination."
                )
            finally:
                self.driver = None