import csv
from pathlib import Path


AGES = [9, 13, 17]
MISSING_VALUES = {"", "—"}


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

        year_raw = cells[0].replace("¹", "")
        try:
            year = int(year_raw)
        except ValueError:
            continue

        row = {"Year": year, "Jurisdiction": cells[1]}
        for category, value in zip(categories, cells[2 : 2 + len(categories)]):
            row[category] = "" if value in MISSING_VALUES else value
        rows.append(row)

    return categories, rows


def report_discrepancies(
    age: int, categories: list[str], txt_rows: list[dict], csv_path: Path
) -> None:
    if not csv_path.exists():
        print(f"Age {age}: no legacy CSV at {csv_path.name}; skipping comparison")
        return

    with csv_path.open(newline="", encoding="utf-8-sig") as f:
        csv_rows = list(csv.DictReader(f))

    txt_by_year = {row["Year"]: row for row in txt_rows}
    csv_by_year = {int(row["Year"]): row for row in csv_rows}

    in_csv_only = sorted(csv_by_year.keys() - txt_by_year.keys())
    in_txt_only = sorted(txt_by_year.keys() - csv_by_year.keys())

    mismatches = []
    for year in sorted(txt_by_year.keys() & csv_by_year.keys()):
        txt_row = txt_by_year[year]
        csv_row = csv_by_year[year]
        for category in categories:
            txt_value = txt_row.get(category, "")
            csv_value = (csv_row.get(category) or "").strip()
            if txt_value != csv_value:
                mismatches.append((year, category, txt_value, csv_value))

    if not in_csv_only and not in_txt_only and not mismatches:
        print(f"Age {age}: TXT and CSV agree")
        return

    print(f"Age {age}:")
    print(f"  In CSV but not in TXT: {in_csv_only}")
    print(f"  In TXT but not in CSV: {in_txt_only}")
    if mismatches:
        print("  Value mismatches:")
        for year, category, txt_value, csv_value in mismatches:
            print(f"    {year} {category!r}: TXT={txt_value!r} CSV={csv_value!r}")
    else:
        print("  Value mismatches: none")


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    source_dir = project_root / "data" / "source" / "ltt"
    output_path = project_root / "data" / "derived" / "ltt.csv"

    fieldnames = ["Year", "Age", "Read for Fun", "Percent"]
    tidy_rows = []

    print("Discrepancy report (TXT vs CSV):")
    for age in AGES:
        txt_path = source_dir / f"{age}.txt"
        csv_path = source_dir / f"{age}.csv"

        categories, txt_rows = parse_txt(txt_path)

        for row in txt_rows:
            for category in categories:
                value = row.get(category, "")
                if value == "":
                    continue
                tidy_rows.append(
                    {
                        "Year": row["Year"],
                        "Age": age,
                        "Read for Fun": category,
                        "Percent": float(value),
                    }
                )

        report_discrepancies(age, categories, txt_rows, csv_path)

    tidy_rows.sort(key=lambda r: (r["Year"], r["Age"]))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(tidy_rows)


if __name__ == "__main__":
    main()
