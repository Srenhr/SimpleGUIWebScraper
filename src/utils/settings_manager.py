# src/utils/settings_manager.py
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class Settings:
    last_url: str = ""
    last_output_directory: str = ""
    last_file_type: str = ".pdf"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Settings':
        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "last_url": self.last_url,
            "last_output_directory": self.last_output_directory,
            "last_file_type": self.last_file_type
        }

class SettingsManager:
    def __init__(self, settings_file: Path):
        self.settings_file = settings_file
        self.logger = logging.getLogger(__name__)

    def load_settings(self) -> Settings:
        """Load settings from file or return defaults"""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, "r", encoding='utf-8') as f:
                    data = json.load(f)
                    self.logger.debug(f"Loaded settings: {data}")
                    return Settings.from_dict(data)
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in settings file: {e}")
        except Exception as e:
            self.logger.error(f"Error loading settings: {e}")
        return Settings()

    def save_settings(self, settings: Settings) -> None:
        """Save settings to file"""
        try:
            self.settings_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.settings_file, "w", encoding='utf-8') as f:
                json.dump(settings.to_dict(), f, indent=4)
                self.logger.debug(f"Saved settings: {settings}")
        except Exception as e:
            self.logger.error(f"Error saving settings: {e}")
            raise

def save_settings(settings_file: Path, settings_data: Dict[str, Any]) -> None:
    """Helper function to save settings"""
    manager = SettingsManager(settings_file)
    settings = Settings.from_dict(settings_data)
    manager.save_settings(settings)

def load_settings(settings_file: Path) -> Dict[str, Any]:
    """Helper function to load settings"""
    manager = SettingsManager(settings_file)
    settings = manager.load_settings()
    return settings.to_dict()

__all__ = ['Settings', 'SettingsManager', 'save_settings', 'load_settings']