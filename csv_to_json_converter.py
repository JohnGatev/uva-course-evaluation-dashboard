"""
CSV → Aspect JSON Converter
============================
Converts a semicolon-delimited course feedback CSV (Qualtrics-style, 3-row header)
into one JSON file per evaluated aspect.

Usage
-----
1. Set INPUT_CSV  to the path of your CSV file.
2. Set OUTPUT_DIR to the folder where the JSON files should be saved.
3. Run the script. The output folder is created automatically if it does not exist.

Output
------
One JSON file per aspect, named after the aspect_key, e.g.:
    assignments.json
    organisation_of_the_course.json
    course_readings.json
    lecture_content_or_delivery.json
    tutorial_activities.json
    didactic_approach_of_the_lecturers.json
    other.json
"""

import csv
import json
import os
import re

# ── USER CONFIGURATION ────────────────────────────────────────────────────────
INPUT_CSV  = os.environ.get("INPUT_CSV", r"/Users/johngatev/Library/CloudStorage/OneDrive-UvA/Work/UvA/UvA TLC - AI Innovation and Literacy/Bot Setup/Summary Bot/Evaluation Dashboard/raw file Midterm feedback CR2CA_February 26, 2026_08.csv")          # <-- set your CSV path here
OUTPUT_DIR = os.environ.get("OUTPUT_DIR", r"/Users/johngatev/Library/CloudStorage/OneDrive-UvA/Work/UvA/UvA TLC - AI Innovation and Literacy/Bot Setup/Summary Bot/Evaluation Dashboard/JSON Outputs")      # <-- set your output folder here
# ─────────────────────────────────────────────────────────────────────────────


# ── ASPECT DEFINITIONS ───────────────────────────────────────────────────────
# Each entry maps:
#   display_label      : the label as it appears in Q2_Tips / Q4_Tops cells
#   aspect_key         : snake_case identifier used in IDs and as filename
#   tip_col_index      : 0-based column index of the tip free-text field
#   top_col_index      : 0-based column index of the top free-text field
#   top_display_label  : label as it appears in Q4_Tops (may differ from tip label)

ASPECTS = [
    {
        "display_label":     "The organisation of the course",
        "aspect_key":        "organisation_of_the_course",
        "display_name":      "The organisation of the course",
        "tip_col_index":     2,
        "top_col_index":     10,
        "top_display_label": "The organisation of the course",
    },
    {
        "display_label":     "The course readings",
        "aspect_key":        "course_readings",
        "display_name":      "The course readings",
        "tip_col_index":     3,
        "top_col_index":     11,
        "top_display_label": "The course readings",
    },
    {
        "display_label":     "The lecture content or delivery",
        "aspect_key":        "lecture_content_or_delivery",
        "display_name":      "The lecture content or delivery",
        "tip_col_index":     4,
        "top_col_index":     12,
        "top_display_label": "The lecture content or delivery",
    },
    {
        "display_label":     "The tutorial activities",
        "aspect_key":        "tutorial_activities",
        "display_name":      "The tutorial activities",
        "tip_col_index":     5,
        "top_col_index":     13,
        "top_display_label": "The tutorial activities",
    },
    {
        "display_label":     "The didactic approach of the lecturer(s)",
        "aspect_key":        "didactic_approach_of_the_lecturers",
        "display_name":      "The didactic approach of the lecturer(s)",
        "tip_col_index":     6,
        "top_col_index":     14,
        "top_display_label": "The didactic approach of the lecturer(s)",
    },
    {
        "display_label":     "The assignments",
        "aspect_key":        "assignments",
        "display_name":      "The assignments",
        "tip_col_index":     7,
        "top_col_index":     15,
        "top_display_label": "The assignments",
    },
    {
        "display_label":     "Other",
        "aspect_key":        "other",
        "display_name":      "Other",
        "tip_col_index":     8,
        "top_col_index":     16,
        "top_display_label": "Other",
    },
]

# Build fast lookup: display_label -> aspect definition
ASPECT_BY_TIP_LABEL = {a["display_label"]:     a for a in ASPECTS}
ASPECT_BY_TOP_LABEL = {a["top_display_label"]: a for a in ASPECTS}


def normalise_label(raw: str) -> str:
    """Strip whitespace from a selection label."""
    return raw.strip()


def parse_selection_list(cell: str) -> list[tuple[str, int]]:
    """
    Parse a comma-separated selection cell (Q2_Tips or Q4_Tops).
    Returns a list of (normalised_label, 1-based_position) tuples.
    Empty or whitespace-only cells return an empty list.
    """
    if not cell or not cell.strip():
        return []
    items = [normalise_label(item) for item in cell.split(",") if normalise_label(item)]
    return [(label, idx + 1) for idx, label in enumerate(items)]


def build_comment_id(row_index: int, comment_type: str, aspect_key: str, position: int) -> str:
    """
    Construct a comment ID in the format:
        r{NNNN}_{tip|top}_{aspect_key}_{position}

    row_index   : 0-based index of the data row (header rows excluded)
    comment_type: 'tip' or 'top'
    aspect_key  : snake_case aspect identifier
    position    : ordinal position of this aspect in the respondent's selection list
    """
    return f"r{row_index:04d}_{comment_type}_{aspect_key}_{position}"


def load_csv(filepath: str) -> list[list[str]]:
    """
    Load the CSV, stripping the BOM if present, using semicolon as delimiter.
    Returns all rows as lists of strings (including the 2 header rows).
    """
    rows = []
    with open(filepath, newline="", encoding="utf-8-sig") as fh:
        reader = csv.reader(fh, delimiter=";")
        for row in reader:
            rows.append(row)
    return rows


def initialise_aspect_store() -> dict:
    """
    Build the in-memory data structure that will accumulate comments
    for every aspect before serialisation.
    """
    store = {}
    for aspect in ASPECTS:
        key = aspect["aspect_key"]
        store[key] = {
            "aspect": {
                "aspect_key":              key,
                "display_name":            aspect["display_name"],
                "display_labels_observed": [],          # populated during processing
            },
            "counts": {
                "tip_comment_count": 0,
                "top_comment_count": 0,
            },
            "tips_by_tutorial_group": {},
            "tops_by_tutorial_group": {},
            "_tip_labels_seen":  set(),                 # internal; removed before output
            "_top_labels_seen":  set(),                 # internal; removed before output
        }
    return store


def add_comment(
    store:         dict,
    aspect_key:    str,
    comment_type:  str,   # 'tip' or 'top'
    tutorial_group: str,
    comment_id:    str,
    text:          str,
    label_seen:    str,
):
    """Insert a single comment into the correct bucket of the store."""
    entry = store[aspect_key]

    # Track observed display labels
    label_set_key = f"_{comment_type}_labels_seen"
    entry[label_set_key].add(label_seen)

    # Choose the correct group dict
    group_dict_key = f"{comment_type}s_by_tutorial_group"
    group_dict     = entry[group_dict_key]

    if tutorial_group not in group_dict:
        group_dict[tutorial_group] = {"comment_count": 0, "comments": []}

    group_dict[tutorial_group]["comments"].append(
        {"id": comment_id, "tutorial_group": tutorial_group, "text": text}
    )
    group_dict[tutorial_group]["comment_count"] += 1
    entry["counts"][f"{comment_type}_comment_count"] += 1


def process_rows(data_rows: list[list[str]], store: dict) -> None:
    """
    Iterate over every respondent row and populate the store.

    Column layout (0-based):
        0   Q1_Tutorial  – tutorial group number
        1   Q2_Tips      – comma-separated tip aspect selections
        2   Q3_Tips_explained_1  – organisation_of_the_course tip text
        3   Q3_Tips_explained_2  – course_readings tip text
        4   Q3_Tips_explained_7  – lecture_content_or_delivery tip text
        5   Q3_Tips_explained_3  – tutorial_activities tip text
        6   Q3_Tips_explained_4  – didactic_approach_of_the_lecturers tip text
        7   Q3_Tips_explained_5  – assignments tip text
        8   Q3_Tips_explained_6  – other tip text
        9   Q4_Tops      – comma-separated top aspect selections
        10  Q5_Tops_explained_1  – organisation_of_the_course top text
        11  Q5_Tops_explained_2  – course_readings top text  (label: "course material(s)")
        12  Q5_Tops_explained_7  – lecture_content_or_delivery top text
        13  Q5_Tops_explained_3  – tutorial_activities top text
        14  Q5_Tops_explained_4  – didactic_approach_of_the_lecturers top text
        15  Q5_Tops_explained_5  – assignments top text
        16  Q5_Tops_explained_6  – other top text
    """
    for row_index, row in enumerate(data_rows):
        # Pad short rows to avoid index errors
        while len(row) < 17:
            row.append("")

        tutorial_group = row[0].strip()
        if not tutorial_group:
            continue  # skip empty rows

        # ── TIPS ──────────────────────────────────────────────────────────────
        tip_selections = parse_selection_list(row[1])
        for label, position in tip_selections:
            aspect = ASPECT_BY_TIP_LABEL.get(label)
            if aspect is None:
                continue  # unrecognised label; skip

            text = row[aspect["tip_col_index"]].strip()
            if not text:
                continue  # selected but no free text; skip

            comment_id = build_comment_id(row_index, "tip", aspect["aspect_key"], position)
            add_comment(
                store,
                aspect["aspect_key"],
                "tip",
                tutorial_group,
                comment_id,
                text,
                label,
            )

        # ── TOPS ──────────────────────────────────────────────────────────────
        top_selections = parse_selection_list(row[9])
        for label, position in top_selections:
            aspect = ASPECT_BY_TOP_LABEL.get(label)
            if aspect is None:
                continue

            text = row[aspect["top_col_index"]].strip()
            if not text:
                continue

            comment_id = build_comment_id(row_index, "top", aspect["aspect_key"], position)
            add_comment(
                store,
                aspect["aspect_key"],
                "top",
                tutorial_group,
                comment_id,
                text,
                label,
            )


def finalise_store(store: dict) -> None:
    """
    Convert internal sets to sorted lists and remove private keys
    before serialisation.
    """
    for entry in store.values():
        entry["aspect"]["display_labels_observed"] = sorted(
            entry.pop("_tip_labels_seen") | entry.pop("_top_labels_seen")
        )


def write_json_files(store: dict, output_dir: str) -> None:
    """Write one JSON file per aspect into output_dir."""
    os.makedirs(output_dir, exist_ok=True)
    for aspect_key, data in store.items():
        filepath = os.path.join(output_dir, f"{aspect_key}.json")
        with open(filepath, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
        print(f"  Written: {filepath}")


def main():
    print(f"Reading CSV:  {INPUT_CSV}")
    all_rows  = load_csv(INPUT_CSV)

    # Row 0 = internal column codes  (skip)
    # Row 1 = human-readable labels  (skip)
    # Row 2+ = respondent data
    data_rows = all_rows[2:]
    print(f"  Data rows found: {len(data_rows)}")

    store = initialise_aspect_store()
    process_rows(data_rows, store)
    finalise_store(store)

    print(f"\nWriting JSON files to: {OUTPUT_DIR}")
    write_json_files(store, OUTPUT_DIR)

    print("\nSummary:")
    for aspect_key, data in store.items():
        tips = data["counts"]["tip_comment_count"]
        tops = data["counts"]["top_comment_count"]
        print(f"  {aspect_key:<45}  tips={tips:>3}  tops={tops:>3}")

    print("\nDone.")


if __name__ == "__main__":
    main()
