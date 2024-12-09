# src/core/download_manager.py
import aiohttp
import asyncio
import logging
import random
from pathlib import Path
from typing import Dict, List, Optional, Callable
from aiohttp.client_exceptions import ClientError
from urllib.parse import urlparse, unquote
from .exceptions import DownloaderError, DownloadTimeout

from ..config import AppConfig

class DownloadManager:
    def __init__(self, config: AppConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self._cache: Dict[str, Path] = {}
        self._session: Optional[aiohttp.ClientSession] = None
        self.timeout = aiohttp.ClientTimeout(total=30, connect=10)
        self.connector = None

    async def ensure_session(self) -> None:
        """Ensure session is active with lazy connector initialization"""
        if not self._session or self._session.closed:
            if not self.connector:
                self.connector = aiohttp.TCPConnector(
                    limit=10,
                    ttl_dns_cache=300,
                    use_dns_cache=True
                )
            self._session = aiohttp.ClientSession(
                timeout=self.timeout,
                connector=self.connector
            )

    async def _validate_download(self, path: Path, expected_size: int) -> bool:
        """Validate downloaded file size"""
        if not path.exists():
            return False
        if expected_size and path.stat().st_size != expected_size:
            self.logger.error(f"Size mismatch for {path}")
            return False
        return True

    async def download_file(
        self,
        url: str, 
        output_dir: Path,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Path:
        """Download single file with comprehensive error handling"""
        if url in self._cache:
            self.logger.debug(f"Using cached file for {url}")
            return self._cache[url]

        filename = unquote(Path(url).name)
        output_path = output_dir / filename
        temp_path = output_path.with_suffix('.tmp')

        # if progress_callback:
        #     await progress_callback(f"Starting download of {filename}")

        if output_path.exists():
            self.logger.info(f"{filename} already exists, skipping...")
            self._cache[url] = output_path
            if progress_callback:
                await progress_callback(f"{filename} already exists, skipping...")
            return output_path

        await self.ensure_session()
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
                    
                    if progress_callback:
                        await progress_callback(f"Starting download of {filename}")
                    
                    with open(temp_path, 'wb') as f:
                        downloaded = 0
                        async for chunk in response.content.iter_chunked(chunk_size):
                            if downloaded == 0:  # First chunk timeout
                                await asyncio.wait_for(asyncio.sleep(0), timeout=10)
                            f.write(chunk)
                            downloaded += len(chunk)

                    if await self._validate_download(temp_path, total_size):
                        temp_path.rename(output_path)
                        self._cache[url] = output_path
                        self.logger.info(f"Successfully downloaded {filename}")
                        if progress_callback:
                            await progress_callback(f"Successfully downloaded {filename}")
                        return output_path
                    else:
                        temp_path.unlink(missing_ok=True)
                        raise DownloaderError(f"Download validation failed for {filename}")

            except DownloadTimeout:
                raise
            except Exception as e:
                self.logger.error(f"Download attempt {attempt + 1} failed for {url}: {e}")
                if attempt == self.config.RETRY_ATTEMPTS - 1:
                    raise DownloaderError(f"Failed to download {filename}") from e
                await asyncio.sleep(1 * (attempt + 1))
                temp_path.unlink(missing_ok=True)

        raise DownloaderError(f"All download attempts failed for {filename}")

    async def download_files(
        self,
        files: List[str],
        output_dir: Path,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> List[Path]:
        """Download multiple files concurrently with progress updates"""
        await self.ensure_session()
        
        self.logger.info(f"Starting download of {len(files)} files to {output_dir}")
        tasks = [
            self.download_file(url, output_dir, progress_callback)
            for url in files
        ]
        
        try:
            return await asyncio.gather(*tasks)
        except Exception as e:
            self.logger.error(f"Error during concurrent downloads: {e}")
            raise

    async def _add_delay(self) -> None:
        """Add random delay between downloads"""
        delay = random.uniform(self.config.DEFAULT_DELAY_MIN, self.config.DEFAULT_DELAY_MAX)
        await asyncio.sleep(delay)

    async def cleanup(self) -> None:
        """Clean up resources"""
        if self._session and not self._session.closed:
            try:
                await self._session.close()
            except Exception as e:
                self.logger.error(f"Error closing session: {e}")