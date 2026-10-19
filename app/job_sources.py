
import re
from html import unescape

import httpx

from app.models import JobListing

ARBEITNOW_API_URL = "https://www.arbeitnow.com/api/job-board-api"

# Broad role keywords for software engineering and AI/data jobs.
ROLE_KEYWORDS = (
    "software engineer",
    "software developer",
    "backend developer",
    "backend engineer",
    "frontend developer",
    "frontend engineer",
    "full stack developer",
    "fullstack developer",
    "python developer",
    "python engineer",
    "machine learning",
    "ai engineer",
    "artificial intelligence",
    "data scientist",
    "data engineer",
    "ml engineer",
    "deep learning",
    "nlp engineer",
    "computer vision",
)

# These usually indicate a role unsuitable for our initial target.
EXCLUDED_TITLE_KEYWORDS = (
    "senior",
    "lead ",
    "principal",
    "director",
    "head of",
    "duales studium",
    "working student",
    "werkstudent",
    "internship",
    "praktikum",
    "student assistant",
)


def clean_html(value: str) -> str:
    """Convert HTML descriptions into readable plain text."""
    value = re.sub(r"<(br|/p|/div|/li|/h[1-6])\b[^>]*>", " ", value, flags=re.I)
    value = re.sub(r"<[^>]+>", " ", value)
    value = unescape(value)
    return re.sub(r"\s+", " ", value).strip()




def is_germany_location(location: str) -> bool:
    value = location.casefold().strip()

    # Unknown locations should not be treated as German.
    if not value:
        return False

    german_markers = (
        "germany",
        "deutschland",
        "berlin",
        "munich",
        "münchen",
        "hamburg",
        "frankfurt",
        "cologne",
        "köln",
        "bonn",
        "stuttgart",
        "düsseldorf",
        "dortmund",
        "leipzig",
        "dresden",
        "aachen",
        "karlsruhe",
        "heidelberg",
        "frechen",
        "potsdam",
        "bremen",
        "hannover",
        "nuremberg",
        "nürnberg",
        "remote in germany",
        "remote, germany",
    )

    if any(marker in value for marker in german_markers):
        return True

    return False



def fetch_arbeitnow_jobs(
    limit: int = 20,
    keyword: str | None = None,
    relevant_only: bool = True,
) -> list[JobListing]:
    response = httpx.get(ARBEITNOW_API_URL, timeout=15.0)
    response.raise_for_status()

    payload = response.json()
    jobs: list[JobListing] = []
    query = keyword.strip().casefold() if keyword else None

    for item in payload.get("data", []):
        title = item.get("title") or "Untitled"
        title_lower = title.casefold()


        if relevant_only:
            if any(word in title_lower for word in EXCLUDED_TITLE_KEYWORDS):
                continue

            if not any(word in title_lower for word in ROLE_KEYWORDS):
                continue

            location = item.get("location") or ""
            if not is_germany_location(location):
                continue
    
        
        description = clean_html(item.get("description") or "")

        job = JobListing(
            title=title,
            company=item.get("company_name") or "Unknown company",
            location=item.get("location") or "Germany",
            description=description,
            url=item.get("url"),
            source="arbeitnow",
            required_skills=item.get("tags") or [],
        )

        searchable_text = " ".join(
            [
                job.title,
                job.company,
                job.location,
                job.description,
                *job.required_skills,
            ]
        ).casefold()

        if query and query not in searchable_text:
            continue

        jobs.append(job)

        if len(jobs) >= limit:
            break

    return jobs
