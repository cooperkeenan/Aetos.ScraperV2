import logging
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import List, Optional, Set

import psycopg2
from psycopg2.extras import RealDictCursor

from ....domain.repositories.i_listing_repository import IListingRepository

logger = logging.getLogger(__name__)


class ListingRepository(IListingRepository):
    """Simple listing history repository - tracks seen URLs from last 7 days only"""

    def __init__(self, connection_string: str):
        self.connection_string = connection_string

    @contextmanager
    def _get_cursor(self, dict_cursor=False):
        conn = psycopg2.connect(self.connection_string)
        try:
            cursor_factory = RealDictCursor if dict_cursor else None
            cursor = conn.cursor(cursor_factory=cursor_factory)
            try:
                yield cursor
                conn.commit()
            finally:
                cursor.close()
        finally:
            conn.close()

    def add_listing(
        self,
        url: str,
        title: Optional[str] = None,
        price: Optional[float] = None,
        location: Optional[str] = None,
        description: Optional[str] = None,
    ) -> None:
        query = """
            INSERT INTO listing_history (url, title, price, location, description)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (url) DO NOTHING
        """

        try:
            with self._get_cursor() as cur:
                cur.execute(query, (url, title, price, location, description))
                logger.debug(f"Added listing: {url[:50]}...")

        except Exception as e:
            logger.error(f"Failed to add listing {url}: {e}")
            raise


    def urls_exist(self, urls: List[str]) -> Set[str]:
      
        if not urls:
            return set()

        seven_days_ago = datetime.now() - timedelta(days=7)

        query = """
            SELECT url 
            FROM listing_history 
            WHERE url = ANY(%s)
            AND created_at >= %s
        """

        try:
            with self._get_cursor() as cur:
                cur.execute(query, (urls, seven_days_ago))
                existing_urls = {row[0] for row in cur.fetchall()}
                
                logger.info(
                    f"Found {len(existing_urls)} URLs seen in last 7 days (out of {len(urls)} checked)"
                )
                return existing_urls

        except Exception as e:
            logger.error(f"Failed to check URLs: {e}")
            return set()
