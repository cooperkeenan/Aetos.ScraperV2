import logging
import uuid
from typing import Dict

from fastapi import BackgroundTasks, FastAPI, HTTPException

from .models import JobStatus, JobStatusResponse, ScrapeRequest, ScrapeResponse
from .session_executor import SessionExecutor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Aetos Scraper API", version="1.0.0")

jobs: Dict[str, JobStatusResponse] = {}

session_executor = SessionExecutor(jobs)


@app.get("/")
def root():
    return {"message": "Aetos Scraper API", "status": "running"}


@app.post("/scrape", response_model=ScrapeResponse)
def scrape_brand(request: ScrapeRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())

    jobs[job_id] = JobStatusResponse(
        job_id=job_id, status=JobStatus.PENDING, brand=request.brand
    )

    background_tasks.add_task(session_executor.execute, job_id, request.brand)

    logger.info(f"Created scrape job {job_id} for brand: {request.brand}")

    return ScrapeResponse(
        job_id=job_id,
        status=JobStatus.PENDING,
        message=f"Scrape job started for brand: {request.brand}",
    )


@app.get("/scrape/{job_id}", response_model=JobStatusResponse)
def get_job_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    return jobs[job_id]


@app.get("/jobs", response_model=Dict[str, JobStatusResponse])
def list_jobs():
    return jobs