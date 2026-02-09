import logging
import time
from typing import Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

logger = logging.getLogger(__name__)


class DescriptionScraper:
    """Fetches listing descriptions by clicking into posts"""

    def __init__(self, driver):
        self.driver = driver

    def fetch_description(self, listing_url: str) -> Optional[str]:
        """
        Navigate to listing and extract description
        Returns full description text or None if failed
        """
        try:
            logger.info(
                f"[Description] Fetching description from: {listing_url[:80]}..."
            )

            self.driver.get(listing_url)
            time.sleep(1.5)

            description_selectors = [
                "div[style*='text-align: start']",
                "div.x1iorvi4.x4uap5.xjkvuk6",
                "span[dir='auto']",
                "div.xdj266r",
            ]

            description_text = ""

            for selector in description_selectors:
                try:
                    elements = WebDriverWait(
                        self.driver, 3
                    ).until(  # Reduced from 5 seconds
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

            if description_text:
                description_text = description_text.strip()
                logger.info(
                    f"[Description] Found {len(description_text)} chars: {description_text[:100]}..."
                )
                return description_text

            logger.warning(f"[Description] No description found")
            return None

        except Exception as e:
            logger.error(f"[Description] Failed to fetch: {e}")
            return None
