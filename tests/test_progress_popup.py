
import pytest
import asyncio
from unittest.mock import patch, Mock
from src.ui.progress_popup import ProgressPopup, create_progress_popup

@pytest.fixture
def progress_popup():
    return ProgressPopup(total=5, success_message="Downloaded", skip_message="Skipped")

@pytest.mark.asyncio
async def test_progress_popup_update(progress_popup):
    with patch.object(progress_popup, '_create_window', return_value=Mock()) as mock_create_window:
        progress_popup.window = mock_create_window()
        progress_popup.progress_bar = progress_popup.window["-PROGRESS-"]
        progress_popup.log = progress_popup.window["-LOG-"]

        await progress_popup.update("Downloaded file1.pdf")
        assert progress_popup.current == 1
        progress_popup.progress_bar.update_bar.assert_called_with(1, 5)
        progress_popup.log.print.assert_called_with("Downloaded file1.pdf")

        await progress_popup.update("Skipped file2.pdf")
        assert progress_popup.current == 2
        progress_popup.progress_bar.update_bar.assert_called_with(2, 5)
        progress_popup.log.print.assert_called_with("Skipped file2.pdf")

@pytest.mark.asyncio
async def test_progress_popup_wait_for_close(progress_popup):
    with patch.object(progress_popup, '_create_window', return_value=Mock()) as mock_create_window:
        progress_popup.window = mock_create_window()
        progress_popup.window.read.return_value = (None, None)

        task = asyncio.create_task(progress_popup.wait_for_close())
        await asyncio.sleep(0.1)
        progress_popup.close()
        await task

        assert progress_popup.closed

def test_progress_popup_close(progress_popup):
    with patch.object(progress_popup, '_create_window', return_value=Mock()) as mock_create_window:
        progress_popup.window = mock_create_window()
        progress_popup.close()
        progress_popup.window.close.assert_called_once()
        assert progress_popup.closed

def test_create_progress_popup():
    popup = create_progress_popup(total=5, success_message="Downloaded", skip_message="Skipped")
    assert isinstance(popup, ProgressPopup)
    assert popup.total == 5
    assert popup.success_message == "Downloaded"
    assert popup.skip_message == "Skipped"