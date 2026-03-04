import logging
import uuid
import os
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

        # Health Check
        @self.app.get("/")
        def root():  # type: ignore
            return {"message": "Aetos Scraper API", "status": "running"}


        # Start Scrape
        @self.app.post("/scrape", response_model=ScrapeResponse, dependencies=[Depends(self._verify_api_key)])
        def scrape_brand(request: ScrapeRequest, background_tasks: BackgroundTasks):
            job_id = str(uuid.uuid4())

            self.jobs[job_id] = JobStatusResponse(
                job_id=job_id, status=JobStatus.PENDING, brands=request.brands
            )

            background_tasks.add_task(
                self.session_executor.execute, job_id, request.brands, request.search
            )

            logger.info(f"Created scrape job {job_id} for brands: {request.brands}, search: {request.search}")

            return ScrapeResponse(
                job_id=job_id,
                status=JobStatus.PENDING,
                message=f"Scrape job started for brands: {request.brands}",
            )


        # Check Job Status
        @self.app.get("/scrape/{job_id}", response_model=JobStatusResponse, dependencies=[Depends(self._verify_api_key)],)
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

        @self.app.get("/logs/{filename}", dependencies=[Depends(self._verify_api_key)])
        def get_log_file(filename: str):
            from fastapi.responses import FileResponse
            path = f"/app/logs/{filename}"
            if not os.path.exists(path):
                raise HTTPException(status_code=404, detail="File not found")
            return FileResponse(path)


api = ScraperAPI()
app = api.app