# src/scraper/marketplace_scraper.py
"""
Facebook Marketplace Scraper
Searches and extracts listing data
"""

import time
import random
from typing import List, Dict, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class MarketplaceScraper:
    """
    Scrapes Facebook Marketplace listings
    """
    
    def __init__(self, driver):
        self.driver = driver
        self.base_url = "https://www.facebook.com/marketplace"
        
    def search(self, query: str, location: Optional[str] = None) -> bool:
        """
        Navigate to marketplace and search for query
        
        Args:
            query: Search term (e.g., "canon camera")
            location: Optional location filter
            
        Returns:
            True if search successful, False otherwise
        """
        print(f"[Scraper] 🔍 Searching for: '{query}'")
        
        try:
            # Navigate to marketplace
            search_url = f"{self.base_url}/search"
            if location:
                search_url += f"?location={location}"
            
            self.driver.get(search_url)
            self._human_delay(2, 4)
            
            # Find search input
            search_input = self._find_search_input()
            if not search_input:
                print("[Scraper] ❌ Search input not found")
                return False
            
            # Type search query
            print(f"[Scraper] ⌨️  Typing query...")
            search_input.clear()
            self._human_type(search_input, query)
            
            # Press Enter
            search_input.send_keys(Keys.RETURN)
            self._human_delay(3, 5)
            
            print("[Scraper] ✅ Search submitted")
            return True
            
        except Exception as e:
            print(f"[Scraper] ❌ Search failed: {e}")
            return False
    
    def _find_search_input(self) -> Optional[any]:
        """Find the marketplace search input"""
        selectors = [
            "input[placeholder*='Search' i]",
            "input[aria-label*='Search' i]",
            "input[type='search']",
            "input[placeholder*='What are you looking for' i]"
        ]
        
        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        return element
            except:
                continue
        
        return None
    
    def scroll_and_collect(self, max_listings: int = 50) -> List[Dict]:
        """
        Scroll through results and collect listings
        
        Args:
            max_listings: Maximum number of listings to collect
            
        Returns:
            List of listing dictionaries
        """
        print(f"[Scraper] 📜 Scrolling to collect up to {max_listings} listings...")
        
        listings = []
        seen_urls = set()
        scroll_attempts = 0
        max_scroll_attempts = 20
        
        while len(listings) < max_listings and scroll_attempts < max_scroll_attempts:
            # Extract current visible listings
            new_listings = self._extract_visible_listings(seen_urls)
            
            if new_listings:
                listings.extend(new_listings)
                print(f"[Scraper] 📦 Collected {len(listings)}/{max_listings} listings")
            
            # Scroll down
            self._scroll_down()
            scroll_attempts += 1
            
            # Check if no new listings after 3 attempts
            if scroll_attempts % 3 == 0 and not new_listings:
                print("[Scraper] No new listings found, stopping")
                break
            
            self._human_delay(1, 2)
        
        print(f"[Scraper] ✅ Collected {len(listings)} total listings")
        return listings[:max_listings]
    
    def _extract_visible_listings(self, seen_urls: set) -> List[Dict]:
        """Extract listings currently visible on page"""
        new_listings = []
        
        try:
            # Facebook marketplace listings are in <a> tags with href="/marketplace/item/"
            listing_links = self.driver.find_elements(
                By.CSS_SELECTOR, 
                "a[href*='/marketplace/item/']"
            )
            
            for link in listing_links:
                try:
                    url = link.get_attribute('href')
                    
                    # Skip if already seen
                    if url in seen_urls or not url:
                        continue
                    
                    # Extract listing data
                    listing = self._extract_listing_data(link, url)
                    
                    if listing:
                        new_listings.append(listing)
                        seen_urls.add(url)
                
                except Exception as e:
                    # Skip individual listing errors
                    continue
        
        except Exception as e:
            print(f"[Scraper] ⚠️  Error extracting listings: {e}")
        
        return new_listings
    
    def _extract_listing_data(self, element, url: str) -> Optional[Dict]:
        """Extract data from a single listing element"""
        try:
            # Get parent container (usually contains image + details)
            parent = element
            for _ in range(3):  # Go up 3 levels to find container
                parent = parent.find_element(By.XPATH, '..')
            
            # Extract title
            title = self._extract_title(element)
            if not title:
                return None
            
            # Extract price
            price = self._extract_price(parent)
            
            # Extract image URL
            image_url = self._extract_image(parent)
            
            # Extract location (optional)
            location = self._extract_location(parent)
            
            listing = {
                'url': url,
                'title': title,
                'price': price,
                'image_url': image_url,
                'location': location,
                'scraped_at': time.time()
            }
            
            return listing
            
        except Exception as e:
            return None
    
    def _extract_title(self, element) -> Optional[str]:
        """Extract listing title"""
        try:
            # Try aria-label first
            aria_label = element.get_attribute('aria-label')
            if aria_label:
                return aria_label.strip()
            
            # Try text content
            text = element.text.strip()
            if text:
                return text.split('\n')[0]  # First line is usually title
            
            return None
        except:
            return None
    
    def _extract_price(self, element) -> Optional[float]:
        """Extract listing price"""
        try:
            # Look for price text (usually starts with £ or $)
            text_elements = element.find_elements(By.XPATH, ".//*[contains(text(), '£') or contains(text(), '$')]")
            
            for text_elem in text_elements:
                text = text_elem.text.strip()
                
                # Extract numbers from price text
                import re
                price_match = re.search(r'[£$]?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)', text)
                if price_match:
                    price_str = price_match.group(1).replace(',', '')
                    return float(price_str)
            
            return None
        except:
            return None
    
    def _extract_image(self, element) -> Optional[str]:
        """Extract listing image URL"""
        try:
            img_elements = element.find_elements(By.TAG_NAME, 'img')
            for img in img_elements:
                src = img.get_attribute('src')
                if src and 'fbcdn.net' in src:
                    return src
            return None
        except:
            return None
    
    def _extract_location(self, element) -> Optional[str]:
        """Extract listing location"""
        try:
            # Location is usually in the description area
            # This is optional and might not always work
            text = element.text
            lines = text.split('\n')
            
            # Location is often after price
            for line in lines:
                if any(word in line.lower() for word in ['mile', 'km', 'away']):
                    return line.strip()
            
            return None
        except:
            return None
    
    def _scroll_down(self):
        """Scroll down the page"""
        try:
            # Scroll to bottom
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # Alternative: Scroll by viewport height
            # self.driver.execute_script("window.scrollBy(0, window.innerHeight);")
        except:
            pass
    
    def _human_type(self, element, text: str):
        """Type text with human-like delays"""
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))
    
    def _human_delay(self, min_seconds: float = 1, max_seconds: float = 3):
        """Add human-like delay"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
    
    def print_listings(self, listings: List[Dict], limit: int = 3):
        """Pretty print listings for testing"""
        print("\n" + "="*80)
        print(f"📋 FOUND {len(listings)} LISTINGS")
        print("="*80)
        
        for i, listing in enumerate(listings[:limit], 1):
            price_str = f"£{listing['price']:.0f}" if listing.get('price') else "Price unknown"
            location_str = f" - {listing['location']}" if listing.get('location') else ""
            
            print(f"\n{i}. {listing['title']}")
            print(f"   💰 {price_str}{location_str}")
            print(f"   🔗 {listing['url']}")
            
        if len(listings) > limit:
            print(f"\n... and {len(listings) - limit} more")
        
        print("\n" + "="*80 + "\n")