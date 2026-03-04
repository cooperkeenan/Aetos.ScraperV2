from abc import ABC, abstractmethod
from typing import Tuple

from ...domain.models.listing import Listing
from ...domain.models.product import Product


class BaseMatcher(ABC):

    @abstractmethod
    def match(self, listing: Listing, product: Product) -> Tuple[float, str]:
        """Return a (score, reason) tuple for a listing/product pair."""
        raise NotImplementedError
