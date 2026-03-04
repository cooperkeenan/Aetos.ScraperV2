import logging
import random
import time

logger = logging.getLogger(__name__)


class BrowserHelper:

    def __init__(self, driver):
        self.driver = driver

    def human_type(self, element, text: str) -> None:
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))

    def human_delay(self, min_seconds: float = 1, max_seconds: float = 3) -> None:
        time.sleep(random.uniform(min_seconds, max_seconds))

    def scroll_down(self) -> bool:
        try:
            self.driver.execute_script("""
                const links = document.querySelectorAll('a[href*="/marketplace/item/"]');
                if (links.length) links[links.length - 1].scrollIntoView({block: 'end', behavior: 'smooth'});
            """)
            time.sleep(random.uniform(0.8, 1.4))
            return True

        except Exception as e:
            logger.debug(f"Scroll failed: {e}")
            return False

    def save_screenshot(self, filepath: str) -> bool:
        try:
            self.driver.save_screenshot(filepath)
            logger.info(f"Screenshot: {filepath}")
            return True
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            return False

    def save_html(self, filepath: str) -> bool:
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            return True
        except Exception as e:
            logger.error(f"HTML save failed: {e}")
            return False