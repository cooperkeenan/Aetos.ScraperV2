import logging
import uuid
from typing import Dict

from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException
from typing_extensions import Annotated

from ..core.settings import get_settings
from .models import JobStatus, JobStatusResponse, ScrapeRequest, ScrapeResponse
from .session_executor import SessionExecutor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ScraperAPI:

    def __init__(self):
        self.settings = get_settings()
        self.app = FastAPI(title="Aetos Scraper API", version="1.0.0")
        self.jobs: Dict[str, JobStatusResponse] = {}
        self.session_executor = SessionExecutor(self.jobs)

        self._register_routes()

        logger.info("[API] Initialized with API key authentication")

    def _verify_api_key(self, x_api_key: Annotated[str, Header()] = None) -> str:
        if x_api_key != self.settings.api_key:
            raise HTTPException(status_code=401, detail="Invalid API key")
        return x_api_key

    def _register_routes(self):

        @self.app.get("/")
        def root():  # type: ignore
            return {"message": "Aetos Scraper API", "status": "running"}

        @self.app.post(
            "/scrape",
            response_model=ScrapeResponse,
            dependencies=[Depends(self._verify_api_key)],
        )
        def scrape_brand(request: ScrapeRequest, background_tasks: BackgroundTasks):  # type: ignore
            job_id = str(uuid.uuid4())

            search_term = request.search if request.search else request.brand

            self.jobs[job_id] = JobStatusResponse(
                job_id=job_id, status=JobStatus.PENDING, brand=request.brand
            )

            background_tasks.add_task(
                self.session_executor.execute, job_id, request.brand, search_term
            )

            logger.info(f"Created scrape job {job_id} for brand: {request.brand}, search: {search_term}")

            return ScrapeResponse(
                job_id=job_id,
                status=JobStatus.PENDING,
                message=f"Scrape job started for brand: {request.brand}",
            )

        @self.app.get(
            "/scrape/{job_id}",
            response_model=JobStatusResponse,
            dependencies=[Depends(self._verify_api_key)],
        )
        def get_job_status(job_id: str):  # type: ignore
            if job_id not in self.jobs:
                raise HTTPException(status_code=404, detail="Job not found")
            return self.jobs[job_id]

        @self.app.get(
            "/jobs",
            response_model=Dict[str, JobStatusResponse],
            dependencies=[Depends(self._verify_api_key)],
        )
        def list_jobs():  # type: ignore
            return self.jobs


api = ScraperAPI()
app = api.app