
import re

from app.models import JobListing


# Skills from your profile, including common alternative spellings.
DEFAULT_SKILLS = {
    "python": ("python",),
    "java": ("java",),
    "c++": ("c++", "cpp"),
    "sql": ("sql",),
    "fastapi": ("fastapi",),
    "machine learning": ("machine learning", "ml"),
    "deep learning": ("deep learning",),
    "process mining": ("process mining",),
    "conformance checking": ("conformance checking",),
    "ocel": ("ocel",),
    "pandas": ("pandas",),
    "numpy": ("numpy",),
    "scikit-learn": ("scikit-learn", "scikit learn", "sklearn"),
    "tensorflow": ("tensorflow",),
    "pytorch": ("pytorch", "py torch"),
    "pm4py": ("pm4py",),
    "react": ("react",),
    "typescript": ("typescript",),
    "redux": ("redux",),
    "postgresql": ("postgresql", "postgres"),
    "mysql": ("mysql",),
    "neo4j": ("neo4j",),
    "git": ("git",),
    "docker": ("docker",),
    "aws": ("aws", "amazon web services"),
    "gcp": ("gcp", "google cloud"),
}

ROLE_KEYWORDS = {
    "software": (
        "software engineer",
        "software developer",
        "backend engineer",
        "backend developer",
        "frontend engineer",
        "frontend developer",
        "full stack",
        "fullstack",
        "python developer",
    ),
    "ai": (
        "machine learning engineer",
        "ml engineer",
        "ai engineer",
        "artificial intelligence",
        "deep learning",
        "nlp engineer",
        "computer vision",
    ),
    "data": (
        "data engineer",
        "data scientist",
        "data analyst",
        "analytics engineer",
        "data platform",
        "process mining",
    ),
}

EARLY_CAREER_TERMS = (
    "graduate",
    "entry level",
    "entry-level",
    "junior",
    "new grad",
    "berufseinsteiger",
    "absolvent",
)

SENIOR_TERMS = (
    "senior",
    "staff",
    "principal",
    "lead engineer",
    "tech lead",
    "director",
    "head of",
    "engineering manager",
)


def contains_term(text: str, term: str) -> bool:
    """Match a term without accidentally matching it inside another word."""
    pattern = rf"(?<!\w){re.escape(term.casefold())}(?!\w)"
    return re.search(pattern, text.casefold()) is not None



def detect_experience_requirement(text: str) -> int | None:
    """Detect explicit experience requirements in job descriptions."""
    text = text.casefold()

    # Handle ranges first, using the lower bound.
    range_pattern = r"\b(\d+)\s+to\s+(\d+)\s+years?\b"
    range_match = re.search(range_pattern, text)

    if range_match:
        return int(range_match.group(1))

    patterns = (
        r"\b(?:at least|min(?:imum)?)\s+(\d+)\s+years?\b",
        r"\b(\d+)\s*\+\s*years?\b",
        r"\b(\d+)\s+years?\s+(?:of\s+)?(?:professional\s+)?experience\b",
        r"\b(\d+)\s+years?\s+professional\s+experience\b",
    )

    matches = []
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            matches.append(int(match.group(1)))

    return max(matches) if matches else None



def score_job(
    job: JobListing,
    target_skills: list[str] | None = None,
) -> dict:
    """Return an explainable relevance score from 0 to 100."""

    skills = target_skills or list(DEFAULT_SKILLS.keys())
    title = job.title.casefold()
    description = job.description.casefold()
    location = job.location.casefold()

    # 1. Role relevance: up to 35 points.
    matching_roles = [
        role
        for role, keywords in ROLE_KEYWORDS.items()
        if any(keyword in title for keyword in keywords)
    ]

    if matching_roles:
        role_points = 35
    elif any(
        keyword in description
        for keywords in ROLE_KEYWORDS.values()
        for keyword in keywords
    ):
        role_points = 15
    else:
        role_points = 0

    # 2. Skill overlap: up to 45 points.
    searchable_text = f"{title} {description}"
    matched_skills = []

    for skill in skills:
        normalized_skill = skill.casefold().strip()
        aliases = DEFAULT_SKILLS.get(
            normalized_skill,
            (normalized_skill,),
        )

        if any(contains_term(searchable_text, alias) for alias in aliases):
            matched_skills.append(skill)

    skill_points = min(45, round(45 * len(matched_skills) / 5))

    # 3. Experience-level fit: up to 15 points, with a seniority penalty.
    senior_matches = [
        term for term in SENIOR_TERMS if term in title
    ]
    early_career_matches = [
        term
        for term in EARLY_CAREER_TERMS
        if term in title
    ]

    seniority_penalty = 25 if senior_matches else 0
    
    experience_years = detect_experience_requirement(description)
    experience_penalty = (
        min(30, experience_years * 10)
        if experience_years is not None
        else 0
    )

    if senior_matches:
        seniority_points = 0
    elif early_career_matches:
        seniority_points = 15
    else:
        # A neutral title isn't proof that a role is unsuitable.
        seniority_points = 10

    # 4. Location fit: up to 5 points.
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
        "aachen",
        "stuttgart",
        "düsseldorf",
    )

    location_points = (
        5
        if any(marker in location for marker in german_markers)
        else 0
    )

    raw_score = (
        role_points
        + skill_points
        + seniority_points
        + location_points
        - seniority_penalty
        - experience_penalty
    )
    final_score = max(0, min(100, raw_score))

    reasons = []

    if matching_roles:
        reasons.append(
            "Relevant role track: " + ", ".join(matching_roles)
        )
    elif role_points:
        reasons.append("Relevant engineering or data terms in description")

    if matched_skills:
        reasons.append(
            "Matching skills: " + ", ".join(matched_skills)
        )
    else:
        reasons.append("No target skills found in title or description")

    if senior_matches:
        reasons.append(
            "Seniority mismatch: " + ", ".join(senior_matches)
        )
    elif early_career_matches:
        reasons.append("Title indicates an early-career opportunity")
    else:
        reasons.append("Seniority is unclear from the title")

    if experience_years is not None:
        reasons.append(
            f"Experience requirement detected: {experience_years} year(s)"
    )
        
    if location_points:
        reasons.append("Location appears to be in Germany")

    return {
        "score": final_score,
        "role_points": role_points,
        "skill_points": skill_points,
        "seniority_points": seniority_points,
        "location_points": location_points,
        "seniority_penalty": seniority_penalty,
        "matched_skills": matched_skills,
        "matching_roles": matching_roles,
        "reasons": reasons,
        "experience_years_required": experience_years,
        "experience_penalty": experience_penalty,
    }

