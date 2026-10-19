
from app.job_scoring import score_job
from app.models import JobListing


def make_job(title, description, location="Berlin"):
    return JobListing(
        title=title,
        company="Example GmbH",
        location=location,
        description=description,
    )


def test_matching_software_job_scores_well():
    job = make_job(
        "Junior Python Backend Engineer",
        "Build APIs with Python, FastAPI, SQL, PostgreSQL and Docker.",
    )

    result = score_job(job)

    assert result["score"] >= 60
    assert "python" in result["matched_skills"]
    assert "fastapi" in result["matched_skills"]
    assert "software" in result["matching_roles"]


def test_ai_job_matches_ml_skills():
    job = make_job(
        "Machine Learning Engineer",
        "Use Python, PyTorch, Pandas and deep learning.",
    )

    result = score_job(job)

    assert "ai" in result["matching_roles"]
    assert "python" in result["matched_skills"]
    assert "pytorch" in result["matched_skills"]


def test_data_job_matches_sql_and_process_mining():
    job = make_job(
        "Data Engineer",
        "Build SQL pipelines and analyse processes with process mining.",
    )

    result = score_job(job)

    assert "data" in result["matching_roles"]
    assert "sql" in result["matched_skills"]
    assert "process mining" in result["matched_skills"]


def test_senior_job_gets_penalty():
    job = make_job(
        "Senior Software Engineer",
        "Build software with Python and SQL.",
    )

    result = score_job(job)

    assert result["seniority_penalty"] == 25
    assert any("Seniority mismatch" in reason for reason in result["reasons"])


def test_unrelated_job_scores_low():
    job = make_job(
        "Sales Manager",
        "Manage sales accounts and build customer relationships.",
    )

    result = score_job(job)

    assert result["score"] < 40
    assert result["matched_skills"] == []


def test_score_is_bounded():
    job = make_job(
        "Junior AI Engineer",
        "Python SQL FastAPI machine learning deep learning PyTorch "
        "TensorFlow Pandas NumPy scikit-learn.",
    )

    result = score_job(job)

    assert 0 <= result["score"] <= 100


def test_experience_requirement_reduces_score():
    job = make_job(
        "Backend Engineer",
        "Requirements: at least 3 years of professional product development "
        "experience. Strong Python and SQL skills.",
    )

    result = score_job(job)

    assert result["experience_years_required"] == 3
    assert result["experience_penalty"] == 30
    assert any(
        "Experience requirement detected" in reason
        for reason in result["reasons"]
    )

def test_detect_experience_requirement_with_plus():
    job = make_job(
        "Software Engineer",
        "Requirements include 2+ years of experience.",
    )
    result = score_job(job)

    assert result["experience_years_required"] == 2


def test_detect_experience_requirement_when_unspecified():
    job = make_job(
        "Junior Python Developer",
        "We welcome applicants who are eager to learn Python.",
    )
    result = score_job(job)

    assert result["experience_years_required"] is None
    assert result["experience_penalty"] == 0


def test_detect_experience_requirement_in_range():
    job = make_job(
        "Data Engineer",
        "Candidates should have 3 to 5 years of experience.",
    )
    result = score_job(job)

    assert result["experience_years_required"] == 3