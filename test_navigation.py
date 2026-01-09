#!/usr/bin/env python3
"""
Test Facebook Marketplace Scraper
Logs in, searches for "canon", prints first 3 results
"""

from dotenv import load_dotenv
from src.core.config_service import get_config
from src.services.browser_service import BrowserService
from src.services.proxy_service import ProxyService
from src.services.facebook_service import FacebookService
from src.services.session_service import SessionService
from src.scraper.marketplace_scraper import MarketplaceScraper

load_dotenv()


def test_navigation():
    """Test marketplace scraping with saved cookies"""
    
    SEARCH_QUERY = "canon"
    MAX_RESULTS = 3
    
    print("="*80)
    print("🧪 Testing Facebook Marketplace Scraper")
    print("="*80)
    
    try:
        # Setup services
        config = get_config()
        proxy_service = ProxyService() if config.proxy.enabled else None
        
        # Test proxy if enabled
        if proxy_service:
            print("\n[Test] Testing proxy...")
            ip = proxy_service.test_proxy(proxy_service.get_proxy_url())
            if not ip:
                print("[Test] ⚠️  Proxy test failed, continuing anyway...")
        
        # Create services
        browser = BrowserService(config, proxy_service)
        session = SessionService(config)
        facebook = FacebookService(config, browser, session)
        
        with browser:
            # Restore session
            print("\n[Test] Restoring Facebook session...")
            if not facebook.restore_session():
                print("[Test] ❌ No valid session found!")
                print("[Test] Run your messenger bot first to generate cookies")
                return
            
            print("[Test] ✅ Session restored")
            
            # Create scraper
            scraper = MarketplaceScraper(browser.get_driver())
            
            # Search
            print(f"\n[Test] Searching for '{SEARCH_QUERY}'...")
            if not scraper.search(SEARCH_QUERY):
                print("[Test] ❌ Search failed")
                browser.take_screenshot("search_failed")
                return
            
            # Collect results
            print(f"\n[Test] Collecting first {MAX_RESULTS} results...")
            listings = scraper.scroll_and_collect(max_listings=MAX_RESULTS)
            
            if not listings:
                print("[Test] ❌ No listings found")
                browser.take_screenshot("no_listings")
                return
            
            # Print results
            scraper.print_listings(listings, limit=MAX_RESULTS)
            
            print("[Test] ✅ Test completed successfully!")
            
    except Exception as e:
        print(f"\n[Test] ❌ Test failed: {e}")
        if 'browser' in locals():
            browser.take_screenshot("test_error")
        raise


if __name__ == "__main__":
    test_navigation()