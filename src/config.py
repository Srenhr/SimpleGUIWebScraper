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
            if (config_path.exists()):
                with open(config_path, encoding='utf-8') as f:
                    config_data = json.load(f)
                    for key in ['SETTINGS_FILE', 'LOG_DIR']:
                        if key in config_data:
                            config_data[key] = Path(config_data[key])
                    return cls(**config_data)
        except (json.JSONDecodeError, TypeError) as e:
            logging.error(f"Error loading config: {e}")
        return cls()

    def save_to_file(self, config_path: Path = Path("config.json")) -> None:
        """Save configuration to JSON file"""
        try:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                config_dict = asdict(self)
                for key in ['SETTINGS_FILE', 'LOG_DIR']:
                    config_dict[key] = str(config_dict[key])
                json.dump(config_dict, f, indent=4)
        except Exception as e:
            logging.error(f"Error saving config: {e}")
            raise

    def update_log_level(self, cli_log_level: Optional[int]) -> None:
        """Update log level from command line argument"""
        if cli_log_level is not None:
            self.LOG_LEVEL = cli_log_level