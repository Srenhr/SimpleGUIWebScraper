# Simple Web Scraper and Downloader

This is a personal hobby project – a simple web scraper and file downloader application. It allows users to fetch and download files (such as `.pdf`, `.docx`, etc.) from web pages. The application includes a GUI for easier interaction and supports settings persistence across sessions.

## Features

- Fetch files of specific types (e.g., `.pdf`, `.docx`) from a given URL.
- Download files to a specified directory.
- GUI for ease of use.
- Settings are saved between sessions (e.g., last URL, output directory, file type).
- Randomized delays between requests to avoid being blocked by websites.

## Dependencies

This project requires the following Python libraries:

- `beautifulsoup4` for parsing HTML content.
- `PySimpleGUI` for creating the graphical user interface.
- `requests` for making HTTP requests.

You can install the required dependencies by running:

```bash
pip install -r requirements.txt
