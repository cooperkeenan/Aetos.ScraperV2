from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Listing:

    url: str
    title: str
    price: Optional[float]
    image_url: Optional[str]
    location: Optional[str]
    scraped_at: Optional[float] = None

    def has_price(self) -> bool:
        return self.price is not None and self.price > 0

    def get_title_normalized(self) -> str:
        return self.title.lower().strip()

    def __str__(self) -> str:
        price_str = f"£{self.price:.0f}" if self.price else "No price"
        return f"{self.title} - {price_str}"
