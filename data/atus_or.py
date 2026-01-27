import csv
from pathlib import Path

from odds import compute_odds


def main() -> None:
    base_dir = Path(__file__).parent
    source_path = base_dir / "atus.csv"
    output_path = base_dir / "atus_or.csv"

    rows = []

    with source_path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        for row in reader:
            year_raw = (row.get("Year") or "").strip()
            percent_raw = (row.get("Percent") or "").strip()

            if not year_raw or not percent_raw:
                continue

            try:
                year = int(float(year_raw))
                percent = float(percent_raw)
            except ValueError:
                continue

            rows.append(
                {
                    "Year": year,
                    "ID": (row.get("ID") or "").strip(),
                    "Activity": (row.get("Activity") or "").strip(),
                    "Percent": percent,
                }
            )

    min_year_per_id: dict[str, int] = {}
    for row in rows:
        id_value = row["ID"]
        year = row["Year"]
        if not id_value:
            continue
        if id_value not in min_year_per_id or year < min_year_per_id[id_value]:
            min_year_per_id[id_value] = year

    baseline_odds: dict[str, float] = {}
    for row in rows:
        id_value = row["ID"]
        if not id_value or id_value not in min_year_per_id:
            continue
        if row["Year"] != min_year_per_id[id_value]:
            continue

        try:
            baseline_odds[id_value] = compute_odds(row["Percent"])
        except ValueError:
            continue

    output_rows = []
    for row in rows:
        id_value = row["ID"]
        if not id_value or id_value not in baseline_odds:
            continue

        try:
            odds = compute_odds(row["Percent"])
        except ValueError:
            continue

        baseline = baseline_odds[id_value]
        odds_ratio = odds / baseline if baseline != 0 else float("nan")

        output_rows.append(
            {
                "Year": row["Year"],
                "ID": id_value,
                "Activity": row["Activity"],
                "Percent": row["Percent"],
                "Odds": round(odds, 6),
                "Odds Ratio": round(odds_ratio, 6),
            }
        )

    output_rows.sort(key=lambda r: (r["Year"], r["ID"]))

    fieldnames = ["Year", "ID", "Activity", "Percent", "Odds", "Odds Ratio"]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)


if __name__ == "__main__":
    main()
