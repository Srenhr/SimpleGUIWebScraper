# src/ui/scraper_gui.py
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
import PySimpleGUI as sg
from selenium.webdriver.common.by import By

from ..config import AppConfig
from ..core.browser_manager import BrowserManager
from ..core.scraper_service import ScraperService
from ..core.file_downloader import download_files
from ..utils.settings_manager import save_settings, load_settings
from .progress_popup import create_progress_popup

class WebScraperGUI:
    def __init__(self, config: AppConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.browser_manager = BrowserManager(config)
        self.scraper_service = ScraperService(config, self.browser_manager)
        self.settings = load_settings(config.SETTINGS_FILE)
        self.window: Optional[sg.Window] = None
        self.files: List[str] = []

    def create_layout(self) -> list:
        return [
            [sg.Text("Enter URL:"), 
             sg.InputText(self.settings.get("last_url", ""), key="-URL-", expand_x=True)],
            [sg.Text("Select Output Folder:"), 
             sg.Input(self.settings.get("last_output_directory", ""), key="-OUTPUT-"), 
             sg.FolderBrowse()],
            [sg.Text("File Type:"), 
             sg.InputText(self.settings.get("last_file_type", ".pdf"), key="-FILETYPE-")],
            [sg.Button("Search")],
            [sg.Text("Files Found:")],
            [sg.Column([
                [sg.Table(
                    values=[], 
                    headings=["File Name"], 
                    auto_size_columns=False,
                    justification="left",
                    key="-FILELIST-",
                    enable_events=True,
                    expand_x=True,
                    expand_y=True,
                    right_click_menu=["", ["Show in Browser"]]
                )]
            ], expand_x=True, expand_y=True)],
            [sg.Button("Download Selected")]
        ]

    async def handle_show_in_browser(self, values: Dict[str, Any]) -> None:
        selected_indices = values["-FILELIST-"]
        if not selected_indices:
            return
            
        selected_file = self.files[selected_indices[0]]
        
        try:
            # Only initialize browser when needed
            driver = self.browser_manager.get_driver()
            driver.get(values["-URL-"])
            element = driver.find_element(By.PARTIAL_LINK_TEXT, Path(selected_file).name)
            driver.execute_script("arguments[0].style.border='3px solid red'", element)
            #await asyncio.sleep(3)
            
            # Cleanup browser after use
            #self.browser_manager.cleanup()
            
        except Exception as e:
            self.logger.error(f"Error showing in browser: {e}")
            sg.popup_error(f"Error highlighting element: {e}")
            self.browser_manager.cleanup()

    async def handle_search(self, values: Dict[str, Any]) -> None:
        url = values["-URL-"]
        file_type = values["-FILETYPE-"]

        try:
            self.window["-FILELIST-"].update([["Searching..."]])
            self.files = self.scraper_service.fetch_files(url, [file_type])
            
            if not self.files:
                self.window["-FILELIST-"].update([["No files found."]])
                return

            file_data = [[Path(f).name] for f in self.files]
            self.window["-FILELIST-"].update(file_data)

        except Exception as e:
            self.logger.error(f"Error during search: {e}", exc_info=True)
            sg.popup_error(f"An error occurred: {str(e)}")

    async def handle_download(self, values: Dict[str, Any]) -> None:
        selected_indices = values["-FILELIST-"]
        if not selected_indices:
            sg.popup_error("Please select at least one file.")
            return

        output_dir = Path(values["-OUTPUT-"])
        selected_files = [self.files[i] for i in selected_indices]
        
        try:
            progress = create_progress_popup(len(selected_files))
            await download_files(selected_files, output_dir, self.config, progress.update)
            progress.close()

            # save_settings(self.config.SETTINGS_FILE, {
            #     "last_url": values["-URL-"],
            #     "last_output_directory": str(output_dir),
            #     "last_file_type": values["-FILETYPE-"]
            # })

        except Exception as e:
            self.logger.error(f"Error during download: {e}", exc_info=True)
            sg.popup_error(f"An error occurred: {str(e)}")

    async def run(self) -> None:
        self.window = sg.Window(
            'Web Scraper', 
            self.create_layout(),
            resizable=True,
            finalize=True
        )

        try:
            while True:
                event, values = self.window.read(timeout=100)
                
                if event == sg.WIN_CLOSED:
                    save_settings(self.config.SETTINGS_FILE, {
                        "last_url": self.window["-URL-"].get(),
                        "last_output_directory": self.window["-OUTPUT-"].get(),
                        "last_file_type": self.window["-FILETYPE-"].get()
                    })
                    break
                
                elif event == "Search":
                    await self.handle_search(values)
                    
                elif event == "Download Selected":
                    await self.handle_download(values)
                    
                elif event == "Show in Browser":
                    await self.handle_show_in_browser(values)

        finally:
            self.browser_manager.cleanup()
            if self.window:
                self.window.close()

def start_gui(config: AppConfig) -> None:
    gui = WebScraperGUI(config)
    asyncio.run(gui.run())