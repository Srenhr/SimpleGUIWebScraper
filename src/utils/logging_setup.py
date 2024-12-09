# src/utils/logging_setup.py
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler
from ..config import AppConfig

def setup_logging(config: AppConfig) -> None:
    """Initialize logging configuration with rotating file handler"""
    try:
        # Create logs directory if it doesn't exist
        log_dir = config.LOG_DIR
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create formatters
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_formatter = logging.Formatter(
            '%(levelname)s: %(message)s'
        )

        # Setup rotating file handler
        file_handler = RotatingFileHandler(
            filename=log_dir / "webscraper.log",
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.DEBUG)

        # Setup console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(config.LOG_LEVEL)

        # Setup root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
            
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)

    except Exception as e:
        print(f"Failed to setup logging: {e}")
        # Fallback to basic config
        logging.basicConfig(
            level=config.LOG_LEVEL,
            format='%(levelname)s: %(message)s'
        )