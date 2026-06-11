import csv
from pathlib import Path

from odds import add_odds_ratios


def main() -> None:
    derived_dir = Path(__file__).resolve().parents[2] / "data" / "derived"
    source_path = derived_dir / "ltt.csv"
    output_path = derived_dir / "ltt_or.csv"

    rows = []
    read_order: dict[str, int] = {}
    with source_path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            read_value = row["Read for Fun"]
            read_order.setdefault(read_value, len(read_order))
            rows.append(
                {
                    "Year": int(row["Year"]),
                    "Age": int(row["Age"]),
                    "Read for Fun": read_value,
                    "Percent": float(row["Percent"]),
                }
            )

    output_rows = add_odds_ratios(rows, key=lambda r: (r["Age"], r["Read for Fun"]))
    output_rows.sort(key=lambda r: (r["Year"], r["Age"], read_order[r["Read for Fun"]]))

    fieldnames = ["Year", "Age", "Read for Fun", "Percent", "Odds", "Odds Ratio"]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)


if __name__ == "__main__":
    main()
