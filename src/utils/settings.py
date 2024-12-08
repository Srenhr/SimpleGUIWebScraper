import os
import json
import logging

SETTINGS_FILE = "settings.json"

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            settings = json.load(f)
            logging.info(f"Settings loaded: {settings}")
            return settings
    else:
        logging.debug("Settings file not found, returning default settings.")
        return {"last_url": "", "last_output_directory": "", "last_file_type": ".pdf"}

def save_settings(url, output_directory, file_type):
    settings = {
        "last_url": url,
        "last_output_directory": output_directory,
        "last_file_type": file_type
    }
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)
        logging.info(f"Settings saved: {settings}")
