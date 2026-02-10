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
        self.driver = driver
        self.description_scraper = DescriptionScraper(driver)
        self.title_matcher = TitleMatcher()
        self.price_matcher = PriceMatcher()
        self.keyword_filter = KeywordFilter(reject_keywords or [], boost_keywords or [])
        self.confidence_calculator = ConfidenceCalculator()
        self.min_confidence = get_settings().MIN_CONFIDENCE_THRESHOLD

    def match_listings(
        self, listings: List[Listing], products: List[Product]
    ) -> List[MatchResult]:

        """Match multiple listings, returning best match for each listing"""
        logger.info(
            f"\n[Matching] Processing {len(listings)} listings vs {len(products)} products"
        )

        self._log_sample_listings(listings[:3])

        all_matches = []
        for listing in listings:
            best_match = self._find_best_match(listing, products)
            if best_match:
                all_matches.append(best_match)

        logger.info(f"\n[Matching] Found {len(all_matches)} matches")
        return all_matches

    def _find_best_match(
        self, listing: Listing, products: List[Product]
    ) -> Optional[MatchResult]:
        """Find best matching product for a listing"""
        matches = []

        for product in products:
            match = self._match_single(listing, product)
            if match and match.is_confident_match():
                matches.append(match)

        if not matches:
            return None

        # Return highest confidence match
        best_match = max(matches, key=lambda m: m.confidence)
        
        logger.info(
            f"[Match] '{listing.title[:50]}' → "
            f"{best_match.product.model} ({best_match.confidence:.0f}%)"
        )

        return best_match

    def _match_single(
        self, listing: Listing, product: Product
    ) -> Optional[MatchResult]:
      
        # Phase 1: Quick rejection checks
        title_score, title_reason = self.title_matcher.match(listing, product)
        if title_score < 60:
            return None

        price_score, price_reason = self.price_matcher.match(listing, product)
        if price_score == 0:
            return None

        # Check title for reject keywords (fast, no description fetch yet)
        if self._has_reject_keywords_in_title(listing, product):
            return None

        # Phase 2: Fetch description for promising matches
        self._ensure_description(listing)

        # Final keyword check with description
        keyword_score, keyword_reason = self.keyword_filter.match(listing, product)
        if keyword_score == 0:
            logger.info(f"[Match] Rejected: {keyword_reason}")
            return None

        # Calculate final confidence
        confidence = self._calculate_confidence(
            title_score, price_score, keyword_score, listing
        )

        return self._create_match_result(
            listing=listing,
            product=product,
            confidence=confidence,
            title_score=title_score,
            price_score=price_score,
            keyword_score=keyword_score,
            title_reason=title_reason,
            price_reason=price_reason,
            keyword_reason=keyword_reason,
        )

    def _has_reject_keywords_in_title(
        self, listing: Listing, product: Product
    ) -> bool:
        initial_score, reason = self.keyword_filter.match(listing, product)
        if initial_score == 0:
            logger.debug(f"[Match] Rejected by title: {reason}")
            return True
        return False

    def _ensure_description(self, listing: Listing) -> None:
        if not listing.description:
            logger.info(
                f"[Match] Fetching description: {listing.title[:50]}..."
            )
            listing.description = self.description_scraper.fetch_description(
                listing.url
            )

    def _calculate_confidence(
        self,
        title_score: float,
        price_score: float,
        keyword_score: float,
        listing: Listing,
    ) -> float:
        confidence, _ = self.confidence_calculator.calculate(
            title_score, price_score, keyword_score
        )

        # Add boost bonus
        boost_count = self.keyword_filter.count_boost_keywords(listing)
        if boost_count > 0:
            boost_bonus = min(boost_count * 5, 20)
            confidence = min(confidence + boost_bonus, 100)

        return confidence

    def _create_match_result(
        self,
        listing: Listing,
        product: Product,
        confidence: float,
        title_score: float,
        price_score: float,
        keyword_score: float,
        title_reason: str,
        price_reason: str,
        keyword_reason: str,
    ) -> MatchResult:
        _, breakdown = self.confidence_calculator.calculate(
            title_score, price_score, keyword_score
        )

        # Add boost info to breakdown
        boost_count = self.keyword_filter.count_boost_keywords(listing)
        if boost_count > 0:
            boost_bonus = min(boost_count * 5, 20)
            breakdown.append(f"Boost: +{boost_bonus}% ({boost_count} keywords)")

        return MatchResult(
            listing=listing,
            product=product,
            confidence=confidence,
            reasons=[title_reason, price_reason, keyword_reason, *breakdown],
            title_score=title_score,
            price_score=price_score,
            keyword_score=keyword_score,
        )

    def _log_sample_listings(self, listings: List[Listing]) -> None:
        if not listings:
            return

        for i, listing in enumerate(listings, 1):
            price_str = f"£{listing.price}" if listing.price else "None"
            logger.info(f"\n  Listing {i}: '{listing.title}' - {price_str}")