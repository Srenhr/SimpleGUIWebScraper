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
        """Ensure driver is working"""
        try:
            if self.driver:
                self.driver.title  # Test if driver is responsive
                return self.driver
        except WebDriverException as e:
            self.logger.warning(f"Driver check failed: {e}")
            self.cleanup()
            self.driver = self._create_driver()
        return self.driver

    def cleanup(self) -> None:
        """Clean up browser resources"""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                self.logger.error(f"Cleanup error: {e}")
            finally:
                self.driver = None
                # Add small delay to allow proper cleanup
                time.sleep(0.5)