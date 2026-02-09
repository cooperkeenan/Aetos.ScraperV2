import re
from typing import List, Tuple

from rapidfuzz import fuzz

from ...domain.models.listing import Listing
from ...domain.models.product import Product
from .base_matcher import BaseMatcher


class TitleMatcher(BaseMatcher):
    """
    Improved title matcher with exact model matching and fuzzy scoring

    Scoring priority:
    1. Exact model match (100%) - e.g., "a6400" in title, product model is "a6400"
    2. Alias match (90%) - e.g., "Alpha 6400" matches product with alias "a6400"
    3. Fuzzy pattern match (70-85%) - similar strings with fuzzy scoring
    4. Brand only (40%) - just brand name found

    Returns only if score >= 60
    """

    def match(self, listing: Listing, product: Product) -> Tuple[float, str]:

        title = listing.get_title_normalized()

        if not title:
            return (0.0, "No title to match")

        # Extract potential model numbers from title (alphanumeric sequences)
        title_models = self._extract_model_numbers(title)
        product_model = product.model.lower()

        # 1. Check for EXACT model match (highest priority)
        if product_model in title_models:
            return (100.0, f"Exact model match: '{product.model}'")

        # 2. Check brand presence (required for any match)
        if not self._check_brand(title, product.brand):
            return (0.0, f"Brand '{product.brand}' not found in title")

        score = 40.0  # Base score for brand match
        matched_terms = [f"brand '{product.brand}'"]

        # 3. Check aliases for exact match
        alias_match = self._check_aliases_exact(title_models, product.aliases)
        if alias_match:
            return (90.0, f"Alias exact match: '{alias_match}'")

        # 4. Check full product name similarity
        full_name_score = fuzz.partial_ratio(title, product.full_name.lower())
        if full_name_score >= 85:
            score += 50
            matched_terms.append(f"full name similarity {full_name_score}%")
            return (min(score, 100), f"Matched: {', '.join(matched_terms)}")

        # 5. Check fuzzy patterns
        fuzzy_match, fuzzy_score = self._check_fuzzy_patterns_scored(
            title, product.fuzzy_patterns
        )
        if fuzzy_match and fuzzy_score >= 80:
            score += 40
            matched_terms.append(f"pattern '{fuzzy_match}' ({fuzzy_score}% similar)")
            return (min(score, 100), f"Matched: {', '.join(matched_terms)}")

        # If we only have brand, that's too weak
        if score <= 40:
            return (0.0, "Only brand matched - insufficient for product identification")

        return (min(score, 100), f"Matched: {', '.join(matched_terms)}")

    def _extract_model_numbers(self, text: str) -> List[str]:
        """
        Extract potential model numbers from text
        e.g., "Sony a6400" -> ["a6400", "6400"]
        e.g., "Sony Alpha a7R IV" -> ["a7r", "a7riv", "7", "iv"]
        """
        # Find alphanumeric sequences that look like models
        patterns = [
            r"\b([a-z]+\d+[a-z]*)\b",  # a6400, a7iii, a7riv
            r"\b(\d+[a-z]+)\b",  # 6400d, 7r
        ]

        models = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            models.extend(matches)

        return [m.lower() for m in models]

    def _check_brand(self, title: str, brand: str) -> bool:
        """Check if brand is present in title"""
        return re.search(rf"\b{re.escape(brand.lower())}\b", title) is not None

    def _check_aliases_exact(self, title_models: List[str], aliases: List[str]) -> str:
        """Check if any alias exactly matches extracted model numbers"""
        for alias in aliases:
            alias_lower = alias.lower()
            if alias_lower in title_models:
                return alias
        return ""

    def _check_fuzzy_patterns_scored(
        self, title: str, patterns: List[str]
    ) -> Tuple[str, int]:
        """
        Check fuzzy patterns and return best match with score
        Returns (pattern, score) or ("", 0) if no good match
        """
        best_pattern = ""
        best_score = 0

        for pattern in patterns:
            score = fuzz.partial_ratio(pattern.lower(), title)
            if score > best_score:
                best_score = score
                best_pattern = pattern

        return (best_pattern, best_score)
