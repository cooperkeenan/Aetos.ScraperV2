from decimal import Decimal
from typing import Tuple

from ...domain.models.listing import Listing
from ...domain.models.product import Product
from .base_matcher import BaseMatcher


class PriceMatcher(BaseMatcher):

    def match(self, listing: Listing, product: Product) -> Tuple[float, str]:

        if not listing.has_price():
            return (50.0, "No price available")

        price = Decimal(str(listing.price))

        if product.is_price_in_range(listing.price):
            profit = product.get_potential_profit(listing.price)
            return (
                100.0,
                f"Price £{price:.0f} in range (£{product.buy_price_min}-£{product.buy_price_max}), profit: £{profit:.0f}",
            )

        if price < product.buy_price_min:
            return (0.0, f"Price £{price:.0f} too low (min £{product.buy_price_min})")

        return (0.0, f"Price £{price:.0f} too high (max £{product.buy_price_max})")
