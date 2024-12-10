import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
import PySimpleGUI as sg
from selenium.webdriver.common.by import By
from ..config import AppConfig
from ..core.browser_manager import BrowserManager
from ..core.scraper_service import ScraperService
from ..core.download_manager import DownloadManager
from ..utils.settings_manager import save_settings, load_settings
from ..utils.exceptions import log_and_raise, BrowserError, ScraperError, DownloaderError
from .progress_popup import create_progress_popup

class WebScraperGUI:
    def __init__(self, config: AppConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.browser_manager = BrowserManager(config)
        self.scraper_service = ScraperService(config, self.browser_manager)
        self.download_manager = DownloadManager(config)
        self.settings = load_settings(self.config.SETTINGS_FILE)
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

    async def handle_search(self, values: Dict[str, Any]) -> None:
        url = values["-URL-"]
        file_type = values["-FILETYPE-"]

        try:
            self.window["-FILELIST-"].update([["Searching..."]])
            self.files = await self.scraper_service.fetch_files(url, [file_type])
            
            if not self.files:
                self.window["-FILELIST-"].update([["No files found."]])
                return

            file_data = [[Path(f).name] for f in self.files]
            self.window["-FILELIST-"].update(file_data)

        except ScraperError as e:
            log_and_raise(self.logger, f"Scraping error: {e}", ScraperError, e)
            sg.popup_error(f"Error during search: {str(e)}")
            self.window["-FILELIST-"].update([["Error occurred"]])
        except Exception as e:
            log_and_raise(self.logger, f"Unexpected error during search: {e}", Exception, e)
            sg.popup_error(f"An unexpected error occurred: {str(e)}")
            self.window["-FILELIST-"].update([["Error occurred"]])

    async def handle_download(self, values: Dict[str, Any]) -> None:
        selected_indices = values["-FILELIST-"]
        if not selected_indices:
            sg.popup_error("Please select at least one file.")
            return

        output_dir = Path(values["-OUTPUT-"])
        selected_files = [self.files[i] for i in selected_indices]
        
        try:
            progress = create_progress_popup(
                len(selected_files),
                self.download_manager.SUCCESS_MESSAGE,
                self.download_manager.SKIP_MESSAGE
            )
            await self.download_manager.download_files(
                selected_files, 
                output_dir,
                progress.update
            )
            await progress.wait_for_close()

        except DownloaderError as e:
            log_and_raise(self.logger, f"Download error: {e}", DownloaderError, e)
            sg.popup_error(f"Error during download: {str(e)}")
        except Exception as e:
            log_and_raise(self.logger, f"Unexpected error during download: {e}", Exception, e)
            sg.popup_error(f"An unexpected error occurred: {str(e)}")

    async def handle_show_in_browser(self, values: Dict[str, Any]) -> None:
        selected_indices = values["-FILELIST-"]
        if not selected_indices:
            return
            
        selected_file = self.files[selected_indices[0]]
        
        try:
            driver = self.browser_manager.get_driver()
            driver.get(values["-URL-"])
            element = driver.find_element(By.PARTIAL_LINK_TEXT, Path(selected_file).name)
            driver.execute_script("arguments[0].style.border='3px solid red'", element)
        except BrowserError as e:
            log_and_raise(self.logger, f"Browser error: {e}", BrowserError, e)
            sg.popup_error(f"Browser error: {str(e)}")
            self.browser_manager.cleanup()
        except Exception as e:
            log_and_raise(self.logger, f"Unexpected error in browser: {e}", Exception, e)
            sg.popup_error(f"An unexpected error occurred: {str(e)}")
            self.browser_manager.cleanup()

    async def run(self) -> None:
        await self.download_manager.ensure_session()
        
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

        except Exception as e:
            self.logger.error(f"Fatal error in GUI: {e}", exc_info=True)
            sg.popup_error(f"A fatal error occurred: {str(e)}")
        finally:
            await self.download_manager.cleanup()
            self.browser_manager.cleanup()
            if self.window:
                self.window.close()

def start_gui(config: AppConfig) -> None:
    gui = WebScraperGUI(config)
    asyncio.run(gui.run())