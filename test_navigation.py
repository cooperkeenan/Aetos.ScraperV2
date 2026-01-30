#!/usr/bin/env python3
"""
Test Facebook Marketplace Scraper with Matching
"""

import logging
import sys
from decimal import Decimal

from dotenv import load_dotenv

from src.core.config_service import get_config
from src.domain.models.listing import Listing
from src.domain.models.product import Product
from src.matching.matching_engine import MatchingEngine
from src.scraper.marketplace_scraper import MarketplaceScraper
from src.services.browser_service import BrowserService
from src.services.facebook_service import FacebookService
from src.services.proxy_service import ProxyService
from src.services.session_service import SessionService

load_dotenv()

file_handler = logging.FileHandler("/app/logs/output.log", mode="w")
file_handler.setFormatter(logging.Formatter("%(message)s"))

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[logging.StreamHandler(sys.stdout), file_handler],
)
logger = logging.getLogger(__name__)


def get_sample_products():
    """Sample Canon products for testing"""
    return [
        Product(
            id=1,
            brand="Canon",
            model="1000D",
            full_name="Canon EOS 1000D / Rebel XS",
            category="DSLR",
            buy_price_min=Decimal("40"),
            buy_price_max=Decimal("80"),
            sell_target=Decimal("130"),
            active=True,
            fuzzy_patterns=["cannon 1000d", "canon 1000 d", "rebel xs", "kiss f"],
            aliases=["1000d", "eos 1000d", "rebel xs", "xs", "kiss f"],
        ),
        Product(
            id=2,
            brand="Canon",
            model="1100D",
            full_name="Canon EOS 1100D / Rebel T3",
            category="DSLR",
            buy_price_min=Decimal("60"),
            buy_price_max=Decimal("120"),
            sell_target=Decimal("160"),
            active=True,
            fuzzy_patterns=["cannon 1100d", "canon 1100 d", "rebel t3", "kiss x50"],
            aliases=["1100d", "eos 1100d", "rebel t3", "t3", "kiss x50"],
        ),
        Product(
            id=3,
            brand="Canon",
            model="550D",
            full_name="Canon EOS 550D / Rebel T2i",
            category="DSLR",
            buy_price_min=Decimal("100"),
            buy_price_max=Decimal("160"),
            sell_target=Decimal("220"),
            active=True,
            fuzzy_patterns=["cannon 550d", "canon 550 d", "rebel t2i", "kiss x4"],
            aliases=["550d", "eos 550d", "rebel t2i", "t2i", "kiss x4"],
        ),
        Product(
            id=4,
            brand="Canon",
            model="2000D",
            full_name="Canon EOS 2000D / Rebel T7",
            category="DSLR",
            buy_price_min=Decimal("150"),
            buy_price_max=Decimal("220"),
            sell_target=Decimal("300"),
            active=True,
            fuzzy_patterns=["cannon 2000d", "canon 2000 d", "rebel t7"],
            aliases=["2000d", "eos 2000d", "rebel t7", "t7"],
        ),
        Product(
            id=5,
            brand="Canon",
            model="4000D",
            full_name="Canon EOS 4000D / Rebel T100",
            category="DSLR",
            buy_price_min=Decimal("200"),
            buy_price_max=Decimal("320"),
            sell_target=Decimal("400"),
            active=True,
            fuzzy_patterns=["cannon 4000d", "canon 4000 d", "rebel t100"],
            aliases=["4000d", "eos 4000d", "rebel t100", "t100"],
        ),
    ]


def test_navigation():
    """Test marketplace scraping with matching"""

    SEARCH_QUERY = "canon"

    logger.info("=" * 80)
    logger.info("🧪 Testing Facebook Marketplace Scraper + Matching")
    logger.info("=" * 80)

    try:
        config = get_config()
        proxy_service = ProxyService() if config.proxy.enabled else None

        if proxy_service:
            logger.info("\n[Test] Testing proxy...")
            ip = proxy_service.test_proxy(proxy_service.get_proxy_url())
            if not ip:
                logger.warning("[Test] ⚠️  Proxy test failed, continuing anyway...")

        browser = BrowserService(config, proxy_service)
        session = SessionService(config)
        facebook = FacebookService(config, browser, session)

        with browser:
            logger.info("\n[Test] Restoring Facebook session...")

            if not facebook.restore_session():
                logger.error("[Test] ❌ No valid session found!")
                logger.error("[Test] Run your messenger bot first to generate cookies")
                return

            logger.info("[Test] ✅ Session restored")

            scraper = MarketplaceScraper(browser.get_driver())

            logger.info(f"\n[Test] Searching for '{SEARCH_QUERY}'...")

            if not scraper.search(SEARCH_QUERY):
                logger.error("[Test] ❌ Search failed")
                browser.take_screenshot("search_failed")
                return

            logger.info(
                f"\n[Test] Collecting listings (will stop after 10 scrolls without '{SEARCH_QUERY}')..."
            )
            listing_dicts = scraper.collect_listings(
                max_listings=200, keyword=SEARCH_QUERY
            )

            if not listing_dicts:
                logger.error("[Test] ❌ No listings found")
                browser.take_screenshot("no_listings")
                return

            # Print HTML structure for debugging (since ACR Tasks is ephemeral)
            logger.info("[Test] 💾 Extracting HTML structure for debugging...")
            page_html = browser.get_driver().page_source

            import re

            # Find all listing links
            listing_pattern = r'<a[^>]*href="[^"]*marketplace/item/[^"]*"[^>]*>.*?</a>'
            listing_matches = list(re.finditer(listing_pattern, page_html, re.DOTALL))

            logger.info(f"\n[Test] Found {len(listing_matches)} listing links in HTML")
            logger.info("\n[Test] ========== FIRST 3 LISTINGS HTML ==========")

            for i, match in enumerate(listing_matches[:3]):
                logger.info(f"\n--- Listing {i+1} ---")
                snippet = match.group(0)
                # Print first 1500 chars of each listing
                logger.info(snippet[:1500])
                if len(snippet) > 1500:
                    logger.info(f"... (truncated, total length: {len(snippet)} chars)")

            logger.info("\n[Test] ========== END HTML ==========\n")

            logger.info(f"\n[Test] ✅ Collected {len(listing_dicts)} listings")

            # Debug: Show first 3 raw listings
            logger.info("\n[Test] Sample listings (raw data):")
            for i, l in enumerate(listing_dicts[:3], 1):
                logger.info(f"  {i}. Title: '{l.get('title', 'EMPTY')}'")
                logger.info(f"     Price: £{l.get('price', 0)}")
                logger.info(f"     URL: {l.get('url', '')[:80]}...")

            # Convert to Listing objects
            listings = [
                Listing(
                    url=l["url"],
                    title=l.get("title", ""),
                    price=l.get("price"),
                    image_url=l.get("image_url"),
                    location=l.get("location"),
                    scraped_at=l.get("scraped_at"),
                )
                for l in listing_dicts
            ]

            # Load products and run matching
            logger.info("\n[Test] Loading products and running matching...")
            products = get_sample_products()
            avoid_keywords = ["broken", "damaged", "for parts", "spares", "repair"]

            engine = MatchingEngine(avoid_keywords=avoid_keywords)
            matches = engine.match_listings(listings, products)

            # Display results
            logger.info("\n" + "=" * 80)
            logger.info(f"MATCHING RESULTS")
            logger.info("=" * 80)
            logger.info(f"Scraped: {len(listings)} listings")
            logger.info(f"Products: {len(products)}")
            logger.info(f"Matches: {len(matches)} above 70% confidence")
            logger.info("=" * 80)

            if matches:
                for i, match in enumerate(matches[:10], 1):
                    match_dict = match.to_dict()
                    profit = match_dict["potential_profit"]

                    logger.info(f"\n{i}. {match.listing.title}")
                    logger.info(f"   💰 £{match.listing.price:.0f}")
                    logger.info(
                        f"   ✓ {match.product.full_name} ({match.confidence:.1f}% confidence)"
                    )
                    if profit:
                        logger.info(f"   💵 Potential profit: £{profit:.0f}")
                    logger.info(f"   🔗 {match.listing.url}")

                if len(matches) > 10:
                    logger.info(f"\n... and {len(matches) - 10} more matches")
            else:
                logger.info("\n⚠️  No matches found above confidence threshold")
                logger.info("(Check if listings have titles extracted correctly)")

            logger.info("\n" + "=" * 80)
            logger.info("[Test] ✅ Test completed successfully!")

    except Exception as e:
        logger.error(f"\n[Test] ❌ Test failed: {e}", exc_info=True)
        if "browser" in locals():
            browser.take_screenshot("test_error")
        raise


if __name__ == "__main__":
    test_navigation()
