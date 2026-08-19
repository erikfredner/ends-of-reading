import csv
from collections import defaultdict
from pathlib import Path

from odds import add_odds_ratios


WEEKLY_OR_MORE = {"Almost every day", "Once or twice a week"}


def main() -> None:
    derived_dir = Path(__file__).resolve().parents[2] / "data" / "derived"
    source_path = derived_dir / "ltt.csv"
    output_path = derived_dir / "ltt_or_weekly.csv"

    sums: dict[tuple[int, int], float] = defaultdict(float)
    with source_path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["Read for Fun"] not in WEEKLY_OR_MORE:
                continue
            sums[(int(row["Year"]), int(row["Age"]))] += float(row["Percent"])

    aggregated_rows = [
        {
            "Year": year,
            "Age": age,
            "Read for Fun": "Weekly or more often",
            "Percent": percent,
        }
        for (year, age), percent in sums.items()
    ]

    output_rows = add_odds_ratios(
        aggregated_rows, key=lambda r: r["Age"], require_common_baseline=True
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
