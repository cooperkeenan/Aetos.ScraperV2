# src/services/session_service.py
import logging
import os
import pickle
from typing import List, Dict, Optional, Any

from ..core.config_service import ConfigService


logger = logging.getLogger(__name__)


class SessionService:
    
    def __init__(self, config: ConfigService):
        self.config = config
        self.cookie_file = os.path.join(config.paths.cookies_dir, "fb_cookies.pkl")
    
    
    def load_cookies(self) -> Optional[List[Dict[str, Any]]]:
        try:
            if not os.path.exists(self.cookie_file):
                logger.info("[Session] No cookies found")
                return None
            
            with open(self.cookie_file, 'rb') as f:
                cookies = pickle.load(f)
            
            logger.info("[Session] Loaded %s cookies", len(cookies))
            return cookies
            
        except Exception as e:
            logger.error("[Session] Failed to load cookies: %s", e)
            return None
    

    def validate_cookies(self, cookies: List[Dict[str, Any]]) -> bool:
        if not cookies:
            return False
        
        # Check for essential Facebook cookies
        cookie_names = {cookie.get('name') for cookie in cookies}
        essential = {'c_user', 'xs'}
        
        if not essential.issubset(cookie_names):
            logger.warning("[Session] Missing essential cookies")
            return False
        
        logger.info("[Session] Cookies valid")
        return True
