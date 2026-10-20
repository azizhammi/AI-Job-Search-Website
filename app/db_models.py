
from sqlalchemy import JSON, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(300), index=True)
    company: Mapped[str] = mapped_column(String(300), index=True)
    location: Mapped[str] = mapped_column(String(200), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    url: Mapped[str] = mapped_column(String(1000), unique=True, index=True)
    source: Mapped[str] = mapped_column(String(100), default="")
    required_skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    application_status: Mapped[str] = mapped_column(
        String(50),
        default="saved",
        nullable=False,
    )

    application_notes: Mapped[str] = mapped_column(
        Text,
        default="",
        nullable=False,
    )
