

import logging
import os
import pickle
import random
import time

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from ..core.settings import Settings
from .browser_service import BrowserService
from .session_service import SessionService

logger = logging.getLogger(__name__)


class FacebookService:

    def __init__(self, settings: Settings, browser: BrowserService, session: SessionService):
        self.settings = settings
        self.browser = browser
        self.session = session
        self.driver = None

    def restore_session(self) -> bool:
        cookies = self.session.load_cookies()
        if cookies and self.session.validate_cookies(cookies):
            if self._restore_from_cookies(cookies):
                return True
            logger.warning("[Facebook] Cookie restoration failed, trying manual login...")

        return self._manual_login()

    def _restore_from_cookies(self, cookies) -> bool:
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
                logger.warning("[Facebook] Failed to add cookie %s: %s", cookie.get("name"), e)

        logger.info("[Facebook] Refreshing page with cookies...")
        self.driver.refresh()
        self._human_delay(3, 5)

        if self._is_logged_in():
            logger.info("[Facebook] ✅ Session restored from cookies")
            return True

        logger.warning("[Facebook] Cookie session invalid")
        return False

    def _manual_login(self) -> bool:
        fb_user = os.getenv("GOOGLE_USER")
        fb_pass = os.getenv("GOOGLE_PASS")

        if not fb_user or not fb_pass:
            logger.error("[Facebook] No credentials found in env (GOOGLE_USER/GOOGLE_PASS)")
            return False

        logger.info(f"[Facebook] Attempting manual login as {fb_user}...")

        try:
            if not self.driver:
                self.driver = self.browser.get_driver()

            self.driver.get("https://www.facebook.com")
            self._human_delay(3, 5)

            self._dismiss_cookie_consent()

            try:
                email_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='email']"))
                )
            except TimeoutException:
                logger.error(f"[Facebook] Email input not found - URL: {self.driver.current_url}")
                self.browser.take_screenshot("facebook_no_email_input")
                return False

            email_input.clear()
            for char in fb_user:
                email_input.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))

            self._human_delay(0.5, 1)

            try:
                pass_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='pass']"))
                )
            except TimeoutException:
                logger.error("[Facebook] Password input not found")
                self.browser.take_screenshot("facebook_no_password_input")
                return False

            pass_input.clear()
            for char in fb_pass:
                pass_input.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))

            self._human_delay(0.5, 1)

            try:
                login_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "[aria-label='Log In'][role='button']"))
                )
                login_button.click()
                logger.info("[Facebook] Login submitted")
            except TimeoutException:
                logger.error("[Facebook] Login button not found")
                self.browser.take_screenshot("facebook_no_login_button")
                return False

            self._human_delay(5, 7)

            if self._is_logged_in():
                logger.info("[Facebook] ✅ Manual login successful!")
                self._save_session_cookies()
                return True

            logger.error(f"[Facebook] Login failed - URL: {self.driver.current_url}")
            logger.error(f"[Facebook] Page text: {self.driver.find_element(By.TAG_NAME, 'body').text[:300]}")
            self.browser.take_screenshot("facebook_login_failed")
            return False

        except Exception as e:
            logger.error(f"[Facebook] Manual login error: {e}", exc_info=True)
            self.browser.take_screenshot("facebook_login_error")
            return False

    def _dismiss_cookie_consent(self) -> None:
        consent_selectors = [
            "button[data-cookiebanner='accept_button']",
            "button[title='Accept all']",
            "button[title='Allow all cookies']",
        ]
        for selector in consent_selectors:
            try:
                btn = WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                btn.click()
                logger.info(f"[Facebook] Dismissed cookie consent")
                self._human_delay(1, 2)
                return
            except TimeoutException:
                continue

    def _save_session_cookies(self) -> None:
        try:
            cookies = self.driver.get_cookies()
            cookie_path = os.path.join(self.settings.cookies_dir, "fb_cookies.pkl")
            with open(cookie_path, "wb") as f:
                pickle.dump(cookies, f)
            logger.info(f"[Facebook] Saved {len(cookies)} cookies")
        except Exception as e:
            logger.warning(f"[Facebook] Failed to save cookies: {e}")

    def _is_logged_in(self) -> bool:
        current_url = self.driver.current_url.lower()

        if any(path in current_url for path in ["facebook.com/?", "facebook.com/home"]):
            logger.info("[Facebook] Logged in (detected by URL)")
            return True

        selectors = [
            "[aria-label='Home']",
            "[aria-label='Your profile']",
            "[role='navigation']",
            "div[data-pagelet='LeftRail']",
        ]

        for selector in selectors:
            try:
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                logger.info(f"[Facebook] Logged in (found: {selector})")
                return True
            except TimeoutException:
                continue

        logger.warning("[Facebook] No login indicators found")
        return False

    def _human_delay(self, min_seconds: float = 1, max_seconds: float = 3) -> None:
        time.sleep(random.uniform(min_seconds, max_seconds))