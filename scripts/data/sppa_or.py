"""Add odds ratios to the SPPA reading rates cited in the manuscript.

Reads the already-tidy ``data/source/sppa.csv`` (no stage-1 extraction step)
and writes ``data/derived/sppa_or.csv``.

Every category is baselined to its own earliest year except poetry. The 1982
and 1985 surveys asked whether respondents had read *or listened to* poetry,
so those two values are not comparable with later ones; the manuscript
baselines poetry to 1992 alongside novels/short stories and plays, and this
script drops the earlier poetry rows rather than carrying them at a ratio that
would not mean what the rest of the column means.
"""

import csv
from pathlib import Path

from odds import add_odds_ratios

CATEGORY_ORDER = [
    "Any book or magazine",
    "Any book",
    "Literature",
    "Novels or short stories",
    "Poetry",
    "Plays",
]

# Categories needing an explicit baseline year; everything else uses its own
# earliest year. See the module docstring for why poetry starts at 1992.
PINNED_BASELINES = {"Poetry": 1992}


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    source_path = project_root / "data" / "source" / "sppa.csv"
    output_path = project_root / "data" / "derived" / "sppa_or.csv"

    rows = []
    with source_path.open(newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            percent = (row["Percent"] or "").strip()
            if not percent:
                continue
            rows.append(
                {
                    "Year": int(row["Year"]),
                    "Read in the last year": row["Read in the last year"],
                    "Percent": float(percent),
                    "Source": row["Source"],
                    "Location": row["Location"],
                }
            )

    key = lambda r: r["Read in the last year"]
    output_rows = add_odds_ratios(
        [r for r in rows if key(r) not in PINNED_BASELINES], key=key
    )
    for category, baseline_year in PINNED_BASELINES.items():
        output_rows.extend(
            add_odds_ratios(
                [r for r in rows if key(r) == category],
                key=key,
                baseline_year=baseline_year,
            )
        )

    order = {category: i for i, category in enumerate(CATEGORY_ORDER)}
    output_rows.sort(key=lambda r: (r["Year"], order[key(r)]))

    fieldnames = [
        "Year",
        "Read in the last year",
        "Percent",
        "Source",
        "Location",
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
