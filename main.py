"""
Main entry point for the file downloader and scraper application.

This script initializes and starts the graphical user interface (GUI), allowing the user to
download files from a specified URL. It interacts with the `gui` module to display the interface
and manage the flow of downloading and scraping files.

Usage:
    Run this script to launch the GUI and start downloading files from the web.

Dependencies:
    - `requests` for making HTTP requests.
    - `BeautifulSoup` from `bs4` for parsing HTML and extracting links.
    - `urllib.parse` for URL manipulation.
    - `random` and `time` for adding random delays to requests (in the downloader).
"""
from gui import start_gui

if __name__ == "__main__":
    start_gui()
