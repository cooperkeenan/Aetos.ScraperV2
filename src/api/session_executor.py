import logging
from typing import Dict

from ..application.product_service import ProductService
from ..application.scraping_orchestration import ScrapingOrchestrator
from ..core.settings import get_settings
from ..infrastructure.database.connection import get_connection_string
from ..infrastructure.database.repositories.listing_repository import (
    ListingRepository,
)
from ..infrastructure.database.repositories.product_repository import (
    ProductRepository,
)
from ..services.browser_service import BrowserService
from ..services.facebook_service import FacebookService
from ..services.proxy_service import ProxyService
from ..services.session_service import SessionService
from .models import JobStatus, JobStatusResponse

logger = logging.getLogger(__name__)


class SessionExecutor:

    def __init__(self, jobs: Dict[str, JobStatusResponse]):
        self.jobs = jobs

    def execute(
        self, job_id: str, brand: str, search_term: str, require_price_match: bool = True
    ):
        logger.info(
            f"[Job {job_id}] Starting scrape for brand: {brand}, search: {search_term}"
        )

        self.jobs[job_id].status = JobStatus.RUNNING

        try:
            settings = get_settings()
            connection_string = get_connection_string()

            product_repository = ProductRepository(connection_string)
            listing_repository = ListingRepository(connection_string)
            
            product_service = ProductService(product_repository)

            proxy_service = ProxyService() if settings.proxy_enabled else None
            browser = BrowserService(settings, proxy_service)
            session = SessionService(settings)
            facebook = FacebookService(settings, browser, session)

            with browser:
                if not facebook.restore_session():
                    raise Exception("Failed to restore Facebook session")

                orchestrator = ScrapingOrchestrator(
                    product_service, 
                    browser.get_driver(),
                    listing_repository
                )

                result = orchestrator.scrape_and_match_brand(
                    brand, search_term, require_price_match=require_price_match
                )

                self.jobs[job_id].status = JobStatus.COMPLETED
                self.jobs[job_id].result = result

                logger.info(
                    f"[Job {job_id}] Completed - Found {result['stats'].get('total_matches', 0)} matches"
                )

        except Exception as e:
            logger.error(f"[Job {job_id}] Failed: {e}", exc_info=True)
            self.jobs[job_id].status = JobStatus.FAILED
            self.jobs[job_id].error = str(e)