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
        fuzzy_match, similarity = self._check_fuzzy_patterns_strict(title, product.fuzzy_patterns)
        if fuzzy_match and similarity >= 90:
            return (90.0, f"Model pattern match: '{fuzzy_match}' ({similarity:.0f}% similar)")

        # No match
        return (0.0, "No model number match")

    def _check_brand(self, title: str, brand: str) -> bool:
        """Brand must appear as whole word"""
        return re.search(rf"\b{re.escape(brand.lower())}\b", title) is not None

    def _exact_model_match(self, title: str, model: str) -> bool:
        """
        Exact model number match with word boundaries
        Examples: "a6400", "a7 III", "a7iii"
        """
        # Normalize model - remove spaces
        model_normalized = model.lower().replace(" ", "")
        
        # Try with spaces removed from title too
        title_no_spaces = re.sub(r'\s+', '', title)
        
        if model_normalized in title_no_spaces:
            return True
        
        # Also try with word boundary (for cases like "a6400 camera")
        if re.search(rf"\b{re.escape(model.lower())}\b", title):
            return True
        
        return False

    def _check_aliases(self, title: str, aliases: list) -> str:
        """Check for exact alias matches"""
        for alias in aliases:
            alias_normalized = alias.lower().replace(" ", "")
            title_no_spaces = re.sub(r'\s+', '', title)
            
            if alias_normalized in title_no_spaces:
                return alias
            
            if re.search(rf"\b{re.escape(alias.lower())}\b", title):
                return alias
        
        return ""

    def _check_fuzzy_patterns_strict(self, title: str, patterns: list) -> Tuple[str, float]:
        """
        Check fuzzy patterns but require high similarity (>90%)
        This prevents "a200" matching "a5000" or "a6400" matching "a7rv"
        """
        for pattern in patterns:
            pattern_normalized = pattern.lower().replace(" ", "")
            title_no_spaces = re.sub(r'\s+', '', title)
            
            # Check if pattern exists in title
            if pattern_normalized in title_no_spaces:
                similarity = self._calculate_similarity(pattern_normalized, title_no_spaces)
                if similarity >= 90:
                    return (pattern, similarity)
        
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
        extracted = text[idx:idx + len(pattern)]
        
        # Calculate character-by-character match
        matches = sum(1 for a, b in zip(pattern, extracted) if a == b)
        similarity = (matches / len(pattern)) * 100
        
        return similarity