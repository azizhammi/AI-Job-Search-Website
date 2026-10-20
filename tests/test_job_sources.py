
from app.job_sources import (
    clean_html,
    is_germany_location,
    is_relevant_title,
)

def test_clean_html_removes_tags():
    result = clean_html(
        "<p>Build APIs</p><ul><li>Python</li><li>FastAPI</li></ul>"
    )

    assert "<p>" not in result
    assert "<li>" not in result
    assert "Build APIs" in result
    assert "Python" in result
    assert "FastAPI" in result


def test_clean_html_decodes_entities():
    result = clean_html("Software &amp; AI")

    assert result == "Software & AI"


def test_germany_location_accepts_german_city():
    assert is_germany_location("Berlin") is True


def test_germany_location_accepts_germany():
    assert is_germany_location("Remote in Germany") is True


def test_germany_location_rejects_netherlands():
    assert is_germany_location("Rijssen, Overijssel, Nederland") is False


def test_germany_location_rejects_unknown_location():
    assert is_germany_location("") is False


def test_relevant_title_accepts_backend_engineer():
    assert is_relevant_title("Backend Engineer (m/f/d)") is True


def test_relevant_title_accepts_machine_learning_engineer():
    assert is_relevant_title("ML-Engineer - Machine Learning") is True


def test_relevant_title_rejects_staff_engineer():
    assert is_relevant_title("Staff Software Engineer") is False


def test_relevant_title_rejects_working_student():
    assert is_relevant_title("Working Student - Python Developer") is False


def test_relevant_title_matches_search_terms():
    assert is_relevant_title("Data Platform Engineer", "data engineer") is True


def test_relevant_title_rejects_unrelated_role():
    assert is_relevant_title("Sales Representative") is False
