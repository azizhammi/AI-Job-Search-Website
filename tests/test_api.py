
from fastapi.testclient import TestClient

from app.main import app, jobs_db

client = TestClient(app)


def setup_function():
    jobs_db.clear()


def test_root_endpoint():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["app"] == "AI Job Copilot"


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_job():
    response = client.post(
        "/jobs",
        json={
            "title": "Python Developer",
            "company": "Example GmbH",
            "location": "Berlin, Germany",
            "description": "Build backend APIs",
            "required_skills": ["Python", "FastAPI"],
        },
    )

    assert response.status_code == 201
    assert response.json()["id"] > 0
    assert response.json()["title"] == "Python Developer"


def test_list_jobs():
    client.post(
        "/jobs",
        json={
            "title": "AI Engineer",
            "company": "Example AI",
        },
    )

    response = client.get("/jobs")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["company"] == "Example AI"


def test_search_jobs_by_skill():
    client.post(
        "/jobs",
        json={
            "title": "Backend Developer",
            "company": "Example GmbH",
            "required_skills": ["Python", "FastAPI"],
        },
    )

    response = client.get("/jobs/search", params={"q": "fastapi"})

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "Backend Developer"


def test_search_returns_no_match():
    response = client.get("/jobs/search", params={"q": "Rust"})

    assert response.status_code == 200
    assert response.json() == []
