# src/ui/progress_popup.py
import asyncio
import logging
from dataclasses import dataclass
import PySimpleGUI as sg

@dataclass
class ProgressState:
    window: sg.Window
    progress_bar: sg.ProgressBar
    log: sg.Multiline
    current: int = 0
    total: int = 0

class ProgressPopup:
    def __init__(self, total: int, success_message: str, skip_message: str):
        self.total = total
        self.current = 0
        self.success_message = success_message
        self.skip_message = skip_message
        self.logger = logging.getLogger(__name__)
        self.window = self._create_window()
        self.progress_bar = self.window["-PROGRESS-"]
        self.log = self.window["-LOG-"]
        self.closed = False

    def _create_window(self) -> sg.Window:
        """Create progress window with error handling"""
        try:
            layout = [
                [sg.Text("Downloading Files...")],
                [sg.ProgressBar(
                    self.total, 
                    orientation='h',
                    size=(40, 20),
                    key="-PROGRESS-"
                )],
                [sg.Multiline(
                    "", 
                    size=(60, 15),
                    disabled=True,
                    autoscroll=True,
                    key="-LOG-",
                    background_color='white',
                    text_color='black'
                )],
                [sg.Button("Close", key="-CLOSE-", disabled=True)]
            ]
            return sg.Window(
                "Download Progress",
                layout,
                modal=True,
                finalize=True,
                keep_on_top=True
            )
        except Exception as e:
            self.logger.error(f"Error creating progress window: {e}")
            raise

    async def update(self, message: str) -> None:
        """Update progress bar and log with error handling"""
        if self.closed:
            return

        try:
            # Update progress when a file is complete
            if self.success_message in message or self.skip_message in message:
                self.current += 1
                self.progress_bar.update_bar(self.current, self.total)
            
            # Print all messages
            self.log.print(message)
            
            # Process events
            event, _ = self.window.read(timeout=1)
            if event in (sg.WIN_CLOSED, "-CLOSE-"):
                self.close()
                return
                
            # When all files are processed
            if self.current >= self.total:
                #self.log.print("\nAll files processed successfully!")
                self.window["-CLOSE-"].update(disabled=False)
            
            self.window.refresh()
            await asyncio.sleep(0.001)

        except Exception as e:
            self.logger.error(f"Error updating progress: {e}")
            self.close()

    async def wait_for_close(self) -> None:
        """Wait until the user clicks the close button"""
        while not self.closed:
            event, _ = self.window.read(timeout=100)
            if event in (sg.WIN_CLOSED, "-CLOSE-"):
                self.close()
                break
            await asyncio.sleep(0.1)

    def close(self) -> None:
        """Close progress window with cleanup"""
        if not self.closed:
            try:
                if self.window:
                    self.window.close()
            except Exception as e:
                self.logger.error(f"Error closing progress window: {e}")
            finally:
                self.window = None
                self.closed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

def create_progress_popup(total: int, success_message: str, skip_message: str) -> ProgressPopup:
    """Factory function to create progress popup"""
    try:
        return ProgressPopup(total, success_message, skip_message)
    except Exception as e:
        logging.error(f"Failed to create progress popup: {e}")
        raise