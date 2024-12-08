"""
Main entry point for the file downloader and scraper application.

This script initializes and starts the graphical user interface (GUI), allowing the user to
download files from a specified URL. It interacts with the `gui` module to display the interface
and manage the flow of downloading and scraping files.
"""

from src.ui import start_gui
import argparse
import logging

def main():
    parser = argparse.ArgumentParser(
        description="File downloader and scraper application. Allows downloading files from a specified URL and scraping content."
    )
    parser.add_argument(
        '-d', '--debug',
        help="Enable debugging output with detailed statements.",
        action="store_const", dest="loglevel", const=logging.DEBUG,
        default=logging.WARNING,
    )
    parser.add_argument(
        '-v', '--verbose',
        help="Enable verbose logging for more detailed information.",
        action="store_const", dest="loglevel", const=logging.INFO,
    )
    args = parser.parse_args()    
    logging.basicConfig(level=args.loglevel,format="%(asctime)s - %(levelname)s - %(message)s")

    start_gui()

if __name__ == "__main__":
    main()
