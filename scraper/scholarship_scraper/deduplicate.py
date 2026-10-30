
"""Conservative scholarship deduplication.

Responsibilities:
- Identify likely duplicate scholarships.
- Protect meaningful eligibility variants.
- Preserve source URLs and raw metadata.
- Automatically merge only high-confidence matches.
- Keep uncertain matches separate and save them for review.
"""

import json
import re

from difflib import SequenceMatcher
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

INPUT_FILE = DATA_DIR / "normalized_scholarships.json"

OUTPUT_FILE = DATA_DIR / "deduplicated_scholarships.json"

REVIEW_FILE = DATA_DIR / "deduplication_review.json"

MERGE_THRESHOLD = 0.96
REVIEW_THRESHOLD = 0.90


# =========================================================
# TEXT NORMALIZATION
# =========================================================

def normalize_text(value):

    if value is None:
        return ""

    text = str(value).casefold().replace("&", " and ")

    text = re.sub(
        r"\bishan\s*uday\b",
        "ishan uday",
        text,
    )

    text = re.sub(
        r"\bn\s*e\s*r\b|\bner\b",
        "north eastern region",
        text,
    )

    text = re.sub(
        r"[^\w\s]",
        " ",
        text,
    )

    return " ".join(text.split())


def title_key(value):

    text = normalize_text(value)

    text = re.sub(
        r"\b(merit based|welfare based) scheme\b",
        " ",
        text,
    )

    text = re.sub(
        r"\bschemes?\b|\bscholarships?\b",
        " ",
        text,
    )

    return " ".join(text.split())


def similarity(title_a, title_b):

    a1 = normalize_text(title_a)
    b1 = normalize_text(title_b)

    if not a1 or not b1:
        return 0.0

    return max(
        SequenceMatcher(None, a1, b1).ratio(),
        SequenceMatcher(
            None,
            title_key(title_a),
            title_key(title_b),
        ).ratio(),
    )


# =========================================================
# VARIANT PROTECTION
# =========================================================

def has_opposing_variant(title_a, title_b):

    a = normalize_text(title_a)
    b = normalize_text(title_b)

    opposing_pairs = [

        (r"\bschools?\b", r"\bcolleges?\b"),

        (r"\bdegrees?\b", r"\bdiplomas?\b"),

        (
            r"\bunder\s*graduate\b|\bug\b",
            r"\bpost\s*graduate\b|\bpg\b",
        ),

        (
            r"\bpre\s*matric\b",
            r"\bpost\s*matric\b",
        ),

        (r"\bboys?\b", r"\bgirls?\b"),

        (r"\bmales?\b", r"\bfemales?\b"),

        (
            r"\bsc\b|\bscheduled caste\b",
            r"\bst\b|\bscheduled tribe\b",
        ),
    ]

    for left, right in opposing_pairs:

        left_a = bool(re.search(left, a))
        right_a = bool(re.search(right, a))

        left_b = bool(re.search(left, b))
        right_b = bool(re.search(right, b))

        if (
            (left_a and right_b)
            or (right_a and left_b)
        ):
            return True

    return False


# =========================================================
# PROVIDER NORMALIZATION
# =========================================================

def canonical_provider(value):

    text = normalize_text(value)

    if not text:
        return ""

    aliases = {

        "ugc":
            "university grants commission",

        "university grants commission":
            "university grants commission",

        "aicte":
            "all india council for technical education",

        "all india council for technical education":
            "all india council for technical education",

        "mha":
            "ministry of home affairs",

        "ministry of home affairs":
            "ministry of home affairs",
    }

    return aliases.get(text, text)


# =========================================================
# CONFLICT CHECKING
# =========================================================

def conflicting_details(a, b):

    conflicts = []

    fields = (
        "amount",
        "amount_text",
        "education_level",
        "category",
        "location",
        "income_requirement",
        "tenure",
    )

    for field in fields:

        value_a = normalize_text(a.get(field))
        value_b = normalize_text(b.get(field))

        if (
            value_a
            and value_b
            and value_a != value_b
        ):
            conflicts.append(field)

    return conflicts


# =========================================================
# RECORD COMPARISON
# =========================================================

def compare_records(a, b):

    title_a = a.get("title")
    title_b = b.get("title")

    score = similarity(title_a, title_b)

    if not title_a or not title_b:
        return "different", score, "Missing title"

    if has_opposing_variant(title_a, title_b):

        return (
            "different",
            score,
            "Different protected scholarship variants",
        )

    conflicts = conflicting_details(a, b)

    if conflicts:

        return (
            "different",
            score,
            "Conflicting details: " + ", ".join(conflicts),
        )

    provider_a = canonical_provider(a.get("provider"))
    provider_b = canonical_provider(b.get("provider"))

    if (
        provider_a
        and provider_b
        and provider_a != provider_b
    ):

        return (
            "different",
            score,
            "Different known providers",
        )

    if (
        score >= MERGE_THRESHOLD
        and provider_a
        and provider_a == provider_b
    ):

        return (
            "merge",
            score,
            "High title similarity, equivalent known provider, no conflicts",
        )

    if score >= REVIEW_THRESHOLD:

        if not provider_a or not provider_b:

            return (
                "review",
                score,
                "Provider missing on at least one record; do not auto-merge",
            )

        return (
            "review",
            score,
            "High title similarity; requires confirmation",
        )

    return (
        "different",
        score,
        "Below review threshold",
    )


# =========================================================
# MERGING HELPERS
# =========================================================

def nonempty(value):

    return value not in (None, "", [], {})


def make_source_reference(record):

    fields = (
        "source",
        "source_url",
        "detail_url",
        "application_url",
        "guidelines_url",
        "faq_url",
        "scraped_at",
    )

    return {
        key: record.get(key)
        for key in fields
        if nonempty(record.get(key))
    }


def merge_records(records):

    """Merge fields without losing original source provenance."""

    merged = dict(records[0])

    protected_fields = {
        "raw_metadata",
        "source",
        "source_url",
        "detail_url",
        "application_url",
        "guidelines_url",
        "faq_url",
        "sources",
        "source_references",
        "source_metadata",
        "alternate_titles",
    }

    # Fill missing ordinary fields.
    for record in records[1:]:

        for key, value in record.items():

            if key in protected_fields:
                continue

            if (
                not nonempty(merged.get(key))
                and nonempty(value)
            ):
                merged[key] = value

    titles = set()
    sources = set()
    source_refs = []
    source_metadata = []

    for record in records:

        title = record.get("title")

        if title:
            titles.add(title)

        existing_titles = record.get("alternate_titles", [])

        if isinstance(existing_titles, list):

            titles.update(
                item for item in existing_titles if item
            )

        source = record.get("source")

        if source:
            sources.add(source)

        existing_sources = record.get("sources", [])

        if isinstance(existing_sources, list):

            sources.update(
                item for item in existing_sources if item
            )

        reference = make_source_reference(record)

        if reference and reference not in source_refs:
            source_refs.append(reference)

        metadata = record.get("raw_metadata")

        if nonempty(metadata):

            entry = {
                "source": source,
                "metadata": metadata,
            }

            if entry not in source_metadata:
                source_metadata.append(entry)

        # Preserve already merged provenance if this function
        # is ever applied to records that were merged previously.
        for reference in record.get("source_references", []):
            if reference not in source_refs:
                source_refs.append(reference)

        for entry in record.get("source_metadata", []):
            if entry not in source_metadata:
                source_metadata.append(entry)

    titles.discard(merged.get("title"))

    if titles:
        merged["alternate_titles"] = sorted(titles)

    if sources:
        merged["sources"] = sorted(sources)

    if source_refs:
        merged["source_references"] = source_refs

    if source_metadata:
        merged["source_metadata"] = source_metadata

    return merged


# =========================================================
# MAIN
# =========================================================

def main():

    if not INPUT_FILE.exists():

        raise SystemExit(
            f"ERROR: Input not found: {INPUT_FILE}\n"
            "Run normalizer.py first."
        )

    try:

        with INPUT_FILE.open("r", encoding="utf-8") as handle:
            records = json.load(handle)

    except json.JSONDecodeError as exc:

        raise SystemExit(
            f"ERROR: Invalid JSON in {INPUT_FILE}: {exc}"
        )

    if (
        not isinstance(records, list)
        or any(not isinstance(record, dict) for record in records)
    ):

        raise SystemExit(
            "ERROR: Expected a JSON list containing only objects."
        )

    pair_results = []

    # Compare every pair.
    for i in range(len(records)):

        for j in range(i + 1, len(records)):

            decision, score, reason = compare_records(
                records[i],
                records[j],
            )

            if decision in ("merge", "review"):

                pair_results.append({

                    "record_a": i + 1,
                    "record_b": j + 1,

                    "title_a": records[i].get("title"),
                    "title_b": records[j].get("title"),

                    "decision": decision,

                    "similarity": round(score, 4),

                    "reason": reason,
                })

    # Automatic merge candidates.
    merge_candidates = sorted(

        (
            item
            for item in pair_results
            if item["decision"] == "merge"
        ),

        key=lambda item: item["similarity"],

        reverse=True,
    )

    parent = list(range(len(records)))

    def find(index):

        while parent[index] != index:

            parent[index] = parent[parent[index]]
            index = parent[index]

        return index

    def members(root):

        return [
            index
            for index in range(len(records))
            if find(index) == root
        ]

    def can_join(root_a, root_b):

        for i in members(root_a):

            for j in members(root_b):

                decision, _, _ = compare_records(
                    records[i],
                    records[j],
                )

                if decision != "merge":
                    return False

        return True

    actual_merges = []

    for candidate in merge_candidates:

        i = candidate["record_a"] - 1
        j = candidate["record_b"] - 1

        root_a = find(i)
        root_b = find(j)

        if root_a == root_b:
            continue

        if not can_join(root_a, root_b):
            continue

        parent[root_b] = root_a

        actual_merges.append(candidate)

    # Build final groups.
    groups = {}

    for index, record in enumerate(records):

        root = find(index)

        groups.setdefault(root, []).append(record)

    final_records = [
        merge_records(group)
        for group in groups.values()
    ]

    # Review candidates remain separate.
    review_items = []

    for item in pair_results:

        if item["decision"] != "review":
            continue

        i = item["record_a"] - 1
        j = item["record_b"] - 1

        if find(i) != find(j):
            review_items.append(item)

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    with OUTPUT_FILE.open("w", encoding="utf-8") as handle:

        json.dump(
            final_records,
            handle,
            indent=2,
            ensure_ascii=False,
        )

    with REVIEW_FILE.open("w", encoding="utf-8") as handle:

        json.dump(

            {
                "input_records": len(records),

                "output_records": len(final_records),

                "automatic_merge_groups_reduced_by":
                    len(records) - len(final_records),

                "review_candidates": review_items,

                "automatic_merges": actual_merges,

                "note": (
                    "Review candidates remain separate in the output. "
                    "No uncertain pair is automatically merged."
                ),
            },

            handle,

            indent=2,

            ensure_ascii=False,
        )

    print("\nDEDUPLICATION COMPLETE")

    print("Input records:", len(records))

    print("Output records:", len(final_records))

    print(
        "Records consolidated:",
        len(records) - len(final_records),
    )

    print("Review candidates:", len(review_items))

    print("Output:", OUTPUT_FILE)

    print("Review report:", REVIEW_FILE)


if __name__ == "__main__":
    main()
