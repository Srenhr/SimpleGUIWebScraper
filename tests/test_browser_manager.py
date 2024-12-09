# tests/test_browser_manager.py
import pytest
from unittest.mock import Mock, patch
from selenium.common.exceptions import WebDriverException
from src.core.browser_manager import BrowserManager
from src.config import AppConfig
from src.core.exceptions import BrowserError

@pytest.fixture
def config():
    return AppConfig()

@pytest.fixture
def mock_webdriver():
    with patch('selenium.webdriver.Firefox') as mock:
        yield mock

@pytest.fixture
def browser_manager(config):
    return BrowserManager(config)

class TestBrowserManager:
    def test_detect_default_browser_windows(self, browser_manager):
        with patch('platform.system', return_value='Windows'):
            with patch('winreg.OpenKey'), \
                 patch('winreg.QueryValueEx', return_value=('ChromeHTML', None)):
                browser_type = browser_manager._detect_default_browser()
                assert browser_type == 'chrome'

    def test_ensure_driver_retry_success(self, browser_manager, mock_webdriver):
        browser_manager.driver = Mock()
        browser_manager.driver.title.side_effect = [
            WebDriverException("Failed"),
            None  # Success on second try
        ]
        
        driver = browser_manager._ensure_driver()
        assert driver is not None
        assert browser_manager.driver.quit.call_count == 1

    def test_ensure_driver_max_retries(self, browser_manager, mock_webdriver):
        browser_manager.driver = Mock()
        browser_manager.driver.title.side_effect = WebDriverException("Failed")
        
        with pytest.raises(BrowserError):
            browser_manager._ensure_driver()

    def test_cleanup(self, browser_manager):
        mock_driver = Mock()
        browser_manager.driver = mock_driver
        
        browser_manager.cleanup()
        assert mock_driver.quit.called
        assert browser_manager.driver is None

    @patch('time.sleep')  # Prevent actual delays in tests
    def test_create_driver_with_options(self, mock_sleep, browser_manager, config):
        with patch('selenium.webdriver.Firefox') as mock_firefox:
            browser_manager.browser_type = 'firefox'
            driver = browser_manager._create_driver()
            
            assert driver is not None
            # Verify user agent was set
            mock_firefox.call_args[1]['options'].preferences.get(
                'general.useragent.override'
            ) == config.USER_AGENT