import os
import threading
import webbrowser
import PySimpleGUI as sg
from scraper import fetch_files
from settings import save_settings, load_settings
from downloader import download_files_with_progress
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.safari.service import Service as SafariService
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
import time
import platform

def detect_default_browser():
    """Detect the system's default browser."""
    if platform.system() == "Windows":
        import winreg
        try:
            registry_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\Shell\Associations\URLAssociations\http\UserChoice")
            prog_id, _ = winreg.QueryValueEx(registry_key, "ProgId")
            if "chrome" in prog_id.lower():
                return "chrome"
            elif "firefox" in prog_id.lower():
                return "firefox"
            elif "edge" in prog_id.lower():
                return "edge"
            return "unknown"
        except Exception:
            return "unknown"
    elif platform.system() == "Darwin":  # macOS
        try:
            # Check the default browser on macOS using the 'open' command
            browser_name = webbrowser.get().name.lower()
            if "chrome" in browser_name:
                return "chrome"
            elif "firefox" in browser_name:
                return "firefox"
            elif "safari" in browser_name:
                return "safari"
            return "unknown"
        except Exception:
            return "unknown"
    elif platform.system() == "Linux":
        try:
            # On Linux, try getting the default browser from the 'xdg-settings' command
            import subprocess
            browser_name = subprocess.check_output(["xdg-settings", "get", "default-web-browser"]).decode("utf-8").strip()
            if "chrome" in browser_name:
                return "chrome"
            elif "firefox" in browser_name:
                return "firefox"
            return "unknown"
        except Exception:
            return "unknown"
    return "unknown"


def get_webdriver():
    """Return a Selenium WebDriver based on the system's default browser."""
    browser_name = detect_default_browser().lower()

    if "chrome" in browser_name:
        service = ChromeService(ChromeDriverManager().install())
        return webdriver.Chrome(service=service)
    elif "firefox" in browser_name:
        service = FirefoxService(GeckoDriverManager().install())
        return webdriver.Firefox(service=service)
    elif "safari" in browser_name and platform.system() == "Darwin":
        return webdriver.Safari(service=SafariService())
    else:
        # If the browser is not recognized, fallback to Firefox
        service = FirefoxService(GeckoDriverManager().install())
        return webdriver.Firefox(service=service)


def ensure_driver(driver):
    """Check if the driver is closed and reinitialize if necessary."""
    try:
        driver.title  # Attempt to fetch the title to check if the driver is alive
    except (AttributeError, Exception):
        # If an exception occurs, the driver is likely closed
        driver.quit()  # Close the old driver if it's closed
        driver = get_webdriver()  # Reinitialize the driver
    return driver


def highlight_element(driver, element):
    """Highlight the HTML element using Selenium."""
    driver.execute_script("arguments[0].style.border='3px solid red'", element)
    time.sleep(3)  # Pause to allow the highlight to be visible


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


def start_gui(developer_mode):
    """Start the GUI application."""
    settings = load_settings()
    driver = None  # WebDriver will be initialized on demand

    layout = [
        [sg.Text("Enter URL:"), sg.InputText(settings.get("last_url", ""), key="-URL-", expand_x=True)],
        [sg.Text("Select Output Folder:"), sg.Input(settings.get("last_output_directory", ""), key="-OUTPUT-", expand_x=True), sg.FolderBrowse()],
        [sg.Text("Enter File Type (e.g., .pdf):"), sg.InputText(settings.get("last_file_type", ".pdf"), key="-FILETYPE-", expand_x=True)],
        [sg.Button("Search")],  # Moved Search button above "Files Found"
        [sg.Text("Files Found:")],
        [sg.Column([
            [sg.Table(values=[], headings=["File Name"], auto_size_columns=False, justification="left", key="-FILELIST-", enable_events=True, right_click_menu=["", ["Show in Browser"]], expand_x=True, expand_y=True)]
        ], expand_x=True, expand_y=True)],
        [sg.Button("Download Selected")]
    ]

    window_title = "Simple Web Scraper - Developer Mode" if developer_mode else "Simple Web Scraper"
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
            except Exception as e:
                sg.popup_error(f"Error: {e}")

        if event == "Download Selected":
            selected_files = [files[i] for i in values["-FILELIST-"]]
            if not selected_files:
                sg.popup_error("Please select at least one file.")
            else:
                progress_popup(selected_files, values["-URL-"], values["-OUTPUT-"])

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
                except Exception as e:
                    sg.popup_error(f"Error while highlighting element: {e}")

    if driver:
        driver.quit()
    window.close()
