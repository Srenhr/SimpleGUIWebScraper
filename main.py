"""
Main entry point for the file downloader and scraper application.

This script initializes and starts the graphical user interface (GUI), allowing the user to
download files from a specified URL. It interacts with the `gui` module to display the interface
and manage the flow of downloading and scraping files.
"""

from gui import start_gui
import argparse

def main():
    # Parse command-line arguments to enable developer mode
    parser = argparse.ArgumentParser(description="Simple Web Scraper and Downloader")
    parser.add_argument('--developer', action='store_true', help="Enable developer mode for inspecting HTML elements.")
    args = parser.parse_args()

    # Pass developer_mode to the GUI or scraper
    start_gui(developer_mode=args.developer)

if __name__ == "__main__":
    main()
