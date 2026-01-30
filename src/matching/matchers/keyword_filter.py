from typing import List, Tuple

from ...domain.models.listing import Listing
from ...domain.models.product import Product
from .base_matcher import BaseMatcher


class KeywordFilter(BaseMatcher):

    def __init__(self, avoid_keywords: List[str]):
        self.avoid_keywords = [kw.lower() for kw in avoid_keywords]

    def match(self, listing: Listing, product: Product) -> Tuple[float, str]:

        title = listing.get_title_normalized()

        if not title:
            return (100.0, "No title to filter")

        for keyword in self.avoid_keywords:
            if keyword in title:
                return (0.0, f"Rejected: contains avoid keyword '{keyword}'")

        return (100.0, "No avoid keywords found")
