import logging
from typing import Dict, List

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

    def get_filter_keywords(self) -> Dict[str, List[str]]:
        """Get all filter keywords (reject and boost)"""
        logger.info("Fetching filter keywords")
        keywords_dict = self.product_repository.get_global_filter_keywords()

        reject = keywords_dict.get("reject", [])
        boost = keywords_dict.get("boost", [])

        logger.info(
            f"Loaded {len(reject)} reject keywords: {reject[:5] if reject else []}"
        )
        logger.info(f"Loaded {len(boost)} boost keywords: {boost[:5] if boost else []}")

        return keywords_dict
    
    def get_products_for_brands(self, brands: List[str]) -> List[Product]:
        products = self.product_repository.get_active_products_by_brands(brands)
        logger.info(f"Found {len(products)} products across {brands}")
        
        return products
