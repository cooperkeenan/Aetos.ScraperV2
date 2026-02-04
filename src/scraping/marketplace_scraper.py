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
            logger.info(f"[Scraper] Navigating to: {search_url}")
            
            self.driver.get(search_url)
            self.browser.human_delay(5, 7)

            current_url = self.driver.current_url
            logger.info(f"[Scraper] Current URL after search: {current_url}")
            
            if "/marketplace/" not in current_url:
                logger.error(f"[Scraper] Not on marketplace. URL: {current_url}")
                logger.error(f"[Scraper] Page title: {self.driver.title}")
                
                # Log page content for debugging
                try:
                    page_text = self.driver.find_element(By.TAG_NAME, "body").text[:500]
                    logger.error(f"[Scraper] Page content: {page_text}")
                except:
                    pass
                
                # Take screenshot
                try:
                    import datetime
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    screenshot_path = f"/app/logs/marketplace_search_failed_{timestamp}.png"
                    self.driver.save_screenshot(screenshot_path)
                    logger.error(f"[Scraper] Screenshot saved: {screenshot_path}")
                except Exception as e:
                    logger.error(f"[Scraper] Screenshot failed: {e}")
                
                return False

            logger.info("[Scraper] ✅ Successfully loaded marketplace search")
            return True
            
        except Exception as e:
            logger.error(f"[Scraper] Search failed with exception: {e}", exc_info=True)
            return False

    def collect_listings(
        self, max_listings: int = 200, keyword: str = None
    ) -> List[Dict]:
        listings = []
        seen_urls = set()
        scrolls_without_keyword = 0

        time.sleep(3)

        for scroll in range(100):
            new_listings = self._extract_visible_listings(seen_urls)

            if new_listings:
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

            if scrolls_without_keyword >= 10:
                logger.info(f"Stopped: 10 scrolls without '{keyword}' in titles")
                break

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