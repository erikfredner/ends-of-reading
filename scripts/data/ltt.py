import csv
from pathlib import Path


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    source_dir = project_root / "data" / "source" / "ltt"
    output_path = project_root / "data" / "derived" / "ltt.csv"

    fieldnames = ["Year", "Age", "Read for Fun", "Percent"]
    rows = []

    for csv_path in sorted(source_dir.glob("*.csv"), key=lambda p: int(p.stem)):
        age = int(csv_path.stem)

        with csv_path.open(newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)

            for row in reader:
                year = int(row["Year"])
                for column, value in row.items():
                    if column in {"Year", "Jurisdiction"}:
                        continue
                    if value in ("", None):
                        continue

                    rows.append(
                        {
                            "Year": year,
                            "Age": age,
                            "Read for Fun": column,
                            "Percent": float(value),
                        }
                    )

    rows.sort(key=lambda r: (r["Year"], r["Age"]))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
