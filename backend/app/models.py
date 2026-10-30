
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    Date,
    DateTime,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Scholarship(Base):
    __tablename__ = "scholarships"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )

    # Core scholarship information
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    provider: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    objective: Mapped[str | None] = mapped_column(Text, nullable=True)
    eligibility: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Financial and academic details
    amount: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    amount_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    slots: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tenure: Mapped[str | None] = mapped_column(String(255), nullable=True)
    education_level: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    income_requirement: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    # Application timeline
    opening_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    deadline: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Links
    application_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    detail_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    guidelines_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    faq_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Scraping metadata
    scraped_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    raw_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, nullable=True
    )
        # Provenance information from the deduplicated dataset
    sources: Mapped[list[str] | None] = mapped_column(
        JSON, nullable=True
    )

    source_references: Mapped[list[dict[str, Any]] | None] = mapped_column(
        JSON, nullable=True
    )

    source_metadata: Mapped[list[dict[str, Any]] | None] = mapped_column(
        JSON, nullable=True
    )

    # Lifecycle tracking
    status: Mapped[str] = mapped_column(
        String(30), default="ACTIVE", nullable=False
    )
    first_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
