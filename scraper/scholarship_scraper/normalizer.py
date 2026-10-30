import json
from pathlib import Path
from datetime import datetime


# =========================================================
# PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"

NSP_FILE = DATA_DIR / "nsp_scholarships.json"
UGC_FILE = DATA_DIR / "ugc_scholarships.json"
SCHEMESININDIA_FILE = DATA_DIR / "schemesinindia_scholarships.json"

OUTPUT_FILE = DATA_DIR / "normalized_scholarships.json"


# =========================================================
# LOAD JSON FILE
# =========================================================

def load_json(file_path):

    try:

        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except FileNotFoundError:

        print(f"\nFile not found: {file_path}")
        return []

    except json.JSONDecodeError:

        print(f"\nInvalid JSON file: {file_path}")
        return []


# =========================================================
# CLEAN TEXT
# =========================================================

def clean_text(value):

    if value is None:
        return None

    if not isinstance(value, str):
        return value

    value = " ".join(value.split())

    if value == "":
        return None

    return value

def get_value(data, *keys):
    """Return the first non-empty value found in the raw record."""
    for key in keys:
        value = data.get(key)

        if value is None:
            continue

        if isinstance(value, str):
            value = value.strip()
            if not value:
                continue

        return value

    return None


# =========================================================
# NORMALIZE NSP RECORD
# =========================================================

def normalize_nsp(scholarship):

    return {

        # -----------------------------------------
        # Common scholarship fields
        # -----------------------------------------

        "title": clean_text(
            scholarship.get("title")
        ),

        "provider": clean_text(
            scholarship.get("section")
        ),

        "description": None,

        "objective": None,

        "eligibility": None,

        "amount": None,

        "slots": None,

        "tenure": None,

        "education_level": None,

        "category": None,

        "location": None,

        "income_requirement": None,

        # -----------------------------------------
        # Dates
        # -----------------------------------------

        "opening_date": scholarship.get(
            "scheme_open_date"
        ),

        "deadline": scholarship.get(
            "application_deadline"
        ),

        # -----------------------------------------
        # URLs
        # -----------------------------------------

        "application_url": get_value(
            scholarship,
            "application_url",
            "application_link",
            "apply_url",
        ),

        "source": clean_text(
            scholarship.get("source")
        ),

        "source_url": get_value(
            scholarship,
            "source_url",
        ),

        "detail_url": get_value(
            scholarship,
            "detail_url",
            "scheme_url",
            "scholarship_url",
        ),

        "guidelines_url": get_value(
            scholarship,
            "specifications_url",
            "guidelines_url",
        ),

        "faq_url": get_value(
            scholarship,
            "faq_url",
        ),

        # -----------------------------------------
        # Metadata
        # -----------------------------------------

        "scraped_at": datetime.now().isoformat(),

        # Keep NSP-specific information
        # instead of throwing it away.
        "raw_metadata": {

            "timeline": scholarship.get(
                "timeline"
            ),

            "defective_verification_deadline":
                scholarship.get(
                    "defective_verification_deadline"
                ),

            "institute_verification_deadline":
                scholarship.get(
                    "institute_verification_deadline"
                ),

            "dno_sno_mno_verification_deadline":
                scholarship.get(
                    "dno_sno_mno_verification_deadline"
                )
        }
    }


# =========================================================
# NORMALIZE UGC RECORD
# =========================================================

def normalize_ugc(scholarship):

    return {

        # -----------------------------------------
        # Common scholarship fields
        # -----------------------------------------

        "title": clean_text(
            scholarship.get("title")
        ),

        "provider": clean_text(
            scholarship.get("source")
        ),

        "description": None,

        "objective": clean_text(
            scholarship.get("objective")
        ),

        "eligibility": clean_text(
            scholarship.get("eligibility")
        ),

        "amount": clean_text(
            scholarship.get("financial_assistance")
        ),

        "slots": clean_text(
            scholarship.get("slots")
        ),

        "tenure": clean_text(
            scholarship.get("tenure")
        ),

        "education_level": None,

        "category": None,

        "location": None,

        "income_requirement": None,

        # -----------------------------------------
        # Dates
        # -----------------------------------------

        "opening_date": get_value(
            scholarship,
            "opening_date",
            "scheme_open_date",
        ),

        "deadline": get_value(
            scholarship,
            "deadline",
            "application_deadline",
        ),

        # -----------------------------------------
        # URLs
        # -----------------------------------------

        "application_url": get_value(
            scholarship,
            "application_url",
            "application_link",
            "apply_url",
        ),

        "source": clean_text(
            scholarship.get("source")
        ),

        "source_url": get_value(
            scholarship,
            "source_url",
        ),

        "detail_url": get_value(
            scholarship,
            "detail_url",
            "scheme_url",
            "scholarship_url",
        ),

        "guidelines_url": get_value(
            scholarship,
            "guidelines_url",
            "specifications_url",
        ),

        "faq_url": get_value(
            scholarship,
            "faq_url",
        ),
        # -----------------------------------------
        # Metadata
        # -----------------------------------------

        "scraped_at": datetime.now().isoformat(),

        "raw_metadata": {

            "remark": clean_text(
                scholarship.get("remark")
            )
        }
    }
# =========================================================
# NORMALIZE SCHEMES IN INDIA RECORD
# =========================================================
def normalize_schemesinindia(scholarship):

    key_facts = scholarship.get("key_facts")

    if not isinstance(key_facts,dict):
        key_facts={}

    eligibility = scholarship.get("eligibility")

    if isinstance(eligibility,list):
        eligibility = "; ".join(str(item).strip()
                                for item in eligibility
                                if item)
    amount_text = clean_text(scholarship.get("amount_text") or key_facts.get("Scholarship Amount"))



    return{
        "title":clean_text(scholarship.get("title")),

        "provider":None,

        "description":clean_text(scholarship.get("description")),

        "objective":clean_text(scholarship.get("objective")),

        "eligibility":clean_text(eligibility),

        "amount":None,
        "amount_text":amount_text,

        "slots": clean_text(key_facts.get("Beneficiaries / Year")),

        "tenure": clean_text(scholarship.get("tenure") or key_facts.get("Duration")),

        "education_level":None,

        "category": None,

        "location": None,

        "income_requirement":clean_text(scholarship.get("income_requirement") or key_facts.get("Income Limit")),

        "opening_date":scholarship.get("opening_date"),

        "deadline":scholarship.get("deadline"),

        "application_url" : get_value(scholarship, "application_url", "application_link","apply_url"),

        "source":clean_text(scholarship.get("source")),

        "source_url":get_value(scholarship,"source_url"),

        "detail_url":get_value(scholarship, "detail_url","scheme_url","scholarship_url"),

        "guidelines_url":get_value(scholarship,"guidelines_url","specifications_url"),

        "faq_url":get_value(scholarship, "faq_url"),

        "scraped_at": datetime.now().isoformat(),

        "raw_metadata": {"documents_required": scholarship.get("documents_required"),

        "amount_text": scholarship.get("amount_text"),

        "key_facts": key_facts, "faqs": scholarship.get("faqs"),

        "external_links": scholarship.get("external_links", []),
        
        "application_url_candidate": scholarship.get(
        "application_url_candidate"),

        "original_scraped_at": scholarship.get("scraped_at")
        }
    }


# =========================================================
# MAIN
# =========================================================

def main():

    print("\n========================================")
    print("SCHOLARSHIP DATA NORMALIZER")
    print("========================================")

    # -----------------------------------------
    # Load raw data
    # -----------------------------------------

    nsp_data = load_json(NSP_FILE)

    ugc_data = load_json(UGC_FILE)

    schemesinindia_data = load_json(SCHEMESININDIA_FILE)

    print(
        f"\nNSP records found: {len(nsp_data)}"
    )

    print(
        f"UGC records found: {len(ugc_data)}"
    )
    print(
    f"Schemes in India records found: {len(schemesinindia_data)}"
    )

    # -----------------------------------------
    # Normalize NSP
    # -----------------------------------------

    normalized_data = []

    for scholarship in nsp_data:

        normalized_data.append(
            normalize_nsp(scholarship)
        )

    # -----------------------------------------
    # Normalize UGC
    # -----------------------------------------

    for scholarship in ugc_data:

        normalized_data.append(
            normalize_ugc(scholarship)
        )

    # -----------------------------------------
    # Normalize Schemes in India
    # -----------------------------------------
    for scholarship in schemesinindia_data:

        normalized_data.append(
            normalize_schemesinindia(scholarship)
        )
    # -----------------------------------------
    # Save normalized data
    # -----------------------------------------

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            normalized_data,
            file,
            indent=4,
            ensure_ascii=False
        )

    # -----------------------------------------
    # Summary
    # -----------------------------------------

    print("\n========================================")
    print("NORMALIZATION COMPLETE")
    print("========================================")

    print(
        f"NSP normalized: {len(nsp_data)}"
    )

    print(
        f"UGC normalized: {len(ugc_data)}"
    )
    print(
    f"Schemes in India normalized: {len(schemesinindia_data)}"
    )

    print(
        f"Total normalized: {len(normalized_data)}"
    )

    print(
        f"\nOutput file:"
    )

    print(OUTPUT_FILE)

    print("========================================")


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    main()