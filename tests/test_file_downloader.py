# tests/test_file_downloader.py
import pytest
import aiohttp
from pathlib import Path
from unittest.mock import patch, AsyncMock
from src.core.download_manager import DownloadManager
from src.config import AppConfig
from src.utils.exceptions import DownloaderError

@pytest.fixture
def config():
    return AppConfig()

@pytest.fixture
def download_manager(config):
    return DownloadManager(config)

class TestDownloadManager:
    @pytest.mark.asyncio
    async def test_session_management(self, download_manager):
        async with download_manager:
            assert download_manager._session is not None
            assert not download_manager._session.closed
        assert download_manager._session.closed

    @pytest.mark.asyncio
    async def test_download_file_cache(self, download_manager, tmp_path):
        url = "http://example.com/test.pdf"
        download_manager._cache[url] = tmp_path / "cached.pdf"
        
        result = await download_manager.download_file(url, tmp_path)
        assert result == download_manager._cache[url]

    @pytest.mark.asyncio
    async def test_download_file_with_progress(self, download_manager, tmp_path):
        url = "http://example.com/test.pdf"
        progress_calls = []
        
        async def progress_callback(msg: str):
            progress_calls.append(msg)

        mock_response = AsyncMock()
        mock_response.headers = {"content-length": "1024"}
        mock_response.content.iter_chunked = AsyncMock(
            return_value=[b"data" * 256]
        )

        with patch("aiohttp.ClientSession") as mock_session:
            mock_session.return_value.__aenter__.return_value.get.return_value = mock_response
            mock_response.__aenter__.return_value = mock_response
            
            async with download_manager:
                await download_manager.download_file(
                    url, tmp_path, progress_callback
                )

        assert len(progress_calls) > 0
        assert any("Successfully downloaded" in msg for msg in progress_calls)

    @pytest.mark.asyncio
    async def test_download_retry_logic(self, download_manager, tmp_path):
        url = "http://example.com/test.pdf"
        
        with patch("aiohttp.ClientSession") as mock_session:
            mock_session.return_value.__aenter__.return_value.get.side_effect = [
                aiohttp.ClientError(),  # First attempt fails
                AsyncMock()  # Second attempt succeeds
            ]
            
            with pytest.raises(DownloaderError):
                async with download_manager:
                    await download_manager.download_file(url, tmp_path)

    @pytest.mark.asyncio
    async def test_concurrent_downloads(self, download_manager, tmp_path):
        urls = [
            "http://example.com/1.pdf",
            "http://example.com/2.pdf",
            "http://example.com/3.pdf"
        ]
        
        mock_response = AsyncMock()
        mock_response.headers = {"content-length": "1024"}
        mock_response.content.iter_chunked = AsyncMock(
            return_value=[b"data" * 256]
        )

        with patch("aiohttp.ClientSession") as mock_session:
            mock_session.return_value.__aenter__.return_value.get.return_value = mock_response
            mock_response.__aenter__.return_value = mock_response
            
            async with download_manager:
                results = await download_manager.download_files(urls, tmp_path)

        assert len(results) == len(urls)
        assert all(isinstance(r, Path) for r in results)

    @pytest.mark.asyncio
    async def test_download_file_retry_logic(self, download_manager, tmp_path):
        url = "http://example.com/test.pdf"
        
        with patch("aiohttp.ClientSession") as mock_session:
            mock_session.return_value.__aenter__.return_value.get.side_effect = [
                aiohttp.ClientError(),  # First attempt fails
                AsyncMock()  # Second attempt succeeds
            ]
            
            result = await download_manager.download_file(url, tmp_path)
            assert result == tmp_path / "test.pdf"