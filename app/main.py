
from fastapi import FastAPI, HTTPException, Query, status

from app.config import settings
from app.models import HealthResponse, JobListing, JobResponse

from app.job_sources import fetch_arbeitnow_jobs

from app.job_scoring import score_job
from app.models import ScoredJobResponse

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="An AI-powered job search assistant for Germany.",
)

# Temporary storage. We will replace this with a database later.
jobs_db: list[JobResponse] = []
next_job_id = 1


@app.get("/", tags=["General"])
def root():
    return {
        "app": settings.app_name,
        "message": "Welcome to AI Job Copilot",
        "docs": "/docs",
    }


@app.get("/health", response_model=HealthResponse, tags=["General"])
def health_check():
    return HealthResponse(
        status="ok",
        app_name=settings.app_name,
        version=settings.app_version,
    )


@app.post(
    "/jobs",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Jobs"],
)
def create_job(job: JobListing):
    global next_job_id

    saved_job = JobResponse(
        id=next_job_id,
        **job.model_dump(),
    )

    jobs_db.append(saved_job)
    next_job_id += 1

    return saved_job


@app.get("/jobs", response_model=list[JobResponse], tags=["Jobs"])
def list_jobs():
    return jobs_db


@app.get("/jobs/search", response_model=list[JobResponse], tags=["Jobs"])
def search_jobs(q: str = Query(min_length=1)):
    query = q.strip().casefold()

    if not query:
        raise HTTPException(
            status_code=422,
            detail="Search query cannot be empty.",
        )

    results = []

    for job in jobs_db:
        searchable_text = " ".join(
            [
                job.title,
                job.company,
                job.location,
                job.description,
                *job.required_skills,
            ]
        ).casefold()

        if query in searchable_text:
            results.append(job)

    return results


@app.get("/jobs/import", response_model=list[JobResponse], tags=["Jobs"])
def import_jobs(
    limit: int = Query(default=20, ge=1, le=100),
    keyword: str | None = None,
):
    try:
        external_jobs = fetch_arbeitnow_jobs(
            limit=limit,
            keyword=keyword,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="Could not retrieve jobs from Arbeitnow.",
        ) from exc

    imported_jobs = []

    for job in external_jobs:
        imported_job = JobResponse(
            id=0,
            **job.model_dump(),
        )
        imported_jobs.append(imported_job)

    return imported_jobs


@app.get(
    "/jobs/import/scored",
    response_model=list[ScoredJobResponse],
    tags=["Jobs"],
)
def import_scored_jobs(
    limit: int = Query(default=20, ge=1, le=100),
    keyword: str | None = None,
):
    try:
        external_jobs = fetch_arbeitnow_jobs(
            limit=100,
            keyword=keyword,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="Could not retrieve jobs from Arbeitnow.",
        ) from exc

    scored_jobs = []

    for job in external_jobs:
        relevance = score_job(job)

        scored_jobs.append(
            {
                "job": JobResponse(id=0, **job.model_dump()),
                "relevance": relevance,
            }
        )

    scored_jobs.sort(
        key=lambda item: item["relevance"]["score"],
        reverse=True,
    )

    return scored_jobs[:limit]
