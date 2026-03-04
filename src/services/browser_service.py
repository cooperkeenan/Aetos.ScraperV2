"""
Stealth browser service with proxy support
Supports both local development and Docker environments
"""

import logging
import os
import subprocess
import time
from typing import Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait

from ..core.settings import Settings
from .proxy_service import ProxyService

logger = logging.getLogger(__name__)


class BrowserService:
    """
    Manages Chrome instances with stealth and proxy support
    Works in both local and Docker environments
    """

    def __init__(self, settings: Settings, proxy_service: ProxyService = None):
        self.settings = settings
        self.proxy_service = proxy_service
        self.driver: Optional[webdriver.Chrome] = None
        self._proxy_env_backup = {}

        # Only setup Docker environment if actually in Docker
        if settings.is_docker:
            logger.info("[Browser] Running in Docker mode")
            self._ensure_docker_environment()
        else:
            logger.info("[Browser] Running in local development mode")

    def _ensure_docker_environment(self):
        """Set up virtual display and test binaries (Docker only)"""
        if not os.environ.get("DISPLAY"):
            os.environ["DISPLAY"] = ":99"

        self._start_xvfb()
        self._test_binaries()

    def _start_xvfb(self):
        """Start virtual display (Docker only)"""
        try:
            subprocess.run(["pgrep", "Xvfb"], check=True, capture_output=True)
            logger.info("[Browser] Xvfb already running")
        except subprocess.CalledProcessError:
            logger.info("[Browser] Starting Xvfb...")
            subprocess.Popen(
                ["Xvfb", ":99", "-screen", "0", "1920x1080x16"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            time.sleep(2)

    def _test_binaries(self):
        """Test Chrome and ChromeDriver binaries (Docker only)"""
        try:
            # Test Chrome
            result = subprocess.run(
                ["/opt/chrome-linux64/chrome", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                logger.info("[Browser] Chrome: %s", result.stdout.strip())
            else:
                raise RuntimeError("Chrome binary test failed")

            # Test ChromeDriver
            result = subprocess.run(
                ["/usr/bin/chromedriver", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                logger.info("[Browser] ChromeDriver: %s", result.stdout.strip())
            else:
                raise RuntimeError("ChromeDriver binary test failed")

        except Exception as e:
            raise RuntimeError(f"Binary test failed: {e}")

    def create_driver(self) -> webdriver.Chrome:
        """Create Chrome driver with stealth and proxy"""
        logger.info("[Browser] Creating stealth Chrome driver...")

        # Clear proxy env vars that interfere with Chrome startup
        self._proxy_env_backup = self._clear_proxy_env()

        try:
            options = self._get_stealth_options()
            service = self._get_chrome_service()

            self.driver = webdriver.Chrome(service=service, options=options)

            # Configure timeouts
            self.driver.implicitly_wait(10)
            self.driver.set_page_load_timeout(30)

            # Apply stealth patches
            self._apply_stealth_patches()

            # Test proxy if configured
            if self.proxy_service and self.proxy_service.is_configured():
                proxy_url = self.proxy_service.get_proxy_url() if self.proxy_service and self.proxy_service.is_configured() else None
                if proxy_url:
                    options.add_argument(f"--proxy-server={proxy_url}")
                    logger.info(f"[Browser] Proxy configured for Chrome")
                ip = self.proxy_service.test_proxy(proxy_url)
                if not ip:
                    logger.warning("[Browser] ⚠️ Proxy test failed, continuing anyway")

            logger.info("[Browser] ✅ Stealth Chrome driver ready")
            return self.driver

        except Exception as e:
            self._restore_proxy_env()
            raise RuntimeError(f"Failed to create driver: {e}")
        finally:
            # Always restore proxy env vars
            self._restore_proxy_env()

    def _get_stealth_options(self) -> Options:
        """Get Chrome options with maximum stealth"""
        options = Options()

        if self.settings.is_docker:
            # Docker-specific options
            options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.binary_location = "/opt/chrome-linux64/chrome"
        else:
            # Local development - use system Chrome
            if self.settings.browser_headless:
                options.add_argument("--headless=new")

        # Common options
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--start-maximized")

        # Maximum stealth options
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        options.add_argument("--disable-default-apps")
        options.add_argument("--disable-sync")
        options.add_argument("--disable-translate")
        options.add_argument("--hide-scrollbars")
        options.add_argument("--mute-audio")
        options.add_argument("--no-first-run")
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-backgrounding-occluded-windows")
        options.add_argument("--disable-renderer-backgrounding")
        options.add_argument("--disable-features=TranslateUI")
        options.add_argument("--disable-ipc-flooding-protection")

        # User agent
        options.add_argument(f"--user-agent={self.settings.browser_user_agent}")

        # Experimental options for stealth
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        return options

    def _get_chrome_service(self) -> Service:
        """Get Chrome service"""
        if self.settings.is_docker:
            # Docker uses fixed path
            return Service(
                executable_path="/usr/bin/chromedriver", log_output=subprocess.DEVNULL
            )
        else:
            # Local development - chromedriver should be in PATH
            return Service(log_output=subprocess.DEVNULL)

    def _apply_stealth_patches(self):
        """Apply JavaScript stealth patches"""
        try:
            # Hide webdriver property
            self.driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )

            # Override plugins
            self.driver.execute_script(
                "Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})"
            )

            # Override languages
            self.driver.execute_script(
                "Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})"
            )

            logger.info("[Browser] ✅ Stealth patches applied")

        except Exception as e:
            logger.warning("[Browser] ⚠️ Stealth patches failed: %s", e)

    def _clear_proxy_env(self) -> dict:
        """Clear proxy env vars that interfere with Chrome"""
        proxy_vars = ["http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY"]
        backup = {}

        for var in proxy_vars:
            if var in os.environ:
                backup[var] = os.environ.pop(var)
                logger.info("[Browser] Temporarily cleared %s", var)

        return backup

    def _restore_proxy_env(self):
        """Restore proxy environment variables"""
        for var, value in self._proxy_env_backup.items():
            os.environ[var] = value
            logger.info("[Browser] Restored %s", var)
        self._proxy_env_backup.clear()

    def get_driver(self) -> webdriver.Chrome:
        """Get driver instance"""
        if not self.driver:
            self.create_driver()
        return self.driver

    def take_screenshot(self, name: str = "screenshot") -> Optional[str]:
        """Take screenshot"""
        if not self.driver:
            return None

        if not (self.settings.save_debug_screenshots or self.settings.save_screenshots_on_error):
            return None

        try:
            import datetime

            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.settings.screenshots_dir}/{name}_{timestamp}.png"
            self.driver.save_screenshot(filename)
            logger.info("[Browser] Screenshot: %s", filename)
            return filename
        except Exception as e:
            logger.warning("[Browser] Screenshot failed: %s", e)
            return None

    def quit(self):
        """Quit browser safely"""
        if self.driver:
            try:
                self.driver.quit()
                self.driver = None
                logger.info("[Browser] ✅ Browser closed")
            except Exception as e:
                logger.warning("[Browser] Error closing: %s", e)

    def wait(self, timeout: int = 10):
        """Get WebDriverWait instance"""
        return WebDriverWait(self.get_driver(), timeout)

    def __enter__(self):
        return self.get_driver()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.quit()
