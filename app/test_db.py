
from sqlalchemy import select

from app.database import SessionLocal
from app.db_models import Job
from app.init_db import init_db


def main() -> None:
    init_db()

    with SessionLocal() as db:
        test_url = "https://example.com/test-job"

        # Avoid inserting the same test job more than once.
        job = db.scalar(select(Job).where(Job.url == test_url))

        if job is None:
            job = Job(
                title="Junior Python Developer",
                company="Example Company",
                location="Aachen, Germany",
                description="Python, FastAPI, SQLAlchemy",
                url=test_url,
                source="test",
                required_skills=["Python", "FastAPI", "SQLAlchemy"],
            )
            db.add(job)
            db.commit()
            db.refresh(job)

        print(f"Saved job: {job.title}")
        print(f"Company: {job.company}")
        print(f"Database ID: {job.id}")
        print(f"Skills: {job.required_skills}")


if __name__ == "__main__":
    main()
