
from fastapi import Depends, FastAPI, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import Base, engine, get_db
from app.db_models import Job
from app.models import (
    DashboardResponse,
    HealthResponse,
    JobListing,
    JobResponse,
    JobStatusUpdate,
    ScoredJobResponse,
)
from app.job_sources import fetch_arbeitnow_jobs
from app.job_scoring import score_job


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="An AI-powered job search assistant for Germany.",
)

# Create database tables when the application starts.
Base.metadata.create_all(bind=engine)


# ---------- Helpers ----------

def job_to_response(job: Job) -> JobResponse:
    """Convert a database job into the public API response model."""
    return JobResponse.model_validate(
        {
            "id": job.id,
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "description": job.description,
            "url": job.url,
            "source": job.source,
            "required_skills": job.required_skills,
            "application_status": job.application_status,
            "application_notes": job.application_notes,
        }
    )


def external_job_to_response(
    job: JobListing,
    job_id: int,
    application_status: str = "saved",
    application_notes: str = "",
) -> JobResponse:
    """Convert an external listing into the public API response model."""
    return JobResponse.model_validate(
        {
            **job.model_dump(),
            "id": job_id,
            "application_status": application_status,
            "application_notes": application_notes,
        }
    )


def fetch_external_jobs(
    limit: int,
    keyword: str | None,
) -> list[JobListing]:
    """Fetch listings and translate provider errors into an API error."""
    try:
        return fetch_arbeitnow_jobs(
            limit=limit,
            keyword=keyword,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="Could not retrieve jobs from Arbeitnow.",
        ) from exc


# ---------- General ----------

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


# ---------- Saved jobs ----------

@app.post(
    "/jobs",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Jobs"],
)
def create_job(
    job: JobListing,
    db: Session = Depends(get_db),
):
    """Explicitly save one job to the collection."""
    existing_job = db.scalar(
        select(Job).where(Job.url == str(job.url))
    )

    if existing_job:
        raise HTTPException(
            status_code=409,
            detail="A job with this URL already exists.",
        )

    saved_job = Job(**job.model_dump())
    db.add(saved_job)
    db.commit()
    db.refresh(saved_job)

    return job_to_response(saved_job)


@app.get(
    "/jobs",
    response_model=list[JobResponse],
    tags=["Jobs"],
)
def list_jobs(db: Session = Depends(get_db)):
    """List jobs that have actually been saved."""
    jobs = db.scalars(
        select(Job).order_by(Job.id)
    ).all()

    return [job_to_response(job) for job in jobs]


@app.get(
    "/jobs/search",
    response_model=list[JobResponse],
    tags=["Jobs"],
)
def search_jobs(
    q: str = Query(min_length=1),
    db: Session = Depends(get_db),
):
    """Search the saved collection by job details or required skills."""
    query = q.strip().casefold()

    if not query:
        raise HTTPException(
            status_code=422,
            detail="Search query cannot be empty.",
        )

    jobs = db.scalars(
        select(Job).order_by(Job.id)
    ).all()

    results = []

    for job in jobs:
        searchable_text = " ".join(
            [
                job.title or "",
                job.company or "",
                job.location or "",
                job.description or "",
                *(job.required_skills or []),
            ]
        ).casefold()

        if query in searchable_text:
            results.append(job_to_response(job))

    return results


# ---------- Discover jobs: DOES NOT SAVE ----------

@app.get(
    "/jobs/discover",
    response_model=list[JobListing],
    tags=["Job Discovery"],
)
def discover_jobs(
    limit: int = Query(default=20, ge=1, le=100),
    keyword: str | None = Query(default=None, max_length=100),
):
    """
    Fetch external job listings for review.

    This endpoint does not write to the database.
    A job is saved only when the client explicitly calls POST /jobs.
    """
    return fetch_external_jobs(
        limit=limit,
        keyword=keyword,
    )


# ---------- Legacy import: fetches AND saves ----------

@app.get(
    "/jobs/import",
    response_model=list[JobResponse],
    tags=["Jobs"],
)
def import_jobs(
    limit: int = Query(default=20, ge=1, le=100),
    keyword: str | None = None,
    db: Session = Depends(get_db),
):
    """
    Legacy endpoint: fetch external jobs and save them automatically.

    The new dashboard should use GET /jobs/discover instead.
    """
    external_jobs = fetch_external_jobs(
        limit=limit,
        keyword=keyword,
    )

    imported_jobs = []

    for job in external_jobs:
        existing_job = db.scalar(
            select(Job).where(Job.url == str(job.url))
        )

        if existing_job:
            imported_jobs.append(job_to_response(existing_job))
            continue

        saved_job = Job(**job.model_dump())
        db.add(saved_job)
        db.flush()

        imported_jobs.append(job_to_response(saved_job))

    db.commit()

    return imported_jobs


# ---------- Legacy scored import: fetches AND saves ----------

@app.get(
    "/jobs/import/scored",
    response_model=list[ScoredJobResponse],
    tags=["Jobs"],
)
def import_scored_jobs(
    limit: int = Query(default=20, ge=1, le=100),
    keyword: str | None = None,
    db: Session = Depends(get_db),
):
    """
    Legacy endpoint: fetch, score, and automatically save external jobs.
    """
    external_jobs = fetch_external_jobs(
        limit=100,
        keyword=keyword,
    )

    scored_jobs = []

    for job in external_jobs:
        existing_job = db.scalar(
            select(Job).where(Job.url == str(job.url))
        )

        if existing_job:
            saved_job = existing_job
        else:
            saved_job = Job(**job.model_dump())
            db.add(saved_job)
            db.flush()

        relevance = score_job(job)

        scored_jobs.append(
            {
                "job": job_to_response(saved_job),
                "relevance": relevance,
            }
        )

    db.commit()

    scored_jobs.sort(
        key=lambda item: item["relevance"]["score"],
        reverse=True,
    )

    return scored_jobs[:limit]


# ---------- Application tracker ----------

@app.patch(
    "/jobs/{job_id}/status",
    response_model=JobResponse,
    tags=["Jobs"],
)
def update_job_status(
    job_id: int,
    update: JobStatusUpdate,
    db: Session = Depends(get_db),
):
    """Update a saved job's application status and notes."""
    job = db.get(Job, job_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found.",
        )

    job.application_status = update.application_status
    job.application_notes = update.application_notes

    db.commit()
    db.refresh(job)

    return job_to_response(job)


# ---------- Dashboard ----------

@app.get(
    "/dashboard",
    response_model=DashboardResponse,
    tags=["Dashboard"],
)
def get_dashboard(db: Session = Depends(get_db)):
    """Calculate metrics and relevance scores for saved jobs."""
    jobs = db.scalars(
        select(Job).order_by(Job.id)
    ).all()

    statuses = [
        "saved",
        "applied",
        "interview",
        "rejected",
        "offer",
    ]
    status_counts = {item: 0 for item in statuses}

    scored_jobs = []

    for job in jobs:
        status_counts[job.application_status] = (
            status_counts.get(job.application_status, 0) + 1
        )

        listing = JobListing(
            title=job.title,
            company=job.company,
            location=job.location,
            description=job.description,
            url=job.url,
            source=job.source,
            required_skills=job.required_skills or [],
        )

        relevance = score_job(listing)

        scored_jobs.append(
            {
                "job": job_to_response(job),
                "relevance": relevance,
            }
        )

    scored_jobs.sort(
        key=lambda item: item["relevance"]["score"],
        reverse=True,
    )

    return DashboardResponse(
        total_jobs=len(jobs),
        status_counts=status_counts,
        top_matches=scored_jobs[:10],
    )
