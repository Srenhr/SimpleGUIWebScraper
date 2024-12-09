# src/core/file_downloader.py
import aiohttp
import asyncio
import logging
import random
from pathlib import Path
from typing import Dict, List, Optional, Callable
from aiohttp.client_exceptions import ClientError
from urllib.parse import urlparse, unquote
from .exceptions import DownloaderError

from ..config import AppConfig

class DownloadManager:
    def __init__(self, config: AppConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self._cache: Dict[str, Path] = {}
        self._session: Optional[aiohttp.ClientSession] = None
        self.timeout = aiohttp.ClientTimeout(total=30, connect=10)
        self.connector = aiohttp.TCPConnector(
            limit=10,
            ttl_dns_cache=300,
            use_dns_cache=True
        )

    async def __aenter__(self):
        self._session = aiohttp.ClientSession(
            timeout=self.timeout,
            connector=self.connector
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.close()

    async def _add_delay(self) -> None:
        """Add random delay between downloads"""
        delay = random.uniform(self.config.DEFAULT_DELAY_MIN, self.config.DEFAULT_DELAY_MAX)
        await asyncio.sleep(delay)

    async def download_file(
        self,
        url: str, 
        output_dir: Path,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Path:
        """Download single file with caching and progress updates"""
        if url in self._cache:
            self.logger.debug(f"Using cached file for {url}")
            return self._cache[url]

        filename = unquote(Path(url).name)
        output_path = output_dir / filename

        if output_path.exists():
            self.logger.info(f"{filename} already exists, skipping...")
            self._cache[url] = output_path
            if progress_callback:
                await progress_callback(f"{filename} already exists, skipping...")
            return output_path

        chunk_size = min(self.config.DOWNLOAD_CHUNK_SIZE * 2, 81920)
        
        for attempt in range(self.config.RETRY_ATTEMPTS):
            try:
                await self._add_delay()
                if not self._session:
                    raise DownloaderError("No active session")

                async with self._session.get(url) as response:
                    response.raise_for_status()
                    total_size = int(response.headers.get('content-length', 0))
                    
                    output_dir.mkdir(parents=True, exist_ok=True)
                    with open(output_path, 'wb') as f:
                        downloaded = 0
                        last_update = 0
                        update_frequency = max(chunk_size * 10, 102400)
                        
                        async for chunk in response.content.iter_chunked(chunk_size):
                            f.write(chunk)
                            downloaded += len(chunk)
                            
                            if progress_callback and total_size:
                                if downloaded - last_update >= update_frequency:
                                    percent = int(downloaded * 100 / total_size)
                                    await progress_callback(f"Downloading {filename}: {percent}%")
                                    last_update = downloaded

                self.logger.info(f"Successfully downloaded {filename}")
                if progress_callback:
                    await progress_callback(f"Successfully downloaded {filename}")
                
                self._cache[url] = output_path
                return output_path

            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                self.logger.error(f"Download attempt {attempt + 1} failed for {url}: {e}")
                if attempt == self.config.RETRY_ATTEMPTS - 1:
                    raise DownloaderError(
                        f"Failed to download {filename} after {self.config.RETRY_ATTEMPTS} attempts"
                    ) from e
                await asyncio.sleep(1 * (attempt + 1))

    async def download_files(
        self,
        files: List[str],
        output_dir: Path,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> List[Path]:
        """Download multiple files concurrently with progress updates"""
        self.logger.info(f"Starting download of {len(files)} files to {output_dir}")
        
        async with self:  # Use context manager for session
            tasks = [
                self.download_file(url, output_dir, progress_callback)
                for url in files
            ]
            return await asyncio.gather(*tasks)