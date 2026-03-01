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
            current_scroll = self.driver.execute_script("return window.pageYOffset;")
            page_height = self.driver.execute_script("return document.body.scrollHeight;")
            window_height = self.driver.execute_script("return window.innerHeight;")

            logger.info(
                "Scroll metrics: current=%s window=%s page=%s",
                current_scroll,
                window_height,
                page_height,
            )

            if current_scroll + window_height >= page_height - 500:
                logger.info("Scroll result: at-bottom=true")
                return False

            scroll_method = random.choice(["smooth_scroll", "page_scroll"])
            time.sleep(2)

            if scroll_method == "smooth_scroll":
                self._smooth_scroll()
            else:
                self._page_scroll()

            new_scroll = self.driver.execute_script("return window.pageYOffset;")
            moved = new_scroll != current_scroll
            logger.info("Scroll result: method=%s moved=%s before=%s after=%s", scroll_method, moved, current_scroll, new_scroll)
            return bool(moved)
        except Exception as e:
            logger.debug(f"Scroll failed: {e}")
            return False

    def _smooth_scroll(self) -> None:
        scroll_amount = random.randint(300, 800)
        increments = random.randint(3, 6)
        increment_size = max(1, scroll_amount // increments)

        for _ in range(increments):
            self.driver.execute_script(f"window.scrollBy(0, {increment_size});")
            time.sleep(random.uniform(0.1, 0.3))

    def _page_scroll(self) -> None:
        window_height = self.driver.execute_script("return window.innerHeight;")
        scroll_amount = random.randint(int(window_height * 0.3), int(window_height * 0.8))
        self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")

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
