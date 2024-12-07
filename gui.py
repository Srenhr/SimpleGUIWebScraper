import os
import threading
import PySimpleGUI as sg
from selenium.webdriver.common.by import By
from scraper import fetch_files
from settings import save_settings, load_settings
from downloader import download_files_with_progress
from browser_utils import detect_default_browser, get_webdriver, ensure_driver, highlight_element
import logging

def progress_popup(files, base_url, output_directory):
    """Popup with a progress bar and log for downloading files."""
    layout = [
        [sg.Text("Downloading Files...")],
        [sg.ProgressBar(len(files), orientation='h', size=(40, 20), key="-PROGRESS-")],
        [sg.Multiline("", size=(60, 15), disabled=True, autoscroll=True, key="-LOG-")],
        [sg.Button("Close", key="-CLOSE-", disabled=True)]
    ]

    popup = sg.Window("Download Progress", layout, modal=True, finalize=True)
    progress_bar = popup["-PROGRESS-"]
    log = popup["-LOG-"]

    def update_progress(current, log_text):
        progress_bar.update(current)
        log.update(log_text)
        popup.refresh()

    def download_task():
        try:
            download_files_with_progress(base_url, files, output_directory, update_progress)
        except Exception as e:
            update_progress(len(files), f"Error: {e}")
        finally:
            popup["-CLOSE-"].update(disabled=False)

    threading.Thread(target=download_task, daemon=True).start()

    while True:
        event, _ = popup.read()
        if event in (sg.WINDOW_CLOSED, "-CLOSE-"):
            break

    popup.close()


def start_gui():
    """Start the GUI application."""
    settings = load_settings()
    driver = None  # WebDriver will be initialized on demand

    layout = [
        [sg.Text("Enter URL:"), sg.InputText(settings.get("last_url", ""), key="-URL-", expand_x=True)],
        [sg.Text("Select Output Folder:"), sg.Input(settings.get("last_output_directory", ""), key="-OUTPUT-", expand_x=True), sg.FolderBrowse()],
        [sg.Text("Enter File Type (e.g., .pdf):"), sg.InputText(settings.get("last_file_type", ".pdf"), key="-FILETYPE-", expand_x=True)],
        [sg.Button("Search")],
        [sg.Text("Files Found:")],
        [sg.Column([
            [sg.Table(values=[], headings=["File Name"], auto_size_columns=False, justification="left", key="-FILELIST-", enable_events=True, right_click_menu=["", ["Show in Browser"]], expand_x=True, expand_y=True)]
        ], expand_x=True, expand_y=True)],
        [sg.Button("Download Selected")]
    ]

    window_title = "Simple Web Scraper"
    window = sg.Window(window_title, layout, resizable=True, finalize=True)

    files = []

    while True:
        event, values = window.read()

        if event == sg.WINDOW_CLOSED:
            save_settings(
                window["-URL-"].get(),
                window["-OUTPUT-"].get(),
                window["-FILETYPE-"].get()
            )
            break

        if event == "Search":
            try:
                files = fetch_files(values["-URL-"], values["-FILETYPE-"])
                file_data = [[os.path.basename(f)] for f in files] or [["No files found."]]
                window["-FILELIST-"].update(file_data)
                logging.debug(f"Search executed for URL: {values['-URL-']} and file type: {values['-FILETYPE-']}")

            except Exception as e:
                sg.popup_error(f"Error: {e}")
                logging.error(f"Error occurred during search: {e}")

        if event == "Download Selected":
            selected_files = [files[i] for i in values["-FILELIST-"]]
            if not selected_files:
                sg.popup_error("Please select at least one file.")
            else:
                progress_popup(selected_files, values["-URL-"], values["-OUTPUT-"])
                logging.debug(f"Files selected for download: {selected_files}")

        if event == "Show in Browser":
            selected_file_index = values["-FILELIST-"][0] if values["-FILELIST-"] else None
            if selected_file_index is not None:
                if not driver:
                    driver = get_webdriver()

                driver = ensure_driver(driver)  # Ensure the driver is alive

                selected_file = files[selected_file_index]
                file_url = values["-URL-"]
                driver.get(file_url)

                try:
                    element = driver.find_element(By.PARTIAL_LINK_TEXT, os.path.basename(selected_file))
                    highlight_element(driver, element)
                    logging.debug(f"Navigating to {file_url} and highlighting element for {selected_file}")

                except Exception as e:
                    sg.popup_error(f"Error while highlighting element: {e}")
                    logging.error(f"Error occurred while interacting with the browser: {e}")


    if driver:
        driver.quit()
    window.close()
