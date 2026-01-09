
import os
import yaml
from typing import Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class BrowserConfig:
    headless: bool = True
    window_size: str = "1920,1080"
    user_agent: str = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
    page_load_timeout: int = 30
    implicit_wait: int = 10
    enable_stealth: bool = True


@dataclass
class ProxyConfig:
    enabled: bool = False
    provider: str = "iproyal"
    sticky_sessions: bool = True
    username: Optional[str] = None
    password: Optional[str] = None
    country: str = "gb"
    city: str = "edinburgh"


@dataclass
class PathConfig:
    cookies_dir: str = "/app/cookies"
    logs_dir: str = "/app/logs"
    screenshots_dir: str = "/app/logs/screenshots"


class ConfigService:
    
    def __init__(self, config_path: str = None):
        if config_path is None:
            # Try local config first, fallback to /app/config.yaml for Docker
            if os.path.exists("config.yaml"):
                config_path = "config.yaml"
            elif os.path.exists("/app/config.yaml"):
                config_path = "/app/config.yaml"
            else:
                config_path = "config.yaml"  # Will show "not found" message
        
        self.config_path = config_path
        self.config_path = config_path
        self.browser = BrowserConfig()
        self.proxy = ProxyConfig()
        self.paths = PathConfig()
        
        self._load_config()
        self._load_env_vars()
        self._ensure_directories()
    
    def _load_config(self) -> None:
        try:
            if not os.path.exists(self.config_path):
                print(f"[Config] No config at {self.config_path}, using defaults")
                return
            
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f) or {}
            
            # Apply browser config
            if 'browser' in config:
                for key, value in config['browser'].items():
                    if hasattr(self.browser, key):
                        setattr(self.browser, key, value)
            
            # Apply proxy config
            if 'proxy' in config:
                for key, value in config['proxy'].items():
                    if hasattr(self.proxy, key):
                        setattr(self.proxy, key, value)
            
            # Apply paths config
            if 'paths' in config:
                for key, value in config['paths'].items():
                    if hasattr(self.paths, key):
                        setattr(self.paths, key, value)
        
        except Exception as e:
            print(f"[Config] Error loading: {e}, using defaults")
    
    def _load_env_vars(self) -> None:
        # Proxy credentials
        self.proxy.username = os.getenv("IPROYAL_USER")
        self.proxy.password = os.getenv("IPROYAL_PASS")
        self.proxy.country = os.getenv("PROXY_COUNTRY", self.proxy.country)
        
        cities = os.getenv("PROXY_CITIES", self.proxy.city)
        self.proxy.city = cities.split(',')[0] if cities else self.proxy.city
        
        if os.getenv("USE_PROXY"):
            self.proxy.enabled = os.getenv("USE_PROXY", "false").lower() == "true"
    
    def _ensure_directories(self) -> None:
        for attr in ['cookies_dir', 'logs_dir', 'screenshots_dir']:
            path = getattr(self.paths, attr)
            Path(path).mkdir(parents=True, exist_ok=True)
    
    def get_proxy_url(self) -> Optional[str]:
        if not self.proxy.enabled or not self.proxy.username or not self.proxy.password:
            return None
        
        if self.proxy.provider == "iproyal":
            import hashlib
            import datetime
            
            parts = [f"country-{self.proxy.country}"]
            if self.proxy.city:
                parts.append(f"city-{self.proxy.city}")
            
            if self.proxy.sticky_sessions:
                session_id = hashlib.md5(
                    f"fb-messenger-{datetime.date.today()}".encode()
                ).hexdigest()[:8]
                parts.append(f"session-{session_id}")
            
            password = f"{self.proxy.password}_{'_'.join(parts)}"
            return f"http://{self.proxy.username}:{password}@geo.iproyal.com:12321"
        
        return None


_config_instance: Optional[ConfigService] = None


def get_config() -> ConfigService:
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigService()
    return _config_instance