"""PostgreSQL implementation of Product repository"""

import logging
from typing import Dict, List

import psycopg2
from psycopg2.extras import RealDictCursor

from ....domain.models.product import Product
from ....domain.repositories.i_product_repository import IProductRepository

logger = logging.getLogger(__name__)


class ProductRepository(IProductRepository):

    def __init__(self, connection_string: str):
        self.connection_string = connection_string

    def _get_connection(self):
        return psycopg2.connect(self.connection_string)

    def get_active_products_by_brand(self, brand: str) -> List[Product]:
        query = """
            SELECT 
                p.id, p.brand, p.model, p.full_name, p.category,
                p.buy_price_min, p.buy_price_max, p.sell_target, p.active
            FROM products p
            WHERE p.brand = %s AND p.active = true
            ORDER BY p.model
        """

        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(query, (brand,))
                    rows = cur.fetchall()

                    products = []
                    for row in rows:
                        product = self._row_to_product(row)
                        product.fuzzy_patterns = self._get_fuzzy_patterns(
                            product.id, cur
                        )
                        product.aliases = self._get_aliases(product.id, cur)
                        products.append(product)

                    logger.info(f"Loaded {len(products)} products for brand '{brand}'")
                    return products

        except Exception as e:
            logger.error(f"Failed to get products for brand '{brand}': {e}")
            raise

    def get_all_active_products(self) -> List[Product]:
        query = """
            SELECT 
                p.id, p.brand, p.model, p.full_name, p.category,
                p.buy_price_min, p.buy_price_max, p.sell_target, p.active
            FROM products p
            WHERE p.active = true
            ORDER BY p.brand, p.model
        """

        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(query)
                    rows = cur.fetchall()

                    products = []
                    for row in rows:
                        product = self._row_to_product(row)
                        product.fuzzy_patterns = self._get_fuzzy_patterns(
                            product.id, cur
                        )
                        product.aliases = self._get_aliases(product.id, cur)
                        products.append(product)

                    logger.info(f"Loaded {len(products)} active products")
                    return products

        except Exception as e:
            logger.error(f"Failed to get all active products: {e}")
            raise

    def get_brands(self) -> List[str]:
        query = """
            SELECT DISTINCT brand
            FROM products
            WHERE active = true
            ORDER BY brand
        """

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query)
                    brands = [row[0] for row in cur.fetchall()]
                    logger.info(f"Loaded {len(brands)} brands")
                    return brands

        except Exception as e:
            logger.error(f"Failed to get brands: {e}")
            raise

    def get_global_filter_keywords(self) -> Dict[str, List[str]]:
        query = """
            SELECT filter_type, keyword
            FROM filter_keywords
            ORDER BY filter_type, keyword
        """

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query)

                    keywords = {}
                    for filter_type, keyword in cur.fetchall():
                        if filter_type not in keywords:
                            keywords[filter_type] = []
                        keywords[filter_type].append(keyword)

                    logger.info(
                        f"Loaded filter keywords: {dict((k, len(v)) for k, v in keywords.items())}"
                    )
                    return keywords

        except Exception as e:
            logger.error(f"Failed to get filter keywords: {e}")
            raise
    
    def get_active_products_by_brands(self, brands: List[str]) -> List[Product]:
        query = """
            SELECT 
                p.id, p.brand, p.model, p.full_name, p.category,
                p.buy_price_min, p.buy_price_max, p.sell_target, p.active
            FROM products p
            WHERE p.brand = ANY(%s) AND p.active = true
            ORDER BY p.brand, p.model
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(query, (brands,))
                    rows = cur.fetchall()

                    products = []
                    for row in rows:
                        product = self._row_to_product(row)
                        product.fuzzy_patterns = self._get_fuzzy_patterns(product.id, cur)
                        product.aliases = self._get_aliases(product.id, cur)
                        products.append(product)

                    logger.info(f"Loaded {len(products)} products for brands {brands}")
                    return products

        except Exception as e:
            logger.error(f"Failed to get products for brands {brands}: {e}")
            raise

    def _get_fuzzy_patterns(self, product_id: int, cursor) -> List[str]:
        cursor.execute(
            "SELECT pattern FROM product_fuzzy_patterns WHERE product_id = %s",
            (product_id,),
        )
        return [row['pattern'] for row in cursor.fetchall()]

    def _get_aliases(self, product_id: int, cursor) -> List[str]:
        cursor.execute(
            "SELECT alias FROM product_aliases WHERE product_id = %s", (product_id,)
        )
        return [row['alias'] for row in cursor.fetchall()]

    def _row_to_product(self, row: dict) -> Product:
        return Product(
            id=row["id"],
            brand=row["brand"],
            model=row["model"],
            full_name=row["full_name"],
            category=row["category"],
            buy_price_min=row["buy_price_min"],
            buy_price_max=row["buy_price_max"],
            sell_target=row["sell_target"],
            active=row["active"],
            fuzzy_patterns=[],
            aliases=[],
        )