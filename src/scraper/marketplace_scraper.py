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
        try:
            search_url = f"{self.base_url}/search/?query={query}"
            self.driver.get(search_url)
            self.browser.human_delay(5, 7)

            if "/marketplace/" not in self.driver.current_url:
                logger.error(f"Not on marketplace. URL: {self.driver.current_url}")
                return False

            return True
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return False

    def collect_listings(
        self, max_listings: int = 200, keyword: str = None
    ) -> List[Dict]:
        listings = []
        seen_urls = set()
        scrolls_without_keyword = 0

        time.sleep(3)

        for scroll in range(100):  # Max 50 scrolls as safety limit
            new_listings = self._extract_visible_listings(seen_urls)

            if new_listings:
                # Check if any new listings contain the keyword
                if keyword:
                    has_keyword = any(
                        keyword.lower() in listing.get("title", "").lower()
                        for listing in new_listings
                    )
                    if has_keyword:
                        scrolls_without_keyword = 0
                    else:
                        scrolls_without_keyword += 1
                else:
                    scrolls_without_keyword = 0

                listings.extend(new_listings)
                logger.info(
                    f"Collected {len(listings)} total "
                    f"({scrolls_without_keyword} scrolls without '{keyword}')"
                )
            else:
                scrolls_without_keyword += 1

            # Stop if we've scrolled 10 times without finding the keyword
            if scrolls_without_keyword >= 10:
                logger.info(f"Stopped: 10 scrolls without '{keyword}' in titles")
                break

            # Also stop if we hit max_listings
            if len(listings) >= max_listings:
                logger.info(f"Stopped: reached max_listings ({max_listings})")
                break

            self.browser.scroll_down()
            self.browser.human_delay(1, 2)

        logger.info(f"Collected {len(listings)} total listings")
        return listings

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
            logger.error(f"Extraction error: {e}")

        return new_listings
