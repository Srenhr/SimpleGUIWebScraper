# src/main.py
import asyncio
import argparse
import logging
from pathlib import Path

from src.config import AppConfig
from src.ui.scraper_gui import start_gui
from src.utils.logging_setup import setup_logging

def parse_args():
    parser = argparse.ArgumentParser(description="Web Scraper")
    parser.add_argument('-d', '--debug', help="Debug mode", 
                       action="store_const", dest="loglevel",
                       const=logging.DEBUG, default=None)
    parser.add_argument('-v', '--verbose', help="Verbose output",
                       action="store_const", dest="loglevel",
                       const=logging.INFO, default=None)
    return parser.parse_args()

def main():
    args = parse_args()
    config = AppConfig.load_from_file()
    config.update_log_level(args.loglevel)
    setup_logging(config)
    
    try:
        start_gui(config)
    except Exception as e:
        logging.error(f"Application error: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()