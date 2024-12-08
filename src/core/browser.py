import webbrowser
import time
import platform
import logging
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.safari.service import Service as SafariService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager



def detect_default_browser():
    if platform.system() == "Windows":
        import winreg
        try:
            registry_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\Shell\Associations\URLAssociations\http\UserChoice")
            prog_id, _ = winreg.QueryValueEx(registry_key, "ProgId")
            if "chrome" in prog_id.lower():
                logging.info("Detected Chrome as the default browser.")
                return "chrome"
            elif "firefox" in prog_id.lower():
                logging.info("Detected Firefox as the default browser.")
                return "firefox"
            elif "edge" in prog_id.lower():
                logging.info("Detected Edge as the default browser.")
                return "edge"
            return "unknown"
        except Exception as e:
            logging.error(f"Error detecting default browser: {e}")
            return "unknown"
    elif platform.system() == "Darwin":
        try:
            browser_name = webbrowser.get().name.lower()
            logging.info(f"Detected {browser_name} as the default browser.")
            return "chrome" if "chrome" in browser_name else "firefox" if "firefox" in browser_name else "safari" if "safari" in browser_name else "unknown"
        except Exception as e:
            logging.error(f"Error detecting default browser on macOS: {e}")
            return "unknown"
    elif platform.system() == "Linux":
        try:
            import subprocess
            browser_name = subprocess.check_output(["xdg-settings", "get", "default-web-browser"]).decode("utf-8").strip()
            logging.info(f"Detected {browser_name} as the default browser.")
            return "chrome" if "chrome" in browser_name else "firefox" if "firefox" in browser_name else "unknown"
        except Exception as e:
            logging.error(f"Error detecting default browser on Linux: {e}")
            return "unknown"
    return "unknown"


def get_webdriver():
    browser_name = detect_default_browser().lower()
    if "chrome" in browser_name:
        service = ChromeService(ChromeDriverManager().install())
        logging.info("Using Chrome WebDriver.")
        return webdriver.Chrome(service=service)
    elif "firefox" in browser_name:
        service = FirefoxService(GeckoDriverManager().install())
        logging.info("Using Firefox WebDriver.")
        return webdriver.Firefox(service=service)
    elif "safari" in browser_name and platform.system() == "Darwin":
        logging.info("Using Safari WebDriver.")
        return webdriver.Safari(service=SafariService())
    else:
        service = FirefoxService(GeckoDriverManager().install())
        logging.warning("Default browser not recognized. Using Firefox WebDriver.")
        return webdriver.Firefox(service=service)


def ensure_driver(driver):
    try:
        driver.title
    except (AttributeError, Exception) as e:
        logging.error(f"Driver not working: {e}. Reinitializing driver.")
        driver.quit()
        driver = get_webdriver()
    return driver


def highlight_element(driver, element):
    driver.execute_script("arguments[0].style.border='3px solid red'", element)
    time.sleep(3)
    logging.info("Element highlighted.")

class BrowserManager:
    def __init__(self):
        self.driver = None
        
    def get_driver(self):
        if not self.driver:
            self.driver = get_webdriver()
        return ensure_driver(self.driver)
