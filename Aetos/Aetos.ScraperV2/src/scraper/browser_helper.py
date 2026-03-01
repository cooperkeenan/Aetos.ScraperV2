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
            result = self.driver.execute_script(
                """
                const getScrollable = () => {
                  const candidates = Array.from(
                    document.querySelectorAll(
                      "div[role='feed'], div[role='main'], div[data-pagelet*='Marketplace'], div[aria-label*='Marketplace']"
                    )
                  );
                  const withDoc = [document.scrollingElement, ...candidates].filter(Boolean);
                  let best = null;
                  let bestScroll = 0;
                  for (const el of withDoc) {
                    const scrollable = el.scrollHeight - el.clientHeight;
                    if (scrollable > bestScroll) {
                      bestScroll = scrollable;
                      best = el;
                    }
                  }
                  return best;
                };

                const el = getScrollable();
                if (!el) return { moved: false, reason: "no-scrollable" };
                const before = el.scrollTop;
                el.scrollBy(0, 800);
                return {
                  moved: el.scrollTop !== before,
                  tag: el.tagName,
                  role: el.getAttribute("role"),
                  aria: el.getAttribute("aria-label"),
                  before,
                  after: el.scrollTop,
                  height: el.scrollHeight,
                  client: el.clientHeight,
                };
                """
            )
            if result:
                logger.info(
                    "Scroll result: moved=%s tag=%s role=%s aria=%s before=%s after=%s height=%s client=%s",
                    result.get("moved"),
                    result.get("tag"),
                    result.get("role"),
                    result.get("aria"),
                    result.get("before"),
                    result.get("after"),
                    result.get("height"),
                    result.get("client"),
                )
            return bool(result and result.get("moved"))
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
