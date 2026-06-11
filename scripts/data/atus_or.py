import csv
from pathlib import Path

from odds import add_odds_ratios


def main() -> None:
    derived_dir = Path(__file__).resolve().parents[2] / "data" / "derived"
    source_path = derived_dir / "atus.csv"
    output_path = derived_dir / "atus_or.csv"

    rows = []
    with source_path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append(
                {
                    "Year": int(row["Year"]),
                    "ID": row["ID"],
                    "Activity": row["Activity"],
                    "Percent": float(row["Percent"]),
                }
            )

    output_rows = add_odds_ratios(rows, key=lambda r: r["ID"])
    output_rows.sort(key=lambda r: (r["Year"], r["ID"]))

    fieldnames = ["Year", "ID", "Activity", "Percent", "Odds", "Odds Ratio"]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)


if __name__ == "__main__":
    main()
