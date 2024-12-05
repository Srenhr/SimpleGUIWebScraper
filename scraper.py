from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

def fetch_files(url, file_types):
    """
    Fetch files of the specified type(s) from the given URL.

    Args:
        url (str): The URL of the webpage to scrape.
        file_types (list[str]): List of file extensions (e.g., [".pdf", ".docx"]).

    Returns:
        list[str]: List of absolute URLs for the files matching the given extensions.
    """
    # Validate URL
    parsed_url = urlparse(url)
    if not parsed_url.scheme or not parsed_url.netloc:
        raise ValueError(f"Invalid URL: {url}")

    # User-Agent header to avoid 403 errors
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to fetch URL {url}: {e}")

    # Parse the webpage content
    soup = BeautifulSoup(response.content, "html.parser")
    links = soup.find_all("a", href=True)

    # Collect valid file links
    valid_files = []
    for link in links:
        href = link["href"]
        # Check if the link ends with any of the specified file types
        if any(href.lower().endswith(ft.lower()) for ft in file_types):
            # Convert relative URLs to absolute URLs
            absolute_url = urljoin(url, href)
            # Ensure the absolute URL is valid
            if urlparse(absolute_url).scheme in ("http", "https"):
                valid_files.append(absolute_url)

    # Log if no files are found
    if not valid_files:
        print(f"No files of types {file_types} found at {url}.")

    return valid_files
