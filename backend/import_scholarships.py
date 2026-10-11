
import json
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from sqlalchemy import select

from app.database import SessionLocal
from app.models import Scholarship


DATA_FILE = (
    Path(__file__).resolve().parent.parent
    / "scraper"
    / "scholarship_scraper"
    / "data"
    / "normalized_scholarships.json"
)


def parse_date(value):
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except (ValueError, TypeError):
        return None


def parse_datetime(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def parse_amount(value):
    """Parse an amount only when the numeric value is unambiguous."""
    if value is None or isinstance(value, bool):
        return None

    if isinstance(value, (int, float, Decimal)):
        try:
            return Decimal(str(value))
        except InvalidOperation:
            return None

    if isinstance(value, str):
        cleaned = value.strip().replace(",", "")
        if re.fullmatch(r"\d+(?:\.\d{1,2})?", cleaned):
            try:
                return Decimal(cleaned)
            except InvalidOperation:
                return None

    return None


def clean_text(value):
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    value = str(value).strip()
    return value or None


def infer_education_level(title, eligibility=None):
    """Infer only levels supported by explicit title/eligibility wording."""
    text = f"{title or ''} {eligibility or ''}".lower()
    levels = []

    patterns = [
        ("diploma", r"\bdiploma\b"),
        (
            "school",
            r"\bpre[- ]matric\b|\bpost[- ]matric\b|"
            r"\bschool students?\b|\bin schools?\b|"
            r"\bclass (?:ix|x|xi|xii|9|10|11|12)\b",
        ),
        (
            "undergraduate",
            r"\bunder[- ]graduate\b|\bundergraduate\b|"
            r"\bug degree\b|\bug programme\b|\bbachelor'?s?\b|"
            r"\bnts[- ]?ug\b|technical degree",
        ),
        (
            "postgraduate",
            r"\bpost[- ]graduate\b|\bpostgraduate\b|"
            r"\bpg degree\b|\bpg programme\b|\bmaster'?s?\b|"
            r"\bnts[- ]?pg\b",
        ),
        ("phd", r"\bph\.?d\.?\b|\bdoctoral\b|\bdoctorate\b"),
    ]

    for level, pattern in patterns:
        if re.search(pattern, text):
            levels.append(level)

    # Avoid classifying "Top Class Education in College" as
    # undergraduate: the title alone doesn't establish the degree level.
    return ", ".join(dict.fromkeys(levels)) or None


def infer_category(title, existing=None):
    """Use explicit scheme labels; don't guess from the provider alone."""
    if existing:
        return existing

    text = (title or "").lower()

    if re.search(r"\bmerit[- ]based scheme\b|\bmerit based\b", text):
        return "merit"

    if re.search(r"\bwelfare[- ]based scheme\b|\bwelfare based\b", text):
        return "welfare"

    if re.search(r"\bminority\b", text):
        return "minority"

    if re.search(r"\bdisabilit(?:y|ies)\b|\bspecially abled\b", text):
        return "disability"

    if re.search(r"\bneed[- ]based\b|\bmeans[- ]based\b", text):
        return "need"

    return None


def infer_location(title, provider, eligibility, existing=None):
    """Infer location only from explicit regional or national clues."""
    if existing:
        return existing

    text = f"{title or ''} {provider or ''} {eligibility or ''}".lower()

    # Regional restrictions take precedence over national wording.
    if re.search(r"jammu\s*(?:&|and)?\s*kashmir|ladakh", text):
        return "Jammu and Kashmir / Ladakh"

    if re.search(r"north[- ]?eastern region|\bner\b", text):
        return "North Eastern Region"

    # Do not assume every record on a national portal is open nationwide.
    # Explicitly national schemes and national-level institutions are
    # reasonable indicators, but this is still an inference.
    if (
        re.search(r"\bnational scholarship\b|\bnational talent scholarship\b", text)
        or (provider or "").strip().lower()
        in {"university grants commission", "aicte", "all india council for technical education"}
    ):
        return "India"

    return None


def import_scholarships():
    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Normalized data file not found: {DATA_FILE}"
        )

    with DATA_FILE.open("r", encoding="utf-8") as file:
        records = json.load(file)

    if not isinstance(records, list):
        raise ValueError("Expected the JSON file to contain a list of records.")

    inserted = 0
    updated = 0
    skipped = 0
    errors = []

    with SessionLocal() as db:
        try:
            for index, record in enumerate(records, start=1):
                title = clean_text(record.get("title"))
                provider = clean_text(record.get("provider"))

                if not title or not provider:
                    skipped += 1
                    errors.append(
                        f"Record {index}: missing title or provider"
                    )
                    continue

                source_url = clean_text(record.get("source_url"))

                statement = select(Scholarship).where(
                    Scholarship.title == title,
                    Scholarship.source_url == source_url,
                )
                scholarship = db.scalars(statement).first()

                is_new = scholarship is None
                if is_new:
                    scholarship = Scholarship(
                        title=title,
                        provider=provider,
                    )

                amount_value = record.get("amount")
                if isinstance(amount_value, (dict, list)):
                    amount_text = json.dumps(
                        amount_value, ensure_ascii=False
                    )
                else:
                    amount_text = clean_text(amount_value)

                eligibility = clean_text(record.get("eligibility"))

                education_level = (
                    clean_text(record.get("education_level"))
                    or infer_education_level(title, eligibility)
                )

                category = infer_category(
                    title,
                    clean_text(record.get("category")),
                )

                location = infer_location(
                    title,
                    provider,
                    eligibility,
                    clean_text(record.get("location")),
                )

                # Core fields
                scholarship.title = title
                scholarship.provider = provider

                # For optional fields, preserve an existing value if the
                # latest source has no value. New records remain nullable.
                optional_values = {
                    "description": clean_text(record.get("description")),
                    "objective": clean_text(record.get("objective")),
                    "eligibility": eligibility,
                    "amount": parse_amount(amount_value),
                    "amount_text": amount_text,
                    "slots": clean_text(record.get("slots")),
                    "tenure": clean_text(record.get("tenure")),
                    "education_level": education_level,
                    "category": category,
                    "location": location,
                    "income_requirement": clean_text(
                        record.get("income_requirement")
                    ),
                    "opening_date": parse_date(record.get("opening_date")),
                    "deadline": parse_date(record.get("deadline")),
                    "application_url": clean_text(
                        record.get("application_url")
                    ),
                    "source": clean_text(record.get("source")),
                    "source_url": source_url,
                    "detail_url": clean_text(record.get("detail_url")),
                    "guidelines_url": clean_text(
                        record.get("guidelines_url")
                    ),
                    "faq_url": clean_text(record.get("faq_url")),
                    "scraped_at": parse_datetime(record.get("scraped_at")),
                    "raw_metadata": record.get("raw_metadata"),
                }

                for field, value in optional_values.items():
                    if value is not None or is_new:
                        setattr(scholarship, field, value)

                if is_new:
                    db.add(scholarship)
                    inserted += 1
                else:
                    updated += 1

            db.commit()

        except Exception:
            db.rollback()
            raise

    print("\nScholarship import completed.")
    print(f"Records in source file: {len(records)}")
    print(f"Inserted: {inserted}")
    print(f"Updated: {updated}")
    print(f"Skipped: {skipped}")

    if errors:
        print("\nRecords needing attention:")
        for error in errors:
            print(f"- {error}")


if __name__ == "__main__":
    import_scholarships()
