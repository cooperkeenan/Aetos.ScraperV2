
import logging
from typing import List, Optional

from ..core.settings import MatchingSettings
from ..domain.models.listing import Listing
from ..domain.models.match_result import MatchResult
from ..domain.models.product import Product
from .confidence_calculator import ConfidenceCalculator
from .matchers.keyword_filter import KeywordFilter
from .matchers.price_matcher import PriceMatcher
from .matchers.title_matcher import TitleMatcher

logger = logging.getLogger(__name__)


class MatchingEngine:

    
    def __init__(self, avoid_keywords: List[str] = None):

        # Initialize matchers
        self.title_matcher = TitleMatcher()
        self.price_matcher = PriceMatcher()
        self.keyword_filter = KeywordFilter(avoid_keywords or [])
        
        # Initialize confidence calculator
        self.confidence_calculator = ConfidenceCalculator()
        
        # Get threshold from settings
        self.min_confidence = MatchingSettings.MIN_CONFIDENCE_THRESHOLD
    
    def match_listing(
        self,
        listing: Listing,
        products: List[Product]
    ) -> List[MatchResult]:

        results = []
        
        for product in products:
            result = self._match_single(listing, product)
            if result and result.is_confident_match():
                results.append(result)
        
        results.sort(key=lambda r: r.confidence, reverse=True)
        
        logger.info(
            f"Matched listing '{listing.title[:50]}...' - "
            f"Found {len(results)} matches above {self.min_confidence}%"
        )
        
        return results
    
    def match_listings(
        self,
        listings: List[Listing],
        products: List[Product]
    ) -> List[MatchResult]:

        all_results = []
        
        for listing in listings:
            matches = self.match_listing(listing, products)
            all_results.extend(matches)
        
        logger.info(
            f"Matched {len(listings)} listings against {len(products)} products - "
            f"Found {len(all_results)} total matches"
        )
        
        return all_results
    
    def _match_single(
        self,
        listing: Listing,
        product: Product
    ) -> Optional[MatchResult]:
        
        # Run all matchers
        title_score, title_reason = self.title_matcher.match(listing, product)
        price_score, price_reason = self.price_matcher.match(listing, product)
        keyword_score, keyword_reason = self.keyword_filter.match(listing, product)
        
        # Calculate final confidence
        confidence, breakdown = self.confidence_calculator.calculate(
            title_score,
            price_score,
            keyword_score
        )
        
        # Build result
        result = MatchResult(
            listing=listing,
            product=product,
            confidence=confidence,
            reasons=[title_reason, price_reason, keyword_reason, *breakdown]
        )
        
        return result