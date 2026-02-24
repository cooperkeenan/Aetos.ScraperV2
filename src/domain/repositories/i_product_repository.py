from abc import ABC, abstractmethod
from typing import Dict, List

from ..models.product import Product


class IProductRepository(ABC):

    @abstractmethod
    def get_active_products_by_brand(self, brand: str) -> List[Product]:
        pass

    @abstractmethod
    def get_active_products_by_brands(self, brands: List[str]) -> List[Product]:
        pass

    @abstractmethod
    def get_all_active_products(self) -> List[Product]:
        pass

    @abstractmethod
    def get_brands(self) -> List[str]:
        pass

    @abstractmethod
    def get_global_filter_keywords(self) -> Dict[str, List[str]]:
        pass