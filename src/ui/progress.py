import threading
import PySimpleGUI as sg
from src.core import download_files_with_progress

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