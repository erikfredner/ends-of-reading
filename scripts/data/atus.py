import csv
import math
from pathlib import Path


def parse_filename(csv_path: Path) -> tuple[str, str]:
    stem = csv_path.stem
    id_part = stem.split()[0]
    activity = stem.split(" - ", 1)[1] if " - " in stem else ""
    return id_part, activity


PARTICIPATION_ID_PREFIX = "TUU30105"


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    source_dir = project_root / "data" / "source" / "atus"
    output_path = project_root / "data" / "derived" / "atus.csv"

    fieldnames = ["Year", "ID", "Activity", "Percent"]
    rows = []

    for csv_path in sorted(source_dir.glob(f"{PARTICIPATION_ID_PREFIX}*.csv")):
        id_part, activity = parse_filename(csv_path)

        with csv_path.open(newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)

            for row in reader:
                year_str = (row.get("Year") or "").strip()
                estimate_str = (row.get("Estimate") or "").strip()

                if not year_str or not estimate_str:
                    continue

                try:
                    year = int(float(year_str))
                except ValueError:
                    continue

                try:
                    percent = float(estimate_str)
                except ValueError:
                    continue

                if math.isnan(percent):
                    continue

                rows.append(
                    {
                        "Year": year,
                        "ID": id_part,
                        "Activity": activity,
                        "Percent": percent,
                    }
                )

    rows.sort(key=lambda r: (r["Year"], r["ID"]))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
