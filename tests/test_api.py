
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


@pytest.fixture
def client():
    # Each test gets its own isolated in-memory database.
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(
        bind=test_engine,
        autoflush=False,
        autocommit=False,
    )

    Base.metadata.create_all(bind=test_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()


def test_root_endpoint(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["app"] == "AI Job Copilot"


def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_job(client):
    response = client.post(
        "/jobs",
        json={
            "title": "Python Developer",
            "company": "Example GmbH",
            "location": "Berlin, Germany",
            "description": "Build backend APIs",
            "url": "https://example.com/python-developer",
            "source": "test",
            "required_skills": ["Python", "FastAPI"],
        },
    )

    assert response.status_code == 201
    assert response.json()["id"] > 0
    assert response.json()["title"] == "Python Developer"


def test_list_jobs(client):
    client.post(
        "/jobs",
        json={
            "title": "AI Engineer",
            "company": "Example AI",
            "url": "https://example.com/ai-engineer",
        },
    )

    response = client.get("/jobs")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["company"] == "Example AI"


def test_search_jobs_by_skill(client):
    client.post(
        "/jobs",
        json={
            "title": "Backend Developer",
            "company": "Example GmbH",
            "url": "https://example.com/backend-developer",
            "required_skills": ["Python", "FastAPI"],
        },
    )

    response = client.get("/jobs/search", params={"q": "fastapi"})

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "Backend Developer"


def test_search_returns_no_match(client):
    response = client.get("/jobs/search", params={"q": "Rust"})

    assert response.status_code == 200
    assert response.json() == []


def test_duplicate_job_url_returns_conflict(client):
    job = {
        "title": "Python Developer",
        "company": "Example GmbH",
        "url": "https://example.com/duplicate",
    }

    first_response = client.post("/jobs", json=job)
    second_response = client.post("/jobs", json=job)

    assert first_response.status_code == 201
    assert second_response.status_code == 409


def test_update_job_status(client):
    create_response = client.post(
        "/jobs",
        json={
            "title": "Junior Python Developer",
            "company": "Example GmbH",
            "url": "https://example.com/status-test",
        },
    )

    job_id = create_response.json()["id"]

    response = client.patch(
        f"/jobs/{job_id}/status",
        json={
            "application_status": "applied",
            "application_notes": "Applied through the company website.",
        },
    )

    assert response.status_code == 200
    assert response.json()["application_status"] == "applied"
    assert (
        response.json()["application_notes"]
        == "Applied through the company website."
    )


def test_update_job_status_rejects_invalid_status(client):
    create_response = client.post(
        "/jobs",
        json={
            "title": "Junior Python Developer",
            "company": "Example GmbH",
            "url": "https://example.com/invalid-status-test",
        },
    )

    job_id = create_response.json()["id"]

    response = client.patch(
        f"/jobs/{job_id}/status",
        json={
            "application_status": "maybe",
            "application_notes": "",
        },
    )

    assert response.status_code == 422


def test_update_job_status_returns_404_for_missing_job(client):
    response = client.patch(
        "/jobs/9999/status",
        json={
            "application_status": "applied",
            "application_notes": "Test",
        },
    )

    assert response.status_code == 404
