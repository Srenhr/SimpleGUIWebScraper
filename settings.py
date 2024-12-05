import os
import json

SETTINGS_FILE = "settings.json"

def load_settings():
    """Load user settings from a JSON file."""
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    return {"last_url": "", "last_output_directory": "", "last_file_type": ".pdf"}

def save_settings(url, output_directory, file_type):
    """Save user settings to a JSON file."""
    settings = {
        "last_url": url,
        "last_output_directory": output_directory,
        "last_file_type": file_type
    }
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)