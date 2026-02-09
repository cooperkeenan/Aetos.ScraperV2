import logging
from typing import List, Optional

from ..core.settings import get_settings
from ..domain.models.listing import Listing
from ..domain.models.match_result import MatchResult
from ..domain.models.product import Product
from ..scraper.description_scraper import DescriptionScraper
from .confidence_calculator import ConfidenceCalculator
from .matchers.keyword_filter import KeywordFilter
from .matchers.price_matcher import PriceMatcher
from .matchers.title_matcher import TitleMatcher

logger = logging.getLogger(__name__)


class MatchingEngine:

    def __init__(
        self,
        driver,
        reject_keywords: List[str] = None,
        boost_keywords: List[str] = None,
    ):
        settings = get_settings()
        self.driver = driver
        self.description_scraper = DescriptionScraper(driver)
        self.title_matcher = TitleMatcher()
        self.price_matcher = PriceMatcher()
        self.keyword_filter = KeywordFilter(reject_keywords or [], boost_keywords or [])
        self.confidence_calculator = ConfidenceCalculator()
        self.min_confidence = settings.MIN_CONFIDENCE_THRESHOLD

    def match_listing(
        self, listing: Listing, products: List[Product]
    ) -> List[MatchResult]:
        results = []

        for product in products:
            result = self._match_single(listing, product)
            if result and result.is_confident_match():
                results.append(result)

        results.sort(key=lambda r: r.confidence, reverse=True)
        return results

    def match_listings(
        self, listings: List[Listing], products: List[Product]
    ) -> List[MatchResult]:
        all_results = []

        logger.info(f"\n[Matching Debug] Testing first 3 listings:")
        for i, listing in enumerate(listings[:3], 1):
            logger.info(f"\n  Listing {i}: '{listing.title}'")
            logger.info(f"  Price: £{listing.price if listing.price else 'None'}")

        for listing in listings:
            matches = self.match_listing(listing, products)
            all_results.extend(matches)

        logger.info(
            f"Matched {len(listings)} listings against {len(products)} products - "
            f"Found {len(all_results)} total matches"
        )

        return all_results

    def _match_single(
        self, listing: Listing, product: Product
    ) -> Optional[MatchResult]:
        """
        Two-phase matching:
        1. Check title for quick reject keywords
        2. If title/price match looks promising, fetch description
        3. Check description for reject/boost keywords
        """

        # Phase 1: Quick title/price check
        title_score, title_reason = self.title_matcher.match(listing, product)
        price_score, price_reason = self.price_matcher.match(listing, product)

        # Quick reject if title or price completely fail
        if title_score < 40 or price_score == 0:
            return None

        # Phase 1.5: Check title for reject keywords (before fetching description)
        initial_keyword_score, initial_keyword_reason = self.keyword_filter.match(
            listing, product
        )
        if initial_keyword_score == 0:
            logger.info(f"[Match] Rejected by title keywords: {initial_keyword_reason}")
            return None

        # Phase 2: Fetch description for promising matches
        if not listing.description:
            logger.info(
                f"[Match] Fetching description for potential match: {listing.title[:50]}..."
            )
            listing.description = self.description_scraper.fetch_description(
                listing.url
            )

        # Phase 3: Final keyword check with description
        keyword_score, keyword_reason = self.keyword_filter.match(listing, product)

        if keyword_score == 0:
            logger.info(f"[Match] Rejected by description keywords: {keyword_reason}")
            return None

        # Calculate confidence with boost
        boost_count = self.keyword_filter.count_boost_keywords(listing)

        confidence, breakdown = self.confidence_calculator.calculate(
            title_score, price_score, keyword_score
        )

        # Add boost bonus (5% per boost keyword, max 20%)
        if boost_count > 0:
            boost_bonus = min(boost_count * 5, 20)
            confidence = min(confidence + boost_bonus, 100)
            breakdown.append(f"Boost: +{boost_bonus}% ({boost_count} keywords)")

        result = MatchResult(
            listing=listing,
            product=product,
            confidence=confidence,
            reasons=[title_reason, price_reason, keyword_reason, *breakdown],
            title_score=title_score,
            price_score=price_score,
            keyword_score=keyword_score,
        )

        return result
