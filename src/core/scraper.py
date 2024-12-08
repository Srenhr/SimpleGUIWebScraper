import logging
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

def fetch_files(url, file_types):
    parsed_url = urlparse(url)
    if not parsed_url.scheme or not parsed_url.netloc:
        logging.error(f"Invalid URL: {url}")
        raise ValueError(f"Invalid URL: {url}")

    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        logging.info(f"Successfully fetched URL: {url}")
    except requests.RequestException as e:
        logging.error(f"Failed to fetch URL {url}: {e}")
        raise RuntimeError(f"Failed to fetch URL {url}: {e}")

    soup = BeautifulSoup(response.content, "html.parser")
    links = soup.find_all("a", href=True)

    valid_files = []
    for link in links:
        href = link["href"]
        if any(href.lower().endswith(ft.lower()) for ft in file_types):
            absolute_url = urljoin(url, href)
            if urlparse(absolute_url).scheme in ("http", "https"):
                valid_files.append(absolute_url)

    if not valid_files:
        logging.warning(f"No files of types {file_types} found at {url}.")
    else:
        logging.info(f"Found {len(valid_files)} file(s) of types {file_types} at {url}.")

    return valid_files
