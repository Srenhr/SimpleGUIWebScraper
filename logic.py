import requests
from bs4 import BeautifulSoup
import urllib.parse
import os
import urllib.request
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Default values
DEFAULT_URL = os.getenv("URL", "")
DEFAULT_OUTPUT_DIRECTORY = os.getenv("DEFAULT_OUTPUT_DIRECTORY", "downloads")
DEFAULT_FILE_TYPE = os.getenv("DEFAULT_FILE_TYPE", ".pdf")

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
