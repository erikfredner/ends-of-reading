from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from plotting import plot_grouped_timeseries
from style import apply_style


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot SPPA reading rates.")
    parser.add_argument(
        "--include-magazine",
        action="store_true",
        help='Include the "Any book or magazine" series (1982, 1985 only).',
    )
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[2]
    data_path = project_root / "data" / "source" / "sppa.csv"
    fig_output = project_root / "figures" / "fig1.png"

    apply_style()

    df = pd.read_csv(data_path)

    category_order = [
        "Any book",
        "Literature",
        "Novels or short stories",
        "Poetry",
        "Plays",
    ]
    if args.include_magazine:
        category_order.insert(0, "Any book or magazine")

    plot_grouped_timeseries(
        df=df,
        group_col="Read in the last year",
        group_order=category_order,
        value_column="Percent",
        ylabel="US adults reading in the past year",
        output_path=fig_output,
        legend_title="Type of reading",
        hline=50,
        ylim=(0, 100),
        tick_every_year=True,
        percent_y=True,
    )


if __name__ == "__main__":
    main()
