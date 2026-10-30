
import csv
import json
import re
import requests

from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from html import unescape


# =========================================================
# PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

INPUT_FILE = DATA_DIR / "normalized_scholarships.json"
VERIFIED_FILE = DATA_DIR / "verified_scholarships.json"
AUDIT_FILE = DATA_DIR / "scholarship_audit.csv"
SUMMARY_FILE = DATA_DIR / "audit_summary.json"

REQUEST_TIMEOUT = 12

HEADERS = {
    "User-Agent": "Mozilla/5.0 ScholarshipFinder/1.0"
}

REQUIRED_FIELDS = [
    "title",
    "source",
    "source_url",
]

OPTIONAL_URL_FIELDS = [
    "application_url",
    "detail_url",
    "guidelines_url",
    "faq_url",
]

DATE_FIELDS = [
    "opening_date",
    "deadline",
]


# =========================================================
# HELPERS
# =========================================================

def is_missing(value):
    return value is None or (
        isinstance(value, str) and not value.strip()
    )


def clean_text(value):
    if value is None:
        return ""

    return " ".join(str(value).split()).strip()


def normalize_title(value):
    value = clean_text(value).lower()
    value = re.sub(r"[^a-z0-9\s]", " ", value)
    return " ".join(value.split())


def valid_url_format(url):
    if not isinstance(url, str):
        return False

    parsed = urlparse(url.strip())

    return (
        parsed.scheme in ("http", "https")
        and bool(parsed.netloc)
    )


def fetch_page(url):
    """
    Fetch a webpage and return its status, final URL and text.
    """

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True,
        )

        status = response.status_code
        final_url = response.url

        if status in (403, 429):
            return "BLOCKED_OR_RATE_LIMITED", status, final_url, ""

        if status >= 400:
            return "HTTP_ERROR", status, final_url, ""

        content_type = response.headers.get("Content-Type", "")

        if "html" not in content_type.lower():
            return "NON_HTML_RESPONSE", status, final_url, ""

        html = response.text

        # Remove scripts and styles before checking page text.
        html = re.sub(
            r"<(script|style).*?>.*?</\1>",
            " ",
            html,
            flags=re.IGNORECASE | re.DOTALL,
        )

        text = re.sub(r"<[^>]+>", " ", html)
        text = unescape(text)
        text = clean_text(text)

        return "RESPONDS", status, final_url, text

    except requests.exceptions.Timeout:
        return "TIMEOUT", "", "", ""

    except requests.exceptions.RequestException as error:
        return (
            "CONNECTION_ERROR",
            "",
            "",
            str(error),
        )


def title_found_on_page(title, page_text):
    """
    Check whether the normalized title appears in page text.
    """

    normalized_title = normalize_title(title)
    normalized_page = normalize_title(page_text)

    if not normalized_title or not normalized_page:
        return False

    return normalized_title in normalized_page


def add_issue(issues, record_number, scholarship, field, value, issue, notes=""):
    issues.append({
        "record_number": record_number,
        "title": scholarship.get("title", ""),
        "provider": scholarship.get("provider", ""),
        "source": scholarship.get("source", ""),
        "field": field,
        "value": value if value is not None else "",
        "issue": issue,
        "notes": notes,
        "source_url": scholarship.get("source_url", ""),
    })


# =========================================================
# VERIFY ONE RECORD
# =========================================================

def verify_record(index, scholarship, issues, seen):
    reasons = []

    def reject(reason):
        reasons.append(reason)

    title = clean_text(scholarship.get("title"))
    source = clean_text(scholarship.get("source"))
    source_url = clean_text(scholarship.get("source_url"))

    # -----------------------------------------------------
    # 1. Required fields
    # -----------------------------------------------------

    for field in REQUIRED_FIELDS:
        value = scholarship.get(field)

        if is_missing(value):
            add_issue(
                issues,
                index,
                scholarship,
                field,
                value,
                "MISSING_REQUIRED_FIELD",
            )
            reject(f"Missing required field: {field}")

    if not title or not source_url:
        return False, reasons

    # Provider is allowed to be unknown at this stage.
    # It must not be guessed from the aggregator name.

    # -----------------------------------------------------
    # 2. Date format validation
    # -----------------------------------------------------

    for field in DATE_FIELDS:
        value = scholarship.get(field)

        if is_missing(value):
            continue

        try:
            datetime.strptime(str(value), "%Y-%m-%d")

        except ValueError:
            add_issue(
                issues,
                index,
                scholarship,
                field,
                value,
                "INVALID_DATE_FORMAT",
                "Expected YYYY-MM-DD.",
            )
            reject(f"Invalid date format: {field}")

    # -----------------------------------------------------
    # 3. URL format validation
    # -----------------------------------------------------

    for field in ["source_url"] + OPTIONAL_URL_FIELDS:
        url = scholarship.get(field)

        if is_missing(url):
            continue

        if not valid_url_format(url):
            add_issue(
                issues,
                index,
                scholarship,
                field,
                url,
                "INVALID_URL_FORMAT",
            )

            if field == "source_url":
                reject("Invalid source URL")

    if reasons:
        return False, reasons

    # -----------------------------------------------------
    # 4. Check source page availability
    # -----------------------------------------------------

    result, status, final_url, page_text = fetch_page(source_url)

    if result != "RESPONDS":
        add_issue(
            issues,
            index,
            scholarship,
            "source_url",
            source_url,
            result,
            f"HTTP status: {status}; final URL: {final_url}",
        )

        reject("Source page could not be verified")
        return False, reasons

    # -----------------------------------------------------
    # 5. Check scholarship title on source page
    # -----------------------------------------------------

    if not title_found_on_page(title, page_text):
        add_issue(
            issues,
            index,
            scholarship,
            "title",
            title,
            "TITLE_NOT_FOUND_ON_SOURCE_PAGE",
            "The exact normalized title was not found in the fetched page text.",
        )

        reject("Scholarship title not found on source page")

    # -----------------------------------------------------
    # 6. Duplicate detection
    # -----------------------------------------------------

    duplicate_key = (
        source.lower(),
        normalize_title(title),
    )

    if duplicate_key in seen:
        add_issue(
            issues,
            index,
            scholarship,
            "title",
            title,
            "DUPLICATE_RECORD",
            f"Matches record {seen[duplicate_key]}.",
        )

        reject("Duplicate record")

    else:
        seen[duplicate_key] = index

    # -----------------------------------------------------
    # 7. Check optional URLs
    # -----------------------------------------------------

    for field in OPTIONAL_URL_FIELDS:
        url = scholarship.get(field)

        if is_missing(url):
            # Missing application links or deadlines are not
            # grounds for rejection.
            continue

        if not valid_url_format(url):
            add_issue(
                issues,
                index,
                scholarship,
                field,
                url,
                "INVALID_URL_FORMAT",
            )
            continue

        url_result, url_status, url_final, _ = fetch_page(url)

        if url_result != "RESPONDS":
            add_issue(
                issues,
                index,
                scholarship,
                field,
                url,
                url_result,
                f"HTTP status: {url_status}; final URL: {url_final}",
            )

    # -----------------------------------------------------
    # 8. Final decision
    # -----------------------------------------------------

    return len(reasons) == 0, reasons


# =========================================================
# MAIN AUDIT
# =========================================================

def main():

    print("\n========================================")
    print("SCHOLARSHIP FINDER - AUTOMATED AUDIT")
    print("========================================")

    if not INPUT_FILE.exists():
        print("\nERROR: Normalized JSON file not found.")
        print("Expected:", INPUT_FILE)
        return

    try:
        with INPUT_FILE.open("r", encoding="utf-8") as file:
            scholarships = json.load(file)

    except json.JSONDecodeError:
        print("\nERROR: Invalid JSON file.")
        return

    if not isinstance(scholarships, list):
        print("\nERROR: Expected a list of scholarship records.")
        return

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    verified_records = []
    audit_rows = []
    seen = {}

    rejected_count = 0

    # -----------------------------------------------------
    # Process records
    # -----------------------------------------------------

    for index, scholarship in enumerate(scholarships, start=1):

        print(
            f"\nChecking {index}/{len(scholarships)}: "
            f"{scholarship.get('title', 'Untitled')}"
        )

        if not isinstance(scholarship, dict):
            rejected_count += 1
            continue

        accepted, reasons = verify_record(
            index,
            scholarship,
            audit_rows,
            seen,
        )

        if accepted:
            verified_record = scholarship.copy()

            verified_record["verification"] = {
                "status": "AUTOMATED_CHECKS_PASSED",
                "verified_at": datetime.now().isoformat(),
                "method": "Source URL availability and title match",
            }

            verified_records.append(verified_record)
            print("Result: ACCEPTED")

        else:
            rejected_count += 1
            print("Result: REJECTED")
            for reason in reasons:
                print(" -", reason)

    # -----------------------------------------------------
    # Save verified records
    # -----------------------------------------------------

    with VERIFIED_FILE.open("w", encoding="utf-8") as file:
        json.dump(
            verified_records,
            file,
            indent=4,
            ensure_ascii=False,
        )

    # -----------------------------------------------------
    # Save audit CSV
    # -----------------------------------------------------

    audit_columns = [
        "record_number",
        "title",
        "provider",
        "source",
        "field",
        "value",
        "issue",
        "notes",
        "source_url",
    ]

    with AUDIT_FILE.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=audit_columns,
        )

        writer.writeheader()
        writer.writerows(audit_rows)

    # -----------------------------------------------------
    # Save summary
    # -----------------------------------------------------

    summary = {
        "total_records": len(scholarships),
        "accepted_records": len(verified_records),
        "rejected_records": rejected_count,
        "audit_issues": len(audit_rows),
        "completed_at": datetime.now().isoformat(),
        "verification_note": (
            "Automated checks do not establish definitive "
            "official authenticity. Source-page availability "
            "and title matching are preliminary evidence only."
        ),
    }

    with SUMMARY_FILE.open("w", encoding="utf-8") as file:
        json.dump(summary, file, indent=4)

    # -----------------------------------------------------
    # Terminal summary
    # -----------------------------------------------------

    print("\n========================================")
    print("AUDIT COMPLETED")
    print("========================================")

    print("Total records:", len(scholarships))
    print("Accepted records:", len(verified_records))
    print("Rejected records:", rejected_count)
    print("Audit issues:", len(audit_rows))

    print("\nOutput files:")
    print("Verified JSON:", VERIFIED_FILE)
    print("Audit CSV:", AUDIT_FILE)
    print("Summary JSON:", SUMMARY_FILE)

    print("\n========================================")


if __name__ == "__main__":
    main()
