import csv
from pathlib import Path

from odds import add_odds_ratios


def main() -> None:
    derived_dir = Path(__file__).resolve().parents[2] / "data" / "derived"
    source_path = derived_dir / "atus_ed.csv"
    output_path = derived_dir / "atus_ed_or.csv"

    rows = []
    edu_order: dict[str, int] = {}
    with source_path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            edu = row["Educational Attainment"]
            edu_order.setdefault(edu, len(edu_order))
            rows.append(
                {
                    "Year": int(row["Year"]),
                    "ID": row["ID"],
                    "Activity": row["Activity"],
                    "Educational Attainment": edu,
                    "Percent": float(row["Percent"]),
                }
            )

    output_rows = add_odds_ratios(rows, key=lambda r: r["Educational Attainment"])
    output_rows.sort(key=lambda r: (r["Year"], edu_order[r["Educational Attainment"]]))

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
