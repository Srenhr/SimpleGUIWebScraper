# src/ui/progress_popup.py
import asyncio
import PySimpleGUI as sg
from dataclasses import dataclass
from typing import Callable, Optional

@dataclass
class ProgressState:
    window: sg.Window
    progress_bar: sg.ProgressBar
    log: sg.Multiline
    current: int = 0
    total: int = 0

class ProgressPopup:
    def __init__(self, total: int):
        self.total = total
        self.current = 0
        self.window = self._create_window()
        self.progress_bar = self.window["-PROGRESS-"]
        self.log = self.window["-LOG-"]

    def _create_window(self) -> sg.Window:
        layout = [
            [sg.Text("Downloading Files...")],
            [sg.ProgressBar(self.total, orientation='h', size=(40, 20), key="-PROGRESS-")],
            [sg.Multiline("", size=(60, 15), disabled=True, autoscroll=True, key="-LOG-")],
            [sg.Button("Close", key="-CLOSE-", disabled=True)]
        ]
        return sg.Window("Download Progress", layout, modal=True, finalize=True)

    async def update(self, message: str) -> None:
        """Update progress bar and log with new message"""
        self.current += 1
        self.progress_bar.update(self.current)
        self.log.print(message)
        
        # Process events more frequently
        event, _ = self.window.read(timeout=1)  # Reduced timeout
        if event in (sg.WIN_CLOSED, "-CLOSE-"):
            self.close()
            return
            
        if self.current >= self.total:
            self.window["-CLOSE-"].update(disabled=False)
        
        # Force window refresh
        self.window.refresh()
        await asyncio.sleep(0.001)  # Smaller sleep interval

    def close(self) -> None:
        """Close the progress window"""
        if self.window:
            self.window.close()
            self.window = None

def create_progress_popup(total: int) -> ProgressPopup:
    """Factory function to create progress popup"""
    return ProgressPopup(total)