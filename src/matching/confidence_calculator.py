from typing import List, Tuple

from ..core.settings import get_settings


class ConfidenceCalculator:

    def calculate(
        self, title_score: float, price_score: float, keyword_score: float
    ) -> Tuple[float, List[str]]:
        """Calculate weighted confidence score"""
        settings = get_settings()

        confidence = (
            title_score * settings.TITLE_WEIGHT
            + price_score * settings.PRICE_WEIGHT
            + keyword_score * settings.KEYWORD_WEIGHT
        )

        breakdown = [
            f"Title: {title_score:.0f}% (weight {int(settings.TITLE_WEIGHT * 100)}%)",
            f"Price: {price_score:.0f}% (weight {int(settings.PRICE_WEIGHT * 100)}%)",
            f"Keywords: {keyword_score:.0f}% (weight {int(settings.KEYWORD_WEIGHT * 100)}%)",
        ]

        return confidence, breakdown
