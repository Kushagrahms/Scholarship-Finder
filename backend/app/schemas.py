from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict


class ScholarshipResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    provider: str | None = None
    description: str | None = None
    objective: str | None = None
    eligibility: str | None = None

    amount: Decimal | None = None
    amount_text: str | None = None
    slots: str | None = None
    tenure: str | None = None
    education_level: str | None = None
    category: str | None = None
    location: str | None = None
    income_requirement: str | None = None

    opening_date: date | None = None
    deadline: date | None = None

    application_url: str | None = None
    source: str | None = None
    source_url: str | None = None
    detail_url: str | None = None
    guidelines_url: str | None = None
    faq_url: str | None = None

    scraped_at: datetime | None = None
    raw_metadata: dict[str, Any] | None = None

    sources: list[str] | None = None
    source_references: list[dict[str, Any]] | None = None
    source_metadata: list[dict[str, Any]] | None = None
    
    status: str
    first_seen: datetime
    last_seen: datetime
    updated_at: datetime
