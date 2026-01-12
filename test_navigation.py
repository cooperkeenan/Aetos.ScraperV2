#!/usr/bin/env python3
"""
Test Facebook Marketplace Scraper
Tests the refactored scraper with SOLID principles
"""

import logging
import sys
import time

from dotenv import load_dotenv

from src.core.config_service import get_config
from src.scraper.marketplace_scraper import MarketplaceScraper
from src.services.browser_service import BrowserService
from src.services.facebook_service import FacebookService
from src.services.proxy_service import ProxyService
from src.services.session_service import SessionService

load_dotenv()

# Configure logging
file_handler = logging.FileHandler("/app/logs/output.log", mode="w")
file_handler.setFormatter(logging.Formatter("%(message)s"))

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[logging.StreamHandler(sys.stdout), file_handler],
)
logger = logging.getLogger(__name__)


def test_navigation():
    """Test marketplace scraping with saved cookies"""

    SEARCH_QUERY = "canon"
    MAX_RESULTS = 3

    logger.info("=" * 80)
    logger.info("🧪 Testing Facebook Marketplace Scraper")
    logger.info("=" * 80)

    try:
        # Setup services
        config = get_config()
        proxy_service = ProxyService() if config.proxy.enabled else None

        if proxy_service:
            logger.info("\n[Test] Testing proxy...")
            ip = proxy_service.test_proxy(proxy_service.get_proxy_url())
            if not ip:
                logger.warning("[Test] ⚠️  Proxy test failed, continuing anyway...")

        # Create services
        browser = BrowserService(config, proxy_service)
        session = SessionService(config)
        facebook = FacebookService(config, browser, session)

        with browser:
            # Restore session
            logger.info("\n[Test] Restoring Facebook session...")

            if not facebook.restore_session():
                logger.error("[Test] ❌ No valid session found!")
                logger.error("[Test] Run your messenger bot first to generate cookies")
                return

            logger.info("[Test] ✅ Session restored")

            # Create scraper
            scraper = MarketplaceScraper(browser.get_driver())

            # Search
            logger.info(f"\n[Test] Searching for '{SEARCH_QUERY}'...")

            if not scraper.search(SEARCH_QUERY):
                logger.error("[Test] ❌ Search failed")
                browser.take_screenshot("search_failed")
                return

            # Collect results
            logger.info(f"\n[Test] Collecting first {MAX_RESULTS} results...")
            listings = scraper.collect_listings(max_listings=MAX_RESULTS)

            if not listings:
                logger.error("[Test] ❌ No listings found")
                browser.take_screenshot("no_listings")
                return

            # Print results
            scraper.print_listings(listings, limit=MAX_RESULTS)

            logger.info("[Test] ✅ Test completed successfully!")

    except Exception as e:
        logger.error(f"\n[Test] ❌ Test failed: {e}", exc_info=True)
        if "browser" in locals():
            browser.take_screenshot("test_error")
        raise


if __name__ == "__main__":
    test_navigation()
