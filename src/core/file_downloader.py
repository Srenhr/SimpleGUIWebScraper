# src/core/file_downloader.py
import aiohttp
import asyncio
import logging
import random
from pathlib import Path
from typing import List, Optional, Callable
from aiohttp.client_exceptions import ClientError
from urllib.parse import urlparse, unquote

from ..config import AppConfig

async def add_delay(config: AppConfig) -> None:
    """Add random delay between downloads"""
    delay = random.uniform(config.DEFAULT_DELAY_MIN, config.DEFAULT_DELAY_MAX)
    await asyncio.sleep(delay)

async def download_file(
    url: str, 
    output_dir: Path,
    config: AppConfig,
    progress_callback: Optional[Callable[[str], None]] = None
) -> None:
    """Download a single file with progress updates"""
    logger = logging.getLogger(__name__)
    filename = unquote(Path(url).name)
    output_path = output_dir / filename

    # Skip if file exists
    if output_path.exists():
        logger.info(f"{filename} already exists, skipping...")
        if progress_callback:
            await progress_callback(f"{filename} already exists, skipping...")
        return

    update_frequency = max(1, config.DOWNLOAD_CHUNK_SIZE * 10)  # Update every 10 chunks minimum
    
    for attempt in range(config.RETRY_ATTEMPTS):
        try:
            await add_delay(config)
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    total_size = int(response.headers.get('content-length', 0))
                    
                    output_dir.mkdir(parents=True, exist_ok=True)
                    with open(output_path, 'wb') as f:
                        downloaded = 0
                        last_update = 0
                        
                        async for chunk in response.content.iter_chunked(config.DOWNLOAD_CHUNK_SIZE):
                            f.write(chunk)
                            downloaded += len(chunk)
                            
                            # Update progress more frequently
                            if progress_callback and total_size:
                                current_time = asyncio.get_event_loop().time()
                                if downloaded - last_update >= update_frequency:
                                    percent = int(downloaded * 100 / total_size)
                                    await progress_callback(f"Downloading {filename}: {percent}%")
                                    last_update = downloaded
                                    await asyncio.sleep(0.001)  # Allow GUI updates
            
            logger.info(f"Successfully downloaded {filename}")
            if progress_callback:
                await progress_callback(f"Successfully downloaded {filename}")
            return

        except ClientError as e:
            logger.error(f"Download attempt {attempt + 1} failed for {url}: {e}")
            if attempt == config.RETRY_ATTEMPTS - 1:
                if progress_callback:
                    await progress_callback(f"Failed to download {filename}: {e}")
                raise
            await asyncio.sleep(1)

async def download_files(
    files: List[str],
    output_dir: Path,
    config: AppConfig,
    progress_callback: Optional[Callable[[str], None]] = None
) -> None:
    """Download multiple files with progress updates"""
    logger = logging.getLogger(__name__)
    logger.info(f"Starting download of {len(files)} files to {output_dir}")
    
    tasks = []
    for url in files:
        task = asyncio.create_task(
            download_file(url, output_dir, config, progress_callback)
        )
        tasks.append(task)
    
    await asyncio.gather(*tasks, return_exceptions=True)