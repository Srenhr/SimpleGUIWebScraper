import os
import threading
import PySimpleGUI as sg
from scraper import fetch_files
from settings import save_settings, load_settings
from downloader import download_files_with_progress

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

    # Run the download task in a separate thread
    threading.Thread(target=download_task, daemon=True).start()

    while True:
        event, _ = popup.read()
        if event in (sg.WINDOW_CLOSED, "-CLOSE-"):
            break

    popup.close()


def start_gui():
    """Start the GUI application."""
    settings = load_settings()
    layout = [
        [sg.Text("Enter URL:"), sg.InputText(settings.get("last_url", ""), key="-URL-")],
        [sg.Text("Select Output Folder:"), sg.Input(settings.get("last_output_directory", ""), key="-OUTPUT-"), sg.FolderBrowse()],
        [sg.Text("Enter File Type (e.g., .pdf):"), sg.InputText(settings.get("last_file_type", ".pdf"), key="-FILETYPE-")],
        [sg.Button("Search")],
        [sg.Listbox(values=[], size=(60, 20), select_mode=sg.LISTBOX_SELECT_MODE_MULTIPLE, key="-FILELIST-")],
        [sg.Button("Download Selected")]
    ]

    window = sg.Window("Simple Web Scraper", layout)
    files = []

    while True:
        event, values = window.read()

        if event == sg.WINDOW_CLOSED:
            # Ensure that values is not None before accessing
            if values:
                print(f"Saving settings: {values.get('-URL-', '')}, Output Folder={values.get('-OUTPUT-', '')}, File Type={values.get('-FILETYPE-', '')}")
                save_settings(
                    window["-URL-"].get(),
                    window["-OUTPUT-"].get(),
                    window["-FILETYPE-"].get()
                )
            break


        if event == "Search":
            try:
                files = fetch_files(values["-URL-"], values["-FILETYPE-"])
                window["-FILELIST-"].update([os.path.basename(f) for f in files] or ["No files found."])
            except Exception as e:
                sg.popup_error(f"Error: {e}")

        if event == "Download Selected":
            selected_files = [f for f in files if os.path.basename(f) in values["-FILELIST-"]]
            if not selected_files:
                sg.popup_error("Please select at least one file.")
            else:
                progress_popup(selected_files, values["-URL-"], values["-OUTPUT-"])

    window.close()

