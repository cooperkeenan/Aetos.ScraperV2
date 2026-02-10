import logging
import time
from typing import Dict, List

from selenium.webdriver.common.by import By

from .browser_helper import BrowserHelper
from .element_extractor import ElementExtractor

logger = logging.getLogger(__name__)


class MarketplaceScraper:

    def __init__(self, driver):
        self.driver = driver
        self.browser = BrowserHelper(driver)
        self.base_url = "https://www.facebook.com/marketplace"

    def search(self, query: str) -> bool:

        search_url = f"{self.base_url}/search/?query={query}"
        logger.info(f"[Scraper] Searching: {search_url}")

        try:
            self.driver.get(search_url)
            time.sleep(3)

            if not self._is_on_marketplace():
                self._log_search_failure()
                return False

            logger.info("[Scraper] Search successful")
            return True

        except Exception as e:
            logger.error(f"[Scraper] Search failed: {e}", exc_info=True)
            return False

    def collect_listings(self, max_listings: int = 200) -> List[Dict]:

        logger.info("[Scraper] Starting collection...")
        time.sleep(2)

        listings = []
        seen_urls = set()
        scrolls_without_new = 0

        for scroll in range(100):
            new_listings = self._extract_visible_listings(seen_urls)

            if new_listings:
                listings.extend(new_listings)
                scrolls_without_new = 0
                time.sleep(0.5)
                logger.debug(f"Collected {len(listings)} total")
            else:
                scrolls_without_new += 1

            if scrolls_without_new >= 20:
                logger.info("Stopped: No new listings found")
                break

            if len(listings) >= max_listings:
                logger.info(f"Stopped: Reached {max_listings} listings")
                break

            self.browser.scroll_down()
            time.sleep(1)

        logger.info(f"[Scraper] Collected {len(listings)} listings")
        return listings

    def _is_on_marketplace(self) -> bool:
        current_url = self.driver.current_url
        return "/marketplace/" in current_url

    def _log_search_failure(self) -> None:
        logger.error(f"[Scraper] Not on marketplace")
        logger.error(f"[Scraper] URL: {self.driver.current_url}")
        logger.error(f"[Scraper] Title: {self.driver.title}")

        try:
            body_text = self.driver.find_element(By.TAG_NAME, "body").text[:500]
            logger.error(f"[Scraper] Page content: {body_text}")
        except:
            pass

        self._save_failure_screenshot()

    def _save_failure_screenshot(self) -> None:
        try:
            import datetime

            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            path = f"/app/logs/marketplace_failed_{timestamp}.png"
            self.driver.save_screenshot(path)
            logger.error(f"[Scraper] Screenshot: {path}")
        except Exception as e:
            logger.error(f"[Scraper] Screenshot failed: {e}")

    def _extract_visible_listings(self, seen_urls: set) -> List[Dict]:

        new_listings = []

        try:
            links = self.driver.find_elements(
                By.CSS_SELECTOR, "a[href*='/marketplace/item/']"
            )

            for link in links:
                try:
                    url = link.get_attribute("href")
                    if url and url not in seen_urls:
                        listing = ElementExtractor.extract_listing_data(link, url)
                        if listing:
                            new_listings.append(listing)
                            seen_urls.add(url)
                except:
                    continue

        except Exception as e:
            logger.error(f"[Scraper] Extraction error: {e}")

        return new_listings