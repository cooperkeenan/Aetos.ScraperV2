import logging
import time
from typing import Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

logger = logging.getLogger(__name__)


class DescriptionScraper:

    def __init__(self, driver):
        self.driver = driver

    def fetch_description(self, listing_url: str) -> Optional[str]:
        try:
            self.driver.get(listing_url)
            time.sleep(1.5)

            description_selectors = [
                "div[data-testid='marketplace-pdp-description']",
                "div.xz9dl7a div.x1iorvi4",
                "div[style*='text-align: start']",
            ]
            description_text = ""

            for selector in description_selectors:
                try:
                    elements = WebDriverWait(self.driver, 3).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
                    )
                    for elem in elements:
                        text = elem.text.strip()
                        if text and len(text) > 20:
                            if text not in description_text:
                                description_text += " " + text
                    if description_text:
                        break
                except:
                    continue

            return description_text.strip() if description_text else None

        except Exception as e:
            logger.error(f"[Description] Failed to fetch: {e}")
            return None
