
import json
import re
from difflib import SequenceMatcher
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
INPUT_FILE = DATA_DIR / "normalized_scholarships.json"
OUTPUT_FILE = DATA_DIR / "deduplicated_scholarships.json"

MERGE_THRESHOLD = 0.95
REVIEW_THRESHOLD = 0.90


def normalize_text(value):
    """Normalize wording without discarding meaningful differences."""
    if value is None:
        return ""

    text = str(value).lower().replace("&", " and ")

    # Normalize known naming variations.
    text = re.sub(r"ishan\s*uday", "ishan uday", text)
    text = re.sub(r"\bn\s*e\s*r\b", "north eastern region", text)
    text = re.sub(r"\bner\b", "north eastern region", text)

    # Convert punctuation and hyphens into spaces.
    text = re.sub(r"[^\w\s]", " ", text)

    return " ".join(text.split())


def title_key(value):
    """Remove generic words for a secondary title comparison."""
    text = normalize_text(value)

    text = re.sub(
        r"\bmerit based scheme\b|\bschemes?\b|\bscholarships?\b",
        " ",
        text,
    )

    return " ".join(text.split())


def title_similarity(title_a, title_b):
    a = normalize_text(title_a)
    b = normalize_text(title_b)

    if not a or not b:
        return 0.0

    return max(
        SequenceMatcher(None, a, b).ratio(),
        SequenceMatcher(
            None,
            title_key(title_a),
            title_key(title_b),
        ).ratio(),
    )


def has_conflicting_variant(title_a, title_b):
    """Detect variants that must never be merged automatically."""
    a = normalize_text(title_a)
    b = normalize_text(title_b)

    variants = [
        # School versus college, including plural forms.
        (r"\bschools?\b", r"\bcolleges?\b"),

        # Degree versus diploma.
        (r"\bdegrees?\b", r"\bdiplomas?\b"),

        # Undergraduate versus postgraduate.
        (
            r"\bunder\s*graduate\b|\bug\b",
            r"\bpost\s*graduate\b|\bpg\b",
        ),

        # Pre-matric versus post-matric.
        (
            r"\bpre\s*matric\b",
            r"\bpost\s*matric\b",
        ),

        # Other explicitly different variants.
        (r"\bboys?\b", r"\bgirls?\b"),
        (r"\bmales?\b", r"\bfemales?\b"),
    ]

    for first_pattern, second_pattern in variants:
        first_a = bool(re.search(first_pattern, a))
        second_a = bool(re.search(second_pattern, a))
        first_b = bool(re.search(first_pattern, b))
        second_b = bool(re.search(second_pattern, b))

        if (
            (first_a and second_b)
            or (second_a and first_b)
        ):
            return True

    return False


def conflicting_details(a, b):
    """Return populated fields whose normalized values disagree."""
    fields = [
        "amount",
        "education_level",
        "category",
        "location",
        "income_requirement",
    ]

    conflicts = []

    for field in fields:
        value_a = normalize_text(a.get(field))
        value_b = normalize_text(b.get(field))

        if value_a and value_b and value_a != value_b:
            conflicts.append(field)

    return conflicts


def provider_matches(a, b):
    provider_a = normalize_text(a.get("provider"))
    provider_b = normalize_text(b.get("provider"))

    return bool(
        provider_a
        and provider_b
        and provider_a == provider_b
    )


def compare_records(a, b):
    title_a = a.get("title", "")
    title_b = b.get("title", "")
    score = title_similarity(title_a, title_b)

    if not title_a or not title_b:
        return "different", score, "Missing title"

    # Variant protection takes priority over title similarity.
    if has_conflicting_variant(title_a, title_b):
        return "different", score, "Different scholarship variants"

    conflicts = conflicting_details(a, b)

    if conflicts:
        return (
            "different",
            score,
            "Conflicting details: " + ", ".join(conflicts),
        )

    same_provider = provider_matches(a, b)

    if score >= MERGE_THRESHOLD and same_provider:
        return (
            "merge",
            score,
            "95%+ title similarity, matching provider, no conflicts",
        )

    if score >= MERGE_THRESHOLD and not same_provider:
        return (
            "review",
            score,
            "High title similarity but provider is missing or differs",
        )

    if score >= REVIEW_THRESHOLD:
        return (
            "review",
            score,
            "Title similarity is at least 90%; needs verification",
        )

    return "different", score, "Below review threshold"


def merge_records(a, b):
    """Combine records while retaining missing fields and source details."""
    merged = dict(a)

    for key, value in b.items():
        if merged.get(key) in (None, "", [], {}):
            if value not in (None, "", [], {}):
                merged[key] = value

    # Preserve alternate titles.
    titles = set()

    for record in (a, b):
        title = record.get("title")

        if title:
            titles.add(title)

        existing_titles = record.get("alternate_titles", [])

        if isinstance(existing_titles, list):
            titles.update(
                item for item in existing_titles if item
            )

    titles.discard(merged.get("title"))

    if titles:
        merged["alternate_titles"] = sorted(titles)

    # Preserve source names.
    sources = set()

    for record in (a, b):
        source = record.get("source")

        if isinstance(source, str) and source:
            sources.add(source)

        existing_sources = record.get("sources", [])

        if isinstance(existing_sources, list):
            sources.update(
                item for item in existing_sources if item
            )

    if sources:
        merged["sources"] = sorted(sources)

    return merged


def main():
    if not INPUT_FILE.exists():
        print(f"ERROR: Input file not found:\n{INPUT_FILE}")
        print("Run normalizer.py first.")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as file:
        scholarships = json.load(file)

    if not isinstance(scholarships, list):
        print("ERROR: Expected a JSON list of scholarship records.")
        return

    if not all(isinstance(item, dict) for item in scholarships):
        print("ERROR: Every scholarship record must be a JSON object.")
        return

    # Compare every original pair before merging anything.
    pair_results = []

    for i in range(len(scholarships)):
        for j in range(i + 1, len(scholarships)):
            decision, score, reason = compare_records(
                scholarships[i],
                scholarships[j],
            )

            if decision in ("merge", "review"):
                pair_results.append(
                    (i, j, decision, score, reason)
                )

    # Process strongest matches first.
    merge_pairs = sorted(
        (
            item for item in pair_results
            if item[2] == "merge"
        ),
        key=lambda item: item[3],
        reverse=True,
    )

    # Each group represents records considered duplicates.
    parent = list(range(len(scholarships)))

    def find(index):
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def group_members(root):
        return [
            i for i in range(len(scholarships))
            if find(i) == root
        ]

    def can_join_groups(root_a, root_b):
        members_a = group_members(root_a)
        members_b = group_members(root_b)

        # Every cross-group pair must independently qualify
        # for merging. This prevents unsafe chain-based merges.
        for i in members_a:
            for j in members_b:
                decision, _, _ = compare_records(
                    scholarships[i],
                    scholarships[j],
                )

                if decision != "merge":
                    return False

        return True

    actual_merges = []

    for i, j, decision, score, reason in merge_pairs:
        root_a = find(i)
        root_b = find(j)

        if root_a == root_b:
            continue

        if not can_join_groups(root_a, root_b):
            continue

        parent[root_b] = root_a
        actual_merges.append((i, j, score, reason))

    # Build final records from the validated groups.
    groups = {}

    for index, record in enumerate(scholarships):
        root = find(index)
        groups.setdefault(root, []).append(record)

    final_scholarships = []

    for group in groups.values():
        merged = dict(group[0])

        for record in group[1:]:
            merged = merge_records(merged, record)

        final_scholarships.append(merged)

    # Print actual merges.
    print("\nAUTOMATIC MERGES")

    if not actual_merges:
        print("No records qualified for automatic merging.")

    for i, j, score, reason in actual_merges:
        print(f"\n  Listing A: {scholarships[i].get('title')}")
        print(f"  Listing B: {scholarships[j].get('title')}")
        print(f"  Similarity: {score:.0%}")
        print("  Reason:", reason)

    # Show review candidates, excluding records already in
    # the same successfully merged group.
    print("\nPOTENTIAL DUPLICATES REQUIRING REVIEW")

    review_count = 0

    for i, j, decision, score, reason in pair_results:
        if decision != "review":
            continue

        if find(i) == find(j):
            continue

        review_count += 1

        print(f"\n  Listing A: {scholarships[i].get('title')}")
        print(f"  Listing B: {scholarships[j].get('title')}")
        print(f"  Similarity: {score:.0%}")
        print("  Reason:", reason)
        print("  Action: Kept separate for review")

    # Save only the final dataset.
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(
            final_scholarships,
            file,
            indent=4,
            ensure_ascii=False,
        )

    print("\nFINAL SUMMARY")
    print("Original records:", len(scholarships))
    print("Duplicate records merged:", len(scholarships) - len(final_scholarships))
    print("Final records:", len(final_scholarships))
    print("Review candidates:", review_count)
    print("Output file:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
