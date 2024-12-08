from dataclasses import dataclass

@dataclass
class Config:
    DEFAULT_DELAY_MIN: float = 1.0
    DEFAULT_DELAY_MAX: float = 3.0
    USER_AGENT: str = "Mozilla/5.0"
    SETTINGS_FILE: str = "settings.json"