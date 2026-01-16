import logging
from typing import List

from ..domain.models.product import Product
from ..domain.repositories.i_product_repository import IProductRepository

logger = logging.getLogger(__name__)


class ProductService:
    """Service for product-related business logic"""

    def __init__(self, product_repository: IProductRepository):
        self.product_repository = product_repository

    def get_products_for_brand(self, brand: str) -> List[Product]:

        logger.info(f"Fetching products for brand: {brand}")
        products = self.product_repository.get_active_products_by_brand(brand)
        logger.info(f"Found {len(products)} products for {brand}")
        return products

    def get_avoid_keywords(self) -> List[str]:
        """Get global avoid keywords"""
        logger.info("Fetching avoid keywords")
        keywords_dict = self.product_repository.get_global_filter_keywords()
        avoid_keywords = keywords_dict.get("avoid", [])
        logger.info(f"Loaded {len(avoid_keywords)} avoid keywords")
        return avoid_keywords
