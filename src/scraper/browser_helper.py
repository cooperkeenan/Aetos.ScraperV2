import random
import time


class BrowserHelper:

    def __init__(self, driver):
        self.driver = driver

    def human_delay(self, min_seconds: float = 1, max_seconds: float = 3) -> None:
        time.sleep(random.uniform(min_seconds, max_seconds))

    def scroll_down(self) -> None:
        try:
            self.driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);"
            )
        except:
            pass
