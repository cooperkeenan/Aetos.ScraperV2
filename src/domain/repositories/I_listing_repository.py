from abc import ABC, abstractmethod
from typing import List, Optional, Set

from ..models.listing import Listing


class IListingRepository(ABC):

    @abstractmethod
    def upsert_listing(
        self, 
        url: str,
        title: Optional[str] = None,
        price: Optional[float] = None,
        location: Optional[str] = None,
        image_url: Optional[str] = None,
        description: Optional[str] = None,
        product_id: Optional[int] = None,
        match_confidence: Optional[float] = None
    ) -> int:
        """
        Insert or update listing
        - If URL exists: update last_seen_at, times_seen, and other fields if provided
        - If URL is new: insert new record
        
        Returns listing_id
        """
        pass

    @abstractmethod
    def get_listing_by_url(self, url: str) -> Optional[Listing]:
        """Get listing by URL"""
        pass

    @abstractmethod
    def get_analyzed_urls(self, urls: List[str]) -> Set[str]:
        """
        Get URLs that have already been analyzed (have product_id)
        Returns set of URLs that were already matched to products
        """
        pass

    @abstractmethod
    def mark_as_sold(self, listing_id: int) -> bool:
        """Mark listing as sold"""
        pass

    @abstractmethod
    def get_recent_listings(self, limit: int = 100) -> List[Listing]:
        """Get most recently seen listings"""
        pass

    @abstractmethod
    def get_listings_by_product(self, product_id: int) -> List[Listing]:
        """Get all listings matched to a product"""
        pass