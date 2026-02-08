import datetime
import hashlib
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class Settings:
    """Unified settings for Aetos Scraper"""

    # Matching
    MIN_CONFIDENCE_THRESHOLD: float = 70.0
    TITLE_WEIGHT: float = 0.6
    PRICE_WEIGHT: float = 0.3
    KEYWORD_WEIGHT: float = 0.1

    # Scraping
    MAX_LISTINGS_DEFAULT: int = 1000

    # API
    api_key: str = "your-secret-key-change-me"

    # Database
    db_host: str = "localhost"
    db_port: str = "5432"
    db_name: str = "aetos"
    db_user: str = "postgres"
    db_password: str = ""

    # Browser
    browser_headless: bool = True
    browser_window_size: str = "1920,1080"
    browser_user_agent: str = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
    browser_page_load_timeout: int = 30
    browser_implicit_wait: int = 10
    browser_enable_stealth: bool = True

    # Proxy
    proxy_enabled: bool = True
    proxy_provider: str = "iproyal"
    proxy_sticky_sessions: bool = True
    proxy_username: Optional[str] = None
    proxy_password: Optional[str] = None
    proxy_country: str = "gb"
    proxy_city: str = "edinburgh"

    # Paths
    cookies_dir: str = "cookies"
    logs_dir: str = "logs"
    screenshots_dir: str = "logs/screenshots"

    # Facebook credentials
    fb_user: Optional[str] = None
    fb_pass: Optional[str] = None

    # Environment detection
    is_docker: bool = False

    def __post_init__(self):
        """Load configuration after initialization"""
        self._detect_environment()
        self._load_from_yaml()
        self._load_from_env()
        self._ensure_directories()

    def _detect_environment(self):
        """Detect if running in Docker"""
        self.is_docker = os.path.exists("/.dockerenv") or os.path.exists(
            "/app/config.yaml"
        )

        if self.is_docker:
            self.cookies_dir = "/app/cookies"
            self.logs_dir = "/app/logs"
            self.screenshots_dir = "/app/logs/screenshots"

    def _load_from_yaml(self):
        """Load settings from config.yaml"""
        config_path = "/app/config.yaml" if self.is_docker else "config.yaml"

        if not os.path.exists(config_path):
            logger.info(f"[Settings] No config.yaml found at {config_path}")
            return

        try:
            with open(config_path, "r") as f:
                config = yaml.safe_load(f) or {}

            # Browser settings
            if "browser" in config:
                browser = config["browser"]
                self.browser_headless = browser.get("headless", self.browser_headless)
                self.browser_window_size = browser.get(
                    "window_size", self.browser_window_size
                )
                self.browser_user_agent = browser.get(
                    "user_agent", self.browser_user_agent
                )
                self.browser_page_load_timeout = browser.get(
                    "page_load_timeout", self.browser_page_load_timeout
                )
                self.browser_implicit_wait = browser.get(
                    "implicit_wait", self.browser_implicit_wait
                )
                self.browser_enable_stealth = browser.get(
                    "enable_stealth", self.browser_enable_stealth
                )

            # Proxy settings
            if "proxy" in config:
                proxy = config["proxy"]
                self.proxy_enabled = proxy.get("enabled", self.proxy_enabled)
                self.proxy_provider = proxy.get("provider", self.proxy_provider)
                self.proxy_sticky_sessions = proxy.get(
                    "sticky_sessions", self.proxy_sticky_sessions
                )

            # Path settings (only if not Docker)
            if "paths" in config and not self.is_docker:
                paths = config["paths"]
                self.cookies_dir = paths.get("cookies_dir", self.cookies_dir)
                self.logs_dir = paths.get("logs_dir", self.logs_dir)
                self.screenshots_dir = paths.get(
                    "screenshots_dir", self.screenshots_dir
                )

            logger.info("[Settings] Loaded config from config.yaml")

        except Exception as e:
            logger.warning(f"[Settings] Error loading config.yaml: {e}")

    def _load_from_env(self):
        """Load settings from environment variables"""
        # API
        self.api_key = os.getenv("API_KEY", self.api_key)

        # Database
        self.db_host = os.getenv("DB_HOST", self.db_host)
        self.db_port = os.getenv("DB_PORT", self.db_port)
        self.db_name = os.getenv("DB_NAME", self.db_name)
        self.db_user = os.getenv("DB_USER", self.db_user)
        self.db_password = os.getenv("DB_PASSWORD", self.db_password)

        # Proxy
        self.proxy_username = os.getenv("IPROYAL_USER")
        self.proxy_password = os.getenv("IPROYAL_PASS")
        self.proxy_country = os.getenv("PROXY_COUNTRY", self.proxy_country)

        cities = os.getenv("PROXY_CITIES", self.proxy_city)
        self.proxy_city = cities.split(",")[0] if cities else self.proxy_city

        if os.getenv("USE_PROXY"):
            self.proxy_enabled = os.getenv("USE_PROXY", "false").lower() == "true"

        # Facebook
        self.fb_user = os.getenv("GOOGLE_USER")  # Reusing for Facebook
        self.fb_pass = os.getenv("GOOGLE_PASS")

    def _ensure_directories(self):
        """Create required directories"""
        for dir_path in [self.cookies_dir, self.logs_dir, self.screenshots_dir]:
            Path(dir_path).mkdir(parents=True, exist_ok=True)

    def get_db_connection_string(self) -> str:
        """Get database connection string"""
        return (
            f"host={self.db_host} "
            f"port={self.db_port} "
            f"dbname={self.db_name} "
            f"user={self.db_user} "
            f"password={self.db_password} "
            f"sslmode=require"
        )

    def get_proxy_url(self) -> Optional[str]:
        """Get proxy URL with sticky session"""
        if not self.proxy_enabled or not self.proxy_username or not self.proxy_password:
            return None

        if self.proxy_provider == "iproyal":
            parts = [f"country-{self.proxy_country}"]

            if self.proxy_city:
                parts.append(f"city-{self.proxy_city}")

            if self.proxy_sticky_sessions:
                session_id = hashlib.md5(
                    f"fb-messenger-{datetime.date.today()}".encode()
                ).hexdigest()[:8]
                parts.append(f"session-{session_id}")

            password = f"{self.proxy_password}_{'_'.join(parts)}"
            return f"http://{self.proxy_username}:{password}@geo.iproyal.com:12321"

        return None

    def validate(self) -> bool:
        """Validate required settings"""
        if not self.db_password:
            logger.error("[Settings] DB_PASSWORD not set")
            return False
        return True


# Singleton instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get settings singleton"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
