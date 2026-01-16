from abc import ABC, abstractmethod
from typing import Dict, List

from ..models.product import Product


class IProductRepository(ABC):

    @abstractmethod
    def get_active_products_by_brand(self, brand: str) -> List[Product]:
        """
        Get all active products for a specific brand

        Args:
            brand: Brand name (e.g., "Canon")

        Returns:
            List of Product entities with patterns and aliases loaded
        """
        pass

    @abstractmethod
    def get_all_active_products(self) -> List[Product]:
        """
        Get all active products

        Returns:
            List of all active Product entities
        """
        pass

    @abstractmethod
    def get_brands(self) -> List[str]:
        """
        Get list of unique brands that have active products

        Returns:
            List of brand names
        """
        pass

    @abstractmethod
    def get_global_filter_keywords(self) -> Dict[str, List[str]]:
        """
        Get global filter keywords by type

        Returns:
            Dictionary with filter_type as key, list of keywords as value
            Example: {'avoid': ['damaged', 'broken'], 'require': ['original']}
        """
        pass
