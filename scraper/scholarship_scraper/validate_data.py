import json
import sys
from datetime import datetime


# =========================================================
# GET FILE PATH
# =========================================================

if len(sys.argv) < 2:

    print("\nPlease provide a JSON file.")
    print("\nExample:")
    print(
        "python validate_data.py "
        "data/nsp_scholarships.json"
    )

    sys.exit(1)


FILE_PATH = sys.argv[1]


# =========================================================
# LOAD DATA
# =========================================================

try:

    with open(
        FILE_PATH,
        "r",
        encoding="utf-8"
    ) as file:

        scholarships = json.load(file)

except FileNotFoundError:

    print("\nFile not found:")
    print(FILE_PATH)

    sys.exit(1)

except json.JSONDecodeError:

    print("\nInvalid JSON file:")
    print(FILE_PATH)

    sys.exit(1)


# =========================================================
# REQUIRED FIELDS
# =========================================================

COMMON_REQUIRED_FIELDS = [
    "source",
    "title",
    "source_url"
]


# =========================================================
# PRINT HEADER
# =========================================================

print("\n================================")
print("SCHOLARSHIP DATA VALIDATION")
print("================================")

print("File:", FILE_PATH)
print("Total records:", len(scholarships))


# =========================================================
# CHECK REQUIRED FIELDS
# =========================================================

invalid_records = 0

for index, scholarship in enumerate(
    scholarships,
    start=1
):

    missing_fields = []

    for field in COMMON_REQUIRED_FIELDS:

        if (
            field not in scholarship
            or scholarship[field] is None
            or scholarship[field] == ""
        ):

            missing_fields.append(field)

    if missing_fields:

        invalid_records += 1

        print("\nRecord:", index)
        print(
            "Title:",
            scholarship.get("title")
        )
        print(
            "Missing fields:",
            missing_fields
        )


# =========================================================
# CHECK DATES
# =========================================================

DATE_FIELDS = [
    "scheme_open_date",
    "application_deadline",
    "defective_verification_deadline",
    "institute_verification_deadline",
    "dno_sno_mno_verification_deadline"
]

invalid_dates = 0

for index, scholarship in enumerate(
    scholarships,
    start=1
):

    for field in DATE_FIELDS:

        if field not in scholarship:
            continue

        date_value = scholarship.get(field)

        if date_value is None or date_value == "":
            continue

        try:

            datetime.strptime(
                date_value,
                "%Y-%m-%d"
            )

        except ValueError:

            invalid_dates += 1

            print("\nInvalid date found")
            print("Record:", index)
            print(
                "Title:",
                scholarship.get("title")
            )
            print("Field:", field)
            print("Value:", date_value)


# =========================================================
# CHECK URLS
# =========================================================

URL_FIELDS = [
    "specifications_url",
    "faq_url",
    "detail_url",
    "source_url"
]

invalid_urls = 0

for index, scholarship in enumerate(
    scholarships,
    start=1
):

    for field in URL_FIELDS:

        if field not in scholarship:
            continue

        url = scholarship.get(field)

        # Missing URL is allowed
        if url is None or url == "":
            continue

        # Fake /null URL
        if url.rstrip("/").endswith("/null"):

            invalid_urls += 1

            print("\nInvalid URL found")
            print("Record:", index)
            print(
                "Title:",
                scholarship.get("title")
            )
            print("Field:", field)
            print("URL:", url)

        # Invalid URL format
        elif not (
            url.startswith("http://")
            or url.startswith("https://")
        ):

            invalid_urls += 1

            print("\nInvalid URL format")
            print("Record:", index)
            print(
                "Title:",
                scholarship.get("title")
            )
            print("Field:", field)
            print("URL:", url)


# =========================================================
# CHECK DUPLICATES
# =========================================================

duplicate_records = 0

seen_scholarships = set()

for index, scholarship in enumerate(
    scholarships,
    start=1
):

    source = scholarship.get(
        "source"
    )

    title = scholarship.get(
        "title"
    )

    if source:
        source = " ".join(
            source.split()
        )

    if title:
        title = " ".join(
            title.split()
        )

    duplicate_key = (
        source,
        title
    )

    if duplicate_key in seen_scholarships:

        duplicate_records += 1

        print(
            "\nDuplicate scholarship found"
        )

        print("Record:", index)
        print("Source:", source)
        print("Title:", title)

    else:

        seen_scholarships.add(
            duplicate_key
        )


# =========================================================
# CHECK EMPTY IMPORTANT VALUES
# =========================================================

empty_values = 0

IMPORTANT_FIELDS = [
    "title"
]

for index, scholarship in enumerate(
    scholarships,
    start=1
):

    for field in IMPORTANT_FIELDS:

        value = scholarship.get(field)

        if value is None or value == "":

            empty_values += 1

            print("\nEmpty important field")
            print("Record:", index)
            print("Field:", field)


# =========================================================
# FINAL RESULT
# =========================================================

print("\n================================")

if invalid_records == 0:
    print("REQUIRED FIELDS: PASS")
else:
    print("REQUIRED FIELDS: FAIL")
    print(
        "Invalid records:",
        invalid_records
    )


if invalid_dates == 0:
    print("DATE VALIDATION: PASS")
else:
    print("DATE VALIDATION: FAIL")
    print(
        "Invalid dates:",
        invalid_dates
    )


if invalid_urls == 0:
    print("URL VALIDATION: PASS")
else:
    print("URL VALIDATION: FAIL")
    print(
        "Invalid URLs:",
        invalid_urls
    )


if duplicate_records == 0:
    print("DUPLICATE CHECK: PASS")
else:
    print("DUPLICATE CHECK: FAIL")
    print(
        "Duplicate records:",
        duplicate_records
    )


if empty_values == 0:
    print("IMPORTANT VALUES: PASS")
else:
    print("IMPORTANT VALUES: FAIL")
    print(
        "Empty important values:",
        empty_values
    )


print("================================")