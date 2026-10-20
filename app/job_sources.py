
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
    "staff ",
    "lead ",
    "principal",
    "director",
    "head of",
    "chief ",
    "manager",
    "duales studium",
    "working student",
    "werkstudent",
    "internship",
    "praktikum",
    "student assistant",
)


def is_relevant_title(title: str, keyword: str | None = None) -> bool:
    """Check whether a job title fits our target roles and seniority."""
    title_lower = title.casefold()

    if any(word in title_lower for word in EXCLUDED_TITLE_KEYWORDS):
        return False

    known_role = any(role in title_lower for role in ROLE_KEYWORDS)

    query_terms = keyword.casefold().split() if keyword and keyword.strip() else []
    query_matches_title = (
        bool(query_terms)
        and all(term in title_lower for term in query_terms)
    )

    return known_role or query_matches_title


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
    """Fetch and filter jobs from Arbeitnow, following available API pages."""
    current_url = ARBEITNOW_API_URL
    params = None
    jobs: list[JobListing] = []
    seen_urls: set[str] = set()

    query_terms = keyword.casefold().split() if keyword and keyword.strip() else []

    while current_url and len(jobs) < limit:
        response = httpx.get(
            current_url,
            params=params,
            timeout=15.0,
        )
        response.raise_for_status()
        payload = response.json()

        for item in payload.get("data", []):
            title = item.get("title") or "Untitled"
            title_lower = title.casefold()
            location = item.get("location") or ""

            if relevant_only:
                if not is_relevant_title(title, keyword):
                    continue

                if not is_germany_location(location):
                    continue

            description = clean_html(item.get("description") or "")

            job = JobListing(
                title=title,
                company=item.get("company_name") or "Unknown company",
                location=location or "Germany",
                description=description,
                url=item.get("url"),
                source="arbeitnow",
                required_skills=item.get("tags") or [],
            )

            searchable_text = " ".join([
                job.title,
                job.company,
                job.location,
                job.description,
                *job.required_skills,
            ]).casefold()

            # Match all search words, not necessarily the exact phrase.
            if query_terms and not all(
                term in searchable_text for term in query_terms
            ):
                continue

            if job.url and job.url in seen_urls:
                continue

            if job.url:
                seen_urls.add(job.url)

            jobs.append(job)

            if len(jobs) >= limit:
                break

        # Follow the next URL supplied by the API, when available.
        links = payload.get("links") or {}
        next_url = links.get("next")

        if next_url:
            current_url = next_url
            params = None
        else:
            # Some paginated APIs provide page numbers through metadata.
            meta = payload.get("meta") or {}
            current_page = meta.get("current_page")
            last_page = meta.get("last_page")

            if (
                isinstance(current_page, int)
                and isinstance(last_page, int)
                and current_page < last_page
            ):
                current_url = ARBEITNOW_API_URL
                params = {"page": current_page + 1}
            else:
                break

    return jobs[:limit]

