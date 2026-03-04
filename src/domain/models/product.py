from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional


@dataclass
class Product:

    id: int
    brand: str
    model: str
    full_name: str
    category: str
    buy_price_min: Decimal
    buy_price_max: Decimal
    sell_target: Decimal
    active: bool

    fuzzy_patterns: List[str]
    aliases: List[str]

    def is_price_in_range(self, price: float) -> bool:
        return self.buy_price_min <= Decimal(str(price)) <= self.buy_price_max

    def get_potential_profit(self, buy_price: float) -> Optional[Decimal]:
        if not self.is_price_in_range(buy_price):
            return None
        return self.sell_target - Decimal(str(buy_price))

    def __str__(self) -> str:
        return f"{self.brand} {self.model}"
