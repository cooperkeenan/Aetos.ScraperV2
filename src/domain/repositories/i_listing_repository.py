from abc import ABC, abstractmethod
from typing import List, Optional, Set


class IListingRepository(ABC):

    @abstractmethod
    def add_listing(
        self,
        url: str,
        title: Optional[str] = None,
        price: Optional[float] = None,
        location: Optional[str] = None,
        description: Optional[str] = None,
    ) -> None:
        """
        Add new listing to history
        Does nothing if URL already exists
        """
        pass

    @abstractmethod
    def urls_exist(self, urls: List[str]) -> Set[str]:
        """
        Check which URLs have been seen in the last 7 days (batch operation)
        Returns set of URLs that already exist in recent history
        """
        pass
