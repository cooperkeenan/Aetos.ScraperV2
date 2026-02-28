import logging
import os
import pickle
from typing import List, Optional

from ..core.settings import Settings

logger = logging.getLogger(__name__)


class SessionService:
    """Handles cookie loading and validation"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.cookie_path = os.path.join(settings.logs_dir, "fb_cookies.pkl")

    def load_cookies(self) -> Optional[List[dict]]:
        """Load cookies from file"""
        try:
            if not os.path.exists(self.cookie_path):
                logger.info("[Session] No saved cookies found")
                return None

            with open(self.cookie_path, "rb") as f:
                cookies = pickle.load(f)

            logger.info(f"[Session] Loaded {len(cookies)} cookies")
            return cookies

        except Exception as e:
            logger.warning(f"[Session] Failed to load cookies: {e}")
            return None

    def validate_cookies(self, cookies: List[dict]) -> bool:
        """Validate cookies have required fields"""
        if not cookies:
            return False

        required_fields = ["name", "value", "domain"]

        for cookie in cookies:
            if not all(field in cookie for field in required_fields):
                logger.warning("[Session] Cookie missing required fields")
                return False

        logger.info("[Session] Cookies valid")
        return True
