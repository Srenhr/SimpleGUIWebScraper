# tests/test_integration.py
import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch
from src.ui.scraper_gui import WebScraperGUI
from src.core.scraper_service import ScraperService
from src.config import AppConfig

@pytest.fixture
def config():
    return AppConfig()

@pytest.fixture
def mock_window():
    with patch('PySimpleGUI.Window') as mock:
        window = Mock()
        window.read.return_value = (sg.WIN_CLOSED, None)
        mock.return_value = window
        yield window

class TestIntegration:
    @pytest.mark.asyncio
    async def test_search_and_download_flow(self, config, mock_window):
        gui = WebScraperGUI(config)
        
        # Mock search results
        files = ["http://example.com/test1.pdf", "http://example.com/test2.pdf"]
        with patch.object(ScraperService, 'fetch_files', return_value=files):
            values = {
                "-URL-": "http://example.com",
                "-FILETYPE-": ".pdf",
                "-OUTPUT-": str(Path("downloads")),
                "-FILELIST-": [0]  # Select first file
            }
            
            await gui.handle_search(values)
            assert mock_window["-FILELIST-"].update.called
            
            # Mock download
            with patch('src.core.file_downloader.download_files') as mock_download:
                await gui.handle_download(values)
                assert mock_download.called

    @pytest.mark.asyncio
    async def test_browser_highlight_flow(self, config, mock_window):
        gui = WebScraperGUI(config)
        
        # Setup test state
        gui.files = ["http://example.com/test.pdf"]
        values = {
            "-URL-": "http://example.com",
            "-FILELIST-": [0]
        }
        
        with patch.object(gui.browser_manager, 'get_driver') as mock_get_driver:
            mock_driver = Mock()
            mock_get_driver.return_value = mock_driver
            
            await gui.handle_show_in_browser(values)
            
            assert mock_driver.get.called
            assert mock_driver.find_element.called
            assert mock_driver.execute_script.called

    @pytest.mark.asyncio
    async def test_error_propagation(self, config, mock_window):
        gui = WebScraperGUI(config)
        
        # Test search error handling
        with patch.object(ScraperService, 'fetch_files', side_effect=Exception("Test error")):
            with patch('PySimpleGUI.popup_error') as mock_popup:
                values = {"-URL-": "http://example.com", "-FILETYPE-": ".pdf"}
                await gui.handle_search(values)
                assert mock_popup.called

    @pytest.mark.asyncio
    async def test_search_retry_logic(self, config, mock_window):
        gui = WebScraperGUI(config)
        
        # Mock search results with retry logic
        with patch.object(ScraperService, 'fetch_files', side_effect=[Exception("Test error"), ["http://example.com/test1.pdf"] ]):
            values = {
                "-URL-": "http://example.com",
                "-FILETYPE-": ".pdf",
                "-OUTPUT-": str(Path("downloads")),
                "-FILELIST-": [0]  # Select first file
            }
            
            await gui.handle_search(values)
            assert mock_window["-FILELIST-"].update.called