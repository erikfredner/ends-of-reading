import csv
from pathlib import Path


AGES = [9, 13, 17]
MISSING_VALUES = {"", "—"}

# NAEP footnotes the years collected under the pre-2008 instrument with a
# superscript one ("2004¹") and leaves the revised-format years unmarked. The
# marker is the only record of the break in the dumps, so carry it through
# rather than hard-coding the changeover year downstream.
ORIGINAL_FORMAT_MARKER = "¹"
ORIGINAL_FORMAT = "Original"
REVISED_FORMAT = "Revised"


def _find_header_index(lines: list[str]) -> int:
    for index, line in enumerate(lines):
        cells = [cell.strip() for cell in line.split("\t")]
        if len(cells) >= 3 and cells[0] == "Year" and cells[1] == "Jurisdiction":
            return index
    raise ValueError("could not find LTT table header row")


def parse_txt(path: Path) -> tuple[list[str], list[dict]]:
    with path.open(encoding="utf-8") as f:
        lines = [line.rstrip("\n") for line in f]

    header_index = _find_header_index(lines)
    subheader_cells = [cell.strip() for cell in lines[header_index - 1].split("\t")]
    categories = [cell for cell in subheader_cells if cell]
    expected_columns = 2 + len(categories)

    rows = []
    for line in lines[header_index + 1 :]:
        if not line.strip():
            break
        stripped = line.strip()
        if stripped.startswith(("— ", "¹", "NOTE:", "SOURCE:")):
            break

        cells = [cell.strip() for cell in line.split("\t")]
        if len(cells) < expected_columns:
            continue

        year_raw = cells[0].replace(ORIGINAL_FORMAT_MARKER, "")
        try:
            year = int(year_raw)
        except ValueError:
            continue

        assessment_format = (
            ORIGINAL_FORMAT
            if ORIGINAL_FORMAT_MARKER in cells[0]
            else REVISED_FORMAT
        )
        row = {
            "Year": year,
            "Jurisdiction": cells[1],
            "Assessment Format": assessment_format,
        }
        for category, value in zip(categories, cells[2 : 2 + len(categories)]):
            row[category] = "" if value in MISSING_VALUES else value
        rows.append(row)

    return categories, rows


def tidy(age: int, categories: list[str], txt_rows: list[dict]) -> list[dict]:
    # NAEP dumps can list a year twice (original and revised assessment
    # formats, e.g. "2004" and "2004¹"). Today at most one of the pair carries
    # values; if both ever do, summing downstream would silently double-count.
    seen: set[tuple[int, str]] = set()
    rows = []
    for row in txt_rows:
        for category in categories:
            value = row.get(category, "")
            if value == "":
                continue
            key = (row["Year"], category)
            if key in seen:
                raise ValueError(
                    f"duplicate LTT value for year {row['Year']}, age {age}, "
                    f"category {category!r} — multiple assessment formats "
                    "with data for the same year?"
                )
            seen.add(key)
            rows.append(
                {
                    "Year": row["Year"],
                    "Age": age,
                    "Read for Fun": category,
                    "Percent": float(value),
                    "Assessment Format": row["Assessment Format"],
                }
            )
    return rows


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    source_dir = project_root / "data" / "source" / "ltt"
    output_path = project_root / "data" / "derived" / "ltt.csv"

    fieldnames = ["Year", "Age", "Read for Fun", "Percent", "Assessment Format"]
    tidy_rows = []

    for age in AGES:
        categories, txt_rows = parse_txt(source_dir / f"{age}.txt")
        tidy_rows.extend(tidy(age, categories, txt_rows))

    tidy_rows.sort(key=lambda r: (r["Year"], r["Age"]))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(tidy_rows)


if __name__ == "__main__":
    main()
