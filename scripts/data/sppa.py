import csv
from pathlib import Path


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    source_path = project_root / "data" / "source" / "sppa.csv"
    output_path = project_root / "data" / "derived" / "sppa.csv"

    with source_path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = ["Year", "Read in the last year", "Percent"]
        rows = []

        for row in reader:
            year = int(row["Year"])
            for column, value in row.items():
                if column == "Year":
                    continue
                if value in ("", None):
                    continue

                percent = round(float(value) * 100, 1)
                rows.append(
                    {
                        "Year": year,
                        "Read in the last year": column,
                        "Percent": percent,
                    }
                )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
