import logging
from typing import List, Optional

import psycopg2
from psycopg2.extras import RealDictCursor

from ....domain.models.listing import Listing
from ....domain.repositories.i_listing_repository import IListingRepository

logger = logging.getLogger(__name__)


class ListingRepository(IListingRepository):

    def __init__(self, connection_string: str):
        self.connection_string = connection_string

    def _get_connection(self):
        return psycopg2.connect(self.connection_string)

    def upsert_listing(
        self,
        url: str,
        title: Optional[str] = None,
        price: Optional[float] = None,
        location: Optional[str] = None,
        image_url: Optional[str] = None,
        description: Optional[str] = None,
        product_id: Optional[int] = None,
        match_confidence: Optional[float] = None,
    ) -> int:
        """
        Insert new listing or update if URL exists
        Tracks price changes and updates timestamps
        """
        query = """
            INSERT INTO listings (
                url, title, price, location, image_url, description,
                product_id, match_confidence, first_seen_at, last_seen_at, 
                last_price, times_seen
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), %s, 1)
            ON CONFLICT (url) DO UPDATE SET
                title = COALESCE(EXCLUDED.title, listings.title),
                location = COALESCE(EXCLUDED.location, listings.location),
                image_url = COALESCE(EXCLUDED.image_url, listings.image_url),
                description = COALESCE(EXCLUDED.description, listings.description),
                product_id = COALESCE(EXCLUDED.product_id, listings.product_id),
                match_confidence = COALESCE(EXCLUDED.match_confidence, listings.match_confidence),
                last_seen_at = NOW(),
                times_seen = listings.times_seen + 1,
                price = CASE 
                    WHEN EXCLUDED.price IS NOT NULL AND EXCLUDED.price != listings.price 
                    THEN EXCLUDED.price 
                    ELSE listings.price 
                END,
                price_changed_at = CASE 
                    WHEN EXCLUDED.price IS NOT NULL AND EXCLUDED.price != listings.price 
                    THEN NOW() 
                    ELSE listings.price_changed_at 
                END,
                last_price = CASE 
                    WHEN EXCLUDED.price IS NOT NULL AND EXCLUDED.price != listings.price 
                    THEN listings.price 
                    ELSE listings.last_price 
                END
            RETURNING id
        """

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        query,
                        (
                            url,
                            title,
                            price,
                            location,
                            image_url,
                            description,
                            product_id,
                            match_confidence,
                            price,
                        ),
                    )
                    listing_id = cur.fetchone()[0]
                    conn.commit()
                    
                    logger.info(f"Upserted listing {listing_id}: {url[:50]}...")
                    return listing_id

        except Exception as e:
            logger.error(f"Failed to upsert listing {url}: {e}")
            raise

    def get_listing_by_url(self, url: str) -> Optional[Listing]:
        query = """
            SELECT url, title, price, location, image_url, description,
                   first_seen_at
            FROM listings
            WHERE url = %s
        """

        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(query, (url,))
                    row = cur.fetchone()

                    if row:
                        return Listing(
                            url=row["url"],
                            title=row["title"],
                            price=float(row["price"]) if row["price"] else None,
                            location=row["location"],
                            image_url=row["image_url"],
                            description=row["description"],
                            scraped_at=row["first_seen_at"].timestamp()
                            if row["first_seen_at"]
                            else None,
                        )
                    return None

        except Exception as e:
            logger.error(f"Failed to get listing {url}: {e}")
            return None

    def mark_as_sold(self, listing_id: int) -> bool:
        query = "UPDATE listings SET status = 'sold' WHERE id = %s"

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (listing_id,))
                    conn.commit()
                    return True

        except Exception as e:
            logger.error(f"Failed to mark listing {listing_id} as sold: {e}")
            return False

    def get_recent_listings(self, limit: int = 100) -> List[Listing]:
        query = """
            SELECT url, title, price, location, image_url, description,
                   first_seen_at
            FROM listings
            WHERE status = 'active'
            ORDER BY last_seen_at DESC
            LIMIT %s
        """

        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(query, (limit,))
                    rows = cur.fetchall()

                    return [
                        Listing(
                            url=row["url"],
                            title=row["title"],
                            price=float(row["price"]) if row["price"] else None,
                            location=row["location"],
                            image_url=row["image_url"],
                            description=row["description"],
                            scraped_at=row["first_seen_at"].timestamp()
                            if row["first_seen_at"]
                            else None,
                        )
                        for row in rows
                    ]

        except Exception as e:
            logger.error(f"Failed to get recent listings: {e}")
            return []

    def get_listings_by_product(self, product_id: int) -> List[Listing]:
        query = """
            SELECT url, title, price, location, image_url, description,
                   first_seen_at
            FROM listings
            WHERE product_id = %s AND status = 'active'
            ORDER BY last_seen_at DESC
        """

        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(query, (product_id,))
                    rows = cur.fetchall()

                    return [
                        Listing(
                            url=row["url"],
                            title=row["title"],
                            price=float(row["price"]) if row["price"] else None,
                            location=row["location"],
                            image_url=row["image_url"],
                            description=row["description"],
                            scraped_at=row["first_seen_at"].timestamp()
                            if row["first_seen_at"]
                            else None,
                        )
                        for row in rows
                    ]

        except Exception as e:
            logger.error(f"Failed to get listings for product {product_id}: {e}")
            return []