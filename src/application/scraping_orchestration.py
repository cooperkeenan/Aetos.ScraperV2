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
        self.settings = get_settings()

    def scrape_and_match_brand(
        self,
        brand: str,
        search_term: str,
        require_price_match: bool = True,
    ) -> Dict[str, Any]:
        logger.info(f"Starting scrape for brand: {brand}, search: {search_term}")

        # Step 1: Load products
        products = self._load_products(brand)
        if not products:
            return self._create_error_response(brand, "No products found")

        # Step 2: Scrape marketplace
        listings = self._scrape_marketplace(search_term)
        if not listings:
            return self._create_error_response(brand, "No listings found", len(products))

        # Step 3: Filter out already seen listings
        new_listings = self._filter_seen_listings(listings)
        if not new_listings:
            return self._create_response(
                brand=brand,
                products_count=len(products),
                matches=[],
                stats={
                    "listings_scraped": len(listings),
                    "listings_skipped": len(listings),
                    "listings_analyzed": 0,
                }
            )

        # Step 4: Match listings to products (saves identified ones internally)
        matches = self._match_listings(new_listings, products, require_price_match)

        # Step 5: Generate response
        stats = self._generate_stats(listings, new_listings, matches, products)
        
        logger.info(f"Complete - Found {len(matches)} matches")
        logger.info("=" * 80)

        return self._create_response(brand, len(products), matches, stats)

    def _load_products(self, brand: str) -> List:
        logger.info(f"\n[Step 1] Loading products for '{brand}'...")
        products = self.product_service.get_products_for_brand(brand)
        
        if products:
            logger.info(f"Loaded {len(products)} products")
        else:
            logger.warning(f"No products found for '{brand}'")
        
        return products

    def _scrape_marketplace(self, search_term: str) -> List[Listing]:
        logger.info(f"\n[Step 2] Scraping marketplace for '{search_term}'...")
        
        if not self.scraper.search(search_term):
            logger.error("Search failed")
            return []

        raw_listings = self.scraper.collect_listings(self.settings.MAX_LISTINGS_DEFAULT)
        logger.info(f"Scraped {len(raw_listings)} listings")

        return [
            Listing(
                url=l["url"],
                title=l["title"],
                price=l.get("price"),
                image_url=l.get("image_url"),
                location=l.get("location"),
                scraped_at=l.get("scraped_at"),
            )
            for l in raw_listings
        ]

    def _filter_seen_listings(self, listings: List[Listing]) -> List[Listing]:
        logger.info(f"\n[Step 3] Filtering already seen listings...")
        
        all_urls = [l.url for l in listings]
        existing_urls = self.listing_repository.urls_exist(all_urls)
        new_listings = [l for l in listings if l.url not in existing_urls]
        
        logger.info(
            f"Skipping {len(existing_urls)} seen, analyzing {len(new_listings)} new"
        )

        if new_listings:
            self._log_sample_listings(new_listings[:5])

        return new_listings

    def _match_listings(
        self, listings: List[Listing], products: List, require_price_match: bool
    ) -> List[MatchResult]:
        logger.info(f"\n[Step 4] Matching {len(listings)} listings...")

        keywords = self.product_service.get_filter_keywords()
        matching_engine = MatchingEngine(
            driver=self.driver,
            reject_keywords=keywords.get("reject", []),
            boost_keywords=keywords.get("boost", []),
        )

        all_matches = matching_engine.match_listings(listings, products)
        logger.info(f"Found {len(all_matches)} matches above threshold")

        # Save ALL identified listings (we know what they are)
        self._save_identified_listings(all_matches)

        # Then filter for API response based on price requirement
        if require_price_match:
            matches = [m for m in all_matches if m.has_price_match()]
            logger.info(f"Filtered to {len(matches)} with price match")
        else:
            matches = all_matches

        return matches

    def _save_identified_listings(self, matches: List[MatchResult]) -> None:
        """
        Save all listings where we identified the product (title matched)
        This prevents re-analyzing them even if price was wrong
        """
        logger.info(f"\n[Step 4.5] Saving {len(matches)} identified listings to history...")
        
        for match in matches:
            try:
                self.listing_repository.add_listing(
                    url=match.listing.url,
                    title=match.listing.title,
                    price=match.listing.price,
                    location=match.listing.location,
                    description=match.listing.description,
                )
            except Exception as e:
                logger.warning(f"Failed to save {match.listing.url[:50]}: {e}")

    def _save_matches(self, matches: List[MatchResult]) -> None:
        """Deprecated - now using _save_identified_listings"""
        pass

    def _generate_stats(
        self,
        all_listings: List[Listing],
        analyzed_listings: List[Listing],
        matches: List[MatchResult],
        products: List,
    ) -> Dict[str, Any]:
        matches_per_product = {}
        for match in matches:
            matches_per_product[match.product.id] = (
                matches_per_product.get(match.product.id, 0) + 1
            )

        avg_confidence = (
            sum(m.confidence for m in matches) / len(matches) if matches else 0
        )

        matched_urls = {m.listing.url for m in matches}
        unmatched = len([l for l in analyzed_listings if l.url not in matched_urls])

        return {
            "listings_scraped": len(all_listings),
            "listings_skipped": len(all_listings) - len(analyzed_listings),
            "listings_analyzed": len(analyzed_listings),
            "total_matches": len(matches),
            "unique_listings_matched": len(matched_urls),
            "unmatched_listings": unmatched,
            "average_confidence": round(avg_confidence, 2),
            "products_with_matches": len(matches_per_product),
            "matches_per_product": matches_per_product,
        }

    def _log_sample_listings(self, listings: List[Listing]) -> None:
        logger.info("\n[Debug] Sample listings:")
        for i, listing in enumerate(listings, 1):
            price_str = f"£{listing.price}" if listing.price else "No price"
            logger.info(f"  {i}. {listing.title[:60]} - {price_str}")

    def _create_response(
        self,
        brand: str,
        products_count: int,
        matches: List[MatchResult],
        stats: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "brand": brand,
            "products_count": products_count,
            "matches": [m.to_dict() for m in matches],
            "stats": stats,
        }

    def _create_error_response(
        self, brand: str, error: str, products_count: int = 0
    ) -> Dict[str, Any]:
        return {
            "brand": brand,
            "products_count": products_count,
            "matches": [],
            "stats": {"error": error},
        }