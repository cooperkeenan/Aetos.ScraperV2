import re
from typing import Tuple

from ...domain.models.listing import Listing
from ...domain.models.product import Product
from .base_matcher import BaseMatcher


class TitleMatcher(BaseMatcher):

    def match(self, listing: Listing, product: Product) -> Tuple[float, str]:

        title = listing.get_title_normalized()

        if not title:
            return (0.0, "No title to match")

        score = 0.0
        matched_terms = []

        brand_match = self._check_brand(title, product.brand)
        if brand_match:
            score += 40
            matched_terms.append(f"brand '{product.brand}'")

        exact_match = self._check_exact_patterns(title, product)
        if exact_match:
            score = 100
            matched_terms.append(f"exact match '{exact_match}'")
            return (score, f"Matched: {', '.join(matched_terms)}")

        alias_match = self._check_aliases(title, product.aliases)
        if alias_match:
            score += 50
            matched_terms.append(f"alias '{alias_match}'")

        fuzzy_match = self._check_fuzzy_patterns(title, product.fuzzy_patterns)
        if fuzzy_match:
            score += 30
            matched_terms.append(f"pattern '{fuzzy_match}'")

        score = min(score, 100)

        if matched_terms:
            return (score, f"Matched: {', '.join(matched_terms)}")

        return (0.0, "No title match")

    def _check_brand(self, title: str, brand: str) -> bool:
        return re.search(rf"\b{re.escape(brand.lower())}\b", title) is not None

    def _check_exact_patterns(self, title: str, product: Product) -> str:
        patterns = [product.model.lower(), product.full_name.lower()]

        for pattern in patterns:
            if pattern in title:
                return pattern
        return ""

    def _check_aliases(self, title: str, aliases: list) -> str:
        for alias in aliases:
            if re.search(rf"\b{re.escape(alias.lower())}\b", title):
                return alias
        return ""

    def _check_fuzzy_patterns(self, title: str, patterns: list) -> str:
        for pattern in patterns:
            if pattern.lower() in title:
                return pattern
        return ""
