import logging
import os
from typing import Dict, List

import requests

from ..application.product_service import ProductService
from ..application.scraping_orchestration import ScrapingOrchestrator
from ..core.settings import get_settings
from ..infrastructure.database.connection import get_connection_string
from ..infrastructure.database.repositories.listing_repository import ListingRepository
from ..infrastructure.database.repositories.product_repository import ProductRepository
from ..services.browser_service import BrowserService
from ..services.facebook_service import FacebookService
from ..services.proxy_service import ProxyService
from ..services.session_service import SessionService
from .models import JobStatus, JobStatusResponse

logger = logging.getLogger(__name__)

ORCHESTRATOR_WEBHOOK_URL = os.getenv(
    "ORCHESTRATOR_WEBHOOK_URL",
    "https://aetos-orchestrator-func-gycubdb8cxd0fsgs.uksouth-01.azurewebsites.net/api/webhooks/scraper/job-complete",
)
ORCHESTRATOR_API_KEY = os.getenv("ORCHESTRATOR_API_KEY", "aetos-production-key-2024")


class SessionExecutor:

    def __init__(self, jobs: Dict[str, JobStatusResponse]):
        self.jobs = jobs

    def execute(self, job_id: str, brands: List[str], search_term: str, require_price_match: bool = True):
        logger.info(f"[Job {job_id}] Starting scrape for brands: {brands}, search: {search_term}")
        self.jobs[job_id].status = JobStatus.RUNNING

        try:
            settings = get_settings()
            connection_string = get_connection_string()

            product_service = ProductService(ProductRepository(connection_string))
            proxy_service = ProxyService() if settings.proxy_enabled else None
            browser = BrowserService(settings, proxy_service)
            facebook = FacebookService(settings, browser, SessionService(settings))

            with browser:
                if not facebook.restore_session():
                    raise Exception("Failed to restore Facebook session")

                result = ScrapingOrchestrator(
                    product_service,
                    browser.get_driver(),
                    ListingRepository(connection_string),
                ).scrape_and_match_brand(brands, search_term, require_price_match=require_price_match)

            self.jobs[job_id].status = JobStatus.COMPLETED
            self.jobs[job_id].result = result
            logger.info(f"[Job {job_id}] Completed - Found {result['stats'].get('total_matches', 0)} matches")

            self._notify_orchestrator(job_id, brands, result)

        except Exception as e:
            logger.error(f"[Job {job_id}] Failed: {e}", exc_info=True)
            self.jobs[job_id].status = JobStatus.FAILED
            self.jobs[job_id].error = str(e)


    def _notify_orchestrator(self, job_id: str, brands: List[str], result: dict) -> None:
        payload = {
            "job_id": job_id,
            "brands": brands,
            "matches": result.get("matches", []),
        }
        try:
            response = requests.post(
                ORCHESTRATOR_WEBHOOK_URL,
                json=payload,
                headers={"x-api-key": ORCHESTRATOR_API_KEY},
                timeout=30,
            )
            response.raise_for_status()
            logger.info(f"[Job {job_id}] Orchestrator notified - {response.status_code}")
        except Exception as e:
            logger.error(f"[Job {job_id}] Failed to notify orchestrator: {e}")