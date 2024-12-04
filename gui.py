import urllib.request
import os
import PySimpleGUI as sg
from logic import fetch_files, download_files, save_settings, load_settings

def progress_popup(files, base_url, output_directory):
    """Popup with a progress bar and log for downloading files."""
    layout = [
        [sg.Text("Downloading Files...")],
        [sg.ProgressBar(len(files), orientation='h', size=(40, 20), key="-PROGRESS-")],
        [sg.Multiline("", size=(60, 15), disabled=True, autoscroll=True, key="-LOG-")],
        [sg.Button("Close", key="-CLOSE-", disabled=True)]
    ]

    popup = sg.Window("Download Progress", layout, modal=True, finalize=True)  # Added finalize=True
    progress_bar = popup["-PROGRESS-"]
    log = popup["-LOG-"]

    logs = []
    for i, file in enumerate(files):
        file_url = urllib.parse.urljoin(base_url, file)
        file_name = os.path.join(output_directory, os.path.basename(file))

        # Check if file exists
        if os.path.exists(file_name):
            message = f"File {file_name} already exists. Skipping download."
            logs.append(message)
        else:
            try:
                urllib.request.urlretrieve(file_url, file_name)
                message = f"Downloaded {file_name}"
                logs.append(message)
            except Exception as e:
                message = f"Failed to download {file_name}: {e}"
                logs.append(message)

        # Update the popup's progress bar and log
        current_log = "\n".join(logs)
        log.update(current_log)
        progress_bar.update(i + 1)
        popup.refresh()

    # Enable the "Close" button after all downloads are complete
    popup["-CLOSE-"].update(disabled=False)
    popup.read(close=True)


def start_gui():
    # Load previous session settings
    settings = load_settings()
    last_url = settings.get("last_url", "")
    last_output_directory = settings.get("last_output_directory", "")
    last_file_type = settings.get("last_file_type", ".pdf")

    # Layout for the GUI
    layout = [
        [sg.Text("Enter URL:"), sg.InputText(last_url, key="-URL-")],
        [sg.Text("Select Output Folder:"), sg.Input(last_output_directory, key="-OUTPUT-", enable_events=True), sg.FolderBrowse(initial_folder=last_output_directory)],
        [sg.Text("Enter File Type (e.g., .pdf):"), sg.InputText(last_file_type, key="-FILETYPE-")],
        [sg.Button("Search")],
        [sg.Listbox(values=[], enable_events=False, select_mode=sg.LISTBOX_SELECT_MODE_MULTIPLE, size=(60, 20), key="-FILELIST-")],
        [sg.Button("Download Selected")]
    ]

    window = sg.Window("File Downloader", layout)

    files = []
    while True:
        event, values = window.read()

        if event == sg.WINDOW_CLOSED:
            # Save settings to JSON on exit
            save_settings(
                window["-URL-"].get(),
                window["-OUTPUT-"].get(),
                window["-FILETYPE-"].get()
            )
            break

        if event == "Search":
            url = values["-URL-"]
            file_type = values["-FILETYPE-"]
            output_folder = values["-OUTPUT-"]

            if not url or not output_folder:
                sg.popup_error("Please provide both a URL and an output folder!")
                continue

            try:
                files = fetch_files(url, file_type)
                if files:
                    window["-FILELIST-"].update(files)
                else:
                    sg.popup("No files found for the specified file type.")
            except Exception as e:
                sg.popup_error(f"Error: {e}")

        if event == "Download Selected":
            selected_files = values["-FILELIST-"]
            if not selected_files:
                sg.popup_error("Please select at least one file to download.")
                continue

            # try:
            #     download_files(values["-URL-"], selected_files, values["-OUTPUT-"])
            #     sg.popup("Selected files downloaded successfully!")
            # except Exception as e:
            #     sg.popup_error(f"Error: {e}")

            try:
                # Show progress bar popup
                progress_popup(selected_files, values["-URL-"], values["-OUTPUT-"])
                # sg.popup("Selected files downloaded successfully!")
            except Exception as e:
                sg.popup_error(f"Error: {e}")

    window.close()