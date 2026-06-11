import csv
from pathlib import Path


ID_VALUE = "TUU30105AA01006315"
ACTIVITY_VALUE = "Reading for personal interest"


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    source_path = project_root / "data" / "source" / "atus_ed.csv"
    output_path = project_root / "data" / "derived" / "atus_ed.csv"

    rows = []

    with source_path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            return

        edu_columns = [name for name in reader.fieldnames if name != "Year"]
        edu_order = {name: idx for idx, name in enumerate(edu_columns)}

        for row in reader:
            year_raw = (row.get("Year") or "").strip()
            if not year_raw:
                continue

            try:
                year = int(float(year_raw))
            except ValueError:
                continue

            for column in edu_columns:
                value_raw = (row.get(column) or "").strip()
                if not value_raw:
                    continue

                try:
                    percent = float(value_raw)
                except ValueError:
                    continue

                rows.append(
                    {
                        "Year": year,
                        "ID": ID_VALUE,
                        "Activity": ACTIVITY_VALUE,
                        "Educational Attainment": column,
                        "Percent": percent,
                        "_edu_order": edu_order[column],
                    }
                )

    rows.sort(key=lambda r: (r["Year"], r["_edu_order"]))
    for row in rows:
        row.pop("_edu_order", None)

    fieldnames = ["Year", "ID", "Activity", "Educational Attainment", "Percent"]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
