from dataclasses import dataclass, field
from decimal import Decimal
from typing import List, Optional

from ...core.settings import get_settings
from .listing import Listing
from .product import Product


@dataclass
class MatchResult:

    listing: Listing
    product: Product
    confidence: float  # 0-100
    reasons: List[str] = field(default_factory=list)
    
    # Component scores for filtering
    title_score: float = 0.0
    price_score: float = 0.0
    keyword_score: float = 0.0

    def is_confident_match(self) -> bool:
        settings = get_settings()
        return self.confidence >= settings.MIN_CONFIDENCE_THRESHOLD
    
    def has_price_match(self) -> bool:
        """Check if the price was within acceptable range"""
        return self.price_score > 0

    def add_reason(self, reason: str) -> None:
        self.reasons.append(reason)

    def to_dict(self) -> dict:

        # Calculate profit safely
        profit: Optional[Decimal] = None
        if self.listing.price:
            profit = self.product.get_potential_profit(self.listing.price)

        return {
            "listing": {
                "url": self.listing.url,
                "title": self.listing.title,
                "price": self.listing.price,
                "location": self.listing.location,
            },
            "product": {
                "id": self.product.id,
                "brand": self.product.brand,
                "model": self.product.model,
                "full_name": self.product.full_name,
            },
            "confidence": round(self.confidence, 2),
            "match_breakdown": {
                "title_score": round(self.title_score, 2),
                "price_score": round(self.price_score, 2),
                "keyword_score": round(self.keyword_score, 2),
            },
            "reasons": self.reasons,
            "potential_profit": float(profit) if profit is not None else None,
        }

    def __str__(self) -> str:
        return f"Match: {self.product} - {self.confidence:.0f}% confidence"