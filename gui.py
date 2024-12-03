import PySimpleGUI as sg
from logic import fetch_files, download_files, save_settings, load_settings

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

            try:
                download_files(values["-URL-"], selected_files, values["-OUTPUT-"])
                sg.popup("Selected files downloaded successfully!")
            except Exception as e:
                sg.popup_error(f"Error: {e}")

    window.close()
