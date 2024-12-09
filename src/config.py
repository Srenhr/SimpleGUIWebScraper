# src/config.py
from dataclasses import dataclass, asdict
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any

@dataclass
class AppConfig:
    DEFAULT_DELAY_MIN: float = 1.0
    DEFAULT_DELAY_MAX: float = 3.0
    USER_AGENT: str = "Mozilla/5.0"
    SETTINGS_FILE: Path = Path("settings.json")
    LOG_LEVEL: int = logging.WARNING
    DOWNLOAD_CHUNK_SIZE: int = 8192
    RETRY_ATTEMPTS: int = 3
    LOG_DIR: Path = Path("logs")

    @classmethod
    def load_from_file(cls, config_path: Path = Path("config.json")) -> 'AppConfig':
        """Load configuration from JSON file"""
        try:
            if config_path.exists():
                with open(config_path, encoding='utf-8') as f:
                    config_data = json.load(f)
                    # Convert string paths to Path objects
                    if 'SETTINGS_FILE' in config_data:
                        config_data['SETTINGS_FILE'] = Path(config_data['SETTINGS_FILE'])
                    if 'LOG_DIR' in config_data:
                        config_data['LOG_DIR'] = Path(config_data['LOG_DIR'])
                    return cls(**config_data)
        except (json.JSONDecodeError, TypeError) as e:
            logging.error(f"Error loading config: {e}")
        return cls()

    def save_to_file(self, config_path: Path = Path("config.json")) -> None:
        """Save configuration to JSON file"""
        try:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                # Convert Path objects to strings for JSON serialization
                config_dict = asdict(self)
                config_dict['SETTINGS_FILE'] = str(self.SETTINGS_FILE)
                config_dict['LOG_DIR'] = str(self.LOG_DIR)
                json.dump(config_dict, f, indent=4)
        except Exception as e:
            logging.error(f"Error saving config: {e}")
            raise

    def update_log_level(self, cli_log_level: Optional[int]) -> None:
        """Update log level from command line argument"""
        if cli_log_level is not None:
            self.LOG_LEVEL = cli_log_level
            
    def validate(self) -> None:
        """Validate configuration values"""
        if self.DEFAULT_DELAY_MIN < 0:
            raise ValueError("DEFAULT_DELAY_MIN must be non-negative")
        if self.DEFAULT_DELAY_MAX < self.DEFAULT_DELAY_MIN:
            raise ValueError("DEFAULT_DELAY_MAX must be greater than DEFAULT_DELAY_MIN")
        if self.RETRY_ATTEMPTS < 1:
            raise ValueError("RETRY_ATTEMPTS must be positive")
        if self.DOWNLOAD_CHUNK_SIZE < 1:
            raise ValueError("DOWNLOAD_CHUNK_SIZE must be positive")