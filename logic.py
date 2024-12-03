import requests
from bs4 import BeautifulSoup
import urllib.parse
import os
import urllib.request
import json

# File for storing user settings
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

def fetch_files(url, file_type):
    """Fetch files of the specified type from the given URL."""
    response = requests.get(url)
    response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)

    soup = BeautifulSoup(response.content, 'html.parser')
    links = soup.find_all('a', href=True)
    files = [link['href'] for link in links if link['href'].endswith(file_type)]
    
    return files

def download_files(base_url, files, output_directory):
    """Download selected files to the specified output directory."""
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    for file in files:
        file_url = urllib.parse.urljoin(base_url, file)
        file_name = os.path.join(output_directory, os.path.basename(file))
        
        if os.path.exists(file_name):
            print(f"File {file_name} already exists. Skipping download.")
            continue

        try:
            print(f"Downloading {file}...")
            urllib.request.urlretrieve(file_url, file_name)
        except Exception as e:
            print(f"Failed to download {file}: {e}")
        else:
            print(f"Saved to {file_name}")
