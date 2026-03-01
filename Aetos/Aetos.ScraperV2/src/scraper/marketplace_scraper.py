import datetime
import logging
import time
from typing import Dict, List

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from ..core.settings import get_settings
from .browser_helper import BrowserHelper
from .element_extractor import ElementExtractor

logger = logging.getLogger(__name__)


class MarketplaceScraper:

    def __init__(self, driver):
        self.driver = driver
        self.browser = BrowserHelper(driver)
        self.settings = get_settings()
        self.base_url = "https://www.facebook.com/marketplace"

    def search(self, query: str) -> bool:
        search_url = f"{self.base_url}/search/?query={query}"
        logger.info(f"[Scraper] Searching: {search_url}")

        try:
            self.driver.get(search_url)
            self._wait_for_marketplace_results(timeout=15)

            if not self._is_on_marketplace():
                self._log_search_failure()
                return False

            logger.info("[Scraper] Search successful")
            return True

        except Exception as e:
            logger.error(f"[Scraper] Search failed: {e}", exc_info=True)
            return False

    def collect_listings(self, brands: List[str]) -> List[Dict]:
        max_listings = self.settings.MAX_LISTINGS_DEFAULT
        max_without_brand = self.settings.MAX_SCROLLS_WITHOUT_BRAND_MATCH

        logger.info(f"[Scraper] Starting collection (max={max_listings}, brands={brands})...")
        self._wait_for_marketplace_ready(timeout=15)

        listings = []
        seen_urls = set()
        scrolls_without_new = 0
        consecutive_without_brand = 0
        brands_lower = [b.lower() for b in brands]

        for scroll in range(100):
            new_listings = self._extract_visible_listings(seen_urls)

            if new_listings:
                scrolls_without_new = 0
                for listing in new_listings:
                    listings.append(listing)
                    if any(b in listing["title"].lower() for b in brands_lower):
                        consecutive_without_brand = 0
                    else:
                        consecutive_without_brand += 1

                time.sleep(0.5)
            else:
                scrolls_without_new += 1

            if scrolls_without_new >= 10:
                logger.info("Stopped: No new listings found")
                break

            if len(listings) >= max_listings:
                logger.info(f"Stopped: Reached {max_listings} listings")
                break

            if consecutive_without_brand >= max_without_brand:
                logger.info(f"Stopped: {max_without_brand} consecutive listings without brand match")
                break

            before_dom_count = self._count_listing_elements()
            moved = self.browser.scroll_down()
            logger.info(
                "[Scraper] Scroll attempt: moved=%s before_count=%s",
                moved,
                before_dom_count,
            )
            self._wait_for_more_listings(before_dom_count, timeout_seconds=6)
            after_dom_count = self._count_listing_elements()
            logger.info(
                "[Scraper] Listings after scroll: after_count=%s (+%s)",
                after_dom_count,
                max(0, after_dom_count - before_dom_count),
            )
            if not moved and after_dom_count <= before_dom_count:
                logger.info("[Scraper] Primary scroll failed; trying fallback scrollIntoView")
                self._scroll_last_listing_into_view()
                self._wait_for_more_listings(after_dom_count, timeout_seconds=6)
                after_fallback_count = self._count_listing_elements()
                logger.info(
                    "[Scraper] Listings after fallback: after_count=%s (+%s)",
                    after_fallback_count,
                    max(0, after_fallback_count - after_dom_count),
                )
                self._save_scroll_debug_snapshot()
            time.sleep(1.5)

        logger.info(f"[Scraper] Collected {len(listings)} listings")
        return listings

    def _is_on_marketplace(self) -> bool:
        return "/marketplace/" in self.driver.current_url

    def _wait_for_marketplace_results(self, timeout: int = 15) -> None:
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: "/marketplace/" in d.current_url
            )
            WebDriverWait(self.driver, timeout).until(
                lambda d: len(d.find_elements(By.CSS_SELECTOR, "a[href*='/marketplace/item/']")) > 0
            )
            logger.info("[Scraper] Marketplace results loaded")
        except Exception as e:
            logger.warning("[Scraper] Marketplace results wait timed out: %s", e)
    
    def _wait_for_marketplace_ready(self, timeout: int = 15) -> None:
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            WebDriverWait(self.driver, timeout).until(
                lambda d: len(d.find_elements(By.CSS_SELECTOR, "a[href*='/marketplace/item/']")) > 0
            )
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.execute_script(
                    "const busy = document.querySelector('[aria-busy=\"true\"]'); return !busy;"
                )
            )
            logger.info("[Scraper] Marketplace DOM ready")
        except Exception as e:
            logger.warning("[Scraper] Marketplace ready wait timed out: %s", e)

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
            links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/marketplace/item/']")

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

    def _count_listing_elements(self) -> int:
        try:
            return len(self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/marketplace/item/']"))
        except Exception:
            return 0

    def _wait_for_more_listings(self, before_count: int, timeout_seconds: int = 6) -> bool:
        end = time.time() + timeout_seconds
        while time.time() < end:
            if self._count_listing_elements() > before_count:
                return True
            time.sleep(0.5)
        return False

    def _scroll_last_listing_into_view(self) -> bool:
        try:
            links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/marketplace/item/']")
            if not links:
                return False
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'end'});",
                links[-1],
            )
            return True
        except Exception:
            return False

    def _save_scroll_debug_snapshot(self) -> None:
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            html_path = f"/app/logs/marketplace_scroll_debug_{timestamp}.html"
            png_path = f"/app/logs/marketplace_scroll_debug_{timestamp}.png"
            if self.browser.save_html(html_path):
                logger.info(f"[Scraper] HTML snapshot: {html_path}")
            if self.browser.save_screenshot(png_path):
                logger.info(f"[Scraper] Screenshot snapshot: {png_path}")
        except Exception as e:
            logger.error(f"[Scraper] Debug snapshot failed: {e}")
