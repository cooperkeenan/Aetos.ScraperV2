import re
from typing import Tuple

from ...domain.models.listing import Listing
from ...domain.models.product import Product
from .base_matcher import BaseMatcher


class TitleMatcher(BaseMatcher):
    """
    Strict title matching - requires exact model numbers
    No fuzzy matching that causes false positives
    """

    def match(self, listing: Listing, product: Product) -> Tuple[float, str]:
        title = listing.get_title_normalized()

        if not title:
            return (0.0, "No title to match")

        # Must match brand first
        if not self._check_brand(title, product.brand):
            return (0.0, f"Brand '{product.brand}' not found in title")

        # Check for exact model match (highest priority)
        if self._exact_model_match(title, product.model):
            return (100.0, f"Exact model match: '{product.model}'")

        # Check aliases (also exact)
        alias_match = self._check_aliases(title, product.aliases)
        if alias_match:
            return (100.0, f"Exact alias match: '{alias_match}'")

        # Check fuzzy patterns (strict - must be very similar)
        fuzzy_match, similarity = self._check_fuzzy_patterns_strict(
            title, product.fuzzy_patterns
        )
        if fuzzy_match and similarity >= 90:
            return (
                90.0,
                f"Model pattern match: '{fuzzy_match}' ({similarity:.0f}% similar)",
            )

        # No match
        return (0.0, "No model number match")

    def _check_brand(self, title: str, brand: str) -> bool:
        """Brand must appear as whole word"""
        return re.search(rf"\b{re.escape(brand.lower())}\b", title) is not None

    def _exact_model_match(self, title: str, model: str) -> bool:

        model_normalized = model.lower().replace(" ", "")
        title_no_spaces = re.sub(r"\s+", "", title)

        if re.search(
            rf"(?<![a-z0-9]){re.escape(model_normalized)}(?![a-z0-9])", title_no_spaces
        ):
            return True

        if re.search(rf"\b{re.escape(model.lower())}\b", title):
            return True

        return False

    def _check_aliases(self, title: str, aliases: list) -> str:
        title_no_spaces = re.sub(r"\s+", "", title)

        for alias in aliases:
            alias_normalized = alias.lower().replace(" ", "")

            if re.search(
                rf"(?<![a-z0-9]){re.escape(alias_normalized)}(?![a-z0-9])",
                title_no_spaces,
            ):
                return alias

            if re.search(rf"\b{re.escape(alias.lower())}\b", title):
                return alias

        return ""

    def _check_fuzzy_patterns_strict(
        self, title: str, patterns: list
    ) -> Tuple[str, float]:
        title_no_spaces = re.sub(r"\s+", "", title)

        for pattern in patterns:
            pattern_normalized = pattern.lower().replace(" ", "")

            # Exact boundary match — treat as 100% confident, no similarity calc needed
            if re.search(
                rf"(?<![a-z0-9]){re.escape(pattern_normalized)}(?![a-z0-9])",
                title_no_spaces,
            ):
                return (pattern, 100.0)

            if re.search(rf"\b{re.escape(pattern.lower())}\b", title):
                return (pattern, 100.0)

        return ("", 0.0)

    def _calculate_similarity(self, pattern: str, text: str) -> float:
        """
        Calculate how similar the pattern is to the relevant part of text
        Returns 0-100 score
        """
        # Find where pattern appears in text
        idx = text.find(pattern)
        if idx == -1:
            return 0.0

        # Extract the same length from text
        extracted = text[idx : idx + len(pattern)]

        # Calculate character-by-character match
        matches = sum(1 for a, b in zip(pattern, extracted) if a == b)
        similarity = (matches / len(pattern)) * 100

        return similarity
