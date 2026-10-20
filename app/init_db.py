
from app.database import Base, engine
from app import db_models  # Register the Job model with SQLAlchemy


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully.")


if __name__ == "__main__":
    init_db()
