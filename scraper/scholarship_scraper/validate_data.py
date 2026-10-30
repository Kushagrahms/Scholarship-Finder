
"""Validate raw or normalized scholarship JSON without network requests.

Responsibilities:
- Validate record structure and field formats.
- Support raw and normalized datasets.
- Allow unknown providers.
- Treat expired deadlines as warnings.
- Do not perform duplicate detection or network verification.
"""

import argparse
import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path
from urllib.parse import urlparse


RAW_REQUIRED = ("title", "source", "source_url")
NORMALIZED_REQUIRED = ("title", "source", "source_url")

RAW_DATES = (
    "scheme_open_date",
    "application_deadline",
    "defective_verification_deadline",
    "institute_verification_deadline",
    "dno_sno_mno_verification_deadline",
)

NORMALIZED_DATES = ("opening_date", "deadline")

URL_FIELDS = (
    "source_url",
    "application_url",
    "application_link",
    "apply_url",
    "application_url_candidate",
    "detail_url",
    "scheme_url",
    "scholarship_url",
    "specifications_url",
    "guidelines_url",
    "faq_url",
)

RAW_MARKERS = set(RAW_DATES)
NORMALIZED_MARKERS = {
    "opening_date",
    "deadline",
    "raw_metadata",
}


def is_missing(value):
    return value is None or (
        isinstance(value, str) and not value.strip()
    )


def valid_date(value):
    if not isinstance(value, str) or len(value) != 10:
        return False

    try:
        return date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def valid_url(value):
    if not isinstance(value, str) or not value.strip():
        return False

    try:
        parsed = urlparse(value.strip())

        return (
            parsed.scheme.lower() in ("http", "https")
            and bool(parsed.hostname)
            and not any(ch.isspace() for ch in parsed.netloc)
        )

    except ValueError:
        return False


def detect_schema(records):
    raw_score = 0
    normalized_score = 0

    for record in records[:50]:
        if not isinstance(record, dict):
            continue

        keys = set(record)

        raw_score += len(RAW_MARKERS & keys)
        normalized_score += len(NORMALIZED_MARKERS & keys)

    if raw_score == normalized_score == 0:
        raise ValueError(
            "Could not auto-detect schema. "
            "Pass --schema raw or --schema normalized."
        )

    return (
        "normalized"
        if normalized_score > raw_score
        else "raw"
    )


def main():

    parser = argparse.ArgumentParser(
        description="Validate scholarship JSON structure and formats."
    )

    parser.add_argument(
        "file",
        help="JSON file to validate",
    )

    parser.add_argument(
        "--schema",
        choices=("auto", "raw", "normalized"),
        default="auto",
    )

    args = parser.parse_args()

    path = Path(args.file).expanduser().resolve()

    try:
        with path.open("r", encoding="utf-8") as handle:
            records = json.load(handle)

    except FileNotFoundError:
        print(f"ERROR: File not found: {path}")
        return 2

    except json.JSONDecodeError as exc:
        print(f"ERROR: Invalid JSON: {exc}")
        return 2

    except OSError as exc:
        print(f"ERROR: Cannot read file: {exc}")
        return 2

    if not isinstance(records, list):
        print("ERROR: Expected the top-level JSON value to be a list.")
        return 2

    try:
        schema = (
            detect_schema(records)
            if args.schema == "auto"
            else args.schema
        )

    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 2

    required = (
        NORMALIZED_REQUIRED
        if schema == "normalized"
        else RAW_REQUIRED
    )

    date_fields = (
        NORMALIZED_DATES
        if schema == "normalized"
        else RAW_DATES
    )

    counts = Counter()
    issues = []
    today = date.today()

    def issue(kind, index, title, field, value, message):
        counts[kind] += 1

        issues.append({
            "type": kind,
            "record_number": index,
            "title": title or "",
            "field": field,
            "value": value,
            "message": message,
        })

    for index, record in enumerate(records, start=1):

        if not isinstance(record, dict):
            issue(
                "INVALID_RECORD",
                index,
                "",
                "record",
                "",
                "Expected a JSON object",
            )
            continue

        title = record.get("title")

        # Required fields
        for field in required:
            if is_missing(record.get(field)):
                issue(
                    "MISSING_REQUIRED",
                    index,
                    title,
                    field,
                    record.get(field),
                    "Required field is missing",
                )

        # Provider is intentionally nullable.
        if "provider" in record:
            provider = record["provider"]

            if provider is not None and not isinstance(provider, str):
                issue(
                    "INVALID_TYPE",
                    index,
                    title,
                    "provider",
                    provider,
                    "Provider must be a string or null",
                )

        # Dates
        for field in date_fields:
            value = record.get(field)

            if is_missing(value):
                counts["MISSING_OPTIONAL_DATE"] += 1
                continue

            if not valid_date(value):
                issue(
                    "INVALID_DATE",
                    index,
                    title,
                    field,
                    value,
                    "Expected a real date formatted YYYY-MM-DD",
                )
                continue

            if field in ("deadline", "application_deadline"):
                if date.fromisoformat(value) < today:
                    counts["EXPIRED_DEADLINE_WARNING"] += 1

        # URLs
        for field in URL_FIELDS:
            value = record.get(field)

            if is_missing(value):
                continue

            if not valid_url(value):
                issue(
                    "INVALID_URL",
                    index,
                    title,
                    field,
                    value,
                    "URL must be an absolute HTTP or HTTPS URL",
                )

        # Normalized schema type checks
        if schema == "normalized":

            text_fields = (
                "description",
                "objective",
                "amount",
                "amount_text",
                "tenure",
                "education_level",
                "category",
                "location",
                "income_requirement",
                "source",
                "source_url",
                "detail_url",
            )

            for field in text_fields:
                value = record.get(field)

                if value is not None and not isinstance(value, str):
                    issue(
                        "INVALID_TYPE",
                        index,
                        title,
                        field,
                        value,
                        "Expected a string or null",
                    )

            for field in ("eligibility", "slots"):
                value = record.get(field)

                if value is not None and not isinstance(
                    value, (str, list)
                ):
                    issue(
                        "INVALID_TYPE",
                        index,
                        title,
                        field,
                        value,
                        "Expected a string, list, or null",
                    )

    error_types = (
        "INVALID_RECORD",
        "MISSING_REQUIRED",
        "INVALID_TYPE",
        "INVALID_DATE",
        "INVALID_URL",
    )

    errors = sum(counts[k] for k in error_types)

    print("\n" + "=" * 54)
    print("SCHOLARSHIP DATA VALIDATION")
    print("=" * 54)

    print(f"File:    {path}")
    print(f"Schema:  {schema}")
    print(f"Records: {len(records)}")

    print("-" * 54)

    for key in error_types:
        print(
            f"{key.replace('_', ' ').title():30} "
            f"{counts[key]}"
        )

    print(
        f"{'Missing optional dates':30} "
        f"{counts['MISSING_OPTIONAL_DATE']}"
    )

    print(
        f"{'Expired deadline warnings':30} "
        f"{counts['EXPIRED_DEADLINE_WARNING']}"
    )

    if issues:
        print("\nISSUES (first 40):")

        for item in issues[:40]:
            print(
                f"- [{item['type']}] "
                f"Record {item['record_number']}: "
                f"{item['title'] or '(untitled)'} | "
                f"{item['field']}={item['value']!r} | "
                f"{item['message']}"
            )

        if len(issues) > 40:
            print(f"... plus {len(issues) - 40} more.")

    print("\nRESULT:", "PASS" if errors == 0 else "FAIL")

    print(
        "Expired deadlines are warnings, not validation failures."
    )

    print(
        "Missing optional deadlines/application URLs are allowed."
    )

    print(
        "No network checks or duplicate detection are performed."
    )

    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
