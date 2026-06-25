import csv
import math
from pathlib import Path


def parse_series_file(txt_path: Path) -> tuple[str, str, list[str]]:
    """Read a raw BLS ATUS dump.

    Returns the series id (the filename stem), the activity label (from the
    ``Activity:`` line in the metadata header), and the CSV body lines starting
    at the ``Year,Period,Estimate,Standard Error`` header.
    """
    id_part = txt_path.stem
    lines = txt_path.read_text(encoding="utf-8-sig").splitlines()

    activity = ""
    header_idx = None
    for i, line in enumerate(lines):
        if line.startswith("Activity:"):
            activity = line.split(":", 1)[1].strip()
        elif line.startswith("Year,"):
            header_idx = i
            break

    data_lines = lines[header_idx:] if header_idx is not None else []
    return id_part, activity, data_lines


PARTICIPATION_ID_PREFIX = "TUU30105"


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    source_dir = project_root / "data" / "source" / "atus"
    output_path = project_root / "data" / "derived" / "atus.csv"

    fieldnames = ["Year", "ID", "Activity", "Percent"]
    rows = []

    for txt_path in sorted(source_dir.glob(f"{PARTICIPATION_ID_PREFIX}*.txt")):
        id_part, activity, data_lines = parse_series_file(txt_path)

        reader = csv.DictReader(data_lines)

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
