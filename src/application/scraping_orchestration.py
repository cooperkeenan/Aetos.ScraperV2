import logging
from typing import Any, Dict, List

from selenium import webdriver

from ..core.settings import get_settings
from ..domain.models.listing import Listing
from ..domain.models.match_result import MatchResult
from ..domain.repositories.i_listing_repository import IListingRepository
from ..matching.matching_engine import MatchingEngine
from ..scraper.marketplace_scraper import MarketplaceScraper
from .product_service import ProductService

logger = logging.getLogger(__name__)


class ScrapingOrchestrator:

    def __init__(
        self,
        product_service: ProductService,
        driver: webdriver.Chrome,
        listing_repository: IListingRepository,
    ):
        self.product_service = product_service
        self.driver = driver
        self.scraper = MarketplaceScraper(driver)
        self.listing_repository = listing_repository

    def scrape_and_match_brand(
        self,
        brand: str,
        search_term: str,
        max_listings: int = None,
        require_price_match: bool = True,
    ) -> Dict[str, Any]:
        settings = get_settings()

        if max_listings is None:
            max_listings = settings.MAX_LISTINGS_DEFAULT

        logger.info(
            f"Starting scrape and match workflow for brand: {brand}, search: {search_term}"
        )

        logger.info(f"\n[Step 1] Fetching products for brand '{brand}'...")
        products = self.product_service.get_products_for_brand(brand)

        if not products:
            logger.warning(f"No active products found for brand '{brand}'")
            return {
                "brand": brand,
                "products_count": 0,
                "matches": [],
                "stats": {"error": "No products found"},
            }

        logger.info(f"Loaded {len(products)} products: {[str(p) for p in products]}")

        logger.info(f"\n[Step 2] Scraping marketplace for '{search_term}'...")

        if not self.scraper.search(search_term):
            logger.error(f"Failed to search marketplace for '{search_term}'")
            return {
                "brand": brand,
                "products_count": len(products),
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
                "matches": [],
                "stats": {"listings_scraped": 0},
            }

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

        # Save all scraped listings to database (just URL/title/price at this point)
        logger.info(f"\n[Step 2.5] Saving {len(listing_objects)} listings to database...")
        for listing in listing_objects:
            try:
                self.listing_repository.upsert_listing(
                    url=listing.url,
                    title=listing.title,
                    price=listing.price,
                    location=listing.location,
                    image_url=listing.image_url,
                )
            except Exception as e:
                logger.warning(f"Failed to save listing {listing.url}: {e}")

        # Filter out already analyzed listings
        logger.info(f"\n[Step 2.6] Checking for already analyzed listings...")
        all_urls = [l.url for l in listing_objects]
        analyzed_urls = self.listing_repository.get_analyzed_urls(all_urls)
        
        new_listings = [l for l in listing_objects if l.url not in analyzed_urls]
        
        logger.info(
            f"Skipping {len(analyzed_urls)} already analyzed listings, "
            f"processing {len(new_listings)} new ones"
        )

        if not new_listings:
            logger.info("No new listings to analyze")
            return {
                "brand": brand,
                "products_count": len(products),
                "matches": [],
                "stats": {
                    "listings_scraped": len(listing_objects),
                    "listings_skipped": len(analyzed_urls),
                    "listings_analyzed": 0,
                },
            }

        logger.info(f"\n[Debug] Sample of first 5 new listings:")
        for i, listing in enumerate(new_listings[:5], 1):
            logger.info(f"  {i}. Title: '{listing.title}'")
            logger.info(f"     Price: £{listing.price if listing.price else 'None'}")
            logger.info(f"     URL: {listing.url[:80]}...")

        logger.info(
            f"\n[Step 3] Matching {len(new_listings)} listings against {len(products)} products..."
        )

        keywords = self.product_service.get_filter_keywords()
        matching_engine = MatchingEngine(
            driver=self.driver,
            reject_keywords=keywords.get("reject", []),
            boost_keywords=keywords.get("boost", []),
        )

        all_matches = matching_engine.match_listings(new_listings, products)

        logger.info(
            f"Found {len(all_matches)} matches above {settings.MIN_CONFIDENCE_THRESHOLD}% confidence"
        )

        if require_price_match:
            matches = [m for m in all_matches if m.has_price_match()]
            logger.info(
                f"Filtered to {len(matches)} matches with price match (price within acceptable range)"
            )
        else:
            matches = all_matches
            price_matched = len([m for m in matches if m.has_price_match()])
            logger.info(
                f"Keeping all matches ({price_matched} have price match, {len(matches) - price_matched} do not)"
            )

        # Update matched listings with product info
        logger.info(f"\n[Step 4] Updating {len(matches)} matched listings in database...")
        for match in matches:
            try:
                self.listing_repository.upsert_listing(
                    url=match.listing.url,
                    title=match.listing.title,
                    price=match.listing.price,
                    location=match.listing.location,
                    image_url=match.listing.image_url,
                    description=match.listing.description,
                    product_id=match.product.id,
                    match_confidence=match.confidence,
                )
            except Exception as e:
                logger.warning(f"Failed to update matched listing {match.listing.url}: {e}")

        stats = self._generate_stats(listing_objects, new_listings, matches, products, len(analyzed_urls))

        logger.info(f"\n[Complete] Workflow finished")
        logger.info(f"Stats: {stats}")
        logger.info(f"=" * 80)

        return {
            "brand": brand,
            "products_count": len(products),
            "matches": [m.to_dict() for m in matches],
            "stats": stats,
        }

    def _generate_stats(
        self, 
        all_listings: List[Listing],
        analyzed_listings: List[Listing], 
        matches: List[MatchResult], 
        products: List,
        skipped_count: int
    ) -> Dict[str, Any]:

        matches_per_product = {}
        for match in matches:
            product_id = match.product.id
            if product_id not in matches_per_product:
                matches_per_product[product_id] = 0
            matches_per_product[product_id] += 1

        avg_confidence = (
            sum(m.confidence for m in matches) / len(matches) if matches else 0
        )

        matched_listing_urls = {m.listing.url for m in matches}
        unmatched_count = len(
            [l for l in analyzed_listings if l.url not in matched_listing_urls]
        )

        return {
            "listings_scraped": len(all_listings),
            "listings_skipped": skipped_count,
            "listings_analyzed": len(analyzed_listings),
            "total_matches": len(matches),
            "unique_listings_matched": len(matched_listing_urls),
            "unmatched_listings": unmatched_count,
            "average_confidence": round(avg_confidence, 2),
            "products_with_matches": len(matches_per_product),
            "matches_per_product": matches_per_product,
        }