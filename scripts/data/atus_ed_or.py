import csv
from pathlib import Path

from odds import compute_odds


def main() -> None:
    derived_dir = Path(__file__).resolve().parents[2] / "data" / "derived"
    source_path = derived_dir / "atus_ed.csv"
    output_path = derived_dir / "atus_ed_or.csv"

    rows = []
    edu_order: dict[str, int] = {}

    with source_path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        for row in reader:
            year_raw = (row.get("Year") or "").strip()
            percent_raw = (row.get("Percent") or "").strip()
            edu_raw = (row.get("Educational Attainment") or "").strip()

            if not year_raw or not percent_raw or not edu_raw:
                continue

            try:
                year = int(float(year_raw))
                percent = float(percent_raw)
            except ValueError:
                continue

            if edu_raw not in edu_order:
                edu_order[edu_raw] = len(edu_order)

            rows.append(
                {
                    "Year": year,
                    "ID": (row.get("ID") or "").strip(),
                    "Activity": (row.get("Activity") or "").strip(),
                    "Educational Attainment": edu_raw,
                    "Percent": percent,
                    "_edu_order": edu_order[edu_raw],
                }
            )

    min_year_per_edu: dict[str, int] = {}
    for row in rows:
        edu_value = row["Educational Attainment"]
        year = row["Year"]
        if edu_value not in min_year_per_edu or year < min_year_per_edu[edu_value]:
            min_year_per_edu[edu_value] = year

    baseline_odds: dict[str, float] = {}
    for row in rows:
        edu_value = row["Educational Attainment"]
        if row["Year"] != min_year_per_edu.get(edu_value):
            continue

        try:
            baseline_odds[edu_value] = compute_odds(row["Percent"])
        except ValueError:
            continue

    output_rows = []
    for row in rows:
        edu_value = row["Educational Attainment"]
        if edu_value not in baseline_odds:
            continue

        try:
            odds = compute_odds(row["Percent"])
        except ValueError:
            continue

        baseline = baseline_odds[edu_value]
        odds_ratio = odds / baseline if baseline != 0 else float("nan")

        output_rows.append(
            {
                "Year": row["Year"],
                "ID": row["ID"],
                "Activity": row["Activity"],
                "Educational Attainment": edu_value,
                "Percent": row["Percent"],
                "Odds": round(odds, 6),
                "Odds Ratio": round(odds_ratio, 6),
                "_edu_order": row["_edu_order"],
            }
        )

    output_rows.sort(key=lambda r: (r["Year"], r["_edu_order"]))
    for row in output_rows:
        row.pop("_edu_order", None)

    fieldnames = [
        "Year",
        "ID",
        "Activity",
        "Educational Attainment",
        "Percent",
        "Odds",
        "Odds Ratio",
    ]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)


if __name__ == "__main__":
    main()
