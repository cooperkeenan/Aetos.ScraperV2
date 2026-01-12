# src/scraper/marketplace_scraper.py

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
        logger.info(f"[Scraper] Searching for: '{query}'")

        try:
            search_url = f"{self.base_url}/search/?query={query}"
            self.driver.get(search_url)
            self.browser.human_delay(5, 7)

            if "/marketplace/" not in self.driver.current_url:
                logger.error(f"[Scraper] ❌ Not on marketplace")
                return False

            logger.info("[Scraper] ✅ Search successful")
            return True

        except Exception as e:
            logger.error(f"[Scraper] ❌ Search failed: {e}")
            return False

    def collect_listings(self, max_listings: int = 50) -> List[Dict]:

        logger.info(f"[Scraper] Collecting up to {max_listings} listings...")

        listings = []
        seen_urls = set()
        scroll_attempts = 0
        no_new_count = 0

        time.sleep(3)  # Initial page load

        while len(listings) < max_listings and scroll_attempts < 20:
            scroll_attempts += 1

            new_listings = self._extract_visible_listings(seen_urls)

            if new_listings:
                listings.extend(new_listings)
                logger.info(f"[Scraper] Collected {len(listings)}/{max_listings}")
                no_new_count = 0
            else:
                no_new_count += 1

            if no_new_count >= 3:
                break

            self.browser.scroll_down()
            self.browser.human_delay(1, 2)

        logger.info(f"[Scraper] Collected {len(listings)} total")
        return listings[:max_listings]

    def _extract_visible_listings(self, seen_urls: set) -> List[Dict]:

        new_listings = []

        try:
            listing_links = self.driver.find_elements(
                By.CSS_SELECTOR, "a[href*='/marketplace/item/']"
            )

            for link in listing_links:
                try:
                    url = link.get_attribute("href")
                    if not url or url in seen_urls:
                        continue

                    listing = ElementExtractor.extract_listing_data(link, url)
                    if listing:
                        new_listings.append(listing)
                        seen_urls.add(url)
                except:
                    continue
        except Exception as e:
            logger.error(f"[Scraper] Error: {e}")

        return new_listings

    def print_listings(self, listings: List[Dict], limit: int = 3) -> None:
        """Print formatted listings"""
        logger.info("\n" + "=" * 80)
        logger.info(f" FOUND {len(listings)} LISTINGS")
        logger.info("=" * 80)

        for i, listing in enumerate(listings[:limit], 1):
            price = (
                f"£{listing['price']:.0f}" if listing.get("price") else "Price unknown"
            )
            location = f" - {listing['location']}" if listing.get("location") else ""

            logger.info(f"\n{i}. {listing['title']}")
            logger.info(f"    {price}{location}")
            logger.info(f"    {listing['url']}")

        if len(listings) > limit:
            logger.info(f"\n... and {len(listings) - limit} more")

        logger.info("\n" + "=" * 80 + "\n")
