import csv
from collections import defaultdict
from pathlib import Path

from odds import compute_odds


WEEKLY_OR_MORE = {"Almost every day", "Once or twice a week"}


def main() -> None:
    base_dir = Path(__file__).parent
    source_path = base_dir / "ltt.csv"
    output_path = base_dir / "ltt_or_weekly.csv"

    sums: dict[tuple[int, int], float] = defaultdict(float)

    with source_path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        for row in reader:
            read_raw = (row.get("Read for Fun") or "").strip()
            if read_raw not in WEEKLY_OR_MORE:
                continue

            year_raw = (row.get("Year") or "").strip()
            age_raw = (row.get("Age") or "").strip()
            percent_raw = (row.get("Percent") or "").strip()

            if not year_raw or not age_raw or not percent_raw:
                continue

            try:
                year = int(float(year_raw))
                age = int(float(age_raw))
                percent = float(percent_raw)
            except ValueError:
                continue

            sums[(year, age)] += percent

    aggregated_rows = []
    for (year, age), percent in sums.items():
        aggregated_rows.append(
            {
                "Year": year,
                "Age": age,
                "Read for Fun": "Weekly or more often",
                "Percent": percent,
            }
        )

    min_year_per_age: dict[int, int] = {}
    for row in aggregated_rows:
        age = row["Age"]
        year = row["Year"]
        if age not in min_year_per_age or year < min_year_per_age[age]:
            min_year_per_age[age] = year

    baseline_odds: dict[int, float] = {}
    for row in aggregated_rows:
        age = row["Age"]
        if row["Year"] != min_year_per_age.get(age):
            continue

        try:
            baseline_odds[age] = compute_odds(row["Percent"])
        except ValueError:
            continue

    output_rows = []
    for row in aggregated_rows:
        age = row["Age"]
        if age not in baseline_odds:
            continue

        try:
            odds = compute_odds(row["Percent"])
        except ValueError:
            continue

        baseline = baseline_odds[age]
        odds_ratio = odds / baseline if baseline != 0 else float("nan")

        output_rows.append(
            {
                "Year": row["Year"],
                "Age": age,
                "Read for Fun": row["Read for Fun"],
                "Percent": row["Percent"],
                "Odds": round(odds, 6),
                "Odds Ratio": round(odds_ratio, 6),
            }
        )

    output_rows.sort(key=lambda r: (r["Year"], r["Age"]))

    fieldnames = ["Year", "Age", "Read for Fun", "Percent", "Odds", "Odds Ratio"]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)


if __name__ == "__main__":
    main()
