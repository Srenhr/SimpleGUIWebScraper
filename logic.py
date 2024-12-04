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

    results = []  # To store logs for progress_popup

    for file in files:
        file_path = os.path.join(output_directory, os.path.basename(file))

        # Check if the file already exists
        if os.path.exists(file_path):
            results.append(f"File {file_path} already exists. Skipping...")
            continue

        try:
            file_url = urllib.parse.urljoin(base_url, file)
            urllib.request.urlretrieve(file_url, file_path)
            results.append(f"Successfully downloaded {file} to {file_path}.")
        except Exception as e:
            results.append(f"Failed to download {file}: {e}")
    
    return results
