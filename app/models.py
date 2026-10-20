
from typing import Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    app_name: str
    version: str


class JobListing(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    company: str = Field(min_length=1, max_length=200)
    location: str = "Germany"
    description: str = ""
    url: str | None = None
    source: str = "manual"
    required_skills: list[str] = Field(default_factory=list)


class JobResponse(JobListing):
    id: int
    application_status: str = "saved"
    application_notes: str = ""


class JobStatusUpdate(BaseModel):
    application_status: Literal[
        "saved",
        "applied",
        "interview",
        "rejected",
        "offer",
    ]
    application_notes: str = ""


class JobScoreResponse(BaseModel):
    score: int
    role_points: int
    skill_points: int
    seniority_points: int
    location_points: int
    seniority_penalty: int
    matched_skills: list[str]
    matching_roles: list[str]
    reasons: list[str]
    experience_years_required: int | None
    experience_penalty: int


class ScoredJobResponse(BaseModel):
    job: JobResponse
    relevance: JobScoreResponse



class DashboardResponse(BaseModel):
    total_jobs: int
    status_counts: dict[str, int]
    top_matches: list[ScoredJobResponse]
