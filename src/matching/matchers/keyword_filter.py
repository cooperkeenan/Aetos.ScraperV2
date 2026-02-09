from typing import List, Tuple

from ...domain.models.listing import Listing
from ...domain.models.product import Product
from .base_matcher import BaseMatcher


class KeywordFilter(BaseMatcher):

    def __init__(self, reject_keywords: List[str], boost_keywords: List[str]):
        self.reject_keywords = [kw.lower() for kw in reject_keywords]
        self.boost_keywords = [kw.lower() for kw in boost_keywords]

    def match(self, listing: Listing, product: Product) -> Tuple[float, str]:
        """Check title and description for reject keywords"""
        
        title = listing.get_title_normalized()
        description = getattr(listing, 'description', '') or ''
        description = description.lower()
        
        combined_text = f"{title} {description}".strip()

        if not combined_text:
            return (100.0, "No text to filter")

        for keyword in self.reject_keywords:
            if keyword in title:
                return (0.0, f"Rejected: title contains '{keyword}'")
            if keyword in description:
                return (0.0, f"Rejected: description contains '{keyword}'")

        boost_found = []
        for keyword in self.boost_keywords:
            if keyword in title or keyword in description:
                boost_found.append(keyword)

        if boost_found:
            return (100.0, f"Passed filters, boost keywords: {', '.join(boost_found)}")

        return (100.0, "Passed filters (no reject keywords)")

    def count_boost_keywords(self, listing: Listing) -> int:
        """Count boost keywords in title and description"""
        title = listing.get_title_normalized()
        description = getattr(listing, 'description', '') or ''
        description = description.lower()
        
        combined_text = f"{title} {description}"
        
        count = 0
        for keyword in self.boost_keywords:
            if keyword in combined_text:
                count += 1
        
        return count