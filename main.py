"""
Main entry point for the file downloader and scraper application.

This script initializes and starts the graphical user interface (GUI), allowing the user to
download files from a specified URL. It interacts with the `gui` module to display the interface
and manage the flow of downloading and scraping files.
"""

from gui import start_gui

if __name__ == "__main__":
    start_gui()
