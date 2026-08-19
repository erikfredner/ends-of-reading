"""Collapse the LTT frequency categories to "weekly or more often" and add odds ratios.

Writes two files. ``ltt_or_weekly.csv`` covers the whole series, baselined to
1984, and backs figure 5 and the manuscript's headline LTT claims.
``ltt_or_weekly_revised.csv`` keeps only the years NAEP collected under the
revised assessment format, baselined to the earliest of those, so a decline can
be quoted without spanning the instrument change. Which years belong to which
format comes from the ``Assessment Format`` column that ``ltt_extract.py``
carries over from NAEP's own footnote markers.
"""

import csv
from collections import defaultdict
from pathlib import Path

from odds import add_odds_ratios

WEEKLY_OR_MORE = {"Almost every day", "Once or twice a week"}
REVISED_FORMAT = "Revised"

FIELDNAMES = [
    "Year",
    "Age",
    "Read for Fun",
    "Percent",
    "Assessment Format",
    "Odds",
    "Odds Ratio",
]


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    derived_dir = Path(__file__).resolve().parents[2] / "data" / "derived"
    source_path = derived_dir / "ltt.csv"

    sums: dict[tuple[int, int], float] = defaultdict(float)
    formats: dict[tuple[int, int], str] = {}
    with source_path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["Read for Fun"] not in WEEKLY_OR_MORE:
                continue
            group = (int(row["Year"]), int(row["Age"]))
            sums[group] += float(row["Percent"])
            assessment_format = row["Assessment Format"]
            if formats.setdefault(group, assessment_format) != assessment_format:
                raise ValueError(
                    f"year {group[0]}, age {group[1]} mixes assessment formats — "
                    "summing across them would compare unlike instruments"
                )

    aggregated_rows = [
        {
            "Year": year,
            "Age": age,
            "Read for Fun": "Weekly or more often",
            "Percent": percent,
            "Assessment Format": formats[(year, age)],
        }
        for (year, age), percent in sums.items()
    ]

    by_age = lambda r: r["Age"]

    output_rows = add_odds_ratios(
        aggregated_rows, key=by_age, require_common_baseline=True
    )
    output_rows.sort(key=lambda r: (r["Year"], r["Age"]))
    write_csv(derived_dir / "ltt_or_weekly.csv", output_rows)

    revised_rows = add_odds_ratios(
        [r for r in aggregated_rows if r["Assessment Format"] == REVISED_FORMAT],
        key=by_age,
        require_common_baseline=True,
    )
    revised_rows.sort(key=lambda r: (r["Year"], r["Age"]))
    write_csv(derived_dir / "ltt_or_weekly_revised.csv", revised_rows)


if __name__ == "__main__":
    main()
