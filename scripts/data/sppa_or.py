import csv
from pathlib import Path

from odds import compute_odds


def main() -> None:
    derived_dir = Path(__file__).resolve().parents[2] / "data" / "derived"
    source_path = derived_dir / "sppa.csv"
    output_path = derived_dir / "sppa_or.csv"

    rows = []
    category_order: dict[str, int] = {}

    with source_path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        for row in reader:
            year_raw = (row.get("Year") or "").strip()
            category_raw = (row.get("Read in the last year") or "").strip()
            percent_raw = (row.get("Percent") or "").strip()

            if not year_raw or not category_raw or not percent_raw:
                continue

            try:
                year = int(float(year_raw))
                percent = float(percent_raw)
            except ValueError:
                continue

            if category_raw not in category_order:
                category_order[category_raw] = len(category_order)

            rows.append(
                {
                    "Year": year,
                    "Read in the last year": category_raw,
                    "Percent": percent,
                    "_category_order": category_order[category_raw],
                }
            )

    min_year_per_category: dict[str, int] = {}
    for row in rows:
        category = row["Read in the last year"]
        year = row["Year"]
        if category not in min_year_per_category or year < min_year_per_category[category]:
            min_year_per_category[category] = year

    baseline_odds: dict[str, float] = {}
    for row in rows:
        category = row["Read in the last year"]
        if row["Year"] != min_year_per_category.get(category):
            continue

        try:
            baseline_odds[category] = compute_odds(row["Percent"])
        except ValueError:
            continue

    output_rows = []
    for row in rows:
        category = row["Read in the last year"]
        if category not in baseline_odds:
            continue

        try:
            odds = compute_odds(row["Percent"])
        except ValueError:
            continue

        baseline = baseline_odds[category]
        odds_ratio = odds / baseline if baseline != 0 else float("nan")

        output_rows.append(
            {
                "Year": row["Year"],
                "Read in the last year": category,
                "Percent": row["Percent"],
                "Odds": round(odds, 6),
                "Odds Ratio": round(odds_ratio, 6),
                "_category_order": row["_category_order"],
            }
        )

    output_rows.sort(key=lambda r: (r["Year"], r["_category_order"]))
    for row in output_rows:
        row.pop("_category_order", None)

    fieldnames = ["Year", "Read in the last year", "Percent", "Odds", "Odds Ratio"]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)


if __name__ == "__main__":
    main()
