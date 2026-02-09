from decimal import Decimal
from typing import Tuple

from ...domain.models.listing import Listing
from ...domain.models.product import Product
from .base_matcher import BaseMatcher


class PriceMatcher(BaseMatcher):
    """
    Price scoring with sliding scale:
    - Out of range (below min or above max): 0%
    - At min price: 100%
    - At max price: 60%
    - Linear scale between min and max

    This rewards listings closer to min price (more profit)
    """

    def match(self, listing: Listing, product: Product) -> Tuple[float, str]:

        if not listing.has_price():
            return (0.0, "No price available - rejected")

        price = Decimal(str(listing.price))

        # Reject if outside range
        if price < product.buy_price_min:
            return (0.0, f"Price £{price:.0f} too low (min £{product.buy_price_min})")

        if price > product.buy_price_max:
            return (0.0, f"Price £{price:.0f} too high (max £{product.buy_price_max})")

        # Calculate sliding score (100% at min, 60% at max)
        price_range = float(product.buy_price_max - product.buy_price_min)

        if price_range == 0:
            # Edge case: min == max
            score = 100.0
        else:
            # How far through the range are we? (0.0 = min, 1.0 = max)
            position = float(price - product.buy_price_min) / price_range

            # Linear scale: 100% at min (position=0) down to 60% at max (position=1)
            score = 100.0 - (position * 40.0)

        profit = product.get_potential_profit(listing.price)

        return (
            score,
            f"Price £{price:.0f} in range (£{product.buy_price_min}-£{product.buy_price_max}), "
            f"score: {score:.0f}%, profit: £{profit:.0f}",
        )
