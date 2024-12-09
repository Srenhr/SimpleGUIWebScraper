# src/utils/logging_setup.py
import os
import platform
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler
from ..config import AppConfig

# src/utils/logging_setup.py
def setup_logging(config: AppConfig) -> None:
    """Initialize logging with performance monitoring"""
    try:
        log_dir = config.LOG_DIR
        log_dir.mkdir(parents=True, exist_ok=True)
        
        handlers = [
            RotatingFileHandler(
                filename=log_dir / "webscraper.log",
                maxBytes=5*1024*1024,
                backupCount=3,
                encoding='utf-8'
            ),
            logging.StreamHandler()
        ]
        
        for handler in handlers:
            handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            
        logging.basicConfig(
            level=config.LOG_LEVEL,
            handlers=handlers
        )
        
        # Log system info
        logging.info(f"Python version: {platform.python_version()}")
        logging.info(f"Operating system: {platform.system()} {platform.version()}")
        logging.info(f"CPU count: {os.cpu_count()}")
        
    except Exception as e:
        print(f"Failed to setup logging: {e}")
        logging.basicConfig(level=logging.WARNING)