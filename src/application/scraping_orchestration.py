import logging
from typing import Any, Dict, List

from selenium import webdriver

from ..core.settings import MatchingSettings, ScrapingSettings
from ..domain.models.listing import Listing
from ..domain.models.match_result import MatchResult
from ..matching.matching_engine import MatchingEngine
from ..scraping.marketplace_scraper import MarketplaceScraper
from .product_service import ProductService

logger = logging.getLogger(__name__)


class ScrapingOrchestrator:

    def __init__(self, product_service: ProductService, driver: webdriver.Chrome):
        self.product_service = product_service
        self.scraper = MarketplaceScraper(driver)

    def scrape_and_match_brand(
        self, brand: str, max_listings: int = None
    ) -> Dict[str, Any]:

        if max_listings is None:
            max_listings = ScrapingSettings.MAX_LISTINGS_DEFAULT

        logger.info(f"Starting scrape and match workflow for: {brand}")

        # Step 1: Fetch products for this brand
        logger.info(f"\n[Step 1] Fetching products for brand '{brand}'...")
        products = self.product_service.get_products_for_brand(brand)

        if not products:
            logger.warning(f"No active products found for brand '{brand}'")
            return {
                "brand": brand,
                "products_count": 0,
                "listings": [],
                "matches": [],
                "stats": {"error": "No products found"},
            }

        logger.info(f"Loaded {len(products)} products: {[str(p) for p in products]}")

        # Step 2: Scrape marketplace
        logger.info(f"\n[Step 2] Scraping marketplace for '{brand}'...")

        if not self.scraper.search(brand):
            logger.error(f"Failed to search marketplace for '{brand}'")
            return {
                "brand": brand,
                "products_count": len(products),
                "listings": [],
                "matches": [],
                "stats": {"error": "Search failed"},
            }

        listings = self.scraper.collect_listings(max_listings)
        logger.info(f"Scraped {len(listings)} listings")

        if not listings:
            logger.warning("No listings found")
            return {
                "brand": brand,
                "products_count": len(products),
                "listings": [],
                "matches": [],
                "stats": {"listings_scraped": 0},
            }

        # Convert dict listings to Listing objects
        listing_objects = [
            Listing(
                url=l["url"],
                title=l["title"],
                price=l.get("price"),
                image_url=l.get("image_url"),
                location=l.get("location"),
                scraped_at=l.get("scraped_at"),
            )
            for l in listings
        ]

        # Step 3: Match listings against products
        logger.info(
            f"\n[Step 3] Matching {len(listing_objects)} listings against {len(products)} products..."
        )

        # Get avoid keywords
        avoid_keywords = self.product_service.get_avoid_keywords()

        # Create matching engine
        matching_engine = MatchingEngine(avoid_keywords=avoid_keywords)

        # Run matching
        matches = matching_engine.match_listings(listing_objects, products)

        logger.info(
            f"Found {len(matches)} matches above {MatchingSettings.MIN_CONFIDENCE_THRESHOLD}% confidence"
        )

        # Step 4: Generate stats
        stats = self._generate_stats(listing_objects, matches, products)

        logger.info(f"\n[Complete] Workflow finished")
        logger.info(f"Stats: {stats}")
        logger.info(f"=" * 80)

        return {
            "brand": brand,
            "products_count": len(products),
            "listings": [self._listing_to_dict(l) for l in listing_objects],
            "matches": [m.to_dict() for m in matches],
            "stats": stats,
        }

    def _generate_stats(
        self, listings: List[Listing], matches: List[MatchResult], products: List
    ) -> Dict[str, Any]:
        """Generate statistics for the run"""

        # Count matches per product
        matches_per_product = {}
        for match in matches:
            product_id = match.product.id
            if product_id not in matches_per_product:
                matches_per_product[product_id] = 0
            matches_per_product[product_id] += 1

        # Average confidence
        avg_confidence = (
            sum(m.confidence for m in matches) / len(matches) if matches else 0
        )

        # Listings with/without matches
        matched_listing_urls = {m.listing.url for m in matches}
        unmatched_count = len(
            [l for l in listings if l.url not in matched_listing_urls]
        )

        return {
            "listings_scraped": len(listings),
            "total_matches": len(matches),
            "unique_listings_matched": len(matched_listing_urls),
            "unmatched_listings": unmatched_count,
            "average_confidence": round(avg_confidence, 2),
            "products_with_matches": len(matches_per_product),
            "matches_per_product": matches_per_product,
        }

    def _listing_to_dict(self, listing: Listing) -> Dict[str, Any]:
        """Convert Listing object to dict"""
        return {
            "url": listing.url,
            "title": listing.title,
            "price": listing.price,
            "image_url": listing.image_url,
            "location": listing.location,
            "scraped_at": listing.scraped_at,
        }
