import logging
from typing import List, Tuple

from ..core.settings import MatchingSettings

logger = logging.getLogger(__name__)


class ConfidenceCalculator:

    def __init__(self):

        self.title_weight = MatchingSettings.TITLE_WEIGHT
        self.price_weight = MatchingSettings.PRICE_WEIGHT
        self.keyword_weight = MatchingSettings.KEYWORD_WEIGHT

        # Validate weights sum to 1.0
        total = self.title_weight + self.price_weight + self.keyword_weight
        if not (0.99 <= total <= 1.01):
            raise ValueError(f"Weights must sum to 1.0, got {total}")

    def calculate(
        self, title_score: float, price_score: float, keyword_score: float
    ) -> Tuple[float, List[str]]:

        # Hard reject if keyword filter fails
        if keyword_score == 0:
            return (0.0, ["Rejected due to avoid keywords"])

        # Hard reject if price is 0 (too cheap or too expensive)
        if price_score == 0:
            return (0.0, ["Rejected due to price outside acceptable range"])

        # Calculate weighted average
        confidence = (
            title_score * self.title_weight
            + price_score * self.price_weight
            + keyword_score * self.keyword_weight
        )

        # Generate breakdown
        breakdown = [
            f"Title: {title_score:.0f}% (weight {self.title_weight:.0%})",
            f"Price: {price_score:.0f}% (weight {self.price_weight:.0%})",
            f"Keywords: {keyword_score:.0f}% (weight {self.keyword_weight:.0%})",
        ]

        logger.debug(f"Confidence: {confidence:.1f}% - {' | '.join(breakdown)}")

        return (confidence, breakdown)
