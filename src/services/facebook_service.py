"""Facebook service - Session management only"""

import logging
import os
import pickle
import random
import time

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from ..core.settings import Settings
from .browser_service import BrowserService
from .session_service import SessionService


logger = logging.getLogger(__name__)


class FacebookService:
    """Handles Facebook session restoration"""

    def __init__(
        self, settings: Settings, browser: BrowserService, session: SessionService
    ):
        self.settings = settings
        self.browser = browser
        self.session = session
        self.driver = None

    def restore_session(self) -> bool:
        """Restore session from saved cookies or login manually"""
        # Try cookies first
        cookies = self.session.load_cookies()
        if cookies and self.session.validate_cookies(cookies):
            if self._restore_from_cookies(cookies):
                return True
            logger.warning("[Facebook] Cookie restoration failed, trying manual login...")
        
        # Fallback to manual login
        return self._manual_login()

    def _restore_from_cookies(self, cookies) -> bool:
        """Try to restore session using cookies"""
        self.driver = self.browser.get_driver()
        
        logger.info(f"[Facebook] Loading Facebook with {len(cookies)} cookies...")
        self.driver.get("https://www.facebook.com")
        self.driver.delete_all_cookies()

        for cookie in cookies:
            try:
                if "expiry" in cookie and cookie["expiry"] < time.time():
                    cookie.pop("expiry", None)
                self.driver.add_cookie(cookie)
            except Exception as e:
                logger.warning(
                    "[Facebook] Failed to add cookie %s: %s",
                    cookie.get("name"),
                    e,
                )

        logger.info("[Facebook] Refreshing page with cookies...")
        self.driver.refresh()
        self._human_delay(3, 5)

        if self._is_logged_in():
            logger.info("[Facebook] ✅ Session restored from cookies")
            return True

        logger.warning("[Facebook] Cookie session invalid")
        return False

    def _manual_login(self) -> bool:
        """Manual login using credentials from .env"""
        fb_user = os.getenv("GOOGLE_USER")  # Reusing GOOGLE_USER for Facebook
        fb_pass = os.getenv("GOOGLE_PASS")  # Reusing GOOGLE_PASS for Facebook
        
        if not fb_user or not fb_pass:
            logger.error("[Facebook] No credentials found in .env (GOOGLE_USER/GOOGLE_PASS)")
            return False
        
        logger.info(f"[Facebook] Attempting manual login as {fb_user}...")
        
        try:
            if not self.driver:
                self.driver = self.browser.get_driver()
            
            # Go to login page
            self.driver.get("https://www.facebook.com/login")
            self._human_delay(2, 3)
            
            # Enter email
            email_input = WebDriverWait(self.driver, 10).until(
                lambda d: d.find_element(By.ID, "email") or d.find_element(By.NAME, "email")
            )
            email_input.clear()
            for char in fb_user:
                email_input.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))
            
            self._human_delay(0.5, 1)
            
            # Enter password
            pass_input = self.driver.find_element(By.ID, "pass")
            pass_input.clear()
            for char in fb_pass:
                pass_input.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))
            
            self._human_delay(0.5, 1)
            
            # Click login button
            login_button = self.driver.find_element(By.NAME, "login")
            login_button.click()
            
            logger.info("[Facebook] Login submitted, waiting for response...")
            self._human_delay(5, 7)
            
            # Check if logged in
            if self._is_logged_in():
                logger.info("[Facebook] ✅ Manual login successful!")
                
                # Save cookies for next time
                self._save_session_cookies()
                
                return True
            
            # Check for errors
            current_url = self.driver.current_url
            page_text = self.driver.find_element(By.TAG_NAME, "body").text[:500]
            
            logger.error(f"[Facebook] Login failed - URL: {current_url}")
            logger.error(f"[Facebook] Page content: {page_text}")
            
            self.browser.take_screenshot("facebook_login_failed")
            
            return False
            
        except Exception as e:
            logger.error(f"[Facebook] Manual login error: {e}", exc_info=True)
            self.browser.take_screenshot("facebook_login_error")
            return False

    def _save_session_cookies(self):
        """Save current session cookies"""
        try:
            cookies = self.driver.get_cookies()
            cookie_path = os.path.join(self.settings.cookies_dir, "fb_cookies.pkl")
            
            with open(cookie_path, 'wb') as f:
                pickle.dump(cookies, f)
            
            logger.info(f"[Facebook] Saved {len(cookies)} cookies for future use")
            
        except Exception as e:
            logger.warning(f"[Facebook] Failed to save cookies: {e}")

    def _is_logged_in(self) -> bool:
        """Check if logged in"""
        current_url = self.driver.current_url.lower()
        
        # Check URL patterns
        if any(path in current_url for path in ["facebook.com/?", "facebook.com/home"]):
            logger.info("[Facebook] Logged in (detected by URL)")
            return True

        # Check for navigation elements
        selectors = [
            "[aria-label='Home']",
            "[aria-label='Your profile']", 
            "[role='navigation']",
            "div[data-pagelet='LeftRail']"
        ]
        
        for selector in selectors:
            try:
                WebDriverWait(self.driver, 5).until(
                    lambda d: d.find_element(By.CSS_SELECTOR, selector)
                )
                logger.info(f"[Facebook] Logged in (found selector: {selector})")
                return True
            except TimeoutException:
                continue

        logger.warning("[Facebook] No login indicators found")
        return False

    def _human_delay(self, min_seconds: float = 1, max_seconds: float = 3):
        """Add human-like delay"""
        time.sleep(random.uniform(min_seconds, max_seconds))
