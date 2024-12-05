"""
Main entry point for the file downloader and scraper application.

This script initializes and starts the graphical user interface (GUI), allowing the user to
download files from a specified URL. It interacts with the `gui` module to display the interface
and manage the flow of downloading and scraping files.

Usage:
    Run this script to launch the GUI and start downloading files from the web.

Dependencies:
    - requests: For making HTTP requests.
    - bs4 (BeautifulSoup): For parsing HTML content.
    - os: For file system operations.
    - urllib.parse: For URL handling.
    - time: For adding delays.
    - random: For generating random numbers.
    - json: For saving and loading settings.
"""

from gui import start_gui

if __name__ == "__main__":
    start_gui()
