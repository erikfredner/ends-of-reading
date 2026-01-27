import csv
from pathlib import Path

from odds import compute_odds


def main() -> None:
    base_dir = Path(__file__).parent
    source_path = base_dir / "ltt.csv"
    output_path = base_dir / "ltt_or.csv"

    rows = []
    read_order: dict[str, int] = {}

    with source_path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        for row in reader:
            year_raw = (row.get("Year") or "").strip()
            age_raw = (row.get("Age") or "").strip()
            read_raw = (row.get("Read for Fun") or "").strip()
            percent_raw = (row.get("Percent") or "").strip()

            if not year_raw or not age_raw or not read_raw or not percent_raw:
                continue

            try:
                year = int(float(year_raw))
                age = int(float(age_raw))
                percent = float(percent_raw)
            except ValueError:
                continue

            if read_raw not in read_order:
                read_order[read_raw] = len(read_order)

            rows.append(
                {
                    "Year": year,
                    "Age": age,
                    "Read for Fun": read_raw,
                    "Percent": percent,
                    "_read_order": read_order[read_raw],
                }
            )

    min_year_per_group: dict[tuple[int, str], int] = {}
    for row in rows:
        key = (row["Age"], row["Read for Fun"])
        year = row["Year"]
        if key not in min_year_per_group or year < min_year_per_group[key]:
            min_year_per_group[key] = year

    baseline_odds: dict[tuple[int, str], float] = {}
    for row in rows:
        key = (row["Age"], row["Read for Fun"])
        if row["Year"] != min_year_per_group.get(key):
            continue

        try:
            baseline_odds[key] = compute_odds(row["Percent"])
        except ValueError:
            continue

    output_rows = []
    for row in rows:
        key = (row["Age"], row["Read for Fun"])
        if key not in baseline_odds:
            continue

        try:
            odds = compute_odds(row["Percent"])
        except ValueError:
            continue

        baseline = baseline_odds[key]
        odds_ratio = odds / baseline if baseline != 0 else float("nan")

        output_rows.append(
            {
                "Year": row["Year"],
                "Age": row["Age"],
                "Read for Fun": row["Read for Fun"],
                "Percent": row["Percent"],
                "Odds": round(odds, 6),
                "Odds Ratio": round(odds_ratio, 6),
                "_read_order": row["_read_order"],
            }
        )

    output_rows.sort(key=lambda r: (r["Year"], r["Age"], r["_read_order"]))
    for row in output_rows:
        row.pop("_read_order", None)

    fieldnames = ["Year", "Age", "Read for Fun", "Percent", "Odds", "Odds Ratio"]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)


if __name__ == "__main__":
    main()
