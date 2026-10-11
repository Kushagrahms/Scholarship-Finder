import csv
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
import requests

# =========================================================
# EXACT PATHS: MATCH YOUR EXISTING PROJECT
# =========================================================

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR/"data"

INPUT_FILE = DATA_DIR/"normalized_scholarships.json"
AUDIT_FILE = DATA_DIR/"scholarship_audit.csv"
MANUAL_FILE = DATA_DIR/"manual_verification.csv"

REQUIRED_FIELDS=[
    "title", 
    "provider",
    "source",
    "source_url",
]

REVIEW_FIELDS = [
    "deadline",
    "application_url",
    "detail_url",
]

DATE_FIELDS = [
    "opening_date",
    "deadline",
]

URL_FIELDS = [
    "source_url",
    "application_url",
    "detail_url",
    "guidelines_url",
    "faq_url",
]

REQUEST_TIMEOUT = 10

def is_missing(value):
    return value is None or( isinstance(value,str) and not value.strip())

def valid_url_format(value):
    if not isinstance(value,str) or not value.strip():
        return False

    parsed = urlparse(value.strip())

    return(parsed.scheme in ("http","https") and bool(parsed.netloc) and "." in parsed.netloc)

def check_live_url(url):
    try:
        response = requests.get(url,timeout=REQUEST_TIMEOUT, allow_redirects=True, 
                                headers={"User-Agent":"ScholarshipFinderAudit/1.0"}, stream=True,)
        status = response.status_code
        finale_url = response.url
        response.close()

        if status in (403,429):
            result = "BLOCKED_OR_RATE_LIMITED"
        elif status >=400 :
            result = "HTTP_ERROR"
        else:
            result = "RESPONDS"

        return result,status,finale_url
    except requests.exceptions.Timeout:
        return "TIMEOUT","",""

    except requests.exceptions.RequestException as error:
        return(
            "CONNECTION_ERROR: "+type(error).__name__,"","",
        )

# =========================================================
# MAIN AUDIT
# =========================================================

def main():
    print("\n======================================")
    print("SCHOLARSHIP FINDER - DATA AUDIT")
    print("======================================")
    print("Input:", INPUT_FILE)

    if not INPUT_FILE.exists():
        print("\nERROR: Normalized file not found.")
        print("Expected path:", INPUT_FILE)
        print("\nRun this first:")
        print("python normalizer.py")
        return

    try:
        with INPUT_FILE.open("r",encoding="utf-8") as file:
            scholarships = json.load(file)

    except json.JSONDecodeError:
        print("ERROR: The normalized JSON is invalid.")
        return

    if not isinstance(scholarships,list):
        print("ERROR: Expected a JSON list of scholarships.")
        return
    if not all(isinstance(itme,dict )for itme in scholarships):
        print("ERROR: Every record must be a JSON object.")
        return

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    audit_rows = []
    manual_rows=[]
    seen={}

    # -----------------------------------------------------
    # Check each scholarship
    # -----------------------------------------------------
    for index,scholarship in enumerate(scholarships,start=1):
        title = scholarship.get("title") or ""
        provider = scholarship.get("provider") or ""
        source = scholarship.get("source") or ""
        source_url = scholarship.get("source_url") or ""

        def add_issue(field,value,issue,notes=""):
            audit_rows.append({
                "record_number":index,
                "title":title,
                "provider":provider,
                "field":field,
                "value":value if value is not None else "",
                "issue":issue,
                "notes":notes,
                "source_url":source_url,
            })
        for field in REQUIRED_FIELDS:
            value = scholarship.get(field)

            if is_missing(value):
                add_issue(
                    field,value,"MISSING_REQUIRED_FIELD",
                )
        for field in REVIEW_FIELDS:
            value = scholarship.get(field)

            if is_missing(value):
                add_issue(
                    field,value,"REVIEW_MISSING_VALUE","Check the official source; it may not publish this field.",
                )
        for field in DATE_FIELDS:
            value = scholarship.get(field)

            if is_missing(value):
                continue

            try:
                datetime.strptime(str(value), "%Y-%m-%d")
            except ValueError:
                add_issue(
                    field,value,"INVALID_DATE_FORMAT","Expected YYYY-MM-DD, e.g. 2026-10-31.",
                )
        for field in URL_FIELDS:
            url = scholarship.get(field)

            if is_missing(url):
                continue

            if not valid_url_format(url):
                add_issue(
                    field,url,"INVALID_URL_FORMAT",
                )
                continue
            result ,status,final_url = check_live_url(url)

            if result != "RESPONDS":
                add_issue(
                    field,url,result,f"HTTP status: {status}; final URL: {final_url}",
                )
        # E. Exact duplicate check
        # Use source + normalized title, as in your validator.
        duplicate_key = (
            " ".join(str(source).lower().split()),
            " ".join(str(title).lower().split()),
        )

        if title and duplicate_key in seen:
            add_issue(
                "title",
                title,
                "POSSIBLE_EXACT_DUPLICATE",
                f"Matches record {seen[duplicate_key]}. Review before removing.",
            )
        elif title:
            seen[duplicate_key] = index

        # F. Create a manual verification row.
        # Fill the comparison columns after checking the
        # original official website.
        manual_rows.append({
            "record_number": index,
            "title": title,
            "provider": provider,
            "opening_date": scholarship.get("opening_date") or "",
            "deadline": scholarship.get("deadline") or "",
            "source": source,
            "source_url": source_url,
            "application_url": scholarship.get("application_url") or "",
            "title_match": "",
            "provider_match": "",
            "deadline_match": "",
            "link_correct": "",
            "notes": "",
        })

    # -----------------------------------------------------
    # Write audit report
    # -----------------------------------------------------

    audit_columns = [
        "record_number",
        "title",
        "provider",
        "field",
        "value",
        "issue",
        "notes",
        "source_url",
    ]

    with AUDIT_FILE.open(
        "w", newline="", encoding="utf-8-sig"
    ) as file:
        writer = csv.DictWriter(file, fieldnames=audit_columns)
        writer.writeheader()
        writer.writerows(audit_rows)

    # -----------------------------------------------------
    # Write manual verification sheet
    # -----------------------------------------------------

    manual_columns = [
        "record_number",
        "title",
        "provider",
        "opening_date",
        "deadline",
        "source",
        "source_url",
        "application_url",
        "title_match",
        "provider_match",
        "deadline_match",
        "link_correct",
        "notes",
    ]

    with MANUAL_FILE.open(
        "w", newline="", encoding="utf-8-sig"
    ) as file:
        writer = csv.DictWriter(file, fieldnames=manual_columns)
        writer.writeheader()
        writer.writerows(manual_rows)

    # -----------------------------------------------------
    # Summary
    # -----------------------------------------------------

    print("\nRecords checked:", len(scholarships))
    print("Audit issues recorded:", len(audit_rows))
    print("Audit report:", AUDIT_FILE)
    print("Manual verification sheet:", MANUAL_FILE)

    print("\nAudit completed.")
    print("Review each issue; not every issue is a scraper bug.")


if __name__ == "__main__":
    main()






        
