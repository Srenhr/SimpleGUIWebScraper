import PySimpleGUI as sg
from logic import fetch_files, download_files, DEFAULT_URL, DEFAULT_OUTPUT_DIRECTORY, DEFAULT_FILE_TYPE

def start_gui():
    # Layout for the GUI
    layout = [
        [sg.Text("Enter URL:"), sg.InputText(DEFAULT_URL, key="-URL-")],
        [sg.Text("Select Output Folder:"), sg.Input(DEFAULT_OUTPUT_DIRECTORY, key="-OUTPUT-", enable_events=True), sg.FolderBrowse()],
        [sg.Text("Enter File Type (e.g., .pdf):"), sg.InputText(DEFAULT_FILE_TYPE, key="-FILETYPE-")],
        [sg.Button("Search"), sg.Button("Exit")],
        [sg.Listbox(values=[], enable_events=False, select_mode=sg.LISTBOX_SELECT_MODE_MULTIPLE, size=(60, 20), key="-FILELIST-")],
        [sg.Button("Download Selected")]
    ]

    window = sg.Window("File Downloader", layout)

    files = []
    while True:
        event, values = window.read()
        
        if event in (sg.WINDOW_CLOSED, "Exit"):
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

            try:
                download_files(values["-URL-"], selected_files, values["-OUTPUT-"])
                sg.popup("Selected files downloaded successfully!")
            except Exception as e:
                sg.popup_error(f"Error: {e}")

    window.close()
